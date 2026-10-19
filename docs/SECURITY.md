# Hangar Security Policy

## Core Principle: Localhost Only
Hangar is strictly designed for local machine execution by a single developer. It must **never** be exposed to a public network, reverse-proxied without authentication, or bound to `0.0.0.0`.

## Drive-By Web Page Defense

Because local APIs can be targeted by malicious websites running in the user's browser, Hangar employs multi-layer protection:

1. **Strict Host Verification**:
   - The backend explicitly validates the `Host` header.
   - Allowed hosts: `localhost`, `127.0.0.1`, `[::1]` with the configured port (e.g. `:7777`).
   - Any external domain or unrecognized host is immediately rejected with HTTP 403, preventing DNS rebinding attacks.

2. **CORS Preflight & Custom Header Enforcement**:
   - Every mutating/non-GET request (POST, PUT, PATCH, DELETE) and WebSocket connection must contain the `X-Hangar-Client: 1` header.
   - Malicious web pages attempting `fetch()` cannot set custom headers cross-origin without triggering a browser CORS preflight.
   - Wildcard CORS (`*`) is prohibited.
   - Allowed `Origin` values are strictly restricted to `http://localhost:7777`, `http://127.0.0.1:7777`, `http://[::1]:7777`, and `http://localhost:3000` (in dev mode).
   - Any request violating origin or header checks receives an immediate HTTP 403 Forbidden.

3. **No Arbitrary Command Execution**:
   - Process commands are only run if they are stored component configurations explicitly saved by the user.
   - No generic `exec` endpoint exists.

4. **Safe Process Isolation**:
   - Processes are started in their own process groups.
   - Graceful termination followed by forced tree kill guarantees no orphaned processes or hung listening ports.
