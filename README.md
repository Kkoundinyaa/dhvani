# dhvani

**Phonetic normalization for Hinglish text.**

dhvani resolves the spelling chaos of Romanized Hindi. It knows that "bahut", "bohot", "boht", and "bhot" are all the same word, and normalizes them to a canonical form using IPA as a bridge representation.

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

## The Problem

600M+ Indians write online in Hinglish (Hindi in Latin script, mixed with English). There is no standardized spelling:

| Word | Variants typed online |
|------|----------------------|
| बहुत (very) | bahut, bohot, boht, bhot, bahot, bht, bhaut |
| अच्छा (good) | accha, achha, acha, achaa, aacha |
| कैसे (how) | kaise, kese, kayse, kse |

This breaks search, sentiment analysis, content moderation, and every other NLP tool. dhvani fixes it.

---

## Install

```bash
pip install dhvani
```

That's it. No model downloads, no API keys, no GPU needed. The 1M+ word lexicon ships with the package.

---

## Usage

### Transliteration

```python
import dhvani

# Handles messy social media text
dhvani.to_devanagari("kya karra h tu")
# -> "क्या कर रहा है तू"

# Handles elongated text
dhvani.to_devanagari("bohotttt achaaa yaaaar")
# -> "बहुत अच्छा यार"

# Preserves English words and punctuation
dhvani.to_devanagari("the movie was really acchi thi!")
# -> "the movie was really अच्छी थी!"
```

### Phonetic Matching

```python
# Same word, different spellings
dhvani.are_same("bahut", "bohot")     # True
dhvani.are_same("theek", "tik")       # True
dhvani.are_same("yaar", "yr")         # True

# Cross-script matching
dhvani.are_same("bahut", "बहुत")      # True
dhvani.are_same("achaaaa", "अच्छा")   # True (handles elongation)

# Different words correctly rejected
dhvani.are_same("bahut", "accha")     # False
```

### IPA Conversion

```python
dhvani.to_ipa("kaise ho bhai")
# -> "kɛːseː ɦoː bʱaːiː"

dhvani.to_ipa("bahut accha")
# -> "bəɦʊt̪ ət͡ʃːʰaː"
```

### Language Identification

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

## How It Works

All variant spellings of a Hindi word produce the same sound. dhvani uses IPA (International Phonetic Alphabet) as a universal bridge:

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
| 1 | Lexicon lookup (1M+ entries) | <1ms | ~99% of words |
| 2 | AI model (IndicXlit + epitran) | ~4s | Rare/novel words |
| 3 | Rule-based G2P | <1ms | Fallback (no deps) |

The lexicon was built from Hindi Wikipedia (50K articles), IITB parallel corpus (500K sentences), and MASSIVE/XNLI datasets, generating 10 romanized spelling variants per word via IPA-to-Roman rules.

### Preprocessing Pipeline

Before lookup, input goes through:
1. **Punctuation stripping** (preserved and reattached after conversion)
2. **Repeated character collapsing** ("bohotttt" -> "bohot")
3. **Double consonant fallback** (tries collapsed form if double misses)
4. **Context-aware language ID** (disambiguates words like "are", "the", "bus")

---

## Use Cases

**Search & Retrieval** -- Index Hinglish content once, find it regardless of spelling. A search for "accha" finds posts containing "achha", "acha", "achaa".

**Sentiment Analysis** -- Normalize text before classification. Spelling variants of sentiment words ("bakwas", "bakwaas", "bakwass") all resolve to the same form.

**Content Moderation** -- Detect abusive content regardless of spelling obfuscation.

**Preprocessing for LLMs** -- Reduce vocabulary size and improve tokenization for Hindi/Hinglish fine-tuning.

---

## Performance

- 1,072,153 lexicon entries
- <1ms per word (lexicon hit)
- ~2s cold start (lexicon load), then instant
- No model needed at inference (pure lookup + rules)
- Tested on Cardiff Hindi Tweet Sentiment dataset: +1.2% macro F1 improvement over raw text

---

## Research

Built on findings from IPA-GPT research at Ohio State University, which demonstrated that phonetic (IPA) representations enable significant cross-lingual transfer improvements for script-divergent languages like Hindi-Urdu.

---

## License

MIT

---

## Links

- **PyPI**: [dhvani](https://pypi.org/project/dhvani/)
- **GitHub**: [Kkoundinyaa/dhwani](https://github.com/Kkoundinyaa/dhwani)
- **Author**: Krishna Badikela, Ohio State University
