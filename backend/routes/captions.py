"""Caption / subtitle endpoints — upload WebVTT tracks, list, fetch, delete."""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse

from database import db, VIDEO_STORAGE_PATH
from models import User
from security import get_current_user, require_admin

router = APIRouter(prefix="/api")

CAPTIONS_DIR = VIDEO_STORAGE_PATH / "captions"
CAPTIONS_DIR.mkdir(exist_ok=True)


def _is_valid_vtt(text: str) -> bool:
    """A minimal sanity check — WebVTT files start with the 'WEBVTT' signature."""
    return text.lstrip().upper().startswith("WEBVTT")


def _srt_to_vtt(text: str) -> str:
    """Convert SubRip (.srt) to WebVTT — replaces ',' with '.' in timestamps."""
    lines = text.replace("\r\n", "\n").split("\n")
    out = ["WEBVTT", ""]
    for line in lines:
        # Replace decimal commas in cue timing lines
        if "-->" in line:
            line = line.replace(",", ".")
        # Skip pure-numeric SRT cue index lines
        if line.strip().isdigit():
            continue
        out.append(line)
    return "\n".join(out)


@router.get("/videos/{video_id}/captions")
async def list_captions(video_id: str, current_user: User = Depends(get_current_user)):
    """List all caption tracks for a video."""
    video = await db.videos.find_one({"id": video_id}, {"_id": 0, "id": 1})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    items = await db.captions.find(
        {"video_id": video_id}, {"_id": 0, "file_path": 0}
    ).sort("created_at", 1).to_list(50)
    return {"video_id": video_id, "count": len(items), "items": items}


@router.post("/videos/{video_id}/captions")
async def upload_caption(
    video_id: str,
    file: UploadFile = File(...),
    language: str = Form(...),
    label: Optional[str] = Form(None),
    is_default: bool = Form(False),
    current_user: User = Depends(require_admin),
):
    """Upload a caption track. Supports .vtt natively and converts .srt automatically."""
    video = await db.videos.find_one({"id": video_id}, {"_id": 0, "id": 1})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if not language or len(language) > 10:
        raise HTTPException(status_code=400, detail="Language code is required (e.g., 'en', 'fr')")

    raw = (await file.read()).decode("utf-8", errors="replace")
    suffix = Path(file.filename or "").suffix.lower()

    if suffix == ".srt" or (not _is_valid_vtt(raw) and "-->" in raw):
        vtt_content = _srt_to_vtt(raw)
    elif _is_valid_vtt(raw):
        vtt_content = raw
    else:
        raise HTTPException(status_code=400, detail="Unsupported caption format. Upload a .vtt or .srt file.")

    caption_id = str(uuid.uuid4())
    out_path = CAPTIONS_DIR / f"{caption_id}.vtt"
    out_path.write_text(vtt_content, encoding="utf-8")

    # If this caption is set as default, unset any existing default for the same video
    if is_default:
        await db.captions.update_many(
            {"video_id": video_id, "is_default": True},
            {"$set": {"is_default": False}},
        )

    doc = {
        "id": caption_id,
        "video_id": video_id,
        "language": language.lower(),
        "label": label or language.upper(),
        "is_default": bool(is_default),
        "file_path": str(out_path),
        "size_bytes": out_path.stat().st_size,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.captions.insert_one(doc)
    public = {k: v for k, v in doc.items() if k not in ("file_path", "_id")}
    return public


@router.get("/captions/{caption_id}")
async def fetch_caption(caption_id: str):
    """Public — needs to be accessible to the <track> element which can't carry auth headers."""
    caption = await db.captions.find_one({"id": caption_id}, {"_id": 0})
    if not caption:
        raise HTTPException(status_code=404, detail="Caption not found")
    path = Path(caption["file_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Caption file missing on disk")
    return FileResponse(
        path,
        media_type="text/vtt",
        headers={"Access-Control-Allow-Origin": "*"},
    )


@router.delete("/videos/{video_id}/captions/{caption_id}")
async def delete_caption(
    video_id: str,
    caption_id: str,
    current_user: User = Depends(require_admin),
):
    caption = await db.captions.find_one({"id": caption_id, "video_id": video_id}, {"_id": 0})
    if not caption:
        raise HTTPException(status_code=404, detail="Caption not found")
    path = Path(caption["file_path"])
    if path.exists():
        path.unlink()
    await db.captions.delete_one({"id": caption_id})
    return {"message": "Caption deleted"}
