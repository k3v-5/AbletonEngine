# engine/sound_design/decent_sampler/templates/designed_808.py
"""
Sample-Based Designed 808 Sub Bass Archetype for Decent Sampler.

Features:
- Full-keyboard pitch tracking (pitchKeyTrack=1.0)
- Legato pitch gliding for pitch slides
- Wave folding & saturation for audible punch on small speakers
- Macro controls: Glide, Drive, Cutoff, Sub Release
"""

from ..builder import DecentSamplerBuilder
from ..policies import AudioSafetyPolicy


def create_808_sub_bass(
    name: str = "Tuned Studio 808",
    sample_path: str = "Samples/808_sub_c1.wav",
    root_note: int = 24,  # C1
) -> DecentSamplerBuilder:
    """Creates a production-ready tuned 808 Sub Bass instrument."""
    builder = DecentSamplerBuilder(name=name)
    builder.set_global_properties(
        volume=1.0,
        glide_time=0.08,
        glide_mode="legato",
    )

    # 808 Sample covering full bass range (C0 to C3 / notes 12 to 48)
    builder.add_sample(
        path=sample_path,
        root_note=root_note,
        lo_note=12,
        hi_note=60,
        group_index=0,
    )

    # 808 Envelope: instant transient punch, sustained body, controlled tail
    builder.set_envelope(
        attack=AudioSafetyPolicy.RECOMMENDED_MIN_ATTACK_SEC,
        decay=2.5,
        sustain=0.6,
        release=0.4,
        group_index=0,
    )

    # Effects: Group-level wave folder for aggressive distortion, global LP filter
    builder.add_effect("wave_folder", drive=1.5, threshold=0.8, level="group", group_index=0)
    builder.add_effect("lowpass", frequency=450.0, resonance=0.8, level="instrument")

    # Macro UI controls
    builder.add_macro_knob(
        label="Drive",
        parameter="FX_DRIVE",
        level="group",
        target_index=0,
        min_value=1.0,
        max_value=25.0,
        default_value=1.5,
        value_type="linear",
    )
    builder.add_macro_knob(
        label="Cutoff",
        parameter="FX_FILTER_FREQUENCY",
        level="instrument",
        target_index=0,
        min_value=60.0,
        max_value=2500.0,
        default_value=450.0,
        value_type="hertz",
    )
    builder.add_macro_knob(
        label="Glide",
        parameter="GLIDE_TIME",
        level="instrument",
        target_index=0,
        min_value=0.0,
        max_value=0.5,
        default_value=0.08,
        value_type="linear",
    )
    builder.add_macro_knob(
        label="Release",
        parameter="ENV_RELEASE",
        level="group",
        target_index=0,
        min_value=0.05,
        max_value=3.0,
        default_value=0.4,
        value_type="linear",
    )

    return builder
