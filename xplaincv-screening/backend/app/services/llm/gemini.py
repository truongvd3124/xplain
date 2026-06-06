"""Gemini implementation of the LLMProvider protocol.

Prompt + parsing ported from xplaincv-mvp llm_extract.py.
"""

import json

from google import genai
from google.genai import types

from app.config import settings
from app.services.llm.base import LlmExtractionError

_MIN_CONCEPTS = 5
_MAX_CONCEPTS = 12

_SYSTEM_PROMPT = f"""\
    You extract VISUAL attributes for image recognition with a CLIP model.

    Given a class name and its description, return the concrete, visually
    observable attributes a vision model could detect in a photo: body parts,
    shapes, colours, textures, patterns, materials.

    Rules:
    - Keep ONLY visual attributes. Drop abstract or behavioural traits
    (e.g. "loyal", "fast", "intelligent", "friendly").
    - Each concept is a short noun phrase of 2-4 words (e.g. "floppy ears",
    "furry coat", "four legs"). Lower-case, no trailing punctuation.
    - Do NOT include the class name itself as a concept.
    - "importance" is an integer 1-5: how decisive the attribute is for
    recognising this class (5 = highly distinctive).
    - Return between {_MIN_CONCEPTS} and {_MAX_CONCEPTS} concepts.

    Return ONLY a JSON array, e.g.:
    [{{"concept": "floppy ears", "importance": 4}},
    {{"concept": "furry coat", "importance": 5}}]
    """


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self._model = model or settings.GEMINI_MODEL

    def is_available(self) -> bool:
        return bool(self._api_key)

    def extract_concepts(self, class_name: str, description: str) -> list[dict]:
        raw = self._call(class_name, description)
        return _parse_concepts(raw)

    def _call(self, class_name: str, description: str) -> str:
        client = genai.Client(api_key=self._api_key)
        user_prompt = f"Class name: {class_name}\nDescription: {description}"
        try:
            response = client.models.generate_content(
                model=self._model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
        except Exception as exc:  # noqa: BLE001 - surface any SDK error uniformly
            raise LlmExtractionError(f"Gemini request failed: {exc}") from exc

        if not response.text:
            raise LlmExtractionError("Gemini returned an empty response")
        return response.text


def _parse_concepts(raw: str) -> list[dict]:
    """Validate and normalise the LLM's JSON response."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LlmExtractionError(f"LLM response is not valid JSON: {exc}") from exc

    if not isinstance(data, list):
        raise LlmExtractionError("LLM response is not a JSON array")

    concepts: list[dict] = []
    seen: set[str] = set()
    for item in data:
        if not isinstance(item, dict):
            continue
        concept = str(item.get("concept", "")).strip().lower()
        if not concept or concept in seen:
            continue
        seen.add(concept)
        importance = _clamp_importance(item.get("importance", 3))
        concepts.append({"concept": concept, "importance": importance})

    if not concepts:
        raise LlmExtractionError("LLM response contained no usable concepts")
    return concepts


def _clamp_importance(value: object) -> int:
    """Coerce an importance score into the integer range 1-5."""
    try:
        number = int(round(float(value)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 3
    return max(1, min(5, number))
