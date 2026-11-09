from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.video import Video, VideoJob, VideoStatus
from app.models.user import User
from app.schemas.video import (
    VideoResponse, VideoListResponse, VideoJobResponse,
    StartProductionRequest, ApproveVideoRequest, RejectVideoRequest,
)
from app.services.video_pipeline import VideoPipeline

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("/start-production", response_model=VideoJobResponse, status_code=202)
async def start_production(
    payload: StartProductionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    pipeline = VideoPipeline(db)
    job = await pipeline.start_production(
        idea_id=payload.idea_id,
        video_format=payload.format,
        made_for_kids=payload.made_for_kids,
    )
    # In production this would dispatch to Celery:
    # from app.workers.tasks.video_tasks import run_video_pipeline
    # run_video_pipeline.delay(job.id)
    # For now, run inline in background
    background_tasks.add_task(_run_pipeline_bg, job.id)
    return job


async def _run_pipeline_bg(job_id: int):
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        pipeline = VideoPipeline(db)
        await pipeline.run_pipeline(job_id)
        await db.commit()


@router.get("", response_model=VideoListResponse)
async def list_videos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: VideoStatus | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(Video)
    if status:
        q = q.where(Video.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    result = await db.execute(q.order_by(Video.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    return VideoListResponse(items=result.scalars().all(), total=total, page=page, page_size=page_size)


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    video = await db.get(Video, video_id)
    if not video:
        raise HTTPException(404, "Video not found")
    return video


@router.post("/{video_id}/approve", response_model=VideoResponse)
async def approve_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    video = await db.get(Video, video_id)
    if not video:
        raise HTTPException(404, "Video not found")
    if video.status != VideoStatus.pending_approval:
        raise HTTPException(400, f"Video is in status {video.status}, expected pending_approval")
    video.status = VideoStatus.approved
    video.approved_by_id = current_user.id
    return video


@router.post("/{video_id}/reject", response_model=VideoResponse)
async def reject_video(
    video_id: int, reason: str, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)
):
    video = await db.get(Video, video_id)
    if not video:
        raise HTTPException(404, "Video not found")
    video.status = VideoStatus.rejected
    video.rejection_reason = reason
    return video


@router.get("/{video_id}/jobs", response_model=list[VideoJobResponse])
async def get_video_jobs(video_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    result = await db.execute(select(VideoJob).where(VideoJob.video_id == video_id))
    return result.scalars().all()


@router.get("/{video_id}/jobs/{job_id}", response_model=VideoJobResponse)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    job = await db.get(VideoJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job
