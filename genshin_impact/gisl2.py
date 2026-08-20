# gisl2.py
"""
New SQL‑backed convenience functions for Genshin Impact data.
Requires the database initialized in gisl.py.
"""

import json
import logging
from typing import Union, List, Dict, Optional

# Import the shared raw-data dispatcher from the main module - avoids
# re-implementing the same single-row SQL query gisl.py already has in
# get_character_data_sql (this used to duplicate it inline).
from .gisl import _get_raw_character_data

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Internal helper: fetch full JSON for a character by key
# ----------------------------------------------------------------------
def _get_character_json(character_key: str, use_sql: bool = True) -> Optional[Dict]:
    """
    Retrieve the full JSON data for a character.

    use_sql (default True): single-row SQL query, no monolith load.
    use_sql=False: legacy monolithic dict (see gisl.py's module docstring
    for the memory tradeoff this triggers on first use).
    """
    return _get_raw_character_data(character_key, use_sql)

# ----------------------------------------------------------------------
# 1. Passive Talents
# ----------------------------------------------------------------------
def get_passive_talents(
    character_key: str,
    option: str = "all",
    use_sql: bool = True
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
    use_sql : bool, default True
        Single-row SQL query vs. the legacy monolithic dict. See
        gisl.py's _get_raw_character_data. Output is identical either way.

    Returns
    -------
    str, list, or None
        Formatted string, raw data, or None if character not found.
    """
    char_data = _get_character_json(character_key, use_sql)
    if not char_data:
        return None

    # Try common keys for passive talents (none of the current character
    # files use these, but left in case the schema adds a dedicated field)
    passives = (
        char_data.get("passive_talents") or
        char_data.get("passives") or
        []
    )

    # Fallback: derive from the talents list by EXCLUDING the 3 known
    # active-combat types, rather than matching an inclusion list of
    # passive type strings. The old inclusion list checked for exact
    # matches on "passive"/"utility"/"1st ascension"/"4th ascension",
    # which never matched anything - real type strings are the full
    # phrases ("1st Ascension Passive", "Utility Passive", "Moonsign
    # Benediction Passive", ...), so this returned zero passives for
    # every character (confirmed against aino.json). Exclusion is also
    # more robust to new passive categories a future character adds
    # (e.g. "Moonsign Benediction Passive" itself wasn't anticipated by
    # the old inclusion list) - no enum to maintain going forward.
    if not passives and "talents" in char_data:
        _active_types = {"normal attack", "elemental skill", "elemental burst"}
        passives = [
            t for t in char_data["talents"]
            if t.get("type", "").lower() not in _active_types
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
    option: str = "all",
    use_sql: bool = True
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
          Always returned as Markdown - there's currently no way to
          combine "one specific index" with "alltext" plain formatting
          in a single call. If you need that combination, use "allraw"
          and format the single dict yourself, or ask for that to be
          added as a real feature (separate index/format params) rather
          than overloading one option string for both.
    use_sql : bool, default True
        Single-row SQL query vs. the legacy monolithic dict. See
        gisl.py's _get_raw_character_data. Output is identical either way.

    Returns
    -------
    str, list, or None
    """
    char_data = _get_character_json(character_key, use_sql)
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
            # NOTE: option is already proven numeric here (int(option)
            # succeeded), so it can never equal "allraw" - that branch
            # was dead code, removed.
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
    option: str = "all",
    use_sql: bool = True
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
    use_sql : bool, default True
        Single-row SQL query vs. the legacy monolithic dict. See
        gisl.py's _get_raw_character_data. Output is identical either way.

    Returns
    -------
    str, dict, or None
    """
    char_data = _get_character_json(character_key, use_sql)
    if not char_data:
        return None

    # additional_titles is a list in the real schema (e.g.
    # ["Chief Alchemist of the Knights of Favonius"]), never a "title"
    # string key - that key doesn't exist in any character file.
    titles = char_data.get("additional_titles") or []
    if isinstance(titles, str):
        titles = [titles]

    summary = {
        "name": char_data.get("name", "Unknown"),
        "element": char_data.get("element", "Unknown"),
        "weapon": char_data.get("weapon_type", "Unknown"),
        "rarity": char_data.get("rarity", 0),
        "region": char_data.get("region", "Unknown"),
        "affiliation": char_data.get("affiliation", "Unknown"),
        "role": char_data.get("role", "Unknown"),
        "constellation": char_data.get("constellation_name", "Unknown"),
        "titles": titles,
        # description / icon: no character file has ever had these keys
        # (confirmed against aino.json and albedo.json - structurally
        # absent from the schema, not just usually empty). Left as
        # placeholders so this doesn't break if the schema adds them
        # later; they will not appear in formatted output until then.
        "description": char_data.get("description", ""),
        "icon": char_data.get("icon", ""),
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
            f"Role: {summary['role']}",
            f"Constellation: {summary['constellation']}",
        ]
        if summary['titles']:
            lines.append(f"Title(s): {', '.join(summary['titles'])}")
        if summary['description']:
            lines.append(f"\n{summary['description']}")
        return "\n".join(lines)
    else:  # "all" with Markdown
        title = f"**{summary['name']}**"
        if summary['titles']:
            title += f" – *{', '.join(summary['titles'])}*"
        lines = [
            title,
            f"**Element:** {summary['element']} | **Weapon:** {summary['weapon']}",
            f"**Rarity:** {'⭐' * summary['rarity']}",
            f"**Region:** {summary['region']} | **Affiliation:** {summary['affiliation']}",
            f"**Role:** {summary['role']}",
            f"**Constellation:** {summary['constellation']}",
        ]
        if summary['description']:
            lines.append(f"\n{summary['description']}")
        return "\n".join(lines)
