#!/usr/bin/env python3
"""
tag_parser.py — Module 3
Resolves the ID/link/array relationships from parsed config tags
and produces a flat list of (value_a, value_b) pairs ready for
the combination engine.
"""

# ─────────────────────────────────────────────
#  Date Splitter
# ─────────────────────────────────────────────

def expand_date(value: str) -> list:
    """
    Splits a date string into useful sub-parts.
    '25051998' → ['25051998','2505','1998','05','25','98']
    """
    v = value.strip()
    parts = [v]
    if len(v) == 8:
        dd, mm, yyyy = v[0:2], v[2:4], v[4:8]
        yy = yyyy[2:]
        parts += [dd+mm, yyyy, mm, dd, yy]
    elif len(v) == 6:
        dd, mm, yy = v[0:2], v[2:4], v[4:6]
        parts += [dd+mm, mm, dd, yy]
    return list(dict.fromkeys(parts))   # dedupe, preserve order


# ─────────────────────────────────────────────
#  ID Registry Builder
# ─────────────────────────────────────────────

def build_id_registry(config: dict) -> dict:
    """
    Walks all tags in identity + interests and builds a lookup:
      id_name → list of string values

    Single:  car1(BMW)          → { 'car1': ['BMW'] }
    Array:   arr_cars[]={}      → { 'arr_cars': ['BMW','Nano','Suzuki'] }
    Date:    dob1(25051998)     → { 'dob1': ['25051998','2505','1998',...] }
    Linked:  jersey1(45,team1)  → resolved later in resolve_pairs()
    """
    registry = {}
    all_tags = config.get("identity", []) + config.get("interests", [])

    for tag in all_tags:
        tid   = tag["id"]
        dtype = tag["dtype"]
        kind  = tag["kind"]

        if kind == "array":
            registry[tid] = tag["values"]

        elif kind in ("single", "linked"):
            raw = tag["value"]
            if dtype == "@date":
                registry[tid] = expand_date(raw)
            else:
                registry[tid] = [raw]

    return registry


# ─────────────────────────────────────────────
#  Pair Resolver
# ─────────────────────────────────────────────

def resolve_pairs(config: dict, registry: dict) -> list:
    """
    Resolves every tag into (left_value, right_value) pairs.

    Rules:
      single tag        → just its own values, no pairing yet
      linked tag        → pairs its value(s) with each value of linked id
      match(arr1, arr2) → every combo of arr1 × arr2  (future extension)

    Returns a list of resolved tag dicts:
    [
      { "id": "person1", "values": ["John"],          "linked_values": None },
      { "id": "jersey1", "values": ["45"],             "linked_values": ["CSK"] },
      { "id": "car_no1", "values": ["5074"],           "linked_values": ["BMW","Nano","Suzuki"] },
      ...
    ]
    """
    resolved = []
    all_tags = config.get("identity", []) + config.get("interests", [])

    for tag in all_tags:
        tid  = tag["id"]
        kind = tag["kind"]

        if kind == "array":
            # Arrays are reference targets; they also contribute as standalone values
            resolved.append({
                "id"            : tid,
                "values"        : registry[tid],
                "linked_values" : None,
                "dtype"         : tag["dtype"],
                "kind"          : "array",
            })

        elif kind == "single":
            resolved.append({
                "id"            : tid,
                "values"        : registry[tid],
                "linked_values" : None,
                "dtype"         : tag["dtype"],
                "kind"          : "single",
            })

        elif kind == "linked":
            link_id     = tag["link"]
            own_values  = registry.get(tid, [tag["value"]])
            link_values = registry.get(link_id, [link_id])

            resolved.append({
                "id"            : tid,
                "values"        : own_values,
                "linked_values" : link_values,
                "dtype"         : tag["dtype"],
                "kind"          : "linked",
            })

    return resolved


# ─────────────────────────────────────────────
#  Flat Word List Extractor
# ─────────────────────────────────────────────

def extract_base_words(resolved: list) -> list:
    """
    From the resolved tag list, extract every individual word
    that will be used as raw material by the combinator.
    Returns a flat deduplicated list of strings.
    """
    words = []
    for item in resolved:
        words.extend(item["values"])
        if item["linked_values"]:
            words.extend(item["linked_values"])
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for w in words:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique


# ─────────────────────────────────────────────
#  Public Entry Point
# ─────────────────────────────────────────────

def process_tags(config: dict) -> dict:
    """
    Main entry point for Module 3.
    Takes the parsed config dict (from Module 2) and returns:
    {
        "registry" : { id → [values] },
        "resolved" : [ resolved tag dicts ],
        "pairs"    : [ (left, right) tuples for linked tags ],
        "words"    : [ flat list of all individual words ]
    }
    """
    registry = build_id_registry(config)
    resolved = resolve_pairs(config, registry)

    # Build explicit pairs from linked tags
    pairs = []
    for item in resolved:
        if item["kind"] == "linked" and item["linked_values"]:
            for lv in item["linked_values"]:
                for ov in item["values"]:
                    pairs.append((lv, ov))   # (car_name, car_number)

    words = extract_base_words(resolved)

    return {
        "registry": registry,
        "resolved": resolved,
        "pairs"   : pairs,
        "words"   : words,
    }

# ─────────────────────────────────────────────
#  View Commands
# ─────────────────────────────────────────────

from colorama import Fore, init
init(autoreset=True)

def view_tags(config: dict):
    """
    view tags — shows all tag IDs, their type, kind and linked ID.
    """
    all_tags = config.get("identity", []) + config.get("interests", [])
    if not all_tags:
        print(Fore.RED + "  No tags found.")
        return

    print(Fore.CYAN + "\n  ── View Tags ───────────────────────────────")
    print(Fore.YELLOW + f"  {'ID':<20} {'Type':<10} {'Kind':<10} {'Linked To':<15}")
    print(Fore.WHITE  + "  " + "─" * 58)

    for tag in all_tags:
        tid    = tag["id"]
        dtype  = tag["dtype"]
        kind   = tag["kind"]
        link   = tag.get("link", "—")
        source = tag.get("source", "")
        link_display = f"→ {link}" if link else "—"
        file_note    = f" [file: {source}]" if source else ""
        print(Fore.GREEN + f"  {tid:<20}" +
              Fore.WHITE  + f" {dtype:<10} {kind:<10} {link_display}{file_note}")

    print(Fore.CYAN + "  ────────────────────────────────────────────\n")


def view_data(config: dict):
    """
    view data — shows all values grouped by tag in tabular format.
    Large file-loaded arrays shown as tables.
    """
    all_tags = config.get("identity", []) + config.get("interests", [])
    if not all_tags:
        print(Fore.RED + "  No data found.")
        return

    print(Fore.CYAN + "\n  ── View Data ───────────────────────────────")

    for tag in all_tags:
        tid   = tag["id"]
        dtype = tag["dtype"]
        kind  = tag["kind"]

        print(Fore.YELLOW + f"\n  [{tid}]  {dtype}  ({kind})")

        if kind == "array":
            values = tag["values"]
            source = tag.get("source", "")
            if source:
                print(Fore.WHITE + f"  Loaded from file: {source}")
            # Tabular display for arrays
            col_width = max(len(v) for v in values) + 4
            cols      = max(1, 60 // col_width)
            print(Fore.WHITE + "  " + "─" * (col_width * cols))
            for i, val in enumerate(values):
                end = "\n  " if (i + 1) % cols == 0 else ""
                print(Fore.WHITE + f"  {val:<{col_width}}", end=end)
            print()
            print(Fore.WHITE + f"  Total: {len(values)} values")

        else:
            value = tag.get("value", "—")
            link  = tag.get("link", "")
            print(Fore.WHITE + f"  Value : {value}")
            if link:
                print(Fore.WHITE + f"  Linked: → {link}")

    print(Fore.CYAN + "\n  ────────────────────────────────────────────\n")


def view_all(config: dict):
    """view all — shows everything: tags + data + specs + transforms."""
    view_tags(config)
    view_data(config)

    # Specs
    specs = config.get("specs", {})
    if specs:
        print(Fore.CYAN + "\n  ── Specs ───────────────────────────────────")
        for k, v in specs.items():
            print(Fore.WHITE + f"  {k:<25} = {v}")
        print()

    # Transforms
    t = config.get("transformations", {})
    if t.get("global"):
        print(Fore.CYAN + "  ── Transformations ─────────────────────────")
        print(Fore.WHITE + f"  global = {', '.join(t['global'])}")
        print()

    # Priority
    p = config.get("priority", {})
    if p.get("order"):
        print(Fore.CYAN + "  ── Priority ────────────────────────────────")
        print(Fore.WHITE + f"  order = {' > '.join(p['order'])}")
        print(Fore.CYAN + "  ────────────────────────────────────────────\n")

# ─────────────────────────────────────────────
# End of tag_parser.py
# ────────────────────────────────────────────