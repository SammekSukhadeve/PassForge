# PassForge — Targeted Wordlist Generator

PassForge is a Python-based command-line tool designed for **authorized penetration testers, CTF players and security researchers** to generate intelligent, targeted password wordlists using socially engineered data about a target.

Unlike traditional tools like CUPP that treat all data as flat unrelated strings, PassForge introduces a **relational tag system** — you define how pieces of information connect to each other and the engine generates context-aware combinations. For example a car number gets paired only with its car name, not randomly with unrelated words. This produces smaller, smarter and more accurate wordlists.

> **Disclaimer:** PassForge is strictly intended for authorized penetration testing, CTF challenges and personal password auditing. Always ensure you have explicit written permission before testing any system you do not own. Misuse of this tool is illegal and unethical.

---

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Project Structure](#project-structure)
4. [Getting Started](#getting-started)
5. [Core Commands](#core-commands)
6. [Customize Subshell](#customize-subshell)
7. [Tag System](#tag-system)
8. [Sections in a Custom Config](#sections-in-a-custom-config)
9. [Transformation Flags](#transformation-flags)
10. [Spec Filter Options](#spec-filter-options)
11. [View Commands](#view-commands)
12. [Password Checker](#password-checker)
13. [Auto Mode](#auto-mode)
14. [Download Wordlist](#download-wordlist)
15. [Workflow Example](#workflow-example)

---

## Features

- **Custom Shell Environment** — interactive REPL shell with tab autocomplete and command history
- **Relational Tag System** — link data points together so combinations are context-aware, not random
- **Array Support** — group multiple values under one tag and link them to other tags
- **File Input Support** — load names, dates or any data directly from a `.txt` file
- **Customize Subshell** — build your entire config interactively from the terminal without editing any file
- **Auto Mode** — guided question-answer session that builds a config automatically
- **Transformation Engine** — leet speak, capitalize, upper, lower, reverse and title case
- **Default Transformations** — all flags active by default unless customized
- **Spec Filter** — filter output based on known password policy rules
- **Priority Sorting** — most probable passwords appear at the top of the wordlist
- **Password Strength Checker** — entropy scoring, pattern detection and improvement tips
- **Dictionary Checker** — checks against local wordlists and HaveIBeenPwned breach database
- **Auto Dictionary Scanning** — drop any `.txt` wordlist into the dictionaries folder and it is picked up automatically
- **Download Command** — save your wordlist directly to any location on your system
- **Temp File Cleanup** — all session files are deleted automatically when the tool closes

---

## Installation

### Requirements
- Python 3.8 or higher
- pip

### Install Dependencies

```bash
pip install prompt_toolkit colorama pyfiglet requests zxcvbn tqdm
```

### Clone or Download

```bash
git clone https://github.com/yourusername/passforge.git
cd passforge
```

### Run

```bash
python3 passforge.py
```

---

## Project Structure

```
passforge/
│
├── passforge.py                 Entry point — run this to start the tool
│
├── shell/
│   ├── __init__.py
│   └── shell.py                 Shell environment, all commands, session state
│
├── parser/
│   ├── __init__.py
│   ├── config_parser.py         Reads and parses .custom config files
│   └── tag_parser.py            Resolves tag links, arrays and view commands
│
├── engine/
│   ├── __init__.py
│   ├── combinator.py            Generates all word combinations
│   ├── transformer.py           Applies leet, reverse, capitalize etc.
│   └── filter.py                Filters output by spec rules and priority
│
├── checker/
│   ├── __init__.py
│   ├── strength.py              Password strength scoring and pattern detection
│   └── dictionary.py            Checks against local wordlists and HIBP API
│
├── dictionaries/
│   └── common_passwords.txt     Bundled common passwords list
│
├── custom/                      Saved config files (.custom)
└── output/                      Generated wordlists (temporary)
```

---

## Getting Started

### Quick Start with Auto Mode
The fastest way to get started — let PassForge ask you the questions:

```
passforge> auto
```

### Manual Start
```
passforge> customize            (build config interactively)
passforge> generate             (generate wordlist)
passforge> download mylist      (save wordlist to your system)
```

---

## Core Commands

| Command | Description |
|---|---|
| `auto` | Launch guided Q&A to build a config automatically |
| `customize` | Open the customize subshell to build config interactively |
| `load custom <name>` | Load a saved config into the session |
| `show custom` | Display the currently loaded config in structured form |
| `unload custom` | Unload the current config and clear all session data |
| `generate` | Generate wordlist from the loaded config |
| `generate --output <path>` | Generate and save to a custom file path |
| `show wordlist` | Preview the first 20 entries of the generated wordlist |
| `save wordlist <path>` | Save wordlist to a specified path |
| `wordlist stats` | Show total entries, length range, capitals, numbers, symbols |
| `download <filename>` | Save the wordlist to your home directory or a specified path |
| `check password` | Check a password against dictionaries and breach database |
| `check strength` | Rate a password's strength with entropy and pattern analysis |
| `view tags` | Show all tags with their ID, type, kind and linked ID |
| `view data` | Show all values grouped by tag in tabular format |
| `view all` | Show everything — tags, data, specs and transforms |
| `status` | Show current session state |
| `history` | Show commands typed this session |
| `clear` | Clear the terminal screen |
| `help` | Show the full help menu |
| `exit / quit` | Exit PassForge and delete all temp files |

---

## Customize Subshell

The customize subshell lets you build your entire config interactively from the terminal without opening or editing any file manually.

### How to enter
```
passforge> customize
```

### Customize Commands

| Command | Description |
|---|---|
| `add identity` | Add a personal info tag (name, DOB, email etc.) |
| `add interests` | Add an interests tag (team, car, jersey number etc.) |
| `add transform` | Set transformation flags |
| `add spec` | Set a password spec rule |
| `add priority` | Set priority order of sections |
| `remove <id>` | Remove a tag by its ID |
| `view tags` | Show all tags created so far |
| `view data` | Show all values in tabular form |
| `view all` | Show everything |
| `save` | Save current session data to a .custom file |
| `clear all` | Clear all data in current session |
| `help` | Show customize help menu |
| `exit` | Return to main shell |

### Example Session

```
passforge> customize

[customize] > add identity
  Choose input method:
    1) Type a value directly
    2) Load values from a file
  Choice (1/2): 1
  Enter tag: @name person1(John)
  ✔ Tag 'person1' added to [identity].

[customize] > add identity
  Choice (1/2): 1
  Enter tag: @date dob1(25051998)
  ✔ Tag 'dob1' added to [identity].

[customize] > add interests
  Choice (1/2): 1
  Enter tag: @string team1(CSK)
  ✔ Tag 'team1' added to [interests].

[customize] > add interests
  Choice (1/2): 1
  Enter tag: @number jersey1(45, team1)
  ✔ Tag 'jersey1' added to [interests].

[customize] > add transform
  Enter flags: -le, -cp
  ✔ Transforms set: ['leet', 'capitalize']

[customize] > add spec
  Spec key   : min_length
  Spec value : 8
  ✔ min_length = 8

[customize] > save
  Save to: john
  ✔ Config saved to: custom/john.custom

[customize] > exit
  ✔ Returning to main shell.
```

---

## Tag System

Tags are the core of PassForge. They define the data about a target and how different pieces of data relate to each other.

### Tag Syntax

```
@type   id(value)                  Single value
@type   id(value, linked_id)       Value linked to another tag
@type   arr_id[] = {v1, v2, v3}   Array of values
@type   id(file:path/to/file.txt)  Load values from a file
```

### Tag Types

| Type | Used For | Example |
|---|---|---|
| `@name` | Person names | `@name person1(John)` |
| `@date` | Dates of birth | `@date dob1(25051998)` |
| `@string` | Any text value | `@string team1(CSK)` |
| `@number` | Any number value | `@number jersey1(45, team1)` |

### Single Tag
A simple tag with one value.
```
@name   person1(John)
@string city1(Pune)
```

### Linked Tag
Links a value to another tag's ID. PassForge will only pair these two together, not randomly with other data.
```
@string  team1(CSK)
@number  jersey1(45, team1)
```
Generates: `CSK45`, `45CSK`, `csk45`, `Csk45` etc.

### Array Tag
Groups multiple related values under one ID.
```
@string  arr_cars[] = {BMW, Nano, Suzuki}
```

### Linked Array Tag
Links a value to every item in an array.
```
@string  arr_cars[] = {BMW, Nano, Suzuki}
@number  car_no1(5074, arr_cars)
```
Generates: `BMW5074`, `Nano5074`, `Suzuki5074`, `5074BMW` etc.

### File Input Tag
Load many values at once from a `.txt` file. Each line in the file becomes one value.
```
add identity → Choose option 2 → Load from file
Tag type : @name
Tag ID   : names1
File path: /home/user/names.txt
```

---

## Sections in a Custom Config

Every config is divided into five sections:

### [identity]
Personal information about the target.
```
@name    person1(John)
@date    dob1(25051998)
@string  email1(john@gmail)
@name    father1(Robert)
@name    mother1(Mary)
@name    pet1(Bruno)
```

### [interests]
Hobbies, teams, cars and external interests.
```
@string  team1(CSK)
@number  jersey1(45, team1)
@string  arr_cars[] = {BMW, Audi, Suzuki}
@number  car_no1(5074, arr_cars)
@string  city1(Pune)
```

### [transformations]
How to mutate each word. All flags are active by default. Customize using full names or shortcuts.
```
global = leet, capitalize
global = -le, -cp, -up
```

### [specs]
Filter the output based on known password policy rules.
```
must_have_capital = true
must_have_symbol  = false
must_have_number  = true
min_length        = 8
max_length        = 16
```

### [priority]
Which section's combinations appear at the top of the wordlist.
```
order = identity > interests
```

---

## Transformation Flags

Transformations mutate each word into multiple variants. All flags are **on by default**. You can set custom flags in the customize subshell or in your config file.

| Flag | Shortcut | Example |
|---|---|---|
| `leet` | `-le` | `password` → `p@ssw0rd` |
| `capitalize` | `-cp` | `john` → `John` |
| `upper` | `-up` | `bmw` → `BMW` |
| `lower` | `-l` | `BMW` → `bmw` |
| `reverse` | `-rv` | `john` → `nhoj` |
| `title` | `-t` | `john doe` → `John Doe` |

### Setting Transforms in Customize

```
[customize] > add transform
  Enter flags: -le, -cp, -rv
  ✔ Transforms set: ['leet', 'capitalize', 'reverse']
```

---

## Spec Filter Options

If you know the target system's password policy, set these rules to filter out combinations that would never be accepted as valid passwords.

| Key | Values | What it does |
|---|---|---|
| `must_have_capital` | `true / false` | Keep only passwords with a capital letter |
| `must_have_symbol` | `true / false` | Keep only passwords with a symbol |
| `must_have_number` | `true / false` | Keep only passwords with a number |
| `min_length` | number | Discard passwords shorter than this |
| `max_length` | number | Discard passwords longer than this |

### Setting Specs in Customize

```
[customize] > add spec
  Spec key   : must_have_capital
  Spec value : true
  ✔ must_have_capital = True

[customize] > add spec
  Spec key   : min_length
  Spec value : 8
  ✔ min_length = 8
```

---

## View Commands

View commands let you inspect all the data you have entered so far.

### `view tags`
Shows all tag IDs, their type, kind and what they are linked to.
```
passforge> view tags

  ID                   Type       Kind       Linked To
  ────────────────────────────────────────────────────
  person1              @name      single     —
  dob1                 @date      single     —
  team1                @string    single     —
  jersey1              @number    linked     → team1
  arr_cars             @string    array      —
  car_no1              @number    linked     → arr_cars
```

### `view data`
Shows all values grouped by tag. Arrays shown in tabular format.
```
passforge> view data

  [person1]  @name  (single)
  Value : John

  [arr_cars]  @string  (array)
  BMW         Nano        Suzuki
  Total: 3 values
```

### `view all`
Shows everything — tags, data, specs, transformations and priority.

---

## Password Checker

### Check Against Dictionaries
```
passforge> check password
  Enter password to check: password123

  [Local Dictionaries]
    common_passwords    : FOUND ✘  — common password!
    rockyou             : FOUND ✘  — common password!

  [HaveIBeenPwned Breach Database]
  ✘  Found in 2,418,819 breached accounts!
     This password should NEVER be used.
```

### Check Password Strength
```
passforge> check strength
  Enter password to rate: MyD0g$Bruno99

  Password   : *************
  Length     : 13 characters
  Entropy    : 78.4 bits
  Rating     : Strong ★★★★☆
  Crack time : centuries
```

### Adding More Dictionaries
Drop any `.txt` wordlist file into the `dictionaries/` folder and PassForge will automatically check against it.

```
dictionaries/
├── common_passwords.txt    (bundled)
├── rockyou.txt             (download from SecLists)
└── darkweb2017.txt         (download from SecLists)
```

---

## Auto Mode

Auto mode asks you a series of guided questions and builds the config automatically. No tag syntax knowledge needed.

```
passforge> auto

  [Personal Info]
  First Name  : John
  Middle Name :
  Last Name   : Doe
  DOB         : 25051998
  Nickname    : JD

  [Family]
  Father's Name : Robert
  Mother's Name : Mary

  [Partner]
  Have a Partner? (y/n): y
  Partner's Name : Sara
  Partner's DOB  : 10021995

  [Children]
  Have Children? (y/n): n

  [Pet]
  Have a Pet? (y/n): y
  Pet's Name : Bruno

  [Interests]
  Favourite Team   : CSK
  Jersey Number    : 45
  Car Name(s)      : BMW, Audi
  Car Number       : 5074

  Save config as: configs/john
  ✔ Config saved to: custom/john.custom
```

---

## Download Wordlist

After generating a wordlist use the `download` command to save it anywhere on your system.

```
# Save to home directory
passforge> download mylist
✔ Wordlist saved to: /home/kali/mylist.txt

# Save to a specific path
passforge> download /home/kali/Desktop/mylist.txt
✔ Wordlist saved to: /home/kali/Desktop/mylist.txt
```

If the file already exists the tool will ask before overwriting:
```
  File already exists at /home/kali/mylist.txt
  Overwrite? (y/n):
```

---

## Workflow Example

Full example from start to finish:

```
# Step 1 — Start PassForge
python3 passforge.py

# Step 2 — Build config (choose one)
passforge> auto                          (guided questions)
passforge> customize                     (manual tag entry)

# Step 3 — Verify your data
passforge> view all

# Step 4 — Generate wordlist
passforge> generate
  ✔ Pairs found    : 4
  ✔ Base words     : 14
  ✔ Raw combos     : 2827
  ✔ After filter   : 1734
  ✔ Wordlist saved to: output/wordlist.txt

# Step 5 — Inspect results
passforge> wordlist stats
passforge> show wordlist

# Step 6 — Download wordlist
passforge> download target_wordlist

# Step 7 — Check a password
passforge> check password
passforge> check strength

# Step 8 — Exit (all temp files deleted automatically)
passforge> exit
```

---

## License

This project is licensed under the **GNU General Public License v3.0**.
See the [LICENSE](LICENSE) file for details.

---

## Contributing

Pull requests are welcome. For major changes please open an issue first to discuss what you would like to change.

---

*PassForge — Built for the security community. Use responsibly.*
