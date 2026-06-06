import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Classification
from app.schemas import ClassifyResponse, HistoryItem, PaginatedHistory

router = APIRouter(prefix="/api", tags=["history"])


def _to_history_item(row: Classification) -> HistoryItem:
    return HistoryItem(
        id=row.id,
        mode=row.mode,
        predicted_class=row.predicted_class,
        confidence=row.confidence,
        image_url=f"/uploads/{row.image_filename}",
        created_at=row.created_at,
    )


def _to_response(row: Classification) -> ClassifyResponse:
    return ClassifyResponse(
        id=row.id,
        image_url=f"/uploads/{row.image_filename}",
        created_at=row.created_at,
        **json.loads(row.result_json),
    )


@router.get("/history", response_model=PaginatedHistory)
def list_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.query(func.count(Classification.id)).scalar()
    rows = (
        db.query(Classification)
        .order_by(desc(Classification.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedHistory(
        items=[_to_history_item(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/history/{classification_id}", response_model=ClassifyResponse)
def get_classification(classification_id: int, db: Session = Depends(get_db)):
    row = db.query(Classification).filter_by(id=classification_id).first()
    if not row:
        raise HTTPException(404, "Classification not found")
    return _to_response(row)
