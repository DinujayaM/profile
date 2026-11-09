import enum
from typing import Optional
from sqlalchemy import String, Text, Integer, Float, Boolean, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class PrivacyStatus(str, enum.Enum):
    private = "private"
    unlisted = "unlisted"
    public = "public"


class UploadStatus(str, enum.Enum):
    pending = "pending"
    uploading = "uploading"
    processing = "processing"
    published = "published"
    failed = "failed"
    removed = "removed"


class YouTubeChannel(Base, TimestampMixin):
    __tablename__ = "youtube_channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    channel_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    channel_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    access_token_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expiry: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    subscriber_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_views: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    video_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_synced_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    quota_used_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_quota_limit: Mapped[int] = mapped_column(Integer, default=10000, nullable=False)

    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    uploads: Mapped[list["YouTubeUpload"]] = relationship("YouTubeUpload", back_populates="channel", lazy="select")


class ScheduledStatus(str, enum.Enum):
    scheduled = "scheduled"


class YouTubeUpload(Base, TimestampMixin):
    __tablename__ = "youtube_uploads"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey("youtube_channels.id"), nullable=False)
    youtube_video_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    category_id: Mapped[str] = mapped_column(String(10), default="27", nullable=False)  # 27 = Education
    privacy_status: Mapped[PrivacyStatus] = mapped_column(SAEnum(PrivacyStatus), default=PrivacyStatus.private, nullable=False)
    made_for_kids: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    scheduled_publish_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    upload_status: Mapped[UploadStatus] = mapped_column(SAEnum(UploadStatus), default=UploadStatus.pending, nullable=False)
    upload_progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    playlist_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    thumbnail_uploaded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quota_cost: Mapped[int] = mapped_column(Integer, default=1600, nullable=False)
    uploaded_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    admin_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    channel: Mapped["YouTubeChannel"] = relationship("YouTubeChannel", back_populates="uploads")
