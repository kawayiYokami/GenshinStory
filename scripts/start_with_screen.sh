#!/usr/bin/env bash

set -euo pipefail

# One-click launcher for frontend + backend in detached screen sessions.
# Usage:
#   ./scripts/start_with_screen.sh start
#   ./scripts/start_with_screen.sh stop
#   ./scripts/start_with_screen.sh restart
#   ./scripts/start_with_screen.sh status

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONT_SESSION="genshinstory_frontend"
BACK_SESSION="genshinstory_backend"

FRONT_HOST="${FRONT_HOST:-0.0.0.0}"
FRONT_PORT="${FRONT_PORT:-5713}"
BACK_HOST="${BACK_HOST:-127.0.0.1}"
BACK_PORT="${BACK_PORT:-8000}"
FRONT_SEARCH_MODE="${FRONT_SEARCH_MODE:-backend}"
FRONT_BACKEND_URL="${FRONT_BACKEND_URL:-/api}"
FRONT_SKIP_BUILD="${FRONT_SKIP_BUILD:-0}"

FRONT_CMD="cd \"$ROOT_DIR\" && pnpm --dir web/docs-site preview --host $FRONT_HOST --port $FRONT_PORT"
BACK_CMD="cd \"$ROOT_DIR\" && uv run uvicorn main:app --host $BACK_HOST --port $BACK_PORT --app-dir web/backend"
FRONT_BUILD_CMD="cd \"$ROOT_DIR\" && VITE_SEARCH_MODE=$FRONT_SEARCH_MODE VITE_BACKEND_URL=$FRONT_BACKEND_URL pnpm --dir web/docs-site build"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[ERROR] Missing command: $1"
    exit 1
  fi
}

ensure_front_build_exists() {
  if [[ ! -f "$ROOT_DIR/web/docs-site/dist/index.html" ]]; then
    echo "[ERROR] Missing frontend build artifact: web/docs-site/dist/index.html"
    echo "[HINT] Run: pnpm --dir web/docs-site build"
    exit 1
  fi
}

build_frontend() {
  if [[ "$FRONT_SKIP_BUILD" == "1" ]]; then
    echo "[INFO] Skip frontend build (FRONT_SKIP_BUILD=1)"
    return 0
  fi
  echo "[INFO] Building frontend with VITE_SEARCH_MODE=$FRONT_SEARCH_MODE VITE_BACKEND_URL=$FRONT_BACKEND_URL"
  bash -lc "$FRONT_BUILD_CMD"
}

session_exists() {
  local name="$1"
  screen -list | grep -q "[.]$name[[:space:]]"
}

start_one() {
  local session="$1"
  local cmd="$2"
  if session_exists "$session"; then
    echo "[INFO] Session already exists: $session"
    return 0
  fi
  echo "[INFO] Starting session: $session"
  screen -dmS "$session" bash -lc "$cmd"
}

stop_one() {
  local session="$1"
  if session_exists "$session"; then
    echo "[INFO] Stopping session: $session"
    screen -S "$session" -X quit
  else
    echo "[INFO] Session not running: $session"
  fi
}

print_status() {
  echo "[INFO] Current screen sessions:"
  if screen -list | grep -E "($FRONT_SESSION|$BACK_SESSION)" >/dev/null 2>&1; then
    screen -list | grep -E "($FRONT_SESSION|$BACK_SESSION)" || true
  else
    echo "  (none)"
  fi
}

usage() {
  cat <<EOF
Usage: $0 <start|stop|restart|status>

Environment overrides:
  FRONT_HOST (default: $FRONT_HOST)
  FRONT_PORT (default: $FRONT_PORT)
  BACK_HOST  (default: $BACK_HOST)
  BACK_PORT  (default: $BACK_PORT)
  FRONT_SEARCH_MODE (default: $FRONT_SEARCH_MODE)
  FRONT_BACKEND_URL (default: $FRONT_BACKEND_URL)
  FRONT_SKIP_BUILD  (default: $FRONT_SKIP_BUILD)
EOF
}

main() {
  require_cmd screen
  require_cmd pnpm
  require_cmd uv

  local action="${1:-start}"
  case "$action" in
    start)
      build_frontend
      ensure_front_build_exists
      start_one "$BACK_SESSION" "$BACK_CMD"
      start_one "$FRONT_SESSION" "$FRONT_CMD"
      print_status
      echo "[INFO] Attach frontend: screen -r $FRONT_SESSION"
      echo "[INFO] Attach backend : screen -r $BACK_SESSION"
      ;;
    stop)
      stop_one "$FRONT_SESSION"
      stop_one "$BACK_SESSION"
      print_status
      ;;
    restart)
      build_frontend
      ensure_front_build_exists
      stop_one "$FRONT_SESSION"
      stop_one "$BACK_SESSION"
      start_one "$BACK_SESSION" "$BACK_CMD"
      start_one "$FRONT_SESSION" "$FRONT_CMD"
      print_status
      echo "[INFO] Attach frontend: screen -r $FRONT_SESSION"
      echo "[INFO] Attach backend : screen -r $BACK_SESSION"
      ;;
    status)
      print_status
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
