# GI Static Data Library
• If contact is needed urgently, please send me a friend request in Discord, @sys_delta. I'm much more active on discord than gmail.
```
License
This project is licensed under the BSD 3-Clause License.
```

This is my personal project of making a library containing information on items, characters and weapons from a game I play, named Genshin Impact. I made this library to serve as a static, usable offline library. For some this may be useful. For me it's just a hobby.

# Current Details:
`REQUIRED DEPENDENCY (Installing GISDL also installs the dependencies): Packaging and Requests`

Also- SQL backend added for performance future-proofing. `get_talent_materials`, `get_ascension_data`, `get_ascension_levels`, `get_ascension_stats`, `get_passive_talents`, `get_constellations`, and `get_character_summary` now all take a `use_sql` parameter (default `True`) so they fetch via a single-row SQL query instead of loading every character into memory - old calls that don't pass it are unaffected signature-wise, they just get the faster path automatically. Pass `use_sql=False` to force the old monolithic-dict behavior.
MOONSIGN ADDED!

Characters Added:
 * Aino, Albedo

---

# 🚀 genshin-impact Data Library Integration Guide

The genshin-impact library provides static character and material data. This guide covers installation, core retrieval, and Discord implementation using slash commands and autocompletion.
The core package for all data functions is `genshin_impact`.
# 1. Installation, Updating and data import.
Begin by installing the library and setting up a try import block to prevent your application from crashing if the dependency is missing. And also optionally an update check.
### 1.1 💾 Installation
pip install genshin-impact
### 1.2 🐍 Import Method (This just avoids crashes)
```py
import discord
from discord import app_commands

try:
    # All of the imports are important for the later sections.
	# The first 2 are for Discord autocomplete and get data. The 3 after are if you want to well, add a `find by x` command.
	# The last 4 are for update check, getting talent mats, ascension mats and ascension levels.
	
	# Note: All the examples import the minimum methods needed for that example. This import block contains all you'd normally need. (Unless u go and use legacy methods)
	
	
    from genshin_impact import (get_character_data, get_all_characters_data,
	find_characters_by_material, find_characters_by_element, find_characters_by_weapon_type,
	check_for_updates, get_talent_materials, get_ascension_data, get_ascension_stats)
except ImportError:
    # Handle the missing dependency gracefully
    print("❌ FATAL ERROR: genshin_impact not installed or accessible.")
    # In a Discord bot context, you would log this error or notify the user.
    
# Primary retrieval
character_data = get_character_data("albedo") 
if not character_data:
    # Handle Character Not Found (e.g., return None)
    return
```
### 1.3🔎 Checking for Updates
The `check_for_updates()` function allows you to programmatically check the PyPI repository to see if a newer version of the genshin-impact package is available. Using Python 3.10+ Structural Pattern Matching, you can handle specific build statuses like development modes or outdated dev versions.
```py
from genshin_impact import check_for_updates

def check_for_new_version():
    update_status = check_for_updates()
    message = update_status.get("message", "Unknown status")
    
    # Structural Pattern Matching (Python 3.10+)
    match update_status.get("status"):
        case "update":
            print(f"✨ UPDATE AVAILABLE! {message}")
        case "outdated_dev":
            print(f"⚠️ DEV BUILD OUTDATED: {message}")
        case "dev":
            print(f"🛠️ DEVELOPMENT MODE: {message}")
        case "ok":
            print(f"✅ Status: {message}")
        case _: # This is the wildcard/fallback
            print(f"⚠️ Update Check Failed: {message}")

check_for_new_version()
```
---
# 2.1 🤖  Discord Bot Implementation (I'm using cogs)

This updated Cog includes three sub-commands to handle the different ways of viewing character progression.

```python
import discord
from discord import app_commands
from discord.ext import commands
# Added the new methods to the import list
from genshin_impact import (
    get_character_data, 
    get_all_characters_data, 
    get_ascension_data, 
    get_ascension_stats, 
    get_ascension_levels
)

class GenshinCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.element_colors = {
            "pyro": 0xef797d, "hydro": 0x4cc3f1, "anemo": 0x75f3d9,
            "electro": 0xaf8ef3, "dendro": 0xa5c83b, "cryo": 0x98def4, "geo": 0xffae00
        }

    def get_color(self, name):
        data = get_character_data(name)
        element = data.get('element', '').lower() if data else ""
        return self.element_colors.get(element, 0x808080)

    @app_commands.command(name="ascension_mats", description="Get only ascension materials for a character")
    async def ascension_mats(self, interaction: discord.Interaction, name: str):
        # Uses get_ascension_data for a materials-only focus
        res = get_ascension_data(name, "all")
        embed = discord.Embed(title=f"{name.title()} Ascension Materials", description=res, color=self.get_color(name))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ascension_stats", description="Get only stat growth for a character (Lv 1-100)")
    async def ascension_stats(self, interaction: discord.Interaction, name: str):
        # Uses get_ascension_stats for a stats-only focus, including Level 100 logic
        res = get_ascension_stats(name)
        embed = discord.Embed(title=f"{name.title()} Stat Progression", description=res, color=self.get_color(name))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ascension_full", description="Get both materials and stats in one view")
    async def ascension_full(self, interaction: discord.Interaction, name: str):
        # Uses get_ascension_levels for the combined view
        res = get_ascension_levels(name, "all")
        embed = discord.Embed(title=f"{name.title()} Full Ascension Details", description=res, color=self.get_color(name))
        await interaction.response.send_message(embed=embed)

    @ascension_mats.autocomplete('name')
    @ascension_stats.autocomplete('name')
    @ascension_full.autocomplete('name')
    async def char_autocomplete(self, interaction: discord.Interaction, current: str):
        all_chars = get_all_characters_data()
        return [
            app_commands.Choice(name=char['name'], value=key)
            for key, char in all_chars.items() 
            if current.lower() in char['name'].lower()
        ][:25]

async def setup(bot):
    await bot.add_cog(GenshinCog(bot))

```
### 2.2 Accessing Detailed Levels and Tiers (Updated Table)

This table describes the three methods.

| Requested Detail | Method to Use | Data Structure | Display Logic |
|---|---|---|---|
| Ascension Materials | `get_ascension_data(name, opt)` | Formatted String or List | Focuses on items like Gems, Boss Mats, and Specialties for A1-A6. |
| Ascension Stats | `get_ascension_stats(name)` | Formatted String | Displays HP, ATK, and DEF growth from A0 up to A6-C8 (Level 100). |
| Full Progression | `get_ascension_levels(name, opt)` | Formatted String | Combines materials and stats; automatically labels Level 100 as "Stat Increase Only". |

By providing these three distinct entry points, users can choose between a concise farming list, a theory-crafting stat sheet, or a full overview of character investment.

---
# 4.1 🧩 Talent Material Retrieval `get_talent_materials`
This method handles internal mapping for talent levels (Index 0 = Level 1->2, Index 8 = Level 9->10). It automatically includes Weekly Boss materials and the Crown of Insight at the correct levels.

Options:
- "all": Formatted string with bold headers and Markdown hyperlinks (Ideal for Discord Embeds).
- "alltext": Plain text string with headers but no links/bolding (Uses \n instead of #).
- "allraw": Returns the raw material list as a list of dictionaries
- 0-8 (Integer/String): Returns the formatted requirements for a specific level progression index.
  ⚙️ Internal Logic: Index Mapping
  The library internally handles the positional offsets for materials so the user can use a simple 0-8 index system:
Internal Index Level-Up Step Included Items
- 0 1 -> 2 Books & Common Mats
- 5 6 -> 7 Weekly Boss Mats start here
- 8 9 -> 10 Includes Crown of Insight

### 🤖 Discord Implementation Example
```py
@app_commands.command(name="talents", description="Get talent requirements")
async def talents(self, interaction: discord.Interaction, name: str, index: int = None):
    # Fetch formatted data using the library's internal indexing
    if index is not None:
        # Returns specific index 0-8
        res = get_talent_materials(name, str(index))
    else:
        # Returns full formatted list
        res = get_talent_materials(name, "all")
    
    await interaction.response.send_message(res)
```
### 4.2 Passive Talents `get_passive_talents(name, option="all")`
Retrieves a character's passive talents (including utility and ascension passives).

Options:
- "all" – Formatted string with Markdown bold headers (ideal for Discord Embeds).
- "alltext" – Plain text with no Markdown.
- "allraw" – Raw list of passive talent dictionaries.

### Discord Example
```py
@app_commands.command(name="passives", description="Show a character's passive talents")
async def passives(self, interaction: discord.Interaction, name: str):
    res = get_passive_talents(name, "all")
    embed = discord.Embed(title=f"{name.title()} Passive Talents", description=res)
    await interaction.response.send_message(embed=embed)
```

---

# 5. 🆕 Constellations and Character overview
### 5.1 Constellations `get_constellations(name, option="all")`

Retrieves constellation data. In addition to the standard string options, you can pass an integer (0–5) to get a single constellation.

Options:
- "all" – Formatted string with all constellations (C1 to C6).
- "alltext" – Plain text.
- "allraw" – Raw list of constellation dictionaries.
- 0 to 5 – Return only the specified constellation (0 = C1).

### Discord Example

```py
@app_commands.command(name="constellations", description="Show a character's constellations")
async def constellations(self, interaction: discord.Interaction, name: str, level: int = None):
    if level is not None:
        res = get_constellations(name, str(level))
    else:
        res = get_constellations(name, "all")
    embed = discord.Embed(title=f"{name.title()} Constellations", description=res)
    await interaction.response.send_message(embed=embed)
```

### 5.2 Character Overview `get_character_summary(name, option="all")`

Returns a concise summary of basic character information (name, element, weapon, rarity, region, affiliation, constellation, description, etc.).

Options:
- "all" – Formatted string with Markdown.
- "alltext" – Plain text.
- "allraw" – Raw dictionary of summary fields (useful for building custom embeds).

### Discord Example
```py
@app_commands.command(name="summary", description="Quick overview of a character")
async def summary(self, interaction: discord.Interaction, name: str):
    res = get_character_summary(name, "all")
    embed = discord.Embed(title=f"{name.title()} Summary", description=res)
    await interaction.response.send_message(embed=embed)
```

---

# `- Update LOGS -`
# -Update 0.1.7dev1-0.1.7-
 * Added new functions for heavy lifting data.
 * the editor is still WIP. Once it is done, characters will fly in.


# -Update 0.1.3-0.1.6-
 * Added SQL Backend for performance furture proofing
 * SQL is made using the data files in the same directory as the library, if not in system cache if possible. If that's not possible then RAM
 * Abstracted SQL as a json in the old methods.
 * Changed License from MIT to BSD.
 * Added an editor for me. I HATE WRITING JSONS!>!>!???!
 ??
 !??!?
 * um, I broke the code- my bot crashed. T-T. It's fixed now (;


# -Update 0.1.3dev1 to dev2-
 * Changed setup.py and setup.cfg to pyproject.toml
 * Tetsing out new update check system.
 * Please dont use dev versions unless you want to contribute.
 * Added a talent method for those who don't want to use the manual method of doing the formatting themselves.
 

# -Update 0.0.9 to 0.1.2-
 * Added Aino
 * Added character list
 * Added pending list
 * Added personal description.
 * Fixed A DAM "CLOSING" ISSUE
 * Added a dependency: Packaging
 * Experimental Test on lvl 90-100 data.


# -Update 0.0.2 to 0.0.8-
 * Removed the json load print.
 * Added a guide for retrieving data.
 * Fixed thr guide formatting.
 * Fixed a major file error.
 * Added an update check.
 * Upgraded the guide.
 * Fixed some misc spelling errors
 * Fixed ImportError



# -Update-
 * Renamed the repo to genshin impact.
 * Version reset to 0.0.1


# -Update 0.1.0 to 0.1.5-
* Trying to fix the talent retrieve function.
* Added a print system temporarily to help me debug

# -Update 0.0.9-
* Fixing the lib issues

# -Update 0.0.8-
* Trying a new json retreval system using lib

# -Update 0.0.7-
* Trying to fix the same error that I tried to fix on 0.0.6.

# -Update 0.0.6-
* Fixed an issue with retrieving character list by mats/element/weapon.

# -Update 0.0.3 to 0.0.5-
* Fixed a json error.
* Fixed multiple json errors. :<
* I FORGOT TO SAVE THE ERROR FIXES

# -Update 0.0.2-
* Added Albedo
* Changed the gisl.py lookup system

---

# LEGACY METHODS!
# 3.1 Discord Autocomplete for Slash Commands

For autocompletion use the function `get_all_characters_data` to provide real-time character name suggestions in your slash commands (app_commands).
* ⚙️ Autocomplete Logic
```py
from discord import app_commands

async def character_autocomplete(interaction: discord.Interaction, current: str):
    # CRITICAL: This imports the helper function
    from genshin_impact import get_all_characters_data 
    
    # 1. Get ALL character names (the keys are always lowercase)
    all_names = get_all_characters_data().keys()
    
    # 2. Filter the names based on user input
    return [
        # Set the displayed 'name' to Title Case and the internal 'value' to lowercase
        app_commands.Choice(name=name.title(), value=name)
        for name in all_names if current.lower() in name
    ][:25] # Discord limits suggestions to 25
    
# --- Command Implementation ---
@app_commands.command(name="character", description="Get detailed data for a character.")
@app_commands.describe(character_name="Start typing the character's name...")
@app_commands.autocomplete(character_name=character_autocomplete)
async def character_command(self, interaction: discord.Interaction, character_name: str):
    # 'character_name' will be the lowercase 'value' from autocomplete, ready for lookup!
    # data = get_character_data(character_name) ...
    pass
```

### 3.2 Accessing Detailed Levels and Tiers
The dictionary returned by `get_character_data(name)` is highly structured. To display specific subsets like Passive Talents or a full summary, use the following mapping:
| Requested Detail | Access Key | Data Structure | Display Logic |
|---|---|---|---|
| Main Talents | `data['talents']` | `list[dict]` | Iterate to display name/desc of the three active combat talents. |
| Passive Talents | `data['talents']` | `list[dict]` | [NEW] Every talent's `type` is one of exactly 3 active-combat values ("Normal Attack", "Elemental Skill", "Elemental Burst") or a passive value that varies per character ("1st Ascension Passive", "Utility Passive", "Moonsign Benediction Passive", etc. - the exact wording is not fixed). Filter passives by **excluding** the 3 known active types, not by matching a list of passive-type strings - a fixed inclusion list won't cover new passive categories future characters add. `get_passive_talents()` does this for you. |
| Constellations | `data['constellations']` | `list[dict]` | Iterate (indices 0-5) to display info for C1 through C6. |
| Ascension Levels | `data['ascension_levels']` | `dict` | Iterate over `.items()` to show level milestones and stat changes. |
| Full Summary | Multiple | mixed | [NEW] Combine top-level keys like element, weapon_type, rarity, and region. |

### 3.2b 🗂️ Character JSON Schema Reference

This section exists because the schema below was never fully written down anywhere, and every field on it has been the source of a real bug at some point - either in the library code or in something built against it. Treat this as the source of truth over any other description of the schema in this document, this codebase, or your own memory of it.

Top-level keys on a character's JSON object (confirmed present on every character file as of this writing): `name`, `element`, `weapon_type`, `region`, `role`, `rarity`, `affiliation`, `birthday`, `additional_titles`, `constellation_name`, `ascension_stat`, `stats_table`, `ascension_levels`, `ascension_materials`, `talents`, `constellations`.

**There is no `title`, `description`, or `icon` key.** Character titles live in `additional_titles`, which is a **list** of strings (usually one entry, but treat it as a list) - not a singular string. If you're adding icon/description support, that's new schema, not a rename of an existing field.

**`ascension_materials` vs `ascension_levels` - these are not interchangeable, and mixing them up is the single most common source of bugs in this codebase so far:**
- `ascension_materials` is a small fixed dict with 4 keys - `gems`, `boss_mat`, `local_specialty`, `common_mat` - each holding `{"name": ..., "link": ...}` for the **untiered family name** (e.g. `"Varunada Lazurite"`). This exists purely to label/group a character's 4 material slots for a short summary display (see `genshin.py`'s `/character_data` embed for a working example). It has no amounts and cannot be used to look up a specific tier's cost.
- `ascension_levels` is a dict keyed by the **exact tiered material name** (e.g. `"Varunada Lazurite Silver"`, `"Varunada Lazurite Fragment"`), each holding `{"A1": {"level_range": ..., "amount": <int>, "link": ...}, "A2": {...}, ...}` - this is where actual per-tier amounts live, and it's the correct key to search or sum against. `find_characters_by_material` / `find_characters_by_material_sql` both match against this, not against `ascension_materials`.
- If you ever need to go from a family name (`"Varunada Lazurite"`) to its tiered variants, you have to build that mapping yourself by cross-referencing the two - there's no `ascension_levels` key that contains the untiered name, and no `ascension_materials` field that lists the tiers.

**`talents` is a list where `level_materials` is polymorphic depending on the talent's `type`:**
- For the 3 active-combat types - `"Normal Attack"`, `"Elemental Skill"`, `"Elemental Burst"` - `level_materials` is a dict, e.g. `{"level": [{"material": ..., "amount": "0-3-4-6-9", "link": ...}, ...]}`. In practice **only the first talent in the list (`talents[0]`, always Normal Attack) has this populated** - Skill and Burst store `level_materials: {}` (empty dict, no `"level"` key), because their costs are identical to Attack's in-game and aren't duplicated in the data. Any code walking materials from Skill/Burst needs to fall back to `talents[0]`, not read an empty list as "no materials."
- For every other talent type (passives - the exact type string varies per character, e.g. `"1st Ascension Passive"`, `"Utility Passive"`, `"Moonsign Benediction Passive"`) `level_materials` is a **plain string**, not a dict - it holds an unlock-condition label (`"A1"`, `"A4"`, `"Utiliy (Auto-unlocked)"`, etc.), completely unrelated in shape to the active-talent case. Code that assumes `level_materials` is always a dict and calls `.get("level", [])` on it unconditionally will crash (`AttributeError`) the moment it reaches a passive talent - check `isinstance(level_materials, dict)` first.
- Because Skill/Burst duplicate Attack's cost data by convention, don't insert/count materials once per talent in that list - do it once, from `talents[0]`, or totals come out inflated by however many active talents happen to share that cost (confirmed: 3x for a typical character with Attack+Skill+Burst).

**Amount strings have two unrelated encodings depending on where they live** - see §3.3 for the full talent-side breakdown:
- `talents[].level_materials.level[].amount`: a `"-"`-joined positional progression string (talent side). Sum every digit segment for a grand total; don't assume exactly 2 segments.
- `ascension_levels[material][tier].amount`: a single plain integer, already per-tier, no encoding to parse.


### 3.3 🧩 Talent Material Retrieval: Handling Positional Data
The material amount string is a compressed, positionally indexed list (e.g., `"0-0-0-0-0-4-6-9-12"`). Zeros are placeholders used to keep the alignment consistent across different material types, some of which don't start dropping until a later level-up step.

* A. Understanding the Positional Indexing

The code parses the raw string into an `amounts` list, split on `-`. **The list is 0-indexed, and index `i` always maps to `amounts_by_index[i]`, the same variable the code actually uses** - this section previously described a different, sparser scheme (`materials_by_level[1]`, `[6]`, `[9]`) that never matched the real implementation; ignore any older version of this section if you have one cached. The header shown to the user is `f"Level {idx + 1} -> {idx + 2}"`:

| Index | Level-Up Step |
|---|---|
| 0 | 1 -> 2 |
| 1 | 2 -> 3 |
| 2 | 3 -> 4 |
| 3 | 4 -> 5 |
| 4 | 5 -> 6 |
| 5 | 6 -> 7 |
| 6 | 7 -> 8 |
| 7 | 8 -> 9 |
| 8 | 9 -> 10 |

This matches the table in §4.1 exactly - if the two ever disagree again, trust §4.1's table and the code, not prose.

* B. The Logic for Dealing with Zero Placeholders

We use a conditional `if amount > 0:` check to ignore placeholders while respecting the positional alignment.

  * Case 1: Standard Progression (Talent Books & Common Drops)

    A 9-segment string maps directly, one segment per index, skipping zeros:
    ```py
    for i, amt in enumerate(amounts):
        if i < 9 and amt > 0:
            mats_by_index[i].append(...)
    ```

  * Case 2: Weekly Boss Drops (4-item short list)

    Weekly-boss materials never appear before level 60 (the level 6->7 step), so instead of storing a 9-segment string with 5 leading zeros, they're stored as a **4-item list** covering indices 5-8 only. Detected purely by `len(amounts) == 4` - there is no explicit tag on the material marking it as a boss drop, so this length check must stay reliable; a non-boss material with exactly 4 non-zero level-up steps would currently be misread as a boss material and offset incorrectly. Confirmed as of this writing that no such collision exists in the roster.
    ```py
    elif len(amounts) == 4:  # Weekly Boss Offset
        for i, amt in enumerate(amounts):
            if amt > 0:
                mats_by_index[i + 5].append(...)  # i=0 -> index 5 (Level 6->7)
    ```

  * Case 3: Crown of Insight

    Always a flat `"1"`, pinned directly to index 8 (Level 9->10) regardless of string content:
    ```py
    if "Crown of Insight" in mat_name:
        mats_by_index[8].append({'amt': 1, ...})
    ```

  * Ascension materials use the same `amount > 0` style summing but are NOT positionally encoded - each tier (`"A1"`, `"A2"`, ...) stores one plain integer amount directly, e.g. `ascension_levels["Broken Drive Shaft"]["A1"]["amount"] == 3`. Don't apply the talent parsing logic above to ascension amounts; they're a different shape entirely (see the schema reference below).