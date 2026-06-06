"""Text -> visual concepts, with noise filtering."""

from app.schemas.concept import ConceptIn, ExtractResponse
from app.services.concept_filter import is_noise, normalize_class_names
from app.services.llm.base import LLMProvider


class ConceptService:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    def extract(self, name: str, description: str) -> ExtractResponse:
        raw = self.llm.extract_concepts(name, description)
        class_names = normalize_class_names([name])
        kept, dropped = [], []
        for item in raw:
            if is_noise(item["concept"], class_names):
                dropped.append(item["concept"])
            else:
                kept.append(ConceptIn(concept=item["concept"],
                                      importance=item["importance"]))
        return ExtractResponse(source=self.llm.name, concepts=kept, dropped=dropped)
