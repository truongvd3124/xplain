#!/usr/bin/env bash
# Celery worker. --pool=solo is REQUIRED: CUDA contexts cannot survive the
# prefork pool's fork(). Use --pool=threads if concurrency is ever needed.
cd "$(dirname "$0")"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
exec ../.venv/bin/python -m celery -A app.tasks.celery_app:celery worker \
    --pool=solo --concurrency=1 --loglevel=info "$@"
