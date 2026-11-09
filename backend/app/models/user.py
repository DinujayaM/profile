from sqlalchemy import String, Boolean, Enum as SAEnum
from sqlalchemy.orm import mapped_column, Mapped
from app.core.database import Base
from app.models.base import TimestampMixin
import enum


class UserRole(str, enum.Enum):
    viewer = "viewer"
    editor = "editor"
    admin = "admin"
    superadmin = "superadmin"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.editor, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    totp_secret: Mapped[str] = mapped_column(String(64), nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[str] = mapped_column(String(64), nullable=True)

    def __repr__(self) -> str:
        return f"<User {self.email}>"
