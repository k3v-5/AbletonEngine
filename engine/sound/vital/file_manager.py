# engine/sound/vital/file_manager.py
"""
Vital Preset Manager
Handles saving, serialization, verification, and cataloging of .vital JSON preset files
both inside the engine repository and into the user's local Vital directory.
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from engine.sound.vital.models import VitalPresetSpec

USER_VITAL_PRESETS_DIR = Path(r"D:\Documentos\Vital\User\Presets\PIE_Presets")
ENGINE_PRESETS_DIR = Path(r"F:\Dev\AbletonEngine\presets\vital")
TEMPLATE_PATH = Path(__file__).parent / "template.vital"

class VitalPresetManager:
    """Manages serialization and deployment of .vital patches."""

    def __init__(
        self,
        user_dir: Optional[Path] = None,
        engine_dir: Optional[Path] = None,
        template_path: Optional[Path] = None
    ):
        self.user_dir = user_dir or USER_VITAL_PRESETS_DIR
        self.engine_dir = engine_dir or ENGINE_PRESETS_DIR
        self.template_path = template_path or TEMPLATE_PATH
        
        # Ensure target directories exist
        self.engine_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.user_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def _load_base_template(self) -> Dict[str, Any]:
        """Loads clean base template with initialized Vital parameters and wavetables."""
        if self.template_path.exists():
            with open(self.template_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "author": "Ableton PIE Engine",
            "comments": "Synthesized Preset",
            "macro1": "Macro 1",
            "macro2": "Macro 2",
            "macro3": "Macro 3",
            "macro4": "Macro 4",
            "preset_style": "Bass",
            "settings": {},
            "synth_version": "1.6.2"
        }

    def serialize_spec_to_dict(self, spec: VitalPresetSpec) -> Dict[str, Any]:
        """Transforms a VitalPresetSpec into a valid Vital preset JSON object."""
        preset = self._load_base_template()
        settings = preset.setdefault("settings", {})
        
        # Metadata
        preset["author"] = spec.author
        preset["comments"] = spec.comments
        preset["macro1"] = spec.macro1
        preset["macro2"] = spec.macro2
        preset["macro3"] = spec.macro3
        preset["macro4"] = spec.macro4
        preset["preset_style"] = spec.preset_style.value if hasattr(spec.preset_style, "value") else str(spec.preset_style)

        # Apply Oscillators
        for i, osc in enumerate(spec.oscillators, start=1):
            settings[f"osc_{i}_on"] = 1.0 if osc.on else 0.0
            settings[f"osc_{i}_level"] = osc.level
            settings[f"osc_{i}_pan"] = osc.pan
            settings[f"osc_{i}_transpose"] = float(osc.transpose)
            settings[f"osc_{i}_tune"] = osc.tune
            settings[f"osc_{i}_wave_frame"] = osc.wave_frame
            settings[f"osc_{i}_unison_voices"] = float(osc.unison_voices)
            settings[f"osc_{i}_unison_detune"] = osc.unison_detune
            settings[f"osc_{i}_unison_blend"] = osc.unison_blend
            settings[f"osc_{i}_distortion_type"] = float(osc.distortion_type)
            settings[f"osc_{i}_distortion_amount"] = osc.distortion_amount
            settings[f"osc_{i}_spectral_morph_type"] = float(osc.spectral_morph_type)
            settings[f"osc_{i}_spectral_morph_amount"] = osc.spectral_morph_amount
            settings[f"osc_{i}_destination"] = float(osc.destination)

        # Apply Filters
        for i, flt in enumerate(spec.filters, start=1):
            settings[f"filter_{i}_on"] = 1.0 if flt.on else 0.0
            settings[f"filter_{i}_model"] = float(flt.model)
            settings[f"filter_{i}_style"] = float(flt.style)
            settings[f"filter_{i}_cutoff"] = flt.cutoff
            settings[f"filter_{i}_resonance"] = flt.resonance
            settings[f"filter_{i}_drive"] = flt.drive
            settings[f"filter_{i}_blend"] = flt.blend
            settings[f"filter_{i}_keytrack"] = flt.keytrack

        # Apply Envelopes
        for i, env in enumerate(spec.envelopes, start=1):
            settings[f"env_{i}_attack"] = env.attack
            settings[f"env_{i}_decay"] = env.decay
            settings[f"env_{i}_sustain"] = env.sustain
            settings[f"env_{i}_release"] = env.release
            settings[f"env_{i}_attack_power"] = env.attack_power
            settings[f"env_{i}_decay_power"] = env.decay_power
            settings[f"env_{i}_release_power"] = env.release_power

        # Apply LFOs
        for i, lfo in enumerate(spec.lfos, start=1):
            settings[f"lfo_{i}_frequency"] = lfo.frequency
            settings[f"lfo_{i}_sync"] = 1.0 if lfo.sync else 0.0
            settings[f"lfo_{i}_tempo"] = float(lfo.tempo)
            settings[f"lfo_{i}_smooth_time"] = lfo.smooth_time

        # Apply Effects
        fx = spec.effects
        settings["distortion_on"] = 1.0 if fx.distortion_on else 0.0
        settings["distortion_drive"] = fx.distortion_drive
        settings["distortion_mix"] = fx.distortion_mix
        settings["distortion_type"] = float(fx.distortion_type)
        
        settings["compressor_on"] = 1.0 if fx.compressor_on else 0.0
        settings["compressor_attack"] = fx.compressor_attack
        settings["compressor_release"] = fx.compressor_release
        settings["compressor_mix"] = fx.compressor_mix
        settings["compressor_band_gain"] = fx.compressor_band_gain

        settings["chorus_on"] = 1.0 if fx.chorus_on else 0.0
        settings["chorus_dry_wet"] = fx.chorus_dry_wet
        settings["chorus_voices"] = float(fx.chorus_voices)

        settings["delay_on"] = 1.0 if fx.delay_on else 0.0
        settings["delay_dry_wet"] = fx.delay_dry_wet
        settings["delay_tempo"] = float(fx.delay_tempo)
        settings["delay_feedback"] = fx.delay_feedback
        settings["delay_style"] = float(fx.delay_style)

        settings["reverb_on"] = 1.0 if fx.reverb_on else 0.0
        settings["reverb_dry_wet"] = fx.reverb_dry_wet
        settings["reverb_decay_time"] = fx.reverb_decay_time
        settings["reverb_size"] = fx.reverb_size

        # Apply Modulations
        mod_list = []
        for idx, mod in enumerate(spec.modulations, start=1):
            if idx > 64:
                break
            mod_list.append({
                "source": mod.source,
                "destination": mod.destination
            })
            settings[f"modulation_{idx}_amount"] = mod.amount
            settings[f"modulation_{idx}_bipolar"] = 1.0 if mod.bipolar else 0.0
            settings[f"modulation_{idx}_bypass"] = 0.0
            settings[f"modulation_{idx}_power"] = 0.0
            settings[f"modulation_{idx}_stereo"] = 0.0
        settings["modulations"] = mod_list

        # Apply custom settings overrides
        for k, v in spec.settings.items():
            settings[k] = v

        return preset

    def save_preset(
        self,
        spec: VitalPresetSpec,
        filename: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Saves a synthesized preset to both engine library and user Vital folder.
        Returns dictionary with file paths and preset name.
        """
        if not filename:
            clean_name = "".join(c for c in spec.preset_name if c.isalnum() or c in (" ", "_", "-")).strip()
            filename = f"{clean_name}.vital"
        if not filename.endswith(".vital"):
            filename += ".vital"

        data = self.serialize_spec_to_dict(spec)

        engine_path = self.engine_dir / filename
        with open(engine_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        user_path = None
        try:
            self.user_dir.mkdir(parents=True, exist_ok=True)
            user_path_candidate = self.user_dir / filename
            with open(user_path_candidate, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            user_path = str(user_path_candidate)
        except Exception:
            pass

        return {
            "preset_name": spec.preset_name,
            "filename": filename,
            "engine_path": str(engine_path),
            "user_path": user_path or str(engine_path),
            "style": spec.preset_style.value if hasattr(spec.preset_style, "value") else str(spec.preset_style)
        }

    def list_presets(self, category: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """Scans engine and user directories for .vital presets and extracts metadata."""
        presets = []
        scanned_names = set()
        
        dirs_to_scan = [self.user_dir, self.engine_dir]
        for sdir in dirs_to_scan:
            if not sdir.exists():
                continue
            for f in sdir.glob("*.vital"):
                if f.name in scanned_names:
                    continue
                scanned_names.add(f.name)
                try:
                    with open(f, "r", encoding="utf-8") as pf:
                        d = json.load(pf)
                    name = f.stem
                    style = d.get("preset_style", "Unknown")
                    author = d.get("author", "Unknown")
                    comments = d.get("comments", "")
                    macros = [d.get(f"macro{i}", f"Macro {i}") for i in range(1, 5)]
                    
                    if category and category.lower() not in style.lower():
                        continue
                    if search and (search.lower() not in name.lower() and search.lower() not in comments.lower()):
                        continue
                        
                    presets.append({
                        "name": name,
                        "style": style,
                        "author": author,
                        "comments": comments,
                        "macros": macros,
                        "path": str(f)
                    })
                except Exception:
                    continue
        return presets
