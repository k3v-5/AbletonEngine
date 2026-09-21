# tests/test_sample_genesis_pipelines.py
"""
Tests for the 4 Canonical Sample Genesis Pipelines:
- Génesis A: Resample melódico
- Génesis B: Freeze / Ambient Pad
- Génesis C: Micro-sample
- Génesis D: Audio -> MIDI -> Audio (Ciclo Evolutivo Recurrente)
Also tests the 'Render Before Sample' engine.
"""

import os
import pytest
from pathlib import Path

from engine.audio_genesis.provenance import (
    AudioProvenanceEngine,
    SampleProvenanceRecord,
    SampleOrigin,
    AudioSourceLocation,
    InstrumentProvenance,
    CreativeGovernanceError,
)
from engine.audio_genesis.render_engine import (
    RenderToAudioEngine,
    RenderRequest,
)
from engine.audio_genesis.mutation_engine import (
    SampleMutationEngine,
    GenesisPipelineType,
)
from engine.composition.compositional_dna import CompositionalDNA, PrimaryMotif, MotifNote


@pytest.fixture
def prov_engine():
    return AudioProvenanceEngine()


@pytest.fixture
def render_engine(prov_engine, tmp_path):
    return RenderToAudioEngine(provenance_engine=prov_engine, cache_dir=tmp_path / "renders")


@pytest.fixture
def mutation_engine(prov_engine, tmp_path):
    return SampleMutationEngine(provenance_engine=prov_engine, output_dir=tmp_path / "mutations")


@pytest.fixture
def root_provenance(render_engine):
    dna = CompositionalDNA(
        song_id="kendrick_soul",
        bpm=110.0,
        primary_motif=PrimaryMotif(
            name="Alright Hook Motif",
            notes=[
                MotifNote(pitch=63, start_time=0.0, duration=0.5),
                MotifNote(pitch=66, start_time=0.5, duration=0.5),
                MotifNote(pitch=70, start_time=1.0, duration=1.0),
            ]
        )
    )
    req = RenderRequest(
        track_name="Emotional Piano",
        clip_name="Hook 1",
        bars=(20, 24),
        instrument_name="Analog Lab V",
        preset_name="Stage-73 Warm",
        device_category="keys",
        bpm=110.0,
        song_dna=dna
    )
    res = render_engine.render_material(req)
    return res.provenance_record


def test_render_before_sample_creates_original_generated_record(render_engine):
    dna = CompositionalDNA(song_id="song_test", bpm=120.0)
    req = RenderRequest(
        track_name="Rhodes Keys",
        bars=(1, 4),
        instrument_name="Stage-73 V2",
        device_category="keys",
        song_dna=dna
    )
    result = render_engine.render_material(req)

    assert result.provenance_record.origin == SampleOrigin.ORIGINAL_GENERATED
    assert result.provenance_record.generation_depth == 0
    assert result.provenance_record.source.track == "Rhodes Keys"
    assert Path(result.audio_path).exists()
    assert result.metadata.duration_sec > 0
    assert result.metadata.sample_rate == 44100


def test_genesis_a_melodic_resample(mutation_engine, root_provenance):
    res = mutation_engine.execute_genesis(
        source_record=root_provenance,
        pipeline_type=GenesisPipelineType.MELODIC_RESAMPLE,
        target_destination="Simpler",
        custom_params={"pitch_shift": -7, "drive_db": 5.0}
    )

    assert res.pipeline_type == GenesisPipelineType.MELODIC_RESAMPLE
    assert res.provenance_record.origin == SampleOrigin.DERIVED_FROM_SONG
    assert res.provenance_record.parent_sample_id == root_provenance.sample_id
    assert res.provenance_record.generation_depth == 1
    assert Path(res.audio_path).exists()
    proc_names = [p.name for p in res.provenance_record.processing]
    assert "pitch_shift" in proc_names
    assert "analog_saturation" in proc_names


def test_genesis_b_freeze_pad(mutation_engine, root_provenance):
    res = mutation_engine.execute_genesis(
        source_record=root_provenance,
        pipeline_type=GenesisPipelineType.FREEZE_PAD,
        target_destination="AudioClip",
        custom_params={"stretch_factor": 4.0, "hpf_hz": 300.0}
    )

    assert res.pipeline_type == GenesisPipelineType.FREEZE_PAD
    assert res.provenance_record.origin == SampleOrigin.DERIVED_FROM_SONG
    assert Path(res.audio_path).exists()
    proc_names = [p.name for p in res.provenance_record.processing]
    assert "granular_freeze" in proc_names
    assert "time_stretch" in proc_names


def test_genesis_c_micro_sample(mutation_engine, root_provenance):
    res = mutation_engine.execute_genesis(
        source_record=root_provenance,
        pipeline_type=GenesisPipelineType.MICRO_SAMPLE,
        target_destination="TransientLayer",
        custom_params={"window_ms": 150.0, "root_tune_midi": 63}
    )

    assert res.pipeline_type == GenesisPipelineType.MICRO_SAMPLE
    assert res.provenance_record.origin == SampleOrigin.DERIVED_FROM_SONG
    assert Path(res.audio_path).exists()
    proc_names = [p.name for p in res.provenance_record.processing]
    assert "micro_window_isolate" in proc_names
    assert "fast_adsr_envelope" in proc_names


def test_genesis_d_audio_to_midi_cycle(mutation_engine, root_provenance):
    res = mutation_engine.execute_genesis(
        source_record=root_provenance,
        pipeline_type=GenesisPipelineType.AUDIO_TO_MIDI_CYCLE,
        target_destination="Simpler",
        custom_params={"new_synth": "SubLab XL", "freq_shift_hz": 80.0}
    )

    assert res.pipeline_type == GenesisPipelineType.AUDIO_TO_MIDI_CYCLE
    assert res.provenance_record.origin == SampleOrigin.DERIVED_FROM_SONG
    assert res.derived_midi_notes is not None
    assert len(res.derived_midi_notes) > 0
    assert res.provenance_record.instrument.device == "SubLab XL"
    assert Path(res.audio_path).exists()


def test_mutation_engine_rejects_unprovenanced_source(mutation_engine):
    untracked_record = SampleProvenanceRecord(
        sample_id="pirated_sample_01",
        origin=SampleOrigin.UNKNOWN,
        source=AudioSourceLocation(track="External Unknown"),
        instrument=InstrumentProvenance()
    )

    with pytest.raises(CreativeGovernanceError):
        mutation_engine.execute_genesis(
            source_record=untracked_record,
            pipeline_type=GenesisPipelineType.MELODIC_RESAMPLE
        )
