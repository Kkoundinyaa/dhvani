"""Extract unique Hindi/Hinglish words from available datasets.

Sources:
1. Our curated Hinglish wordlist (data/hinglish_wordlist.txt)
2. Hindi dataset (krishna_proj/hindi_dataset/train.csv) - extract Devanagari words
3. Common Hinglish words from social media (hardcoded high-frequency list)

Output: A consolidated wordlist with both Devanagari and Romanized Hindi words.
"""

import csv
import os
import re
import sys
from collections import Counter
from pathlib import Path

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]+")
LATIN_WORD_RE = re.compile(r"[a-zA-Z]+")


def extract_devanagari_words(csv_path: str, max_rows: int = 20000) -> Counter:
    """Extract all Devanagari words from the Hindi dataset CSV."""
    word_counts = Counter()
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= max_rows:
                break
            text = row.get("text", "")
            words = DEVANAGARI_RE.findall(text)
            for w in words:
                if len(w) >= 2:  # skip single chars
                    word_counts[w] += 1
    return word_counts


def load_hinglish_wordlist(path: str) -> list:
    """Load our curated Hinglish wordlist."""
    words = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            words.append(line.lower())
    return words


# High-frequency Hinglish words from social media (common on Twitter/Reddit/YT)
SOCIAL_MEDIA_HINGLISH = [
    # Expressions
    "lmao", "rofl", "haha", "hehe", "lol",
    # Common Hinglish internet words
    "sahi", "mast", "zabardast", "bekar", "bakwas", "faltu", "kamaal",
    "pagal", "bewakoof", "chutiya", "gaandu", "bhosdike",
    "dhamaal", "dhakkan", "chirkut", "fattu", "jhandu",
    # Hinglish verbs (informal)
    "karega", "karegi", "karenge", "karunga", "karungi",
    "jayega", "jayegi", "jayenge", "jaunga", "jaungi",
    "aayega", "aayegi", "aayenge", "aaunga", "aaungi",
    "milega", "milegi", "milenge", "milunga",
    "dikhega", "dikhegi", "dikhenge",
    "hoga", "hogi", "honge",
    "chahiye", "chahie", "chaiye",
    "sakta", "sakti", "sakte",
    "wala", "wali", "wale", "waala", "waali", "waale",
    # Social/relationship
    "bhabhi", "jiju", "behen", "didi", "chacha", "chachi",
    "mama", "mami", "nana", "nani", "dada", "dadi",
    "rishtedaar", "padosi", "saheli", "pagli",
    # Food & daily life
    "chai", "doodh", "roti", "daal", "sabzi", "biryani",
    "samosa", "pakoda", "paratha", "chapati", "naan",
    "mithai", "laddu", "barfi", "gulab", "jamun",
    "rickshaw", "auto", "metro", "dhaba", "jugaad",
    # Feelings & states
    "pareshan", "khush", "dukhi", "gussa", "naraz",
    "thak", "thaka", "thaki", "bore", "excited",
    "tension", "stress", "chill", "relax", "maza",
    # Money & work
    "paisa", "paise", "rupay", "rupaye", "naukri",
    "tankhwah", "salary", "office", "meeting", "kaam",
    # Time expressions
    "subah", "dopahar", "shaam", "raat", "aaj",
    "kal", "parso", "narso", "haftah", "mahina", "saal",
    # Intensifiers & fillers
    "ekdum", "poora", "sach", "pakka", "seedha",
    "sidha", "ulta", "seedhe", "sachchi", "jhooth",
    # Question patterns
    "kisko", "kisme", "kisse", "kiski", "kiska",
    "kisliye", "kab", "kahaan", "kahin", "kidhar",
    # Conjunctions & connectors
    "warna", "nahi_toh", "tabhi", "isiliye", "haalaki",
    "lekin", "magar", "parantu", "kyunki", "taaki",
    # Common verb forms
    "baith", "baitho", "baithiye",
    "uth", "utho", "uthiye",
    "so", "soyo", "sona", "soja",
    "kha", "khao", "khaiye", "khale",
    "pi", "piyo", "peelo",
    "padh", "padho", "padhle",
    "likh", "likho", "likhle",
    "bhej", "bhejo", "bhejdo",
    "rakh", "rakho", "rakhdo",
    "band", "bando", "bandh", "bandho",
    "khol", "kholo", "kholdo",
    # Slang & modern
    "scene", "setting", "jugaad", "fundaa", "funda",
    "bindaas", "timepass", "chillam", "vella", "lafda",
    "chamcha", "kachra", "bakchodi", "gandi", "harami",
]


def main():
    # Update this path to your local project root
    project_root = Path(os.environ.get("DHWANI_PROJECT_ROOT", "/users/PAS2836/krishnakb/ondemand/krishna_proj"))
    output_dir = project_root / "dhwani" / "data"

    # 1. Load curated wordlist
    hinglish_words = load_hinglish_wordlist(str(output_dir / "hinglish_wordlist.txt"))
    print(f"Curated wordlist: {len(hinglish_words)} words")

    # 2. Extract Devanagari words from Hindi dataset
    hindi_csv = project_root / "hindi_dataset" / "train.csv"
    if hindi_csv.exists():
        dev_counts = extract_devanagari_words(str(hindi_csv))
        # Take top 10K most frequent
        top_devanagari = [w for w, _ in dev_counts.most_common(10000)]
        print(f"Devanagari words from dataset: {len(top_devanagari)} (top 10K)")
    else:
        top_devanagari = []
        print("Hindi dataset not found, skipping")

    # 3. Social media words
    social_words = SOCIAL_MEDIA_HINGLISH
    print(f"Social media Hinglish: {len(social_words)} words")

    # 4. Combine and deduplicate
    all_romanized = list(set(hinglish_words + social_words))
    all_devanagari = list(set(top_devanagari))

    # Write output files
    roman_out = output_dir / "romanized_words.txt"
    dev_out = output_dir / "devanagari_words.txt"

    with open(roman_out, "w", encoding="utf-8") as f:
        for w in sorted(all_romanized):
            f.write(w + "\n")

    with open(dev_out, "w", encoding="utf-8") as f:
        for w in sorted(all_devanagari):
            f.write(w + "\n")

    print(f"\nOutput:")
    print(f"  Romanized words: {roman_out} ({len(all_romanized)} words)")
    print(f"  Devanagari words: {dev_out} ({len(all_devanagari)} words)")
    print(f"  Total unique words: {len(all_romanized) + len(all_devanagari)}")


if __name__ == "__main__":
    main()
