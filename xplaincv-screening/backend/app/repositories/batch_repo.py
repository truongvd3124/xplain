"""Data access for screening batches."""

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db.models import BatchStatus, Decision, ScreeningBatch, VerificationResult


class BatchRepo:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, profile_id: int, total_images: int) -> ScreeningBatch:
        batch = ScreeningBatch(profile_id=profile_id, total_images=total_images)
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def get(self, batch_id: int) -> ScreeningBatch | None:
        return self.db.get(ScreeningBatch, batch_id)

    def list_all(self) -> list[ScreeningBatch]:
        return list(self.db.scalars(
            select(ScreeningBatch).order_by(ScreeningBatch.created_at.desc())
        ))

    def set_total(self, batch_id: int, total: int) -> None:
        self.db.execute(
            update(ScreeningBatch)
            .where(ScreeningBatch.id == batch_id)
            .values(total_images=total)
        )
        self.db.commit()

    def set_status(self, batch_id: int, status: BatchStatus,
                   error: str | None = None) -> None:
        self.db.execute(
            update(ScreeningBatch)
            .where(ScreeningBatch.id == batch_id)
            .values(status=status, error=error)
        )

    def set_processed(self, batch_id: int, processed: int) -> None:
        self.db.execute(
            update(ScreeningBatch)
            .where(ScreeningBatch.id == batch_id)
            .values(processed=processed)
        )

    def decision_counts(self, batch_id: int) -> dict[str, int]:
        rows = self.db.execute(
            select(VerificationResult.final_decision, func.count())
            .where(VerificationResult.batch_id == batch_id)
            .group_by(VerificationResult.final_decision)
        ).all()
        counts = {d.value: 0 for d in Decision}
        for decision, count in rows:
            counts[decision.value] = count
        return counts
