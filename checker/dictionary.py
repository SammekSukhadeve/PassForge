#!/usr/bin/env python3
"""
dictionary.py — Module 6
Checks a password against locally bundled common password
dictionaries and the HaveIBeenPwned API (breach database).
"""

import os
import hashlib
import requests
from colorama import Fore, init

init(autoreset=True)

# ─────────────────────────────────────────────
#  Dictionary Paths
# ─────────────────────────────────────────────

BASE_DIR        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICT_DIR        = os.path.join(BASE_DIR, "dictionaries")
COMMON_DICT     = os.path.join(DICT_DIR, "common_passwords.txt")
ROCKYOU_DICT    = os.path.join(DICT_DIR, "rockyou.txt")


# ─────────────────────────────────────────────
#  Local Dictionary Check
# ─────────────────────────────────────────────

def check_local_dict(password: str, dict_path: str) -> bool:
    """
    Returns True if password is found in the dictionary file.
    Streams line by line to handle large files like rockyou.
    """
    if not os.path.exists(dict_path):
        return False

    pwd_lower = password.lower()
    try:
        with open(dict_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.strip().lower() == pwd_lower:
                    return True
    except Exception:
        return False
    return False


def check_all_local(password: str) -> dict:
    results = {}

    # Auto-scan: picks up ANY .txt file in the dictionaries/ folder
    if not os.path.exists(DICT_DIR):
        return results

    for filename in os.listdir(DICT_DIR):
        if filename.endswith(".txt"):
            dict_name = filename.replace(".txt", "")
            dict_path = os.path.join(DICT_DIR, filename)
            results[dict_name] = check_local_dict(password, dict_path)

    return results


# ─────────────────────────────────────────────
#  HaveIBeenPwned API Check (k-anonymity model)
# ─────────────────────────────────────────────

def check_hibp(password: str) -> dict:
    """
    Checks password against HaveIBeenPwned using the
    k-anonymity model — only the first 5 chars of the
    SHA1 hash are sent, never the full password.

    Returns:
    {
        "found"  : True/False,
        "count"  : number of times seen in breaches,
        "error"  : None or error message
    }
    """
    sha1     = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix   = sha1[:5]
    suffix   = sha1[5:]

    try:
        resp = requests.get(
            f"https://api.pwnedpasswords.com/range/{prefix}",
            headers={"Add-Padding": "true"},
            timeout=5
        )
        if resp.status_code != 200:
            return {"found": False, "count": 0, "error": f"API error {resp.status_code}"}

        for line in resp.text.splitlines():
            line_suffix, _, count = line.partition(":")
            if line_suffix.upper() == suffix:
                return {"found": True, "count": int(count.strip()), "error": None}

        return {"found": False, "count": 0, "error": None}

    except requests.exceptions.ConnectionError:
        return {"found": False, "count": 0, "error": "No internet connection"}
    except requests.exceptions.Timeout:
        return {"found": False, "count": 0, "error": "API request timed out"}
    except Exception as e:
        return {"found": False, "count": 0, "error": str(e)}


# ─────────────────────────────────────────────
#  Full Check + Pretty Printer
# ─────────────────────────────────────────────

def print_dictionary_report(password: str):
    """Runs all checks and prints a full report."""

    print(Fore.CYAN + "\n  ── Dictionary Check Report ─────────────────")
    print(Fore.WHITE + f"  Checking : {'*' * len(password)}\n")

    # Local dictionaries
    print(Fore.YELLOW + "  [Local Dictionaries]")
    local = check_all_local(password)

    for dict_name, found in local.items():
        if found is None:
            print(Fore.WHITE + f"    {dict_name:<22} : " + Fore.YELLOW + "Not available (download separately)")
        elif found:
            print(Fore.WHITE + f"    {dict_name:<22} : " + Fore.RED + "FOUND ✘  — common password!")
        else:
            print(Fore.WHITE + f"    {dict_name:<22} : " + Fore.GREEN + "Not found ✔")

    # HIBP check
    print(Fore.YELLOW + "\n  [HaveIBeenPwned Breach Database]")
    print(Fore.WHITE  + "  Contacting API (k-anonymity — your password is never sent)...")

    hibp = check_hibp(password)

    if hibp["error"]:
        print(Fore.YELLOW + f"  ⚠  Could not reach HIBP: {hibp['error']}")
    elif hibp["found"]:
        print(Fore.RED    + f"  ✘  Found in {hibp['count']:,} breached accounts!")
        print(Fore.RED    + "     This password should NEVER be used.")
    else:
        print(Fore.GREEN  + "  ✔  Not found in any known breach databases.")

    print(Fore.CYAN + "\n  ────────────────────────────────────────────\n")
