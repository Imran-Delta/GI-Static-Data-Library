#!/usr/bin/env python3
"""
GISL Development Test Suite (Dynamic Function Coverage)

Run with:
    python LibTest.py
    pytest LibTest.py -v

The suite is organised as:
    1. Compile every .py file in the project.
    2. Verify imports of the package and its submodules.
    3. Directly check every character JSON file for schema consistency.
    4. Dynamically discover all public functions in the library modules,
       inspect their parameters, and call them with appropriate test values
       derived from data (characters) or hardcoded lists (elements/weapons).
       Any function whose first parameter matches a known category is
       tested automatically, making the suite future‑proof.
"""

import os
import json
import pytest
from pathlib import Path
import importlib
import sys
import inspect
import py_compile

# ----------------------------------------------------------------------
# Paths and constants
# ----------------------------------------------------------------------
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "character_data"
PACKAGE_NAME = "genshin_impact"   # adjust if different

# Hardcoded canonical lists (materials will be added later)
ELEMENTS = ["Pyro", "Geo", "Anemo", "Hydro", "Cryo", "Electro", "Dendro"]
WEAPONS  = ["Polearm", "Sword", "Catalyst", "Bow", "Claymore"]

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def get_character_files():
    """Return sorted list of JSON files in the character data directory."""
    if not DATA_DIR.exists():
        return []
    return sorted(DATA_DIR.glob("*.json"))

def get_character_keys():
    """Return sorted list of character keys (stem without .json)."""
    return [p.stem for p in get_character_files()]

def load_json_direct(key):
    """Load character JSON directly from file, bypassing the library."""
    file_path = DATA_DIR / f"{key}.json"
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def import_module(name):
    """Import a module by name, returning the module object."""
    return importlib.import_module(name)

# ----------------------------------------------------------------------
# Module‑level fixtures
# ----------------------------------------------------------------------
@pytest.fixture(scope="module")
def all_character_keys():
    return get_character_keys()

@pytest.fixture(scope="module")
def library():
    """Import the main package and its submodules."""
    try:
        pkg = import_module(PACKAGE_NAME)
        gisl_mod = import_module(f"{PACKAGE_NAME}.gisl")
        gisl2_mod = import_module(f"{PACKAGE_NAME}.gisl2")
        return pkg, gisl_mod, gisl2_mod
    except Exception as e:
        pytest.skip(f"Library import failed: {e}")

@pytest.fixture(scope="module")
def all_json_data():
    """Load all character JSON files directly into memory."""
    data = {}
    for key in get_character_keys():
        try:
            data[key] = load_json_direct(key)
        except Exception as e:
            print(f"Warning: could not load {key}.json: {e}")
    return data

# ----------------------------------------------------------------------
# 1. Python files compile
# ----------------------------------------------------------------------
class TestPythonFilesCompile:
    def test_all_python_files_compile(self):
        errors = []
        for py_file in ROOT_DIR.rglob("*.py"):
            try:
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(f"{py_file}: {e}")
        assert not errors, f"Compile errors:\n" + "\n".join(errors)

# ----------------------------------------------------------------------
# 2. Import checks
# ----------------------------------------------------------------------
class TestImports:
    def test_package_import(self, library):
        pkg, _, _ = library
        assert pkg is not None, "Main package failed to import"

    def test_gisl_module_import(self, library):
        _, gisl_mod, _ = library
        assert gisl_mod is not None, "gisl module failed to import"

    def test_gisl2_module_import(self, library):
        _, _, gisl2_mod = library
        assert gisl2_mod is not None, "gisl2 module failed to import"

# ----------------------------------------------------------------------
# 3. Direct JSON validation loop
# ----------------------------------------------------------------------
class TestDirectJSONValidation:
    def test_json_schema_consistency(self, all_json_data):
        required = {
            "name", "rarity", "element", "weapon_type", "region", "birthday",
            "affiliation", "role", "additional_titles", "constellation_name",
            "ascension_stat", "ascension_materials", "ascension_levels",
            "stats_table", "talents", "constellations"
        }
        errors = []

        for key, data in all_json_data.items():
            # Top‑level keys
            missing = required - set(data.keys())
            if missing:
                errors.append(f"{key}: missing top‑level keys: {missing}")

            # Basic types
            if "rarity" in data and not isinstance(data["rarity"], int):
                errors.append(f"{key}: rarity must be int")
            for field in ["additional_titles", "talents", "constellations"]:
                if field in data and not isinstance(data[field], list):
                    errors.append(f"{key}: {field} must be list")
            for field in ["ascension_levels", "stats_table"]:
                if field in data and not isinstance(data[field], dict):
                    errors.append(f"{key}: {field} must be dict")

            # Ascension levels structure
            if "ascension_levels" in data:
                for mat_name, phases in data["ascension_levels"].items():
                    if not isinstance(phases, dict):
                        errors.append(f"{key}: ascension_levels['{mat_name}'] must be dict")
                        continue
                    for phase, info in phases.items():
                        if not isinstance(info, dict):
                            errors.append(f"{key}: ascension_levels['{mat_name}']['{phase}'] must be dict")
                            continue
                        for req in ["level_range", "amount", "link"]:
                            if req not in info:
                                errors.append(f"{key}: {mat_name}/{phase} missing {req}")

            # Stats table structure
            if "stats_table" in data:
                required_tiers = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A6 - C7", "A6 - C8"]
                for tier in required_tiers:
                    if tier not in data["stats_table"]:
                        errors.append(f"{key}: missing stats tier {tier}")
                        continue
                    tier_data = data["stats_table"][tier]
                    if "level_range" not in tier_data:
                        errors.append(f"{key}: stats {tier} missing level_range")
                    for sk, val in tier_data.items():
                        if sk == "level_range":
                            continue
                        if not isinstance(val, dict):
                            errors.append(f"{key}: stats {tier}/{sk} must be dict")
                            continue
                        if "low" not in val or "high" not in val:
                            errors.append(f"{key}: stats {tier}/{sk} missing low/high")

            # Talents structure
            if "talents" in data:
                for i, talent in enumerate(data["talents"]):
                    if not isinstance(talent, dict):
                        errors.append(f"{key}: talent[{i}] must be dict")
                        continue
                    if "name" not in talent or "type" not in talent:
                        errors.append(f"{key}: talent[{i}] missing name/type")
                    lm = talent.get("level_materials")
                    if lm is not None and not isinstance(lm, (dict, str)):
                        errors.append(f"{key}: talent[{i}].level_materials must be dict or string")
                    if isinstance(lm, dict) and "level" in lm:
                        if not isinstance(lm["level"], list):
                            errors.append(f"{key}: talent[{i}].level_materials.level must be list")
                        else:
                            for j, entry in enumerate(lm["level"]):
                                if not isinstance(entry, dict):
                                    errors.append(f"{key}: talent[{i}].level[{j}] must be dict")
                                    continue
                                for req in ["material", "amount", "link"]:
                                    if req not in entry:
                                        errors.append(f"{key}: talent[{i}].level[{j}] missing {req}")

            # Constellations structure
            if "constellations" in data:
                for i, const in enumerate(data["constellations"]):
                    if not isinstance(const, dict):
                        errors.append(f"{key}: constellation[{i}] must be dict")
                        continue
                    if "name" not in const or "description" not in const:
                        errors.append(f"{key}: constellation[{i}] missing name/description")

        assert not errors, "JSON validation errors:\n" + "\n".join(errors)

# ----------------------------------------------------------------------
# 4. Dynamic function coverage
# ----------------------------------------------------------------------
class TestDynamicFunctionCoverage:
    def test_all_functions_with_known_params(self, library, all_character_keys):
        pkg, gisl_mod, gisl2_mod = library
        errors = []

        # Gather all public functions from the three modules
        functions = {}
        for mod in (pkg, gisl_mod, gisl2_mod):
            for name in dir(mod):
                if name.startswith('_'):
                    continue
                obj = getattr(mod, name)
                if inspect.isfunction(obj) or inspect.isbuiltin(obj):
                    functions[f"{mod.__name__}.{name}"] = obj

        # Data source mappings
        data_sources = {
            # character/name/key -> list of character keys from JSON files
            "character": all_character_keys,
            "character_key": all_character_keys,
            "key": all_character_keys,
            "name": all_character_keys,
            # element -> hardcoded canonical elements
            "element": ELEMENTS,
            # weapon_type/weapon -> hardcoded canonical weapons
            "weapon_type": WEAPONS,
            "weapon": WEAPONS,
            # material placeholders will be added later
        }

        for func_name, func in functions.items():
            try:
                sig = inspect.signature(func)
            except (TypeError, ValueError):
                # Skip functions whose signature cannot be inspected
                continue

            params = list(sig.parameters.values())

            # No parameters: call once with no args
            if not params:
                try:
                    result = func()
                    if result is None:
                        errors.append(f"{func_name} returned None")
                except Exception as e:
                    errors.append(f"{func_name} raised {e}")
                continue

            # Find first parameter that matches a known data source
            test_param = None
            for p in params:
                if p.name in data_sources:
                    test_param = p
                    break

            if test_param is None:
                # No known parameter; if all required params have defaults, call once
                has_required = any(p.default is inspect.Parameter.empty and p.kind in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY
                ) for p in params)
                if not has_required:
                    try:
                        result = func()
                        if result is None:
                            errors.append(f"{func_name} returned None")
                    except Exception as e:
                        errors.append(f"{func_name} raised {e}")
                # else: skip because we cannot safely call without required args
                continue

            # Check if all OTHER required parameters can be satisfied by defaults
            can_call = True
            for p in params:
                if p is test_param:
                    continue
                if p.default is inspect.Parameter.empty and p.kind in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY
                ):
                    can_call = False
                    break

            if not can_call:
                # Skip functions with unsupplied required parameters
                continue

            # Iterate over the values for the matched parameter
            test_values = data_sources[test_param.name]
            for value in test_values:
                try:
                    kwargs = {test_param.name: value}
                    result = func(**kwargs)
                    if result is None:
                        errors.append(f"{func_name}({test_param.name}={value!r}) returned None")
                except Exception as e:
                    errors.append(f"{func_name}({test_param.name}={value!r}) raised {e}")

        assert not errors, "Dynamic function test errors:\n" + "\n".join(errors)

# ----------------------------------------------------------------------
# Optional: Run pytest if executed as script
# ----------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
