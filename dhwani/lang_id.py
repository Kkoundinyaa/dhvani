"""Word-level language identification for Hinglish text.

Classifies each word as:
- "hi": Hindi written in Latin script (Romanized)
- "hi_dev": Hindi written in Devanagari
- "en": English
"""

import re
from typing import List

# Devanagari Unicode range
DEVANAGARI_RANGE = re.compile(r"[\u0900-\u097F]")

# Common English words (top ~200 function words + common words)
# This is a fast heuristic; we don't need 100% accuracy
ENGLISH_WORDS = frozenset([
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "can", "could", "must", "need", "dare",
    "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
    "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "because", "but", "and", "or", "if", "while", "about", "up",
    "this", "that", "these", "those", "i", "me", "my", "myself", "we",
    "our", "you", "your", "he", "him", "his", "she", "her", "it", "its",
    "they", "them", "their", "what", "which", "who", "whom", "whose",
    "movie", "film", "phone", "time", "good", "bad", "best", "worst",
    "like", "love", "hate", "want", "know", "think", "see", "look",
    "come", "go", "get", "make", "say", "tell", "give", "take", "find",
    "new", "old", "great", "big", "small", "long", "little", "much",
    "right", "well", "also", "back", "now", "still", "already", "always",
    "never", "ever", "even", "really", "very", "too", "quite", "actually",
    "ok", "okay", "yes", "no", "yeah", "please", "thanks", "sorry",
])

# Common Romanized Hindi words (high-frequency indicators)
HINDI_WORDS = frozenset([
    "hai", "he", "ho", "hain", "tha", "thi", "the", "hoga", "hogi",
    "ka", "ki", "ke", "ko", "se", "me", "mein", "par", "pe", "tak",
    "aur", "ya", "bhi", "hi", "na", "nahi", "nahin", "mat", "bas",
    "kya", "kaise", "kab", "kahan", "kaun", "kitna", "kitne", "kitni",
    "ye", "yeh", "wo", "woh", "wahi", "yahi", "iska", "uska", "unka",
    "mera", "tera", "humara", "tumhara", "apna", "apne", "apni",
    "accha", "acha", "achha", "bura", "sahi", "galat", "theek", "thik",
    "bahut", "bohot", "boht", "bahot", "zyada", "kam", "thoda", "kuch",
    "ab", "abhi", "tab", "jab", "phir", "fir", "pehle", "baad",
    "yaar", "yr", "bhai", "bro", "dude", "re", "arre", "are",
    "karo", "karna", "kar", "kiya", "karke", "karunga", "karungi",
    "dekho", "dekhna", "dekh", "dekha", "dekhte", "dikhao",
    "bolo", "bolna", "bol", "bola", "bolte", "batao", "bata",
    "chalo", "chalna", "chal", "chala", "chalte", "jao", "jana", "ja",
    "aao", "aana", "aa", "aaya", "aayi", "aaye",
    "lelo", "lena", "le", "liya", "liye", "lete",
    "do", "dena", "de", "diya", "diye", "dete",
    "khana", "pani", "ghar", "kaam", "paisa", "log", "wala", "wali",
    "sab", "sabhi", "koi", "kahin", "kabhi", "hamesha",
    "ek", "do", "teen", "char", "panch",
    "lekin", "magar", "kyunki", "isliye", "toh", "to",
    "nhi", "ni", "h", "hn", "hm", "hmm",
    "samajh", "samjh", "pata", "malum", "matlab",
    "bilkul", "zarur", "zaroor", "shayad", "lagta", "lagti",
])

# Characters that only appear in Hindi romanization (retroflex representations)
HINDI_CHAR_PATTERNS = re.compile(
    r"(aa|ee|oo|ai|au|bh|ch|dh|gh|jh|kh|ph|sh|th|"
    r"chh|shh|ng|nk|gy|dy|"
    r"\bji\b|\bji$|\bwala\b|\bwali\b|\bwale\b)"
)


def is_devanagari(word: str) -> bool:
    """Check if word contains Devanagari characters."""
    return bool(DEVANAGARI_RANGE.search(word))


def classify_word(word: str) -> str:
    """Classify a single word as 'hi', 'en', or 'hi_dev'."""
    clean = word.lower().strip(".,!?;:'\"()-")

    if not clean:
        return "en"

    if is_devanagari(clean):
        return "hi_dev"

    # Check known word lists
    if clean in HINDI_WORDS:
        return "hi"
    if clean in ENGLISH_WORDS:
        return "en"

    # Heuristic: words with Hindi-typical character patterns
    if HINDI_CHAR_PATTERNS.search(clean):
        return "hi"

    # Heuristic: very short abbreviations common in Hinglish
    if clean in ("h", "hn", "hm", "nhi", "ni", "yr", "mt", "bs", "bc", "mc"):
        return "hi"

    # Default: if it looks like it could be English (common suffixes)
    english_suffixes = ("tion", "ment", "ness", "ing", "ble", "ful", "less", "ous", "ive")
    if any(clean.endswith(s) for s in english_suffixes):
        return "en"

    # Default to Hindi for ambiguous romanized words
    # (In Hinglish text, ambiguous Latin-script words are more likely Hindi)
    return "hi"


def word_level_lang_id(words: List[str]) -> List[str]:
    """Classify each word in a list as 'hi', 'en', or 'hi_dev'."""
    return [classify_word(w) for w in words]
