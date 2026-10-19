# Hangar — How to Run & How It Works

> **Hangar** is a single-user localhost dashboard to register, start, stop, and monitor your local development projects — all from one screen.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step-by-Step: Running the Project](#step-by-step-running-the-project)
3. [How the Application Works](#how-the-application-works)
4. [Adding an Application](#adding-an-application)
5. [Where Do Applications Run?](#where-do-applications-run)
6. [Starting, Stopping, and Restarting](#starting-stopping-and-restarting)
7. [Logs](#logs)
8. [Activity & Notifications](#activity--notifications)
9. [Settings](#settings)
10. [Architecture Overview](#architecture-overview)

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | Must be in system PATH |
| Node.js | 18+ | For frontend dev server |
| pip | any | Comes with Python |
| npm | 9+ | Comes with Node.js |
| Git | any | Optional, for version control |

---

## Step-by-Step: Running the Project

### 1. Clone / Download the Project

```bash
git clone https://github.com/Akshayjankar/hangar.git
cd hangar
```

Or extract `Hanger_1810.zip` and open a terminal inside the `Hangar` folder.

---

### 2. Set Up the Python Virtual Environment

```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Install Python Dependencies

```bash
pip install -r backend/requirements.lock
```

Or using pyproject.toml:

```bash
cd backend
pip install -e .
cd ..
```

---

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

### 5. Run in Development Mode (Two Terminals)

**Terminal 1 — Backend (FastAPI)**

```powershell
# Windows
$env:PYTHONPATH = "C:\path\to\Hangar\backend"
$env:HANGAR_DEV_ORIGIN = "http://localhost:3002"
python -m uvicorn hangar.main:app --reload --host 127.0.0.1 --port 7777
```

```bash
# macOS / Linux
PYTHONPATH=./backend HANGAR_DEV_ORIGIN=http://localhost:3002 \
  uvicorn hangar.main:app --reload --host 127.0.0.1 --port 7777
```

**Terminal 2 — Frontend (Next.js)**

```powershell
# Windows
cd frontend
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:7777"
$env:NEXT_PUBLIC_WS_URL  = "ws://127.0.0.1:7777/ws"
npm run dev
```

```bash
# macOS / Linux
cd frontend
NEXT_PUBLIC_API_URL=http://127.0.0.1:7777 \
  NEXT_PUBLIC_WS_URL=ws://127.0.0.1:7777/ws \
  npm run dev
```

Then open **http://localhost:3002** in your browser.

---

### 6. Run using the Scripts (Recommended)

Pre-built scripts handle both servers in one command:

**Windows:**
```powershell
.\scripts\dev.ps1
```

**macOS / Linux:**
```bash
bash scripts/dev.sh
```

---

### 7. Production Mode (Build + Serve)

```powershell
# Windows
.\scripts\build.ps1
.\scripts\start.ps1
```

```bash
# macOS / Linux
bash scripts/build.sh
bash scripts/start.sh
```

This builds the Next.js static export and serves it directly from FastAPI at:
```
http://localhost:7777
```

---

### 8. Load Sample Applications (Optional)

After the app is running, click **"Load samples"** in the header, or call:

```bash
curl -X POST http://localhost:7777/api/samples/load \
  -H "X-Hangar-Client: 1" \
  -H "Origin: http://localhost:3002"
```

This creates two demo projects:
- **Sample Shop** — web (4101), API (4102), DB (4103)
- **Sample Blog** — web (4111), API (4112), DB (sqlite file)

---

## How the Application Works

### System Architecture

```
Browser (http://localhost:3002 in dev / http://localhost:7777 in prod)
   │
   ├── REST API (/api/*)  ──────────────►  FastAPI  (127.0.0.1:7777)
   │                                          │
   └── WebSocket (/ws)  ─────────────────────┤
                                              ├─ Supervisor    → spawns & tracks child processes
                                              ├─ Health Checker → TCP / HTTP / process probes
                                              ├─ Log Tailer    → reads log files, streams over WS
                                              ├─ Metrics       → CPU, RSS samples every 2s
                                              ├─ Events Engine → crash / start / stop events
                                              └─ SQLite DB     → ~/.hangar/hangar.db
```

### Data Storage

Hangar stores all its data in **`~/.hangar/`** (your user home directory):

| Path | Contents |
|---|---|
| `~/.hangar/hangar.db` | SQLite database: all apps, components, runs, events, metrics, settings |
| `~/.hangar/logs/<component_id>/run-<run_id>.log` | Live stdout+stderr output from each process run |

> **Your project source code is never touched.** Hangar only stores its own metadata and log copies.

---

## Adding an Application

1. Click **"Add application"** in the top-right header.
2. Fill in the form:
   - **Name** — display name (e.g. *My Shop*)
   - **Description** — optional short description
   - **Project folder** — the root path of your project on disk
   - **Tags** — optional tags for filtering
3. Add one or more **Components** (e.g. Frontend, Backend, Database):
   - **Name** — component label (e.g. *shop-api*)
   - **Kind** — `frontend`, `backend`, `database`, or `worker`
   - **Working directory** — where to run the command from
   - **Start command** — e.g. `npm run dev` or `uvicorn main:app --reload --port 8000`
   - **Stop command** — optional; if blank, Hangar kills the process tree
   - **Port** — the port the component listens on (used for health checks and status)
   - **Health check type** — TCP (default), HTTP GET, or process-alive
4. Click **Save and register**.

The application appears immediately in the dashboard. Its status starts as **Stopped**.

---

## Where Do Applications Run?

- **Applications run on your local machine**, in their own **project folder** (the `cwd` you configured).
- Hangar spawns each component as a **child process** — it does not use Docker, SSH, or any containers (unless you set a Docker command yourself).
- All child processes are started in their **own process group** so Hangar can stop the entire tree (including child spawns) cleanly.
- Child process stdout and stderr are **merged and written directly to a log file** on disk:
  ```
  ~/.hangar/logs/<component_id>/run-<run_id>.log
  ```
  This means logs survive Hangar restarts.

### Component Lifecycle

```
[Stopped] → click Start → [Starting] → health check passes → [Running]
                                     → grace period expires  → [Unhealthy]
                                     → process exits         → [Crashed]
[Running] → click Stop  → [Stopping] → process killed        → [Stopped]
[Crashed] → autorestart on → retries with backoff (1s → 2s → 4s → 8s → 16s)
                          → max restarts hit → [Restart Loop] event raised
```

### Ordered vs Parallel Start

When you click **"Start all"** on a project:
- **Ordered mode** (default): Hangar starts components tier by tier —
  - Tier 1: Databases first (must be healthy before next tier)
  - Tier 2: Backends and workers
  - Tier 3: Frontends last
- **Parallel mode**: all components start at once.

---

## Starting, Stopping, and Restarting

| Action | How |
|---|---|
| Start a single component | Click the **toggle switch** next to a component in the project card |
| Stop a single component | Click the toggle switch again (slide it off) |
| Restart a single component | Click the **Restart** button next to a component |
| Start all components | Click **Start** in the project card header |
| Stop all components | Click **Stop** in the project card header |
| Start all favourites | Click **Start favourites** on the Overview page |
| Start all projects | Click **Start all** on the Overview page |

### Process Stopping

When you stop a component, Hangar:
1. Runs the **stop command** if one was configured (e.g. `docker compose stop`)
2. Otherwise, terminates the **entire process tree** (all children, grandchildren, etc.)
3. Waits up to 5 seconds for graceful shutdown
4. Force-kills anything remaining (`SIGKILL` on POSIX, `taskkill /T /F` on Windows)
5. Verifies the port is free before marking the component as stopped

---

## Logs

- Navigate to the **Logs** tab in the sidebar.
- Select a component from the dropdown.
- Logs stream live as the process writes to its log file (200ms polling).
- Use **Follow** to auto-scroll to the latest output.
- Use **Copy** or **Download** to export logs.
- Use **Clear** to remove the log file for the current run.

Logs are coloured by ANSI escape codes that the process itself emits (e.g. Next.js, uvicorn, Django, etc. all colour their own output).

---

## Activity & Notifications

- The **Activity** tab shows a timestamped timeline of all system events.
- Events include: started, stopped, restarted, crashed, unhealthy, recovered, port conflict, restart loop, high CPU, high memory.
- Each crash event shows the last 20 log lines directly in the timeline.
- **Toast notifications** appear in the bottom-right for errors and warnings.
- Click the **bell icon** in the top-right to see the latest 8 events.

---

## Settings

Open **Settings** (gear icon in the sidebar) to configure:

| Setting | Default | Description |
|---|---|---|
| Theme | System | Light / Dark / System |
| On exit | Leave running | Whether to stop child processes when Hangar closes |
| Health interval | 5s | How often to probe each component |
| Startup grace | 30s | How long to wait for a health check before marking unhealthy |
| Log retention | 10 runs / 500 MB | How many past run log files to keep |
| CPU alert threshold | 90% | Event raised when a component exceeds this CPU% |
| Memory alert threshold | 1024 MB | Event raised when a component exceeds this RSS |
| Autorestart default | true | Whether new components autorestart on crash by default |

---

## Architecture Overview

### Backend (`backend/hangar/`)

| Module | Role |
|---|---|
| `main.py` | FastAPI app, mounts all routers, serves static files |
| `config.py` | Paths (`HANGAR_HOME`, `LOGS_DIR`), port, name constants |
| `security.py` | Host / Origin / X-Hangar-Client middleware — blocks DNS rebinding |
| `db.py` | SQLAlchemy async engine, session factory, table creation |
| `models.py` | SQLAlchemy ORM models (Application, Component, Run, Event, Metric, Settings) |
| `schemas.py` | Pydantic request/response schemas |
| `core/supervisor.py` | Spawns and tracks child processes, handles adopt-on-restart |
| `core/process.py` | Low-level process spawn with log file redirection |
| `core/orchestrator.py` | Ordered / parallel multi-component start/stop jobs |
| `core/health.py` | TCP, HTTP, process, command, file health checks |
| `core/logtail.py` | Follows active log files, pushes lines over WebSocket |
| `core/metrics.py` | psutil CPU/RSS sampling, 2s live + 1-min DB persist |
| `core/events.py` | Creates and broadcasts events (crash, start, stop, etc.) |
| `core/bus.py` | In-process pub/sub bus connecting core modules to WS clients |
| `core/ports.py` | Lists listening TCP ports, detects conflicts |
| `core/detect.py` | Scans a folder depth-2 and suggests component configs |
| `core/presets.py` | Built-in presets (Node dev, Uvicorn, Django, Docker Compose, etc.) |

### Frontend (`frontend/src/`)

| Path | Role |
|---|---|
| `app/layout.tsx` | Root layout with theme hydration |
| `app/page.tsx` | Entry point — renders `<HangarDashboard>` |
| `components/dashboard/HangarDashboard.tsx` | Main shell: state, WebSocket, tab routing |
| `components/dashboard/ProjectCard.tsx` | Per-project rack unit with component rows and controls |
| `components/dashboard/MasterControl.tsx` | Overview hero panel (Start all, Stop all, machine stats) |
| `components/dashboard/LogViewer.tsx` | Log stream viewer with follow, copy, download |
| `components/dashboard/EventsTimeline.tsx` | Activity timeline with crash log expansion |
| `components/layout/Sidebar.tsx` | Navigation rail (Overview, Applications, Logs, Activity, Settings) |
| `components/layout/Header.tsx` | Page title bar with search, Load samples, Add application |
| `components/layout/CommandPalette.tsx` | Ctrl+K quick-access palette |
| `components/ui/PowerSwitch.tsx` | The toggle+lamp component for each service |
| `lib/api.ts` | All REST API call helpers |
| `lib/ws.ts` | WebSocket client with reconnect backoff |
| `lib/types.ts` | TypeScript interfaces for all domain objects |

---

## Quick Reference: Key URLs

| URL | Description |
|---|---|
| `http://localhost:3002` | Frontend dev server |
| `http://localhost:7777` | Backend API + production frontend |
| `http://localhost:7777/api/overview` | Overview endpoint |
| `http://localhost:7777/api/applications` | List all registered apps |
| `ws://localhost:7777/ws` | WebSocket for live updates |
| `~/.hangar/hangar.db` | SQLite database file |
| `~/.hangar/logs/` | All component log files |

