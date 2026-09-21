# tests/test_audio_provenance.py
"""
Tests for Audio Provenance Engine:
Validates Rule 1 (Source Policy), UNKNOWN veto, CreativeGovernanceError,
SampleProvenanceRecord serialization, and AudioGenealogyTree tracking.
"""

import pytest
from engine.audio_genesis.provenance import (
    SampleOrigin,
    CreativeUsagePolicy,
    CreativeGovernanceError,
    AudioSourceLocation,
    InstrumentProvenance,
    ProcessingStep,
    RenderMetadata,
    SampleProvenanceRecord,
    AudioGenealogyTree,
    AudioProvenanceEngine,
)


def test_sample_origin_enum_values():
    assert SampleOrigin.ORIGINAL_GENERATED == "original_generated"
    assert SampleOrigin.DERIVED_FROM_SONG == "derived_from_song"
    assert SampleOrigin.USER_IMPORTED == "user_imported"
    assert SampleOrigin.CATALOG_SAMPLE == "catalog_sample"
    assert SampleOrigin.UNKNOWN == "unknown"


def test_creative_usage_policy_unknown_forbidden():
    rec_unknown = SampleProvenanceRecord(
        sample_id="samp_unknown_01",
        origin=SampleOrigin.UNKNOWN,
        source=AudioSourceLocation(track="Random Audio"),
        instrument=InstrumentProvenance()
    )
    assert rec_unknown.creative_usage == CreativeUsagePolicy.FORBIDDEN
    assert not rec_unknown.is_autogenous

    rec_gen = SampleProvenanceRecord(
        sample_id="samp_gen_01",
        origin=SampleOrigin.ORIGINAL_GENERATED,
        source=AudioSourceLocation(track="Emotional Piano"),
        instrument=InstrumentProvenance(device="Analog Lab V")
    )
    assert rec_gen.creative_usage == CreativeUsagePolicy.ALLOWED
    assert rec_gen.is_autogenous


def test_creative_governance_error_raised_on_unknown():
    engine = AudioProvenanceEngine()
    rec_unknown = SampleProvenanceRecord(
        sample_id="samp_untracked_99",
        origin=SampleOrigin.UNKNOWN,
        source=AudioSourceLocation(track="Track 7"),
        instrument=InstrumentProvenance()
    )

    with pytest.raises(CreativeGovernanceError) as excinfo:
        engine.validate_creative_usage(rec_unknown, allow_external_override=False)

    assert "Cannot use unprovenanced audio" in str(excinfo.value)
    assert "samp_untracked_99" in str(excinfo.value)


def test_creative_governance_override_allowed_when_explicit():
    engine = AudioProvenanceEngine()
    rec_unknown = SampleProvenanceRecord(
        sample_id="samp_user_sample_01",
        origin=SampleOrigin.UNKNOWN,
        source=AudioSourceLocation(track="External Foley"),
        instrument=InstrumentProvenance()
    )
    # With explicit override, it does not raise
    assert engine.validate_creative_usage(rec_unknown, allow_external_override=True) is True


def test_sample_provenance_record_serialization_roundtrip():
    rec = SampleProvenanceRecord(
        sample_id="genesis_0042",
        origin=SampleOrigin.ORIGINAL_GENERATED,
        source=AudioSourceLocation(
            source_type="generated_render",
            track="Emotional Piano",
            clip="Hook 1",
            bars=(20, 24),
            midi_source=True,
            midi_notes_hash="abcdef123456"
        ),
        instrument=InstrumentProvenance(
            device="Analog Lab V",
            preset="Vintage Rhodes 73",
            device_category="keys"
        ),
        processing=[
            ProcessingStep("saturator", {"drive_db": 4.5}),
            ProcessingStep("reverse", {}),
            ProcessingStep("stretch", {"factor": 1.37}),
            ProcessingStep("pitch_shift", {"semitones": -7}),
        ],
        render=RenderMetadata(
            format="wav",
            duration_sec=2.31,
            sample_rate=44100,
            channels=2,
            peak_dbfs=-4.2,
            rms_dbfs=-16.8,
            file_path="/cache/renders/genesis_0042.wav",
            content_hash="9f8e7d6c5b4a"
        ),
        destination="Simpler",
        parent_sample_id=None,
        generation_depth=0,
        song_id="Alright_Kendrick_Style"
    )

    d = rec.to_dict()
    assert d["sample_id"] == "genesis_0042"
    assert d["origin"] == "original_generated"
    assert d["creative_usage"] == "allowed"
    assert d["source"]["track"] == "Emotional Piano"
    assert d["source"]["bars"] == [20, 24]
    assert len(d["processing"]) == 4
    assert d["render"]["duration_sec"] == 2.31

    restored = SampleProvenanceRecord.from_dict(d)
    assert restored.sample_id == rec.sample_id
    assert restored.origin == rec.origin
    assert restored.source.track == "Emotional Piano"
    assert restored.instrument.device == "Analog Lab V"
    assert len(restored.processing) == 4
    assert restored.processing[2].name == "stretch"
    assert restored.render.duration_sec == 2.31


def test_audio_genealogy_tree_multi_generation_trace():
    tree = AudioGenealogyTree()

    # Generation 0: Root Render
    root = SampleProvenanceRecord(
        sample_id="root_piano_01",
        origin=SampleOrigin.ORIGINAL_GENERATED,
        source=AudioSourceLocation(track="Piano"),
        instrument=InstrumentProvenance(device="Stage-73 V2"),
        generation_depth=0
    )
    tree.add_record(root)

    # Generation 1: Resampled mutation
    gen1 = SampleProvenanceRecord(
        sample_id="mut_piano_reverse_02",
        origin=SampleOrigin.DERIVED_FROM_SONG,
        source=AudioSourceLocation(track="Piano"),
        instrument=InstrumentProvenance(device="Stage-73 V2"),
        parent_sample_id="root_piano_01",
        generation_depth=1,
        processing=[ProcessingStep("reverse", {}), ProcessingStep("pitch_shift", {"semitones": -7})]
    )
    tree.add_record(gen1)

    # Generation 2: Granular stretch of gen 1
    gen2 = SampleProvenanceRecord(
        sample_id="mut_piano_pad_03",
        origin=SampleOrigin.DERIVED_FROM_SONG,
        source=AudioSourceLocation(track="Piano"),
        instrument=InstrumentProvenance(device="Stage-73 V2"),
        parent_sample_id="mut_piano_reverse_02",
        generation_depth=2,
        processing=[ProcessingStep("granular_stretch", {"factor": 4.0})]
    )
    tree.add_record(gen2)

    lineage = tree.get_lineage("mut_piano_pad_03")
    assert len(lineage) == 3
    assert lineage[0].sample_id == "root_piano_01"
    assert lineage[1].sample_id == "mut_piano_reverse_02"
    assert lineage[2].sample_id == "mut_piano_pad_03"


def test_audio_genealogy_tree_ascii_rendering():
    engine = AudioProvenanceEngine()

    root = SampleProvenanceRecord(
        sample_id="root_rhodes",
        origin=SampleOrigin.ORIGINAL_GENERATED,
        source=AudioSourceLocation(track="Rhodes Keys"),
        instrument=InstrumentProvenance(device="Stage-73"),
        destination="RenderBuffer",
        generation_depth=0
    )
    engine.register_sample(root)

    child_a = SampleProvenanceRecord(
        sample_id="sample_a_chop",
        origin=SampleOrigin.DERIVED_FROM_SONG,
        source=AudioSourceLocation(track="Rhodes Keys"),
        instrument=InstrumentProvenance(device="Stage-73"),
        parent_sample_id="root_rhodes",
        destination="Simpler",
        generation_depth=1,
        processing=[ProcessingStep("slice", {}), ProcessingStep("reverse", {})]
    )
    engine.register_sample(child_a)

    ascii_rep = engine.get_genealogy_tree().render_ascii_tree()
    assert "ORIGINAL SONG GENESIS" in ascii_rep
    assert "root_rhodes" in ascii_rep
    assert "sample_a_chop" in ascii_rep
    assert "Simpler" in ascii_rep


def test_provenance_engine_session_audit():
    engine = AudioProvenanceEngine()

    s1 = SampleProvenanceRecord("s1", SampleOrigin.ORIGINAL_GENERATED, AudioSourceLocation(), InstrumentProvenance())
    s2 = SampleProvenanceRecord("s2", SampleOrigin.DERIVED_FROM_SONG, AudioSourceLocation(), InstrumentProvenance())
    s3 = SampleProvenanceRecord("s3", SampleOrigin.USER_IMPORTED, AudioSourceLocation(), InstrumentProvenance())
    s4 = SampleProvenanceRecord("s4", SampleOrigin.UNKNOWN, AudioSourceLocation(), InstrumentProvenance())

    audit = engine.audit_session_samples([s1, s2, s3, s4])
    assert audit["total_samples"] == 4
    assert audit["compliant_count"] == 3
    assert audit["unprovenanced_violations"] == ["s4"]
    assert audit["is_fully_compliant"] is False
    assert audit["autogenous_ratio"] == 0.5
