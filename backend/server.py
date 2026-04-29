"""StreamHost API — application entry point."""
import os
import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from database import client, db
from security import hash_password
from models import User

from routes.auth import router as auth_router
from routes.videos import router as videos_router
from routes.upload import router as upload_router
from routes.mesh import router as mesh_router
from routes.playlab import router as playlab_router
from routes.users import router as users_router
from routes.analytics import router as analytics_router
from routes.comments import router as comments_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="StreamHost API", version="2025.12.17")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(videos_router)
app.include_router(upload_router)
app.include_router(mesh_router)
app.include_router(playlab_router)
app.include_router(users_router)
app.include_router(analytics_router)
app.include_router(comments_router)


async def initialize_admin_user():
    """Ensure the default admin account exists — self-healing on every startup."""
    try:
        existing = await db.users.find_one({"username": "StreamHost"})
        if not existing:
            admin = User(
                username="StreamHost",
                password_hash=hash_password("password1234!@#"),
                role="admin",
                is_active=True,
                must_change_password=True,
            )
            doc = admin.model_dump()
            doc["created_at"] = doc["created_at"].isoformat()
            await db.users.insert_one(doc)
            logger.info("Default admin user created: StreamHost")
        else:
            # Backfill new fields for legacy documents that predate multi-user support
            backfill = {}
            if "role" not in existing:
                backfill["role"] = "admin"
            if "is_active" not in existing:
                backfill["is_active"] = True
            if backfill:
                await db.users.update_one({"username": "StreamHost"}, {"$set": backfill})
                logger.info(f"Backfilled admin user fields: {list(backfill.keys())}")
            logger.info(f"Admin user exists: {existing.get('id', 'unknown')}")
    except Exception as e:
        logger.error(f"Error during admin init: {e}")
        try:
            admin = User(
                username="StreamHost",
                password_hash=hash_password("password1234!@#"),
                role="admin",
                is_active=True,
                must_change_password=True,
            )
            doc = admin.model_dump()
            doc["created_at"] = doc["created_at"].isoformat()
            await db.users.insert_one(doc)
            logger.info("Admin user recreated after error")
        except Exception as inner:
            logger.error(f"Failed to recreate admin user: {inner}")


@app.on_event("startup")
async def startup_event():
    await initialize_admin_user()
    logger.info("StreamHost video hosting service started")


@app.on_event("shutdown")
async def shutdown_event():
    client.close()
