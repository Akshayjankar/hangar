from __future__ import annotations
import asyncio
import json
import logging
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger("hangar.bus")


class EventBus:
    """
    WebSocket message bus allowing clients to subscribe to channels:
    - "status": live component and application status changes
    - "events": system/process alerts, crash reports, info events
    - "metrics": 2-second resource telemetry
    - "logs:<componentId>": streaming process log output
    - "job:<jobId>": multi-step orchestration job progress
    """

    def __init__(self) -> None:
        # Map websocket to set of subscribed channels
        self._clients: dict[WebSocket, set[str]] = {}
        # Buffer for log lines per component: component_id -> list[str]
        self._log_buffers: dict[str, list[dict[str, Any]]] = {}
        self._flusher_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        if self._flusher_task is None or self._flusher_task.done():
            self._flusher_task = asyncio.create_task(self._log_flush_loop())

    async def stop(self) -> None:
        if self._flusher_task and not self._flusher_task.done():
            self._flusher_task.cancel()
            try:
                await self._flusher_task
            except asyncio.CancelledError:
                pass
            self._flusher_task = None

    async def register(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients[ws] = set()
        logger.debug("Client registered to bus (%d total)", len(self._clients))

    async def unregister(self, ws: WebSocket) -> None:
        async with self._lock:
            if ws in self._clients:
                del self._clients[ws]
        logger.debug("Client unregistered from bus (%d remaining)", len(self._clients))

    async def subscribe(self, ws: WebSocket, channel: str) -> None:
        async with self._lock:
            if ws in self._clients:
                self._clients[ws].add(channel)
        logger.debug("Client subscribed to channel %s", channel)

    async def unsubscribe(self, ws: WebSocket, channel: str) -> None:
        async with self._lock:
            if ws in self._clients:
                self._clients[ws].discard(channel)
        logger.debug("Client unsubscribed from channel %s", channel)

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        """Broadcast message to all clients subscribed to channel."""
        targets: list[WebSocket] = []
        async with self._lock:
            for ws, channels in self._clients.items():
                if channel in channels:
                    targets.append(ws)

        if not targets:
            return

        payload = json.dumps({"channel": channel, "data": message})
        stale: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_text(payload)
            except Exception:
                stale.append(ws)

        if stale:
            async with self._lock:
                for ws in stale:
                    if ws in self._clients:
                        del self._clients[ws]

    async def push_log(self, component_id: str, line: str, run_id: str, is_system: bool = False) -> None:
        """Enqueue a log line into the batched delivery buffer."""
        async with self._lock:
            if component_id not in self._log_buffers:
                self._log_buffers[component_id] = []
            self._log_buffers[component_id].append({
                "component_id": component_id,
                "line": line,
                "run_id": run_id,
                "is_system": is_system,
            })

    async def _log_flush_loop(self) -> None:
        """Flushes buffered log lines every 100 ms in batches of up to 50 lines."""
        while True:
            try:
                await asyncio.sleep(0.1)
                batches_to_send: dict[str, list[dict[str, Any]]] = {}

                async with self._lock:
                    if not self._log_buffers:
                        continue
                    for cid, lines in list(self._log_buffers.items()):
                        if lines:
                            batch = lines[:50]
                            batches_to_send[cid] = batch
                            self._log_buffers[cid] = lines[50:]
                            if not self._log_buffers[cid]:
                                del self._log_buffers[cid]

                for cid, batch in batches_to_send.items():
                    channel = f"logs:{cid}"
                    await self.broadcast(channel, {"type": "log_batch", "lines": batch})
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in bus log flush loop: %s", e)


bus = EventBus()

