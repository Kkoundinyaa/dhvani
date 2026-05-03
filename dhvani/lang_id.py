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
    "message", "comment", "post", "share", "video", "photo", "pic",
    "app", "website", "online", "offline", "download", "upload",
    "edit", "delete", "send", "call", "text", "email", "chat",
    "kidding", "joking", "waiting", "going", "coming", "doing", "being",
    "watching", "eating", "drinking", "sleeping", "working", "playing",
    "talking", "walking", "running", "sitting", "standing", "reading",
    "writing", "listening", "thinking", "feeling", "trying", "leaving",
    "amazing", "awesome", "beautiful", "boring", "crazy", "different",
    "enough", "everything", "nothing", "something", "someone", "anyone",
    "happy", "sad", "angry", "funny", "serious", "stupid", "smart",
    "friend", "family", "brother", "sister", "mother", "father",
    "money", "people", "place", "house", "office", "work",
    "chicken", "curry", "coffee", "pizza", "burger", "sandwich",
    "breakfast", "lunch", "dinner", "restaurant", "order", "menu",
    "college", "school", "teacher", "student", "class", "exam",
    "match", "cricket", "football", "game", "team", "player",
    "train", "flight", "ticket", "hotel", "room", "car", "bike",
    "number", "problem", "reason", "chance", "system", "process",
    "company", "business", "meeting", "project", "deadline",
    "party", "wedding", "birthday", "weekend", "holiday",
    "music", "song", "dance", "show", "episode", "season",
    "whatsapp", "instagram", "facebook", "twitter", "google",
    "phone", "laptop", "computer", "internet", "wifi", "password",
    "message", "group", "chat", "block", "report", "share",
])

# Common Romanized Hindi words (high-frequency indicators)
HINDI_WORDS = frozenset([
    "hai", "he", "ho", "hain", "tha", "thi", "hoga", "hogi",
    "ka", "ki", "ke", "ko", "se", "me", "mein", "par", "pe", "tak",
    "aur", "ya", "bhi", "hi", "na", "nahi", "nahin", "mat", "bas",
    "kya", "kaise", "kab", "kahan", "kaun", "kitna", "kitne", "kitni",
    "ye", "yeh", "wo", "woh", "wahi", "yahi", "iska", "uska", "unka",
    "mera", "tera", "humara", "tumhara", "apna", "apne", "apni",
    "accha", "acha", "achha", "bura", "sahi", "galat", "theek", "thik",
    "bahut", "bohot", "boht", "bahot", "zyada", "kam", "thoda", "kuch",
    "ab", "abhi", "tab", "jab", "phir", "fir", "pehle", "baad",
    "yaar", "yr", "bhai", "bro", "dude", "re", "arre",
    "karo", "karna", "kar", "kiya", "karke", "karunga", "karungi",
    "dekho", "dekhna", "dekh", "dekha", "dekhte", "dikhao",
    "bolo", "bolna", "bol", "bola", "bolte", "batao", "bata",
    "chalo", "chalna", "chal", "chala", "chalte", "jao", "jana", "ja",
    "aao", "aana", "aa", "aaya", "aayi", "aaye",
    "lelo", "lena", "le", "liya", "liye", "lete",
    "dena", "de", "diya", "diye", "dete",
    "khana", "pani", "ghar", "kaam", "paisa", "log", "wala", "wali",
    "sab", "sabhi", "koi", "kahin", "kabhi", "hamesha",
    "ek", "teen", "char", "panch",
    "lekin", "magar", "kyunki", "isliye", "toh", "to",
    "nhi", "ni", "h", "hn", "hm", "hmm",
    "samajh", "samjh", "pata", "malum", "matlab",
    "bilkul", "zarur", "zaroor", "shayad", "lagta", "lagti",
    "aloo", "roti", "dal", "daal", "paneer", "chai",
    "bus", "matar", "dost", "pyaar", "ishq",
    "subah", "raat", "dopahar", "shaam",
    "paani", "khana", "ghar", "dukan", "school",
    "wala", "wali", "wale", "waala", "waali", "waale",
    "karra", "karr", "karre", "krna", "krke", "kro",
    "rha", "rhi", "rhe",
    "bht", "bhot", "boht", "bhaut",
    "tu", "tujhe", "mujhe", "hume", "unhe",
    "bey", "be", "oye", "abe", "abey", "arre", "arey",
    "lodu", "chutiya", "bc", "mc", "madarchod", "behenchod",
    "gaandu", "saala", "saale", "saali", "kamina", "kamini",
    "harami", "haramkhor", "gadha", "gadhe", "ullu",
    "chal", "chalo", "nikal", "hatt", "hatja",
])

# Words that are BOTH valid English AND valid Hindi
# Context is needed to disambiguate these
AMBIGUOUS_WORDS = frozenset([
    "are",  # en: "are you" / hi: "अरे" (hey!)
    "the",  # en: article / hi: "थे" (were)
    "he",   # en: pronoun / hi: "है" variant
    "do",   # en: verb / hi: "दो" (two/give)
    "us",   # en: pronoun / hi: "उस" (that)
    "par",  # en: golf par / hi: "पर" (on/but)
    "mat",  # en: noun / hi: "मत" (don't)
    "log",  # en: noun / hi: "लोग" (people)
    "sir",  # en: title / hi: "सिर" (head)
    "bus",  # en: vehicle / hi: "बस" (enough/stop)
    "am",   # en: verb / hi: "आम" (mango/common)
    "in",   # en: preposition / hi: "इन" (these)
    "so",   # en: conjunction / hi: "सो" (so/sleep)
    "or",   # en: conjunction / hi: "और" (and)
    "no",   # en: negation / hi: same
    "is",   # en: verb / hi: "इस" (this)
    "it",   # en: pronoun / hi: could be Hindi
    "me",   # en: pronoun / hi: "में" (in)
    "her",  # en: pronoun / hi: "हर" (every)
    "to",   # en: preposition / hi: "तो" (then)
    "hi",   # en: greeting / hi: "ही" (emphasis)
    "be",   # en: verb / hi: "बे" (hey/slang address)
])

# Characters that only appear in Hindi romanization
HINDI_CHAR_PATTERNS = re.compile(
    r"(aa|ee|oo|ai|au|bh|ch|dh|gh|jh|kh|ph|sh|th|"
    r"chh|shh|ng|nk|gy|dy|"
    r"\bji\b|\bji$|\bwala\b|\bwali\b|\bwale\b)"
)


def is_devanagari(word: str) -> bool:
    """Check if word contains Devanagari characters."""
    return bool(DEVANAGARI_RANGE.search(word))


def classify_word(word: str) -> str:
    """Classify a single word as 'hi', 'en', or 'hi_dev' (no context)."""
    clean = word.lower().strip(".,!?;:'\"()-")

    if not clean:
        return "en"

    if is_devanagari(clean):
        return "hi_dev"

    # Check known word lists (Hindi first since this is a Hinglish tool)
    if clean in HINDI_WORDS:
        return "hi"
    if clean in ENGLISH_WORDS and clean not in AMBIGUOUS_WORDS:
        return "en"

    # English suffixes check BEFORE Hindi char patterns
    # (e.g., "kidding" contains "dh" but is clearly English)
    english_suffixes = ("tion", "ment", "ness", "ing", "ble", "ful", "less", "ous", "ive", "ally", "edly", "ting", "ding")
    if any(clean.endswith(s) for s in english_suffixes):
        return "en"

    # Heuristic: words with Hindi-typical character patterns
    if HINDI_CHAR_PATTERNS.search(clean):
        return "hi"

    # Heuristic: very short abbreviations common in Hinglish
    if clean in ("h", "hn", "hm", "nhi", "ni", "yr", "mt", "bs", "bc", "mc"):
        return "hi"

    # Default to Hindi for ambiguous romanized words
    return "hi"


def _resolve_ambiguous(word: str, prev_lang: str, next_lang: str) -> str:
    """Resolve an ambiguous word using surrounding context.

    If neighbors are English, lean English. If neighbors are Hindi, lean Hindi.
    """
    en_score = 0
    hi_score = 0

    if prev_lang == "en":
        en_score += 1
    elif prev_lang in ("hi", "hi_dev"):
        hi_score += 1

    if next_lang == "en":
        en_score += 1
    elif next_lang in ("hi", "hi_dev"):
        hi_score += 1

    if en_score > hi_score:
        return "en"
    # Default to Hindi for ties (Hinglish text is more likely Hindi)
    return "hi"


def word_level_lang_id(words: List[str]) -> List[str]:
    """Classify each word in a list as 'hi', 'en', or 'hi_dev'.

    Uses context-aware disambiguation for ambiguous words.
    """
    # First pass: classify without context, mark ambiguous
    tags = []
    ambiguous_indices = []
    for i, w in enumerate(words):
        clean = w.lower().strip(".,!?;:'\"()-")
        if clean in AMBIGUOUS_WORDS:
            tags.append("_ambiguous")
            ambiguous_indices.append(i)
        else:
            tags.append(classify_word(w))

    # Second pass: resolve ambiguous words using context
    for i in ambiguous_indices:
        prev_lang = tags[i - 1] if i > 0 else ""
        # For next, skip other ambiguous words
        next_lang = ""
        for j in range(i + 1, len(tags)):
            if tags[j] != "_ambiguous":
                next_lang = tags[j]
                break

        tags[i] = _resolve_ambiguous(words[i], prev_lang, next_lang)

    return tags
