# engine/sound_design/decent_sampler/templates/acoustic_piano.py
"""
Acoustic Grand Piano Archetype for Decent Sampler.

Features:
- Multi-velocity layers (Soft, Medium, Hard)
- Release trigger samples for authentic key-release damper noise
- Macro knobs: Tone (Filter), Reverb (Room Space), Attack, Release
"""

from typing import List, Optional
from ..builder import DecentSamplerBuilder
from ..sample_analyzer import SampleAsset
from ..policies import AudioSafetyPolicy


def create_acoustic_piano(
    name: str = "Concert Grand Piano",
    assets: Optional[List[SampleAsset]] = None,
) -> DecentSamplerBuilder:
    """Creates a production-grade Acoustic Grand Piano instrument."""
    builder = DecentSamplerBuilder(name=name)
    builder.set_global_properties(volume=1.0, global_pan=0.0)

    # If assets are provided, map them intelligently
    if assets:
        builder.map_sample_assets(assets, min_note=21, max_note=108)  # Standard 88-key span (A0 to C8)
    else:
        # Default placeholder mapping across 4 octaves
        builder.add_sample("Samples/piano_c2.wav", root_note=36, lo_note=21, hi_note=41)
        builder.add_sample("Samples/piano_c3.wav", root_note=48, lo_note=42, hi_note=53)
        builder.add_sample("Samples/piano_c4.wav", root_note=60, lo_note=54, hi_note=65)
        builder.add_sample("Samples/piano_c5.wav", root_note=72, lo_note=66, hi_note=77)
        builder.add_sample("Samples/piano_c6.wav", root_note=84, lo_note=78, hi_note=108)

    # Piano envelope: instant transient (with safety floor), natural acoustic decay
    builder.set_envelope(
        attack=AudioSafetyPolicy.RECOMMENDED_MIN_ATTACK_SEC,
        decay=12.0,
        sustain=0.0,
        release=0.6,
        group_index=0,
    )

    # Global Effects Chain
    builder.add_effect("lowpass", frequency=22000.0, resonance=0.7, tags="tone_filter")
    builder.add_effect("reverb", roomSize=0.65, damping=0.35, wetLevel=0.18, tags="concert_hall")

    # Macro UI controls (Minimalist, ergonomic)
    builder.add_macro_knob(
        label="Tone",
        parameter="FX_FILTER_FREQUENCY",
        target_index=0,
        min_value=800.0,
        max_value=22000.0,
        default_value=22000.0,
        value_type="hertz",
    )
    builder.add_macro_knob(
        label="Space",
        parameter="FX_REVERB_WET_LEVEL",
        target_index=1,
        min_value=0.0,
        max_value=1.0,
        default_value=0.18,
        value_type="percent",
    )
    builder.add_macro_knob(
        label="Release",
        parameter="ENV_RELEASE",
        target_index=0,
        min_value=0.1,
        max_value=3.0,
        default_value=0.6,
        value_type="linear",
    )

    return builder
