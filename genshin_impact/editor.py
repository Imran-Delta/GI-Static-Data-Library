#!/usr/bin/env python3
"""
GISL Editor CLI

Interactive menu + optional command-line args.

Usage:
    python editor.py                # Interactive menu
    python editor.py create-yaml [keys ...]
    python editor.py flush-yaml [keys ...]
    python editor.py create-preview [--single-file] [keys ...]

The temporary directory is ./.CharTMP (created if needed).
"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Working directory (where the script is run from)
CWD = Path.cwd()
DATA_DIR = CWD / "character_data"
TMP_DIR = CWD / ".CharTMP"          # Base temp directory for YAML and Markdown

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
TMP_DIR.mkdir(exist_ok=True)

# ----------------------------------------------------------------------
# Utility functions
# ----------------------------------------------------------------------
def generate_fandom_link(name: str) -> str:
    """Generate a Fandom wiki link for a material/character name."""
    if not name:
        return ""
    slug = name.strip().replace(" ", "_")
    return f"https://genshin-impact.fandom.com/wiki/{slug}"

def save_character_json(file_path: Path, data: dict):
    """Atomically write JSON with custom low/high compacting."""
    json_string = json.dumps(data, indent=4, ensure_ascii=False)
    # Compact low/high objects to single line
    pattern = r'\{\s*\n\s*"low":\s*"(.*?)",\s*\n\s*"high":\s*"(.*?)"\s*\n\s*\}'
    compact_json = re.sub(pattern, r'{ "low": "\1", "high": "\2" }', json_string)

    fd, temp_path = tempfile.mkstemp(dir=file_path.parent, text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(compact_json)

    if file_path.exists():
        shutil.copy2(file_path, str(file_path) + ".bak")
    os.replace(temp_path, file_path)

def load_character_json(key: str) -> dict:
    """Load a character JSON from the data directory."""
    file_path = DATA_DIR / f"{key}.json"
    if not file_path.exists():
        print(f"Error: {key}.json does not exist.")
        sys.exit(1)
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# ----------------------------------------------------------------------
# YAML Export (with comments)
# ----------------------------------------------------------------------
def export_to_yaml(char_data: dict) -> str:
    """
    Convert character dict to a YAML string with explanatory comments.
    All string values are quoted for safety when editing on mobile.
    """
    lines = []
    name = char_data.get("name", "")
    first_title = char_data.get("additional_titles", [""])[0] if char_data.get("additional_titles") else ""
    lines.append(f"# Character: {name}")
    if first_title:
        lines.append(f"# Title: {first_title}")
    lines.append("# Edit this file, then run: python editor.py flush-yaml <key>")
    lines.append("")

    # Top-level scalar fields
    scalar_fields = [
        ("name", "Display name", True),
        ("rarity", "Rarity (integer)", False),
        ("element", "Element", True),
        ("weapon_type", "Weapon type", True),
        ("region", "Region", True),
        ("birthday", "Birthday", True),
        ("affiliation", "Affiliation", True),
        ("role", "Role", True),
        ("constellation_name", "Constellation name", True),
        ("ascension_stat", "Special ascension stat", True),
    ]
    for key, comment, quote in scalar_fields:
        value = char_data.get(key, "")
        if quote and isinstance(value, str):
            value_str = json.dumps(value)
        else:
            value_str = str(value)
        lines.append(f"# {comment}")
        lines.append(f"{key}: {value_str}")
        lines.append("")

    # Additional titles (list of strings)
    lines.append("# Additional titles (list)")
    lines.append("additional_titles:")
    titles = char_data.get("additional_titles", [])
    if titles:
        for t in titles:
            lines.append(f'  - "{t}"')
    else:
        lines.append("  - \"\"")
    lines.append("")

    # Ascension materials
    lines.append("# Ascension materials (base family names)")
    lines.append("ascension_materials:")
    asc_mats = char_data.get("ascension_materials", {})
    for category in ["gems", "boss_mat", "local_specialty", "common_mat"]:
        info = asc_mats.get(category, {"name": "", "link": ""})
        mat_name = info.get("name", "")
        link = info.get("link", "")
        lines.append(f"  {category}:")
        lines.append(f'    name: "{mat_name}"')
        lines.append(f'    link: "{link}"')
        lines.append("")

    # Ascension levels
    lines.append("# Ascension levels (exact tiered material names as keys)")
    lines.append("# Each key maps to a dict of phases (A1..A6)")
    lines.append("ascension_levels:")
    asc_levels = char_data.get("ascension_levels", {})
    for mat_name, phases in asc_levels.items():
        lines.append(f'  "{mat_name}":')
        for phase, details in sorted(phases.items(), key=lambda x: x[0]):
            level_range = details.get("level_range", "")
            amount = details.get("amount", 0)
            link = details.get("link", "")
            lines.append(f"    {phase}:")
            lines.append(f'      level_range: "{level_range}"')
            lines.append(f"      amount: {amount}")
            lines.append(f'      link: "{link}"')
        lines.append("")

    # Stats table
    lines.append("# Stats table (tiers A0..A6, A6-C7, A6-C8)")
    lines.append("# For each stat, low/high are strings")
    lines.append("stats_table:")
    stats_table = char_data.get("stats_table", {})
    tier_order = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A6 - C7", "A6 - C8"]
    for tier in tier_order:
        if tier not in stats_table:
            continue
        data = stats_table[tier]
        lvl_range = data.get("level_range", "")
        lines.append(f"  {tier}:")
        lines.append(f'    level_range: "{lvl_range}"')
        for stat_key, stat_val in data.items():
            if stat_key == "level_range":
                continue
            if isinstance(stat_val, dict):
                low = stat_val.get("low", "0")
                high = stat_val.get("high", "0")
                lines.append(f"    {stat_key}:")
                lines.append(f'      low: "{low}"')
                lines.append(f'      high: "{high}"')
            else:
                lines.append(f'    {stat_key}: "{stat_val}"')
        lines.append("")

    # Talents
    lines.append("# Talents (list)")
    lines.append("# For active talents, level_materials is a dict with a 'level' list.")
    lines.append("# For passive talents, level_materials is a string (unlock condition).")
    lines.append("talents:")
    talents = char_data.get("talents", [])
    for i, talent in enumerate(talents):
        name = talent.get("name", "")
        type_ = talent.get("type", "")
        desc = talent.get("description", "")
        lines.append(f"  - name: \"{name}\"")
        lines.append(f"    type: \"{type_}\"")
        lines.append(f"    description: \"{desc}\"")
        lm = talent.get("level_materials")
        if isinstance(lm, dict):
            lines.append("    level_materials:")
            level_list = lm.get("level", [])
            if level_list:
                lines.append("      level:")
                for entry in level_list:
                    mat = entry.get("material", "")
                    amount = entry.get("amount", "")
                    link = entry.get("link", "")
                    lines.append(f'        - material: "{mat}"')
                    lines.append(f'          amount: "{amount}"')
                    lines.append(f'          link: "{link}"')
            else:
                lines.append("      level: []")
        elif isinstance(lm, str):
            lines.append(f'    level_materials: "{lm}"')
        else:
            lines.append("    level_materials: null")
        lines.append("")

    # Constellations
    lines.append("# Constellations (list)")
    lines.append("constellations:")
    constellations = char_data.get("constellations", [])
    for const in constellations:
        name = const.get("name", "")
        desc = const.get("description", "")
        lines.append(f'  - name: "{name}"')
        lines.append(f'    description: "{desc}"')
        lines.append("")

    return "\n".join(lines)

# ----------------------------------------------------------------------
# YAML Import and Validation
# ----------------------------------------------------------------------
try:
    import yaml
except ImportError:
    print("PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

def validate_data(data: dict, key: str) -> list:
    """Validate character data. Return list of error messages."""
    errors = []
    required = [
        "name", "rarity", "element", "weapon_type", "region", "birthday",
        "affiliation", "role", "additional_titles", "constellation_name",
        "ascension_stat", "ascension_materials", "ascension_levels",
        "stats_table", "talents", "constellations"
    ]
    for req in required:
        if req not in data:
            errors.append(f"Missing top-level key: {req}")

    # Type checks
    if "rarity" in data and not isinstance(data["rarity"], int):
        errors.append("rarity must be an integer")
    if "additional_titles" in data and not isinstance(data["additional_titles"], list):
        errors.append("additional_titles must be a list")
    if "talents" in data and not isinstance(data["talents"], list):
        errors.append("talents must be a list")
    if "constellations" in data and not isinstance(data["constellations"], list):
        errors.append("constellations must be a list")
    if "ascension_levels" in data and not isinstance(data["ascension_levels"], dict):
        errors.append("ascension_levels must be a dict")
    if "stats_table" in data and not isinstance(data["stats_table"], dict):
        errors.append("stats_table must be a dict")

    # Ascension levels structure
    if "ascension_levels" in data and isinstance(data["ascension_levels"], dict):
        for mat_name, phases in data["ascension_levels"].items():
            if not isinstance(phases, dict):
                errors.append(f"ascension_levels['{mat_name}'] must be a dict")
                continue
            for phase, details in phases.items():
                if not isinstance(details, dict):
                    errors.append(f"ascension_levels['{mat_name}']['{phase}'] must be a dict")
                    continue
                if "level_range" not in details or "amount" not in details or "link" not in details:
                    errors.append(f"ascension_levels['{mat_name}']['{phase}'] missing required keys")

    # Stats table structure
    if "stats_table" in data and isinstance(data["stats_table"], dict):
        required_tiers = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A6 - C7", "A6 - C8"]
        for tier in required_tiers:
            if tier not in data["stats_table"]:
                errors.append(f"Missing tier in stats_table: {tier}")
                continue
            tier_data = data["stats_table"][tier]
            if not isinstance(tier_data, dict):
                errors.append(f"stats_table['{tier}'] must be a dict")
                continue
            if "level_range" not in tier_data:
                errors.append(f"stats_table['{tier}'] missing 'level_range'")
            stat_keys = set(tier_data.keys()) - {"level_range"}
            if not stat_keys:
                errors.append(f"stats_table['{tier}'] has no stat keys")
            for sk in stat_keys:
                val = tier_data[sk]
                if not isinstance(val, dict):
                    errors.append(f"stats_table['{tier}']['{sk}'] should be a dict")
                    continue
                if "low" not in val or "high" not in val:
                    errors.append(f"stats_table['{tier}']['{sk}'] missing low/high")

    # Talents
    if "talents" in data and isinstance(data["talents"], list):
        for i, talent in enumerate(data["talents"]):
            if not isinstance(talent, dict):
                errors.append(f"talents[{i}] must be a dict")
                continue
            if "name" not in talent or "type" not in talent:
                errors.append(f"talents[{i}] missing name or type")
            lm = talent.get("level_materials")
            if lm is not None and not isinstance(lm, (dict, str)):
                errors.append(f"talents[{i}].level_materials must be dict or string")
            if isinstance(lm, dict) and "level" in lm:
                if not isinstance(lm["level"], list):
                    errors.append(f"talents[{i}].level_materials.level must be a list")
                else:
                    for j, entry in enumerate(lm["level"]):
                        if not isinstance(entry, dict):
                            errors.append(f"talents[{i}].level[{j}] must be dict")
                            continue
                        if "material" not in entry or "amount" not in entry or "link" not in entry:
                            errors.append(f"talents[{i}].level[{j}] missing keys")

    # Constellations
    if "constellations" in data and isinstance(data["constellations"], list):
        for i, const in enumerate(data["constellations"]):
            if not isinstance(const, dict):
                errors.append(f"constellations[{i}] must be a dict")
                continue
            if "name" not in const or "description" not in const:
                errors.append(f"constellations[{i}] missing name or description")

    return errors

def flush_yaml_to_json(key: str):
    """Read YAML edit file for key, validate, and write JSON."""
    yaml_file = TMP_DIR / f"{key}.yaml"
    if not yaml_file.exists():
        print(f"Error: {yaml_file} does not exist.")
        return

    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error parsing YAML: {e}")
        return

    errors = validate_data(data, key)
    if errors:
        print(f"Validation errors for {key}:")
        for err in errors:
            print(f"  - {err}")
        print("Not saving JSON. Fix the YAML and retry.")
        return

    json_path = DATA_DIR / f"{key}.json"
    save_character_json(json_path, data)
    print(f"Saved {json_path}")

# ----------------------------------------------------------------------
# Markdown Preview
# ----------------------------------------------------------------------
def format_amount_string(amounts) -> str:
    if isinstance(amounts, list):
        return ", ".join(str(a) for a in amounts)
    return str(amounts)

def format_material_phases(mat_name: str, material_data: dict) -> str:
    lines = [f"### {mat_name}"]
    for phase, details in sorted(material_data.items(), key=lambda x: x[0]):
        if isinstance(details, dict):
            lvl_range = details.get("level_range", "")
            amount = details.get("amount", 0)
            link = details.get("link", "")
            lines.append(f"- **{phase}** ({lvl_range}): amount {amount} [link]({link})")
        else:
            lines.append(f"- **{phase}**: {details}")
    return "\n".join(lines)

def format_stats_table_md(stats_table: dict) -> str:
    if not stats_table:
        return "No stats table found.\n"
    sample = next(iter(stats_table.values()))
    stat_keys = [k for k in sample.keys() if k != "level_range"]
    header = "| Tier | Level Range | " + " | ".join(stat_keys) + " |\n"
    separator = "|------|--------------|" + "|".join(["---"] * len(stat_keys)) + "|\n"
    lines = [header, separator]
    tier_order = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A6 - C7", "A6 - C8"]
    tiers = sorted(stats_table.keys(), key=lambda x: (tier_order.index(x) if x in tier_order else 99, x))
    for tier in tiers:
        data = stats_table[tier]
        lvl_range = data.get("level_range", "")
        row = [tier, lvl_range]
        for sk in stat_keys:
            val = data.get(sk, {})
            if isinstance(val, dict):
                row.append(f"{val.get('low', '0')} - {val.get('high', '0')}")
            else:
                row.append(str(val))
        lines.append("| " + " | ".join(row) + " |\n")
    return "".join(lines)

def format_talents_md(talents: list) -> str:
    lines = []
    for i, talent in enumerate(talents, 1):
        name = talent.get("name", f"Talent {i}")
        type_ = talent.get("type", "")
        desc = talent.get("description", "")
        lines.append(f"## Talent {i}: {name}")
        lines.append(f"**Type:** {type_}")
        if desc:
            lines.append(f"**Description:** {desc}")
        lm = talent.get("level_materials")
        if isinstance(lm, dict):
            level_list = lm.get("level", [])
            if level_list:
                lines.append("**Upgrade Materials:**")
                for entry in level_list:
                    mat = entry.get("material", "?")
                    amounts = entry.get("amount", "")
                    link = entry.get("link", "")
                    lines.append(f"- {mat}: {format_amount_string(amounts)} [link]({link})")
            else:
                lines.append("No material data.")
        elif lm:  # string
            lines.append(f"**Unlock condition:** {lm}")
        lines.append("")
    return "\n".join(lines)

def format_constellations_md(constellations: list) -> str:
    lines = []
    for i, const in enumerate(constellations, 1):
        name = const.get("name", f"C{i}")
        desc = const.get("description", "")
        lines.append(f"## Constellation {i}: {name}")
        if desc:
            lines.append(f"**Description:** {desc}")
        lines.append("")
    return "\n".join(lines)

def generate_character_md(char_data: dict) -> str:
    name = char_data.get("name", "Unknown")
    first_title = char_data.get("additional_titles", [""])[0] if char_data.get("additional_titles") else ""
    element = char_data.get("element", "?")
    weapon = char_data.get("weapon_type", "?")
    region = char_data.get("region", "?")
    rarity = char_data.get("rarity", "?")
    birthday = char_data.get("birthday", "?")
    affiliation = char_data.get("affiliation", "?")
    role = char_data.get("role", "?")
    constellation_name = char_data.get("constellation_name", "?")
    ascension_stat = char_data.get("ascension_stat", "?")

    md = []
    md.append(f"# {name}")
    if first_title:
        md.append(f"*{first_title}*")
    md.append("")
    md.append(f"- **Element:** {element}")
    md.append(f"- **Weapon:** {weapon}")
    md.append(f"- **Region:** {region}")
    md.append(f"- **Rarity:** {rarity}")
    md.append(f"- **Birthday:** {birthday}")
    md.append(f"- **Affiliation:** {affiliation}")
    md.append(f"- **Role:** {role}")
    md.append(f"- **Constellation Name:** {constellation_name}")
    md.append(f"- **Special Ascension Stat:** {ascension_stat}")
    md.append("")

    md.append("## Ascension Materials")
    asc_mats = char_data.get("ascension_materials", {})
    for category, info in asc_mats.items():
        if isinstance(info, dict):
            mat_name = info.get("name", "")
            link = info.get("link", "")
            md.append(f"- **{category}:** {mat_name} [link]({link})")
    md.append("")

    md.append("## Ascension Levels")
    asc_levels = char_data.get("ascension_levels", {})
    for mat_name, phases in asc_levels.items():
        md.append(format_material_phases(mat_name, phases))
        md.append("")

    md.append("## Stats Table")
    md.append(format_stats_table_md(char_data.get("stats_table", {})))
    md.append("")

    md.append("## Talents")
    md.append(format_talents_md(char_data.get("talents", [])))
    md.append("")

    md.append("## Constellations")
    md.append(format_constellations_md(char_data.get("constellations", [])))
    md.append("")

    return "\n".join(md)

# ----------------------------------------------------------------------
# Helper: list character keys and YAML keys
# ----------------------------------------------------------------------
def get_character_keys():
    """Return sorted list of character keys (filenames without .json)."""
    if not DATA_DIR.exists():
        return []
    return sorted(p.stem for p in DATA_DIR.glob("*.json"))

def get_yaml_keys():
    """Return sorted list of YAML edit files (stem only)."""
    if not TMP_DIR.exists():
        return []
    return sorted(p.stem for p in TMP_DIR.glob("*.yaml"))

def select_keys(all_keys, prompt, allow_all=True):
    """
    Interactive selection.
    Shows numbered list, asks for comma-separated numbers or 'all'.
    Returns list of selected keys.
    """
    if not all_keys:
        print("No items available.")
        return []
    print("\nAvailable items:")
    for i, key in enumerate(all_keys, 1):
        print(f"  {i:3}. {key}")
    print("  Enter 'all' for all, or comma-separated numbers (e.g., 1,3,5)")
    choice = input(prompt).strip()
    if choice.lower() == 'all' and allow_all:
        return all_keys
    if not choice:
        return []
    try:
        nums = [int(x.strip()) for x in choice.split(',') if x.strip()]
        selected = []
        for n in nums:
            if 1 <= n <= len(all_keys):
                selected.append(all_keys[n-1])
        return selected
    except ValueError:
        print("Invalid input. No selection made.")
        return []

# ----------------------------------------------------------------------
# Interactive Menu
# ----------------------------------------------------------------------
def interactive_menu():
    while True:
        print("\n" + "="*50)
        print("  GISL EDITOR - INTERACTIVE MENU")
        print("="*50)
        print("  1. Create YAML edit files from JSON")
        print("  2. Flush YAML edits back to JSON")
        print("  3. Generate Markdown previews")
        print("  4. Exit")
        print("-"*50)
        choice = input("Select an option: ").strip()

        if choice == '1':
            keys = get_character_keys()
            selected = select_keys(keys, "Enter characters to export (or 'all'): ", allow_all=True)
            if selected:
                for key in selected:
                    json_path = DATA_DIR / f"{key}.json"
                    if json_path.exists():
                        with open(json_path, 'r', encoding='utf-8') as f:
                            char_data = json.load(f)
                        yaml_content = export_to_yaml(char_data)
                        yaml_path = TMP_DIR / f"{key}.yaml"
                        with open(yaml_path, 'w', encoding='utf-8') as f:
                            f.write(yaml_content)
                        print(f"Exported {key}.yaml")
                    else:
                        print(f"Warning: {key}.json not found.")
            else:
                print("No characters selected.")

        elif choice == '2':
            yaml_keys = get_yaml_keys()
            selected = select_keys(yaml_keys, "Enter YAML files to flush (or 'all'): ", allow_all=True)
            if selected:
                for key in selected:
                    flush_yaml_to_json(key)
            else:
                print("No YAML files selected.")

        elif choice == '3':
            keys = get_character_keys()
            selected = select_keys(keys, "Enter characters to preview (or 'all'): ", allow_all=True)
            if selected:
                single = input("Combine all into a single Markdown file? (y/n): ").strip().lower() == 'y'
                if single:
                    combined_md = ["# Character Data Preview\n"]
                    for key in selected:
                        json_path = DATA_DIR / f"{key}.json"
                        if json_path.exists():
                            with open(json_path, 'r', encoding='utf-8') as f:
                                char_data = json.load(f)
                            combined_md.append(f"<a name='{key}'></a>\n")
                            combined_md.append(generate_character_md(char_data))
                            combined_md.append("\n---\n")
                    out_file = TMP_DIR / "all_characters.md"
                    with open(out_file, 'w', encoding='utf-8') as f:
                        f.write("\n".join(combined_md))
                    print(f"Wrote combined preview to {out_file}")
                else:
                    for key in selected:
                        json_path = DATA_DIR / f"{key}.json"
                        if json_path.exists():
                            with open(json_path, 'r', encoding='utf-8') as f:
                                char_data = json.load(f)
                            md_content = generate_character_md(char_data)
                            out_file = TMP_DIR / f"{key}.md"
                            with open(out_file, 'w', encoding='utf-8') as f:
                                f.write(md_content)
                            print(f"Wrote {out_file}")
            else:
                print("No characters selected.")

        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

# ----------------------------------------------------------------------
# Command-line handlers (fallback)
# ----------------------------------------------------------------------
def cmd_create_yaml(args):
    keys = args.keys
    if not keys:
        keys = get_character_keys()
    if not keys:
        print("No character JSON files found.")
        return
    for key in keys:
        json_path = DATA_DIR / f"{key}.json"
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                char_data = json.load(f)
            yaml_content = export_to_yaml(char_data)
            yaml_path = TMP_DIR / f"{key}.yaml"
            with open(yaml_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            print(f"Exported {key}.yaml")
        else:
            print(f"Warning: {key}.json not found.")

def cmd_flush_yaml(args):
    keys = args.keys
    if not keys:
        keys = get_yaml_keys()
    if not keys:
        print("No YAML edit files found.")
        return
    for key in keys:
        flush_yaml_to_json(key)

def cmd_create_preview(args):
    keys = args.keys
    if not keys:
        keys = get_character_keys()
    if not keys:
        print("No character JSON files found.")
        return
    if args.single_file:
        combined_md = ["# Character Data Preview\n"]
        for key in keys:
            json_path = DATA_DIR / f"{key}.json"
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    char_data = json.load(f)
                combined_md.append(f"<a name='{key}'></a>\n")
                combined_md.append(generate_character_md(char_data))
                combined_md.append("\n---\n")
        out_file = TMP_DIR / "all_characters.md"
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(combined_md))
        print(f"Wrote combined preview to {out_file}")
    else:
        for key in keys:
            json_path = DATA_DIR / f"{key}.json"
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    char_data = json.load(f)
                md_content = generate_character_md(char_data)
                out_file = TMP_DIR / f"{key}.md"
                with open(out_file, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                print(f"Wrote {out_file}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="GISL Editor CLI")
    subparsers = parser.add_subparsers(dest="command", required=False)

    # create-yaml
    p_create = subparsers.add_parser("create-yaml", help="Export JSON to YAML edit files")
    p_create.add_argument("keys", nargs="*", help="Character keys (default: all)")

    # flush-yaml
    p_flush = subparsers.add_parser("flush-yaml", help="Apply YAML edits back to JSON")
    p_flush.add_argument("keys", nargs="*", help="Character keys (default: all)")

    # create-preview
    p_preview = subparsers.add_parser("create-preview", help="Generate Markdown previews")
    p_preview.add_argument("keys", nargs="*", help="Character keys (default: all)")
    p_preview.add_argument("--single-file", action="store_true", help="Combine all into one Markdown file")

    args = parser.parse_args()

    if args.command == "create-yaml":
        cmd_create_yaml(args)
    elif args.command == "flush-yaml":
        cmd_flush_yaml(args)
    elif args.command == "create-preview":
        cmd_create_preview(args)
    else:
        # No command or unknown? Show interactive menu
        interactive_menu()

if __name__ == "__main__":
    main()

