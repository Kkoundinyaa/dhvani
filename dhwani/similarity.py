"""Phonetic similarity scoring between words.

Uses IPA representations to compute similarity, handling
variant spellings of the same Hindi word.
"""

from dhwani.ipa import romanized_hindi_to_ipa, devanagari_to_ipa
from dhwani.normalizer import ipa_to_canonical
from dhwani.lang_id import is_devanagari


def _get_canonical_ipa(word: str) -> str:
    """Get canonical IPA for a word in any script."""
    word = word.strip()
    if is_devanagari(word):
        ipa = devanagari_to_ipa(word)
    else:
        ipa = romanized_hindi_to_ipa(word)
    return ipa_to_canonical(ipa)


def edit_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return edit_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]


def phonetic_similarity(word1: str, word2: str) -> float:
    """Compute phonetic similarity between two words (0 to 1).

    Words can be in any script (Romanized Hindi, Devanagari, or English).
    Similarity is computed over canonical IPA representations.

    Args:
        word1: First word
        word2: Second word

    Returns:
        Float between 0 (completely different) and 1 (identical)
    """
    canon1 = _get_canonical_ipa(word1)
    canon2 = _get_canonical_ipa(word2)

    if not canon1 or not canon2:
        return 0.0

    if canon1 == canon2:
        return 1.0

    max_len = max(len(canon1), len(canon2))
    distance = edit_distance(canon1, canon2)

    return 1.0 - (distance / max_len)
