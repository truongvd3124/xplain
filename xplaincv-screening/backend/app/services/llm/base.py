"""LLM provider interface for text -> visual-concept extraction."""

from typing import Protocol


class LlmExtractionError(RuntimeError):
    """Raised when the LLM call fails or returns an unparseable response."""


class LLMProvider(Protocol):
    name: str

    def is_available(self) -> bool:
        """True if the provider is configured (API key present)."""
        ...

    def extract_concepts(self, class_name: str, description: str) -> list[dict]:
        """Return [{"concept": str, "importance": int 1-5}, ...].

        Raises LlmExtractionError on failure.
        """
        ...
