# tests/test_impacts_downlifters.py
import pytest
from engine.arrangement.impacts.downlifters import (
    ImpactType,
    DownlifterCurve,
    ImpactEngine,
)


class MockConnection:
    def __init__(self):
        self.commands = []

    def send_command(self, cmd: str, params: dict):
        self.commands.append((cmd, params))
        return {"status": "ok"}


def test_downlifter_filter_decay():
    env = ImpactEngine.generate_downlifter_sweep(
        start_bar=1.0,
        duration_bars=4.0,
        cutoff_start=20000.0,
        cutoff_end=150.0,
        curve=DownlifterCurve.EXPONENTIAL,
        resolution_steps=16,
    )
    assert env.impact_type == ImpactType.DOWNLIFTER_NOISE
    assert len(env.cutoff_points) == 17
    # First point should start near 20kHz
    assert env.cutoff_points[0][1] >= 19000.0
    # Last point should taper down towards 150Hz
    assert env.cutoff_points[-1][1] <= 1200.0
    # Volume points should decay
    assert env.volume_points[0][1] > env.volume_points[-1][1]


def test_sub_boom_pitch_drop():
    env = ImpactEngine.generate_sub_boom(
        target_bar=1.0,
        duration_beats=4.0,
        root_pitch=36,
    )
    assert env.impact_type == ImpactType.SUB_BOOM_DROP
    assert len(env.midi_notes) == 1
    assert env.midi_notes[0]["pitch"] == 36
    # Pitch bend should start high and drop
    assert len(env.pitch_bend_points) > 0
    assert env.pitch_bend_points[0][1] > env.pitch_bend_points[-1][1]


def test_reverse_cymbal_swell_with_silence_vacuum():
    env = ImpactEngine.generate_reverse_cymbal_swell(
        target_bar=9.0,
        duration_bars=2.0,
        pre_impact_gap_beats=0.05,
    )
    assert env.impact_type == ImpactType.REVERSE_CYMBAL_SWELL
    assert len(env.volume_points) > 0
    # Last point before drop must be 0.0 for vacuum effect
    assert env.volume_points[-1][1] == 0.0
    assert env.volume_points[-2][1] == 0.0


def test_apply_impact_live_adapter():
    conn = MockConnection()
    res = ImpactEngine.apply_impact_to_live(
        conn=conn,
        track_index=13,
        impact_type=ImpactType.SUB_BOOM_DROP,
        target_bar=33.0,
        duration_bars=2.0,
    )
    assert res["status"] == "success"
    cmd_names = [c[0] for c in conn.commands]
    assert "create_clip" in cmd_names
    assert "add_notes_to_clip" in cmd_names
