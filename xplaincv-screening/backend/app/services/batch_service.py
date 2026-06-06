"""Batch lifecycle: create + enqueue, list, detail."""

from app.config import settings
from app.db.models import ScreeningBatch
from app.repositories.batch_repo import BatchRepo
from app.repositories.profile_repo import ProfileRepo
from app.repositories.result_repo import ResultRepo
from app.schemas.batch import BatchCreateResponse, BatchDetail, BatchSummary
from app.schemas.result import ResultSummary
from app.services.profile_service import ProfileNotBuiltError, ProfileNotFoundError
from app.storage import local as storage


class BatchNotFoundError(LookupError):
    pass


class BatchService:
    def __init__(self, batch_repo: BatchRepo, result_repo: ResultRepo,
                 profile_repo: ProfileRepo) -> None:
        self.batches = batch_repo
        self.results = result_repo
        self.profiles = profile_repo

    def create(self, profile_id: int,
               files: list[tuple[str | None, bytes]]) -> BatchCreateResponse:
        profile = self.profiles.get(profile_id)
        if profile is None:
            raise ProfileNotFoundError(f"profile {profile_id} not found")
        if profile.built_at is None:
            raise ProfileNotBuiltError(
                f"profile {profile_id} must be built before screening"
            )
        if not files:
            raise ValueError("no images supplied")
        if len(files) > settings.MAX_BATCH_IMAGES:
            raise ValueError(
                f"batch too large: {len(files)} > {settings.MAX_BATCH_IMAGES}"
            )

        batch = self.batches.create(profile_id=profile_id, total_images=0)

        saved = 0
        for filename, data in files:
            try:
                storage.save_batch_image(batch.id, filename, data)
                saved += 1
            except storage.InvalidImageError:
                continue  # unreadable upload — skip silently, count below
        self.batches.set_total(batch.id, saved)

        # Imported lazily: the API process must not pull in the worker's CLIP
        # loading path at import time.
        from app.tasks.screening_tasks import screen_batch
        screen_batch.delay(batch.id)

        return BatchCreateResponse(batch_id=batch.id, status="pending",
                                   total_images=saved)

    def list_all(self) -> list[BatchSummary]:
        return [self._to_summary(b) for b in self.batches.list_all()]

    def get_detail(self, batch_id: int, page: int, page_size: int) -> BatchDetail:
        batch = self.batches.get(batch_id)
        if batch is None:
            raise BatchNotFoundError(f"batch {batch_id} not found")
        rows, total = self.results.page_for_batch(batch_id, page, page_size)
        profile = self.profiles.get(batch.profile_id)
        return BatchDetail(
            batch=self._to_summary(batch),
            threshold_score=profile.threshold_score if profile else 0.0,
            results=[
                ResultSummary(
                    id=r.id,
                    batch_id=r.batch_id,
                    image_url=r.image_url,
                    final_decision=r.final_decision.value,
                    confidence_score=r.confidence_score,
                    reject_reason=r.reject_reason,
                )
                for r in rows
            ],
            page=page,
            page_size=page_size,
            total_results=total,
        )

    def _to_summary(self, batch: ScreeningBatch) -> BatchSummary:
        counts = self.batches.decision_counts(batch.id)
        return BatchSummary(
            id=batch.id,
            profile_id=batch.profile_id,
            profile_name=batch.profile.name if batch.profile else "?",
            status=batch.status.value,
            total_images=batch.total_images,
            processed=batch.processed,
            accepted=counts.get("ACCEPTED", 0),
            rejected=counts.get("REJECTED", 0),
            error=batch.error,
            created_at=batch.created_at,
        )
