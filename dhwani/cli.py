"""Command-line interface for dhwani."""

import sys


def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    command = sys.argv[1].lower()

    if command in ("help", "--help", "-h"):
        print_help()
    elif command in ("devanagari", "dev", "d"):
        cmd_devanagari(sys.argv[2:])
    elif command in ("ipa", "i"):
        cmd_ipa(sys.argv[2:])
    elif command in ("same", "s"):
        cmd_same(sys.argv[2:])
    elif command in ("langs", "l", "identify"):
        cmd_langs(sys.argv[2:])
    elif command in ("normalize", "norm", "n"):
        cmd_normalize(sys.argv[2:])
    elif command in ("stats",):
        cmd_stats()
    else:
        # If no command, treat all args as text for devanagari conversion
        cmd_devanagari(sys.argv[1:])


def print_help():
    print("""dhwani - Phonetic normalization for Hinglish text

Usage:
  dhwani devanagari <text>    Convert Hinglish to Devanagari
  dhwani ipa <text>           Convert to IPA transcription
  dhwani same <word1> <word2> Check if two words are phonetically the same
  dhwani langs <text>         Identify language of each word
  dhwani normalize <text>     Normalize to canonical form
  dhwani stats                Show lexicon statistics

Shortcuts:
  dhwani d <text>             Same as 'devanagari'
  dhwani i <text>             Same as 'ipa'
  dhwani s <w1> <w2>          Same as 'same'

Examples:
  dhwani devanagari "bohot accha movie thi yaar"
  dhwani same bahut bohot
  dhwani langs "ye movie really acchi thi"
""")


def cmd_devanagari(args):
    if not args:
        print("Error: provide text to convert")
        sys.exit(1)
    import dhwani
    text = " ".join(args)
    print(dhwani.to_devanagari(text))


def cmd_ipa(args):
    if not args:
        print("Error: provide text to convert")
        sys.exit(1)
    import dhwani
    text = " ".join(args)
    print(dhwani.to_ipa(text))


def cmd_same(args):
    if len(args) < 2:
        print("Error: provide two words to compare")
        sys.exit(1)
    import dhwani
    from dhwani.similarity import phonetic_similarity
    word1, word2 = args[0], args[1]
    same = dhwani.are_same(word1, word2)
    score = phonetic_similarity(word1, word2)
    print(f"{'True' if same else 'False'} (phonetic similarity: {score:.2f})")


def cmd_langs(args):
    if not args:
        print("Error: provide text to identify")
        sys.exit(1)
    import dhwani
    text = " ".join(args)
    result = dhwani.identify_languages(text)
    parts = [f"{word}[{lang}]" for word, lang in result]
    print(" ".join(parts))


def cmd_normalize(args):
    if not args:
        print("Error: provide text to normalize")
        sys.exit(1)
    import dhwani
    text = " ".join(args)
    print(dhwani.normalize(text))


def cmd_stats():
    from dhwani.lexicon.lookup import get_lexicon_stats
    from dhwani.cache import get_cache_stats
    lex = get_lexicon_stats()
    cache = get_cache_stats()
    print(f"Lexicon:")
    print(f"  IPA entries:        {lex['ipa_entries']:,}")
    print(f"  Correction entries: {lex['correction_entries']:,}")
    print(f"  Generated loaded:   {not lex['using_builtin_only']}")
    print(f"Cache:")
    print(f"  Entries:            {cache['entries']:,}")
    print(f"  Path:               {cache['path']}")


if __name__ == "__main__":
    main()
