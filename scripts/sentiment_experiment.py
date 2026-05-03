"""Sentiment analysis experiment: with vs without dhwani normalization.

Shows that normalizing Hinglish spelling variants with dhwani improves
sentiment classification accuracy on real Hindi tweets.

Approach:
- Use a Hindi/Hinglish sentiment lexicon (positive/negative word lists)
- Run on cardiffnlp/tweet_sentiment_multilingual Hindi dataset
- Compare: raw text matching vs dhwani-normalized matching

This demonstrates dhwani's value as a preprocessing layer for NLP.
"""

import sys
import re
import json
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset
from sklearn.metrics import accuracy_score, f1_score, classification_report

import dhvani
from dhvani.similarity import phonetic_similarity


# ===========================================================================
# Hinglish Sentiment Lexicon
# These are words that carry sentiment in Hinglish social media text.
# The key insight: each word has MANY spelling variants that a lexicon
# approach would miss without normalization.
# ===========================================================================

POSITIVE_WORDS_HINDI = {
    # Devanagari canonical forms (what dhwani normalizes TO)
    "अच्छा", "अच्छी", "अच्छे", "बहुत", "प्यार", "खुश", "खुशी",
    "शानदार", "बढ़िया", "मज़ा", "मजा", "सुंदर", "धन्यवाद", "शुक्रिया",
    "जीत", "कमाल", "लाजवाब", "दमदार", "शाबाश", "वाह",
    "पसंद", "दिल", "जबरदस्त", "फैन", "तारीफ", "इज़्ज़त",
    "सही", "सच", "ज़रूर", "हमेशा", "प्यारा", "प्यारी",
}

POSITIVE_WORDS_ROMAN = {
    # Romanized variants (what users actually type)
    "accha", "achha", "acha", "achaa", "acchi", "achhi",
    "bahut", "bohot", "boht", "bhot", "bht",
    "pyaar", "pyar", "pyari",
    "khush", "khushi", "kushi",
    "shandar", "shaandar",
    "badhiya", "badhia", "badiya",
    "maza", "mazaa", "mja",
    "sundar", "sunder",
    "dhanyavad", "dhanyavaad", "shukriya", "thnx", "thanks",
    "jeet", "jit",
    "kamaal", "kamal",
    "lajawab", "lajawaab",
    "damdaar", "damdar",
    "shabaash", "shabash",
    "waah", "wah", "vaah",
    "pasand", "psnd",
    "dil",
    "jabardast", "jabrdast", "zabardast",
    "fan",
    "sahi", "shi",
    "sach", "sachme", "sacchi",
    "zaroor", "zarur",
    "hamesha", "humesha",
    "good", "great", "best", "amazing", "awesome", "love", "beautiful",
    "nice", "perfect", "excellent", "wonderful", "fantastic", "brilliant",
    "happy", "glad", "proud", "super", "wow", "yay",
    "congratulations", "congrats",
    "hit", "blockbuster", "masterpiece",
}

NEGATIVE_WORDS_HINDI = {
    "बुरा", "बुरी", "गलत", "बेकार", "घटिया", "बकवास",
    "नफरत", "गुस्सा", "दुख", "दुखी", "तकलीफ",
    "हार", "फेल", "बर्बाद", "तबाह",
    "झूठ", "झूठा", "फ़ालतू", "फालतू", "पागल",
    "चोर", "धोखा", "बेवकूफ", "मूर्ख",
    "शर्म", "अफसोस", "दर्द", "रोना",
    "खराब", "बदतर", "भयानक",
}

NEGATIVE_WORDS_ROMAN = {
    "bura", "buri", "bure",
    "galat", "glat",
    "bekaar", "bekar", "bakwas", "bakwaas", "bakwass",
    "ghatiya", "ghtiya", "ghatia",
    "nafrat", "nafrt",
    "gussa", "gusa", "gusse",
    "dukh", "dukhi",
    "taklif", "takleef",
    "haar", "har",
    "fail", "failed",
    "barbaad", "barbad", "tabah", "tabahi",
    "jhooth", "jhuth", "jhoota", "jhutha",
    "faltu", "faaltu", "falto",
    "pagal", "paagal", "pgal",
    "chor", "dhokha", "dhoka",
    "bewkoof", "bevkoof", "bewakoof", "bewakuf",
    "sharam", "shame",
    "afsos",
    "dard",
    "rona", "ro",
    "kharab", "khrab", "kharb",
    "bad", "worst", "terrible", "horrible", "hate", "stupid",
    "boring", "waste", "useless", "pathetic", "disgusting",
    "angry", "sad", "disappointed", "annoyed", "frustrated",
    "flop", "disaster", "trash", "garbage", "cringe",
}

NEGATION_WORDS = {
    "nahi", "nahin", "nhi", "ni", "na", "mat", "naa",
    "not", "no", "never", "dont", "don't", "didn't", "isn't", "wasn't",
    "neither", "nor", "without",
    "नहीं", "मत", "ना", "न",
}


def clean_tweet(text):
    """Basic tweet cleaning."""
    text = re.sub(r'http\S+|www\S+', '', text)  # URLs
    text = re.sub(r'@\w+', '', text)  # mentions
    text = re.sub(r'#(\w+)', r'\1', text)  # hashtags (keep word)
    text = re.sub(r'[^\w\s]', ' ', text)  # punctuation
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()


def sentiment_lexicon_raw(text):
    """Sentiment classification using raw word matching (no normalization)."""
    words = text.split()
    pos_count = 0
    neg_count = 0
    has_negation = False

    for i, word in enumerate(words):
        if word in NEGATION_WORDS:
            has_negation = True
            continue

        is_pos = word in POSITIVE_WORDS_ROMAN
        is_neg = word in NEGATIVE_WORDS_ROMAN

        # Simple negation handling: flip sentiment of next word
        if has_negation:
            is_pos, is_neg = is_neg, is_pos
            has_negation = False

        if is_pos:
            pos_count += 1
        if is_neg:
            neg_count += 1

    if pos_count > neg_count:
        return 2  # positive
    elif neg_count > pos_count:
        return 0  # negative
    else:
        return 1  # neutral


def sentiment_lexicon_normalized(text):
    """Sentiment classification with dhwani normalization."""
    words = text.split()
    pos_count = 0
    neg_count = 0
    has_negation = False

    # Get Devanagari normalized version
    try:
        devanagari = dhvani.to_devanagari(text)
        dev_words = devanagari.split()
    except Exception:
        dev_words = []

    for i, word in enumerate(words):
        if word in NEGATION_WORDS:
            has_negation = True
            continue

        # Check romanized
        is_pos = word in POSITIVE_WORDS_ROMAN
        is_neg = word in NEGATIVE_WORDS_ROMAN

        # Also check Devanagari normalized form
        if i < len(dev_words):
            dev_word = dev_words[i]
            if dev_word in POSITIVE_WORDS_HINDI:
                is_pos = True
            if dev_word in NEGATIVE_WORDS_HINDI:
                is_neg = True

        # Negation handling
        if has_negation:
            is_pos, is_neg = is_neg, is_pos
            has_negation = False

        if is_pos:
            pos_count += 1
        if is_neg:
            neg_count += 1

    if pos_count > neg_count:
        return 2  # positive
    elif neg_count > pos_count:
        return 0  # negative
    else:
        return 1  # neutral


def main():
    print("=" * 70)
    print("HINGLISH SENTIMENT ANALYSIS: dhwani normalization impact")
    print("=" * 70)
    print()

    # Load dataset
    print("Loading dataset: cardiffnlp/tweet_sentiment_multilingual (hindi)...")
    ds_test = load_dataset('cardiffnlp/tweet_sentiment_multilingual', 'hindi', split='test')
    print(f"Test set: {len(ds_test)} tweets")
    print(f"Label distribution: {dict(Counter(ds_test['label']))}")
    print()

    # Clean tweets
    texts = [clean_tweet(row['text']) for row in ds_test]
    labels = [row['label'] for row in ds_test]

    # Run WITHOUT normalization
    print("Running sentiment analysis WITHOUT dhwani normalization...")
    preds_raw = [sentiment_lexicon_raw(t) for t in texts]
    acc_raw = accuracy_score(labels, preds_raw)
    f1_raw = f1_score(labels, preds_raw, average='macro')
    print(f"  Accuracy: {acc_raw:.4f}")
    print(f"  Macro F1: {f1_raw:.4f}")
    print()

    # Run WITH normalization
    print("Running sentiment analysis WITH dhwani normalization...")
    preds_norm = [sentiment_lexicon_normalized(t) for t in texts]
    acc_norm = accuracy_score(labels, preds_norm)
    f1_norm = f1_score(labels, preds_norm, average='macro')
    print(f"  Accuracy: {acc_norm:.4f}")
    print(f"  Macro F1: {f1_norm:.4f}")
    print()

    # Improvement
    acc_diff = (acc_norm - acc_raw) * 100
    f1_diff = (f1_norm - f1_raw) * 100
    print("-" * 70)
    print(f"IMPROVEMENT with dhwani:")
    print(f"  Accuracy: +{acc_diff:.2f} percentage points")
    print(f"  Macro F1: +{f1_diff:.2f} percentage points")
    print("-" * 70)
    print()

    # Show some examples where normalization helped
    print("EXAMPLES where dhwani normalization changed the prediction:")
    print()
    label_map = {0: 'negative', 1: 'neutral', 2: 'positive'}
    count = 0
    for i, (text, true, raw, norm) in enumerate(zip(texts, labels, preds_raw, preds_norm)):
        if raw != norm and norm == true and count < 10:
            dev = dhvani.to_devanagari(text)
            print(f"  Text:       {text[:80]}")
            print(f"  Normalized: {dev[:80]}")
            print(f"  True: {label_map[true]} | Without dhwani: {label_map[raw]} | With dhwani: {label_map[norm]}")
            print()
            count += 1

    # Save results
    results = {
        "dataset": "cardiffnlp/tweet_sentiment_multilingual (hindi)",
        "test_size": len(ds_test),
        "without_normalization": {"accuracy": acc_raw, "macro_f1": f1_raw},
        "with_normalization": {"accuracy": acc_norm, "macro_f1": f1_norm},
        "improvement": {"accuracy_points": acc_diff, "f1_points": f1_diff},
    }
    output_path = Path(__file__).parent.parent / "data" / "sentiment_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()
