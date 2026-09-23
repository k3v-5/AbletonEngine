# engine/sound_design/vital_sound_engine.py
"""
Vital Sound Engine.

Autonomous sound synthesis and preset design engine for Vital Synth.
Sculpts and generates production-ready .vital patch files with guaranteed acoustic
audibility, custom algorithmic wavetables, and safe parameter boundaries.
"""

from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import json
import logging

from engine.sound_design.vital_parameter_schema import VitalParameterSchema
from engine.sound_design.vital_wavetable_synth import WavetableSynthesizer
from engine.sound_design.vital_archetype_catalog import ArchetypeCatalog
from engine.sound_design.vital_sound_sculptor import VitalSoundSculptor
from engine.sound_design.vital_design_validator import VitalDesignValidator, VitalValidationError, ValidationReport
from engine.sound_design.vital_modular_designer import VitalModularDesigner

logger = logging.getLogger("VitalSoundEngine")


class VitalSoundEngine:
    """
    Main orchestrator for programmatically creating and mutating Vital synth presets.
    Decoupled from session flow, usable anywhere in the engine or from external scripts.
    """

    DEFAULT_OUTPUT_DIR = Path("cache/vital_presets")

    def __init__(self, catalog_paths: Optional[List[Path]] = None):
        self.catalog = ArchetypeCatalog(search_paths=catalog_paths)
        self.sculptor = VitalSoundSculptor()
        self.schema = VitalParameterSchema()
        self.wavetable_synth = WavetableSynthesizer()
        self.validator = VitalDesignValidator()
        self.modular_designer = VitalModularDesigner()

    def create_preset(
        self,
        preset_name: str,
        role: str = "BASS_SUB",
        directives: Optional[Dict[str, Any]] = None,
        output_dir: Optional[Path] = None,
        base_archetype_name: Optional[str] = None
    ) -> Path:
        """
        Creates a new production-ready .vital preset by sculpting a battle-tested archetype.

        Args:
            preset_name: Display name of the new preset.
            role: Musical category (e.g. 'BASS_808', 'BASS_REECE', 'LEAD_SAW', 'CHORD_SUPERAW', 'PAD_LUSH').
            directives: High-level macro sound design directives (brightness, warmth_drive, punch, space, etc.).
            output_dir: Directory where the .vital file will be written.
            base_archetype_name: Optional specific preset to use as anchor.

        Returns:
            Path to the saved .vital file.
        """
        target_dir = output_dir or self.DEFAULT_OUTPUT_DIR
        target_dir.mkdir(parents=True, exist_ok=True)

        directives = directives or {}

        # 1. Select Archetype Anchor
        file_path, base_data = self.catalog.select_archetype(
            role=role,
            preferred_name=base_archetype_name
        )
        logger.info(f"[VitalSoundEngine] Using archetype base: {file_path.name} for role {role}")

        # 2. Sculpt Sound Semantically
        sculpted_data = self.sculptor.sculpt_preset(
            base_preset=base_data,
            directives=directives,
            preset_name=preset_name
        )

        # 3. Sanitize and Clamp All Settings
        settings = sculpted_data.get("settings", {})
        for param_name, param_val in list(settings.items()):
            if isinstance(param_val, (int, float)):
                settings[param_name] = self.schema.clamp_parameter(param_name, param_val)

        # 4. Enforce Non-Negotiable Invariants
        sculpted_data["settings"] = self.schema.enforce_anti_silence_invariants(settings)

        # 5. Write .vital Preset File
        safe_filename = "".join(c for c in preset_name if c.isalnum() or c in ("_", "-")).strip()
        if not safe_filename:
            safe_filename = "Generated_Patch"
        out_path = target_dir / f"{safe_filename}.vital"

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(sculpted_data, f, indent=2)

        logger.info(f"[VitalSoundEngine] Successfully generated preset: {out_path} ({out_path.stat().st_size} bytes)")
        return out_path

    def mutate_preset(
        self,
        source_path: Path,
        directives: Dict[str, Any],
        new_name: Optional[str] = None,
        output_dir: Optional[Path] = None
    ) -> Path:
        """
        Takes an existing .vital file and mutates its sonic characteristics.
        """
        source_path = Path(source_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source preset not found: {source_path}")

        base_data = json.loads(source_path.read_text(encoding="utf-8"))
        preset_name = new_name or f"{source_path.stem}_Mutated"

        target_dir = output_dir or self.DEFAULT_OUTPUT_DIR
        target_dir.mkdir(parents=True, exist_ok=True)

        sculpted_data = self.sculptor.sculpt_preset(
            base_preset=base_data,
            directives=directives,
            preset_name=preset_name
        )

        # Clamp and enforce invariants
        settings = sculpted_data.get("settings", {})
        for param_name, param_val in list(settings.items()):
            if isinstance(param_val, (int, float)):
                settings[param_name] = self.schema.clamp_parameter(param_name, param_val)

        sculpted_data["settings"] = self.schema.enforce_anti_silence_invariants(settings)

        out_path = target_dir / f"{preset_name}.vital"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(sculpted_data, f, indent=2)

        logger.info(f"[VitalSoundEngine] Mutated preset saved: {out_path}")
        return out_path

    def design_granular_preset(
        self,
        preset_name: str,
        spec: Dict[str, Any],
        role_archetype: str = "LEAD_SAW",
        output_dir: Optional[Path] = None,
        strict: bool = False
    ) -> Tuple[Path, Dict[str, Any]]:
        """
        Designs a custom preset using low-level granular specifications
        (custom waveforms, specialized filter models like Diode 303/Comb,
        custom LFO shapes like Sample & Hold, and modulation routing matrices).

        Validates all inputs, provides diagnostic reports on any auto-corrections,
        and guarantees acoustic integrity (anti-silence invariants).

        Returns:
            Tuple[Path, Dict[str, Any]]: (path_to_preset_file, diagnostic_validation_report)
        """
        target_dir = output_dir or self.DEFAULT_OUTPUT_DIR
        target_dir.mkdir(parents=True, exist_ok=True)

        # 1. Validate Specification
        report = self.validator.validate_specification(spec, strict=strict)

        # 2. Select Backbone Base Preset
        _, base_data = self.catalog.select_archetype(role=role_archetype)

        # 3. Materialize Modular Design
        designed_data = self.modular_designer.design_preset(
            base_preset=base_data,
            sanitized_spec=report.sanitized_spec,
            preset_name=preset_name
        )

        # 4. Sanitize and Clamp All Settings
        settings = designed_data.get("settings", {})
        for param_name, param_val in list(settings.items()):
            if isinstance(param_val, (int, float)):
                settings[param_name] = self.schema.clamp_parameter(param_name, param_val)

        # 5. Enforce Acoustic Integrity Gatekeeper
        designed_data["settings"] = self.schema.enforce_anti_silence_invariants(settings)

        # 6. Save .vital Preset File
        safe_filename = "".join(c for c in preset_name if c.isalnum() or c in ("_", "-")).strip() or "Custom_Patch"
        out_path = target_dir / f"{safe_filename}.vital"

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(designed_data, f, indent=2)

        logger.info(
            f"[VitalSoundEngine] Granular preset created: {out_path} "
            f"(Errors: {len(report.errors)}, Warnings: {len(report.warnings)}, Corrections: {len(report.corrections)})"
        )
        return out_path, report.to_dict()

    def audit_preset_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Audits a .vital file on disk to verify structural validity and audibility.
        """
        p = Path(file_path)
        if not p.exists():
            return {"valid": False, "error": "File does not exist"}

        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            return {"valid": False, "error": f"Invalid JSON syntax: {e}"}

        settings = data.get("settings", {})
        if not settings:
            return {"valid": False, "error": "Missing 'settings' key"}

        vol = float(settings.get("volume", 0.0))
        filter_cutoff = float(settings.get("filter_1_cutoff", 0.0))
        osc1_on = float(settings.get("osc_1_on", 0.0))
        osc1_level = float(settings.get("osc_1_level", 0.0))
        sustain = float(settings.get("env_1_sustain", 0.0))
        decay = float(settings.get("env_1_decay", 0.0))

        # Check all audio generators (osc 1, 2, 3, and sampler)
        osc1_active = osc1_on >= 0.5 and osc1_level >= 0.05
        osc2_active = float(settings.get("osc_2_on", 0.0)) >= 0.5 and float(settings.get("osc_2_level", 0.0)) >= 0.05
        osc3_active = float(settings.get("osc_3_on", 0.0)) >= 0.5 and float(settings.get("osc_3_level", 0.0)) >= 0.05
        sample_active = float(settings.get("sample_on", 0.0)) >= 0.5 and float(settings.get("sample_level", 0.0)) >= 0.05
        has_generator = osc1_active or osc2_active or osc3_active or sample_active

        # Audible if master volume safe, generator active, and note duration >= 25ms
        is_audible = (
            vol >= self.schema.VOLUME_MIN and
            has_generator and
            (sustain > 0.01 or decay >= 0.025)
        )

        return {
            "valid": True,
            "audible": is_audible,
            "preset_name": data.get("preset_name", p.stem),
            "file_size_bytes": p.stat().st_size,
            "volume": vol,
            "filter_cutoff": filter_cutoff,
            "osc1_level": osc1_level,
            "env1_sustain": sustain,
            "env1_decay": decay,
            "wavetables_count": len(settings.get("wavetables", [])),
            "has_sampler": bool(settings.get("sample", {}).get("samples"))
        }

    def list_available_archetypes(self) -> Dict[str, List[str]]:
        """Returns all discovered preset names grouped by category."""
        result = {}
        for category, presets in self.catalog.catalog.items():
            result[category] = [p["name"] for p in presets]
        return result
