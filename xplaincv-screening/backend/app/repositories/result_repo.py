"""Data access for verification results."""

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.models import VerificationResult


class ResultRepo:
    def __init__(self, db: Session) -> None:
        self.db = db

    def bulk_insert(self, results: list[VerificationResult]) -> None:
        self.db.add_all(results)

    def delete_for_batch(self, batch_id: int) -> None:
        """Idempotency: clear earlier partial results before a task (re)runs."""
        self.db.execute(
            delete(VerificationResult).where(VerificationResult.batch_id == batch_id)
        )

    def get(self, result_id: int) -> VerificationResult | None:
        return self.db.get(VerificationResult, result_id)

    def page_for_batch(self, batch_id: int, page: int,
                       page_size: int) -> tuple[list[VerificationResult], int]:
        total = self.db.scalar(
            select(func.count())
            .select_from(VerificationResult)
            .where(VerificationResult.batch_id == batch_id)
        ) or 0
        rows = list(self.db.scalars(
            select(VerificationResult)
            .where(VerificationResult.batch_id == batch_id)
            .order_by(VerificationResult.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ))
        return rows, total
