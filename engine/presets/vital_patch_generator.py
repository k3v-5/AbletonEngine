# engine/presets/vital_patch_generator.py
"""
Programmatic Vital Synth Patch Generator:
Generates production-grade .vital preset files (JSON) for modern wavetable sound design
without requiring manual preset selection or commercial patch banks.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger("VitalPatchGenerator")


class VitalPatchGenerator:
    """Creates synthesized .vital patches dynamically for EDM/Bass sound design."""

    @classmethod
    def create_patch_dict(
        cls,
        preset_name: str,
        sound_type: str = "BASS_GROWL",
        cutoff: float = 0.65,
        resonance: float = 0.45,
        distortion_drive: float = 0.60
    ) -> Dict[str, Any]:
        """
        Generates standard Vital JSON structure.
        """
        sound_type_upper = sound_type.upper()

        osc1_wave = 1.0  # Saw
        if "GROWL" in sound_type_upper or "BASS" in sound_type_upper:
            osc1_wave = 3.0  # Formant/Wavetable
        elif "SUB" in sound_type_upper:
            osc1_wave = 0.0  # Sine

        patch = {
            "author": "AbletonEngine AI Executive Producer",
            "comments": f"Synthesized patch for {preset_name} ({sound_type})",
            "preset_name": preset_name,
            "preset_style": sound_type,
            "synth_version": "1.5.5",
            "settings": {
                "polyphony": 1 if "BASS" in sound_type_upper or "LEAD" in sound_type_upper else 8,
                "osc_1_on": 1.0,
                "osc_1_wave_frame": osc1_wave,
                "osc_1_level": 0.85,
                "osc_1_unison_voices": 4 if "LEAD" in sound_type_upper else 1,
                "osc_1_unison_detune": 0.15 if "LEAD" in sound_type_upper else 0.0,
                "filter_1_on": 1.0,
                "filter_1_cutoff": cutoff,
                "filter_1_resonance": resonance,
                "distortion_on": 1.0 if distortion_drive > 0.1 else 0.0,
                "distortion_drive": distortion_drive,
                "chorus_on": 1.0 if "PAD" in sound_type_upper else 0.0,
                "reverb_on": 1.0 if "PAD" in sound_type_upper or "LEAD" in sound_type_upper else 0.0,
                "delay_on": 1.0 if "LEAD" in sound_type_upper or "PLUCK" in sound_type_upper else 0.0
            }
        }
        return patch

    @classmethod
    def save_vital_preset(
        cls,
        preset_name: str,
        sound_type: str = "BASS_GROWL",
        output_dir: Optional[Path] = None,
        **kwargs
    ) -> Path:
        """
        Writes a synthesized .vital patch file to disk.
        """
        target_dir = output_dir or Path("cache/vital_presets")
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c for c in preset_name if c.isalnum() or c in ("_", "-")).strip()
        filepath = target_dir / f"{safe_name}.vital"

        patch_data = cls.create_patch_dict(preset_name=preset_name, sound_type=sound_type, **kwargs)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(patch_data, f, indent=2)

        logger.info(f"Generated Vital preset: {filepath}")
        return filepath
