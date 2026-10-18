#!/usr/bin/env python3
"""
Sample Echo API using Python standard library only.
Supports:
  --port <port>
  --crash-after <seconds>
Provides:
  GET /health -> {"status": "ok", "uptime": <seconds>}
  GET /       -> {"message": "Sample API running", "port": <port>}
Logs a line per second with occasional WARN and ERROR.
"""
from __future__ import annotations
import argparse
import datetime
import http.server
import json
import os
import random
import socketserver
import sys
import threading
import time

start_time = time.time()


class EchoHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        uptime = round(time.time() - start_time, 1)
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = json.dumps({"status": "ok", "uptime_s": uptime})
            self.wfile.write(resp.encode("utf-8"))
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        resp = json.dumps({
            "service": "sample-echo-api",
            "path": self.path,
            "uptime_s": uptime,
            "time": datetime.datetime.utcnow().isoformat(),
        })
        self.wfile.write(resp.encode("utf-8"))

    def log_message(self, format: str, *args) -> None:
        # Standard HTTP access log
        sys.stdout.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] HTTP {format % args}\n")
        sys.stdout.flush()


def periodic_logger(stop_event: threading.Event) -> None:
    counter = 0
    levels = ["INFO", "INFO", "INFO", "WARN", "INFO", "INFO", "ERROR", "INFO"]
    sample_msgs = [
        "Processing periodic health metrics heartbeat",
        "Cache hit ratio: 98.4%",
        "Synced 12 state records with database",
        "Slow response detected on downstream connection pool",
        "Worker thread queue size is nominal (2 items)",
        "Database pool connection latency 4.2ms",
        "Connection reset by peer during keepalive check (retrying)",
        "Dispatched event notification batch to subscriber pool",
    ]

    while not stop_event.is_set():
        time.sleep(1.0)
        counter += 1
        level = random.choice(levels)
        msg = random.choice(sample_msgs)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sys.stdout.write(f"[{now_str}] {level} [tick {counter}] {msg}\n")
        sys.stdout.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description="Hangar Sample Echo API")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "4102")), help="Port to bind")
    parser.add_argument("--crash-after", type=int, default=0, help="Simulate a crash after N seconds (0 = never)")
    args = parser.parse_args()

    port = args.port
    crash_after = args.crash_after

    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO Starting Echo API on port {port} (crash_after={crash_after}s)")
    sys.stdout.flush()

    stop_event = threading.Event()
    log_thread = threading.Thread(target=periodic_logger, args=(stop_event,), daemon=True)
    log_thread.start()

    if crash_after > 0:
        def crash_timer():
            time.sleep(crash_after)
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR Fatal crash triggered by --crash-after {crash_after}s!")
            sys.stdout.flush()
            # Non-zero exit code to simulate crash
            os._exit(1)

        t = threading.Thread(target=crash_timer, daemon=True)
        t.start()

    class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True

    try:
        with ThreadedTCPServer(("127.0.0.1", port), EchoHandler) as httpd:
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO Listening at http://127.0.0.1:{port}/")
            sys.stdout.flush()
            httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO Echo API shutdown cleanly.")


if __name__ == "__main__":
    main()

