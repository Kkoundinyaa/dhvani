"""dhvani demo - Hinglish phonetic normalization that actually works."""

import sys
import os
import re
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr
import dhvani
from dhvani.similarity import phonetic_similarity

# Pre-warm
print("Loading lexicon...", flush=True)
phonetic_similarity("a", "b")
print("Ready.", flush=True)

# Load search index
SEARCH_INDEX = None
SEARCH_CORPUS = None
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


# ===========================================================================
# Backend
# ===========================================================================

def live_convert(text):
    if not text.strip():
        return ""
    dev = dhvani.to_devanagari(text)
    ipa = dhvani.to_ipa(text)
    langs = dhvani.identify_languages(text)

    # Build a nice output
    lang_tags = ""
    for word, lang in langs:
        cls = "hi" if lang in ("hi", "hi_dev") else "en"
        lang_tags += f'<span class="lang-chip lang-{cls}">{word}</span> '

    escaped = text.replace('\\', '\\\\').replace('"', '\\"')
    html = f"""
    <div class="convert-output">
        <div class="output-section">
            <div class="output-label">DEVANAGARI</div>
            <div class="output-main devanagari-text">{dev}</div>
        </div>
        <div class="output-section">
            <div class="output-label">IPA TRANSCRIPTION</div>
            <div class="output-main ipa-text">/{ipa}/</div>
        </div>
        <div class="output-section">
            <div class="output-label">LANGUAGE DETECTION</div>
            <div class="lang-chips">{lang_tags}</div>
        </div>
        <div class="code-snippet">
            <div class="code-label">PYTHON</div>
            <pre>import dhvani
dhvani.to_devanagari("{escaped}")
dhvani.to_ipa("{escaped}")</pre>
        </div>
    </div>"""
    return html


def search_corpus(query):
    if not query.strip():
        return ""

    if SEARCH_INDEX and SEARCH_CORPUS:
        return _search_indexed(query)
    return '<div class="search-empty">Search index not loaded.</div>'


def _search_indexed(query):
    query_words = re.sub(r'[.,!?;:"\'\-()\[\]]', ' ', query.lower().strip()).split()
    if not query_words:
        return ""

    matched_indices = set()
    for qw in query_words:
        if qw in SEARCH_INDEX["romanized"]:
            matched_indices.update(SEARCH_INDEX["romanized"][qw])
        try:
            qw_dev = dhvani.to_devanagari(qw)
            if qw_dev and qw_dev in SEARCH_INDEX["devanagari"]:
                matched_indices.update(SEARCH_INDEX["devanagari"][qw_dev])
        except Exception:
            pass

    if not matched_indices:
        return f'<div class="search-empty">No results for "<strong>{query}</strong>". Try: accha, film, modi, cricket, pyaar, desh</div>'

    sorted_indices = sorted(matched_indices)[:15]
    total = len(matched_indices)

    sent_icons = {"positive": "+", "negative": "-", "neutral": "~"}
    sent_cls = {"positive": "pos", "negative": "neg", "neutral": "neu"}

    html = f'<div class="search-header">{total} results for "<strong>{query}</strong>" <span class="search-note">Matches all spelling variants via phonetic normalization</span></div>'
    html += '<div class="search-grid">'

    for idx in sorted_indices:
        entry = SEARCH_CORPUS[idx]
        sent = entry["sentiment"]
        cls = sent_cls.get(sent, "neu")
        icon = sent_icons.get(sent, "~")
        html += f"""<div class="tweet-card">
            <div class="tweet-sent sent-{cls}">{icon}</div>
            <div class="tweet-body">
                <div class="tweet-text">{entry['text']}</div>
                <div class="tweet-dev">{entry['devanagari']}</div>
            </div>
        </div>"""

    html += '</div>'
    if total > 15:
        html += f'<div class="search-more">+ {total - 15} more results</div>'
    return html


def compare_words(word_a, word_b):
    if not word_a or not word_b or not word_a.strip() or not word_b.strip():
        return '<div class="search-empty">Enter two words to compare.</div>'

    a, b = word_a.strip(), word_b.strip()
    ipa_a = dhvani.to_ipa(a)
    ipa_b = dhvani.to_ipa(b)
    dev_a = dhvani.to_devanagari(a)
    dev_b = dhvani.to_devanagari(b)
    score = phonetic_similarity(a, b)
    match = score > 0.8

    match_cls = "compare-match" if match else "compare-nomatch"
    match_label = "Same word" if match else "Different words"
    match_icon = "=" if match else "&ne;"

    html = f"""
    <div class="compare-result {match_cls}">
        <div class="compare-verdict">
            <span class="compare-icon">{match_icon}</span>
            <span class="compare-label">{match_label}</span>
            <span class="compare-score">{score:.0%} similarity</span>
        </div>
        <div class="compare-grid">
            <div class="compare-col">
                <div class="compare-word">{a}</div>
                <div class="compare-ipa">/{ipa_a}/</div>
                <div class="compare-dev">{dev_a}</div>
            </div>
            <div class="compare-col">
                <div class="compare-word">{b}</div>
                <div class="compare-ipa">/{ipa_b}/</div>
                <div class="compare-dev">{dev_b}</div>
            </div>
        </div>
        <div class="code-snippet">
            <div class="code-label">PYTHON</div>
            <pre>import dhvani
dhvani.are_same("{a}", "{b}")  # {match}</pre>
        </div>
    </div>"""
    return html


def analyze_sentiment(text):
    if not text.strip():
        return ""

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

    improved = raw_sent != norm_sent
    sent_cls = {"positive": "pos", "negative": "neg", "neutral": "neu"}

    html = f"""
    <div class="sent-card">
        <div class="sent-section">
            <div class="sent-sec-label">INPUT</div>
            <div class="sent-sec-text">{text}</div>
        </div>
        <div class="sent-section">
            <div class="sent-sec-label">NORMALIZED</div>
            <div class="sent-sec-text dev">{dev_text}</div>
        </div>
        <div class="sent-comparison">
            <div class="sent-box">
                <div class="sent-box-label">Without dhvani</div>
                <div class="sent-badge sent-{sent_cls[raw_sent]}">{raw_sent}</div>
                <div class="sent-score">{pos_raw} positive / {neg_raw} negative signals</div>
            </div>
            <div class="sent-arrow">vs</div>
            <div class="sent-box {('sent-box-highlight' if improved else '')}">
                <div class="sent-box-label">With dhvani</div>
                <div class="sent-badge sent-{sent_cls[norm_sent]}">{norm_sent}</div>
                <div class="sent-score">{pos_norm} positive / {neg_norm} negative signals</div>
            </div>
        </div>
    </div>"""

    if improved:
        html += '<div class="sent-insight">Normalization resolved spelling variants to known sentiment words, changing the classification.</div>'

    escaped = text.replace('\\', '\\\\').replace('"', '\\"')
    html += f"""
    <div class="code-snippet">
        <div class="code-label">PYTHON</div>
        <pre>import dhvani
normalized = dhvani.to_devanagari("{escaped}")
# Feed normalized text to your sentiment model</pre>
    </div>"""

    return html


# ===========================================================================
# CSS
# ===========================================================================

from dhvani.lexicon.lookup import get_lexicon_stats
stats = get_lexicon_stats()
lex_count = f"{stats['ipa_entries']:,}"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&family=Noto+Sans+Devanagari:wght@400;500;600&display=swap');

/* === Global === */
.gradio-container {
    max-width: 860px !important;
    margin: 0 auto !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    background: #fafafa !important;
}
.dark .gradio-container { background: #09090b !important; }
footer { display: none !important; }

/* === Header === */
.hero {
    text-align: center;
    padding: 56px 24px 36px;
    background: linear-gradient(180deg, #fff 0%, #fafafa 100%);
    border-bottom: 1px solid #e5e7eb;
}
.dark .hero {
    background: linear-gradient(180deg, #0a0a0a 0%, #09090b 100%);
    border-color: #1f1f1f;
}
.hero-logo {
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.05em;
    color: #09090b;
    margin: 0 0 8px;
    line-height: 1;
}
.dark .hero-logo { color: #fafafa; }
.hero-tagline {
    font-size: 0.95rem;
    color: #71717a;
    font-weight: 400;
    margin: 0 0 20px;
    line-height: 1.6;
}
.hero-stats {
    display: inline-flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
}
.stat-chip {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    padding: 5px 12px;
    border-radius: 100px;
    background: #f4f4f5;
    color: #52525b;
    border: 1px solid #e4e4e7;
}
.dark .stat-chip {
    background: #18181b;
    color: #a1a1aa;
    border-color: #27272a;
}

/* === Tabs === */
.tab-nav {
    border-bottom: 1px solid #e5e7eb !important;
    background: #fff !important;
    padding: 0 16px !important;
}
.dark .tab-nav { background: #0a0a0a !important; border-color: #1f1f1f !important; }
.tab-nav button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    padding: 14px 20px !important;
    color: #a1a1aa !important;
    border: none !important;
    background: none !important;
    letter-spacing: 0.01em;
}
.tab-nav button.selected {
    color: #09090b !important;
    box-shadow: inset 0 -2px 0 #09090b !important;
}
.dark .tab-nav button.selected {
    color: #fafafa !important;
    box-shadow: inset 0 -2px 0 #fafafa !important;
}

/* === Tab content === */
.tab-intro {
    font-size: 0.88rem;
    color: #71717a;
    margin: 16px 0 20px;
    line-height: 1.6;
}
.tab-intro strong { color: #3f3f46; font-weight: 500; }
.dark .tab-intro strong { color: #d4d4d8; }

/* === Convert output === */
.convert-output {
    background: #fff;
    border: 1px solid #e4e4e7;
    border-radius: 12px;
    padding: 20px 24px;
    margin-top: 12px;
}
.dark .convert-output { background: #18181b; border-color: #27272a; }
.output-section { margin-bottom: 16px; }
.output-section:last-child { margin-bottom: 0; }
.output-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: #a1a1aa;
    margin-bottom: 6px;
}
.output-main {
    font-size: 1.15rem;
    color: #18181b;
    line-height: 1.7;
}
.dark .output-main { color: #e4e4e7; }
.devanagari-text {
    font-family: 'Noto Sans Devanagari', sans-serif;
    font-weight: 500;
}
.ipa-text {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1rem;
    color: #6366f1;
}
.dark .ipa-text { color: #a5b4fc; }
.lang-chips { display: flex; flex-wrap: wrap; gap: 5px; }
.lang-chip {
    font-size: 0.78rem;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 5px;
}
.lang-hi { background: #eef2ff; color: #4338ca; border: 1px solid #c7d2fe; }
.lang-en { background: #f4f4f5; color: #52525b; border: 1px solid #e4e4e7; }
.dark .lang-hi { background: #1e1b4b; color: #a5b4fc; border-color: #312e81; }
.dark .lang-en { background: #27272a; color: #a1a1aa; border-color: #3f3f46; }

/* === Search === */
.search-header {
    font-size: 0.85rem;
    color: #3f3f46;
    margin-bottom: 12px;
    font-weight: 500;
}
.dark .search-header { color: #d4d4d8; }
.search-note {
    font-size: 0.75rem;
    color: #a1a1aa;
    font-weight: 400;
    margin-left: 8px;
}
.search-grid { display: flex; flex-direction: column; gap: 6px; }
.tweet-card {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 16px;
    background: #fff;
    border: 1px solid #e4e4e7;
    border-radius: 10px;
    transition: border-color 0.15s;
}
.tweet-card:hover { border-color: #a1a1aa; }
.dark .tweet-card { background: #18181b; border-color: #27272a; }
.dark .tweet-card:hover { border-color: #52525b; }
.tweet-sent {
    width: 24px;
    height: 24px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 700;
    flex-shrink: 0;
    margin-top: 2px;
}
.sent-pos { background: #dcfce7; color: #166534; }
.sent-neg { background: #fee2e2; color: #991b1b; }
.sent-neu { background: #f4f4f5; color: #52525b; }
.dark .sent-pos { background: #052e16; color: #86efac; }
.dark .sent-neg { background: #450a0a; color: #fca5a5; }
.dark .sent-neu { background: #27272a; color: #a1a1aa; }
.tweet-body { flex: 1; min-width: 0; }
.tweet-text { font-size: 0.88rem; color: #27272a; line-height: 1.5; }
.dark .tweet-text { color: #e4e4e7; }
.tweet-dev { font-size: 0.78rem; color: #a1a1aa; margin-top: 3px; font-family: 'Noto Sans Devanagari', sans-serif; }
.search-empty { text-align: center; padding: 32px; color: #a1a1aa; font-size: 0.88rem; }
.search-more { text-align: center; padding: 10px; color: #71717a; font-size: 0.8rem; font-weight: 500; }

/* === Sentiment === */
.sent-card {
    background: #fff;
    border: 1px solid #e4e4e7;
    border-radius: 12px;
    padding: 20px 24px;
    margin-top: 12px;
}
.dark .sent-card { background: #18181b; border-color: #27272a; }
.sent-section { margin-bottom: 14px; }
.sent-sec-label {
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: #a1a1aa;
    margin-bottom: 4px;
}
.sent-sec-text { font-size: 0.92rem; color: #27272a; line-height: 1.5; }
.sent-sec-text.dev { font-family: 'Noto Sans Devanagari', sans-serif; color: #6366f1; }
.dark .sent-sec-text { color: #e4e4e7; }
.dark .sent-sec-text.dev { color: #a5b4fc; }
.sent-comparison {
    display: flex;
    align-items: stretch;
    gap: 12px;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #f4f4f5;
}
.dark .sent-comparison { border-color: #27272a; }
.sent-box {
    flex: 1;
    text-align: center;
    padding: 16px 12px;
    border-radius: 10px;
    background: #f9fafb;
    border: 1px solid #f4f4f5;
}
.dark .sent-box { background: #0a0a0a; border-color: #27272a; }
.sent-box-highlight { border-color: #6366f1 !important; background: #eef2ff; }
.dark .sent-box-highlight { border-color: #6366f1 !important; background: #1e1b4b; }
.sent-box-label { font-size: 0.7rem; font-weight: 600; color: #71717a; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.05em; }
.sent-badge {
    display: inline-block;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 4px 12px;
    border-radius: 5px;
}
.sent-pos { background: #dcfce7; color: #166534; }
.sent-neg { background: #fee2e2; color: #991b1b; }
.sent-neu { background: #f4f4f5; color: #52525b; }
.sent-score { font-size: 0.72rem; color: #a1a1aa; margin-top: 8px; font-family: 'JetBrains Mono', monospace; }
.sent-arrow { display: flex; align-items: center; font-size: 0.75rem; color: #d4d4d8; font-weight: 600; }
.sent-insight {
    margin-top: 12px;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 0.8rem;
    background: #eef2ff;
    color: #4338ca;
    border: 1px solid #c7d2fe;
    font-weight: 500;
}
.dark .sent-insight { background: #1e1b4b; color: #a5b4fc; border-color: #312e81; }

/* === Compare === */
.compare-result {
    border-radius: 12px;
    padding: 20px 24px;
    margin-top: 12px;
    border: 2px solid;
}
.compare-match { background: #f0fdf4; border-color: #22c55e; }
.compare-nomatch { background: #fef2f2; border-color: #ef4444; }
.dark .compare-match { background: #052e16; border-color: #16a34a; }
.dark .compare-nomatch { background: #450a0a; border-color: #dc2626; }
.compare-verdict {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
}
.compare-icon {
    font-size: 1.5rem;
    font-weight: 800;
    line-height: 1;
}
.compare-match .compare-icon { color: #16a34a; }
.compare-nomatch .compare-icon { color: #dc2626; }
.compare-label {
    font-size: 1rem;
    font-weight: 700;
    color: #18181b;
}
.dark .compare-label { color: #fafafa; }
.compare-score {
    font-size: 0.78rem;
    font-family: 'JetBrains Mono', monospace;
    color: #71717a;
    margin-left: auto;
}
.compare-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}
.compare-col {
    background: #fff;
    border: 1px solid #e4e4e7;
    border-radius: 10px;
    padding: 14px 16px;
    text-align: center;
}
.dark .compare-col { background: #18181b; border-color: #27272a; }
.compare-word { font-size: 1.1rem; font-weight: 600; color: #18181b; margin-bottom: 6px; }
.dark .compare-word { color: #fafafa; }
.compare-ipa { font-family: 'JetBrains Mono', monospace; font-size: 0.88rem; color: #6366f1; margin-bottom: 4px; }
.dark .compare-ipa { color: #a5b4fc; }
.compare-dev { font-family: 'Noto Sans Devanagari', sans-serif; font-size: 0.95rem; color: #71717a; }

/* === Code snippet === */
.code-snippet {
    margin-top: 14px;
    padding-top: 14px;
    border-top: 1px solid #f4f4f5;
}
.dark .code-snippet { border-color: #27272a; }
.code-label {
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: #a1a1aa;
    margin-bottom: 6px;
}
.code-snippet pre {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    background: #f4f4f5;
    border: 1px solid #e4e4e7;
    border-radius: 8px;
    padding: 10px 14px;
    color: #3f3f46;
    line-height: 1.6;
    overflow-x: auto;
    margin: 0;
    white-space: pre;
}
.dark .code-snippet pre {
    background: #0a0a0a;
    border-color: #27272a;
    color: #d4d4d8;
}

/* === Buttons === */
.primary {
    background: #18181b !important;
    color: #fafafa !important;
    border: none !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    border-radius: 8px !important;
    padding: 11px 28px !important;
    letter-spacing: 0.01em;
    transition: background 0.15s !important;
}
.primary:hover { background: #27272a !important; }
.dark .primary { background: #fafafa !important; color: #09090b !important; }
.dark .primary:hover { background: #e4e4e7 !important; }

/* === Inputs === */
textarea, input[type="text"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    border-radius: 8px !important;
}

/* === About === */
.about-text { font-size: 0.84rem; color: #71717a; line-height: 1.7; }
.about-text strong { color: #3f3f46; }
.dark .about-text strong { color: #d4d4d8; }
.about-footer {
    font-size: 0.75rem; color: #a1a1aa; margin-top: 14px;
    padding-top: 14px; border-top: 1px solid #f4f4f5;
}
.dark .about-footer { border-color: #27272a; }
.about-footer a { color: #6366f1; text-decoration: none; }
.about-footer a:hover { text-decoration: underline; }
"""


# ===========================================================================
# Layout
# ===========================================================================

with gr.Blocks(title="dhvani") as demo:

    gr.HTML(f"""
    <div class="hero">
        <div class="hero-logo">dhvani</div>
        <p class="hero-tagline">
            Phonetic normalization for Hinglish.<br>
            Makes NLP actually work on code-mixed Hindi-English text.
        </p>
        <div class="hero-stats">
            <span class="stat-chip">{lex_count} lexicon entries</span>
            <span class="stat-chip">No model at inference</span>
            <span class="stat-chip">&lt;1ms per word</span>
            <span class="stat-chip">pip install dhvani</span>
        </div>
    </div>
    """)

    with gr.Tabs():

        with gr.TabItem("Normalize"):
            gr.HTML("""<p class="tab-intro">
                Type messy Hinglish. Get clean Devanagari, IPA transcription, and per-word language detection.
                Handles elongated text, abbreviations, slang, and mixed scripts.
            </p>""")

            input_text = gr.Textbox(
                show_label=False,
                placeholder="Try: bohotttt achaaa movie thi yaar, maza aa gaya",
                lines=2,
                container=False,
            )
            convert_btn = gr.Button("Normalize", variant="primary", size="lg")
            convert_output = gr.HTML()

            convert_btn.click(live_convert, inputs=input_text, outputs=convert_output)
            input_text.submit(live_convert, inputs=input_text, outputs=convert_output)
            input_text.change(live_convert, inputs=input_text, outputs=convert_output)

            gr.Examples(
                examples=[
                    ["bohotttt achaaa movie thi yaar, maza aa gaya"],
                    ["kya karra h tu aajkal, sab theek?"],
                    ["bhai sahb kya kmaal ki acting ki hai salman ne"],
                    ["arre waah shndaar century by kohli"],
                    ["chal bey nikal yahan se, faltuuu log"],
                    ["paneer masala aur dal chawal dena bhai"],
                ],
                inputs=input_text,
                label="Try these",
            )

        with gr.TabItem("Same Word?"):
            gr.HTML("""<p class="tab-intro">
                Do two different spellings refer to the same word?
                Type any two romanized Hindi words and find out. Uses IPA as a phonetic bridge.
            </p>""")

            with gr.Row():
                word_a = gr.Textbox(label="Word 1", placeholder="e.g. bahut", lines=1)
                word_b = gr.Textbox(label="Word 2", placeholder="e.g. bohot", lines=1)

            compare_btn = gr.Button("Compare", variant="primary", size="lg")
            compare_output = gr.HTML()

            compare_btn.click(compare_words, inputs=[word_a, word_b], outputs=compare_output)
            word_a.submit(compare_words, inputs=[word_a, word_b], outputs=compare_output)
            word_b.submit(compare_words, inputs=[word_a, word_b], outputs=compare_output)

            gr.Examples(
                examples=[
                    ["bahut", "bohot"],
                    ["accha", "achha"],
                    ["kaise", "kese"],
                    ["shaandar", "shandar"],
                    ["bakwas", "bkwaas"],
                    ["ghatiya", "ghtiya"],
                ],
                inputs=[word_a, word_b],
                label="Try these pairs",
            )

        with gr.TabItem("Search"):
            gr.HTML(f"""<p class="tab-intro">
                Search <strong>{len(SEARCH_CORPUS) if SEARCH_CORPUS else 0} real Hindi tweets</strong>.
                Type any spelling variant and find all matches.
                "accha" finds posts with achha, acha, achaa. "bohot" finds bahut, boht, bhot.
            </p>""")

            search_input = gr.Textbox(
                show_label=False,
                placeholder="Search: accha, film, modi, cricket, pyaar, desh...",
                lines=1,
                container=False,
            )
            search_btn = gr.Button("Search", variant="primary", size="lg")
            search_results = gr.HTML()

            search_btn.click(search_corpus, inputs=search_input, outputs=search_results)
            search_input.submit(search_corpus, inputs=search_input, outputs=search_results)

            gr.Examples(
                examples=["achha", "bohot", "pyaar", "modi", "cricket", "bakwaas"],
                inputs=search_input,
                label="Try these",
            )

        with gr.TabItem("Sentiment"):
            gr.HTML("""<p class="tab-intro">
                Lexicon-based sentiment analysis on Hinglish text. Compares results
                <strong>with and without</strong> dhvani normalization to show how spelling
                variation causes missed signals.
            </p>""")

            sent_input = gr.Textbox(
                show_label=False,
                placeholder="Try: bohot acchi movie thi yaar, kamaal ki acting",
                lines=2,
                container=False,
            )
            sent_btn = gr.Button("Analyze", variant="primary", size="lg")
            sent_output = gr.HTML()

            sent_btn.click(analyze_sentiment, inputs=sent_input, outputs=sent_output)
            sent_input.submit(analyze_sentiment, inputs=sent_input, outputs=sent_output)

            gr.Examples(
                examples=[
                    ["kmaal kr diya usne, jabrdst performance"],
                    ["ekdm faltuuu movie thi yaar"],
                    ["bekaaaar si movie thi interval me nikal gaye"],
                    ["khraab direction thi ekdum, bevkoof director"],
                    ["mza aa gya live concert me jaake"],
                    ["shndaar performance, full mza aaya"],
                ],
                inputs=sent_input,
                label="Try these (dhvani changes the result!)",
            )

    with gr.Accordion("About", open=False):
        gr.HTML(f"""
        <p class="about-text">
            <strong>dhvani</strong> resolves spelling variation in Romanized Hindi using IPA
            (International Phonetic Alphabet) as a bridge. All romanizations of a word produce
            the same sound, so they map to the same IPA form. This enables search, sentiment
            analysis, and content moderation to work on code-mixed Indian social media text
            without requiring a language model at inference time.
        </p>
        <p class="about-text" style="margin-top:8px;">
            Evaluated on the Cardiff Hindi Tweet Sentiment dataset, normalization improves
            macro F1 by +1.2 points. The improvement increases on highly informal text.
        </p>
        <p class="about-footer">
            {lex_count} entries | &lt;1ms/word | Built at Ohio State University |
            <a href="https://pypi.org/project/dhvani/">PyPI</a> |
            <a href="https://github.com/Kkoundinyaa/dhvani">GitHub</a> |
            MIT License
        </p>
        """)


if __name__ == "__main__":
    demo.queue(default_concurrency_limit=5)
    demo.launch(share=True, css=CSS)
