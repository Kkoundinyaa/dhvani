"""dhvani demo - Flask backend serving a beautiful frontend."""

import sys
import os
import re
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, send_from_directory

import dhvani
from dhvani.similarity import phonetic_similarity
from dhvani.lexicon.lookup import get_lexicon_stats

app = Flask(__name__, static_folder="static")

# Pre-warm
print("Loading lexicon...", flush=True)
phonetic_similarity("a", "b")
stats = get_lexicon_stats()
LEX_COUNT = f"{stats['ipa_entries']:,}"
print("Ready.", flush=True)

# Load search index
SEARCH_CORPUS = None
SEARCH_INDEX = None
_index_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "search_index.json")
if os.path.exists(_index_path):
    print("Loading search index...", flush=True)
    with open(_index_path, "r", encoding="utf-8") as _f:
        _index_data = json.load(_f)
        SEARCH_CORPUS = _index_data["corpus"]
        SEARCH_INDEX = {
            "devanagari": _index_data["inverted_devanagari"],
            "romanized": _index_data["inverted_romanized"],
        }
    print(f"Indexed: {len(SEARCH_CORPUS)} tweets.", flush=True)

# Sentiment lexicons
POSITIVE = {"accha", "achha", "acha", "achaa", "acchi", "achhi",
    "bahut", "bohot", "boht", "bhot", "bht", "bhaut",
    "pyaar", "pyar", "khush", "khushi", "shandar", "shaandar",
    "badhiya", "maza", "mazaa", "mast", "kamaal", "kamal",
    "lajawab", "jabardast", "zabardast", "waah", "wah",
    "dil", "sahi", "sachme", "hit", "superb", "dhamakedaar",
    "mazedaar", "pasand", "pyaari", "pyara",
    "good", "great", "best", "amazing", "awesome", "love",
    "beautiful", "nice", "loved", "perfect", "wonderful", "super"}

NEGATIVE = {"bura", "buri", "galat", "bekaar", "bekar",
    "bakwas", "bakwaas", "ghatiya", "boring", "kharab",
    "faltu", "faaltu", "pagal", "bewakoof", "tatti",
    "barbaad", "barbad", "dukh", "dukhi", "gussa",
    "worst", "waste", "slow", "weak", "neend",
    "bad", "terrible", "horrible", "hate", "stupid",
    "useless", "pathetic", "flop", "cringe", "below",
    "lodu", "chutiya", "madarchod", "behenchod",
    "gaandu", "saala", "saale", "saali",
    "kamina", "kamini", "harami", "haramkhor",
    "gadha", "gadhe", "ullu", "bevda",
    "gandu", "mc", "bc", "bkl",
    "wahiyat", "ghanta", "jhooth", "dhoka",
    "nafrat", "zeher", "zehreela"}

POSITIVE_DEV = {"अच्छा", "अच्छी", "अच्छे", "बहुत", "मजा", "मज़ा",
    "कमाल", "शानदार", "लाजवाब", "जबरदस्त", "वाह", "दिल",
    "खुश", "खुशी", "प्यार", "प्यारी", "प्यारा", "पसंद",
    "सही", "सच", "मस्त", "बढ़िया", "धमाकेदार", "मज़ेदार",
    "सुपर्ब", "हिट", "फैन"}

NEGATIVE_DEV = {"बुरा", "बुरी", "गलत", "बेकार", "बकवास", "घटिया",
    "खराब", "फ़ालतू", "फालतू", "पागल", "बेवकूफ", "बर्बाद",
    "दुख", "दुखी", "गुस्सा", "नींद", "टट्टी", "वेस्ट",
    "बोरिंग", "फ्लॉप", "स्लो", "वीक",
    "लोडू", "चूतिया", "मादरचोद", "बहनचोद",
    "गांडू", "साला", "साले", "साली",
    "कमीना", "कमीनी", "हरामी", "हरामखोर",
    "गधा", "गधे", "उल्लू", "नफरत", "ज़हर"}


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/stats")
def api_stats():
    return jsonify({
        "lexicon_count": LEX_COUNT,
        "tweet_count": len(SEARCH_CORPUS) if SEARCH_CORPUS else 0,
    })


@app.route("/api/normalize", methods=["POST"])
def api_normalize():
    text = request.json.get("text", "").strip()
    if not text:
        return jsonify({"error": "empty"}), 400

    dev = dhvani.to_devanagari(text)
    ipa = dhvani.to_ipa(text)
    langs = dhvani.identify_languages(text)

    return jsonify({
        "devanagari": dev,
        "ipa": ipa,
        "languages": [{"word": w, "lang": l} for w, l in langs],
    })


@app.route("/api/compare", methods=["POST"])
def api_compare():
    a = request.json.get("word_a", "").strip()
    b = request.json.get("word_b", "").strip()
    if not a or not b:
        return jsonify({"error": "empty"}), 400

    return jsonify({
        "word_a": a,
        "word_b": b,
        "ipa_a": dhvani.to_ipa(a),
        "ipa_b": dhvani.to_ipa(b),
        "dev_a": dhvani.to_devanagari(a),
        "dev_b": dhvani.to_devanagari(b),
        "similarity": round(phonetic_similarity(a, b), 3),
        "match": phonetic_similarity(a, b) > 0.8,
    })


@app.route("/api/search", methods=["POST"])
def api_search():
    query = request.json.get("query", "").strip()
    if not query:
        return jsonify({"results": [], "total": 0, "normalization": None})

    query_words = re.sub(r'[.,!?;:"\'\-()\[\]]', ' ', query.lower()).split()
    if not query_words:
        return jsonify({"results": [], "total": 0, "normalization": None})

    # Always include normalization info for the query
    norm_info = {
        "devanagari": dhvani.to_devanagari(query),
        "ipa": dhvani.to_ipa(query),
    }

    if not SEARCH_INDEX or not SEARCH_CORPUS:
        return jsonify({"results": [], "total": 0, "normalization": norm_info})

    matched = set()
    for qw in query_words:
        # Direct romanized match
        if qw in SEARCH_INDEX["romanized"]:
            matched.update(SEARCH_INDEX["romanized"][qw])
        # Phonetic match via Devanagari normalization
        try:
            qw_dev = dhvani.to_devanagari(qw)
            if qw_dev and qw_dev in SEARCH_INDEX["devanagari"]:
                matched.update(SEARCH_INDEX["devanagari"][qw_dev])
        except Exception:
            pass

    sorted_idx = sorted(matched)[:20]
    results = []
    for idx in sorted_idx:
        e = SEARCH_CORPUS[idx]
        results.append({"text": e["text"], "devanagari": e["devanagari"], "sentiment": e["sentiment"]})

    return jsonify({"results": results, "total": len(matched), "normalization": norm_info})


@app.route("/api/sentiment", methods=["POST"])
def api_sentiment():
    text = request.json.get("text", "").strip()
    if not text:
        return jsonify({"error": "empty"}), 400

    clean = re.sub(r'[^\w\s]', ' ', text.lower())
    words = clean.split()

    pos_raw = sum(1 for w in words if w in POSITIVE)
    neg_raw = sum(1 for w in words if w in NEGATIVE)

    dev_text = dhvani.to_devanagari(clean)
    dev_words = dev_text.split()

    pos_norm = pos_raw + sum(1 for w in dev_words if w in POSITIVE_DEV)
    neg_norm = neg_raw + sum(1 for w in dev_words if w in NEGATIVE_DEV)

    raw_sent = "positive" if pos_raw > neg_raw else ("negative" if neg_raw > pos_raw else "neutral")
    norm_sent = "positive" if pos_norm > neg_norm else ("negative" if neg_norm > pos_norm else "neutral")

    return jsonify({
        "input": text,
        "normalized": dev_text,
        "without": {"sentiment": raw_sent, "positive": pos_raw, "negative": neg_raw},
        "with": {"sentiment": norm_sent, "positive": pos_norm, "negative": neg_norm},
        "changed": raw_sent != norm_sent,
    })


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    print(f"\n  Open: http://localhost:{args.port}\n", flush=True)
    app.run(host="0.0.0.0", port=args.port, debug=False)
