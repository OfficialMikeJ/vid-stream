"""Auth routes: login and change-password."""
from fastapi import APIRouter, HTTPException, Depends, Request

from database import db
from models import LoginRequest, ChangePasswordRequest, User
from security import verify_password, hash_password, create_access_token, get_current_user
from rate_limit import limiter, LIMIT_LOGIN, LIMIT_PASSWORD

router = APIRouter(prefix="/api")


@router.post("/auth/login")
@limiter.limit(LIMIT_LOGIN)
async def login(request: Request, body: LoginRequest):
    user = await db.users.find_one({"username": body.username}, {"_id": 0})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account is deactivated")
    token = create_access_token(data={"sub": user["username"], "role": user.get("role", "admin")})
    return {
        "access_token": token,
        "token_type": "bearer",
        "must_change_password": user.get("must_change_password", False),
        "role": user.get("role", "admin"),
        "username": user["username"],
    }


@router.post("/auth/change-password")
@limiter.limit(LIMIT_PASSWORD)
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
):
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    new_hash = hash_password(body.new_password)
    await db.users.update_one(
        {"username": current_user.username},
        {"$set": {"password_hash": new_hash, "must_change_password": False}},
    )
    return {"message": "Password changed successfully"}
