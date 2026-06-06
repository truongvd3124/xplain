import asyncio
import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Classification
from app.schemas import ClassifyResponse

router = APIRouter(prefix="/api", tags=["classify"])

ALLOWED_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/bmp",
    "image/tiff",
    "image/avif",
}
VALID_MODES = {"auto", "manual", "hybrid"}


def _parse(text: str) -> list[str]:
    return [x.strip() for x in text.split(",") if x.strip()]


@router.post("/classify", response_model=ClassifyResponse)
async def classify(
    request: Request,
    mode: str = Form(...),
    image: UploadFile = File(...),
    dataset: str = Form(""),
    concepts: str = Form(""),
    labels: str = Form(""),
    alpha: float = Form(0.5),
    db: Session = Depends(get_db),
):
    if mode not in VALID_MODES:
        raise HTTPException(400, f"Invalid mode: {mode}")
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Unsupported image type: {image.content_type}")

    concept_list = _parse(concepts)
    label_list = _parse(labels)
    service = request.app.state.xplain_service

    if mode == "auto" and not dataset:
        raise HTTPException(400, "Auto mode requires dataset")
    if mode == "manual":
        if not concept_list:
            raise HTTPException(400, "Manual mode requires concepts")
        if len(label_list) < 2:
            raise HTTPException(400, "Manual mode requires at least 2 labels")
    if mode == "hybrid":
        if not dataset:
            raise HTTPException(400, "Hybrid mode requires dataset")
        if not concept_list:
            raise HTTPException(400, "Hybrid mode requires user concepts")
    if len(concept_list) > 50 or len(label_list) > 50:
        raise HTTPException(400, "Maximum 50 concepts/labels allowed")

    ext = Path(image.filename or "upload.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    filepath = settings.UPLOAD_DIR / filename
    filepath.write_bytes(await image.read())

    try:
        pil_image = Image.open(filepath).convert("RGB")
        if mode == "auto":
            result = await asyncio.to_thread(service.classify_auto, pil_image, dataset)
        elif mode == "manual":
            result = await asyncio.to_thread(
                service.classify_manual, pil_image, concept_list, label_list
            )
        else:
            result = await asyncio.to_thread(
                service.classify_hybrid, pil_image, concept_list, dataset, alpha
            )
    except Exception as e:
        filepath.unlink(missing_ok=True)
        raise HTTPException(500, f"Inference failed: {e}")

    record = Classification(
        mode=mode,
        image_filename=filename,
        original_filename=image.filename or "unknown",
        predicted_class=result["predicted_class"],
        confidence=result["confidence"],
        feat_gap=result["feat_gap"],
        result_json=json.dumps(result),
        inference_time_ms=result["inference_time_ms"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return ClassifyResponse(
        id=record.id,
        image_url=f"/uploads/{filename}",
        created_at=record.created_at,
        **result,
    )
