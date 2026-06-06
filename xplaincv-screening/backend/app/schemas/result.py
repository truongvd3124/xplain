from pydantic import BaseModel


class ConceptScoreRow(BaseModel):
    concept: str
    weight: float
    probability: float
    present: bool


class ResultSummary(BaseModel):
    id: int
    batch_id: int
    image_url: str
    final_decision: str
    confidence_score: float
    reject_reason: str | None


class ResultDetail(ResultSummary):
    profile_id: int
    profile_name: str
    threshold_score: float
    presence_threshold: float
    concept_score: float
    prototype_score: float | None
    coverage: float
    concepts: list[ConceptScoreRow]
