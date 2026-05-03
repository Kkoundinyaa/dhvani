"""IPA conversion for Hindi text in various scripts.

Handles:
- Devanagari Hindi -> IPA (via espeak-ng)
- Romanized Hindi -> IPA (via rule-based G2P + lexicon lookup)
"""

import re
import unicodedata
from typing import Optional

from dhvani.lexicon.lookup import lookup_ipa


# Romanized Hindi to IPA mapping rules
# Based on Hindi phonology applied to common romanization conventions
CONSONANT_MAP = {
    # Aspirated consonants (must come before unaspirated)
    "chh": "t͡ʃʰ",
    "chch": "t͡ʃːʰ",
    "kh": "kʰ",
    "gh": "ɡʱ",
    "ch": "t͡ʃ",
    "jh": "d͡ʒʱ",
    "th": "tʰ",  # dental aspirated (not English 'th')
    "dh": "dʱ",
    "ph": "pʰ",
    "bh": "bʱ",
    "sh": "ʃ",
    "shh": "ʂ",  # retroflex sh
    # Basic consonants
    "k": "k",
    "g": "ɡ",
    "c": "t͡ʃ",
    "j": "d͡ʒ",
    "t": "t̪",  # dental t
    "d": "d̪",  # dental d
    "p": "p",
    "b": "b",
    "n": "n",
    "m": "m",
    "l": "l",
    "r": "ɾ",
    "v": "ʋ",
    "w": "ʋ",
    "s": "s",
    "h": "ɦ",
    "y": "j",
    "f": "f",
    "z": "z",
    "q": "q",
    "x": "kʰ",
}

# Vowel mappings (longer patterns first)
VOWEL_MAP = {
    "aa": "aː",
    "ee": "iː",
    "oo": "uː",
    "ai": "ɛː",
    "au": "ɔː",
    "ei": "eː",
    "ou": "oː",
    "a": "ə",
    "e": "eː",
    "i": "ɪ",
    "o": "oː",
    "u": "ʊ",
}

# Nasalization patterns
NASAL_PATTERNS = {
    "an": "ã",
    "in": "ĩ",
    "un": "ũ",
}

# Build regex for tokenizing (longest match first)
_all_graphemes = sorted(
    list(CONSONANT_MAP.keys()) + list(VOWEL_MAP.keys()),
    key=len,
    reverse=True,
)
_GRAPHEME_RE = re.compile("|".join(re.escape(g) for g in _all_graphemes) + r"|.", re.IGNORECASE)


def romanized_hindi_to_ipa(word: str, use_model: bool = True) -> str:
    """Convert a Romanized Hindi word to IPA.

    Three-tier approach:
    1. Lexicon lookup (instant, most common words)
    2. Model-based pipeline via IndicXlit + epitran (accurate, needs deps)
    3. Rule-based G2P fallback (always available)

    Args:
        word: A single word in Romanized Hindi (e.g., "bahut", "accha")
        use_model: Whether to try model-based pipeline (default True)

    Returns:
        IPA transcription string
    """
    clean = word.lower().strip()

    # Tier 1: Lexicon lookup (fastest)
    ipa = lookup_ipa(clean)
    if ipa:
        return ipa

    # Tier 1.1: Try collapsing double consonants (e.g., "bohott" -> "bohot")
    from dhvani.corrector import _collapse_doubles
    collapsed = _collapse_doubles(clean)
    if collapsed != clean:
        ipa = lookup_ipa(collapsed)
        if ipa:
            return ipa

    # Tier 1.5: Runtime cache (learned from previous Tier 2 calls)
    from dhvani.cache import cache_get_ipa
    cached_ipa = cache_get_ipa(clean)
    if cached_ipa:
        return cached_ipa

    # Tier 2: Model-based pipeline (most accurate, results get cached)
    # Only use if the model is already loaded -- never block on first load
    if use_model:
        try:
            from dhvani.ipa_pipeline import romanized_to_ipa_model, romanized_to_devanagari_model, is_available, is_loaded
            if is_available() and is_loaded():
                ipa_result = romanized_to_ipa_model(clean)
                # Cache for next time
                from dhvani.cache import cache_store
                dev_candidates = romanized_to_devanagari_model(clean, topk=1)
                dev = dev_candidates[0] if dev_candidates else ""
                cache_store(clean, dev, ipa_result)
                return ipa_result
        except (ImportError, Exception):
            pass

    # Tier 3: Rule-based fallback
    return _rule_based_g2p(clean)


def _rule_based_g2p(word: str) -> str:
    """Rule-based grapheme-to-phoneme for Romanized Hindi."""
    result = []
    i = 0
    word_lower = word.lower()

    while i < len(word_lower):
        matched = False

        # Try longest match first (3 chars, then 2, then 1)
        for length in (3, 2, 1):
            chunk = word_lower[i:i + length]

            if chunk in CONSONANT_MAP:
                result.append(CONSONANT_MAP[chunk])
                i += length
                matched = True
                break
            elif chunk in VOWEL_MAP:
                result.append(VOWEL_MAP[chunk])
                i += length
                matched = True
                break

        if not matched:
            # Keep unknown characters as-is (numbers, punctuation)
            result.append(word_lower[i])
            i += 1

    return "".join(result)


def devanagari_to_ipa(word: str) -> str:
    """Convert Devanagari Hindi text to IPA.

    Uses rule-based mapping (fast, always available).
    Falls back to espeak-ng only if phonemizer is already imported.
    """
    # Use rule-based by default (instant, no external deps)
    return _devanagari_rule_based(word)


# Devanagari character to IPA mapping
_DEVANAGARI_MAP = {
    "\u0915": "k", "\u0916": "kʰ", "\u0917": "ɡ", "\u0918": "ɡʱ", "\u0919": "ŋ",
    "\u091A": "t͡ʃ", "\u091B": "t͡ʃʰ", "\u091C": "d͡ʒ", "\u091D": "d͡ʒʱ", "\u091E": "ɲ",
    "\u091F": "ʈ", "\u0920": "ʈʰ", "\u0921": "ɖ", "\u0922": "ɖʱ", "\u0923": "ɳ",
    "\u0924": "t̪", "\u0925": "t̪ʰ", "\u0926": "d̪", "\u0927": "d̪ʱ", "\u0928": "n",
    "\u092A": "p", "\u092B": "pʰ", "\u092C": "b", "\u092D": "bʱ", "\u092E": "m",
    "\u092F": "j", "\u0930": "ɾ", "\u0932": "l", "\u0935": "ʋ",
    "\u0936": "ʃ", "\u0937": "ʂ", "\u0938": "s", "\u0939": "ɦ",
    # Vowels (independent)
    "\u0905": "ə", "\u0906": "aː", "\u0907": "ɪ", "\u0908": "iː",
    "\u0909": "ʊ", "\u090A": "uː", "\u090F": "eː", "\u0910": "ɛː",
    "\u0913": "oː", "\u0914": "ɔː",
    # Vowel matras (dependent)
    "\u093E": "aː", "\u093F": "ɪ", "\u0940": "iː",
    "\u0941": "ʊ", "\u0942": "uː", "\u0947": "eː", "\u0948": "ɛː",
    "\u094B": "oː", "\u094C": "ɔː",
    # Virama (halant) - suppresses inherent 'a'
    "\u094D": "",
    # Anusvara, Chandrabindu
    "\u0902": "̃", "\u0901": "̃",
}


def _devanagari_rule_based(word: str) -> str:
    """Fallback rule-based Devanagari to IPA."""
    result = []
    chars = list(word)
    i = 0

    while i < len(chars):
        char = chars[i]

        if char in _DEVANAGARI_MAP:
            ipa_char = _DEVANAGARI_MAP[char]

            # Check if next char is halant (virama)
            if i + 1 < len(chars) and chars[i + 1] == "\u094D":
                result.append(ipa_char)
                i += 2  # skip halant
            # Check if next char is a vowel matra
            elif i + 1 < len(chars) and chars[i + 1] in _DEVANAGARI_MAP and "\u093E" <= chars[i + 1] <= "\u094C":
                result.append(ipa_char)
                i += 1  # vowel matra will be processed next iteration
            # Consonant without matra or halant -> inherent schwa
            elif "\u0915" <= char <= "\u0939":
                result.append(ipa_char + "ə")
                i += 1
            else:
                result.append(ipa_char)
                i += 1
        else:
            result.append(char)
            i += 1

    return "".join(result)
