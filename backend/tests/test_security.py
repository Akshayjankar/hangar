from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport
from hangar.main import app


@pytest.mark.asyncio
async def test_valid_host_header_allowed():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost:7777") as client:
        resp = await client.get("/api/overview", headers={"Host": "localhost:7777"})
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_invalid_host_header_rejected_with_403():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost:7777") as client:
        # Malicious external host
        resp = await client.get("/api/overview", headers={"Host": "evil-website.com:7777"})
        assert resp.status_code == 403
        assert "Invalid Host header" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_mutating_request_requires_origin_and_hangar_client_header():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost:7777") as client:
        # Missing Origin
        resp = await client.post(
            "/api/samples/load",
            headers={"Host": "localhost:7777", "X-Hangar-Client": "1"},
        )
        assert resp.status_code == 403

        # Invalid Origin (drive-by attack from another web page)
        resp = await client.post(
            "/api/samples/load",
            headers={
                "Host": "localhost:7777",
                "Origin": "https://malicious-site.com",
                "X-Hangar-Client": "1",
            },
        )
        assert resp.status_code == 403
        assert "Origin not allowed" in resp.json()["detail"]

        # Missing X-Hangar-Client header
        resp = await client.post(
            "/api/samples/load",
            headers={
                "Host": "localhost:7777",
                "Origin": "http://localhost:7777",
            },
        )
        assert resp.status_code == 403
        assert "X-Hangar-Client" in resp.json()["detail"]

        # Valid Origin and X-Hangar-Client: 1
        resp = await client.post(
            "/api/samples/load",
            headers={
                "Host": "localhost:7777",
                "Origin": "http://localhost:7777",
                "X-Hangar-Client": "1",
            },
        )
        assert resp.status_code in {200, 201}


@pytest.mark.asyncio
async def test_dev_origin_is_permitted():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost:7777") as client:
        resp = await client.post(
            "/api/samples/load",
            headers={
                "Host": "localhost:7777",
                "Origin": "http://localhost:3000",
                "X-Hangar-Client": "1",
            },
        )
        assert resp.status_code in {200, 201}

