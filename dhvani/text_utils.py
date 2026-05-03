"""Text preprocessing utilities for handling messy social media input.

Handles:
- Punctuation stripping and reattachment
- Elongated/repeated character collapsing (e.g., "bahutttt" -> "bahut")
"""

import re

# Punctuation that can appear attached to words
PUNCT_PATTERN = re.compile(r'^([^\w]*)(.+?)([^\w]*)$')


def strip_punctuation(word: str):
    """Strip leading/trailing punctuation from a word.

    Returns (prefix_punct, clean_word, suffix_punct).
    """
    match = PUNCT_PATTERN.match(word)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return '', word, ''


def collapse_repeated(word: str) -> str:
    """Collapse 3+ repeated characters to 2, then try lookups with both 2 and 1.

    Only collapses runs of 3 or more of the same character.
    "bahutttt" -> "bahut" (tttt -> t, since tt not a valid variant either)
    "achaaaa" -> "achaa" (aaaa -> aa, valid Hindi double vowel)
    "yarrrr" -> "yarr" -> then lookup tries "yarr" and "yar"
    "mutter" -> "mutter" (only 2 t's, not touched)
    "karra" -> "karra" (only 2 r's, not touched)
    """
    result = []
    i = 0
    while i < len(word):
        char = word[i]
        count = 1
        while i + count < len(word) and word[i + count] == char:
            count += 1

        if count >= 3:
            # Collapse 3+ to max 2 (preserves valid doubles like "aa", "ee")
            result.append(char * 2)
        else:
            result.append(char * count)

        i += count

    return ''.join(result)


def normalize_input(word: str):
    """Full input normalization pipeline.

    Returns (prefix_punct, normalized_word, suffix_punct).
    """
    prefix, clean, suffix = strip_punctuation(word)
    clean = clean.lower()
    clean = collapse_repeated(clean)
    return prefix, clean, suffix
