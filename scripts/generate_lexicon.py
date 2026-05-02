"""Generate a large Hinglish lexicon using IndicXlit + epitran on HPC.

Two passes:
1. Romanized words -> IndicXlit -> Devanagari -> epitran -> IPA
   Output: {romanized: {devanagari: "...", ipa: "..."}}

2. Devanagari words -> epitran -> IPA, then reverse-transliterate to get romanized variants
   Output: same format, more coverage

The output JSON is used by dhwani's corrector for instant lookups.

Usage:
    python scripts/generate_lexicon.py --romanized data/romanized_words.txt --devanagari data/devanagari_words.txt --output dhwani/lexicon/hinglish_lexicon.json
"""

import argparse
import json
import logging
import sys
import torch
import argparse as _argparse
from pathlib import Path
from typing import Dict

# Fix for PyTorch 2.6+ security change
torch.serialization.add_safe_globals([_argparse.Namespace])

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def process_romanized_words(words_file: str) -> Dict[str, dict]:
    """Process romanized Hinglish words through IndicXlit + epitran.

    Returns: {word: {"devanagari": "...", "ipa": "..."}}
    """
    from ai4bharat.transliteration import XlitEngine
    import epitran

    logger.info("Initializing IndicXlit engine...")
    xlit = XlitEngine("hi", beam_width=10, rescore=True)

    logger.info("Initializing epitran engine...")
    epi = epitran.Epitran("hin-Deva")

    # Load words
    with open(words_file, "r", encoding="utf-8") as f:
        words = [line.strip().lower() for line in f if line.strip() and not line.startswith("#")]

    logger.info(f"Processing {len(words)} romanized words...")
    lexicon = {}
    errors = 0

    for i, word in enumerate(words):
        if i % 200 == 0 and i > 0:
            logger.info(f"  Progress: {i}/{len(words)} ({errors} errors)")

        try:
            # Get top Devanagari candidate
            result = xlit.translit_word(word, topk=1)
            candidates = result.get("hi", [])
            if not candidates:
                continue

            devanagari = candidates[0]

            # Get IPA from Devanagari
            ipa = epi.transliterate(devanagari)
            if not ipa:
                continue

            lexicon[word] = {
                "devanagari": devanagari,
                "ipa": ipa,
            }

        except Exception as e:
            errors += 1
            if errors < 10:
                logger.warning(f"  Error on '{word}': {e}")

    logger.info(f"Processed {len(lexicon)}/{len(words)} romanized words ({errors} errors)")
    return lexicon


def process_devanagari_words(words_file: str) -> Dict[str, dict]:
    """Process Devanagari words through epitran for IPA.

    Returns: {devanagari_word: {"devanagari": "...", "ipa": "..."}}
    """
    import epitran

    logger.info("Initializing epitran engine...")
    epi = epitran.Epitran("hin-Deva")

    # Load words
    with open(words_file, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    logger.info(f"Processing {len(words)} Devanagari words...")
    lexicon = {}
    errors = 0

    for i, word in enumerate(words):
        if i % 500 == 0 and i > 0:
            logger.info(f"  Progress: {i}/{len(words)} ({errors} errors)")

        try:
            ipa = epi.transliterate(word)
            if not ipa:
                continue

            # Store with a dev prefix to distinguish
            lexicon[f"__dev__{word}"] = {
                "devanagari": word,
                "ipa": ipa,
            }

        except Exception as e:
            errors += 1
            if errors < 10:
                logger.warning(f"  Error on '{word}': {e}")

    logger.info(f"Processed {len(lexicon)}/{len(words)} Devanagari words ({errors} errors)")
    return lexicon


def build_correction_map(lexicon: Dict[str, dict]) -> Dict[str, str]:
    """Build the final correction map: {romanized_word: devanagari}.

    This is what the corrector uses for instant lookups.
    """
    correction_map = {}
    for key, value in lexicon.items():
        if not key.startswith("__dev__"):
            correction_map[key] = value["devanagari"]
    return correction_map


def build_ipa_map(lexicon: Dict[str, dict]) -> Dict[str, str]:
    """Build IPA lookup map: {romanized_word: ipa}.

    This is what the IPA module uses for instant lookups.
    """
    ipa_map = {}
    for key, value in lexicon.items():
        if not key.startswith("__dev__"):
            ipa_map[key] = value["ipa"]
    return ipa_map


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Hinglish lexicon for dhwani")
    parser.add_argument("--romanized", type=str, help="Romanized word list file")
    parser.add_argument("--devanagari", type=str, help="Devanagari word list file")
    parser.add_argument("--output", type=str, default="dhwani/lexicon/hinglish_lexicon.json",
                        help="Output JSON lexicon file")
    args = parser.parse_args()

    full_lexicon = {}

    # Process romanized words (needs IndicXlit + epitran)
    if args.romanized and Path(args.romanized).exists():
        roman_lex = process_romanized_words(args.romanized)
        full_lexicon.update(roman_lex)

    # Process Devanagari words (needs epitran only)
    if args.devanagari and Path(args.devanagari).exists():
        dev_lex = process_devanagari_words(args.devanagari)
        full_lexicon.update(dev_lex)

    if not full_lexicon:
        logger.error("No words processed! Check input files.")
        sys.exit(1)

    # Build output maps
    correction_map = build_correction_map(full_lexicon)
    ipa_map = build_ipa_map(full_lexicon)

    # Save everything
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Main lexicon (full data)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(full_lexicon, f, ensure_ascii=False, indent=2)

    # Correction map (romanized -> devanagari)
    correction_path = output_path.parent / "correction_map.json"
    with open(correction_path, "w", encoding="utf-8") as f:
        json.dump(correction_map, f, ensure_ascii=False, indent=2)

    # IPA map (romanized -> ipa)
    ipa_path = output_path.parent / "ipa_map.json"
    with open(ipa_path, "w", encoding="utf-8") as f:
        json.dump(ipa_map, f, ensure_ascii=False, indent=2)

    logger.info(f"Done! Output files:")
    logger.info(f"  Full lexicon: {output_path} ({len(full_lexicon)} entries)")
    logger.info(f"  Correction map: {correction_path} ({len(correction_map)} entries)")
    logger.info(f"  IPA map: {ipa_path} ({len(ipa_map)} entries)")
