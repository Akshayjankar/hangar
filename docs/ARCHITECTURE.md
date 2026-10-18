# Hangar Architecture

Hangar is a lightweight, single-user dashboard for managing local development projects (frontends, backends, databases, workers) on your local machine.

## High-Level Topology

```
Browser  ── REST /api + WebSocket /ws ──►  FastAPI (127.0.0.1:7777)
 Next.js static export served by FastAPI     ├─ Supervisor: spawn, track, stop process trees
 (dev: Next on :3000, proxy /api)            ├─ Health checker, metrics sampler (psutil)
                                             ├─ Log tailer (files on disk) ─► WebSocket bus
                                             ├─ Event engine ─► notifications
                                             └─ SQLite (config, runs, events, 1-min metrics)
Child processes (your projects) write stdout+stderr straight to per-run log files.
```

## Key Principles & Design Decisions

1. **Localhost Only**: Backend strictly binds to `127.0.0.1` on port 7777 (or `$HANGAR_PORT`). Non-local hosts, invalid origins, and requests lacking `X-Hangar-Client: 1` are rejected with HTTP 403.
2. **Offline-First & Self-Contained**: No external CDN links, no cloud analytics, and no remote calls. Fonts are locally bundled via NPM (`@fontsource-variable/bricolage-grotesque` and `@fontsource/jetbrains-mono`).
3. **Data Location**: Stored in `~/.hangar` (configurable via `HANGAR_HOME`):
   - `hangar.db`: SQLite database managed via SQLAlchemy 2 + aiosqlite.
   - `logs/<component_id>/run-<run_id>.log`: Per-run output files with merged stdout and stderr.
4. **Resilient Process Supervision**:
   - Spawns child processes in their own process groups.
   - Stops processes cleanly using tree termination: graceful SIGTERM / `psutil.terminate()`, 5-second wait, followed by `psutil.kill()` (with `taskkill /T /F` fallback on Windows), then verifies port release.
   - Re-adopts running children across Hangar restarts by tracking PID + process creation time in `runs`.
5. **Real-Time Communication**:
   - Unified WebSocket at `/ws` for live component status, job step execution, event notifications, log tailing, and metrics.
   - Efficient disk-to-WebSocket tailing with 200 ms polling and batched delivery (max 50 lines per 100 ms).

## Justification of Dependencies

### Backend
- **fastapi**: High-performance async ASGI web framework for REST API and WebSockets.
- **uvicorn[standard]**: Production-ready ASGI server for serving API and static files.
- **pydantic (v2)**: Robust data validation, settings management, and serialization.
- **sqlalchemy (v2)**: Modern async ORM and query builder for SQLite.
- **aiosqlite**: Async SQLite driver allowing non-blocking database queries within the FastAPI event loop.
- **psutil**: Cross-platform process and system monitoring (tree termination, CPU/RSS sampling, listening port detection).
- **httpx**: Async HTTP client for performing HTTP GET health checks.
- **pytest & pytest-asyncio**: Unit and integration test runners for async backend endpoints and supervisor logic.

### Frontend
- **next & react**: Standard React framework used in static export mode (`output: 'export'`) for production.
- **typescript**: Type safety across UI models and API clients.
- **tailwindcss**: Utility-first CSS styling strictly adhering to the blueprint design token system.
- **lucide-react**: Lightweight icon set for all controls, statuses, and navigation.
- **echarts**: Modular, accessible charting library for time-series metrics, donuts, and heatmaps.
- **@tanstack/react-virtual**: Virtualization for high-throughput log streams (up to 100,000 lines).
- **@radix-ui/react-\*** (`dialog`, `tooltip`, `dropdown-menu`, `popover`): Accessible, unstyled primitives with keyboard navigation and focus trapping.
- **@fontsource-variable/bricolage-grotesque** & **@fontsource/jetbrains-mono**: Self-hosted fonts ensuring zero network reliance.
