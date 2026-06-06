from fastapi import APIRouter, Request

from app.schemas import DatasetInfo

router = APIRouter(prefix="/api", tags=["datasets"])


@router.get("/datasets", response_model=list[DatasetInfo])
def list_datasets(request: Request):
    return request.app.state.xplain_service.get_datasets()
