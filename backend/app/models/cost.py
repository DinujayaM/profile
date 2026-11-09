import enum
from typing import Optional
from sqlalchemy import String, Float, Integer, Enum as SAEnum, ForeignKey, JSON, Date
from sqlalchemy.orm import mapped_column, Mapped
from app.core.database import Base
from app.models.base import TimestampMixin


class CostCategory(str, enum.Enum):
    llm = "llm"
    image_generation = "image_generation"
    video_generation = "video_generation"
    tts = "tts"
    music_generation = "music_generation"
    storage = "storage"
    compute = "compute"
    youtube_api = "youtube_api"
    other = "other"


class CostRecord(Base, TimestampMixin):
    __tablename__ = "cost_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[Optional[int]] = mapped_column(ForeignKey("videos.id"), nullable=True)
    job_id: Mapped[Optional[int]] = mapped_column(ForeignKey("video_jobs.id"), nullable=True)
    category: Mapped[CostCategory] = mapped_column(SAEnum(CostCategory), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    amount_usd: Mapped[float] = mapped_column(Float, nullable=False)
    units: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    unit_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)   # tokens, images, seconds, chars
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    record_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # YYYY-MM-DD
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class CostLimit(Base, TimestampMixin):
    __tablename__ = "cost_limits"

    id: Mapped[int] = mapped_column(primary_key=True)
    limit_type: Mapped[str] = mapped_column(String(20), nullable=False)  # daily | monthly
    limit_usd: Mapped[float] = mapped_column(Float, nullable=False)
    alert_threshold_pct: Mapped[float] = mapped_column(Float, default=80.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    pause_on_exceed: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
