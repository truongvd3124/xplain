"""POST /api/verify -- predict the best-matching class for an uploaded image."""

import io
import time
import uuid

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from PIL import Image, UnidentifiedImageError

from app.config import settings
from app.routers.profiles import ALLOWED_IMAGE_TYPES, _extension
from app.schemas import CandidateScore, VerifyResponse
from app.services import profile_store, verify_service

router = APIRouter(prefix="/api", tags=["verify"])

_UPLOAD_DIR = settings.DATA_DIR / "uploads"


@router.post("/verify", response_model=VerifyResponse)
async def verify_image(request: Request, image: UploadFile = File(...)):
    """Score the image against every stored profile and return the best match."""
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, f"Unsupported image type: {image.content_type}")

    summaries = profile_store.list_profiles()
    if not summaries:
        raise HTTPException(
            400, "Chưa có profile nào — hãy tạo một profile bên tab Builder."
        )

    blob = await image.read()
    try:
        pil = Image.open(io.BytesIO(blob)).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(400, "Cannot read the uploaded image")

    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}{_extension(image.content_type)}"
    (_UPLOAD_DIR / filename).write_bytes(blob)

    clip = request.app.state.clip
    start = time.time()
    embedding = clip.encode_image(pil)

    ranking: list[CandidateScore] = []
    concept_rows_by_id: dict[str, list[dict]] = {}
    for summary in summaries:
        profile = profile_store.load_profile(summary["id"])
        scored = verify_service.score(clip, embedding, profile)
        concept_rows_by_id[scored["profile_id"]] = scored["concepts"]
        ranking.append(CandidateScore(
            profile_id=scored["profile_id"],
            class_name=scored["class_name"],
            score=scored["score"],
            concept_score=scored["concept_score"],
            prototype_score=scored["prototype_score"],
            num_present=scored["num_present"],
            num_concepts=scored["num_concepts"],
        ))

    ranking.sort(key=lambda c: c.score, reverse=True)
    elapsed_ms = int((time.time() - start) * 1000)

    # Highest-scoring candidate that clears the gate; scanning past ranking[0]
    # lets a cleaner runner-up win over a strong-but-unbalanced top score.
    winner = next((c for c in ranking if _passes_gate(c)), None)

    return VerifyResponse(
        decision="match" if winner else "no_match",
        predicted=winner,
        concepts=concept_rows_by_id[winner.profile_id] if winner else [],
        ranking=ranking,
        threshold=settings.MATCH_THRESHOLD,
        image_url=f"/uploads/{filename}",
        inference_time_ms=elapsed_ms,
    )


def _passes_gate(c: CandidateScore) -> bool:
    """Match only if every evidence source clears its own floor."""
    if c.score < settings.MATCH_THRESHOLD:
        return False
    if c.concept_score < settings.CONCEPT_FLOOR:
        return False
    # Breadth, not just a high average: enough concepts individually present.
    if c.num_concepts > 0:
        coverage = c.num_present / c.num_concepts
        if coverage < settings.COVERAGE_FLOOR:
            return False
    if c.prototype_score is not None and c.prototype_score < settings.PROTOTYPE_FLOOR:
        return False
    return True
