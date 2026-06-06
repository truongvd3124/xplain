#!/usr/bin/env bash
# Start XplainCV MVP — backend (FastAPI + CLIP) and frontend (Vite) together.
# Usage:  ./run.sh        (Ctrl+C stops both)
set -euo pipefail

# --- paths ------------------------------------------------------------------
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
VENV_PY="/home/ubuntu/zcbm/venv/bin/python"

BACKEND_PORT=8000
FRONTEND_PORT=5173

# --- helpers ----------------------------------------------------------------
log()  { printf '\033[1;36m[run]\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31m[run]\033[0m %s\n' "$*" >&2; }

# Free a TCP port by killing whatever is listening on it.
free_port() {
  local port="$1" pids
  pids="$(lsof -ti :"$port" 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    log "port $port busy — stopping pid(s): $pids"
    kill $pids 2>/dev/null || true
    sleep 1
  fi
}

# --- preflight --------------------------------------------------------------
[ -x "$VENV_PY" ]                || { err "venv python not found: $VENV_PY"; exit 1; }
[ -d "$FRONTEND/node_modules" ]  || { err "frontend deps missing — run: cd frontend && npm install"; exit 1; }

free_port "$BACKEND_PORT"
free_port "$FRONTEND_PORT"

# --- cleanup on exit --------------------------------------------------------
BACKEND_PID=""
FRONTEND_PID=""
cleanup() {
  log "shutting down..."
  [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
  [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null || true
  wait 2>/dev/null || true
  log "stopped."
}
trap cleanup INT TERM EXIT

# --- backend ----------------------------------------------------------------
log "starting backend on http://localhost:$BACKEND_PORT ..."
( cd "$BACKEND" && PYTHONPATH=. "$VENV_PY" run.py ) &
BACKEND_PID=$!

# Wait for the backend to answer /api/health (CLIP load takes a few seconds).
log "waiting for backend (CLIP model loading) ..."
for i in $(seq 1 40); do
  if curl -sf "http://localhost:$BACKEND_PORT/api/health" >/dev/null 2>&1; then
    health="$(curl -s "http://localhost:$BACKEND_PORT/api/health")"
    log "backend ready — $health"
    break
  fi
  kill -0 "$BACKEND_PID" 2>/dev/null || { err "backend exited during startup"; exit 1; }
  sleep 1
  [ "$i" -eq 40 ] && { err "backend did not become ready in time"; exit 1; }
done

# --- frontend ---------------------------------------------------------------
log "starting frontend on http://localhost:$FRONTEND_PORT ..."
( cd "$FRONTEND" && npm run dev ) &
FRONTEND_PID=$!

echo
log "================================================================"
log "  XplainCV MVP is up.  Open:  http://localhost:$FRONTEND_PORT"
log "  API docs:                   http://localhost:$BACKEND_PORT/docs"
log "  Press Ctrl+C to stop both."
log "================================================================"
echo

# Keep the script alive; exit (and clean up) if either server dies.
wait -n "$BACKEND_PID" "$FRONTEND_PID"
err "one of the servers stopped — shutting the other down."
