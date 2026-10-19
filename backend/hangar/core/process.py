from __future__ import annotations
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
import psutil

from ..config import DEFAULT_SHELL


def spawn_process(
    cmd: str,
    cwd: str | Path,
    log_file_path: str | Path,
    env: dict[str, str] | None = None,
    port: int | None = None,
    shell_override: str | None = None,
) -> tuple[subprocess.Popen, int, float]:
    """
    Spawns a child process with:
    - stdout and stderr merged directly into log_file_path (file open in append/write mode).
    - its own process group / session.
    - PORT and PYTHONUNBUFFERED=1 injected.
    - merged system environment.
    Returns: (popen_instance, pid, create_time)
    """
    log_path = Path(log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    # Open file for writing process output
    log_file = open(log_path, "a", encoding="utf-8", errors="replace", buffering=1)

    merged_env = os.environ.copy()
    merged_env["PYTHONUNBUFFERED"] = "1"
    if port:
        merged_env["PORT"] = str(port)
    if env:
        merged_env.update(env)

    shell = shell_override or DEFAULT_SHELL

    cwd_path = Path(cwd).resolve()
    if not cwd_path.exists():
        raise FileNotFoundError(f"Working directory does not exist: {cwd_path}")

    creationflags = 0
    start_new_session = False

    if sys.platform == "win32":
        # CREATE_NEW_PROCESS_GROUP allows sending CTRL_BREAK_EVENT and isolating signals
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        # On Windows, use /s /c and pass raw command line to prevent quote stripping
        cmd_line = f'{shell} /s /c "{cmd}"'
        proc = subprocess.Popen(
            cmd_line,
            cwd=str(cwd_path),
            env=merged_env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
        )
    else:
        start_new_session = True
        proc = subprocess.Popen(
            [shell, "-c", cmd],
            cwd=str(cwd_path),
            env=merged_env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=start_new_session,
        )

    pid = proc.pid
    # Capture psutil create_time for re-adoption
    try:
        p = psutil.Process(pid)
        create_time = p.create_time()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        create_time = time.time()

    return proc, pid, create_time


def kill_process_tree(pid: int, timeout_s: float = 5.0) -> bool:
    """
    Gracefully terminates then forcefully kills the process and all its children.
    psutil: terminate, wait up to timeout_s, then kill.
    On Windows, also falls back to `taskkill /T /F /PID <pid>`.
    """
    try:
        parent = psutil.Process(pid)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return True

    try:
        children = parent.children(recursive=True)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        children = []

    all_procs = children + [parent]

    # Step 1: Graceful SIGTERM / terminate
    for p in all_procs:
        try:
            p.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Wait for termination
    gone, alive = psutil.wait_procs(all_procs, timeout=timeout_s)

    # Step 2: Forceful SIGKILL / kill on any lingering processes
    if alive:
        for p in alive:
            try:
                p.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        psutil.wait_procs(alive, timeout=1.0)

    # Step 3: Windows fallback to ensure no stray processes survived
    if sys.platform == "win32":
        try:
            # Check if still running
            if psutil.pid_exists(pid):
                subprocess.run(
                    ["taskkill", "/T", "/F", "/PID", str(pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
        except Exception:
            pass

    return not psutil.pid_exists(pid)


def is_process_match(pid: int, expected_create_time: float, tolerance_s: float = 2.0) -> bool:
    """Check if the PID exists and matches the recorded create_time (for re-adoption)."""
    try:
        p = psutil.Process(pid)
        if not p.is_running() or p.status() == psutil.STATUS_ZOMBIE:
            return False
        return abs(p.create_time() - expected_create_time) <= tolerance_s
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False
