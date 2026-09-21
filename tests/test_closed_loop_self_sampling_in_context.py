# tests/test_closed_loop_self_sampling_in_context.py
"""
Integration test for Closed-Loop Self-Sampling & Contextual Sonic Critic:
Validates that emergent candidates created before arrangement placement
can be audited in-situ in specific sections (e.g., Hook 3, Verse 1, Bridge),
providing concrete physical answers to:
'Puse esta mutación en el Hook 3 → ¿la canción realmente mejoró?'
"""

import pytest
from engine.audio_genesis.self_sampling_engine import (
    SelfSamplingEngine,
    EmergentProposalBatch,
    EmergentSoundCandidate,
)
from engine.audio_genesis.sonic_recursion import (
    RecursiveTargetRole,
    DistanceCategory,
)
from engine.creative.contextual_sonic_critic import (
    ContextualVerdict,
    ContextualAuditReport,
)
from engine.composition.compositional_dna import (
    CompositionalDNA,
    PrimaryMotif,
    MotifNote,
)


@pytest.fixture
def song_dna():
    return CompositionalDNA(
        song_id="closed_loop_song",
        title="Harmonic Loop DNA",
        bpm=120.0,
        primary_motif=PrimaryMotif(
            name="Theme Lead",
            notes=[
                MotifNote(pitch=60, start_time=0.0, duration=0.5),
                MotifNote(pitch=64, start_time=0.5, duration=0.5),
                MotifNote(pitch=67, start_time=1.0, duration=1.0),
            ]
        )
    )


@pytest.fixture
def engine():
    return SelfSamplingEngine()


def test_audit_candidate_in_context_returns_verifiable_answer(engine, song_dna):
    # 1. Propose emergent sounds for a floating pad
    batch = engine.propose_emergent_sounds(
        song_dna=song_dna,
        musical_need="dark_floating_texture",
        target_role=RecursiveTargetRole.PAD_TEXTURE,
        candidate_count=3,
        strict_distance=False
    )
    assert batch.winner_candidate is not None
    winner = batch.winner_candidate

    # 2. Audit the winner in Hook 3 context
    report = engine.audit_candidate_in_context(
        candidate=winner,
        section_name="Hook 3",
        song_dna=song_dna
    )

    assert isinstance(report, ContextualAuditReport)
    assert report.section_name == "Hook 3"
    assert report.candidate_id == winner.candidate_id
    assert winner.contextual_report is not None
    assert winner.contextual_report.verdict in [
        ContextualVerdict.DEFINITIVE_IMPROVEMENT,
        ContextualVerdict.MARGINAL_BENEFIT,
        ContextualVerdict.DEGRADATION
    ]
    # Verify report is populated with full acoustic metrics
    assert report.baseline_metrics.rms_dbfs < 0.0
    assert report.staged_metrics.rms_dbfs < 0.0
    assert len(report.dimension_scores) == 10
    assert len(report.actionable_directive) > 10


def test_batch_proposal_with_section_context_evaluates_all_candidates(engine, song_dna):
    # Proposing candidates directly with section_context performs automatic in-situ audition
    batch = engine.propose_emergent_sounds(
        song_dna=song_dna,
        musical_need="sub_harmonic_foundation",
        target_role=RecursiveTargetRole.BASS,
        candidate_count=3,
        section_context="Hook 3"
    )

    for cand in batch.candidates:
        assert cand.distance_category in [
            DistanceCategory.SUBTLE_RECOGNIZABLE_VARIATION.value,
            DistanceCategory.BALANCED_EVOLUTION.value,
            DistanceCategory.RADICAL_DISCOVERY.value,
        ]
        assert cand.contextual_report is not None
        assert cand.contextual_report.section_name == "Hook 3"
