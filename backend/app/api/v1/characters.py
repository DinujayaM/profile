from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.character import Character, CharacterAsset, CharacterType
from app.models.user import User
from app.services.ai.factory import get_image_provider

router = APIRouter(prefix="/characters", tags=["characters"])


class CharacterCreate(BaseModel):
    name: str
    character_type: CharacterType = CharacterType.main
    description: str
    personality: Optional[str] = None
    appearance: str
    color_palette: Optional[list] = None
    image_generation_prompt: Optional[str] = None
    tags: Optional[list] = None


class CharacterResponse(BaseModel):
    id: int
    name: str
    character_type: CharacterType
    description: str
    personality: Optional[str]
    appearance: str
    reference_image_url: Optional[str]
    is_active: bool
    tags: Optional[list]
    model_config = {"from_attributes": True}


@router.post("", response_model=CharacterResponse, status_code=201)
async def create_character(
    payload: CharacterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(Character).where(Character.name == payload.name))
    if result.scalar_one_or_none():
        raise HTTPException(400, "Character name already exists")
    char = Character(**payload.model_dump(), created_by_id=current_user.id)
    db.add(char)
    await db.flush()
    return char


@router.post("/{character_id}/generate-image", response_model=CharacterResponse)
async def generate_character_image(
    character_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    char = await db.get(Character, character_id)
    if not char:
        raise HTTPException(404, "Character not found")

    prompt = char.image_generation_prompt or (
        f"Original children's cartoon character: {char.name}. "
        f"Appearance: {char.appearance}. "
        "Bright colorful 3D animation style, friendly and cute, "
        "white background, full body portrait, high quality"
    )
    provider = get_image_provider()
    img = await provider.generate(prompt, 1024, 1024)
    char.reference_image_url = img.url

    asset = CharacterAsset(
        character_id=char.id,
        asset_type="portrait",
        file_url=img.url,
        image_provider=img.provider,
        generation_prompt=prompt,
        generation_cost_usd=img.cost_usd,
        is_primary=True,
    )
    db.add(asset)
    await db.flush()
    return char


@router.get("", response_model=list[CharacterResponse])
async def list_characters(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Character).where(Character.is_active == True)
        .offset((page - 1) * page_size).limit(page_size)
    )
    return result.scalars().all()


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(character_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    char = await db.get(Character, character_id)
    if not char:
        raise HTTPException(404, "Character not found")
    return char


@router.delete("/{character_id}", status_code=204)
async def delete_character(character_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    char = await db.get(Character, character_id)
    if not char:
        raise HTTPException(404, "Character not found")
    char.is_active = False  # Soft delete
