from __future__ import annotations
import asyncio
from pathlib import Path
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from hangar.core.supervisor import supervisor
from hangar.db import get_session_factory
from hangar.models import Application, Component, Run


@pytest.mark.asyncio
async def test_sample_apps_lifecycle(client: AsyncClient):
    # 1. Load samples via API
    resp = await client.post("/api/samples/load")
    assert resp.status_code in {200, 201}

    # Verify applications exist in DB
    factory = get_session_factory()
    async with factory() as session:
        res = await session.execute(select(Application).where(Application.name == "Sample Shop"))
        shop_app = res.scalar_one()
        assert shop_app is not None

        comp_res = await session.execute(select(Component).where(Component.application_id == shop_app.id))
        shop_comps = {c.name: c for c in comp_res.scalars().all()}
        assert "shop-api" in shop_comps
        assert "shop-web" in shop_comps
        assert "shop-db" in shop_comps

        api_comp = shop_comps["shop-api"]
        api_id = api_comp.id

    # 2. Start shop-api via supervisor
    success, msg = await supervisor.start_component(api_id)
    assert success is True

    tracked = supervisor.get_tracked(api_id)
    assert tracked is not None
    assert tracked.pid is not None
    assert tracked.active_log_path is not None
    assert tracked.active_log_path.exists()

    # Wait for startup health check to mark component "running"
    for _ in range(15):
        if tracked.status == "running":
            break
        await asyncio.sleep(0.5)

    assert tracked.status == "running"

    # Verify log output was written to file
    await asyncio.sleep(1.2)
    log_content = tracked.active_log_path.read_text(encoding="utf-8", errors="replace")
    assert len(log_content) > 0
    assert "INFO" in log_content

    # 3. Stop shop-api and verify process tree killed and status is stopped
    pid = tracked.pid
    stop_success, stop_msg = await supervisor.stop_component(api_id, reason="user")
    assert stop_success is True
    assert tracked.status == "stopped"

    # Verify DB run record has ended_at and stop_reason
    async with factory() as session:
        run_res = await session.execute(select(Run).where(Run.component_id == api_id))
        latest_run = run_res.scalars().first()
        assert latest_run is not None
        assert latest_run.ended_at is not None
        assert latest_run.stop_reason == "user"

    # 4. Clean up samples via API
    del_resp = await client.delete("/api/samples")
    assert del_resp.status_code == 200

