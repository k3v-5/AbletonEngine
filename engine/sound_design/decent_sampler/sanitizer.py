# engine/sound_design/decent_sampler/sanitizer.py
"""
Resilient Sanitizer & Auto-Corrector for Decent Sampler Models.

Heals common sound design slips, normalizes identifiers, fixes path separators,
and enforces safety policies without breaking production sessions.
"""

from typing import List, Tuple, Set
from pathlib import Path
import re

from .schema import DecentSamplerSchema
from .model import (
    InstrumentModel,
    GroupModel,
    SampleZoneModel,
    EffectModel,
    ControlModel,
    BindingModel,
)
from .policies import AudioSafetyPolicy, ResourcePolicy, UXPolicy


class DecentSamplerSanitizer:
    """
    Applies non-destructive corrections to an InstrumentModel to guarantee
    schema conformity, acoustic integrity, and AI auto-completion.
    """

    @classmethod
    def sanitize(
        cls,
        instrument: InstrumentModel,
        auto_complete: bool = True,
        normalize_headroom: bool = True,
    ) -> Tuple[InstrumentModel, List[str]]:
        """
        Sanitizes an InstrumentModel in-place and returns a log of corrections applied.
        """
        corrections: List[str] = []

        # 1. Sanitize instrument-level effects
        cls._sanitize_effects(instrument.effects, "instrument", corrections)

        # 2. Sanitize groups, samples, and group-level effects
        migrated_effects: List[EffectModel] = []

        for g_idx, group in enumerate(instrument.groups):
            # Audio safety policy: envelope anti-click floor
            if group.amp_env_enabled:
                if group.attack < AudioSafetyPolicy.RECOMMENDED_MIN_ATTACK_SEC:
                    old_att = group.attack
                    group.attack = AudioSafetyPolicy.RECOMMENDED_MIN_ATTACK_SEC
                    corrections.append(
                        f"group[{g_idx}] attack raised from {old_att}s to {group.attack}s "
                        "(AudioSafetyPolicy anti-click floor)."
                    )
                if group.release < AudioSafetyPolicy.RECOMMENDED_MIN_RELEASE_SEC:
                    old_rel = group.release
                    group.release = AudioSafetyPolicy.RECOMMENDED_MIN_RELEASE_SEC
                    corrections.append(
                        f"group[{g_idx}] release raised from {old_rel}s to {group.release}s "
                        "(AudioSafetyPolicy anti-click floor)."
                    )

            # Check for group effects that should be global (reverb, delay)
            retained_group_effects = []
            for e_idx, effect in enumerate(group.effects):
                cls._sanitize_single_effect(effect, f"group[{g_idx}].effects[{e_idx}]", corrections)
                if effect.type in DecentSamplerSchema.GLOBAL_ONLY_EFFECTS:
                    corrections.append(
                        f"Moved '{effect.type}' from group[{g_idx}] to instrument-level <effects> "
                        "(Decent Sampler global-only effect compatibility rule)."
                    )
                    migrated_effects.append(effect)
                else:
                    retained_group_effects.append(effect)
            group.effects = retained_group_effects

            # Dynamic velocity auto-completion
            if auto_complete:
                vel_layers = set((s.lo_vel, s.hi_vel) for s in group.samples)
                if group.amp_vel_track == 0.0 and len(vel_layers) <= 1:
                    group.amp_vel_track = 0.85
                    corrections.append(
                        f"group[{g_idx}] ampVelTrack auto-set to 0.85 to ensure musical dynamic touch response."
                    )

            # Sanitize samples within group
            for s_idx, sample in enumerate(group.samples):
                cls._sanitize_sample(sample, f"group[{g_idx}].sample[{s_idx}]", corrections)

        # Add migrated effects to instrument
        for eff in migrated_effects:
            instrument.add_effect(eff)

        # 3. Headroom normalization for polyphony
        if normalize_headroom:
            cls._normalize_gain_headroom(instrument, corrections)

        # 4. Auto-complete missing UI knobs for orphaned effects
        if auto_complete:
            cls._auto_complete_controls(instrument, corrections)

        return instrument, corrections

    @classmethod
    def _normalize_gain_headroom(cls, instrument: InstrumentModel, corrections: List[str]) -> None:
        """Scales down group volumes if total potential gain risks clipping the DAW master bus."""
        simultaneous_gain = 0.0
        active_groups: List[GroupModel] = []
        for g in instrument.groups:
            if not g.enabled:
                continue
            if g.seq_mode in ("always", "true_random"):
                simultaneous_gain += g.volume
                active_groups.append(g)
            elif g.seq_mode == "round_robin":
                simultaneous_gain = max(simultaneous_gain, g.volume)
                active_groups.append(g)

        total_gain = simultaneous_gain * instrument.volume
        # Max safe gain ~1.41 (+3dB)
        if total_gain > 1.41 and active_groups:
            scale_factor = 1.0 / total_gain
            for g in active_groups:
                g.volume = round(g.volume * scale_factor, 4)
            corrections.append(
                f"Normalized simultaneous group gains by {scale_factor:.3f}x to protect DAW headroom "
                f"(reduced potential peak from {total_gain:.2f} to 1.0)."
            )

    @classmethod
    def _auto_complete_controls(cls, instrument: InstrumentModel, corrections: List[str]) -> None:
        """Automatically synthesizes UI knobs with bindings for any unmapped effects."""
        bound_positions: Set[int] = set()
        for ctrl in instrument.ui.controls:
            for b in ctrl.bindings:
                if b.type == "effect" and b.level == "instrument" and b.position is not None:
                    bound_positions.add(b.position)

        for pos, effect in enumerate(instrument.effects):
            if pos in bound_positions:
                continue

            eff_type = effect.type.lower()
            # Calculate next knob position
            knob_idx = len(instrument.ui.controls)
            coords = UXPolicy.calculate_knob_layout(knob_idx + 1)
            kx, ky = coords[-1] if coords else (40 + knob_idx * 100, 40)

            if "lowpass" in eff_type:
                knob = ControlModel(
                    control_type="labeled-knob",
                    label="Cutoff",
                    x=kx,
                    y=ky,
                    width=80,
                    height=80,
                    min_value=0.0,
                    max_value=1.0,
                    value=1.0,
                    default_value=1.0,
                    type="float",
                    bindings=[
                        BindingModel(
                            type="effect",
                            level="instrument",
                            position=pos,
                            parameter="FX_FILTER_FREQUENCY",
                            translation="table",
                            translation_table=DecentSamplerSchema.DEFAULT_LOG_FILTER_TABLE,
                        )
                    ],
                )
                instrument.add_control(knob)
                corrections.append(
                    f"Auto-completed UI knob 'Cutoff' with 7-point log table for orphaned effect[{pos}] '{eff_type}'."
                )
            elif "reverb" in eff_type:
                knob = ControlModel(
                    control_type="labeled-knob",
                    label="Reverb",
                    x=kx,
                    y=ky,
                    width=80,
                    height=80,
                    min_value=0.0,
                    max_value=100.0,
                    value=15.0,
                    default_value=15.0,
                    type="percent",
                    bindings=[
                        BindingModel(
                            type="effect",
                            level="instrument",
                            position=pos,
                            parameter="FX_REVERB_WET_LEVEL",
                            translation="linear",
                            translation_output_min=0.0,
                            translation_output_max=1.0,
                        )
                    ],
                )
                instrument.add_control(knob)
                corrections.append(
                    f"Auto-completed UI knob 'Reverb' for orphaned effect[{pos}] '{eff_type}'."
                )
            elif "delay" in eff_type:
                knob = ControlModel(
                    control_type="labeled-knob",
                    label="Delay",
                    x=kx,
                    y=ky,
                    width=80,
                    height=80,
                    min_value=0.0,
                    max_value=100.0,
                    value=0.0,
                    default_value=0.0,
                    type="percent",
                    bindings=[
                        BindingModel(
                            type="effect",
                            level="instrument",
                            position=pos,
                            parameter="FX_DELAY_WET_LEVEL",
                            translation="linear",
                            translation_output_min=0.0,
                            translation_output_max=1.0,
                        )
                    ],
                )
                instrument.add_control(knob)
                corrections.append(
                    f"Auto-completed UI knob 'Delay' for orphaned effect[{pos}] '{eff_type}'."
                )


    @classmethod
    def _sanitize_effects(cls, effects: List[EffectModel], context: str, corrections: List[str]) -> None:
        for idx, effect in enumerate(effects):
            cls._sanitize_single_effect(effect, f"{context}.effects[{idx}]", corrections)

    @classmethod
    def _sanitize_single_effect(cls, effect: EffectModel, context: str, corrections: List[str]) -> None:
        # Canonical lowercase invariant
        if effect.type != effect.type.lower():
            old_type = effect.type
            effect.type = effect.type.lower()
            corrections.append(
                f"{context}: Lowercased effect type from '{old_type}' to canonical '{effect.type}'."
            )

    @classmethod
    def _sanitize_sample(cls, sample: SampleZoneModel, context: str, corrections: List[str]) -> None:
        # Path normalization: Windows backslash to forward slash
        if "\\" in sample.path:
            old_path = sample.path
            sample.path = sample.path.replace("\\", "/")
            corrections.append(
                f"{context}: Converted Windows backslashes to forward slashes in path ('{sample.path}')."
            )

        # Strip Windows drive letter if present for portability
        if len(sample.path) > 1 and sample.path[1] == ":":
            old_path = sample.path
            sample.path = re.sub(r"^[a-zA-Z]:[/|\\]+", "", sample.path)
            corrections.append(
                f"{context}: Stripped absolute drive letter from path ('{old_path}' -> '{sample.path}')."
            )

        # Note range ordering & clamping
        sample.root_note = max(0, min(sample.root_note, 127))
        sample.lo_note = max(0, min(sample.lo_note, 127))
        sample.hi_note = max(0, min(sample.hi_note, 127))

        if sample.lo_note > sample.hi_note:
            sample.lo_note, sample.hi_note = sample.hi_note, sample.lo_note
            corrections.append(
                f"{context}: Inverted note bounds swapped to [lo={sample.lo_note}, hi={sample.hi_note}]."
            )

        if sample.root_note < sample.lo_note:
            sample.root_note = sample.lo_note
            corrections.append(
                f"{context}: rootNote raised to loNote ({sample.root_note}) to maintain valid trigger range."
            )
        elif sample.root_note > sample.hi_note:
            sample.root_note = sample.hi_note
            corrections.append(
                f"{context}: rootNote lowered to hiNote ({sample.root_note}) to maintain valid trigger range."
            )

        # Velocity range ordering & clamping
        sample.lo_vel = max(0, min(sample.lo_vel, 127))
        sample.hi_vel = max(0, min(sample.hi_vel, 127))

        if sample.lo_vel > sample.hi_vel:
            sample.lo_vel, sample.hi_vel = sample.hi_vel, sample.lo_vel
            corrections.append(
                f"{context}: Inverted velocity bounds swapped to [lo={sample.lo_vel}, hi={sample.hi_vel}]."
            )

        # Round-robin consistency
        if sample.seq_position > sample.seq_length:
            old_len = sample.seq_length
            sample.seq_length = sample.seq_position
            corrections.append(
                f"{context}: seqLength expanded from {old_len} to {sample.seq_length} to match seqPosition."
            )
