from __future__ import annotations
import asyncio
import os
import socket
import subprocess
from pathlib import Path
from typing import Any
import httpx
import psutil

from ..schemas import HealthConfig


async def check_tcp(port: int, host: str = "127.0.0.1", timeout_s: float = 2.0) -> tuple[bool, str]:
    """Check TCP connection."""
    loop = asyncio.get_running_loop()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        await asyncio.wait_for(loop.sock_connect(sock, (host, port)), timeout=timeout_s)
        sock.close()
        return True, f"TCP connection to {host}:{port} succeeded"
    except asyncio.TimeoutError:
        return False, f"TCP connection to {host}:{port} timed out after {timeout_s}s"
    except Exception as e:
        return False, f"TCP connect to {host}:{port} failed: {e}"


async def check_http(url: str, timeout_s: float = 3.0) -> tuple[bool, str]:
    """Check HTTP GET 2xx/3xx response."""
    try:
        async with httpx.AsyncClient(timeout=timeout_s, verify=False) as client:
            resp = await client.get(url)
            if 200 <= resp.status_code < 400:
                return True, f"HTTP GET {url} returned {resp.status_code}"
            return False, f"HTTP GET {url} returned status {resp.status_code}"
    except httpx.TimeoutException:
        return False, f"HTTP GET {url} timed out after {timeout_s}s"
    except Exception as e:
        return False, f"HTTP GET {url} error: {e}"


def check_process(pid: int | None) -> tuple[bool, str]:
    """Check if process with PID is alive."""
    if not pid:
        return False, "No PID associated with component"
    try:
        p = psutil.Process(pid)
        if p.is_running() and p.status() != psutil.STATUS_ZOMBIE:
            return True, f"Process {pid} is alive ({p.status()})"
        return False, f"Process {pid} is not running or zombie"
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False, f"Process {pid} does not exist"


def check_file(path_str: str) -> tuple[bool, str]:
    """Check if file exists and has size > 0."""
    try:
        p = Path(path_str)
        if p.exists() and p.is_file():
            return True, f"File {path_str} exists ({p.stat().st_size} bytes)"
        return False, f"File {path_str} not found or is a directory"
    except Exception as e:
        return False, f"Error checking file {path_str}: {e}"


async def check_command(cmd: str, cwd: str, timeout_s: float = 3.0) -> tuple[bool, str]:
    """Check if custom command exits with code 0."""
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
            if proc.returncode == 0:
                return True, f"Command exited with code 0"
            err_msg = stderr.decode(errors="replace").strip() or stdout.decode(errors="replace").strip()
            return False, f"Command exited with code {proc.returncode}: {err_msg[:100]}"
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return False, f"Command timed out after {timeout_s}s"
    except Exception as e:
        return False, f"Failed to run command check: {e}"


async def run_health_check(
    health_config: HealthConfig | dict[str, Any],
    port: int | None = None,
    pid: int | None = None,
    cwd: str | None = None,
) -> tuple[bool, str]:
    """
    Evaluates health according to config.
    Defaults to TCP connect if a port is set and type is tcp/unspecified.
    """
    if isinstance(health_config, dict):
        cfg = HealthConfig(**health_config)
    else:
        cfg = health_config

    check_type = cfg.type
    timeout_s = cfg.timeout_s

    # Default to TCP check if port is declared and check_type is default or tcp
    if (check_type == "tcp" or (check_type == "process" and not cfg.target and port)) and port:
        target_port = port
        if cfg.target and cfg.target.isdigit():
            target_port = int(cfg.target)
        return await check_tcp(target_port, timeout_s=timeout_s)

    if check_type == "http":
        target_url = cfg.target
        if not target_url and port:
            target_url = f"http://127.0.0.1:{port}/"
        if not target_url:
            return False, "HTTP check configured without target URL or port"
        return await check_http(target_url, timeout_s=timeout_s)

    if check_type == "process":
        return check_process(pid)

    if check_type == "file":
        if not cfg.target:
            return False, "File check configured without target path"
        return check_file(cfg.target)

    if check_type == "command":
        if not cfg.target:
            return False, "Command check configured without target command"
        return await check_command(cfg.target, cwd=cwd or ".", timeout_s=timeout_s)

    # Fallback to process check
    return check_process(pid)

