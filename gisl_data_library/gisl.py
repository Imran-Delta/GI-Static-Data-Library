"""
A static library for retrieving Genshin Impact character and material data.
The data is loaded from a bundled gisl_data.json file.
"""
import json
import importlib.resources as pkg_resources

try:
    # Use importlib.resources to access the bundled JSON file
    json_data = pkg_resources.files('gisl_data_library').joinpath('gisl_data.json').read_text(encoding='utf-8')
    gisl_data = json.loads(json_data)
except Exception as e:
    # Handle the case where the data file cannot be found or decoded
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
    Finds and returns a list of characters who use a specific material, along with the amount needed.

    Args:
        material_name: The name of the material to search for.

    Returns:
        A list of dictionaries, where each dictionary contains the character's name,
        the type of material (e.g., 'ascension' or 'talent'), and the amount.
    """
    characters_using_material = []
    for char_name, char_data in gisl_data.items():
        total_amount = 0
        material_type = ""

        # Check ascension materials
        found_in_ascension = False
        for mat_key, mat_data in char_data.get('ascension_levels', {}).items():
            if material_name.lower() in mat_key.lower():
                for stage in mat_data.values():
                    if 'amount' in stage:
                        total_amount += stage['amount']
                        material_type = "ascension"
                found_in_ascension = True
                break

        # Check talent materials (only if not found in ascension to avoid duplicates)
        if not found_in_ascension:
            for talent in char_data.get('talents', []):
                for level_mats in talent.get('level_materials', {}).values():
                    for mat in level_mats:
                        if material_name.lower() in mat['material'].lower():
                            total_amount += mat.get('amount', 0)
                            material_type = "talent"

        if total_amount > 0:
            characters_using_material.append({
                "character": char_data['name'],
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
