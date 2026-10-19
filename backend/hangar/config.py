from __future__ import annotations
import os
import sys
from pathlib import Path

# Working name kept in one config constant so it can be easily renamed
APP_NAME: str = os.environ.get("HANGAR_APP_NAME", "Hangar")
VERSION: str = "0.1.0"

# Networking constraints: strictly 127.0.0.1, refuses to bind elsewhere
BIND_HOST: str = "127.0.0.1"
DEFAULT_PORT: int = 7777
PORT: int = int(os.environ.get("HANGAR_PORT", str(DEFAULT_PORT)))

# Allowed Origins & Host header validation
DEV_ORIGIN: str = os.environ.get("HANGAR_DEV_ORIGIN", "http://localhost:3002")
ALLOWED_HOSTS: set[str] = {
    "localhost",
    "127.0.0.1",
    "[::1]",
    f"localhost:{PORT}",
    f"127.0.0.1:{PORT}",
    f"[::1]:{PORT}",
}

ALLOWED_ORIGINS: set[str] = {
    f"http://localhost:{PORT}",
    f"http://127.0.0.1:{PORT}",
    f"http://[::1]:{PORT}",
    DEV_ORIGIN,
    "http://127.0.0.1:3002",
}

# Storage paths
DEFAULT_HOME: Path = Path.home() / ".hangar"
HANGAR_HOME: Path = Path(os.environ.get("HANGAR_HOME", str(DEFAULT_HOME))).expanduser().resolve()
DB_PATH: Path = HANGAR_HOME / "hangar.db"
LOGS_DIR: Path = HANGAR_HOME / "logs"

# Demo data flag
DEMO_HISTORY: bool = bool(int(os.environ.get("HANGAR_DEMO_HISTORY", "0")))

# Static files directory for Next.js exported frontend
STATIC_DIR: Path = Path(__file__).resolve().parent.parent.parent / "frontend" / "out"

# Default settings
DEFAULT_SHELL: str = "cmd.exe" if sys.platform == "win32" else "/bin/sh"

DEFAULT_SETTINGS: dict[str, str | int | float | bool] = {
    "theme": "system",
    "shell_override": DEFAULT_SHELL,
    "health_interval_s": 5,
    "startup_grace_s": 30,
    "autorestart_default": True,
    "max_restarts": 5,
    "log_retention_runs": 10,
    "log_max_total_mb": 500,
    "cpu_alert_pct": 90.0,
    "memory_alert_pct": 80.0,
    "notify_toasts": True,
    "notify_browser": False,
    "notify_sound": False,
    "on_exit": "leave_running",  # "leave_running" | "stop_all"
}


def ensure_data_directories() -> None:
    """Ensure ~/.hangar and ~/.hangar/logs exist."""
    HANGAR_HOME.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

