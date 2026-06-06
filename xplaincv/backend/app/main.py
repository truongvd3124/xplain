from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
from app.routers import classify, datasets, history
from app.services.xplain_service import XplainService


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    service = XplainService(settings)
    service.load_model()
    app.state.xplain_service = service
    yield


app = FastAPI(title="XplainCV", version="3.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

app.include_router(classify.router)
app.include_router(datasets.router)
app.include_router(history.router)
