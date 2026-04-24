"""
A static library for retrieving Genshin Impact character and material data.
The data is loaded from the bundled character_data directory into a SQLite database.
A monolithic dictionary (gisl_data) is provided for backward compatibility,
but is built lazily only when needed.
"""
import json
import sqlite3
import logging
import time
import os
import sys
from pathlib import Path
from contextlib import closing

# For version checking (Dynamic, avoids __init__.py circular import)
import importlib.metadata
import requests
from packaging.version import parse as parse_version

logger = logging.getLogger(__name__)

# Package configuration
PACKAGE_NAME = 'genshin_impact'
DATA_DIR = 'character_data'
PYPI_PACKAGE_NAME = 'genshin-impact'

try:
    __version__ = importlib.metadata.version(PYPI_PACKAGE_NAME)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"  # Fallback if not installed via pip

# ----------------------------------------------------------------------
# SQLite database (persisted to disk if possible)
# ----------------------------------------------------------------------
_conn = None                 # database connection
_gisl_data = None            # legacy monolithic dictionary (built lazily)
_tables_initialized = False  # indicates whether the DB is ready

def _get_data_path():
    """Return the Path to the character_data directory, trying multiple methods."""
    try:
        import importlib.resources as pkg_resources
        if hasattr(pkg_resources, 'files'):
            data_path = pkg_resources.files(PACKAGE_NAME) / DATA_DIR
            if data_path.is_dir():
                return data_path
    except (ImportError, AttributeError, Exception):
        pass

    # Fallback to local relative path
    fallback_path = Path(__file__).parent / DATA_DIR
    if fallback_path.is_dir():
        return fallback_path
    return None

def _get_db_path():
    """
    Determine the best location for the persistent database file.
    Returns a Path object or None (fallback to :memory:).
    """
    # 1. Try to use the directory where this script resides
    lib_dir = Path(__file__).parent
    db_name = f"gisl_v{__version__.replace('.', '_')}.db"
    lib_path = lib_dir / db_name

    try:
        # Test write access by touching a temp file
        test_file = lib_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        return lib_path
    except (OSError, PermissionError):
        pass

    # 2. Try system cache directory
    if sys.platform == "win32":
        cache_root = os.environ.get("LOCALAPPDATA")
        if cache_root:
            cache_dir = Path(cache_root) / "genshin-impact" / "cache"
        else:
            cache_dir = Path.home() / "AppData" / "Local" / "genshin-impact" / "cache"
    elif sys.platform == "darwin":  # macOS
        cache_dir = Path.home() / "Library" / "Caches" / "genshin-impact"
    else:  # Linux / other Unix
        cache_dir = Path.home() / ".cache" / "genshin-impact"

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / db_name

    try:
        test_file = cache_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        return cache_path
    except (OSError, PermissionError):
        pass

    # 3. Fallback: in-memory database (no persistence)
    return None

def _db_needs_rebuild(conn):
    """Check if the connected database has the correct version."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT value FROM metadata WHERE key='version'")
        row = cur.fetchone()
        if row and row[0] == __version__:
            return False
    except sqlite3.OperationalError:
        # Table 'metadata' probably doesn't exist
        pass
    return True

def _build_db_from_json(conn):
    """Build the database schema and load all character JSON files."""
    with closing(conn.cursor()) as c:
        # ---- Tables ----
        c.execute("""
            CREATE TABLE character_core (
                id INTEGER PRIMARY KEY,
                key TEXT UNIQUE,
                name TEXT,
                rarity INTEGER,
                element TEXT,
                weapon_type TEXT,
                region TEXT,
                full_json TEXT
            )
        """)

        c.execute("""
            CREATE TABLE material_index (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                link TEXT
            )
        """)

        c.execute("""
            CREATE TABLE character_material (
                character_id INTEGER,
                material_id INTEGER,
                usage_type TEXT,
                amount TEXT,  -- raw amount string (e.g., "3-6")
                FOREIGN KEY(character_id) REFERENCES character_core(id),
                FOREIGN KEY(material_id) REFERENCES material_index(id)
            )
        """)
        c.execute("CREATE INDEX idx_char_mat ON character_material(material_id)")

        # ---- Metadata table for version and other info ----
        c.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)")
        c.execute("INSERT INTO metadata (key, value) VALUES (?, ?)", ("version", __version__))

        # ---- Locate data directory ----
        data_path = _get_data_path()
        if data_path is None:
            logger.error(f"Data directory '{DATA_DIR}' not found.")
            return

        # ---- Iterate over all .json files ----
        for json_file in data_path.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    char_data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")
                continue

            char_key = json_file.stem

            # Insert character core
            c.execute("""
                INSERT INTO character_core (key, name, rarity, element, weapon_type, region, full_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                char_key,
                char_data.get("name", ""),
                char_data.get("rarity", 0),
                char_data.get("element", ""),
                char_data.get("weapon_type", ""),
                char_data.get("region", ""),
                json.dumps(char_data, ensure_ascii=False)
            ))
            char_id = c.lastrowid

            # ---- Index materials ----
            mat_cache = {}

            def get_material_id(name, link=""):
                if name in mat_cache:
                    return mat_cache[name]
                c.execute("INSERT OR IGNORE INTO material_index (name, link) VALUES (?, ?)",
                          (name, link))
                c.execute("SELECT id FROM material_index WHERE name = ?", (name,))
                row = c.fetchone()
                if row:
                    mat_id = row["id"]
                    mat_cache[name] = mat_id
                    return mat_id
                return None

            # Ascension materials
            asc_levels = char_data.get("ascension_levels", {})
            for full_mat_name, tiers in asc_levels.items():
                mat_id = get_material_id(full_mat_name, "")
                if mat_id is None:
                    continue
                for tier, info in tiers.items():
                    amount = info.get("amount", 0)
                    c.execute("""
                        INSERT INTO character_material (character_id, material_id, usage_type, amount)
                        VALUES (?, ?, ?, ?)
                    """, (char_id, mat_id, "ascension", str(amount)))

            # Talent materials
            talents = char_data.get("talents", [])
            na_materials = talents[0].get("level_materials", {}) if talents else {}

            for talent in talents:
                lvl_mats = talent.get("level_materials")

                if isinstance(lvl_mats, dict) and not lvl_mats.get("level"):
                    lvl_mats = na_materials

                if isinstance(lvl_mats, dict):
                    for mat_entry in lvl_mats.get("level", []):
                        mat_name = mat_entry.get("material") or mat_entry.get("name")
                        if not mat_name:
                            continue
                        amount = mat_entry.get("amount", "")
                        link = mat_entry.get("link", "")
                        mat_id = get_material_id(mat_name, link)
                        if mat_id is None:
                            continue
                        c.execute("""
                            INSERT INTO character_material (character_id, material_id, usage_type, amount)
                            VALUES (?, ?, ?, ?)
                        """, (char_id, mat_id, "talent", str(amount)))

        conn.commit()

def _init_db():
    """Initialize the SQLite database (persistent or in-memory)."""
    global _conn, _tables_initialized

    start = time.perf_counter()
    db_path = _get_db_path()

    if db_path is not None:
        # Persistent file: check if it exists and has correct version
        if db_path.exists():
            # Try to connect and verify version
            try:
                test_conn = sqlite3.connect(str(db_path))
                test_conn.row_factory = sqlite3.Row
                if not _db_needs_rebuild(test_conn):
                    # Database is good
                    _conn = test_conn
                    _tables_initialized = True
                    logger.info(f"Connected to existing database at {db_path}")
                    return
                else:
                    test_conn.close()
                    logger.info("Database version mismatch, rebuilding...")
            except Exception as e:
                logger.warning(f"Could not open existing database: {e}. Rebuilding...")
                try:
                    test_conn.close()
                except:
                    pass

        # Need to rebuild: create a new database file
        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(db_path))
        _conn.row_factory = sqlite3.Row
        _build_db_from_json(_conn)
        _tables_initialized = True
        logger.info(f"Built new database at {db_path} in {time.perf_counter() - start:.3f}s")
    else:
        # Fallback to in-memory
        _conn = sqlite3.connect(":memory:")
        _conn.row_factory = sqlite3.Row
        _build_db_from_json(_conn)
        _tables_initialized = True
        logger.info(f"Built in-memory database in {time.perf_counter() - start:.3f}s")

# Initialize the database immediately when module is imported
_init_db()

# ----------------------------------------------------------------------
# Lazy monolithic dictionary loader
# ----------------------------------------------------------------------
def _load_monolith():
    """Populate _gisl_data by reading full_json from the database."""
    global _gisl_data
    if _gisl_data is not None:
        return
    _gisl_data = {}
    with closing(_conn.cursor()) as c:
        c.execute("SELECT key, full_json FROM character_core")
        for row in c.fetchall():
            _gisl_data[row["key"]] = json.loads(row["full_json"])
    logger.debug("Monolithic dictionary built from database")

def _ensure_monolith():
    """Make sure the monolithic dict is loaded (for legacy functions)."""
    if _gisl_data is None:
        _load_monolith()


def get_all_character_names() -> list[tuple[str, str]]:
    """
    Returns a list of (key, name) for all characters.
    Used for fast autocomplete without loading full JSON.
    """
    if not _tables_initialized:
        return []
    with closing(_conn.cursor()) as c:
        c.execute("SELECT key, name FROM character_core")
        return [(row["key"], row["name"]) for row in c.fetchall()]

def get_all_material_names() -> list[str]:
    """Return all material names from the index (for autocomplete)."""
    if not _tables_initialized:
        return []
    with closing(_conn.cursor()) as c:
        c.execute("SELECT name FROM material_index ORDER BY name")
        return [row["name"] for row in c.fetchall()]

def find_characters_by_criteria(material: str = None, element: str = None, weapon: str = None) -> list[str]:
    """
    Find character names that match all given criteria (AND).
    Uses SQL for speed.
    """
    if not _tables_initialized:
        return []

    query = """
        SELECT DISTINCT c.name
        FROM character_core c
    """
    params = []
    conditions = []

    if material:
        query += """
            JOIN character_material cm ON c.id = cm.character_id
            JOIN material_index m ON cm.material_id = m.id
        """
        conditions.append("LOWER(m.name) = ?")
        params.append(material.lower())

    if element:
        conditions.append("LOWER(c.element) = ?")
        params.append(element.lower())

    if weapon:
        conditions.append("LOWER(c.weapon_type) = ?")
        params.append(weapon.lower())

    if not conditions:
        return []  # No criteria – return empty list

    query += " WHERE " + " AND ".join(conditions)

    with closing(_conn.cursor()) as c:
        c.execute(query, params)
        return [row["name"] for row in c.fetchall()]

# ----------------------------------------------------------------------
# Legacy functions (exactly as in original gisl.py)
# ----------------------------------------------------------------------

def get_character_data(character_key: str) -> dict | None:
    """
    Retrieves the full data for a specific character by their key.
    (Legacy version – uses the monolithic dictionary.)
    """
    _ensure_monolith()
    return _gisl_data.get(character_key.lower())

def get_all_characters_data() -> dict:
    """
    Returns the full dictionary of all character data (legacy).
    """
    _ensure_monolith()
    return _gisl_data

def find_characters_by_material(material_name: str) -> list:
    """
    Finds and returns a list of characters that use a given ascension or talent material.
    (Legacy version – uses the monolithic dictionary.)
    """
    _ensure_monolith()
    material_name = material_name.lower()
    characters_using_material = {}

    for char_key, char_data in _gisl_data.items():
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
    (Legacy version – uses the monolithic dictionary.)
    """
    _ensure_monolith()
    matching_characters = []
    for char_name, char_data in _gisl_data.items():
        if 'element' in char_data and char_data['element'].lower() == element_name.lower():
            matching_characters.append(char_data['name'])
    return matching_characters

def find_characters_by_weapon_type(weapon_type: str) -> list:
    """
    Finds and returns a list of character names that match the given weapon type.
    (Legacy version – uses the monolithic dictionary.)
    """
    _ensure_monolith()
    matching_characters = []
    for char_name, char_data in _gisl_data.items():
        if 'weapon_type' in char_data and char_data['weapon_type'].lower() == weapon_type.lower():
            matching_characters.append(char_data['name'])
    return matching_characters

def get_talent_materials(name: str, option: str = "all") -> any:
    """
    Retrieves talent level‑up materials for a character.
    (Legacy version – uses get_character_data, which now uses the dict.)
    """
    name_key = name.lower()
    char_data = get_character_data(name_key)
    if not char_data:
        return f"Character '{name}' not found."

    try:
        talents_list = char_data.get('talents', [])
        mats_list = talents_list[0].get('level_materials', {}).get('level', [])
    except (IndexError, AttributeError):
        return "No talent data available."

    if option == "allraw":
        return mats_list

    # Mapping Indices 0-8 to Levels 1->2 through 9->10
    mats_by_index = {i: [] for i in range(9)}

    for material in mats_list:
        mat_name = material.get('material', 'N/A')
        amt_str = str(material.get('amount', '0'))
        link = material.get('link', '')
        amounts = [int(a) for a in amt_str.split('-') if a.strip().isdigit()]

        # Boss/Crown Logic handled internally
        if "Crown of Insight" in mat_name:
            mats_by_index[8].append({'amt': 1, 'name': mat_name, 'link': link})
        elif len(amounts) == 4: # Weekly Boss Offset
            for i, amt in enumerate(amounts):
                if amt > 0: mats_by_index[i + 5].append({'amt': amt, 'name': mat_name, 'link': link})
        else: # Standard Progression
            for i, amt in enumerate(amounts):
                if i < 9 and amt > 0: mats_by_index[i].append({'amt': amt, 'name': mat_name, 'link': link})

    def format_level(idx, text_only=False):
        if not mats_by_index[idx]: return None
        header = f"Level {idx + 1} -> {idx + 2}"
        display_header = f"**{header}**" if not text_only else header
        lines = [f"- {m['amt']}x {m['name']}" if text_only or not m['link'] else f"- [{m['amt']}x {m['name']}]({m['link']})" for m in mats_by_index[idx]]
        return f"{display_header}\n" + "\n".join(lines)

    # Specific Index Check
    try:
        idx_opt = int(option)
        if 0 <= idx_opt <= 8:
            return format_level(idx_opt) or f"No data for index {idx_opt}."
    except ValueError:
        pass

    # 'all' vs 'alltext'
    is_text = (option == "alltext")
    output = [format_level(i, text_only=is_text) for i in range(9) if format_level(i, text_only=is_text)]
    return ("\n\n" if not is_text else "\n").join(output) if output else "No talent data found."

def get_ascension_data(character_key: str, option: str = "all") -> str | dict | None:
    """
    Retrieves and formats ascension materials for a character.
    (Legacy version – uses get_character_data.)
    """
    char_data = get_character_data(character_key)
    if not char_data or 'ascension_levels' not in char_data:
        return None

    asc_data = char_data['ascension_levels']
    # Dynamically find all unique ascension tags (A1, A2, etc.)
    all_tags = sorted(list(set(
        tag for mat_info in asc_data.values() for tag in mat_info.keys()
    )), key=lambda x: (len(x), x)) # Sorts A1 before A10

    # Build internal list of materials per ascension step
    mats_by_index = [[] for _ in range(len(all_tags))]

    for mat_name, levels in asc_data.items():
        for i, tag in enumerate(all_tags):
            if tag in levels:
                info = levels[tag]
                mats_by_index[i].append({
                    'amt': info.get('amount', 0),
                    'name': mat_name,
                    'link': info.get('link'),
                    'range': info.get('level_range', 'N/A')
                })

    def format_asc_level(idx, text_only=False):
        if idx >= len(mats_by_index) or not mats_by_index[idx]:
            return None

        tag = all_tags[idx]
        # Get range from first material in list
        lvl_range = mats_by_index[idx][0]['range']
        header = f"Ascension {tag} ({lvl_range})"

        display_header = f"**{header}**" if not text_only else header
        lines = []
        for m in mats_by_index[idx]:
            line = f"- {m['amt']}x {m['name']}"
            if not text_only and m['link']:
                line = f"- [{m['amt']}x {m['name']}]({m['link']})"
            lines.append(line)

        return f"{display_header}\n" + "\n".join(lines)

    # Handle Options
    if option == "allraw":
        return mats_by_index

    if option in ["all", "alltext"]:
        is_text = (option == "alltext")
        results = [format_asc_level(i, is_text) for i in range(len(mats_by_index))]
        return "\n\n".join(filter(None, results))

    try:
        idx_opt = int(option)
        return format_asc_level(idx_opt) or f"No data for index {idx_opt}"
    except (ValueError, IndexError):
        return f"Invalid option: {option}. Use 0-{len(all_tags)-1}, 'all', 'alltext', or 'allraw'."

def get_ascension_levels(character_key: str, option: str = "all") -> str | list | None:
    """
    Retrieves ascension data. Levels A1-A6 show materials;
    Levels A7+ (Level 100 logic) show stats only.
    (Legacy version – uses get_character_data.)
    """
    char_data = get_character_data(character_key)
    if not char_data:
        return None

    asc_mats = char_data.get('ascension_levels', {})
    stats_table = char_data.get('stats_table', {})

    # Identify all unique tiers from both mats and stats
    all_tiers = sorted(list(set(list(stats_table.keys()))), key=lambda x: (len(x), x))
    # Remove A0 as it's the base state
    if "A0" in all_tiers: all_tiers.remove("A0")

    processed_data = []
    for tier in all_tiers:
        tier_info = {"tier": tier, "range": "", "mats": [], "stats": {}}

        # Get Stats
        if tier in stats_table:
            tier_info["range"] = stats_table[tier].get("level_range", "")
            tier_info["stats"] = {k: v for k, v in stats_table[tier].items() if k != "level_range"}

        # Get Mats (A1-A6)
        for mat_name, levels in asc_mats.items():
            if tier in levels:
                tier_info["mats"].append({
                    "name": mat_name,
                    "amount": levels[tier].get("amount"),
                    "link": levels[tier].get("link")
                })
        processed_data.append(tier_info)

    def format_output(data_list, text_only=False):
        output = []
        for item in data_list:
            header = f"Ascension {item['tier']} ({item['range']})"
            res = [f"**{header}**" if not text_only else header]

            if item['mats']:
                res.append("Materials:")
                for m in item['mats']:
                    line = f"- {m['amount']}x {m['name']}"
                    if not text_only and m['link']:
                        line = f"- [{m['amount']}x {m['name']}]({m['link']})"
                    res.append(line)
            else:
                res.append("*No materials required (Stat Increase Only)*")

            res.append("Stats Gained:")
            for stat, val in item['stats'].items():
                res.append(f"- {stat}: {val.get('high')}")
            output.append("\n".join(res))
        return "\n\n".join(output)

    # Handle Options
    if option == "allraw": return processed_data
    if option == "all": return format_output(processed_data)
    if option == "alltext": return format_output(processed_data, True)

    try:
        idx = int(option)
        return format_output([processed_data[idx]])
    except:
        return f"Invalid option. Use 0-{len(processed_data)-1} or 'all'."

def get_ascension_stats(character_key: str) -> str:
    """
    Displays only the stat growth for all ascension tiers (A1 through A7+).
    (Legacy version – uses get_character_data.)
    """
    char_data = get_character_data(character_key)
    if not char_data or 'stats_table' not in char_data:
        return f"No stat data found for {character_key}."

    stats_table = char_data['stats_table']
    # Sort tiers: A0, A1... A6, A6-C7, A6-C8
    tiers = sorted(stats_table.keys(), key=lambda x: (len(x), x))

    output = [f"--- {char_data.get('name', character_key)} Stat Progression ---"]

    for tier in tiers:
        data = stats_table[tier]
        header = f"Tier {tier} ({data.get('level_range', 'N/A')})"
        output.append(f"**{header}**")

        for stat, values in data.items():
            if stat != "level_range":
                # Show the range of the stat for that tier
                output.append(f"- {stat}: {values.get('low')} -> {values.get('high')}")
        output.append("") # Spacer

    return "\n".join(output)

def check_for_updates() -> dict:
    """
    Checks PyPI for updates and intelligently handles Dev/Beta builds.
    """
    try:
        # 1. Get current installed version
        current_version_str = __version__
        if current_version_str == "0.0.0":
            return {
                "update_available": False,
                "message": "GI_STATIC_DATA_LIBRARY: Error: The package is not installed via pip, version unknown."
            }

        current_version = parse_version(current_version_str)

        # 2. Query PyPI API
        pypi_url = f"https://pypi.org/pypi/{PYPI_PACKAGE_NAME}/json"
        response = requests.get(pypi_url, timeout=5)
        response.raise_for_status()

        data = response.json()
        latest_version_str = data['info']['version']
        latest_version = parse_version(latest_version_str)

        # 3. Intelligent Version Logic

        # If the local version is a pre-release (dev, alpha, beta, rc)
        # OR if it's strictly newer than what's on PyPI
        if current_version.is_prerelease or current_version > latest_version:
            # Check if there's actually a newer stable version out that we should move to
            if latest_version > current_version:
                return {
                    "update_available": True,
                    "status": "outdated_dev",
                    "message": f"GI_STATIC_DATA_LIBRARY: Outdated Dev Build ({current_version_str}). New stable {latest_version_str} is available!"
                }
            else:
                return {
                    "update_available": False,
                    "status": "dev",
                    "message": f"GI_STATIC_DATA_LIBRARY: Running Dev Build / Open Beta ({current_version_str})."
                }

        # Standard Version Logic for regular users
        if latest_version > current_version:
            return {
                "update_available": True,
                "status": "update",
                "message": f"GI_STATIC_DATA_LIBRARY: A new version ({latest_version_str}) is available! Run 'pip install --upgrade {PYPI_PACKAGE_NAME}'."
            }

        return {
            "update_available": False,
            "status": "ok",
            "message": f"GI_STATIC_DATA_LIBRARY: You are running the latest version: {current_version_str}."
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

# ----------------------------------------------------------------------
# New SQL‑based functions (for speed)
# ----------------------------------------------------------------------

def _parse_amount(amount_str: str) -> int:
    if not amount_str:
        return 0
    parts = amount_str.split('-')
    if len(parts) == 2:
        try:
            low, high = int(parts[0]), int(parts[1])
            return low + high
        except:
            pass
    try:
        return int(amount_str)
    except:
        return 0

def find_characters_by_material_sql(material_name: str) -> list:
    """
    Finds characters that use a given material. Uses SQL for speed.
    Returns a list of dicts with keys: character, material_type, amount.
    (Same format as the legacy version.)
    """
    if not _tables_initialized:
        return []

    with closing(_conn.cursor()) as c:
        c.execute("""
            SELECT c.name, cm.usage_type, cm.amount
            FROM character_material cm
            JOIN character_core c ON cm.character_id = c.id
            JOIN material_index m ON cm.material_id = m.id
            WHERE LOWER(m.name) = ?
        """, (material_name.lower(),))
        rows = c.fetchall()

    result = {}
    for row in rows:
        name = row["name"]
        usage = row["usage_type"]
        amount_str = row["amount"]
        total = _parse_amount(amount_str)

        if name in result:
            result[name]["amount"] += total
            if usage not in result[name]["material_type"]:
                result[name]["material_type"] += f" & {usage}"
        else:
            result[name] = {
                "character": name,
                "material_type": usage,
                "amount": total
            }

    return list(result.values())

def find_characters_by_element_sql(element_name: str) -> list:
    """
    Finds characters by element. Uses SQL for speed.
    Returns a list of character names.
    """
    if not _tables_initialized:
        return []
    with closing(_conn.cursor()) as c:
        c.execute("SELECT name FROM character_core WHERE LOWER(element) = ?", (element_name.lower(),))
        return [row["name"] for row in c.fetchall()]

def find_characters_by_weapon_type_sql(weapon_type: str) -> list:
    """
    Finds characters by weapon type. Uses SQL.
    Returns a list of character names.
    """
    if not _tables_initialized:
        return []
    with closing(_conn.cursor()) as c:
        c.execute("SELECT name FROM character_core WHERE LOWER(weapon_type) = ?", (weapon_type.lower(),))
        return [row["name"] for row in c.fetchall()]

def get_character_data_sql(character_key: str) -> dict | None:
    """
    Retrieves the full data for a specific character by their key directly from SQL.
    (May be slightly slower than dict for single lookup, but included for completeness.)
    """
    if not _tables_initialized:
        return None
    with closing(_conn.cursor()) as c:
        c.execute("SELECT full_json FROM character_core WHERE key = ?", (character_key.lower(),))
        row = c.fetchone()
        if row:
            return json.loads(row["full_json"])
    return None
