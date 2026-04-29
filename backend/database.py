"""Shared database connection and storage path configuration."""
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]

VIDEO_STORAGE_PATH = ROOT_DIR / "video_storage"
VIDEO_STORAGE_PATH.mkdir(exist_ok=True)
(VIDEO_STORAGE_PATH / "originals").mkdir(exist_ok=True)
(VIDEO_STORAGE_PATH / "thumbnails").mkdir(exist_ok=True)
(VIDEO_STORAGE_PATH / "hls").mkdir(exist_ok=True)
(VIDEO_STORAGE_PATH / "temp").mkdir(exist_ok=True)
