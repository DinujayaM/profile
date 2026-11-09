"""Cost guard — enforces daily and monthly spending limits.

Raises CostLimitExceeded before any AI provider call if the limit would
be breached. The check is a lightweight DB aggregate query.
"""
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.cost import CostRecord
from app.core.config import settings


class CostLimitExceeded(HTTPException):
    def __init__(self, period: str, limit: float, used: float):
        super().__init__(
            status_code=429,
            detail=f"Cost limit exceeded: {period} limit ${limit:.2f}, used ${used:.2f}",
        )


async def check_cost_limits(db: AsyncSession, estimated_cost: float = 0.0) -> None:
    """Raise CostLimitExceeded if adding estimated_cost would exceed any limit."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    daily_used = await _sum_since(db, today_start)
    if daily_used + estimated_cost > settings.DAILY_COST_LIMIT_USD:
        raise CostLimitExceeded("daily", settings.DAILY_COST_LIMIT_USD, daily_used)

    monthly_used = await _sum_since(db, month_start)
    if monthly_used + estimated_cost > settings.MONTHLY_COST_LIMIT_USD:
        raise CostLimitExceeded("monthly", settings.MONTHLY_COST_LIMIT_USD, monthly_used)


async def record_cost(
    db: AsyncSession,
    category: str,
    provider: str,
    cost_usd: float,
    description: str = "",
    video_id: int | None = None,
) -> None:
    if cost_usd <= 0:
        return
    from app.models.cost import CostRecord, CostCategory
    record = CostRecord(
        category=category,
        provider=provider,
        cost_usd=cost_usd,
        description=description,
        video_id=video_id,
    )
    db.add(record)


async def _sum_since(db: AsyncSession, since: datetime) -> float:
    result = await db.execute(
        select(func.coalesce(func.sum(CostRecord.cost_usd), 0)).where(
            CostRecord.created_at >= since
        )
    )
    return float(result.scalar() or 0)
