from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from app.config import settings
from app.deps import get_batch_service
from app.schemas.batch import BatchCreateResponse, BatchDetail, BatchSummary
from app.services.batch_service import BatchNotFoundError, BatchService
from app.services.profile_service import ProfileNotBuiltError, ProfileNotFoundError

router = APIRouter(prefix="/api/batches", tags=["batches"])


@router.post("", response_model=BatchCreateResponse, status_code=202)
async def create_batch(
    profile_id: int = Form(...),
    files: list[UploadFile] = File(...),
    service: BatchService = Depends(get_batch_service),
):
    payload = [(f.filename, await f.read()) for f in files]
    try:
        return service.create(profile_id, payload)
    except ProfileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ProfileNotBuiltError as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("", response_model=list[BatchSummary])
def list_batches(service: BatchService = Depends(get_batch_service)):
    return service.list_all()


@router.get("/{batch_id}", response_model=BatchDetail)
def get_batch(
    batch_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.RESULTS_PAGE_SIZE, ge=1, le=100),
    service: BatchService = Depends(get_batch_service),
):
    try:
        return service.get_detail(batch_id, page, page_size)
    except BatchNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
