from __future__ import annotations
import datetime
import json
import random
import sys
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import DEMO_HISTORY
from ..core.supervisor import supervisor
from ..db import get_db_session
from ..models import Application, Component, Event, Metric1m

router = APIRouter(prefix="/samples", tags=["samples"])

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"
PYTHON_EXE = sys.executable


@router.post("/load", status_code=status.HTTP_201_CREATED)
async def load_samples(session: AsyncSession = Depends(get_db_session)):
    """Creates the two sample applications (Sample Shop and Sample Blog)."""
    # Check if samples already exist
    existing = await session.execute(
        select(Application).where(Application.name.in_(["Sample Shop", "Sample Blog"]))
    )
    if existing.scalars().first():
        return {"message": "Sample applications are already loaded."}

    static_dir = SAMPLES_DIR / "static_site"
    static_dir.mkdir(parents=True, exist_ok=True)
    echo_script = SAMPLES_DIR / "echo_api.py"
    fake_db_script = SAMPLES_DIR / "fake_db.py"

    # 1. Sample Shop
    shop_app = Application(
        name="Sample Shop",
        description="E-commerce demo application with Web, API, and DB",
        icon="Boxes",
        path=str(SAMPLES_DIR),
        tags=json.dumps(["ecommerce", "demo", "python"]),
        favorite=True,
        sort=1,
        start_mode="ordered",
    )
    session.add(shop_app)
    await session.flush()

    shop_db = Component(
        application_id=shop_app.id,
        kind="database",
        name="shop-db",
        cwd=str(SAMPLES_DIR),
        start_cmd=f'"{PYTHON_EXE}" "{fake_db_script}" --port 4103',
        env=json.dumps({"PORT": "4103"}),
        port=4103,
        tier=1,
        health=json.dumps({"type": "tcp", "target": "4103", "interval_s": 5, "timeout_s": 3, "startup_grace_s": 15}),
        autorestart=True,
        max_restarts=5,
    )
    shop_api = Component(
        application_id=shop_app.id,
        kind="backend",
        name="shop-api",
        cwd=str(SAMPLES_DIR),
        start_cmd=f'"{PYTHON_EXE}" "{echo_script}" --port 4102',
        env=json.dumps({"PORT": "4102"}),
        port=4102,
        url="http://localhost:4102",
        tier=2,
        health=json.dumps({"type": "http", "target": "http://127.0.0.1:4102/health", "interval_s": 5, "timeout_s": 3, "startup_grace_s": 20}),
        autorestart=True,
        max_restarts=5,
    )
    shop_web = Component(
        application_id=shop_app.id,
        kind="frontend",
        name="shop-web",
        cwd=str(static_dir),
        start_cmd=f'"{PYTHON_EXE}" -m http.server 4101',
        env=json.dumps({"PORT": "4101"}),
        port=4101,
        url="http://localhost:4101",
        tier=3,
        health=json.dumps({"type": "tcp", "target": "4101", "interval_s": 5, "timeout_s": 3, "startup_grace_s": 15}),
        autorestart=True,
        max_restarts=5,
    )
    session.add_all([shop_db, shop_api, shop_web])

    # 2. Sample Blog
    blog_app = Application(
        name="Sample Blog",
        description="Blogging platform with auto-crashing API for testing crash notifications",
        icon="ScrollText",
        path=str(SAMPLES_DIR),
        tags=json.dumps(["blog", "crash-test", "sqlite"]),
        favorite=False,
        sort=2,
        start_mode="ordered",
    )
    session.add(blog_app)
    await session.flush()

    # Pre-create SQLite dummy file for blog-db
    blog_db_file = SAMPLES_DIR / "blog.db"
    if not blog_db_file.exists():
        blog_db_file.write_text("-- sample sqlite db", encoding="utf-8")

    blog_db = Component(
        application_id=blog_app.id,
        kind="database",
        name="blog-db",
        cwd=str(SAMPLES_DIR),
        start_cmd=f'"{PYTHON_EXE}" -c "import time; print(\'blog-db sqlite ready\'); time.sleep(86400)"',
        env=json.dumps({}),
        port=None,
        tier=1,
        health=json.dumps({"type": "file", "target": str(blog_db_file), "interval_s": 5, "timeout_s": 3, "startup_grace_s": 15}),
        autorestart=True,
        max_restarts=5,
    )
    blog_api = Component(
        application_id=blog_app.id,
        kind="backend",
        name="blog-api",
        cwd=str(SAMPLES_DIR),
        start_cmd=f'"{PYTHON_EXE}" "{echo_script}" --port 4112 --crash-after 40',
        env=json.dumps({"PORT": "4112"}),
        port=4112,
        url="http://localhost:4112",
        tier=2,
        health=json.dumps({"type": "http", "target": "http://127.0.0.1:4112/health", "interval_s": 5, "timeout_s": 3, "startup_grace_s": 20}),
        autorestart=True,
        max_restarts=5,
    )
    blog_web = Component(
        application_id=blog_app.id,
        kind="frontend",
        name="blog-web",
        cwd=str(static_dir),
        start_cmd=f'"{PYTHON_EXE}" -m http.server 4111',
        env=json.dumps({"PORT": "4111"}),
        port=4111,
        url="http://localhost:4111",
        tier=3,
        health=json.dumps({"type": "tcp", "target": "4111", "interval_s": 5, "timeout_s": 3, "startup_grace_s": 15}),
        autorestart=True,
        max_restarts=5,
    )
    session.add_all([blog_db, blog_api, blog_web])
    await session.flush()

    # Seed demo history if HANGAR_DEMO_HISTORY=1
    if DEMO_HISTORY:
        now = datetime.datetime.utcnow()
        for hour in range(24):
            point_time = now - datetime.timedelta(hours=24 - hour)
            for comp in [shop_db, shop_api, shop_web, blog_db, blog_api, blog_web]:
                session.add(
                    Metric1m(
                        ts=point_time,
                        component_id=comp.id,
                        cpu_pct=round(random.uniform(0.5, 12.0), 2),
                        rss_mb=round(random.uniform(25.0, 85.0), 2),
                    )
                )
            # Machine metric
            session.add(
                Metric1m(
                    ts=point_time,
                    component_id=None,
                    cpu_pct=round(random.uniform(10.0, 35.0), 2),
                    rss_mb=round(random.uniform(3000.0, 4500.0), 2),
                )
            )

    await session.commit()
    return {"message": "Sample applications loaded successfully."}


@router.delete("", status_code=status.HTTP_200_OK)
async def delete_samples(session: AsyncSession = Depends(get_db_session)):
    """Stops and removes the sample applications."""
    res = await session.execute(
        select(Application).where(Application.name.in_(["Sample Shop", "Sample Blog"]))
    )
    apps = res.scalars().all()
    for app in apps:
        comp_res = await session.execute(select(Component).where(Component.application_id == app.id))
        comps = comp_res.scalars().all()
        for c in comps:
            await supervisor.stop_component(c.id, reason="user")
        await session.delete(app)

    await session.commit()
    return {"message": "Sample applications removed."}

