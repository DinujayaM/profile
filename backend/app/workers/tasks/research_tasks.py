import asyncio
from app.workers.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.research_service import ResearchService
from app.models.video_idea import VideoIdea
import structlog

log = structlog.get_logger()


@celery_app.task
def run_daily_research():
    """Auto-generate a batch of video ideas each morning."""
    async def _run():
        async with AsyncSessionLocal() as db:
            svc = ResearchService()
            ideas, cost = await svc.generate_ideas(count=5)
            for idea_data in ideas:
                idea = VideoIdea(**idea_data.model_dump(), research_source="daily_scheduler")
                db.add(idea)
            await db.commit()
            log.info("daily_research_done", count=len(ideas), cost=cost)

    asyncio.run(_run())
