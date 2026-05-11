"""Core API for dhwani - the main user-facing functions."""

from typing import List, Tuple

from dhvani.lang_id import word_level_lang_id
from dhvani.ipa import romanized_hindi_to_ipa, devanagari_to_ipa
from dhvani.normalizer import ipa_to_canonical
from dhvani.transliterate import ipa_to_devanagari, roman_to_devanagari
from dhvani.similarity import phonetic_similarity
from dhvani.text_utils import normalize_input


def _romanized_to_devanagari(word: str) -> str:
    """Best-effort romanized Hindi to Devanagari conversion.

    Priority:
    1. Direct correction lookup (known variants -> canonical Devanagari)
    2. Model-based (IndicXlit) with phonetic post-correction
    3. IPA-pivot fallback
    """
    from dhvani.corrector import correct_transliteration, _direct_lookup

    # First: check if we have a direct known mapping (fastest + most accurate)
    direct = _direct_lookup(word)
    if direct:
        return direct

    # Second: check runtime cache (learned from previous calls)
    from dhvani.cache import cache_get_devanagari
    cached = cache_get_devanagari(word)
    if cached:
        return cached

    # Third: use model with correction (only if already loaded -- never block)
    try:
        from dhvani.ipa_pipeline import romanized_to_devanagari_model, is_available, is_loaded
        if is_available() and is_loaded():
            candidates = romanized_to_devanagari_model(word, topk=1)
            if candidates:
                corrected = correct_transliteration(candidates[0], word)
                # Cache for next time
                from dhvani.ipa_pipeline import devanagari_to_ipa_epitran
                from dhvani.cache import cache_store
                try:
                    ipa = devanagari_to_ipa_epitran(corrected)
                    cache_store(word, corrected, ipa)
                except Exception:
                    cache_store(word, corrected, "")
                return corrected
    except (ImportError, Exception):
        pass

    # Fallback: IPA pivot
    from dhvani.transliterate import roman_to_devanagari
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
    # Run lang_id on cleaned words (stripped of punctuation + collapsed repeats)
    cleaned = []
    punct_info = []
    for word in words:
        prefix, clean, suffix = normalize_input(word)
        cleaned.append(clean)
        punct_info.append((prefix, suffix, word))

    lang_tags = word_level_lang_id(cleaned)
    result = []

    for clean, (prefix, suffix, original), lang in zip(cleaned, punct_info, lang_tags):
        if lang == "en":
            result.append(original)
        elif lang == "hi":
            if target == "devanagari":
                converted = _romanized_to_devanagari(clean)
                result.append(prefix + converted + suffix)
            else:
                ipa = romanized_hindi_to_ipa(clean)
                if target == "ipa":
                    result.append(prefix + ipa + suffix)
                else:
                    result.append(prefix + ipa_to_canonical(ipa) + suffix)
        elif lang == "hi_dev":
            ipa = devanagari_to_ipa(clean)
            if target == "ipa":
                result.append(prefix + ipa + suffix)
            elif target == "devanagari":
                result.append(original)
            else:
                result.append(prefix + ipa_to_canonical(ipa) + suffix)
        else:
            result.append(original)

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
    cleaned = []
    for word in words:
        _, clean, _ = normalize_input(word)
        cleaned.append(clean)
    tags = word_level_lang_id(cleaned)
    return list(zip(words, tags))


def batch_normalize(texts: List[str], target: str = "roman") -> List[str]:
    """Normalize a list of Hinglish texts to a canonical form.

    Args:
        texts: List of input Hinglish texts
        target: Output format - "roman", "devanagari", or "ipa"

    Returns:
        List of normalized texts in the target representation
    """
    return [normalize(text, target=target) for text in texts]


def batch_to_devanagari(texts: List[str]) -> List[str]:
    """Convert a list of Hinglish texts to Devanagari.

    Args:
        texts: List of input Hinglish texts

    Returns:
        List of texts with Hindi words converted to Devanagari
    """
    return [to_devanagari(text) for text in texts]


def batch_to_ipa(texts: List[str]) -> List[str]:
    """Convert a list of Hinglish texts to IPA representation.

    Args:
        texts: List of input Hinglish texts

    Returns:
        List of texts in IPA representation
    """
    return [to_ipa(text) for text in texts]
