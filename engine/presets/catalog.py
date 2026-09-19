"""
engine/presets/catalog.py - Unified AI Preset Search & Catalog Engine.

Indexes and queries presets across:
1. Arturia SQLite Catalog (14,105 presets: Analog Lab V, Pigments, Jup-8, Prophet, CS-80, B-3, DX7, Efx FRAGMENTS, Efx MOTIONS, etc.)
2. Prototype Audio Fraction (282 analog multisampled presets across 4 expansions)
3. Ableton User Library (.adv / .adg presets)
4. MIDI Program Change mappings for Analog Lab, Omnisphere, Massive, and ZENOLOGY.
"""

import os
import sqlite3
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("PresetCatalog")

# Default database and library locations
ARTURIA_DB_CANDIDATES = [
    r"C:\ProgramData\Arturia\Presets\db.db3",
    r"E:\Arturia\Presets\db.db3"
]

FRACTION_EXPANSIONS_CANDIDATES = [
    r"E:\FL\Prototype.Audio.Fraction.v1.1.2\Expansions\Expansions",
    os.path.expandvars(r"%APPDATA%\Prototype Audio\Fraction\Expansions")
]

USER_LIBRARY_PRESETS_CANDIDATES = [
    r"D:\Documentos\Ableton\User Library\Presets",
    os.path.expandvars(r"%USERPROFILE%\Documents\Ableton\User Library\Presets"),
    r"C:\Users\sasuk\Documents\Ableton\User Library\Presets"
]


class PresetCatalog:
    """Omniscient preset search engine for AI music production."""

    def __init__(self):
        self._arturia_db_path = self._resolve_existing_path(ARTURIA_DB_CANDIDATES)
        self._fraction_dir = self._resolve_existing_path(FRACTION_EXPANSIONS_CANDIDATES)
        self._user_library_dir = self._resolve_existing_path(USER_LIBRARY_PRESETS_CANDIDATES)

    @staticmethod
    def _resolve_existing_path(candidates: List[str]) -> Optional[str]:
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def search_presets(
        self,
        query: str = "",
        role: Optional[str] = None,
        plugin: Optional[str] = None,
        limit: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Unified search across all preset sources.

        Args:
            query: Free text search (e.g. 'Rhodes', '808', 'Reese', 'Warm', 'Jup-8', 'Glitch')
            role: Musical role (e.g. 'bass', 'lead', 'pad', 'keys', 'organ', 'strings', 'fx', 'drums')
            plugin: Target plugin filter (e.g. 'Analog Lab V', 'Fraction', 'Pigments', 'Fragments', 'Motions', 'Omnisphere', 'Massive', 'ZENOLOGY')
            limit: Maximum number of results to return
        """
        results: List[Dict[str, Any]] = []

        # 1. Search Arturia database if available
        if self._arturia_db_path and (not plugin or self._is_arturia_plugin(plugin)):
            arturia_results = self._search_arturia(query, role, plugin, limit=limit)
            results.extend(arturia_results)

        # 2. Search Fraction expansions if relevant
        if self._fraction_dir and (not plugin or "fraction" in plugin.lower()):
            fraction_results = self._search_fraction(query, role, limit=limit)
            results.extend(fraction_results)

        # 3. Standard MIDI Program Lists for Omnisphere, Massive, ZENOLOGY
        if plugin and plugin.lower() in ("omnisphere", "massive", "zenology"):
            midi_synths = self._get_midi_synth_templates(plugin, query, role, limit=limit)
            results.extend(midi_synths)

        # 4. Search Ableton User Library .adv / .adg presets
        if self._user_library_dir:
            user_lib_results = self._search_user_library(query, role, plugin, limit=limit)
            results.extend(user_lib_results)

        # 5. Standard MIDI Program Lists for other plugins
        if plugin and plugin.lower() not in ("omnisphere", "massive", "zenology"):
            midi_synths = self._get_midi_synth_templates(plugin, query, role, limit=limit)
            results.extend(midi_synths)

        # Sort and trim
        return results[:limit]

    def _is_arturia_plugin(self, plugin_name: str) -> bool:
        arturia_keywords = [
            "analog lab", "pigments", "fragments", "motions", "refract",
            "jup-8", "prophet", "cs-80", "mini", "modular", "b-3", "dx7",
            "synclavier", "piano", "clavinet", "farfisa", "solina", "vox",
            "arturia"
        ]
        p_lower = plugin_name.lower()
        return any(kw in p_lower for kw in arturia_keywords)

    def _search_arturia(
        self,
        query: str,
        role: Optional[str],
        plugin: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Query Arturia db.db3 for presets matching query and filters."""
        if not self._arturia_db_path:
            return []

        results = []
        try:
            conn = sqlite3.connect(f"file:{self._arturia_db_path}?mode=ro", uri=True)
            cursor = conn.cursor()

            conditions = ["1=1"]
            params = []

            if query:
                conditions.append("(p.name LIKE ? OR i.name LIKE ? OR i.display_name LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])

            if plugin:
                p_clean = plugin.lower().replace("arturia", "").replace("vst3", "").strip()
                if "analog lab" in p_clean:
                    # Analog Lab can load all Arturia instruments, prioritize Analog Lab / Multi
                    conditions.append("(i.name LIKE '%Analog Lab%' OR i.display_name LIKE '%Multi%' OR 1=1)")
                else:
                    clean_plug = plugin.replace("Arturia", "").replace("V", "").strip()
                    conditions.append("(i.name LIKE ? OR i.display_name LIKE ?)")
                    params.extend([f"%{clean_plug}%", f"%{clean_plug}%"])

            if role:
                role_lower = role.lower().strip()
                synonyms = [role_lower]
                ROLE_SYNONYMS = {
                    "keys": ["keys", "piano", "electric piano", "rhodes", "ep", "clavinet", "wurlitzer"],
                    "bass": ["bass", "sub", "808", "reese", "acid"],
                    "lead": ["lead", "mono", "solo", "hook", "saw"],
                    "pad": ["pad", "strings", "ambient", "drone", "atmosphere", "evolving"],
                    "pluck": ["pluck", "arp", "sequence", "mallet", "bell", "chime"],
                    "organ": ["organ", "b3", "tonewheel", "drawbar", "vox"],
                    "drums": ["drum", "percussion", "kit", "snare", "kick", "hat"],
                    "fx": ["fx", "sfx", "sweep", "noise", "granular", "riser", "impact", "glitch"]
                }
                for r_key, r_syns in ROLE_SYNONYMS.items():
                    if role_lower in r_key or r_key in role_lower:
                        synonyms = r_syns
                        break

                role_clauses = []
                for syn in synonyms:
                    role_clauses.append("(p.name LIKE ? OR t.name LIKE ? OR st.name LIKE ?)")
                    params.extend([f"%{syn}%", f"%{syn}%", f"%{syn}%"])
                conditions.append(f"({' OR '.join(role_clauses)})")

            where_clause = " AND ".join(conditions)

            sql = f"""
                SELECT 
                    p.key_id,
                    p.name AS preset_name,
                    i.name AS instrument_name,
                    i.display_name AS instrument_display,
                    p.file_path,
                    COALESCE(t.name, 'General') AS category_type,
                    COALESCE(st.name, 'General') AS subtype
                FROM Preset_Id p
                JOIN Instruments i ON p.instrument_key = i.key_id
                LEFT JOIN Types_V2 t ON p.type_v2 = t.key_id
                LEFT JOIN Subtypes_V2 st ON p.subtype_v2 = st.key_id
                WHERE {where_clause}
                ORDER BY p.rating DESC, p.name ASC
                LIMIT ?
            """
            params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()

            for r in rows:
                key_id, p_name, inst_name, inst_disp, fpath, cat, subcat = r

                inst_lower = inst_name.lower()
                is_effect = any(fx in inst_lower for fx in ["fragment", "motion", "refract", "comp", "delay", "rev", "dist", "pre", "filter"])

                if is_effect:
                    load_method = "user_library_adv"
                    load_hint = f"Save/Load .adv in User Library for {inst_name}"
                else:
                    load_method = "midi_program_change"
                    load_hint = f"Analog Lab Playlist / Program Change (Index {key_id % 128})"

                results.append({
                    "preset_name": p_name,
                    "plugin": inst_disp or inst_name,
                    "family": "Arturia",
                    "musical_role": cat if cat != "General" else subcat,
                    "subtype": subcat,
                    "loading_method": load_method,
                    "selection_hint": load_hint,
                    "file_path": fpath,
                    "program_change_id": key_id % 128
                })

        except Exception as e:
            logger.error(f"Error querying Arturia database: {e}")

        return results

    def _search_fraction(
        self,
        query: str,
        role: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search Prototype Audio Fraction 282 factory presets on disk."""
        if not self._fraction_dir:
            return []

        results = []
        q_lower = query.lower()
        role_lower = (role or "").lower()

        try:
            for exp in os.listdir(self._fraction_dir):
                exp_path = os.path.join(self._fraction_dir, exp, "UserPresets")
                if not os.path.exists(exp_path):
                    continue

                for root, _, files in os.walk(exp_path):
                    rel = os.path.relpath(root, exp_path)
                    folder_role = rel.replace("\\", " / ")

                    for f in files:
                        if not f.endswith(".preset"):
                            continue

                        preset_name = f[:-7]
                        p_lower = preset_name.lower()

                        if query and (q_lower not in p_lower and q_lower not in folder_role.lower()):
                            continue
                        if role and (role_lower not in folder_role.lower() and role_lower not in p_lower):
                            continue

                        results.append({
                            "preset_name": preset_name,
                            "plugin": "Fraction",
                            "family": "Prototype Audio",
                            "expansion": exp,
                            "musical_role": folder_role,
                            "loading_method": "user_library_adv",
                            "selection_hint": f"Load from User Library or select in Fraction GUI ({exp})",
                            "file_path": os.path.join(root, f),
                            "program_change_id": None
                        })

                        if len(results) >= limit:
                            return results

        except Exception as e:
            logger.error(f"Error searching Fraction presets: {e}")

        return results

    def _search_user_library(
        self,
        query: str,
        role: Optional[str],
        plugin: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Search Ableton User Library .adv and .adg presets."""
        if not self._user_library_dir:
            return []

        results = []
        q_lower = query.lower()
        role_lower = (role or "").lower()
        plug_lower = (plugin or "").lower()

        try:
            for root, _, files in os.walk(self._user_library_dir):
                for f in files:
                    if not (f.endswith(".adv") or f.endswith(".adg")):
                        continue

                    preset_name = os.path.splitext(f)[0]
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, self._user_library_dir)
                    rel_lower = rel_path.lower()

                    if query and (q_lower not in preset_name.lower() and q_lower not in rel_lower):
                        continue
                    if role and (role_lower not in rel_lower and role_lower not in preset_name.lower()):
                        continue
                    if plugin and (plug_lower not in rel_lower):
                        continue

                    uri_formatted = "user_library/Presets/" + rel_path.replace("\\", "/")

                    results.append({
                        "preset_name": preset_name,
                        "plugin": plugin if plugin else os.path.basename(root),
                        "family": "User Library",
                        "musical_role": os.path.basename(os.path.dirname(root)),
                        "loading_method": "user_library_adv",
                        "selection_hint": f"Directly loadable via load_instrument_or_effect",
                        "file_path": full_path,
                        "browser_uri": uri_formatted
                    })

                    if len(results) >= limit:
                        return results

        except Exception as e:
            logger.error(f"Error scanning User Library: {e}")

        return results

    def _get_midi_synth_templates(
        self,
        plugin: str,
        query: str,
        role: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Provide MIDI Program Change templates for Omnisphere, Massive, and ZENOLOGY."""
        results = []
        p_lower = plugin.lower()

        if "omnisphere" in p_lower:
            slots = [
                ("Omnisphere Live Slot 1", "Lead / Pluck", 0),
                ("Omnisphere Live Slot 2", "Atmospheric Pad", 1),
                ("Omnisphere Live Slot 3", "Acoustic / Hybrid Keys", 2),
                ("Omnisphere Live Slot 4", "Bass / Sub", 3),
                ("Omnisphere Live Slot 5", "Motion / Arp", 4),
                ("Omnisphere Live Slot 6", "Cinematic Texture", 5),
                ("Omnisphere Live Slot 7", "Bells / Mallets", 6),
                ("Omnisphere Live Slot 8", "FX / Drone", 7),
            ]
            for name, default_role, pc in slots:
                if (not query or query.lower() in name.lower() or query.lower() in default_role.lower()) and \
                   (not role or role.lower() in default_role.lower()):
                    results.append({
                        "preset_name": name,
                        "plugin": "Omnisphere",
                        "family": "Spectrasonics",
                        "musical_role": default_role,
                        "loading_method": "midi_program_change",
                        "selection_hint": f"Live Mode Slot {pc+1} (Program Change {pc})",
                        "program_change_id": pc
                    })

        elif "massive" in p_lower:
            programs = [
                ("Massive Program 1 (Bassline)", "Bass", 0),
                ("Massive Program 2 (Reese Sub)", "Bass", 1),
                ("Massive Program 3 (Aggressive Saw Lead)", "Lead", 2),
                ("Massive Program 4 (Wavetable Pluck)", "Pluck", 3),
                ("Massive Program 5 (Supersaw Chords)", "Synth", 4),
                ("Massive Program 6 (Dark Ambient Pad)", "Pad", 5),
            ]
            for name, default_role, pc in programs:
                if (not query or query.lower() in name.lower() or query.lower() in default_role.lower()) and \
                   (not role or role.lower() in default_role.lower()):
                    results.append({
                        "preset_name": name,
                        "plugin": "Massive",
                        "family": "Native Instruments",
                        "musical_role": default_role,
                        "loading_method": "midi_program_change",
                        "selection_hint": f"Massive Program List #{pc+1} (Program Change {pc})",
                        "program_change_id": pc
                    })

        elif "zenology" in p_lower or "roland" in p_lower:
            tones = [
                ("ZENOLOGY Tone: 106 Lead", "Lead", 0, 0),
                ("ZENOLOGY Tone: Juno Strings", "Strings / Pad", 1, 0),
                ("ZENOLOGY Tone: SH-101 Bass", "Bass", 2, 0),
                ("ZENOLOGY Tone: Jupiter-8 Brass", "Brass", 3, 0),
                ("ZENOLOGY Tone: D-50 Pizzagogo", "Pluck / Keys", 4, 0),
                ("ZENOLOGY Tone: JD-800 Piano", "Keys", 5, 0),
            ]
            for name, default_role, pc, bank in tones:
                if (not query or query.lower() in name.lower() or query.lower() in default_role.lower()) and \
                   (not role or role.lower() in default_role.lower()):
                    results.append({
                        "preset_name": name,
                        "plugin": "ZENOLOGY",
                        "family": "Roland Cloud",
                        "musical_role": default_role,
                        "loading_method": "midi_program_change",
                        "selection_hint": f"Roland Tone #{pc+1} (Bank {bank}, Program {pc})",
                        "program_change_id": pc,
                        "bank": bank
                    })

        return results[:limit]


# Global catalog singleton
preset_catalog = PresetCatalog()
