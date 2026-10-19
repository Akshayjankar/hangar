#!/usr/bin/env python3
"""
Sample Fake DB using Python standard library only.
Listens on a TCP port (default 4103) and logs client connections.
"""
from __future__ import annotations
import argparse
import datetime
import os
import socket
import sys
import threading


def handle_client(conn: socket.socket, addr: tuple[str, int]) -> None:
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sys.stdout.write(f"[{now_str}] INFO New DB connection accepted from {addr[0]}:{addr[1]}\n")
    sys.stdout.flush()
    try:
        conn.sendall(b"+OK FakeDB ready\r\n")
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(b"+OK\r\n")
    except Exception:
        pass
    finally:
        conn.close()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sys.stdout.write(f"[{now_str}] INFO DB connection closed from {addr[0]}:{addr[1]}\n")
        sys.stdout.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description="Hangar Sample Fake DB")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "4103")), help="TCP port to listen on")
    args = parser.parse_args()

    port = args.port
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sys.stdout.write(f"[{now_str}] INFO Initializing FakeDB engine on port {port}...\n")
    sys.stdout.flush()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("127.0.0.1", port))
        server.listen(10)
        sys.stdout.write(f"[{now_str}] INFO FakeDB listening on 127.0.0.1:{port}\n")
        sys.stdout.flush()

        while True:
            conn, addr = server.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            client_thread.start()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        sys.stdout.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO FakeDB shutdown cleanly.\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()

