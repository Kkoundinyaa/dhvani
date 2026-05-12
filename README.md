# dhvani

Phonetic normalization for Hinglish text.

dhvani maps variant spellings of Romanized Hindi to canonical forms using IPA as a bridge. "bahut", "bohot", "boht", and "bhot" all produce the same IPA, so they all normalize to the same word.

[Live Demo](https://krishnabadikela-dhvani.hf.space) | [PyPI](https://pypi.org/project/dhvani/) | v0.2.5

```python
pip install dhvani
```

```python
import dhvani

dhvani.to_devanagari("bohotttt achaaa movie thi yaar")
# -> "बहुत अच्छा movie थी यार"

dhvani.are_same("bahut", "bohot")   # True
dhvani.are_same("bahut", "बहुत")    # True (cross-script)

dhvani.to_ipa("kaise ho bhai")
# -> "kɛːseː ɦoː bʱaːiː"
```

---

## The problem

600M+ Indians write online in Hinglish (Hindi in Latin script, mixed with English). There is no standardized spelling:

| Word | Variants typed online |
|------|----------------------|
| बहुत (very) | bahut, bohot, boht, bhot, bahot, bht, bhaut |
| अच्छा (good) | accha, achha, acha, achaa, aacha |
| कैसे (how) | kaise, kese, kayse, kse |
| बोसड़ीके | bosdike, bsdk, bosdk, bsdke, bhosdike |

Every NLP tool that does exact string matching on this text will miss things. dhvani fixes that by normalizing spelling before anything else runs.

---

## Install

```bash
pip install dhvani
```

The 1M+ word lexicon ships with the package. No model downloads, no API keys, no GPU.

---

## Usage

### Transliteration

```python
import dhvani

# Messy social media text
dhvani.to_devanagari("kya karra h tu")
# -> "क्या कर रहा है तू"

# Elongated text
dhvani.to_devanagari("bohotttt achaaa yaaaar")
# -> "बहुत अच्छा यार"

# Abbreviations and vowel-dropped forms
dhvani.to_devanagari("bsdk kya kr rha hai")
# -> "बोसड़ीके क्या कर रहा है"

# English words and punctuation are left alone
dhvani.to_devanagari("the movie was really acchi thi!")
# -> "the movie was really अच्छी थी!"
```

### Phonetic matching

```python
# Same word, different spellings
dhvani.are_same("bahut", "bohot")     # True
dhvani.are_same("theek", "tik")       # True
dhvani.are_same("bsdk", "bosdike")    # True

# Cross-script matching
dhvani.are_same("bahut", "बहुत")      # True
dhvani.are_same("achaaaa", "अच्छा")   # True (handles elongation)

# Different words correctly rejected
dhvani.are_same("bahut", "accha")     # False
```

### IPA conversion

```python
dhvani.to_ipa("kaise ho bhai")
# -> "kɛːseː ɦoː bʱaːiː"

dhvani.to_ipa("bahut accha")
# -> "bəɦʊt̪ ət͡ʃːʰaː"
```

### Language identification

```python
dhvani.identify_languages("the movie was really acchi thi")
# -> [("the", "en"), ("movie", "en"), ("was", "en"),
#     ("really", "en"), ("acchi", "hi"), ("thi", "hi")]

# Context-aware: "are" resolves differently based on neighbors
dhvani.identify_languages("are you kidding me")
# -> all English

dhvani.identify_languages("are bhai kya kar raha hai")
# -> "are" tagged as Hindi (अरे)
```

### Batch processing

```python
dhvani.batch_to_devanagari(["bahut accha", "kya haal hai", "bohot maza aaya"])
# -> ["बहुत अच्छा", "क्या हाल है", "बहुत मज़ा आया"]

dhvani.batch_to_ipa(["bahut", "accha", "kaise"])
# -> ["bəɦʊt̪", "ət͡ʃːʰaː", "kɛːseː"]
```

### CLI

```bash
dhvani devanagari "bohot accha movie thi yaar"
# बहुत अच्छा movie थी यार

dhvani ipa "kaise ho bhai"
# kɛːseː ɦoː bʱaːiː

dhvani same "bahut" "bohot"
# True (similarity: 1.00)
```

---

## How it works

All variant spellings of a Hindi word produce the same sound. dhvani routes through IPA (International Phonetic Alphabet) to collapse them:

```
"bahut"  ─┐
"bohot"  ─┤
"boht"   ─┼──> /bəɦʊt̪/ ──> बहुत
"bhot"   ─┤
"bahotttt"─┘
```

### Architecture

| Tier | Method | Latency | When used |
|------|--------|---------|-----------|
| 0 | Corrector map (500+ hand-verified entries) | <1ms | Abbreviations, slang, vowel-dropped |
| 1 | Lexicon lookup (1M+ entries) | <1ms | ~99% of standard words |
| 2 | AI model (IndicXlit + epitran) | ~4s | Rare/novel words |
| 3 | Rule-based G2P | <1ms | Fallback (no deps) |

The lexicon was built from Hindi Wikipedia (50K articles), IITB parallel corpus (500K sentences), and MASSIVE/XNLI datasets. Each Devanagari word gets 10 romanized spelling variants generated via IPA-to-Roman rules.

### Preprocessing

Before lookup, input goes through:
1. Punctuation stripping (preserved and reattached after)
2. Repeated character collapsing ("bohotttt" -> "bohot")
3. Double consonant fallback (tries collapsed form if double misses)
4. Context-aware language ID (disambiguates words like "are", "the", "bus")

---

## Use cases

Search: index Hinglish content once, find it regardless of spelling. Searching "accha" also finds "achha", "acha", "achaa".

Tokenization: 40% word-level vocabulary reduction and 15-17% fewer BPE/WordPiece tokens when normalizing before tokenization (measured on SentiMix, 545K texts).

Preprocessing for models: normalize messy Hinglish input before feeding to classifiers, chatbots, or LLMs. Spelling variants of the same word resolve to one canonical form.

---

## Live demo

[krishnabadikela-dhvani.hf.space](https://krishnabadikela-dhvani.hf.space)

Three tabs: Normalize (live typing with word-by-word diff, Devanagari, IPA, and language detection), Explorer (type a word, see all known spelling variants), Search (phonetic search over 3,033 real Hindi tweets).

---

## Numbers

- 1,072,153 lexicon entries, 500+ hand-curated corrector entries
- <1ms per word on lexicon hit
- ~2s cold start (lexicon load), then instant
- No model at inference, pure lookup + rules
- 9.7MB package, pip install, zero config

---

## API reference

| Function | Description |
|----------|-------------|
| `dhvani.to_devanagari(text)` | Convert Romanized Hindi to Devanagari |
| `dhvani.to_ipa(text)` | Convert to IPA transcription |
| `dhvani.are_same(word1, word2)` | Check if two words are phonetically equivalent |
| `dhvani.identify_languages(text)` | Per-word language detection (hi/en/hi_dev) |
| `dhvani.normalize(text, target)` | Normalize to "roman", "devanagari", or "ipa" |
| `dhvani.batch_to_devanagari(texts)` | Batch convert list of texts |
| `dhvani.batch_to_ipa(texts)` | Batch IPA conversion |
| `dhvani.batch_normalize(texts)` | Batch normalization |

---

## Research

This grew out of IPA-GPT research at Ohio State University. That work showed IPA representations improve cross-lingual transfer for script-divergent language pairs like Hindi-Urdu by 15-25%. The spelling normalization problem in dhvani is the same underlying issue: same concept, different surface forms.

---

## License

MIT

---

- [Live Demo](https://krishnabadikela-dhvani.hf.space)
- [PyPI](https://pypi.org/project/dhvani/)
- [GitHub](https://github.com/Kkoundinyaa/dhvani)
- Author: Krishna Badikela, Ohio State University
