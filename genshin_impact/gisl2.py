# gisl2.py
"""
New SQL‑backed convenience functions for Genshin Impact data.
Requires the database initialized in gisl.py.
"""

import json
import logging
from typing import Union, List, Dict, Optional

# Import the shared database connection from the main module
from .gisl import _conn, _tables_initialized

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Internal helper: fetch full JSON for a character by key
# ----------------------------------------------------------------------
def _get_character_json(character_key: str) -> Optional[Dict]:
    """Retrieve the full JSON data for a character directly from SQL."""
    if not _tables_initialized:
        logger.error("Database not initialized")
        return None
    cursor = _conn.cursor()
    cursor.execute(
        "SELECT full_json FROM character_core WHERE key = ?",
        (character_key.lower(),)
    )
    row = cursor.fetchone()
    if row:
        return json.loads(row["full_json"])
    return None

# ----------------------------------------------------------------------
# 1. Passive Talents
# ----------------------------------------------------------------------
def get_passive_talents(
    character_key: str,
    option: str = "all"
) -> Union[str, List[Dict], None]:
    """
    Retrieve passive talents for a character.

    Parameters
    ----------
    character_key : str
        The character's key (lowercase, e.g., 'albedo').
    option : str, default "all"
        - "all"       : formatted string with Markdown bold headers (ideal for Discord).
        - "alltext"   : plain text with no Markdown.
        - "allraw"    : raw list of passive talent dictionaries.

    Returns
    -------
    str, list, or None
        Formatted string, raw data, or None if character not found.
    """
    char_data = _get_character_json(character_key)
    if not char_data:
        return None

    # Try common keys for passive talents
    passives = (
        char_data.get("passive_talents") or
        char_data.get("passives") or
        []
    )

    # If passives are stored inside the talents list with type "Passive"
    if not passives and "talents" in char_data:
        passives = [
            t for t in char_data["talents"]
            if t.get("type", "").lower() in ("passive", "utility", "1st ascension", "4th ascension")
        ]

    if not passives:
        return f"No passive talent data found for `{character_key}`."

    if option == "allraw":
        return passives

    lines = []
    for i, p in enumerate(passives, 1):
        name = p.get("name", f"Passive {i}")
        desc = p.get("description", "No description.")
        unlock = p.get("unlock", "")

        if option == "alltext":
            entry = f"{name}\n{desc}"
            if unlock:
                entry += f"\n(Unlock: {unlock})"
        else:  # "all" (Markdown)
            entry = f"**{name}**"
            if unlock:
                entry += f" – *{unlock}*"
            entry += f"\n{desc}"
        lines.append(entry)

    separator = "\n\n" if option == "alltext" else "\n"
    return separator.join(lines)

# ----------------------------------------------------------------------
# 2. Constellations
# ----------------------------------------------------------------------
def get_constellations(
    character_key: str,
    option: str = "all"
) -> Union[str, List[Dict], None]:
    """
    Retrieve constellation data for a character.

    Parameters
    ----------
    character_key : str
        The character's key.
    option : str, default "all"
        - "all"       : formatted string with Markdown (C1, C2, ...).
        - "alltext"   : plain text.
        - "allraw"    : raw list of constellation dictionaries.
        - 0..5 (int)  : return only the specified constellation (0 = C1).

    Returns
    -------
    str, list, or None
    """
    char_data = _get_character_json(character_key)
    if not char_data:
        return None

    constellations = char_data.get("constellations", [])
    if not constellations:
        return f"No constellation data found for `{character_key}`."

    # Handle numeric index option (0..5)
    try:
        idx = int(option)
        if 0 <= idx < len(constellations):
            c = constellations[idx]
            if option == "allraw":   # but raw only makes sense for all, so treat as all
                return [c]
            name = c.get("name", f"C{idx+1}")
            desc = c.get("description", "No description.")
            if option == "alltext":
                return f"{name}\n{desc}"
            else:
                return f"**{name}**\n{desc}"
        else:
            return f"Index {idx} out of range. Character has {len(constellations)} constellations."
    except ValueError:
        pass  # not an integer, continue with string options

    if option == "allraw":
        return constellations

    # Build full output
    lines = []
    for i, c in enumerate(constellations, 1):
        name = c.get("name", f"C{i}")
        desc = c.get("description", "")
        if option == "alltext":
            entry = f"C{i}: {name}\n{desc}"
        else:
            entry = f"**C{i}: {name}**\n{desc}"
        lines.append(entry)

    separator = "\n\n" if option == "alltext" else "\n"
    return separator.join(lines)

# ----------------------------------------------------------------------
# 3. Character Profile / Summary
# ----------------------------------------------------------------------
def get_character_summary(
    character_key: str,
    option: str = "all"
) -> Union[str, Dict, None]:
    """
    Return a concise summary of a character.

    Parameters
    ----------
    character_key : str
        The character's key.
    option : str, default "all"
        - "all"     : formatted string with Markdown.
        - "alltext" : plain text.
        - "allraw"  : raw dictionary of summary fields.

    Returns
    -------
    str, dict, or None
    """
    char_data = _get_character_json(character_key)
    if not char_data:
        return None

    summary = {
        "name": char_data.get("name", "Unknown"),
        "element": char_data.get("element", "Unknown"),
        "weapon": char_data.get("weapon_type", "Unknown"),
        "rarity": char_data.get("rarity", 0),
        "region": char_data.get("region", "Unknown"),
        "affiliation": char_data.get("affiliation", "Unknown"),
        "constellation": char_data.get("constellation_name", "Unknown"),
        "description": char_data.get("description", ""),
        "icon": char_data.get("icon", ""),
        "title": char_data.get("title", ""),
    }

    if option == "allraw":
        return summary

    # Build a readable block
    if option == "alltext":
        lines = [
            f"Name: {summary['name']}",
            f"Element: {summary['element']}",
            f"Weapon: {summary['weapon']}",
            f"Rarity: {'⭐' * summary['rarity']}",
            f"Region: {summary['region']}",
            f"Affiliation: {summary['affiliation']}",
            f"Constellation: {summary['constellation']}",
        ]
        if summary['title']:
            lines.append(f"Title: {summary['title']}")
        if summary['description']:
            lines.append(f"\n{summary['description']}")
        return "\n".join(lines)
    else:  # "all" with Markdown
        title = f"**{summary['name']}**"
        if summary['title']:
            title += f" – *{summary['title']}*"
        lines = [
            title,
            f"**Element:** {summary['element']} | **Weapon:** {summary['weapon']}",
            f"**Rarity:** {'⭐' * summary['rarity']}",
            f"**Region:** {summary['region']} | **Affiliation:** {summary['affiliation']}",
            f"**Constellation:** {summary['constellation']}",
        ]
        if summary['description']:
            lines.append(f"\n{summary['description']}")
        return "\n".join(lines)