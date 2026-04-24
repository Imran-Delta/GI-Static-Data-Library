#!/usr/bin/env python3
"""
Genshin Impact Library Interactive Test (Overhauled)
-----------------------------------------------------
Allows side-by-side testing of legacy (monolithic dict) and SQL-backed functions.
Data entry is fully interactive – no hardcoded names.
"""

import json
import logging
import sys
from typing import Optional

# ----------------------------------------------------------------------
# Try to import the library
# ----------------------------------------------------------------------
try:
    from genshin_impact import (
        check_for_updates,
        get_character_data,
        get_all_characters_data,
        find_characters_by_material,
        find_characters_by_element,
        find_characters_by_weapon_type,
        get_talent_materials,
        get_ascension_data,
        get_ascension_levels,
        get_ascension_stats,
        get_passive_talents,
        get_constellations,
        get_character_summary,
        get_all_character_names,
        get_all_material_names,
        find_characters_by_criteria,  # SQL multi‑filter
    )
    # SQL‑specific functions (not in the main __init__ yet)
    from genshin_impact.gisl import (
        find_characters_by_material_sql,
        find_characters_by_element_sql,
        find_characters_by_weapon_type_sql,
        get_character_data_sql,
    )
    library_available = True
except ImportError as e:
    print(f"❌ FATAL: {e}")
    library_available = False
    sys.exit(1)

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Pretty printing helpers
# ----------------------------------------------------------------------
def print_title(text: str):
    print(f"\n{'=' * 60}\n  {text}\n{'=' * 60}")

def print_json(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))

def print_list(items, prefix="• "):
    for item in items:
        print(f"{prefix}{item}")


# ----------------------------------------------------------------------
# Utility: check for updates (called at startup)
# ----------------------------------------------------------------------
def show_update_status():
    status = check_for_updates()
    msg = status.get("message", "Unknown")
    match status.get("status"):
        case "update":
            print(f"✨ UPDATE AVAILABLE: {msg}")
        case "outdated_dev":
            print(f"⚠️ DEV BUILD OUTDATED: {msg}")
        case "dev":
            print(f"🛠️ DEVELOPMENT MODE: {msg}")
        case "ok":
            print(f"✅ {msg}")
        case _:
            print(f"⚠️ UPDATE CHECK FAILED: {msg}")


# ----------------------------------------------------------------------
# Interactive data retrieval
# ----------------------------------------------------------------------
def prompt_character(default="aino") -> str:
    """Ask for a character key (lowercase) with a default."""
    name = input(f"Character key (default: {default}): ").strip()
    return name if name else default

def prompt_query(label: str) -> str:
    """Ask for a search query string."""
    return input(f"Enter {label}: ").strip()

def get_character_data_fn(use_sql: bool, key: str):
    if use_sql:
        return get_character_data_sql(key)
    return get_character_data(key)


# ----------------------------------------------------------------------
# Menu actions
# ----------------------------------------------------------------------
def action_character_data(use_sql: bool):
    key = prompt_character()
    data = get_character_data_fn(use_sql, key)
    if not data:
        print(f"❌ Character '{key}' not found.")
        return
    print_title(f"Character Data for {data.get('name', key)} {'(SQL)' if use_sql else '(Legacy)'}")
    print_json(data)

def action_show_talents(use_sql: bool):
    key = prompt_character()
    data = get_character_data_fn(use_sql, key)
    if not data:
        print(f"❌ Character '{key}' not found.")
        return
    talents = data.get('talents', [])
    if not talents:
        print("No talent data.")
        return
    print_title(f"Talents for {data.get('name', key)}")
    for t in talents:
        print(f"\n[{t.get('type', '?')}] {t.get('name', '?')}")
        print(f"  {t.get('description', 'No description.')}")

def action_ascension_mats(use_sql: bool):
    key = prompt_character()
    data = get_character_data_fn(use_sql, key)
    if not data:
        print(f"❌ Character '{key}' not found.")
        return
    levels = data.get('ascension_levels', {})
    if not levels:
        print("No ascension data.")
        return
    mats_by_level = {f"A{i}": [] for i in range(1,7)}
    totals = {}
    for mat_name, lvls in levels.items():
        for lvl_key, info in lvls.items():
            if lvl_key in mats_by_level:
                mats_by_level[lvl_key].append(f"{info.get('amount')}x {mat_name} ({info.get('level_range')})")
                totals[mat_name] = totals.get(mat_name, 0) + info.get('amount', 0)
    print_title(f"Ascension Materials for {data.get('name', key)}")
    for lvl in [f"A{i}" for i in range(1,7)]:
        if mats_by_level[lvl]:
            print(f"\n{lvl}:")
            print_list(mats_by_level[lvl])
    print("\nTOTAL NEEDED:")
    for name, count in totals.items():
        print(f"  {count}x {name}")

def action_stats(use_sql: bool):
    key = prompt_character()
    data = get_character_data_fn(use_sql, key)
    if not data:
        print(f"❌ Character '{key}' not found.")
        return
    stats_table = data.get('stats_table', {})
    asc_stat = data.get('ascension_stat', '')
    if not stats_table:
        print("No stats data.")
        return
    print_title(f"Base Stats for {data.get('name', key)}")
    for tier, st in stats_table.items():
        line = f"{tier} ({st.get('level_range','')}): "
        for stat_name in ['HP','ATK','DEF',asc_stat]:
            if stat_name in st:
                val = st[stat_name]
                if isinstance(val, dict):
                    line += f"{stat_name}: {val.get('low','?')}→{val.get('high','?')}  "
                else:
                    line += f"{stat_name}: {val}  "
        print(line)

def action_talent_mats(use_sql: bool):
    key = prompt_character()
    # get_talent_materials is legacy-only, but works on data fetched either way
    result = get_talent_materials(key, "all")
    print_title(f"Talent Materials for {key.title()}")
    print(result)

def action_constellations(use_sql: bool):
    key = prompt_character()
    data = get_character_data_fn(use_sql, key)
    if not data:
        print(f"❌ Character '{key}' not found.")
        return
    consts = data.get('constellations', [])
    if not consts:
        print("No constellation data.")
        return
    print_title(f"Constellations for {data.get('name', key)}")
    for c in consts:
        print(f"\n{c.get('name','?')}")
        print(f"  {c.get('description','No description.')}")

def action_find(use_sql: bool, search_type: str):
    query = prompt_query(f"{search_type} name")
    if search_type == "element":
        if use_sql:
            results = find_characters_by_element_sql(query)
        else:
            results = find_characters_by_element(query)
    elif search_type == "weapon":
        if use_sql:
            results = find_characters_by_weapon_type_sql(query)
        else:
            results = find_characters_by_weapon_type(query)
    elif search_type == "material":
        if use_sql:
            # Returns list of dicts with character, material_type, amount
            raw = find_characters_by_material_sql(query)
            results = [f"{r['character']} ({r['material_type']}): {r['amount']}" for r in raw]
        else:
            raw = find_characters_by_material(query)
            results = [f"{r['character']} ({r['material_type']}): {r['amount']}" for r in raw]
    else:
        print("Invalid search type.")
        return
    print_title(f"{search_type.title()} search '{query}' {'[SQL]' if use_sql else '[Legacy]'}")
    if not results:
        print("No matches found.")
    else:
        print_list(results)

def action_find_multi():
    print("Leave a field blank to ignore it.")
    material = input("Material (optional): ").strip() or None
    element = input("Element (optional): ").strip() or None
    weapon = input("Weapon type (optional): ").strip() or None
    results = find_characters_by_criteria(material, element, weapon)
    print_title("Multi‑criteria search (SQL)")
    if not results:
        print("No matches found.")
    else:
        print_list(results)

def action_passive_talents():
    key = prompt_character()
    res = get_passive_talents(key, "all")
    print_title(f"Passive Talents for {key.title()}")
    print(res)

def action_constellations_index():
    key = prompt_character()
    idx = input("Constellation index (0-5): ").strip()
    try:
        res = get_constellations(key, idx)
        print_title(f"Constellation {idx} for {key.title()}")
        print(res)
    except Exception as e:
        print(f"Error: {e}")

def action_summary():
    key = prompt_character()
    res = get_character_summary(key, "all")
    print_title(f"Character Summary for {key.title()}")
    print(res)

def action_autocomplete_test():
    prefix = input("Type start of character name: ").strip()
    names = get_all_character_names()
    matches = [(k,n) for k,n in names if prefix.lower() in n.lower()]
    print_title(f"Autocomplete matches for '{prefix}'")
    for key, name in matches[:25]:
        print(f"  {name} (key: {key})")


# ----------------------------------------------------------------------
# Main menu loop
# ----------------------------------------------------------------------
def main():
    show_update_status()
    default_char = "aino"
    use_sql_default = False

    while True:
        print("\n" + "=" * 60)
        print("  Genshin Impact Library Test Suite (Overhauled)")
        print("=" * 60)
        print(f"  Default character: {default_char}")
        print("  SQL mode (for applicable ops): ", "ON" if use_sql_default else "OFF")
        print("-" * 60)
        print("  1  : Set default character key")
        print("  2  : Toggle SQL mode for data/retrieval ops")
        print("--- Character Data ---")
        print("  3  : Get Character Data (legacy)")
        print("  4  : Get Character Data (SQL)")
        print("  5  : Show Talents")
        print("  6  : Show Ascension Materials")
        print("  7  : Show Base Stats")
        print("  8  : Show Talent Materials (formatted)")
        print("  9  : Show Constellations")
        print("--- Find Characters ---")
        print("  10 : Find by Element (legacy)")
        print("  11 : Find by Element (SQL)")
        print("  12 : Find by Material (legacy)")
        print("  13 : Find by Material (SQL)")
        print("  14 : Find by Weapon (legacy)")
        print("  15 : Find by Weapon (SQL)")
        print("  16 : Find by multiple criteria (SQL)")
        print("--- New Convenience Functions ---")
        print("  17 : Passive Talents")
        print("  18 : Single Constellation (by index)")
        print("  19 : Character Summary")
        print("  20 : Autocomplete simulation")
        print("--- Other ---")
        print("  21 : Check for updates")
        print("  0  : Exit")
        print("-" * 60)
        choice = input("Enter choice: ").strip()

        try:
            # Utility toggles
            if choice == '1':
                default_char = prompt_character(default_char)
            elif choice == '2':
                use_sql_default = not use_sql_default
                print(f"SQL mode for data ops: {'ON' if use_sql_default else 'OFF'}")
            # Character data ops (use current SQL toggle)
            elif choice == '3':
                action_character_data(use_sql=False)
            elif choice == '4':
                action_character_data(use_sql=True)
            elif choice == '5':
                action_show_talents(use_sql_default)
            elif choice == '6':
                action_ascension_mats(use_sql_default)
            elif choice == '7':
                action_stats(use_sql_default)
            elif choice == '8':
                action_talent_mats(use_sql_default)  # always legacy function, but ok
            elif choice == '9':
                action_constellations(use_sql_default)
            # Find ops (separate legacy/SQL)
            elif choice == '10':
                action_find(use_sql=False, search_type="element")
            elif choice == '11':
                action_find(use_sql=True, search_type="element")
            elif choice == '12':
                action_find(use_sql=False, search_type="material")
            elif choice == '13':
                action_find(use_sql=True, search_type="material")
            elif choice == '14':
                action_find(use_sql=False, search_type="weapon")
            elif choice == '15':
                action_find(use_sql=True, search_type="weapon")
            elif choice == '16':
                action_find_multi()
            elif choice == '17':
                action_passive_talents()
            elif choice == '18':
                action_constellations_index()
            elif choice == '19':
                action_summary()
            elif choice == '20':
                action_autocomplete_test()
            elif choice == '21':
                show_update_status()
            elif choice == '0':
                print("Goodbye!")
                break
            else:
                print("Invalid choice.")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
