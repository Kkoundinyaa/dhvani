"""Model-based IPA pipeline using AI4Bharat IndicXlit + epitran.

This is Tier 2 of dhwani's architecture: the most accurate path for
converting informal Romanized Hindi to IPA. Uses a pretrained 11M param
transformer (IndicXlit) to handle messy/informal spellings, then epitran
for Devanagari -> IPA.

Optional dependency: install with `pip install dhwani[models]`
"""

import logging
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)

_xlit_engine = None
_epitran_engine = None


def _get_xlit_engine():
    """Lazy-load the IndicXlit transliteration engine."""
    global _xlit_engine
    if _xlit_engine is None:
        try:
            import torch
            import argparse
            # IndicXlit uses fairseq checkpoints that need these globals whitelisted
            torch.serialization.add_safe_globals([argparse.Namespace])
            from ai4bharat.transliteration import XlitEngine
            _xlit_engine = XlitEngine("hi", beam_width=10, rescore=True)
            logger.info("IndicXlit engine loaded successfully")
        except ImportError:
            raise ImportError(
                "ai4bharat-transliteration is required for model-based pipeline. "
                "Install with: pip install ai4bharat-transliteration"
            )
    return _xlit_engine


def _get_epitran_engine():
    """Lazy-load the epitran Hindi engine."""
    global _epitran_engine
    if _epitran_engine is None:
        try:
            import epitran
            _epitran_engine = epitran.Epitran("hin-Deva")
            logger.info("Epitran hin-Deva engine loaded successfully")
        except ImportError:
            raise ImportError(
                "epitran is required for model-based pipeline. "
                "Install with: pip install epitran"
            )
    return _epitran_engine


def romanized_to_devanagari_model(word: str, topk: int = 3) -> List[str]:
    """Convert informal Romanized Hindi to Devanagari using IndicXlit.

    Handles messy spellings like "bohot", "accha", "kese" that rule-based
    systems cannot process.

    Args:
        word: Romanized Hindi word (informal spelling)
        topk: Number of Devanagari candidates to return

    Returns:
        List of Devanagari candidates (best first)
    """
    engine = _get_xlit_engine()
    result = engine.translit_word(word.lower().strip(), topk=topk)
    candidates = result.get("hi", [])
    return candidates if candidates else [word]


def devanagari_to_ipa_epitran(word: str) -> str:
    """Convert Devanagari text to IPA using epitran.

    Args:
        word: Hindi text in Devanagari script

    Returns:
        IPA transcription
    """
    engine = _get_epitran_engine()
    return engine.transliterate(word)


def romanized_to_ipa_model(word: str) -> str:
    """Full pipeline: Romanized Hindi -> Devanagari -> IPA.

    This is the most accurate path for informal Hinglish words.

    Args:
        word: Informal Romanized Hindi word (e.g., "bohot", "accha")

    Returns:
        IPA transcription
    """
    # Stage 1: Romanized -> Devanagari (top candidate)
    candidates = romanized_to_devanagari_model(word, topk=1)
    devanagari = candidates[0] if candidates else word

    # Stage 2: Devanagari -> IPA
    ipa = devanagari_to_ipa_epitran(devanagari)
    return ipa


def romanized_to_ipa_with_candidates(word: str, topk: int = 3) -> List[Tuple[str, str]]:
    """Get multiple IPA candidates for a romanized word.

    Useful for disambiguation or showing alternatives.

    Args:
        word: Romanized Hindi word
        topk: Number of candidates

    Returns:
        List of (devanagari, ipa) tuples
    """
    candidates = romanized_to_devanagari_model(word, topk=topk)
    results = []
    for dev in candidates:
        ipa = devanagari_to_ipa_epitran(dev)
        results.append((dev, ipa))
    return results


def is_available() -> bool:
    """Check if model-based pipeline dependencies are installed."""
    try:
        import ai4bharat.transliteration
        import epitran
        return True
    except ImportError:
        return False
