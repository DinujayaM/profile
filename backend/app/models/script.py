import enum
from typing import Optional
from sqlalchemy import String, Text, Integer, Float, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class ScriptStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    rejected = "rejected"
    in_production = "in_production"


class Script(Base, TimestampMixin):
    __tablename__ = "scripts"

    id: Mapped[int] = mapped_column(primary_key=True)
    idea_id: Mapped[int] = mapped_column(ForeignKey("video_ideas.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    introduction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    main_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ending: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    full_script: Mapped[str] = mapped_column(Text, nullable=False)
    song_lyrics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    narration_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_duration_minutes: Mapped[float] = mapped_column(Float, default=3.0, nullable=False)
    llm_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    generation_cost_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[ScriptStatus] = mapped_column(SAEnum(ScriptStatus), default=ScriptStatus.draft, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    idea: Mapped["VideoIdea"] = relationship("VideoIdea", back_populates="scripts")
    storyboards: Mapped[list["Storyboard"]] = relationship("Storyboard", back_populates="script", lazy="select")

    def __repr__(self) -> str:
        return f"<Script {self.title}>"


class Storyboard(Base, TimestampMixin):
    __tablename__ = "storyboards"

    id: Mapped[int] = mapped_column(primary_key=True)
    script_id: Mapped[int] = mapped_column(ForeignKey("scripts.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    total_scenes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    script: Mapped["Script"] = relationship("Script", back_populates="storyboards")
    scenes: Mapped[list["StoryboardScene"]] = relationship("StoryboardScene", back_populates="storyboard", order_by="StoryboardScene.scene_number", lazy="select")


class StoryboardScene(Base, TimestampMixin):
    __tablename__ = "storyboard_scenes"

    id: Mapped[int] = mapped_column(primary_key=True)
    storyboard_id: Mapped[int] = mapped_column(ForeignKey("storyboards.id"), nullable=False)
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    character_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    background_description: Mapped[str] = mapped_column(Text, nullable=False)
    animation_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dialogue: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    narration: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    image_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_image_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    character_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    storyboard: Mapped["Storyboard"] = relationship("Storyboard", back_populates="scenes")
