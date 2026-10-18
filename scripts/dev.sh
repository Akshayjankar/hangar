#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HANGAR_PORT="${HANGAR_PORT:-7777}"
export PYTHONPATH="$ROOT_DIR/backend:$PYTHONPATH"
export HANGAR_DEV_ORIGIN="http://localhost:3000"
export NEXT_PUBLIC_API_URL="http://127.0.0.1:${HANGAR_PORT}"
export NEXT_PUBLIC_WS_URL="ws://127.0.0.1:${HANGAR_PORT}/ws"

echo "Starting Hangar dev servers on port ${HANGAR_PORT}..."
trap 'kill $(jobs -p)' EXIT

python -m uvicorn hangar.main:app --reload --host 127.0.0.1 --port "${HANGAR_PORT}" &
npm run dev --prefix "$ROOT_DIR/frontend" &

wait

