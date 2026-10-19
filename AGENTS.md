# AGENT PROMPT: Hangar, a personal control panel for localhost projects

> Save as `AGENTS.md` / `CLAUDE.md` / `.cursorrules` in an empty repo. Read fully, build phase by phase, stop after each phase and show its acceptance checks. "Hangar" is a working name; keep it in one config constant so it can be renamed.

## 1. GOAL
A single-user dashboard, run on my own machine, where I register my **localhost projects** and, from one screen:
1. **Start, stop and restart** each project's frontend, backend and database (one by one, or the whole project in one click, in the safe order).
2. **See status and resource use** at a glance, with graphs.
3. **Read logs** of everything, live and from past runs, merged or side by side.
4. Get **notifications with reasons** when something crashes, fails to start, hits a port conflict or misbehaves.

**Stack (fixed):** Next.js (TypeScript) frontend, Python FastAPI backend.
**Non-goals:** no login or accounts, no roles, no remote servers or SSH, no cloud, no email alerts, no multi-user, no Kubernetes.

## 2. HARD CONSTRAINTS
- **Localhost only.** The backend binds `127.0.0.1` and refuses to bind elsewhere. One command runs everything: `python -m hangar` serves the built UI and API at `http://localhost:7777` and opens the browser (`--no-browser` to skip).
- **No auth, so guard against drive-by web pages** (any website can try to call a local API):
  - Allow only `Host` values `localhost`, `127.0.0.1`, `[::1]` with the configured port (blocks DNS rebinding).
  - On every non-GET request and every WebSocket handshake, require `Origin` to be the app's own origin (plus `http://localhost:3000` in dev) **and** a custom header `X-Hangar-Client: 1` (forces CORS preflight). No wildcard CORS. Reject with 403.
  - Process commands are only ever created through the UI/API as data I typed. No endpoint runs an arbitrary command that is not a stored component.
  - README states plainly: never expose Hangar to a network.
- **Cross-platform:** Windows, macOS and Linux. Use `pathlib`; never hardcode `/` or `\`; pick the shell per platform (cmd.exe on Windows, `/bin/sh` on POSIX) with a Settings override.
- **Minimal dependencies**, each justified in `docs/ARCHITECTURE.md`. Pin exact versions in lockfiles (use the current stable versions at build time). Works fully offline after install: no CDN, no telemetry, fonts bundled via npm packages.
- **Data lives in `~/.hangar/`** (override `HANGAR_HOME`): `hangar.db` (SQLite) and `logs/`.

## 3. ARCHITECTURE
```
Browser  ── REST /api + one WebSocket /ws ──►  FastAPI (127.0.0.1:7777)
 Next.js static export served by FastAPI         ├─ Supervisor: spawn, track, stop process trees
 (dev: Next on :3000, proxy /api)                ├─ Health checker, metrics sampler (psutil)
                                                 ├─ Log tailer (files on disk) ─► WebSocket bus
                                                 ├─ Event engine ─► notifications
                                                 └─ SQLite (config, runs, events, 1-min metrics)
Child processes (my projects) write stdout+stderr straight to per-run log files.
```
- **Child output goes directly to a file** (`logs/<component_id>/run-<run_id>.log`, stderr merged into stdout), so logs survive Hangar restarts. The tailer follows the active file (200 ms polling) and pushes new lines over the WebSocket.
- Children start in their own process group/session. Stopping kills the **whole tree** (psutil: terminate, wait 5 s, kill; on Windows also fall back to `taskkill /T /F`) and verifies the port is free.
- On startup Hangar **re-adopts** still-running children (match pid + create_time from the last run). Setting `on_exit`: `leave_running` (default) or `stop_all`.
- Production: `next build` with `output: 'export'`, served as static files by FastAPI. Dev: `scripts/dev` runs `uvicorn --reload` on 7777 and `next dev` on 3000 with `/api` rewrites; the WebSocket connects directly to `ws://127.0.0.1:7777/ws` (`NEXT_PUBLIC_WS_URL`).

## 4. DOMAIN MODEL (SQLite via SQLAlchemy 2 + aiosqlite; create tables on start, keep a schema_version table)
| Table | Fields |
|---|---|
| `applications` | id, name, description, icon (key from a fixed icon set), path (project folder), tags JSON, favorite, sort, start_mode (`ordered`/`parallel`), created_at |
| `components` | id, application_id, kind (`frontend`/`backend`/`database`/`worker`), name, cwd, start_cmd, stop_cmd nullable, env JSON, port nullable, url nullable, health JSON `{type: tcp/http/process/command/file, target, interval_s, timeout_s, startup_grace_s}`, tier (default database 1, backend 2, worker 2, frontend 3), autorestart bool, max_restarts, start_on_launch bool |
| `runs` | id, component_id, pid, create_time, started_at, ended_at, exit_code, stop_reason (`user`/`crash`/`restart`/`system`), log_path |
| `events` | id, ts, level (`info`/`warn`/`error`), type, application_id, component_id, title, reason, detail JSON (e.g. last 20 log lines), read |
| `metrics_1m` | ts, component_id, cpu_pct, rss_mb |
| `settings` | key, value |

Component status (computed, pushed live): `stopped`, `starting`, `running`, `stopping`, `crashed`, `failed`, `unhealthy`, `external` (port is busy and healthy but not started by Hangar). **Application status** is rolled up: any crashed/failed -> `problem`; else any unhealthy -> `degraded`; some running some stopped -> `partial`; all running -> `running`; all stopped -> `stopped`.

## 5. BACKEND SPEC
**Start:** validate `cwd` exists and `start_cmd` is non-empty; if `port` is set and busy, fail with an event naming the process holding it (pid, name) and offer "Kill it and start" in the UI. Inject `PORT` and `PYTHONUNBUFFERED=1`, merge env with the OS env. `starting` becomes `running` when the health check passes within `startup_grace_s` (default 30), else `unhealthy` with a reason.
**Stop:** run `stop_cmd` if set (Docker presets use it), else terminate the tree. **Restart** = stop then start.
**Whole application (ordered):** start by tier ascending (database, backend, frontend), each tier waits for health before the next; stop in reverse order. `parallel` mode starts all at once. One job per request with per-step progress pushed live; on a failed step stop the sequence, mark the rest skipped, raise an event with the reason; the UI offers "Retry from failed step". An application-level lock blocks concurrent actions.
**Crash handling:** process exits non-zero while it should run -> `crashed`, event with exit code, reason and the last 20 log lines. If `autorestart`, retry with backoff 1, 2, 4, 8, 16 s up to `max_restarts` per 5 minutes, then stop trying and raise "restart loop" event.
**Health checks:** TCP connect (default when a port is set), HTTP GET (2xx/3xx), process alive, custom command (exit 0), file exists (for SQLite). Interval default 5 s.
**Metrics:** every 2 s sample CPU %, RSS and thread count for each tracked process tree, plus machine CPU and memory; keep 1 h in memory, persist 1-minute averages for 7 days.
**Events** (notifications are events with level warn or error): `crash`, `start_failed`, `unhealthy`, `recovered`, `port_conflict`, `high_cpu`, `high_memory` (thresholds in Settings), `restart_loop`, plus info events `started`, `stopped`, `restarted`. Push live over WS.
**Ports:** list listening TCP ports via `psutil.net_connections` with pid, process name, command line and whether Hangar manages it; handle AccessDenied gracefully. Flag **conflicts** (a stopped component's declared port is held by something else, or two components declare the same port). Kill action requires the pid in the request and confirms the process still owns the port.
**Detect from folder** (`POST /api/detect {path}`): scan up to depth 2 and return suggested components, never auto-save:
- `package.json`: scripts `dev`/`start`; Next/Vite/CRA -> frontend (ports 3000/5173/3000); Express/Nest/Fastify -> backend.
- Python: FastAPI (`uvicorn <module>:app --reload --port 8000`), Django (`manage.py runserver`), Flask; use `.venv`/`venv` interpreter if present.
- `docker-compose.yml`: each service; postgres/mysql/mariadb/mongo/redis images -> database with `docker compose up -d <svc>` / `docker compose stop <svc>`.
- `.env`: PORT and DATABASE_URL ports. Common folder names (`frontend`, `client`, `web`, `backend`, `server`, `api`) hint at kind.
**Presets** in the Add flow: Node dev server, Python/Uvicorn, Django, Flask, Docker container, Docker Compose service, PostgreSQL / MySQL / MongoDB / Redis via a local service command, SQLite file, custom command.
**Logs API:** history = last N lines by reverse-reading the file; search (substring or regex); list previous runs per component; download; clear. Keep the last 10 runs per component and cap total log size (Settings, default 500 MB). Insert a system line when a run ends (`exited with code 1`).

**REST (`/api`)**
```
GET /overview                                 GET/POST /applications   GET/PATCH/DELETE /applications/{id}
POST /applications/{id}/components            PATCH/DELETE /components/{id}
POST /components/{id}/{start|stop|restart}    POST /applications/{id}/{start|stop|restart}   POST /actions/{start-all|stop-all}
GET /jobs/{id}                                GET /components/{id}/runs
GET /components/{id}/logs?lines=&q=&regex=&run=   GET /logs/merged?components=&lines=&q=   DELETE /components/{id}/logs
GET /ports       POST /ports/{port}/kill      GET /events?level=&type=&app=&unread=   POST /events/{id}/read   POST /events/read-all
GET /metrics?component=&range=1h|6h|24h|7d    POST /detect                POST /applications/{id}/open-folder   POST /applications/{id}/open-editor
POST /samples/load   DELETE /samples          GET/PUT /settings           GET /export   POST /import
```
**WebSocket `/ws`:** client sends `{sub: "status"|"events"|"metrics"|"logs:<componentId>"}` / `{unsub}`; server pushes `status`, `job.step`, `event`, `metrics`, `log` (batched, max 50 lines per 100 ms per subscription). Auto-reconnect with backoff on the client; REST polling every 5 s as fallback.

## 6. DESIGN SYSTEM: "Blueprint"
**Concept.** A drafting-table look for a machine-room task: the interface is quiet, drawn in line work, and **the only things that carry colour are the status lights**. The memorable element is the **toggle switch plus glowing status lamp** on every component. Everything else is monochrome and disciplined. Do not use the NSE palette, purple gradients, or any of these common defaults: cream background with serif and terracotta, near-black with one acid-green accent, newspaper hairline layouts, identical rounded cards with the same soft shadow, gradient washes, ALL-CAPS labels or eyebrows above headings, numbered markers (01, 02) where nothing is a sequence, middle-dot meta strings, or arrows appended to button text.

**Themes** (toggle in the header: Light / Dark / System, stored locally, applied before first paint to avoid flash). Define as CSS variables in `globals.css`, map in Tailwind, never hardcode hex in components.

| Token | Dark "Cyanotype" | Light "Tracing paper" |
|---|---|---|
| `--bg` | `#0A2036` | `#E8EDF0` |
| `--surface` | `#0F2D49` | `#F6F8F9` |
| `--surface-2` | `#153A5C` | `#DCE4E9` |
| `--line` | `#27537A` | `#B7C5CF` |
| `--text` | `#E8F1F8` | `#0C2237` |
| `--muted` | `#8DAFC8` | `#51677A` |
| `--primary` (buttons, focus) | `#E8F1F8` with text `#0A2036` | `#0C2237` with text `#F6F8F9` |
| `--run` | `#34D8A5` | `#0B8E68` (text `#07745A`) |
| `--start` | `#63B8FF` | `#1A6DB5` (text `#14579A`) |
| `--warn` | `#F4B94E` | `#9A6107` (text `#7A4B00`) |
| `--err` | `#FF6B7C` | `#C22E42` (text `#A8222F`) |
| `--off` | `#6F8DA6` | `#75899A` |

Primary actions are chalk-on-blueprint (dark) and ink-on-paper (light): no coloured accent button. Chart categorical series and per-application log chips use a stable six-hue set: sky, mint, sand, rose, lilac `#A7A3FF` (dark) / `#5B52D6` (light), steel. Page background carries a very faint 24 px blueprint grid (about 4 % opacity) fixed behind content, in both themes. Light-mode status text uses the darker "text" values to keep AA contrast. Dark mode lamps glow (soft `box-shadow` in the status colour); light mode lamps are flat with a ring.

**Type.** One family: **Bricolage Grotesque** (variable; use the optical-size and width axes: condensed and heavy for page titles, normal for UI), via `@fontsource-variable/bricolage-grotesque`. **JetBrains Mono** (`@fontsource/jetbrains-mono`) only for logs, commands, paths and ports in code boxes. Tabular numerals for all numbers. Scale 12 / 13 / 14 / 16 / 20 / 28 / 44. Sentence case everywhere. Page titles are large and set as a design element (heavy, tight). No tracked-out caps.

**Shape and depth.** Panels have 1 px `--line` borders and **no drop shadows**; hierarchy comes from surface steps. Radii by role: 6 px rack units and panels, 999 px toggles and lamps, 4 px inputs. Overview panels are deliberately different sizes (not a grid of identical cards). Dividers appear only where they separate real groups (component rows inside a rack unit).

**Icons.** `lucide-react` (bundled, stroke 1.75) on every nav item, status, button, tab and empty state; text-only controls are not acceptable. Icon-only buttons get a tooltip and `aria-label`. Map: Overview `LayoutDashboard`, Applications `Boxes`, Logs `ScrollText`, Ports `Cable`, Activity `Activity`, Settings `Settings`, Frontend `Globe`, Backend `Server`, Database `Database`, Worker `Cog`, Start `Play`, Stop `Square`, Restart `RotateCw`, Restart all `RefreshCcw`, Open in browser `ExternalLink`, Open folder `FolderOpen`, Open in editor `Code`, Favourite `Star`, Notifications `Bell`, Theme `Sun`/`Moon`, Search `Search`, Detect `ScanSearch`, Add `Plus`, Kill `Skull`, Crash `OctagonAlert`, Warning `TriangleAlert`, Info `Info`.

**The toggle and lamp** (`<PowerSwitch>`, `role="switch"`, `aria-checked`, `aria-label="Backend shop-api"`, 44 px touch height): thumb slides 180 ms with a slight spring. States: off (thumb left, lamp `--off`), starting (thumb right, lamp `--start` pulsing, spinner), on (lamp `--run`), crashed (thumb left, lamp `--err` with `OctagonAlert`), unhealthy (thumb right, lamp `--warn`). Status is always lamp + icon + word ("Running"), never colour alone. Clicking while starting/stopping is ignored with a tooltip.

**Motion.** One orchestrated moment: on first load of a session the lamps light one after another across the Overview and Applications (about 600 ms total). Otherwise motion only answers an action (toggle, expand, toast, drawer 150 ms). Honour `prefers-reduced-motion`.

**Writing.** Plain verbs, active voice, the same verb in the button, the toast and the activity entry ("Restart" -> "Restarting shop-api" -> "shop-api restarted"). Errors say what happened and how to fix it ("Port 4102 is in use by node (pid 8841). Kill it and start, or change the port."). Empty states invite an action.

## 7. SCREENS
**Shell.** Left **dock**: slim vertical rail with icon above label for Overview, Applications, Logs, Ports, Activity, Settings (active item gets a lamp-style marker and a filled surface). A small geometric arch mark (hangar roof) at the top; no logo image needed. Top bar: large page title at left; right-aligned: search/command palette trigger (`Ctrl+K`: jump to an app, start/stop/restart anything, switch theme), theme switch, notification bell with unread badge and dropdown (latest 8 with reasons). A thin connection indicator ("Live" / "Reconnecting") sits in the dock footer.

**Overview**
- **Master panel** (top, wide): total running over total components; **Start favourites**, **Start all**, **Stop all** buttons; machine CPU and memory as two small live gauges.
- **Graphs** (ECharts, themed to the tokens; every chart has a time-range switch 1h / 6h / 24h / 7d, tooltip, empty and loading state, and a text summary for screen readers):
  1. CPU by application, stacked area.
  2. Memory by application, horizontal bars (top 8).
  3. Component status, donut with the total in the centre.
  4. Uptime ribbons, one strip per application for 24 h, coloured by status (hand-built SVG).
  5. Events heatmap (day by hour, 7 days).
  6. Machine CPU and memory, two sparklines.
- **Favourites strip:** compact rack units with their switches.
- **Recent activity:** last 8 events with icon, reason and time.
- Charts show "Collecting data" until at least two points exist.

**Applications**
- Toolbar: search, filter chips (All, Running, Stopped, Problems), tag filter, view switch (Rack / Table), **Detect from folder** and **Add application**.
- **Rack unit** per application (wireframe):
```
┌───────────────────────────────────────────────────────────┐
│ [icon] Sample Shop  [tags]            Star Folder Code  ⋮ │
│ ───────────────────────────────────────────────────────── │
│ (lamp) Frontend  shop-web  :4101  cpu sparkline  2m  [switch] Restart Open │
│ (lamp) Backend   shop-api  :4102  cpu sparkline  2m  [switch] Restart Open │
│ (lamp) Database  shop-db   :4103  cpu sparkline  2m  [switch] Restart      │
│ ───────────────────────────────────────────────────────── │
│ [Start all / Stop all]  Restart all        Last: crashed 3 min ago         │
└───────────────────────────────────────────────────────────┘
```
  (Build with icons and real components; the wireframe uses words as placeholders.) Clicking the port chip or **Open** opens `url` in a new tab. Clicking the application name opens a **detail drawer** (full screen on phones) with tabs: Components (edit commands, env, ports, health, order, autorestart), Logs (merged for this app), Metrics, Activity. **Start all / Stop all** runs the ordered job with live per-step progress inside the unit and a Cancel and "Retry from failed step" on failure.
- **Add application** is a 3-step sheet: (1) name, folder, icon, tags; (2) components: pick presets or "Detect from folder" results, edit command, port, health; (3) review and "Test start" dry run (validates folder, command, port free) then save.
- Components of the same application may be reordered by tier by drag handle.

**Logs**
- Left selector: tree of applications and components with lamps and checkboxes, "All running" quick pick, run selector (Current or a previous run).
- Layouts: **Merged** (one stream, each line prefixed with a coloured component chip) or **Split** (up to 3 side-by-side panes).
- Toolbar: search with regex toggle, level chips (Error, Warn, Info, Debug) from line heuristics (`ERROR`, `Traceback`, `Exception`, `WARN`, `INFO`), timestamps toggle, wrap, follow (auto-scroll) and pause, clear view, clear file, download, copy.
- Dark panel always uses JetBrains Mono on `--surface`; virtualised for 100k lines; "Jump to latest" button when scrolled up; strip ANSI codes for search but render colours; run-end system lines highlighted. Opening logs from a crash event jumps to that moment.

**Ports**
- Table: port, process (name and pid), command line, owner (application and component, or "external"), state; filters: Dev ports (3000 to 9999), Managed, Conflicts. Conflict banner at the top. Row actions: Open, Kill (confirm dialog showing the process and pid).

**Activity**
- Timeline grouped by day. Each entry: icon, title, **reason**, time, application and component. Crash entries expand to show the last 20 log lines and a link to open logs. Filters: level, type, application, unread only. "Mark all read". Toasts appear for new warn and error events; optional browser notifications (permission requested only when the user turns the setting on).

**Settings**
- Appearance (Light / Dark / System), shell override, health interval and startup grace defaults, autorestart default, log retention (runs per component, total size cap), CPU and memory alert thresholds, notification options (toasts, browser notifications, sound off by default), `on_exit` behaviour, **Sample apps** (load / remove), Export and Import config as JSON, show data folder path, version.

## 8. RESPONSIVE AND ACCESSIBLE
- Mobile-first; verify at 360, 390, 768, 1024, 1280, 1440, 1920 (and landscape phone). **No horizontal page scroll** at any width; only log lines, wide tables inside their own container, and snap rows may scroll sideways.
- Below 768 the dock becomes a bottom tab bar (Overview, Applications, Logs, More); rack units are one column; tables become stacked rows; drawers and dialogs become full-screen bottom sheets; charts go full width at 200 px tall; touch targets at least 44 px; respect safe areas; use `dvh`, `min-w-0`, `clamp()`.
- Keyboard operable everywhere, visible 2 px focus ring, focus trap in dialogs, status never colour-only, AA contrast in both themes, ARIA live region for new notifications.

## 9. SAMPLE APPS (so the UI works on day one, with no real project)
`POST /samples/load` creates two real, runnable applications using only the Python standard library, shipped in `backend/hangar/samples/`:
- **Sample Shop:** `shop-web` (`python -m http.server 4101` on a tiny static folder), `shop-api` (`echo_api.py --port 4102`: JSON endpoint and `/health`, logs a line per second with occasional WARN and ERROR), `shop-db` (`fake_db.py --port 4103`: TCP listener that logs connections).
- **Sample Blog:** `blog-web` (4111), `blog-api` (4112, started with `--crash-after 40` so crash events, autorestart and the restart-loop notification can be seen), `blog-db` (SQLite file check).
Setting `HANGAR_DEMO_HISTORY=1` seeds 24 h of fake metrics and events so charts look full for screenshots; the UI shows a small "Demo history" badge while it is active. Without it, charts fill from live data within a minute.

## 10. FILE TREE (create exactly this, add files only if needed)
```
hangar/
├── AGENTS.md  README.md
├── docs/ (ARCHITECTURE.md  DESIGN.md  SECURITY.md)
├── scripts/ (dev.sh dev.ps1  build.sh build.ps1  start.sh start.ps1)
├── backend/
│   ├── pyproject.toml  requirements.lock
│   ├── hangar/
│   │   ├── __main__.py        # python -m hangar
│   │   ├── main.py  config.py  security.py  db.py  models.py  schemas.py
│   │   ├── api/ (overview.py applications.py components.py actions.py logs.py ports.py
│   │   │         events.py metrics.py detect.py settings.py samples.py ws.py)
│   │   ├── core/ (supervisor.py process.py orchestrator.py health.py logtail.py
│   │   │          metrics.py events.py ports.py detect.py presets.py bus.py)
│   │   └── samples/ (echo_api.py fake_db.py static_site/)
│   └── tests/
└── frontend/
    ├── package.json  package-lock.json  next.config.mjs  tailwind.config.ts  tsconfig.json
    └── src/
        ├── app/ (layout.tsx page.tsx applications/ logs/ ports/ activity/ settings/)
        ├── styles/globals.css            # all tokens, both themes, blueprint grid
        ├── components/
        │   ├── shell/ (Dock, TopBar, ThemeSwitch, CommandPalette, NotificationBell, ConnectionDot)
        │   ├── ui/ (Button, IconButton, PowerSwitch, Lamp, StatusPill, Dialog, Sheet, Tooltip,
        │   │        Tabs, Toast, Skeleton, EmptyState, DataTable)
        │   ├── features/ (RackUnit, ApplicationDrawer, AddApplicationSheet, DetectResults,
        │   │              MasterPanel, LogViewer, LogSelector, PortTable, ActivityTimeline)
        │   └── charts/ (Chart.tsx, theme.ts, CpuStacked, MemoryBars, StatusDonut,
        │                UptimeRibbon, EventsHeatmap, Sparkline, Gauge)
        └── lib/ (api.ts, ws.ts, theme.ts, types.ts, format.ts)
```
**Dependencies.** Backend: `fastapi`, `uvicorn[standard]`, `pydantic` v2, `sqlalchemy` 2, `aiosqlite`, `psutil`, `httpx`, `pytest`. Frontend: `next`, `react`, `typescript`, `tailwindcss`, `lucide-react`, `echarts` (tree-shaken), `@tanstack/react-virtual`, `@radix-ui/react-dialog`, `-tooltip`, `-dropdown-menu`, `-popover`, `@fontsource-variable/bricolage-grotesque`, `@fontsource/jetbrains-mono`. Anything else needs a one-line justification.

**Commands.** Install: `pip install -r backend/requirements.lock` and `npm ci --prefix frontend`. Dev: `scripts/dev`. Build and run: `scripts/build` then `python -m hangar`. Tests: `pytest backend/tests` and `npm run typecheck && npm run build --prefix frontend`.

**Env** (all optional): `HANGAR_HOME` (default `~/.hangar`), `HANGAR_PORT` (7777), `HANGAR_DEV_ORIGIN` (`http://localhost:3000`), `HANGAR_DEMO_HISTORY` (0), `NEXT_PUBLIC_WS_URL` (dev only).

## 11. PHASES (stop after each and show its checks)
1. **Engine:** backend skeleton, security guards, SQLite, supervisor, per-run log files, health checks, WebSocket, sample apps. *Check:* load samples via API, start `shop-api`, see it `running`, kill its tree on stop, a Host/Origin-forged request returns 403.
2. **Shell, theme, Applications:** tokens, both themes, dock, top bar, PowerSwitch and lamps, rack units, ordered Start all / Stop all with progress. *Check:* toggling a switch starts and stops the real sample process; Start all runs database, backend, frontend in order.
3. **Logs:** live tail, merged and split views, search, previous runs. *Check:* lines appear live; a crash shows a system line; logs survive a Hangar restart.
4. **Overview and metrics:** sampler, 1-minute persistence, all six graphs, master panel. *Check:* graphs fill with sample-app data and resize on rotation and window changes.
5. **Ports, Activity, notifications:** port map and conflicts, event engine, bell, toasts, crash detail, autorestart and restart-loop. *Check:* `blog-api` crash produces a crash event with the last log lines and a toast; port conflict shows a clear fix.
6. **Detect, Add flow, Settings, polish:** detect from folder, presets, Add sheet, settings, export/import, empty/error/loading states, responsive pass, README. *Check:* detect a real local project and run it from the UI.

## 12. ACCEPTANCE CRITERIA
- [ ] `python -m hangar` starts on `127.0.0.1:7777`, opens the UI, needs no login, and refuses non-local Host, wrong Origin or missing `X-Hangar-Client` (403).
- [ ] I can add a real localhost project (frontend, backend, database) and start, stop and restart each component, or the whole application in one click in tier order, with live progress and a clear failure path.
- [ ] Stopping always kills the full process tree and frees the port (verified on the sample apps); works on Windows, macOS, Linux (state what was actually tested).
- [ ] Logs are live, searchable, mergeable and split-able, persist per run, and survive restarting Hangar; Hangar re-adopts running children.
- [ ] Overview shows all six graphs with real data, in both themes, with range switch and no layout jump on resize.
- [ ] Crash, failed start, port conflict, unhealthy and restart-loop each create an Activity entry with a readable reason and a toast; unread badge works.
- [ ] Light, Dark and System themes are both fully designed, switch instantly with no flash on load, and meet AA contrast; the look matches section 6 (blueprint, status-only colour, no NSE palette, none of the listed defaults).
- [ ] Every nav item, button, status, tab and empty state has an icon; every toggle is a labelled `role="switch"`; status is never colour alone.
- [ ] No horizontal page scroll from 320 to 3840 px; bottom tab bar and bottom sheets on phones; checked at the seven widths listed.
- [ ] Works fully offline after install; no external requests (check the browser network tab).
- [ ] Backend tests cover supervisor start/stop tree kill, health checks, ordered job and failure path, port detection, detect heuristics and the security guards. Frontend type-checks and builds without errors.
- [ ] Screenshots of Overview, Applications, Logs and Ports in light and dark at phone and desktop widths are saved in `docs/screenshots/`.

## 13. RULES FOR THE AGENT
- Build and review every screen with the sample apps first; never leave a screen that only works with a special project.
- Match section 6 exactly; do not fall back to default component-library styling.
- Ask before adding any dependency not listed; prefer the standard library.
- Keep functions small, typed, tested; no placeholder TODOs in finished phases.
- After each phase: summarise what was built, list new dependencies, give the commands to run and verify, and say what you did not test.
- If a requirement is ambiguous, choose the simplest safe option, state the assumption in one line, and continue.
