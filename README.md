# dhwani

**Phonetic normalization for Hinglish text.**

dhwani (ध्वनि = "sound") understands that "bahut", "bohot", "boht", and "bhot" are all the same word. It normalizes the chaos of Romanized Hindi into something computers can actually work with.

## Why?

600M+ Indians write online in Hinglish (Hindi in Latin script mixed with English). But there's no standard spelling:

```
"बहुत" gets written as: bahut, bohot, boht, bhot, bahot
"अच्छा" gets written as: accha, achha, acha, achaa
"कैसे" gets written as: kaise, kese, kayse
```

Every NLP tool breaks on this. dhwani fixes it.

## Install

```bash
pip install git+https://github.com/Kkoundinyaa/dhwani.git
```

For higher accuracy on rare words (optional):
```bash
pip install "dhwani[models] @ git+https://github.com/Kkoundinyaa/dhwani.git"
```

## Usage

```python
import dhwani

# Check if two words are the same (variant spellings)
dhwani.are_same("bahut", "bohot")   # True
dhwani.are_same("accha", "achha")   # True
dhwani.are_same("bahut", "accha")   # False

# Convert Hinglish to Devanagari
dhwani.to_devanagari("bohot accha movie thi yaar")
# -> "बहुत अच्छा movie थी यार"

# Convert to IPA (phonetic representation)
dhwani.to_ipa("kaise ho bhai")
# -> "kɛːseː ɦoː bʱaːiː"

# Word-level language identification
dhwani.identify_languages("ye movie really acchi thi bro")
# -> [("ye", "hi"), ("movie", "en"), ("really", "en"), ("acchi", "hi"), ("thi", "hi"), ("bro", "hi")]

# Normalize text
dhwani.normalize("bohot acha movie thi")
# -> canonical normalized form
```

## CLI

```bash
dhwani devanagari "bohot accha movie thi yaar"
# बहुत अच्छा movie थी यार

dhwani ipa "kaise ho bhai"
# kɛːseː ɦoː bʱaːiː

dhwani same "bahut" "bohot"
# True (phonetic similarity: 1.00)

dhwani langs "ye movie bohot acchi thi"
# ye[hi] movie[en] bohot[hi] acchi[hi] thi[hi]
```

## How It Works

dhwani routes through IPA (International Phonetic Alphabet) as a bridge representation. All variant spellings of a word produce the same sound, so they map to the same IPA:

```
"bahut" ─┐
"bohot" ─┤──> /bəɦʊt̪/ ──> बहुत
"boht"  ─┤
"bhot"  ─┘
```

**Three-tier architecture for speed:**

| Tier | Method | Speed | Coverage |
|------|--------|-------|----------|
| 1 | Lexicon lookup (151K entries) | 0.001ms | ~95% of common words |
| 2 | AI model (IndicXlit + epitran) | ~4s | Handles anything |
| 3 | Rule-based G2P | 0.005ms | Always available |

Plus a runtime cache that learns: words processed by Tier 2 get cached permanently, so the library gets faster over time.

## Features

- **Phonetic equivalence**: Detect if two words are the same regardless of spelling
- **Transliteration**: Romanized Hindi to Devanagari (and back)
- **IPA conversion**: Any Hindi text (Roman or Devanagari) to IPA
- **Language ID**: Word-level Hindi/English classification in mixed text
- **Zero dependencies** for basic use (lexicon + rules)
- **151K-word lexicon** built from real Hindi corpora
- **Runtime learning**: Gets smarter the more you use it

## Research

Built on findings from IPA-GPT research at Ohio State University, which showed that phonetic (IPA) representations dramatically improve cross-lingual NLP for script-divergent languages like Hindi-Urdu.

## License

MIT
