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

    # The top-ranked profile is taken as the prediction.
    winner = ranking[0]

    return VerifyResponse(
        decision="match",
        predicted=winner,
        concepts=concept_rows_by_id[winner.profile_id],
        ranking=ranking,
        threshold=settings.MATCH_THRESHOLD,
        image_url=f"/uploads/{filename}",
        inference_time_ms=elapsed_ms,
    )
