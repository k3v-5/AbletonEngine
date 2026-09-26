# engine/sound_design/decent_sampler/templates/drum_kit.py
"""
Percussive Acoustic Drum Kit Archetype for Decent Sampler.

Features:
- One-shot playback (ampEnvEnabled=False)
- Round-robin sequencing on snare hits to prevent machine-gunning
- Hi-hat choke grouping via silencedByTags (closed hat silences ringing open hat)
- Master bus dynamics compressor and room ambiance
"""

from typing import List, Optional
from ..builder import DecentSamplerBuilder
from ..model import GroupModel, SampleZoneModel


def create_drum_kit(name: str = "Studio Acoustic Drum Kit") -> DecentSamplerBuilder:
    """Creates a production-ready Drum Kit with choke groups and round-robin."""
    builder = DecentSamplerBuilder(name=name)
    builder.set_global_properties(volume=1.0)
    builder.instrument.groups.clear()  # Start fresh with per-drum groups

    # 1. Kick Drum (Note 36 / C1) - One-shot
    kick_group = GroupModel(name="Kick", amp_env_enabled=False)
    kick_group.add_sample(SampleZoneModel(path="Samples/kick.wav", root_note=36, lo_note=36, hi_note=36))
    builder.instrument.add_group(kick_group)

    # 2. Snare Drum (Note 38 / D1) - 3x Round-Robin to prevent machine-gunning
    snare_group = GroupModel(name="Snare", amp_env_enabled=False, seq_mode="round_robin")
    snare_group.add_sample(SampleZoneModel(path="Samples/snare_rr1.wav", root_note=38, lo_note=38, hi_note=38, seq_mode="round_robin", seq_position=1, seq_length=3))
    snare_group.add_sample(SampleZoneModel(path="Samples/snare_rr2.wav", root_note=38, lo_note=38, hi_note=38, seq_mode="round_robin", seq_position=2, seq_length=3))
    snare_group.add_sample(SampleZoneModel(path="Samples/snare_rr3.wav", root_note=38, lo_note=38, hi_note=38, seq_mode="round_robin", seq_position=3, seq_length=3))
    builder.instrument.add_group(snare_group)

    # 3. Closed Hi-Hat (Note 42 / F#1) - Emits tag "hh_closed"
    closed_hh = GroupModel(name="HiHat_Closed", amp_env_enabled=False, tags="hh_closed")
    closed_hh.add_sample(SampleZoneModel(path="Samples/hihat_closed.wav", root_note=42, lo_note=42, hi_note=42, tags="hh_closed"))
    builder.instrument.add_group(closed_hh)

    # 4. Open Hi-Hat (Note 46 / A#1) - Choked when "hh_closed" triggers!
    open_hh = GroupModel(
        name="HiHat_Open",
        amp_env_enabled=False,
        silenced_by_tags="hh_closed",
        silencing_mode="fast",
        silencing_decay=0.03,  # 30ms tight choke fade
    )
    open_hh.add_sample(SampleZoneModel(path="Samples/hihat_open.wav", root_note=46, lo_note=46, hi_note=46))
    builder.instrument.add_group(open_hh)

    # Global Processing: Punchy compressor + room ambiance
    builder.add_effect("compressor", threshold=-16.0, ratio=4.0, attack=15.0, release=80.0, inputGain=0.0, outputGain=2.0)
    builder.add_effect("reverb", roomSize=0.35, damping=0.5, wetLevel=0.15)

    # Macro Knobs
    builder.add_macro_knob(
        label="Room Space",
        parameter="FX_REVERB_WET_LEVEL",
        target_index=1,
        min_value=0.0,
        max_value=1.0,
        default_value=0.15,
        value_type="percent",
    )
    builder.add_macro_knob(
        label="Comp Ratio",
        parameter="FX_RATIO",
        target_index=0,
        min_value=1.0,
        max_value=12.0,
        default_value=4.0,
        value_type="linear",
    )

    return builder
