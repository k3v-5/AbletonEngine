# engine/instruments/presets/universal_indexer.py
"""
Universal VST Preset Indexer:
Orchestrates multi-vendor preset adapters (Arturia SQLite, FabFilter directory trees,
Vital JSONs, Serum FXPs, Valhalla DSP banks, and Native Live 12 devices).
Maintains a high-speed disk cache (vst_preset_index.json) enabling sub-millisecond
retrieval across 30,000+ presets.
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from .models import PresetRecord
from .adapters import (
    ArturiaDbAdapter,
    FabFilterTreeAdapter,
    VitalPresetAdapter,
    SerumPresetAdapter,
    ValhallaPresetAdapter,
    NativePresetAdapter,
)


class UniversalIndexer:
    DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "cache"
    DEFAULT_CACHE_FILE = DEFAULT_CACHE_DIR / "vst_preset_index.json"

    def __init__(self, cache_file: Optional[Path] = None):
        self.cache_file = cache_file or self.DEFAULT_CACHE_FILE
        self._presets: List[PresetRecord] = []
        self._indexed_at: float = 0.0
        self._is_loaded: bool = False

    def load_or_index(self, force_reindex: bool = False) -> List[PresetRecord]:
        """Loads presets from cache if available, otherwise executes full scan and saves cache."""
        if self._is_loaded and not force_reindex:
            return self._presets

        if not force_reindex and self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._presets = [PresetRecord.from_dict(d) for d in data.get("presets", [])]
                    self._indexed_at = data.get("timestamp", 0.0)
                    self._is_loaded = True
                    return self._presets
            except Exception:
                # If cache is corrupted, reindex
                pass

        return self.reindex()

    def reindex(self) -> List[PresetRecord]:
        """Runs all adapters and writes cache to disk."""
        adapters = [
            ArturiaDbAdapter(),
            FabFilterTreeAdapter(),
            VitalPresetAdapter(),
            SerumPresetAdapter(),
            ValhallaPresetAdapter(),
            NativePresetAdapter(),
        ]

        all_presets: List[PresetRecord] = []
        seen_ids = set()

        for adapter in adapters:
            try:
                if adapter.is_available():
                    scanned = adapter.scan()
                    for p in scanned:
                        if p.id not in seen_ids:
                            seen_ids.add(p.id)
                            all_presets.append(p)
            except Exception:
                continue

        self._presets = all_presets
        self._indexed_at = time.time()
        self._is_loaded = True

        # Save to disk cache
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": self._indexed_at,
                    "count": len(self._presets),
                    "presets": [p.to_dict() for p in self._presets]
                }, f)
        except Exception:
            pass

        return self._presets

    def get_all_presets(self) -> List[PresetRecord]:
        if not self._is_loaded:
            self.load_or_index()
        return self._presets

    def get_stats(self) -> Dict[str, Any]:
        presets = self.get_all_presets()
        vendors: Dict[str, int] = {}
        plugins: Dict[str, int] = {}
        categories: Dict[str, int] = {}

        for p in presets:
            vendors[p.vendor] = vendors.get(p.vendor, 0) + 1
            plugins[p.plugin_name] = plugins.get(p.plugin_name, 0) + 1
            categories[p.category] = categories.get(p.category, 0) + 1

        return {
            "total_presets": len(presets),
            "vendors": vendors,
            "plugins": dict(sorted(plugins.items(), key=lambda x: x[1], reverse=True)[:25]),
            "categories": categories,
            "cached": self.cache_file.exists(),
        }
