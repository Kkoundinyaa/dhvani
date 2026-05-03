"""Massively expand the dhwani lexicon using Hindi Wikipedia + IITB corpus + social media slang.

Strategy:
1. Extract Devanagari words from Hindi Wikipedia (150K+ articles)
2. Extract from IITB Hindi-English parallel corpus (1.5M sentences)
3. Add hand-curated social media abbreviations/slang
4. Generate romanized spelling variants via IPA (up to 10 per word)
5. Merge with existing 151K lexicon

Target: 500K-1M entries

Usage:
    python scripts/expand_lexicon_v2.py [--max-wiki-articles 50000] [--max-variants 10]

Requires: epitran, datasets
"""

import argparse
import json
import logging
import re
import sys
from collections import Counter
from itertools import product
from pathlib import Path
from typing import Dict, List, Set, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]+")

# ============================================================
# Social media abbreviations & slang (hand-curated)
# These will NEVER appear in formal datasets.
# Format: romanized -> (devanagari, ipa)
# ============================================================
SOCIAL_MEDIA_SLANG = {
    # Single letter abbreviations
    "h": ("है", "ɦɛː"),
    "k": ("क", "kə"),
    "m": ("में", "mẽː"),
    "r": ("र", "ɾə"),
    "b": ("ब", "bə"),
    "n": ("न", "nə"),
    "v": ("व", "ʋə"),
    "u": ("यू", "juː"),
    # Common abbreviations
    "kr": ("कर", "kəɾ"),
    "krr": ("कर", "kəɾ"),
    "kro": ("करो", "kəɾoː"),
    "krna": ("करना", "kəɾnaː"),
    "krke": ("करके", "kəɾkeː"),
    "krega": ("करेगा", "kəɾeːɡaː"),
    "kregi": ("करेगी", "kəɾeːɡiː"),
    "krega": ("करेगा", "kəɾeːɡaː"),
    "krdiya": ("कर दिया", "kəɾd̪ɪjaː"),
    "krrha": ("कर रहा", "kəɾɾəɦaː"),
    "karra": ("कर रहा", "kəɾɾəɦaː"),
    "karr": ("कर", "kəɾ"),
    "karre": ("कर रहे", "kəɾɾəɦeː"),
    "karha": ("कर रहा", "kəɾɾəɦaː"),
    "karrha": ("कर रहा", "kəɾɾəɦaː"),
    "mt": ("मत", "mət̪"),
    "nhi": ("नहीं", "nəɦĩː"),
    "ni": ("नहीं", "nəɦĩː"),
    "nai": ("नहीं", "nəɦĩː"),
    "nh": ("नहीं", "nəɦĩː"),
    "yr": ("यार", "jaːɾ"),
    "yrrr": ("यार", "jaːɾ"),
    "yarr": ("यार", "jaːɾ"),
    "yarrr": ("यार", "jaːɾ"),
    "bro": ("भाई", "bʱaːiː"),
    "bhai": ("भाई", "bʱaːiː"),
    "bro": ("भाई", "bʱaːiː"),
    "bhaiya": ("भैया", "bʱɛːjaː"),
    "bhaiyya": ("भैया", "bʱɛːjaː"),
    "bc": ("बीसी", "biːsiː"),
    "mc": ("एमसी", "eːmsiː"),
    "lol": ("लोल", "loːl"),
    "lmao": ("lmao", ""),
    "btw": ("btw", ""),
    "pls": ("प्लीज़", "pliːz"),
    "plz": ("प्लीज़", "pliːz"),
    "thnx": ("थैंक्स", "tʰɛːŋks"),
    "thx": ("थैंक्स", "tʰɛːŋks"),
    "msg": ("मैसेज", "mɛːseːd͡ʒ"),
    "dm": ("डीएम", "ɖiːeːm"),
    # Contracted verb forms
    "rha": ("रहा", "ɾəɦaː"),
    "rhi": ("रही", "ɾəɦiː"),
    "rhe": ("रहे", "ɾəɦeː"),
    "tha": ("था", "t̪ʰaː"),
    "thi": ("थी", "t̪ʰiː"),
    "ho": ("हो", "ɦoː"),
    "hai": ("है", "ɦɛː"),
    "hain": ("हैं", "ɦɛ̃ː"),
    "hn": ("हां", "ɦãː"),
    "hmm": ("हम्म", "ɦəmm"),
    "hm": ("हम", "ɦəm"),
    "haa": ("हां", "ɦãː"),
    "han": ("हां", "ɦãː"),
    "ji": ("जी", "d͡ʒiː"),
    "jii": ("जी", "d͡ʒiː"),
    # Common social media words
    "acha": ("अच्छा", "ət͡ʃːʰaː"),
    "achaa": ("अच्छा", "ət͡ʃːʰaː"),
    "achchha": ("अच्छा", "ət͡ʃːʰaː"),
    "thik": ("ठीक", "ʈʰiːk"),
    "thk": ("ठीक", "ʈʰiːk"),
    "tik": ("ठीक", "ʈʰiːk"),
    "tikhe": ("ठीक है", "ʈʰiːkɦɛː"),
    "theekhai": ("ठीक है", "ʈʰiːkɦɛː"),
    "sahi": ("सही", "səɦiː"),
    "shi": ("सही", "səɦiː"),
    "shi": ("सही", "səɦiː"),
    "sb": ("सब", "səb"),
    "sbko": ("सबको", "səbkoː"),
    "sbse": ("सबसे", "səbseː"),
    "kyu": ("क्यूं", "kjũː"),
    "kyn": ("क्यूं", "kjũː"),
    "kyun": ("क्यूं", "kjũː"),
    "q": ("क्यूं", "kjũː"),
    "kidhr": ("किधर", "kɪd̪ʱəɾ"),
    "kidr": ("किधर", "kɪd̪ʱəɾ"),
    "udhr": ("उधर", "ʊd̪ʱəɾ"),
    "idhr": ("इधर", "ɪd̪ʱəɾ"),
    "wha": ("वहां", "ʋəɦãː"),
    "yha": ("यहां", "jəɦãː"),
    "wahan": ("वहां", "ʋəɦãː"),
    "yahan": ("यहां", "jəɦãː"),
    "abhi": ("अभी", "əbʱiː"),
    "abh": ("अभी", "əbʱiː"),
    "abi": ("अभी", "əbʱiː"),
    "bs": ("बस", "bəs"),
    "bas": ("बस", "bəs"),
    "bss": ("बस", "bəs"),
    "fir": ("फिर", "pʰɪɾ"),
    "phir": ("फिर", "pʰɪɾ"),
    "fr": ("फिर", "pʰɪɾ"),
    "tb": ("तब", "t̪əb"),
    "tab": ("तब", "t̪əb"),
    "jb": ("जब", "d͡ʒəb"),
    "jab": ("जब", "d͡ʒəb"),
    "kb": ("कब", "kəb"),
    "kab": ("कब", "kəb"),
    "lg": ("लग", "ləɡ"),
    "lga": ("लगा", "ləɡaː"),
    "lgta": ("लगता", "ləɡt̪aː"),
    "lgra": ("लग रहा", "ləɡɾəɦaː"),
    "bnda": ("बंदा", "bən̪d̪aː"),
    "bndi": ("बंदी", "bən̪d̪iː"),
    "bnd": ("बंद", "bən̪d̪"),
    "smjh": ("समझ", "səməd͡ʒʱ"),
    "smj": ("समझ", "səməd͡ʒʱ"),
    "btao": ("बताओ", "bət̪aːoː"),
    "bta": ("बता", "bət̪aː"),
    "btana": ("बताना", "bət̪aːnaː"),
    "btade": ("बता दे", "bət̪aːd̪eː"),
    "pta": ("पता", "pət̪aː"),
    "pta": ("पता", "pət̪aː"),
    "ptani": ("पता नहीं", "pət̪aːnəɦĩː"),
    "dkh": ("देख", "d̪eːkʰ"),
    "dekh": ("देख", "d̪eːkʰ"),
    "dkhle": ("देख ले", "d̪eːkʰleː"),
    "chl": ("चल", "t͡ʃəl"),
    "chlo": ("चलो", "t͡ʃəloː"),
    "chlna": ("चलना", "t̪͡ʃəlnaː"),
    "chle": ("चले", "t͡ʃəleː"),
    "agya": ("आ गया", "aːɡəjaː"),
    "hogya": ("हो गया", "ɦoːɡəjaː"),
    "hogyi": ("हो गई", "ɦoːɡəiː"),
    "krdia": ("कर दिया", "kəɾd̪ɪjaː"),
    "dedia": ("दे दिया", "d̪eːd̪ɪjaː"),
    "lelia": ("ले लिया", "leːlɪjaː"),
    "aaja": ("आ जा", "aːd͡ʒaː"),
    "aajao": ("आ जाओ", "aːd͡ʒaːoː"),
    "jaana": ("जाना", "d͡ʒaːnaː"),
    "jana": ("जाना", "d͡ʒaːnaː"),
    "ruk": ("रुक", "ɾʊk"),
    "rukk": ("रुक", "ɾʊk"),
    "rkho": ("रखो", "ɾəkʰoː"),
    "rkh": ("रख", "ɾəkʰ"),
    "suno": ("सुनो", "sʊnoː"),
    "sun": ("सुन", "sʊn"),
    "sunna": ("सुनना", "sʊnnaː"),
    "bolo": ("बोलो", "boːloː"),
    "bol": ("बोल", "boːl"),
    "bolna": ("बोलना", "boːlnaː"),
    "bola": ("बोला", "boːlaː"),
    "boli": ("बोली", "boːliː"),
    "bole": ("बोले", "boːleː"),
    "mko": ("मुझको", "mʊd͡ʒʱkoː"),
    "mjhe": ("मुझे", "mʊd͡ʒʱeː"),
    "tko": ("तुझको", "t̪ʊd͡ʒʱkoː"),
    "tjhe": ("तुझे", "t̪ʊd͡ʒʱeː"),
    "usko": ("उसको", "ʊskoː"),
    "usse": ("उससे", "ʊsseː"),
    "iske": ("इसके", "ɪskeː"),
    "uske": ("उसके", "ʊskeː"),
    "apna": ("अपना", "əpnaː"),
    "apni": ("अपनी", "əpniː"),
    "apne": ("अपने", "əpneː"),
    "mera": ("मेरा", "meːɾaː"),
    "meri": ("मेरी", "meːɾiː"),
    "mere": ("मेरे", "meːɾeː"),
    "tera": ("तेरा", "t̪eːɾaː"),
    "teri": ("तेरी", "t̪eːɾiː"),
    "tere": ("तेरे", "t̪eːɾeː"),
    "hmara": ("हमारा", "ɦəmaːɾaː"),
    "hmari": ("हमारी", "ɦəmaːɾiː"),
    "hmare": ("हमारे", "ɦəmaːɾeː"),
    "tmhara": ("तुम्हारा", "t̪ʊmɦaːɾaː"),
    "tmhari": ("तुम्हारी", "t̪ʊmɦaːɾiː"),
    "tmhare": ("तुम्हारे", "t̪ʊmɦaːɾeː"),
    "tumhara": ("तुम्हारा", "t̪ʊmɦaːɾaː"),
    "tumhari": ("तुम्हारी", "t̪ʊmɦaːɾiː"),
    "tumhare": ("तुम्हारे", "t̪ʊmɦaːɾeː"),
    "unka": ("उनका", "ʊnkaː"),
    "unki": ("उनकी", "ʊnkiː"),
    "unke": ("उनके", "ʊnkeː"),
    "inka": ("इनका", "ɪnkaː"),
    "inki": ("इनकी", "ɪnkiː"),
    "inke": ("इनके", "ɪnkeː"),
    # Question words abbreviated
    "kya": ("क्या", "kjaː"),
    "kaise": ("कैसे", "kɛːseː"),
    "kse": ("कैसे", "kɛːseː"),
    "kahan": ("कहां", "kəɦãː"),
    "kha": ("कहां", "kəɦãː"),
    "kaun": ("कौन", "kɔːn"),
    "kon": ("कौन", "kɔːn"),
    "kitna": ("कितना", "kɪt̪naː"),
    "kitni": ("कितनी", "kɪt̪niː"),
    "kitne": ("कितने", "kɪt̪neː"),
    "kisko": ("किसको", "kɪskoː"),
    "kisse": ("किससे", "kɪsseː"),
    # Emphatic particles
    "bhi": ("भी", "bʱiː"),
    "toh": ("तो", "t̪oː"),
    "to": ("तो", "t̪oː"),
    "na": ("ना", "naː"),
    "hi": ("ही", "ɦiː"),
    "wala": ("वाला", "ʋaːlaː"),
    "wali": ("वाली", "ʋaːliː"),
    "wale": ("वाले", "ʋaːleː"),
    "waala": ("वाला", "ʋaːlaː"),
    "waali": ("वाली", "ʋaːliː"),
    "waale": ("वाले", "ʋaːleː"),
    # Time words
    "aaj": ("आज", "aːd͡ʒ"),
    "kal": ("कल", "kəl"),
    "abhi": ("अभी", "əbʱiː"),
    "baad": ("बाद", "baːd̪"),
    "pehle": ("पहले", "pəɦleː"),
    "phle": ("पहले", "pəɦleː"),
    "phele": ("पहले", "pəɦleː"),
    # Emotions/reactions
    "sach": ("सच", "sət͡ʃ"),
    "sachme": ("सच में", "sət͡ʃmẽː"),
    "sacchi": ("सच्ची", "sət͡ʃːiː"),
    "pakka": ("पक्का", "pəkːaː"),
    "srsly": ("सीरियसली", "siːɾɪjəsliː"),
    "bhot": ("बहुत", "bəɦʊt̪"),
    "bht": ("बहुत", "bəɦʊt̪"),
    "boht": ("बहुत", "bəɦʊt̪"),
    "bhaut": ("बहुत", "bəɦʊt̪"),
    "bht": ("बहुत", "bəɦʊt̪"),
    "zada": ("ज़्यादा", "zjaːd̪aː"),
    "zyada": ("ज़्यादा", "zjaːd̪aː"),
    "zyda": ("ज़्यादा", "zjaːd̪aː"),
    "jyada": ("ज़्यादा", "zjaːd̪aː"),
    "jyda": ("ज़्यादा", "zjaːd̪aː"),
    "koi": ("कोई", "koːiː"),
    "kuch": ("कुछ", "kʊt͡ʃʰ"),
    "kch": ("कुछ", "kʊt͡ʃʰ"),
    "kuchh": ("कुछ", "kʊt͡ʃʰ"),
}


# IPA phoneme to possible romanized spellings
IPA_TO_ROMAN_VARIANTS = {
    # Vowels
    "ə": ["a", ""],
    "aː": ["aa", "a"],
    "ɪ": ["i"],
    "iː": ["ee", "i", "ii"],
    "ʊ": ["u"],
    "uː": ["oo", "u", "uu"],
    "eː": ["e", "ei", "ay"],
    "e": ["e"],
    "æː": ["ai", "e"],
    "ɛː": ["ai", "e", "ae"],
    "oː": ["o", "ou"],
    "o": ["o"],
    "ɔː": ["au", "o", "aw"],
    # Consonants - aspirated
    "kʰ": ["kh", "k"],
    "ɡʱ": ["gh", "g"],
    "t͡ʃʰ": ["chh", "ch", "cch"],
    "d͡ʒʱ": ["jh", "j"],
    "ʈʰ": ["th", "t"],
    "ɖʱ": ["dh", "d"],
    "t̪ʰ": ["th", "t"],
    "d̪ʱ": ["dh", "d"],
    "pʰ": ["ph", "f", "p"],
    "bʱ": ["bh", "b"],
    # Consonants - basic
    "k": ["k", "c", "q"],
    "ɡ": ["g"],
    "g": ["g"],
    "t͡ʃ": ["ch", "c"],
    "d͡ʒ": ["j", "z"],
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
    "j": ["y", ""],
    "ɾ": ["r"],
    "r": ["r"],
    "l": ["l"],
    "ʋ": ["v", "w"],
    "v": ["v", "w"],
    "ʃ": ["sh", "s"],
    "ʂ": ["sh", "s"],
    "s": ["s"],
    "ɦ": ["h", ""],
    "h": ["h"],
    "f": ["f", "ph"],
    "z": ["z", "j"],
    "q": ["q", "k"],
    "x": ["kh"],
    # Plain ASCII variants
    "t": ["t"],
    "d": ["d"],
    "u": ["u"],
    "i": ["i", "ee"],
    "a": ["a"],
    "o": ["o"],
    "e": ["e"],
    # Nasalization
    "\u0303": ["n", "m", ""],
    "̃": ["n", "m", ""],
    # Gemination
    "ː": ["", ""],
    # Common clusters
    "d͡ʒ̤": ["jh", "j"],
    "ɡ̤": ["gh", "g"],
    "t͡ʃt͡ʃʰ": ["cchh", "chch", "ch"],
}

_SORTED_IPA = sorted(IPA_TO_ROMAN_VARIANTS.keys(), key=len, reverse=True)


def ipa_to_roman_variants(ipa: str, max_variants: int = 10) -> List[str]:
    """Generate plausible romanized spellings from an IPA string."""
    phonemes = []
    i = 0
    while i < len(ipa):
        matched = False
        for length in range(min(6, len(ipa) - i), 0, -1):
            chunk = ipa[i:i + length]
            if chunk in IPA_TO_ROMAN_VARIANTS:
                phonemes.append(chunk)
                i += length
                matched = True
                break
        if not matched:
            i += 1

    if not phonemes:
        return []

    roman_options = [IPA_TO_ROMAN_VARIANTS[p] for p in phonemes]

    total_combos = 1
    for opts in roman_options:
        total_combos *= len(opts)

    if total_combos <= max_variants * 3:
        variants = set()
        for combo in product(*roman_options):
            variant = "".join(combo).strip()
            if len(variant) >= 1:
                variants.add(variant)
    else:
        variants = set()
        base = "".join(opts[0] for opts in roman_options)
        if len(base) >= 1:
            variants.add(base)

        for i, opts in enumerate(roman_options):
            for alt in opts[1:]:
                variant = "".join(
                    alt if j == i else roman_options[j][0]
                    for j in range(len(roman_options))
                )
                if len(variant) >= 1:
                    variants.add(variant)
                if len(variants) >= max_variants:
                    break
            if len(variants) >= max_variants:
                break

    return sorted(variants)[:max_variants]


def extract_wikipedia_words(max_articles: int = 50000) -> Counter:
    """Extract Devanagari words from Hindi Wikipedia."""
    from datasets import load_dataset

    logger.info(f"Loading Hindi Wikipedia (streaming, up to {max_articles} articles)...")
    ds = load_dataset("wikimedia/wikipedia", "20231101.hi", split="train", streaming=True)

    word_counts = Counter()
    for i, row in enumerate(ds):
        if i >= max_articles:
            break
        if i % 5000 == 0 and i > 0:
            logger.info(f"  Processed {i} articles, {len(word_counts)} unique words so far...")

        text = row.get("text", "")
        words = DEVANAGARI_RE.findall(text)
        for w in words:
            if 2 <= len(w) <= 20:
                word_counts[w] += 1

    logger.info(f"  Wikipedia: {len(word_counts)} unique Devanagari words from {min(i+1, max_articles)} articles")
    return word_counts


def extract_iitb_words(max_sentences: int = 500000) -> Counter:
    """Extract Devanagari words from IITB Hindi-English parallel corpus."""
    from datasets import load_dataset

    logger.info(f"Loading IITB Hindi-English corpus (streaming, up to {max_sentences} sentences)...")
    ds = load_dataset("cfilt/iitb-english-hindi", split="train", streaming=True)

    word_counts = Counter()
    for i, row in enumerate(ds):
        if i >= max_sentences:
            break
        if i % 50000 == 0 and i > 0:
            logger.info(f"  Processed {i} sentences, {len(word_counts)} unique words so far...")

        translation = row.get("translation", {})
        text = translation.get("hi", "")
        words = DEVANAGARI_RE.findall(text)
        for w in words:
            if 2 <= len(w) <= 20:
                word_counts[w] += 1

    logger.info(f"  IITB: {len(word_counts)} unique Devanagari words from {min(i+1, max_sentences)} sentences")
    return word_counts


def process_devanagari_words(words: List[str], max_variants: int = 10) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Process Devanagari words: get IPA via epitran, generate romanized variants."""
    import epitran

    logger.info("Initializing epitran hin-Deva...")
    epi = epitran.Epitran("hin-Deva")

    logger.info(f"Processing {len(words)} Devanagari words (max {max_variants} variants each)...")

    correction_map = {}
    ipa_map = {}
    total_variants = 0
    errors = 0

    for i, word in enumerate(words):
        if i % 5000 == 0 and i > 0:
            logger.info(f"  Progress: {i}/{len(words)} ({total_variants} variants, {errors} errors)")

        try:
            ipa = epi.transliterate(word)
            if not ipa or len(ipa) < 1:
                continue

            variants = ipa_to_roman_variants(ipa, max_variants=max_variants)

            for variant in variants:
                if variant not in correction_map:
                    correction_map[variant] = word
                    ipa_map[variant] = ipa
                    total_variants += 1

        except Exception as e:
            errors += 1
            if errors < 10:
                logger.warning(f"  Error on '{word}': {e}")

    logger.info(f"Generated {total_variants} romanized variants from {len(words)} words ({errors} errors)")
    return correction_map, ipa_map


def main():
    parser = argparse.ArgumentParser(description="Massively expand dhwani lexicon")
    parser.add_argument("--max-wiki-articles", type=int, default=50000,
                        help="Max Wikipedia articles to process (default: 50000)")
    parser.add_argument("--max-iitb-sentences", type=int, default=500000,
                        help="Max IITB sentences to process (default: 500000)")
    parser.add_argument("--max-variants", type=int, default=10,
                        help="Max romanized variants per word (default: 10)")
    parser.add_argument("--min-freq", type=int, default=2,
                        help="Min word frequency to include (default: 2)")
    parser.add_argument("--output", type=str,
                        default="/users/PAS2836/krishnakb/ondemand/krishna_proj/dhwani/dhwani/lexicon/",
                        help="Output directory")
    parser.add_argument("--skip-wiki", action="store_true", help="Skip Wikipedia extraction")
    parser.add_argument("--skip-iitb", action="store_true", help="Skip IITB extraction")
    args = parser.parse_args()

    all_words = Counter()

    # Load existing Devanagari word lists
    data_dir = Path("/users/PAS2836/krishnakb/ondemand/krishna_proj/dhwani/data")
    for wordfile in ["devanagari_words_large.txt", "devanagari_words.txt"]:
        fpath = data_dir / wordfile
        if fpath.exists():
            with open(fpath, "r", encoding="utf-8") as f:
                for line in f:
                    w = line.strip()
                    if w:
                        all_words[w] += 5  # boost existing words

    logger.info(f"Loaded {len(all_words)} existing Devanagari words")

    # Extract from Wikipedia
    if not args.skip_wiki:
        wiki_words = extract_wikipedia_words(max_articles=args.max_wiki_articles)
        all_words.update(wiki_words)
        logger.info(f"After Wikipedia: {len(all_words)} unique words")

    # Extract from IITB
    if not args.skip_iitb:
        iitb_words = extract_iitb_words(max_sentences=args.max_iitb_sentences)
        all_words.update(iitb_words)
        logger.info(f"After IITB: {len(all_words)} unique words")

    # Filter by frequency
    filtered_words = [w for w, c in all_words.most_common() if c >= args.min_freq and 2 <= len(w) <= 20]
    logger.info(f"After filtering (freq >= {args.min_freq}): {len(filtered_words)} words")

    # Save the expanded Devanagari word list
    expanded_path = data_dir / "devanagari_words_expanded.txt"
    with open(expanded_path, "w", encoding="utf-8") as f:
        for w in filtered_words:
            f.write(w + "\n")
    logger.info(f"Saved expanded word list to {expanded_path}")

    # Generate romanized variants via epitran + IPA
    correction_map, ipa_map = process_devanagari_words(filtered_words, max_variants=args.max_variants)

    # Add social media slang
    slang_added = 0
    for roman, (dev, ipa) in SOCIAL_MEDIA_SLANG.items():
        if roman not in correction_map and ipa:
            correction_map[roman] = dev
            ipa_map[roman] = ipa
            slang_added += 1
    logger.info(f"Added {slang_added} social media slang entries")

    # Merge with existing lexicon
    output_dir = Path(args.output)
    correction_path = output_dir / "correction_map.json"
    ipa_path = output_dir / "ipa_map.json"

    existing_correction = {}
    existing_ipa = {}
    if correction_path.exists():
        with open(correction_path, "r", encoding="utf-8") as f:
            existing_correction = json.load(f)
        logger.info(f"Loaded existing correction_map: {len(existing_correction)} entries")
    if ipa_path.exists():
        with open(ipa_path, "r", encoding="utf-8") as f:
            existing_ipa = json.load(f)
        logger.info(f"Loaded existing ipa_map: {len(existing_ipa)} entries")

    # Existing entries take priority (they're verified)
    new_correction = 0
    new_ipa = 0
    for k, v in correction_map.items():
        if k not in existing_correction:
            existing_correction[k] = v
            new_correction += 1
    for k, v in ipa_map.items():
        if k not in existing_ipa:
            existing_ipa[k] = v
            new_ipa += 1

    logger.info(f"New entries added: {new_correction} correction, {new_ipa} IPA")
    logger.info(f"Final lexicon size: {len(existing_correction)} correction, {len(existing_ipa)} IPA")

    # Save
    with open(correction_path, "w", encoding="utf-8") as f:
        json.dump(existing_correction, f, ensure_ascii=False)
    with open(ipa_path, "w", encoding="utf-8") as f:
        json.dump(existing_ipa, f, ensure_ascii=False)

    logger.info(f"Saved to {output_dir}")
    logger.info("Done!")


if __name__ == "__main__":
    main()
