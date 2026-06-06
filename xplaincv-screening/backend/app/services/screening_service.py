"""Per-image ACCEPT/REJECT decision with concept-level explanation.

ACCEPTED requires BOTH:
  - final score >= profile.threshold_score
  - coverage (fraction of concepts present) >= COVERAGE_FLOOR

reject_reason names the lowest-probability missing concepts so the user sees
*why* an image failed, not just that it failed.
"""

from dataclasses import dataclass, field

import numpy as np

from app.config import settings
from app.services import scoring
from app.services.profile_service import ProfileBundle


@dataclass
class ScreeningOutcome:
    final_decision: str               # "ACCEPTED" | "REJECTED"
    confidence_score: float
    reject_reason: str | None
    concept_scores: dict = field(default_factory=dict)  # JSONB payload


def evaluate(image_embedding: np.ndarray, bundle: ProfileBundle,
             clip_neutral: np.ndarray, logit_scale: float) -> dict:
    """Pure scoring of one image against one profile — no decision.

    Shared by screening (decide) and predict mode (/api/verify).
    """
    probabilities = scoring.concept_probabilities(
        image_embedding, bundle.concept_embeddings, clip_neutral, logit_scale
    )
    c_score = scoring.concept_score(probabilities, bundle.weights)
    p_score = (
        scoring.prototype_score(image_embedding, bundle.prototype,
                                bundle.proto_lo, bundle.proto_hi)
        if bundle.has_references else None
    )
    final = scoring.blend(c_score, p_score or 0.0, bundle.has_references,
                          settings.CONCEPT_WEIGHT)

    rows = [
        {
            "concept": c["concept"],
            "weight": c["weight"],
            "probability": round(float(p), 4),
            "present": bool(p >= settings.PRESENCE_THRESHOLD),
        }
        for c, p in zip(bundle.concepts, probabilities)
    ]
    num_present = sum(r["present"] for r in rows)
    coverage = num_present / len(rows) if rows else 0.0

    return {
        "final": float(final),
        "concept_score": float(c_score),
        "prototype_score": float(p_score) if p_score is not None else None,
        "coverage": coverage,
        "num_present": num_present,
        "rows": rows,
    }


def decide(image_embedding: np.ndarray, bundle: ProfileBundle,
           clip_neutral: np.ndarray, logit_scale: float) -> ScreeningOutcome:
    ev = evaluate(image_embedding, bundle, clip_neutral, logit_scale)
    final, c_score, p_score = ev["final"], ev["concept_score"], ev["prototype_score"]
    rows, coverage = ev["rows"], ev["coverage"]

    accepted = (final >= bundle.threshold_score
                and coverage >= settings.COVERAGE_FLOOR)

    return ScreeningOutcome(
        final_decision="ACCEPTED" if accepted else "REJECTED",
        confidence_score=round(float(final), 4),
        reject_reason=None if accepted else _reject_reason(
            rows, final, coverage, bundle.threshold_score
        ),
        concept_scores={
            "concept_score": round(c_score, 4),
            "prototype_score": round(p_score, 4) if p_score is not None else None,
            "coverage": round(coverage, 4),
            "concepts": rows,
        },
    )


def _reject_reason(rows: list[dict], final: float, coverage: float,
                   threshold: float) -> str:
    missing = sorted(
        (r for r in rows if not r["present"]),
        key=lambda r: r["probability"],
    )[: settings.MAX_REJECT_REASON_CONCEPTS]

    parts: list[str] = []
    if final < threshold:
        parts.append(f"score {final:.2f} below threshold {threshold:.2f}")
    if coverage < settings.COVERAGE_FLOOR:
        parts.append(
            f"only {coverage:.0%} of expected concepts detected"
            f" (minimum {settings.COVERAGE_FLOOR:.0%})"
        )
    if missing:
        names = ", ".join(r["concept"] for r in missing)
        parts.append(f"missing: {names}")
    return "; ".join(parts) if parts else "score below threshold"


def error_outcome(message: str) -> ScreeningOutcome:
    """Recorded when one image cannot be processed; the batch continues."""
    return ScreeningOutcome(
        final_decision="REJECTED",
        confidence_score=0.0,
        reject_reason=f"processing error: {message}",
        concept_scores={"concept_score": 0.0, "prototype_score": None,
                        "coverage": 0.0, "concepts": [], "error": message},
    )
