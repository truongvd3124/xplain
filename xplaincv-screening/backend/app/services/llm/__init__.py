from app.config import settings
from app.services.llm.base import LlmExtractionError, LLMProvider
from app.services.llm.gemini import GeminiProvider

__all__ = ["LLMProvider", "LlmExtractionError", "GeminiProvider", "get_llm_provider"]

_provider: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    """Resolve the configured provider (swap point for OpenAI later)."""
    global _provider
    if _provider is None:
        if settings.LLM_PROVIDER != "gemini":
            raise ValueError(f"Unknown LLM_PROVIDER: {settings.LLM_PROVIDER!r}")
        _provider = GeminiProvider()
    return _provider
