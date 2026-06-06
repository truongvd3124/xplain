"""Dependency-injection wiring (FastAPI Depends).

router -> service -> repository -> Session. The Celery worker does not use
this module; it builds its own Session and resolves CLIP via clip_provider.
"""

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.batch_repo import BatchRepo
from app.repositories.profile_repo import ProfileRepo
from app.repositories.result_repo import ResultRepo
from app.services.batch_service import BatchService
from app.services.clip_engine import ClipEngine
from app.services.concept_service import ConceptService
from app.services.llm import LLMProvider, get_llm_provider
from app.services.profile_service import ProfileService


def get_clip(request: Request) -> ClipEngine:
    return request.app.state.clip


def get_llm() -> LLMProvider:
    return get_llm_provider()


def get_profile_repo(db: Session = Depends(get_db)) -> ProfileRepo:
    return ProfileRepo(db)


def get_batch_repo(db: Session = Depends(get_db)) -> BatchRepo:
    return BatchRepo(db)


def get_result_repo(db: Session = Depends(get_db)) -> ResultRepo:
    return ResultRepo(db)


def get_concept_service(llm: LLMProvider = Depends(get_llm)) -> ConceptService:
    return ConceptService(llm)


def get_profile_service(
    repo: ProfileRepo = Depends(get_profile_repo),
    clip: ClipEngine = Depends(get_clip),
) -> ProfileService:
    return ProfileService(repo, clip)


def get_batch_service(
    batch_repo: BatchRepo = Depends(get_batch_repo),
    result_repo: ResultRepo = Depends(get_result_repo),
    profile_repo: ProfileRepo = Depends(get_profile_repo),
) -> BatchService:
    return BatchService(batch_repo, result_repo, profile_repo)
