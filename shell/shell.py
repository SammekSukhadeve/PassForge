#!/usr/bin/env python3

import os
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from colorama import init, Fore
import pyfiglet

# All Modules
from parser.config_parser import parse_config, pretty_print_config, ConfigParseError
from parser.tag_parser     import process_tags
from engine.combinator     import generate_wordlist
from engine.filter         import apply_spec_filter, wordlist_stats
from checker.strength      import print_strength_report
from checker.dictionary    import print_dictionary_report

init(autoreset=True)

# ─────────────────────────────────────────────
#  Shell State
# ─────────────────────────────────────────────

class ShellState:
    def __init__(self):
        self.loaded_config   = None
        self.output_file     = None
        self.config_data     = {}
        self.tag_data        = {}
        self.wordlist        = []
        self.session_history = []
        self._temp_files     = []   # tracks all temp files for cleanup on exit

    def cleanup(self):
        """Deletes all temp files created during this session."""
        import glob
        deleted = []

        # Delete explicitly tracked temp files
        for path in self._temp_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    deleted.append(path)
                except Exception:
                    pass

        # Also wipe output/ and configs/ folders entirely
        for folder in ["output", "custom"]:
            if os.path.exists(folder):
                for f in glob.glob(os.path.join(folder, "*")):
                    try:
                        os.remove(f)
                        deleted.append(f)
                    except Exception:
                        pass

        if deleted:
            print(Fore.YELLOW + f"  Session cleanup: {len(deleted)} temp file(s) deleted.")


# ─────────────────────────────────────────────
#  Banner
# ─────────────────────────────────────────────

def print_banner():
    banner = pyfiglet.figlet_format("PassForge", font="slant")
    print(Fore.CYAN + banner)
    print(Fore.YELLOW + "  ╔══════════════════════════════════════════════════╗")
    print(Fore.YELLOW + "  ║   Targeted Wordlist Generator  |  v1.0           ║")
    print(Fore.YELLOW + "  ║   For authorized penetration testing only        ║")
    print(Fore.YELLOW + "  ╚══════════════════════════════════════════════════╝")
    print(Fore.WHITE  + "\n  Type 'help' to see available commands.\n")


# ─────────────────────────────────────────────
#  Help Menu
# ─────────────────────────────────────────────

def print_help(topic=None):
    print(Fore.CYAN + """
  ╔══════════════════════════════════════════════════════════════╗
  ║                    PassForge  v1.0                           ║
  ║      Targeted Wordlist Generator for Authorized Testing      ║
  ╚══════════════════════════════════════════════════════════════╝""")

    print(Fore.WHITE + """
  PassForge builds smart, targeted password wordlists using
  socially engineered data. Unlike flat tools like CUPP, PassForge
  uses a relational tag system — you define how pieces of data are
  connected and it generates context-aware combinations.
  Intended strictly for authorized penetration testing and CTFs.
""")

    print(Fore.YELLOW + "  ── CORE COMMANDS ─────────────────────────────────────────────")
    core = [
        ("auto",                      "Launch guided Q&A to auto-build a config file.\n"
                                      "         Asks about name, DOB, family, partner,\n"
                                      "         children, pets and interests step by step."),
        ("customize",                 "Enter to customize your wordlist\n"
                                      "         Example: customize → then add identity → then @name person1(John) and so on..."),
        ("load custom",        "Load a custom file into the session.\n"
                                      "         Example: load custom mydata → looks for custom/mydata.custom"),
        ("show config",               "Show the loaded custom file in structured form."),
        ("unload config",             "Unload the current custom file and clear session data."),
        ("generate",                  "Generate wordlist from loaded config.\n"
                                      "         Saves to output/wordlist.txt by default."),
        ("generate --output <path>",  "Generate and save to a custom path.\n"
                                      "         Example: generate --output ~/Desktop/out.txt"),
        ("show wordlist",             "Preview first 20 entries of the generated wordlist."),
        ("save wordlist <path>",      "Save wordlist to a specified file."),
        ("wordlist stats",            "Show total entries, length range, capitals, symbols."),
        ("check password",            "Check a password against all loaded dictionaries\n"
                                      "         and HaveIBeenPwned breach database."),
        ("check strength",            "Rate password strength — entropy, crack time,\n"
                                      "         weak pattern detection and suggestions."),
        ("status",                    "Show current session state."),
        ("history",                   "Show commands typed this session."),
        ("clear",                     "Clear the terminal screen."),
        ("exit / quit",               "Exit PassForge."),
    ]
    for cmd, desc in core:
        print(Fore.GREEN + f"\n    {cmd}")
        print(Fore.WHITE + f"         {desc}")

    print(Fore.YELLOW + "\n\n  ── VIEW COMMANDS ─────────────────────────────────────────────")
    views = [
        ("view tags",   "Show all tags with their ID, type, kind and linked ID."),
        ("view data",   "Show all values grouped by tag.\n"
                        "         File-loaded arrays shown in tabular format."),
        ("view all",    "Show everything — tags, data, specs and transforms."),
    ]
    for cmd, desc in views:
        print(Fore.GREEN + f"\n    {cmd}")
        print(Fore.WHITE + f"         {desc}")

    print(Fore.YELLOW + "\n\n  ── TAG TYPES (In Customize shell) ───────────────────────────────────────")
    print(Fore.WHITE + """
    @name    person1(Rohit)               Single name value
    @date    dob1(25051998)               Date — auto split into DD MM YYYY combos
    @string  team1(CSK)                   Any string value
    @number  jersey1(45, team1)           Number linked to another tag ID
    @string  arr_cars[] = {BMW,Nano}      Array of multiple values
    @number  car_no1(5074, arr_cars)      Number linked to every item in an array

    File input — load values from a .txt file:
    @name    names1(file:names.txt)       Each line in names.txt becomes a value
    @date    dobs1(file:dobs.txt)         Works for any tag type
""")

    print(Fore.YELLOW + "  ── TRANSFORMATION FLAGS ──────────────────────────────────────")
    print(Fore.WHITE + """
    All flags are active by DEFAULT unless you specify custom ones.
    Specify in [transformations] section of custom using full name or shortcut.

    Flag          Shortcut    Example
    ──────────────────────────────────────────────
    leet          -le         password  →  p@ssw0rd
    capitalize    -cp         john      →  John
    upper         -up         bmw       →  BMW
    lower         -l          BMW       →  bmw
    reverse       -rv         john      →  nhoj
    title         -t          john doe  →  John Doe

    Usage in .pwconf:
    global = leet, capitalize       (full names)
    global = -le, -cp               (shortcuts)
    global = -le, -cp, -up, -rv     (mix allowed)
""")

    print(Fore.YELLOW + "  ── SPEC FILTER OPTIONS ───────────────────────────────────────")
    print(Fore.WHITE + """
    must_have_capital = true/false    Only keep passwords with a capital letter
    must_have_symbol  = true/false    Only keep passwords with a symbol
    must_have_number  = true/false    Only keep passwords with a number
    min_length        = 8             Discard passwords shorter than this
    max_length        = 16            Discard passwords longer than this
""")

    print(Fore.YELLOW + "  ── COMMON SYNTAX ─────────────────────────────────────────────")
    print(Fore.WHITE + """
    ;                     Comment line — ignored by parser
    @type  id(value)      Single value tag
    @type  id(val, link)  Linked tag — val paired with linked id's values
    @type  arr[] = {}     Array of values
    global = flag,flag    Transformation flags (full name or shortcut)
    order = a > b         Priority order for wordlist sorting
""")

    print(Fore.YELLOW + "  ── TYPICAL WORKFLOW ──────────────────────────────────────────")
    print(Fore.WHITE + """
    passforge> auto                              (guided config builder)
         OR
    passforge> new config configs/target.pwconf  (blank template)
    passforge> load config configs/target.pwconf
    passforge> view all                          (verify your data)
    passforge> generate
    passforge> wordlist stats
    passforge> show wordlist
    passforge> check strength
""")
    print(Fore.CYAN + "  ──────────────────────────────────────────────────────────────\n")
    

# ─────────────────────────────────────────────
#  Command Handlers
# ─────────────────────────────────────────────

def handle_status(state: ShellState):
    print(Fore.CYAN + "\n  ── Session Status ──────────────────────────")
    cfg = state.loaded_config or Fore.RED + "None"
    out = state.output_file   or Fore.RED + "None"
    wl  = str(len(state.wordlist)) + " entries" if state.wordlist else Fore.RED + "Not generated"
    print(Fore.WHITE + f"  Config loaded  : {Fore.GREEN}{cfg}")
    print(Fore.WHITE + f"  Output file    : {Fore.GREEN}{out}")
    print(Fore.WHITE + f"  Wordlist       : {Fore.GREEN}{wl}")
    print(Fore.CYAN  + "  ────────────────────────────────────────────\n")


def handle_history(state: ShellState):
    if not state.session_history:
        print(Fore.YELLOW + "  No commands in history yet.")
        return
    print(Fore.CYAN + "\n  ── Command History ─────────────────────────")
    for i, cmd in enumerate(state.session_history, 1):
        print(Fore.WHITE + f"  {i:>3}  {cmd}")
    print(Fore.CYAN + "  ────────────────────────────────────────────\n")


def handle_load_config(args: list, state: ShellState):
    def handle_load_config(args: list, state: ShellState):
        if len(args) < 1:
            print(Fore.RED + "  Usage: load custom <name>")
        return
    path = args[0]
    # Auto-add .custom extension if missing
    if not path.endswith(".custom"):
        path += ".custom"
    # Auto-look in custom/ folder if no folder given
    if os.path.dirname(path) == "":
        path = os.path.join("custom", path)
    if not os.path.exists(path):
        print(Fore.RED + f"  Error: File not found → {path}")
        print(Fore.YELLOW + f"  Tip: Files are saved in the 'custom/' folder.")
        print(Fore.YELLOW + f"  Use 'load custom <name>' without folder or extension.")
        return
    if not path.endswith(".custom"):
        print(Fore.YELLOW + "  Warning: File does not have .custom extension.")
    try:
        parsed = parse_config(path)
        state.loaded_config = path
        state.config_data   = parsed
        state.tag_data      = {}
        state.wordlist      = []
        tags_count = len(parsed.get("identity", [])) + len(parsed.get("interests", []))
        print(Fore.GREEN + f"  ✔ Config loaded  : {path}")
        print(Fore.WHITE + f"  ✔ Tags found     : {tags_count}")
        print(Fore.WHITE + f"  ✔ Transforms     : {parsed['transformations']['global'] or 'none'}")
        print(Fore.WHITE + f"  ✔ Spec filter    : min={parsed['specs']['min_length']} max={parsed['specs']['max_length']}")
    except ConfigParseError as e:
        print(Fore.RED + f"  ✘ Parse error:\n  {e}")
    except FileNotFoundError as e:
        print(Fore.RED + f"  ✘ {e}")


def handle_show_config(state: ShellState):
    if not state.loaded_config:
        print(Fore.RED + "  No config loaded. Use: load config <path>")
        return
    if not state.config_data:
        print(Fore.YELLOW + "  Config file is loaded but not yet parsed.")
        return
    pretty_print_config(state.config_data)


def handle_unload_config(state: ShellState):
    if not state.loaded_config:
        print(Fore.YELLOW + "  No config is currently loaded.")
        return
    state.loaded_config = None
    state.config_data   = {}
    state.tag_data      = {}
    state.wordlist      = []
    print(Fore.GREEN + "  ✔ Config unloaded.")


def handle_new_config(args: list):
    if len(args) < 1:
        print(Fore.RED + "  Usage: new config <path>")
        return
    path = args[0]
    if not path.endswith(".custom"):
        path += ".custom"
    template = """; PassForge Configuration File
; Generated by PassForge v1.0
; Remove the semicolons (;) to activate each line

[identity]
; @name    person1(John)
; @date    dob1(25051998)
; @string  email1(john@gmail.com)

[interests]
; @string  team1(CSK)
; @number  jersey1(45, team1)
; @string  arr_cars[] = {BMW, Nano, Suzuki}
; @number  car_no1(5074, arr_cars)

[transformations]
; global = leet, capitalize

[specs]
; must_have_capital = true
; must_have_symbol  = false
; must_have_number  = true
; min_length        = 8
; max_length        = 16

[priority]
; order = identity > interests
"""
    try:
        if os.path.dirname(path) == "":
            path = os.path.join("custom", path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(template)
        print(Fore.GREEN + f"  ✔ Blank config created: {path}")
        print(Fore.WHITE + f"  Open it in any text editor and fill in your data.")
    except Exception as e:
        print(Fore.RED + f"  Error creating config: {e}")


def handle_generate(args: list, state: ShellState):
    if not state.loaded_config:
        print(Fore.RED + "  No config loaded. Use: load config <path>")
        return

    # Check for --output flag
    output_path = "output/wordlist.txt"
    if "--output" in args:
        idx = args.index("--output")
        if idx + 1 < len(args):
            output_path = args[idx + 1]
            state.output_file = output_path

    print(Fore.CYAN + "\n  ── Generating Wordlist ─────────────────────")

    # Module 3 — process tags
    print(Fore.WHITE + "  ⚙  Processing tags and ID links...")
    state.tag_data = process_tags(state.config_data)
    print(Fore.WHITE + f"  ✔ Pairs found    : {len(state.tag_data['pairs'])}")
    print(Fore.WHITE + f"  ✔ Base words     : {len(state.tag_data['words'])}")

    # Module 4 — generate combinations
    raw_wordlist = generate_wordlist(state.tag_data, state.config_data)
    print(Fore.WHITE + f"  ✔ Raw combos     : {len(raw_wordlist)}")

    # Module 5 — apply spec filter
    print(Fore.WHITE + "  ⚙  Applying spec filter...")
    state.wordlist = apply_spec_filter(raw_wordlist, state.config_data.get("specs", {}))
    print(Fore.WHITE + f"  ✔ After filter   : {len(state.wordlist)}")

    # Save to file
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(state.wordlist))

    print(Fore.GREEN + f"\n  ✔ Wordlist saved to: {output_path}")
    print(Fore.CYAN  + "  ────────────────────────────────────────────\n")


def handle_show_wordlist(state: ShellState):
    if not state.wordlist:
        print(Fore.RED + "  No wordlist generated yet. Run: generate")
        return
    print(Fore.CYAN + f"\n  ── Wordlist Preview (first 20 of {len(state.wordlist)}) ──")
    for word in state.wordlist[:20]:
        print(Fore.WHITE + f"  {word}")
    if len(state.wordlist) > 20:
        print(Fore.YELLOW + f"  ... and {len(state.wordlist) - 20} more entries")
    print(Fore.CYAN + "  ────────────────────────────────────────────\n")


def handle_save_wordlist(args: list, state: ShellState):
    if not state.wordlist:
        print(Fore.RED + "  No wordlist to save. Run: generate first.")
        return
    path = args[0] if args else "output/wordlist.txt"
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(state.wordlist))
    print(Fore.GREEN + f"  ✔ Wordlist saved to: {path}")

def handle_download(args: list, state: ShellState):
    if not state.wordlist:
        print(Fore.RED + "  No wordlist generated yet. Run: generate first.")
        return

    filename = args[0] if args else "wordlist.txt"
    if not filename.endswith(".txt"):
        filename += ".txt"

    dest = os.path.join(os.path.expanduser("~"), filename)

    # Check if file already exists
    if os.path.exists(dest):
        overwrite = input(
            Fore.YELLOW + f"  File '{filename}' already exists at {dest}.\n"
                          f"  Overwrite? (y/n): " + Fore.WHITE
        ).strip().lower()
        if overwrite != "y":
            print(Fore.YELLOW + "  Download cancelled.")
            return

    with open(dest, "w") as f:
        f.write("\n".join(state.wordlist))

    print(Fore.GREEN + f"  ✔ Wordlist saved to: {dest}")
    print(Fore.WHITE + f"  Total entries: {len(state.wordlist)}")
    state._temp_files.append(dest)

def handle_wordlist_stats(state: ShellState):
    if not state.wordlist:
        print(Fore.RED + "  No wordlist generated yet.")
        return
    stats = wordlist_stats(state.wordlist)
    print(Fore.CYAN + "\n  ── Wordlist Stats ──────────────────────────")
    print(Fore.WHITE + f"  Total entries  : {stats['total']}")
    print(Fore.WHITE + f"  Shortest       : {stats['min_length']} chars")
    print(Fore.WHITE + f"  Longest        : {stats['max_length']} chars")
    print(Fore.WHITE + f"  Avg length     : {stats['avg_length']} chars")
    print(Fore.WHITE + f"  Has capitals   : {stats['has_capitals']} entries")
    print(Fore.WHITE + f"  Has numbers    : {stats['has_numbers']} entries")
    print(Fore.WHITE + f"  Has symbols    : {stats['has_symbols']} entries")
    print(Fore.CYAN  + "  ────────────────────────────────────────────\n")


def handle_check_password():
    pwd = input(Fore.WHITE + "  Enter password to check: ")
    if not pwd:
        print(Fore.RED + "  No password entered.")
        return
    print_dictionary_report(pwd)


def handle_check_strength():
    pwd = input(Fore.WHITE + "  Enter password to rate: ")
    if not pwd:
        print(Fore.RED + "  No password entered.")
        return
    print_strength_report(pwd)

def handle_auto(state: ShellState):
    """
    Auto mode — guided Q&A to build a config interactively.
    """
    print(Fore.CYAN + "\n  ── Auto Config Builder ─────────────────────")
    print(Fore.WHITE + "  Answer the questions below. Press Enter to skip.\n"
                       "  Multiple values: separate with commas (John, Johnny)\n")

    tags_identity  = []
    tags_interests = []

    def ask(prompt_text, tag_type, tag_prefix, section_list):
        raw = input(Fore.GREEN + f"  {prompt_text}: " + Fore.WHITE).strip()
        if not raw:
            return
        values = [v.strip() for v in raw.split(",") if v.strip()]
        if len(values) == 1:
            section_list.append(f"{tag_type}  {tag_prefix}({values[0]})")
        else:
            arr_name = f"arr_{tag_prefix}"
            section_list.append(
                f"{tag_type}  {arr_name}[] = {{{', '.join(values)}}}"
            )

    # Block 1 — Basic identity
    print(Fore.YELLOW + "  [Personal Info]")
    ask("First Name",   "@name",   "firstname",  tags_identity)
    ask("Middle Name",  "@name",   "middlename", tags_identity)
    ask("Last Name",    "@name",   "lastname",   tags_identity)
    ask("Date of Birth (DDMMYYYY)", "@date", "dob", tags_identity)
    ask("Nickname",     "@name",   "nickname",   tags_identity)

    # Block 2 — Family
    print(Fore.YELLOW + "\n  [Family]")
    ask("Father's Name", "@name", "father", tags_identity)
    ask("Mother's Name", "@name", "mother", tags_identity)

    # Block 3 — Partner
    print(Fore.YELLOW + "\n  [Partner]")
    has_partner = input(Fore.GREEN + "  Have a Partner? (y/n): " + Fore.WHITE).strip().lower()
    if has_partner == "y":
        ask("Partner's Name", "@name", "partner",     tags_identity)
        ask("Partner's DOB",  "@date", "partner_dob", tags_identity)

    # Block 4 — Children
    print(Fore.YELLOW + "\n  [Children]")
    has_children = input(Fore.GREEN + "  Have Children? (y/n): " + Fore.WHITE).strip().lower()
    if has_children == "y":
        ask("Children's Name(s)", "@name", "child",     tags_identity)
        ask("Children's DOB(s)",  "@date", "child_dob", tags_identity)

    # Block 5 — Pet
    print(Fore.YELLOW + "\n  [Pet]")
    has_pet = input(Fore.GREEN + "  Have a Pet? (y/n): " + Fore.WHITE).strip().lower()
    if has_pet == "y":
        ask("Pet's Name", "@name", "pet", tags_interests)

    # Block 6 — Interests
    print(Fore.YELLOW + "\n  [Interests]")
    ask("Favourite Team",         "@string", "team",  tags_interests)
    ask("Favourite Player",       "@name",   "player", tags_interests)
    ask("Jersey/Shirt Number",    "@number", "jersey", tags_interests)
    ask("Car Name(s)",            "@string", "arr_cars", tags_interests)
    ask("Car Number",             "@number", "car_no",   tags_interests)
    ask("Favourite City",         "@string", "city",  tags_interests)

    # Save to .pwconf
    name = input(Fore.GREEN + "\n  Save config as (e.g. configs/target.pwconf): "
                 + Fore.WHITE).strip()
    if not name:
        name = "configs/auto_generated.pwconf"
    if not name.endswith(".pwconf"):
        name += ".pwconf"

    os.makedirs(os.path.dirname(name) if os.path.dirname(name) else ".", exist_ok=True)

    lines = ["; PassForge Auto-Generated Config\n\n"]
    lines.append("[identity]\n")
    for t in tags_identity:
        lines.append(f"{t}\n")
    lines.append("\n[interests]\n")
    for t in tags_interests:
        lines.append(f"{t}\n")
    lines.append("\n[transformations]\n; global = leet, capitalize\n")
    lines.append("\n[specs]\n; min_length = 8\n; max_length = 16\n")
    lines.append("\n[priority]\n; order = identity > interests\n")

    with open(name, "w") as f:
        f.writelines(lines)

    print(Fore.GREEN + f"\n  ✔ Config saved to: {name}")
    print(Fore.WHITE + f"  You can now run: load config {name}")
    print(Fore.CYAN  + "  ────────────────────────────────────────────\n")

def handle_view(args: list, state: ShellState):
    from parser.tag_parser import view_tags, view_data, view_all
    if not state.config_data:
        print(Fore.RED + "  No config loaded. Use: load config <path>")
        return
    sub = " ".join(args).lower().strip()
    if sub == "tags":
        view_tags(state.config_data)
    elif sub == "data":
        view_data(state.config_data)
    elif sub == "all":
        view_all(state.config_data)
    else:
        print(Fore.RED + "  Usage: view tags | view data | view all")
    
# ─────────────────────────────────────────────
#  Customize Subshell
# ─────────────────────────────────────────────

CUSTOMIZE_COMMANDS = [
    "add identity", "add interests", "add transform",
    "add spec", "add priority",
    "remove", "view tags", "view data", "view all",
    "save", "clear all", "help", "exit",
]

def customize_help():
    print(Fore.CYAN + "\n  ── Customize Subshell Commands ─────────────")
    cmds = [
        ("add identity",        "Add a tag to [identity] section"),
        ("add interests",       "Add a tag to [interests] section"),
        ("add transform",       "Set transformation flags"),
        ("add spec",            "Set a spec rule"),
        ("add priority",        "Set priority order"),
        ("remove <id>",         "Remove a tag by its ID"),
        ("view tags",           "Show all tags created so far"),
        ("view data",           "Show all values in tabular form"),
        ("view all",            "Show everything"),
        ("save",                "Save current data to a .pwconf file"),
        ("clear all",           "Clear all data in this session"),
        ("help",                "Show this menu"),
        ("exit",                "Exit customize and return to main shell"),
    ]
    for cmd, desc in cmds:
        print(Fore.GREEN + f"    {cmd:<22}" + Fore.WHITE + desc)
    print()
    print(Fore.YELLOW + "  Tag syntax examples:")
    print(Fore.WHITE  +
        "    @name   person1(John)\n"
        "    @date   dob1(25051998)\n"
        "    @string team1(CSK)\n"
        "    @number jersey1(45, team1)\n"
        "    @string arr_cars[] = {BMW, Nano, Suzuki}\n"
        "    @name   names1(file:names.txt)\n"
    )
    print(Fore.YELLOW + "  Transform flags (full or shortcut):")
    print(Fore.WHITE  + "    -le=leet  -cp=capitalize  -up=upper  -l=lower  -rv=reverse  -t=title\n")
    print(Fore.CYAN + "  ────────────────────────────────────────────\n")


def handle_customize(state: ShellState):
    """
    Opens an interactive subshell where the user can build
    their config entirely from the terminal without editing files.
    All data is stored in state.config_data directly.
    """
    from parser.tag_parser import view_tags, view_data, view_all
    from parser.config_parser import parse_tag_line, ConfigParseError

    # Initialize config_data structure if empty
    if not state.config_data:
        state.config_data = {
            "identity"       : [],
            "interests"      : [],
            "transformations": {"global": []},
            "specs"          : {
                "must_have_capital": False,
                "must_have_symbol" : False,
                "must_have_number" : False,
                "min_length"       : 6,
                "max_length"       : 20,
            },
            "priority"       : {"order": []},
            "_meta"          : {"filepath": "in-memory", "line_count": 0},
        }
        state.loaded_config = "in-memory"

    sub_session = PromptSession(
        completer=WordCompleter(CUSTOMIZE_COMMANDS, ignore_case=True),
        style=SHELL_STYLE
    )

    print(Fore.CYAN + "\n  ── Customize Mode ──────────────────────────")
    print(Fore.WHITE + "  Build your config interactively.")
    print(Fore.WHITE + "  Type 'help' for commands, 'exit' to return.\n")

    while True:
        try:
            raw = sub_session.prompt(
                HTML("<bracket>[</bracket><prompt>customize</prompt><bracket>]</bracket> > ")
            ).strip()

            if not raw:
                continue

            parts = raw.split()
            cmd   = " ".join(parts).lower()

            # ── exit ──
            if parts[0] == "exit":
                print(Fore.GREEN + "  ✔ Returning to main shell. Data kept in session.")
                break

            # ── help ──
            elif parts[0] == "help":
                customize_help()

            # ── add identity / add interests ──
            elif cmd.startswith("add identity") or cmd.startswith("add interests"):
                section = "identity" if "identity" in cmd else "interests"

                print(Fore.WHITE +
                    "  Choose input method:\n"
                    "    1) Type a value directly\n"
                    "    2) Load values from a file\n"
                )
                method = input(Fore.GREEN + "  Choice (1/2): " + Fore.WHITE).strip()

                parsed_tag = None

                if method == "2":
                    dtype    = input(Fore.GREEN + "  Tag type (@name/@date/@string/@number): "
                                     + Fore.WHITE).strip()
                    tag_id   = input(Fore.GREEN + "  Tag ID (e.g. names1): "
                                     + Fore.WHITE).strip()
                    filepath = input(Fore.GREEN + "  File path: "
                                     + Fore.WHITE).strip().strip('"').strip("'")

                    if not dtype or not tag_id or not filepath:
                        print(Fore.RED + "  Cancelled — all fields required.")
                        continue

                    if not os.path.exists(filepath):
                        print(Fore.RED + f"  ✘ File not found: {filepath}")
                        continue

                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
                            file_values = [
                                line.strip() for line in fh
                                if line.strip() and not line.startswith(";")
                            ]
                        if not file_values:
                            print(Fore.RED + "  ✘ File is empty.")
                            continue

                        parsed_tag = {
                            "kind"  : "array",
                            "dtype" : dtype if dtype.startswith("@") else f"@{dtype}",
                            "id"    : tag_id,
                            "values": file_values,
                            "source": filepath,
                        }
                        print(Fore.GREEN + f"  ✔ Loaded {len(file_values)} values from file.")

                    except Exception as e:
                        print(Fore.RED + f"  ✘ Could not read file: {e}")
                        continue

                else:
                    print(Fore.WHITE +
                        "  Syntax examples:\n"
                        "    @name   person1(John)\n"
                        "    @date   dob1(25051998)\n"
                        "    @string team1(CSK)\n"
                        "    @number jersey1(45, team1)\n"
                        "    @string arr_cars[] = {BMW, Nano, Suzuki}\n"
                    )
                    tag_raw = input(Fore.GREEN + "  Enter tag: " + Fore.WHITE).strip()
                    if not tag_raw:
                        print(Fore.YELLOW + "  Skipped.")
                        continue
                    try:
                        parsed_tag = parse_tag_line(tag_raw, 0)
                    except Exception as e:
                        print(Fore.RED + f"  ✘ {e}")
                        continue

                if parsed_tag is None:
                    print(Fore.RED + "  ✘ Could not process tag. Try again.")
                    continue

                existing_ids = [t["id"] for t in state.config_data[section]]
                if parsed_tag["id"] in existing_ids:
                    confirm = input(
                        Fore.YELLOW + f"  ⚠ ID '{parsed_tag['id']}' already exists. "
                                      f"Overwrite? (y/n): " + Fore.WHITE
                    ).strip().lower()
                    if confirm != "y":
                        print(Fore.YELLOW + "  Skipped — existing tag kept.")
                        continue
                    state.config_data[section] = [
                        t for t in state.config_data[section]
                        if t["id"] != parsed_tag["id"]
                    ]
                    print(Fore.YELLOW + f"  Overwriting '{parsed_tag['id']}'...")

                state.config_data[section].append(parsed_tag)
                print(Fore.GREEN + f"  ✔ Tag '{parsed_tag['id']}' added to [{section}].")

            # ── add transform ──
            elif cmd.startswith("add transform"):
                print(Fore.WHITE + "  Flags: leet(-le) capitalize(-cp) upper(-up) lower(-l) reverse(-rv) title(-t)")
                raw_flags = input(Fore.GREEN + "  Enter flags (comma separated): " + Fore.WHITE).strip()
                from engine.transformer import resolve_flags
                flags = [f.strip() for f in raw_flags.split(",") if f.strip()]
                resolved = resolve_flags(flags)
                if resolved:
                    state.config_data["transformations"]["global"] = resolved
                    print(Fore.GREEN + f"  ✔ Transforms set: {resolved}")
                else:
                    print(Fore.RED + "  ✘ No valid flags found.")

            # ── add spec ──
            elif cmd.startswith("add spec"):
                print(Fore.WHITE +
                    "  Available specs:\n"
                    "    must_have_capital (true/false)\n"
                    "    must_have_symbol  (true/false)\n"
                    "    must_have_number  (true/false)\n"
                    "    min_length        (number)\n"
                    "    max_length        (number)\n"
                )
                key = input(Fore.GREEN + "  Spec key   : " + Fore.WHITE).strip().lower()
                val = input(Fore.GREEN + "  Spec value : " + Fore.WHITE).strip().lower()
                bool_keys = {"must_have_capital", "must_have_symbol", "must_have_number"}
                int_keys  = {"min_length", "max_length"}
                if key in bool_keys:
                    state.config_data["specs"][key] = val == "true"
                    print(Fore.GREEN + f"  ✔ {key} = {val == 'true'}")
                elif key in int_keys:
                    try:
                        state.config_data["specs"][key] = int(val)
                        print(Fore.GREEN + f"  ✔ {key} = {int(val)}")
                    except ValueError:
                        print(Fore.RED + "  ✘ Value must be a number.")
                else:
                    print(Fore.RED + f"  ✘ Unknown spec key '{key}'.")

            # ── add priority ──
            elif cmd.startswith("add priority"):
                print(Fore.WHITE + "  Example: identity > interests")
                raw_p = input(Fore.GREEN + "  Priority order: " + Fore.WHITE).strip()
                import re
                order = [s.strip() for s in re.split(r">|,", raw_p) if s.strip()]
                state.config_data["priority"]["order"] = order
                print(Fore.GREEN + f"  ✔ Priority set: {' > '.join(order)}")

            # ── remove <id> ──
            elif cmd.startswith("remove"):
                if len(parts) < 2:
                    print(Fore.RED + "  Usage: remove <tag_id>")
                    continue
                target_id = parts[1]
                removed = False
                for section in ("identity", "interests"):
                    before = len(state.config_data[section])
                    state.config_data[section] = [
                        t for t in state.config_data[section]
                        if t["id"] != target_id
                    ]
                    if len(state.config_data[section]) < before:
                        print(Fore.GREEN + f"  ✔ Tag '{target_id}' removed from [{section}].")
                        removed = True
                if not removed:
                    print(Fore.RED + f"  ✘ Tag ID '{target_id}' not found.")

            # ── view ──
            elif cmd == "view tags":
                view_tags(state.config_data)
            elif cmd == "view data":
                view_data(state.config_data)
            elif cmd == "view all":
                view_all(state.config_data)

            # ── save ──
            elif parts[0] == "save":
                save_path = input(
                    Fore.GREEN + "  Save to (e.g. configs/target.pwconf): " + Fore.WHITE
                ).strip()
                if not save_path:
                    save_path = "custom/custom.custom"
                if not save_path.endswith(".custom"):
                    save_path += ".custom"
                if os.path.dirname(save_path) == "":
                    save_path = os.path.join("custom", save_path)
                _save_config_to_file(state.config_data, save_path)
                if os.path.dirname(save_path) == "":
                    save_path = os.path.join("custom", save_path)
                _save_config_to_file(state.config_data, save_path)
                state.loaded_config = save_path
                state._temp_files.append(save_path)   # mark as temp

            # ── clear all ──
            elif cmd == "clear all":
                confirm = input(Fore.YELLOW + "  Clear all data? (y/n): " + Fore.WHITE).strip().lower()
                if confirm == "y":
                    state.config_data = {}
                    state.loaded_config = None
                    state.wordlist = []
                    print(Fore.GREEN + "  ✔ All data cleared.")

            else:
                print(Fore.RED + f"  Unknown command: '{raw}'. Type 'help'.")

        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n  Use 'exit' to return to main shell.")
        except EOFError:
            break


def _save_config_to_file(config_data: dict, path: str):
    """Serializes in-memory config_data back to a .pwconf file."""
    import os
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)

    lines = ["; PassForge Config — saved from customize mode\n\n"]

    for section in ("identity", "interests"):
        lines.append(f"[{section}]\n")
        for tag in config_data.get(section, []):
            kind = tag["kind"]
            dtype = tag["dtype"]
            tid   = tag["id"]
            if kind == "array":
                vals = ", ".join(tag["values"])
                lines.append(f"{dtype}  {tid}[] = {{{vals}}}\n")
            elif kind == "linked":
                lines.append(f"{dtype}  {tid}({tag['value']}, {tag['link']})\n")
            else:
                lines.append(f"{dtype}  {tid}({tag['value']})\n")
        lines.append("\n")

    lines.append("[transformations]\n")
    flags = config_data.get("transformations", {}).get("global", [])
    if flags:
        lines.append(f"global = {', '.join(flags)}\n")
    lines.append("\n")

    lines.append("[specs]\n")
    for k, v in config_data.get("specs", {}).items():
        lines.append(f"{k} = {str(v).lower()}\n")
    lines.append("\n")

    lines.append("[priority]\n")
    order = config_data.get("priority", {}).get("order", [])
    if order:
        lines.append(f"order = {' > '.join(order)}\n")

    with open(path, "w") as f:
        f.writelines(lines)

    print(Fore.GREEN + f"  ✔ Config saved to: {path}")


# ─────────────────────────────────────────────
#  Command Router
# ─────────────────────────────────────────────

def route_command(raw: str, state: ShellState) -> bool:
    parts = raw.strip().split()
    if not parts:
        return True
    cmd = " ".join(parts).lower()

    if parts[0] in ("exit", "quit"):
        print(Fore.CYAN + "\n  Goodbye. Stay ethical.\n")
        state.cleanup()
        return False
    elif parts[0] == "clear":
        os.system("cls" if os.name == "nt" else "clear")
        print_banner()
    elif parts[0] == "help":
        print_help()
    elif parts[0] == "history":
        handle_history(state)
    elif parts[0] == "status":
        handle_status(state)
    elif cmd.startswith("load custom"):
        path_args = [" ".join(parts[2:])] if len(parts) > 2 else []
        handle_load_config(path_args, state)
    elif cmd == "show custom":
        handle_show_config(state)
    elif cmd == "unload custom":
        handle_unload_config(state)
    elif parts[0] == "new" and len(parts) >= 2 and parts[1] == "config":
        # Usage: new config <path>
        # Pass everything after the 'new config' tokens
        path_args = [" ".join(parts[2:])] if len(parts) > 2 else []
        handle_new_config(path_args)
    elif parts[0] == "customize":
        handle_customize(state)

    elif cmd.startswith("download"):
        path_args = [" ".join(parts[1:])] if len(parts) > 1 else []
        handle_download(path_args, state)
    elif parts[0] == "generate":
        handle_generate(parts[1:], state)
    elif cmd == "show wordlist":
        handle_show_wordlist(state)
    elif cmd.startswith("save wordlist"):
        path_args = [" ".join(parts[2:])] if len(parts) > 2 else []
        handle_save_wordlist(path_args, state)
    elif cmd == "wordlist stats":
        handle_wordlist_stats(state)
    elif cmd == "check password":
        handle_check_password()
    elif cmd == "check strength":
        handle_check_strength()
    elif parts[0] == "auto":
        handle_auto(state)
    elif parts[0] == "view":
        handle_view(parts[1:], state)
    else:
        print(Fore.RED + f"  Unknown command: '{raw}'. Type 'help' for commands.")

    return True


# ─────────────────────────────────────────────
#  Main Shell Class
# ─────────────────────────────────────────────

ALL_COMMANDS = [
    "help", "clear", "exit", "quit", "history", "status",
    "load custom", "show custom", "unload custom", "customize",
    "new config", 
    "generate", "generate --output",
    "show wordlist", "save wordlist", "wordlist stats",
    "check password", "check strength",
    "download",
    "auto",
    "view tags", "view data", "view all",
]


SHELL_STYLE = Style.from_dict({
    "prompt" : "ansicyan bold",
    "bracket": "ansiyellow",
})

class PassForgeShell:
    def __init__(self):
        self.state     = ShellState()
        self.completer = WordCompleter(ALL_COMMANDS, ignore_case=True)
        self.session   = PromptSession(completer=self.completer, style=SHELL_STYLE)

    def run(self):
        os.system("cls" if os.name == "nt" else "clear")
        print_banner()
        while True:
            try:
                cfg_label = ""
                if self.state.loaded_config:
                    name = os.path.basename(self.state.loaded_config)
                    cfg_label = f"[{name}] "
                prompt_str = HTML(
                    f"<bracket>[</bracket>"
                    f"<prompt>passforge</prompt>"
                    f"<bracket>]</bracket>"
                    f" {cfg_label}> "
                )
                raw = self.session.prompt(prompt_str)
                if not raw.strip():
                    continue
                self.state.session_history.append(raw.strip())
                keep_running = route_command(raw.strip(), self.state)
                if not keep_running:
                    break
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n  Use 'exit' to quit PassForge.")
            except EOFError:
                print(Fore.CYAN + "\n  Goodbye. Stay ethical.\n")
                self.state.cleanup()
                break

#what is this file for?
""" This file contains the main shell implementation for the PassForge application.
 It defines the command-line interface, command routing, and interactive subshell for customizing configurations. 
 The shell allows users to load configs, generate wordlists, view stats, and more, all from a user-friendly terminal interface. """