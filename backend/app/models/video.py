import enum
from typing import Optional
from sqlalchemy import String, Text, Float, Integer, Enum as SAEnum, ForeignKey, JSON, Boolean
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class VideoStatus(str, enum.Enum):
    draft = "draft"
    generating = "generating"
    quality_check = "quality_check"
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"
    uploading = "uploading"
    published = "published"
    failed = "failed"
    archived = "archived"


class VideoFormat(str, enum.Enum):
    landscape = "landscape"   # 1920x1080
    portrait = "portrait"     # 1080x1920


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    retrying = "retrying"
    cancelled = "cancelled"


class Video(Base, TimestampMixin):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    idea_id: Mapped[Optional[int]] = mapped_column(ForeignKey("video_ideas.id"), nullable=True)
    script_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scripts.id"), nullable=True)
    storyboard_id: Mapped[Optional[int]] = mapped_column(ForeignKey("storyboards.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    thumbnail_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    video_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    format: Mapped[VideoFormat] = mapped_column(SAEnum(VideoFormat), default=VideoFormat.landscape, nullable=False)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    width: Mapped[int] = mapped_column(Integer, default=1920, nullable=False)
    height: Mapped[int] = mapped_column(Integer, default=1080, nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(nullable=True)
    status: Mapped[VideoStatus] = mapped_column(SAEnum(VideoStatus), default=VideoStatus.draft, nullable=False)
    made_for_kids: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    total_cost_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    youtube_video_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    subtitle_file_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    production_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    scenes: Mapped[list["VideoScene"]] = relationship("VideoScene", back_populates="video", order_by="VideoScene.scene_order", lazy="select")
    jobs: Mapped[list["VideoJob"]] = relationship("VideoJob", back_populates="video", lazy="select")

    def __repr__(self) -> str:
        return f"<Video {self.title}>"


class VideoScene(Base, TimestampMixin):
    __tablename__ = "video_scenes"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), nullable=False)
    storyboard_scene_id: Mapped[Optional[int]] = mapped_column(ForeignKey("storyboard_scenes.id"), nullable=True)
    scene_order: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    video_clip_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    video_clip_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    image_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    video_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    generation_cost_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    generation_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    video: Mapped["Video"] = relationship("Video", back_populates="scenes")


class VideoJob(Base, TimestampMixin):
    __tablename__ = "video_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[Optional[int]] = mapped_column(ForeignKey("videos.id"), nullable=True)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)  # pipeline, scene_gen, audio_gen, etc.
    step: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[JobStatus] = mapped_column(SAEnum(JobStatus), default=JobStatus.queued, nullable=False)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    started_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    completed_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    cost_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    video: Mapped[Optional["Video"]] = relationship("Video", back_populates="jobs")
