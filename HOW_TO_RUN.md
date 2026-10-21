# Hangar — How to Run (Simple Guide)

Hangar is a **control panel for your local projects**.

You open it in the browser, add your projects (frontend, backend, database), and then you can:

- start / stop / restart them
- see if they are healthy
- read live logs
- get alerts when something crashes

It runs only on **your computer** (`localhost`). It is not meant for the internet.

---

## What you need first

| Tool | Version | Why |
|---|---|---|
| Python | 3.11 or newer | Runs the Hangar backend |
| Node.js | 18 or newer | Runs the Hangar UI in dev mode |
| pip | any | Installs Python packages |
| npm | 9 or newer | Installs frontend packages |

---

## Quick idea: what Hangar does

Think of Hangar like a **dashboard for your local apps**.

1. You register a project (for example: Shop).
2. You add its parts (frontend, API, database).
3. Hangar starts those parts for you with the commands you give.
4. Hangar watches them, shows logs, and tells you if something fails.

Important: Hangar does **not** change your project source code. It only stores Hangar’s own data and logs.

---

## How to run Hangar

### Step 1 — Get the project

```bash
git clone https://github.com/Akshayjankar/hangar.git
cd hangar
```

Or unzip the project folder and open a terminal inside it.

---

### Step 2 — Create a Python virtual environment

This keeps Hangar’s packages separate from your system Python.

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### Step 3 — Install backend packages

```bash
pip install -r backend/requirements.lock
```

---

### Step 4 — Install frontend packages

```bash
cd frontend
npm install
cd ..
```

---

### Step 5 — Start Hangar (easiest way)

Use the ready-made script. It starts both backend and UI.

**Windows:**
```powershell
.\scripts\dev.ps1
```

**macOS / Linux:**
```bash
bash scripts/dev.sh
```

Then open:

- UI: **http://localhost:3002**
- API: **http://127.0.0.1:7777**

> Note: Hangar UI uses port **3002** so it does not clash with other apps on port 3000.

---

### Optional: start backend and UI in two terminals

**Terminal 1 — Backend**

```bash
# macOS / Linux
PYTHONPATH=./backend HANGAR_DEV_ORIGIN=http://localhost:3002 \
  uvicorn hangar.main:app --reload --host 127.0.0.1 --port 7777
```

```powershell
# Windows
$env:PYTHONPATH = "C:\path\to\Hangar\backend"
$env:HANGAR_DEV_ORIGIN = "http://localhost:3002"
python -m uvicorn hangar.main:app --reload --host 127.0.0.1 --port 7777
```

**Terminal 2 — Frontend**

```bash
# macOS / Linux
cd frontend
NEXT_PUBLIC_API_URL=http://127.0.0.1:7777 \
  NEXT_PUBLIC_WS_URL=ws://127.0.0.1:7777/ws \
  npm run dev
```

```powershell
# Windows
cd frontend
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:7777"
$env:NEXT_PUBLIC_WS_URL  = "ws://127.0.0.1:7777/ws"
npm run dev
```

Open **http://localhost:3002**.

---

## Production-style start (API only on 7777)

The backend serves **API only**. The UI always runs separately on port **3002**.

**Windows:**
```powershell
.\scripts\start.ps1
# in another terminal:
cd frontend
npm run start
```

**macOS / Linux:**
```bash
bash scripts/start.sh
# in another terminal:
cd frontend && npm run start
```

Or:

```bash
python -m hangar
```

Then open the UI at **http://localhost:3002** (API stays at **http://localhost:7777**).

---

## Try it with sample apps

After Hangar is running, click **Load samples** in the UI.

This creates two demo projects:

- **Sample Shop** — web `:4101`, API `:4102`, fake DB `:4103`
- **Sample Blog** — web `:4111`, API `:4112`, sqlite DB check

These are great for learning how start/stop, logs, and crash events look.

---

## Add your own project

1. Click **Add application**.
2. Enter a name and your project folder path.
3. The form opens with three component slots ready: **Database**, **Backend**, and **Frontend**.
4. Fill each one (or remove what you do not need; use the buttons to add more):
   - **Database** — e.g. `docker compose up -d db` (tier 1)
   - **Backend** — e.g. `uvicorn main:app --reload --port 8000` (tier 2)
   - **Frontend** — e.g. `npm run dev` (tier 3)
5. For each component, set name, start command, optional working directory, port, and health check.
6. Choose **Start mode**: Ordered (db → backend → frontend) or Parallel.
7. Click **Save and register**.

Your project now shows up on the dashboard as **Stopped**. Use **Start all** to run components in order, or toggle one service at a time.

---

## Where Hangar runs your commands (and how)

After you save an application, Hangar does **not** run anything yet. It only stores your settings.

When you click **Start** (or flip a component switch), Hangar runs the **start command you typed**, on **your computer**, like this:

### 1. Where it runs

| Setting you filled | What Hangar does with it |
|---|---|
| **Working directory (cwd)** | Hangar `cd`s into this folder first, then runs the command there |
| **Start command** | Exact shell command Hangar runs (example: `npm run dev`) |
| **Port** (optional) | Hangar also sets env var `PORT` to that value |
| **Env** (optional) | Extra environment variables merged on top of your normal OS env |

So if your backend cwd is `/Users/you/shop/api` and start command is `uvicorn main:app --port 8000`, Hangar effectively does the same idea as:

```bash
cd /Users/you/shop/api
uvicorn main:app --port 8000
```

Your project source code stays in that folder. Hangar does not copy or rewrite it.

### 2. How it starts the process

1. Checks the working folder exists and the start command is not empty.
2. If a port is set, checks that port is free. If something else owns it, start fails with a clear “port in use” message.
3. Opens a new log file for this run under `~/.hangar/logs/<component_id>/run-<run_id>.log`.
4. Starts the command in the **background** through the system shell (no popup terminal window):
   - macOS / Linux: `/bin/sh -c "<your start command>"`
   - Windows: `cmd.exe /s /c "<your start command>"`  
     (`cmd.exe` is only the runner Hangar uses behind the scenes — it does **not** open a Command Prompt window on your desktop)
5. Puts the process in its **own process group**, so Hangar can stop the whole tree later (parent + children).
6. Sends **stdout + stderr** into that log file (merged). You read this in Hangar **Logs**, not in a separate terminal.
7. Watches health (TCP / HTTP / process / file, based on what you configured).
8. When health passes → status becomes **Running**. If not in time → **Unhealthy**. If the process exits → **Crashed**.

Hangar also injects:

- `PYTHONUNBUFFERED=1` (so Python logs show up quickly)
- `PORT=<your port>` when a port is configured

### 3. How it stops the process

When you click **Stop**:

1. If you set a **stop command** (example: `docker compose stop db`), Hangar runs that first.
2. If not, Hangar asks the process tree to terminate, waits a few seconds, then force-kills anything left.
3. It checks the port is free, then marks the component **Stopped**.

### 4. What Hangar stores vs what your app uses

| Location | Who owns it | Purpose |
|---|---|---|
| Your project folder | You | Real app code and configs |
| `~/.hangar/hangar.db` | Hangar | Saved apps, commands, runs, events, settings |
| `~/.hangar/logs/...` | Hangar | Copied process output for live + past logs |

Simple rule: **commands run in your project folder; Hangar only keeps metadata and logs in `~/.hangar/`.**

---

## Start, stop, restart — simple controls

| What you want | What to click |
|---|---|
| Start one service | Toggle switch on that row |
| Stop one service | Toggle switch again |
| Restart one service | Restart button |
| Start whole project | Start all on the project card |
| Stop whole project | Stop all on the project card |

### Start order (when using Start all)

By default Hangar starts in a safe order:

1. Database first
2. Backend / workers next
3. Frontend last

It waits for each step to become healthy before moving on.

---

## What the status lights mean

| Status | Meaning |
|---|---|
| Stopped | Not running |
| Starting | Command launched, waiting to become healthy |
| Running | Healthy and up |
| Stopping | Shutting down |
| Unhealthy | Process is up, but health check failed |
| Crashed | Process exited unexpectedly |
| Failed | Could not start (bad command, busy port, etc.) |

---

## Logs

Open the **Logs** page to:

- watch live output
- search lines
- follow latest output
- copy / download logs
- open older runs

Logs are saved per run, so they remain after Hangar restarts.

---

## Activity and alerts

The **Activity** page is Hangar’s event history.

You will see things like:

- started / stopped / restarted
- crash
- unhealthy
- port conflict
- restart loop
- high CPU / high memory

Crash events also show the last log lines, so you can see what went wrong quickly.

Toasts appear for warnings and errors. The bell icon shows recent alerts.

---

## Settings you may care about

| Setting | Simple meaning |
|---|---|
| Theme | Light / Dark / System |
| On exit | Keep your apps running when Hangar closes, or stop them |
| Startup grace | How long Hangar waits before saying “unhealthy” |
| Health interval | How often Hangar checks each service |
| Autorestart | Restart a crashed service automatically |
| Log retention | How many old log files to keep |

---

## How the pieces talk to each other

```
Your browser
   │
   ├── REST calls (/api/...) ──► Hangar backend (port 7777)
   └── Live updates (WebSocket) ─► same backend

Hangar backend then:
   - starts/stops your processes
   - checks health
   - reads log files
   - collects CPU/memory
   - saves data in ~/.hangar/
```

In short:

- **Frontend** = the screen you click
- **Backend** = the engine that actually starts and watches processes

---

## Useful URLs

| URL | What it is |
|---|---|
| http://localhost:3002 | Hangar UI |
| http://localhost:7777 | Hangar API only (JSON / `/api` / `/ws`) |
| http://localhost:7777/api/overview | Overview data |
| http://localhost:7777/api/applications | Your registered apps |
| ws://127.0.0.1:7777/ws | Live updates |

---

## Safety notes (important)

- Hangar binds to `127.0.0.1` only.
- Do **not** expose it to a public network.
- Never put secrets into chat, commits, or screenshots.

---

## Common problems

**Port 3002 or 7777 already in use**  
Stop the other app, or change Hangar’s port with env vars (`HANGAR_PORT`, frontend `-p` in `frontend/package.json`).

**Frontend cannot talk to backend**  
Make sure backend is running on `7777` and `HANGAR_DEV_ORIGIN` matches the UI origin (`http://localhost:3002`).

**Start fails with “port in use”**  
Something else already owns that port. Kill that process from the Ports/UI flow, or change the component port.

**Command fails immediately**  
Check working directory and start command. Open Logs for the exact error.

---

## One-line summary

Hangar is your local “mission control” for starting, stopping, watching, and debugging your localhost projects from one simple screen.
