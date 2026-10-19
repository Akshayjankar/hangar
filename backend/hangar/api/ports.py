from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.ports import kill_port_owner, list_listening_ports
from ..core.supervisor import supervisor
from ..db import get_db_session
from ..models import Component
from ..schemas import KillPortRequest, PortInfo

router = APIRouter(prefix="/ports", tags=["ports"])


@router.get("", response_model=list[PortInfo])
async def get_ports(session: AsyncSession = Depends(get_db_session)):
    # Build managed pids map: pid -> (app_id, comp_id, comp_name)
    managed_pids: dict[int, tuple[str, str, str]] = {}
    for cid, tracked in supervisor.components.items():
        if tracked.pid and tracked.status in {"running", "starting", "unhealthy"}:
            managed_pids[tracked.pid] = (tracked.app_id, cid, tracked.name)

    # Build component ports map: port -> (app_id, comp_id, comp_name, status)
    comp_res = await session.execute(select(Component).where(Component.port.is_not(None)))
    comps = comp_res.scalars().all()
    component_ports: dict[int, tuple[str, str, str, str]] = {}
    for c in comps:
        if c.port:
            tracked = supervisor.get_tracked(c.id)
            c_status = tracked.status if tracked else "stopped"
            component_ports[c.port] = (c.application_id, c.id, c.name, c_status)

    return await list_listening_ports(managed_pids, component_ports)


@router.post("/{port}/kill")
async def kill_port(port: int, payload: KillPortRequest):
    try:
        success = kill_port_owner(port, payload.pid)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to kill process holding port")
        return {"message": f"Successfully killed process on port {port}"}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

