"""Noise filter for concepts retrieved from the CLIP bank.

Why this exists
---------------
The 8M-entry concept bank is built from web image-caption datasets
(CC3M, CC12M, YFCC15M, Flickr30K). Captions are scraped, not curated, so
many entries are not useful as human-readable concepts:

  - Filename junk         : "camera roll-1463", "img_5516", "p1020826"
  - URL / hashtag / tag   : "http://...", "#foodie", "@bruxelles"
  - Decorative wrappers   : "~the bald eagle~", "'beautiful eagle"
  - Caption fragments     : "flight air show 0529 saturday morning"
  - Repeated-char gimmick : "f-f-f-f-fashion", "t t tiger"
  - Class-name leakage    : "pizzeria capri" while classifying pizza
                            (circular reasoning — concept echoes the label)

Public API
----------
    normalize_class_names(names) -> set[str]
        Convert a raw class-name iterable into the comparable form used
        by ``is_noise`` (lowercased, underscores/hyphens turned to spaces,
        whitespace collapsed).

    is_noise(concept, class_names=None) -> bool
        Return True if the concept should be hidden from the user.
        Pass ``class_names`` (already normalized) to also block
        class-name circular reasoning. Omit it in modes without a
        fixed dataset (e.g. manual mode).

Everything else is module-private.
"""

from __future__ import annotations

import re
from typing import Iterable

__all__ = ["is_noise", "normalize_class_names"]


# ---------------------------------------------------------------------------
# Tunable thresholds
# ---------------------------------------------------------------------------

# A concept is dropped if it has fewer than this many alphabetic characters.
_MIN_ALPHA_CHARS = 3

# A concept is dropped if it spans more than this many whitespace tokens
# (above this it is almost always a free-form caption, not a concept).
_MAX_WORDS = 5


# ---------------------------------------------------------------------------
# Compiled patterns (compile once at import, reuse forever)
# ---------------------------------------------------------------------------

# Camera-default filename prefixes seen in web caption scrapes.
_FILENAME_PREFIXES = (
    r"(?:img|imgp|dsc|dscn|dscf|dcim|mg|sho|cjm|thp|adcn|fy|"
    r"file|image|photo|pic|p)"
)

# Filename-style junk: "camera roll-1234", "img_5516", "p1020826", and any
# 4+-digit run anywhere (which catches almost every photo serial).
_FILENAME_JUNK = re.compile(
    rf"""(?ix)
    \b camera \s* roll \b
    | \b {_FILENAME_PREFIXES} [_\s\-]? \d{{3,}} \b
    | \d{{4,}}
    """
)

# Hashtags / @-mentions / URL fragments.
_SOCIAL_OR_URL = re.compile(
    r"(?i)(^[#@])|\b(?:https?://|www\.|\.com\b|\.net\b|\.org\b)"
)

# Repeated single-letter tokens joined by space or hyphen, e.g. "f-f-f-f".
_CHAR_REPEAT = re.compile(r"\b([a-z])(?:[\s\-]\1){2,}\b", re.IGNORECASE)

# Decorative chars often left wrapping a caption: ~text~, 'text', "text"...
_WRAPPER_CHARS = "~`'\"«»‚‘’“”"
_WRAPPER_STRIP = re.compile(
    rf"^[{re.escape(_WRAPPER_CHARS)}\s]+|[{re.escape(_WRAPPER_CHARS)}\s]+$"
)

# CLIP-style article prefixes that we strip before comparing to class names.
_ARTICLE_PREFIXES = (
    "a photo of a ",
    "a photo of ",
    "an image of ",
    "the ",
    "a ",
    "an ",
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _strip_wrappers(s: str) -> str:
    """Remove decorative quote/tilde/etc. characters from both ends."""
    return _WRAPPER_STRIP.sub("", s)


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
    """True if the concept contains any class name (circular reasoning).

    Matching strategy varies by class-name length to balance recall and
    false-positive risk:

      * len < 3   skipped (too short to match safely)
      * len 3-4   whole-word match only:
                  "cat" matches "cat food" but not "category"
      * len >= 5  prefix match (catches plurals & in-stem extensions:
                  "pizza" -> pizzas, "sushi" -> sushiroll)
                  PLUS stem match if the class ends in a vowel
                  (drops the trailing vowel and requires >=1 trailing
                  letter): "pizza" -> "pizzeria", "sushi" -> "sushibar".
    """
    c = _strip_article(concept)
    for cn in class_names:
        n = len(cn)
        if n < 3:
            continue
        if n < 5:
            if re.search(r"\b" + re.escape(cn) + r"\b", c):
                return True
            continue
        # Prefix: catches "pizza", "pizzas", "delicious pizza", "sushibar"
        if re.search(r"\b" + re.escape(cn), c):
            return True
        # Stem: catches Italian -eria-style derivations off vowel endings
        if cn[-1] in "aeiou":
            stem = cn[:-1]
            if len(stem) >= 4 and re.search(
                r"\b" + re.escape(stem) + r"[a-z]+", c
            ):
                return True
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def normalize_class_names(names: Iterable[str]) -> set[str]:
    """Build the comparable form of a class-name list for ``is_noise``."""
    return {_normalize(n) for n in names}


def is_noise(concept: str, class_names: set[str] | None = None) -> bool:
    """Return True if ``concept`` should be hidden from the user.

    Args:
        concept:     Raw concept string from the bank.
        class_names: Optional set produced by ``normalize_class_names``.
                     When provided, concepts that echo a class name are
                     also dropped (circular reasoning). Pass ``None`` in
                     modes with no fixed dataset (e.g. manual).
    """
    s = _strip_wrappers(concept).strip()

    # Length / character mix
    if sum(ch.isalpha() for ch in s) < _MIN_ALPHA_CHARS:
        return True
    if len(s) // 2 > sum(ch.isalpha() for ch in s):
        # majority of characters are non-alphabetic (digits/punct)
        return True
    if len(s.split()) > _MAX_WORDS:
        return True

    # Pattern-based junk
    if _FILENAME_JUNK.search(s):
        return True
    if _SOCIAL_OR_URL.search(s):
        return True
    if _CHAR_REPEAT.search(s):
        return True

    # Class-name circular reasoning (only when a dataset is active)
    if class_names and _echoes_class_name(_normalize(s), class_names):
        return True

    return False
