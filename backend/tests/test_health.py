from __future__ import annotations
import os
import socket
import sys
import tempfile
from pathlib import Path
import pytest

from hangar.core.health import (
    check_command,
    check_file,
    check_http,
    check_process,
    check_tcp,
    run_health_check,
)
from hangar.schemas import HealthConfig


@pytest.mark.asyncio
async def test_tcp_health_check():
    # Spin up temporary listening socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    port = sock.getsockname()[1]

    try:
        healthy, reason = await check_tcp(port, timeout_s=1.0)
        assert healthy is True
        assert "succeeded" in reason
    finally:
        sock.close()

    # Closed port
    healthy, reason = await check_tcp(port, timeout_s=0.5)
    assert healthy is False


@pytest.mark.asyncio
async def test_process_health_check():
    current_pid = os.getpid()
    healthy, reason = check_process(current_pid)
    assert healthy is True

    # Non-existent PID
    healthy, reason = check_process(9999999)
    assert healthy is False


@pytest.mark.asyncio
async def test_file_health_check():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"data")
        f_path = f.name

    try:
        healthy, reason = check_file(f_path)
        assert healthy is True
        assert "exists" in reason
    finally:
        os.unlink(f_path)

    healthy, reason = check_file("non_existent_file_path.xyz")
    assert healthy is False


@pytest.mark.asyncio
async def test_command_health_check():
    healthy, reason = await check_command(f'"{sys.executable}" -c "exit(0)"', cwd=".", timeout_s=2.0)
    assert healthy is True

    healthy, reason = await check_command(f'"{sys.executable}" -c "exit(1)"', cwd=".", timeout_s=2.0)
    assert healthy is False

