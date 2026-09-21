# tests/test_self_sampling_engine.py
"""
Integration tests for Self-Sampling Engine:
- Pre-arrangement emergent sound creation (5 concurrent candidates).
- Ranking via Generative Taste Engine (10 axes).
- Automatic registration into Sonic Family Registry.
- Inter-sectional cross-pollination.
- Governance boundary validation.
"""

import pytest
from pathlib import Path

from engine.audio_genesis.self_sampling_engine import (
    SelfSamplingEngine,
    EmergentProposalBatch,
    EmergentSoundCandidate,
)
from engine.audio_genesis.sonic_recursion import (
    RecursiveTargetRole,
    SonicFamilyRegistry,
)
from engine.audio_genesis.provenance import (
    AudioProvenanceEngine,
    CreativeGovernanceError,
)
from engine.composition.compositional_dna import (
    CompositionalDNA,
    PrimaryMotif,
    MotifNote,
)


@pytest.fixture
def song_dna():
    return CompositionalDNA(
        song_id="self_sampling_song",
        title="Kendrick Closed Loop",
        bpm=110.0,
        primary_motif=PrimaryMotif(
            name="Alright Genetic Hook",
            notes=[
                MotifNote(pitch=63, start_time=0.0, duration=0.5, velocity=95),
                MotifNote(pitch=66, start_time=0.5, duration=0.5, velocity=90),
                MotifNote(pitch=70, start_time=1.0, duration=1.0, velocity=100),
            ]
        )
    )


@pytest.fixture
def engine():
    return SelfSamplingEngine()


def test_propose_emergent_sounds_creates_candidates_before_placement(engine, song_dna):
    batch = engine.propose_emergent_sounds(
        song_dna=song_dna,
        musical_need="dark_floating_texture",
        target_role=RecursiveTargetRole.PAD_TEXTURE,
        candidate_count=5
    )

    assert isinstance(batch, EmergentProposalBatch)
    assert batch.target_role == RecursiveTargetRole.PAD_TEXTURE
    assert len(batch.candidates) == 5

    # Verify each candidate has full dossier
    for cand in batch.candidates:
        assert cand.mutation_result is not None
        assert cand.instrument_result is not None
        assert cand.taste_card is not None
        assert 0.0 <= cand.artistic_score <= 1.0
        assert 0.10 <= cand.perceptual_distance <= 1.0
        assert cand.mutation_result.provenance_record.parent_sample_id is not None


def test_taste_engine_ranks_and_selects_winner(engine, song_dna):
    batch = engine.propose_emergent_sounds(
        song_dna=song_dna,
        musical_need="percussive_transient_punch",
        target_role=RecursiveTargetRole.PERCUSSION,
        candidate_count=5
    )

    assert batch.winner_candidate is not None
    winner = batch.winner_candidate

    # Winner must be among the approved candidates and have top score
    approved = [c for c in batch.candidates if c.is_approved]
    assert winner in approved
    assert winner.artistic_score == max(c.artistic_score for c in approved)
    assert winner.instrument_result.plan.destination.value == "transient_layer"


def test_winner_registered_as_sonic_family(engine, song_dna):
    batch = engine.propose_emergent_sounds(
        song_dna=song_dna,
        musical_need="sub_harmonic_foundation",
        target_role=RecursiveTargetRole.BASS,
        candidate_count=5
    )

    assert batch.registered_family is not None
    fam = batch.registered_family
    assert fam.target_role == RecursiveTargetRole.BASS

    # Check it exists in engine's registry
    reg_fam = engine.family_registry.get_family(fam.family_id)
    assert reg_fam is not None
    assert reg_fam.ancestor_sample_id.startswith("render_")


def test_recursive_cross_pollinate_between_sections(engine, song_dna):
    # Take Verse 1 Rhodes and cross-pollinate into a Bridge Pad
    cand = engine.recursive_cross_pollinate(
        source_track_name="Rhodes Keys",
        source_section="Verse 1",
        target_section="Bridge",
        target_role=RecursiveTargetRole.PAD_TEXTURE,
        song_dna=song_dna
    )

    assert isinstance(cand, EmergentSoundCandidate)
    assert cand.target_role == RecursiveTargetRole.PAD_TEXTURE
    assert cand.seed_track_name == "Rhodes Keys"
    assert cand.mutation_result.provenance_record.generation_depth == 1
    assert "Bridge" in cand.name
    assert cand.instrument_result.plan.target_track_name == "Pad Texture (Bridge)"


def test_cross_pollination_fails_when_seed_at_max_depth(engine, song_dna):
    # If the source record is already at generation 3, it should fail with CreativeGovernanceError
    from engine.audio_genesis.provenance import SampleProvenanceRecord, SampleOrigin, AudioSourceLocation, InstrumentProvenance

    deep_record = SampleProvenanceRecord(
        sample_id="deep_seed_03",
        origin=SampleOrigin.DERIVED_FROM_SONG,
        source=AudioSourceLocation(track="Rhodes Keys"),
        instrument=InstrumentProvenance(),
        generation_depth=3
    )
    engine.provenance_engine.register_sample(deep_record)

    # Attempting to mutate deep_record directly via mutation engine triggers GenerationDepthGuard
    from engine.audio_genesis.sonic_recursion import GenerationDepthGuard
    with pytest.raises(CreativeGovernanceError) as excinfo:
        GenerationDepthGuard.validate_depth(deep_record)

    assert "Veto Regla 4 (Límite generacional)" in str(excinfo.value)
