from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.deps import get_concept_service, get_profile_service
from app.schemas.concept import ExtractRequest, ExtractResponse
from app.schemas.profile import ProfileCreate, ProfileDetail, ProfileSummary
from app.services.concept_service import ConceptService
from app.services.llm.base import LlmExtractionError
from app.services.profile_service import ProfileNotFoundError, ProfileService

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


@router.post("/extract-concepts", response_model=ExtractResponse)
def extract_concepts(
    payload: ExtractRequest,
    service: ConceptService = Depends(get_concept_service),
):
    if not service.llm.is_available():
        raise HTTPException(503, "LLM provider is not configured (no API key); "
                                 "enter concepts manually instead")
    try:
        return service.extract(payload.name, payload.description)
    except LlmExtractionError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.get("", response_model=list[ProfileSummary])
def list_profiles(service: ProfileService = Depends(get_profile_service)):
    return service.list_all()


@router.post("", response_model=ProfileDetail, status_code=201)
def create_profile(
    payload: ProfileCreate,
    service: ProfileService = Depends(get_profile_service),
):
    return service.create(payload)


@router.get("/{profile_id}", response_model=ProfileDetail)
def get_profile(
    profile_id: int,
    service: ProfileService = Depends(get_profile_service),
):
    try:
        return service.to_detail(service.get(profile_id))
    except ProfileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.delete("/{profile_id}", status_code=204)
def delete_profile(
    profile_id: int,
    service: ProfileService = Depends(get_profile_service),
):
    try:
        service.delete(profile_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/{profile_id}/reference-images", response_model=ProfileDetail)
async def add_reference_images(
    profile_id: int,
    files: list[UploadFile] = File(...),
    service: ProfileService = Depends(get_profile_service),
):
    payload = [(f.filename, await f.read()) for f in files]
    try:
        return service.add_reference_images(profile_id, payload)
    except ProfileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc


@router.post("/{profile_id}/build", response_model=ProfileDetail)
def build_profile(
    profile_id: int,
    service: ProfileService = Depends(get_profile_service),
):
    try:
        return service.build(profile_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
