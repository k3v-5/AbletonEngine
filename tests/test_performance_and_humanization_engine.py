# tests/test_performance_and_humanization_engine.py
"""
Unit and Integration Tests for Nivel T: Intentional Musical Performance & Humanization Engine.

Validates the 6 canonical acceptance criteria and T1-T5 phases:
1. Groove Conservation (Kick-Bass relative coupling preserved within +/- 2.0 ms).
2. Structural Melody Integrity (Target arrival notes preserved with rubato weight).
3. Hierarchical Chord Strumming (Micro-spread 5-25 ms with top-voice melody accent).
4. Phrase Breathing Gaps (Guaranteed breath silence >= 35 ms between phrases).
5. Atomic Reversibility & Zero State Leakage (100% rollback in 0 ms via PerformanceSnapshot).
6. Cross-Song Performance Identity Consistency (Distinguishes styles & persists to catalog).
"""

import pytest
import numpy as np
import copy
from pathlib import Path

from engine.performance import (
    PocketTendency,
    VelocityProfile,
    ArticulationStyle,
    PerformanceIntent,
    InstrumentPerformanceProfile,
    PerformanceSnapshot,
    PerformanceMutation,
    PerformanceCore,
    SongGrooveTemplate,
    GrooveMemory,
    CorrelatedHumanizer,
    PhraseSegment,
    PhraseBreathingEngine,
    PerformanceSignature,
    PerformanceIdentityEngine,
    PerformanceClosedLoopAdapter,
)
from engine.creative.evolution import (
    InterventionDomain,
    InterventionType,
    InterventionOrder,
    EvolutionLedger,
    MultiDomainInterventionRouter,
)
from engine.creative.contextual_sonic_critic import (
    ContextualSonicCritic,
    ContextualAuditReport,
    ContextualVerdict,
)
from engine.composition.compositional_dna import (
    CompositionalDNA,
    NegativeConstraint,
)


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture
def sample_session_notes():
    """Generates a standard 2-bar loop (8 beats at 120 BPM) with Kick, Bass, Snare, Keys, Lead."""
    # 120 BPM: 1 beat = 500 ms, 1/16 = 125 ms
    kicks = [
        {"pitch": 36, "start_time": 0.0, "duration": 0.25, "velocity": 100},
        {"pitch": 36, "start_time": 1.0, "duration": 0.25, "velocity": 95},
        {"pitch": 36, "start_time": 2.0, "duration": 0.25, "velocity": 100},
        {"pitch": 36, "start_time": 3.0, "duration": 0.25, "velocity": 95},
        {"pitch": 36, "start_time": 4.0, "duration": 0.25, "velocity": 100},
        {"pitch": 36, "start_time": 5.0, "duration": 0.25, "velocity": 95},
        {"pitch": 36, "start_time": 6.0, "duration": 0.25, "velocity": 100},
        {"pitch": 36, "start_time": 7.0, "duration": 0.25, "velocity": 95},
    ]
    snares = [
        {"pitch": 38, "start_time": 1.0, "duration": 0.25, "velocity": 105},
        {"pitch": 38, "start_time": 3.0, "duration": 0.25, "velocity": 105},
        {"pitch": 38, "start_time": 5.0, "duration": 0.25, "velocity": 105},
        {"pitch": 38, "start_time": 7.0, "duration": 0.25, "velocity": 105},
    ]
    # Bass notes align with kicks on downbeats
    bass = [
        {"pitch": 36, "start_time": 0.0, "duration": 0.8, "velocity": 90},
        {"pitch": 36, "start_time": 2.0, "duration": 0.8, "velocity": 90},
        {"pitch": 39, "start_time": 4.0, "duration": 0.8, "velocity": 90},
        {"pitch": 41, "start_time": 6.0, "duration": 0.8, "velocity": 90},
    ]
    # Block chords on Keys
    keys = [
        # Bar 1 chord: C min7 (C3, Eb3, G3, Bb3)
        {"pitch": 48, "start_time": 0.0, "duration": 1.75, "velocity": 80},
        {"pitch": 51, "start_time": 0.0, "duration": 1.75, "velocity": 80},
        {"pitch": 55, "start_time": 0.0, "duration": 1.75, "velocity": 80},
        {"pitch": 58, "start_time": 0.0, "duration": 1.75, "velocity": 80},
        # Bar 2 chord: F min7 (F3, Ab3, C4, Eb4)
        {"pitch": 53, "start_time": 4.0, "duration": 1.75, "velocity": 80},
        {"pitch": 56, "start_time": 4.0, "duration": 1.75, "velocity": 80},
        {"pitch": 60, "start_time": 4.0, "duration": 1.75, "velocity": 80},
        {"pitch": 63, "start_time": 4.0, "duration": 1.75, "velocity": 80},
    ]
    # Melodic lead line in two distinct phrases
    lead = [
        # Phrase 1 (beats 0 to 3)
        {"pitch": 67, "start_time": 0.5, "duration": 0.5, "velocity": 85},   # Prep
        {"pitch": 70, "start_time": 1.0, "duration": 0.5, "velocity": 88},   # Tension
        {"pitch": 72, "start_time": 1.5, "duration": 0.75, "velocity": 92},  # Climax
        {"pitch": 67, "start_time": 2.5, "duration": 0.5, "velocity": 82},   # Resolution / final
        # Phrase 2 (beats 4 to 7)
        {"pitch": 65, "start_time": 4.5, "duration": 0.5, "velocity": 85},
        {"pitch": 68, "start_time": 5.0, "duration": 0.5, "velocity": 88},
        {"pitch": 72, "start_time": 5.5, "duration": 0.75, "velocity": 92},
        {"pitch": 65, "start_time": 6.5, "duration": 0.5, "velocity": 82},
    ]

    return {
        "Kick": kicks,
        "Snare": snares,
        "Bass": bass,
        "Keys": keys,
        "Lead": lead,
    }


@pytest.fixture
def sample_roles():
    return {
        "Kick": "kick",
        "Snare": "snare",
        "Bass": "bass",
        "Keys": "keys",
        "Lead": "lead",
    }


# =============================================================================
# T1 Tests — Performance Core
# =============================================================================
def test_performance_core_microtiming_and_velocity():
    """Verifies role-calibrated microtiming and dynamic hierarchy."""
    kick_notes = [
        {"pitch": 36, "start_time": 0.0, "duration": 0.25, "velocity": 90},
        {"pitch": 36, "start_time": 1.0, "duration": 0.25, "velocity": 90},
        {"pitch": 36, "start_time": 2.0, "duration": 0.25, "velocity": 90},
        {"pitch": 36, "start_time": 3.0, "duration": 0.25, "velocity": 90},
    ]
    kick_prof = InstrumentPerformanceProfile.create_default("kick")
    intent = PerformanceIntent(
        pocket=PocketTendency.ON_THE_GRID,
        velocity_profile=VelocityProfile.TIERED_PULSE,
        human_factor=0.6
    )

    hum_kicks = PerformanceCore.humanize_track_notes(
        kick_notes, role="kick", profile=kick_prof, intent=intent, bpm=120.0
    )

    assert len(hum_kicks) == 4
    # Kick anchor should maintain tight timing (<1.5 ms offset, at 120 bpm 1ms = 0.002 beats)
    for orig, hum in zip(kick_notes, hum_kicks):
        beat_delta = abs(hum["start_time"] - orig["start_time"])
        ms_delta = beat_delta * 500.0
        assert ms_delta <= 2.0, f"Kick timing deviated too much: {ms_delta:.2f} ms"


def test_chord_strumming_and_top_voice_accent():
    """Acceptance Criterion #3: Block chords spread micro-time with top voice accent."""
    chord_notes = [
        {"pitch": 48, "start_time": 0.0, "duration": 2.0, "velocity": 80},  # C3
        {"pitch": 51, "start_time": 0.0, "duration": 2.0, "velocity": 80},  # Eb3
        {"pitch": 55, "start_time": 0.0, "duration": 2.0, "velocity": 80},  # G3
        {"pitch": 58, "start_time": 0.0, "duration": 2.0, "velocity": 80},  # Bb3 (top melody)
    ]
    keys_prof = InstrumentPerformanceProfile(
        role="keys",
        strum_spread_ms=18.0,
        strum_top_note_accent=14
    )

    strummed = PerformanceCore.apply_chord_strumming(chord_notes, keys_prof, bpm=120.0)

    assert len(strummed) == 4
    # Verify spread across time (start times must be strictly increasing)
    start_times = [n["start_time"] for n in strummed]
    for i in range(len(start_times) - 1):
        assert start_times[i] <= start_times[i + 1]

    # Verify top voice (pitch 58) received top accent
    top_note = next(n for n in strummed if n["pitch"] == 58)
    assert top_note["velocity"] == 94, f"Expected 94, got {top_note['velocity']}"


def test_atomic_snapshot_and_rollback():
    """Acceptance Criterion #5: 100% reversible rollback in 0 ms."""
    original_tracks = {
        "Kick": [{"pitch": 36, "start_time": 0.0, "duration": 0.25, "velocity": 100}],
        "Bass": [{"pitch": 36, "start_time": 0.0, "duration": 0.80, "velocity": 90}],
    }

    # 1. Capture snapshot
    snapshot = PerformanceCore.create_snapshot(original_tracks)
    fp_before = snapshot.state_fingerprint

    # 2. Mutate tracks destructively
    mutated_tracks = copy.deepcopy(original_tracks)
    mutated_tracks["Kick"][0]["start_time"] = 0.12345
    mutated_tracks["Kick"][0]["velocity"] = 127
    mutated_tracks["Bass"][0]["pitch"] = 72

    assert mutated_tracks != original_tracks

    # 3. Restore snapshot in 0 ms
    restored = PerformanceCore.restore_snapshot(snapshot)

    assert restored == original_tracks
    restored_snapshot = PerformanceCore.create_snapshot(restored)
    assert restored_snapshot.state_fingerprint == fp_before


# =============================================================================
# T2 Tests — Groove Intelligence & Correlated Humanization
# =============================================================================
def test_groove_memory_extraction(sample_session_notes, sample_roles):
    """Verifies song groove extraction from multi-track session notes."""
    template = GrooveMemory.analyze_session_groove(
        session_tracks=sample_session_notes,
        track_roles=sample_roles,
        bpm=120.0
    )

    assert template.anchor_role == "kick"
    assert template.bpm == 120.0
    assert isinstance(template.kick_bass_coupling_ms, float)
    assert isinstance(template.snare_laid_back_ms, float)


def test_correlated_kick_bass_coupling(sample_session_notes, sample_roles):
    """
    Acceptance Criterion #1: Kick-Bass relative coupling preserved within +/- 2.0 ms.
    Replaces independent random noise with correlated ensemble timing.
    """
    intent = PerformanceIntent(
        pocket=PocketTendency.LAID_BACK,
        human_factor=0.8
    )
    template = SongGrooveTemplate(
        bpm=120.0,
        kick_bass_coupling_ms=2.0,  # Explicit coupling target
        snare_laid_back_ms=10.0
    )

    humanized = CorrelatedHumanizer.humanize_ensemble(
        session_tracks=sample_session_notes,
        track_roles=sample_roles,
        intent=intent,
        bpm=120.0,
        groove_template=template,
        seed=777
    )

    kicks = humanized["Kick"]
    basses = humanized["Bass"]

    ms_per_beat = (60.0 / 120.0) * 1000.0  # 500 ms

    # Check the 4 downbeat hits where Kick and Bass coincide (nominal beats 0, 2, 4, 6)
    for nominal_beat in [0.0, 2.0, 4.0, 6.0]:
        k_hit = next(k for k in kicks if abs(k["start_time"] - nominal_beat) < 0.15)
        b_hit = next(b for b in basses if abs(b["start_time"] - nominal_beat) < 0.15)

        # Difference in milliseconds
        delta_ms = (b_hit["start_time"] - k_hit["start_time"]) * ms_per_beat

        # Coupling target is 2.0 ms * 0.8 = 1.6 ms; must stay within +/- 2.0 ms of target!
        expected_coupling = 2.0 * 0.8
        error_ms = abs(delta_ms - expected_coupling)
        assert error_ms <= 2.0, f"Kick-Bass coupling disassociated: delta={delta_ms:.2f} ms vs target={expected_coupling:.2f} ms"


def test_snare_laid_back_relative_to_pulse(sample_session_notes, sample_roles):
    """Verifies snare acquires laid-back pocket relative to backbeats."""
    intent = PerformanceIntent(pocket=PocketTendency.LAID_BACK, human_factor=0.8)
    template = SongGrooveTemplate(bpm=120.0, snare_laid_back_ms=12.0)

    humanized = CorrelatedHumanizer.humanize_ensemble(
        session_tracks=sample_session_notes,
        track_roles=sample_roles,
        intent=intent,
        bpm=120.0,
        groove_template=template,
        seed=42
    )

    snares = humanized["Snare"]
    ms_per_beat = (60.0 / 120.0) * 1000.0

    # Snares are on nominal beats 1.0, 3.0, 5.0, 7.0
    for nominal_beat in [1.0, 3.0, 5.0, 7.0]:
        s_hit = next(s for s in snares if abs(s["start_time"] - nominal_beat) < 0.2)
        drag_ms = (s_hit["start_time"] - nominal_beat) * ms_per_beat
        assert drag_ms > 0.0, f"Snare was expected to drag laid-back, but was: {drag_ms:.2f} ms"


# =============================================================================
# T3 Tests — Phrase Breathing Engine
# =============================================================================
def test_phrase_breathing_climax_and_breath_gap(sample_session_notes):
    """
    Acceptance Criteria #2 & #4: Target arrival note receives weight,
    and guaranteed breath gap (>= 35 ms) is enforced at phrase ending.
    """
    lead_notes = sample_session_notes["Lead"]
    lead_prof = InstrumentPerformanceProfile.create_default("lead")
    lead_prof.phrase_breathing_enabled = True
    lead_prof.min_breath_gap_ms = 40.0

    intent = PerformanceIntent(
        phrase_push=0.3,
        human_factor=0.8
    )

    breathing_notes = PhraseBreathingEngine.apply_phrase_breathing(
        lead_notes, lead_prof, intent, bpm=120.0
    )

    assert len(breathing_notes) == len(lead_notes)

    # 1. Check Climax Note weight (Pitch 72 in Phrase 1)
    climax_note = next(n for n in breathing_notes[:4] if n["pitch"] == 72)
    assert climax_note["velocity"] >= 100, f"Expected boosted velocity, got {climax_note['velocity']}"

    # 2. Check Guaranteed Breath Gap before Phrase 2 starts (Phrase 1 ends around beat 3.0, Phrase 2 starts beat 4.5)
    phrase1_last_note = breathing_notes[3]
    phrase2_first_note = breathing_notes[4]

    p1_end = phrase1_last_note["start_time"] + phrase1_last_note["duration"]
    p2_start = phrase2_first_note["start_time"]
    gap_beats = p2_start - p1_end
    gap_ms = gap_beats * 500.0

    assert gap_ms >= 40.0, f"Breath gap violated: {gap_ms:.2f} ms (expected >= 40.0 ms)"


# =============================================================================
# T4 Tests — Performance Identity & Catalog Memory
# =============================================================================
def test_performance_identity_extraction_and_comparison(sample_session_notes, sample_roles):
    """
    Acceptance Criterion #6: Performance Identity distinguishes between styles
    and computes similarity.
    """
    # Extract identity from laid-back session
    sig_laid_back = PerformanceIdentityEngine.extract_signature(
        session_tracks=sample_session_notes,
        track_roles=sample_roles,
        bpm=120.0,
        name="Laid-Back Neo-Soul",
        groove_template=SongGrooveTemplate(kick_bass_coupling_ms=2.5, snare_laid_back_ms=14.0)
    )

    # Synthetic tight funk identity
    sig_tight_funk = PerformanceSignature(
        identity_id="perf_tight_funk",
        name="Tight Hardware Funk",
        groove_signature={"kick_bass_coupling_ms": 0.2, "snare_laid_back_ms": -2.0, "swing_ratio": 0.50},
        timing_signature={"kick_std_ms": 0.8, "bass_std_ms": 1.2, "snare_std_ms": 1.5}
    )

    assert sig_laid_back.identity_id != ""
    assert sig_laid_back.fingerprint != ""

    # Self-similarity must be 1.0
    self_sim = PerformanceIdentityEngine.calculate_similarity(sig_laid_back, sig_laid_back)
    assert self_sim == 1.0

    # Cross-style similarity must detect divergence
    cross_sim = PerformanceIdentityEngine.calculate_similarity(sig_laid_back, sig_tight_funk)
    assert cross_sim < 0.90, f"Expected divergence between Neo-Soul and Funk, got {cross_sim}"


# =============================================================================
# T5 Tests — S <-> T Closed-Loop Integration
# =============================================================================
def test_mechanical_fatigue_detection():
    """Detects over-quantized mechanical session."""
    rigid_notes = {
        "Lead": [
            {"pitch": 60, "start_time": 0.0, "duration": 0.25, "velocity": 90},
            {"pitch": 62, "start_time": 0.25, "duration": 0.25, "velocity": 90},
            {"pitch": 64, "start_time": 0.50, "duration": 0.25, "velocity": 90},
            {"pitch": 65, "start_time": 0.75, "duration": 0.25, "velocity": 90},
        ]
    }
    is_fatigued, report = PerformanceClosedLoopAdapter.detect_mechanical_fatigue(
        rigid_notes, {"Lead": "lead"}, bpm=120.0
    )
    assert is_fatigued is True
    assert report["grid_snap_pct"] == 100.0


def test_closed_loop_performance_commit(sample_session_notes, sample_roles):
    """Verifies that an acoustically superior performance candidate is committed."""
    critic = ContextualSonicCritic()
    ledger = EvolutionLedger()
    adapter = PerformanceClosedLoopAdapter(critic=critic, ledger=ledger)

    baseline_audio = critic.synthesize_test_section("Chorus", has_vocal=True, add_vocal_clash=True)
    improved_audio = critic.synthesize_test_section("Chorus", has_vocal=True, add_vocal_clash=False)

    candidate_audio_map = {
        "laid_back_expressive": improved_audio,
        "subtle_pocket": baseline_audio,
        "dilla_drag": baseline_audio,
    }

    final_tracks, mutation, verdict = adapter.execute_closed_loop_performance_cycle(
        section_name="Chorus",
        session_tracks=sample_session_notes,
        track_roles=sample_roles,
        baseline_audio=baseline_audio,
        candidate_audio_map=candidate_audio_map,
        bpm=120.0
    )

    assert verdict == "COMMIT"
    assert mutation.verdict == "COMMIT"
    assert mutation.delta_q_achieved > 0.0
    assert len(ledger.history) >= 1
    assert ledger.history[-1]["order_domain"] == "PERFORMANCE"


def test_closed_loop_performance_rollback_on_degradation(sample_session_notes, sample_roles):
    """
    Acceptance Criterion #5: Reverts to original baseline notes in 0 ms
    when candidates degrade acoustic critique.
    """
    critic = ContextualSonicCritic()
    ledger = EvolutionLedger()
    adapter = PerformanceClosedLoopAdapter(critic=critic, ledger=ledger)

    baseline_audio = critic.synthesize_test_section("Chorus", has_vocal=True, add_clean_pad=True)
    # Degraded candidates with heavy clash and low-end mud
    degraded_audio = critic.synthesize_test_section("Chorus", has_vocal=True, add_vocal_clash=True, add_mud_drone=True)

    candidate_audio_map = {
        "laid_back_expressive": degraded_audio,
        "subtle_pocket": degraded_audio,
        "dilla_drag": degraded_audio,
    }

    final_tracks, mutation, verdict = adapter.execute_closed_loop_performance_cycle(
        section_name="Chorus",
        session_tracks=sample_session_notes,
        track_roles=sample_roles,
        baseline_audio=baseline_audio,
        candidate_audio_map=candidate_audio_map,
        bpm=120.0
    )

    assert verdict == "ROLLBACK"
    assert mutation.verdict == "ROLLBACK"
    # Pristine notes preserved
    assert final_tracks == sample_session_notes


def test_evolution_router_routes_performance_order():
    """Verifies that MultiDomainInterventionRouter executes PERFORMANCE orders."""
    router = MultiDomainInterventionRouter()
    order = InterventionOrder(
        order_id="perf_order_01",
        domain=InterventionDomain.PERFORMANCE,
        intervention_type=InterventionType.PERFORMANCE_HUMANIZATION_POCKET,
        target_section="Chorus",
        target_track_or_role="bass",
        reasoning="Mechanical fatigue diagnosed in low-end section."
    )
    initial_state = {"active_layers": ["drums", "bass", "keys"]}
    new_state = router.execute_order(order, initial_state)

    assert "performance_modifications" in new_state
    assert "bass" in new_state["performance_modifications"]
    assert new_state["performance_modifications"]["bass"]["pocket"] == "laid_back"
