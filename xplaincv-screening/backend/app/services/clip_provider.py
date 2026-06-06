"""Process-local ClipEngine singleton.

Both entry points resolve the model through here:
  - FastAPI: lifespan() calls get_clip() once and pins it to app.state.clip
  - Celery:  worker_process_init signal calls get_clip() post-fork
"""

import logging

from app.config import settings
from app.services.clip_engine import ClipEngine

logger = logging.getLogger(__name__)

_clip: ClipEngine | None = None


def get_clip() -> ClipEngine:
    global _clip
    if _clip is None:
        logger.info("Loading CLIP %s ...", settings.CLIP_BACKBONE)
        _clip = ClipEngine(settings.CLIP_BACKBONE)
        _clip.neutral_embedding  # warm the neutral-prompt cache
        logger.info(
            "CLIP %s loaded on %s (embed_dim=%d)",
            settings.CLIP_BACKBONE, _clip.device, _clip.embed_dim,
        )
    return _clip
