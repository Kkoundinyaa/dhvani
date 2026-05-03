"""dhwani demo - Hinglish NLP preprocessing that actually makes a difference.

Shows dhwani's value through three real applications:
1. Live Hinglish normalizer (type messy Hinglish, get clean Devanagari)
2. Spelling-agnostic search (find all variants of a word in a corpus)
3. Sentiment analysis improvement (with vs without normalization)
"""

import sys
import os
import re
import json
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr
import dhvani
from dhvani.similarity import phonetic_similarity

# Pre-warm lexicon
print("Loading lexicon...", flush=True)
phonetic_similarity("a", "b")
print("Ready.", flush=True)

# ===========================================================================
# Load pre-built search index (real Hindi tweets)
# ===========================================================================

SEARCH_INDEX = None
SEARCH_CORPUS = None

_index_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "search_index.json")
if os.path.exists(_index_path):
    print("Loading pre-built search index...", flush=True)
    with open(_index_path, "r", encoding="utf-8") as _f:
        _index_data = json.load(_f)
        SEARCH_CORPUS = _index_data["corpus"]
        SEARCH_INDEX = {
            "devanagari": _index_data["inverted_devanagari"],
            "romanized": _index_data["inverted_romanized"],
        }
    print(f"Search index loaded: {len(SEARCH_CORPUS)} tweets.", flush=True)
else:
    print("Warning: No pre-built search index found. Using sample corpus as fallback.", flush=True)


# ===========================================================================
# Sample corpus: realistic Hinglish social media comments
# ===========================================================================

SAMPLE_CORPUS = [
    "bohot acchi movie thi yaar, maza aa gaya",
    "kya bakwas hai ye, time waste",
    "bhai sahab kya acting ki hai, kamaal",
    "boht boring thi, interval me nikal gaye",
    "accha tha lekin climax galat tha",
    "yr ye to masterpiece hai bilkul",
    "kharab thi ekdum, mat dekhna",
    "bhot achha gana hai ye, loop pe suno",
    "bahut bura laga sunke, dukhi ho gaya",
    "mast movie hai, full paisa vasool",
    "faltu movie thi, paise barbaad",
    "shandar performance by everyone",
    "kya ghatiya acting thi usne ki",
    "bhai dil khush ho gaya dekhke",
    "pagal hai kya ye director, kuch bhi banaya",
    "bahut pyaari movie hai, family ke saath dekho",
    "bekaar script thi, story me koi dum nahi",
    "jabardast movie hai boss, ekdum dhamakedaar",
    "ye movie dekh ke gussa aa gaya",
    "waah bhai waah, kya film banayi hai",
    "bhot hi bakwas ending thi",
    "sachme acchi movie thi, zarur dekhna",
    "kya bekar gaana hai ye, band karo",
    "dal makhani aur naan best combo hai",
    "daal chawal khana hai aaj raat",
    "dil ko choo liya is movie ne",
    "bohot hi zyada boring tha, neend aa gayi",
    "maza nhi aaya, bahut slow thi",
    "superb acting, lajawab performance",
    "achha nahi laga mujhe, below average",
    "paisa wasool movie hai ye to",
    "kya tatti movie thi yaar, worst",
    "bhaut accha kaam kiya hai inhone",
    "ghatiya direction, ghatiya script, sab bekaar",
    "mazedaar movie hai, comedy bhi achi thi",
    "nahi dekhni chahiye ye movie, time waste",
    "shandar shandar shandar, hit hogi ye",
    "bhai mazaa aa gaya live dekhke",
    "bahut hi dard hua dekhke ye scene",
    "achhi photography thi lekin story weak",
    "kya kamaal ka gaana likha hai yaar",
    "bohot zyaada acchi movie thi, loved it",
]


# ===========================================================================
# Backend functions
# ===========================================================================

def live_convert(text):
    """Real-time Hinglish to Devanagari + IPA."""
    if not text.strip():
        return "", ""
    return dhvani.to_devanagari(text), dhvani.to_ipa(text)


def search_corpus(query):
    """Spelling-agnostic search over 2700+ real Hindi tweets using pre-built index."""
    if not query.strip():
        return ""

    # If pre-built index is available, use fast index lookup
    if SEARCH_INDEX is not None and SEARCH_CORPUS is not None:
        return _search_indexed(query)

    # Fallback to sample corpus search
    return _search_fallback(query)


def _search_indexed(query):
    """Fast search using the pre-built inverted index."""
    query_words = re.sub(r'[.,!?;:"\'\-()\[\]]', ' ', query.lower().strip()).split()
    if not query_words:
        return ""

    matched_indices = set()

    for qw in query_words:
        # Look up exact romanized match
        if qw in SEARCH_INDEX["romanized"]:
            matched_indices.update(SEARCH_INDEX["romanized"][qw])

        # Normalize query word to Devanagari and look up
        try:
            qw_dev = dhvani.to_devanagari(qw)
            if qw_dev and qw_dev in SEARCH_INDEX["devanagari"]:
                matched_indices.update(SEARCH_INDEX["devanagari"][qw_dev])
        except Exception:
            pass

    if not matched_indices:
        return f"""<div class="search-empty">
            No results found for "{query}". Try words like: accha, film, modi, cricket, pyaar
        </div>"""

    # Sort by index and limit to 20 results
    sorted_indices = sorted(matched_indices)[:20]

    sentiment_colors = {"positive": "#16a34a", "negative": "#dc2626", "neutral": "#6b7280"}

    total = len(matched_indices)
    shown = len(sorted_indices)
    html = f'<div class="search-meta">{total} results for "{query}" (showing {shown}, matches all spelling variants)</div>'

    for idx in sorted_indices:
        entry = SEARCH_CORPUS[idx]
        sent = entry["sentiment"]
        color = sentiment_colors.get(sent, "#6b7280")
        html += f"""<div class="search-result">
            <div class="search-original">{entry['text']}</div>
            <div class="search-dev">{entry['devanagari']}</div>
            <div style="font-size:0.72rem; margin-top:3px; color:{color}; font-weight:500; text-transform:uppercase;">{sent}</div>
        </div>"""

    return html


def _search_fallback(query):
    """Fallback search over the sample corpus (used if index not available)."""
    query_words = query.lower().strip().split()
    results = []

    query_dev = dhvani.to_devanagari(query.lower().strip())
    query_dev_words = query_dev.split()

    for comment in SAMPLE_CORPUS:
        comment_lower = comment.lower()
        comment_words = re.sub(r'[.,!?;:"\'\-()\[\]]', ' ', comment_lower).split()
        comment_dev = dhvani.to_devanagari(comment_lower)
        comment_dev_words = re.sub(r'[.,!?;:"\'\-()\[\]]', ' ', comment_dev).split()

        matched = False
        for qi, qw in enumerate(query_words):
            qw_dev = query_dev_words[qi] if qi < len(query_dev_words) else ""

            for ci, cw in enumerate(comment_words):
                if qw == cw:
                    matched = True
                    break
                cw_dev = comment_dev_words[ci] if ci < len(comment_dev_words) else ""
                if qw_dev and cw_dev and len(qw_dev) >= 2:
                    if qw_dev == cw_dev:
                        matched = True
                        break
                    shorter = min(len(qw_dev), len(cw_dev))
                    longer = max(len(qw_dev), len(cw_dev))
                    if shorter >= 2 and longer <= shorter + 1:
                        prefix_len = 0
                        for a, b in zip(qw_dev, cw_dev):
                            if a == b:
                                prefix_len += 1
                            else:
                                break
                        if prefix_len >= shorter - 1 and prefix_len >= 2:
                            matched = True
                            break
                try:
                    if len(qw) >= 3 and len(cw) >= 3 and phonetic_similarity(qw, cw) >= 0.85:
                        matched = True
                        break
                except Exception:
                    pass
            if matched:
                break

        if matched:
            dev = dhvani.to_devanagari(comment)
            results.append((comment, dev))

    if not results:
        return f"""<div class="search-empty">
            No results found for "{query}". Try words like: accha, bakwas, maza, boring, kamaal
        </div>"""

    html = f'<div class="search-meta">{len(results)} results for "{query}" (matches all spelling variants)</div>'
    for original, dev in results:
        html += f"""<div class="search-result">
            <div class="search-original">{original}</div>
            <div class="search-dev">{dev}</div>
        </div>"""

    return html


def analyze_sentiment(text):
    """Simple sentiment analysis showing normalization impact."""
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
        # Slang/abusive (strong negative sentiment)
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

    # Without normalization
    pos_raw = sum(1 for w in words if w in POSITIVE)
    neg_raw = sum(1 for w in words if w in NEGATIVE)

    # With normalization
    dev_text = dhvani.to_devanagari(clean)
    dev_words = dev_text.split()

    pos_norm = pos_raw + sum(1 for w in dev_words if w in POSITIVE_DEV)
    neg_norm = neg_raw + sum(1 for w in dev_words if w in NEGATIVE_DEV)

    # Determine sentiments
    if pos_raw > neg_raw:
        raw_sent = "positive"
    elif neg_raw > pos_raw:
        raw_sent = "negative"
    else:
        raw_sent = "neutral"

    if pos_norm > neg_norm:
        norm_sent = "positive"
    elif neg_norm > pos_norm:
        norm_sent = "negative"
    else:
        norm_sent = "neutral"

    improved = raw_sent != norm_sent

    # Build result HTML
    sent_colors = {"positive": "#16a34a", "negative": "#dc2626", "neutral": "#6b7280"}

    html = f"""
    <div class="sent-container">
        <div class="sent-input">
            <div class="sent-label">Input</div>
            <div class="sent-text">{text}</div>
        </div>
        <div class="sent-normalized">
            <div class="sent-label">Normalized (Devanagari)</div>
            <div class="sent-text">{dev_text}</div>
        </div>
        <div class="sent-results">
            <div class="sent-col">
                <div class="sent-label">Without dhwani</div>
                <div class="sent-verdict" style="color:{sent_colors[raw_sent]}">{raw_sent.upper()}</div>
                <div class="sent-counts">+{pos_raw} / -{neg_raw}</div>
            </div>
            <div class="sent-col">
                <div class="sent-label">With dhwani</div>
                <div class="sent-verdict" style="color:{sent_colors[norm_sent]}">{norm_sent.upper()}</div>
                <div class="sent-counts">+{pos_norm} / -{neg_norm}</div>
            </div>
        </div>
    </div>"""

    if improved:
        html += '<div class="sent-note">dhwani normalization changed the prediction by resolving spelling variants to known sentiment words.</div>'

    return html


# ===========================================================================
# CSS
# ===========================================================================

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

.gradio-container {
    max-width: 820px !important;
    margin: 0 auto !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
}
footer { display: none !important; }

/* Header */
.hdr { padding: 44px 0 28px; text-align: center; border-bottom: 1px solid #f0f0f0; margin-bottom: 4px; }
.dark .hdr { border-color: #1a1a1a; }
.hdr-title { font-size: 1.8rem; font-weight: 700; letter-spacing: -0.04em; color: #0a0a0a; margin: 0 0 6px; }
.dark .hdr-title { color: #fafafa; }
.hdr-sub { font-size: 0.86rem; color: #6b7280; margin: 0 0 16px; line-height: 1.5; }
.hdr-pills { display: inline-flex; gap: 6px; }
.hdr-pill { font-size: 0.7rem; font-weight: 500; padding: 3px 10px; border-radius: 100px; border: 1px solid #e5e7eb; color: #6b7280; background: #fafafa; }
.dark .hdr-pill { border-color: #262626; background: #141414; color: #737373; }

/* Tabs */
.tab-nav button { font-weight: 500 !important; font-size: 0.84rem !important; padding: 11px 18px !important; color: #9ca3af !important; }
.tab-nav button.selected { color: #0a0a0a !important; box-shadow: inset 0 -2px 0 #0a0a0a !important; }
.dark .tab-nav button.selected { color: #fafafa !important; box-shadow: inset 0 -2px 0 #fafafa !important; }

.tab-desc { font-size: 0.84rem; color: #9ca3af; margin: 10px 0 14px; }

/* Search results */
.search-meta { font-size: 0.8rem; color: #6b7280; margin-bottom: 10px; font-weight: 500; }
.search-result { padding: 10px 14px; border: 1px solid #f0f0f0; border-radius: 8px; margin-bottom: 6px; }
.dark .search-result { border-color: #262626; }
.search-original { font-size: 0.9rem; color: #374151; }
.dark .search-original { color: #d1d5db; }
.search-dev { font-size: 0.82rem; color: #9ca3af; margin-top: 2px; }
.search-empty { font-size: 0.88rem; color: #9ca3af; padding: 20px; text-align: center; }

/* Sentiment */
.sent-container { border: 1px solid #f0f0f0; border-radius: 10px; padding: 16px; }
.dark .sent-container { border-color: #262626; }
.sent-input, .sent-normalized { margin-bottom: 12px; }
.sent-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em; color: #9ca3af; font-weight: 600; margin-bottom: 4px; }
.sent-text { font-size: 0.9rem; color: #374151; line-height: 1.5; }
.dark .sent-text { color: #d1d5db; }
.sent-results { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 14px; padding-top: 14px; border-top: 1px solid #f0f0f0; }
.dark .sent-results { border-color: #262626; }
.sent-col { text-align: center; padding: 12px; border-radius: 8px; background: #f9fafb; }
.dark .sent-col { background: #141414; }
.sent-verdict { font-size: 1.1rem; font-weight: 700; margin: 4px 0; }
.sent-counts { font-size: 0.75rem; color: #9ca3af; font-family: 'JetBrains Mono', monospace; }
.sent-note { font-size: 0.8rem; color: #2563eb; margin-top: 10px; padding: 8px 12px; background: #eff6ff; border-radius: 6px; }
.dark .sent-note { background: #172554; color: #93c5fd; }

/* Buttons */
.primary { background: #0a0a0a !important; color: #fff !important; border: none !important; font-weight: 500 !important; border-radius: 6px !important; }
.dark .primary { background: #fafafa !important; color: #0a0a0a !important; }

textarea, input[type="text"] { font-family: 'Inter', sans-serif !important; font-size: 0.9rem !important; }
"""


# ===========================================================================
# Layout
# ===========================================================================

from dhvani.lexicon.lookup import get_lexicon_stats
stats = get_lexicon_stats()
lex_count = f"{stats['ipa_entries']:,}"

with gr.Blocks(title="dhwani") as demo:

    gr.HTML(f"""
    <div class="hdr">
        <div class="hdr-title">dhwani</div>
        <p class="hdr-sub">
            Phonetic normalization for Hinglish. A preprocessing layer<br>
            that makes NLP tools work on code-mixed Hindi-English text.
        </p>
        <div class="hdr-pills">
            <span class="hdr-pill">{lex_count} lexicon entries</span>
            <span class="hdr-pill">Spelling-agnostic</span>
            <span class="hdr-pill">No model at inference</span>
        </div>
    </div>
    """)

    with gr.Tabs():

        # === Tab 1: Live Normalizer ===
        with gr.TabItem("Normalize"):
            gr.HTML('<p class="tab-desc">Type messy Hinglish. Get clean Devanagari and IPA instantly.</p>')

            input_text = gr.Textbox(
                show_label=False,
                placeholder="bohotttt achaaa movie thi yaar, maza aa gaya",
                lines=2,
                container=False,
            )
            convert_btn = gr.Button("Normalize", variant="primary", size="lg")

            with gr.Row(equal_height=True):
                output_dev = gr.Textbox(label="Devanagari", lines=2, interactive=False, buttons=["copy"])
                output_ipa = gr.Textbox(label="IPA", lines=2, interactive=False, buttons=["copy"])

            convert_btn.click(live_convert, inputs=input_text, outputs=[output_dev, output_ipa])
            input_text.submit(live_convert, inputs=input_text, outputs=[output_dev, output_ipa])

            gr.Examples(
                examples=[
                    ["bohotttt achaaa movie thi yaar"],
                    ["kya karra h tu aajkal"],
                    ["paneer masala aur dal chawal dena bhai"],
                    ["ye bilkul galat hai, bus mat karo"],
                    ["the movie was really acchi thi"],
                ],
                inputs=input_text,
                label="",
            )

        # === Tab 2: Search ===
        with gr.TabItem("Search"):
            gr.HTML("""<p class="tab-desc">
                Search 2700+ real Hindi tweets. Finds all spelling variants automatically via Devanagari normalization.<br>
                Try "accha" (also finds achha, acha, achaa) or "film" or "modi" or "cricket".
            </p>""")

            search_input = gr.Textbox(
                show_label=False,
                placeholder="Search: accha, maza, boring, kamaal, bakwas...",
                lines=1,
                container=False,
            )
            search_btn = gr.Button("Search", variant="primary", size="lg")
            search_results = gr.HTML()

            search_btn.click(search_corpus, inputs=search_input, outputs=search_results)
            search_input.submit(search_corpus, inputs=search_input, outputs=search_results)

            gr.Examples(
                examples=["accha", "film", "modi", "cricket", "pyaar", "desh"],
                inputs=search_input,
                label="",
            )

        # === Tab 3: Sentiment ===
        with gr.TabItem("Sentiment"):
            gr.HTML("""<p class="tab-desc">
                Lexicon-based sentiment analysis. Shows how dhwani normalization catches
                sentiment words that raw text matching misses due to spelling variation.
            </p>""")

            sent_input = gr.Textbox(
                show_label=False,
                placeholder="e.g. bohot hi acchi movie thi, kamaal ki acting",
                lines=2,
                container=False,
            )
            sent_btn = gr.Button("Analyze", variant="primary", size="lg")
            sent_output = gr.HTML()

            sent_btn.click(analyze_sentiment, inputs=sent_input, outputs=sent_output)
            sent_input.submit(analyze_sentiment, inputs=sent_input, outputs=sent_output)

            gr.Examples(
                examples=[
                    ["bohot acchi movie thi yaar, maza aa gaya"],
                    ["kya bakwas hai ye, bekaar movie"],
                    ["bhai sahab kya kamaal ki acting ki hai"],
                    ["bhot hi ghatiya thi, pagal director"],
                    ["sachme achha laga dekhke, dil khush ho gaya"],
                    ["faltu movie, barbaad ho gaye paise"],
                ],
                inputs=sent_input,
                label="",
            )

    with gr.Accordion("About", open=False):
        gr.HTML(f"""
        <p style="font-size:0.84rem; color:#6b7280; line-height:1.65;">
            <strong>dhwani</strong> is a phonetic normalization library for Hinglish text.
            It resolves the wild spelling variation in Romanized Hindi ("bahut", "bohot", "boht", "bhot"
            are all the same word) using IPA as a bridge representation. This enables downstream NLP
            tasks like sentiment analysis, search, and content moderation to work correctly on
            code-mixed Indian social media text.
        </p>
        <p style="font-size:0.84rem; color:#6b7280; line-height:1.65; margin-top:8px;">
            Evaluated on the Cardiff Hindi Tweet Sentiment dataset: dhwani normalization improves
            macro F1 by +1.2 points over raw text matching. The improvement is larger on highly
            informal text with more spelling variation.
        </p>
        <p style="font-size:0.78rem; color:#9ca3af; margin-top:12px; padding-top:12px; border-top:1px solid #f0f0f0;">
            {lex_count} lexicon entries | No model needed at inference | Built at Ohio State University |
            <a href="https://github.com/Kkoundinyaa/dhwani" style="color:#2563eb;">GitHub</a> | MIT License
        </p>
        """)

if __name__ == "__main__":
    demo.queue(default_concurrency_limit=5)
    demo.launch(share=True, css=CSS)
