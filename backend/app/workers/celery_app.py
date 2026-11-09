from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "tinytales",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks.video_tasks", "app.workers.tasks.research_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=1800,   # 30 min soft limit
    task_time_limit=3600,        # 1 hour hard limit
    beat_schedule={
        "daily-research": {
            "task": "app.workers.tasks.research_tasks.run_daily_research",
            "schedule": 60 * 60 * 8,  # 08:00 daily (simplified)
        },
    },
)
