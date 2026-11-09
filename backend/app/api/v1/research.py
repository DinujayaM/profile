from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.video_idea import VideoIdea, IdeaStatus
from app.models.user import User
from app.schemas.video_idea import (
    VideoIdeaCreate, VideoIdeaUpdate, VideoIdeaResponse,
    VideoIdeaListResponse, GenerateIdeasRequest,
)
from app.services.research_service import ResearchService

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/generate-ideas", response_model=list[VideoIdeaResponse])
async def generate_ideas(
    payload: GenerateIdeasRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    svc = ResearchService()
    ideas, cost = await svc.generate_ideas(
        count=payload.count,
        categories=payload.categories,
        age_categories=payload.age_categories,
        keywords=payload.keywords,
    )
    saved = []
    for idea_data in ideas:
        idea = VideoIdea(**idea_data.model_dump(), created_by_id=current_user.id)
        db.add(idea)
        saved.append(idea)
    await db.flush()
    return saved


@router.get("/ideas", response_model=VideoIdeaListResponse)
async def list_ideas(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: IdeaStatus | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = select(VideoIdea)
    if status:
        q = q.where(VideoIdea.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    result = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    items = result.scalars().all()
    return VideoIdeaListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/ideas/{idea_id}", response_model=VideoIdeaResponse)
async def get_idea(idea_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    idea = await db.get(VideoIdea, idea_id)
    if not idea:
        raise HTTPException(404, "Idea not found")
    return idea


@router.put("/ideas/{idea_id}", response_model=VideoIdeaResponse)
async def update_idea(
    idea_id: int,
    payload: VideoIdeaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    idea = await db.get(VideoIdea, idea_id)
    if not idea:
        raise HTTPException(404, "Idea not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(idea, field, value)
    if payload.status == IdeaStatus.approved:
        idea.approved_by_id = current_user.id
    return idea


@router.post("/ideas/{idea_id}/approve", response_model=VideoIdeaResponse)
async def approve_idea(idea_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    idea = await db.get(VideoIdea, idea_id)
    if not idea:
        raise HTTPException(404, "Idea not found")
    idea.status = IdeaStatus.approved
    idea.approved_by_id = current_user.id
    return idea


@router.post("/ideas/{idea_id}/reject", response_model=VideoIdeaResponse)
async def reject_idea(
    idea_id: int, reason: str, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)
):
    idea = await db.get(VideoIdea, idea_id)
    if not idea:
        raise HTTPException(404, "Idea not found")
    idea.status = IdeaStatus.rejected
    idea.rejection_reason = reason
    return idea


@router.delete("/ideas/{idea_id}", status_code=204)
async def delete_idea(idea_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    idea = await db.get(VideoIdea, idea_id)
    if not idea:
        raise HTTPException(404, "Idea not found")
    await db.delete(idea)
