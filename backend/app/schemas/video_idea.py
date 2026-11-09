from typing import Optional, List
from pydantic import BaseModel
from app.models.video_idea import AgeCategory, ContentCategory, IdeaStatus


class VideoIdeaCreate(BaseModel):
    title: str
    concept: str
    educational_value: Optional[str] = None
    age_category: AgeCategory
    content_category: ContentCategory
    estimated_duration_minutes: float = 3.0
    keywords: Optional[List[str]] = None


class VideoIdeaUpdate(BaseModel):
    title: Optional[str] = None
    concept: Optional[str] = None
    educational_value: Optional[str] = None
    status: Optional[IdeaStatus] = None
    rejection_reason: Optional[str] = None
    estimated_cost_usd: Optional[float] = None


class VideoIdeaResponse(BaseModel):
    id: int
    title: str
    concept: str
    educational_value: Optional[str]
    age_category: AgeCategory
    content_category: ContentCategory
    estimated_duration_minutes: float
    estimated_cost_usd: Optional[float]
    status: IdeaStatus
    keywords: Optional[List[str]]
    created_by_id: Optional[int]

    model_config = {"from_attributes": True}


class VideoIdeaListResponse(BaseModel):
    items: List[VideoIdeaResponse]
    total: int
    page: int
    page_size: int


class GenerateIdeasRequest(BaseModel):
    count: int = 5
    categories: Optional[List[ContentCategory]] = None
    age_categories: Optional[List[AgeCategory]] = None
    keywords: Optional[List[str]] = None
