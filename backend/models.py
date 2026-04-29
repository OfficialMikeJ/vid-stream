"""All Pydantic data models."""
import uuid
import secrets
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone


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
    processing_status: str = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmbedSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    video_id: str
    allowed_domains: List[str] = []
    player_color: str = "#3b82f6"
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


class MeshNode(BaseModel):
    model_config = ConfigDict(extra="ignore")
    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    url: str
    api_key: str
    status: str = "unknown"
    last_seen: Optional[str] = None
    storage_total_gb: Optional[float] = None
    storage_used_gb: Optional[float] = None
    video_count: Optional[int] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MeshNodeCreate(BaseModel):
    name: str
    url: str
    api_key: str


class PlayLabSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    api_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    enabled: bool = True
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
