import tkinter as tk
from tkinter import ttk, messagebox
import json
import re
import os
import tempfile
import shutil
from tkhtmlview import HTMLLabel

class GenshinInfoEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("GISL Editor Pro - Internal Dev Tool")
        self.root.geometry("1600x900")
        
        self.colors = {
            "bg": "#1e1e1e",
            "sidebar": "#252526",
            "input_bg": "#333333",
            "text": "#d4d4d4",
            "header": "#569cd6",
            "accent": "#ce9178",
            "table_head": "#37373d"
        }
        
        self.root.configure(bg=self.colors["bg"])
        
        # --- NEW DIRECTORY TRACKER ---
        self.data_dir = os.path.join(os.path.dirname(__file__), "character_data")
        os.makedirs(self.data_dir, exist_ok=True)
        # -----------------------------
        
        self.data = {}
        self.current_char_key = None
        
        # UI State Trackers
        self.entries = {}           # Standard profile fields
        self.title_entries = []     # For the dynamic "Additional Titles" list
        self.mat_entries = {}       # For Ascension Materials
        self.stat_widgets = {}      # For Stats Table
        self.current_stat_keys = []
        self.ascension_visible = True

        self.setup_ui()
        self.load_file()

    def setup_ui(self):
        self.paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=self.colors["bg"], bd=0)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # --- SIDEBAR ---
        sidebar = tk.Frame(self.paned, bg=self.colors["sidebar"], width=400)
        self.paned.add(sidebar)
        
        tk.Label(sidebar, text="CHARACTER SELECT", bg=self.colors["sidebar"], fg=self.colors["header"], font=("Consolas", 10, "bold")).pack(pady=10)
        self.char_selector = ttk.Combobox(sidebar, state="readonly")
        self.char_selector.pack(fill=tk.X, padx=10, pady=5)
        # --- ADDED: NEW CHARACTER BUTTON ---
        btn_frame2 = tk.Frame(sidebar, bg=self.colors["sidebar"])
        btn_frame2.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(btn_frame2, text="➕ New Character", bg=self.colors["input_bg"], fg="white",
                  relief="flat", command=self.new_character).pack(fill=tk.X)
        self.char_selector.bind("<<ComboboxSelected>>", self.load_character)

        self.html_view = HTMLLabel(sidebar, html="<h2 style='color:gray;'>Select character</h2>", background=self.colors["sidebar"])
        self.html_view.pack(fill=tk.BOTH, expand=True, padx=5)

        # --- MAIN EDITOR ---
        editor_cont = tk.Frame(self.paned, bg=self.colors["bg"])
        self.paned.add(editor_cont)

        btn_frame = tk.Frame(editor_cont, bg=self.colors["bg"])
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(btn_frame, text="💾 SAVE DATABASE", bg="#2d5a27", fg="white", relief="flat", command=self.save_data, font=("Arial", 10, "bold"), padx=20).pack(side=tk.RIGHT)

        self.canvas = tk.Canvas(editor_cont, bg=self.colors["bg"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(editor_cont, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=self.colors["bg"])
        
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def generate_fandom_link(self, name):
        if not name: return ""
        slug = name.strip().replace(" ", "_")
        return f"https://genshin-impact.fandom.com/wiki/{slug}"

    # ----------------------------------------------------------------------
    # UI Builders
    # ----------------------------------------------------------------------
    def build_adventure_section(self, char_data):
        group = tk.LabelFrame(self.scroll_frame, text=" PROFILE & ADVENTURE ", bg=self.colors["bg"], fg=self.colors["header"], font=("Arial", 10, "bold"), padx=10, pady=10)
        group.pack(fill=tk.X, pady=10, padx=10)

        fields = [
            ("Display Name", "name"), ("Rarity", "rarity"),
            ("Element", "element"), ("Weapon", "weapon_type"),
            ("Region", "region"), ("Birthday", "birthday"),
            ("Affiliation", "affiliation"), ("Role", "role"),
            ("Constellation Name", "constellation_name"),
            ("Special Stat Type", "ascension_stat")
        ]

        for i, (label, key) in enumerate(fields):
            row, col = divmod(i, 2)
            f_frame = tk.Frame(group, bg=self.colors["bg"])
            f_frame.grid(row=row, column=col, sticky="ew", padx=10, pady=5)
            tk.Label(f_frame, text=label.upper(), bg=self.colors["bg"], fg="#888", font=("Arial", 8)).pack(anchor="w")
            ent = tk.Entry(f_frame, bg=self.colors["input_bg"], fg="white", borderwidth=0, insertbackground="white")
            ent.insert(0, str(char_data.get(key, "")))
            ent.pack(fill=tk.X, ipady=3)
            self.entries[key] = ent
        group.columnconfigure((0,1), weight=1)

    def build_titles_section(self, char_data):
        group = tk.LabelFrame(self.scroll_frame, text=" ADDITIONAL TITLES ", bg=self.colors["bg"], 
                              fg=self.colors["header"], font=("Arial", 10, "bold"), padx=10, pady=10)
        group.pack(fill=tk.X, pady=10, padx=10)

        self.title_container = tk.Frame(group, bg=self.colors["bg"])
        self.title_container.pack(fill=tk.X)
        
        self.title_entries = []
        for title in char_data.get("additional_titles", []):
            self.add_title_field(title)

        tk.Button(group, text="+ ADD TITLE", bg=self.colors["input_bg"], fg=self.colors["accent"], 
                  relief="flat", command=lambda: self.add_title_field("")).pack(pady=5)

    def add_title_field(self, value):
        row = tk.Frame(self.title_container, bg=self.colors["bg"])
        row.pack(fill=tk.X, pady=2)
        
        ent = tk.Entry(row, bg=self.colors["input_bg"], fg=self.colors["text"], borderwidth=0)
        ent.insert(0, value)
        ent.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=2)
        self.title_entries.append(ent)
        
        tk.Button(row, text="X", bg="#442222", fg="white", relief="flat", 
                  command=lambda r=row, e=ent: [self.title_entries.remove(e), r.destroy()]).pack(side=tk.RIGHT, padx=5)

    def build_ascension_section(self, char_data):
        self.asc_group = tk.LabelFrame(self.scroll_frame, text=" ASCENSION & STATS ", bg=self.colors["bg"], fg=self.colors["header"], font=("Arial", 10, "bold"), padx=10, pady=10)
        self.asc_group.pack(fill=tk.X, pady=10, padx=10)

        self.asc_content = tk.Frame(self.asc_group, bg=self.colors["bg"])
        self.asc_content.pack(fill=tk.X)

        self.toggle_btn = tk.Button(self.asc_group, text="Collapse", bg=self.colors["input_bg"], fg="white", relief="flat", command=self.toggle_ascension)
        self.toggle_btn.pack(anchor="ne")

        mat_frame = tk.Frame(self.asc_content, bg=self.colors["bg"])
        mat_frame.pack(fill=tk.X, pady=(0, 15))
        
        mats_data = char_data.get("ascension_materials", {})
        lvl_data = char_data.get("ascension_levels", {})
        self.mat_entries = {}

        # 1. Primary Identifiers
        gem_base = mats_data.get("gems", {}).get("name", "")
        boss_name = mats_data.get("boss_mat", {}).get("name", "")
        local_name = mats_data.get("local_specialty", {}).get("name", "")

        standards = [("Gems (Base Name)", "gems", gem_base), ("Boss Material", "boss_mat", boss_name), ("Local Specialty", "local_specialty", local_name)]
        for i, (lbl, key, val) in enumerate(standards):
            tk.Label(mat_frame, text=lbl.upper(), bg=self.colors["bg"], fg="#888", font=("Arial", 8)).grid(row=i, column=0, sticky="w", padx=(0,10))
            ent = tk.Entry(mat_frame, bg=self.colors["input_bg"], fg="#9cdcfe", borderwidth=0)
            ent.insert(0, val)
            ent.grid(row=i, column=1, sticky="ew", pady=2, ipady=2)
            self.mat_entries[key] = ent

        # 2. Robust Common Material Detection
        all_keys = list(lvl_data.keys())
        gem_keys = [k for k in all_keys if gem_base and k.startswith(gem_base)]
        non_common = gem_keys + ([boss_name] if boss_name else []) + ([local_name] if local_name else [])
        common_keys = [k for k in all_keys if k not in non_common]

        def get_min_phase(key):
            phases = lvl_data[key].keys()
            try: return min(int(p[1:]) for p in phases if p.startswith('A'))
            except: return 99

        common_keys.sort(key=get_min_phase)

        tiers = [("COMMON T1 (LOW)", "common_t1"), ("COMMON T2 (MID)", "common_t2"), ("COMMON T3 (HIGH)", "common_t3")]
        for i, (lbl, key) in enumerate(tiers, start=3):
            tk.Label(mat_frame, text=lbl, bg=self.colors["bg"], fg="#888", font=("Arial", 8)).grid(row=i, column=0, sticky="w")
            ent = tk.Entry(mat_frame, bg=self.colors["input_bg"], fg="#9cdcfe", borderwidth=0)
            idx = i - 3
            if idx < len(common_keys): ent.insert(0, common_keys[idx])
            ent.grid(row=i, column=1, sticky="ew", pady=2)
            self.mat_entries[key] = ent

        mat_frame.columnconfigure(1, weight=1)

        # 3. Stats Table Display
        stats_table = char_data.get("stats_table", {})
        if not stats_table: return

        first_tier = next(iter(stats_table.values()))
        self.current_stat_keys = [k for k in first_tier.keys() if k != "level_range"]
        
        table_frame = tk.Frame(self.asc_content, bg="#2d2d2d", padx=1, pady=1)
        table_frame.pack(fill=tk.X)

        headers = ["TIER", "LVL RANGE"] + [k.upper() for k in self.current_stat_keys]
        for c, h in enumerate(headers):
            tk.Label(table_frame, text=h, bg=self.colors["table_head"], fg="white", font=("Arial", 8, "bold"), padx=5, pady=5).grid(row=0, column=c, sticky="nsew")

        self.stat_widgets = {}
        tier_keys = sorted(stats_table.keys(), key=lambda x: (len(x), x))
        
        for r, tier in enumerate(tier_keys, start=1):
            data = stats_table[tier]
            tk.Label(table_frame, text=tier, bg=self.colors["sidebar"], fg=self.colors["header"]).grid(row=r, column=0, sticky="nsew", padx=1, pady=1)
            row_map = {}
            le = tk.Entry(table_frame, bg=self.colors["input_bg"], fg="white", borderwidth=0, justify="center")
            le.insert(0, data.get("level_range", ""))
            le.grid(row=r, column=1, sticky="nsew", padx=1, pady=1)
            row_map["level_range"] = le

            for i, s_key in enumerate(self.current_stat_keys, start=2):
                val = data.get(s_key, "")
                display_val = f"{val.get('low', '0')} - {val.get('high', '0')}" if isinstance(val, dict) else str(val)
                se = tk.Entry(table_frame, bg=self.colors["input_bg"], fg="white", borderwidth=0, justify="center")
                se.insert(0, display_val)
                se.grid(row=r, column=i, sticky="nsew", padx=1, pady=1)
                row_map[s_key] = se
            self.stat_widgets[tier] = row_map

        for i in range(len(headers)): table_frame.columnconfigure(i, weight=1)

    def build_list_section(self, char_data, key_name, title):
        group = tk.LabelFrame(self.scroll_frame, text=f" {title.upper()} ", bg=self.colors["bg"], fg=self.colors["header"], font=("Arial", 10, "bold"), padx=10, pady=10)
        group.pack(fill=tk.X, pady=10, padx=10)
    
        self.entries[key_name] = []
        for i, item in enumerate(char_data.get(key_name, [])):
            box = tk.Frame(group, bg="#252526", pady=5, padx=5)
            box.pack(fill=tk.X, pady=5)
        
            display_type = item.get("type", f"{title} {i+1}").upper()
            tk.Label(box, text=display_type, bg="#252526", fg=self.colors["header"], font=("Consolas", 9, "bold")).pack(anchor="w")
        
            name_ent = tk.Entry(box, bg=self.colors["input_bg"], fg="white", borderwidth=0)
            name_ent.insert(0, item.get("name", ""))
            name_ent.pack(fill=tk.X, ipady=2)

            tk.Label(box, text="DESCRIPTION", bg="#252526", fg="#dcdcaa", font=("Arial", 8)).pack(anchor="w")
            desc_ent = tk.Text(box, height=4, bg=self.colors["bg"], fg=self.colors["text"], font=("Arial", 9), borderwidth=0)
            desc_ent.insert("1.0", item.get("description", ""))
            desc_ent.pack(fill=tk.X)
            self.entries[key_name].append({"name_w": name_ent, "desc_w": desc_ent, "raw": item})

    def new_character(self):
        """Open a dialog to create a new character file."""
        dialog = tk.Toplevel(self.root)
        dialog.title("New Character")
        dialog.geometry("400x250")
        dialog.configure(bg=self.colors["bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        # Key entry
        tk.Label(dialog, text="Character Key (filename, e.g., 'hu_tao'):",
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(pady=(15,0))
        key_var = tk.StringVar()
        key_entry = tk.Entry(dialog, textvariable=key_var, bg=self.colors["input_bg"],
                             fg="white", borderwidth=0, insertbackground="white")
        key_entry.pack(pady=5, padx=20, fill=tk.X)
        key_entry.focus_set()

        # Special stat entry
        tk.Label(dialog, text="Special Ascension Stat (e.g., 'Elemental Mastery'):",
                 bg=self.colors["bg"], fg=self.colors["text"]).pack(pady=(10,0))
        stat_var = tk.StringVar(value="Elemental Mastery")
        stat_entry = tk.Entry(dialog, textvariable=stat_var, bg=self.colors["input_bg"],
                              fg="white", borderwidth=0, insertbackground="white")
        stat_entry.pack(pady=5, padx=20, fill=tk.X)

        def do_create():
            key = key_var.get().strip().lower()
            spec_stat = stat_var.get().strip()

            if not key:
                messagebox.showerror("Error", "Character key cannot be empty.")
                return
            
            # Sanitize key
            sanitized = re.sub(r'[^a-z0-9_]', '', key.replace(' ', '_'))
            if sanitized != key:
                if not messagebox.askyesno("Confirm", f"Key will be sanitized to '{sanitized}'. Continue?"):
                    return
                key = sanitized

            if not spec_stat:
                messagebox.showerror("Error", "Special stat cannot be empty.")
                return

            file_path = os.path.join(self.data_dir, f"{key}.json")
            if os.path.exists(file_path):
                if not messagebox.askyesno("Overwrite?", f"'{key}.json' already exists. Overwrite?"):
                    return

            # Create template using dummy data for apply_template
            dummy = {"ascension_stat": spec_stat}
            new_data = self.apply_template(dummy)

            try:
                self.save_single_character_safely(file_path, new_data)
                self.data[key] = new_data
                self.update_character_list()
                self.char_selector.set(key)
                self.load_character()
                messagebox.showinfo("Success", f"Created '{key}.json'")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")

        tk.Button(dialog, text="Create", bg="#2d5a27", fg="white",
                  relief="flat", command=do_create).pack(pady=20)
    
    # ----------------------------------------------------------------------
    # Template for new characters
    # ----------------------------------------------------------------------
        def apply_template(self, char_data):
            """
            Generate a complete character template, including ascension_levels.
            char_data should contain at least 'ascension_stat' (e.g., from the dialog).
            """
            spec_stat = char_data.get("ascension_stat", "Special Stat").strip()
            if not spec_stat:
                spec_stat = "Special Stat"

            # Default material base names (user will edit later)
            gem_base = "Gem"
            boss_mat = "Boss Material"
            local_spec = "Local Specialty"
            common_t1 = "Common T1"
            common_t2 = "Common T2"
            common_t3 = "Common T3"

            # ------------------------------------------------------------------
            # Build ascension_levels
            # ------------------------------------------------------------------
            ascension_levels = {}

            def add_material(key, phases):
                """Add a material with its phase entries."""
                material_dict = {}
                for phase, lvl_range in phases:
                    material_dict[phase] = {
                        "level_range": lvl_range,
                        "amount": 0,          # placeholder – edit later
                        "link": ""             # will be generated on save
                    }
                ascension_levels[key] = material_dict

            # Gem tiers
        add_material(f"{gem_base} Sliver", [("A1", "20 -> 40")])
        add_material(f"{gem_base} Fragment", [("A2", "40 -> 50"), ("A3", "50 -> 60")])
        add_material(f"{gem_base} Chunk", [("A4", "60 -> 70"), ("A5", "70 -> 80")])
        add_material(f"{gem_base} Gemstone", [("A6", "80 -> 90")])

        # Boss material (appears from A2 to A6)
        boss_phases = [
            ("A2", "40 -> 50"),
            ("A3", "50 -> 60"),
            ("A4", "60 -> 70"),
            ("A5", "70 -> 80"),
            ("A6", "80 -> 90")
        ]
        add_material(boss_mat, boss_phases)

        # Local specialty (appears in all A1-A6)
        local_phases = [
            ("A1", "20 -> 40"),
            ("A2", "40 -> 50"),
            ("A3", "50 -> 60"),
            ("A4", "60 -> 70"),
            ("A5", "70 -> 80"),
            ("A6", "80 -> 90")
        ]
        add_material(local_spec, local_phases)

        # Common T1 (A1, A2)
        add_material(common_t1, [("A1", "20 -> 40"), ("A2", "40 -> 50")])
        # Common T2 (A3, A4)
        add_material(common_t2, [("A3", "50 -> 60"), ("A4", "60 -> 70")])
        # Common T3 (A5, A6)
        add_material(common_t3, [("A5", "70 -> 80"), ("A6", "80 -> 90")])

        # ------------------------------------------------------------------
        # ascension_materials (top fields)
        # ------------------------------------------------------------------
        ascension_materials = {
            "gems": {"name": gem_base, "link": ""},
            "boss_mat": {"name": boss_mat, "link": ""},
            "local_specialty": {"name": local_spec, "link": ""},
            "common_mat": {"name": common_t1, "link": ""}
        }

        # ------------------------------------------------------------------
        # stats_table (with special stat)
        # ------------------------------------------------------------------
        def get_base():
            return {
                "HP": {"low": "0", "high": "0"},
                "ATK": {"low": "0", "high": "0"},
                "DEF": {"low": "0", "high": "0"},
                spec_stat: {"low": "0", "high": "0"}
            }

        def get_base_excess():
            return {
                "HP": {"low": "0", "high": "0"},
                "ATK": {"low": "0", "high": "0"},
                "DEF": {"low": "0", "high": "0"}
            }

        stats_table = {
            "A0": {"level_range": "1 -> 20", **get_base()},
            "A1": {"level_range": "20 -> 40", **get_base()},
            "A2": {"level_range": "40 -> 50", **get_base()},
            "A3": {"level_range": "50 -> 60", **get_base()},
            "A4": {"level_range": "60 -> 70", **get_base()},
            "A5": {"level_range": "70 -> 80", **get_base()},
            "A6": {"level_range": "80 -> 90", **get_base()},
            "A6 - C7": {"level_range": "90 -> 95", **get_base_excess()},
            "A6 - C8": {"level_range": "95 -> 100", **get_base_excess()}
        }

        # ------------------------------------------------------------------
        # Talents and constellations (empty)
        # ------------------------------------------------------------------
        talents = [
            {"name": "Normal Attack", "type": "Normal Attack", "description": "", "level_materials": {}},
            {"name": "Elemental Skill", "type": "Elemental Skill", "description": "", "level_materials": {}},
            {"name": "Elemental Burst", "type": "Elemental Burst", "description": "", "level_materials": {}},
            {"name": "1st Ascension Passive", "type": "1st Ascension Passive", "description": ""},
            {"name": "4th Ascension Passive", "type": "4th Ascension Passive", "description": ""},
            {"name": "Utility Passive", "type": "Utility Passive", "description": ""}
        ]

        constellations = [
            {"name": "C1", "description": ""},
            {"name": "C2", "description": ""},
            {"name": "C3", "description": ""},
            {"name": "C4", "description": ""},
            {"name": "C5", "description": ""},
            {"name": "C6", "description": ""}
        ]

        # ------------------------------------------------------------------
        # Assemble final template
        # ------------------------------------------------------------------
        return {
            "name": "",
            "rarity": 4,
            "element": "",
            "weapon_type": "",
            "region": "",
            "birthday": "",
            "affiliation": "",
            "role": "",
            "additional_titles": [],
            "constellation_name": "",
            "ascension_stat": spec_stat,
            "ascension_materials": ascension_materials,
            "ascension_levels": ascension_levels,
            "stats_table": stats_table,
            "talents": talents,
            "constellations": constellations
        }

    # ----------------------------------------------------------------------
    # Save / Load
    # ----------------------------------------------------------------------
    def save_data(self):
        """Modified Option 2: Supports character-specific JSON files."""
        if not self.current_char_key:
            messagebox.showwarning("Warning", "No character selected to save.")
            return

        # Use the logic from Option 2 to create the 'updated' dictionary
        # We copy from the in-memory cache first
        updated = self.data.get(self.current_char_key, {}).copy()
        
        try:
            # --- [START OF ORIGINAL SAVE LOGIC] ---
            # 1. Update profile fields
            for key, widget in self.entries.items():
                if isinstance(widget, tk.Entry):
                    val = widget.get()
                    if key == "rarity" and val.isdigit():
                        updated[key] = int(val)
                    else:
                        updated[key] = val

            # 2. Update additional titles
            updated["additional_titles"] = [e.get() for e in self.title_entries]

            # 3. Patch ascension levels 
            lvl_data = updated.get("ascension_levels", {}).copy()
            mats_meta = updated.get("ascension_materials", {})

            def rename_key(old_name, new_name):
                if old_name in lvl_data and old_name != new_name:
                    lvl_data[new_name] = lvl_data.pop(old_name)
                    for phase in lvl_data[new_name].values():
                        if isinstance(phase, dict) and "link" in phase:
                            phase["link"] = self.generate_fandom_link(new_name)

            # Gems
            old_gem_base = mats_meta.get("gems", {}).get("name", "")
            new_gem_base = self.mat_entries["gems"].get().strip()
            if old_gem_base != new_gem_base:
                for suffix in [" Sliver", " Fragment", " Chunk", " Gemstone"]:
                    rename_key(old_gem_base + suffix, new_gem_base + suffix)

            # Boss / Local
            rename_key(mats_meta.get("boss_mat", {}).get("name", ""), self.mat_entries["boss_mat"].get().strip())
            rename_key(mats_meta.get("local_specialty", {}).get("name", ""), self.mat_entries["local_specialty"].get().strip())

            # Commons (just update names, no rename needed because they are new keys)
            ui_t1 = self.mat_entries["common_t1"].get().strip()
            ui_t2 = self.mat_entries["common_t2"].get().strip()
            ui_t3 = self.mat_entries["common_t3"].get().strip()

            # --- Rename common materials in ascension_levels ---
            # Get the old common material names from ascension_levels (sorted by earliest phase)
            lvl_keys = list(lvl_data.keys())
            gem_base = self.mat_entries["gems"].get().strip()
            boss_name = self.mat_entries["boss_mat"].get().strip()
            local_name = self.mat_entries["local_specialty"].get().strip()

            # Identify which keys are not gems, boss, or local
            def is_common_key(k):
                if gem_base and k.startswith(gem_base):
                    return False
                if k == boss_name or k == local_name:
                    return False
                return True

            common_keys = [k for k in lvl_keys if is_common_key(k)]
            # Sort by the earliest ascension phase they appear in (as in the builder)
            def get_min_phase(key):
                phases = lvl_data[key].keys()
                try:
                    return min(int(p[1:]) for p in phases if p.startswith('A'))
                except:
                    return 99
            common_keys.sort(key=get_min_phase)

            # The three new names from the UI
            new_common = [
                self.mat_entries["common_t1"].get().strip(),
                self.mat_entries["common_t2"].get().strip(),
                self.mat_entries["common_t3"].get().strip()
            ]

            # Rename if necessary (assuming the order matches)
            for old_name, new_name in zip(common_keys, new_common):
                if old_name != new_name and old_name in lvl_data:
                    lvl_data[new_name] = lvl_data.pop(old_name)
                    # Update links inside the renamed object
                    for phase in lvl_data[new_name].values():
                        if isinstance(phase, dict) and "link" in phase:
                            phase["link"] = self.generate_fandom_link(new_name)
            updated["ascension_levels"] = lvl_data
            updated["ascension_materials"] = {
                "gems": {"name": new_gem_base, "link": self.generate_fandom_link(new_gem_base)},
                "boss_mat": {"name": self.mat_entries["boss_mat"].get().strip(), "link": self.generate_fandom_link(self.mat_entries["boss_mat"].get().strip())},
                "local_specialty": {"name": self.mat_entries["local_specialty"].get().strip(), "link": self.generate_fandom_link(self.mat_entries["local_specialty"].get().strip())},
                "common_mat": {"name": ui_t1, "link": self.generate_fandom_link(ui_t1)}
            }

            # 4. Update stats table (preserve keys)
            if "stats_table" in updated:
                for tier, widgets in self.stat_widgets.items():
                    if tier in updated["stats_table"]:
                        updated["stats_table"][tier]["level_range"] = widgets["level_range"].get()
                        for s_key in self.current_stat_keys:
                            if s_key in updated["stats_table"][tier]:
                                raw_val = widgets[s_key].get()
                                if " - " in raw_val:
                                    p = raw_val.split(" - ")
                                    updated["stats_table"][tier][s_key] = {"low": p[0].strip(), "high": p[1].strip() if len(p)>1 else ""}
                                else:
                                    updated["stats_table"][tier][s_key] = raw_val

            # 5. Save talents & constellations
            for l_key in ["talents", "constellations"]:
                if l_key in self.entries:
                    new_list = []
                    for e in self.entries[l_key]:
                        item_data = e["raw"].copy()
                        t_name = e["name_w"].get().strip()
                        item_data["name"] = t_name
                        item_data["description"] = e["desc_w"].get("1.0", tk.END).strip()
                        item_data["link"] = self.generate_fandom_link(t_name)
                        new_list.append(item_data)
                    updated[l_key] = new_list

            self.data[self.current_char_key] = updated
            
            # Ensure the subfolder exists
            os.makedirs(self.data_dir, exist_ok=True)
            char_file_path = os.path.join(self.data_dir, f"{self.current_char_key}.json")
            
            # Use the 'Silent Save' logic (Option 3) but targeted at the character file
            self.save_single_character_safely(char_file_path, updated)
            
            messagebox.showinfo("Success", f"Saved {self.current_char_key}.json with all materials preserved.")

        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")

    def save_database_silent(self):
        try:
            json_string = json.dumps(self.data, indent=4, ensure_ascii=False)
            pattern = r'\{\s*\n\s*"low":\s*"(.*?)",\s*\n\s*"high":\s*"(.*?)"\s*\n\s*\}'
            compact_json = re.sub(pattern, r'{ "low": "\1", "high": "\2" }', json_string)

            fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(self.filename)), text=True)
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(compact_json)

            if os.path.exists(self.filename):
                shutil.copy2(self.filename, self.filename + ".bak")

            os.replace(temp_path, self.filename)
        except Exception as e:
            print(f"Silent save error: {e}")

    def load_file(self):
        """Loads all individual JSON files from the character_data directory."""
        self.data = {}
        
        if os.path.exists(self.data_dir):
            for filename in os.listdir(self.data_dir):
                if filename.endswith(".json"):
                    char_key = filename[:-5] # Strip the .json extension
                    file_path = os.path.join(self.data_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            self.data[char_key] = json.load(f)
                    except Exception as e:
                        messagebox.showerror("Load Error", f"Failed to load {filename}:\n{e}")
        
        self.update_character_list()
        
        if self.data:
            messagebox.showinfo("Loaded", f"Successfully loaded {len(self.data)} characters.")
        else:
            messagebox.showwarning("Empty", "No character data found in the directory.")

    def toggle_ascension(self):
        if self.ascension_visible:
            self.asc_content.pack_forget()
            self.toggle_btn.config(text="Expand")
        else:
            self.asc_content.pack(fill=tk.X)
            self.toggle_btn.config(text="Collapse")
        self.ascension_visible = not self.ascension_visible

    def save_single_character_safely(self, file_path, data_dict):
        """A portable version of Option 3's safety logic."""
        import re, tempfile, shutil, os
        
        json_string = json.dumps(data_dict, indent=4, ensure_ascii=False)
        # Apply your custom 'low/high' formatting
        pattern = r'\{\s*\n\s*"low":\s*"(.*?)",\s*\n\s*"high":\s*"(.*?)"\s*\n\s*\}'
        compact_json = re.sub(pattern, r'{ "low": "\1", "high": "\2" }', json_string)

        # Atomic write using tempfile
        fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(file_path), text=True)
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(compact_json)

        # Backup existing file if it exists
        if os.path.exists(file_path):
            shutil.copy2(file_path, file_path + ".bak")

        os.replace(temp_path, file_path)

    def update_character_list(self):
        """Updates the Combobox with the keys from the loaded data."""
        if hasattr(self, 'char_selector'):
            sorted_keys = sorted(self.data.keys())
            self.char_selector['values'] = sorted_keys
            # Select the first character if none is selected
            if sorted_keys and not self.char_selector.get():
                self.char_selector.current(0)
                self.load_character()
    def load_character(self, event=None):
        key = self.char_selector.get()
        self.current_char_key = key
        char_data = self.data.get(key, {})

        # Build rich HTML preview
        titles = char_data.get('additional_titles', [])
        first_title = titles[0] if titles else ""
        talent_html = "".join(f"<li><b>{t.get('name')}:</b> {t.get('description')}</li>" for t in char_data.get('talents', []))
        const_html = "".join(f"<li><b>{c.get('name')}:</b> {c.get('description')}</li>" for c in char_data.get('constellations', []))
        rich_html = f"""
        <div style="background-color:{self.colors['sidebar']}; color:{self.colors['text']}; font-family:sans-serif; padding:10px;">
            <h1 style="color:{self.colors['header']}; margin-bottom:2px;">{char_data.get('name', 'Unknown')}</h1>
            <p style="color:{self.colors['accent']}; margin-top:0;">{first_title}</p>
            <p><b>Element:</b> {char_data.get('element')} | <b>Weapon:</b> {char_data.get('weapon_type')}</p>
            <p><i>{char_data.get('role')}</i></p>
            <hr style="border:0; border-top:1px solid #444;">
            <h3 style="color:{self.colors['header']};">TALENTS</h3>
            <ul>{talent_html if talent_html else "<li>No talents found</li>"}</ul>
            <h3 style="color:{self.colors['header']};">CONSTELLATIONS</h3>
            <ul>{const_html if const_html else "<li>No constellations found</li>"}</ul>
        </div>
        """
        self.html_view.set_html(rich_html)

        # Clear and rebuild editor UI
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.entries = {}
        self.build_adventure_section(char_data)
        self.build_titles_section(char_data)
        self.build_ascension_section(char_data)
        self.build_list_section(char_data, "talents", "Talent")
        self.build_list_section(char_data, "constellations", "Constellation")

if __name__ == "__main__":
    root = tk.Tk()
    app = GenshinInfoEditor(root)
    root.mainloop()