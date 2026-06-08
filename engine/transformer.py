#!/usr/bin/env python3
"""
transformer.py — Module 4
Applies transformations (leet, capitalize, reverse, etc.)
to individual words or word combinations.
"""

# ─────────────────────────────────────────────
#  Leet Speak Map
# ─────────────────────────────────────────────

LEET_MAP = {
    'a': '@', 'A': '@',
    'e': '3', 'E': '3',
    'i': '1', 'I': '1',
    'o': '0', 'O': '0',
    's': '$', 'S': '$',
    't': '7', 'T': '7',
    'g': '9', 'G': '9',
    'b': '8', 'B': '8',
}


# ─────────────────────────────────────────────
#  Individual Transformations
# ─────────────────────────────────────────────

def tf_upper(word: str) -> str:
    return word.upper()

def tf_lower(word: str) -> str:
    return word.lower()

def tf_capitalize(word: str) -> str:
    return word.capitalize()

def tf_title(word: str) -> str:
    return word.title()

def tf_reverse(word: str) -> str:
    return word[::-1]

def tf_leet(word: str) -> str:
    return "".join(LEET_MAP.get(c, c) for c in word)

def tf_leet_partial(word: str) -> str:
    """Only replaces vowels - more realistic leet."""
    vowel_map = {'a':'@','A':'@','e':'3','E':'3','i':'1','I':'1','o':'0','O':'0'}
    return "".join(vowel_map.get(c, c) for c in word)


TRANSFORM_MAP = {
    "upper"     : tf_upper,
    "lower"     : tf_lower,
    "capitalize": tf_capitalize,
    "title"     : tf_title,
    "reverse"   : tf_reverse,
    "leet"      : tf_leet,
}

# Shortcut aliases for transformation flags
SHORTCUT_MAP = {
    "-le": "leet",
    "-cp": "capitalize",
    "-up": "upper",
    "-l" : "lower",
    "-rv": "reverse",
    "-t" : "title",
}

# Default flags applied to every input unless overridden
DEFAULT_FLAGS = ["leet", "capitalize", "upper", "lower", "reverse"]

def resolve_flags(flags: list) -> list:
    """
    Resolves a list of flags/shortcuts to full flag names.
    Example: ["-le", "-cp", "reverse"] → ["leet", "capitalize", "reverse"]
    """
    resolved = []
    for f in flags:
        f = f.strip()
        if f in SHORTCUT_MAP:
            resolved.append(SHORTCUT_MAP[f])
        elif f in TRANSFORM_MAP:
            resolved.append(f)
    return resolved

# ─────────────────────────────────────────────
#  Apply Transformations to a Word
# ─────────────────────────────────────────────

def apply_transforms(word: str, flags: list) -> list:
    """
    Applies a list of transformation flags to a word.
    Returns a list of all variants including the original.

    Example:
        apply_transforms("BMW", ["leet","reverse"])
        → ["BMW", "8|\/|W", "WMB"]
    """
    results = [word]
    for flag in flags:
        fn = TRANSFORM_MAP.get(flag)
        if fn:
            variant = fn(word)
            if variant not in results:
                results.append(variant)
    return results


# ─────────────────────────────────────────────
#  Apply Transformations to a List of Words
# ─────────────────────────────────────────────

def transform_wordlist(words: list, flags: list) -> list:
    """
    Applies transformations to every word in the list.
    Returns expanded list with all variants.
    """
    result = []
    seen   = set()
    for word in words:
        for variant in apply_transforms(word, flags):
            if variant not in seen:
                seen.add(variant)
                result.append(variant)
    return result


# ─────────────────────────────────────────────
#  Separator Variants
# ─────────────────────────────────────────────

SEPARATORS = ["", "_", ".", "-", "@"]

def apply_separators(left: str, right: str, custom_sep: str = None) -> list:
    """
    Joins two strings with various separators.
    If custom_sep is given, only that separator is used.
    """
    if custom_sep is not None:
        return [left + custom_sep + right]
    return [left + sep + right for sep in SEPARATORS]


# ─────────────────────────────────────────────
#  Common Suffix / Prefix Additions
# ─────────────────────────────────────────────

COMMON_SUFFIXES = ["", "1", "12", "123", "!", "#", "@", "007", "786", "1234"]
COMMON_PREFIXES = ["", "1", "the", "my"]

def apply_suffixes(word: str) -> list:
    return [word + s for s in COMMON_SUFFIXES]

def apply_prefixes(word: str) -> list:
    return [p + word for p in COMMON_PREFIXES if p]
