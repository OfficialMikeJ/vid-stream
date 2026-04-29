"""Video comments — authenticated users post; admins moderate."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from database import db
from models import User
from security import get_current_user, require_admin

router = APIRouter(prefix="/api")


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


@router.get("/videos/{video_id}/comments")
async def list_comments(video_id: str, current_user: User = Depends(get_current_user)):
    """List all comments for a video, newest first."""
    video = await db.videos.find_one({"id": video_id}, {"_id": 0, "id": 1})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    items = await db.comments.find(
        {"video_id": video_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    return {"video_id": video_id, "count": len(items), "items": items}


@router.post("/videos/{video_id}/comments")
async def add_comment(
    video_id: str,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
):
    """Both admin and viewer roles can post comments."""
    video = await db.videos.find_one({"id": video_id}, {"_id": 0, "id": 1})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    body = payload.body.strip()
    if not body:
        raise HTTPException(status_code=400, detail="Comment cannot be empty")

    doc = {
        "id": str(uuid.uuid4()),
        "video_id": video_id,
        "username": current_user.username,
        "user_role": current_user.role,
        "body": body,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.comments.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.delete("/videos/{video_id}/comments/{comment_id}")
async def delete_comment(
    video_id: str,
    comment_id: str,
    current_user: User = Depends(get_current_user),
):
    """Admins can delete any comment. Viewers can only delete their own."""
    comment = await db.comments.find_one({"id": comment_id, "video_id": video_id}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if current_user.role != "admin" and comment["username"] != current_user.username:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")

    await db.comments.delete_one({"id": comment_id})
    return {"message": "Comment deleted"}


# ── Admin moderation ─────────────────────────────────────────────────────────

@router.get("/comments")
async def list_all_comments(
    limit: int = 100,
    current_user: User = Depends(require_admin),
):
    """Admin-only: list comments across all videos for moderation."""
    items = await db.comments.find({}, {"_id": 0}).sort("created_at", -1).to_list(min(limit, 500))
    # Hydrate video titles
    if items:
        ids = list({c["video_id"] for c in items})
        videos = await db.videos.find(
            {"id": {"$in": ids}},
            {"_id": 0, "id": 1, "title": 1},
        ).to_list(len(ids))
        title_map = {v["id"]: v["title"] for v in videos}
        for c in items:
            c["video_title"] = title_map.get(c["video_id"], "Deleted video")
    return {"count": len(items), "items": items}
