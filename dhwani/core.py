"""Core API for dhwani - the main user-facing functions."""

from typing import List, Tuple

from dhwani.lang_id import word_level_lang_id
from dhwani.ipa import romanized_hindi_to_ipa, devanagari_to_ipa
from dhwani.normalizer import ipa_to_canonical
from dhwani.transliterate import ipa_to_devanagari, roman_to_devanagari
from dhwani.similarity import phonetic_similarity


def _romanized_to_devanagari(word: str) -> str:
    """Best-effort romanized Hindi to Devanagari conversion.

    Priority:
    1. Direct correction lookup (known variants -> canonical Devanagari)
    2. Model-based (IndicXlit) with phonetic post-correction
    3. IPA-pivot fallback
    """
    from dhwani.corrector import correct_transliteration, _direct_lookup

    # First: check if we have a direct known mapping (fastest + most accurate)
    direct = _direct_lookup(word)
    if direct:
        return direct

    # Second: check runtime cache (learned from previous calls)
    from dhwani.cache import cache_get_devanagari
    cached = cache_get_devanagari(word)
    if cached:
        return cached

    # Third: use model with correction (result gets cached for next time)
    try:
        from dhwani.ipa_pipeline import romanized_to_devanagari_model, is_available
        if is_available():
            candidates = romanized_to_devanagari_model(word, topk=1)
            if candidates:
                corrected = correct_transliteration(candidates[0], word)
                # Cache for next time
                from dhwani.ipa_pipeline import devanagari_to_ipa_epitran
                from dhwani.cache import cache_store
                try:
                    ipa = devanagari_to_ipa_epitran(corrected)
                    cache_store(word, corrected, ipa)
                except Exception:
                    cache_store(word, corrected, "")
                return corrected
    except (ImportError, Exception):
        pass

    # Fallback: IPA pivot
    from dhwani.transliterate import roman_to_devanagari
    return roman_to_devanagari(word)


def normalize(text: str, target: str = "roman") -> str:
    """Normalize Hinglish text to a canonical form.

    Args:
        text: Input Hinglish text (Romanized Hindi, Devanagari, or mixed)
        target: Output format - "roman", "devanagari", or "ipa"

    Returns:
        Normalized text in the target representation
    """
    words = text.split()
    lang_tags = word_level_lang_id(words)
    result = []

    for word, lang in zip(words, lang_tags):
        if lang == "en":
            result.append(word)
        elif lang == "hi":
            if target == "devanagari":
                # Use model-based transliteration directly (more accurate than IPA pivot)
                result.append(_romanized_to_devanagari(word))
            else:
                ipa = romanized_hindi_to_ipa(word)
                if target == "ipa":
                    result.append(ipa)
                else:
                    result.append(ipa_to_canonical(ipa))
        elif lang == "hi_dev":
            ipa = devanagari_to_ipa(word)
            if target == "ipa":
                result.append(ipa)
            elif target == "devanagari":
                result.append(word)
            else:
                result.append(ipa_to_canonical(ipa))
        else:
            result.append(word)

    return " ".join(result)


def to_ipa(text: str) -> str:
    """Convert Hinglish text to IPA representation.

    Handles Romanized Hindi, Devanagari, and English words.
    """
    return normalize(text, target="ipa")


def to_devanagari(text: str) -> str:
    """Convert Romanized Hindi words in text to Devanagari.

    English words are left unchanged.
    """
    return normalize(text, target="devanagari")


def are_same(word1: str, word2: str, threshold: float = 0.85) -> bool:
    """Check if two words are phonetically the same (variant spellings).

    Args:
        word1: First word (any script)
        word2: Second word (any script)
        threshold: Similarity threshold (0-1), default 0.85

    Returns:
        True if the words are phonetically equivalent
    """
    return phonetic_similarity(word1, word2) >= threshold


def identify_languages(text: str) -> List[Tuple[str, str]]:
    """Identify language of each word in Hinglish text.

    Returns:
        List of (word, language) tuples where language is "hi", "en", or "hi_dev"
    """
    words = text.split()
    tags = word_level_lang_id(words)
    return list(zip(words, tags))
