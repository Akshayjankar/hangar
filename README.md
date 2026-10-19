# Hangar ✈️

> A personal control panel for your localhost projects.

Hangar is a single-user dashboard running on your local machine to register, monitor, start, stop, and inspect frontend, backend, database, and worker processes.

> **CRITICAL SECURITY NOTICE**: Never expose Hangar to a public network. Hangar binds strictly to `127.0.0.1` and is designed exclusively for localhost single-user operation.

---

## Features
- **Process Orchestration**: Start, stop, and restart individual components or entire applications in ordered tier sequence (database ➔ backend ➔ frontend).
- **Process Tree Control**: Gracefully terminates and forcefully kills entire process trees (avoiding orphaned child processes and hung ports).
- **Live Logs**: Tailed directly from disk (`logs/<component_id>/run-<run_id>.log`) over WebSocket with merged stdout/stderr.
- **Resource Monitoring**: Real-time CPU, RSS memory, and thread metrics with 1-minute historical persistence.
- **Port Conflict Management**: Detects listening TCP ports, highlights conflicts, and allows single-click cleanup.
- **Project Removal**: Safely removes projects from the dashboard with optional process termination and log cleanup, while guaranteeing that source code and project directories are never touched.
- **Local Autodetect**: Scans local folders for Next.js, Vite, FastAPI, Django, Flask, Express, Docker Compose, etc.
- **Sample Apps**: Shipped with self-contained Python sample apps (Sample Shop, Sample Blog) that work on day one with zero external tools.

---

## Installation & Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend development and building)

### Running Hangar
```bash
# 1. Install dependencies
pip install -r backend/requirements.lock
npm ci --prefix frontend

# 2. Build the frontend
npm run build --prefix frontend

# 3. Launch Hangar
python -m hangar
```

Open `http://localhost:7777` in your browser.

---

## Development

Run frontend and backend simultaneously in hot-reloading dev mode:
```powershell
# Windows
.\scripts\dev.ps1
```
```bash
# Linux / macOS
./scripts/dev.sh
```

Frontend runs on `http://localhost:3000` with API proxying to `http://127.0.0.1:7777`.

---

## Testing
```bash
# Backend unit & integration tests
pytest backend/tests

# Frontend typecheck & lint
npm run typecheck --prefix frontend
```
