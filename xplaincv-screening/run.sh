#!/usr/bin/env bash
# Start everything for local development:
#   infra (docker) -> migrations -> API -> Celery worker -> frontend
set -e
cd "$(dirname "$0")"

echo "[0/4] stopping previous instances"
pkill -f "uvicorn app.main:app"          2>/dev/null || true
pkill -f "celery -A app.tasks.celery_app" 2>/dev/null || true
pkill -f "$(pwd)/frontend/node_modules/.bin/vite" 2>/dev/null || true
sleep 1

echo "[1/4] infra (postgres + redis)"
sudo docker compose up -d

echo "[2/4] migrations"
(cd backend && ../.venv/bin/alembic upgrade head)

echo "[3/4] backend (API :8000 + worker)"
(cd backend && setsid nohup ./run_api.sh    > /tmp/xplain_api.log    2>&1 < /dev/null &)
(cd backend && setsid nohup ./run_worker.sh > /tmp/xplain_worker.log 2>&1 < /dev/null &)

echo "[4/4] frontend (:5173)"
(cd frontend && setsid nohup npm run dev > /tmp/xplain_frontend.log 2>&1 < /dev/null &)

sleep 8
echo
curl -s localhost:8000/api/health && echo
echo "open http://localhost:5173"
