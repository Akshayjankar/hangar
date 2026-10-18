from __future__ import annotations
import json
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import DEFAULT_SETTINGS, HANGAR_HOME, VERSION
from ..db import get_db_session
from ..models import Application, Component, Setting

router = APIRouter(tags=["settings"])


@router.get("/settings")
async def get_settings(session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(Setting))
    rows = res.scalars().all()
    result = dict(DEFAULT_SETTINGS)
    for r in rows:
        try:
            result[r.key] = json.loads(r.value)
        except Exception:
            result[r.key] = r.value
    result["hangar_home"] = str(HANGAR_HOME)
    result["version"] = VERSION
    return result


@router.put("/settings")
async def update_settings(payload: dict[str, Any], session: AsyncSession = Depends(get_db_session)):
    for k, v in payload.items():
        if k in {"hangar_home", "version"}:
            continue
        res = await session.execute(select(Setting).where(Setting.key == k))
        row = res.scalar_one_or_none()
        encoded = json.dumps(v)
        if row:
            row.value = encoded
        else:
            session.add(Setting(key=k, value=encoded))
    await session.commit()
    return {"message": "Settings updated"}


@router.get("/export")
async def export_data(session: AsyncSession = Depends(get_db_session)):
    # Export applications and their components
    app_res = await session.execute(
        select(Application).options(selectinload(Application.components))
    )
    apps = app_res.scalars().all()
    apps_export = []
    for a in apps:
        comps_export = []
        for c in a.components:
            comps_export.append({
                "kind": c.kind,
                "name": c.name,
                "cwd": c.cwd,
                "start_cmd": c.start_cmd,
                "stop_cmd": c.stop_cmd,
                "env": json.loads(c.env) if c.env else {},
                "port": c.port,
                "url": c.url,
                "health": json.loads(c.health) if c.health else {},
                "tier": c.tier,
                "autorestart": c.autorestart,
                "max_restarts": c.max_restarts,
                "start_on_launch": c.start_on_launch,
            })
        apps_export.append({
            "name": a.name,
            "description": a.description,
            "icon": a.icon,
            "path": a.path,
            "tags": json.loads(a.tags) if a.tags else [],
            "favorite": a.favorite,
            "sort": a.sort,
            "start_mode": a.start_mode,
            "components": comps_export,
        })

    # Export settings
    set_res = await session.execute(select(Setting))
    settings_export = {}
    for s in set_res.scalars().all():
        try:
            settings_export[s.key] = json.loads(s.value)
        except Exception:
            settings_export[s.key] = s.value

    return {
        "version": VERSION,
        "exported_at": str(HANGAR_HOME),
        "settings": settings_export,
        "applications": apps_export,
    }


@router.post("/import")
async def import_data(payload: dict[str, Any], session: AsyncSession = Depends(get_db_session)):
    apps_data = payload.get("applications", [])
    for a_data in apps_data:
        app = Application(
            name=a_data["name"],
            description=a_data.get("description", ""),
            icon=a_data.get("icon", "Boxes"),
            path=a_data["path"],
            tags=json.dumps(a_data.get("tags", [])),
            favorite=a_data.get("favorite", False),
            sort=a_data.get("sort", 0),
            start_mode=a_data.get("start_mode", "ordered"),
        )
        session.add(app)
        await session.flush()

        for c_data in a_data.get("components", []):
            comp = Component(
                application_id=app.id,
                kind=c_data["kind"],
                name=c_data["name"],
                cwd=c_data["cwd"],
                start_cmd=c_data["start_cmd"],
                stop_cmd=c_data.get("stop_cmd"),
                env=json.dumps(c_data.get("env", {})),
                port=c_data.get("port"),
                url=c_data.get("url"),
                health=json.dumps(c_data.get("health", {})),
                tier=c_data.get("tier", 2),
                autorestart=c_data.get("autorestart", True),
                max_restarts=c_data.get("max_restarts", 5),
                start_on_launch=c_data.get("start_on_launch", False),
            )
            session.add(comp)

    # Import settings
    settings_data = payload.get("settings", {})
    for k, v in settings_data.items():
        res = await session.execute(select(Setting).where(Setting.key == k))
        row = res.scalar_one_or_none()
        encoded = json.dumps(v)
        if row:
            row.value = encoded
        else:
            session.add(Setting(key=k, value=encoded))

    await session.commit()
    return {"message": "Data imported successfully"}

