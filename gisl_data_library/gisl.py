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
except Exception as e:
    # This block is a failsafe. If the data file cannot be found,
    # the 'gisl_data' dictionary will be initialized as empty,
    # preventing the script from crashing.
    logger.error(f"Error loading data: {e}")
    gisl_data = {}

# --- New function to get character data ---
def get_character_data(character_name: str) -> dict:
    """
    Finds and returns the full data dictionary for a given character.

    Args:
        character_name: The name of the character to search for.

    Returns:
        The dictionary containing the character's full data, or an empty dictionary if not found.
    """
    logger.info(f"Attempting to retrieve data for character: {character_name}")
    data = gisl_data.get(character_name.lower(), {})
    if not data:
        logger.warning(f"No data found for character: {character_name}")
    else:
        logger.info(f"Data found for character: {character_name}")
    return data

# Helper function to calculate the total amount of an ascension material.
def _get_ascension_material_amount(character_data: dict, material_name: str) -> int:
    """
    Helper function to calculate the total amount of an ascension material.

    Args:
        character_data: The dictionary containing character's full data.
        material_name: The name of the ascension material to search for.

    Returns:
        The total amount of the material, or 0 if not found.
    """
    total_amount = 0
    if 'ascension_materials' in character_data:
        for mat_type, mat_data in character_data['ascension_materials'].items():
            if 'name' in mat_data and mat_data['name'] == material_name:
                total_amount += mat_data.get('amount', 0)
    return total_amount

def find_characters_by_material(material_name: str) -> list:
    """
    Finds and returns a list of characters that use the given material.

    Args:
        material_name: The name of the material to search for (e.g., 'Cecilia').

    Returns:
        A list of dictionaries, where each dictionary contains the character's name,
        material type, and the total amount of that material needed.
    """
    material_name_lower = material_name.lower()
    characters_using_material = {}
    
    # Search through all characters for ascension materials
    for char_name, char_data in gisl_data.items():
        if 'ascension_materials' in char_data:
            for mat_type, mat_data in char_data['ascension_materials'].items():
                if mat_data.get('name', '').lower() == material_name_lower:
                    # Logic for getting amount from ascension_levels or elsewhere
                    total_amount = _get_ascension_material_amount(char_data, mat_data['name'])
                    characters_using_material[char_data['name']] = {
                        "character": char_data['name'],
                        "material_type": "ascension",
                        "amount": total_amount
                    }
    
    # Search through all characters for talent materials
    for char_name, char_data in gisl_data.items():
        if 'talent_materials' in char_data:
            total_amount = 0
            for talent_type, talent_data in char_data['talent_materials'].items():
                if 'level_materials' in talent_data:
                    for level, level_mats in talent_data['level_materials'].items():
                        for mat_list_name in ['talent_books', 'common_materials', 'boss_drops']:
                            for mat in level_mats.get(mat_list_name, []):
                                if mat.get('name', '').lower() == material_name_lower:
                                    total_amount += mat.get('amount', 0)
                        
                        mora = level_mats.get('mora')
                        if mora is not None and material_name_lower == 'mora':
                            total_amount += mora
                            
                        crown = level_mats.get('crown_of_insight', 0)
                        if crown > 0 and material_name_lower == 'crown of insight':
                             total_amount += crown
            
            if total_amount > 0 and char_data['name'] not in characters_using_material:
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