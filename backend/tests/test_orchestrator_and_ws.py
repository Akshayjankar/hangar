from __future__ import annotations
import asyncio
import json
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from hangar.core.orchestrator import orchestrator
from hangar.core.supervisor import supervisor
from hangar.db import get_session_factory
from hangar.models import Application, Component


@pytest.mark.asyncio
async def test_ordered_start_and_stop_application(client: AsyncClient):
    # Load samples
    await client.post("/api/samples/load")

    factory = get_session_factory()
    async with factory() as session:
        res = await session.execute(select(Application).where(Application.name == "Sample Shop"))
        app = res.scalar_one()
        app_id = app.id

    # Start ordered application
    job = await orchestrator.start_application(app_id)
    assert job.status in {"running", "completed"}
    assert job.total_steps == 3

    # Wait for completion
    for _ in range(25):
        updated_job = orchestrator.get_job(job.id)
        if updated_job and updated_job.status in {"completed", "failed"}:
            break
        await asyncio.sleep(0.5)

    final_job = orchestrator.get_job(job.id)
    assert final_job is not None
    assert final_job.status == "completed"

    # Verify all components are running
    async with factory() as session:
        comp_res = await session.execute(select(Component).where(Component.application_id == app_id))
        comps = comp_res.scalars().all()
        for c in comps:
            tracked = supervisor.get_tracked(c.id)
            assert tracked is not None
            assert tracked.status == "running"

    # Stop application in reverse order
    stop_job = await orchestrator.stop_application(app_id)
    for _ in range(20):
        updated_stop = orchestrator.get_job(stop_job.id)
        if updated_stop and updated_stop.status in {"completed", "failed"}:
            break
        await asyncio.sleep(0.5)

    final_stop = orchestrator.get_job(stop_job.id)
    assert final_stop is not None
    assert final_stop.status == "completed"

    # Verify all components stopped
    for c in comps:
        tracked = supervisor.get_tracked(c.id)
        assert tracked.status == "stopped"

    # Cleanup
    await client.delete("/api/samples")

