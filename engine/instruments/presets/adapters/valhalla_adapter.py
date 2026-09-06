# engine/instruments/presets/adapters/valhalla_adapter.py
"""
Valhalla DSP Preset & Algorithm Adapter:
Catalog of standard algorithms, modes, and curated presets for:
- ValhallaVintageVerb
- ValhallaDelay
- ValhallaShimmer
- ValhallaPlate
"""

from typing import List, Dict, Any, Optional
from ..models import PresetRecord, PresetCategory


class ValhallaPresetAdapter:
    CATALOG = [
        # ValhallaVintageVerb
        {
            "id": "valhalla_vv_vocal_lush_hall",
            "name": "Lush Vocal Hall",
            "plugin_name": "ValhallaVintageVerb",
            "vendor": "Valhalla DSP",
            "category": PresetCategory.REVERB.value,
            "subcategory": "Vocal",
            "tags": ["reverb", "vocal", "hall", "lush", "spacious"],
            "parameters": {"Mix": 0.25, "Decay": 2.8, "PreDelay": 25.0, "HighCut": 6500.0, "LowCut": 200.0, "Mode": "Concert Hall"}
        },
        {
            "id": "valhalla_vv_snare_plate_80s",
            "name": "1980s Snare Plate",
            "plugin_name": "ValhallaVintageVerb",
            "vendor": "Valhalla DSP",
            "category": PresetCategory.REVERB.value,
            "subcategory": "Drums",
            "tags": ["reverb", "snare", "plate", "vintage", "80s"],
            "parameters": {"Mix": 0.30, "Decay": 1.4, "PreDelay": 0.0, "HighCut": 7500.0, "LowCut": 300.0, "Mode": "Plate"}
        },
        {
            "id": "valhalla_vv_rhodes_ambient_space",
            "name": "Rhodes Ambient Chamber",
            "plugin_name": "ValhallaVintageVerb",
            "vendor": "Valhalla DSP",
            "category": PresetCategory.REVERB.value,
            "subcategory": "Keys",
            "tags": ["reverb", "rhodes", "keys", "warm", "chamber"],
            "parameters": {"Mix": 0.20, "Decay": 3.2, "PreDelay": 15.0, "HighCut": 5000.0, "LowCut": 180.0, "Mode": "Dirty Hall"}
        },
        {
            "id": "valhalla_vv_dark_space_lead",
            "name": "Dark Space Sanctuary",
            "plugin_name": "ValhallaVintageVerb",
            "vendor": "Valhalla DSP",
            "category": PresetCategory.REVERB.value,
            "subcategory": "Lead",
            "tags": ["reverb", "dark", "lead", "synth", "wide"],
            "parameters": {"Mix": 0.35, "Decay": 4.5, "PreDelay": 40.0, "HighCut": 4000.0, "LowCut": 250.0, "Mode": "Sanctuary"}
        },
        # ValhallaDelay
        {
            "id": "valhalla_delay_tape_slapback",
            "name": "Vintage Tape Slap",
            "plugin_name": "ValhallaDelay",
            "vendor": "Valhalla DSP",
            "category": PresetCategory.DELAY.value,
            "subcategory": "Vocal",
            "tags": ["delay", "tape", "slapback", "vocal", "warm"],
            "parameters": {"Mix": 0.20, "DelaySync": 1, "Feedback": 0.15, "Mode": "Tape", "Drive": 0.3}
        },
        {
            "id": "valhalla_delay_dotted_eighth_lead",
            "name": "Dotted 8th Hypnotic Echo",
            "plugin_name": "ValhallaDelay",
            "vendor": "Valhalla DSP",
            "category": PresetCategory.DELAY.value,
            "subcategory": "Lead",
            "tags": ["delay", "pingpong", "dotted_eighth", "lead", "spacious"],
            "parameters": {"Mix": 0.28, "DelaySync": 1, "Feedback": 0.42, "Mode": "HiFi", "Era": "Now"}
        },
        {
            "id": "valhalla_delay_ghost_drift",
            "name": "Ghost Pitch Diffusion",
            "plugin_name": "ValhallaDelay",
            "vendor": "Valhalla DSP",
            "category": PresetCategory.CREATIVE_FX.value,
            "subcategory": "Creative FX",
            "tags": ["delay", "ghost", "pitch", "ambient", "texture"],
            "parameters": {"Mix": 0.40, "Feedback": 0.65, "Mode": "Ghost"}
        },
        # ValhallaPlate & Shimmer
        {
            "id": "valhalla_plate_bright_vocal",
            "name": "Bright Studio Plate",
            "plugin_name": "ValhallaPlate",
            "vendor": "Valhalla DSP",
            "category": PresetCategory.REVERB.value,
            "subcategory": "Vocal",
            "tags": ["reverb", "plate", "bright", "vocal", "presence"],
            "parameters": {"Mix": 0.22, "Decay": 2.2, "HighCut": 8000.0}
        },
        {
            "id": "valhalla_shimmer_celestial_pad",
            "name": "Celestial Octave Shimmer",
            "plugin_name": "ValhallaShimmer",
            "vendor": "Valhalla DSP",
            "category": PresetCategory.CREATIVE_FX.value,
            "subcategory": "Pad",
            "tags": ["reverb", "shimmer", "celestial", "pitch_shift", "ambient"],
            "parameters": {"Mix": 0.45, "Decay": 6.0, "Shift": 12.0}
        },
    ]

    def is_available(self) -> bool:
        return True

    def scan(self) -> List[PresetRecord]:
        records: List[PresetRecord] = []
        for item in self.CATALOG:
            records.append(PresetRecord(
                id=item["id"],
                name=item["name"],
                plugin_name=item["plugin_name"],
                vendor=item["vendor"],
                category=item["category"],
                subcategory=item["subcategory"],
                tags=item["tags"],
                file_path=None,
                format="algorithmic",
                is_factory=True,
                metadata={"parameters": item["parameters"]}
            ))
        return records
