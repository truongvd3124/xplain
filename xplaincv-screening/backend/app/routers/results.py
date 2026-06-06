from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.repositories.result_repo import ResultRepo
from app.schemas.result import ConceptScoreRow, ResultDetail

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("/{result_id}", response_model=ResultDetail)
def get_result(result_id: int, db: Session = Depends(get_db)):
    result = ResultRepo(db).get(result_id)
    if result is None:
        raise HTTPException(404, f"result {result_id} not found")

    profile = result.batch.profile
    scores = result.concept_scores or {}
    return ResultDetail(
        id=result.id,
        batch_id=result.batch_id,
        image_url=result.image_url,
        final_decision=result.final_decision.value,
        confidence_score=result.confidence_score,
        reject_reason=result.reject_reason,
        profile_id=profile.id,
        profile_name=profile.name,
        threshold_score=profile.threshold_score,
        presence_threshold=settings.PRESENCE_THRESHOLD,
        concept_score=scores.get("concept_score", 0.0),
        prototype_score=scores.get("prototype_score"),
        coverage=scores.get("coverage", 0.0),
        concepts=[ConceptScoreRow(**row) for row in scores.get("concepts", [])],
    )
