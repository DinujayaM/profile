"""Script and storyboard generation service."""
import json
import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.ai.factory import get_llm_provider
from app.models.video_idea import VideoIdea
from app.models.script import Script, Storyboard, StoryboardScene, ScriptStatus

SCRIPT_SYSTEM = """
You are a professional children's content writer for TinyTales World.
Create original, engaging, age-appropriate scripts.
Never copy existing shows. Use the unique TinyTales World characters.
Ensure all content is educational and entertaining for children.
"""

SCRIPT_PROMPT = """
Write a complete children's video script for:
Title: {title}
Concept: {concept}
Educational value: {educational_value}
Target age: {age_category}
Duration: {duration} minutes

Include these sections:
1. INTRODUCTION (30 seconds): Hook and character intro
2. MAIN_CONTENT: Core educational story broken into 3-5 mini-scenes
3. SONG_LYRICS: An original catchy song (if appropriate for the category)
4. NARRATION_NOTES: Voice acting guidance
5. ENDING (30 seconds): Summary and sign-off

Return a JSON object with keys:
introduction, main_content, song_lyrics, narration_notes, ending, full_script
"""

STORYBOARD_PROMPT = """
Create a detailed storyboard for this children's video script.
Script: {script}
Duration: {duration} minutes

Generate {scene_count} scenes as a JSON array.
Each scene object must have:
- scene_number: int
- title: string
- description: string (what happens visually)
- character_details: string (characters present, their expressions/actions)
- background_description: string (setting, colors, mood)
- animation_instructions: string (camera moves, effects, transitions)
- dialogue: string (spoken lines if any)
- narration: string (narrator text)
- audio_requirements: string (music mood, sfx)
- duration_seconds: float
- image_prompt: string (detailed DALL-E style prompt for this scene)

Return ONLY the JSON array.
"""


class ScriptService:
    def __init__(self):
        self._llm = get_llm_provider()

    async def generate_script(
        self, idea: VideoIdea, db: AsyncSession
    ) -> tuple[Script, float]:
        prompt = SCRIPT_PROMPT.format(
            title=idea.title,
            concept=idea.concept,
            educational_value=idea.educational_value or "general learning",
            age_category=idea.age_category.value,
            duration=idea.estimated_duration_minutes,
        )
        response = await self._llm.generate(prompt, system=SCRIPT_SYSTEM, max_tokens=6000)
        sections = self._parse_script(response.content)

        script = Script(
            idea_id=idea.id,
            title=idea.title,
            introduction=sections.get("introduction"),
            main_content=sections.get("main_content"),
            song_lyrics=sections.get("song_lyrics"),
            narration_notes=sections.get("narration_notes"),
            ending=sections.get("ending"),
            full_script=sections.get("full_script", response.content),
            target_duration_minutes=idea.estimated_duration_minutes,
            llm_provider=response.provider,
            llm_model=response.model,
            generation_cost_usd=response.cost_usd,
            status=ScriptStatus.draft,
        )
        db.add(script)
        await db.flush()
        return script, response.cost_usd

    async def generate_storyboard(
        self, script: Script, db: AsyncSession
    ) -> tuple[Storyboard, float]:
        scene_count = max(4, int(script.target_duration_minutes * 2))
        prompt = STORYBOARD_PROMPT.format(
            script=script.full_script[:3000],
            duration=script.target_duration_minutes,
            scene_count=scene_count,
        )
        response = await self._llm.generate(prompt, system=SCRIPT_SYSTEM, max_tokens=8000)
        scenes_data = self._parse_storyboard(response.content)

        storyboard = Storyboard(
            script_id=script.id,
            title=script.title,
            total_scenes=len(scenes_data),
            status="draft",
        )
        db.add(storyboard)
        await db.flush()

        for scene_data in scenes_data:
            scene = StoryboardScene(
                storyboard_id=storyboard.id,
                scene_number=scene_data.get("scene_number", 1),
                title=scene_data.get("title"),
                description=scene_data.get("description", ""),
                character_details=scene_data.get("character_details"),
                background_description=scene_data.get("background_description", ""),
                animation_instructions=scene_data.get("animation_instructions"),
                dialogue=scene_data.get("dialogue"),
                narration=scene_data.get("narration"),
                audio_requirements=scene_data.get("audio_requirements"),
                duration_seconds=float(scene_data.get("duration_seconds", 10)),
                image_prompt=scene_data.get("image_prompt"),
            )
            db.add(scene)

        return storyboard, response.cost_usd

    def _parse_script(self, content: str) -> dict:
        content = re.sub(r"```json\s*|\s*```", "", content).strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"full_script": content}

    def _parse_storyboard(self, content: str) -> list:
        content = re.sub(r"```json\s*|\s*```", "", content).strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    pass
            return []
