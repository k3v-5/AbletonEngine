# tests/test_commercial_phase3_dialogue_and_acoustics.py
"""
Comprehensive test suite for Phase 3 Commercial Enhancements in AbletonEngine:
1. Antiphonal Dialogue Engine (Core Multitrack Call & Response)
2. Phase Correlation Sentinel (Low-End Polarity & Transient Alignment)
3. Smart Resonance Carver (Real-Time Dynamic Anti-Masking)
4. Multi-Layer Crossover Stacker (Psychoacoustic 3-Band Separation)
5. Vocal Harmony & Stereo Spread Engine
6. Adaptive Drum Fill Generator (4-Layer Frequency Turnarounds & Kick Dropout)
7. Micro-Stutter & Tape Stop Engine (Music Bus Deceleration with Dry Drum Fills)
8. Copilot Guided Session Phase 6, 7, 8 & Intercept Router Integrations
"""

import pytest
from typing import Dict, Any, List

from engine.music.antiphonal_dialogue import AntiphonalDialogueEngine, DialogueResponseConfig
from engine.mix.phase_correlation_sentinel import PhaseCorrelationSentinel
from engine.mix.smart_resonance_carver import SmartResonanceCarver
from engine.sound.crossover_stacking import MultiLayerCrossoverStacker
from engine.music.vocal_harmony import VocalHarmonyEngine
from engine.music.drums.adaptive_fill import AdaptiveDrumFillGenerator
from engine.arrangement.transitions.micro_stutter import MicroStutterEngine
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.production.copilot.phases.phase_6.handler import Phase6CompositionHandler


class MockAbletonAdapter:
    """Mock connection for Ableton Live OSC commands."""
    def __init__(self):
        self.commands = []

    def send_command(self, cmd: str, params: Dict[str, Any] = None):
        self.commands.append({"command": cmd, "params": params or {}})
        if cmd == "get_session_info":
            return {"status": "SUCCESS", "result": {"track_count": 8, "tempo": 120.0}}
        if cmd == "get_track_info":
            return {"status": "SUCCESS", "result": {"name": f"Track {params.get('track_index', 0)}"}}
        return {"status": "SUCCESS"}


# =============================================================================
# 1. Antiphonal Dialogue Engine Tests (Core Call & Response)
# =============================================================================

def test_antiphonal_dialogue_eligible_filtering():
    """Verifies strict filtering of eligible responder roles vs ineligible rhythm/lead roles."""
    tracks = [
        {"index": 0, "name": "Lead Vocal", "role": "VOCALS"},
        {"index": 1, "name": "Kick", "role": "KICK"},
        {"index": 2, "name": "Main Drums", "role": "DRUMS"},
        {"index": 3, "name": "Sub Bass", "role": "SUB_BASS"},
        {"index": 4, "name": "Electric Piano", "role": "KEYS"},
        {"index": 5, "name": "Brass Stabs", "role": "BRASS"},
        {"index": 6, "name": "Arp Pluck", "role": "PLUCK"},
        {"index": 7, "name": "Riser FX", "role": "FX"}
    ]
    responders = AntiphonalDialogueEngine.filter_eligible_responders(tracks, focal_track_index=0)
    responder_roles = [r.role for r in responders]

    assert "KEYS" in responder_roles
    assert "BRASS" in responder_roles
    assert "PLUCK" in responder_roles

    # Strictly excluded roles
    assert "KICK" not in responder_roles
    assert "DRUMS" not in responder_roles
    assert "SUB_BASS" not in responder_roles
    assert "FX" not in responder_roles
    assert "VOCALS" not in responder_roles


def test_antiphonal_dialogue_rest_window_detection():
    """Verifies focal rest windows are accurately detected with safety guard margins."""
    focal_notes = [
        {"pitch": 64, "start_time": 0.0, "duration": 2.0},  # Ends at beat 2.0
        # Gap of 2.0 beats (beats 2.0 to 4.0)
        {"pitch": 67, "start_time": 4.0, "duration": 2.0},  # Ends at beat 6.0
        # Gap of 4.0 beats (beats 6.0 to 10.0)
        {"pitch": 65, "start_time": 10.0, "duration": 2.0}  # Ends at beat 12.0
    ]
    rest_windows = AntiphonalDialogueEngine.detect_focal_rest_windows(focal_notes, total_beats=16.0, min_rest_beats=1.0)
    assert len(rest_windows) >= 2

    # Check that safety guard margins are applied
    for win in rest_windows:
        assert win["duration"] >= 0.75
        assert win["end_beat"] > win["start_beat"]


def test_antiphonal_dialogue_rotational_dispatch():
    """Verifies that dialogue responses rotate strictly between eligible instruments without collision."""
    tracks = [
        {"index": 0, "name": "Lead Vox", "role": "VOCALS"},
        {"index": 1, "name": "Rhodes", "role": "KEYS"},
        {"index": 2, "name": "Horn Hit", "role": "BRASS"},
        {"index": 3, "name": "Guitar Lick", "role": "GUITAR"}
    ]
    # Focal phrase with 3 rest gaps
    focal_notes = [
        {"pitch": 60, "start_time": 0.0, "duration": 1.5},
        {"pitch": 64, "start_time": 4.0, "duration": 1.5},
        {"pitch": 67, "start_time": 8.0, "duration": 1.5},
        {"pitch": 65, "start_time": 12.0, "duration": 1.5}
    ]
    dialogue = AntiphonalDialogueEngine.orchestrate_rotational_dialogue(
        tracks=tracks,
        focal_track_index=0,
        focal_notes=focal_notes,
        total_beats=16.0,
        scale_root_pitch=60
    )

    assert dialogue["status"] == "SUCCESS"
    assert dialogue["policy"] == "ROTATIONAL"
    events = dialogue["dialogue_events"]
    assert len(events) >= 3

    # Check rotational assignment (Track 1 -> Track 2 -> Track 3 ...)
    assigned_tracks = [e["responder_track"] for e in events]
    assert assigned_tracks[0] == 1
    assert assigned_tracks[1] == 2
    assert assigned_tracks[2] == 3

    # Check responder notes stay strictly within their rest window
    for ev in events:
        w_start = ev["window_start"]
        w_end = ev["window_end"]
        resp_trk_notes = dialogue["dialogue_matrix"][ev["responder_track"]]
        for n in resp_trk_notes:
            if w_start <= n["start_time"] <= w_end:
                assert n["start_time"] >= w_start
                assert (n["start_time"] + n["duration"]) <= (w_end + 0.05)


# =============================================================================
# 2. Phase Correlation Sentinel Tests (Low-End Polarity & Alignment)
# =============================================================================

def test_phase_correlation_destructive_interference():
    """Verifies that negative phase correlation triggers 180 polarity flip recommendation."""
    tracks = [
        {"index": 0, "name": "Kick Sub", "role": "KICK"},
        {"index": 1, "name": "808 Bass", "role": "BASS"}
    ]
    # Anti-phase synthetic signals
    import math
    signal_kick = [math.sin(2 * math.pi * 50 * (i / 1000.0)) for i in range(200)]
    signal_bass = [-math.sin(2 * math.pi * 50 * (i / 1000.0)) for i in range(200)]  # Inverted

    audit = PhaseCorrelationSentinel.audit_kick_bass_coherence(
        tracks,
        sub_sample_kick=signal_kick,
        sub_sample_bass=signal_bass
    )

    assert audit["status"] == "DESTRUCTIVE_INTERFERENCE"
    assert audit["correlation_coefficient"] < -0.80
    assert audit["directives"]["invert_polarity_180"] is True
    assert audit["directives"]["bass_mono_enabled"] is True


def test_phase_correlation_coherent_alignment():
    """Verifies that in-phase signals pass without polarity invert."""
    tracks = [
        {"index": 0, "name": "Kick", "role": "KICK"},
        {"index": 1, "name": "Sub Bass", "role": "BASS"}
    ]
    signal = [0.8 for _ in range(50)]
    audit = PhaseCorrelationSentinel.audit_kick_bass_coherence(
        tracks,
        sub_sample_kick=signal,
        sub_sample_bass=signal
    )
    assert audit["status"] == "COHERENT"
    assert audit["correlation_coefficient"] > 0.80
    assert audit["directives"]["invert_polarity_180"] is False


# =============================================================================
# 3. Smart Resonance Carver Tests (Real-Time Anti-Masking)
# =============================================================================

def test_smart_resonance_carver_clash_detection():
    """Verifies that overlapping role pairs receive complementary dynamic notches."""
    tracks = [
        {"index": 0, "name": "Punch Kick", "role": "KICK"},
        {"index": 1, "name": "Sub Bassline", "role": "BASS"},
        {"index": 2, "name": "Lead Vocal", "role": "VOCALS"},
        {"index": 3, "name": "Synth Lead", "role": "LEAD"}
    ]
    carve_audit = SmartResonanceCarver.audit_session_resonances(tracks)
    clashes = carve_audit["detected_clashes"]
    clash_pairs = [c["pair"] for c in clashes]

    assert "Kick / Bass" in clash_pairs
    assert "Vocals / Lead" in clash_pairs

    # Verify Kick/Bass notch frequency (~52-60 Hz)
    kb_clash = next(c for c in clashes if c["pair"] == "Kick / Bass")
    assert 40.0 <= kb_clash["center_freq_hz"] <= 80.0

    # Verify Vocals/Lead notch frequency (~2500-3500 Hz)
    vl_clash = next(c for c in clashes if c["pair"] == "Vocals / Lead")
    assert 2000.0 <= vl_clash["center_freq_hz"] <= 4000.0


# =============================================================================
# 4. Multi-Layer Crossover Stacker Tests (3-Band Psychoacoustic Split)
# =============================================================================

def test_multilayer_crossover_stacker_bands():
    """Verifies 3-band crossover architecture (Sub Mono <90Hz, Body 90-1200Hz, Air >1200Hz Wide)."""
    split_plan = MultiLayerCrossoverStacker.create_crossover_split(source_track_name="Heavy Reeses Bass")
    layers = split_plan["layers"]

    assert len(layers) == 3
    sub_layer = next(l for l in layers if l["layer_id"] == "SUB")
    body_layer = next(l for l in layers if l["layer_id"] == "BODY")
    air_layer = next(l for l in layers if l["layer_id"] == "AIR")

    # Sub: strictly mono and low-passed
    assert sub_layer["crossover_lp_hz"] <= 95.0
    assert sub_layer["stereo_width"] == 0.0

    # Body: 90 - 1200 Hz
    assert body_layer["crossover_hp_hz"] >= 85.0
    assert body_layer["crossover_lp_hz"] <= 1250.0

    # Air: high-passed and wide
    assert air_layer["crossover_hp_hz"] >= 1150.0
    assert air_layer["stereo_width"] >= 0.85


# =============================================================================
# 5. Vocal Harmony Engine Tests
# =============================================================================

def test_vocal_harmony_stereo_stack():
    """Verifies generation of High (60L) and Low (60R) vocal harmonies with micro-timing."""
    lead_notes = [
        {"pitch": 60, "start_time": 0.0, "duration": 1.0, "velocity": 100},
        {"pitch": 64, "start_time": 1.0, "duration": 1.0, "velocity": 105},
        {"pitch": 67, "start_time": 2.0, "duration": 1.0, "velocity": 98}
    ]
    harmony_stack = VocalHarmonyEngine.generate_vocal_harmony_stack(
        lead_notes=lead_notes,
        scale_root_pitch=60,
        bpm=120.0
    )

    high_notes = harmony_stack["high_harmony_notes"]
    low_notes = harmony_stack["low_harmony_notes"]

    assert len(high_notes) == 3
    assert len(low_notes) == 3

    # High harmony should be higher in pitch and panned Left (-0.60)
    for hn, ln, orig in zip(high_notes, low_notes, lead_notes):
        assert hn["pitch"] > orig["pitch"]
        assert hn["pan"] <= -0.50
        assert ln["pitch"] < orig["pitch"]
        assert ln["pan"] >= 0.50


# =============================================================================
# 6. Adaptive Drum Fill Generator Tests
# =============================================================================

def test_adaptive_drum_fill_layers_and_kick_dropout():
    """Verifies 4-layer turnaround drum fills and kick dropout window on turnaround bars."""
    fill = AdaptiveDrumFillGenerator.generate_turnaround_fill(
        section_length_beats=32.0,
        fill_duration_beats=4.0,
        genre="TRAP",
        bpm=140.0
    )

    assert fill["status"] == "FILL_GENERATED"
    assert fill["start_beat"] == 28.0
    assert fill["duration_beats"] == 4.0
    assert fill["note_count"] >= 8

    # Kick dropout window must cover the fill duration
    kd_start, kd_end = fill["kick_dropout_window"]
    assert kd_start == 28.0
    assert kd_end == 32.0

    # Ensure tuned toms or snare rolls are present
    pitches = [n["pitch"] for n in fill["fill_notes"]]
    assert any(p in [38, 40] for p in pitches)  # Snares
    assert any(p in [41, 43, 45, 47, 48, 55] for p in pitches)  # Toms / Splash


# =============================================================================
# 7. Micro-Stutter & Tape Stop Engine Tests (Option A: Synths Only)
# =============================================================================

def test_micro_stutter_tape_stop_option_a_scope():
    """Verifies tape stop deceleration scoped exclusively to music bus (Option A)."""
    tape_stop = MicroStutterEngine.generate_tape_stop_envelope(
        pre_drop_beat=32.0,
        stop_duration_beats=2.0,
        pitch_drop_semitones=-24.0,
        preserve_drum_fills=True
    )

    assert tape_stop["status"] == "TAPE_STOP_GENERATED"
    assert tape_stop["scope"] == "MUSIC_BUS_ONLY"
    assert tape_stop["preserve_drum_fills"] is True
    assert tape_stop["start_beat"] == 30.0
    assert tape_stop["drop_beat"] == 32.0

    # Check pitch envelope drops down to -24 semitones
    pitch_env = tape_stop["pitch_envelope"]
    assert pitch_env[0]["value"] == 0.0
    assert pitch_env[-2]["value"] <= -20.0  # Decelerated right before drop
    assert pitch_env[-1]["value"] == 0.0   # Instant reset at drop impact


# =============================================================================
# 8. Copilot Guided Session & Phase Integrations
# =============================================================================

def test_phase_6_commercial_enrichments_pass():
    """Verifies apply_commercial_arrangement_enrichments populates session with Call & Response and fills."""
    session = CopilotGuidedSession()
    conn = MockAbletonAdapter()

    session.data["tracks"] = [
        {"index": 0, "name": "Vocal", "role": "VOCALS", "notes": [{"pitch": 64, "start_time": 0.0, "duration": 1.5}]},
        {"index": 1, "name": "Electric Piano", "role": "KEYS", "notes_count": 0},
        {"index": 2, "name": "Drums", "role": "DRUMS", "notes_count": 0}
    ]
    session.data["sections"] = [{"name": "Verse", "bars": 8}]
    session.data["key"] = "C"
    session.data["scale"] = "major"

    enrichments = Phase6CompositionHandler.apply_commercial_arrangement_enrichments(session, conn)

    assert "antiphonal_dialogue" in enrichments
    assert "adaptive_drum_fills" in enrichments
    assert "vocal_harmonies" in enrichments

    assert "antiphonal_dialogue" in session.data
    assert "adaptive_drum_fills" in session.data
    assert "vocal_harmonies" in session.data

    # Responder track should have received notes
    keys_trk = next(t for t in session.data["tracks"] if t["role"] == "KEYS")
    assert keys_trk.get("notes_count", 0) > 0


def test_copilot_global_intercepts_commercial_enhancements():
    """Verifies all 7 commercial enhancement conversational queries in CopilotGuidedSession."""
    session = CopilotGuidedSession()
    session.data["tracks"] = [
        {"index": 0, "name": "Kick", "role": "KICK"},
        {"index": 1, "name": "Bass", "role": "BASS"},
        {"index": 2, "name": "Keys", "role": "KEYS"},
        {"index": 3, "name": "Vocals", "role": "VOCALS"}
    ]

    # 1. Antiphonal Dialogue
    res_dialogue = session.handle_input("ver call and response")
    assert res_dialogue["status"] == "ANTIPHONAL_DIALOGUE_SUMMARY"
    assert "ROTATIONAL" in res_dialogue["policy"]

    # 2. Phase Correlation Sentinel
    res_phase = session.handle_input("alinear fase")
    assert res_phase["status"] == "PHASE_CORRELATION_SUMMARY"
    assert "correlation_coefficient" in res_phase["audit"]

    # 3. Smart Resonance Carver
    res_carver = session.handle_input("ver anti enmascaramiento")
    assert res_carver["status"] == "RESONANCE_CARVER_SUMMARY"

    # 4. Crossover Stacking
    res_cross = session.handle_input("ver crossover stacker")
    assert res_cross["status"] == "CROSSOVER_STACKING_SUMMARY"

    # 5. Vocal Harmonies
    res_harm = session.handle_input("generar armonias vocales")
    assert res_harm["status"] == "VOCAL_HARMONY_SUMMARY"

    # 6. Adaptive Drum Fills
    res_fills = session.handle_input("ver fills adaptativos")
    assert res_fills["status"] == "ADAPTIVE_DRUM_FILLS_SUMMARY"

    # 7. Micro-Stutter & Tape Stop
    res_tape = session.handle_input("ver tape stop")
    assert res_tape["status"] == "MICRO_STUTTER_SUMMARY"
    assert "tape_stop" in res_tape
