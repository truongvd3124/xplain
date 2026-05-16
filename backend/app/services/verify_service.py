"""Score an image against a class profile.

Two evidence sources, blended:

  1. Concept evidence:
       P(concept) = sigmoid(logit_scale * (sim_concept - sim_neutral))
       concept_score = average of those probabilities
  2. Prototype evidence: cosine(image, mean reference embedding).

  score = CONCEPT_WEIGHT * concept_score + (1 - CONCEPT_WEIGHT) * proto_score
        = concept_score                    (profile has no reference images)
"""

import numpy as np

from app.clip_engine import ClipEngine
from app.config import settings
from app.services.profile_store import Profile

_CONCEPT_PROMPT = "a photo of {concept}"
_NEUTRAL_PROMPT = "a photo"

# Neutral-baseline embedding, cached after the first request.
_neutral_embedding: np.ndarray | None = None


def encode_concepts(clip: ClipEngine, concepts: list[dict]) -> np.ndarray:
    prompts = [_CONCEPT_PROMPT.format(concept=c["concept"]) for c in concepts]
    return clip.encode_texts(prompts)


def _neutral(clip: ClipEngine) -> np.ndarray:
    global _neutral_embedding
    if _neutral_embedding is None:
        _neutral_embedding = clip.encode_texts([_NEUTRAL_PROMPT])[0]
    return _neutral_embedding


def _concept_probabilities(clip: ClipEngine, image: np.ndarray,
                            concept_embeddings: np.ndarray) -> np.ndarray:
    """Per-concept presence probabilities for one image, shape (N,)."""
    if concept_embeddings.shape[0] == 0:
        return np.zeros((0,), dtype=np.float32)
    sim_concept = concept_embeddings @ image
    sim_neutral = float(_neutral(clip) @ image)
    logits = clip.logit_scale * (sim_concept - sim_neutral)
    return _sigmoid(logits)


def _concept_score(probabilities: np.ndarray) -> float:
    if probabilities.size == 0:
        return 0.0
    return float(probabilities.mean())


def _prototype_score(image: np.ndarray, prototype: np.ndarray) -> float:
    """Cosine similarity between the image and the prototype, clipped to [0, 1]."""
    raw = float(prototype @ image)
    return float(np.clip(raw, 0.0, 1.0))


def _blend(concept_score: float, prototype_score: float,
           has_references: bool) -> float:
    if not has_references:
        return concept_score
    w = settings.CONCEPT_WEIGHT
    return w * concept_score + (1.0 - w) * prototype_score


def calibrate(clip: ClipEngine, concept_embeddings: np.ndarray,
              concepts: list[dict], ref_embeddings: np.ndarray) -> dict:
    """Placeholder calibration; the prototype window is not tuned yet."""
    return {
        "method": "default",
        "proto_lo": 0.0,
        "proto_hi": 1.0,
        "ref_scores": [],
    }


def score(clip: ClipEngine, image: np.ndarray, profile: Profile) -> dict:
    """Score one already-embedded image against one profile (no decision)."""
    has_refs = profile.num_references > 0

    probabilities = _concept_probabilities(clip, image, profile.concept_embeddings)
    concept_score = _concept_score(probabilities)
    prototype_score = (
        _prototype_score(image, profile.prototype) if has_refs else 0.0
    )
    final = _blend(concept_score, prototype_score, has_refs)

    presence_cutoff = settings.PRESENCE_THRESHOLD
    concept_rows = [
        {
            "concept": c["concept"],
            "importance": c["importance"],
            "probability": round(float(p), 4),
            "present": bool(p >= presence_cutoff),
        }
        for c, p in zip(profile.concepts, probabilities)
    ]
    return {
        "profile_id": profile.id,
        "class_name": profile.class_name,
        "score": round(final, 4),
        "concept_score": round(concept_score, 4),
        "prototype_score": round(prototype_score, 4) if has_refs else None,
        "num_present": sum(r["present"] for r in concept_rows),
        "num_concepts": len(concept_rows),
        "concepts": concept_rows,
    }


def _sigmoid(x: np.ndarray) -> np.ndarray:
    """Numerically stable logistic sigmoid."""
    return np.where(x >= 0, 1.0 / (1.0 + np.exp(-x)),
                    np.exp(x) / (1.0 + np.exp(x)))
