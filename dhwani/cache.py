"""Runtime learning cache for dhwani.

When a word isn't in the lexicon and hits Tier 2 (model), the result
is cached so the same word never needs the model again. The cache
persists to disk so it accumulates across sessions.

This means dhwani gets faster the more you use it.
"""

import json
import os
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

_CACHE: Optional[Dict[str, dict]] = None
_CACHE_DIRTY = False

# Default cache location: ~/.dhwani/cache.json
_DEFAULT_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".dhwani")
_DEFAULT_CACHE_PATH = os.path.join(_DEFAULT_CACHE_DIR, "cache.json")

# Allow override via environment variable
_CACHE_PATH = os.environ.get("DHWANI_CACHE_PATH", _DEFAULT_CACHE_PATH)


def _load_cache() -> Dict[str, dict]:
    """Load the cache from disk."""
    global _CACHE
    if _CACHE is None:
        if os.path.exists(_CACHE_PATH):
            try:
                with open(_CACHE_PATH, "r", encoding="utf-8") as f:
                    _CACHE = json.load(f)
                logger.debug(f"Loaded {len(_CACHE)} cached entries from {_CACHE_PATH}")
            except (json.JSONDecodeError, IOError):
                _CACHE = {}
        else:
            _CACHE = {}
    return _CACHE


def _save_cache():
    """Persist cache to disk."""
    global _CACHE_DIRTY
    if not _CACHE_DIRTY or _CACHE is None:
        return

    os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
    try:
        with open(_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(_CACHE, f, ensure_ascii=False)
        _CACHE_DIRTY = False
        logger.debug(f"Saved {len(_CACHE)} entries to {_CACHE_PATH}")
    except IOError as e:
        logger.warning(f"Failed to save cache: {e}")


def cache_lookup(word: str) -> Optional[dict]:
    """Look up a word in the runtime cache.

    Returns:
        {"devanagari": "...", "ipa": "..."} if cached, None otherwise
    """
    cache = _load_cache()
    return cache.get(word.lower().strip())


def cache_store(word: str, devanagari: str, ipa: str):
    """Store a word's results in the cache.

    Called after Tier 2 (model) processes a word.
    """
    global _CACHE_DIRTY
    cache = _load_cache()
    key = word.lower().strip()
    cache[key] = {"devanagari": devanagari, "ipa": ipa}
    _CACHE_DIRTY = True

    # Auto-save every 50 new entries
    if len(cache) % 50 == 0:
        _save_cache()


def cache_get_ipa(word: str) -> Optional[str]:
    """Get cached IPA for a word."""
    result = cache_lookup(word)
    return result["ipa"] if result else None


def cache_get_devanagari(word: str) -> Optional[str]:
    """Get cached Devanagari for a word."""
    result = cache_lookup(word)
    return result["devanagari"] if result else None


def flush_cache():
    """Force save the cache to disk."""
    _save_cache()


def get_cache_stats() -> dict:
    """Get cache statistics."""
    cache = _load_cache()
    return {
        "entries": len(cache),
        "path": _CACHE_PATH,
        "exists": os.path.exists(_CACHE_PATH),
    }


def clear_cache():
    """Clear the runtime cache (both memory and disk)."""
    global _CACHE, _CACHE_DIRTY
    _CACHE = {}
    _CACHE_DIRTY = True
    _save_cache()


# Register save on exit
import atexit
atexit.register(_save_cache)
