from __future__ import annotations
from typing import Callable
from urllib.parse import urlparse
from fastapi import Request, Response, WebSocket, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .config import ALLOWED_HOSTS, ALLOWED_ORIGINS, PORT


def is_valid_host(host_header: str | None) -> bool:
    """Validate that the Host header matches localhost/127.0.0.1/[::1] on the configured port."""
    if not host_header:
        return False
    # Strip potential outer whitespace
    host = host_header.strip().lower()
    return host in ALLOWED_HOSTS


def is_valid_origin(origin_header: str | None) -> bool:
    """Validate that the Origin header is in the strictly allowed origins set."""
    if not origin_header:
        return False
    norm_origin = origin_header.strip().rstrip("/")
    for allowed in ALLOWED_ORIGINS:
        if norm_origin == allowed.rstrip("/"):
            return True
    return False


def is_valid_hangar_client(header_value: str | None) -> bool:
    """Validate the presence of X-Hangar-Client: 1 header."""
    if not header_value:
        return False
    return header_value.strip() == "1"


class SecurityGuardMiddleware(BaseHTTPMiddleware):
    """
    Middleware strictly enforcing:
    1. Host header validation against localhost/127.0.0.1/[::1]:PORT (prevents DNS rebinding).
    2. Origin & X-Hangar-Client verification on non-GET mutating HTTP requests (POST/PUT/PATCH/DELETE)
       to defeat drive-by attacks from malicious external websites.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Check Host header
        host_header = request.headers.get("host")
        if not is_valid_host(host_header):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Forbidden: Invalid Host header. Localhost only."},
            )

        # 2. Check mutating HTTP methods (POST, PUT, PATCH, DELETE)
        # Note: OPTIONS requests are allowed through for CORS preflight
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            client_header = request.headers.get("x-hangar-client")

            # Check Origin
            if not is_valid_origin(origin):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Forbidden: Origin not allowed."},
                )

            # Check X-Hangar-Client: 1
            if not is_valid_hangar_client(client_header):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Forbidden: Missing or invalid X-Hangar-Client header."},
                )

        response = await call_next(request)
        return response


def validate_websocket_handshake(websocket: WebSocket) -> tuple[bool, str]:
    """
    Validate WebSocket handshake:
    - Host must be valid localhost/127.0.0.1/[::1]
    - Origin must be an allowed origin
    - Client check: X-Hangar-Client header OR 'x-hangar-client' in Sec-WebSocket-Protocol OR query param client=1
    """
    host = websocket.headers.get("host")
    if not is_valid_host(host):
        return False, "Invalid Host header"

    origin = websocket.headers.get("origin")
    if not is_valid_origin(origin):
        return False, "Invalid Origin"

    # Client verification
    header_client = websocket.headers.get("x-hangar-client")
    protocols = websocket.headers.get("sec-websocket-protocol", "")
    query_client = websocket.query_params.get("x-hangar-client") or websocket.query_params.get("client")

    has_client_proof = (
        is_valid_hangar_client(header_client)
        or ("x-hangar-client" in protocols.lower())
        or (query_client == "1")
    )

    if not has_client_proof:
        return False, "Missing or invalid X-Hangar-Client proof"

    return True, "OK"

