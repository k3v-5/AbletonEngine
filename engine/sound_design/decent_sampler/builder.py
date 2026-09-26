# engine/sound_design/decent_sampler/builder.py
"""
High-Level Instrument Compiler & Builder for Decent Sampler.

Orchestrates sample asset planning, domain model construction, multi-tier validation,
sanitization, and XML serialization.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path

from .model import (
    InstrumentModel,
    GroupModel,
    SampleZoneModel,
    EffectModel,
    ModulatorModel,
    BindingModel,
    ControlModel,
    UIModel,
)
from .sample_analyzer import SampleAsset
from .sample_mapper import SampleMapPlanner, PlannedLayer
from .validator import DecentSamplerValidator, ValidationReport, ValidationError
from .sanitizer import DecentSamplerSanitizer
from .serializer import DSPresetSerializer
from .policies import UXPolicy, AudioSafetyPolicy


class DecentSamplerBuilder:
    """
    Fluent builder and compiler interface for generating production-grade .dspreset files.
    """

    def __init__(self, name: str = "New Instrument"):
        self.instrument = InstrumentModel(name=name)
        self._current_group = GroupModel(name="Default Group")
        self.instrument.add_group(self._current_group)

    def set_global_properties(
        self,
        volume: float = 1.0,
        global_pan: float = 0.0,
        global_tuning: float = 0.0,
        glide_time: float = 0.0,
        glide_mode: str = "legato",
    ) -> "DecentSamplerBuilder":
        """Configures instrument-wide acoustic properties."""
        self.instrument.volume = volume
        self.instrument.global_pan = global_pan
        self.instrument.global_tuning = global_tuning
        self.instrument.glide_time = glide_time
        self.instrument.glide_mode = glide_mode
        return self

    def set_envelope(
        self,
        attack: float = 0.001,
        decay: float = 1.0,
        sustain: float = 1.0,
        release: float = 0.3,
        group_index: int = 0,
    ) -> "DecentSamplerBuilder":
        """Sets the ADSR amplitude envelope for a specific group."""
        if 0 <= group_index < len(self.instrument.groups):
            grp = self.instrument.groups[group_index]
            grp.attack = attack
            grp.decay = decay
            grp.sustain = sustain
            grp.release = release
        return self

    def add_sample(
        self,
        path: str,
        root_note: int,
        lo_note: int,
        hi_note: int,
        lo_vel: int = 0,
        hi_vel: int = 127,
        group_index: int = 0,
        tuning: float = 0.0,
        trigger: str = "attack",
        seq_mode: str = "always",
        seq_position: int = 1,
        seq_length: int = 1,
        tags: Optional[str] = None,
    ) -> "DecentSamplerBuilder":
        """Adds a single sample zone explicitly to a group."""
        sample = SampleZoneModel(
            path=path.replace("\\", "/"),
            root_note=root_note,
            lo_note=lo_note,
            hi_note=hi_note,
            lo_vel=lo_vel,
            hi_vel=hi_vel,
            tuning=tuning,
            trigger=trigger,
            seq_mode=seq_mode,
            seq_position=seq_position,
            seq_length=seq_length,
            tags=tags,
        )
        if 0 <= group_index < len(self.instrument.groups):
            self.instrument.groups[group_index].add_sample(sample)
        else:
            new_grp = GroupModel(name=f"Group_{group_index}")
            new_grp.add_sample(sample)
            self.instrument.add_group(new_grp)
        return self

    def map_sample_assets(
        self,
        assets: List[SampleAsset],
        min_note: int = 0,
        max_note: int = 127,
        custom_velocity_layers: Optional[List[PlannedLayer]] = None,
    ) -> "DecentSamplerBuilder":
        """
        Uses SampleMapPlanner to automatically map sample assets across the keyboard
        with zero dead keys and balanced velocity layers.
        """
        # Clear default empty group if no samples in it yet
        if len(self.instrument.groups) == 1 and not self.instrument.groups[0].samples:
            self.instrument.groups.clear()

        planned_zones = SampleMapPlanner.plan(
            assets=assets,
            min_note=min_note,
            max_note=max_note,
            custom_velocity_layers=custom_velocity_layers,
        )
        SampleMapPlanner.apply_to_instrument(self.instrument, planned_zones)
        return self

    def add_effect(
        self,
        effect_type: str,
        tags: Optional[str] = None,
        level: str = "instrument",
        group_index: int = 0,
        **params: Any,
    ) -> "DecentSamplerBuilder":
        """Adds an effect to the global instrument chain or a specific group."""
        effect = EffectModel(
            type=effect_type.lower(),
            tags=tags,
            parameters=params,
        )
        if level == "group":
            if 0 <= group_index < len(self.instrument.groups):
                self.instrument.groups[group_index].effects.append(effect)
        else:
            self.instrument.add_effect(effect)
        return self

    def add_macro_knob(
        self,
        label: str,
        parameter: str,
        level: str = "instrument",
        target_index: int = 0,
        min_value: float = 0.0,
        max_value: float = 1.0,
        default_value: float = 0.5,
        value_type: str = "linear",
        tags: Optional[str] = None,
    ) -> "DecentSamplerBuilder":
        """
        Adds a macro control knob to the UI and binds it to the specified engine parameter.
        Uses UXPolicy for automatic ergonomic layout placement.
        """
        existing_controls = len(self.instrument.ui.controls)
        coords = UXPolicy.calculate_knob_layout(existing_controls + 1)
        x, y = coords[existing_controls]

        binding = BindingModel(
            type="effect" if parameter.startswith("FX_") else "amp",
            level=level,
            parameter=parameter,
            position=target_index,
            tags=tags,
            translation="linear",
            translation_output_min=min_value,
            translation_output_max=max_value,
        )

        control = ControlModel(
            control_type="labeled-knob",
            label=label,
            x=x,
            y=y,
            min_value=min_value,
            max_value=max_value,
            value=default_value,
            default_value=default_value,
            value_type=value_type,
            bindings=[binding],
        )
        self.instrument.add_control(control)
        return self

    def add_log_filter_knob(
        self,
        label: str = "Lowpass",
        target_position: int = 0,
        default_value: float = 1.0,
        track_foreground_color: Optional[str] = "FF41BDBE",
        track_background_color: Optional[str] = "668A8A8A",
    ) -> "DecentSamplerBuilder":
        """
        Adds a lowpass filter knob calibrated with the industry-standard 7-point
        logarithmic frequency table (33Hz -> 22kHz) for natural musical sweeps.
        """
        from .schema import DecentSamplerSchema
        existing_controls = len(self.instrument.ui.controls)
        coords = UXPolicy.calculate_knob_layout(existing_controls + 1)
        x, y = coords[existing_controls]

        binding = BindingModel(
            type="effect",
            level="instrument",
            parameter="FX_FILTER_FREQUENCY",
            position=target_position,
            translation="table",
            translation_table=DecentSamplerSchema.DEFAULT_LOG_FILTER_TABLE,
        )

        control = ControlModel(
            control_type="labeled-knob",
            label=label,
            x=x,
            y=y,
            width=80,
            height=80,
            min_value=0.0,
            max_value=1.0,
            value=default_value,
            default_value=default_value,
            type="float",
            track_foreground_color=track_foreground_color,
            track_background_color=track_background_color,
            bindings=[binding],
        )
        self.instrument.add_control(control)
        return self

    def ensure_production_ready(
        self,
        auto_complete: bool = True,
        strict: bool = False,
    ):
        """
        Audits instrument against the 'Definition of Done'.
        Auto-completes any missing configurations (knobs, dynamics, envelopes)
        and validates acoustic safety.
        """
        from .completeness import InstrumentCompletenessAuditor
        fixes = []
        if auto_complete:
            self.instrument, fixes = DecentSamplerSanitizer.sanitize(self.instrument, auto_complete=True)

        report = InstrumentCompletenessAuditor.audit(self.instrument)
        if auto_complete:
            report.auto_fixes_applied.extend(fixes)

        if strict and not report.is_production_ready:
            raise ValidationError(report.missing_configurations + report.acoustic_risks)

        return report

    def compile(
        self,
        strict: bool = False,
        sanitize: bool = True,
        auto_complete: bool = True,
    ) -> str:
        """
        Compiles the current model into clean .dspreset XML.
        Optionally applies auto-completion, sanitization, and runs 3-tier validation.
        """
        if sanitize:
            self.instrument, _ = DecentSamplerSanitizer.sanitize(
                self.instrument, auto_complete=auto_complete
            )

        report = DecentSamplerValidator.validate_model(self.instrument, strict=strict)
        if not report.is_valid and strict:
            raise ValidationError(report.all_errors)

        return DSPresetSerializer.serialize(self.instrument)

    def save(self, filepath: str, strict: bool = False, sanitize: bool = True) -> Path:
        """Compiles and writes the .dspreset file to disk."""
        xml_str = self.compile(strict=strict, sanitize=sanitize)
        out_path = Path(filepath)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(xml_str, encoding="utf-8")
        return out_path
