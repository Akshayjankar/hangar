from __future__ import annotations
import tempfile
from pathlib import Path
import pytest
from httpx import AsyncClient

from hangar.core.detect import detect_components_in_folder


def test_detect_node_and_fastapi_heuristics():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # 1. Create a dummy frontend with package.json
        fe_dir = root / "frontend"
        fe_dir.mkdir()
        (fe_dir / "package.json").write_text(
            '{"name": "test-fe", "scripts": {"dev": "next dev"}, "dependencies": {"next": "^14.0.0"}}',
            encoding="utf-8",
        )

        # 2. Create a dummy backend with main.py
        be_dir = root / "backend"
        be_dir.mkdir()
        (be_dir / "main.py").write_text(
            "from fastapi import FastAPI\napp = FastAPI()\n",
            encoding="utf-8",
        )

        detected = detect_components_in_folder(root)
        kinds = {d["kind"] for d in detected}
        names = [d["name"] for d in detected]

        assert "frontend" in kinds
        assert "backend" in kinds
        assert any("node" in n for n in names)
        assert any("fastapi" in n for n in names)


@pytest.mark.asyncio
async def test_detect_endpoint(client: AsyncClient):
    with tempfile.TemporaryDirectory() as tmpdir:
        resp = await client.post("/api/detect", json={"path": tmpdir})
        assert resp.status_code == 200
        data = resp.json()
        assert "available_presets" in data
        assert len(data["available_presets"]) > 0

