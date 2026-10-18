from __future__ import annotations
import argparse
import sys
import threading
import time
import webbrowser
import uvicorn

from .config import APP_NAME, BIND_HOST, PORT, VERSION


def open_browser(url: str, delay_s: float = 1.0) -> None:
    def _open():
        time.sleep(delay_s)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    threading.Thread(target=_open, daemon=True).start()


def main() -> None:
    parser = argparse.ArgumentParser(description=f"{APP_NAME}: Control Panel for Localhost Projects")
    parser.add_argument("--port", type=int, default=PORT, help=f"Port to bind (default: {PORT})")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser on startup")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    # Hard constraint: backend binds 127.0.0.1 and refuses to bind elsewhere
    host = BIND_HOST
    port = args.port
    url = f"http://localhost:{port}"

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print(f"\n=======================================================")
    print(f"  [+] {APP_NAME} v{VERSION}")
    print(f"  Localhost Control Panel")
    print(f"  URL: {url}")
    print(f"  Local Binding: {host}:{port}")
    print(f"=======================================================\n")

    if not args.no_browser:
        open_browser(url)

    uvicorn.run(
        "hangar.main:app",
        host=host,
        port=port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()

