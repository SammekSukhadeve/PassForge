#!/usr/bin/env python3
"""
config_parser.py — Module 2
Reads and parses .pwconf configuration files into a structured dictionary
that the rest of the PassForge engine can consume.

.pwconf structure:
    [identity]
    [interests]
    [transformations]
    [specs]
    [priority]
"""

import os
import re
from colorama import Fore, init



init(autoreset=True)

def load_value_from_file(filepath: str) -> list:
    """
    Loads values from a .txt or list file.
    Each line in the file is treated as one value.
    Returns a list of strings.
    """
    if not os.path.exists(filepath):
        raise ConfigParseError(f"File not found: '{filepath}'")
    values = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith(";"):
                values.append(line)
    return values

# ─────────────────────────────────────────────
#  Exceptions
# ─────────────────────────────────────────────

class ConfigParseError(Exception):
    """Raised when the .pwconf file has a syntax error."""
    pass


# ─────────────────────────────────────────────
#  Valid Sections & Keys
# ─────────────────────────────────────────────

VALID_SECTIONS = {"identity", "interests", "transformations", "specs", "priority"}

VALID_SPEC_KEYS = {
    "must_have_capital",
    "must_have_symbol",
    "must_have_number",
    "min_length",
    "max_length",
}

VALID_TRANSFORM_FLAGS = {
    "leet", "upper", "lower", "capitalize",
    "reverse", "title"
}

VALID_TYPES = {"@string", "@number", "@date", "@name"}


# ─────────────────────────────────────────────
#  Raw Line Classifier
# ─────────────────────────────────────────────

def classify_line(line: str) -> str:
    """
    Returns the type of a line:
      'empty'       → blank or whitespace only
      'comment'     → starts with ;
      'section'     → [section_name]
      'tag'         → @type  id(value) or @type arr[]={}
      'spec'        → key = value
      'unknown'     → unrecognised
    """
    stripped = line.strip()
    if not stripped:
        return "empty"
    if stripped.startswith(";"):
        return "comment"
    if re.match(r"^\[.+\]$", stripped):
        return "section"
    if stripped.startswith("@"):
        return "tag"
    if "=" in stripped:
        return "spec"
    return "unknown"


# ─────────────────────────────────────────────
#  Section Parser
# ─────────────────────────────────────────────

def parse_section_name(line: str) -> str:
    """Extracts the section name from a [section] line."""
    match = re.match(r"^\[(.+)\]$", line.strip())
    if not match:
        raise ConfigParseError(f"Invalid section header: '{line.strip()}'")
    name = match.group(1).strip().lower()
    if name not in VALID_SECTIONS:
        raise ConfigParseError(
            f"Unknown section '[{name}]'. Valid sections: {sorted(VALID_SECTIONS)}"
        )
    return name


# ─────────────────────────────────────────────
#  Tag Line Parser
# ─────────────────────────────────────────────

# Matches:  @type   id_name(value)
#           @type   id_name(value, linked_id)
#           @type   arr_name[] = {val1, val2, val3}
#           @type   id_name(value, arr_name)

TAG_SINGLE_RE  = re.compile(
    r"^(?P<dtype>@\w+)\s+(?P<id>\w+)\((?P<value>[^,)]+)(?:,\s*(?P<link>\w+))?\)$"
)
TAG_ARRAY_RE   = re.compile(
    r"^(?P<dtype>@\w+)\s+(?P<id>\w+)\[\]\s*=\s*\{(?P<values>[^}]+)\}$"
)


def parse_tag_line(line: str, lineno: int) -> dict:
    stripped = line.strip()

    # Try array pattern first
    m = TAG_ARRAY_RE.match(stripped)
    if m:
        dtype  = m.group("dtype").lower()
        tag_id = m.group("id").strip()
        raw    = m.group("values")
        values = [v.strip() for v in raw.split(",") if v.strip()]

        if dtype not in VALID_TYPES:
            raise ConfigParseError(
                f"Line {lineno}: Unknown type '{dtype}'. Valid: {sorted(VALID_TYPES)}"
            )
        return {
            "kind"  : "array",
            "dtype" : dtype,
            "id"    : tag_id,
            "values": values,
            "source": "",
        }

    # Try single / linked pattern
    m = TAG_SINGLE_RE.match(stripped)
    if m:
        dtype  = m.group("dtype").lower()
        tag_id = m.group("id").strip()
        value  = m.group("value").strip()
        link   = m.group("link").strip() if m.group("link") else None

        if dtype not in VALID_TYPES:
            raise ConfigParseError(
                f"Line {lineno}: Unknown type '{dtype}'. Valid: {sorted(VALID_TYPES)}"
            )

        # File input support — value can be file:path.txt
        if value.startswith("file:"):
            filepath   = value[5:].strip()
            file_values = load_value_from_file(filepath)
            return {
                "kind"  : "array",
                "dtype" : dtype,
                "id"    : tag_id,
                "values": file_values,
                "source": filepath,
            }

        kind = "linked" if link else "single"
        return {
            "kind"  : kind,
            "dtype" : dtype,
            "id"    : tag_id,
            "value" : value,
            "link"  : link,
            "source": "",
        }

    raise ConfigParseError(
        f"Line {lineno}: Could not parse tag line → '{stripped}'\n"
        f"  Expected formats:\n"
        f"    @type  id(value)\n"
        f"    @type  id(value, linked_id)\n"
        f"    @type  arr_name[] = {{val1, val2}}"
    )



# ─────────────────────────────────────────────
#  Spec & Transformation Parsers
# ─────────────────────────────────────────────

def parse_spec_line(line: str, lineno: int) -> tuple:
    """
    Parses a key = value line from [specs] or [priority] or [transformations].
    Returns (key, value) both as strings.
    """
    if "=" not in line:
        raise ConfigParseError(f"Line {lineno}: Expected 'key = value', got '{line.strip()}'")

    key, _, value = line.partition("=")
    key   = key.strip().lower()
    value = value.strip()

    return key, value


def parse_bool(value: str, key: str, lineno: int) -> bool:
    """Converts 'true'/'false' string to Python bool."""
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    raise ConfigParseError(
        f"Line {lineno}: '{key}' must be 'true' or 'false', got '{value}'"
    )


def parse_int(value: str, key: str, lineno: int) -> int:
    """Converts a string to int with a clean error message."""
    try:
        return int(value)
    except ValueError:
        raise ConfigParseError(
            f"Line {lineno}: '{key}' must be a number, got '{value}'"
        )


def parse_specs_section(lines_with_nos: list) -> dict:
    """
    Parses all lines in the [specs] section.
    Returns a dict like:
    {
        "must_have_capital": True,
        "must_have_symbol" : False,
        "must_have_number" : False,
        "min_length"       : 8,
        "max_length"       : 16,
    }
    """
    specs = {
        "must_have_capital": False,
        "must_have_symbol" : False,
        "must_have_number" : False,
        "min_length"       : 6,
        "max_length"       : 20,
    }

    for lineno, line in lines_with_nos:
        key, value = parse_spec_line(line, lineno)
        if key not in VALID_SPEC_KEYS:
            raise ConfigParseError(
                f"Line {lineno}: Unknown spec key '{key}'. "
                f"Valid keys: {sorted(VALID_SPEC_KEYS)}"
            )
        if key in ("must_have_capital", "must_have_symbol", "must_have_number"):
            specs[key] = parse_bool(value, key, lineno)
        elif key in ("min_length", "max_length"):
            specs[key] = parse_int(value, key, lineno)

    return specs


def parse_transformations_section(lines_with_nos: list) -> dict:
    """
    Parses the [transformations] section.
    If section is empty or global not set, DEFAULT_FLAGS are used.
    """
    from engine.transformer import DEFAULT_FLAGS, resolve_flags

    transforms = {"global": list(DEFAULT_FLAGS)}  # defaults always active

    for lineno, line in lines_with_nos:
        key, value = parse_spec_line(line, lineno)
        if key == "global":
            flags = [f.strip() for f in value.split(",") if f.strip()]
            resolved = resolve_flags(flags)
            if resolved:
                transforms["global"] = resolved   # override defaults
        else:
            raise ConfigParseError(
                f"Line {lineno}: Unknown key '{key}' in [transformations]."
            )

    return transforms


def parse_priority_section(lines_with_nos: list) -> dict:
    """
    Parses the [priority] section.
    Returns:
    {
        "order": ["identity", "interests"]
    }
    """
    priority = {"order": []}

    for lineno, line in lines_with_nos:
        key, value = parse_spec_line(line, lineno)
        if key == "order":
            # e.g. "identity > interests"
            sections = [s.strip().lower() for s in re.split(r">|,", value) if s.strip()]
            priority["order"] = sections
        else:
            raise ConfigParseError(
                f"Line {lineno}: Unknown key '{key}' in [priority]."
            )

    return priority


# ─────────────────────────────────────────────
#  Tag Sections Parser (identity + interests)
# ─────────────────────────────────────────────

def parse_tag_section(lines_with_nos: list) -> list:
    """
    Parses all tag lines in an [identity] or [interests] section.
    Returns a list of tag dicts.
    """
    tags = []
    for lineno, line in lines_with_nos:
        ltype = classify_line(line)
        if ltype in ("empty", "comment"):
            continue
        if ltype == "tag":
            tags.append(parse_tag_line(line, lineno))
        else:
            raise ConfigParseError(
                f"Line {lineno}: Unexpected line in tag section → '{line.strip()}'"
            )
    return tags


# ─────────────────────────────────────────────
#  ID Reference Validator
# ─────────────────────────────────────────────

def validate_links(parsed: dict):
    """
    Checks that every 'link' reference in a tag actually points
    to a declared ID somewhere in identity or interests.
    Raises ConfigParseError if a dangling reference is found.
    """
    declared_ids = set()
    all_tags = parsed.get("identity", []) + parsed.get("interests", [])

    for tag in all_tags:
        declared_ids.add(tag["id"])

    for tag in all_tags:
        if tag.get("kind") == "linked":
            ref = tag.get("link")
            if ref and ref not in declared_ids:
                raise ConfigParseError(
                    f"Tag '{tag['id']}' links to '{ref}' but '{ref}' is not declared."
                )


# ─────────────────────────────────────────────
#  Main Parser
# ─────────────────────────────────────────────

def parse_config(filepath: str) -> dict:
    """
    Reads a .pwconf file and returns a fully parsed config dict:

    {
        "identity"       : [ list of tag dicts ],
        "interests"      : [ list of tag dicts ],
        "transformations": { "global": [...] },
        "specs"          : { "must_have_capital": True, ... },
        "priority"       : { "order": ["identity", "interests"] },
        "_meta"          : { "filepath": "...", "line_count": N }
    }
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Config file not found: '{filepath}'")

    with open(filepath, "r") as f:
        raw_lines = f.readlines()

    # Split into sections, preserving line numbers for error messages
    sections: dict[str, list] = {s: [] for s in VALID_SECTIONS}
    current_section = None

    for lineno, line in enumerate(raw_lines, start=1):
        ltype = classify_line(line)

        if ltype in ("empty", "comment"):
            continue

        if ltype == "section":
            current_section = parse_section_name(line)
            continue

        if current_section is None:
            raise ConfigParseError(
                f"Line {lineno}: Content found before any section header."
            )

        sections[current_section].append((lineno, line))

    # Parse each section
    parsed = {}

    parsed["identity"]        = parse_tag_section(sections["identity"])
    parsed["interests"]       = parse_tag_section(sections["interests"])
    parsed["transformations"] = parse_transformations_section(sections["transformations"])
    parsed["specs"]           = parse_specs_section(sections["specs"])
    parsed["priority"]        = parse_priority_section(sections["priority"])

    # Validate ID cross-references
    validate_links(parsed)

    # Metadata
    parsed["_meta"] = {
        "filepath"  : filepath,
        "line_count": len(raw_lines),
    }

    return parsed


# ─────────────────────────────────────────────
#  Pretty Printer (for 'show config' command)
# ─────────────────────────────────────────────

def pretty_print_config(parsed: dict):
    """Prints the parsed config in a readable format to the terminal."""

    meta = parsed.get("_meta", {})
    print(Fore.CYAN + f"\n  ── Parsed Config: {meta.get('filepath', '?')} ──\n")

    # Identity & Interests
    for section in ("identity", "interests"):
        tags = parsed.get(section, [])
        if not tags:
            continue
        print(Fore.YELLOW + f"  [{section.upper()}]")
        for tag in tags:
            kind = tag["kind"]
            tid  = tag["id"]
            dtype = tag["dtype"]
            if kind == "array":
                vals = ", ".join(tag["values"])
                print(Fore.WHITE + f"    {dtype:<10} {tid}[]  =  {{{vals}}}")
            elif kind == "linked":
                print(Fore.WHITE + f"    {dtype:<10} {tid}({tag['value']}, " +
                      Fore.GREEN + f"→{tag['link']}" + Fore.WHITE + ")")
            else:
                print(Fore.WHITE + f"    {dtype:<10} {tid}({tag['value']})")
        print()

    # Transformations
    t = parsed.get("transformations", {})
    if t.get("global"):
        print(Fore.YELLOW + "  [TRANSFORMATIONS]")
        print(Fore.WHITE + f"    global = {', '.join(t['global'])}")
        print()

    # Specs
    s = parsed.get("specs", {})
    if s:
        print(Fore.YELLOW + "  [SPECS]")
        for k, v in s.items():
            print(Fore.WHITE + f"    {k:<22} = {v}")
        print()

    # Priority
    p = parsed.get("priority", {})
    if p.get("order"):
        print(Fore.YELLOW + "  [PRIORITY]")
        print(Fore.WHITE + f"    order = {' > '.join(p['order'])}")
        print()

    print(Fore.CYAN + "  ─────────────────────────────────────────────\n")
