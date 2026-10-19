from __future__ import annotations
import os
import tempfile
from pathlib import Path
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Set temporary HANGAR_HOME before importing hangar
temp_hangar_dir = tempfile.TemporaryDirectory()
os.environ["HANGAR_HOME"] = temp_hangar_dir.name
os.environ["HANGAR_PORT"] = "7777"
os.environ["HANGAR_DEV_ORIGIN"] = "http://localhost:3000"

from hangar.config import ensure_data_directories
from hangar.db import close_db, init_db
from hangar.main import app


@pytest_asyncio.fixture(autouse=True)
async def setup_test_env():
    ensure_data_directories()
    await init_db()
    yield
    await close_db()


@pytest_asyncio.fixture
async def client():
    # Valid client headers for non-GET requests
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://localhost:7777",
        headers={
            "Host": "localhost:7777",
            "Origin": "http://localhost:7777",
            "X-Hangar-Client": "1",
        },
    ) as ac:
        yield ac

