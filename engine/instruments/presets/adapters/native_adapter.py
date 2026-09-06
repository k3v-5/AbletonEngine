# engine/instruments/presets/adapters/native_adapter.py
"""
Native Ableton Live 12 Suite Preset Adapter:
Bridges the curated PRESET_CATALOG from engine/instruments/library/preset_catalog.py
and core native instruments/effects into the universal preset indexing pipeline.
"""

from typing import List, Dict, Any, Optional
from ..models import PresetRecord, PresetCategory
from ...library.preset_catalog import PRESET_CATALOG


class NativePresetAdapter:
    ROLE_MAPPING = {
        "piano": PresetCategory.PIANO.value,
        "rhodes": PresetCategory.KEYS.value,
        "keys": PresetCategory.KEYS.value,
        "bass": PresetCategory.BASS.value,
        "sub_bass": PresetCategory.SUB_BASS.value,
        "808": PresetCategory.SUB_BASS.value,
        "lead": PresetCategory.LEAD.value,
        "pad": PresetCategory.PAD.value,
        "pluck": PresetCategory.PLUCK.value,
        "strings": PresetCategory.STRINGS.value,
        "brass": PresetCategory.BRASS.value,
        "drums": PresetCategory.DRUMS.value,
        "fx": PresetCategory.FX.value,
    }

    def is_available(self) -> bool:
        return True

    def scan(self) -> List[PresetRecord]:
        records: List[PresetRecord] = []
        for entry in PRESET_CATALOG:
            r_lower = entry.role.lower()
            cat = self.ROLE_MAPPING.get(r_lower, PresetCategory.OTHER.value)
            
            rec_id = f"native_{entry.name.lower().replace(' ', '_').replace('&', 'and')}"
            records.append(PresetRecord(
                id=rec_id,
                name=entry.name,
                plugin_name=entry.category,
                vendor="Ableton",
                category=cat,
                subcategory=entry.character,
                tags=entry.tags + entry.genres,
                file_path=None,
                format="native_adv",
                is_factory=True,
                metadata={
                    "uri": entry.uri,
                    "description": entry.description,
                    "character": entry.character,
                    "genres": entry.genres,
                }
            ))

        # Core native devices
        native_devices = [
            ("Drift", "Ableton", PresetCategory.LEAD.value, ["synth", "analog", "sub", "lead", "poly"]),
            ("Wavetable", "Ableton", PresetCategory.PAD.value, ["synth", "wavetable", "digital", "modern"]),
            ("Operator", "Ableton", PresetCategory.BASS.value, ["fm", "synth", "sub", "aggressive", "percussion"]),
            ("Analog", "Ableton", PresetCategory.BASS.value, ["subtractive", "vintage", "warmth", "moog"]),
            ("Simpler", "Ableton", PresetCategory.KEYS.value, ["sampler", "sample_playback", "warp"]),
            ("EQ Eight", "Ableton", PresetCategory.EQ.value, ["parametric", "surgical", "hpf", "lpf"]),
            ("Drum Buss", "Ableton", PresetCategory.DYNAMICS.value, ["transient", "drive", "crunch", "sub_boom"]),
            ("Glue Compressor", "Ableton", PresetCategory.COMPRESSOR.value, ["vca", "bus", "ssl", "punch"]),
            ("Saturator", "Ableton", PresetCategory.SATURATION.value, ["tape", "waveshaper", "analog_clip", "drive"]),
            ("Utility", "Ableton", PresetCategory.MASTERING.value, ["gain", "mono", "bass_mono", "phase_invert"]),
        ]

        for dev_name, vendor, cat, tags in native_devices:
            rec_id = f"native_device_{dev_name.lower().replace(' ', '_')}"
            records.append(PresetRecord(
                id=rec_id,
                name=f"Default {dev_name}",
                plugin_name=dev_name,
                vendor=vendor,
                category=cat,
                subcategory="Core Device",
                tags=tags,
                file_path=None,
                format="native_core",
                is_factory=True,
                metadata={"is_core_device": True}
            ))

        return records
