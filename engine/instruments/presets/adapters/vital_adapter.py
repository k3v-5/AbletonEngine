# engine/instruments/presets/adapters/vital_adapter.py
"""
Vital Preset Adapter:
Scans Vital presets (.vital files) from user directories and factory banks,
extracting author, style, comments, and macros, and interfacing with VitalBuilder
for procedural sound design.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..models import PresetRecord, PresetCategory


class VitalPresetAdapter:
    DEFAULT_PATHS = [
        r"D:\Documentos\Vital",
        os.path.expanduser(r"~\Documents\Vital"),
    ]

    STYLE_MAPPING = {
        "bass": PresetCategory.BASS.value,
        "lead": PresetCategory.LEAD.value,
        "pad": PresetCategory.PAD.value,
        "keys": PresetCategory.KEYS.value,
        "sequence": PresetCategory.LEAD.value,
        "percussion": PresetCategory.DRUMS.value,
        "sfx": PresetCategory.FX.value,
        "experiment": PresetCategory.CREATIVE_FX.value,
    }

    def __init__(self, search_paths: Optional[List[str]] = None):
        if search_paths:
            self.search_dirs = [Path(p) for p in search_paths]
        else:
            self.search_dirs = [Path(p) for p in self.DEFAULT_PATHS if Path(p).exists()]

    def is_available(self) -> bool:
        return any(d.exists() and d.is_dir() for d in self.search_dirs)

    def scan(self, fast_mode: bool = True) -> List[PresetRecord]:
        """Discovers and parses .vital preset files."""
        records: List[PresetRecord] = []
        seen_paths = set()

        for root_dir in self.search_dirs:
            if not root_dir.exists():
                continue

            for f_path in root_dir.rglob("*.vital"):
                f_str = str(f_path.resolve())
                if f_str in seen_paths:
                    continue
                seen_paths.add(f_str)

                preset_name = f_path.stem
                cat = PresetCategory.OTHER.value
                author = ""
                tags = ["Vital"]
                macros = {}

                # Inspect subfolder path for category clues
                rel_parts = [p.lower() for p in f_path.relative_to(root_dir).parts[:-1]]
                for p in rel_parts:
                    if "bass" in p or "808" in p:
                        cat = PresetCategory.BASS.value
                        tags.append("bass")
                    elif "lead" in p:
                        cat = PresetCategory.LEAD.value
                        tags.append("lead")
                    elif "pad" in p:
                        cat = PresetCategory.PAD.value
                        tags.append("pad")
                    elif "key" in p or "piano" in p:
                        cat = PresetCategory.KEYS.value
                        tags.append("keys")
                    elif "pluck" in p:
                        cat = PresetCategory.PLUCK.value
                        tags.append("pluck")
                    elif "fx" in p or "sfx" in p:
                        cat = PresetCategory.FX.value
                        tags.append("fx")

                # Fast header inspection (read first 1024 bytes to avoid parsing massive wavetable float arrays)
                if cat == PresetCategory.OTHER.value:
                    try:
                        with open(f_path, "r", encoding="utf-8", errors="ignore") as jf:
                            chunk = jf.read(1024)
                            import re
                            m_style = re.search(r'"preset_style"\s*:\s*"([^"]+)"', chunk)
                            if m_style:
                                s_val = m_style.group(1).lower()
                                if s_val in self.STYLE_MAPPING:
                                    cat = self.STYLE_MAPPING[s_val]
                                    tags.append(s_val)
                            m_auth = re.search(r'"author"\s*:\s*"([^"]+)"', chunk)
                            if m_auth:
                                author = m_auth.group(1)
                    except Exception:
                        pass

                # If still OTHER, inspect preset name
                if cat == PresetCategory.OTHER.value:
                    n_lower = preset_name.lower()
                    if "808" in n_lower or "bass" in n_lower or "sub" in n_lower:
                        cat = PresetCategory.BASS.value
                        tags.append("bass")
                    elif "lead" in n_lower:
                        cat = PresetCategory.LEAD.value
                        tags.append("lead")
                    elif "pad" in n_lower:
                        cat = PresetCategory.PAD.value
                        tags.append("pad")
                    elif "pluck" in n_lower:
                        cat = PresetCategory.PLUCK.value
                        tags.append("pluck")

                rec_id = f"vital_{preset_name.replace(' ', '_')}"
                records.append(PresetRecord(
                    id=rec_id,
                    name=preset_name,
                    plugin_name="Vital",
                    vendor="Vital Audio",
                    category=cat,
                    subcategory=cat.lower(),
                    tags=list(set(tags)),
                    file_path=f_str,
                    format="vital",
                    is_factory=False,
                    author=author,
                    metadata={"macros": macros}
                ))

        return records
