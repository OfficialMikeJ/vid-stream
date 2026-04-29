"""Public sharing links — generate short tokenized URLs that bypass auth.

Each link points at a single video. Optional expiration (ISO timestamp) and
password protection. Visiting /api/share/{token} returns the video metadata
and HLS URL the player needs.
"""
import uuid
import secrets
import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from database import db
from models import User
from security import require_admin

router = APIRouter(prefix="/api")


class ShareLinkCreate(BaseModel):
    expires_at: Optional[str] = None  # ISO 8601 string
    password: Optional[str] = None
    label: Optional[str] = None


def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _is_expired(link: dict) -> bool:
    exp = link.get("expires_at")
    if not exp:
        return False
    try:
        return datetime.fromisoformat(exp) < datetime.now(timezone.utc)
    except Exception:
        return False


@router.post("/videos/{video_id}/share")
async def create_share_link(
    video_id: str,
    payload: ShareLinkCreate,
    current_user: User = Depends(require_admin),
):
    """Generate a new sharing link for a video."""
    video = await db.videos.find_one({"id": video_id}, {"_id": 0, "id": 1, "title": 1})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Validate expires_at if provided
    if payload.expires_at:
        try:
            datetime.fromisoformat(payload.expires_at)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expires_at — use ISO 8601 format")

    token = secrets.token_urlsafe(16)  # 22-character URL-safe token
    doc = {
        "id": str(uuid.uuid4()),
        "token": token,
        "video_id": video_id,
        "label": payload.label,
        "expires_at": payload.expires_at,
        "password_hash": _hash_password(payload.password) if payload.password else None,
        "view_count": 0,
        "created_by": current_user.username,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.share_links.insert_one(doc)
    doc.pop("_id", None)
    doc.pop("password_hash", None)
    doc["has_password"] = bool(payload.password)
    return doc


@router.get("/videos/{video_id}/share")
async def list_share_links(
    video_id: str, current_user: User = Depends(require_admin)
):
    """List all share links for a given video."""
    items = await db.share_links.find(
        {"video_id": video_id},
        {"_id": 0, "password_hash": 0},
    ).sort("created_at", -1).to_list(100)
    # Add has_password flag without leaking the hash
    raw = await db.share_links.find({"video_id": video_id}, {"_id": 0, "token": 1, "password_hash": 1}).to_list(100)
    pw_map = {r["token"]: bool(r.get("password_hash")) for r in raw}
    for it in items:
        it["has_password"] = pw_map.get(it["token"], False)
    return {"video_id": video_id, "count": len(items), "items": items}


@router.delete("/share/{token}")
async def revoke_share_link(token: str, current_user: User = Depends(require_admin)):
    """Revoke (delete) a share link."""
    result = await db.share_links.delete_one({"token": token})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Share link not found")
    return {"message": "Share link revoked"}


# ── Public endpoints ─────────────────────────────────────────────────────────

@router.get("/share/{token}")
async def resolve_share_link(token: str, password: Optional[str] = None):
    """Public: resolve a share token to a playable video.

    If the link is password-protected, the caller MUST pass `password`.
    On success, returns video metadata + HLS URL + caption tracks.
    """
    link = await db.share_links.find_one({"token": token}, {"_id": 0})
    if not link:
        raise HTTPException(status_code=404, detail="Share link not found")
    if _is_expired(link):
        raise HTTPException(status_code=410, detail="Share link has expired")

    if link.get("password_hash"):
        if not password:
            # Tell the caller a password is required without revealing the video
            return {"requires_password": True, "label": link.get("label")}
        if _hash_password(password) != link["password_hash"]:
            raise HTTPException(status_code=401, detail="Incorrect password")

    video = await db.videos.find_one(
        {"id": link["video_id"]},
        {"_id": 0, "id": 1, "title": 1, "description": 1, "duration": 1,
         "aspect_ratio": 1, "processing_status": 1, "thumbnail_path": 1, "thumbnail_url": 1},
    )
    if not video:
        raise HTTPException(status_code=404, detail="Video no longer available")

    # Increment view count
    await db.share_links.update_one({"token": token}, {"$inc": {"view_count": 1}})

    # Captions for the player
    caps = await db.captions.find(
        {"video_id": link["video_id"]},
        {"_id": 0, "id": 1, "language": 1, "label": 1, "is_default": 1},
    ).to_list(50)

    return {
        "requires_password": False,
        "video": video,
        "hls_url": f"/api/stream/hls/{link['video_id']}/playlist.m3u8",
        "thumbnail_url": f"/api/stream/thumbnail/{link['video_id']}",
        "captions": caps,
        "label": link.get("label"),
    }
