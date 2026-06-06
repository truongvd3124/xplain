"""The batch screening job.

One task per batch: the profile bundle is loaded once, every image is embedded
and decided in a loop, progress is flushed every BATCH_CHUNK_PROGRESS images so
the dashboard's polling sees it move. A failure on one image records a REJECTED
result with the error as the reason — it never kills the batch.
"""

import logging

from app.config import settings
from app.db.models import BatchStatus, Decision, VerificationResult
from app.db.session import SessionLocal
from app.repositories.batch_repo import BatchRepo
from app.repositories.profile_repo import ProfileRepo
from app.repositories.result_repo import ResultRepo
from app.services import screening_service
from app.services.clip_provider import get_clip
from app.services.profile_service import ProfileService
from app.storage import local as storage
from app.tasks.celery_app import celery

logger = logging.getLogger(__name__)


def _list_batch_images(batch_id: int) -> list[str]:
    """Image URLs for a batch, from its upload directory (sorted, stable)."""
    directory = settings.UPLOAD_DIR / str(batch_id)
    if not directory.is_dir():
        return []
    return [f"/uploads/{batch_id}/{p.name}" for p in sorted(directory.iterdir())
            if p.is_file()]


@celery.task(bind=True, name="screen_batch", max_retries=1)
def screen_batch(self, batch_id: int) -> dict:
    db = SessionLocal()
    clip = get_clip()
    batches = BatchRepo(db)
    results = ResultRepo(db)

    try:
        batch = batches.get(batch_id)
        if batch is None:
            logger.error("screen_batch: batch %s not found", batch_id)
            return {"batch_id": batch_id, "error": "not found"}

        batches.set_status(batch_id, BatchStatus.PROCESSING)
        results.delete_for_batch(batch_id)  # idempotent on retry
        db.commit()

        bundle = ProfileService(ProfileRepo(db), clip).load_bundle(batch.profile_id)
        image_urls = _list_batch_images(batch_id)

        pending: list[VerificationResult] = []
        processed = accepted = 0
        for url in image_urls:
            try:
                embedding = clip.encode_image(storage.open_rgb(url))
                outcome = screening_service.decide(
                    embedding, bundle, clip.neutral_embedding, clip.logit_scale
                )
            except Exception as exc:  # noqa: BLE001 — keep the batch alive
                logger.warning("image %s failed: %s", url, exc)
                outcome = screening_service.error_outcome(str(exc))

            pending.append(VerificationResult(
                batch_id=batch_id,
                image_url=url,
                final_decision=Decision(outcome.final_decision),
                confidence_score=outcome.confidence_score,
                reject_reason=outcome.reject_reason,
                concept_scores=outcome.concept_scores,
            ))
            processed += 1
            accepted += outcome.final_decision == "ACCEPTED"

            if processed % settings.BATCH_CHUNK_PROGRESS == 0:
                results.bulk_insert(pending)
                pending = []
                batches.set_processed(batch_id, processed)
                db.commit()

        results.bulk_insert(pending)
        batches.set_processed(batch_id, processed)
        batches.set_status(batch_id, BatchStatus.COMPLETED)
        db.commit()
        logger.info("batch %s completed: %d/%d accepted",
                    batch_id, accepted, processed)
        return {"batch_id": batch_id, "processed": processed, "accepted": accepted}

    except Exception as exc:
        db.rollback()
        logger.exception("batch %s failed", batch_id)
        batches.set_status(batch_id, BatchStatus.FAILED, error=str(exc))
        db.commit()
        raise
    finally:
        db.close()
