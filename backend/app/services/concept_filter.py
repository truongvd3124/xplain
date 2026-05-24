import re
from typing import Iterable

__all__ = ["is_noise", "normalize_class_names"]


_MIN_ALPHA_CHARS = 3

# More whitespace tokens than this and it reads as a caption, not a concept.
_MAX_WORDS = 5


def _normalize(s: str) -> str:
    """Lowercase, turn `_`/`-` into spaces, collapse runs of whitespace."""
    s = s.lower().strip()
    s = re.sub(r"[_\-]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s


def normalize_class_names(names: Iterable[str]) -> set[str]:
    """Build the comparable form of a class-name list for `is_noise`."""
    return {_normalize(n) for n in names}


def is_noise(concept: str, class_names: set[str] | None = None) -> bool:
    """Return True if ``concept`` should be dropped.

    Args:
        concept:     The concept string (from the LLM or manual entry).
        class_names: Optional set from ``normalize_class_names`` (unused for now).
    """
    s = concept.strip()
    alpha = sum(ch.isalpha() for ch in s)

    if alpha < _MIN_ALPHA_CHARS:
        return True
    if len(s) // 2 > alpha:  # majority non-alphabetic (digits/punctuation)
        return True
    if len(s.split()) > _MAX_WORDS:
        return True
    return False
