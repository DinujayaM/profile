"""Analytics service.

Aggregates production metrics, cost tracking, and YouTube performance data.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.video_idea import VideoIdea, IdeaStatus
from app.models.video import Video, VideoStatus
from app.models.cost import CostRecord, CostCategory
from app.models.youtube import YouTubeUpload, UploadStatus

log = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_stats(self) -> dict:
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Video counts by status
        video_counts = await self._count_by_enum(Video, Video.status)

        # Idea counts
        idea_counts = await self._count_by_enum(VideoIdea, VideoIdea.status)

        # Cost aggregates
        monthly_cost = await self._sum_costs(since=month_start)
        daily_cost = await self._sum_costs(since=today_start)
        cost_by_category = await self._costs_by_category(since=month_start)

        # YouTube uploads
        uploads_total = await self._count_rows(YouTubeUpload)
        uploads_published = await self._count_rows(
            YouTubeUpload, YouTubeUpload.upload_status == UploadStatus.published
        )

        return {
            "videos": {
                "total": sum(video_counts.values()),
                "by_status": video_counts,
            },
            "ideas": {
                "total": sum(idea_counts.values()),
                "by_status": idea_counts,
            },
            "costs": {
                "today_usd": round(daily_cost, 4),
                "this_month_usd": round(monthly_cost, 4),
                "by_category": {k: round(v, 4) for k, v in cost_by_category.items()},
            },
            "youtube": {
                "uploads_total": uploads_total,
                "uploads_published": uploads_published,
            },
        }

    async def get_cost_history(
        self,
        days: int = 30,
        category: Optional[str] = None,
    ) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        query = select(
            func.date(CostRecord.created_at).label("date"),
            func.sum(CostRecord.cost_usd).label("total"),
        ).where(CostRecord.created_at >= since)
        if category:
            query = query.where(CostRecord.category == category)
        query = query.group_by(func.date(CostRecord.created_at)).order_by("date")
        result = await self.db.execute(query)
        return [
            {"date": str(row.date), "cost_usd": round(float(row.total), 4)}
            for row in result
        ]

    async def get_video_performance(self, limit: int = 20) -> list[dict]:
        result = await self.db.execute(
            select(Video).order_by(Video.created_at.desc()).limit(limit)
        )
        videos = result.scalars().all()
        return [
            {
                "id": v.id,
                "title": v.title,
                "status": v.status,
                "total_cost_usd": v.total_cost_usd,
                "quality_score": v.quality_score,
                "duration_seconds": v.duration_seconds,
                "created_at": v.created_at.isoformat(),
            }
            for v in videos
        ]

    # ---------------------------------------------------------------- helpers

    async def _count_by_enum(self, model, col) -> dict:
        result = await self.db.execute(
            select(col, func.count()).group_by(col)
        )
        return {str(row[0].value if hasattr(row[0], "value") else row[0]): row[1]
                for row in result}

    async def _count_rows(self, model, *filters) -> int:
        q = select(func.count()).select_from(model)
        if filters:
            q = q.where(*filters)
        result = await self.db.execute(q)
        return result.scalar() or 0

    async def _sum_costs(self, since: Optional[datetime] = None) -> float:
        q = select(func.coalesce(func.sum(CostRecord.cost_usd), 0))
        if since:
            q = q.where(CostRecord.created_at >= since)
        result = await self.db.execute(q)
        return float(result.scalar() or 0)

    async def _costs_by_category(self, since: Optional[datetime] = None) -> dict:
        q = select(
            CostRecord.category,
            func.sum(CostRecord.cost_usd).label("total"),
        ).group_by(CostRecord.category)
        if since:
            q = q.where(CostRecord.created_at >= since)
        result = await self.db.execute(q)
        return {
            str(row.category.value if hasattr(row.category, "value") else row.category):
            float(row.total)
            for row in result
        }
