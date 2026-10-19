from __future__ import annotations
import asyncio
import logging
import uuid
from typing import Literal
from sqlalchemy import select

from ..db import get_session_factory
from ..models import Application, Component
from ..schemas import JobRead, JobStep
from .bus import bus
from .events import emit_event
from .supervisor import supervisor

logger = logging.getLogger("hangar.orchestrator")


class OrchestrationManager:
    """
    Coordinates application-level start/stop/restart operations.
    Enforces application-level lock to prevent concurrent jobs on the same app.
    Pushes step progress live over WebSocket.
    """

    def __init__(self) -> None:
        self.jobs: dict[str, JobRead] = {}
        self._app_locks: dict[str, asyncio.Lock] = {}
        self._lock = asyncio.Lock()

    async def get_app_lock(self, app_id: str) -> asyncio.Lock:
        async with self._lock:
            if app_id not in self._app_locks:
                self._app_locks[app_id] = asyncio.Lock()
            return self._app_locks[app_id]

    def get_job(self, job_id: str) -> JobRead | None:
        return self.jobs.get(job_id)

    async def start_application(self, app_id: str) -> JobRead:
        lock = await self.get_app_lock(app_id)
        if lock.locked():
            raise RuntimeError(f"An action is already in progress for this application.")

        factory = get_session_factory()
        async with factory() as session:
            res = await session.execute(select(Application).where(Application.id == app_id))
            app = res.scalar_one_or_none()
            if not app:
                raise ValueError("Application not found")

            comp_res = await session.execute(
                select(Component).where(Component.application_id == app_id).order_by(Component.tier.asc())
            )
            components = comp_res.scalars().all()

        job_id = str(uuid.uuid4())
        steps = [
            JobStep(
                component_id=c.id,
                component_name=c.name,
                action="start",
                status="pending",
            )
            for c in components
        ]

        job = JobRead(
            id=job_id,
            application_id=app_id,
            action="start_app",
            status="running",
            current_step=0,
            total_steps=len(steps),
            steps=steps,
        )
        self.jobs[job_id] = job

        # Launch background execution under the app lock
        asyncio.create_task(self._run_start_job(job, components, app.start_mode))
        return job

    async def stop_application(self, app_id: str) -> JobRead:
        lock = await self.get_app_lock(app_id)
        if lock.locked():
            raise RuntimeError(f"An action is already in progress for this application.")

        factory = get_session_factory()
        async with factory() as session:
            res = await session.execute(select(Application).where(Application.id == app_id))
            app = res.scalar_one_or_none()
            if not app:
                raise ValueError("Application not found")

            # Reverse order for stopping: frontend (tier 3) -> backend (2) -> db (1)
            comp_res = await session.execute(
                select(Component).where(Component.application_id == app_id).order_by(Component.tier.desc())
            )
            components = comp_res.scalars().all()

        job_id = str(uuid.uuid4())
        steps = [
            JobStep(
                component_id=c.id,
                component_name=c.name,
                action="stop",
                status="pending",
            )
            for c in components
        ]

        job = JobRead(
            id=job_id,
            application_id=app_id,
            action="stop_app",
            status="running",
            current_step=0,
            total_steps=len(steps),
            steps=steps,
        )
        self.jobs[job_id] = job

        asyncio.create_task(self._run_stop_job(job, components, app.start_mode))
        return job

    async def restart_application(self, app_id: str) -> JobRead:
        """Stops then starts the application."""
        await self.stop_application(app_id)
        # Wait a moment, then start
        await asyncio.sleep(2.0)
        return await self.start_application(app_id)

    async def _run_start_job(self, job: JobRead, components: list[Component], start_mode: str) -> None:
        lock = await self.get_app_lock(job.application_id)
        async with lock:
            await self._push_job_update(job)

            if start_mode == "parallel":
                # Parallel start: start all simultaneously
                tasks = []
                for i, c in enumerate(components):
                    job.steps[i].status = "running"
                    tasks.append(supervisor.start_component(c.id))
                await self._push_job_update(job)

                results = await asyncio.gather(*tasks, return_exceptions=True)
                has_failure = False
                for i, r in enumerate(results):
                    if isinstance(r, Exception) or (isinstance(r, tuple) and not r[0]):
                        job.steps[i].status = "failed"
                        job.steps[i].error = str(r)
                        has_failure = True
                    else:
                        job.steps[i].status = "success"

                job.status = "failed" if has_failure else "completed"
                await self._push_job_update(job)
                return

            # Ordered start: start tier by tier, wait for health before proceeding to next tier
            # Group components by tier
            tiers: dict[int, list[tuple[int, Component]]] = {}
            for idx, c in enumerate(components):
                tiers.setdefault(c.tier, []).append((idx, c))

            sorted_tiers = sorted(tiers.keys())

            for tier_num in sorted_tiers:
                tier_items = tiers[tier_num]
                # Start all components in this tier
                for idx, comp in tier_items:
                    job.current_step = idx + 1
                    job.steps[idx].status = "running"
                    await self._push_job_update(job)

                    success, msg = await supervisor.start_component(comp.id)
                    if not success:
                        job.steps[idx].status = "failed"
                        job.steps[idx].error = msg
                        job.status = "failed"
                        job.error = f"Step failed at {comp.name}: {msg}"

                        # Mark remaining steps skipped
                        for rem_idx in range(idx + 1, len(job.steps)):
                            job.steps[rem_idx].status = "skipped"

                        await self._push_job_update(job)
                        return

                # Wait for all components in this tier to become "running" (passing health check)
                tier_comps = [comp for _, comp in tier_items]
                wait_start = asyncio.get_event_loop().time()
                while True:
                    all_healthy = True
                    for c in tier_comps:
                        tracked = supervisor.get_tracked(c.id)
                        if not tracked or tracked.status in {"failed", "crashed"}:
                            job.status = "failed"
                            job.error = f"{c.name} failed during startup."
                            await self._push_job_update(job)
                            return
                        if tracked.status != "running":
                            all_healthy = False

                    if all_healthy:
                        for idx, _ in tier_items:
                            job.steps[idx].status = "success"
                        await self._push_job_update(job)
                        break

                    if asyncio.get_event_loop().time() - wait_start > 30.0:
                        # Timeout waiting for health
                        for idx, _ in tier_items:
                            job.steps[idx].status = "failed"
                            job.steps[idx].error = "Startup health check timed out"
                        job.status = "failed"
                        job.error = f"Tier {tier_num} health timeout"
                        await self._push_job_update(job)
                        return

                    await asyncio.sleep(0.5)

            job.status = "completed"
            await self._push_job_update(job)

    async def _run_stop_job(self, job: JobRead, components: list[Component], start_mode: str) -> None:
        lock = await self.get_app_lock(job.application_id)
        async with lock:
            await self._push_job_update(job)

            for idx, comp in enumerate(components):
                job.current_step = idx + 1
                job.steps[idx].status = "running"
                await self._push_job_update(job)

                await supervisor.stop_component(comp.id, reason="user")
                job.steps[idx].status = "success"
                await self._push_job_update(job)

            job.status = "completed"
            await self._push_job_update(job)

    async def _push_job_update(self, job: JobRead) -> None:
        channel = f"job:{job.id}"
        await bus.broadcast(channel, job.model_dump())
        await bus.broadcast("job.step", job.model_dump())


orchestrator = OrchestrationManager()

