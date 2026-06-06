"""Pure ZCBM scoring math — ported verbatim from xplaincv-mvp verify_service.py.

Two independent evidence sources, blended:

  1. Concept evidence:
       P(concept) = sigmoid(logit_scale * (sim_concept - sim_neutral))
       concept_score = importance-weighted average of those probabilities
  2. Prototype evidence: cosine(image, mean reference embedding) mapped onto
     [0, 1] with the window calibrated at build time (leave-one-out, >=3 refs).

  score = concept_weight * concept_score + (1 - concept_weight) * proto_score
        = concept_score                    (profile has no reference images)

Framework-free: numpy in, numbers out. No CLIP, no DB, no decision here.
"""

import numpy as np

__all__ = [
    "sigmoid",
    "concept_probabilities",
    "concept_score",
    "prototype_score",
    "blend",
    "build_prototype",
    "calibrate",
]


def sigmoid(x: np.ndarray) -> np.ndarray:
    """Numerically stable logistic sigmoid."""
    return np.where(x >= 0, 1.0 / (1.0 + np.exp(-x)),
                    np.exp(x) / (1.0 + np.exp(x)))


def concept_probabilities(
    image: np.ndarray,
    concept_embeddings: np.ndarray,
    neutral_embedding: np.ndarray,
    logit_scale: float,
) -> np.ndarray:
    """Per-concept presence probabilities for one image, shape (N,)."""
    if concept_embeddings.shape[0] == 0:
        return np.zeros((0,), dtype=np.float32)
    sim_concept = concept_embeddings @ image
    sim_neutral = float(neutral_embedding @ image)
    logits = logit_scale * (sim_concept - sim_neutral)
    return sigmoid(logits)


def concept_score(probabilities: np.ndarray, weights: np.ndarray) -> float:
    """Importance-weighted average of the presence probabilities."""
    if probabilities.size == 0 or weights.sum() == 0:
        return 0.0
    return float(np.dot(probabilities, weights) / weights.sum())


def prototype_score(image: np.ndarray, prototype: np.ndarray,
                    proto_lo: float, proto_hi: float) -> float:
    """Map cosine(image, prototype) onto [0, 1] via the calibrated window."""
    raw = float(prototype @ image)
    span = max(proto_hi - proto_lo, 1e-6)
    return float(np.clip((raw - proto_lo) / span, 0.0, 1.0))


def blend(c_score: float, p_score: float, has_references: bool,
          concept_weight: float) -> float:
    if not has_references:
        return c_score
    return concept_weight * c_score + (1.0 - concept_weight) * p_score


def build_prototype(ref_embeddings: np.ndarray) -> np.ndarray:
    """Mean reference embedding, re-normalised."""
    return _mean_normalised(ref_embeddings)


def calibrate(
    concept_embeddings: np.ndarray,
    weights: np.ndarray,
    ref_embeddings: np.ndarray,
    neutral_embedding: np.ndarray,
    logit_scale: float,
    concept_weight: float,
) -> dict:
    """Derive the prototype-similarity window [proto_lo, proto_hi].

    With >=3 references: leave-one-out — each reference is scored against a
    prototype built from the others; those similarities define the window.
    With fewer references the window stays at the full [0, 1] range.
    `ref_scores` is kept as diagnostics only.
    """
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
        probs = concept_probabilities(
            ref_embeddings[k], concept_embeddings, neutral_embedding, logit_scale
        )
        c_score = concept_score(probs, weights)
        p_score = prototype_score(ref_embeddings[k], loo_protos[k],
                                  proto_lo, proto_hi)
        ref_scores.append(blend(c_score, p_score, True, concept_weight))

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
