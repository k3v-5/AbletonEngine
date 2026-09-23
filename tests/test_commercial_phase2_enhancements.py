# tests/test_commercial_phase2_enhancements.py
"""
Test Suite for Phase 2 Commercial Enhancements:
1. SmartEarCandyEngine (Micro-textures, peripheral panning, 5 density levels)
2. DynamicSpaceDucker (Ducked reverbs/delays, bloom envelope, Live sidechain configuration)
3. ModalVoiceLeadingEngine (Modal borrowing, borrowed chords iv, bVI, bVII, Dorian IV, smooth inversions)
4. MetricModulationEngine (5-level micro-rhythmic metric modulation, triplets, quintuplets)
5. CopilotGuidedSession integration and global query intercepts
"""

import pytest
from unittest.mock import MagicMock
from engine.arrangement.transitions.ear_candy import SmartEarCandyEngine, EarCandyGestureType, EarCandyEvent
from engine.mix.space_ducking import DynamicSpaceDucker, SpaceDuckingMode
from engine.music.harmony.modal_voice_leading import (
    ModalVoiceLeadingEngine, BorrowedChordType, VoicedChord
)
from engine.music.groove.metric_modulation import (
    MetricModulationEngine, MetricModulationLevel
)
from engine.music.models import NoteEvent
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.production.copilot.intercept_router import CopilotInterceptRouter


class DummyMockConnection:
    """Mock connection for Live API testing."""
    def __init__(self):
        self.sent_commands = []

    def send_command(self, cmd: str, args: dict) -> dict:
        self.sent_commands.append({"command": cmd, "args": args})
        if cmd == "get_session_info":
            return {"result": {"track_count": 6}}
        if cmd == "get_track_info":
            return {"result": {"name": f"Track_{args.get('track_index', 0)}", "devices": ["Eq8", "Compressor"]}}
        if cmd == "get_arrangement_clips":
            return {"clips": []}
        return {"status": "ok"}


# =============================================================================
# 1. SMART EAR CANDY ENGINE TESTS
# =============================================================================

def test_ear_candy_generation_and_peripheral_panning():
    sections = [
        {"name": "Intro", "bars": 8},
        {"name": "Verse 1", "bars": 16},
        {"name": "Chorus 1", "bars": 8},
        {"name": "Verse 2", "bars": 16},
        {"name": "Chorus 2", "bars": 8},
        {"name": "Outro", "bars": 8},
    ]
    events = SmartEarCandyEngine.generate_ear_candy_package(
        sections=sections,
        total_bars=64,
        density_level=2,
        seed=42
    )

    assert len(events) >= 6
    # Verify strict peripheral panning: NEVER at Center (0.0)
    for ev in events:
        assert abs(ev.pan) >= 0.35, f"Pan {ev.pan} must be outside center corridor"
        assert abs(ev.pan) <= 0.65
        assert ev.velocity >= 35
        assert ev.velocity <= 100
        assert ev.target_role == "EAR_CANDY"


def test_ear_candy_density_levels():
    sections = [{"name": "Section A", "bars": 16}, {"name": "Section B", "bars": 16}]
    # Level 1 (minimal) vs Level 5 (complextro/glitch)
    events_l1 = SmartEarCandyEngine.generate_ear_candy_package(sections, total_bars=32, density_level=1, seed=42)
    events_l5 = SmartEarCandyEngine.generate_ear_candy_package(sections, total_bars=32, density_level=5, seed=42)

    assert len(events_l5) > len(events_l1)
    summary_md = SmartEarCandyEngine.render_markdown_summary(events_l1, density_level=1)
    assert "Minimalista" in summary_md


# =============================================================================
# 2. DYNAMIC SPACE DUCKER TESTS
# =============================================================================

def test_dynamic_space_ducking_recipes():
    std = DynamicSpaceDucker.get_recipe(SpaceDuckingMode.COMMERCIAL_STANDARD)
    assert std["duck_amount_db"] == -3.5
    assert std["attack_ms"] <= 5.0
    assert std["release_ms"] >= 300.0

    deep = DynamicSpaceDucker.get_recipe(SpaceDuckingMode.DEEP_BLOOM)
    assert deep["duck_amount_db"] == -5.0
    assert deep["release_ms"] >= 450.0


def test_dynamic_space_ducking_envelope():
    # Vocal sings from beat 4.0 to 12.0 and beat 16.0 to 24.0 in a 32-beat song
    vocal_ranges = [(4.0, 12.0), (16.0, 24.0)]
    points = DynamicSpaceDucker.calculate_space_ducking_envelope(
        vocal_ranges_beats=vocal_ranges,
        song_length_beats=32.0,
        mode=SpaceDuckingMode.COMMERCIAL_STANDARD,
        tempo=120.0
    )

    assert len(points) >= 6
    # At start beat 0.0, gain should be 1.0 (unity)
    assert points[0]["value"] == 1.0

    # During vocal phrase (e.g. around beat 6.0), gain is ducked
    mid_phrase_p = next((p for p in points if 4.0 < p["time"] < 12.0), None)
    assert mid_phrase_p is not None
    assert mid_phrase_p["gain_db"] < 0.0


def test_dynamic_space_ducking_device_config():
    mock_conn = DummyMockConnection()
    res = DynamicSpaceDucker.configure_space_ducking_device(
        conn=mock_conn,
        reverb_track_index=4,
        vocal_track_index=3,
        mode=SpaceDuckingMode.COMMERCIAL_STANDARD
    )
    assert res["status"] in ("CONFIGURED", "SIMULATED")


# =============================================================================
# 3. MODAL VOICE LEADING & BORROWED CHORDS TESTS
# =============================================================================

def test_modal_voice_leading_borrowed_chords():
    # Major Key modal borrowings in C Major (root_pc = 0):
    # Minor iv in C Major -> F minor (F, Ab, C)
    iv_chord = ModalVoiceLeadingEngine.calculate_borrowed_chord("C", "major", BorrowedChordType.MINOR_IV)
    assert iv_chord.name == "Fm"
    assert iv_chord.roman_numeral == "iv"
    assert iv_chord.is_borrowed is True

    # Flat-VI in C Major -> Ab Major (Ab, C, Eb)
    bvi_chord = ModalVoiceLeadingEngine.calculate_borrowed_chord("C", "major", BorrowedChordType.FLAT_VI)
    assert bvi_chord.name == "G#" or bvi_chord.name == "Ab" or "VI" in bvi_chord.roman_numeral

    # Minor Key borrowings in A Minor (root_pc = 9):
    # Dorian IV in A Minor -> D Major (D, F#, A)
    dorian_iv = ModalVoiceLeadingEngine.calculate_borrowed_chord("A", "minor", BorrowedChordType.DORIAN_IV)
    assert dorian_iv.name == "D"
    assert dorian_iv.roman_numeral == "IV"


def test_voice_leading_inversion_optimization():
    # Two chords far apart in root position: C Major [60, 64, 67] and F Major [53, 57, 60]
    c_maj = VoicedChord(name="C", roman_numeral="I", pitches=[60, 64, 67], root_pitch_class=0)
    f_maj = VoicedChord(name="F", roman_numeral="IV", pitches=[53, 57, 60], root_pitch_class=5)

    raw_prog = [c_maj, f_maj]
    optimized = ModalVoiceLeadingEngine.optimize_voice_leading(raw_prog)

    assert len(optimized) == 2
    # In 2nd inversion, F Major is [60, 65, 69] where note 60 (C) is common to both!
    dist = ModalVoiceLeadingEngine.calculate_voice_distance(optimized[0].pitches, optimized[1].pitches)
    # Distance should be smooth (<= 6 semitones total across 3 voices = avg <= 2 st)
    assert dist <= 6.0


def test_enrich_progression_with_borrowing():
    # Build enriched minor progression in F minor
    chords = ModalVoiceLeadingEngine.enrich_progression_with_borrowing(
        key_root="F",
        scale="natural_minor",
        inject_emotional_borrowing=True
    )
    assert len(chords) == 4
    # Check at least one chord is marked borrowed
    has_borrowed = any(c.is_borrowed for c in chords)
    assert has_borrowed is True


# =============================================================================
# 4. METRIC MODULATION & POLYRHYTHM ENGINE TESTS
# =============================================================================

def test_metric_modulation_level_configs():
    for lvl in range(1, 6):
        cfg = MetricModulationEngine.get_config(lvl)
        assert "name" in cfg
        assert "subdivisions" in cfg

    assert MetricModulationEngine.get_config(1)["has_triplets"] is False
    assert MetricModulationEngine.get_config(2)["has_triplets"] is True
    assert MetricModulationEngine.get_config(4)["has_quintuplets"] is True


def test_metric_modulation_roll_generation():
    # Level 1 straight roll (16th notes: 4 notes in 1 beat)
    roll_l1 = MetricModulationEngine.generate_metric_roll(target_beat=4.0, duration_beats=1.0, level=1)
    assert len(roll_l1) == 4

    # Level 2 commercial triplet roll (has 6 notes in 1 beat across 16th and 1/24 triplets)
    roll_l2 = MetricModulationEngine.generate_metric_roll(target_beat=4.0, duration_beats=1.0, level=2)
    assert len(roll_l2) >= 5

    # Level 4 odd grouping (quintuplets: 5 notes per beat)
    roll_l4 = MetricModulationEngine.generate_metric_roll(target_beat=4.0, duration_beats=1.0, level=4)
    assert len(roll_l4) == 5
    # Pitches on tail should include micro pitch descent
    assert any(n.pitch < 42 for n in roll_l4)


def test_metric_modulation_apply_to_pattern():
    # 8-bar basic pattern of 1/4 notes
    base_notes = [NoteEvent(pitch=42, start=float(b), duration=0.25, velocity=80) for b in range(32)]
    modulated = MetricModulationEngine.apply_metric_modulation_to_pattern(
        pattern_notes=base_notes,
        level=2,
        total_bars=8,
        seed=42
    )
    assert len(modulated) > len(base_notes)


# =============================================================================
# 5. COPILOT GUIDED SESSION INTEGRATION TESTS
# =============================================================================

def test_copilot_phase2_global_intercepts():
    session = CopilotGuidedSession()
    session.data["current_phase"] = "PHASE_6_COMPOSITION"
    session.data["key"] = "F"
    session.data["scale"] = "natural_minor"
    session.data["sections"] = [{"name": "Verse", "bars": 8}, {"name": "Chorus", "bars": 8}]
    mock_conn = DummyMockConnection()

    # 1. Ear Candy query
    resp_ec = CopilotInterceptRouter.intercept(session, mock_conn, "inyectar ear candy")
    assert resp_ec is not None
    assert resp_ec["status"] == "EAR_CANDY_SUMMARY"
    assert "events_count" in resp_ec

    # 2. Space Ducking query
    resp_sd = CopilotInterceptRouter.intercept(session, mock_conn, "reverbs duckeados")
    assert resp_sd is not None
    assert resp_sd["status"] == "SPACE_DUCKING_SUMMARY"

    # 3. Modal Harmony query
    resp_mh = CopilotInterceptRouter.intercept(session, mock_conn, "intercambio modal")
    assert resp_mh is not None
    assert resp_mh["status"] == "MODAL_HARMONY_SUMMARY"
    assert len(resp_mh["chords"]) == 4

    # 4. Metric Modulation query
    resp_mm = CopilotInterceptRouter.intercept(session, mock_conn, "modulacion metrica")
    assert resp_mm is not None
    assert resp_mm["status"] == "METRIC_MODULATION_SUMMARY"


def test_phase_8_space_ducking_integration():
    session = CopilotGuidedSession()
    session.data["current_phase"] = "PHASE_8_VOCAL_DUCKING"
    session.data["tracks"] = [
        {"index": 0, "name": "Kick Drums", "role": "DRUMS"},
        {"index": 1, "name": "Sub Bass", "role": "BASS"},
        {"index": 2, "name": "Lead Vocal", "role": "VOCALS"},
        {"index": 3, "name": "Reverb Return", "role": "FX"},
    ]
    mock_conn = DummyMockConnection()

    # Advance through Phase 8
    session._handle_phase_8_vocal_ducking(mock_conn, "opcion a")
    assert "space_ducking" in session.data
    assert "spectral_sidechain" in session.data
    assert session.data["space_ducking"]["recipe"]["duck_amount_db"] == -3.5
