"""Storage Mesh routes: register, ping, list, and remove remote StreamHost nodes."""
import shutil
from datetime import datetime, timezone
from typing import Dict, Any

import httpx
from fastapi import APIRouter, HTTPException, Depends

from database import db, VIDEO_STORAGE_PATH
from models import MeshNode, MeshNodeCreate, User
from security import get_current_user

router = APIRouter(prefix="/api")


def _local_storage_stats() -> Dict[str, Any]:
    usage = shutil.disk_usage(VIDEO_STORAGE_PATH)
    return {
        "storage_total_gb": round(usage.total / (1024 ** 3), 2),
        "storage_used_gb": round(usage.used / (1024 ** 3), 2),
        "storage_free_gb": round(usage.free / (1024 ** 3), 2),
        "storage_used_pct": round(usage.used / usage.total * 100, 1),
    }


@router.get("/mesh/status")
async def local_mesh_status():
    """Reports this server's storage and video stats. Used by primary nodes."""
    stats = _local_storage_stats()
    video_count = await db.videos.count_documents({})
    return {"service": "StreamHost", "version": "2025.12.17", "status": "online", "video_count": video_count, **stats}


@router.post("/mesh/nodes")
async def add_mesh_node(node: MeshNodeCreate, current_user: User = Depends(get_current_user)):
    existing = await db.mesh_nodes.find_one({"url": node.url}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="A node with this URL is already registered")

    node_obj = MeshNode(**node.model_dump())

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"{node.url.rstrip('/')}/api/mesh/status",
                headers={"Authorization": f"Bearer {node.api_key}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                node_obj.status = "online"
                node_obj.last_seen = datetime.now(timezone.utc).isoformat()
                node_obj.storage_total_gb = data.get("storage_total_gb")
                node_obj.storage_used_gb = data.get("storage_used_gb")
                node_obj.video_count = data.get("video_count")
            else:
                node_obj.status = "offline"
    except Exception:
        node_obj.status = "offline"

    doc = node_obj.model_dump()
    await db.mesh_nodes.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


@router.get("/mesh/nodes")
async def get_mesh_nodes(current_user: User = Depends(get_current_user)):
    nodes = await db.mesh_nodes.find({}, {"_id": 0}).to_list(100)
    local = _local_storage_stats()
    local_video_count = await db.videos.count_documents({})
    return {
        "local_node": {"name": "This Server (Primary)", "status": "online", "video_count": local_video_count, **local},
        "remote_nodes": nodes,
    }


@router.post("/mesh/nodes/{node_id}/ping")
async def ping_mesh_node(node_id: str, current_user: User = Depends(get_current_user)):
    node = await db.mesh_nodes.find_one({"node_id": node_id}, {"_id": 0})
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    update = {"status": "offline", "last_seen": datetime.now(timezone.utc).isoformat()}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"{node['url'].rstrip('/')}/api/mesh/status",
                headers={"Authorization": f"Bearer {node['api_key']}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                update["status"] = "online"
                update["storage_total_gb"] = data.get("storage_total_gb")
                update["storage_used_gb"] = data.get("storage_used_gb")
                update["video_count"] = data.get("video_count")
    except Exception:
        pass

    await db.mesh_nodes.update_one({"node_id": node_id}, {"$set": update})
    return await db.mesh_nodes.find_one({"node_id": node_id}, {"_id": 0})


@router.delete("/mesh/nodes/{node_id}")
async def remove_mesh_node(node_id: str, current_user: User = Depends(get_current_user)):
    result = await db.mesh_nodes.delete_one({"node_id": node_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"message": "Node removed from mesh pool"}
