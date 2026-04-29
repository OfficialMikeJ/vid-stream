"""Auth routes: login and change-password."""
from fastapi import APIRouter, HTTPException, Depends

from database import db
from models import LoginRequest, ChangePasswordRequest, User
from security import verify_password, hash_password, create_access_token, get_current_user

router = APIRouter(prefix="/api")


@router.post("/auth/login")
async def login(request: LoginRequest):
    user = await db.users.find_one({"username": request.username}, {"_id": 0})
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(data={"sub": user["username"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "must_change_password": user.get("must_change_password", False),
    }


@router.post("/auth/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
):
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    new_hash = hash_password(request.new_password)
    await db.users.update_one(
        {"username": current_user.username},
        {"$set": {"password_hash": new_hash, "must_change_password": False}},
    )
    return {"message": "Password changed successfully"}
