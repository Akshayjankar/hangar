from __future__ import annotations
import json
import shutil
import subprocess
import sys
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import LOGS_DIR
from ..core.orchestrator import orchestrator
from ..core.supervisor import supervisor
from ..db import get_db_session
from ..models import Application, Component
from ..schemas import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
    ComponentCreate,
    ComponentRead,
    JobRead,
)

router = APIRouter(prefix="/applications", tags=["applications"])


async def format_application_read(app: Application) -> ApplicationRead:
    app_status = await supervisor.compute_application_status(app.id)
    comps_read: list[ComponentRead] = []

    for c in sorted(app.components, key=lambda x: x.tier):
        tracked = supervisor.get_tracked(c.id)
        c_status = tracked.status if tracked else "stopped"
        c_reason = tracked.status_reason if tracked else None
        pid = tracked.pid if tracked else None
        cpu = tracked.cpu_pct if tracked else 0.0
        rss = tracked.rss_mb if tracked else 0.0
        run_id = tracked.active_run_id if tracked else None

        try:
            env_dict = json.loads(c.env) if c.env else {}
            health_dict = json.loads(c.health) if c.health else {}
        except Exception:
            env_dict = {}
            health_dict = {}

        comps_read.append(
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

    try:
        tags = json.loads(app.tags) if app.tags else []
    except Exception:
        tags = []

    return ApplicationRead(
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
        components=comps_read,
    )


@router.get("", response_model=list[ApplicationRead])
async def list_applications(session: AsyncSession = Depends(get_db_session)):
    stmt = select(Application).options(selectinload(Application.components)).order_by(Application.sort.asc())
    res = await session.execute(stmt)
    apps = res.scalars().all()
    return [await format_application_read(a) for a in apps]


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(payload: ApplicationCreate, session: AsyncSession = Depends(get_db_session)):
    app = Application(
        name=payload.name,
        description=payload.description,
        icon=payload.icon,
        path=payload.path,
        tags=json.dumps(payload.tags),
        favorite=payload.favorite,
        sort=payload.sort,
        start_mode=payload.start_mode,
    )
    session.add(app)
    await session.flush()

    for c in payload.components:
        comp = Component(
            application_id=app.id,
            kind=c.kind,
            name=c.name,
            cwd=c.cwd,
            start_cmd=c.start_cmd,
            stop_cmd=c.stop_cmd,
            env=json.dumps(c.env),
            port=c.port,
            url=c.url,
            health=json.dumps(c.health.model_dump()),
            tier=c.tier,
            autorestart=c.autorestart,
            max_restarts=c.max_restarts,
            start_on_launch=c.start_on_launch,
        )
        session.add(comp)

    await session.commit()
    # Reload with components
    res = await session.execute(
        select(Application).options(selectinload(Application.components)).where(Application.id == app.id)
    )
    created = res.scalar_one()
    return await format_application_read(created)


@router.get("/{id}", response_model=ApplicationRead)
async def get_application(id: str, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(
        select(Application).options(selectinload(Application.components)).where(Application.id == id)
    )
    app = res.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return await format_application_read(app)


@router.patch("/{id}", response_model=ApplicationRead)
async def update_application(id: str, payload: ApplicationUpdate, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(
        select(Application).options(selectinload(Application.components)).where(Application.id == id)
    )
    app = res.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if payload.name is not None:
        app.name = payload.name
    if payload.description is not None:
        app.description = payload.description
    if payload.icon is not None:
        app.icon = payload.icon
    if payload.path is not None:
        app.path = payload.path
    if payload.tags is not None:
        app.tags = json.dumps(payload.tags)
    if payload.favorite is not None:
        app.favorite = payload.favorite
    if payload.sort is not None:
        app.sort = payload.sort
    if payload.start_mode is not None:
        app.start_mode = payload.start_mode

    await session.commit()
    return await format_application_read(app)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_application(
    id: str,
    stop_first: bool = Query(True),
    session: AsyncSession = Depends(get_db_session),
):
    res = await session.execute(
        select(Application).options(selectinload(Application.components)).where(Application.id == id)
    )
    app = res.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app_name = app.name

    for c in app.components:
        if stop_first:
            await supervisor.stop_component(c.id, reason="user")
        supervisor.remove_tracked(c.id)
        comp_log_dir = LOGS_DIR / c.id
        if comp_log_dir.exists():
            shutil.rmtree(comp_log_dir, ignore_errors=True)

    await session.delete(app)
    await session.commit()
    return {"message": "Application deleted", "name": app_name}


@router.post("/{id}/components", response_model=ComponentRead, status_code=status.HTTP_201_CREATED)
async def add_component(id: str, payload: ComponentCreate, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(Application).where(Application.id == id))
    app = res.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    comp = Component(
        application_id=id,
        kind=payload.kind,
        name=payload.name,
        cwd=payload.cwd,
        start_cmd=payload.start_cmd,
        stop_cmd=payload.stop_cmd,
        env=json.dumps(payload.env),
        port=payload.port,
        url=payload.url,
        health=json.dumps(payload.health.model_dump()),
        tier=payload.tier,
        autorestart=payload.autorestart,
        max_restarts=payload.max_restarts,
        start_on_launch=payload.start_on_launch,
    )
    session.add(comp)
    await session.commit()

    return ComponentRead(
        id=comp.id,
        application_id=comp.application_id,
        name=comp.name,
        kind=comp.kind,
        cwd=comp.cwd,
        start_cmd=comp.start_cmd,
        stop_cmd=comp.stop_cmd,
        env=payload.env,
        port=comp.port,
        url=comp.url,
        health=payload.health,
        tier=comp.tier,
        autorestart=comp.autorestart,
        max_restarts=comp.max_restarts,
        start_on_launch=comp.start_on_launch,
        status="stopped",
    )


@router.post("/{id}/start", response_model=JobRead)
async def start_application(id: str):
    try:
        return await orchestrator.start_application(id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/stop", response_model=JobRead)
async def stop_application(id: str):
    try:
        return await orchestrator.stop_application(id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/restart", response_model=JobRead)
async def restart_application(id: str):
    try:
        return await orchestrator.restart_application(id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/open-folder", status_code=status.HTTP_200_OK)
async def open_folder(id: str, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(Application).where(Application.id == id))
    app = res.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    folder_path = Path(app.path).resolve()
    if not folder_path.exists():
        raise HTTPException(status_code=400, detail=f"Folder does not exist: {folder_path}")

    try:
        if sys.platform == "win32":
            subprocess.Popen(["explorer", str(folder_path)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder_path)])
        else:
            subprocess.Popen(["xdg-open", str(folder_path)])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open folder: {e}")

    return {"message": "Opened folder in file manager"}


@router.post("/{id}/open-editor", status_code=status.HTTP_200_OK)
async def open_editor(id: str, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(Application).where(Application.id == id))
    app = res.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    folder_path = Path(app.path).resolve()
    try:
        if sys.platform == "win32":
            subprocess.Popen(["cmd.exe", "/c", "code", str(folder_path)])
        else:
            subprocess.Popen(["code", str(folder_path)])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to launch editor: {e}")

    return {"message": "Opened project in editor"}

