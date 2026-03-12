# GI Static Data Library
• If contact is needed urgently, please send me a friend request in Discord, @sys_delta. I'm much more active on discord than gmail.
```
License
This project is licensed under the BSD 3-Clause License.
```

This is my personal project of making a library containing information on items, characters and weapons from a game I play, named Genshin Impact. I made this library to serve as a static, usable offline library. For some this may be useful. For me it's just a hobby.

# Current Details:
`REQUIRED DEPENDENCY (Installing GISDL also installs the dependencies): Packaging and Requests`
Also- currently adding a sql backend for performance future proofing, old methods shall not break- (I hope T_T)
MOONSIGN ADDED!

Characters Added:
 * Aino, Albedo (IGNORE THE KAZUHA, IT'S A PLACEHOLDER)

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
The check_for_updates() function allows you to programmatically check the PyPI repository to see if a newer version of the genshin-impact package is available. Using Python 3.10+ Structural Pattern Matching, you can handle specific build statuses like development modes or outdated dev versions.
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
| --- | --- | --- | --- |
| **Ascension Materials** | `get_ascension_data(name, opt)` | Formatted String or List | Focuses on items like Gems, Boss Mats, and Specialties for A1-A6. |
| **Ascension Stats** | `get_ascension_stats(name)` | Formatted String | Displays HP, ATK, and DEF growth from A0 up to A6-C8 (Level 100). |
| **Full Progression** | `get_ascension_levels(name, opt)` | Formatted String | Combines materials and stats; automatically labels Level 100 as "Stat Increase Only". |

By providing these three distinct entry points, users can choose between a concise farming list, a theory-crafting stat sheet, or a full overview of character investment.

# 4. 🧩 Talent Material Retrieval (get_talent_materials)
This method handles internal mapping for talent levels (Index 0 = Level 1->2, Index 8 = Level 9->10). It automatically includes Weekly Boss materials and the Crown of Insight at the correct levels.
Options:
 * "all": Formatted string with bold headers and Markdown hyperlinks (Ideal for Discord Embeds).
 * "alltext": Plain text string with headers but no links/bolding (Uses \n instead of #).
 * "allraw": Returns the raw material list as a list of dictionaries.
 * 0-8 (Integer/String): Returns the formatted requirements for a specific level progression index.
⚙️ Internal Logic: Index Mapping
The library internally handles the positional offsets for materials so the user can use a simple 0-8 index system:

| Internal Index | Level-Up Step | Included Items |
|---|---|---|
| 0 | 1 -> 2 | Books & Common Mats |
| 5 | 6 -> 7 | Weekly Boss Mats start here |
| 8 | 9 -> 10 | Includes Crown of Insight |

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

# `- Update LOGS -`
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


# LEGACY METHODS!

# 3.1 Discord Autocomplete for Slash Commands
For a seamless user experience, use the hidden function get_all_characters_data to provide real-time character name suggestions in your slash commands (app_commands).
⚙️ Autocomplete Logic
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
# 3.2 Accessing Detailed Levels and Tiers
The dictionary returned by get_character_data(name) contains structured information. To display all levels (e.g., C1-C6, or all Ascension Levels), you must iterate through the respective lists or dictionaries.
| Requested Detail | Access Key | Data Structure | Display Logic |
|---|---|---|---|
| Talent Info / Levels | data['talents'] | list of dict | Iterate to display the name and description of each of the three main talents. |
| Constellation Info / Levels | data['constellations'] | list of dict | Iterate (indices 0-5) to display the name and description for each Constellation (C1 to C6). |
| Character Level | data['ascension_levels'] | dict (keys are level brackets) | Iterate over keys (.items()) to display all level milestones and their associated stat changes. |

### 3.3 🧩 Talent Material Retrieval: Handling Positional Data (RAW - Legacy) [You do the formatting yourself]
The amount string for talent materials is a compressed, positionally indexed list of quantities, where zeros (0) are used as crucial placeholders to maintain alignment across all level-up steps.
### A. Understanding the Positional Indexing
The code parses the raw string (e.g., "0-0-0-0-0-4-6-9-12") into an amounts list. The index of an item in this list directly corresponds to a specific level-up step:
| List Index (i) | Level-Up Step | Resulting Code Index |
|---|---|---|
| 0 | 1 \to 2 | materials_by_level[1] |
| ... | ... | ... |
| 5 | 6 \to 7 | materials_by_level[6] |
| 8 | 9 \to 10 | materials_by_level[9] |
### B. The Logic for Dealing with Zero Placeholders
The core implementation uses a conditional check if amount > 0: to ignore placeholders while respecting the positional alignment.
 * Case 1: Standard Progression (Talent Books & Common Drops)
   For materials covering a wide range (often including placeholders, like T3 books), the standard index mapping works by using the check to skip initial zeros:
    
      1. The `if amount > 0:` check skips the zero placeholders (e.g., the first five '0's)
      2. Py Code:
      ```py
      i+1 correctly maps index 5 to level 6 (6->7 step)
      if amount > 0:
      materials_by_level[i + 1].append(...)
      ```

  * Case 2: Weekly Boss Drops (Hardcoded Exception)
      Weekly Boss materials often omit the leading zero placeholders, resulting in a short list (e.g., only 4 items for levels 7 through 10). The code must identify this list size and apply a hardcoded offset.
      
    1.  Identify a short list (e.g., len 4) and apply a starting offset
    ```py
    elif len(amounts) == 4:
    start_level = 6 # Set the start of the   level range
    ```
    2.
    ```py
    start_level + i maps index 0 to level 6 (6->7 step)
    materials_by_level[start_level + i].append(...)
    ```