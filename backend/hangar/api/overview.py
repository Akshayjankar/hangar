from __future__ import annotations
import json
import psutil
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import APP_NAME, VERSION
from ..core.supervisor import supervisor
from ..db import get_db_session
from ..models import Application, Component, Event
from ..schemas import ApplicationRead, ComponentRead, EventRead, OverviewResponse

router = APIRouter(tags=["overview"])


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(session: AsyncSession = Depends(get_db_session)):
    # 1. Total applications and components
    app_res = await session.execute(
        select(Application).options(selectinload(Application.components)).order_by(Application.sort.asc())
    )
    applications = app_res.scalars().all()

    total_apps = len(applications)
    total_components = 0
    running_components = 0
    status_counts: dict[str, int] = {
        "running": 0,
        "starting": 0,
        "stopped": 0,
        "unhealthy": 0,
        "crashed": 0,
        "failed": 0,
        "stopping": 0,
        "external": 0,
    }

    favorites_list: list[ApplicationRead] = []

    for app in applications:
        app_comps_read: list[ComponentRead] = []
        for c in app.components:
            total_components += 1
            tracked = supervisor.get_tracked(c.id)
            c_status = tracked.status if tracked else "stopped"
            c_reason = tracked.status_reason if tracked else None
            pid = tracked.pid if tracked else None
            cpu = tracked.cpu_pct if tracked else 0.0
            rss = tracked.rss_mb if tracked else 0.0
            run_id = tracked.active_run_id if tracked else None

            if c_status in status_counts:
                status_counts[c_status] += 1
            else:
                status_counts[c_status] = 1

            if c_status in {"running", "starting"}:
                running_components += 1

            try:
                env_dict = json.loads(c.env) if c.env else {}
                health_dict = json.loads(c.health) if c.health else {}
            except Exception:
                env_dict = {}
                health_dict = {}

            app_comps_read.append(
                ComponentRead(
                    id=c.id,
                    application_id=c.application_id,
                    name=c.name,
                    kind=c.kind,
                    cwd=c.cwd,
                    start_cmd=c.start_cmd,
                    stop_cmd=c.stop_cmd,
                    env=env_dict,
                    port=c.port,
                    url=c.url,
                    health=health_dict,
                    tier=c.tier,
                    autorestart=c.autorestart,
                    max_restarts=c.max_restarts,
                    start_on_launch=c.start_on_launch,
                    status=c_status,
                    status_reason=c_reason,
                    pid=pid,
                    cpu_pct=cpu,
                    rss_mb=rss,
                    active_run_id=run_id,
                )
            )

        app_status = await supervisor.compute_application_status(app.id)
        try:
            tags = json.loads(app.tags) if app.tags else []
        except Exception:
            tags = []

        app_read = ApplicationRead(
            id=app.id,
            name=app.name,
            description=app.description,
            icon=app.icon,
            path=app.path,
            tags=tags,
            favorite=app.favorite,
            sort=app.sort,
            start_mode=app.start_mode,
            created_at=app.created_at,
            status=app_status,
            components=app_comps_read,
        )

        if app.favorite:
            favorites_list.append(app_read)

    # 2. Machine metrics
    machine_cpu = psutil.cpu_percent(interval=None)
    vmem = psutil.virtual_memory()
    machine_mem_pct = vmem.percent
    machine_mem_used_mb = vmem.used / (1024 * 1024)
    machine_mem_total_mb = vmem.total / (1024 * 1024)

    # 3. Recent 8 events
    event_res = await session.execute(
        select(Event).order_by(Event.ts.desc()).limit(8)
    )
    events = event_res.scalars().all()
    events_read = [
        EventRead(
            id=e.id,
            ts=e.ts,
            level=e.level,
            type=e.type,
            application_id=e.application_id,
            component_id=e.component_id,
            title=e.title,
            reason=e.reason,
            detail=json.loads(e.detail) if e.detail else {},
            read=e.read,
        )
        for e in events
    ]

    return OverviewResponse(
        app_name=APP_NAME,
        version=VERSION,
        total_applications=total_apps,
        total_components=total_components,
        running_components=running_components,
        machine_cpu_pct=round(machine_cpu, 1),
        machine_memory_pct=round(machine_mem_pct, 1),
        machine_memory_used_mb=round(machine_mem_used_mb, 1),
        machine_memory_total_mb=round(machine_mem_total_mb, 1),
        status_counts=status_counts,
        recent_events=events_read,
        favorites=favorites_list,
    )

