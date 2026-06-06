"""Score an image against a class profile.

Two independent evidence sources, blended:

  1. Concept evidence:
       P(concept) = sigmoid(logit_scale * (sim_concept - sim_neutral))
       concept_score = importance-weighted average of those probabilities
  2. Prototype evidence: cosine(image, mean reference embedding) mapped onto
     [0, 1] with the window calibrated at build time.

  score = CONCEPT_WEIGHT * concept_score + (1 - CONCEPT_WEIGHT) * proto_score
        = concept_score                    (profile has no reference images)

`score()` runs per /verify request; `calibrate()` runs once at build time.
The accept/reject decision lives in the verify router, not here.
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


def _weights(concepts: list[dict]) -> np.ndarray:
    return np.array([float(c.get("importance", 3)) for c in concepts],
                    dtype=np.float32)


def _concept_probabilities(clip: ClipEngine, image: np.ndarray,
                            concept_embeddings: np.ndarray) -> np.ndarray:
    """Per-concept presence probabilities for one image, shape (N,)."""
    if concept_embeddings.shape[0] == 0:
        return np.zeros((0,), dtype=np.float32)
    sim_concept = concept_embeddings @ image
    sim_neutral = float(_neutral(clip) @ image)
    logits = clip.logit_scale * (sim_concept - sim_neutral)
    return _sigmoid(logits)


def _concept_score(probabilities: np.ndarray, weights: np.ndarray) -> float:
    if probabilities.size == 0 or weights.sum() == 0:
        return 0.0
    return float(np.dot(probabilities, weights) / weights.sum())


def _prototype_score(image: np.ndarray, prototype: np.ndarray,
                     proto_lo: float, proto_hi: float) -> float:
    """Map cosine(image, prototype) onto [0, 1] via the calibrated window."""
    raw = float(prototype @ image)
    span = max(proto_hi - proto_lo, 1e-6)
    return float(np.clip((raw - proto_lo) / span, 0.0, 1.0))


def _blend(concept_score: float, prototype_score: float,
           has_references: bool) -> float:
    if not has_references:
        return concept_score
    w = settings.CONCEPT_WEIGHT
    return w * concept_score + (1.0 - w) * prototype_score


def calibrate(clip: ClipEngine, concept_embeddings: np.ndarray,
              concepts: list[dict], ref_embeddings: np.ndarray) -> dict:
    """Derive the prototype-similarity window [proto_lo, proto_hi].

    With >=3 references: leave-one-out -- each reference is scored against a
    prototype built from the others; those similarities define the window.
    With fewer references the window stays at the full [0, 1] range.
    `ref_scores` is kept as diagnostics only.
    """
    weights = _weights(concepts)
    num_refs = int(ref_embeddings.shape[0])

    if num_refs < 3:
        return {
            "method": "default",
            "proto_lo": 0.0,
            "proto_hi": 1.0,
            "ref_scores": [],
        }

    loo_similarities = []
    loo_protos = []
    for k in range(num_refs):
        others = np.delete(ref_embeddings, k, axis=0)
        proto_k = _mean_normalised(others)
        loo_protos.append(proto_k)
        loo_similarities.append(float(proto_k @ ref_embeddings[k]))

    proto_lo, proto_hi = _prototype_window(loo_similarities)

    ref_scores = []
    for k in range(num_refs):
        probs = _concept_probabilities(clip, ref_embeddings[k], concept_embeddings)
        c_score = _concept_score(probs, weights)
        p_score = _prototype_score(ref_embeddings[k], loo_protos[k],
                                   proto_lo, proto_hi)
        ref_scores.append(_blend(c_score, p_score, has_references=True))

    return {
        "method": "leave-one-out",
        "proto_lo": round(proto_lo, 4),
        "proto_hi": round(proto_hi, 4),
        "ref_scores": [round(s, 4) for s in ref_scores],
    }


def _prototype_window(loo_similarities: list[float]) -> tuple[float, float]:
    arr = np.asarray(loo_similarities, dtype=np.float64)
    lo = max(0.0, float(arr.min()) - float(arr.std()))
    hi = float(arr.max())
    if hi - lo < 0.05:  # references nearly identical -> widen artificially
        lo, hi = max(0.0, hi - 0.15), hi + 0.02
    return lo, hi


def _mean_normalised(vectors: np.ndarray) -> np.ndarray:
    mean = vectors.mean(axis=0)
    norm = np.linalg.norm(mean)
    return mean / norm if norm > 1e-8 else mean


def score(clip: ClipEngine, image: np.ndarray, profile: Profile) -> dict:
    """Score one already-embedded image against one profile (no decision)."""
    weights = _weights(profile.concepts)
    has_refs = profile.num_references > 0

    probabilities = _concept_probabilities(clip, image, profile.concept_embeddings)
    concept_score = _concept_score(probabilities, weights)
    prototype_score = (
        _prototype_score(image, profile.prototype,
                         profile.calibration["proto_lo"],
                         profile.calibration["proto_hi"])
        if has_refs else 0.0
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
