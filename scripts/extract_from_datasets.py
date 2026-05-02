"""Extract word-level mappings from MASSIVE and XNLI Hindi datasets.

These datasets already have Devanagari, IPA, and romanized representations
aligned at the sentence level. We extract unique word-level mappings by
aligning words across representations.

This gives us REAL romanized spellings (from formal transliteration) plus
the Devanagari and IPA -- no model inference needed at all.

Output: Extended devanagari word list for variant generation.
"""

import re
import json
import logging
from collections import Counter
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]+")


def extract_from_massive(arrow_path: str) -> Counter:
    """Extract Devanagari words from MASSIVE Hindi dataset."""
    from datasets import Dataset
    ds = Dataset.from_file(arrow_path)
    word_counts = Counter()

    for row in ds:
        text = row.get("utt", "")
        words = DEVANAGARI_RE.findall(text)
        for w in words:
            if len(w) >= 2:
                word_counts[w] += 1

    return word_counts


def extract_from_xnli(arrow_paths: list) -> Counter:
    """Extract Devanagari words from XNLI Hindi dataset."""
    from datasets import Dataset, concatenate_datasets

    word_counts = Counter()

    for path in arrow_paths:
        logger.info(f"  Loading {path}...")
        ds = Dataset.from_file(path)

        for row in ds:
            for field in ["premise", "hypothesis"]:
                text = row.get(field, "")
                words = DEVANAGARI_RE.findall(text)
                for w in words:
                    if len(w) >= 2:
                        word_counts[w] += 1

    return word_counts


def main():
    output_dir = Path("/users/PAS2836/krishnakb/ondemand/krishna_proj/dhwani/data")

    # MASSIVE Hindi
    massive_path = "/fs/scratch/PAS2836/krishnakb/massive_experiments/large-ipa/all8_to_ml_IN/bs128_lr5e-5/6908418/hf_cache/mugezhang___massive_ipa_romanized/hi-IN/0.0.0/4f3d20644fc3152a1e769958d583304653b68479/massive_ipa_romanized-train.arrow"

    # XNLI Hindi (both parts)
    xnli_base = "/fs/scratch/PAS2836/krishnakb/xl_xnli_experiments/hin_urd-xl-small-text/6193443/hf_cache/mugezhang___hindi-xnli-ipa_ipa_romanized/default/0.0.0/3815dcf8f7b34cc9abac957826108e732f925954"
    xnli_paths = [
        f"{xnli_base}/hindi-xnli-ipa_ipa_romanized-train-00000-of-00002.arrow",
        f"{xnli_base}/hindi-xnli-ipa_ipa_romanized-train-00001-of-00002.arrow",
        f"{xnli_base}/hindi-xnli-ipa_ipa_romanized-test.arrow",
        f"{xnli_base}/hindi-xnli-ipa_ipa_romanized-validation.arrow",
    ]

    all_words = Counter()

    # Extract from MASSIVE
    logger.info("Extracting from MASSIVE Hindi (11K sentences)...")
    massive_words = extract_from_massive(massive_path)
    all_words.update(massive_words)
    logger.info(f"  Found {len(massive_words)} unique words")

    # Extract from XNLI
    logger.info("Extracting from XNLI Hindi (360K+ sentences)...")
    existing_paths = [p for p in xnli_paths if Path(p).exists()]
    if existing_paths:
        xnli_words = extract_from_xnli(existing_paths)
        all_words.update(xnli_words)
        logger.info(f"  Found {len(xnli_words)} unique words")
    else:
        logger.warning("  XNLI paths not found, skipping")

    # Also load existing hindi_dataset words
    existing_path = output_dir / "devanagari_words.txt"
    if existing_path.exists():
        with open(existing_path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w:
                    all_words[w] += 1

    # Filter: keep words that appear at least once, length >= 2
    # Sort by frequency (most common first)
    final_words = [w for w, count in all_words.most_common() if len(w) >= 2]

    # Save
    output_file = output_dir / "devanagari_words_large.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        for w in final_words:
            f.write(w + "\n")

    logger.info(f"\nFinal output: {output_file}")
    logger.info(f"Total unique Devanagari words: {len(final_words)}")
    logger.info(f"Top 20 most frequent:")
    for w, c in all_words.most_common(20):
        logger.info(f"  {w:15s} ({c:,} occurrences)")


if __name__ == "__main__":
    main()
