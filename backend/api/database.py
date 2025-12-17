# backend/api/database.py
"""
Database configuration and models for PostgreSQL.
"""

import os
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.pool import NullPool

# Database URL from environment
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://tiksimpro:tiksimpro123@localhost:5432/tiksimpro"
)

# For sync operations (migrations, etc.)
SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

# Async session
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


# ===== MODELS =====

class Video(Base):
    """Video generation record."""
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Generator info
    generator_name = Column(String(100), nullable=False)
    generator_params = Column(JSON, default={})

    # Audio info
    audio_mode = Column(String(50))
    audio_params = Column(JSON, default={})
    midi_file = Column(String(255))

    # Video info
    video_path = Column(String(500))
    duration = Column(Float)
    fps = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)

    # Validation
    validation_score = Column(Float)
    validation_details = Column(JSON, default={})

    # Publication
    published_at = Column(DateTime)
    platform = Column(String(50))
    platform_video_id = Column(String(255))

    # Git tracking
    git_commit = Column(String(40))

    # Relationships
    metrics = relationship("Metric", back_populates="video", cascade="all, delete-orphan")


class Metric(Base):
    """Performance metrics scraped from platforms."""
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    platform = Column(String(50), nullable=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    # Metrics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    saves = Column(Integer, default=0)

    # Engagement
    watch_time_avg = Column(Float)
    retention_rate = Column(Float)
    engagement_rate = Column(Float)

    # Relationship
    video = relationship("Video", back_populates="metrics")


class Conversation(Base):
    """Conversation history with Claude."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_message = Column(Text, nullable=False)
    assistant_message = Column(Text, nullable=False)

    # Actions Claude took
    actions_taken = Column(JSON, default=[])

    # System state snapshot at time of conversation
    context_snapshot = Column(JSON, default={})


class ConversationSummary(Base):
    """Summarized conversation history for memory optimization."""
    __tablename__ = "conversation_summaries"

    id = Column(Integer, primary_key=True, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    summary = Column(Text, nullable=False)
    key_decisions = Column(JSON, default=[])

    created_at = Column(DateTime, default=datetime.utcnow)


class SystemState(Base):
    """Current system state."""
    __tablename__ = "system_state"

    id = Column(Integer, primary_key=True, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    loop_running = Column(Boolean, default=False)
    last_error = Column(Text)
    last_video_id = Column(Integer)

    config = Column(JSON, default={})


class AIDecision(Base):
    """AI decision history."""
    __tablename__ = "ai_decisions"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    context = Column(JSON, default={})
    decision = Column(JSON, default={})
    reasoning = Column(Text)


class ConnectedAccount(Base):
    """User's connected social media accounts - only these can be scraped."""
    __tablename__ = "connected_accounts"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    platform = Column(String(50), nullable=False)  # youtube, tiktok
    account_url = Column(String(500), nullable=False)
    account_name = Column(String(255))  # Display name
    account_id = Column(String(255))  # Platform-specific ID (channel ID, username)

    is_active = Column(Boolean, default=True)
    last_scraped = Column(DateTime)

    # Normalized identifiers for matching
    normalized_url = Column(String(500))  # Cleaned URL for comparison


# ===== DATABASE FUNCTIONS =====

async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ===== PYDANTIC SCHEMAS =====

from pydantic import BaseModel
from typing import Optional, List


class VideoBase(BaseModel):
    generator_name: str
    generator_params: dict = {}
    audio_mode: Optional[str] = None
    audio_params: dict = {}
    duration: Optional[float] = None
    fps: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class VideoCreate(VideoBase):
    pass


class VideoResponse(VideoBase):
    id: int
    created_at: datetime
    video_path: Optional[str] = None
    validation_score: Optional[float] = None
    platform: Optional[str] = None
    platform_video_id: Optional[str] = None

    class Config:
        from_attributes = True


class MetricResponse(BaseModel):
    id: int
    video_id: int
    platform: str
    scraped_at: datetime
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    engagement_rate: Optional[float] = None

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    message: str


class ConversationResponse(BaseModel):
    id: int
    created_at: datetime
    user_message: str
    assistant_message: str
    actions_taken: list = []

    class Config:
        from_attributes = True


class PipelineStatus(BaseModel):
    running: bool
    last_video_id: Optional[int] = None
    last_error: Optional[str] = None
    videos_today: int = 0
    total_videos: int = 0


class ConnectedAccountCreate(BaseModel):
    platform: str
    account_url: str
    account_name: Optional[str] = None


class ConnectedAccountResponse(BaseModel):
    id: int
    platform: str
    account_url: str
    account_name: Optional[str] = None
    account_id: Optional[str] = None
    is_active: bool
    last_scraped: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ===== ACCOUNT VALIDATION HELPERS =====

import re

def normalize_youtube_url(url: str) -> str:
    """Extract channel identifier from YouTube URL."""
    url = url.strip().lower()

    # Handle different YouTube URL formats
    patterns = [
        r'youtube\.com/channel/([^/?&]+)',
        r'youtube\.com/c/([^/?&]+)',
        r'youtube\.com/@([^/?&]+)',
        r'youtube\.com/user/([^/?&]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1).lower()

    return url


def normalize_tiktok_url(url: str) -> str:
    """Extract username from TikTok URL."""
    url = url.strip().lower()

    # Handle @username format
    match = re.search(r'tiktok\.com/@([^/?&]+)', url)
    if match:
        return match.group(1).lower()

    return url


def normalize_account_url(platform: str, url: str) -> str:
    """Normalize account URL for comparison."""
    if platform == 'youtube':
        return normalize_youtube_url(url)
    elif platform == 'tiktok':
        return normalize_tiktok_url(url)
    return url.strip().lower()
