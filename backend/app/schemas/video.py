from typing import Optional, List
from pydantic import BaseModel
from app.models.video import VideoStatus, VideoFormat, JobStatus


class VideoResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    tags: Optional[List[str]]
    thumbnail_url: Optional[str]
    video_url: Optional[str]
    format: VideoFormat
    duration_seconds: Optional[float]
    width: int
    height: int
    status: VideoStatus
    made_for_kids: bool
    total_cost_usd: Optional[float]
    quality_score: Optional[float]
    youtube_video_id: Optional[str]

    model_config = {"from_attributes": True}


class VideoListResponse(BaseModel):
    items: List[VideoResponse]
    total: int
    page: int
    page_size: int


class VideoJobResponse(BaseModel):
    id: int
    video_id: Optional[int]
    celery_task_id: Optional[str]
    job_type: str
    step: Optional[str]
    status: JobStatus
    progress_pct: int
    error_message: Optional[str]
    retry_count: int

    model_config = {"from_attributes": True}


class StartProductionRequest(BaseModel):
    idea_id: int
    format: VideoFormat = VideoFormat.landscape
    made_for_kids: bool = True


class ApproveVideoRequest(BaseModel):
    video_id: int
    notes: Optional[str] = None


class RejectVideoRequest(BaseModel):
    video_id: int
    reason: str
