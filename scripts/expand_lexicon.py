"""Expand the lexicon by generating romanized spelling variants for Devanagari words.

Strategy:
1. Take each Devanagari word
2. Get its IPA (via epitran)
3. Generate all plausible romanized spellings from the IPA
4. Map all variants -> canonical Devanagari + IPA

This gives us thousands of romanized variants that all point to the correct word.
No model inference needed at runtime -- just JSON lookups.

Usage:
    python scripts/expand_lexicon.py --devanagari data/devanagari_words.txt --output dhwani/lexicon/
"""

import argparse
import json
import logging
import sys
from itertools import product
from pathlib import Path
from typing import Dict, List, Set, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# IPA phoneme to possible romanized spellings (one phoneme can be written multiple ways)
IPA_TO_ROMAN_VARIANTS = {
    # Vowels
    "ə": ["a", ""],  # schwa: sometimes written, sometimes dropped
    "aː": ["aa", "a"],
    "ɪ": ["i"],
    "iː": ["ee", "i", "ii"],
    "ʊ": ["u"],
    "uː": ["oo", "u", "uu"],
    "eː": ["e", "ei"],
    "e": ["e"],
    "æː": ["ai", "e"],
    "ɛː": ["ai", "e"],
    "oː": ["o"],
    "o": ["o"],
    "ɔː": ["au", "o"],
    # Consonants - aspirated (must check before unaspirated)
    "kʰ": ["kh"],
    "ɡʱ": ["gh"],
    "t͡ʃʰ": ["chh", "ch"],
    "d͡ʒʱ": ["jh"],
    "ʈʰ": ["th"],
    "ɖʱ": ["dh"],
    "t̪ʰ": ["th"],
    "d̪ʱ": ["dh"],
    "pʰ": ["ph", "f"],
    "bʱ": ["bh"],
    # Consonants - basic
    "k": ["k", "c"],
    "ɡ": ["g"],
    "g": ["g"],
    "t͡ʃ": ["ch", "c"],
    "d͡ʒ": ["j"],
    "ʈ": ["t"],
    "ɖ": ["d"],
    "ɽ": ["r", "d"],
    "t̪": ["t"],
    "d̪": ["d"],
    "n": ["n"],
    "ɳ": ["n"],
    "ŋ": ["ng", "n"],
    "ɲ": ["n"],
    "p": ["p"],
    "b": ["b"],
    "m": ["m"],
    "j": ["y"],
    "ɾ": ["r"],
    "r": ["r"],
    "l": ["l"],
    "ʋ": ["v", "w"],
    "v": ["v", "w"],
    "ʃ": ["sh"],
    "ʂ": ["sh"],
    "s": ["s"],
    "ɦ": ["h"],
    "h": ["h"],
    "f": ["f", "ph"],
    "z": ["z", "j"],
    "q": ["q", "k"],
    "x": ["kh"],
    # Plain ASCII variants (epitran sometimes outputs these)
    "t": ["t"],
    "d": ["d"],
    "u": ["u"],
    "i": ["i", "ee"],
    "a": ["a"],
    "o": ["o"],
    "e": ["e"],
    # Nasalization
    "\u0303": ["n", ""],  # combining tilde
    "̃": ["n", ""],
    # Gemination / length on consonants
    "ː": ["", ""],
    # Common clusters
    "d͡ʒ̤": ["jh", "j"],
    "ɡ̤": ["gh", "g"],
    "t͡ʃt͡ʃʰ": ["cchh", "chch", "ch"],
}

# Sorted by length (longest first) for greedy matching
_SORTED_IPA = sorted(IPA_TO_ROMAN_VARIANTS.keys(), key=len, reverse=True)


def ipa_to_roman_variants(ipa: str, max_variants: int = 5) -> List[str]:
    """Generate plausible romanized spellings from an IPA string.

    Uses greedy longest-match tokenization of IPA, then generates
    combinations of possible romanizations for each phoneme.

    Args:
        ipa: IPA transcription string
        max_variants: Maximum number of variants to generate (keeps output manageable)

    Returns:
        List of plausible romanized spellings
    """
    # Tokenize IPA into phonemes (greedy longest match)
    phonemes = []
    i = 0
    while i < len(ipa):
        matched = False
        for length in range(min(4, len(ipa) - i), 0, -1):
            chunk = ipa[i:i + length]
            if chunk in IPA_TO_ROMAN_VARIANTS:
                phonemes.append(chunk)
                i += length
                matched = True
                break
        if not matched:
            # Skip unknown IPA characters
            i += 1

    if not phonemes:
        return []

    # Generate combinations (but limit to avoid explosion)
    roman_options = [IPA_TO_ROMAN_VARIANTS[p] for p in phonemes]

    # If too many combinations, just take first option for each phoneme
    # plus a few strategic variants
    total_combos = 1
    for opts in roman_options:
        total_combos *= len(opts)

    if total_combos <= max_variants * 2:
        # Generate all
        variants = set()
        for combo in product(*roman_options):
            variant = "".join(combo).strip()
            if len(variant) >= 2:
                variants.add(variant)
    else:
        # Generate strategically
        variants = set()
        # Most common spelling (first option for each)
        base = "".join(opts[0] for opts in roman_options)
        if len(base) >= 2:
            variants.add(base)

        # Generate variants by flipping one phoneme at a time
        for i, opts in enumerate(roman_options):
            for alt in opts[1:]:
                variant = "".join(
                    alt if j == i else roman_options[j][0]
                    for j in range(len(roman_options))
                )
                if len(variant) >= 2:
                    variants.add(variant)
                if len(variants) >= max_variants:
                    break
            if len(variants) >= max_variants:
                break

    return sorted(variants)[:max_variants]


def process_devanagari_words(words_file: str, max_variants: int = 5) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Process Devanagari words: get IPA, generate romanized variants.

    Returns:
        (correction_map, ipa_map) where:
        - correction_map: {romanized_variant: canonical_devanagari}
        - ipa_map: {romanized_variant: ipa}
    """
    import epitran

    logger.info("Initializing epitran hin-Deva...")
    epi = epitran.Epitran("hin-Deva")

    with open(words_file, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]

    logger.info(f"Processing {len(words)} Devanagari words...")

    correction_map = {}
    ipa_map = {}
    total_variants = 0
    errors = 0

    for i, word in enumerate(words):
        if i % 1000 == 0 and i > 0:
            logger.info(f"  Progress: {i}/{len(words)} ({total_variants} variants generated, {errors} errors)")

        try:
            # Get IPA
            ipa = epi.transliterate(word)
            if not ipa or len(ipa) < 2:
                continue

            # Generate romanized variants
            variants = ipa_to_roman_variants(ipa, max_variants=max_variants)

            # Map all variants to the canonical word
            for variant in variants:
                if variant not in correction_map:  # don't overwrite existing
                    correction_map[variant] = word
                    ipa_map[variant] = ipa
                    total_variants += 1

        except Exception as e:
            errors += 1
            if errors < 5:
                logger.warning(f"  Error on '{word}': {e}")

    logger.info(f"Done! Generated {total_variants} romanized variants from {len(words)} words ({errors} errors)")
    return correction_map, ipa_map


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Expand dhwani lexicon with romanized variants")
    parser.add_argument("--devanagari", type=str, required=True, help="Devanagari word list")
    parser.add_argument("--output", type=str, default="dhwani/lexicon/", help="Output directory")
    parser.add_argument("--max-variants", type=int, default=5, help="Max romanized variants per word")
    parser.add_argument("--merge", action="store_true", help="Merge with existing lexicon files")
    args = parser.parse_args()

    correction_map, ipa_map = process_devanagari_words(args.devanagari, args.max_variants)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.merge:
        # Load existing and merge (existing takes priority)
        existing_correction = {}
        existing_ipa = {}
        correction_path = output_dir / "correction_map.json"
        ipa_path = output_dir / "ipa_map.json"

        if correction_path.exists():
            with open(correction_path, "r", encoding="utf-8") as f:
                existing_correction = json.load(f)
        if ipa_path.exists():
            with open(ipa_path, "r", encoding="utf-8") as f:
                existing_ipa = json.load(f)

        # New entries only added if not already present
        for k, v in correction_map.items():
            if k not in existing_correction:
                existing_correction[k] = v
        for k, v in ipa_map.items():
            if k not in existing_ipa:
                existing_ipa[k] = v

        correction_map = existing_correction
        ipa_map = existing_ipa

    # Save
    with open(output_dir / "correction_map.json", "w", encoding="utf-8") as f:
        json.dump(correction_map, f, ensure_ascii=False, indent=2)
    with open(output_dir / "ipa_map.json", "w", encoding="utf-8") as f:
        json.dump(ipa_map, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved to {output_dir}:")
    logger.info(f"  correction_map.json: {len(correction_map)} entries")
    logger.info(f"  ipa_map.json: {len(ipa_map)} entries")
