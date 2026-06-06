"""FastAPI entry point.

CLIP is loaded once in the lifespan and pinned to app.state; heavy batch work
never runs here — it is enqueued to the Celery worker.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import batches, health, profiles, results, verify
from app.services.clip_provider import get_clip

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.clip = get_clip()
    yield


app = FastAPI(
    title="XplainScreen — Explainable Automated Image Screening",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(profiles.router)
app.include_router(batches.router)
app.include_router(results.router)
app.include_router(verify.router)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/refs", StaticFiles(directory=settings.REF_DIR), name="refs")
