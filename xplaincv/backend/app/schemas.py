from typing import Literal, Optional

from pydantic import BaseModel


class ConceptScore(BaseModel):
    name: str
    score: float
    source: Optional[str] = None


class LabelScore(BaseModel):
    name: str
    score: float


class InterventionMetrics(BaseModel):
    user_concept_count: int
    user_concept_active: int
    success_rate: float
    contribution_ratio: float
    alpha: float
    bank_reconstr_norm: float
    user_reconstr_norm: float
    changed_prediction: bool
    confidence_delta: float
    agreement: bool


class BankOnlyPrediction(BaseModel):
    predicted_class: str
    confidence: float


class ClassifyResponse(BaseModel):
    id: int
    mode: Literal["auto", "manual", "hybrid"]
    predicted_class: str
    confidence: float
    feat_gap: float
    concepts: list[ConceptScore]
    user_contributions: Optional[list[ConceptScore]] = None
    dataset: Optional[str] = None
    labels: Optional[list[LabelScore]] = None
    user_concepts: Optional[list[str]] = None
    intervention: Optional[InterventionMetrics] = None
    bank_only: Optional[BankOnlyPrediction] = None
    inference_time_ms: int
    image_url: str
    created_at: str


class DatasetInfo(BaseModel):
    name: str
    display_name: str
    num_classes: int


class HistoryItem(BaseModel):
    id: int
    mode: str
    predicted_class: str
    confidence: float
    image_url: str
    created_at: str


class PaginatedHistory(BaseModel):
    items: list[HistoryItem]
    total: int
    page: int
    page_size: int
