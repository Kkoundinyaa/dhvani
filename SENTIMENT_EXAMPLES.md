# dhvani Sentiment Analysis: Where Normalization Helps

This document shows cases where dhvani normalization changes the sentiment
prediction by resolving abbreviated/misspelled Hinglish to known sentiment words.

---

## How it works

Without dhvani: raw text matching against a sentiment lexicon.
With dhvani: normalize to Devanagari first, then match against both romanized AND Devanagari lexicons.

The difference shows up when users type abbreviated or misspelled words that
miss the romanized lexicon but resolve to known Devanagari forms after normalization.

---

## General examples

| Input | Normalized | Without dhvani | With dhvani | Changed? |
|-------|-----------|----------------|-------------|----------|
| kmaal kr diya usne | कमाल कर दिया उसने | neutral (+0/-0) | positive (+1/-0) | YES |
| khraab direction thi ekdum | खराब direction थी एकदुम | neutral (+0/-0) | negative (+0/-1) | YES |
| bevkoof hai kya ye banda | बेवकूफ है क्या ये बंद | neutral (+0/-0) | negative (+0/-1) | YES |
| ekdm faltuuu movie thi yaar | एकदम फालतू movie थी यार | neutral (+0/-0) | negative (+0/-1) | YES |
| shndaar performance, full mza aaya | शनदार पेरफोरमनचे फुल्ल मज़ा आया | neutral (+0/-0) | positive (+1/-0) | YES |
| bkwaas ending thi movie ki | बकवास ending थी movie की | neutral (+0/-0) | negative (+0/-1) | YES |
| bhaut acha kaam kiya hai tune | बहुत अच्छा काम किया है तूने | positive (+2/-0) | positive (+4/-0) |  |
| kya ghtiya acting thi usne ki | क्या घतिय acting थी उसने की | neutral (+0/-0) | neutral (+0/-0) |  |
| mzedaar comedy hai ye | मजेदार चोमेदय है ये | neutral (+0/-0) | neutral (+0/-0) |  |
| jbrdst film thi boss | ज़बरदस्त film थी बोस | neutral (+0/-0) | neutral (+0/-0) |  |
| pgl director ne kch bhi bana diya | पगल दिरेचतोर नए काँच भी बना दिया | neutral (+0/-0) | neutral (+0/-0) |  |
| lajwab gaana hai yaar | लजवब गाना है यार | neutral (+0/-0) | neutral (+0/-0) |  |
| brbad ho gye paise | बरबाद हो गये पैसे | neutral (+0/-0) | neutral (+0/-0) |  |
| pyaari si movie thi family ke liye | प्यारी सई movie थी family के लिये | positive (+1/-0) | positive (+2/-0) |  |
| dhmakedar entry thi bhai ki | दमकेदर एनतरय थी भाई की | neutral (+0/-0) | neutral (+0/-0) |  |
| wahyat script thi puri | वहयत स्क्रिप्ट थी पुरी | neutral (+0/-0) | neutral (+0/-0) |  |
| bdhiya tha interval tak | बदइय था इनतेरवल तक | neutral (+0/-0) | neutral (+0/-0) |  |
| shrmnk harkat hai ye | शरमनक हरकत है ये | neutral (+0/-0) | neutral (+0/-0) |  |
| drd hua dekhke ye scene | दर्द हुआ देखके ये सीन | neutral (+0/-0) | neutral (+0/-0) |  |
| kush ho gya dekhke result | कुश हो गया देखके रेसुलत | neutral (+0/-0) | neutral (+0/-0) |  |

---

## Tweet-style examples

| Input | Normalized | Without dhvani | With dhvani | Changed? |
|-------|-----------|----------------|-------------|----------|
| bhai sahb kya kmaal ki acting ki hai salman ne | भाई साहब क्या कमाल की acting की है सलमान नए | neutral (+0/-0) | positive (+1/-0) | YES |
| modi ji ne desh k liye bhut acha kaam kiya | मोदी ज़ी नए देश कह लिये बहुत अच्छा काम किया | positive (+1/-0) | positive (+3/-0) |  |
| ye gana sun k dil khsh ho gya yaar | ये गाना सुन कह डील खश हो गया यार | positive (+1/-0) | positive (+1/-0) |  |
| kya bkwas match tha aaj, time waste | क्या बकवस match था आज time वास्ते | negative (+0/-1) | negative (+0/-1) |  |
| arre waah bhai shndaar century by kohli | अर्रे वाह भाई शनदार चेनतुरय by कोहली | positive (+1/-0) | positive (+2/-0) |  |
| kitni ghtiya movie thi ye, 3 ghante barbaad | कितनी घतिय movie थी ये  घंटे बरबाद | negative (+0/-1) | negative (+0/-1) |  |
| bhut hi pyaari ladki hai ye, fan ho gya | बहुत हि प्यारी लड़की है ये फन हो गया | positive (+1/-0) | positive (+3/-0) |  |
| faltuuu log hain ye sab, kch nhi hoga inka | फालतू लोग हैं ये सब काँच नहीं होगा इंक | neutral (+0/-0) | negative (+0/-1) | YES |
| mza aa gya live concert me jaake | मज़ा आ गया live चोनचेरत में जाके | neutral (+0/-0) | positive (+1/-0) | YES |
| kya hraami hai ye banda, dhoka de diya | क्या हरामि है ये बंद दओक डीई दिया | negative (+0/-1) | negative (+0/-1) |  |
| sachme kmaal ka gaana likha hai arijit ne | सच में कमाल का गाना लिखा है अरिजीत नए | positive (+1/-0) | positive (+3/-0) |  |
| bekaaaar si movie thi interval me nikal gaye | बेकार सई movie थी इनतेरवल में निकल गये | neutral (+0/-0) | negative (+0/-1) | YES |
| jabrdst jeet thi aaj india ki | जबरदस्त जीत थी आज इनदिअ की | neutral (+0/-0) | positive (+1/-0) | YES |
| khrab performance thi dhoni ki aaj | खराब पेरफोरमनचे थी दओनि की आज | neutral (+0/-0) | negative (+0/-1) | YES |
| bhut bura lga sunke ye news | बहुत बुरा लगा सुनके ये नेवस | negative (+0/-1) | negative (+1/-2) |  |

---

## Summary

- General examples: 6/20 predictions changed by normalization
- Tweet examples: 6/15 predictions changed by normalization
- Total: 12/35 cases where dhvani made a difference

## Why it helps

Common patterns where normalization changes the result:

1. Abbreviated words: "kmaal" not in lexicon, but normalizes to कमाल (positive)
2. Misspelled words: "khraab" not in lexicon, but normalizes to खराब (negative)
3. Elongated words: "faltuuu" collapses to "faltu" then normalizes to फालतू (negative)
4. Vowel-dropped: "bkwas" not in lexicon, but normalizes to बकवास (negative)
5. Slang spelling: "bevkoof" normalizes to बेवकूफ (negative)
