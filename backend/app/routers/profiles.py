"""Profile endpoints -- the "Builder" half of the app.

    POST   /api/extract           description  -> AI-suggested concepts
    GET    /api/profiles          list every stored profile
    GET    /api/profiles/{id}     one profile in detail
    POST   /api/profiles          create/replace a profile (concepts + images)
    DELETE /api/profiles/{id}     remove a profile
"""

import io
import json

import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel

from app.schemas import ExtractResponse, ProfileDetail, ProfileSummary
from app.services import llm_extract, profile_store, verify_service
from app.services.profile_store import Profile

router = APIRouter(prefix="/api", tags=["profiles"])

ALLOWED_IMAGE_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/bmp", "image/avif",
}
MAX_REFERENCE_IMAGES = 15


class ExtractRequest(BaseModel):
    class_name: str
    description: str


@router.post("/extract", response_model=ExtractResponse)
def extract(body: ExtractRequest):
    """Suggest visual concepts from a free-text description using the LLM.

    Without an API key this returns ``source = "unavailable"`` so the UI
    can fall back to manual entry.
    """
    if not body.description.strip():
        raise HTTPException(400, "Description is required")

    if not llm_extract.is_available():
        return ExtractResponse(concepts=[], source="unavailable")

    try:
        concepts = llm_extract.extract_concepts(body.class_name, body.description)
    except llm_extract.LlmExtractionError as exc:
        raise HTTPException(502, f"Concept extraction failed: {exc}")

    return ExtractResponse(concepts=concepts, source="llm")


@router.get("/profiles", response_model=list[ProfileSummary])
def list_profiles():
    return profile_store.list_profiles()


@router.get("/profiles/{profile_id}", response_model=ProfileDetail)
def get_profile(profile_id: str):
    try:
        profile = profile_store.load_profile(profile_id)
    except FileNotFoundError:
        raise HTTPException(404, f"Profile not found: {profile_id}")
    return profile.detail()


@router.post("/profiles", response_model=ProfileDetail)
async def create_profile(
    request: Request,
    class_name: str = Form(...),
    description: str = Form(""),
    concepts: str = Form(...),          # JSON array of {concept, importance}
    images: list[UploadFile] = File(default=[]),
):
    """Create (or replace) a profile: embed concepts, build the prototype,
    calibrate the prototype-similarity window, then save to disk."""
    clip = request.app.state.clip

    concept_list = _parse_concepts(concepts)
    if not concept_list:
        raise HTTPException(400, "At least one usable concept is required")

    if len(images) > MAX_REFERENCE_IMAGES:
        raise HTTPException(400, f"At most {MAX_REFERENCE_IMAGES} images allowed")

    ref_blobs, ref_exts, ref_embeddings = await _embed_reference_images(images, clip)

    concept_embeddings = verify_service.encode_concepts(clip, concept_list)
    prototype = _build_prototype(ref_embeddings, clip.embed_dim)
    calibration = verify_service.calibrate(
        clip, concept_embeddings, concept_list, ref_embeddings
    )

    profile = Profile(
        id=profile_store.slugify(class_name),
        class_name=class_name.strip(),
        description=description.strip(),
        concepts=concept_list,
        concept_embeddings=concept_embeddings,
        prototype=prototype,
        ref_embeddings=ref_embeddings,
        calibration=calibration,
    )
    profile_store.save_profile(profile, ref_blobs, ref_exts)
    return profile.detail()


@router.delete("/profiles/{profile_id}")
def delete_profile(profile_id: str):
    if not profile_store.delete_profile(profile_id):
        raise HTTPException(404, f"Profile not found: {profile_id}")
    return {"deleted": profile_id}


# Helpers


def _parse_concepts(raw: str) -> list[dict]:
    """Parse and validate the JSON concept list from the form field."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(400, "`concepts` must be a JSON array")
    if not isinstance(data, list) or not data:
        raise HTTPException(400, "`concepts` must be a non-empty JSON array")

    parsed: list[dict] = []
    for item in data:
        text = str(item.get("concept", "")).strip().lower()
        if not text:
            continue
        importance = item.get("importance", 3)
        try:
            importance = max(1, min(5, int(importance)))
        except (TypeError, ValueError):
            importance = 3
        parsed.append({"concept": text, "importance": importance})
    return parsed


async def _embed_reference_images(
    images: list[UploadFile], clip
) -> tuple[list[bytes], list[str], np.ndarray]:
    """Read, validate and CLIP-embed the uploaded reference images."""
    blobs: list[bytes] = []
    extensions: list[str] = []
    embeddings: list[np.ndarray] = []

    for upload in images:
        if upload.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                400, f"Unsupported image type: {upload.content_type}"
            )
        blob = await upload.read()
        try:
            pil = Image.open(io.BytesIO(blob)).convert("RGB")
        except UnidentifiedImageError:
            raise HTTPException(400, f"Cannot read image: {upload.filename}")
        embeddings.append(clip.encode_image(pil))
        blobs.append(blob)
        extensions.append(_extension(upload.content_type))

    matrix = (
        np.stack(embeddings) if embeddings
        else np.zeros((0, clip.embed_dim), dtype=np.float32)
    )
    return blobs, extensions, matrix


def _build_prototype(ref_embeddings: np.ndarray, embed_dim: int) -> np.ndarray:
    """Average reference embeddings into a unit-length prototype."""
    if ref_embeddings.shape[0] == 0:
        return np.zeros((embed_dim,), dtype=np.float32)
    mean = ref_embeddings.mean(axis=0)
    norm = np.linalg.norm(mean)
    return (mean / norm if norm > 1e-8 else mean).astype(np.float32)


def _extension(content_type: str) -> str:
    """Map an image MIME type to a file extension."""
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/bmp": ".bmp",
        "image/avif": ".avif",
    }.get(content_type, ".img")
