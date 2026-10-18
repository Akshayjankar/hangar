"""Script to generate docs/Hangar_How_It_Works.pptx with all 17 required sections."""
from __future__ import annotations
import os
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# Blueprint design system colors
BG_COLOR = RGBColor(10, 32, 54)         # #0A2036
SURFACE_COLOR = RGBColor(15, 45, 73)    # #0F2D49
SURFACE_2 = RGBColor(21, 58, 92)        # #153A5C
LINE_COLOR = RGBColor(39, 83, 122)      # #27537A
TEXT_COLOR = RGBColor(232, 241, 248)    # #E8F1F8
MUTED_COLOR = RGBColor(141, 175, 200)   # #8DAFC8
RUN_COLOR = RGBColor(52, 216, 165)      # #34D8A5 (Green lamp)
START_COLOR = RGBColor(99, 184, 255)    # #63B8FF (Blue)
WARN_COLOR = RGBColor(244, 185, 78)     # #F4B94E (Amber)
ERR_COLOR = RGBColor(255, 107, 124)     # #FF6B7C (Red)

def create_deck(output_path: Path):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def add_base_slide(title_text: str, category_text: str = "HANGAR MACHINE ROOM"):
        slide = prs.slides.add_slide(blank_layout)
        
        # Dark navy background
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_COLOR
        bg.line.fill.background()

        # Header Category
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = MUTED_COLOR

        # Header Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_COLOR

        # Thin divider line
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.733), Inches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = LINE_COLOR
        line.line.fill.background()

        return slide

    def add_card(slide, left, top, width, height, title="", border_color=LINE_COLOR, bg_color=SURFACE_COLOR):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1.5)
        
        if title:
            tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.15), width - Inches(0.4), Inches(0.4))
            p = tb.text_frame.paragraphs[0]
            p.text = title
            p.font.size = Pt(15)
            p.font.bold = True
            p.font.color.rgb = START_COLOR
        return shape

    def add_bullet_points(slide, left, top, width, height, points):
        tb = slide.shapes.add_textbox(left, top, width, height)
        tf = tb.text_frame
        tf.word_wrap = True
        for i, pt in enumerate(points):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = f"•  {pt}"
            p.font.size = Pt(13)
            p.font.color.rgb = TEXT_COLOR
            p.space_after = Pt(10)

    # ==========================================
    # SLIDE 1: Title & Section 1: What Hangar Is
    # ==========================================
    s1 = add_base_slide("What Hangar Is & The Problem It Solves", "Section 1: Introduction")
    add_card(s1, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "The Everyday Developer Problem")
    add_bullet_points(s1, Inches(1.0), Inches(2.4), Inches(5.2), Inches(4.2), [
        "Developers juggle 5 to 10 terminal tabs every day to run local projects.",
        "A typical project requires three pieces: a database, an API backend, and a web frontend.",
        "Starting them in the wrong order breaks things (e.g., backend crashes if DB isn't ready).",
        "Terminals get left running in the background, locking ports like 3000 or 8000.",
        "Logs are scattered across dozens of black command prompt windows.",
        "When an app crashes, finding why requires hunting through buried terminal history."
    ])

    add_card(s1, Inches(6.9), Inches(1.8), Inches(5.6), Inches(5.0), "The Hangar Solution")
    add_bullet_points(s1, Inches(7.1), Inches(2.4), Inches(5.2), Inches(4.2), [
        "Hangar is a single machine-room control panel for your own computer (localhost).",
        "Think of it as an airport control tower for all your software projects.",
        "One-click start, stop, and restart for every service or entire project suites.",
        "Safe ordered boot: databases boot first (Tier 1), then backends (Tier 2), then frontends (Tier 3).",
        "Live status lamps: green for healthy, pulsing blue for starting, red for crashed.",
        "Merged real-time logs, resource gauges, and port conflict cleaning from one browser screen."
    ])
    s1.notes_slide.notes_text_frame.text = (
        "Welcome to the complete guide to Hangar. "
        "As software developers, we spend hours opening terminal windows to run our databases, backend APIs, and web frontends. "
        "If you close the laptop or forget what is running, ports get locked and terminal windows multiply. "
        "Hangar solves this completely. It gives you a clean browser dashboard on your computer to supervise, start, stop, and view logs for all your projects in one place."
    )

    # ==========================================
    # SLIDE 2: Section 2: Architecture Diagram
    # ==========================================
    s2 = add_base_slide("The Big Picture: End-to-End Architecture", "Section 2: High-Level Design")
    
    # 4 horizontal architecture boxes
    add_card(s2, Inches(0.8), Inches(2.0), Inches(2.6), Inches(4.5), "1. Browser Client", RUN_COLOR)
    add_bullet_points(s2, Inches(0.9), Inches(2.6), Inches(2.4), Inches(3.6), [
        "User Interface",
        "Next.js 14 + React",
        "Single-page app",
        "Runs on http://localhost:7777",
        "REST API calls for actions",
        "WebSocket connection for live logs & metrics"
    ])

    add_card(s2, Inches(3.8), Inches(2.0), Inches(2.7), Inches(4.5), "2. FastAPI Backend", START_COLOR)
    add_bullet_points(s2, Inches(3.9), Inches(2.6), Inches(2.5), Inches(3.6), [
        "The Brain & Manager",
        "Python FastAPI on 127.0.0.1:7777",
        "Process Supervisor",
        "Tier Orchestrator",
        "Health Monitor (every 5s)",
        "Log Tailer (every 200ms)"
    ])

    add_card(s2, Inches(6.9), Inches(2.0), Inches(2.6), Inches(4.5), "3. SQLite Database", WARN_COLOR)
    add_bullet_points(s2, Inches(7.0), Inches(2.6), Inches(2.4), Inches(3.6), [
        "The Filing Cabinet",
        "File: ~/.hangar/hangar.db",
        "Stores registered projects",
        "Stores components & runs",
        "Stores system events",
        "1-minute metric summaries"
    ])

    add_card(s2, Inches(9.9), Inches(2.0), Inches(2.6), Inches(4.5), "4. Project Processes", ERR_COLOR)
    add_bullet_points(s2, Inches(10.0), Inches(2.6), Inches(2.4), Inches(3.6), [
        "Your Running Code",
        "Child process trees",
        "Frontend (e.g. :3000)",
        "Backend API (e.g. :8000)",
        "Database (e.g. :5432)",
        "Output piped directly to per-run log files on disk"
    ])
    s2.notes_slide.notes_text_frame.text = (
        "Here is how everything connects together. "
        "At the left, you open your web browser. The Next.js dashboard talks to the FastAPI Python backend on port 7777. "
        "The backend acts as the supervisor or general contractor: it launches and tracks your project processes (like Node or Python), "
        "checks their health, tails their log files, and records configuration in an SQLite database filing cabinet."
    )

    # ==========================================
    # SLIDE 3: Section 3: What Localhost Means
    # ==========================================
    s3 = add_base_slide("What 'Localhost' Means & Networking Safety", "Section 3: Networking & Security")
    add_card(s3, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Understanding Localhost & Ports")
    add_bullet_points(s3, Inches(1.0), Inches(2.4), Inches(5.2), Inches(4.2), [
        "Localhost (127.0.0.1): An internal loopback address that means 'this computer right here'.",
        "Data sent to localhost never travels over Wi-Fi, Ethernet, or the internet.",
        "Port: An apartment number on your computer (e.g. 7777 for Hangar, 3000 for web app).",
        "Analogy: 127.0.0.1 is the apartment building; port 7777 is apartment unit #7777.",
        "When you visit http://localhost:7777, your browser talks directly to Hangar running on your machine."
    ])

    add_card(s3, Inches(6.9), Inches(1.8), Inches(5.6), Inches(5.0), "Zero-Trust Security Guards")
    add_bullet_points(s3, Inches(7.1), Inches(2.4), Inches(5.2), Inches(4.2), [
        "Host Header Guard: Refuses any connection whose Host header isn't localhost or 127.0.0.1 (stops DNS rebinding attacks).",
        "Origin & CORS Guard: All mutating requests (POST, DELETE) must originate from Hangar's own origin.",
        "X-Hangar-Client Header: All API calls require 'X-Hangar-Client: 1', preventing malicious external websites from triggering local commands.",
        "Strict Local Binding: The backend binds exclusively to 127.0.0.1 and refuses external network interfaces.",
        "No Remote Execution: Only commands explicitly typed and saved in components can be executed."
    ])
    s3.notes_slide.notes_text_frame.text = (
        "Because Hangar does not use passwords, it is protected with strict network guards. "
        "It only binds to 127.0.0.1, meaning nobody on your local Wi-Fi network can reach it. "
        "Furthermore, browser security filters check the Host header, Origin header, and a custom client header to ensure that no malicious website you visit can secretly tell Hangar to run or kill commands."
    )

    # ==========================================
    # SLIDE 4: Section 4: Folder & File Map
    # ==========================================
    s4 = add_base_slide("Folder & File Map: What Every Part Does", "Section 4: Codebase Structure")
    add_card(s4, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0), "backend/ (FastAPI)")
    add_bullet_points(s4, Inches(0.9), Inches(2.4), Inches(3.5), Inches(4.2), [
        "hangar/main.py: App factory & lifespan",
        "hangar/config.py: Ports, paths, defaults",
        "hangar/db.py: SQLite DB engine & sessions",
        "hangar/models.py: Database schema tables",
        "hangar/core/supervisor.py: Process engine",
        "hangar/core/orchestrator.py: Ordered jobs",
        "hangar/core/health.py: Health check probes",
        "hangar/core/logtail.py: File tailer engine",
        "hangar/api/: 12 REST & WebSocket routes"
    ])

    add_card(s4, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0), "frontend/ (Next.js 14)")
    add_bullet_points(s4, Inches(4.9), Inches(2.4), Inches(3.5), Inches(4.2), [
        "src/app/page.tsx: App entry point",
        "components/dashboard/HangarDashboard.tsx: The main UI control room",
        "components/ui/: Button, Dialog, PowerSwitch, Lamp, StatusPill",
        "src/lib/api.ts: Typed REST client with security header injection",
        "src/lib/ws.ts: WebSocket manager with auto-reconnection backoff",
        "src/styles/globals.css: Blueprint drafting design tokens & grid"
    ])

    add_card(s4, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0), "~/.hangar/ (Data Storage)")
    add_bullet_points(s4, Inches(8.9), Inches(2.4), Inches(3.5), Inches(4.2), [
        "hangar.db: SQLite database storing projects, components, runs, and settings.",
        "logs/<comp_id>/run-<id>.log: Raw text log files written straight from child stdout/stderr.",
        "Persists across reboots and dashboard restarts.",
        "docs/: Architecture, design, and user documentation.",
        "scripts/: PowerShell and Bash launch scripts for dev and prod."
    ])
    s4.notes_slide.notes_text_frame.text = (
        "The project is cleanly divided into three areas. "
        "The backend folder contains Python code responsible for system processes, health checks, and database management. "
        "The frontend folder contains the Next.js React user interface with our drafting-table Blueprint design system. "
        "Finally, all persistent user data lives in the user's home directory under .hangar."
    )

    # ==========================================
    # SLIDE 5: Section 5: Startup Flow
    # ==========================================
    s5 = add_base_slide("Step-by-Step Flow: What Happens at Startup", "Section 5: Lifecycle")
    steps = [
        ("Step 1: Storage & Directories", "Config checks ~/.hangar; creates logs/ directory and hangar.db SQLite database if they don't exist yet."),
        ("Step 2: Database Table Setup", "SQLAlchemy connects via aiosqlite, creates schema_version, applications, components, runs, events, and metrics tables."),
        ("Step 3: Process Re-adoption", "Supervisor scans the database for active runs; checks if PIDs are still alive with matching start times. If so, adopts them!"),
        ("Step 4: Launch Background Tasks", "Supervisor starts health checker (every 5s) and metrics sampler (every 2s). Log tailers attach to active run log files."),
        ("Step 5: Next.js Static Export Serving", "FastAPI mounts frontend/out/ at the root URL (/) and serves REST API at /api and WebSocket bus at /ws."),
        ("Step 6: Browser Connection", "User opens http://localhost:7777; browser downloads the UI, requests /api/overview, and opens the live WebSocket connection.")
    ]
    for i, (st, desc) in enumerate(steps):
        top_pos = Inches(1.8 + i * 0.85)
        add_card(s5, Inches(0.8), top_pos, Inches(11.733), Inches(0.75), "", RUN_COLOR if i == 5 else LINE_COLOR)
        tb = s5.shapes.add_textbox(Inches(1.0), top_pos + Inches(0.08), Inches(11.3), Inches(0.6))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"{st}:  "
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = START_COLOR if i == 5 else TEXT_COLOR
        run = p1.add_run()
        run.text = desc
        run.font.bold = False
        run.font.size = Pt(12)
        run.font.color.rgb = MUTED_COLOR

    s5.notes_slide.notes_text_frame.text = (
        "When you run 'python -m hangar', these six steps execute in order. "
        "Notice Step 3: if Hangar was closed previously while your project servers were still running, "
        "it is smart enough to re-adopt those running processes without needing to restart them. "
        "Then Step 5 serves the static web UI directly from FastAPI, so no Node runtime is needed in production."
    )

    # ==========================================
    # SLIDE 6: Section 6: Background Tasks
    # ==========================================
    s6 = add_base_slide("What Happens in the Background While Open", "Section 6: Background Monitoring")
    add_card(s6, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Background Engines & Intervals")
    add_bullet_points(s6, Inches(1.0), Inches(2.4), Inches(5.2), Inches(4.2), [
        "Health Checker (Every 5 seconds): Probes each running component (TCP socket connect, HTTP GET 200, process check, or SQLite file).",
        "Metrics Sampler (Every 2 seconds): Samples CPU %, RSS memory in MB, and thread counts using psutil across entire process trees.",
        "Metric Averager (Every 1 minute): Computes 1-minute averages and commits them to the metrics_1m table for 7-day trend graphs.",
        "Log Tailer (Every 200 milliseconds): Follows each active log file on disk and broadcasts newly appended lines over the WebSocket bus.",
        "Event Engine (Event-driven): Emits warnings for high CPU (>90%), high memory (>80%), or unexpected process exits."
    ])

    add_card(s6, Inches(6.9), Inches(1.8), Inches(5.6), Inches(5.0), "Live WebSocket Bus (/ws)")
    add_bullet_points(s6, Inches(7.1), Inches(2.4), Inches(5.2), Inches(4.2), [
        "Single Persistent Channel: The browser maintains one WebSocket connection to ws://127.0.0.1:7777/ws.",
        "Client Subscriptions: The UI sends {'sub': 'status'}, {'sub': 'events'}, or {'sub': 'logs:<comp_id>'}.",
        "Push Updates: The server pushes status changes immediately, turning UI lamps from yellow to green without page reloads.",
        "Batched Log Output: Logs are batched (max 50 lines per 100ms) to ensure butter-smooth rendering without UI lag.",
        "Auto-reconnect & Fallback: If disconnected, exponential backoff reconnects automatically; 5-second REST polling serves as fallback."
    ])
    s6.notes_slide.notes_text_frame.text = (
        "While Hangar is open in your browser, several continuous background loops run silently. "
        "The health checker verifies ports every 5 seconds. The metrics engine samples CPU and memory every 2 seconds. "
        "The log tailer checks for new lines on disk every 200ms. "
        "All updates flow through one high-speed WebSocket connection directly to your screen."
    )

    # ==========================================
    # SLIDE 7: Section 7: Process Lifecycle Flow
    # ==========================================
    s7 = add_base_slide("How the Backend Starts, Stops & Restarts Projects", "Section 7: Process Engine")
    add_card(s7, Inches(0.8), Inches(1.8), Inches(3.7), Inches(5.0), "START FLOW", RUN_COLOR)
    add_bullet_points(s7, Inches(0.9), Inches(2.4), Inches(3.5), Inches(4.2), [
        "1. Validate working directory (cwd) and start command.",
        "2. Check if declared port is already busy. If busy, report conflict with holding PID.",
        "3. Create new row in 'runs' table with unique run ID.",
        "4. Spawn subprocess in its own process group with merged stdout+stderr piped to log file.",
        "5. Component status becomes 'starting'.",
        "6. Health check probe runs. When it passes within 30s grace, status turns to 'running' (green lamp)."
    ])

    add_card(s7, Inches(4.8), Inches(1.8), Inches(3.7), Inches(5.0), "STOP FLOW", ERR_COLOR)
    add_bullet_points(s7, Inches(4.9), Inches(2.4), Inches(3.5), Inches(4.2), [
        "1. Set user_stopped flag to True (prevents autorestart from triggering).",
        "2. If custom stop_cmd defined, execute it.",
        "3. Otherwise, kill the entire process tree: send SIGTERM (or terminate on Windows).",
        "4. Wait up to 5 seconds gracefully.",
        "5. Force kill (SIGKILL or taskkill /T /F on Windows) if still clinging to life.",
        "6. Record ended_at in database and turn status lamp to 'stopped'."
    ])

    add_card(s7, Inches(8.8), Inches(1.8), Inches(3.7), Inches(5.0), "RESTART & ORDERING", START_COLOR)
    add_bullet_points(s7, Inches(8.9), Inches(2.4), Inches(3.5), Inches(4.2), [
        "Restart: Sequentially executes Stop flow, waits for port release, then executes Start flow.",
        "Ordered Application Boot:",
        "• Tier 1 (Database): Starts first, waits until healthy.",
        "• Tier 2 (Backend): Starts second, waits until healthy.",
        "• Tier 3 (Frontend): Starts last once API is up.",
        "Application Shutdown:",
        "• Shuts down in exact reverse order (Frontend ➔ Backend ➔ Database)."
    ])
    s7.notes_slide.notes_text_frame.text = (
        "Starting and stopping software correctly is hard. Hangar handles the edge cases. "
        "When starting, it verifies the port is free and pipes child output straight to a log file on disk. "
        "When stopping, it kills the ENTIRE process tree. On Windows, it uses 'taskkill /T /F' to ensure no runaway node.exe or python.exe processes stay behind. "
        "And for whole projects, it starts services by tier: database first, backend second, frontend third."
    )

    # ==========================================
    # SLIDE 8: Section 8: Status Detection
    # ==========================================
    s8 = add_base_slide("How Status is Detected (Lamps & States)", "Section 8: Status Engine")
    
    statuses = [
        ("stopped", "Process is not running. Exit code 0 or stopped by user. Power switch OFF.", MUTED_COLOR),
        ("starting", "Process spawned. Waiting for health check probe to pass within startup grace period.", START_COLOR),
        ("running", "Process is alive and health check passes. Lamp glows bright green. Power switch ON.", RUN_COLOR),
        ("unhealthy", "Process PID is alive, but health check is failing (e.g. HTTP 500 or port unreachable).", WARN_COLOR),
        ("crashed", "Process exited unexpectedly with non-zero exit code. Triggers alert and log capture.", ERR_COLOR),
        ("external", "Port is occupied by an external service not launched by Hangar (e.g. system Docker).", START_COLOR),
    ]

    for i, (name, desc, col) in enumerate(statuses):
        col_idx = i % 2
        row_idx = i // 2
        left_pos = Inches(0.8 + col_idx * 5.9)
        top_pos = Inches(1.8 + row_idx * 1.7)

        add_card(s8, left_pos, top_pos, Inches(5.7), Inches(1.5), name.upper(), col)
        tb = s8.shapes.add_textbox(left_pos + Inches(0.2), top_pos + Inches(0.55), Inches(5.3), Inches(0.85))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = desc
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_COLOR

    s8.notes_slide.notes_text_frame.text = (
        "Components can be in one of six computed statuses. "
        "Importantly, status is never based on simple guessing: it verifies both the operating system process ID and the network health check. "
        "If a process is running but returning 500 errors, Hangar shows an amber 'unhealthy' lamp so you know immediately."
    )

    # ==========================================
    # SLIDE 9: Section 9: Log Collection
    # ==========================================
    s9 = add_base_slide("How Logs Are Collected, Stored & Displayed", "Section 9: Logging Architecture")
    add_card(s9, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "Direct-to-Disk Log Capture")
    add_bullet_points(s9, Inches(1.0), Inches(2.4), Inches(5.2), Inches(4.2), [
        "No Pipe Buffering: Child stdout and stderr are merged and written directly into log files by the OS kernel.",
        "File Path: ~/.hangar/logs/<component_id>/run-<run_id>.log",
        "Survival: Because logs are written to disk, they survive browser refreshes and Hangar backend restarts.",
        "System Log Markers: When a process stops or crashes, Hangar writes a system marker line: [hangar] Process exited with code X.",
        "Log Retention: Automatically maintains the last 10 runs per component and caps total disk space."
    ])

    add_card(s9, Inches(6.9), Inches(1.8), Inches(5.6), Inches(5.0), "Real-Time Terminal Viewer")
    add_bullet_points(s9, Inches(7.1), Inches(2.4), Inches(5.2), Inches(4.2), [
        "Live Tailer Engine: ComponentLogTailer checks file byte offset every 200ms using asynchronous file I/O.",
        "WebSocket Push: Pushes up to 50 new lines at a time directly to the browser viewer.",
        "ANSI Color Rendering: Terminal color codes are stripped for search indexing, but rendered as true terminal colors in the UI.",
        "Crash Context Capture: When a crash occurs, Hangar automatically snapshots the last 20 log lines and attaches them to the activity alert."
    ])
    s9.notes_slide.notes_text_frame.text = (
        "Logs in Hangar are rock-solid because of how they are piped. "
        "Child processes do not write to an in-memory buffer that could overflow; they write straight to a file on your disk. "
        "The log tailer follows this file in real-time, streaming lines to your screen over WebSockets, while preserving past run history."
    )

    # ==========================================
    # SLIDE 10: Section 10: Data Storage & Schema
    # ==========================================
    s10 = add_base_slide("How Data is Stored: SQLite Database Schema", "Section 10: Data Architecture")
    tables = [
        ("applications", "id (UUID), name, description, icon, path (folder), tags (JSON), favorite, sort, start_mode, created_at"),
        ("components", "id, application_id, kind (frontend/backend/db), name, cwd, start_cmd, stop_cmd, env, port, url, health (JSON), tier, autorestart"),
        ("runs", "id, component_id, pid, create_time, started_at, ended_at, exit_code, stop_reason (user/crash/restart/system), log_path"),
        ("events", "id, ts, level (info/warn/error), type, application_id, component_id, title, reason, detail (JSON), read"),
        ("metrics_1m", "ts, component_id, cpu_pct, rss_mb (persisted 1-minute historical averages for 7-day graphs)"),
        ("settings", "key, value (stores theme, shell override, startup grace, health interval, alert thresholds, on_exit)")
    ]
    for i, (tbl, fields) in enumerate(tables):
        top_pos = Inches(1.8 + i * 0.85)
        add_card(s10, Inches(0.8), top_pos, Inches(11.733), Inches(0.75), "", WARN_COLOR)
        tb = s10.shapes.add_textbox(Inches(1.0), top_pos + Inches(0.08), Inches(11.3), Inches(0.6))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"TABLE: {tbl}\n"
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = START_COLOR
        p2 = tf.add_paragraph()
        p2.text = fields
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_COLOR

    s10.notes_slide.notes_text_frame.text = (
        "All data is stored locally in an SQLite database located at ~/.hangar/hangar.db. "
        "We have six primary tables: applications (the projects), components (the individual services), "
        "runs (the execution history of every start and stop), events (notifications and crash logs), "
        "metrics_1m (CPU and RAM history), and settings (configuration)."
    )

    # ==========================================
    # SLIDE 11: Section 11: Page-by-Page Walkthrough
    # ==========================================
    s11 = add_base_slide("Page-by-Page Walkthrough: The 6 Dashboard Screens", "Section 11: User Interface")
    pages = [
        ("1. Overview", "Master power control, total running count, live system CPU/RAM gauges, project rack units, and recent alerts.", "GET /api/overview"),
        ("2. Applications", "Full project management: start/stop ordered sequences, open project in VS Code or Explorer, add projects, and remove projects.", "GET /api/applications"),
        ("3. Logs", "Dedicated full-screen terminal viewer for any service, with live auto-scroll, clear log, download, and past run inspection.", "GET /api/components/{id}/logs"),
        ("4. Ports", "Port inspection table: shows listening TCP ports, owning PIDs, and provides a 1-click 'Kill and free port' button.", "GET /api/ports"),
        ("5. Activity", "Chronological system event timeline: shows every start, stop, restart, crash report, and warning with last 20 log lines.", "GET /api/events"),
        ("6. Settings", "Configure theme (Light/Dark/System), default shell, health intervals, load/remove built-in demo apps, export JSON backup.", "GET/PUT /api/settings")
    ]
    for i, (name, desc, api) in enumerate(pages):
        col_idx = i % 2
        row_idx = i // 2
        left_pos = Inches(0.8 + col_idx * 5.9)
        top_pos = Inches(1.8 + row_idx * 1.7)

        add_card(s11, left_pos, top_pos, Inches(5.7), Inches(1.5), name)
        tb = s11.shapes.add_textbox(left_pos + Inches(0.2), top_pos + Inches(0.5), Inches(5.3), Inches(0.9))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = desc
        p1.font.size = Pt(11)
        p1.font.color.rgb = TEXT_COLOR
        p2 = tf.add_paragraph()
        p2.text = f"Data Feed: {api}"
        p2.font.size = Pt(11)
        p2.font.bold = True
        p2.font.color.rgb = MUTED_COLOR

    s11.notes_slide.notes_text_frame.text = (
        "The dashboard has six tabs along the left rail. "
        "Overview gives you the high-level pulse of your machine. "
        "Applications lets you control and configure your projects. "
        "Logs provides the terminal window. "
        "Ports detects conflicts. "
        "Activity keeps a history of events. "
        "And Settings lets you customize preferences."
    )

    # ==========================================
    # SLIDE 12: Section 12: Complete API Reference
    # ==========================================
    s12 = add_base_slide("API Reference: REST Endpoints", "Section 12: API Specification")
    
    # Create Table for API Endpoints
    rows = 11
    cols = 4
    left = Inches(0.8)
    top = Inches(1.8)
    width = Inches(11.733)
    height = Inches(5.0)

    table_shape = s12.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table
    table.columns[0].width = Inches(1.5)
    table.columns[1].width = Inches(3.8)
    table.columns[2].width = Inches(4.4)
    table.columns[3].width = Inches(2.033)

    headers = ["Method", "Endpoint Path", "Purpose & Action", "Called By"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = SURFACE_2
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = START_COLOR

    api_data = [
        ("GET", "/api/overview", "Returns counts, CPU/RAM stats, apps and recent events", "Overview page load"),
        ("GET / POST", "/api/applications", "List all registered applications or register a new one", "Apps page / Add dialog"),
        ("DELETE", "/api/applications/{id}", "Delete app, stop processes, clean up log files", "Remove Project button"),
        ("POST", "/api/applications/{id}/start", "Start app in safe tier order (DB ➔ API ➔ Web)", "Start app / Start all"),
        ("POST", "/api/applications/{id}/stop", "Stop app components in reverse tier order", "Stop app / Stop all"),
        ("POST", "/api/components/{id}/start", "Start a single component process", "PowerSwitch toggle"),
        ("POST", "/api/components/{id}/stop", "Stop single component process tree", "PowerSwitch toggle"),
        ("GET", "/api/components/{id}/logs", "Fetch historical log lines from disk", "Logs viewer"),
        ("GET", "/api/ports", "List active TCP listening sockets and owners", "Ports tab"),
        ("POST", "/api/ports/{port}/kill", "Force terminate process holding a given port", "Kill port action"),
    ]

    for i, (m, ep, desc, caller) in enumerate(api_data):
        row_idx = i + 1
        for col_idx, val in enumerate([m, ep, desc, caller]):
            cell = table.cell(row_idx, col_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = BG_COLOR if i % 2 == 0 else SURFACE_COLOR
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(10)
            p.font.color.rgb = RUN_COLOR if col_idx == 0 and "GET" in val else ERR_COLOR if col_idx == 0 and "DELETE" in val else START_COLOR if col_idx == 0 else TEXT_COLOR

    s12.notes_slide.notes_text_frame.text = (
        "This table documents the primary REST API endpoints exposed by the FastAPI backend on port 7777. "
        "Every endpoint requires the X-Hangar-Client header. "
        "Notice the DELETE /api/applications/{id} endpoint which was enhanced to handle process stopping and log cleanup."
    )

    # ==========================================
    # SLIDE 13: Section 13: Function Reference
    # ==========================================
    s13 = add_base_slide("Function Reference: Core Architecture", "Section 13: Code Reference")
    
    rows = 9
    cols = 4
    table_shape2 = s13.shapes.add_table(rows, cols, Inches(0.8), Inches(1.8), Inches(11.733), Inches(5.0))
    table2 = table_shape2.table
    table2.columns[0].width = Inches(2.6)
    table2.columns[1].width = Inches(4.5)
    table2.columns[2].width = Inches(2.3)
    table2.columns[3].width = Inches(2.333)

    headers2 = ["Component / Function", "What It Does in One Sentence", "Called By", "Calls"]
    for j, h in enumerate(headers2):
        cell = table2.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = SURFACE_2
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = START_COLOR

    func_data = [
        ("Supervisor.start_component()", "Validates cwd, checks ports, spawns process tree, tails log.", "api/components.py, orchestrator", "spawn_process(), run_health_check()"),
        ("Supervisor.stop_component()", "Kills process tree gracefully (SIGTERM) then force kills (taskkill).", "api/components.py, orchestrator", "kill_process_tree(), db updates"),
        ("Supervisor.remove_tracked()", "Removes in-memory tracking entry when an app is deleted.", "api/applications.py", "self.components.pop()"),
        ("Orchestrator.start_application()", "Executes multi-step ordered startup across component tiers.", "api/applications.py", "supervisor.start_component()"),
        ("run_health_check()", "Probes TCP port, HTTP endpoint, process PID, or SQLite file.", "supervisor monitor loop", "asyncio.open_connection, httpx"),
        ("ComponentLogTailer.run()", "Polls disk log file every 200ms and pushes new lines to WebSocket.", "supervisor background task", "bus.publish()"),
        ("HangarDashboard()", "Main React dashboard component managing tabs, forms, and dialogs.", "src/app/page.tsx", "lib/api.ts, lib/ws.ts"),
        ("handleRemoveApplication()", "Frontend handler sending DELETE request with confirmation state.", "Remove button in UI", "api.deleteApplication(), loadDashboard()"),
    ]

    for i, (fn, desc, called, calls) in enumerate(func_data):
        row_idx = i + 1
        for col_idx, val in enumerate([fn, desc, called, calls]):
            cell = table2.cell(row_idx, col_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = BG_COLOR if i % 2 == 0 else SURFACE_COLOR
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(10)
            p.font.color.rgb = START_COLOR if col_idx == 0 else TEXT_COLOR

    s13.notes_slide.notes_text_frame.text = (
        "This function reference details the most critical functions in Hangar. "
        "The Supervisor class is the heart of process control, while the Orchestrator handles dependencies between services. "
        "On the frontend, HangarDashboard coordinates the user experience and handlers."
    )

    # ==========================================
    # SLIDE 14: Section 14: Click Start Walkthrough
    # ==========================================
    s14 = add_base_slide("Full Example: 'I Click Start on a Project'", "Section 14: Sequence Walkthrough")
    
    seq_steps = [
        ("1. User Click", "User flips PowerSwitch or clicks 'Start app'. Frontend enters loading state; sends POST /api/applications/{id}/start."),
        ("2. Lock & Sequence", "FastAPI orchestrator acquires app lock, fetches components, and sorts them by tier (Database 1, Backend 2, Frontend 3)."),
        ("3. Port Conflict Check", "Supervisor checks if component declared port (e.g. :4102) is in use. If free, proceeds to spawn."),
        ("4. Process Tree Spawn", "Supervisor spawns process using platform shell (cmd.exe on Windows, /bin/sh on POSIX) with output directed to run-<id>.log."),
        ("5. Log Tailer Attach", "Supervisor starts ComponentLogTailer to stream lines from the new log file over the WebSocket bus."),
        ("6. Health Probing", "Component status becomes 'starting' (pulsing blue lamp). Health checker probes TCP/HTTP every 500ms."),
        ("7. Green Lamp Active!", "Health probe returns 200 OK! Component status switches to 'running' (bright green glowing lamp) and WebSocket notifies UI.")
    ]

    for i, (st, desc) in enumerate(seq_steps):
        top_pos = Inches(1.8 + i * 0.75)
        add_card(s14, Inches(0.8), top_pos, Inches(11.733), Inches(0.68), "", RUN_COLOR if i == 6 else START_COLOR if i == 0 else LINE_COLOR)
        tb = s14.shapes.add_textbox(Inches(1.0), top_pos + Inches(0.06), Inches(11.3), Inches(0.55))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"{st}:  "
        p1.font.bold = True
        p1.font.size = Pt(12)
        p1.font.color.rgb = RUN_COLOR if i == 6 else START_COLOR
        run = p1.add_run()
        run.text = desc
        run.font.bold = False
        run.font.size = Pt(11)
        run.font.color.rgb = TEXT_COLOR

    s14.notes_slide.notes_text_frame.text = (
        "Here is the complete step-by-step journey of what happens behind the scenes when you click 'Start'. "
        "From the button click in your browser, through the FastAPI tier orchestrator, subprocess spawn, "
        "log file creation, and health check validation, right up to the green lamp lighting on your screen."
    )

    # ==========================================
    # SLIDE 15: Section 15: Remove Project Feature
    # ==========================================
    s15 = add_base_slide("The Remove Project Feature (Part 3)", "Section 15: New Feature")
    add_card(s15, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0), "How the Remove Feature Works", ERR_COLOR)
    add_bullet_points(s15, Inches(1.0), Inches(2.4), Inches(5.2), Inches(4.2), [
        "Dedicated Remove Button: Each project card on Overview and Applications tabs now has a red trashcan 'Remove' button.",
        "Safety Modal Dialog: Clicking Remove opens a confirmation dialog showing the exact application name and a clear warning.",
        "Stop Running Processes Checkbox: If services are active, a checked-by-default checkbox offers to safely terminate running processes first.",
        "Zero File Destruction Guarantee: Hangar NEVER touches or deletes your project folder, source code, git repository, or local files.",
        "Clean Database & Log Deletion: Deletes the registration from SQLite, cleans up internal supervisor tracking, and deletes old run log files.",
        "Spinner & Disable Protection: Buttons are disabled during the request to prevent double-click race conditions."
    ])

    add_card(s15, Inches(6.9), Inches(1.8), Inches(5.6), Inches(5.0), "Code Implementation Summary", START_COLOR)
    add_bullet_points(s15, Inches(7.1), Inches(2.4), Inches(5.2), Inches(4.2), [
        "Backend API: DELETE /api/applications/{id}?stop_first=true in backend/hangar/api/applications.py.",
        "Supervisor Cleanup: Added supervisor.remove_tracked(comp_id) to remove in-memory tracked components.",
        "Log Purging: Calls shutil.rmtree(LOGS_DIR / comp_id) to free disk space.",
        "Frontend API: Updated deleteApplication(id, stopFirst) in frontend/src/lib/api.ts.",
        "Frontend UI: Integrated Radix confirmation Dialog and feedback toasts in HangarDashboard.tsx.",
        "Full Test Coverage: Automated tests verify deleting stopped apps, deleting with stop_first=false, and 404 for missing IDs."
    ])
    s15.notes_slide.notes_text_frame.text = (
        "In Part 3 of this work, we added the Remove Project feature. "
        "Users can now safely unregister any project from their dashboard. "
        "It includes a confirmation modal, optional automatic process termination, and log directory cleanup, "
        "while providing a 100% guarantee that your actual source code and project folders are never touched."
    )

    # ==========================================
    # SLIDE 16: Section 16: Common Problems & Fixes
    # ==========================================
    s16 = add_base_slide("Common Problems & How Hangar Fixes Them", "Section 16: Troubleshooting")
    problems = [
        ("Problem 1: Port Already in Use", "Hangar detects the conflict before starting, finds the owning PID and process name using psutil, and displays a 'Kill it and start' button in the UI."),
        ("Problem 2: Zombie / Orphan Child Processes", "Hangar spawns processes in distinct process groups. On stop, it terminates the entire tree, falling back to 'taskkill /T /F' on Windows to kill stuck processes."),
        ("Problem 3: Crash Loops & Flapping Services", "If a service crashes repeatedly, autorestart uses exponential backoff (1s, 2s, 4s, 8s, 16s). After 5 attempts, it stops and fires a 'restart_loop' event."),
        ("Problem 4: Backend Unreachable / Reconnecting", "The frontend detects WebSocket drops, shows an amber pulsing dot in the dock, attempts auto-reconnection, and falls back to REST polling."),
        ("Problem 5: Runaway CPU or Memory Leaks", "The metrics engine alerts you with a warning toast whenever a process tree exceeds 90% CPU or 80% RAM for over two sampling intervals.")
    ]
    for i, (pr, fix) in enumerate(problems):
        top_pos = Inches(1.8 + i * 1.0)
        add_card(s16, Inches(0.8), top_pos, Inches(11.733), Inches(0.88), "", WARN_COLOR)
        tb = s16.shapes.add_textbox(Inches(1.0), top_pos + Inches(0.08), Inches(11.3), Inches(0.72))
        tf = tb.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"{pr}:  "
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = WARN_COLOR
        run = p1.add_run()
        run.text = fix
        run.font.bold = False
        run.font.size = Pt(12)
        run.font.color.rgb = TEXT_COLOR

    s16.notes_slide.notes_text_frame.text = (
        "Here are five common developer headaches that Hangar handles automatically. "
        "Port conflicts are detected before launch with one-click cleanup. "
        "Orphaned background processes are eliminated with process tree killing. "
        "Crash loops are halted by exponential backoff to protect system resources."
    )

    # ==========================================
    # SLIDE 17: Section 17: Plain-English Glossary
    # ==========================================
    s17 = add_base_slide("Glossary: Plain-English Technical Terms", "Section 17: Terminology")
    
    terms = [
        ("Localhost", "Your own computer. IP address 127.0.0.1. Network traffic stays entirely inside your machine."),
        ("Port", "A numbered software doorway on your computer (e.g. 7777) allowing programs to receive connections."),
        ("Process", "An active program running in operating system memory (e.g. python.exe or node.exe)."),
        ("PID (Process ID)", "A unique number assigned by Windows or Linux to identify a specific running program."),
        ("Process Tree", "A parent program and all the child programs it spawned (e.g. npm running a Vite dev server)."),
        ("Subprocess", "A program started by another program (e.g. Hangar starting your backend API)."),
        ("Frontend", "The visible user interface screen with buttons and charts that you see in the browser."),
        ("Backend", "The background program that manages data, executes commands, and supervises processes."),
        ("Database", "A filing cabinet file (SQLite) that stores your projects, history, and settings permanently."),
        ("API / Endpoint", "A specific web address (like /api/overview) where programs ask for data or trigger actions."),
        ("WebSocket", "A continuous two-way live connection that allows the server to push updates instantly."),
        ("Polling", "Checking repeatedly on a timer (e.g. every 5 seconds) to see if data has changed.")
    ]

    for i, (t, defn) in enumerate(terms):
        col_idx = i % 2
        row_idx = i // 2
        left_pos = Inches(0.8 + col_idx * 5.9)
        top_pos = Inches(1.8 + row_idx * 0.85)

        tb = s17.shapes.add_textbox(left_pos, top_pos, Inches(5.6), Inches(0.75))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = f"{t}: "
        p.font.bold = True
        p.font.size = Pt(12)
        p.font.color.rgb = START_COLOR
        run = p.add_run()
        run.text = defn
        run.font.bold = False
        run.font.size = Pt(11)
        run.font.color.rgb = TEXT_COLOR

    s17.notes_slide.notes_text_frame.text = (
        "This glossary defines all 12 key technical terms used throughout this presentation and the Hangar documentation. "
        "Every definition is written in simple, everyday language so that any beginner can easily understand how Hangar works."
    )

    # Save presentation
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_path))
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    docs_dir = Path("docs")
    target = docs_dir / "Hangar_How_It_Works.pptx"
    create_deck(target)

