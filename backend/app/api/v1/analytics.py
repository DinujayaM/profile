"""Analytics and dashboard statistics endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.video import Video, VideoStatus, VideoJob, JobStatus
from app.models.youtube import YouTubeUpload, YouTubeChannel
from app.models.cost import CostRecord
from app.models.user import User
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/analytics", tags=["analytics"])


class DashboardStats(BaseModel):
    total_videos: int
    pending_approval: int
    published_videos: int
    failed_jobs: int
    scheduled_uploads: int
    total_youtube_views: Optional[int]
    subscriber_count: Optional[int]
    total_cost_usd: float
    daily_cost_usd: float
    monthly_cost_usd: float


class VideoStatusBreakdown(BaseModel):
    status: str
    count: int


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard_stats(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    total_videos = (await db.execute(select(func.count(Video.id)))).scalar() or 0
    pending = (await db.execute(select(func.count(Video.id)).where(Video.status == VideoStatus.pending_approval))).scalar() or 0
    published = (await db.execute(select(func.count(Video.id)).where(Video.status == VideoStatus.published))).scalar() or 0
    failed = (await db.execute(select(func.count(VideoJob.id)).where(VideoJob.status == JobStatus.failed))).scalar() or 0
    scheduled = (await db.execute(select(func.count(YouTubeUpload.id)).where(
        YouTubeUpload.scheduled_publish_at.isnot(None)
    ))).scalar() or 0

    channel = (await db.execute(select(YouTubeChannel).where(YouTubeChannel.is_active == True))).scalar_one_or_none()
    views = channel.total_views if channel else None
    subs = channel.subscriber_count if channel else None

    total_cost = (await db.execute(select(func.sum(CostRecord.amount_usd)))).scalar() or 0.0

    from datetime import date, timedelta
    today = date.today().isoformat()
    month_start = date.today().replace(day=1).isoformat()
    daily_cost = (await db.execute(
        select(func.sum(CostRecord.amount_usd)).where(CostRecord.record_date == today)
    )).scalar() or 0.0
    monthly_cost = (await db.execute(
        select(func.sum(CostRecord.amount_usd)).where(CostRecord.record_date >= month_start)
    )).scalar() or 0.0

    return DashboardStats(
        total_videos=total_videos,
        pending_approval=pending,
        published_videos=published,
        failed_jobs=failed,
        scheduled_uploads=scheduled,
        total_youtube_views=views,
        subscriber_count=subs,
        total_cost_usd=float(total_cost),
        daily_cost_usd=float(daily_cost),
        monthly_cost_usd=float(monthly_cost),
    )


@router.get("/video-status-breakdown", response_model=list[VideoStatusBreakdown])
async def video_status_breakdown(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    result = await db.execute(
        select(Video.status, func.count(Video.id)).group_by(Video.status)
    )
    return [VideoStatusBreakdown(status=row[0].value, count=row[1]) for row in result.all()]


@router.get("/cost-by-category")
async def cost_by_category(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    result = await db.execute(
        select(CostRecord.category, func.sum(CostRecord.amount_usd))
        .group_by(CostRecord.category)
    )
    return [{"category": row[0].value, "total_usd": float(row[1] or 0)} for row in result.all()]


@router.get("/recent-videos")
async def recent_videos(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    from app.schemas.video import VideoResponse
    result = await db.execute(
        select(Video).order_by(Video.created_at.desc()).limit(10)
    )
    videos = result.scalars().all()
    return [VideoResponse.model_validate(v) for v in videos]
