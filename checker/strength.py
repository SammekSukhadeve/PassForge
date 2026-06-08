#!/usr/bin/env python3
"""
strength.py — Module 6
Rates password strength using entropy calculation,
pattern detection, and zxcvbn scoring.
"""

import re
import math
from colorama import Fore, init

init(autoreset=True)

# ─────────────────────────────────────────────
#  Entropy Calculator
# ─────────────────────────────────────────────

def calc_entropy(password: str) -> float:
    """
    Calculates Shannon entropy of a password.
    Higher = more random = stronger.
    """
    if not password:
        return 0.0
    pool = 0
    if re.search(r'[a-z]', password): pool += 26
    if re.search(r'[A-Z]', password): pool += 26
    if re.search(r'[0-9]', password): pool += 10
    if re.search(r'[^a-zA-Z0-9]', password): pool += 32
    return round(len(password) * math.log2(pool) if pool else 0, 2)


# ─────────────────────────────────────────────
#  Pattern Detector
# ─────────────────────────────────────────────

PATTERNS = [
    (r'^[a-zA-Z]+\d{2,4}$',         "Name + year pattern (e.g. john1998)"),
    (r'^[a-zA-Z]+\d{6,8}$',         "Name + date pattern (e.g. john25051998)"),
    (r'(\w)\1{2,}',                  "Repeated characters (e.g. aaa)"),
    (r'^(123|abc|qwerty|password)',  "Starts with common sequence"),
    (r'(123|abc|qwerty)',            "Contains common sequence"),
    (r'^[a-zA-Z]+$',                 "Letters only — no numbers or symbols"),
    (r'^\d+$',                       "Numbers only"),
    (r'^(.+)\1+$',                   "Repeated pattern (e.g. abcabc)"),
]

def detect_patterns(password: str) -> list:
    """Returns a list of detected weak patterns."""
    found = []
    for pattern, label in PATTERNS:
        if re.search(pattern, password, re.IGNORECASE):
            found.append(label)
    return found


# ─────────────────────────────────────────────
#  Strength Scorer
# ─────────────────────────────────────────────

def score_password(password: str) -> dict:
    """
    Scores a password and returns a full report dict.
    Uses zxcvbn if available, falls back to entropy.
    """
    report = {}

    # Try zxcvbn first
    try:
        import zxcvbn as zx
        result   = zx.zxcvbn(password)
        score    = result["score"]          # 0-4
        feedback = result["feedback"]

        labels   = ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"]
        colors   = [Fore.RED, Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.GREEN]

        report["score"]       = score
        report["label"]       = labels[score]
        report["color"]       = colors[score]
        report["crack_time"]  = result["crack_times_display"]["offline_slow_hashing_1e4_per_second"]
        report["suggestions"] = feedback.get("suggestions", [])
        report["warning"]     = feedback.get("warning", "")
        report["source"]      = "zxcvbn"

    except ImportError:
        # Fallback: entropy based scoring
        entropy = calc_entropy(password)
        if entropy < 28:
            score, label, color = 0, "Very Weak", Fore.RED
        elif entropy < 36:
            score, label, color = 1, "Weak",      Fore.RED
        elif entropy < 50:
            score, label, color = 2, "Fair",       Fore.YELLOW
        elif entropy < 60:
            score, label, color = 3, "Strong",     Fore.GREEN
        else:
            score, label, color = 4, "Very Strong",Fore.GREEN

        report["score"]       = score
        report["label"]       = label
        report["color"]       = color
        report["entropy"]     = entropy
        report["suggestions"] = []
        report["warning"]     = ""
        report["source"]      = "entropy"

    # Always add pattern detection
    report["patterns"]  = detect_patterns(password)
    report["length"]    = len(password)
    report["entropy"]   = calc_entropy(password)

    return report


# ─────────────────────────────────────────────
#  Pretty Printer
# ─────────────────────────────────────────────

def print_strength_report(password: str):
    """Prints a full strength report to terminal."""
    report = score_password(password)
    stars  = "★" * (report["score"] + 1) + "☆" * (4 - report["score"])

    print(Fore.CYAN + "\n  ── Password Strength Report ────────────────")
    print(Fore.WHITE + f"  Password   : {'*' * len(password)}")
    print(Fore.WHITE + f"  Length     : {report['length']} characters")
    print(Fore.WHITE + f"  Entropy    : {report['entropy']} bits")
    print(Fore.WHITE + f"  Rating     : {report['color']}{report['label']} {stars}")

    if "crack_time" in report:
        print(Fore.WHITE + f"  Crack time : {Fore.YELLOW}{report['crack_time']}")

    if report["warning"]:
        print(Fore.YELLOW + f"  Warning    : {report['warning']}")

    if report["patterns"]:
        print(Fore.YELLOW + "\n  Weak patterns detected:")
        for p in report["patterns"]:
            print(Fore.YELLOW + f"    ⚠  {p}")

    if report["suggestions"]:
        print(Fore.CYAN + "\n  Suggestions:")
        for s in report["suggestions"]:
            print(Fore.WHITE + f"    → {s}")

    print(Fore.CYAN + "  ────────────────────────────────────────────\n")
