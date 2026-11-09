import enum
from typing import Optional
from sqlalchemy import String, Text, Boolean, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.orm import mapped_column, Mapped
from app.core.database import Base
from app.models.base import TimestampMixin


class TaskStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"


class ScheduledTask(Base, TimestampMixin):
    __tablename__ = "scheduled_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_run_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_status: Mapped[Optional[TaskStatus]] = mapped_column(SAEnum(TaskStatus), nullable=True)
    next_run_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    run_count: Mapped[int] = mapped_column(default=0, nullable=False)
    fail_count: Mapped[int] = mapped_column(default=0, nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
