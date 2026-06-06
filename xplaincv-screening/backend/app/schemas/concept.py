from pydantic import BaseModel, Field


class ConceptIn(BaseModel):
    concept: str = Field(min_length=1, max_length=300)
    importance: int = Field(default=3, ge=1, le=5)


class ConceptOut(BaseModel):
    id: int
    concept: str
    importance: int
    has_embedding: bool


class ExtractRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)


class ExtractResponse(BaseModel):
    source: str  # "llm"
    concepts: list[ConceptIn]
    dropped: list[str]  # concepts removed by the noise/class-echo filter
