#!/usr/bin/env python3
"""
combinator.py — Module 4
Takes resolved tag data (from Module 3) and generates
all meaningful password combinations.
"""

import itertools
from engine.transformer import (
    apply_transforms, apply_separators,
    apply_suffixes, apply_prefixes,
    transform_wordlist
)

# ─────────────────────────────────────────────
#  Linked Pair Combinations
# ─────────────────────────────────────────────

def combine_pairs(pairs: list, flags: list, sep: str = None) -> list:
    """
    Takes explicit (left, right) pairs from linked tags and
    generates combinations in both orders with separators
    and transformations applied.

    Example:
        pairs = [("BMW", "5074"), ("Nano", "5074")]
        → ["BMW5074", "5074BMW", "bmw5074", ...]
    """
    results = []
    seen    = set()

    for left, right in pairs:
        left_variants  = apply_transforms(left,  flags)
        right_variants = apply_transforms(right, flags)

        for lv in left_variants:
            for rv in right_variants:
                for combo in apply_separators(lv, rv, sep):
                    if combo not in seen:
                        seen.add(combo)
                        results.append(combo)
                # also reverse order
                for combo in apply_separators(rv, lv, sep):
                    if combo not in seen:
                        seen.add(combo)
                        results.append(combo)

    return results


# ─────────────────────────────────────────────
#  Single Word Expansions
# ─────────────────────────────────────────────

def expand_single_words(words: list, flags: list) -> list:
    """
    Takes standalone words and generates:
    - all transformation variants
    - common suffixes appended
    - common prefixes prepended
    """
    results = []
    seen    = set()

    expanded = transform_wordlist(words, flags)

    for word in expanded:
        # raw word
        if word not in seen:
            seen.add(word)
            results.append(word)
        # with suffixes
        for w in apply_suffixes(word):
            if w not in seen:
                seen.add(w)
                results.append(w)
        # with prefixes
        for w in apply_prefixes(word):
            if w not in seen:
                seen.add(w)
                results.append(w)

    return results


# ─────────────────────────────────────────────
#  Free Combination of All Words
# ─────────────────────────────────────────────

def combine_all_words(words: list, flags: list) -> list:
    """
    Generates combinations of 2 words from the full word pool.
    These are lower-priority entries — broad combos.
    """
    results = []
    seen    = set()

    transformed = transform_wordlist(words, flags)

    for a, b in itertools.permutations(transformed, 2):
        for combo in apply_separators(a, b):
            if combo not in seen:
                seen.add(combo)
                results.append(combo)

    return results


# ─────────────────────────────────────────────
#  Priority Sorter
# ─────────────────────────────────────────────

def sort_by_priority(
    paired_combos   : list,
    single_combos   : list,
    broad_combos    : list,
    priority_order  : list
) -> list:
    """
    Merges the three combo lists by the priority order
    defined in [priority] section.

    priority_order = ["identity", "interests"]
    → paired combos first, then singles, then broad
    """
    # For now: paired (most targeted) → singles → broad
    seen   = set()
    result = []

    for combo_list in [paired_combos, single_combos, broad_combos]:
        for word in combo_list:
            if word not in seen:
                seen.add(word)
                result.append(word)

    return result


# ─────────────────────────────────────────────
#  Main Entry Point
# ─────────────────────────────────────────────

def generate_wordlist(tag_data: dict, config: dict) -> list:
    """
    Main entry point for Module 4.
    Takes tag_data (from Module 3) and config (from Module 2).
    Returns a raw wordlist (before spec filtering).
    """
    flags         = config.get("transformations", {}).get("global", [])
    priority_order= config.get("priority", {}).get("order", [])
    pairs         = tag_data.get("pairs", [])
    words         = tag_data.get("words", [])

    print("  ⚙  Generating linked pair combinations...")
    paired_combos = combine_pairs(pairs, flags)

    print("  ⚙  Expanding single words...")
    single_combos = expand_single_words(words, flags)

    print("  ⚙  Generating broad combinations...")
    broad_combos  = combine_all_words(words, flags)

    print("  ⚙  Sorting by priority...")
    wordlist = sort_by_priority(paired_combos, single_combos, broad_combos, priority_order)

    return wordlist
