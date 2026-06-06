"""Predict mode: upload ONE image, score it against ALL built profiles."""

import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.config import settings
from app.deps import get_clip, get_profile_service
from app.schemas.verify import VerifyResponse
from app.services import predict_service
from app.services.clip_engine import ClipEngine
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/api", tags=["verify"])


@router.post("/verify", response_model=VerifyResponse)
async def verify_image(
    file: UploadFile = File(...),
    clip: ClipEngine = Depends(get_clip),
    profiles: ProfileService = Depends(get_profile_service),
):
    data = await file.read()
    try:
        image = Image.open(io.BytesIO(data)).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(422, f"not a readable image: {file.filename}") from exc

    built = [p for p in profiles.repo.list_all() if p.built_at is not None]
    bundles = [profiles.load_bundle(p.id) for p in built]

    embedding = clip.encode_image(image)
    result = predict_service.predict(
        embedding, bundles, clip.neutral_embedding, clip.logit_scale
    )
    return VerifyResponse(
        **result,
        presence_threshold=settings.PRESENCE_THRESHOLD,
        match_threshold=settings.MATCH_THRESHOLD,
    )
