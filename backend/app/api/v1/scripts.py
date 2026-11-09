from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.script import Script, Storyboard, StoryboardScene, ScriptStatus
from app.models.video_idea import VideoIdea
from app.models.user import User
from app.services.script_service import ScriptService

router = APIRouter(prefix="/scripts", tags=["scripts"])


class ScriptResponse(BaseModel):
    id: int
    idea_id: int
    title: str
    introduction: Optional[str]
    main_content: Optional[str]
    song_lyrics: Optional[str]
    full_script: str
    target_duration_minutes: float
    status: ScriptStatus
    generation_cost_usd: Optional[float]
    version: int
    model_config = {"from_attributes": True}


class StoryboardSceneResponse(BaseModel):
    id: int
    scene_number: int
    title: Optional[str]
    description: str
    background_description: str
    dialogue: Optional[str]
    narration: Optional[str]
    duration_seconds: float
    generated_image_url: Optional[str]
    model_config = {"from_attributes": True}


class StoryboardResponse(BaseModel):
    id: int
    script_id: int
    title: str
    total_scenes: int
    status: str
    model_config = {"from_attributes": True}


@router.post("/generate", response_model=ScriptResponse, status_code=201)
async def generate_script(
    idea_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    idea = await db.get(VideoIdea, idea_id)
    if not idea:
        raise HTTPException(404, "Idea not found")
    svc = ScriptService()
    script, _ = await svc.generate_script(idea, db)
    return script


@router.post("/{script_id}/storyboard", response_model=StoryboardResponse, status_code=201)
async def generate_storyboard(
    script_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    script = await db.get(Script, script_id)
    if not script:
        raise HTTPException(404, "Script not found")
    svc = ScriptService()
    board, _ = await svc.generate_storyboard(script, db)
    return board


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(script_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    script = await db.get(Script, script_id)
    if not script:
        raise HTTPException(404, "Script not found")
    return script


@router.get("/storyboard/{storyboard_id}/scenes", response_model=list[StoryboardSceneResponse])
async def get_storyboard_scenes(
    storyboard_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)
):
    result = await db.execute(
        select(StoryboardScene)
        .where(StoryboardScene.storyboard_id == storyboard_id)
        .order_by(StoryboardScene.scene_number)
    )
    return result.scalars().all()


@router.put("/{script_id}/approve", response_model=ScriptResponse)
async def approve_script(script_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    script = await db.get(Script, script_id)
    if not script:
        raise HTTPException(404, "Script not found")
    script.status = ScriptStatus.approved
    return script
