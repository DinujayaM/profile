import enum
from typing import Optional
from sqlalchemy import String, Text, Float, Integer, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class IdeaStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    in_production = "in_production"
    completed = "completed"


class AgeCategory(str, enum.Enum):
    toddler = "0-2"
    preschool = "3-5"
    early_school = "6-8"
    school = "9-12"


class ContentCategory(str, enum.Enum):
    nursery_rhyme = "nursery_rhyme"
    educational = "educational"
    animal_story = "animal_story"
    bedtime_story = "bedtime_story"
    alphabet = "alphabet"
    numbers = "numbers"
    colors = "colors"
    shapes = "shapes"
    seasons = "seasons"
    holiday = "holiday"
    adventure = "adventure"
    friendship = "friendship"
    science = "science"
    music = "music"


class VideoIdea(Base, TimestampMixin):
    __tablename__ = "video_ideas"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    concept: Mapped[str] = mapped_column(Text, nullable=False)
    educational_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    originality_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    age_category: Mapped[AgeCategory] = mapped_column(SAEnum(AgeCategory), nullable=False)
    content_category: Mapped[ContentCategory] = mapped_column(SAEnum(ContentCategory), nullable=False)
    estimated_duration_minutes: Mapped[float] = mapped_column(Float, default=3.0, nullable=False)
    estimated_cost_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[IdeaStatus] = mapped_column(SAEnum(IdeaStatus), default=IdeaStatus.pending, nullable=False)
    keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    research_source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    scripts: Mapped[list["Script"]] = relationship("Script", back_populates="idea", lazy="select")

    def __repr__(self) -> str:
        return f"<VideoIdea {self.title}>"
