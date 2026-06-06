from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.concept import ConceptIn, ConceptOut


class ProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    concepts: list[ConceptIn] = Field(min_length=1)


class ReferenceImageOut(BaseModel):
    id: int
    image_url: str
    has_embedding: bool


class ProfileSummary(BaseModel):
    id: int
    name: str
    description: str
    threshold_score: float
    num_concepts: int
    num_references: int
    is_built: bool
    created_at: datetime


class ProfileDetail(ProfileSummary):
    concepts: list[ConceptOut]
    reference_images: list[ReferenceImageOut]
    calibration: dict | None
