GI-Static-Data-Library
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

	*** Major disclaimer: I did use AI for this. I'm new, but I will slowly change the code using my knowledge as I continue adding more stuff to this library :3

A simple Python library for retrieving Genshin Impact character and material data from a JSON file.

Features
Character Data: Access detailed information about characters including their stats, talents, and constellations.

Material Lookup: Find which characters use a specific ascension or talent material.

Data-driven: The library's data is stored in a JSON file (gisl_data.json), making it easy to update and extend.

Installation
You can install this library directly from your local repository using pip.

pip install .

Usage
Here is a quick example of how to use the library to access character data.

Example: Getting Albedo's Talents
from gisl_data_library import get_character_data
import json

albedo_talents = get_character_data("albedo", "talents")
print(json.dumps(albedo_talents, indent=2))

This will output all the talent data for Albedo, which is useful for figuring out which materials you need for your character.

Example: Finding characters by material
from gisl_data_library import find_characters_by_material
import json

characters_with_cecilia = find_characters_by_material("Cecilia")
print(json.dumps(characters_with_cecilia, indent=2))

License
This project is licensed under the MIT License.