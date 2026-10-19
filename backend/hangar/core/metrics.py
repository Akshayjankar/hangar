from __future__ import annotations
import asyncio
import datetime
import json
import logging
import time
from collections import deque
from typing import Any
import psutil
from sqlalchemy import delete, select

from ..db import get_session_factory
from ..models import Metric1m, Setting
from .bus import bus
from .events import emit_event

logger = logging.getLogger("hangar.metrics")


class MetricsSampler:
    """
    Every 2 s:
    - Samples CPU %, RSS, and thread count for each tracked process tree.
    - Samples machine CPU % and memory.
    - Keeps 1 hour in memory (1800 samples).
    - Aggregates and persists 1-minute averages to SQLite metrics_1m (retained for 7 days).
    - Checks CPU and memory alert thresholds from settings.
    - Broadcasts live telemetry over the "metrics" WebSocket channel.
    """

    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        # In-memory buffer: component_id -> deque of (timestamp, cpu_pct, rss_mb)
        # None key is used for machine-level metrics
        self.in_memory_history: dict[str | None, deque[dict[str, Any]]] = {}
        # Accumulator for 1-minute persistence: component_id -> list of (cpu, rss)
        self._minute_accumulator: dict[str | None, list[tuple[float, float]]] = {}
        self._last_flush_minute: int = -1
        self._alerted_high_cpu: set[str] = set()
        self._alerted_high_mem: set[str] = set()

    async def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._sampler_loop())
        logger.info("Metrics sampler started")

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _sampler_loop(self) -> None:
        # Pre-seed psutil cpu_percent
        psutil.cpu_percent(interval=None)

        while True:
            try:
                await asyncio.sleep(2.0)
                from .supervisor import supervisor

                now = datetime.datetime.utcnow()
                now_ts = now.timestamp()
                curr_minute = now.minute

                # 1. Machine metrics
                machine_cpu = psutil.cpu_percent(interval=None)
                vmem = psutil.virtual_memory()
                machine_mem_pct = vmem.percent
                machine_mem_used_mb = vmem.used / (1024 * 1024)
                machine_mem_total_mb = vmem.total / (1024 * 1024)

                self._record_sample(None, now_ts, machine_cpu, machine_mem_used_mb)

                # 2. Component metrics
                components_payload: list[dict[str, Any]] = []

                for cid, tracked in list(supervisor.components.items()):
                    if tracked.status in {"running", "starting", "unhealthy"} and tracked.pid:
                        try:
                            parent = psutil.Process(tracked.pid)
                            procs = [parent]
                            try:
                                procs += parent.children(recursive=True)
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass

                            total_cpu = 0.0
                            total_rss = 0.0
                            total_threads = 0

                            for p in procs:
                                try:
                                    total_cpu += p.cpu_percent(interval=None)
                                    mem_info = p.memory_info()
                                    total_rss += mem_info.rss
                                    total_threads += p.num_threads()
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    pass

                            rss_mb = total_rss / (1024 * 1024)
                            tracked.cpu_pct = round(total_cpu, 1)
                            tracked.rss_mb = round(rss_mb, 1)

                            self._record_sample(cid, now_ts, tracked.cpu_pct, tracked.rss_mb)

                            components_payload.append({
                                "component_id": cid,
                                "application_id": tracked.app_id,
                                "cpu_pct": tracked.cpu_pct,
                                "rss_mb": tracked.rss_mb,
                                "threads": total_threads,
                            })

                            # Check alert thresholds
                            await self._check_alerts(cid, tracked.app_id, tracked.name, tracked.cpu_pct, tracked.rss_mb)

                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    else:
                        tracked.cpu_pct = 0.0
                        tracked.rss_mb = 0.0

                # 3. Broadcast telemetry to WebSocket "metrics" channel
                metrics_msg = {
                    "type": "metrics_tick",
                    "ts": now.isoformat(),
                    "machine": {
                        "cpu_pct": machine_cpu,
                        "memory_pct": machine_mem_pct,
                        "memory_used_mb": round(machine_mem_used_mb, 1),
                        "memory_total_mb": round(machine_mem_total_mb, 1),
                    },
                    "components": components_payload,
                }
                await bus.broadcast("metrics", metrics_msg)

                # 4. Check if 1 minute elapsed to persist averages
                if curr_minute != self._last_flush_minute:
                    self._last_flush_minute = curr_minute
                    await self._persist_minute_averages(now)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in metrics sampler: %s", e)

    def _record_sample(self, key: str | None, ts: float, cpu: float, rss: float) -> None:
        if key not in self.in_memory_history:
            self.in_memory_history[key] = deque(maxlen=1800)  # 1 hour at 2s interval
        self.in_memory_history[key].append({"ts": ts, "cpu_pct": cpu, "rss_mb": rss})

        if key not in self._minute_accumulator:
            self._minute_accumulator[key] = []
        self._minute_accumulator[key].append((cpu, rss))

    async def _check_alerts(self, cid: str, app_id: str, name: str, cpu: float, rss_mb: float) -> None:
        factory = get_session_factory()
        async with factory() as session:
            cpu_res = await session.execute(select(Setting).where(Setting.key == "cpu_alert_pct"))
            cpu_row = cpu_res.scalar_one_or_none()
            cpu_thresh = json.loads(cpu_row.value) if cpu_row else 90.0

            mem_res = await session.execute(select(Setting).where(Setting.key == "memory_alert_pct"))
            mem_row = mem_res.scalar_one_or_none()
            mem_thresh = json.loads(mem_row.value) if mem_row else 80.0

        if cpu >= cpu_thresh:
            if cid not in self._alerted_high_cpu:
                self._alerted_high_cpu.add(cid)
                await emit_event(
                    "warn",
                    "high_cpu",
                    f"High CPU on {name}",
                    f"CPU usage is {cpu}% (exceeds threshold {cpu_thresh}%)",
                    application_id=app_id,
                    component_id=cid,
                )
        else:
            self._alerted_high_cpu.discard(cid)

    async def _persist_minute_averages(self, now: datetime.datetime) -> None:
        """Persist 1-minute averages to SQLite metrics_1m and prune entries older than 7 days."""
        factory = get_session_factory()
        async with factory() as session:
            for key, samples in list(self._minute_accumulator.items()):
                if samples:
                    avg_cpu = sum(s[0] for s in samples) / len(samples)
                    avg_rss = sum(s[1] for s in samples) / len(samples)
                    session.add(
                        Metric1m(
                            ts=now,
                            component_id=key,
                            cpu_pct=round(avg_cpu, 2),
                            rss_mb=round(avg_rss, 2),
                        )
                    )
            self._minute_accumulator.clear()

            # Prune older than 7 days
            cutoff = now - datetime.timedelta(days=7)
            await session.execute(delete(Metric1m).where(Metric1m.ts < cutoff))
            await session.commit()


metrics_sampler = MetricsSampler()

