# tests/test_sample_instrument_builder.py
"""
Tests for Sample Instrument Builder:
Validates purpose-driven instrument routing, decoupling creative audio from Simpler,
and enforcing governance checks.
"""

import pytest
from engine.audio_genesis.provenance import (
    AudioProvenanceEngine,
    SampleProvenanceRecord,
    SampleOrigin,
    AudioSourceLocation,
    InstrumentProvenance,
    RenderMetadata,
    CreativeGovernanceError,
)
from engine.audio_genesis.instrument_builder import (
    SampleInstrumentBuilder,
    TargetInstrumentDestination,
)


@pytest.fixture
def builder():
    return SampleInstrumentBuilder()


@pytest.fixture
def valid_record():
    return SampleProvenanceRecord(
        sample_id="test_genesis_sample",
        origin=SampleOrigin.DERIVED_FROM_SONG,
        source=AudioSourceLocation(track="Rhodes"),
        instrument=InstrumentProvenance(device="Stage-73 V2"),
        render=RenderMetadata(duration_sec=2.5, file_path="/cache/renders/test.wav")
    )


def test_determine_best_destination_heuristics(builder):
    assert builder.determine_best_destination("lead_melody", 2.0) == TargetInstrumentDestination.SIMPLER_MELODIC
    assert builder.determine_best_destination("bass_synth", 1.5) == TargetInstrumentDestination.SIMPLER_MELODIC
    assert builder.determine_best_destination("vocal_chops", 3.0) == TargetInstrumentDestination.SIMPLER_SLICED
    assert builder.determine_best_destination("vinyl_foley_bed", 8.0) == TargetInstrumentDestination.AUDIO_CLIP
    assert builder.determine_best_destination("ambient_granular_cloud", 5.0) == TargetInstrumentDestination.GRANULAR_STRETCH
    assert builder.determine_best_destination("snare_transient_punch", 0.3) == TargetInstrumentDestination.TRANSIENT_LAYER
    assert builder.determine_best_destination("reverb_atmosphere_space", 6.0) == TargetInstrumentDestination.ATMOSPHERE_BED
    assert builder.determine_best_destination("acoustic_kick_drum", 0.5) == TargetInstrumentDestination.DRUM_RACK_PAD


def test_build_simpler_melodic_plan(builder, valid_record):
    res = builder.build_instrument(
        sample_record=valid_record,
        destination=TargetInstrumentDestination.SIMPLER_MELODIC,
        custom_params={"root_key": 63, "filter_cutoff_hz": 5000.0}
    )
    assert res.status == "SUCCESS"
    assert res.plan.destination == TargetInstrumentDestination.SIMPLER_MELODIC
    assert "Simpler (Classic)" in res.plan.device_chain[0]
    assert res.plan.parameters["playback_mode"] == 0
    assert res.plan.parameters["root_key"] == 63


def test_build_simpler_sliced_plan(builder, valid_record):
    res = builder.build_instrument(
        sample_record=valid_record,
        destination=TargetInstrumentDestination.SIMPLER_SLICED,
        custom_params={"sensitivity": 90.0}
    )
    assert res.status == "SUCCESS"
    assert res.plan.parameters["playback_mode"] == 2
    assert res.plan.parameters["sensitivity"] == 90.0


def test_build_audio_clip_timeline_plan(builder, valid_record):
    res = builder.build_instrument(
        sample_record=valid_record,
        destination=TargetInstrumentDestination.AUDIO_CLIP,
        custom_params={"gain_trim_db": -16.0, "start_beat": 16.0}
    )
    assert res.status == "SUCCESS"
    assert res.plan.routing_instructions["staging"] == "arrangement_clip"
    assert res.plan.parameters["gain_trim_db"] == -16.0
    assert res.plan.parameters["start_beat"] == 16.0


def test_build_granular_stretch_plan(builder, valid_record):
    res = builder.build_instrument(
        sample_record=valid_record,
        destination=TargetInstrumentDestination.GRANULAR_STRETCH,
        custom_params={"spray_ms": 60.0}
    )
    assert res.status == "SUCCESS"
    assert "Grain Delay" in res.plan.device_chain


def test_build_transient_layer_plan(builder, valid_record):
    res = builder.build_instrument(
        sample_record=valid_record,
        destination=TargetInstrumentDestination.TRANSIENT_LAYER,
        custom_params={"transient_gain_db": 3.0}
    )
    assert res.status == "SUCCESS"
    assert res.plan.routing_instructions["type"] == "parallel_layer"
    assert res.plan.parameters["playback_mode"] == 1  # 1-Shot


def test_build_atmosphere_bed_plan(builder, valid_record):
    res = builder.build_instrument(
        sample_record=valid_record,
        destination=TargetInstrumentDestination.ATMOSPHERE_BED
    )
    assert res.status == "SUCCESS"
    assert res.plan.parameters["diffuse_mix"] == 1.0
    assert res.plan.parameters["decay_time_sec"] == 12.0


def test_build_drum_rack_pad_plan(builder, valid_record):
    res = builder.build_instrument(
        sample_record=valid_record,
        destination=TargetInstrumentDestination.DRUM_RACK_PAD,
        custom_params={"pad_note": 36}  # Kick C1
    )
    assert res.status == "SUCCESS"
    assert res.assigned_pad_note == 36
    assert res.plan.destination == TargetInstrumentDestination.DRUM_RACK_PAD


def test_builder_rejects_unprovenanced_sample(builder):
    bad_record = SampleProvenanceRecord(
        sample_id="illegal_sample",
        origin=SampleOrigin.UNKNOWN,
        source=AudioSourceLocation(track="Unknown Source"),
        instrument=InstrumentProvenance()
    )
    with pytest.raises(CreativeGovernanceError):
        builder.build_instrument(sample_record=bad_record)
