"""Phonetic post-correction for transliterated words.

After IndicXlit produces a literal transliteration (e.g., "bohot" -> "बोहोट"),
this module checks if it's phonetically close to a known canonical Hindi word
(e.g., "बहुत") and corrects it.

This solves the core Hinglish problem: informal spellings are phonetic
approximations of real words, not literal transliterations.
"""

from typing import Optional, Tuple

from dhvani.normalizer import ipa_to_canonical
from dhvani.similarity import edit_distance


# Canonical Hindi words with their IPA (the "real" dictionary)
# Format: {canonical_ipa: (devanagari, romanized)}
# This is loaded once and used for all corrections
_CANONICAL_WORDS = None


def _get_canonical_words():
    """Lazy-load the canonical Hindi word dictionary."""
    global _CANONICAL_WORDS
    if _CANONICAL_WORDS is None:
        _CANONICAL_WORDS = _build_canonical_dict()
    return _CANONICAL_WORDS


def _build_canonical_dict():
    """Build the canonical word dictionary.

    Maps simplified IPA -> (devanagari, common_romanization)
    """
    # Core Hindi vocabulary with correct Devanagari and IPA
    # These are the "ground truth" words that variant spellings map to
    words = {
        # word: (devanagari, ipa)
        "bahut": ("बहुत", "bəɦʊt̪"),
        "accha": ("अच्छा", "ət͡ʃːʰaː"),
        "kaise": ("कैसे", "kɛːseː"),
        "nahi": ("नहीं", "nəɦiː"),
        "kya": ("क्या", "kjaː"),
        "yaar": ("यार", "jaːɾ"),
        "theek": ("ठीक", "ʈʰiːk"),
        "hai": ("है", "ɦɛː"),
        "hain": ("हैं", "ɦɛ̃ː"),
        "tha": ("था", "t̪ʰaː"),
        "thi": ("थी", "t̪ʰiː"),
        "the": ("थे", "t̪ʰeː"),
        "aur": ("और", "ɔːɾ"),
        "lekin": ("लेकिन", "leːkɪn"),
        "zyada": ("ज़्यादा", "zjaːd̪aː"),
        "bilkul": ("बिल्कुल", "bɪlkʊl"),
        "matlab": ("मतलब", "mət̪ləb"),
        "samajh": ("समझ", "səməd͡ʒʱ"),
        "zaroor": ("ज़रूर", "zəɾuːɾ"),
        "shayad": ("शायद", "ʃaːjəd̪"),
        "isliye": ("इसलिए", "ɪslɪjeː"),
        "kyunki": ("क्योंकि", "kjoːŋkɪ"),
        "phir": ("फिर", "pʰɪɾ"),
        "abhi": ("अभी", "əbʱiː"),
        "ghar": ("घर", "ɡʱəɾ"),
        "kaam": ("काम", "kaːm"),
        "paisa": ("पैसा", "pɛːsaː"),
        "khana": ("खाना", "kʰaːnaː"),
        "pani": ("पानी", "paːniː"),
        "wala": ("वाला", "ʋaːlaː"),
        "dekh": ("देख", "d̪eːkʰ"),
        "dekho": ("देखो", "d̪eːkʰoː"),
        "karo": ("करो", "kəɾoː"),
        "karna": ("करना", "kəɾnaː"),
        "chalo": ("चलो", "t͡ʃəloː"),
        "bolo": ("बोलो", "boːloː"),
        "jao": ("जाओ", "d͡ʒaːoː"),
        "aao": ("आओ", "aːoː"),
        "suno": ("सुनो", "sʊnoː"),
        "batao": ("बताओ", "bət̪aːoː"),
        "pata": ("पता", "pət̪aː"),
        "log": ("लोग", "loːɡ"),
        "dost": ("दोस्त", "d̪oːst̪"),
        "bhai": ("भाई", "bʱaːiː"),
        "aaj": ("आज", "aːd͡ʒ"),
        "kal": ("कल", "kəl"),
        "subah": ("सुबह", "sʊbəɦ"),
        "raat": ("रात", "ɾaːt̪"),
        "achhi": ("अच्छी", "ət͡ʃːʰiː"),
        "acchi": ("अच्छी", "ət͡ʃːʰiː"),
        "bura": ("बुरा", "bʊɾaː"),
        "sahi": ("सही", "səɦiː"),
        "galat": ("ग़लत", "ɣələt̪"),
        "bada": ("बड़ा", "bəɖaː"),
        "chhota": ("छोटा", "t͡ʃʰoːʈaː"),
        "naya": ("नय���", "nəjaː"),
        "purana": ("पुराना", "pʊɾaːnaː"),
        "toh": ("तो", "t̪oː"),
        "mein": ("में", "mẽː"),
        "hum": ("हम", "ɦəm"),
        "tum": ("तुम", "t̪ʊm"),
        "mujhe": ("मुझे", "mʊd͡ʒʱeː"),
        "tumhe": ("तुम्हें", "t̪ʊmɦẽː"),
        "unhe": ("उन्हें", "ʊnɦẽː"),
        "iske": ("इसके", "ɪskeː"),
        "uske": ("उसके", "ʊskeː"),
        "koi": ("कोई", "koːiː"),
        "kuch": ("कुछ", "kʊt͡ʃʰ"),
        "sab": ("सब", "səb"),
        "bohot": ("बहुत", "bəɦʊt̪"),  # variant -> same as bahut
        "boht": ("बहुत", "bəɦʊt̪"),
        "bhot": ("बहुत", "bəɦʊt̪"),
        "achha": ("अच्छा", "ət͡ʃːʰaː"),
        "acha": ("अच्छा", "ət͡ʃːʰaː"),
        "kese": ("कैसे", "kɛːseː"),
        "nhi": ("नहीं", "nəɦiː"),
        "thik": ("ठीक", "ʈʰiːk"),
        "yr": ("यार", "jaːɾ"),
        "fir": ("फिर", "pʰɪɾ"),
        "paani": ("पानी", "paːniː"),
    }

    # Build the lookup: canonical_ipa -> (devanagari, romanized)
    canonical_dict = {}
    for roman, (dev, ipa) in words.items():
        canonical = ipa_to_canonical(ipa)
        # Store the best (most standard) devanagari for each canonical form
        if canonical not in canonical_dict:
            canonical_dict[canonical] = (dev, roman, ipa)

    return canonical_dict


def correct_transliteration(devanagari: str, original_roman: str) -> str:
    """Correct a literal transliteration to the canonical Hindi word.

    Only corrects if we have high confidence (direct lookup match).
    Otherwise trusts the model output to avoid false corrections.

    Args:
        devanagari: The literal transliteration from IndicXlit (e.g., "बोहोट")
        original_roman: The original romanized input (e.g., "bohot")

    Returns:
        Corrected Devanagari (e.g., "बहुत") or original if no correction found
    """
    # Only correct via direct lookup (high confidence)
    direct = _direct_lookup(original_roman)
    if direct:
        return direct

    # Trust model output for words not in our correction map
    return devanagari


def _collapse_doubles(word: str) -> str:
    """Collapse consecutive double characters to single. e.g., 'yarr' -> 'yar'."""
    result = []
    i = 0
    while i < len(word):
        result.append(word[i])
        if i + 1 < len(word) and word[i] == word[i + 1]:
            i += 2
        else:
            i += 1
    return ''.join(result)


def _direct_lookup(roman: str) -> Optional[str]:
    """Direct lookup of romanized word in canonical dictionary.

    Checks built-in high-priority map FIRST (hand-verified, correct for
    common Hinglish), then falls back to HPC-generated map.
    If not found, tries collapsing double consonants (e.g., "yarr" -> "yar").
    """
    word = roman.lower().strip()

    # Built-in takes priority (hand-verified, handles ambiguous words correctly)
    _VARIANT_TO_CANONICAL = {
        "bohot": "बहुत", "boht": "बहुत", "bhot": "बहुत", "bahot": "बहुत",
        "bahut": "बहुत",
        "accha": "अच्छा", "achha": "अच्छा", "acha": "अच्छा", "achaa": "अच्छा",
        "acchi": "अच्छी", "achhi": "अच्छी", "achi": "अच्छी",
        "kaise": "कैसे", "kese": "कैसे", "kayse": "कैसे",
        "nahi": "नहीं", "nahin": "नहीं", "nhi": "नहीं", "ni": "नहीं",
        "theek": "ठीक", "thik": "ठीक", "tik": "ठीक",
        "yaar": "यार", "yar": "यार", "yr": "यार",
        "phir": "फिर", "fir": "फिर",
        "zyada": "ज़्यादा", "jyada": "ज़्यादा", "zada": "ज़्यादा",
        "bilkul": "बिल्कुल", "bilkool": "बिल्कुल",
        "matlab": "मतलब", "mtlb": "मतलब",
        "samajh": "समझ", "samjh": "समझ", "smjh": "समझ",
        "zaroor": "ज़रूर", "zarur": "ज़रूर",
        "shayad": "शायद",
        "kyunki": "क्योंकि", "kyuki": "क्योंकि",
        "lekin": "लेकिन", "lkn": "लेकिन",
        "isliye": "इसलिए", "islye": "इसलिए",
        "pehle": "पहले", "phle": "पहले",
        "hamesha": "हमेशा", "humesha": "हमेशा",
        "abhi": "अभी",
        "kya": "क्या", "kia": "क्या",
        "hai": "है", "he": "है", "h": "है",
        "hain": "हैं", "hn": "हैं",
        "tha": "था", "thi": "थी", "the": "थे",
        "toh": "तो", "to": "तो",
        "aur": "और", "or": "और",
        "mein": "म��ं", "me": "में",
        "ghar": "घर", "ghr": "घर",
        "kaam": "काम", "kam": "काम",
        "paisa": "पैसा", "paise": "पैसे", "pesa": "पैसा",
        "khana": "खाना",
        "pani": "पानी", "paani": "पानी",
        "wala": "वाला", "wali": "वाली", "wale": "वाले",
        "dekh": "देख", "dekho": "देखो", "dekhna": "देखना",
        "karo": "करो", "karna": "करना", "kar": "कर",
        "chalo": "चल���", "chal": "चल", "chalna": "चलना",
        "bolo": "बोलो", "bol": "बोल", "bolna": "बोलना",
        "suno": "सुनो", "sun": "सुन", "sunna": "सुनना",
        "jao": "जाओ", "ja": "जा", "jana": "जाना",
        "aao": "आओ", "aa": "आ", "aana": "आना",
        "batao": "बताओ", "bata": "बता", "batana": "बताना",
        "pata": "पता", "pta": "पता",
        "log": "\u0932\u094b\u0917", "logo": "\u0932\u094b\u0917\u094b\u0902",
        "dost": "\u0926\u094b\u0938\u094d\u0924",
        "bhai": "\u092d\u093e\u0908",
        "aaj": "\u0906\u091c", "aj": "\u0906\u091c",
        "kal": "\u0915\u0932",
        "subah": "\u0938\u0941\u092c\u0939",
        "raat": "\u0930\u093e\u0924",
        "mat": "\u092e\u0924",
        "bus": "\u092c\u0938",
        "bas": "\u092c\u0938",
        "bada": "\u092c\u0921\u093c\u093e", "badi": "\u092c\u0921\u093c\u0940", "bade": "\u092c\u0921\u093c\u0947",
        "chhota": "\u091b\u094b\u091f\u093e", "chhoti": "\u091b\u094b\u091f\u0940", "chhote": "\u091b\u094b\u091f\u0947",
        "mujhe": "\u092e\u0941\u091d\u0947", "mjhe": "\u092e\u0941\u091d\u0947",
        "tumhe": "\u0924\u0941\u092e\u094d\u0939\u0947\u0902",
        "koi": "\u0915\u094b\u0908",
        "kuch": "\u0915\u0941\u091b",
        "sab": "\u0938\u092c", "sabhi": "\u0938\u092d\u0940",
        "hum": "\u0939\u092e", "tum": "\u0924\u0941\u092e",
        "apna": "\u0905\u092a\u0928\u093e", "apni": "\u0905\u092a\u0928\u0940", "apne": "\u0905\u092a\u0928\u0947",
        "ye": "\u092f\u0947", "yeh": "\u092f\u0947",
        "wo": "\u0935\u094b", "woh": "\u0935\u094b",
        "rahe": "\u0930\u0939\u0947", "raha": "\u0930\u0939\u093e", "rahi": "\u0930\u0939\u0940",
        "ho": "\u0939\u094b",
        "se": "\u0938\u0947",
        "ka": "\u0915\u093e", "ki": "\u0915\u0940", "ke": "\u0915\u0947",
        "ko": "\u0915\u094b",
        "par": "\u092a\u0930", "pe": "\u092a\u0947",
        "na": "\u0928\u093e",
        "bhi": "\u092d\u0940",
        # Food/kitchen words
        "aloo": "आलू", "alo": "आलू", "aaloo": "आलू", "alu": "आलू",
        "matar": "मटर", "mattar": "मटर", "mutter": "मटर",
        "dal": "दाल", "daal": "दाल", "dhal": "दाल",
        "roti": "रोटी", "rotti": "रोटी", "chapati": "चपाती", "chapatti": "चपाती",
        "paneer": "पनीर", "panir": "पनीर", "pneer": "पनीर",
        "chai": "चाय", "chay": "चाय",
        "samosa": "समोसा", "samose": "समोसे",
        "biryani": "बिरयानी", "biriyani": "बिरयानी", "biryni": "बिरयानी",
        "sabzi": "सब्ज़ी", "sabji": "सब्ज़ी",
        "doodh": "दूध", "dudh": "दूध", "dud": "दूध",
        "lassi": "लस्सी", "lasi": "लस्सी",
        "ghee": "घी", "ghi": "घी",
        "masala": "मसाला", "msala": "मसाला",
        "mirch": "मिर्च", "mirchi": "मिर्ची",
        "namak": "नमक", "nmak": "नमक",
        "cheeni": "चीनी", "chini": "चीनी",
        # Social media abbreviations
        "karra": "कर रहा", "karr": "कर", "karre": "कर रहे",
        "krna": "करना", "krke": "करके", "kro": "करो",
        "kr": "कर", "krr": "कर",
        "rha": "रहा", "rhi": "रही", "rhe": "रहे",
        "bht": "बहुत", "bhaut": "बहुत",
        "thk": "ठीक",
        "smjh": "समझ", "smj": "समझ",
        "btao": "बताओ", "bta": "बता", "btana": "बताना",
        "dkh": "देख", "dkhle": "देख ले",
        "chl": "चल", "chlo": "चलो",
        "agya": "आ गया", "hogya": "हो गया", "hogyi": "हो गई",
        "aaja": "आ जा", "aajao": "आ जाओ",
        "lgta": "लगता", "lgra": "लग रहा",
        "pta": "पता", "ptani": "पता नहीं",
        # Numbers
        "do": "दो", "tu": "तू",
        # Pronouns/postpositions commonly wrong in auto-generation
        "hum": "हम", "tum": "तुम",
        "mujhe": "मुझे", "mjhe": "मुझे", "mko": "मुझको",
        "tujhe": "तुझे", "tjhe": "तुझे", "tko": "तुझको",
        "usko": "उसको", "usse": "उससे",
        "iske": "इसके", "uske": "उसके",
        "mera": "मेरा", "meri": "मेरी", "mere": "मेरे",
        "tera": "तेरा", "teri": "तेरी", "tere": "तेरे",
        "unka": "उनका", "unki": "उनकी", "unke": "उनके",
        "hmara": "हमारा", "hmari": "हमारी", "hmare": "हमारे",
        "tumhara": "तुम्हारा", "tumhari": "तुम्हारी", "tumhare": "तुम्हारे",
        # Common verbs
        "suno": "सुनो", "sun": "सुन",
        "bolo": "बोलो", "bola": "बोला", "boli": "बोली",
        "ruk": "रुक", "rukk": "रुक",
        "rkh": "रख", "rkho": "रखो",
        # Emotions
        "sach": "सच", "sachme": "सच में", "pakka": "पक्का",
        "zada": "ज़्यादा", "zyda": "ज़्यादा", "jyda": "ज़्यादा",
        # Time
        "phle": "पहले", "phele": "पहले",
        "abh": "अभी", "abi": "अभी",
        "bs": "बस", "bss": "बस",
        "fr": "फिर", "tb": "तब", "jb": "जब", "kb": "कब",
        # Question words
        "kse": "कैसे", "kon": "कौन", "kyu": "क्यूं", "kyun": "क्यूं",
        "kidhr": "किधर", "udhr": "उधर", "idhr": "इधर",
        # Particles
        "wala": "वाला", "wali": "वाली", "wale": "वाले",
        "waala": "वाला", "waali": "वाली", "waale": "वाले",
        # Slang/address forms
        "bey": "बे", "be": "बे", "oye": "ओये", "abe": "अबे", "abey": "अबे",
        "lodu": "लोडू", "chutiya": "चूतिया", "saala": "साला", "saale": "साले",
        "saali": "साली", "kamina": "कमीना", "kamini": "कमीनी",
        "harami": "हरामी", "gadha": "गधा", "ullu": "उल्लू",
        "gaandu": "गांडू", "gandu": "गांडू",
        "chal": "चल", "nikal": "निकल", "hatt": "हट",
    }

    builtin = _VARIANT_TO_CANONICAL.get(word)
    if builtin:
        return builtin

    # Fall back to HPC-generated correction map (large coverage, auto-generated)
    from dhvani.lexicon.lookup import lookup_devanagari
    generated = lookup_devanagari(word)
    if generated:
        return generated

    # Try collapsing double consonants (e.g., "yarr" -> "yar", "bohott" -> "bohot")
    collapsed = _collapse_doubles(word)
    if collapsed != word:
        builtin2 = _VARIANT_TO_CANONICAL.get(collapsed)
        if builtin2:
            return builtin2
        generated2 = lookup_devanagari(collapsed)
        if generated2:
            return generated2

    return None


def _find_closest_canonical(target_canonical: str, max_distance: int = 3) -> Optional[str]:
    """Find the closest canonical Hindi word by phonetic distance.

    Args:
        target_canonical: Canonical IPA of the word to match
        max_distance: Maximum edit distance to consider a match

    Returns:
        Devanagari of the closest match, or None
    """
    canonical_dict = _get_canonical_words()
    best_dev = None
    best_dist = max_distance + 1

    for canonical_ipa, (dev, roman, ipa) in canonical_dict.items():
        dist = edit_distance(target_canonical, canonical_ipa)
        if dist < best_dist:
            best_dist = dist
            best_dev = dev

    if best_dist <= max_distance:
        return best_dev
    return None
