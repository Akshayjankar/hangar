#!/usr/bin/env python3
"""
Dummy Project Server for Hangar Dashboard Testing.
Uses only Python standard library.
"""
from __future__ import annotations
import argparse
import datetime
import http.server
import json
import os
import socketserver
import sys
import threading
import time

start_time = time.time()


class DummyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        uptime = round(time.time() - start_time, 1)
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "uptime_s": uptime}).encode("utf-8"))
            return

        if self.path == "/crash":
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Simulated crash"}).encode("utf-8"))
            sys.stderr.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CRITICAL Simulated crash requested!\n")
            sys.stderr.flush()
            # Exit process with error code 1 after short delay
            threading.Timer(0.5, lambda: os._exit(1)).start()
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response_data = {
            "message": "Hello from Dummy Project!",
            "status": "online",
            "uptime_seconds": uptime,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        self.wfile.write(json.dumps(response_data, indent=2).encode("utf-8"))

    def log_message(self, format: str, *args) -> None:
        sys.stdout.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] HTTP {format % args}\n")
        sys.stdout.flush()


def background_worker(stop_event: threading.Event) -> None:
    counter = 0
    while not stop_event.is_set():
        time.sleep(2.0)
        counter += 1
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if counter % 5 == 0:
            sys.stdout.write(f"[{now_str}] WARN [DummyProject] High throughput notice (#{counter})\n")
        else:
            sys.stdout.write(f"[{now_str}] INFO [DummyProject] Worker heartbeat #{counter} - operational\n")
        sys.stdout.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description="Dummy Project Server")
    default_port = int(os.environ.get("PORT", "5050"))
    parser.add_argument("--port", type=int, default=default_port, help="Port to listen on (default 5050 or $PORT)")
    args, _ = parser.parse_known_args()

    port = args.port
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO Starting Dummy Server on port {port}...")
    sys.stdout.flush()

    stop_event = threading.Event()
    worker_thread = threading.Thread(target=background_worker, args=(stop_event,), daemon=True)
    worker_thread.start()

    class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        allow_reuse_address = True

    try:
        with ThreadedServer(("127.0.0.1", port), DummyHandler) as httpd:
            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO Listening at http://127.0.0.1:{port}/")
            sys.stdout.flush()
            httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO Server shutdown.")


if __name__ == "__main__":
    main()

