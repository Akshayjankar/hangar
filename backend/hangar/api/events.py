from __future__ import annotations
import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db_session
from ..models import Event
from ..schemas import EventRead

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventRead])
async def list_events(
    level: str | None = None,
    type: str | None = None,
    app: str | None = None,
    unread: bool | None = None,
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db_session),
):
    stmt = select(Event)
    if level:
        stmt = stmt.where(Event.level == level)
    if type:
        stmt = stmt.where(Event.type == type)
    if app:
        stmt = stmt.where(Event.application_id == app)
    if unread is True:
        stmt = stmt.where(Event.read.is_(False))

    stmt = stmt.order_by(Event.ts.desc()).limit(limit)
    res = await session.execute(stmt)
    events = res.scalars().all()

    return [
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


@router.post("/{id}/read")
async def mark_event_read(id: str, session: AsyncSession = Depends(get_db_session)):
    res = await session.execute(select(Event).where(Event.id == id))
    evt = res.scalar_one_or_none()
    if not evt:
        raise HTTPException(status_code=404, detail="Event not found")
    evt.read = True
    await session.commit()
    return {"message": "Event marked as read"}


@router.post("/read-all")
async def mark_all_events_read(session: AsyncSession = Depends(get_db_session)):
    await session.execute(update(Event).values(read=True))
    await session.commit()
    return {"message": "All events marked as read"}

