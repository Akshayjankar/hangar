from __future__ import annotations
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.supervisor import supervisor
from ..db import get_db_session
from ..models import Component, Run
from ..schemas import ComponentRead, ComponentUpdate, RunRead

router = APIRouter(prefix="/components", tags=["components"])


@router.patch("/{id}", response_model=ComponentRead)
async def update_component(id: str, payload: ComponentUpdate, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(Component).where(Component.id == id))
    comp = res.scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail="Component not found")

    if payload.name is not None:
        comp.name = payload.name
    if payload.kind is not None:
        comp.kind = payload.kind
    if payload.cwd is not None:
        comp.cwd = payload.cwd
    if payload.start_cmd is not None:
        comp.start_cmd = payload.start_cmd
    if payload.stop_cmd is not None:
        comp.stop_cmd = payload.stop_cmd
    if payload.env is not None:
        comp.env = json.dumps(payload.env)
    if payload.port is not None:
        comp.port = payload.port
    if payload.url is not None:
        comp.url = payload.url
    if payload.health is not None:
        comp.health = json.dumps(payload.health.model_dump())
    if payload.tier is not None:
        comp.tier = payload.tier
    if payload.autorestart is not None:
        comp.autorestart = payload.autorestart
    if payload.max_restarts is not None:
        comp.max_restarts = payload.max_restarts
    if payload.start_on_launch is not None:
        comp.start_on_launch = payload.start_on_launch

    await session.commit()

    tracked = supervisor.get_tracked(id)
    return ComponentRead(
        id=comp.id,
        application_id=comp.application_id,
        name=comp.name,
        kind=comp.kind,
        cwd=comp.cwd,
        start_cmd=comp.start_cmd,
        stop_cmd=comp.stop_cmd,
        env=json.loads(comp.env) if comp.env else {},
        port=comp.port,
        url=comp.url,
        health=json.loads(comp.health) if comp.health else {},
        tier=comp.tier,
        autorestart=comp.autorestart,
        max_restarts=comp.max_restarts,
        start_on_launch=comp.start_on_launch,
        status=tracked.status if tracked else "stopped",
        status_reason=tracked.status_reason if tracked else None,
        pid=tracked.pid if tracked else None,
        cpu_pct=tracked.cpu_pct if tracked else 0.0,
        rss_mb=tracked.rss_mb if tracked else 0.0,
        active_run_id=tracked.active_run_id if tracked else None,
    )


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_component(id: str, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(Component).where(Component.id == id))
    comp = res.scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail="Component not found")

    await supervisor.stop_component(id, reason="user")
    await session.delete(comp)
    await session.commit()
    return {"message": "Component deleted"}


@router.post("/{id}/start")
async def start_component(id: str):
    success, msg = await supervisor.start_component(id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "status": "starting"}


@router.post("/{id}/stop")
async def stop_component(id: str):
    success, msg = await supervisor.stop_component(id, reason="user")
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "status": "stopped"}


@router.post("/{id}/restart")
async def restart_component(id: str):
    success, msg = await supervisor.restart_component(id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "status": "restarting"}


@router.get("/{id}/runs", response_model=list[RunRead])
async def list_component_runs(id: str, session: AsyncSession = Depends(get_db_session)):
    stmt = select(Run).where(Run.component_id == id).order_by(Run.started_at.desc()).limit(20)
    res = await session.execute(stmt)
    runs = res.scalars().all()
    return [
        RunRead(
            id=r.id,
            component_id=r.component_id,
            pid=r.pid,
            create_time=r.create_time,
            started_at=r.started_at,
            ended_at=r.ended_at,
            exit_code=r.exit_code,
            stop_reason=r.stop_reason,
            log_path=r.log_path,
        )
        for r in runs
    ]

