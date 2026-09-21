# tests/test_audio_genesis_engine_integration.py
"""
Integration tests for AudioGenesisEngine and its connections to:
- CompositionalDNA
- SonicMutationLab
- CatalogMemory
- SimplerSlicer
"""

import pytest
from pathlib import Path

from engine.audio_genesis.audio_genesis_engine import AudioGenesisEngine, GenesisSoundResult
from engine.audio_genesis.provenance import (
    AudioProvenanceEngine,
    SampleOrigin,
    SampleProvenanceRecord,
    CreativeGovernanceError,
)
from engine.audio_genesis.instrument_builder import TargetInstrumentDestination
from engine.audio_genesis.mutation_engine import GenesisPipelineType
from engine.composition.compositional_dna import CompositionalDNA, PrimaryMotif, MotifNote
from engine.sound_design.sonic_mutation_lab import SonicMutationLab
from engine.memory.catalog_memory import CatalogMemory
from engine.instruments.simpler_slicer import SimplerSlicer


@pytest.fixture
def genesis_engine(tmp_path):
    prov = AudioProvenanceEngine()
    return AudioGenesisEngine(provenance_engine=prov)


@pytest.fixture
def sample_dna():
    return CompositionalDNA(
        song_id="alright_closed_ecosystem",
        title="Alright Kendrick Style",
        bpm=110.0,
        primary_motif=PrimaryMotif(
            name="Alright Main Hook",
            notes=[
                MotifNote(pitch=63, start_time=0.0, duration=0.5, velocity=95),
                MotifNote(pitch=66, start_time=0.75, duration=0.5, velocity=90),
                MotifNote(pitch=70, start_time=1.5, duration=1.0, velocity=100),
            ]
        )
    )


def test_full_genesis_flow_render_before_sample_to_simpler(genesis_engine, sample_dna):
    res = genesis_engine.create_provenanced_sound(
        song_dna=sample_dna,
        musical_need="melodic_lead_texture",
        target_destination=TargetInstrumentDestination.SIMPLER_MELODIC
    )

    assert isinstance(res, GenesisSoundResult)
    # Check Root Render
    assert res.root_render.provenance_record.origin == SampleOrigin.ORIGINAL_GENERATED
    assert res.root_render.provenance_record.generation_depth == 0
    # Check Mutation (Genesis A)
    assert res.mutation.pipeline_type == GenesisPipelineType.MELODIC_RESAMPLE
    assert res.mutation.provenance_record.origin == SampleOrigin.DERIVED_FROM_SONG
    assert res.mutation.provenance_record.generation_depth == 1
    # Check Instrument Builder
    assert res.instrument.plan.destination == TargetInstrumentDestination.SIMPLER_MELODIC
    # Check DNA update
    assert len(sample_dna.provenance_records) >= 1
    assert sample_dna.provenance_records[-1]["sample_id"] == res.mutation.mutated_sample_id
    # Check Genealogy ASCII
    assert "ORIGINAL SONG GENESIS" in res.genealogy_ascii
    assert res.mutation.mutated_sample_id in res.genealogy_ascii


def test_full_genesis_flow_ambient_pad_to_audio_clip(genesis_engine, sample_dna):
    res = genesis_engine.create_provenanced_sound(
        song_dna=sample_dna,
        musical_need="ambient_pad_drone",
        target_destination=TargetInstrumentDestination.AUDIO_CLIP
    )

    assert res.mutation.pipeline_type == GenesisPipelineType.FREEZE_PAD
    assert res.instrument.plan.destination == TargetInstrumentDestination.AUDIO_CLIP
    assert res.instrument.plan.parameters["warp_mode"] == "Complex Pro"


def test_full_genesis_flow_micro_sample_to_transient_layer(genesis_engine, sample_dna):
    res = genesis_engine.create_provenanced_sound(
        song_dna=sample_dna,
        musical_need="percussive_pluck_transient",
        target_destination=TargetInstrumentDestination.TRANSIENT_LAYER
    )

    assert res.mutation.pipeline_type == GenesisPipelineType.MICRO_SAMPLE
    assert res.instrument.plan.destination == TargetInstrumentDestination.TRANSIENT_LAYER
    assert res.instrument.plan.parameters["high_pass_hz"] == 1200.0


def test_full_genesis_flow_audio_to_midi_cycle(genesis_engine, sample_dna):
    res = genesis_engine.create_provenanced_sound(
        song_dna=sample_dna,
        musical_need="evolutionary_cycle_hybrid",
        genesis_pipeline=GenesisPipelineType.AUDIO_TO_MIDI_CYCLE,
        target_destination=TargetInstrumentDestination.SIMPLER_MELODIC
    )

    assert res.mutation.pipeline_type == GenesisPipelineType.AUDIO_TO_MIDI_CYCLE
    assert res.mutation.derived_midi_notes is not None
    assert len(res.mutation.derived_midi_notes) > 0


def test_integration_with_sonic_mutation_lab():
    candidates = SonicMutationLab.run_experiment(
        source_track_index=4,
        source_track_name="Emotional Piano",
        source_section="Hook 1",
        target_section="Verse 2"
    )
    assert len(candidates) > 0
    # Every candidate has a verifiable provenance record
    for cand in candidates:
        assert cand.provenance_record is not None
        assert cand.provenance_record.origin == SampleOrigin.DERIVED_FROM_SONG
        assert cand.provenance_record.source.track == "Emotional Piano"
        d = cand.to_dict()
        assert d["provenance_record"] is not None
        assert d["provenance_record"]["is_autogenous"] is True


def test_integration_with_catalog_memory_audit(sample_dna, genesis_engine):
    # Produce two sounds
    res1 = genesis_engine.create_provenanced_sound(song_dna=sample_dna, musical_need="lead_texture")
    res2 = genesis_engine.create_provenanced_sound(song_dna=sample_dna, musical_need="ambient_pad")

    catalog = CatalogMemory()
    audit = catalog.audit_audio_provenance(
        song_id=sample_dna.song_id,
        provenance_records=sample_dna.provenance_records
    )

    assert audit["compliant"] is True
    assert audit["unprovenanced_count"] == 0
    assert audit["autogenous_ratio"] == 1.0
    assert audit["is_closed_ecosystem"] is True

    # Injecting unprovenanced audio causes a violation
    bad_records = list(sample_dna.provenance_records) + [{"sample_id": "untracked", "origin": "unknown"}]
    bad_audit = catalog.audit_audio_provenance(song_id="bad_song", provenance_records=bad_records)
    assert bad_audit["compliant"] is False
    assert bad_audit["unprovenanced_count"] == 1
    assert bad_audit["is_closed_ecosystem"] is False


def test_integration_with_simpler_slicer_governance(genesis_engine, sample_dna):
    sound = genesis_engine.create_provenanced_sound(song_dna=sample_dna, musical_need="sliced_chops")

    # Valid provenanced loading into Simpler
    slice_res = SimplerSlicer.load_provenanced_sample_and_slice(
        conn=None,
        track_index=5,
        sample_provenance=sound.provenance
    )
    assert slice_res["status"] == "SUCCESS"
    assert slice_res["provenance_id"] == sound.provenance.sample_id
    assert slice_res["origin"] == "derived_from_song"

    # Loading unprovenanced sample raises CreativeGovernanceError
    unprovenanced_dummy = {"origin": "unknown", "sample_id": "pirate_01"}
    with pytest.raises(CreativeGovernanceError):
        SimplerSlicer.load_provenanced_sample_and_slice(
            conn=None,
            track_index=5,
            sample_provenance=unprovenanced_dummy,
            allow_external_samples=False
        )

    # Allowed when explicitly overridden by user
    override_res = SimplerSlicer.load_provenanced_sample_and_slice(
        conn=None,
        track_index=5,
        sample_provenance=unprovenanced_dummy,
        allow_external_samples=True
    )
    assert override_res["origin"] == "unknown"
