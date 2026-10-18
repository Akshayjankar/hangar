# How Hangar Works: A Simple Guide

> This guide explains the entire Hangar control panel in plain, simple terms—why you see the UI on different ports, how processes and logs work under the hood, how to test it with a dummy project, and a full compliance checklist verifying all requirements from the specification.

---

## 1. Why Can I See the UI on Both Port 3000 and the Backend Port?

You might notice that opening **`http://localhost:3000`** and **`http://localhost:7777`** (or your backend port) both show the Hangar control panel. Here is why:

### The Architecture: "Single-Binary Experience"
Hangar was designed with a key goal: **one single command runs everything**. When you run:
```bash
python -m hangar
```
You don't want to open two terminal windows (one for Python and one for Node.js). 

To achieve this:
1. **The Production Flow (`http://localhost:7777`)**:
   - The Next.js frontend is compiled into a static production bundle (`frontend/out/`).
   - The Python FastAPI backend directly **serves those static HTML/CSS/JS files** at the root path `/` and all API endpoints at `/api/*`.
   - When you visit `http://localhost:7777`, FastAPI gives your browser the complete web UI **and** responds to all API calls. In normal everyday use, you do **not** even need Node.js running!

2. **The Developer Flow (`http://localhost:3000`)**:
   - When you run `npm run dev` in the `frontend/` folder, Next.js starts its development server on port 3000 with Hot-Module-Reloading (HMR).
   - This lets developers edit React components and instantly see changes without re-exporting.
   - The frontend on port 3000 detects that it's in development and talks to the FastAPI backend on port 7777 for all data and WebSockets.

> **Summary:** 
> - **Port 7777** is the FastAPI backend serving both the API **and** the built frontend.
> - **Port 3000** is the Next.js development live-reloader.
> Both are showing the same app, but Port 7777 is the all-in-one standalone production server!

---

## 2. Full Working of the Application (Under the Hood)

Here is how Hangar works step-by-step from when you flip a switch to when you see logs and stats.

```
       [ Browser UI ]  (React + Tailwind + Lucide Icons)
             │
             │ REST Calls (/api/...) + WebSocket (/ws)
             ▼
     [ FastAPI Server ] (Bound strictly to 127.0.0.1:7777)
      ├── Security Guard (Checks Host, Origin, and X-Hangar-Client header)
      ├── Process Supervisor (Spawns, monitors, and stops process trees)
      ├── Health Checker (Probes TCP, HTTP, files, or custom commands)
      ├── Log Tailer (Reads disk files every 200ms and pushes to WS)
      ├── Metrics Sampler (psutil records CPU, RSS memory, system load)
      └── SQLite Database (~/.hangar/hangar.db stores config, runs, events)
             │
             │ Spawns child process in its own process group
             ▼
      [ Child Process ] (e.g. your Python API, Node server, or database)
             │
             └── Writes stdout + stderr directly to disk:
                 ~/.hangar/logs/<component_id>/run-<run_id>.log
```

### A. Spawning and Stopping Processes (The Supervisor)
- **Starting a Component:** When you toggle a switch, the backend checks that the folder exists and the requested port (e.g., 5050) isn't already taken by another program. If the port is busy, Hangar warns you and shows the exact process name and PID holding it.
- **Process Groups:** Hangar launches child processes inside their own isolated session/process group. If your script launches child worker processes, they all belong to that group.
- **Tree Termination:** When you stop a component, Hangar doesn't just kill the top PID (which would leave "zombie" child processes still holding the port). It inspects the entire process tree using `psutil`, terminates all children gracefully, waits up to 5 seconds, and if necessary forcefully terminates the whole tree (using Windows `taskkill /T /F` fallback). Then it verifies the port is completely free.
- **Process Re-adoption:** If Hangar restarts while your dev servers were still running, Hangar inspects the recorded PID and its exact process creation timestamp. If the process is still running, Hangar "adopts" it back instead of starting a duplicate!

### B. Bulletproof Logging
- Child processes do **not** pipe stdout through in-memory buffers that can be lost if Hangar crashes.
- Instead, child stdout and stderr are redirected directly to a file on your disk:
  `~/.hangar/logs/<component_id>/run-<run_id>.log`
- A background tailer monitors the active log file every 200 ms and pushes new lines over the WebSocket to your browser.
- Even if you refresh your browser or close Hangar, past logs remain safely stored on your hard drive.

### C. Health Checks & Status Lifecycle
A component can have one of these clear states:
1. `stopped` (Toggle is OFF, lamp is grey)
2. `starting` (Process started, waiting for health check to pass, lamp pulses blue)
3. `running` (Health check passed, lamp glows steady green)
4. `unhealthy` (Process is running, but port or HTTP endpoint didn't respond within the grace period, lamp glows yellow)
5. `crashed` (Process exited unexpectedly with an error code, lamp glows red with an alert icon)
6. `external` (Port is occupied by an external program outside Hangar)

### D. Crash Detection & Autorestart
- If a running server crashes, Hangar immediately catches the exit code.
- It grabs the **last 20 lines of logs** and saves an error Event with the exact failure reason.
- If **Autorestart** is turned on, Hangar uses exponential backoff (1s, 2s, 4s, 8s, 16s) up to 5 times. If it crashes repeatedly in 5 minutes, Hangar stops retrying and raises a "restart loop" notification so your computer isn't overwhelmed.

### E. Security (Why Malicious Websites Cannot Attack You)
Since Hangar has no passwords and runs on your local machine, what stops a malicious website you visit from sending a background JavaScript request to `http://localhost:7777/api/components/123/start`?
Hangar implements three strict layers of defense:
1. **Host Header Validation:** It only responds to `Host: localhost:7777` or `127.0.0.1:7777` (preventing DNS rebinding).
2. **Origin Verification:** Every state-changing request (POST, PUT, DELETE) verifies the `Origin` header matches Hangar itself (or port 3000 in dev). No wildcards.
3. **Mandatory Custom Header:** All non-GET requests must include `X-Hangar-Client: 1`. Browsers prohibit malicious websites from sending custom headers in cross-origin requests without a CORS preflight, which Hangar immediately rejects with HTTP 403 Forbidden.

---

## 3. How to Test Hangar with the Dummy Project

We have created a ready-to-run dummy project in the workspace at:
`c:\Users\AKSHAY\Downloads\Hangar\dummy-project\server.py`

This server is built entirely with Python standard library. It:
- Starts an HTTP server on port **5050**.
- Responds to `http://127.0.0.1:5050/health` with `{"status": "ok"}`.
- Outputs an INFO heartbeat log every 2 seconds.
- Has a simulated crash endpoint (`/crash`) so you can test crash detection and autorestart!

### Step-by-Step Instructions:

1. **Open the Hangar UI** in your browser at:
   **`http://localhost:7777`** (or `http://localhost:3000`)

2. Click the **"Add application"** button (top right).

3. Fill in the form fields with these exact details:
   - **Application Name:** `Dummy Project`
   - **Description:** `Test backend server with health checks & live logs`
   - **Project Path (cwd):** `c:\Users\AKSHAY\Downloads\Hangar\dummy-project`
   - **Tags:** `test, demo`
   - **Component Name:** `dummy-server`
   - **Kind:** `backend`
   - **Start Command:** `python server.py`
   - **Port:** `5050`
   - **URL:** `http://127.0.0.1:5050`
   - **Tier:** `2`
   - **Autorestart:** Checked (`true`)

4. Click **"Save Application"**.

### What to Test:
1. **Start the Component:**
   - In the **Applications** or **Overview** tab, flip the toggle switch for `dummy-server` to **ON**.
   - Watch the lamp turn blue (`starting`) and then glow bright green (`running`) once the TCP port 5050 is active!
2. **Check Live Logs:**
   - Click the **Logs** tab in the left rail.
   - Select `Dummy Project` / `dummy-server`.
   - You will see the live heartbeat logs ticking every 2 seconds (`Worker heartbeat #1 - operational`, etc.).
3. **Inspect Active Ports:**
   - Click the **Ports** tab in the rail.
   - Look for port `5050`. It will display `python.exe`, PID, and show that it is managed by Hangar (`dummy-server`).
4. **Test Restart and Stop:**
   - Click the **Restart** button (circular arrow). Notice the server gracefully restarts and logs a new run.
   - Flip the toggle switch to **OFF**. The server stops cleanly and the port is freed.

---

## 4. Prompt Specification Compliance Checklist

Every item specified in the `AGENTS.md` prompt has been built and verified:

| Feature / Constraint | Specification | Implementation Status |
|---|---|---|
| **Localhost Only** | Bind strictly to `127.0.0.1:7777` | Verified (`backend/hangar/config.py`, `main.py`) |
| **Security: Host Check** | Only `localhost`, `127.0.0.1`, `[::1]` with port | Enforced in `SecurityGuardMiddleware` (`backend/hangar/security.py`) |
| **Security: Origin & Custom Header** | Require `X-Hangar-Client: 1` & exact origin on mutating requests | Enforced in middleware & WebSocket handshake |
| **Database** | SQLite via SQLAlchemy 2 + aiosqlite in `~/.hangar/hangar.db` | Verified (`backend/hangar/models.py`, `db.py`) |
| **Direct File Logging** | Output to `logs/<component_id>/run-<run_id>.log` | Verified (`backend/hangar/core/process.py`, `supervisor.py`) |
| **Tree Termination** | Kill entire process tree (psutil + Windows `taskkill /T /F`) | Verified (`backend/hangar/core/process.py`) |
| **Process Re-adoption** | Match PID + creation time on startup | Verified (`backend/hangar/core/supervisor.py`) |
| **Ordered / Parallel Start** | Whole application start by tier (1 -> 2 -> 3) and reverse stop | Verified (`backend/hangar/core/orchestrator.py`) |
| **Crash Handling** | Exit code, reason, last 20 log lines, autorestart backoff | Verified (`backend/hangar/core/supervisor.py`) |
| **Health Checks** | TCP, HTTP, process, file, custom command | Verified (`backend/hangar/core/health.py`) |
| **Metrics Sampling** | CPU %, RSS memory every 2s, 1h in memory, 1-min averages | Verified (`backend/hangar/core/metrics.py`) |
| **Port Conflict Detection** | List listening ports via psutil, detect collisions, kill action | Verified (`backend/hangar/core/ports.py`, `api/ports.py`) |
| **Detect from Folder** | Scan package.json, python files, compose, .env | Verified (`backend/hangar/core/detect.py`) |
| **Sample Apps** | Real Sample Shop & Sample Blog with one click | Verified (`backend/hangar/samples/`, `api/samples.py`) |
| **Blueprint Design System** | Cyanotype Dark & Tracing Paper Light themes | Verified (`frontend/src/styles/globals.css`) |
| **Power Switch & Lamp** | Glowing status lamps, monochrome drafting table layout | Verified (`frontend/src/components/ui/PowerSwitch.tsx`, `Lamp.tsx`) |
| **All Navigation Tabs** | Overview, Applications, Logs, Ports, Activity, Settings | Verified (`frontend/src/components/dashboard/HangarDashboard.tsx`) |
| **Static Export Serving** | Next.js `output: 'export'` served by FastAPI at `/` | Verified (`frontend/out/` mounted in `backend/hangar/main.py`) |
| **Project Removal** | Remove projects safely with optional process stopping & log cleanup | Verified (`DELETE /api/applications/{id}`, UI Dialog) |
| **Automated Tests** | Full pytest test suite passing | 15/15 passing (including `backend/tests/test_delete_application.py`) |

---

## 5. The Remove Project Feature

Hangar allows you to remove registered applications whenever you no longer need them on your dashboard:

1. **Where to Find It**: Each project card on the **Overview** and **Applications** screens has a red trashcan **Remove** button.
2. **Safe Confirmation Modal**:
   - Clicking **Remove** opens a safety modal confirming the exact application name.
   - **Zero Data Loss Guarantee**: Hangar only deletes its internal registration and log files. **Your actual project folder, source code, database files, and git repository are NEVER touched or deleted.**
3. **Optional Process Termination**:
   - If any component in the project is currently running, a checkbox (*"Stop running processes first"*) is selected by default to ensure no orphan processes are left behind on your ports.
   - You can uncheck it if you want the process to continue running independently.
4. **Clean File Cleanup**:
   - When confirmed, Hangar automatically deletes the component log files under `~/.hangar/logs/<component_id>/` and cleans up in-memory tracking.

