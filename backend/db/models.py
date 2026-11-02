from datetime import datetime
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from backend.db.database import Base


class Streamer(Base):
    __tablename__ = "streamers"

    id = Column(Integer, primary_key=True, index=True)
    twitch_id = Column(String, unique=True, index=True, nullable=False)
    twitch_login = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    contract_status = Column(String, default="pending", nullable=False)
    notes = Column(Text, nullable=True)
    last_scanned_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    partnership_date = Column(String, nullable=True)
    followers_count = Column(Integer, default=0, nullable=False)
    last_live_at = Column(DateTime, nullable=True)
    approval_source = Column(String, nullable=True)
    approval_notes = Column(Text, nullable=True)
    approval_file_path = Column(String, nullable=True)

    clips = relationship("Clip", back_populates="streamer", cascade="all, delete-orphan")


class Clip(Base):
    __tablename__ = "clips"

    id = Column(Integer, primary_key=True, index=True)
    twitch_clip_id = Column(String, unique=True, index=True, nullable=False)
    streamer_id = Column(Integer, ForeignKey("streamers.id"), nullable=False)
    title = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    clip_url = Column(String, nullable=True)
    creator_name = Column(String, nullable=True)
    view_count = Column(Integer, default=0, nullable=False)
    duration = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, nullable=True)
    performance_score = Column(Float, default=0.0, nullable=False)
    is_favorite = Column(Boolean, default=False, nullable=False)
    is_outro = Column(Boolean, default=False, nullable=False)
    rating = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
    downloaded = Column(Boolean, default=False, nullable=False)
    local_path = Column(String, nullable=True)
    week_number = Column(Integer, nullable=True)
    cached_at = Column(DateTime, nullable=True)

    streamer = relationship("Streamer", back_populates="clips")


class DiscoveredStreamer(Base):
    __tablename__ = "discovered_streamers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    user_login = Column(String, nullable=True)
    display_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    game_name = Column(String, nullable=True)
    viewer_count = Column(Integer, nullable=True)
    language = Column(String, nullable=True)
    is_mature = Column(Boolean, nullable=True)
    last_seen_live_at = Column(DateTime, nullable=True)
    # TwitchTracker cached stats
    avg_viewers = Column(Float, nullable=True)
    max_viewers = Column(Integer, nullable=True)
    followers_total = Column(Integer, nullable=True)
    hours_streamed = Column(Float, nullable=True)
    days_streamed = Column(Integer, nullable=True)
    peak_viewers = Column(Integer, nullable=True)
    tracker_updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class DownloadJob(Base):
    __tablename__ = "download_jobs"

    id = Column(Integer, primary_key=True, index=True)
    clip_id = Column(Integer, ForeignKey("clips.id"), nullable=False)
    clip_title = Column(String, nullable=True)
    streamer_name = Column(String, nullable=True)
    status = Column(String, default="pending", nullable=False)
    progress = Column(Float, default=0.0, nullable=False)
    subfolder = Column(String, nullable=True)
    save_path = Column(String, nullable=True)
    local_path = Column(String, nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    error_msg = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
