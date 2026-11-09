"""YouTube API endpoints.

OAuth2 flow, channel management, upload scheduling, and admin approval.
Uploads always start as private; public scheduling requires admin approval.
"""
import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.user import User
from app.models.youtube import YouTubeChannel, YouTubeUpload, UploadStatus, PrivacyStatus
from app.services.youtube_service import YouTubeService
from app.workers.tasks.video_tasks import upload_to_youtube

router = APIRouter(prefix="/youtube", tags=["youtube"])

# In-memory CSRF state store (use Redis in production)
_oauth_states: dict[str, int] = {}


class UploadRequest(BaseModel):
    video_id: int
    channel_id: int
    title: str
    description: str = ""
    tags: list[str] = []
    category_id: str = "27"
    made_for_kids: bool = True


class ScheduleRequest(BaseModel):
    upload_id: int
    publish_at: str  # ISO8601 e.g. "2025-01-15T18:00:00Z"


class ApproveUploadRequest(BaseModel):
    upload_id: int


@router.get("/auth-url")
async def get_auth_url(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate the YouTube OAuth2 authorization URL."""
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = current_user.id
    svc = YouTubeService(db)
    url, _ = svc.build_auth_url(state=state)
    return {"auth_url": url, "state": state}


@router.get("/callback")
async def oauth_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Exchange OAuth code for tokens and persist channel."""
    user_id = _oauth_states.pop(state, None)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    svc = YouTubeService(db)
    token_data = await svc.exchange_code(code)
    channel = await svc.save_channel(token_data, user_id)
    return {
        "channel_id": channel.channel_id,
        "channel_name": channel.channel_name,
        "message": "Channel connected successfully",
    }


@router.get("/channels")
async def list_channels(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(YouTubeChannel).where(YouTubeChannel.is_active == True)
    )
    channels = result.scalars().all()
    return [
        {
            "id": c.id,
            "channel_id": c.channel_id,
            "channel_name": c.channel_name,
            "channel_url": c.channel_url,
            "thumbnail_url": c.thumbnail_url,
            "subscriber_count": c.subscriber_count,
            "video_count": c.video_count,
            "quota_used_today": c.quota_used_today,
            "daily_quota_limit": c.daily_quota_limit,
        }
        for c in channels
    ]


@router.post("/uploads")
async def create_upload(
    req: UploadRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Queue a video for YouTube upload. Upload is always private initially."""
    upload = YouTubeUpload(
        video_id=req.video_id,
        channel_id=req.channel_id,
        title=req.title,
        description=req.description,
        tags=req.tags,
        category_id=req.category_id,
        made_for_kids=req.made_for_kids,
        privacy_status=PrivacyStatus.private,
        upload_status=UploadStatus.pending,
        uploaded_by_id=current_user.id,
    )
    db.add(upload)
    await db.flush()
    upload_id = upload.id

    # Kick off upload in background worker
    background_tasks.add_task(upload_to_youtube.delay, upload_id)

    return {"upload_id": upload_id, "status": "queued", "privacy": "private"}


@router.get("/uploads")
async def list_uploads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    result = await db.execute(
        select(YouTubeUpload).order_by(YouTubeUpload.created_at.desc())
        .offset(offset).limit(page_size)
    )
    uploads = result.scalars().all()
    return [
        {
            "id": u.id,
            "video_id": u.video_id,
            "title": u.title,
            "youtube_video_id": u.youtube_video_id,
            "upload_status": u.upload_status,
            "privacy_status": u.privacy_status,
            "upload_progress_pct": u.upload_progress_pct,
            "admin_approved": u.admin_approved,
            "scheduled_publish_at": u.scheduled_publish_at,
            "created_at": u.created_at.isoformat(),
        }
        for u in uploads
    ]


@router.post("/uploads/{upload_id}/approve")
async def approve_upload(
    upload_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin approval required before a video can be scheduled for public publish."""
    upload = await db.get(YouTubeUpload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    upload.admin_approved = True
    return {"upload_id": upload_id, "admin_approved": True}


@router.post("/uploads/schedule-public")
async def schedule_public(
    req: ScheduleRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Schedule a private (and admin-approved) video to go public at a future time."""
    upload = await db.get(YouTubeUpload, req.upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    if not upload.admin_approved:
        raise HTTPException(
            status_code=403,
            detail="Admin approval required before scheduling public publish",
        )
    if upload.upload_status != UploadStatus.published:
        raise HTTPException(status_code=400, detail="Video is not yet uploaded to YouTube")

    svc = YouTubeService(db)
    await svc.schedule_public_publish(req.upload_id, req.publish_at)
    return {
        "upload_id": req.upload_id,
        "scheduled_publish_at": req.publish_at,
        "privacy_status": "scheduled",
    }


@router.delete("/channels/{channel_id}/revoke")
async def revoke_channel(
    channel_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Revoke OAuth tokens and disconnect a channel."""
    from app.services.youtube_service import decrypt_token

    channel = await db.get(YouTubeChannel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    svc = YouTubeService(db)
    if channel.access_token_encrypted:
        try:
            token = decrypt_token(channel.access_token_encrypted)
            await svc.revoke_token(token)
        except Exception:
            pass  # Revocation best-effort

    channel.is_active = False
    channel.access_token_encrypted = None
    channel.refresh_token_encrypted = None
    return {"message": "Channel disconnected and tokens revoked"}
