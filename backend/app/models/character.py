import enum
from typing import Optional
from sqlalchemy import String, Text, Enum as SAEnum, ForeignKey, JSON, Boolean
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class CharacterType(str, enum.Enum):
    main = "main"
    supporting = "supporting"
    background = "background"
    narrator = "narrator"


class Character(Base, TimestampMixin):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    character_type: Mapped[CharacterType] = mapped_column(SAEnum(CharacterType), default=CharacterType.main, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    personality: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    appearance: Mapped[str] = mapped_column(Text, nullable=False)
    color_palette: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    voice_profile_id: Mapped[Optional[int]] = mapped_column(ForeignKey("voice_profiles.id"), nullable=True)
    image_generation_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_image_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    assets: Mapped[list["CharacterAsset"]] = relationship("CharacterAsset", back_populates="character", lazy="select")

    def __repr__(self) -> str:
        return f"<Character {self.name}>"


class CharacterAsset(Base, TimestampMixin):
    __tablename__ = "character_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)  # portrait, full_body, expression, pose
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    image_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    generation_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generation_cost_usd: Mapped[Optional[float]] = mapped_column(nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    character: Mapped["Character"] = relationship("Character", back_populates="assets")
