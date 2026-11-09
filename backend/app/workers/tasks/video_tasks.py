import asyncio
from app.workers.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.video_pipeline import VideoPipeline
from app.models.video import VideoJob, JobStatus
import structlog

log = structlog.get_logger()


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
        log.error("celery_pipeline_failed", job_id=job_id, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def generate_scene_image(self, scene_id: int):
    """Generate image for a single scene."""
    async def _run():
        from app.models.script import StoryboardScene
        from app.services.ai.factory import get_image_provider
        async with AsyncSessionLocal() as db:
            scene = await db.get(StoryboardScene, scene_id)
            if not scene:
                return
            provider = get_image_provider()
            img = await provider.generate(scene.image_prompt or scene.description)
            scene.generated_image_url = img.url
            await db.commit()

    asyncio.run(_run())


@celery_app.task
def upload_to_youtube(upload_id: int):
    """Upload an approved video to YouTube."""
    async def _run():
        from app.services.youtube_service import YouTubeService
        async with AsyncSessionLocal() as db:
            svc = YouTubeService(db)
            await svc.upload(upload_id)
            await db.commit()

    asyncio.run(_run())
