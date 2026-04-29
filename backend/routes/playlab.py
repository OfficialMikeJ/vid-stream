"""PlayLab Integration routes: API key management, video listing, and webhook sync."""
import os
import secrets
from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

import httpx
from fastapi import APIRouter, HTTPException, Depends, Request

from database import db
from models import PlayLabSettings, User, PlayLabImportItem
from security import get_current_user, require_admin
from services import _trigger_playlab_webhook

router = APIRouter(prefix="/api")


async def _get_or_create_settings():
    s = await db.playlab_settings.find_one({}, {"_id": 0})
    if not s:
        obj = PlayLabSettings()
        doc = obj.model_dump()
        await db.playlab_settings.insert_one(doc)
        return doc
    return s


async def _verify_key(request: Request):
    key = request.headers.get("X-PlayLab-Key") or request.query_params.get("api_key")
    if not key:
        raise HTTPException(status_code=401, detail="PlayLab API key required (X-PlayLab-Key header or api_key param)")
    s = await db.playlab_settings.find_one({}, {"_id": 0})
    if not s or s.get("api_key") != key:
        raise HTTPException(status_code=403, detail="Invalid PlayLab API key")
    if not s.get("enabled", True):
        raise HTTPException(status_code=403, detail="PlayLab integration is disabled")
    return s


@router.get("/playlab/settings")
async def get_settings(current_user: User = Depends(get_current_user)):
    s = await _get_or_create_settings()
    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8001")
    return {
        **s,
        "api_base_url": f"{backend_url}/api/playlab",
        "videos_endpoint": f"{backend_url}/api/playlab/videos",
        "video_detail_endpoint": f"{backend_url}/api/playlab/video/{{video_id}}",
    }


@router.post("/playlab/regenerate-key")
async def regenerate_key(current_user: User = Depends(get_current_user)):
    new_key = secrets.token_urlsafe(32)
    await db.playlab_settings.update_one(
        {}, {"$set": {"api_key": new_key, "updated_at": datetime.now(timezone.utc).isoformat()}}, upsert=True
    )
    return {"api_key": new_key, "message": "API key regenerated successfully"}


@router.patch("/playlab/settings")
async def update_settings(enabled: bool, current_user: User = Depends(get_current_user)):
    await db.playlab_settings.update_one(
        {}, {"$set": {"enabled": enabled, "updated_at": datetime.now(timezone.utc).isoformat()}}, upsert=True
    )
    return {"message": f"PlayLab integration {'enabled' if enabled else 'disabled'}"}


@router.patch("/playlab/webhook")
async def update_webhook(
    webhook_url: Optional[str] = None,
    webhook_secret: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Set or clear the webhook URL and optional shared secret."""
    update = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if webhook_url is not None:
        update["webhook_url"] = webhook_url or None
    if webhook_secret is not None:
        update["webhook_secret"] = webhook_secret or None
    await db.playlab_settings.update_one({}, {"$set": update}, upsert=True)
    return {"message": "Webhook settings updated"}


@router.post("/playlab/test-webhook")
async def test_webhook(current_user: User = Depends(get_current_user)):
    """Send a test ping to the configured PlayLab webhook URL."""
    s = await db.playlab_settings.find_one({}, {"_id": 0})
    if not s or not s.get("webhook_url"):
        raise HTTPException(status_code=400, detail="No webhook URL configured")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                s["webhook_url"],
                json={"event": "test", "timestamp": datetime.now(timezone.utc).isoformat(), "message": "StreamHost webhook test"},
            )
            return {"success": True, "status_code": resp.status_code, "response": resp.text[:300]}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/playlab/videos")
async def list_videos(request: Request):
    """List all ready videos with HLS URLs. Authenticate with X-PlayLab-Key header."""
    await _verify_key(request)
    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8001")
    videos = await db.videos.find({"processing_status": "ready"}, {"_id": 0}).to_list(1000)
    result = [
        {
            "id": v["id"],
            "title": v["title"],
            "description": v.get("description"),
            "duration": v.get("duration"),
            "thumbnail_url": f"{backend_url}/api/stream/thumbnail/{v['id']}",
            "hls_url": f"{backend_url}/api/stream/hls/{v['id']}/playlist.m3u8",
            "width": v.get("width"),
            "height": v.get("height"),
            "aspect_ratio": v.get("aspect_ratio"),
            "file_size": v.get("file_size"),
            "created_at": v.get("created_at"),
            "playlab_video_url": f"{backend_url}/api/stream/hls/{v['id']}/playlist.m3u8",
            "playlab_server_type": 2,
        }
        for v in videos
    ]
    return {"count": len(result), "videos": result}


@router.get("/playlab/video/{video_id}")
async def get_video(video_id: str, request: Request):
    """Get a single video with all PlayLab DB-ready fields."""
    await _verify_key(request)
    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8001")
    video = await db.videos.find_one({"id": video_id}, {"_id": 0})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    hls_url = f"{backend_url}/api/stream/hls/{video_id}/playlist.m3u8"
    return {
        "id": video["id"],
        "title": video["title"],
        "description": video.get("description"),
        "duration": video.get("duration"),
        "thumbnail_url": f"{backend_url}/api/stream/thumbnail/{video_id}",
        "hls_url": hls_url,
        "width": video.get("width"),
        "height": video.get("height"),
        "aspect_ratio": video.get("aspect_ratio"),
        "processing_status": video.get("processing_status"),
        "playlab": {
            "server_type": 2,
            "video_url": hls_url,
            "server_seven_twenty": 2, "seven_twenty_video": hls_url,
            "server_four_eighty": 2, "four_eighty_video": hls_url,
            "server_three_sixty": 2, "three_sixty_video": hls_url,
            "server_thousand_eighty": 2, "thousand_eighty_video": hls_url,
        },
    }


@router.post("/playlab/import")
async def import_videos(items: List[PlayLabImportItem], current_user: User = Depends(require_admin)):
    """
    Bulk-import external video URLs into the StreamHost library.
    Each item becomes a video record with processing_status='external'.
    """
    if not items:
        raise HTTPException(status_code=400, detail="No items to import")
    if len(items) > 200:
        raise HTTPException(status_code=400, detail="Maximum 200 items per import")

    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8001")
    created = []

    for item in items:
        video_id = str(uuid4())
        doc = {
            "id": video_id,
            "title": item.title,
            "description": item.description,
            "folder_id": None,
            "original_filename": item.title,
            "file_path": item.hls_url,
            "thumbnail_path": None,
            "thumbnail_url": item.thumbnail_url,
            "hls_path": item.hls_url,
            "duration": None,
            "width": None,
            "height": None,
            "aspect_ratio": None,
            "file_size": 0,
            "format": "hls_external",
            "processing_status": "external",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.videos.insert_one(doc)
        created.append({"id": video_id, "title": item.title, "hls_url": item.hls_url})

    return {
        "imported": len(created),
        "videos": created,
        "message": f"Successfully imported {len(created)} video(s) from PlayLab",
    }
