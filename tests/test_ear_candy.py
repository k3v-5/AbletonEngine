# tests/test_ear_candy.py
import pytest
from engine.arrangement.fx.ear_candy import EarCandyEngine, EarCandyType
from engine.music.models import NoteEvent


def test_tape_stop_envelope():
    res = EarCandyEngine.generate_tape_stop(
        target_bar=17.0,
        duration_beats=1.0,
        curve_exp=2.8
    )

    assert "pitch_bend_points" in res
    assert "volume_points" in res

    p_pts = res["pitch_bend_points"]
    v_pts = res["volume_points"]

    # Drops pitch to -8192
    assert p_pts[-2]["value"] == pytest.approx(-8192.0, abs=10.0)
    # Drops volume to 0.0
    assert v_pts[-2]["value"] == pytest.approx(0.0, abs=0.01)
    # Resets on downbeat (time == 64.01)
    assert p_pts[-1]["value"] == 0.0
    assert v_pts[-1]["value"] == pytest.approx(0.85, abs=0.01)


def test_glitch_stutter_subdivisions():
    snare = NoteEvent(pitch=38, start=15.0, duration=1.0, velocity=90)
    stutter_events = EarCandyEngine.generate_glitch_stutter(snare, pattern="accelerating")

    # Accelerating stages generate 1 + 2 + 4 = 7 micro-hits
    assert len(stutter_events) == 7
    # Velocity should ramp up
    assert stutter_events[-1].velocity > stutter_events[0].velocity
    assert stutter_events[-1].accent is True


def test_pre_drop_vacuum():
    pts = EarCandyEngine.generate_pre_drop_vacuum(target_bar=33.0, silence_duration_beats=1.0)
    # Total 4 control points: baseline before, cut to 0, hold 0, restore
    assert len(pts) == 4
    assert pts[1]["value"] == 0.0
    assert pts[2]["value"] == 0.0
    assert pts[3]["value"] == 0.85
