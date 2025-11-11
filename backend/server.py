from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
import ffmpeg
import json
import shutil
import asyncio
from urllib.parse import urlparse

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create directories for video storage
VIDEO_STORAGE_PATH = ROOT_DIR / "video_storage"
VIDEO_STORAGE_PATH.mkdir(exist_ok=True)
(VIDEO_STORAGE_PATH / "originals").mkdir(exist_ok=True)
(VIDEO_STORAGE_PATH / "thumbnails").mkdir(exist_ok=True)
(VIDEO_STORAGE_PATH / "hls").mkdir(exist_ok=True)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-this')
JWT_ALGORITHM = "HS256"
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    password_hash: str
    must_change_password: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class Folder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    parent_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None

class VideoMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    folder_id: Optional[str] = None
    original_filename: str
    file_path: str
    thumbnail_path: Optional[str] = None
    hls_path: Optional[str] = None
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    aspect_ratio: Optional[str] = None
    file_size: int
    format: Optional[str] = None
    processing_status: str = "pending"  # pending, processing, ready, failed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EmbedSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    video_id: str
    allowed_domains: List[str] = []  # Empty list means all domains allowed
    player_color: str = "#3b82f6"  # Primary color
    show_controls: bool = True
    autoplay: bool = False
    loop: bool = False
    custom_css: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EmbedSettingsCreate(BaseModel):
    video_id: str
    allowed_domains: List[str] = []
    player_color: str = "#3b82f6"
    show_controls: bool = True
    autoplay: bool = False
    loop: bool = False
    custom_css: Optional[str] = None

# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=7)):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        
        user = await db.users.find_one({"username": username}, {"_id": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def initialize_admin_user():
    """Create default admin user if not exists"""
    existing_user = await db.users.find_one({"username": "admin"})
    if not existing_user:
        admin_user = User(
            username="admin",
            password_hash=hash_password("admin123"),
            must_change_password=True
        )
        doc = admin_user.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.users.insert_one(doc)
        logger.info("Default admin user created: admin/admin123")

# Auth endpoints
@api_router.post("/auth/login")
async def login(request: LoginRequest):
    user = await db.users.find_one({"username": request.username}, {"_id": 0})
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "must_change_password": user.get("must_change_password", False)
    }

@api_router.post("/auth/change-password")
async def change_password(request: ChangePasswordRequest, current_user: User = Depends(get_current_user)):
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    new_hash = hash_password(request.new_password)
    await db.users.update_one(
        {"username": current_user.username},
        {"$set": {"password_hash": new_hash, "must_change_password": False}}
    )
    return {"message": "Password changed successfully"}

# Folder endpoints
@api_router.post("/folders", response_model=Folder)
async def create_folder(folder: FolderCreate, current_user: User = Depends(get_current_user)):
    folder_obj = Folder(**folder.model_dump())
    doc = folder_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.folders.insert_one(doc)
    return folder_obj

@api_router.get("/folders", response_model=List[Folder])
async def get_folders(current_user: User = Depends(get_current_user)):
    folders = await db.folders.find({}, {"_id": 0}).to_list(1000)
    for folder in folders:
        if isinstance(folder['created_at'], str):
            folder['created_at'] = datetime.fromisoformat(folder['created_at'])
    return folders

@api_router.delete("/folders/{folder_id}")
async def delete_folder(folder_id: str, current_user: User = Depends(get_current_user)):
    result = await db.folders.delete_one({"id": folder_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Folder not found")
    return {"message": "Folder deleted"}

# Video endpoints
@api_router.post("/videos/upload")
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    folder_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    video_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    original_path = VIDEO_STORAGE_PATH / "originals" / f"{video_id}{file_extension}"
    
    # Save uploaded file
    with open(original_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_size = original_path.stat().st_size
    
    # Create video metadata
    video = VideoMetadata(
        id=video_id,
        title=title,
        description=description,
        folder_id=folder_id,
        original_filename=file.filename,
        file_path=str(original_path),
        file_size=file_size,
        processing_status="pending"
    )
    
    doc = video.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.videos.insert_one(doc)
    
    # Process video in background
    asyncio.create_task(process_video(video_id))
    
    return {"video_id": video_id, "message": "Video uploaded and processing started"}

async def process_video(video_id: str):
    """Process video: extract metadata, generate thumbnail, create HLS stream"""
    try:
        await db.videos.update_one({"id": video_id}, {"$set": {"processing_status": "processing"}})
        
        video = await db.videos.find_one({"id": video_id}, {"_id": 0})
        if not video:
            return
        
        file_path = video["file_path"]
        
        # Extract video metadata
        probe = ffmpeg.probe(file_path)
        video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
        
        if video_stream:
            width = video_stream.get('width')
            height = video_stream.get('height')
            duration = float(probe['format'].get('duration', 0))
            format_name = probe['format'].get('format_name')
            
            # Calculate aspect ratio
            if width and height:
                from math import gcd
                g = gcd(width, height)
                aspect_ratio = f"{width//g}:{height//g}"
            else:
                aspect_ratio = "16:9"
            
            # Generate thumbnail at 10% of video duration
            thumbnail_time = min(duration * 0.1, 5)  # Max 5 seconds in
            thumbnail_path = VIDEO_STORAGE_PATH / "thumbnails" / f"{video_id}.jpg"
            
            (
                ffmpeg
                .input(file_path, ss=thumbnail_time)
                .filter('scale', 1280, -1)
                .output(str(thumbnail_path), vframes=1, format='image2', vcodec='mjpeg')
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Generate HLS stream
            hls_dir = VIDEO_STORAGE_PATH / "hls" / video_id
            hls_dir.mkdir(exist_ok=True)
            hls_playlist = hls_dir / "playlist.m3u8"
            
            (
                ffmpeg
                .input(file_path)
                .output(
                    str(hls_playlist),
                    format='hls',
                    start_number=0,
                    hls_time=10,
                    hls_list_size=0,
                    hls_segment_filename=str(hls_dir / 'segment_%03d.ts')
                )
                .overwrite_output()
                .run(quiet=True)
            )
            
            # Update video metadata
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
                    "processing_status": "ready"
                }}
            )
    except Exception as e:
        logger.error(f"Error processing video {video_id}: {str(e)}")
        await db.videos.update_one(
            {"id": video_id},
            {"$set": {"processing_status": "failed"}}
        )

@api_router.get("/videos", response_model=List[VideoMetadata])
async def get_videos(folder_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"folder_id": folder_id} if folder_id else {}
    videos = await db.videos.find(query, {"_id": 0}).to_list(1000)
    
    for video in videos:
        if isinstance(video['created_at'], str):
            video['created_at'] = datetime.fromisoformat(video['created_at'])
    
    return videos

@api_router.get("/videos/{video_id}", response_model=VideoMetadata)
async def get_video(video_id: str, current_user: User = Depends(get_current_user)):
    video = await db.videos.find_one({"id": video_id}, {"_id": 0})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if isinstance(video['created_at'], str):
        video['created_at'] = datetime.fromisoformat(video['created_at'])
    
    return VideoMetadata(**video)

@api_router.delete("/videos/{video_id}")
async def delete_video(video_id: str, current_user: User = Depends(get_current_user)):
    video = await db.videos.find_one({"id": video_id}, {"_id": 0})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Delete files
    if video.get('file_path') and Path(video['file_path']).exists():
        Path(video['file_path']).unlink()
    if video.get('thumbnail_path') and Path(video['thumbnail_path']).exists():
        Path(video['thumbnail_path']).unlink()
    if video.get('hls_path'):
        hls_dir = Path(video['hls_path']).parent
        if hls_dir.exists():
            shutil.rmtree(hls_dir)
    
    # Delete from database
    await db.videos.delete_one({"id": video_id})
    await db.embed_settings.delete_many({"video_id": video_id})
    
    return {"message": "Video deleted"}

@api_router.patch("/videos/{video_id}")
async def update_video(
    video_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    folder_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    update_data = {}
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if folder_id is not None:
        update_data["folder_id"] = folder_id
    
    if update_data:
        result = await db.videos.update_one({"id": video_id}, {"$set": update_data})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Video not found")
    
    return {"message": "Video updated"}

# Streaming endpoints
@api_router.get("/stream/thumbnail/{video_id}")
async def stream_thumbnail(video_id: str):
    video = await db.videos.find_one({"id": video_id}, {"_id": 0})
    if not video or not video.get('thumbnail_path'):
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    thumbnail_path = Path(video['thumbnail_path'])
    if not thumbnail_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail file not found")
    
    return FileResponse(thumbnail_path, media_type="image/jpeg")

@api_router.get("/stream/hls/{video_id}/playlist.m3u8")
async def stream_hls_playlist(video_id: str, request: Request):
    # Check domain restrictions
    referer = request.headers.get("referer", "")
    if referer:
        embed_settings = await db.embed_settings.find_one({"video_id": video_id}, {"_id": 0})
        if embed_settings and embed_settings.get('allowed_domains'):
            allowed = embed_settings['allowed_domains']
            domain = urlparse(referer).netloc
            if domain and not any(d in domain for d in allowed):
                raise HTTPException(status_code=403, detail="Domain not allowed")
    
    video = await db.videos.find_one({"id": video_id}, {"_id": 0})
    if not video or not video.get('hls_path'):
        raise HTTPException(status_code=404, detail="Video not ready")
    
    playlist_path = Path(video['hls_path'])
    if not playlist_path.exists():
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    return FileResponse(playlist_path, media_type="application/vnd.apple.mpegurl")

@api_router.get("/stream/hls/{video_id}/{segment}")
async def stream_hls_segment(video_id: str, segment: str):
    video = await db.videos.find_one({"id": video_id}, {"_id": 0})
    if not video or not video.get('hls_path'):
        raise HTTPException(status_code=404, detail="Video not ready")
    
    segment_path = Path(video['hls_path']).parent / segment
    if not segment_path.exists():
        raise HTTPException(status_code=404, detail="Segment not found")
    
    return FileResponse(segment_path, media_type="video/mp2t")

# Embed settings endpoints
@api_router.post("/embed-settings", response_model=EmbedSettings)
async def create_embed_settings(
    settings: EmbedSettingsCreate,
    current_user: User = Depends(get_current_user)
):
    # Check if settings already exist
    existing = await db.embed_settings.find_one({"video_id": settings.video_id}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Embed settings already exist for this video")
    
    embed_obj = EmbedSettings(**settings.model_dump())
    doc = embed_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.embed_settings.insert_one(doc)
    return embed_obj

@api_router.get("/embed-settings/{video_id}", response_model=EmbedSettings)
async def get_embed_settings(video_id: str, current_user: User = Depends(get_current_user)):
    settings = await db.embed_settings.find_one({"video_id": video_id}, {"_id": 0})
    if not settings:
        raise HTTPException(status_code=404, detail="Embed settings not found")
    
    if isinstance(settings['created_at'], str):
        settings['created_at'] = datetime.fromisoformat(settings['created_at'])
    if isinstance(settings['updated_at'], str):
        settings['updated_at'] = datetime.fromisoformat(settings['updated_at'])
    
    return EmbedSettings(**settings)

@api_router.patch("/embed-settings/{video_id}")
async def update_embed_settings(
    video_id: str,
    allowed_domains: Optional[List[str]] = None,
    player_color: Optional[str] = None,
    show_controls: Optional[bool] = None,
    autoplay: Optional[bool] = None,
    loop: Optional[bool] = None,
    custom_css: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if allowed_domains is not None:
        update_data["allowed_domains"] = allowed_domains
    if player_color is not None:
        update_data["player_color"] = player_color
    if show_controls is not None:
        update_data["show_controls"] = show_controls
    if autoplay is not None:
        update_data["autoplay"] = autoplay
    if loop is not None:
        update_data["loop"] = loop
    if custom_css is not None:
        update_data["custom_css"] = custom_css
    
    result = await db.embed_settings.update_one({"video_id": video_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Embed settings not found")
    
    return {"message": "Embed settings updated"}

@api_router.get("/embed-code/{video_id}")
async def get_embed_code(video_id: str, current_user: User = Depends(get_current_user)):
    video = await db.videos.find_one({"id": video_id}, {"_id": 0})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    backend_url = os.environ.get('BACKEND_URL', 'http://localhost:8001')
    embed_settings = await db.embed_settings.find_one({"video_id": video_id}, {"_id": 0})
    
    player_color = "#3b82f6"
    show_controls = True
    autoplay = False
    loop = False
    
    if embed_settings:
        player_color = embed_settings.get('player_color', player_color)
        show_controls = embed_settings.get('show_controls', show_controls)
        autoplay = embed_settings.get('autoplay', autoplay)
        loop = embed_settings.get('loop', loop)
    
    embed_code = f'''<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
  <video id="video-{video_id}" 
         style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
         {"controls" if show_controls else ""}
         {"autoplay" if autoplay else ""}
         {"loop" if loop else ""}>
    <source src="{backend_url}/api/stream/hls/{video_id}/playlist.m3u8" type="application/x-mpegURL">
    Your browser does not support the video tag.
  </video>
</div>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
<script>
  var video = document.getElementById('video-{video_id}');
  if (Hls.isSupported()) {{
    var hls = new Hls();
    hls.loadSource('{backend_url}/api/stream/hls/{video_id}/playlist.m3u8');
    hls.attachMedia(video);
  }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
    video.src = '{backend_url}/api/stream/hls/{video_id}/playlist.m3u8';
  }}
</script>'''
    
    return {"embed_code": embed_code}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await initialize_admin_user()
    logger.info("Video hosting service started")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
