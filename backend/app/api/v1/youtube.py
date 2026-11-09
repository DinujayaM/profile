"""YouTube OAuth and upload endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.youtube import YouTubeChannel, YouTubeUpload, UploadStatus, PrivacyStatus
from app.models.video import Video, VideoStatus
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/youtube", tags=["youtube"])


class UploadRequest(BaseModel):
    video_id: int
    title: str
    description: str
    tags: Optional[list[str]] = None
    privacy_status: PrivacyStatus = PrivacyStatus.private
    made_for_kids: bool = True
    scheduled_publish_at: Optional[str] = None


class UploadResponse(BaseModel):
    id: int
    video_id: int
    youtube_video_id: Optional[str]
    upload_status: UploadStatus
    upload_progress_pct: int
    error_message: Optional[str]
    model_config = {"from_attributes": True}


class ChannelResponse(BaseModel):
    id: int
    channel_id: str
    channel_name: Optional[str]
    channel_url: Optional[str]
    subscriber_count: Optional[int]
    total_views: Optional[int]
    video_count: Optional[int]
    quota_used_today: int
    daily_quota_limit: int
    is_active: bool
    model_config = {"from_attributes": True}


@router.get("/auth-url")
async def get_auth_url(_: User = Depends(require_admin)):
    """Return the OAuth2 URL to connect a YouTube channel."""
    if not settings.YOUTUBE_CLIENT_ID:
        raise HTTPException(503, "YouTube OAuth not configured. Set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET.")
    scope = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"
    url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={settings.YOUTUBE_CLIENT_ID}"
        f"&redirect_uri={settings.YOUTUBE_REDIRECT_URI}"
        "&response_type=code"
        f"&scope={scope}"
        "&access_type=offline"
        "&prompt=consent"
    )
    return {"auth_url": url}


@router.get("/callback")
async def oauth_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Handle OAuth2 callback from Google."""
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.YOUTUBE_CLIENT_ID,
                "client_secret": settings.YOUTUBE_CLIENT_SECRET,
                "redirect_uri": settings.YOUTUBE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        tokens = resp.json()

    # Get channel info
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        channel_data = resp.json()

    channel_info = channel_data["items"][0] if channel_data.get("items") else {}
    channel_id = channel_info.get("id", "unknown")

    result = await db.execute(select(YouTubeChannel).where(YouTubeChannel.channel_id == channel_id))
    channel = result.scalar_one_or_none()
    if not channel:
        channel = YouTubeChannel(channel_id=channel_id)
        db.add(channel)

    # Store tokens encrypted (simplified – use proper encryption in production)
    channel.access_token_encrypted = tokens.get("access_token", "")
    channel.refresh_token_encrypted = tokens.get("refresh_token", "")
    channel.channel_name = channel_info.get("snippet", {}).get("title")
    channel.channel_url = f"https://youtube.com/channel/{channel_id}"
    stats = channel_info.get("statistics", {})
    channel.subscriber_count = int(stats.get("subscriberCount", 0))
    channel.total_views = int(stats.get("viewCount", 0))
    channel.video_count = int(stats.get("videoCount", 0))

    await db.flush()
    return {"message": "YouTube channel connected", "channel_name": channel.channel_name}


@router.get("/channels", response_model=list[ChannelResponse])
async def list_channels(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    result = await db.execute(select(YouTubeChannel).where(YouTubeChannel.is_active == True))
    return result.scalars().all()


@router.post("/uploads", response_model=UploadResponse, status_code=202)
async def schedule_upload(
    payload: UploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    video = await db.get(Video, payload.video_id)
    if not video:
        raise HTTPException(404, "Video not found")
    if video.status != VideoStatus.approved:
        raise HTTPException(400, "Video must be approved before uploading")

    result = await db.execute(select(YouTubeChannel).where(YouTubeChannel.is_active == True))
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(503, "No YouTube channel connected")

    upload = YouTubeUpload(
        video_id=payload.video_id,
        channel_id=channel.id,
        title=payload.title,
        description=payload.description,
        tags=payload.tags,
        privacy_status=payload.privacy_status,
        made_for_kids=payload.made_for_kids,
        scheduled_publish_at=payload.scheduled_publish_at,
        upload_status=UploadStatus.pending,
        uploaded_by_id=current_user.id,
    )
    db.add(upload)
    await db.flush()
    # In production: dispatch Celery task
    # from app.workers.tasks.video_tasks import upload_to_youtube
    # upload_to_youtube.delay(upload.id)
    video.status = VideoStatus.uploading
    return upload


@router.get("/uploads", response_model=list[UploadResponse])
async def list_uploads(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    result = await db.execute(select(YouTubeUpload).order_by(YouTubeUpload.created_at.desc()).limit(50))
    return result.scalars().all()
