"""System settings and cost management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import require_admin
from app.models.cost import CostLimit
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["settings"])


class CostLimitCreate(BaseModel):
    limit_type: str  # daily | monthly
    limit_usd: float
    alert_threshold_pct: float = 80.0
    pause_on_exceed: bool = True


class CostLimitResponse(BaseModel):
    id: int
    limit_type: str
    limit_usd: float
    alert_threshold_pct: float
    is_active: bool
    pause_on_exceed: bool
    model_config = {"from_attributes": True}


class SystemConfigResponse(BaseModel):
    llm_provider: str
    image_provider: str
    video_provider: str
    tts_provider: str
    music_provider: str
    storage_provider: str
    scheduler_enabled: bool
    daily_video_target: int
    youtube_connected: bool


@router.get("/config", response_model=SystemConfigResponse)
async def get_config(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    from app.core.config import settings
    from app.models.youtube import YouTubeChannel
    channel = (await db.execute(select(YouTubeChannel).where(YouTubeChannel.is_active == True))).scalar_one_or_none()
    return SystemConfigResponse(
        llm_provider=settings.LLM_PROVIDER,
        image_provider=settings.IMAGE_PROVIDER,
        video_provider=settings.VIDEO_PROVIDER,
        tts_provider=settings.TTS_PROVIDER,
        music_provider=settings.MUSIC_PROVIDER,
        storage_provider=settings.STORAGE_PROVIDER,
        scheduler_enabled=settings.SCHEDULER_ENABLED,
        daily_video_target=settings.DAILY_VIDEO_TARGET,
        youtube_connected=channel is not None,
    )


@router.get("/cost-limits", response_model=list[CostLimitResponse])
async def list_cost_limits(db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    result = await db.execute(select(CostLimit))
    return result.scalars().all()


@router.post("/cost-limits", response_model=CostLimitResponse, status_code=201)
async def create_cost_limit(
    payload: CostLimitCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    limit = CostLimit(**payload.model_dump(), created_by_id=current_user.id)
    db.add(limit)
    await db.flush()
    return limit


@router.put("/cost-limits/{limit_id}", response_model=CostLimitResponse)
async def update_cost_limit(
    limit_id: int,
    payload: CostLimitCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    limit = await db.get(CostLimit, limit_id)
    if not limit:
        raise HTTPException(404, "Cost limit not found")
    for k, v in payload.model_dump().items():
        setattr(limit, k, v)
    return limit
