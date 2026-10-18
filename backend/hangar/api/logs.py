from __future__ import annotations
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import LOGS_DIR
from ..core.logtail import read_last_n_lines, search_log_lines
from ..core.supervisor import supervisor
from ..db import get_db_session
from ..models import Component, Run

router = APIRouter(tags=["logs"])


@router.get("/components/{id}/logs")
async def get_component_logs(
    id: str,
    lines: int = Query(100, ge=1, le=5000),
    q: str | None = None,
    regex: bool = False,
    run: str | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    target_log_path: Path | None = None

    if run:
        run_res = await session.execute(select(Run).where(Run.id == run, Run.component_id == id))
        r = run_res.scalar_one_or_none()
        if r and r.log_path:
            target_log_path = Path(r.log_path)
    else:
        # Check active run from supervisor
        tracked = supervisor.get_tracked(id)
        if tracked and tracked.active_log_path:
            target_log_path = tracked.active_log_path
        else:
            # Get latest run from DB
            latest_run_res = await session.execute(
                select(Run).where(Run.component_id == id).order_by(Run.started_at.desc()).limit(1)
            )
            latest_run = latest_run_res.scalar_one_or_none()
            if latest_run and latest_run.log_path:
                target_log_path = Path(latest_run.log_path)

    if not target_log_path or not target_log_path.exists():
        return {"component_id": id, "lines": [], "run_id": run}

    log_lines = search_log_lines(target_log_path, query=q, is_regex=regex, max_lines=lines)
    return {
        "component_id": id,
        "lines": log_lines,
        "run_id": run or (tracked.active_run_id if tracked else None),
    }


@router.get("/logs/merged")
async def get_merged_logs(
    components: str = Query("", description="Comma-separated component IDs"),
    lines: int = Query(100, ge=1, le=5000),
    q: str | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    comp_ids = [c.strip() for c in components.split(",") if c.strip()]
    if not comp_ids:
        # Fetch all components if none specified
        all_comps = await session.execute(select(Component.id, Component.name))
        comp_records = all_comps.all()
    else:
        records = await session.execute(select(Component.id, Component.name).where(Component.id.in_(comp_ids)))
        comp_records = records.all()

    merged_entries: list[dict[str, str]] = []

    for cid, cname in comp_records:
        tracked = supervisor.get_tracked(cid)
        log_path = tracked.active_log_path if tracked else None
        if not log_path or not log_path.exists():
            latest_res = await session.execute(
                select(Run).where(Run.component_id == cid).order_by(Run.started_at.desc()).limit(1)
            )
            latest_run = latest_res.scalar_one_or_none()
            if latest_run and latest_run.log_path:
                log_path = Path(latest_run.log_path)

        if log_path and log_path.exists():
            comp_lines = search_log_lines(log_path, query=q, is_regex=False, max_lines=lines)
            for line in comp_lines:
                merged_entries.append({
                    "component_id": cid,
                    "component_name": cname,
                    "line": line,
                })

    return {"lines": merged_entries[-lines:]}


@router.delete("/components/{id}/logs")
async def clear_component_logs(id: str, session: AsyncSession = Depends(get_db_session)):
    tracked = supervisor.get_tracked(id)
    if tracked and tracked.active_log_path and tracked.active_log_path.exists():
        open(tracked.active_log_path, "w").close()

    # Clear run logs folder
    comp_log_dir = LOGS_DIR / id
    if comp_log_dir.exists():
        for f in comp_log_dir.glob("*.log"):
            try:
                open(f, "w").close()
            except Exception:
                pass

    return {"message": "Logs cleared"}


@router.get("/components/{id}/logs/download")
async def download_component_logs(
    id: str,
    run: str | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    target_path = None
    if run:
        r_res = await session.execute(select(Run).where(Run.id == run, Run.component_id == id))
        r = r_res.scalar_one_or_none()
        if r and r.log_path:
            target_path = Path(r.log_path)
    else:
        tracked = supervisor.get_tracked(id)
        if tracked and tracked.active_log_path:
            target_path = tracked.active_log_path

    if not target_path or not target_path.exists():
        raise HTTPException(status_code=404, detail="Log file not found")

    return FileResponse(
        path=str(target_path),
        filename=f"hangar-component-{id}.log",
        media_type="text/plain",
    )

