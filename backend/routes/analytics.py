"""Analytics endpoints — video views, watch metrics, and aggregated dashboard data."""
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from database import db
from models import User
from security import get_current_user, require_admin

router = APIRouter(prefix="/api/analytics")


def _hash_visitor(ip: str, user_agent: str) -> str:
    """Anonymized visitor identifier — protects PII while still de-duplicating views."""
    return hashlib.sha256(f"{ip}|{user_agent}".encode()).hexdigest()[:16]


async def record_view(video_id: str, request: Request) -> None:
    """Record a video view. De-dupes per visitor within a 30-minute rolling window."""
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    visitor = _hash_visitor(ip, ua)

    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
    recent = await db.video_views.find_one({
        "video_id": video_id,
        "visitor": visitor,
        "timestamp": {"$gt": cutoff},
    })
    if recent:
        return  # Already counted this visitor recently

    await db.video_views.insert_one({
        "video_id": video_id,
        "visitor": visitor,
        "referrer": request.headers.get("referer", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@router.get("/overview")
async def overview(current_user: User = Depends(require_admin)):
    """High-level stats for dashboard cards."""
    total_videos = await db.videos.count_documents({})
    ready_videos = await db.videos.count_documents({"processing_status": "ready"})
    total_views = await db.video_views.count_documents({})

    # Total storage used (sum of file_size)
    storage_pipeline = [{"$group": {"_id": None, "bytes": {"$sum": "$file_size"}}}]
    storage_result = await db.videos.aggregate(storage_pipeline).to_list(1)
    storage_bytes = storage_result[0]["bytes"] if storage_result else 0

    # Total duration (watch capacity)
    duration_pipeline = [{"$group": {"_id": None, "secs": {"$sum": "$duration"}}}]
    dur_result = await db.videos.aggregate(duration_pipeline).to_list(1)
    total_duration = dur_result[0]["secs"] if dur_result else 0

    # Unique viewers across all videos
    unique = await db.video_views.distinct("visitor")

    # Views in last 24 hours
    cutoff_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    views_24h = await db.video_views.count_documents({"timestamp": {"$gt": cutoff_24h}})

    return {
        "total_videos": total_videos,
        "ready_videos": ready_videos,
        "total_views": total_views,
        "unique_viewers": len(unique),
        "views_24h": views_24h,
        "storage_bytes": storage_bytes,
        "total_duration_seconds": total_duration,
    }


@router.get("/timeline")
async def timeline(days: int = 30, current_user: User = Depends(require_admin)):
    """Daily view counts for the last N days."""
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="days must be 1..365")

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    pipeline = [
        {"$match": {"timestamp": {"$gt": cutoff}}},
        {"$group": {
            "_id": {"$substr": ["$timestamp", 0, 10]},
            "views": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    rows = await db.video_views.aggregate(pipeline).to_list(days + 5)

    # Build a continuous daily series (fill missing days with 0)
    by_date = {row["_id"]: row["views"] for row in rows}
    today = datetime.now(timezone.utc).date()
    series = []
    for offset in range(days - 1, -1, -1):
        d = (today - timedelta(days=offset)).isoformat()
        series.append({"date": d, "views": by_date.get(d, 0)})
    return {"days": days, "series": series}


@router.get("/videos")
async def per_video_stats(
    limit: int = 50,
    sort: str = "views",
    current_user: User = Depends(require_admin),
):
    """Per-video stats: views, unique viewers, last viewed."""
    if sort not in ("views", "unique", "recent"):
        sort = "views"

    pipeline = [
        {"$group": {
            "_id": "$video_id",
            "views": {"$sum": 1},
            "unique_visitors": {"$addToSet": "$visitor"},
            "last_viewed": {"$max": "$timestamp"},
        }},
        {"$project": {
            "video_id": "$_id",
            "_id": 0,
            "views": 1,
            "unique_viewers": {"$size": "$unique_visitors"},
            "last_viewed": 1,
        }},
    ]
    sort_key = {"views": "views", "unique": "unique_viewers", "recent": "last_viewed"}[sort]
    pipeline.append({"$sort": {sort_key: -1}})
    pipeline.append({"$limit": max(1, min(limit, 200))})

    stats = await db.video_views.aggregate(pipeline).to_list(limit)

    # Hydrate with video titles
    if stats:
        ids = [s["video_id"] for s in stats]
        videos = await db.videos.find(
            {"id": {"$in": ids}},
            {"_id": 0, "id": 1, "title": 1, "duration": 1, "processing_status": 1},
        ).to_list(len(ids))
        title_map = {v["id"]: v for v in videos}
        for s in stats:
            v = title_map.get(s["video_id"], {})
            s["title"] = v.get("title", "Deleted video")
            s["duration"] = v.get("duration")
            s["processing_status"] = v.get("processing_status")

    return {"sort": sort, "items": stats}


@router.get("/video/{video_id}")
async def single_video_stats(video_id: str, current_user: User = Depends(get_current_user)):
    """Stats for one specific video — admins and viewers may see this."""
    video = await db.videos.find_one({"id": video_id}, {"_id": 0, "title": 1, "id": 1})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    total = await db.video_views.count_documents({"video_id": video_id})
    unique = await db.video_views.distinct("visitor", {"video_id": video_id})
    cutoff_7d = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    last_7d = await db.video_views.count_documents({
        "video_id": video_id,
        "timestamp": {"$gt": cutoff_7d},
    })
    last = await db.video_views.find_one(
        {"video_id": video_id},
        {"_id": 0, "timestamp": 1},
        sort=[("timestamp", -1)],
    )
    return {
        "video_id": video_id,
        "title": video.get("title"),
        "total_views": total,
        "unique_viewers": len(unique),
        "views_last_7d": last_7d,
        "last_viewed": last["timestamp"] if last else None,
    }
