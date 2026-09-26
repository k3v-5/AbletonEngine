# engine/sound_design/decent_sampler/templates/dual_layer_pad.py
"""
Dual-Layer Atmospheric Pad & Shimmer Template for Decent Sampler.

Features:
- Dual simultaneous layer architecture (Dry synth/acoustic body + Shimmer/Texture layer)
- Logarithmic 7-point lowpass filter sweep
- Independent layer balance controls
- Long, lush swelling envelopes with zero clicks
"""

from typing import List, Optional
from ..builder import DecentSamplerBuilder
from ..model import GroupModel, SampleZoneModel, BindingModel, ControlModel
from ..schema import DecentSamplerSchema
from ..policies import UXPolicy


def create_dual_layer_pad(
    name: str = "Celestial Shimmer Pad",
    dry_samples: Optional[List[SampleZoneModel]] = None,
    shimmer_samples: Optional[List[SampleZoneModel]] = None,
) -> DecentSamplerBuilder:
    """Creates a production-grade dual-layer ambient/shimmer pad instrument."""
    builder = DecentSamplerBuilder(name=name)
    builder.set_global_properties(volume=0.9, global_pan=0.0)

    # Clear initial default group
    builder.instrument.groups.clear()

    # Layer 1: Dry / Warm Core
    dry_group = GroupModel(
        name="Dry Layer",
        volume=0.7,
        attack=0.4,
        decay=6.0,
        sustain=1.0,
        release=1.8,
        seq_mode="always",
        amp_vel_track=0.8,
    )
    if dry_samples:
        for s in dry_samples:
            dry_group.add_sample(s)
    else:
        # Defaults spanning the keyboard
        dry_group.add_sample(SampleZoneModel(path="Samples/pad_c2.wav", root_note=36, lo_note=24, hi_note=47))
        dry_group.add_sample(SampleZoneModel(path="Samples/pad_c3.wav", root_note=48, lo_note=48, hi_note=59))
        dry_group.add_sample(SampleZoneModel(path="Samples/pad_c4.wav", root_note=60, lo_note=60, hi_note=71))
        dry_group.add_sample(SampleZoneModel(path="Samples/pad_c5.wav", root_note=72, lo_note=72, hi_note=83))
        dry_group.add_sample(SampleZoneModel(path="Samples/pad_c6.wav", root_note=84, lo_note=84, hi_note=108))

    # Layer 2: Shimmer / Ambient Texture
    shimmer_group = GroupModel(
        name="Shimmer Layer",
        volume=0.5,
        attack=0.6,
        decay=8.0,
        sustain=1.0,
        release=2.2,
        seq_mode="always",
        amp_vel_track=0.9,
    )
    if shimmer_samples:
        for s in shimmer_samples:
            shimmer_group.add_sample(s)
    else:
        shimmer_group.add_sample(SampleZoneModel(path="Samples/shimmer_c2.wav", root_note=36, lo_note=24, hi_note=47))
        shimmer_group.add_sample(SampleZoneModel(path="Samples/shimmer_c3.wav", root_note=48, lo_note=48, hi_note=59))
        shimmer_group.add_sample(SampleZoneModel(path="Samples/shimmer_c4.wav", root_note=60, lo_note=60, hi_note=71))
        shimmer_group.add_sample(SampleZoneModel(path="Samples/shimmer_c5.wav", root_note=72, lo_note=72, hi_note=83))
        shimmer_group.add_sample(SampleZoneModel(path="Samples/shimmer_c6.wav", root_note=84, lo_note=84, hi_note=108))

    builder.instrument.add_group(dry_group)
    builder.instrument.add_group(shimmer_group)

    # Global Effects
    builder.add_effect("lowpass", frequency=20000.0, resonance=0.7, tags="master_filter")
    builder.add_effect("reverb", roomSize=0.88, damping=0.2, wetLevel=0.35, tags="cathedral_space")

    # Macro Controls with Ergonomic Coordinates
    # Knob 1: Lowpass with 7-point log curve
    builder.add_log_filter_knob(label="Lowpass", target_position=0, default_value=1.0)

    # Knob 2: Shimmer Layer Blend (Controls Group 1 Volume)
    coords = UXPolicy.calculate_knob_layout(5)
    shimmer_ctrl = ControlModel(
        control_type="labeled-knob",
        label="Shimmer",
        x=coords[1][0],
        y=coords[1][1],
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        default_value=0.5,
        type="percent",
        bindings=[
            BindingModel(
                type="amp",
                level="group",
                position=1,
                parameter="AMP_VOLUME",
                translation="linear",
                translation_output_min=0.0,
                translation_output_max=1.0,
            )
        ],
    )
    builder.instrument.add_control(shimmer_ctrl)

    # Knob 3: Reverb Wet
    reverb_ctrl = ControlModel(
        control_type="labeled-knob",
        label="Reverb",
        x=coords[2][0],
        y=coords[2][1],
        min_value=0.0,
        max_value=100.0,
        value=35.0,
        default_value=35.0,
        type="percent",
        bindings=[
            BindingModel(
                type="effect",
                level="instrument",
                position=1,
                parameter="FX_REVERB_WET_LEVEL",
                translation="linear",
                translation_output_min=0.0,
                translation_output_max=1.0,
            )
        ],
    )
    builder.instrument.add_control(reverb_ctrl)

    # Knob 4: Attack Time
    attack_ctrl = ControlModel(
        control_type="labeled-knob",
        label="Attack",
        x=coords[3][0],
        y=coords[3][1],
        min_value=0.05,
        max_value=3.0,
        value=0.4,
        default_value=0.4,
        type="float",
        bindings=[
            BindingModel(
                type="amp",
                level="group",
                position=0,
                parameter="ENV_ATTACK",
                translation="linear",
                translation_output_min=0.05,
                translation_output_max=3.0,
            ),
            BindingModel(
                type="amp",
                level="group",
                position=1,
                parameter="ENV_ATTACK",
                translation="linear",
                translation_output_min=0.05,
                translation_output_max=3.0,
            ),
        ],
    )
    builder.instrument.add_control(attack_ctrl)

    # Knob 5: Release Time
    release_ctrl = ControlModel(
        control_type="labeled-knob",
        label="Release",
        x=coords[4][0],
        y=coords[4][1],
        min_value=0.1,
        max_value=5.0,
        value=1.8,
        default_value=1.8,
        type="float",
        bindings=[
            BindingModel(
                type="amp",
                level="group",
                position=0,
                parameter="ENV_RELEASE",
                translation="linear",
                translation_output_min=0.1,
                translation_output_max=5.0,
            ),
            BindingModel(
                type="amp",
                level="group",
                position=1,
                parameter="ENV_RELEASE",
                translation="linear",
                translation_output_min=0.1,
                translation_output_max=5.0,
            ),
        ],
    )
    builder.instrument.add_control(release_ctrl)

    return builder
