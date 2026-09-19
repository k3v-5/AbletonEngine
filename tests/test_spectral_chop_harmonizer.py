# tests/test_spectral_chop_harmonizer.py
import pytest
import numpy as np
from engine.vocal.spectral_chop_harmonizer import SpectralChopHarmonizer


def test_fundamental_pitch_estimation_f3_and_a4():
    sr = 44100
    t = np.linspace(0, 0.4, int(sr * 0.4))

    # 1. Generate F3 tone (174.61 Hz)
    sine_f3 = np.sin(2 * np.pi * 174.61 * t)
    f3_res = SpectralChopHarmonizer.estimate_fundamental_pitch(sine_f3, sr=sr)
    assert f3_res["is_voiced"] is True
    assert f3_res["confidence"] > 0.85
    assert f3_res["note_name"] == "F3"
    assert f3_res["f0_hz"] == pytest.approx(174.6, abs=3.0)

    # 2. Generate A4 tone (440.0 Hz)
    sine_a4 = np.sin(2 * np.pi * 440.0 * t)
    a4_res = SpectralChopHarmonizer.estimate_fundamental_pitch(sine_a4, sr=sr)
    assert a4_res["is_voiced"] is True
    assert a4_res["note_name"] == "A4"
    assert a4_res["f0_hz"] == pytest.approx(440.0, abs=3.0)


def test_snap_to_scale_in_and_out_of_scale():
    # In F minor: F, G, Ab, Bb, C, Db, Eb
    # F3 is MIDI 53 -> In scale
    snap_f = SpectralChopHarmonizer.snap_to_scale(53.0, key="F", scale="minor")
    assert snap_f["in_scale"] is True
    assert snap_f["semitone_shift"] == 0
    assert snap_f["target_note"] == "F3"

    # F#3 is MIDI 54 -> Out of scale in F minor -> snaps to F3 (53) or G3 (55)
    snap_fsharp = SpectralChopHarmonizer.snap_to_scale(54.0, key="F", scale="minor")
    assert snap_fsharp["in_scale"] is False
    assert abs(snap_fsharp["semitone_shift"]) == 1
    assert snap_fsharp["target_note"] in ["F3", "G3"]


def test_generate_harmonic_intervals():
    # Root F3 (MIDI 53) in F minor
    intervals = SpectralChopHarmonizer.generate_harmonic_intervals(53, key="F", scale="minor")
    assert intervals["root"]["semitone_shift"] == 0
    assert intervals["root"]["note_name"] == "F3"

    # Minor 3rd (+3 semitones) -> G#3 / Ab3
    assert intervals["third"]["semitone_shift"] == 3
    assert intervals["third"]["note_name"] == "G#3"

    # Perfect 5th (+7 semitones) -> C4
    assert intervals["fifth"]["semitone_shift"] == 7
    assert intervals["fifth"]["note_name"] == "C4"

    # Octave up (+12 semitones) -> F4
    assert intervals["octave_up"]["semitone_shift"] == 12
    assert intervals["octave_up"]["note_name"] == "F4"

    # Octave down (-12 semitones) -> F2
    assert intervals["octave_down"]["semitone_shift"] == -12
    assert intervals["octave_down"]["note_name"] == "F2"


def test_create_buildup_stutter_pattern():
    pattern = SpectralChopHarmonizer.create_buildup_stutter_pattern(
        chop_path="vocal_chop_01.wav",
        start_beat=112.0,
        duration_beats=8.0,
        key="F",
        scale="minor"
    )

    assert len(pattern) >= 10
    # Must have pulse, 8th acceleration, 16th roll, and 32nd climax
    stages = [p["stage"] for p in pattern]
    assert "pulse" in stages
    assert "8th_acceleration" in stages
    assert "16th_roll" in stages
    assert "32nd_climax" in stages

    # Check pitch escalation
    climax_events = [p for p in pattern if p["stage"] == "32nd_climax"]
    assert any(c["pitch_shift"] == 12 for c in climax_events)


def test_create_drop_melodic_chops():
    chops = [
        {"file_path": "chop_root.wav", "text": "Hook 1"},
        {"file_path": "chop_third.wav", "text": "Hook 2"}
    ]
    melodic = SpectralChopHarmonizer.create_drop_melodic_chops(
        chops=chops,
        start_beat=128.0,
        length_bars=4
    )

    assert len(melodic) == 8 # 2 chops per bar * 4 bars
    roles = [m["role"] for m in melodic]
    assert "call_root" in roles
    assert "call_third" in roles
    assert "resp_fifth" in roles
    assert "resp_octave" in roles
