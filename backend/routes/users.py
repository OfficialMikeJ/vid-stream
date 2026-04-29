"""User management routes (admin only)."""
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, HTTPException, Depends

from database import db
from models import User, CreateUserRequest
from security import hash_password, require_admin

router = APIRouter(prefix="/api")


@router.get("/users")
async def list_users(current_user: User = Depends(require_admin)):
    """List all users (admin only)."""
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(200)
    for u in users:
        if isinstance(u.get("created_at"), datetime):
            u["created_at"] = u["created_at"].isoformat()
    return users


@router.post("/users")
async def create_user(request: CreateUserRequest, current_user: User = Depends(require_admin)):
    """Create a new user (admin only)."""
    existing = await db.users.find_one({"username": request.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    if request.role not in ("admin", "viewer"):
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'viewer'")

    from uuid import uuid4
    doc = {
        "id": str(uuid4()),
        "username": request.username,
        "password_hash": hash_password(request.password),
        "role": request.role,
        "is_active": True,
        "must_change_password": request.must_change_password,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(doc)
    doc.pop("_id", None)
    doc.pop("password_hash", None)
    return doc


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    role: str = None,
    is_active: bool = None,
    must_change_password: bool = None,
    new_password: str = None,
    current_user: User = Depends(require_admin),
):
    """Update a user's role, active status, or password (admin only)."""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Prevent admin from deactivating themselves
    if user["username"] == current_user.username and is_active is False:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    update = {}
    if role is not None:
        if role not in ("admin", "viewer"):
            raise HTTPException(status_code=400, detail="Role must be 'admin' or 'viewer'")
        update["role"] = role
    if is_active is not None:
        update["is_active"] = is_active
    if must_change_password is not None:
        update["must_change_password"] = must_change_password
    if new_password:
        update["password_hash"] = hash_password(new_password)

    if update:
        await db.users.update_one({"id": user_id}, {"$set": update})
    return {"message": "User updated"}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(require_admin)):
    """Delete a user (admin only). Cannot delete yourself."""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["username"] == current_user.username:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    await db.users.delete_one({"id": user_id})
    return {"message": "User deleted"}
