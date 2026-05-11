"""dhwani - Phonetic normalization toolkit for Hinglish text."""

__version__ = "0.2.5"

from dhvani.core import (
    normalize,
    to_ipa,
    to_devanagari,
    are_same,
    identify_languages,
    batch_normalize,
    batch_to_devanagari,
    batch_to_ipa,
)
