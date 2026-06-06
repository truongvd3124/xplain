from datetime import datetime

from pydantic import BaseModel

from app.schemas.result import ResultSummary


class BatchCreateResponse(BaseModel):
    batch_id: int
    status: str
    total_images: int


class BatchSummary(BaseModel):
    id: int
    profile_id: int
    profile_name: str
    status: str
    total_images: int
    processed: int
    accepted: int
    rejected: int
    error: str | None
    created_at: datetime


class BatchDetail(BaseModel):
    batch: BatchSummary
    threshold_score: float
    results: list[ResultSummary]
    page: int
    page_size: int
    total_results: int
