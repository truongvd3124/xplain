#!/usr/bin/env bash
# FastAPI server (native — uses the project venv that shares the GPU stack).
cd "$(dirname "$0")"
exec ../.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
