import json
import logging
import sys
from genshin_impact import check_for_updates

logger = logging.getLogger(__name__)

# [LOGIC BLOCK] Try/Except for Genshin Impact Library Imports
# This attempts to import all necessary data retrieval functions from the external 'genshin_impact' library.
# If the library is not installed or accessible, it prints an error message and terminates the script.
try:
    from genshin_impact import (get_character_data, get_all_characters_data, find_characters_by_material, find_characters_by_element, find_characters_by_weapon_type,
    get_talent_materials, get_ascension_data, get_ascension_levels)
except ImportError:
    print("❌ Error: `genshin_impact` not found. Please ensure it's installed and accessible.")
    # Exit gracefully if the core library is missing
    sys.exit(1)


# --------------------
# DATA RETRIEVAL
# --------------------

# [LOGIC BLOCK] Data Retrieval - All Characters
# This line attempts to fetch a dictionary of all characters from the library.
all_characters = get_all_characters_data()

# [LOGIC BLOCK] Data Retrieval - Single Character
# This line attempts to fetch the complete data dictionary for the character "aino" (used as a fixed test key).
data = get_character_data("aino")

# --------------------
# EXTRACTED FUNCTIONS
# --------------------

# [FUNCTION] Check for Library Updates
# This function calls the external `check_for_updates()` to check the library version against PyPI.
# It prints a message indicating if an update is available or if the current version is up-to-date.
def check_for_new_version():
    update_status = check_for_updates()
    if update_status.get("update_available"):
        print(f"✨ UPDATE AVAILABLE! {update_status['message']}")
    elif "Error" in update_status.get("message", ""):
        print(f"⚠️ Update Check Failed: {update_status['message']}")
    else:
        print(f"✅ Status: {update_status['message']}")

# [FUNCTION] Simulate Get Character Basic Fields (from /character_data)
# Extracts basic character metadata (Rarity, Element, Weapon Type, Region, Affiliation)
# from the main character data dictionary.
def get_character_data_fields(data):
    fields = {
        "Rarity": data.get('rarity'),
        "Element": data.get('element'),
        "Title": data.get("additional_titles"),
        "Weapon Type": data.get('weapon_type'),
        "Region": data.get('region'),
        "Affiliation": data.get('affiliation')
    }
    # [LOGIC BLOCK] Extract Ascension Material Links (from /character_data)
    # This block formats the Ascension Materials section with names and links for the initial display.
    if data.get('ascension_materials'):
        ascension_mats = data['ascension_materials']
        am_display = (
            f"**Gems:** [{ascension_mats.get('gems', {}).get('name', 'N/A')}]({ascension_mats.get('gems', {}).get('link', 'N/A')})\n"
            f"**Boss Mat:** [{ascension_mats.get('boss_mat', {}).get('name', 'N/A')}]({ascension_mats.get('boss_mat', {}).get('link', 'N/A')})\n"
            f"**Local Specialty:** [{ascension_mats.get('local_specialty', {}).get('name', 'N/A')}]({ascension_mats.get('local_specialty', {}).get('link', 'N/A')})\n"
            f"**Common Mat:** [{ascension_mats.get('common_mat', {}).get('name', 'N/A')}]({ascension_mats.get('common_mat', {}).get('link', 'N/A')})"
        )
        fields["Ascension Materials"] = am_display
    return fields

# [FUNCTION] Simulate Show Talents (from Show Talents Button)
# Iterates through the 'talents' list in the character data and extracts the name, type, and description for each talent.
def simulate_show_talents(data):
    talents = data.get('talents', [])
    talent_list = []
    if talents:
        for talent in talents:
            talent_list.append({
                "type": talent.get('type', 'N/A'),
                "name": talent.get('name', 'N/A'),
                "description": talent.get('description', 'No description.')
            })
    return talent_list

# [FUNCTION] Simulate Show Ascension Materials (from Show Ascension Mats Button)
# Processes the 'ascension_levels' data to group materials by the required ascension level (A1 to A6)
# and calculates the total amount of each material needed for max ascension.
def simulate_show_ascension_mats(data):
    ascension_levels_data = data.get('ascension_levels', {})
    materials_by_ascension_level = {
        "A1": [], "A2": [], "A3": [], "A4": [], "A5": [], "A6": []
    }
    total_materials = {}

    if not ascension_levels_data:
        return materials_by_ascension_level, total_materials

    for material_name, levels in ascension_levels_data.items():
        for level_key, level_info in levels.items():
            if level_key in materials_by_ascension_level:
                materials_by_ascension_level[level_key].append(
                    f"{level_info.get('amount', 'N/A')}x {material_name}"
                )
                # [LOGIC BLOCK] Accumulate Total Materials
                # This logic calculates the running total amount for each unique material.
                current_amount = level_info.get('amount', 0)
                total_materials[material_name] = total_materials.get(material_name, 0) + current_amount
                
    return materials_by_ascension_level, total_materials

# [FUNCTION] Simulate Show Stats (from Show Stats Button)
# Parses the 'stats_table' which contains base stats at various levels.
# It formats the HP, ATK, DEF, and the special Ascension Stat, handling stat ranges ('low' -> 'high').
def simulate_show_stats(data):
    stats_table_data = data.get('stats_table', {})
    stats_output = []

    if not stats_table_data:
        return stats_output
    
    ascension_stat_key = data.get('ascension_stat', '')

    for level in stats_table_data.keys():
        stats = stats_table_data[level]
        
        def format_stat(stat_data):
            # [LOGIC BLOCK] Stat Range Formatting
            # This logic checks if the stat value is a range ('low' and 'high' keys) or a single value ('high' key).
            if 'low' in stat_data and 'high' in stat_data:
                return f"{stat_data.get('low', 'N/A')} -> {stat_data.get('high', 'N/A')}"
            return stat_data.get('high', 'N/A')

        hp = format_stat(stats.get('HP', {}))
        atk = format_stat(stats.get('ATK', {}))
        defense = format_stat(stats.get('DEF', {}))
        ascension_stat = format_stat(stats.get(ascension_stat_key, {}))
        
        next_line = f"**{level}:**\n HP: {hp}\n ATK: {atk}\n DEF: {defense}"
        
        if ascension_stat != 'N/A' and ascension_stat_key:
            next_line += f"\n {ascension_stat_key}: {ascension_stat}"
        
        stats_output.append(next_line)

    return stats_output

# [FUNCTION] Simulate Show Talent Materials (from Show Talent Mats Button)
# The most complex material processing: it maps material amounts (which are provided as a string of amounts
# for all level-ups) to the correct level-up step (e.g., Level 1->2, 2->3).
def simulate_show_talent_mats(data):
    talents = data.get('talents', [])
    materials_by_level = {i: [] for i in range(1, 11)} # Level 1-10

    if not talents:
        return materials_by_level

    for talent in talents:
        level_mats_dict = talent.get('level_materials', {})
        if 'level' not in level_mats_dict:
            continue

        for mat in level_mats_dict['level']:
            material_name = mat.get('material', 'N/A')
            amount_str = str(mat.get('amount', 'N/A'))
            link = mat.get('link', None)
            
            amounts = [int(a) for a in amount_str.split('-') if a.isdigit()]
            mat_display = f"[{amount_str}x {material_name}]({link})" if link else f"{amount_str}x {material_name}"

            # [LOGIC BLOCK] Crown of Insight Mapping
            # Crown is only used for the final level-up (Level 9 -> 10).
            if "Crown of Insight" in material_name:
                materials_by_level[9].append(f"- {mat_display}")
                continue

            # [LOGIC BLOCK] Weekly Boss Material Mapping
            # Weekly boss materials are assumed to be needed for levels 6->7, 7->8, 8->9, 9->10 (4 steps).
            elif len(amounts) == 4:
                start_level = 6
                for i, amount in enumerate(amounts):
                    if amount > 0:
                        mat_display = f"[{amount}x {material_name}]({link})" if link else f"{amount}x {material_name}"
                        materials_by_level[start_level + i].append(f"- {mat_display}")
            
            # [LOGIC BLOCK] Standard Talent Material Mapping
            # Standard materials are used for all levels from 1->2 up to the maximum level in the list (e.g., levels 1->9).
            else:
                for i, amount in enumerate(amounts):
                    if amount > 0:
                        mat_display = f"[{amount}x {material_name}]({link})" if link else f"{amount}x {material_name}"
                        materials_by_level[i + 1].append(f"- {mat_display}")
    
    return materials_by_level

# [FUNCTION] Simulate Show Constellations (from Show Constellations Button)
# Extracts the name and description for each constellation (C1 to C6).
def simulate_show_constellations(data):
    constellations = data.get('constellations', [])
    constellation_list = []
    if constellations:
        for constellation in constellations:
            constellation_list.append({
                "name": constellation.get('name', 'N/A'),
                "description": constellation.get('description', 'No description.')
            })
    return constellation_list

# [FUNCTION] Simulate Find Characters Command (/find_characters)
# Calls the appropriate external search function (by material, element, or weapon) based on 'search_type'.
# It then formats the list of resulting characters into a display string.
def simulate_find_characters(search_type, query):
    results = []
    title = f"Characters for search type: {search_type}"
    
    if search_type == "material":
        results = find_characters_by_material(query)
        title = f"Characters using material: `{query}`"
        # [LOGIC BLOCK] Material Search Result Formatting
        # Formats the material search results to include character name, material type, and total amount.
        result_text = "\n".join([
            f"**{item['character']}** ({item['material_type'].capitalize()} Mat) - **Total: {item['amount']}**"
            for item in results
        ])
    elif search_type == "element":
        results = find_characters_by_element(query)
        title = f"Characters with element: `{query}`"
        result_text = "\n".join([f"• {name}" for name in results])
    elif search_type == "weapon":
        results = find_characters_by_weapon_type(query)
        title = f"Characters using weapon: `{query}`"
        result_text = "\n".join([f"• {name}" for name in results])
    else:
        return "Invalid search type", ""

    if not results:
        return f"❌ No characters found for `{search_type}` with query: `{query}`.", ""
            
    return title, result_text


def test_exposed_talent_method(char_name, opt="all"):
    # This must RETURN the value so 'ps' isn't None
    return get_talent_materials(char_name, opt)


# [FUNCTION] Simulate Character Autocomplete (from /character_data autocomplete)
# Filters the full list of character data to find characters matching the 'current_input' string
# in either their full name or their known nicknames. Returns up to 25 matches.
def simulate_character_autocomplete(all_characters, current_input):
    choices = []
    
    for char_key, char_data in all_characters.items():
        full_name = char_data.get('name', '').lower()
        
        # [LOGIC BLOCK] Autocomplete Filtering
        # Checks if the input is a substring of the character's name OR any of their nicknames (case-insensitive).
        if current_input.lower() in full_name or any(current_input.lower() in n.lower() for n in char_data.get('nicknames', [])):
            # In a real discord bot, this returns a choice object. Here we return a tuple (display_name, value_key)
            choices.append((char_data['name'], char_key))

    return choices[:25]


# --------------------
# INTERACTIVE MENU
# --------------------

# [FUNCTION] Print Menu
# Displays the list of available data simulations to the user in the terminal.
def print_menu():
    print("\n--- Genshin Data Simulator Menu ---")
    print("Default Character for 1-6: Aino | 10-13: Albedo")
    print(" 1: Character Data Fields (Basic Info)")
    print(" 2: Show Talents")
    print(" 3: Show Ascension Materials (by level & total)")
    print(" 4: Show Stats (Base Stats Table)")
    print(" 5: Show Talent Materials (by level-up step)")
    print(" 6: Show Constellations")
    print(" 7: Find Characters by Element (Test: 'Pyro')")
    print(" 8: Find Characters by Material (Test: 'Vajrada Amethyst Sliver')")
    print(" 9: Autocomplete Check (Test: 'al')")
    print("--- Talent Methods ---")
    print("10: Talent: Full Formatted (all)")
    print("11: Talent: Plain Text (alltext)")
    print("12: Talent: Specific Index (0-8)")
    print("13: Talent: Raw Data (allraw)")
    print("--- Ascension Methods ---")
    print("14: Ascension: Full Formatted (all)")
    print("15: Ascension: Specific Index (0-7)")
    print("16: Ascension: Raw Data (allraw)")
    print("17: Ascension: Level Ranges")
    print(" 0: Exit")
    print("-----------------------------------")

# [FUNCTION] Main Menu Loop
# Handles user input and calls the corresponding simulation function based on the choice.
def main_menu():
    # 'data' and 'all_characters' are loaded globally from the data retrieval block
    
    while True:
        print_menu()
        choice = input("Enter your choice (0-17): ").strip()
        
        try:
            if choice == '1':
                # [FUNCTION CALL] Get Character Data Fields
                fields = get_character_data_fields(data)
                print(f"\nCharacter Basic Fields:\n{json.dumps(fields, indent=2)}")
            
            elif choice == '2':
                # [FUNCTION CALL] Simulate Show Talents
                talents = simulate_show_talents(data)
                print(f"\nTalent Data:\n{json.dumps(talents, indent=2)}")

            elif choice == '3':
                # [FUNCTION CALL] Simulate Show Ascension Materials
                levels, total = simulate_show_ascension_mats(data)
                print(f"\nAscension Materials by Level:\n{json.dumps({k: v for k, v in levels.items() if v}, indent=2)}")
                print(f"\nTOTAL Materials Needed:\n{json.dumps(total, indent=2)}")

            elif choice == '4':
                # [FUNCTION CALL] Simulate Show Stats
                stats_output = simulate_show_stats(data)
                print("\nBase Stats by Level:")
                for stat in stats_output:
                    print(stat)

            elif choice == '5':
                # [FUNCTION CALL] Simulate Show Talent Materials
                talent_mats = simulate_show_talent_mats(data)
                print(f"\nTalent Material Data (Levels 1->10):\n{json.dumps({k: v for k, v in talent_mats.items() if v}, indent=2)}")

            elif choice == '6':
                # [FUNCTION CALL] Simulate Show Constellations
                constellations = simulate_show_constellations(data)
                print(f"\nConstellation Data:\n{json.dumps(constellations, indent=2)}")
            
            elif choice == '7':
                # [FUNCTION CALL] Simulate Find Characters (Element)
                find_title, find_results = simulate_find_characters("element", "Pyro")
                print(f"\nFind Characters Test:\nTitle: {find_title}\nResults:\n{find_results}")

            elif choice == '8':
                # [FUNCTION CALL] Simulate Find Characters (Material)
                # Using an example common material
                find_title, find_results = simulate_find_characters("material", "Vajrada Amethyst Sliver")
                print(f"\nFind Characters Test:\nTitle: {find_title}\nResults:\n{find_results}")

            elif choice == '9':
                # [FUNCTION CALL] Simulate Character Autocomplete
                autocomplete_results = simulate_character_autocomplete(all_characters, "al")
                print(f"\nAutocomplete Results for 'al':\n{json.dumps(autocomplete_results, indent=2)}")

            elif choice == "10":
                name = input("Enter character name [Albedo]: ") or "Albedo"
                res = test_exposed_talent_method(name, "all")
                print(f"\n--- {name} Talent (Formatted) ---\n{res}")
            elif choice == "11":
                name = input("Enter character name [Albedo]: ") or "Albedo"
                res = test_exposed_talent_method(name, "alltext")
                print(f"\n--- {name} Talent (Plain Text) ---\n{res}")
            elif choice == "12":
                name = input("Enter character name [Albedo]: ") or "Albedo"
                idx = input("Enter Level Index (0: 1>2, 8: 9>10): ")
                res = test_exposed_talent_method(name, idx)
                print(f"\n--- {name} Index {idx} ---\n{res}")
            elif choice == "13":
                name = input("Enter character name [Albedo]: ") or "Albedo"
                res = test_exposed_talent_method(name, "allraw")
                print(f"\n--- {name} Raw Dict ---\n{json.dumps(res, indent=2)}")
                # --- Add these to the menu choices in LibTest.py ---

            elif choice == "14":
                # Test the new Ascension Method with Level 100 support
                name = input("Enter character name [aino]: ") or "aino"
                res = get_ascension_data(name, "all")
                print(f"\n--- {name} Ascension (Full Formatted) ---\n{res}")
                
            elif choice == "15":
                # Test individual index retrieval (e.g., Level 95->100 is index 7 for Aino)
                name = input("Enter character name [aino]: ") or "aino"
                idx = input("Enter Ascension Index (0: A1, 6: A6-C7, 7: A6-C8): ") or "7"
                res = get_ascension_data(name, idx)
                print(f"\n--- {name} Ascension Index {idx} ---\n{res}")

            elif choice == "16":
                # Test Raw Data output for programmatic use
                name = input("Enter character name [aino]: ") or "aino"
                res = get_ascension_data(name, "allraw")
                print(f"\n--- {name} Ascension Raw JSON ---\n{json.dumps(res, indent=2)}")
            elif choice == "17":
                name = input("Enter character name [aino]: ") or "aino"
                res = get_ascension_levels(name, "all")
                print(f"\n--- {name} Ascension Levels ---\n{res}")
            elif choice == "0":
                print("Exiting. Goodbye!")
                break
            else:
                print("Invalid choice. Please enter a number from 0 to 17.")
        
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")

if __name__ == '__main__':
    # [LOGIC BLOCK] Check Library Version on Start
    # Runs an update check when the script first starts.
    check_for_new_version()
    main_menu()