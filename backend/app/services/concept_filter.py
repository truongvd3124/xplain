import re
from typing import Iterable

__all__ = ["is_noise", "normalize_class_names"]


_MIN_ALPHA_CHARS = 3

# More whitespace tokens than this and it reads as a caption, not a concept.
_MAX_WORDS = 5

# CLIP-style article prefixes stripped before comparing against class names.
_ARTICLE_PREFIXES = (
    "a photo of a ",
    "a photo of ",
    "an image of ",
    "the ",
    "a ",
    "an ",
)


def _normalize(s: str) -> str:
    """Lowercase, turn `_`/`-` into spaces, collapse runs of whitespace."""
    s = s.lower().strip()
    s = re.sub(r"[_\-]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s


def _strip_article(s: str) -> str:
    """Drop a leading `a/an/the/a photo of` prefix if present."""
    for pref in _ARTICLE_PREFIXES:
        if s.startswith(pref):
            return s[len(pref):]
    return s


def _echoes_class_name(concept: str, class_names: set[str]) -> bool:
    """True if the concept contains a class name (circular reasoning)."""
    c = _strip_article(concept)
    for cn in class_names:
        n = len(cn)
        if n < 3:
            continue
        if n < 5:
            if re.search(r"\b" + re.escape(cn) + r"\b", c):
                return True
            continue
        if re.search(r"\b" + re.escape(cn), c):
            return True
        if cn[-1] in "aeiou":
            stem = cn[:-1]
            if len(stem) >= 4 and re.search(r"\b" + re.escape(stem) + r"[a-z]+", c):
                return True
    return False


def normalize_class_names(names: Iterable[str]) -> set[str]:
    """Build the comparable form of a class-name list for `is_noise`."""
    return {_normalize(n) for n in names}


def is_noise(concept: str, class_names: set[str] | None = None) -> bool:
    """Return True if ``concept`` should be dropped.

    Args:
        concept:     The concept string (from the LLM or manual entry).
        class_names: Optional set from ``normalize_class_names``. When given,
                     concepts echoing a class name are also dropped.
    """
    s = concept.strip()
    alpha = sum(ch.isalpha() for ch in s)

    if alpha < _MIN_ALPHA_CHARS:
        return True
    if len(s) // 2 > alpha:  # majority non-alphabetic (digits/punctuation)
        return True
    if len(s.split()) > _MAX_WORDS:
        return True
    if class_names and _echoes_class_name(_normalize(s), class_names):
        return True
    return False
