# tests/test_commercial_enhancements.py
"""
Comprehensive Unit & Integration Test Suite for Commercial Hit-Caliber Enhancements:
1. Hook Contour Engine (Hook Theory, Leap-Step, Vocal Range, Score)
2. Groove Pocket Engine (5-level parameterization, role push/pull, ghost note ratios)
3. Dynamic Spectral Sidechain Engine (Frequency-selective unmasking)
4. Tension Dynamics Engine (Dead air, stereo width collapse, gain dip)
5. Live Bus Submaster Architecture Engine (Non-destructive stem grouping)
6. Emotional Arc Director (Genre + Emotion inference, section inertia retention)
7. Copilot Guided Session Integration (Phase 8 spectral ducking and global query intercepts)
"""

import pytest
from engine.music.models import NoteEvent
from engine.music.melody.hook_contour import HookContourEngine, HookContourType, HookEvaluationReport
from engine.music.groove.pocket import GroovePocketEngine, POCKET_LEVEL_SCALERS, ROLE_MICRO_PUSH_PULL_MS
from engine.mix.spectral_sidechain import DynamicSpectralSidechainEngine
from engine.arrangement.transitions.tension_dynamics import TensionDynamicsEngine
from engine.mix.bus_architecture import LiveBusArchitectureEngine
from engine.arrangement.emotional_arc import EmotionalArcDirector, MusicalEmotion
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
# 1. HOOK CONTOUR ENGINE TESTS
# =============================================================================

def test_hook_contour_detection():
    # Arch melody: ascends to center, then resolves downward
    arch_notes = [
        NoteEvent(pitch=60, start=0.0, duration=1.0, velocity=90),
        NoteEvent(pitch=67, start=1.0, duration=1.0, velocity=100),
        NoteEvent(pitch=60, start=2.0, duration=1.0, velocity=85),
    ]
    assert HookContourEngine.detect_contour(arch_notes) == HookContourType.ARCH

    # Ascending Climax: starts low, climbs steadily
    climax_notes = [
        NoteEvent(pitch=55, start=0.0, duration=1.0, velocity=80),
        NoteEvent(pitch=62, start=1.0, duration=1.0, velocity=90),
        NoteEvent(pitch=72, start=2.0, duration=1.0, velocity=110),
    ]
    assert HookContourEngine.detect_contour(climax_notes) == HookContourType.ASCENDING_CLIMAX


def test_hook_evaluation_leap_step_rule():
    # Leap upward (+7 st from 60 to 67) followed by opposing downward step (-2 st to 65) -> Compliant
    valid_leap_notes = [
        NoteEvent(pitch=60, start=0.0, duration=1.0, velocity=90),
        NoteEvent(pitch=67, start=1.0, duration=1.0, velocity=100),
        NoteEvent(pitch=65, start=2.5, duration=1.0, velocity=90), # step down (-2)
        NoteEvent(pitch=60, start=4.0, duration=1.0, velocity=85),
    ]
    report = HookContourEngine.evaluate_hook(valid_leap_notes)
    assert report.leap_step_violations == 0

    # Leap upward (+7 st from 60 to 67) followed by continued leap upward (+5 st to 72) -> Violation
    violating_notes = [
        NoteEvent(pitch=60, start=0.0, duration=1.0, velocity=90),
        NoteEvent(pitch=67, start=1.0, duration=1.0, velocity=100),
        NoteEvent(pitch=72, start=2.0, duration=1.0, velocity=100), # leaps up again
        NoteEvent(pitch=60, start=3.0, duration=1.0, velocity=85),
    ]
    report_v = HookContourEngine.evaluate_hook(violating_notes)
    assert report_v.leap_step_violations > 0


def test_hook_vocal_range_confinement():
    # 24 semitones range (> 18)
    wide_notes = [
        NoteEvent(pitch=48, start=0.0, duration=1.0, velocity=90),
        NoteEvent(pitch=72, start=2.0, duration=1.0, velocity=100),
    ]
    report = HookContourEngine.evaluate_hook(wide_notes)
    assert report.vocal_range_semitones == 24
    assert not report.is_valid_commercial_hook
    assert any("Rango melódico excesivo" in r for r in report.recommendations)


def test_generate_hook_motif_commercial_compliance():
    # Generates standard commercial hook and evaluates it
    hook_notes = HookContourEngine.generate_hook_motif(key_root="F", scale="natural_minor", phrase_seed=42)
    assert len(hook_notes) >= 8
    report = HookContourEngine.evaluate_hook(hook_notes)
    assert report.is_valid_commercial_hook is True
    assert report.score >= 70.0
    assert report.vocal_range_semitones <= 18
    assert report.has_breathing_space is True


# =============================================================================
# 2. GROOVE POCKET ENGINE 5-LEVEL TESTS
# =============================================================================

def test_groove_pocket_levels():
    assert len(POCKET_LEVEL_SCALERS) == 5
    assert POCKET_LEVEL_SCALERS[1] < POCKET_LEVEL_SCALERS[2] < POCKET_LEVEL_SCALERS[5]
    assert POCKET_LEVEL_SCALERS[2] == 0.45 # Default commercial

    # Lazy snare, rushed hats, dragging 808
    assert ROLE_MICRO_PUSH_PULL_MS["SNARE"] > 0   # Lazy push (+8ms)
    assert ROLE_MICRO_PUSH_PULL_MS["HI_HATS"] < 0 # Rushed pull (-3ms)
    assert ROLE_MICRO_PUSH_PULL_MS["808"] > 0     # Dragging push (+4.5ms)


def test_groove_pocket_application():
    notes = [
        NoteEvent(pitch=38, start=1.0, duration=0.5, velocity=100), # Snare
        NoteEvent(pitch=42, start=1.5, duration=0.25, velocity=80),  # Hat
    ]
    # Level 1 subtle
    subtle_notes = GroovePocketEngine.apply_pocket_by_level(notes, role="SNARE", level=1, bpm=120.0)
    # Level 5 extreme
    intense_notes = GroovePocketEngine.apply_pocket_by_level(notes, role="SNARE", level=5, bpm=120.0)
    # Level 5 should have greater micro-shift than level 1
    shift_subtle = abs(subtle_notes[0].start - 1.0)
    shift_intense = abs(intense_notes[0].start - 1.0)
    assert shift_intense > shift_subtle


def test_ghost_note_dynamic_ratio_clamp():
    # Ghost note ratio must be strictly between 35% and 45% of peak accent
    clamped_low = GroovePocketEngine.clamp_ghost_note_velocity(accent_velocity=100, candidate_velocity=10)
    assert clamped_low >= 35
    clamped_high = GroovePocketEngine.clamp_ghost_note_velocity(accent_velocity=100, candidate_velocity=80)
    assert clamped_high <= 45


# =============================================================================
# 3. DYNAMIC SPECTRAL SIDECHAIN ENGINE TESTS
# =============================================================================

def test_dynamic_spectral_sidechain_recipes():
    kb = DynamicSpectralSidechainEngine.calculate_kick_bass_carving(kick_freq_hz=52.0)
    assert kb["center_freq_hz"] == 52.0
    assert kb["target_cut_db"] < 0

    vm = DynamicSpectralSidechainEngine.calculate_vocal_music_carving()
    assert 1000.0 <= vm["center_freq_hz"] <= 3500.0
    assert vm["target_cut_db"] < 0


def test_dynamic_spectral_sidechain_simulated_and_live():
    mock_conn = DummyMockConnection()
    res = DynamicSpectralSidechainEngine.configure_kick_bass_spectral_carving(
        conn=mock_conn,
        kick_track_idx=0,
        bass_track_idx=1,
        kick_freq_hz=55.0
    )
    assert res["status"] in ("CONFIGURED", "SIMULATED")
    assert res["kick_track_idx"] == 0
    assert res["bass_track_idx"] == 1


# =============================================================================
# 4. TENSION DYNAMICS ENGINE TESTS
# =============================================================================

def test_tension_dynamics_dead_air():
    # 8-bar build ends at beat 32.0. Dead air should be before drop.
    dead_air = TensionDynamicsEngine.calculate_dead_air_window(drop_start_beat=32.0, duration_beats=1.0)
    assert dead_air["silence_start_beat"] == 31.0
    assert dead_air["silence_end_beat"] == 32.0
    assert dead_air["cut_reverb_decay"] is True


def test_tension_dynamics_stereo_narrowing():
    # Collapses to 60% stereo during buildup, explodes to 100% on drop
    points = TensionDynamicsEngine.calculate_stereo_narrowing_automation(
        build_start_beat=16.0,
        drop_start_beat=32.0,
        collapsed_width_percent=60.0
    )
    assert len(points) >= 3
    # Check drop impact point returns to 1.0 (100%)
    drop_point = next((p for p in points if p["time"] == 32.0), None)
    assert drop_point is not None
    assert drop_point["value"] == 1.0


def test_tension_dynamics_predrop_gain_dip():
    dip_points = TensionDynamicsEngine.calculate_predrop_gain_dip(drop_start_beat=32.0, dip_db=-1.2)
    assert len(dip_points) >= 3
    # Drop impact restores to 0.0 dB
    final_p = dip_points[-1]
    assert final_p["time"] == 32.0
    assert final_p["gain_db"] == 0.0


# =============================================================================
# 5. LIVE BUS SUBMASTER ARCHITECTURE TESTS
# =============================================================================

def test_bus_architecture_topology_analysis():
    tracks = [
        {"index": 0, "name": "Kick 909", "role": "KICK"},
        {"index": 1, "name": "Snare Trap", "role": "SNARE"},
        {"index": 2, "name": "Sub 808", "role": "808"},
        {"index": 3, "name": "Piano Rhodes", "role": "KEYS"},
        {"index": 4, "name": "Warm Strings", "role": "PAD"},
        {"index": 5, "name": "Lead Vocal", "role": "VOCALS"},
        {"index": 6, "name": "Riser FX", "role": "FX"},
    ]
    analysis = LiveBusArchitectureEngine.analyze_topology(tracks)
    assert analysis["status"] == "TOPOLOGY_ANALYZED"
    buses = analysis["buses"]
    assert "DRUMS BUS" in buses
    assert "BASS BUS" in buses
    assert "SYNTHS BUS" in buses
    assert "PADS BUS" in buses
    assert "VOCALS BUS" in buses
    assert "FX BUS" in buses

    # Non-destructive check: all original 7 tracks are preserved
    mapped_count = sum(len(trks) for trks in buses.values())
    assert mapped_count == 7


def test_bus_architecture_deployment_nondestructive():
    tracks = [
        {"index": 0, "name": "Kick", "role": "DRUMS"},
        {"index": 1, "name": "Bass", "role": "BASS"},
    ]
    mock_conn = DummyMockConnection()
    res = LiveBusArchitectureEngine.deploy_submix_buses_nondestructive(conn=mock_conn, tracks=tracks)
    assert res["status"] in ("SUCCESS", "SIMULATED")
    assert res["deployed_buses_count"] >= 2


# =============================================================================
# 6. EMOTIONAL ARC DIRECTOR TESTS
# =============================================================================

def test_emotion_inference_rules():
    # Trap in minor -> DARK_AGGRESSIVE
    e_trap = EmotionalArcDirector.infer_emotion(genre="trap", key="F", scale="natural_minor")
    assert e_trap == MusicalEmotion.DARK_AGGRESSIVE

    # Reggaeton -> GROOVY_SENSUAL
    e_reg = EmotionalArcDirector.infer_emotion(genre="reggaeton", key="C", scale="natural_minor")
    assert e_reg == MusicalEmotion.GROOVY_SENSUAL

    # EDM / Dance -> EUPHORIC_ANTHEMIC
    e_edm = EmotionalArcDirector.infer_emotion(genre="edm", key="G", scale="major")
    assert e_edm == MusicalEmotion.EUPHORIC_ANTHEMIC

    # Lofi / Chillout -> NOSTALGIC_CHILL
    e_lofi = EmotionalArcDirector.infer_emotion(genre="lofi", key="D", scale="dorian")
    assert e_lofi == MusicalEmotion.NOSTALGIC_CHILL


def test_emotional_arc_verse_2_inertia_retention():
    sections = [
        {"name": "Intro", "bars": 8},
        {"name": "Verse 1", "bars": 16},
        {"name": "Chorus 1", "bars": 8},
        {"name": "Verse 2", "bars": 16}, # Must retain momentum
        {"name": "Chorus 2", "bars": 8},
        {"name": "Outro", "bars": 8},
    ]
    arc = EmotionalArcDirector.orchestrate_arc(
        sections=sections,
        genre="trap",
        key="F",
        scale="natural_minor"
    )
    assert len(arc) == 6
    v1 = next(s for s in arc if s["name"] == "Verse 1")
    v2 = next(s for s in arc if s["name"] == "Verse 2")

    # Verse 2 target energy must be higher than Verse 1 to maintain hit inertia
    assert v2["target_energy"] > v1["target_energy"]
    assert len(v2["inertia_keep_roles"]) > 0
    assert "808" in v2["inertia_keep_roles"] or "BASS" in v2["inertia_keep_roles"]


# =============================================================================
# 7. COPILOT GUIDED SESSION INTEGRATION TESTS
# =============================================================================

def test_copilot_global_intercepts():
    session = CopilotGuidedSession()
    session.data["current_phase"] = "PHASE_2_SECTIONS"
    session.data["genre"] = "trap"
    session.data["key"] = "F"
    session.data["scale"] = "natural_minor"
    session.data["sections"] = [{"name": "Intro", "bars": 8}, {"name": "Drop", "bars": 16}]
    session.data["tracks"] = [{"index": 0, "name": "Kick", "role": "DRUMS"}]

    mock_conn = DummyMockConnection()

    # 1. Emotional Arc query intercept
    resp_arc = CopilotInterceptRouter.intercept(session, mock_conn, "ver arco emocional")
    assert resp_arc is not None
    assert resp_arc["status"] == "EMOTIONAL_ARC_SUMMARY"
    assert "DARK_AGGRESSIVE" in resp_arc["emotion"]

    # 2. Bus Architecture query intercept
    resp_bus = CopilotInterceptRouter.intercept(session, mock_conn, "ver arquitectura de buses")
    assert resp_bus is not None
    assert resp_bus["status"] == "BUS_ARCHITECTURE_SUMMARY"

    # 3. Hook Theory query intercept
    resp_hook = CopilotInterceptRouter.intercept(session, mock_conn, "evaluar gancho")
    assert resp_hook is not None
    assert resp_hook["status"] == "HOOK_EVALUATION_REPORT"
    assert "hook_report" in resp_hook


def test_phase_8_dynamic_spectral_sidechain_wiring():
    session = CopilotGuidedSession()
    session.data["current_phase"] = "PHASE_8_VOCAL_DUCKING"
    session.data["phase_index"] = 8
    session.data["tracks"] = [
        {"index": 0, "name": "Drums Kick", "role": "DRUMS"},
        {"index": 1, "name": "Sub Bass", "role": "BASS"},
        {"index": 2, "name": "Keys Piano", "role": "KEYS"},
        {"index": 3, "name": "Lead Vocal", "role": "VOCALS"},
    ]
    mock_conn = DummyMockConnection()

    # Advance through Phase 8 with Standard Ducking
    res = session._handle_phase_8_vocal_ducking(mock_conn, "opcion a")
    assert "spectral_sidechain" in session.data
    spectral_sc = session.data["spectral_sidechain"]
    assert "kick_bass" in spectral_sc
    assert "vocal_music" in spectral_sc
