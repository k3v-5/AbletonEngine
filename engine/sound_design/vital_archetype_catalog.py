# engine/sound_design/vital_archetype_catalog.py
"""
Vital Archetype Catalog & Template Indexer.

Discovers, classifies, and indexes production-grade .vital presets from local repositories
and external packs (such as KSHMR and PIE), organizing them into acoustic archetypes
(808, Sub, Reese, Punch Bass, Supersaw Lead, Pluck, Chords, Pads, Rhodes).
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json
import logging

logger = logging.getLogger("VitalArchetypeCatalog")


class ArchetypeCatalog:
    """
    Catalog and selector for baseline Vital presets.
    Provides verified base templates ensuring all wavetables, modulations,
    and gain staging are musically sound before sculpting.
    """

    DEFAULT_CATALOG_PATHS = [
        Path("presets/vital"),
        Path("presets/vital/kshmr"),
        Path("engine/sound/vital"),
        Path(r"C:\Users\kevin.garrido\Downloads\Kshmr Vital Preset Pack Vol. 1\Kshmr Vital Preset Pack Vol\Presets")
    ]

    def __init__(self, search_paths: Optional[List[Path]] = None):
        self.search_paths: List[Path] = search_paths or self.DEFAULT_CATALOG_PATHS
        self.catalog: Dict[str, List[Dict[str, Any]]] = {}
        self._index_all_presets()

    def _index_all_presets(self) -> None:
        """Scans all search paths and populates the classified catalog."""
        seen_paths = set()
        indexed_count = 0

        for path in self.search_paths:
            if not path.exists():
                continue

            for file_path in path.glob("**/*.vital"):
                resolved = file_path.resolve()
                if resolved in seen_paths:
                    continue
                seen_paths.add(resolved)

                try:
                    data = json.loads(resolved.read_text(encoding="utf-8"))
                    category = self._classify_preset(resolved.name, data)
                    
                    entry = {
                        "name": data.get("preset_name", resolved.stem),
                        "file_path": resolved,
                        "style": data.get("preset_style", ""),
                        "author": data.get("author", "Unknown"),
                        "category": category,
                        "polyphony": data.get("settings", {}).get("polyphony", 8.0)
                    }

                    if category not in self.catalog:
                        self.catalog[category] = []
                    self.catalog[category].append(entry)
                    indexed_count += 1

                except Exception as e:
                    logger.debug(f"Could not index preset {resolved.name}: {e}")

        logger.info(f"ArchetypeCatalog initialized with {indexed_count} presets across {len(self.catalog)} categories.")

    def _classify_preset(self, filename: str, data: Dict[str, Any]) -> str:
        """Classifies a preset into an acoustic archetype category based on name and settings."""
        fn = filename.upper()
        style = str(data.get("preset_style", "")).upper()
        poly = float(data.get("settings", {}).get("polyphony", 8.0))

        # 0. Template / Blank
        if "TEMPLATE" in fn:
            return "TEMPLATE"

        # 1. 808 and Glide Basses
        if "808" in fn or "GLIDE" in fn:
            return "BASS_808"

        # 2. Reese and Neuro Basses
        if "REESE" in fn or "NEURO" in fn:
            return "BASS_REECE"

        # 3. Sub Bass
        if "SUB" in fn:
            return "BASS_SUB"

        # 4. General / Punch Bass
        if "BASS" in fn or "BASS" in style:
            return "BASS_PUNCH"

        # 5. Rhodes / E-Piano / Keys
        if "RHODES" in fn or "PIANO" in fn or "KEYS" in fn:
            return "KEYS_RHODES"

        # 6. Plucks & Stabs
        if "PLUCK" in fn or "STAB" in fn:
            return "LEAD_PLUCK"

        # 7. Leads & Supersaws
        if "LEAD" in fn or "LEAD" in style:
            return "LEAD_SAW"

        # 8. Chords & Polysynths
        if "CHORD" in fn or ("PAD" in style and poly > 4 and "PAD" not in fn):
            return "CHORD_SUPERAW"

        # 9. Pads & Textures
        if "PAD" in fn or "PAD" in style:
            return "PAD_LUSH"

        return "GENERIC"

    def get_available_categories(self) -> List[str]:
        """Returns all populated category tags in the catalog."""
        return sorted(list(self.catalog.keys()))

    def get_presets_in_category(self, category: str) -> List[Dict[str, Any]]:
        """Returns list of presets matching a specific category."""
        return self.catalog.get(category.upper(), [])

    def select_archetype(
        self,
        role: str = "BASS_SUB",
        preferred_name: Optional[str] = None
    ) -> Tuple[Path, Dict[str, Any]]:
        """
        Retrieves the best matching preset archetype and loads its full JSON data.
        Falls back gracefully if the exact category is missing.
        """
        role_upper = role.upper().strip()

        # Direct category lookup
        matches = self.catalog.get(role_upper, [])

        # Fallback mappings
        if not matches:
            if "808" in role_upper:
                matches = self.catalog.get("BASS_808", []) or self.catalog.get("BASS_SUB", [])
            elif "SUB" in role_upper:
                matches = self.catalog.get("BASS_SUB", []) or self.catalog.get("BASS_PUNCH", [])
            elif "REECE" in role_upper or "REESE" in role_upper:
                matches = self.catalog.get("BASS_REECE", []) or self.catalog.get("BASS_PUNCH", [])
            elif "BASS" in role_upper:
                matches = self.catalog.get("BASS_PUNCH", []) or self.catalog.get("BASS_SUB", [])
            elif "PERCUSSION" in role_upper or "DRUM" in role_upper or "CLICK" in role_upper or "TRANSIENT" in role_upper:
                matches = self.catalog.get("LEAD_PLUCK", []) or self.catalog.get("BASS_PUNCH", [])
            elif "BELL" in role_upper or "MALLET" in role_upper or "METALLIC" in role_upper:
                matches = self.catalog.get("LEAD_PLUCK", []) or self.catalog.get("KEYS_RHODES", [])
            elif "DRONE" in role_upper or "TEXTURE" in role_upper or "AMBIENT" in role_upper:
                matches = self.catalog.get("PAD_LUSH", [])
            elif "VOCAL" in role_upper or "VOICE" in role_upper:
                matches = self.catalog.get("LEAD_SAW", []) or self.catalog.get("PAD_LUSH", [])
            elif "TEMPLATE" in role_upper:
                matches = self.catalog.get("TEMPLATE", []) or self.catalog.get("GENERIC", [])
            elif "PLUCK" in role_upper:
                matches = self.catalog.get("LEAD_PLUCK", []) or self.catalog.get("LEAD_SAW", [])
            elif "LEAD" in role_upper:
                matches = self.catalog.get("LEAD_SAW", [])
            elif "CHORD" in role_upper or "POLY" in role_upper:
                matches = self.catalog.get("CHORD_SUPERAW", []) or self.catalog.get("PAD_LUSH", [])
            elif "PAD" in role_upper:
                matches = self.catalog.get("PAD_LUSH", [])
            elif "RHODES" in role_upper or "KEY" in role_upper:
                matches = self.catalog.get("KEYS_RHODES", [])

        # Ultimate fallback to any available preset in catalog
        if not matches:
            for cat_list in self.catalog.values():
                if cat_list:
                    matches = cat_list
                    break

        if not matches:
            raise RuntimeError("ArchetypeCatalog: No .vital presets found in any configured search paths.")

        # If a preferred name is requested, search for it
        if preferred_name:
            target = preferred_name.lower()
            for m in matches:
                if target in m["name"].lower() or target in m["file_path"].name.lower():
                    chosen_entry = m
                    break
            else:
                chosen_entry = matches[0]
        else:
            chosen_entry = matches[0]

        file_path = chosen_entry["file_path"]
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return file_path, data
