# engine/instruments/presets/adapters/arturia_db.py
"""
Arturia Preset Database Adapter:
Directly queries Arturia's SQLite database (C:\\ProgramData\\Arturia\\Presets\\db.db3)
extracting presets with instrument, type, subtype, and tag classification for:
- Instruments: Pigments, Analog Lab V, Mellotron V, Mini V3, Prophet, Jup-8, etc.
- Effects: Efx MOTIONS, Efx FRAGMENTS, Efx REFRACT, Rev PLATE-140, Delay TAPE-201, etc.
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..models import PresetRecord, PresetCategory


class ArturiaDbAdapter:
    DEFAULT_DB_PATH = r"C:\ProgramData\Arturia\Presets\db.db3"

    TYPE_MAPPING = {
        "bass": PresetCategory.BASS.value,
        "lead": PresetCategory.LEAD.value,
        "pad": PresetCategory.PAD.value,
        "keys": PresetCategory.KEYS.value,
        "electric piano": PresetCategory.KEYS.value,
        "piano": PresetCategory.PIANO.value,
        "organ": PresetCategory.ORGAN.value,
        "strings": PresetCategory.STRINGS.value,
        "brass & winds": PresetCategory.BRASS.value,
        "drums": PresetCategory.DRUMS.value,
        "vocal": PresetCategory.VOCAL.value,
        "delay": PresetCategory.DELAY.value,
        "reverb": PresetCategory.REVERB.value,
        "distortion": PresetCategory.DISTORTION.value,
        "modulation": PresetCategory.MODULATION.value,
        "filter": PresetCategory.FILTER.value,
        "dynamics": PresetCategory.DYNAMICS.value,
        "eq": PresetCategory.EQ.value,
        "sound effects": PresetCategory.FX.value,
        "texture": PresetCategory.CREATIVE_FX.value,
        "transition": PresetCategory.CREATIVE_FX.value,
        "experimental": PresetCategory.CREATIVE_FX.value,
        "rhythmic": PresetCategory.CREATIVE_FX.value,
    }

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or self.DEFAULT_DB_PATH)

    def is_available(self) -> bool:
        return self.db_path.exists() and self.db_path.is_file()

    def scan(self) -> List[PresetRecord]:
        """Queries the SQLite database and returns normalized PresetRecord entries."""
        if not self.is_available():
            return []

        records: List[PresetRecord] = []
        try:
            # Read-only URI mode to prevent database locking
            uri = f"file:{self.db_path.as_posix()}?mode=ro"
            conn = sqlite3.connect(uri, uri=True, timeout=5.0)
            cursor = conn.cursor()

            # Pre-load tags map: preset_id -> [tag_names]
            tag_map: Dict[int, List[str]] = {}
            try:
                tag_rows = cursor.execute("""
                    SELECT pt.preset_key, t.name 
                    FROM Preset_Tags_V2 pt 
                    JOIN Tags_V2 t ON pt.tag_key = t.key_id
                """).fetchall()
                for p_id, t_name in tag_rows:
                    if p_id not in tag_map:
                        tag_map[p_id] = []
                    tag_map[p_id].append(str(t_name))
            except Exception:
                pass

            # Query presets with full joins
            query = """
                SELECT 
                    p.key_id,
                    p.name,
                    COALESCE(i.display_name, i.name, 'Arturia') as inst_name,
                    COALESCE(t.name, 'Standard') as type_name,
                    COALESCE(st.name, '') as subtype_name,
                    COALESCE(p.file_path, '') as file_path,
                    COALESCE(p.sound_designer, '') as author,
                    COALESCE(p.analoglab_factory, 1) as is_factory
                FROM Preset_Id p
                LEFT JOIN Instruments i ON p.instrument_key = i.key_id
                LEFT JOIN Types_V2 t ON p.type_v2 = t.key_id
                LEFT JOIN Subtypes_V2 st ON p.subtype_v2 = st.key_id
                WHERE p.name IS NOT NULL AND TRIM(p.name) != ''
            """
            rows = cursor.execute(query).fetchall()
            conn.close()

            for r in rows:
                p_id, name, inst_name, type_name, subtype_name, file_path, author, is_factory = r
                t_lower = type_name.lower().strip()
                cat = self.TYPE_MAPPING.get(t_lower, PresetCategory.OTHER.value)
                
                tags = tag_map.get(p_id, [])
                if subtype_name and subtype_name not in tags:
                    tags.append(subtype_name)

                record = PresetRecord(
                    id=f"arturia_{p_id}_{name.replace(' ', '_')}",
                    name=name,
                    plugin_name=inst_name,
                    vendor="Arturia",
                    category=cat,
                    subcategory=subtype_name,
                    tags=tags,
                    file_path=file_path if file_path else None,
                    format="arturia_db",
                    is_factory=bool(is_factory),
                    author=author,
                    metadata={
                        "raw_type": type_name,
                        "arturia_id": p_id,
                    }
                )
                records.append(record)

        except Exception as e:
            # Safe degradation if database is locked or corrupted
            return []

        return records
