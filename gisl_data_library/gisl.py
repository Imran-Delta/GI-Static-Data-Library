"""
A static library for retrieving Genshin Impact character and material data.
The data is loaded from a bundled gisl_data.json file.
"""
import json
import importlib.resources as pkg_resources
import logging

# Set up logging to capture potential errors
logger = logging.getLogger(__name__)

# The 'gisl_data_library' is a hardcoded package name. This will work,
# but a more dynamic approach could be used in a larger project.
PACKAGE_NAME = 'gisl_data_library'
DATA_FILE_NAME = 'gisl_data.json'

try:
    # Use importlib.resources to access the bundled JSON file
    # This path is now correct because we've updated setup.py to include the data file.
    json_data = pkg_resources.files(PACKAGE_NAME).joinpath(DATA_FILE_NAME).read_text(encoding='utf-8')
    gisl_data = json.loads(json_data)
    logger.info("Successfully loaded gisl_data.json")
    print("GISL_DATA_LIBRARY: Data loaded successfully.")
except Exception as e:
    # This block is a failsafe. If the data file cannot be found,
    # the 'gisl_data' dictionary will be initialized as empty,
    # preventing the script from crashing.
    logger.error(f"Error loading data: {e}")
    print(f"GISL_DATA_LIBRARY: Error loading data from {DATA_FILE_NAME}: {e}")
    gisl_data = {}

def get_character_data(character_key: str) -> dict or None:
    """
    Retrieves the full data for a specific character by their key.

    Args:
        character_key: The lowercase key of the character (e.g., 'albedo').

    Returns:
        A dictionary of the character's data, or None if not found.
    """
    return gisl_data.get(character_key.lower())

def get_all_characters_data() -> dict:
    """
    Returns the full dictionary of all character data.

    Returns:
        A dictionary containing all character data.
    """
    return gisl_data

def find_characters_by_material(material_name: str) -> list:
    """
    Finds and returns a list of characters that use a given ascension or talent material.

    Args:
        material_name: The name of the material to search for (e.g., "Prithiva Topaz", "Crown of Insight").

    Returns:
        A list of dictionaries, each containing character name, material type, and total amount.
    """
    material_name = material_name.lower()
    characters_using_material = {}

    for char_key, char_data in gisl_data.items():
        # Check for ascension materials
        ascension_mats = char_data.get('ascension_materials', {})
        for mat_type, mat_info in ascension_mats.items():
            if mat_info and mat_info.get('name', '').lower() == material_name:
                total_amount = 0
                for level_info in char_data.get('ascension_levels', {}).values():
                    # Sum the amounts for the matching material
                    if mat_info['name'] in level_info:
                        total_amount += level_info[mat_info['name']]['amount']

                if char_data['name'] not in characters_using_material:
                    characters_using_material[char_data['name']] = {
                        "character": char_data['name'],
                        "material_type": "ascension",
                        "amount": total_amount
                    }
                else:
                    # Update the amount if the character is already found
                    characters_using_material[char_data['name']]['amount'] += total_amount

        # Check for talent materials
        talents = char_data.get('talents', [])
        for talent in talents:
            talent_mats = talent.get('level_materials', {}).get('level', [])
            total_amount = 0
            for mat_info in talent_mats:
                if mat_info.get('material', '').lower() == material_name:
                    amounts_str = mat_info.get('amount', '')
                    amounts = [int(a) for a in amounts_str.split('-') if a.isdigit()]
                    total_amount += sum(amounts)
            
            if total_amount > 0:
                characters_using_material[char_data['name']] = {
                    "character": char_data['name'],
                    "material_type": "talent",
                    "amount": total_amount
                }

    # Convert the dictionary values to a list and return
    return list(characters_using_material.values())

def find_characters_by_element(element_name: str) -> list:
    """
    Finds and returns a list of character names that match the given element.

    Args:
        element_name: The name of the element to search for (e.g., "Anemo", "Geo").

    Returns:
        A list of matching character names.
    """
    matching_characters = []
    for char_name, char_data in gisl_data.items():
        if 'element' in char_data and char_data['element'].lower() == element_name.lower():
            matching_characters.append(char_data['name'])
    return matching_characters

def find_characters_by_weapon_type(weapon_type: str) -> list:
    """
    Finds and returns a list of character names that match the given weapon type.

    Args:
        weapon_type: The type of weapon to search for (e.g., "Sword", "Bow").

    Returns:
        A list of matching character names.
    """
    matching_characters = []
    for char_name, char_data in gisl_data.items():
        if 'weapon_type' in char_data and char_data['weapon_type'].lower() == weapon_type.lower():
            matching_characters.append(char_data['name'])
    return matching_characters