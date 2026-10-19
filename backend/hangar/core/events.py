from __future__ import annotations
import datetime
import json
import logging
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session_factory
from ..models import Event
from .bus import bus

logger = logging.getLogger("hangar.events")


async def emit_event(
    level: str,  # "info" | "warn" | "error"
    event_type: str,  # "started", "stopped", "restarted", "crash", "start_failed", "unhealthy", "recovered", "port_conflict", "high_cpu", "high_memory", "restart_loop"
    title: str,
    reason: str,
    application_id: str | None = None,
    component_id: str | None = None,
    detail: dict[str, Any] | list[Any] | None = None,
    session: AsyncSession | None = None,
) -> Event:
    """Creates, persists, and broadcasts an event to subscribers."""
    event_id = str(uuid.uuid4())
    ts = datetime.datetime.utcnow()
    detail_json = json.dumps(detail or {})

    evt = Event(
        id=event_id,
        ts=ts,
        level=level,
        type=event_type,
        application_id=application_id,
        component_id=component_id,
        title=title,
        reason=reason,
        detail=detail_json,
        read=False,
    )

    if session is not None:
        session.add(evt)
        await session.flush()
    else:
        factory = get_session_factory()
        async with factory() as s:
            s.add(evt)
            await s.commit()

    # Broadcast event via websocket
    event_dict = {
        "id": event_id,
        "ts": ts.isoformat(),
        "level": level,
        "type": event_type,
        "application_id": application_id,
        "component_id": component_id,
        "title": title,
        "reason": reason,
        "detail": detail or {},
        "read": False,
    }
    await bus.broadcast("events", event_dict)
    return evt

