from __future__ import annotations
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

from ..schemas import ComponentCreate, HealthConfig

logger = logging.getLogger("hangar.detect")


def detect_components_in_folder(base_path: str | Path) -> list[dict[str, Any]]:
    """
    Scans a folder up to depth 2 and returns detected component configurations.
    Never auto-saves.
    """
    root = Path(base_path).resolve()
    if not root.exists() or not root.is_dir():
        return []

    detected: list[dict[str, Any]] = []

    # Gather search directories: root + depth 1 subdirs
    scan_dirs = [root]
    try:
        for child in root.iterdir():
            if child.is_dir() and not child.name.startswith(".") and child.name not in {"node_modules", "__pycache__", "dist", "build"}:
                scan_dirs.append(child)
    except Exception as e:
        logger.warning("Error reading directories in %s: %s", root, e)

    for d in scan_dirs:
        rel_name = d.name.lower()
        hint_kind = None
        if rel_name in {"frontend", "client", "web", "ui"}:
            hint_kind = "frontend"
        elif rel_name in {"backend", "server", "api", "service"}:
            hint_kind = "backend"

        # 1. Check package.json
        pkg_file = d / "package.json"
        if pkg_file.exists():
            try:
                pkg_data = json.loads(pkg_file.read_text(encoding="utf-8"))
                scripts = pkg_data.get("scripts", {})
                deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}

                start_cmd = "npm run dev" if "dev" in scripts else ("npm start" if "start" in scripts else "npm run build")
                port = 3000
                kind = hint_kind or "frontend"

                if "next" in deps:
                    port = 3000
                    kind = "frontend"
                elif "vite" in deps:
                    port = 5173
                    kind = "frontend"
                elif "react-scripts" in deps:
                    port = 3000
                    kind = "frontend"
                elif "express" in deps or "fastify" in deps or "@nestjs/core" in deps:
                    port = 8000
                    kind = "backend"

                tier = 3 if kind == "frontend" else 2
                detected.append({
                    "name": f"{d.name}-node",
                    "kind": kind,
                    "cwd": str(d),
                    "start_cmd": start_cmd,
                    "stop_cmd": None,
                    "env": {},
                    "port": port,
                    "url": f"http://localhost:{port}",
                    "health": {"type": "tcp", "target": str(port), "interval_s": 5, "timeout_s": 3, "startup_grace_s": 30},
                    "tier": tier,
                })
            except Exception as e:
                logger.warning("Error parsing %s: %s", pkg_file, e)

        # 2. Check Python
        py_interpreter = "python"
        for venv_name in [".venv", "venv"]:
            venv_bin = d / venv_name / ("Scripts" if sys.platform == "win32" else "bin") / ("python.exe" if sys.platform == "win32" else "python")
            if venv_bin.exists():
                py_interpreter = str(venv_bin)
                break

        # Check Django
        if (d / "manage.py").exists():
            detected.append({
                "name": f"{d.name}-django",
                "kind": "backend",
                "cwd": str(d),
                "start_cmd": f'"{py_interpreter}" manage.py runserver 8000',
                "stop_cmd": None,
                "env": {},
                "port": 8000,
                "url": "http://localhost:8000",
                "health": {"type": "tcp", "target": "8000", "interval_s": 5, "timeout_s": 3, "startup_grace_s": 30},
                "tier": 2,
            })

        # Check FastAPI / Uvicorn
        main_py = d / "main.py"
        app_py = d / "app.py"
        target_py = main_py if main_py.exists() else (app_py if app_py.exists() else None)
        if target_py and not (d / "manage.py").exists():
            try:
                content = target_py.read_text(encoding="utf-8", errors="replace")
                if "FastAPI" in content:
                    mod = target_py.stem
                    detected.append({
                        "name": f"{d.name}-fastapi",
                        "kind": "backend",
                        "cwd": str(d),
                        "start_cmd": f'"{py_interpreter}" -m uvicorn {mod}:app --reload --port 8000',
                        "stop_cmd": None,
                        "env": {},
                        "port": 8000,
                        "url": "http://localhost:8000",
                        "health": {"type": "http", "target": "http://127.0.0.1:8000/docs", "interval_s": 5, "timeout_s": 3, "startup_grace_s": 30},
                        "tier": 2,
                    })
                elif "Flask" in content:
                    detected.append({
                        "name": f"{d.name}-flask",
                        "kind": "backend",
                        "cwd": str(d),
                        "start_cmd": f'"{py_interpreter}" -m flask run --port 5000',
                        "stop_cmd": None,
                        "env": {},
                        "port": 5000,
                        "url": "http://localhost:5000",
                        "health": {"type": "tcp", "target": "5000", "interval_s": 5, "timeout_s": 3, "startup_grace_s": 30},
                        "tier": 2,
                    })
            except Exception as e:
                logger.warning("Error reading %s: %s", target_py, e)

        # 3. Check docker-compose.yml
        compose_file = d / "docker-compose.yml"
        if not compose_file.exists():
            compose_file = d / "docker-compose.yaml"

        if compose_file.exists():
            try:
                import yaml
                data = yaml.safe_load(compose_file.read_text(encoding="utf-8"))
                services = data.get("services", {})
                for s_name, s_cfg in services.items():
                    image = str(s_cfg.get("image", "")).lower()
                    is_db = any(k in image or k in s_name.lower() for k in ["postgres", "mysql", "mariadb", "mongo", "redis"])
                    kind = "database" if is_db else "worker"
                    tier = 1 if is_db else 2

                    port = None
                    ports_cfg = s_cfg.get("ports", [])
                    if ports_cfg:
                        # Extract host port
                        m = re.search(r"(\d+):", str(ports_cfg[0]))
                        if m:
                            port = int(m.group(1))

                    detected.append({
                        "name": f"{s_name}-compose",
                        "kind": kind,
                        "cwd": str(d),
                        "start_cmd": f"docker compose up -d {s_name}",
                        "stop_cmd": f"docker compose stop {s_name}",
                        "env": {},
                        "port": port,
                        "url": f"http://localhost:{port}" if port else None,
                        "health": {"type": "tcp", "target": str(port), "interval_s": 5, "timeout_s": 3, "startup_grace_s": 30} if port else {"type": "process", "target": None, "interval_s": 5, "timeout_s": 3, "startup_grace_s": 30},
                        "tier": tier,
                    })
            except Exception as e:
                logger.warning("Error parsing %s: %s", compose_file, e)

    return detected

