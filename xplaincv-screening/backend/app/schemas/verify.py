from pydantic import BaseModel

from app.schemas.result import ConceptScoreRow


class CandidateScore(BaseModel):
    profile_id: int
    profile_name: str
    score: float
    concept_score: float
    prototype_score: float | None
    coverage: float
    num_present: int
    num_concepts: int
    passes_gate: bool
    concepts: list[ConceptScoreRow]


class VerifyResponse(BaseModel):
    match: CandidateScore | None        # None => no profile passed the gate
    candidates: list[CandidateScore]    # all built profiles, ranked by score
    presence_threshold: float
    match_threshold: float
