"""Background services: video processing and PlayLab webhook delivery."""
import os
import json
import hmac
import hashlib
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from math import gcd

import ffmpeg
import httpx

from database import db, VIDEO_STORAGE_PATH

logger = logging.getLogger(__name__)


async def process_video(video_id: str) -> None:
    """Process a video: extract metadata, generate thumbnail, create HLS stream."""
    try:
        await db.videos.update_one({"id": video_id}, {"$set": {"processing_status": "processing"}})

        video = await db.videos.find_one({"id": video_id}, {"_id": 0})
        if not video:
            return

        file_path = video["file_path"]
        probe = ffmpeg.probe(file_path)
        video_stream = next((s for s in probe["streams"] if s["codec_type"] == "video"), None)

        if video_stream:
            width = video_stream.get("width")
            height = video_stream.get("height")
            duration = float(probe["format"].get("duration", 0))
            format_name = probe["format"].get("format_name")

            if width and height:
                g = gcd(width, height)
                aspect_ratio = f"{width // g}:{height // g}"
            else:
                aspect_ratio = "16:9"

            thumbnail_time = min(duration * 0.1, 5)
            thumbnail_path = VIDEO_STORAGE_PATH / "thumbnails" / f"{video_id}.jpg"

            (
                ffmpeg
                .input(file_path, ss=thumbnail_time)
                .filter("scale", 1280, -1)
                .output(str(thumbnail_path), vframes=1, format="image2", vcodec="mjpeg")
                .overwrite_output()
                .run(quiet=True)
            )

            hls_dir = VIDEO_STORAGE_PATH / "hls" / video_id
            hls_dir.mkdir(exist_ok=True)
            hls_playlist = hls_dir / "playlist.m3u8"

            (
                ffmpeg
                .input(file_path)
                .output(
                    str(hls_playlist),
                    format="hls",
                    start_number=0,
                    hls_time=10,
                    hls_list_size=0,
                    hls_segment_filename=str(hls_dir / "segment_%03d.ts"),
                )
                .overwrite_output()
                .run(quiet=True)
            )

            await db.videos.update_one(
                {"id": video_id},
                {"$set": {
                    "width": width,
                    "height": height,
                    "duration": duration,
                    "aspect_ratio": aspect_ratio,
                    "format": format_name,
                    "thumbnail_path": str(thumbnail_path),
                    "hls_path": str(hls_playlist),
                    "processing_status": "ready",
                }},
            )

            # Fire PlayLab webhook (non-blocking — errors are logged, not raised)
            asyncio.create_task(_trigger_playlab_webhook(video_id))

    except Exception as e:
        logger.error(f"Error processing video {video_id}: {e}")
        await db.videos.update_one(
            {"id": video_id}, {"$set": {"processing_status": "failed"}}
        )


async def _trigger_playlab_webhook(video_id: str) -> None:
    """POST video-ready payload to the configured PlayLab webhook URL."""
    settings = await db.playlab_settings.find_one({}, {"_id": 0})
    if not settings or not settings.get("enabled") or not settings.get("webhook_url"):
        return

    video = await db.videos.find_one({"id": video_id}, {"_id": 0})
    if not video or video.get("processing_status") != "ready":
        return

    backend_url = os.environ.get("BACKEND_URL", "http://localhost:8001")
    hls_url = f"{backend_url}/api/stream/hls/{video_id}/playlist.m3u8"

    payload = {
        "event": "video.ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "video": {
            "id": video["id"],
            "title": video["title"],
            "description": video.get("description"),
            "duration": video.get("duration"),
            "hls_url": hls_url,
            "thumbnail_url": f"{backend_url}/api/stream/thumbnail/{video_id}",
            "aspect_ratio": video.get("aspect_ratio"),
            "width": video.get("width"),
            "height": video.get("height"),
            "playlab_server_type": 2,
            "seven_twenty_video": hls_url,
            "server_seven_twenty": 2,
        },
    }

    headers = {"Content-Type": "application/json"}
    raw_body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    if settings.get("webhook_secret"):
        sig = hmac.new(
            settings["webhook_secret"].encode(), raw_body, hashlib.sha256
        ).hexdigest()
        headers["X-StreamHost-Signature"] = f"sha256={sig}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(settings["webhook_url"], content=raw_body, headers=headers)
            logger.info(f"PlayLab webhook sent for {video_id}: HTTP {resp.status_code}")
    except Exception as e:
        logger.error(f"PlayLab webhook failed for {video_id}: {e}")
