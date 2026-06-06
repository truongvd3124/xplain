import redis as redis_lib
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.deps import get_llm
from app.services.llm import LLMProvider

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db), llm: LLMProvider = Depends(get_llm)):
    db_ok = redis_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
    try:
        redis_lib.Redis.from_url(settings.REDIS_URL, socket_timeout=2).ping()
        redis_ok = True
    except Exception:
        pass
    return {
        "status": "ok" if (db_ok and redis_ok) else "degraded",
        "db": db_ok,
        "redis": redis_ok,
        "llm_available": llm.is_available(),
        "clip_backbone": settings.CLIP_BACKBONE,
    }
