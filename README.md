GI-Static-Data-Library
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

Contributing
Contributions are welcome! If you would like to add new data or improve existing data, please:

Fork the repository.

Create a new branch (git checkout -b feature/your-feature-name).

Add your changes.

Commit your changes (git commit -m "Add new feature").

Push to the branch (git push origin feature/your-feature-name).

Create a pull request on GitHub.

License
This project is licensed under the MIT License.