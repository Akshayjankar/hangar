from __future__ import annotations
import logging
from typing import Any
import psutil
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session_factory
from ..models import Component
from ..schemas import PortInfo
from .process import kill_process_tree

logger = logging.getLogger("hangar.ports")


def get_process_holding_port(port: int) -> tuple[int | None, str | None, str | None]:
    """Finds the PID, process name, and cmdline listening on the given TCP port."""
    try:
        connections = psutil.net_connections(kind="tcp")
        for conn in connections:
            if conn.status == psutil.CONN_LISTEN and conn.laddr and conn.laddr.port == port:
                pid = conn.pid
                if pid:
                    try:
                        p = psutil.Process(pid)
                        name = p.name()
                        try:
                            cmdline = " ".join(p.cmdline())
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            cmdline = name
                        return pid, name, cmdline
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        return pid, "Unknown", None
                return None, None, None
    except (psutil.AccessDenied, Exception) as e:
        logger.warning("Could not read net_connections: %s", e)
    return None, None, None


async def list_listening_ports(
    managed_pids: dict[int, tuple[str, str, str]],  # pid -> (app_id, comp_id, comp_name)
    component_ports: dict[int, tuple[str, str, str, str]],  # port -> (app_id, comp_id, comp_name, status)
) -> list[PortInfo]:
    """
    Lists all listening TCP ports and marks:
    - whether managed by Hangar
    - conflicts (e.g. stopped component's port held by someone else, or port claimed by multiple components)
    """
    results: list[PortInfo] = []
    seen_ports: set[int] = set()

    try:
        connections = psutil.net_connections(kind="tcp")
    except (psutil.AccessDenied, Exception) as e:
        logger.warning("Error inspecting net connections: %s", e)
        connections = []

    for conn in connections:
        if conn.status == psutil.CONN_LISTEN and conn.laddr:
            port = conn.laddr.port
            if port in seen_ports:
                continue
            seen_ports.add(port)

            pid = conn.pid
            p_name = None
            cmdline = None
            if pid:
                try:
                    p = psutil.Process(pid)
                    p_name = p.name()
                    try:
                        cmdline = " ".join(p.cmdline())
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        cmdline = p_name
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    p_name = "Unknown"

            is_managed = False
            app_id = None
            comp_id = None
            comp_name = None
            conflict = False
            conflict_reason = None

            if pid and pid in managed_pids:
                is_managed = True
                app_id, comp_id, comp_name = managed_pids[pid]
            elif port in component_ports:
                c_app_id, c_comp_id, c_name, c_status = component_ports[port]
                # If component is stopped or starting, but port is already held by an unmanaged process
                if c_status != "running":
                    conflict = True
                    conflict_reason = f"Port {port} declared for {c_name} ({c_status}) is held by external process {p_name} (pid {pid})"
                    app_id = c_app_id
                    comp_id = c_comp_id
                    comp_name = c_name

            # Exclude low OS privileged ports (<1024) and Windows kernel services
            # unless they are explicitly managed by Hangar or conflicting with a Hangar component
            is_os_service = (
                (port < 1024)
                or (pid is not None and pid <= 4)
                or (p_name is not None and p_name.lower() in {
                    "system", "svchost.exe", "csrss.exe", "smss.exe", "services.exe",
                    "winlogon.exe", "lsass.exe", "spoolsv.exe", "registry"
                })
            )

            if is_os_service and not is_managed and not conflict:
                continue

            results.append(
                PortInfo(
                    port=port,
                    pid=pid,
                    process_name=p_name,
                    cmdline=cmdline,
                    managed=is_managed,
                    application_id=app_id,
                    component_id=comp_id,
                    component_name=comp_name,
                    conflict=conflict,
                    conflict_reason=conflict_reason,
                )
            )

    return sorted(results, key=lambda x: x.port)


def kill_port_owner(port: int, target_pid: int) -> bool:
    """Confirms target_pid still owns the port, then kills its process tree."""
    if target_pid <= 4:
        raise ValueError(f"Cannot terminate critical operating system process (PID {target_pid})")

    curr_pid, name, _ = get_process_holding_port(port)
    if curr_pid != target_pid:
        raise ValueError(f"Port {port} is no longer owned by PID {target_pid} (current: {curr_pid})")

    if name and name.lower() in {
        "system", "svchost.exe", "csrss.exe", "smss.exe", "services.exe",
        "winlogon.exe", "lsass.exe", "spoolsv.exe", "registry"
    }:
        raise ValueError(f"Cannot terminate protected system process '{name}' (PID {target_pid})")

    return kill_process_tree(target_pid)

