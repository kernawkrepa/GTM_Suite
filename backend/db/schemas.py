from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel

ContractStatus = Literal[
    "pending", "approved", "rejected", "contacted",
    "signed", "active", "inactive", "waitlist"
]


# ── Streamer ──────────────────────────────────────────────────────────────────

class StreamerBase(BaseModel):
    twitch_id: str
    twitch_login: str
    display_name: str
    avatar_url: Optional[str] = None
    contract_status: ContractStatus = "pending"
    notes: Optional[str] = None
    partnership_date: Optional[str] = None
    followers_count: int = 0
    approval_source: Optional[str] = None
    approval_notes: Optional[str] = None
    approval_file_path: Optional[str] = None


class StreamerCreate(StreamerBase):
    pass


class StreamerUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    contract_status: Optional[ContractStatus] = None
    notes: Optional[str] = None
    partnership_date: Optional[str] = None
    followers_count: Optional[int] = None
    approval_source: Optional[str] = None
    approval_notes: Optional[str] = None
    approval_file_path: Optional[str] = None


class StreamerOut(StreamerBase):
    id: int
    last_scanned_at: Optional[datetime] = None
    last_live_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Clip ──────────────────────────────────────────────────────────────────────

class ClipOut(BaseModel):
    id: int
    twitch_clip_id: str
    streamer_id: int
    streamer_name: Optional[str] = None
    streamer_login: Optional[str] = None
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    clip_url: Optional[str] = None
    creator_name: Optional[str] = None
    view_count: int = 0
    duration: float = 0.0
    created_at: Optional[datetime] = None
    performance_score: float = 0.0
    is_favorite: bool = False
    is_outro: bool = False
    rating: int = 0
    notes: Optional[str] = None
    downloaded: bool = False
    local_path: Optional[str] = None
    week_number: Optional[int] = None
    cached_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ClipUpdate(BaseModel):
    is_favorite: Optional[bool] = None
    is_outro: Optional[bool] = None
    rating: Optional[int] = None
    notes: Optional[str] = None
    week_number: Optional[int] = None
    downloaded: Optional[bool] = None
    local_path: Optional[str] = None


class ClipCountsOut(BaseModel):
    total: int
    favorites: int
    downloaded: int
    outro: int


# ── Download Queue ────────────────────────────────────────────────────────────

class EnqueueRequest(BaseModel):
    clip_ids: list[int]
    save_path: str
    subfolder: Optional[str] = None
    export_txt: bool = False
    export_csv: bool = False
    overwrite: bool = False


class LocalCheckItem(BaseModel):
    clip_id: int
    twitch_clip_id: str
    streamer_login: str
    title: str


class CheckLocalRequest(BaseModel):
    items: list[LocalCheckItem]
    save_path: str


class CheckLocalResult(BaseModel):
    clip_id: int
    exists: bool
    path: Optional[str] = None


class DownloadJobOut(BaseModel):
    id: int
    clip_id: int
    clip_title: Optional[str] = None
    streamer_name: Optional[str] = None
    status: str
    progress: float
    subfolder: Optional[str] = None
    save_path: Optional[str] = None
    local_path: Optional[str] = None
    attempts: int
    error_msg: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Settings ──────────────────────────────────────────────────────────────────

class SettingsOut(BaseModel):
    TWITCH_CLIENT_ID: str
    TWITCH_CLIENT_SECRET: str
    DEFAULT_DOWNLOAD_PATH: str
    HOME_DEFAULT_LANGUAGE: str
    MAX_CONCURRENT_DOWNLOADS: int
    SCAN_MAX_CLIPS_PER_STREAMER: int


class SettingsUpdate(BaseModel):
    TWITCH_CLIENT_ID: Optional[str] = None
    TWITCH_CLIENT_SECRET: Optional[str] = None
    DEFAULT_DOWNLOAD_PATH: Optional[str] = None
    HOME_DEFAULT_LANGUAGE: Optional[str] = None
    MAX_CONCURRENT_DOWNLOADS: Optional[int] = None
    SCAN_MAX_CLIPS_PER_STREAMER: Optional[int] = None


# ── Discovery ─────────────────────────────────────────────────────────────────

class DiscoveredStreamerOut(BaseModel):
    id: int
    user_id: str
    user_login: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    game_name: Optional[str] = None
    viewer_count: Optional[int] = None
    language: Optional[str] = None
    is_mature: Optional[bool] = None
    avg_viewers: Optional[float] = None
    max_viewers: Optional[int] = None
    followers_total: Optional[int] = None
    hours_streamed: Optional[float] = None
    days_streamed: Optional[int] = None
    peak_viewers: Optional[int] = None
    tracker_updated_at: Optional[datetime] = None
    already_added: bool = False

    model_config = {"from_attributes": True}


class FromDiscoveryRequest(BaseModel):
    user_id: str
    user_login: str
    display_name: str
    avatar_url: Optional[str] = None
