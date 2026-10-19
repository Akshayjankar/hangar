from __future__ import annotations
import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.metrics import metrics_sampler
from ..db import get_db_session
from ..models import Metric1m
from ..schemas import MetricPoint, MetricsResponse

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_model=MetricsResponse)
async def get_metrics(
    component: str | None = None,
    range: str = Query("1h", pattern="^(1h|6h|24h|7d)$"),
    session: AsyncSession = Depends(get_db_session),
):
    now = datetime.datetime.utcnow()
    points: list[MetricPoint] = []

    # Map range string to timedelta
    range_deltas = {
        "1h": datetime.timedelta(hours=1),
        "6h": datetime.timedelta(hours=6),
        "24h": datetime.timedelta(hours=24),
        "7d": datetime.timedelta(days=7),
    }
    cutoff = now - range_deltas[range]

    # If range is 1h, also inspect in-memory buffer for real-time 2s resolution
    if range == "1h":
        buf = metrics_sampler.in_memory_history.get(component)
        if buf:
            for s in buf:
                dt = datetime.datetime.utcfromtimestamp(s["ts"])
                if dt >= cutoff:
                    points.append(MetricPoint(ts=dt, cpu_pct=s["cpu_pct"], rss_mb=s["rss_mb"]))

    # If buffer has fewer than 10 points or range > 1h, query persisted 1m points
    if len(points) < 10 or range != "1h":
        stmt = (
            select(Metric1m)
            .where(Metric1m.component_id == component, Metric1m.ts >= cutoff)
            .order_by(Metric1m.ts.asc())
        )
        res = await session.execute(stmt)
        persisted = res.scalars().all()
        persisted_points = [
            MetricPoint(ts=p.ts, cpu_pct=p.cpu_pct, rss_mb=p.rss_mb) for p in persisted
        ]
        # If we had in-memory points for 1h, merge or prefer persisted + latest
        if not points:
            points = persisted_points
        else:
            # Append only newer points from in-memory
            last_ts = persisted_points[-1].ts if persisted_points else cutoff
            for pt in points:
                if pt.ts > last_ts:
                    persisted_points.append(pt)
            points = persisted_points

    return MetricsResponse(component_id=component, range=range, points=points)
