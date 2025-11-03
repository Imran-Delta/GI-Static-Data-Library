# GI Static Data Library
• If contact is needed urgently, please send me a friend request in Discord, @sys_delta. I'm much more active on discord than gmail.
```
License
This project is licensed under the MIT License.
```

This is my personal project of making a library containing information on items, characters and weapons from a game I play, named Genshin Impact. I made this library to serve as a static, usable offline library. For some this may be useful. For me it's just a hobby.

## Current Details:
`REQUIRED DEPENDENCY: Packaging`
The newly added level 95 and level 100's ascension stats, and the moonsign stuff have not been added yet. I have to create the logic for it to prevent errors.

Characters Added:
 * Aino, Albedo (IGNORE THE KAZUHA, IT'S A PLACEHOLDER)

# 🚀 genshin-impact Data Library Integration Guide

The genshin-impact library provides immediate and safe access to static character and material data. This guide covers installation, core retrieval, and Discord implementation using modern slash commands and autocompletion.
The core package for all data functions is genshin_impact.
# 1. Installation and Safe Core Retrieval
Begin by installing the library and setting up a safe import pattern to prevent your application from crashing if the dependency is missing. And also optionally an update check.

### 💾 Installation
`pip install genshin-impact`

### 🐍 Safe Data Retrieval Pattern (Recommended)
```py
import discord
from discord import app_commands

try:
    # Import the main data lookup function
    from genshin_impact import get_character_data
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
### 🔎 Checking for Updates
The check_for_updates() function allows you to programmatically check the PyPI repository to see if a newer version of the genshin-impact package is available. It returns a dictionary containing the update status, current version, latest version, and a user-friendly message.
### CRITICAL: Import the update function from the library
```py
from genshin_impact import check_for_updates

def check_for_new_version():
    # Call the function to get the status dictionary
    update_status = check_for_updates()

    # Handle the result
    if update_status.get("update_available"):
        # A new version is available, provide the message and instruction
        print(f"✨ UPDATE AVAILABLE! {update_status['message']}")
        # Example output: A new version (0.0.4) is available! Current version is 0.0.3. Run 'pip install --upgrade genshin-impact'.
    elif "Error" in update_status.get("message", ""):
        # An error occurred (e.g., package not installed, no connection to PyPI)
        print(f"⚠️ Update Check Failed: {update_status['message']}")
    else:
        # You are running the latest version or a newer dev build
        print(f"✅ Status: {update_status['message']}")
        # Example output: You are running the latest version: 0.0.3.

# Call the check function (e.g., on application startup)
check_for_new_version()
```
# 2. Discord Autocomplete for Slash Commands
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
# 3. Accessing Detailed Levels and Tiers
The dictionary returned by get_character_data(name) contains structured information. To display all levels (e.g., C1-C6, or all Ascension Levels), you must iterate through the respective lists or dictionaries.
| Requested Detail | Access Key | Data Structure | Display Logic |
|---|---|---|---|
| Talent Info / Levels | data['talents'] | list of dict | Iterate to display the name and description of each of the three main talents. |
| Constellation Info / Levels | data['constellations'] | list of dict | Iterate (indices 0-5) to display the name and description for each Constellation (C1 to C6). |
| Character Level | data['ascension_levels'] | dict (keys are level brackets) | Iterate over keys (.items()) to display all level milestones and their associated stat changes. |
# 4. 🧩 Talent Material Retrieval: Handling Positional Data
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
The core implementation uses a conditional check `if amount > 0:` to ignore placeholders while respecting the positional alignment.

   * Case 1: Standard Progression (Talent Books & Common Drops)
    For materials covering a wide range (often including placeholders, like T3 books), the standard index mapping works by using the check to skip initial zeros:
    
      1. The `if amount > 0:` check skips the zero placeholders (e.g., the first five '0's)
      2.
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

# `- Update LOGS -`
# -Update 0.0.9 to 0.1.1-
   * Added Aino
   * Added character list
   * Added pending list
   * Added personal description.
   * Fixed A DAM "CLOSING" ISSUE
   * Added a dependency: Packaging


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