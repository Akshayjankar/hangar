#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HANGAR_PORT="${HANGAR_PORT:-7777}"
export NEXT_PUBLIC_API_URL="http://127.0.0.1:${HANGAR_PORT}"
export NEXT_PUBLIC_WS_URL="ws://127.0.0.1:${HANGAR_PORT}/ws"

echo "Building Hangar frontend static export for port ${HANGAR_PORT}..."
npm run build --prefix "$ROOT_DIR/frontend"
echo "Frontend build complete."

