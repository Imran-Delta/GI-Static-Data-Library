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

    Args:
        material_name: The name of the material to search for.

    Returns:
        A list of dictionaries, where each dictionary contains the character's
        name, the type of material (ascension or talent), and the amount needed.
    """
    characters_using_material = []
    for char_name, char_data in gisl_data.items():
        total_amount = 0
        material_type = ""
        
        # Failsafe for missing 'ascension_materials'
        ascension_mats = char_data.get('ascension_materials', {})
        if ascension_mats:
            # The keys of ascension_mats are the material names themselves
            for mat_name_key, levels_data in ascension_mats.items(): # Renamed for clarity
                if mat_name_key.lower() == material_name.lower():
                    # We need to sum up the amounts from all levels (A1, A2, etc.)
                    # for this material for this character.
                    for level_key, level_info in levels_data.items():
                        amount_value = level_info.get('amount', 0)
                        if isinstance(amount_value, (int, float)):
                            total_amount += amount_value
                    material_type = "ascension"

        # Failsafe for missing 'talents'
        talents = char_data.get('talents', [])
        for talent in talents:
            # Failsafe for missing 'level_materials'
            level_mats = talent.get('level_materials', [])
            for mat in level_mats:
                if mat.get('name', '').lower() == material_name.lower():
                    amount_value = mat.get('amount', 0)
                    
                    # Failsafe for non-integer amounts. This handles cases where
                    # the amount is a string like "3-2" or simply missing.
                    if not isinstance(amount_value, (int, float)):
                        # You can decide how to handle this. For now, we'll
                        # default to 0 if the value is not a number.
                        amount_value = 0
                    
                    total_amount += amount_value
                    material_type = "talent"

        if total_amount > 0:
            characters_using_material.append({
                "character": char_data.get('name', 'Unknown Character'), # Added failsafe for character name
                "material_type": material_type,
                "amount": total_amount
            })

    return characters_using_material

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
