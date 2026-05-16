"""Pydantic request/response models for the API layer."""

from pydantic import BaseModel

class ConceptItem(BaseModel):
    """One visual concept and its importance (1-5)."""

    concept: str
    importance: int = 3


class ExtractResponse(BaseModel):
    """Result of LLM concept extraction (Builder, step 1)."""

    concepts: list[ConceptItem]
    source: str  # "llm" or "unavailable"


class ProfileSummary(BaseModel):
    """Lightweight profile info for list views."""

    id: str
    class_name: str
    description: str
    num_concepts: int
    num_references: int
    created_at: str


class CalibrationInfo(BaseModel):
    method: str
    proto_lo: float
    proto_hi: float
    ref_scores: list[float]


class ProfileDetail(ProfileSummary):
    """Full profile info, including concepts and calibration."""

    concepts: list[ConceptItem]
    calibration: CalibrationInfo


# Verification


class ConceptPresence(BaseModel):
    """How strongly one concept was detected in the verified image."""

    concept: str
    importance: int
    probability: float
    present: bool


class CandidateScore(BaseModel):
    """One profile's score for an uploaded image (no per-concept rows)."""

    profile_id: str
    class_name: str
    score: float
    concept_score: float
    prototype_score: float | None = None
    num_present: int
    num_concepts: int


class VerifyResponse(BaseModel):
    """Predict-mode outcome: the best-matching class (or no match)."""

    decision: str                              # "match" | "no_match"
    predicted: CandidateScore | None = None    # winning profile, if any
    concepts: list[ConceptPresence] = []       # breakdown for the winner
    ranking: list[CandidateScore]              # every profile, sorted desc
    threshold: float                           # global MATCH_THRESHOLD
    image_url: str
    inference_time_ms: int
