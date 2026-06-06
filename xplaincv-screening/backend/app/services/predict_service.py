"""Predict mode (ported from xplaincv-mvp's verify): one image, ALL profiles.

Every built profile is scored as a candidate and ranked by blended score.
The match is the best-ranked candidate that clears the two-evidence gate:

    score >= MATCH_THRESHOLD
    concept_score >= CONCEPT_FLOOR
    coverage >= COVERAGE_FLOOR
    prototype_score >= PROTOTYPE_FLOOR   (only when the profile has references)

No candidate passes -> no_match (open-set rejection).
"""

import numpy as np

from app.config import settings
from app.services import screening_service
from app.services.profile_service import ProfileBundle


def passes_gate(ev: dict, has_references: bool) -> bool:
    if ev["final"] < settings.MATCH_THRESHOLD:
        return False
    if ev["concept_score"] < settings.CONCEPT_FLOOR:
        return False
    if ev["coverage"] < settings.COVERAGE_FLOOR:
        return False
    if has_references and (ev["prototype_score"] or 0.0) < settings.PROTOTYPE_FLOOR:
        return False
    return True


def predict(image_embedding: np.ndarray, bundles: list[ProfileBundle],
            clip_neutral: np.ndarray, logit_scale: float) -> dict:
    candidates = []
    for bundle in bundles:
        ev = screening_service.evaluate(
            image_embedding, bundle, clip_neutral, logit_scale
        )
        candidates.append({
            "profile_id": bundle.profile_id,
            "profile_name": bundle.name,
            "score": round(ev["final"], 4),
            "concept_score": round(ev["concept_score"], 4),
            "prototype_score": (
                round(ev["prototype_score"], 4)
                if ev["prototype_score"] is not None else None
            ),
            "coverage": round(ev["coverage"], 4),
            "num_present": ev["num_present"],
            "num_concepts": len(ev["rows"]),
            "passes_gate": passes_gate(ev, bundle.has_references),
            "concepts": ev["rows"],
        })

    candidates.sort(key=lambda c: c["score"], reverse=True)
    match = next((c for c in candidates if c["passes_gate"]), None)
    return {"match": match, "candidates": candidates}
