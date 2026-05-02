"""Transliteration between scripts using IPA as pivot.

Romanized Hindi <-> IPA <-> Devanagari
"""

import re

# IPA to Devanagari mapping
_IPA_TO_DEVANAGARI = {
    # Consonants
    "k": "\u0915", "kʰ": "\u0916", "ɡ": "\u0917", "ɡʱ": "\u0918", "ŋ": "\u0919",
    "g": "\u0917",
    "t͡ʃ": "\u091A", "t͡ʃʰ": "\u091B", "d͡ʒ": "\u091C", "d͡ʒʱ": "\u091D", "ɲ": "\u091E",
    "ʈ": "\u091F", "ʈʰ": "\u0920", "ɖ": "\u0921", "ɖʱ": "\u0922", "ɳ": "\u0923",
    "t̪": "\u0924", "t̪ʰ": "\u0925", "d̪": "\u0926", "d̪ʱ": "\u0927", "n": "\u0928",
    "t": "\u0924", "d": "\u0926",
    "p": "\u092A", "pʰ": "\u092B", "b": "\u092C", "bʱ": "\u092D", "m": "\u092E",
    "j": "\u092F", "ɾ": "\u0930", "r": "\u0930", "l": "\u0932", "ʋ": "\u0935", "v": "\u0935",
    "ʃ": "\u0936", "ʂ": "\u0937", "s": "\u0938", "ɦ": "\u0939", "h": "\u0939",
    "f": "\u092B", "z": "\u091C\u093C",  # फ़, ज़
    "q": "\u0915\u093C",  # क़
    # Vowels (as matras - will be handled contextually)
}

_IPA_VOWEL_TO_MATRA = {
    "ə": "",  # inherent, no matra needed
    "aː": "\u093E",
    "ɪ": "\u093F", "iː": "\u0940", "i": "\u093F",
    "ʊ": "\u0941", "uː": "\u0942", "u": "\u0941",
    "eː": "\u0947", "e": "\u0947",
    "ɛː": "\u0948",
    "oː": "\u094B", "o": "\u094B",
    "ɔː": "\u094C",
}

_IPA_VOWEL_TO_INDEPENDENT = {
    "ə": "\u0905",
    "aː": "\u0906", "a": "\u0905",
    "ɪ": "\u0907", "iː": "\u0908", "i": "\u0907",
    "ʊ": "\u0909", "uː": "\u090A", "u": "\u0909",
    "eː": "\u090F", "e": "\u090F",
    "ɛː": "\u0910",
    "oː": "\u0913", "o": "\u0913",
    "ɔː": "\u0914",
}


def ipa_to_devanagari(ipa: str) -> str:
    """Convert IPA transcription to Devanagari script.

    Args:
        ipa: IPA string representing Hindi phonemes

    Returns:
        Devanagari string
    """
    if not ipa:
        return ""

    result = []
    i = 0
    prev_was_consonant = False

    while i < len(ipa):
        matched = False

        # Try longest match first (up to 4 chars for complex consonants)
        for length in range(min(4, len(ipa) - i), 0, -1):
            chunk = ipa[i:i + length]

            # Check if it's a consonant
            if chunk in _IPA_TO_DEVANAGARI:
                result.append(_IPA_TO_DEVANAGARI[chunk])
                prev_was_consonant = True
                i += length
                matched = True
                break

            # Check if it's a vowel
            if prev_was_consonant and chunk in _IPA_VOWEL_TO_MATRA:
                matra = _IPA_VOWEL_TO_MATRA[chunk]
                if matra:  # non-empty (not inherent schwa)
                    result.append(matra)
                prev_was_consonant = False
                i += length
                matched = True
                break
            elif not prev_was_consonant and chunk in _IPA_VOWEL_TO_INDEPENDENT:
                result.append(_IPA_VOWEL_TO_INDEPENDENT[chunk])
                prev_was_consonant = False
                i += length
                matched = True
                break

        if not matched:
            # Skip unknown IPA characters
            i += 1
            prev_was_consonant = False

    return "".join(result)


def roman_to_devanagari(word: str) -> str:
    """Convert Romanized Hindi directly to Devanagari via IPA pivot.

    Args:
        word: Romanized Hindi word (e.g., "bahut", "accha")

    Returns:
        Devanagari string
    """
    from dhwani.ipa import romanized_hindi_to_ipa
    ipa = romanized_hindi_to_ipa(word)
    return ipa_to_devanagari(ipa)
