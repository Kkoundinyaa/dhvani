"""IPA normalization to canonical forms.

Strips diacritics, reduces allophonic variation, and maps to a canonical
representation for comparison and lookup.
"""

import re
import unicodedata


# Diacritics to strip for normalization (stress marks, length marks for comparison)
_DIACRITICS_TO_STRIP = re.compile(r"[ˈˌːˑ̤̥̃̊̈ʰʱ]")

# Allophonic reductions (map allophones to a canonical phoneme)
_ALLOPHONE_MAP = {
    "ɾ": "r",
    "ʋ": "v",
    "ɡ": "g",
    "d̪": "d",
    "t̪": "t",
    "ɪ": "i",
    "ʊ": "u",
    "ə": "a",
    "ɛ": "e",
    "ɔ": "o",
}


def ipa_to_canonical(ipa: str) -> str:
    """Convert IPA to a simplified canonical form for matching.

    This strips diacritics and reduces allophonic variation so that
    different pronunciations of the same word map to the same form.

    Args:
        ipa: IPA string

    Returns:
        Simplified canonical string (lossy, for matching only)
    """
    # Strip combining diacritics
    normalized = unicodedata.normalize("NFD", ipa)
    # Remove combining characters (category M)
    normalized = "".join(c for c in normalized if unicodedata.category(c)[0] != "M")

    # Strip known diacritics
    normalized = _DIACRITICS_TO_STRIP.sub("", normalized)

    # Apply allophone reductions
    for source, target in _ALLOPHONE_MAP.items():
        normalized = normalized.replace(source, target)

    return normalized


def strip_diacritics_ipa(ipa: str) -> str:
    """Strip only IPA diacritics while preserving base characters.

    Less aggressive than ipa_to_canonical - keeps phonemic distinctions
    but removes suprasegmental features.
    """
    # Remove stress marks and length marks only
    return re.sub(r"[ˈˌːˑ]", "", ipa)
