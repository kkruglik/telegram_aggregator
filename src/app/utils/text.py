import logging
import re
from functools import lru_cache

import pymorphy3

logger = logging.getLogger("news_aggregator")

_morph = pymorphy3.MorphAnalyzer()
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return [t for t in _PUNCT_RE.sub(" ", text.lower()).split() if t]


@lru_cache(maxsize=4096)
def _lemma(word: str) -> str:
    return _morph.parse(word)[0].normal_form


@lru_cache(maxsize=512)
def _keyword_lemmas(kw: str) -> frozenset[str]:
    return frozenset(_lemma(t) for t in _tokenize(kw))


def find_matched_keyword(text: str, keywords: set[str]) -> str | None:
    """Return the first keyword that matches the text, or None.

    Returns the original keyword string as the user typed it.
    """
    if not keywords:
        return None
    text_lemmas = {_lemma(t) for t in _tokenize(text)}
    for kw in keywords:
        kw_lemmas = _keyword_lemmas(kw)
        if kw_lemmas and kw_lemmas.issubset(text_lemmas):
            logger.debug(f"Keyword matched: '{kw}' (lemmas: {kw_lemmas})")
            return kw
    return None


def matches_keywords(text: str, keywords: set[str]) -> bool:
    """True if text contains all lemmas of at least one keyword (word or phrase).
    Returns True when keywords is empty (no filter = pass everything).
    """
    if not keywords:
        return True
    return find_matched_keyword(text, keywords) is not None
