"""Celery application.

CUDA + Celery rules (do not break these):
  - run the worker with --pool=solo (or threads); NEVER prefork — CUDA
    contexts do not survive fork().
  - CLIP is loaded in worker_process_init (post-fork), never at import time.
"""

from celery import Celery
from celery.signals import worker_process_init

from app.config import settings

celery = Celery(
    "xplain_screening",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.screening_tasks"],
)

celery.conf.update(
    task_acks_late=True,            # redeliver if the worker dies mid-batch
    worker_prefetch_multiplier=1,
    task_track_started=True,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
)


@worker_process_init.connect
def _init_worker(**_kwargs) -> None:
    """Warm the process-local CLIP singleton once per worker process."""
    from app.services.clip_provider import get_clip

    get_clip()
