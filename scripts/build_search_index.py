"""Build a pre-indexed search system from real Hindi tweets.

Loads cardiffnlp/tweet_sentiment_multilingual 'hindi' splits,
cleans tweets, normalizes with dhwani, and builds an inverted index.
Saves to data/search_index.json.
"""

import sys
import os
import re
import json

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

import dhvani
from dhvani.similarity import phonetic_similarity

# Pre-warm lexicon
print("Pre-warming lexicon...", flush=True)
phonetic_similarity("a", "b")
print("Lexicon ready.", flush=True)

from datasets import load_dataset

SENTIMENT_MAP = {0: "negative", 1: "neutral", 2: "positive"}


def clean_tweet(text):
    """Remove URLs, @mentions, keep hashtag text, remove excess punctuation."""
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    # Remove @mentions
    text = re.sub(r'@\w+', '', text)
    # Keep hashtag text (remove # symbol but keep the word)
    text = re.sub(r'#(\w+)', r'\1', text)
    # Remove excess whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def tokenize(text):
    """Split text into words, stripping punctuation safely (not breaking Devanagari)."""
    cleaned = re.sub(r'[.,!?;:"\'\-()\[\]]', ' ', text)
    return [w for w in cleaned.split() if w]


def build_index():
    print("Loading cardiffnlp/tweet_sentiment_multilingual hindi splits...", flush=True)
    ds_train = load_dataset("cardiffnlp/tweet_sentiment_multilingual", "hindi", split="train")
    ds_test = load_dataset("cardiffnlp/tweet_sentiment_multilingual", "hindi", split="test")
    ds_val = load_dataset("cardiffnlp/tweet_sentiment_multilingual", "hindi", split="validation")

    # Combine all splits
    all_texts = list(ds_train["text"]) + list(ds_test["text"]) + list(ds_val["text"])
    all_labels = list(ds_train["label"]) + list(ds_test["label"]) + list(ds_val["label"])
    print(f"Loaded {len(all_texts)} tweets total.", flush=True)

    corpus = []  # list of {text, cleaned, devanagari, sentiment}
    inverted_devanagari = {}  # normalized_word -> [indices]
    inverted_romanized = {}   # lowercase_word -> [indices]

    for i, (text, label) in enumerate(zip(all_texts, all_labels)):
        if i % 200 == 0:
            print(f"  Processing tweet {i}/{len(all_texts)}...", flush=True)

        cleaned = clean_tweet(text)
        if not cleaned:
            continue

        # Normalize full text to Devanagari
        devanagari = dhvani.to_devanagari(cleaned)

        entry = {
            "text": cleaned,
            "devanagari": devanagari,
            "sentiment": SENTIMENT_MAP.get(label, "neutral"),
        }
        idx = len(corpus)
        corpus.append(entry)

        # Tokenize and build inverted indices
        words = tokenize(cleaned.lower())
        for word in words:
            # Romanized index
            if word not in inverted_romanized:
                inverted_romanized[word] = []
            if idx not in inverted_romanized[word]:
                inverted_romanized[word].append(idx)

            # Normalize word to Devanagari and index
            try:
                dev_word = dhvani.to_devanagari(word)
                if dev_word and dev_word != word:
                    if dev_word not in inverted_devanagari:
                        inverted_devanagari[dev_word] = []
                    if idx not in inverted_devanagari[dev_word]:
                        inverted_devanagari[dev_word].append(idx)
            except Exception:
                pass

    print(f"Corpus: {len(corpus)} tweets", flush=True)
    print(f"Devanagari index: {len(inverted_devanagari)} unique normalized words", flush=True)
    print(f"Romanized index: {len(inverted_romanized)} unique words", flush=True)

    # Save
    output = {
        "corpus": corpus,
        "inverted_devanagari": inverted_devanagari,
        "inverted_romanized": inverted_romanized,
    }

    out_path = os.path.join(parent_dir, "data", "search_index.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=None)

    print(f"Saved index to {out_path} ({os.path.getsize(out_path) / 1024:.1f} KB)", flush=True)


if __name__ == "__main__":
    build_index()
