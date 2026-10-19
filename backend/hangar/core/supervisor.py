from __future__ import annotations
import asyncio
import datetime
import json
import logging
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any
import psutil
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import DEFAULT_SETTINGS, LOGS_DIR, ensure_data_directories
from ..db import get_session_factory
from ..models import Application, Component, Run, Setting
from ..schemas import ComponentStatusType
from .bus import bus
from .events import emit_event
from .health import run_health_check
from .logtail import ComponentLogTailer, read_last_n_lines
from .ports import get_process_holding_port
from .process import is_process_match, kill_process_tree, spawn_process

logger = logging.getLogger("hangar.supervisor")


class TrackedComponent:
    def __init__(self, component_id: str, app_id: str, name: str) -> None:
        self.component_id = component_id
        self.app_id = app_id
        self.name = name
        self.status: ComponentStatusType = "stopped"
        self.status_reason: str | None = None
        self.proc: subprocess.Popen | None = None
        self.pid: int | None = None
        self.create_time: float | None = None
        self.active_run_id: str | None = None
        self.active_log_path: Path | None = None
        self.tailer: ComponentLogTailer | None = None
        self.start_time: float | None = None
        self.user_stopped: bool = False
        self.restart_timestamps: list[float] = []
        self.cpu_pct: float = 0.0
        self.rss_mb: float = 0.0


class Supervisor:
    """Manages the process lifecycle, health monitoring, crash recovery, and log tailing."""

    def __init__(self) -> None:
        self.components: dict[str, TrackedComponent] = {}
        self._monitor_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Starts the supervisor monitoring loop and re-adopts existing runs."""
        ensure_data_directories()
        await self._readopt_running_processes()
        if self._monitor_task is None or self._monitor_task.done():
            self._monitor_task = asyncio.create_task(self._supervision_loop())
        logger.info("Supervisor started")

    async def stop(self) -> None:
        """Stops the supervisor. If on_exit is 'stop_all', terminates all managed processes."""
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        # Check on_exit setting
        on_exit = "leave_running"
        factory = get_session_factory()
        async with factory() as session:
            res = await session.execute(select(Setting).where(Setting.key == "on_exit"))
            row = res.scalar_one_or_none()
            if row:
                try:
                    on_exit = json.loads(row.value)
                except Exception:
                    pass

        if on_exit == "stop_all":
            logger.info("on_exit=stop_all: Stopping all managed components")
            for cid in list(self.components.keys()):
                await self.stop_component(cid, reason="system")

        # Stop all log tailers
        for tracked in self.components.values():
            if tracked.tailer:
                await tracked.tailer.stop()

    def get_tracked(self, component_id: str) -> TrackedComponent | None:
        return self.components.get(component_id)

    def remove_tracked(self, component_id: str) -> None:
        """Remove a tracked component entry (used when deleting an application)."""
        self.components.pop(component_id, None)

    async def get_or_create_tracked(self, component: Component) -> TrackedComponent:
        if component.id not in self.components:
            self.components[component.id] = TrackedComponent(
                component_id=component.id,
                app_id=component.application_id,
                name=component.name,
            )
        return self.components[component.id]

    async def _readopt_running_processes(self) -> None:
        """Re-adopts still-running children across Hangar restarts."""
        factory = get_session_factory()
        async with factory() as session:
            # Find runs without ended_at
            stmt = select(Run, Component).join(Component, Run.component_id == Component.id).where(Run.ended_at.is_(None))
            res = await session.execute(stmt)
            open_runs = res.all()

            for run, comp in open_runs:
                tracked = await self.get_or_create_tracked(comp)
                if is_process_match(run.pid, run.create_time):
                    # Process is still alive and matches!
                    tracked.pid = run.pid
                    tracked.create_time = run.create_time
                    tracked.active_run_id = run.id
                    tracked.active_log_path = Path(run.log_path)
                    tracked.status = "running"
                    tracked.status_reason = "Re-adopted on Hangar launch"

                    # Start log tailing
                    tailer = ComponentLogTailer(comp.id, run.id, tracked.active_log_path)
                    tailer.start()
                    tracked.tailer = tailer
                    logger.info("Re-adopted running process for component %s (PID: %d)", comp.name, run.pid)
                else:
                    # Process died while Hangar was offline
                    run.ended_at = datetime.datetime.utcnow()
                    run.stop_reason = "system"
                    run.exit_code = -1
                    session.add(run)
                    tracked.status = "stopped"
            await session.commit()

    async def start_component(self, component_id: str) -> tuple[bool, str]:
        """Starts a single component process."""
        async with self._lock:
            factory = get_session_factory()
            async with factory() as session:
                res = await session.execute(select(Component).where(Component.id == component_id))
                comp = res.scalar_one_or_none()
                if not comp:
                    return False, f"Component {component_id} not found"

                tracked = await self.get_or_create_tracked(comp)

                if tracked.status in {"starting", "running"}:
                    return True, f"Component {comp.name} is already {tracked.status}"

                # 1. Validation: check cwd
                cwd_path = Path(comp.cwd).resolve()
                if not cwd_path.exists():
                    msg = f"Working directory does not exist: {cwd_path}"
                    tracked.status = "failed"
                    tracked.status_reason = msg
                    await emit_event(
                        "error",
                        "start_failed",
                        f"Failed to start {comp.name}",
                        msg,
                        application_id=comp.application_id,
                        component_id=comp.id,
                        session=session,
                    )
                    await self._broadcast_status(comp.application_id, comp.id)
                    return False, msg

                # 2. Validation: check start_cmd
                if not comp.start_cmd or not comp.start_cmd.strip():
                    msg = f"Start command is empty"
                    tracked.status = "failed"
                    tracked.status_reason = msg
                    await emit_event(
                        "error",
                        "start_failed",
                        f"Failed to start {comp.name}",
                        msg,
                        application_id=comp.application_id,
                        component_id=comp.id,
                        session=session,
                    )
                    await self._broadcast_status(comp.application_id, comp.id)
                    return False, msg

                # 3. Validation: check port conflict
                if comp.port:
                    holder_pid, holder_name, _ = get_process_holding_port(comp.port)
                    if holder_pid:
                        msg = f"Port {comp.port} is in use by {holder_name} (pid {holder_pid}). Kill it and start, or change the port."
                        tracked.status = "failed"
                        tracked.status_reason = msg
                        await emit_event(
                            "error",
                            "port_conflict",
                            f"Port conflict for {comp.name}",
                            msg,
                            application_id=comp.application_id,
                            component_id=comp.id,
                            detail={"port": comp.port, "pid": holder_pid, "process_name": holder_name},
                            session=session,
                        )
                        await self._broadcast_status(comp.application_id, comp.id)
                        return False, msg

                # Fetch settings for shell override
                setting_res = await session.execute(select(Setting).where(Setting.key == "shell_override"))
                shell_row = setting_res.scalar_one_or_none()
                shell_override = json.loads(shell_row.value) if shell_row else None

                # Setup run
                run_id = str(uuid.uuid4())
                run_dir = LOGS_DIR / comp.id
                run_dir.mkdir(parents=True, exist_ok=True)
                log_path = run_dir / f"run-{run_id}.log"

                # Parse env dict
                try:
                    env_dict = json.loads(comp.env) if comp.env else {}
                except Exception:
                    env_dict = {}

                tracked.status = "starting"
                tracked.status_reason = "Spawning process"
                tracked.user_stopped = False
                tracked.start_time = time.time()
                await self._broadcast_status(comp.application_id, comp.id)

                try:
                    proc, pid, create_time = spawn_process(
                        cmd=comp.start_cmd,
                        cwd=cwd_path,
                        log_file_path=log_path,
                        env=env_dict,
                        port=comp.port,
                        shell_override=shell_override,
                    )
                except Exception as e:
                    tracked.status = "failed"
                    tracked.status_reason = f"Spawn error: {e}"
                    await emit_event(
                        "error",
                        "start_failed",
                        f"Failed to start {comp.name}",
                        str(e),
                        application_id=comp.application_id,
                        component_id=comp.id,
                        session=session,
                    )
                    await self._broadcast_status(comp.application_id, comp.id)
                    return False, str(e)

                tracked.proc = proc
                tracked.pid = pid
                tracked.create_time = create_time
                tracked.active_run_id = run_id
                tracked.active_log_path = log_path

                # Create Run record
                run = Run(
                    id=run_id,
                    component_id=comp.id,
                    pid=pid,
                    create_time=create_time,
                    started_at=datetime.datetime.utcnow(),
                    log_path=str(log_path),
                )
                session.add(run)
                await session.commit()

                # Start log tailer
                if tracked.tailer:
                    await tracked.tailer.stop()
                tailer = ComponentLogTailer(comp.id, run_id, log_path)
                tailer.start()
                tracked.tailer = tailer

                # Emit started event
                await emit_event(
                    "info",
                    "started",
                    f"{comp.name} started",
                    f"Process spawned with PID {pid}",
                    application_id=comp.application_id,
                    component_id=comp.id,
                )

        # Background task to wait for health check before marking "running"
        asyncio.create_task(self._wait_for_startup_health(comp.id, comp.application_id, comp.name))
        return True, "Process started"

    async def _wait_for_startup_health(self, component_id: str, app_id: str, name: str) -> None:
        """Polls health check during startup grace period to transition starting -> running."""
        factory = get_session_factory()
        async with factory() as session:
            res = await session.execute(select(Component).where(Component.id == component_id))
            comp = res.scalar_one_or_none()
            if not comp:
                return

            try:
                health_cfg = json.loads(comp.health) if comp.health else {}
            except Exception:
                health_cfg = {}

        grace_s = health_cfg.get("startup_grace_s", 30.0)
        start_t = time.time()
        tracked = self.components.get(component_id)

        while time.time() - start_t < grace_s:
            if not tracked or tracked.status != "starting" or tracked.user_stopped:
                return

            # Check if process is still alive
            if tracked.proc and tracked.proc.poll() is not None:
                # Died before reaching health
                return

            is_healthy, reason = await run_health_check(
                health_cfg,
                port=comp.port,
                pid=tracked.pid,
                cwd=comp.cwd,
            )

            if is_healthy:
                tracked.status = "running"
                tracked.status_reason = reason
                await self._broadcast_status(app_id, component_id)
                return

            await asyncio.sleep(0.5)

        # Grace period expired
        if tracked and tracked.status == "starting":
            tracked.status = "unhealthy"
            tracked.status_reason = f"Health check failed to pass within startup grace ({grace_s}s)"
            await emit_event(
                "warn",
                "unhealthy",
                f"{name} is unhealthy",
                tracked.status_reason,
                application_id=app_id,
                component_id=component_id,
            )
            await self._broadcast_status(app_id, component_id)

    async def stop_component(self, component_id: str, reason: str = "user") -> tuple[bool, str]:
        """Stops a component process tree and verifies port is freed."""
        tracked = self.components.get(component_id)
        if not tracked or tracked.status == "stopped":
            return True, "Component is already stopped"

        tracked.status = "stopping"
        tracked.user_stopped = True
        tracked.status_reason = f"Stopping ({reason})"
        await self._broadcast_status(tracked.app_id, component_id)

        factory = get_session_factory()
        async with factory() as session:
            res = await session.execute(select(Component).where(Component.id == component_id))
            comp = res.scalar_one_or_none()
            stop_cmd = comp.stop_cmd if comp else None
            port = comp.port if comp else None

        # Execute custom stop command if defined
        if stop_cmd and stop_cmd.strip():
            try:
                proc = await asyncio.create_subprocess_shell(
                    stop_cmd,
                    cwd=comp.cwd if comp else ".",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(proc.communicate(), timeout=10.0)
            except Exception as e:
                logger.warning("Stop command for %s failed: %s", component_id, e)

        # Terminate and kill full process tree
        if tracked.pid:
            kill_process_tree(tracked.pid, timeout_s=5.0)

        # Wait for port to be released
        if port:
            for _ in range(10):
                holder_pid, _, _ = get_process_holding_port(port)
                if not holder_pid or holder_pid != tracked.pid:
                    break
                await asyncio.sleep(0.3)

        # Insert system line into run log
        if tracked.active_log_path and tracked.active_log_path.exists():
            try:
                with open(tracked.active_log_path, "a", encoding="utf-8") as f:
                    f.write(f"\n[Hangar] Process stopped by {reason}\n")
            except Exception:
                pass
            if tracked.active_run_id:
                await bus.push_log(component_id, f"[Hangar] Process stopped by {reason}", tracked.active_run_id, is_system=True)

        # Close tailer
        if tracked.tailer:
            await tracked.tailer.stop()
            tracked.tailer = None

        # Update run in DB
        if tracked.active_run_id:
            async with factory() as session:
                run_res = await session.execute(select(Run).where(Run.id == tracked.active_run_id))
                run = run_res.scalar_one_or_none()
                if run:
                    run.ended_at = datetime.datetime.utcnow()
                    run.stop_reason = reason
                    run.exit_code = 0
                    session.add(run)
                    await session.commit()

        tracked.status = "stopped"
        tracked.status_reason = f"Stopped ({reason})"
        tracked.proc = None
        tracked.pid = None
        tracked.cpu_pct = 0.0
        tracked.rss_mb = 0.0

        await emit_event(
            "info",
            "stopped",
            f"{tracked.name} stopped",
            f"Component stopped by {reason}",
            application_id=tracked.app_id,
            component_id=component_id,
        )
        await self._broadcast_status(tracked.app_id, component_id)
        return True, "Stopped"

    async def restart_component(self, component_id: str) -> tuple[bool, str]:
        """Restarts a component: stop followed by start."""
        await self.stop_component(component_id, reason="restart")
        await asyncio.sleep(0.5)
        success, msg = await self.start_component(component_id)
        if success:
            tracked = self.components.get(component_id)
            if tracked:
                await emit_event(
                    "info",
                    "restarted",
                    f"{tracked.name} restarted",
                    "Component restarted successfully",
                    application_id=tracked.app_id,
                    component_id=component_id,
                )
        return success, msg

    async def _supervision_loop(self) -> None:
        """Periodic background loop checking process aliveness, crash detection, autorestart, and health."""
        while True:
            try:
                await asyncio.sleep(2.0)
                factory = get_session_factory()

                for cid, tracked in list(self.components.items()):
                    if tracked.status in {"running", "starting", "unhealthy"}:
                        # 1. Process exit / crash check
                        exit_code = None
                        if tracked.proc:
                            exit_code = tracked.proc.poll()
                        elif tracked.pid:
                            try:
                                p = psutil.Process(tracked.pid)
                                if not p.is_running() or p.status() == psutil.STATUS_ZOMBIE:
                                    exit_code = -1
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                exit_code = -1

                        if exit_code is not None:
                            # Process died!
                            if not tracked.user_stopped:
                                await self._handle_crash(tracked, exit_code)
                            else:
                                tracked.status = "stopped"
                                await self._broadcast_status(tracked.app_id, cid)
                            continue

                        # 2. Health check if status is running
                        if tracked.status == "running":
                            async with factory() as session:
                                res = await session.execute(select(Component).where(Component.id == cid))
                                comp = res.scalar_one_or_none()
                                if comp:
                                    try:
                                        h_cfg = json.loads(comp.health) if comp.health else {}
                                    except Exception:
                                        h_cfg = {}
                                    is_healthy, reason = await run_health_check(
                                        h_cfg,
                                        port=comp.port,
                                        pid=tracked.pid,
                                        cwd=comp.cwd,
                                    )
                                    if not is_healthy:
                                        tracked.status = "unhealthy"
                                        tracked.status_reason = reason
                                        await emit_event(
                                            "warn",
                                            "unhealthy",
                                            f"{tracked.name} unhealthy",
                                            reason,
                                            application_id=tracked.app_id,
                                            component_id=cid,
                                        )
                                        await self._broadcast_status(tracked.app_id, cid)

                        # 3. Health recovery check if status is unhealthy
                        elif tracked.status == "unhealthy":
                            async with factory() as session:
                                res = await session.execute(select(Component).where(Component.id == cid))
                                comp = res.scalar_one_or_none()
                                if comp:
                                    try:
                                        h_cfg = json.loads(comp.health) if comp.health else {}
                                    except Exception:
                                        h_cfg = {}
                                    is_healthy, reason = await run_health_check(
                                        h_cfg,
                                        port=comp.port,
                                        pid=tracked.pid,
                                        cwd=comp.cwd,
                                    )
                                    if is_healthy:
                                        tracked.status = "running"
                                        tracked.status_reason = "Health recovered"
                                        await emit_event(
                                            "info",
                                            "recovered",
                                            f"{tracked.name} recovered",
                                            "Health check is now passing",
                                            application_id=tracked.app_id,
                                            component_id=cid,
                                        )
                                        await self._broadcast_status(tracked.app_id, cid)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in supervisor loop: %s", e)

    async def _handle_crash(self, tracked: TrackedComponent, exit_code: int) -> None:
        """Handles an unexpected process termination."""
        cid = tracked.component_id
        app_id = tracked.app_id
        name = tracked.name

        tracked.status = "crashed"
        tracked.status_reason = f"Process exited unexpectedly with code {exit_code}"

        # Insert system line in run log
        if tracked.active_log_path and tracked.active_log_path.exists():
            try:
                with open(tracked.active_log_path, "a", encoding="utf-8") as f:
                    f.write(f"\n[Hangar] Process exited with code {exit_code}\n")
            except Exception:
                pass
            if tracked.active_run_id:
                await bus.push_log(cid, f"[Hangar] Process exited with code {exit_code}", tracked.active_run_id, is_system=True)

        # Get last 20 log lines for event detail
        last_lines = read_last_n_lines(tracked.active_log_path or "", n=20)

        # Update run in DB
        factory = get_session_factory()
        async with factory() as session:
            if tracked.active_run_id:
                run_res = await session.execute(select(Run).where(Run.id == tracked.active_run_id))
                run = run_res.scalar_one_or_none()
                if run:
                    run.ended_at = datetime.datetime.utcnow()
                    run.exit_code = exit_code
                    run.stop_reason = "crash"
                    session.add(run)

            comp_res = await session.execute(select(Component).where(Component.id == cid))
            comp = comp_res.scalar_one_or_none()
            autorestart = comp.autorestart if comp else True
            max_restarts = comp.max_restarts if comp else 5
            await session.commit()

        await emit_event(
            "error",
            "crash",
            f"{name} crashed",
            f"Exited with code {exit_code}",
            application_id=app_id,
            component_id=cid,
            detail={"exit_code": exit_code, "last_lines": last_lines},
        )
        await self._broadcast_status(app_id, cid)

        # Check autorestart & backoff
        if autorestart:
            now = time.time()
            # Prune restarts older than 5 minutes (300 s)
            tracked.restart_timestamps = [t for t in tracked.restart_timestamps if now - t < 300]

            if len(tracked.restart_timestamps) >= max_restarts:
                # Restart loop triggered!
                msg = f"{name} exceeded max restarts ({max_restarts} in 5 min). Giving up."
                logger.warning(msg)
                await emit_event(
                    "error",
                    "restart_loop",
                    f"Restart loop on {name}",
                    msg,
                    application_id=app_id,
                    component_id=cid,
                )
                return

            restart_count = len(tracked.restart_timestamps)
            tracked.restart_timestamps.append(now)
            # Backoff: 1, 2, 4, 8, 16 s
            backoff_s = min(16, 2 ** restart_count)
            logger.info("Scheduling autorestart for %s in %ds (attempt %d)", name, backoff_s, restart_count + 1)

            async def _do_restart():
                await asyncio.sleep(backoff_s)
                if tracked.status == "crashed" and not tracked.user_stopped:
                    await self.start_component(cid)

            asyncio.create_task(_do_restart())

    async def _broadcast_status(self, app_id: str, component_id: str) -> None:
        """Computes and broadcasts the component and application status over WebSocket."""
        tracked = self.components.get(component_id)
        c_status = tracked.status if tracked else "stopped"
        c_reason = tracked.status_reason if tracked else None

        # Compute rolled up application status
        app_status = await self.compute_application_status(app_id)

        payload = {
            "type": "status_update",
            "application_id": app_id,
            "component_id": component_id,
            "component_status": c_status,
            "component_status_reason": c_reason,
            "application_status": app_status,
        }
        await bus.broadcast("status", payload)

    async def compute_application_status(self, app_id: str) -> str:
        """
        Application status rolled up:
        - any crashed/failed -> problem
        - else any unhealthy -> degraded
        - some running some stopped -> partial
        - all running -> running
        - all stopped -> stopped
        """
        factory = get_session_factory()
        async with factory() as session:
            res = await session.execute(select(Component).where(Component.application_id == app_id))
            components = res.scalars().all()

        if not components:
            return "stopped"

        statuses: list[ComponentStatusType] = []
        for c in components:
            tracked = self.components.get(c.id)
            if tracked:
                statuses.append(tracked.status)
            else:
                statuses.append("stopped")

        if any(s in {"crashed", "failed"} for s in statuses):
            return "problem"
        if any(s == "unhealthy" for s in statuses):
            return "degraded"

        running_or_starting = [s for s in statuses if s in {"running", "starting"}]
        if len(running_or_starting) == len(statuses):
            return "running"
        if len(running_or_starting) > 0:
            return "partial"
        return "stopped"


supervisor = Supervisor()

