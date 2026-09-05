# tests/test_transition_risers.py
import pytest
from engine.arrangement.transitions.risers import (
    SweepFilterType,
    TransitionRisersEngine
)


class MockAdapter:
    def __init__(self):
        self.commands = []

    def send_command(self, cmd, params):
        self.commands.append((cmd, params))
        return {"status": "ok"}


def test_filter_sweep_generation():
    points = TransitionRisersEngine.generate_filter_sweep(
        target_bar=33.0,
        duration_bars=2.0,
        sweep_type=SweepFilterType.LOW_PASS_RISE,
        min_freq=300.0,
        max_freq=18000.0
    )
    assert len(points) >= 32
    assert points[0]["value"] >= 250.0
    assert points[-1]["value"] == 18000.0
    # Values should be monotonically increasing
    vals = [p["value"] for p in points[:-1]]
    assert vals[-1] > vals[0]


def test_noise_pitch_riser_curves():
    res = TransitionRisersEngine.generate_noise_pitch_riser(
        target_bar=17.0,
        duration_bars=2.0
    )
    assert "volume_envelope" in res
    assert "pitch_bend_envelope" in res
    assert len(res["volume_envelope"]) > 0
    assert len(res["pitch_bend_envelope"]) > 0

    # Max pitch bend should reach near 8191
    max_pitch = max(p["value"] for p in res["pitch_bend_envelope"])
    assert max_pitch > 8000.0


def test_procedural_snare_roll():
    notes = TransitionRisersEngine.generate_procedural_snare_roll(
        target_bar=33.0,
        duration_bars=1.0,
        snare_pitch=38
    )
    assert len(notes) >= 15
    for n in notes:
        assert n.pitch == 38
        assert n.duration > 0.0
        assert 0 < n.velocity <= 127

    # Velocities should ramp up
    assert notes[-1].velocity > notes[0].velocity


def test_apply_transition_riser_adapter():
    adapter = MockAdapter()
    res = TransitionRisersEngine.apply_transition_riser(
        conn=adapter,
        track_index=13,
        target_bar=33.0,
        duration_bars=2.0
    )
    assert res["status"] == "SUCCESS"
    assert res["sweep_points_count"] > 0
    assert res["snare_notes_count"] > 0
    cmd_names = [c[0] for c in adapter.commands]
    assert "create_arrangement_automation_envelope" in cmd_names
    assert "add_notes_to_clip" in cmd_names
