from functools import lru_cache
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Application
    APP_ENV: str = "development"
    SECRET_KEY: str
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database
    DATABASE_URL: str
    POSTGRES_DB: str = "tinytales"

    # Redis / Celery
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Storage
    STORAGE_PROVIDER: str = "local"
    LOCAL_STORAGE_PATH: str = "/app/storage"
    S3_BUCKET_NAME: Optional[str] = None
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    GCS_BUCKET_NAME: Optional[str] = None
    GCS_PROJECT_ID: Optional[str] = None

    # LLM
    LLM_PROVIDER: str = "mock"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o"

    # Image Generation
    IMAGE_PROVIDER: str = "mock"
    STABILITY_API_KEY: Optional[str] = None
    IMAGE_MODEL: str = "dall-e-3"

    # Video Generation
    VIDEO_PROVIDER: str = "mock"
    RUNWAY_API_KEY: Optional[str] = None
    PIKA_API_KEY: Optional[str] = None

    # TTS
    TTS_PROVIDER: str = "mock"
    ELEVENLABS_API_KEY: Optional[str] = None
    GOOGLE_TTS_API_KEY: Optional[str] = None

    # Music
    MUSIC_PROVIDER: str = "mock"
    SUNO_API_KEY: Optional[str] = None
    UDIO_API_KEY: Optional[str] = None

    # YouTube
    YOUTUBE_CLIENT_ID: Optional[str] = None
    YOUTUBE_CLIENT_SECRET: Optional[str] = None
    YOUTUBE_REDIRECT_URI: str = "http://localhost:8000/api/v1/youtube/callback"
    YOUTUBE_CHANNEL_ID: Optional[str] = None

    # Cost Limits
    DAILY_COST_LIMIT_USD: float = 50.0
    MONTHLY_COST_LIMIT_USD: float = 1000.0

    # Scheduler
    SCHEDULER_ENABLED: bool = True
    DAILY_VIDEO_TARGET: int = 1
    RESEARCH_CRON: str = "0 8 * * *"
    PRODUCTION_CRON: str = "30 8 * * *"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
