#!/usr/bin/env python3
"""
filter.py — Module 5
Filters and cleans the generated wordlist based on
the [specs] rules defined in the .pwconf config.
"""

import re

# ─────────────────────────────────────────────
#  Individual Spec Checks
# ─────────────────────────────────────────────

def has_capital(word: str) -> bool:
    return any(c.isupper() for c in word)

def has_symbol(word: str) -> bool:
    return bool(re.search(r'[^a-zA-Z0-9]', word))

def has_number(word: str) -> bool:
    return any(c.isdigit() for c in word)

def meets_length(word: str, min_len: int, max_len: int) -> bool:
    return min_len <= len(word) <= max_len


# ─────────────────────────────────────────────
#  Spec Mutators
# (try to salvage a word that almost meets specs)
# ─────────────────────────────────────────────

def force_capital(word: str) -> str:
    """Capitalizes first letter if no capital exists."""
    return word[0].upper() + word[1:] if word else word

def force_symbol(word: str) -> str:
    """Appends '!' if no symbol exists."""
    return word + "!"

def force_number(word: str) -> str:
    """Appends '1' if no digit exists."""
    return word + "1"


# ─────────────────────────────────────────────
#  Main Filter Function
# ─────────────────────────────────────────────

def apply_spec_filter(wordlist: list, specs: dict) -> list:
    """
    Filters the wordlist based on [specs] rules.

    Strategy:
    1. If word already meets all specs → keep as-is
    2. If word fails a spec but can be mutated to meet it → mutate and keep
    3. If word fails length rules → discard (no mutation)

    Returns filtered + mutated list.
    """
    must_capital = specs.get("must_have_capital", False)
    must_symbol  = specs.get("must_have_symbol",  False)
    must_number  = specs.get("must_have_number",  False)
    min_len      = specs.get("min_length", 6)
    max_len      = specs.get("max_length", 20)

    result = []
    seen   = set()

    for word in wordlist:
        w = word

        # Hard length filter — discard if too long already
        if len(w) > max_len:
            continue

        # Apply mutations to meet specs
        if must_capital and not has_capital(w):
            w = force_capital(w)
        if must_symbol and not has_symbol(w):
            w = force_symbol(w)
        if must_number and not has_number(w):
            w = force_number(w)

        # Check final length after mutations
        if not meets_length(w, min_len, max_len):
            continue

        if w not in seen:
            seen.add(w)
            result.append(w)

    return result


# ─────────────────────────────────────────────
#  Stats Reporter
# ─────────────────────────────────────────────

def wordlist_stats(wordlist: list) -> dict:
    """Returns a stats dict about the wordlist."""
    if not wordlist:
        return {"total": 0}

    lengths = [len(w) for w in wordlist]
    return {
        "total"       : len(wordlist),
        "min_length"  : min(lengths),
        "max_length"  : max(lengths),
        "avg_length"  : round(sum(lengths) / len(lengths), 1),
        "has_symbols" : sum(1 for w in wordlist if has_symbol(w)),
        "has_numbers" : sum(1 for w in wordlist if has_number(w)),
        "has_capitals": sum(1 for w in wordlist if has_capital(w)),
    }
