# engine/sound_design/decent_sampler/templates/orchestral_strings.py
"""
Orchestral Strings Archetype for Decent Sampler.

Features:
- Expressive bow attack and natural sustained decay
- Chorus ensemble widening and hall reverberation
- Macro knobs: Expression (Filter), Ensemble (Chorus), Reverb, Attack, Release
"""

from typing import List, Optional
from ..builder import DecentSamplerBuilder
from ..sample_analyzer import SampleAsset


def create_orchestral_strings(
    name: str = "Symphonic String Ensemble",
    assets: Optional[List[SampleAsset]] = None,
) -> DecentSamplerBuilder:
    """Creates an expressive Orchestral Strings instrument."""
    builder = DecentSamplerBuilder(name=name)
    builder.set_global_properties(volume=1.0, global_pan=0.0)

    if assets:
        builder.map_sample_assets(assets, min_note=36, max_note=96)
    else:
        builder.add_sample("Samples/strings_c2.wav", root_note=36, lo_note=36, hi_note=47)
        builder.add_sample("Samples/strings_c3.wav", root_note=48, lo_note=48, hi_note=59)
        builder.add_sample("Samples/strings_c4.wav", root_note=60, lo_note=60, hi_note=71)
        builder.add_sample("Samples/strings_c5.wav", root_note=72, lo_note=72, hi_note=83)
        builder.add_sample("Samples/strings_c6.wav", root_note=84, lo_note=84, hi_note=96)

    # Expressive bowed strings envelope: smooth swelling attack, full sustain, long tail
    builder.set_envelope(
        attack=0.25,
        decay=2.0,
        sustain=1.0,
        release=1.2,
        group_index=0,
    )

    # Global Effects Chain
    builder.add_effect("lowpass", frequency=18000.0, resonance=0.5, tags="expression_filter")
    builder.add_effect("chorus", mix=0.25, modDepth=0.2, modRate=0.3, tags="ensemble_chorus")
    builder.add_effect("reverb", roomSize=0.8, damping=0.3, wetLevel=0.35, tags="orchestral_hall")

    # Macro UI Controls
    builder.add_macro_knob(
        label="Expression",
        parameter="FX_FILTER_FREQUENCY",
        target_index=0,
        min_value=500.0,
        max_value=20000.0,
        default_value=18000.0,
        value_type="hertz",
    )
    builder.add_macro_knob(
        label="Ensemble",
        parameter="FX_CHORUS_MIX",
        target_index=1,
        min_value=0.0,
        max_value=1.0,
        default_value=0.25,
        value_type="percent",
    )
    builder.add_macro_knob(
        label="Reverb",
        parameter="FX_REVERB_WET_LEVEL",
        target_index=2,
        min_value=0.0,
        max_value=1.0,
        default_value=0.35,
        value_type="percent",
    )
    builder.add_macro_knob(
        label="Attack",
        parameter="ENV_ATTACK",
        target_index=0,
        min_value=0.01,
        max_value=2.0,
        default_value=0.25,
        value_type="linear",
    )

    return builder
