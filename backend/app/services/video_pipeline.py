"""
Video production pipeline service.
Orchestrates the full 15-step pipeline from idea → published video.
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.video import Video, VideoScene, VideoJob, VideoStatus, VideoFormat, JobStatus
from app.models.video_idea import VideoIdea, IdeaStatus
from app.models.script import Script, Storyboard
from app.models.audio import AudioAsset, MusicAsset
from app.models.cost import CostRecord, CostCategory
from app.services.ai.factory import (
    get_llm_provider, get_image_provider, get_tts_provider,
    get_music_provider, get_video_clip_provider,
)
from app.services.script_service import ScriptService
import structlog

log = structlog.get_logger()


class VideoPipeline:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._script_svc = ScriptService()
        self._image = get_image_provider()
        self._tts = get_tts_provider()
        self._music = get_music_provider()
        self._video_clip = get_video_clip_provider()

    async def start_production(
        self,
        idea_id: int,
        video_format: VideoFormat = VideoFormat.landscape,
        made_for_kids: bool = True,
    ) -> VideoJob:
        idea = await self.db.get(VideoIdea, idea_id)
        if not idea:
            raise ValueError(f"VideoIdea {idea_id} not found")

        width, height = (1920, 1080) if video_format == VideoFormat.landscape else (1080, 1920)
        video = Video(
            idea_id=idea_id,
            title=idea.title,
            format=video_format,
            width=width,
            height=height,
            made_for_kids=made_for_kids,
            status=VideoStatus.generating,
        )
        self.db.add(video)
        await self.db.flush()

        job = VideoJob(
            video_id=video.id,
            job_type="full_pipeline",
            step="queued",
            status=JobStatus.queued,
            progress_pct=0,
        )
        self.db.add(job)
        await self.db.flush()

        idea.status = IdeaStatus.in_production
        return job

    async def run_pipeline(self, job_id: int) -> None:
        """Execute the full production pipeline. Called by Celery worker."""
        job = await self.db.get(VideoJob, job_id)
        if not job:
            raise ValueError(f"VideoJob {job_id} not found")

        video = await self.db.get(Video, job.video_id)
        idea = await self.db.get(VideoIdea, video.idea_id)

        async def update_progress(step: str, pct: int):
            job.step = step
            job.progress_pct = pct
            job.status = JobStatus.running
            await self.db.flush()
            log.info("pipeline_progress", job_id=job_id, step=step, pct=pct)

        try:
            job.status = JobStatus.running
            job.started_at = datetime.now(timezone.utc).isoformat()
            total_cost = 0.0

            # Step 1-2: Generate Script
            await update_progress("generating_script", 10)
            script, cost = await self._script_svc.generate_script(idea, self.db)
            video.script_id = script.id
            total_cost += cost

            # Step 3: Generate Storyboard
            await update_progress("generating_storyboard", 20)
            storyboard, cost = await self._script_svc.generate_storyboard(script, self.db)
            video.storyboard_id = storyboard.id
            total_cost += cost

            # Step 4: Generate scene images
            await update_progress("generating_images", 35)
            scenes_result = await self.db.execute(
                select(Storyboard).where(Storyboard.id == storyboard.id)
            )
            scenes_total_cost = await self._generate_scene_images(video, storyboard)
            total_cost += scenes_total_cost

            # Step 5: Generate animated video clips
            await update_progress("generating_video_clips", 50)
            clip_cost = await self._generate_video_clips(video)
            total_cost += clip_cost

            # Step 6: Generate voiceover/narration
            await update_progress("generating_audio", 65)
            audio_cost = await self._generate_audio(video, script)
            total_cost += audio_cost

            # Step 7: Generate background music
            await update_progress("generating_music", 75)
            music_cost = await self._generate_music(video, script)
            total_cost += music_cost

            # Step 8-10: Render final video (FFmpeg)
            await update_progress("rendering_video", 85)
            await self._render_video(video)

            # Step 11: Generate thumbnail
            await update_progress("generating_thumbnail", 92)
            thumb_cost = await self._generate_thumbnail(video, idea)
            total_cost += thumb_cost

            # Step 12: Quality checks
            await update_progress("quality_check", 97)
            video.quality_score = await self._quality_check(video)

            # Finalise
            video.total_cost_usd = total_cost
            video.status = VideoStatus.pending_approval
            job.status = JobStatus.completed
            job.progress_pct = 100
            job.completed_at = datetime.now(timezone.utc).isoformat()
            job.cost_usd = total_cost
            await self.db.flush()

            log.info("pipeline_complete", video_id=video.id, cost=total_cost)

        except Exception as exc:
            log.error("pipeline_failed", job_id=job_id, error=str(exc))
            job.status = JobStatus.failed
            job.error_message = str(exc)
            video.status = VideoStatus.failed
            await self.db.flush()
            raise

    async def _generate_scene_images(self, video: Video, storyboard: Storyboard) -> float:
        from app.models.script import StoryboardScene
        result = await self.db.execute(
            select(StoryboardScene).where(StoryboardScene.storyboard_id == storyboard.id)
        )
        scenes = result.scalars().all()
        total_cost = 0.0

        for sb_scene in scenes:
            prompt = sb_scene.image_prompt or sb_scene.description
            img = await self._image.generate(prompt, video.width, video.height)
            sb_scene.generated_image_url = img.url
            total_cost += img.cost_usd

            vs = VideoScene(
                video_id=video.id,
                storyboard_scene_id=sb_scene.id,
                scene_order=sb_scene.scene_number,
                description=sb_scene.description,
                image_url=img.url,
                duration_seconds=sb_scene.duration_seconds,
                image_provider=img.provider,
                generation_cost_usd=img.cost_usd,
                generation_prompt=prompt,
                status="image_ready",
            )
            self.db.add(vs)

        await self.db.flush()
        return total_cost

    async def _generate_video_clips(self, video: Video) -> float:
        result = await self.db.execute(
            select(VideoScene).where(VideoScene.video_id == video.id)
        )
        scenes = result.scalars().all()
        total_cost = 0.0

        for scene in scenes:
            if not scene.image_url:
                continue
            clip = await self._video_clip.generate(
                prompt=scene.description or "",
                source_image_url=scene.image_url,
                duration_seconds=int(scene.duration_seconds),
            )
            scene.video_clip_url = clip.video_url
            scene.video_provider = clip.provider
            scene.generation_cost_usd = (scene.generation_cost_usd or 0) + clip.cost_usd
            scene.status = "clip_ready"
            total_cost += clip.cost_usd

        await self.db.flush()
        return total_cost

    async def _generate_audio(self, video: Video, script: Script) -> float:
        tts = get_tts_provider()
        narration_text = script.full_script[:2000]  # simplified
        audio = await tts.synthesize(narration_text, voice_id="narrator_sunny")
        asset = AudioAsset(
            video_id=video.id,
            asset_type="narration",
            text_content=narration_text[:500],
            file_url=audio.audio_url,
            duration_seconds=audio.duration_seconds,
            tts_provider=audio.provider,
            generation_cost_usd=audio.cost_usd,
        )
        self.db.add(asset)
        await self.db.flush()
        return audio.cost_usd

    async def _generate_music(self, video: Video, script: Script) -> float:
        music = get_music_provider()
        result = await music.generate(
            prompt=f"cheerful upbeat children's background music for: {video.title}",
            duration_seconds=int((script.target_duration_minutes or 3) * 60),
            lyrics=script.song_lyrics or "",
        )
        asset = MusicAsset(
            video_id=video.id,
            title=f"{video.title} - Theme",
            asset_type="background",
            file_url=result.audio_url,
            duration_seconds=result.duration_seconds,
            music_provider=result.provider,
            generation_cost_usd=result.cost_usd,
        )
        self.db.add(asset)
        await self.db.flush()
        return result.cost_usd

    async def _render_video(self, video: Video) -> None:
        # In production: use FFmpeg/MoviePy to combine scenes + audio
        # Mock: set a placeholder URL
        video.video_url = f"/storage/videos/{video.id}/final.mp4"
        video.duration_seconds = 180.0
        video.file_size_bytes = 50_000_000
        await self.db.flush()

    async def _generate_thumbnail(self, video: Video, idea: VideoIdea) -> float:
        prompt = (
            f"Children's YouTube thumbnail for '{idea.title}', "
            "bright colorful cartoon style, friendly characters, "
            "bold text placeholder area, high quality digital art"
        )
        img = await self._image.generate(prompt, 1280, 720)
        video.thumbnail_url = img.url
        await self.db.flush()
        return img.cost_usd

    async def _quality_check(self, video: Video) -> float:
        # In production: validate file integrity, duration, resolution
        # Return a 0-100 quality score
        return 85.0
