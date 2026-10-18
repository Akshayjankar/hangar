from __future__ import annotations
import asyncio
import io
import logging
import os
import re
from pathlib import Path
from typing import Any

from .bus import bus

logger = logging.getLogger("hangar.logtail")


class ComponentLogTailer:
    """Tails active run log file for a component and streams new lines to the event bus."""

    def __init__(self, component_id: str, run_id: str, log_path: Path | str) -> None:
        self.component_id = component_id
        self.run_id = run_id
        self.log_path = Path(log_path)
        self._stopped = False
        self._task: asyncio.Task | None = None
        self._last_offset = 0

    def start(self) -> None:
        self._stopped = False
        self._task = asyncio.create_task(self._tail_loop())

    async def stop(self) -> None:
        self._stopped = True
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _tail_loop(self) -> None:
        """Polls log file every 200ms for newly written lines."""
        while not self._stopped:
            try:
                await asyncio.sleep(0.2)
                if not self.log_path.exists():
                    continue

                file_size = self.log_path.stat().st_size
                if file_size < self._last_offset:
                    # File was truncated or rotated
                    self._last_offset = 0

                if file_size > self._last_offset:
                    with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
                        f.seek(self._last_offset)
                        new_content = f.read()
                        self._last_offset = f.tell()

                    if new_content:
                        lines = new_content.splitlines()
                        for line in lines:
                            await bus.push_log(self.component_id, line, self.run_id)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error tailing log %s: %s", self.log_path, e)


def read_last_n_lines(file_path: Path | str, n: int = 100) -> list[str]:
    """Reads the last n lines of a file efficiently by seeking backwards in blocks."""
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return []

    lines: list[str] = []
    buffer_size = 8192

    try:
        with open(path, "rb") as f:
            f.seek(0, io.SEEK_END)
            end_pos = f.tell()
            remaining_bytes = end_pos
            blocks: list[bytes] = []

            while remaining_bytes > 0 and len(lines) <= n:
                read_size = min(buffer_size, remaining_bytes)
                remaining_bytes -= read_size
                f.seek(remaining_bytes, io.SEEK_SET)
                chunk = f.read(read_size)
                blocks.insert(0, chunk)
                full_text = b"".join(blocks).decode("utf-8", errors="replace")
                lines = full_text.splitlines()

            return lines[-n:]
    except Exception as e:
        logger.error("Error reading last lines of %s: %s", path, e)
        return []


def search_log_lines(
    file_path: Path | str,
    query: str | None = None,
    is_regex: bool = False,
    max_lines: int = 200,
) -> list[str]:
    """Search log lines matching query or regex."""
    lines = read_last_n_lines(file_path, n=max_lines * 5)
    if not query:
        return lines[-max_lines:]

    results: list[str] = []
    if is_regex:
        try:
            pattern = re.compile(query, re.IGNORECASE)
            for l in lines:
                if pattern.search(l):
                    results.append(l)
        except re.error:
            # Fallback to substring if regex is invalid
            for l in lines:
                if query.lower() in l.lower():
                    results.append(l)
    else:
        q_lower = query.lower()
        for l in lines:
            if q_lower in l.lower():
                results.append(l)

    return results[-max_lines:]

