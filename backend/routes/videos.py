"""Video CRUD, streaming, embed settings, and folder endpoints."""
import os
import shutil
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Request
from fastapi.responses import FileResponse

from database import db, VIDEO_STORAGE_PATH
from models import VideoMetadata, EmbedSettings, EmbedSettingsCreate, Folder, FolderCreate, User, PlayerSettings
from security import get_current_user, require_admin
from services import process_video

router = APIRouter(prefix="/api")


# ── Health ───────────────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    try:
        await db.command("ping")
        return {"status": "healthy", "service": "StreamHost API", "version": "2025.12.17", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")


# ── Folders ──────────────────────────────────────────────────────────────────

@router.post("/folders", response_model=Folder)
async def create_folder(folder: FolderCreate, current_user: User = Depends(require_admin)):
    obj = Folder(**folder.model_dump())
    doc = obj.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.folders.insert_one(doc)
    return obj


@router.get("/folders", response_model=List[Folder])
async def get_folders(current_user: User = Depends(get_current_user)):
    folders = await db.folders.find({}, {"_id": 0}).to_list(1000)
    for f in folders:
        if isinstance(f["created_at"], str):
            f["created_at"] = datetime.fromisoformat(f["created_at"])
    return folders


@router.delete("/folders/{folder_id}")
async def delete_folder(folder_id: str, current_user: User = Depends(require_admin)):
    result = await db.folders.delete_one({"id": folder_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Folder not found")
    return {"message": "Folder deleted"}


# ── Videos ───────────────────────────────────────────────────────────────────

@router.post("/videos/upload")
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    folder_id: Optional[str] = Form(None),
    current_user: User = Depends(require_admin),
):
    max_size = 56 * 1024 * 1024 * 1024
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > max_size:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 56GB.")

    from uuid import uuid4
    video_id = str(uuid4())
    ext = Path(file.filename).suffix
    original_path = VIDEO_STORAGE_PATH / "originals" / f"{video_id}{ext}"

    with open(original_path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)

    video = VideoMetadata(
        id=video_id,
        title=title,
        description=description,
        folder_id=folder_id,
        original_filename=file.filename,
        file_path=str(original_path),
        file_size=original_path.stat().st_size,
        processing_status="pending",
    )
    doc = video.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.videos.insert_one(doc)
    asyncio.create_task(process_video(video_id))
    return {"video_id": video_id, "message": "Video uploaded and processing started"}


@router.get("/videos", response_model=List[VideoMetadata])
async def get_videos(
    folder_id: Optional[str] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
    sort: str = "newest",
    current_user: User = Depends(get_current_user),
):
    query = {}
    if folder_id:
        query["folder_id"] = folder_id
    if status:
        query["processing_status"] = status
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    sort_field = "created_at"
    sort_order = -1 if sort in ("newest", "date_desc") else 1

    videos = await db.videos.find(query, {"_id": 0}).sort(sort_field, sort_order).to_list(1000)
    for v in videos:
        if isinstance(v["created_at"], str):
            v["created_at"] = datetime.fromisoformat(v["created_at"])
    return videos


@router.get("/videos/{video_id}", response_model=VideoMetadata)
async def get_video(video_id: str, current_user: User = Depends(get_current_user)):
    video = await db.videos.find_one({"id": video_id}, {"_id": 0})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if isinstance(video["created_at"], str):
        video["created_at"] = datetime.fromisoformat(video["created_at"])
    return VideoMetadata(**video)


@router.delete("/videos/{video_id}")
async def delete_video(video_id: str, current_user: User = Depends(require_admin)):
    video = await db.videos.find_one({"id": video_id}, {"_id": 0})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.get("file_path") and Path(video["file_path"]).exists():
        Path(video["file_path"]).unlink()
    if video.get("thumbnail_path") and Path(video["thumbnail_path"]).exists():
        Path(video["thumbnail_path"]).unlink()
    if video.get("hls_path"):
        hls_dir = Path(video["hls_path"]).parent
        if hls_dir.exists():
            shutil.rmtree(hls_dir)
    await db.videos.delete_one({"id": video_id})
    await db.embed_settings.delete_many({"video_id": video_id})
    return {"message": "Video deleted"}


@router.patch("/videos/{video_id}")
async def update_video(
    video_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    folder_id: Optional[str] = None,
    current_user: User = Depends(require_admin),
):
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if folder_id is not None:
        update_data["folder_id"] = folder_id
    if update_data:
        result = await db.videos.update_one({"id": video_id}, {"$set": update_data})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Video not found")
    return {"message": "Video updated"}


# ── Streaming ────────────────────────────────────────────────────────────────

@router.get("/stream/thumbnail/{video_id}")
async def stream_thumbnail(video_id: str):
    video = await db.videos.find_one({"id": video_id}, {"_id": 0})
    if not video:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    # External (imported) videos may have a URL instead of a local file
    if video.get("thumbnail_url"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(video["thumbnail_url"])
    if not video.get("thumbnail_path"):
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    path = Path(video["thumbnail_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail file not found")
    return FileResponse(path, media_type="image/jpeg")


@router.get("/stream/hls/{video_id}/playlist.m3u8")
async def stream_hls_playlist(video_id: str, request: Request):
    referer = request.headers.get("referer", "")
    if referer:
        embed = await db.embed_settings.find_one({"video_id": video_id}, {"_id": 0})
        if embed and embed.get("allowed_domains"):
            domain = urlparse(referer).netloc
            if domain and not any(d in domain for d in embed["allowed_domains"]):
                raise HTTPException(status_code=403, detail="Domain not allowed")

    video = await db.videos.find_one({"id": video_id}, {"_id": 0})
    if not video or not video.get("hls_path"):
        raise HTTPException(status_code=404, detail="Video not ready")
    path = Path(video["hls_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Playlist not found")
    return FileResponse(path, media_type="application/vnd.apple.mpegurl")


@router.get("/stream/hls/{video_id}/{segment}")
async def stream_hls_segment(video_id: str, segment: str):
    video = await db.videos.find_one({"id": video_id}, {"_id": 0})
    if not video or not video.get("hls_path"):
        raise HTTPException(status_code=404, detail="Video not ready")
    seg_path = Path(video["hls_path"]).parent / segment
    if not seg_path.exists():
        raise HTTPException(status_code=404, detail="Segment not found")
    return FileResponse(seg_path, media_type="video/mp2t")


# ── Embed Settings ───────────────────────────────────────────────────────────

@router.post("/embed-settings", response_model=EmbedSettings)
async def create_embed_settings(
    settings: EmbedSettingsCreate, current_user: User = Depends(require_admin)
):
    existing = await db.embed_settings.find_one({"video_id": settings.video_id}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Embed settings already exist for this video")
    obj = EmbedSettings(**settings.model_dump())
    doc = obj.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    doc["updated_at"] = doc["updated_at"].isoformat()
    await db.embed_settings.insert_one(doc)
    return obj


@router.get("/embed-settings/{video_id}", response_model=EmbedSettings)
async def get_embed_settings(video_id: str, current_user: User = Depends(get_current_user)):
    s = await db.embed_settings.find_one({"video_id": video_id}, {"_id": 0})
    if not s:
        raise HTTPException(status_code=404, detail="Embed settings not found")
    for f in ("created_at", "updated_at"):
        if isinstance(s[f], str):
            s[f] = datetime.fromisoformat(s[f])
    return EmbedSettings(**s)


@router.patch("/embed-settings/{video_id}")
async def update_embed_settings(
    video_id: str,
    allowed_domains: Optional[List[str]] = None,
    player_color: Optional[str] = None,
    show_controls: Optional[bool] = None,
    autoplay: Optional[bool] = None,
    loop: Optional[bool] = None,
    custom_css: Optional[str] = None,
    current_user: User = Depends(require_admin),
):
    update = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if allowed_domains is not None:
        update["allowed_domains"] = allowed_domains
    if player_color is not None:
        update["player_color"] = player_color
    if show_controls is not None:
        update["show_controls"] = show_controls
    if autoplay is not None:
        update["autoplay"] = autoplay
    if loop is not None:
        update["loop"] = loop
    if custom_css is not None:
        update["custom_css"] = custom_css
    result = await db.embed_settings.update_one({"video_id": video_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Embed settings not found")
    return {"message": "Embed settings updated"}


@router.get("/embed-code/{video_id}")
async def get_embed_code(video_id: str, current_user: User = Depends(get_current_user)):
    video = await db.videos.find_one({"id": video_id}, {"_id": 0})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8001")
    embed = await db.embed_settings.find_one({"video_id": video_id}, {"_id": 0})

    player_color = embed.get("player_color", "#3b82f6") if embed else "#3b82f6"  # noqa: F841
    show_controls = embed.get("show_controls", True) if embed else True
    autoplay = embed.get("autoplay", False) if embed else False
    loop = embed.get("loop", False) if embed else False

    code = f'''<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
  <video id="video-{video_id}"
         style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
         {"controls" if show_controls else ""}
         {"autoplay" if autoplay else ""}
         {"loop" if loop else ""}>
    <source src="{backend_url}/api/stream/hls/{video_id}/playlist.m3u8" type="application/x-mpegURL">
    Your browser does not support the video tag.
  </video>
</div>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<script>
  var video = document.getElementById('video-{video_id}');
  if (Hls.isSupported()) {{
    var hls = new Hls();
    hls.loadSource('{backend_url}/api/stream/hls/{video_id}/playlist.m3u8');
    hls.attachMedia(video);
  }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
    video.src = '{backend_url}/api/stream/hls/{video_id}/playlist.m3u8';
  }}
</script>'''
    return {"embed_code": code}


# ── Player Settings ──────────────────────────────────────────────────────────

_DEFAULT_PLAYER = {
    "primary_color": "#3b82f6",
    "background_color": "#000000",
    "show_controls": True,
    "autoplay": False,
    "loop": False,
}


@router.get("/settings/player")
async def get_player_settings(current_user: User = Depends(get_current_user)):
    s = await db.global_settings.find_one({"type": "player"}, {"_id": 0})
    if not s:
        return _DEFAULT_PLAYER
    return {k: v for k, v in s.items() if k != "type"}


@router.patch("/settings/player")
async def update_player_settings(settings: PlayerSettings, current_user: User = Depends(require_admin)):
    update = settings.model_dump()
    update["type"] = "player"
    await db.global_settings.update_one({"type": "player"}, {"$set": update}, upsert=True)
    return {"message": "Player settings saved", **settings.model_dump()}
