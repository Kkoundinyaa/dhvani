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


# ===== Content Moderation =====

# Abusive words: canonical Devanagari -> (English meaning, known romanized variants)
# dhvani catches ALL variants via normalization; exact match only catches what's listed
ABUSIVE_WORDS = {
    "चूतिया": {
        "meaning": "idiot (vulgar)",
        "variants": ["chutiya", "chutia", "chtiya", "chtyia", "chutya", "chutyia",
                      "chootiya", "chootia", "chtia", "chutiye", "chutiyapa",
                      "chtiyo", "chutiyo", "chutiapa"],
    },
    "बहनचोद": {
        "meaning": "sister-f***er",
        "variants": ["behenchod", "bhenchod", "benchod", "bhnchod", "bc",
                      "behen chod", "behanchod", "bhenchd", "bhnchd", "bahinchod"],
    },
    "मादरचोद": {
        "meaning": "mother-f***er",
        "variants": ["madarchod", "maderchod", "mdrchod", "mc", "madrchod",
                      "motherchod", "madarchd", "mdrchd", "maadarchod"],
    },
    "बोसड़ीके": {
        "meaning": "born of a prostitute",
        "variants": ["bosdike", "bsdk", "bsdke", "bosdk", "bosdke",
                      "bosdiwale", "bsdwale", "bosadike", "bhosdike",
                      "bhosdiwale", "bhsdk", "bhosdke"],
    },
    "गांडू": {
        "meaning": "a**hole (person)",
        "variants": ["gandu", "gaandu", "gndu", "gaandu", "ganduu",
                      "gandu", "gaand", "gand"],
    },
    "साला": {
        "meaning": "brother-in-law (used as insult)",
        "variants": ["saala", "sala", "saale", "sale", "saaley",
                      "saali", "sali", "saaliyan"],
    },
    "कमीना": {
        "meaning": "scoundrel",
        "variants": ["kamina", "kameena", "kmina", "kameene", "kamine",
                      "kamini", "kameeni", "kamino", "kmeena"],
    },
    "हरामी": {
        "meaning": "illegitimate/scoundrel",
        "variants": ["harami", "hrami", "haraami", "haraamee",
                      "haramkhor", "hmkhor", "haraamkhor", "hramkhor"],
    },
    "गधा": {
        "meaning": "donkey (calling someone stupid)",
        "variants": ["gadha", "gdha", "gadhe", "gdhe", "gadhaa",
                      "gadho", "gadhon"],
    },
    "उल्लू": {
        "meaning": "owl (calling someone idiot)",
        "variants": ["ullu", "ulloo", "ulu", "ulluu",
                      "ullu ka pattha", "ullu ke patthe"],
    },
    "बेवकूफ": {
        "meaning": "fool/idiot",
        "variants": ["bewakoof", "bevkoof", "bevkuf", "bwkoof",
                      "bewkoof", "bewaqoof", "bevakuf", "bvkoof",
                      "bewkuf", "bevkf"],
    },
    "पागल": {
        "meaning": "crazy/insane",
        "variants": ["pagal", "pagl", "pgl", "pagla", "paglu",
                      "paagal", "pagalon", "pgal", "paagl"],
    },
    "लोडू": {
        "meaning": "idiot (vulgar)",
        "variants": ["lodu", "lodu", "loduu", "lodu", "laude",
                      "lavde", "lvde", "laudu", "lwde"],
    },
    "बकलोल": {
        "meaning": "idiot/fool",
        "variants": ["baklol", "bkl", "bakl", "baklund", "bklol",
                      "baklole", "bklnd"],
    },
    "कुत्ता": {
        "meaning": "dog (calling someone a dog)",
        "variants": ["kutta", "kuta", "kutte", "kute", "kuttey",
                      "kutiya", "kutia", "kuttia"],
    },
    "सूअर": {
        "meaning": "pig (insult)",
        "variants": ["suar", "suwar", "sooar", "soor", "suwwar",
                      "suwar ki aulad"],
    },
    "टट्टी": {
        "meaning": "crap/garbage",
        "variants": ["tatti", "tati", "ttti", "tattii",
                      "tty", "tatty"],
    },
    "घटिया": {
        "meaning": "cheap/terrible",
        "variants": ["ghatiya", "ghtiya", "ghatya", "ghateya",
                      "ghatiyaa", "ghatiyo"],
    },
    "बकवास": {
        "meaning": "nonsense/rubbish",
        "variants": ["bakwas", "bakwaas", "bkwas", "bkwaas",
                      "bakvas", "bkvas", "bakwass"],
    },
    "नालायक": {
        "meaning": "worthless/useless",
        "variants": ["nalayak", "nalayq", "nalayk", "nalayik",
                      "nalaayak", "nlayak", "nlyak"],
    },
    "भड़वा": {
        "meaning": "pimp (insult)",
        "variants": ["bhadwa", "bhadva", "bhdwa", "bhadwe",
                      "bhadwo", "bhdva"],
    },
    "रंडी": {
        "meaning": "prostitute (slur)",
        "variants": ["randi", "rndi", "randee", "rndee",
                      "randiya", "randiyan", "rndiyan"],
    },
    "चमार": {
        "meaning": "casteist slur",
        "variants": ["chamar", "chamaar", "chmaar", "chmar",
                      "chamaaron", "chamaro"],
    },
    "भिखारी": {
        "meaning": "beggar (insult)",
        "variants": ["bhikhari", "bhikari", "bhkhari", "bhikhaari",
                      "bhikaari", "bhkhri", "bhikharion"],
    },
}

# Also match derived forms that the corrector produces
_ABUSIVE_DERIVED = {
    "गांड", "चूतियापा", "कुत्ते", "कुतिया", "लौड़े",
    "कमीने", "कमीनी", "गधे", "भड़वे", "साले", "साली",
    "हरामखोर",
}

# Build flat sets for fast lookup
_ABUSIVE_DEVANAGARI = set(ABUSIVE_WORDS.keys()) | _ABUSIVE_DERIVED

# Realistic exact-match blocklist: only the most obvious canonical spellings
# This is what a human would typically put in a blocklist
_ABUSIVE_EXACT = {
    "chutiya", "behenchod", "madarchod", "bosdike", "gandu",
    "saala", "saali", "kamina", "harami", "gadha", "ullu",
    "bewakoof", "pagal", "lodu", "baklol", "kutta", "suar",
    "tatti", "ghatiya", "bakwas", "nalayak", "bhadwa", "randi",
    "chamar", "bhikhari",
}
# Total: ~25 entries - a typical hand-built blocklist


@app.route("/api/moderate", methods=["POST"])
def api_moderate():
    text = request.json.get("text", "").strip()
    if not text:
        return jsonify({"error": "empty"}), 400

    clean = re.sub(r'[^\w\s]', ' ', text.lower())
    words = clean.split()

    # Exact-match detection
    exact_flagged = [w for w in words if w in _ABUSIVE_EXACT]

    # dhvani-normalized detection
    dev_text = dhvani.to_devanagari(clean)
    dev_words = dev_text.split()
    dhvani_flagged = []
    for orig, dev in zip(words, dev_words):
        if dev in _ABUSIVE_DEVANAGARI:
            meaning = ABUSIVE_WORDS.get(dev, {}).get("meaning", "abusive/offensive")
            dhvani_flagged.append({"word": orig, "devanagari": dev,
                                   "meaning": meaning})

    return jsonify({
        "input": text,
        "normalized": dev_text,
        "exact_match": {"flagged": exact_flagged, "count": len(exact_flagged)},
        "dhvani": {"flagged": dhvani_flagged, "count": len(dhvani_flagged)},
        "words_checked": len(words),
    })


@app.route("/api/moderation_stats")
def api_moderation_stats():
    """Show how many variants each abusive word has."""
    stats = []
    for dev, info in ABUSIVE_WORDS.items():
        stats.append({
            "devanagari": dev,
            "meaning": info["meaning"],
            "variant_count": len(info["variants"]),
            "variants": info["variants"][:8],  # show first 8
        })
    return jsonify({
        "words": stats,
        "total_words": len(ABUSIVE_WORDS),
        "total_variants": sum(len(v["variants"]) for v in ABUSIVE_WORDS.values()),
    })


# ===== Word Explorer =====

@app.route("/api/explore", methods=["POST"])
def api_explore():
    """Given a word, show its canonical form and all known variants."""
    word = request.json.get("word", "").strip()
    if not word:
        return jsonify({"error": "empty"}), 400

    dev = dhvani.to_devanagari(word)
    ipa = dhvani.to_ipa(word)

    from dhvani.corrector import get_variants_for_devanagari
    # Get all known romanized variants for this Devanagari form
    variants = get_variants_for_devanagari(dev)
    # Also check each word in multi-word outputs
    dev_words = dev.split()
    if len(dev_words) > 1:
        for dw in dev_words:
            variants.extend(get_variants_for_devanagari(dw))

    # Deduplicate and remove the input word itself
    variants = sorted(set(v for v in variants if v.lower() != word.lower()))

    return jsonify({
        "input": word,
        "devanagari": dev,
        "ipa": ipa,
        "variant_count": len(variants),
        "variants": variants,
    })


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    print(f"\n  Open: http://localhost:{args.port}\n", flush=True)
    app.run(host="0.0.0.0", port=args.port, debug=False)
