import enum
from typing import Optional
from sqlalchemy import String, Text, Float, Integer, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class VoiceProfile(Base, TimestampMixin):
    __tablename__ = "voice_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_voice_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    age_tone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)   # child, adult, elderly
    accent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(20), default="en-US", nullable=False)
    sample_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class AudioAsset(Base, TimestampMixin):
    __tablename__ = "audio_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[Optional[int]] = mapped_column(ForeignKey("videos.id"), nullable=True)
    scene_id: Mapped[Optional[int]] = mapped_column(ForeignKey("video_scenes.id"), nullable=True)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)  # narration, dialogue, sfx
    text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    voice_profile_id: Mapped[Optional[int]] = mapped_column(ForeignKey("voice_profiles.id"), nullable=True)
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tts_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    generation_cost_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    language: Mapped[str] = mapped_column(String(20), default="en-US", nullable=False)


class MusicAsset(Base, TimestampMixin):
    __tablename__ = "music_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[Optional[int]] = mapped_column(ForeignKey("videos.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)  # background, song, jingle
    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lyrics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mood: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    genre: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    music_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    generation_cost_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_original: Mapped[bool] = mapped_column(default=True, nullable=False)
