import json

from app.config import settings
from google import genai
from google.genai import types

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


class LlmExtractionError(RuntimeError):
    """Raised when the LLM call fails or returns an unparseable response."""


def is_available() -> bool:
    """True if an API key is configured and AI extraction can run."""
    return bool(settings.GEMINI_API_KEY)


def extract_concepts(class_name: str, description: str) -> list[dict]:
    raw = _call_gemini(class_name, description)
    return _parse_concepts(raw)


def _call_gemini(class_name: str, description: str) -> str:
    """Send the prompt to Gemini and return the raw text response."""
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    user_prompt = f"Class name: {class_name}\nDescription: {description}"

    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
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
