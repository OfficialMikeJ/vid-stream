"""Chunked upload routes with resume support."""
import shutil
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
import asyncio

from database import db, VIDEO_STORAGE_PATH
from models import VideoMetadata, User
from security import get_current_user, require_admin
from services import process_video

router = APIRouter(prefix="/api")


@router.post("/upload/init")
async def init_chunked_upload(
    filename: str = Form(...),
    title: str = Form(...),
    total_size: int = Form(...),
    description: str = Form(None),
    folder_id: str = Form(None),
    current_user: User = Depends(require_admin),
):
    """Initialize a chunked upload session. Returns upload_id and video_id."""
    from uuid import uuid4
    upload_id = str(uuid4())
    video_id = str(uuid4())

    temp_dir = VIDEO_STORAGE_PATH / "temp" / upload_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    await db.uploads.insert_one({
        "upload_id": upload_id,
        "video_id": video_id,
        "filename": filename,
        "title": title,
        "description": description,
        "folder_id": folder_id,
        "total_size": total_size,
        "chunks_received": [],
        "status": "in_progress",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"upload_id": upload_id, "video_id": video_id}


@router.get("/upload/status/{upload_id}")
async def get_upload_status(
    upload_id: str,
    current_user: User = Depends(get_current_user),
):
    """Return the list of already-received chunks so the client can resume interrupted uploads."""
    meta = await db.uploads.find_one({"upload_id": upload_id}, {"_id": 0})
    if not meta:
        raise HTTPException(status_code=404, detail="Upload session not found")
    return {
        "upload_id": upload_id,
        "status": meta["status"],
        "chunks_received": meta.get("chunks_received", []),
        "total_size": meta.get("total_size"),
        "title": meta.get("title"),
        "filename": meta.get("filename"),
    }


@router.post("/upload/chunk")
async def upload_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    chunk: UploadFile = File(...),
    current_user: User = Depends(require_admin),
):
    """Return the list of already-received chunks so the client can resume interrupted uploads."""
    meta = await db.uploads.find_one({"upload_id": upload_id}, {"_id": 0})
    if not meta:
        raise HTTPException(status_code=404, detail="Upload session not found")
    if meta["status"] != "in_progress":
        raise HTTPException(status_code=400, detail="Upload session is not active")

    temp_dir = VIDEO_STORAGE_PATH / "temp" / upload_id
    chunk_path = temp_dir / f"chunk_{chunk_index:06d}"

    content = await chunk.read()
    with open(chunk_path, "wb") as f:
        f.write(content)

    await db.uploads.update_one(
        {"upload_id": upload_id},
        {"$addToSet": {"chunks_received": chunk_index}},
    )

    meta = await db.uploads.find_one({"upload_id": upload_id}, {"_id": 0})
    chunks_received = meta.get("chunks_received", [])

    if len(chunks_received) >= total_chunks:
        video_id = meta["video_id"]
        filename = meta["filename"]
        file_extension = Path(filename).suffix
        original_path = VIDEO_STORAGE_PATH / "originals" / f"{video_id}{file_extension}"

        with open(original_path, "wb") as output:
            for i in range(total_chunks):
                cf_path = temp_dir / f"chunk_{i:06d}"
                with open(cf_path, "rb") as cf:
                    shutil.copyfileobj(cf, output)

        shutil.rmtree(temp_dir)
        file_size = original_path.stat().st_size

        video = VideoMetadata(
            id=video_id,
            title=meta["title"],
            description=meta.get("description"),
            folder_id=meta.get("folder_id"),
            original_filename=filename,
            file_path=str(original_path),
            file_size=file_size,
            processing_status="pending",
        )
        doc = video.model_dump()
        doc["created_at"] = doc["created_at"].isoformat()
        await db.videos.insert_one(doc)

        await db.uploads.update_one(
            {"upload_id": upload_id}, {"$set": {"status": "complete"}}
        )

        asyncio.create_task(process_video(video_id))

        return {"status": "complete", "video_id": video_id, "message": "Upload complete, processing started"}

    return {
        "status": "in_progress",
        "chunk_index": chunk_index,
        "chunks_received": len(chunks_received),
        "total_chunks": total_chunks,
    }
