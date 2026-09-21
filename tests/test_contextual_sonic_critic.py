# tests/test_contextual_sonic_critic.py
"""
Unit and physical integration tests for Contextual Sonic Critic (Nivel R):
Evaluates:
- Physical audio signal analysis (RMS, Peak, Crest Factor, Frequency Bands, Stereo Width, Mono Correlation).
- In-situ A/B Section Audition (Baseline vs Staged).
- Definitive improvement approval in Hook 3.
- Veto on severe vocal masking (1.0 - 3.5 kHz corridor).
- Veto on mono phase collapse (anti-phase cancellation).
- Veto on low-mid mud zone congestion (200 - 500 Hz).
- Veto on transient crushing (drum punch destruction).
- Flexible distance classification: Subtle Variation (<0.25) vs Balanced (0.25-0.88) vs Radical Discovery (>0.88).
- Marginal benefit verdict handling.
"""

import pytest
import numpy as np
import math

from engine.creative.contextual_sonic_critic import (
    ContextualDimension,
    ContextualVerdict,
    AudioSectionAcousticSnapshot,
    ContextualAcousticDeltas,
    ContextualAuditReport,
    ContextualSonicCritic,
)
from engine.audio_genesis.sonic_recursion import (
    DistanceCategory,
    PerceptualDistanceAuditor,
)
from engine.composition.compositional_dna import (
    CompositionalDNA,
    PrimaryMotif,
    MotifNote,
)


@pytest.fixture
def critic():
    return ContextualSonicCritic()


@pytest.fixture
def song_dna():
    return CompositionalDNA(
        song_id="critic_eval_song",
        title="Contextual Sonic Test",
        bpm=120.0,
        primary_motif=PrimaryMotif(
            name="Theme Lead",
            notes=[MotifNote(pitch=60, start_time=0.0, duration=0.5)]
        )
    )


def test_physical_snapshot_analysis(critic):
    # Synthesize 1 second stereo test signal: Kick (60 Hz) + Vocal (2200 Hz)
    audio = critic.synthesize_test_section(duration_sec=1.0, has_vocal=True)
    snapshot = critic.analyze_audio_signal(audio, sample_rate=44100)

    assert isinstance(snapshot, AudioSectionAcousticSnapshot)
    assert 0.99 <= snapshot.duration_sec <= 1.01
    assert snapshot.peak_dbfs > -30.0
    assert snapshot.rms_dbfs > -35.0
    assert snapshot.crest_factor_db > 0.0
    assert snapshot.sub_energy_dbfs > -60.0       # 60 Hz kick detected
    assert snapshot.vocal_corridor_dbfs > -40.0   # 2200 Hz tone detected
    assert 0.90 <= snapshot.mono_correlation <= 1.0


def test_approves_clean_improvement_in_hook(critic, song_dna):
    # Baseline: Drums + Bass + Vocals
    baseline = critic.synthesize_test_section("Hook 3", has_vocal=True)

    # Staged: Baseline + Clean Warm Pad with gentle stereo spread
    staged = critic.synthesize_test_section("Hook 3", has_vocal=True, add_clean_pad=True)

    report = critic.evaluate_staged_sound_in_context(
        section_name="Hook 3",
        baseline_audio=baseline,
        staged_audio=staged,
        song_dna=song_dna,
        target_role="pad_texture",
        candidate_id="cand_pad_01",
        distance_score=0.45
    )

    assert isinstance(report, ContextualAuditReport)
    assert report.verdict == ContextualVerdict.DEFINITIVE_IMPROVEMENT
    assert report.net_improvement_score >= 0.10
    assert len(report.veto_flags) == 0
    assert report.deltas.delta_rms_db > 0.3
    assert report.dimension_scores[ContextualDimension.VOCAL_CLEARANCE.value] > 0.85
    assert report.dimension_scores[ContextualDimension.ENERGY_TRAJECTORY.value] > 0.85
    assert "Aprobar e integrar" in report.actionable_directive
    assert "Hook 3" in report.actionable_directive


def test_vetoes_vocal_masking(critic, song_dna):
    baseline = critic.synthesize_test_section("Hook 3", has_vocal=True)
    # Staged: Adds massive loud synth directly in the vocal corridor (2200 Hz)
    staged = critic.synthesize_test_section("Hook 3", has_vocal=True, add_vocal_clash=True)

    report = critic.evaluate_staged_sound_in_context(
        section_name="Hook 3",
        baseline_audio=baseline,
        staged_audio=staged,
        song_dna=song_dna,
        target_role="lead",
        candidate_id="cand_clash_01",
        distance_score=0.50
    )

    assert report.verdict == ContextualVerdict.DEGRADATION
    assert report.net_improvement_score < 0.0
    assert "VOCAL_MASKING_EXCEEDED" in report.veto_flags
    assert report.dimension_scores[ContextualDimension.VOCAL_CLEARANCE.value] <= 0.40
    assert "Rechazar o intervenir fader" in report.actionable_directive
    assert "ahogar la voz principal" in report.actionable_directive
    assert any("sidechain dinámico" in s for s in report.mixing_suggestions)


def test_vetoes_mono_phase_collapse(critic, song_dna):
    baseline = critic.synthesize_test_section("Chorus", has_vocal=True)
    # Staged: Anti-phase audio (Right = -Left)
    staged = critic.synthesize_test_section("Chorus", has_vocal=True, add_phase_inversion=True)

    report = critic.evaluate_staged_sound_in_context(
        section_name="Chorus",
        baseline_audio=baseline,
        staged_audio=staged,
        song_dna=song_dna,
        target_role="pad_texture",
        candidate_id="cand_phase_fail",
        distance_score=0.60
    )

    assert report.verdict == ContextualVerdict.DEGRADATION
    assert "MONO_PHASE_COLLAPSE" in report.veto_flags
    assert report.dimension_scores[ContextualDimension.SPACE_WIDTH.value] <= 0.10
    assert "Veto crítico de fase" in report.actionable_directive


def test_vetoes_mud_zone_saturation(critic, song_dna):
    baseline = critic.synthesize_test_section("Verse 1", has_vocal=True)
    # Staged: Overbearing 300 Hz resonance
    staged = critic.synthesize_test_section("Verse 1", has_vocal=True, add_mud_drone=True)

    report = critic.evaluate_staged_sound_in_context(
        section_name="Verse 1",
        baseline_audio=baseline,
        staged_audio=staged,
        song_dna=song_dna,
        target_role="bass",
        candidate_id="cand_mud_sub",
        distance_score=0.40
    )

    assert report.verdict == ContextualVerdict.DEGRADATION
    assert "MUD_ZONE_CONGESTION" in report.veto_flags
    assert report.dimension_scores[ContextualDimension.SPECTRAL_CROWDING.value] <= 0.30
    assert "saturación de graves medios" in report.actionable_directive


def test_vetoes_transient_crushing(critic, song_dna):
    baseline = critic.synthesize_test_section("Drop", has_vocal=False)
    # Staged: Heavy squash limiting destroying dynamic crest factor
    staged = critic.synthesize_test_section("Drop", has_vocal=False, add_squash_limiting=True)

    report = critic.evaluate_staged_sound_in_context(
        section_name="Drop",
        baseline_audio=baseline,
        staged_audio=staged,
        song_dna=song_dna,
        target_role="drums",
        candidate_id="cand_squash",
        distance_score=0.35,
        has_lead_vocal=False
    )

    assert report.verdict == ContextualVerdict.DEGRADATION
    assert "TRANSIENTS_CRUSHED" in report.veto_flags
    assert report.dimension_scores[ContextualDimension.TRANSIENTS.value] <= 0.30
    assert "aplastamiento de batería" in report.actionable_directive


def test_distance_flexibility_approves_subtle_and_radical_when_musically_sound(critic, song_dna):
    baseline = critic.synthesize_test_section("Hook 3", has_vocal=True)
    staged = critic.synthesize_test_section("Hook 3", has_vocal=True, add_clean_pad=True)

    # 1. Subtle recognizable variation (distance = 0.15, < 0.25)
    # Previously hard-vetoed, now classified and approved because the sound elevates the section!
    desc_subtle = PerceptualDistanceAuditor.get_distance_descriptor(0.15)
    assert desc_subtle["category"] == "subtle_recognizable_variation"

    report_subtle = critic.evaluate_staged_sound_in_context(
        section_name="Hook 3",
        baseline_audio=baseline,
        staged_audio=staged,
        song_dna=song_dna,
        target_role="pad_texture",
        candidate_id="cand_subtle_motif",
        distance_score=0.15
    )
    assert report_subtle.verdict == ContextualVerdict.DEFINITIVE_IMPROVEMENT
    assert report_subtle.distance_category == "subtle_recognizable_variation"
    assert "Preserva el motivo con fidelidad" in report_subtle.actionable_directive

    # 2. Radical discovery (distance = 0.92, > 0.88)
    # Previously hard-vetoed, now recognized as bold discovery and approved because mix is clean!
    desc_radical = PerceptualDistanceAuditor.get_distance_descriptor(0.92)
    assert desc_radical["category"] == "radical_discovery"

    report_radical = critic.evaluate_staged_sound_in_context(
        section_name="Hook 3",
        baseline_audio=baseline,
        staged_audio=staged,
        song_dna=song_dna,
        target_role="ear_candy",
        candidate_id="cand_radical_glitch",
        distance_score=0.92
    )
    assert report_radical.verdict == ContextualVerdict.DEFINITIVE_IMPROVEMENT
    assert report_radical.distance_category == "radical_discovery"
    assert "metamorfosis audaz" in report_radical.actionable_directive


def test_marginal_benefit_evaluation(critic, song_dna):
    # Dict-based acoustic snapshots with nearly flat delta (minimal change)
    baseline_metrics = {
        "rms_dbfs": -18.0,
        "peak_dbfs": -6.0,
        "crest_factor_db": 12.0,
        "vocal_corridor_dbfs": -22.0,
        "mud_energy_dbfs": -25.0,
        "sub_energy_dbfs": -20.0,
        "stereo_width": 0.30,
        "mono_correlation": 0.85,
        "sub_mono_correlation": 0.95
    }
    # Staged with tiny +0.05 dB change
    staged_metrics = {
        "rms_dbfs": -17.95,
        "peak_dbfs": -5.98,
        "crest_factor_db": 11.97,
        "vocal_corridor_dbfs": -21.98,
        "mud_energy_dbfs": -24.95,
        "sub_energy_dbfs": -20.0,
        "stereo_width": 0.31,
        "mono_correlation": 0.85,
        "sub_mono_correlation": 0.95
    }

    report = critic.evaluate_staged_sound_in_context(
        section_name="Bridge",
        baseline_audio=baseline_metrics,
        staged_audio=staged_metrics,
        song_dna=song_dna,
        target_role="pad_texture",
        candidate_id="cand_subtle_pad",
        distance_score=0.50
    )

    assert report.verdict == ContextualVerdict.MARGINAL_BENEFIT
    assert 0.0 <= report.net_improvement_score < 0.10
    assert "Beneficio marginal" in report.actionable_directive
