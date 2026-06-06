"""FastAPI entry point. CLIP loads once at startup, shared via app.state.clip."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.clip_engine import ClipEngine
from app.config import settings
from app.routers import profiles, verify
from app.services import llm_extract

_UPLOAD_DIR = settings.DATA_DIR / "uploads"
_PROFILES_DIR = settings.DATA_DIR / "profiles"

# Storage folders must exist before StaticFiles is mounted (below).
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
_PROFILES_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.clip = ClipEngine(settings.CLIP_BACKBONE)
    yield


app = FastAPI(title="XplainCV MVP", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Verified-image uploads, served statically so the UI can show them back.
app.mount("/uploads", StaticFiles(directory=str(_UPLOAD_DIR)), name="uploads")

app.include_router(profiles.router)
app.include_router(verify.router)


@app.get("/api/health")
def health():
    """Liveness probe; also reports whether AI extraction is configured."""
    return {"status": "ok", "llm_available": llm_extract.is_available()}
