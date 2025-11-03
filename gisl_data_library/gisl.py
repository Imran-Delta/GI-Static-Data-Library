"""
A static library for retrieving Genshin Impact character and material data.
The data is loaded from a bundled gisl_data.json file.
"""
import json
import importlib.resources as pkg_resources
import logging

# Module imports for the new update checker function
import requests
import importlib.metadata
from packaging.version import parse as parse_version

# Set up logging to capture potential errors
logger = logging.getLogger(__name__)

# Package configuration
PACKAGE_NAME = 'genshin_impact'
DATA_FILE_NAME = 'gisl_data.json'
# The name used on PyPI, defined in setup.py
PYPI_PACKAGE_NAME = 'genshin-impact'

try:
    # Use the robust read_text method for stability
    json_data = pkg_resources.read_text(PACKAGE_NAME, DATA_FILE_NAME)
    gisl_data = json.loads(json_data)
    'logger.info("Successfully loaded gisl_data.json")'
    'print("GISL_DATA_LIBRARY: Data loaded successfully.")'
except Exception as e:
    # This block is a failsafe.
    logger.error(f"Error loading data: {e}")
    print(f"GI_STATIC_DATA_LIBRARY: Error loading data from {DATA_FILE_NAME}: {e}")
    gisl_data = {}


def check_for_updates() -> dict:
    """
    Checks the PyPI repository for a newer version of the package.

    Returns:
        A dictionary containing the status of the update check.
    """
    try:
        # 1. Get current installed version
        current_version_str = importlib.metadata.version(PYPI_PACKAGE_NAME)
        current_version = parse_version(current_version_str)

        # 2. Query PyPI API for the latest version
        pypi_url = f"https://pypi.org/pypi/{PYPI_PACKAGE_NAME}/json"
        response = requests.get(pypi_url, timeout=5)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        latest_version_str = response.json()['info']['version']
        latest_version = parse_version(latest_version_str)

        # 3. Compare versions
        if latest_version > current_version:
            return {
                "update_available": True,
                "current_version": current_version_str,
                "latest_version": latest_version_str,
                "message": f"GI_STATIC_DATA_LIBRARY: A new version ({latest_version_str}) is available! Current version is {current_version_str}. Run 'pip install --upgrade {PYPI_PACKAGE_NAME}'."
            }
        elif latest_version == current_version:
            return {
                "update_available": False,
                "current_version": current_version_str,
                "latest_version": latest_version_str,
                "message": f"GI_STATIC_DATA_LIBRARY: You are running the latest version: {current_version_str}."
            }
        else:
             # Should not happen unless running a pre-release/local dev build
            return {
                "update_available": False,
                "current_version": current_version_str,
                "latest_version": latest_version_str,
                "message": f"GI_STATIC_DATA_LIBRARY: Current version {current_version_str} is newer than the public version {latest_version_str}. (Possibly a dev build)"
            }

    except importlib.metadata.PackageNotFoundError:
        return {
            "update_available": False,
            "message": f"GI_STATIC_DATA_LIBRARY: Error: The package '{PYPI_PACKAGE_NAME}' does not appear to be installed via pip."
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"GI_STATIC_DATA_LIBRARY: Error checking for updates: {e}")
        return {
            "update_available": False,
            "message": f"GI_STATIC_DATA_LIBRARY: Failed to check for updates. Could not connect to PyPI: {e}"
        }
    except Exception as e:
        logger.error(f"GI_STATIC_DATA_LIBRARY: An unexpected error occurred during update check: {e}")
        return {
            "update_available": False,
            "message": f"GI_STATIC_DATA_LIBRARY: An unexpected error occurred during the update check: {e}"
        }

def get_character_data(character_key: str) -> dict | None:
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
        # --- Ascension Materials Check ---
        total_ascension_amount = 0
        ascension_mats = char_data.get('ascension_materials', {})

        for mat_type, mat_info in ascension_mats.items():
            if mat_info and mat_info.get('name', '').lower() == material_name:
                mat_key = mat_info['name'] 
                for level_info in char_data.get('ascension_levels', {}).values():
                    if mat_key in level_info:
                        total_ascension_amount += level_info[mat_key]['amount']
                
                characters_using_material[char_data['name']] = {
                    "character": char_data['name'],
                    "material_type": "ascension",
                    "amount": total_ascension_amount
                }
                break

        # --- Talent Materials Check ---
        total_talent_amount = 0
        
        for talent in char_data.get('talents', []):
            talent_mats = talent.get('level_materials', {}).get('level', [])
            
            for mat_info in talent_mats:
                if mat_info.get('material', '').lower() == material_name:
                    amounts_str = mat_info.get('amount', '')
                    
                    if amounts_str:
                        amounts = [int(a) for a in amounts_str.split('-') if a.isdigit()]
                        total_talent_amount += sum(amounts)
        
        if total_talent_amount > 0:
            characters_using_material[char_data['name']] = {
                "character": char_data['name'],
                "material_type": "talent",
                "amount": total_talent_amount
            }

    return list(characters_using_material.values())

def find_characters_by_element(element_name: str) -> list:
    """
    Finds and returns a list of character names that match the given element.
    """
    matching_characters = []
    for char_name, char_data in gisl_data.items():
        if 'element' in char_data and char_data['element'].lower() == element_name.lower():
            matching_characters.append(char_data['name'])
    return matching_characters

def find_characters_by_weapon_type(weapon_type: str) -> list:
    """
    Finds and returns a list of character names that match the given weapon type.
    """
    matching_characters = []
    for char_name, char_data in gisl_data.items():
        if 'weapon_type' in char_data and char_data['weapon_type'].lower() == weapon_type.lower():
            matching_characters.append(char_data['name'])
    return matching_characters