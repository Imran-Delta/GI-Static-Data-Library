"""
A static library for retrieving Genshin Impact character and material data.
The data is loaded from a bundled gisl_data.json file.
"""
import json
import importlib.resources as pkg_resources

# The 'gisl_data_library' is a hardcoded package name. This will work,
# but a more dynamic approach could be used in a larger project.
PACKAGE_NAME = 'gisl_data_library'
DATA_FILE_NAME = 'gisl_data.json'

try:
    # Use importlib.resources to access the bundled JSON file
    # This path is now correct because we've updated setup.py to include the data file.
    json_data = pkg_resources.files(PACKAGE_NAME).joinpath(DATA_FILE_NAME).read_text(encoding='utf-8')
    gisl_data = json.loads(json_data)
except Exception as e:
    # This block is a failsafe. If the data file cannot be found,
    # the 'gisl_data' dictionary will be initialized as empty,
    # preventing the script from crashing.
    print(f"Error loading data: {e}")
    gisl_data = {}

def _get_ascension_material_amount(character_data: dict, material_name: str) -> int:
    """
    Helper function to calculate the total amount of an ascension material.

    Args:
        character_data: The dictionary containing character's full data.
        material_name: The name of the ascension material to search for.

    Returns:
        The total amount of the material needed for full ascension.
    """
    total_amount = 0
    ascension_levels = character_data.get('ascension_levels', {})

    # Iterate through all materials listed in the ascension_levels table
    for mat_name, levels in ascension_levels.items():
        if mat_name.lower() == material_name.lower():
            for level_data in levels.values():
                amount = level_data.get('amount', 0)
                # Ensure the amount is an integer before adding
                if isinstance(amount, (int, float)):
                    total_amount += int(amount)

    return total_amount

def get_character_data(character_name: str, data_point: str = None) -> dict | list | None:
    """
    Retrieves all or specific data for a Genshin Impact character from the JSON file.

    Args:
        character_name: The name of the character to retrieve (e.g., "Albedo").
        data_point: Optional. A specific data key to retrieve (e.g., "talents", "constellations").

    Returns:
        A dictionary or list containing the requested data, or None if not found.
    """
    character = gisl_data.get(character_name.lower())
    if not character:
        return None
    if data_point:
        return character.get(data_point)
    return character

def find_characters_by_material(material_name: str) -> list:
    """
    Finds and returns a list of characters that use a specific material.
    Handles potential inconsistencies in the JSON structure.

    Args:
        material_name: The name of the material to search for.

    Returns:
        A list of dictionaries, where each dictionary contains the character's
        name, the type of material (ascension or talent), and the amount needed.
    """
    characters_using_material = {} # Use a dictionary to store unique characters
    for char_name, char_data in gisl_data.items():
        
        # Check ascension materials first
        ascension_total = _get_ascension_material_amount(char_data, material_name)
        if ascension_total > 0:
            characters_using_material[char_data['name']] = {
                "character": char_data['name'],
                "material_type": "ascension",
                "amount": ascension_total
            }
            continue # Move to the next character after finding an ascension match

        # Check talent materials (only if not found as an ascension material for this char)
        total_amount = 0
        talents = char_data.get('talents', [])
        if isinstance(talents, list):
            for talent in talents:
                if isinstance(talent, dict):
                    level_mats = talent.get('level_materials', {})
                    if isinstance(level_mats, dict):
                        for materials_in_level in level_mats.values():
                            if isinstance(materials_in_level, list):
                                for mat in materials_in_level:
                                    if isinstance(mat, dict) and mat.get('material', '').lower() == material_name.lower():
                                        amount_value = mat.get('amount', 0)

                                        # Handle non-numeric amounts like "3-2"
                                        if isinstance(amount_value, str):
                                            try:
                                                if '-' in amount_value:
                                                    amount_value = int(amount_value.split('-')[0])
                                                elif '+' in amount_value:
                                                    amount_value = sum(int(n) for n in amount_value.split('+'))
                                                else:
                                                    amount_value = int(amount_value)
                                            except ValueError:
                                                amount_value = 0
                                        elif not isinstance(amount_value, (int, float)):
                                            amount_value = 0

                                        total_amount += amount_value
        
        # If any amount was found for talent materials, add it to the dictionary
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