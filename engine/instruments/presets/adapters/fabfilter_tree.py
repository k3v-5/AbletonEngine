# engine/instruments/presets/adapters/fabfilter_tree.py
"""
FabFilter Preset Tree Adapter:
Recursively scans the local filesystem for FabFilter .ffp preset files across:
- Pro-Q 4, Pro-Q 3, Pro-Q 2 (Parametric EQ & Dynamic EQ)
- Pro-C 3, Pro-C 2 (Vocal, Drum Bus, Master Bus Compressor)
- Pro-L 2 (True Peak Limiter & Loudness)
- Saturn 2 (Multiband Tape, Tube, Saturation)
- Timeless 3, Volcano 3, Twin 3, Pro-R 2, Pro-MB, Pro-DS, etc.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..models import PresetRecord, PresetCategory


class FabFilterTreeAdapter:
    DEFAULT_PRESET_PATHS = [
        r"D:\Documentos\FabFilter\Presets",
        os.path.expanduser(r"~\Documents\FabFilter\Presets"),
    ]

    PLUGIN_CATEGORIES = {
        "pro-q": PresetCategory.EQ.value,
        "pro-q 2": PresetCategory.EQ.value,
        "pro-q 3": PresetCategory.EQ.value,
        "pro-q 4": PresetCategory.EQ.value,
        "pro-c": PresetCategory.COMPRESSOR.value,
        "pro-c 2": PresetCategory.COMPRESSOR.value,
        "pro-c 3": PresetCategory.COMPRESSOR.value,
        "pro-l": PresetCategory.LIMITER.value,
        "pro-l 2": PresetCategory.LIMITER.value,
        "pro-mb": PresetCategory.DYNAMICS.value,
        "pro-ds": PresetCategory.DYNAMICS.value,
        "pro-g": PresetCategory.DYNAMICS.value,
        "pro-r": PresetCategory.REVERB.value,
        "pro-r 2": PresetCategory.REVERB.value,
        "saturn": PresetCategory.SATURATION.value,
        "saturn 2": PresetCategory.SATURATION.value,
        "timeless 2": PresetCategory.DELAY.value,
        "timeless 3": PresetCategory.DELAY.value,
        "volcano 2": PresetCategory.FILTER.value,
        "volcano 3": PresetCategory.FILTER.value,
        "twin 2": PresetCategory.LEAD.value,
        "twin 3": PresetCategory.LEAD.value,
        "one": PresetCategory.BASS.value,
        "micro": PresetCategory.FILTER.value,
        "simplon": PresetCategory.FILTER.value,
    }

    def __init__(self, root_paths: Optional[List[str]] = None):
        if root_paths:
            self.search_dirs = [Path(p) for p in root_paths]
        else:
            self.search_dirs = [Path(p) for p in self.DEFAULT_PRESET_PATHS if Path(p).exists()]

    def is_available(self) -> bool:
        return any(d.exists() and d.is_dir() for d in self.search_dirs)

    def scan(self) -> List[PresetRecord]:
        """Recursively discovers all .ffp files and parses their semantic metadata."""
        records: List[PresetRecord] = []
        seen_paths = set()

        for root_dir in self.search_dirs:
            if not root_dir.exists():
                continue

            for file_path in root_dir.rglob("*.ffp"):
                f_str = str(file_path.resolve())
                if f_str in seen_paths:
                    continue
                seen_paths.add(f_str)

                # Rel path: e.g. "Pro-Q 4\Aces\Musical Low Cut Filter.ffp"
                try:
                    rel = file_path.relative_to(root_dir)
                    parts = rel.parts
                    plugin_folder = parts[0] if len(parts) > 0 else "FabFilter"
                    subcat = parts[1] if len(parts) > 2 else ("General" if len(parts) == 2 else "")
                    preset_name = file_path.stem

                    plugin_key = plugin_folder.lower().strip()
                    cat = self.PLUGIN_CATEGORIES.get(plugin_key, PresetCategory.OTHER.value)

                    tags = [plugin_folder]
                    if subcat and subcat != "General":
                        tags.append(subcat)

                    # Infer additional tags from name
                    n_lower = preset_name.lower()
                    for kw, tag in [
                        ("vocal", "vocal"), ("kick", "kick"), ("snare", "snare"),
                        ("drum", "drums"), ("bass", "bass"), ("master", "mastering"),
                        ("tape", "tape"), ("tube", "tube"), ("wide", "stereo"),
                        ("clean", "clean"), ("warm", "warm"), ("punch", "punch")
                    ]:
                        if kw in n_lower and tag not in tags:
                            tags.append(tag)

                    rec_id = f"fabfilter_{plugin_folder.replace(' ', '_')}_{preset_name.replace(' ', '_')}"
                    records.append(PresetRecord(
                        id=rec_id,
                        name=preset_name,
                        plugin_name=f"FabFilter {plugin_folder}",
                        vendor="FabFilter",
                        category=cat,
                        subcategory=subcat,
                        tags=tags,
                        file_path=f_str,
                        format="ffp",
                        is_factory=True,
                        metadata={
                            "plugin_family": plugin_folder,
                            "relative_path": str(rel),
                        }
                    ))
                except Exception:
                    continue

        return records
