import asyncio
import logging
from app.workers.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.video_pipeline import VideoPipeline
from app.models.video import VideoJob, JobStatus, VideoStatus

log = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_video_pipeline(self, job_id: int):
    """Run the full video production pipeline for a given job ID."""
    async def _run():
        async with AsyncSessionLocal() as db:
            pipeline = VideoPipeline(db)
            await pipeline.run_pipeline(job_id)
            await db.commit()

    try:
        asyncio.run(_run())
    except Exception as exc:
        log.error("celery_pipeline_failed job_id=%d error=%s", job_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def render_video(self, video_id: int):
    """Render a video using FFmpeg after all scene assets are ready."""
    async def _run():
        from app.models.video import Video, VideoScene
        from app.models.audio import AudioAsset, MusicAsset
        from app.services.render_service import RenderService, RenderJob, SceneAssets
        from app.core.config import settings
        from sqlalchemy import select
        import os

        async with AsyncSessionLocal() as db:
            video = await db.get(Video, video_id)
            if not video:
                return

            result = await db.execute(
                select(VideoScene).where(VideoScene.video_id == video_id)
                .order_by(VideoScene.scene_number)
            )
            scenes = result.scalars().all()

            scene_assets = []
            for scene in scenes:
                clip = scene.video_clip_path or ""
                audio = scene.audio_path or ""
                if not (clip and os.path.exists(clip) and audio and os.path.exists(audio)):
                    log.warning("Scene %d missing assets, skipping render", scene.id)
                    continue
                scene_assets.append(SceneAssets(
                    index=scene.scene_number,
                    clip_path=clip,
                    audio_path=audio,
                    duration_seconds=scene.duration_seconds or 5.0,
                    subtitle_text=scene.dialogue or "",
                ))

            if not scene_assets:
                video.status = VideoStatus.failed
                await db.commit()
                return

            storage = settings.LOCAL_STORAGE_PATH
            output_path = f"{storage}/videos/{video_id}/final.mp4"
            thumb_path = f"{storage}/videos/{video_id}/thumbnail.jpg"

            job = RenderJob(
                video_id=video_id,
                scenes=scene_assets,
                output_path=output_path,
                thumbnail_path=thumb_path,
            )
            svc = RenderService()
            result = await svc.render(job)

            if result.success:
                video.file_path = result.output_path
                video.thumbnail_path = result.thumbnail_path
                video.duration_seconds = result.duration_seconds
                video.file_size_bytes = result.file_size_bytes
                video.status = VideoStatus.pending_approval
            else:
                video.status = VideoStatus.failed
                log.error("Render failed video=%d: %s", video_id, result.error)

            await db.commit()

    try:
        asyncio.run(_run())
    except Exception as exc:
        log.error("render_task_failed video_id=%d error=%s", video_id, exc)
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def upload_to_youtube(self, upload_id: int):
    """Upload an approved video to YouTube (always starts as private)."""
    async def _run():
        from app.models.youtube import YouTubeUpload, UploadStatus
        from app.services.youtube_service import YouTubeService
        from app.models.video import Video

        async with AsyncSessionLocal() as db:
            upload = await db.get(YouTubeUpload, upload_id)
            if not upload:
                return

            video = await db.get(Video, upload.video_id)
            if not video or not video.file_path:
                upload.upload_status = UploadStatus.failed
                upload.error_message = "Video file not found"
                await db.commit()
                return

            upload.upload_status = UploadStatus.uploading
            await db.commit()

            try:
                svc = YouTubeService(db)
                result = await svc.upload_video(
                    upload_id=upload_id,
                    file_path=video.file_path,
                    title=upload.title,
                    description=upload.description or "",
                    tags=upload.tags or [],
                    category_id=upload.category_id,
                    made_for_kids=upload.made_for_kids,
                )
                upload.youtube_video_id = result["youtube_video_id"]
                upload.upload_status = UploadStatus.published
                upload.upload_progress_pct = 100
            except Exception as exc:
                upload.upload_status = UploadStatus.failed
                upload.error_message = str(exc)[:500]
                log.error("youtube_upload_failed upload_id=%d: %s", upload_id, exc)

            await db.commit()

    try:
        asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc)
