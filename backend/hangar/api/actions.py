from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.orchestrator import orchestrator
from ..core.supervisor import supervisor
from ..db import get_db_session
from ..models import Application, Component
from ..schemas import JobRead

router = APIRouter(tags=["actions"])


@router.get("/jobs/{id}", response_model=JobRead)
async def get_job_status(id: str):
    job = orchestrator.get_job(id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/actions/start-all")
async def start_all(session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(Application))
    apps = res.scalars().all()
    started_jobs = []
    for a in apps:
        try:
            job = await orchestrator.start_application(a.id)
            started_jobs.append(job.id)
        except Exception:
            pass
    return {"message": "Started all applications", "jobs": started_jobs}


@router.post("/actions/stop-all")
async def stop_all(session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(Application))
    apps = res.scalars().all()
    stopped_jobs = []
    for a in apps:
        try:
            job = await orchestrator.stop_application(a.id)
            stopped_jobs.append(job.id)
        except Exception:
            pass
    return {"message": "Stopped all applications", "jobs": stopped_jobs}


@router.post("/actions/start-favorites")
async def start_favorites(session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(Application).where(Application.favorite.is_(True)))
    apps = res.scalars().all()
    started_jobs = []
    for a in apps:
        try:
            job = await orchestrator.start_application(a.id)
            started_jobs.append(job.id)
        except Exception:
            pass
    return {"message": "Started favorite applications", "jobs": started_jobs}

