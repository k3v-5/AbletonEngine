# engine/instruments/presets/adapters/serum_adapter.py
"""
Xfer Serum Preset Adapter:
Scans .fxp presets across Xfer directories and categorizes them by musical role.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..models import PresetRecord, PresetCategory


class SerumPresetAdapter:
    DEFAULT_PATHS = [
        r"D:\Documentos\Xfer\Serum Presets",
        r"D:\Documentos\Xfer\Serum 2 Presets",
        r"D:\Documentos\Serum presets",
        os.path.expanduser(r"~\AppData\Roaming\Xfer\Serum Presets"),
    ]

    CATEGORY_HINTS = {
        "bass": PresetCategory.BASS.value,
        "808": PresetCategory.SUB_BASS.value,
        "sub": PresetCategory.SUB_BASS.value,
        "lead": PresetCategory.LEAD.value,
        "pad": PresetCategory.PAD.value,
        "pluck": PresetCategory.PLUCK.value,
        "key": PresetCategory.KEYS.value,
        "piano": PresetCategory.PIANO.value,
        "arp": PresetCategory.LEAD.value,
        "seq": PresetCategory.LEAD.value,
        "fx": PresetCategory.FX.value,
        "sfx": PresetCategory.FX.value,
    }

    def __init__(self, search_paths: Optional[List[str]] = None):
        if search_paths:
            self.search_dirs = [Path(p) for p in search_paths]
        else:
            self.search_dirs = [Path(p) for p in self.DEFAULT_PATHS if Path(p).exists()]

    def is_available(self) -> bool:
        return any(d.exists() and d.is_dir() for d in self.search_dirs)

    def scan(self) -> List[PresetRecord]:
        records: List[PresetRecord] = []
        seen_paths = set()

        for root_dir in self.search_dirs:
            if not root_dir.exists():
                continue

            for f_path in root_dir.rglob("*.fxp"):
                f_str = str(f_path.resolve())
                if f_str in seen_paths:
                    continue
                seen_paths.add(f_str)

                preset_name = f_path.stem
                cat = PresetCategory.OTHER.value
                tags = ["Serum"]

                # Extract category from subfolder path or name
                full_str = (str(f_path.relative_to(root_dir)) + " " + preset_name).lower()
                for hint, mapped_cat in self.CATEGORY_HINTS.items():
                    if hint in full_str:
                        cat = mapped_cat
                        tags.append(hint)
                        break

                rec_id = f"serum_{preset_name.replace(' ', '_')}"
                records.append(PresetRecord(
                    id=rec_id,
                    name=preset_name,
                    plugin_name="Serum",
                    vendor="Xfer Records",
                    category=cat,
                    subcategory=cat.lower(),
                    tags=list(set(tags)),
                    file_path=f_str,
                    format="fxp",
                    is_factory=False,
                    metadata={"relative_path": str(f_path.relative_to(root_dir))}
                ))

        return records
