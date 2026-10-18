"""Tests for the DELETE /api/applications/{id} endpoint."""
from __future__ import annotations
import os
import pytest
from httpx import AsyncClient


@pytest.fixture
async def sample_app(client: AsyncClient):
    """Create a sample application for testing deletion."""
    payload = {
        "name": "Test Delete App",
        "description": "App for testing deletion",
        "icon": "Boxes",
        "path": os.getcwd(),
        "tags": ["test"],
        "favorite": False,
        "sort": 0,
        "start_mode": "ordered",
        "components": [
            {
                "name": "test-backend",
                "kind": "backend",
                "cwd": os.getcwd(),
                "start_cmd": "echo hello",
                "stop_cmd": None,
                "env": {},
                "port": None,
                "url": None,
                "health": {
                    "type": "process",
                    "target": None,
                    "interval_s": 5,
                    "timeout_s": 3,
                    "startup_grace_s": 30,
                },
                "tier": 2,
                "autorestart": False,
                "max_restarts": 3,
                "start_on_launch": False,
            }
        ],
    }
    res = await client.post("/api/applications", json=payload)
    assert res.status_code == 201
    return res.json()


async def test_delete_existing_stopped_app(client: AsyncClient, sample_app: dict):
    """Deleting an existing stopped application returns 200 and the app is gone."""
    app_id = sample_app["id"]
    res = await client.delete(f"/api/applications/{app_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["message"] == "Application deleted"
    assert data["name"] == "Test Delete App"

    # Verify it is gone
    res2 = await client.get(f"/api/applications/{app_id}")
    assert res2.status_code == 404


async def test_delete_nonexistent_app_returns_404(client: AsyncClient):
    """Deleting a non-existent application returns 404."""
    res = await client.delete("/api/applications/nonexistent-id-12345")
    assert res.status_code == 404
    assert res.json()["detail"] == "Application not found"


async def test_delete_with_stop_first_false(client: AsyncClient, sample_app: dict):
    """Deleting with stop_first=false skips stopping and still deletes."""
    app_id = sample_app["id"]
    res = await client.delete(f"/api/applications/{app_id}?stop_first=false")
    assert res.status_code == 200
    data = res.json()
    assert data["message"] == "Application deleted"
    assert data["name"] == "Test Delete App"

    # Verify it is gone
    res2 = await client.get(f"/api/applications/{app_id}")
    assert res2.status_code == 404

