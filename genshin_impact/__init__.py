"""
GI Static Data Library
Licensed under BSD 3-Clause
Copyright (c) 2025-2026 Imran Bin Gifary (System Delta)
"""

__version__ = "0.1.7"
__author__ = "Imran Bin Gifary (System Delta)"
__license__ = "BSD-3-Clause"

from .gisl import (
    get_character_data, 
    get_all_characters_data, 
    find_characters_by_material, 
    find_characters_by_element, 
    find_characters_by_weapon_type,
    check_for_updates, 
    get_talent_materials, 
    get_ascension_data, 
    get_ascension_levels, 
    get_ascension_stats,
    get_all_character_names,      # (already added earlier)
    get_all_material_names,       # <-- new
    find_characters_by_criteria,  # <-- new
)
from .gisl2 import (
    get_passive_talents,
    get_constellations,
    get_character_summary
)