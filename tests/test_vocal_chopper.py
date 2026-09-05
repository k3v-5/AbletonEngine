# tests/test_vocal_chopper.py
import pytest
from engine.vocal.chopper import (
    VocalChopStyle,
    VocalChopNote,
    VocalChopperEngine
)


class MockAdapter:
    def __init__(self):
        self.commands = []

    def send_command(self, cmd, params):
        self.commands.append((cmd, params))
        return {"status": "ok"}


def test_vocal_scale_pitches():
    pitches = VocalChopperEngine.get_scale_pitches(root="F", scale="minor", octave=5)
    assert len(pitches) >= 14
    # F5 is 77
    assert 77 in pitches


def test_vocal_hook_chops_generation():
    chops = VocalChopperEngine.generate_hook_chops(
        root="F",
        scale="minor",
        style=VocalChopStyle.MELODIC_HOOK,
        total_bars=4.0
    )
    assert len(chops) >= 12
    for c in chops:
        assert c.pitch > 0
        assert -1.0 <= c.pan <= 1.0
        assert 0 <= c.velocity <= 127


def test_vocal_stutter_and_call_response():
    stutters = VocalChopperEngine.generate_hook_chops(
        root="C",
        scale="major",
        style=VocalChopStyle.STUTTER_DROP,
        total_bars=2.0
    )
    assert len(stutters) >= 16

    call_resp = VocalChopperEngine.generate_hook_chops(
        root="G",
        scale="dorian",
        style=VocalChopStyle.CALL_AND_RESPONSE,
        total_bars=2.0
    )
    assert len(call_resp) >= 8


def test_vocal_pan_and_delay_automation():
    chops = VocalChopperEngine.generate_hook_chops(root="F", scale="minor", total_bars=2.0)
    pan_points = VocalChopperEngine.calculate_pan_automation(chops)
    delay_points = VocalChopperEngine.calculate_delay_send_automation(chops)

    assert len(pan_points) > 0
    assert len(delay_points) > 0
    for p in pan_points:
        assert -1.0 <= p["value"] <= 1.0


def test_vocal_generate_and_apply_adapter():
    adapter = MockAdapter()
    res = VocalChopperEngine.generate_and_apply_vocal_chops(
        conn=adapter,
        track_index=4,
        root="F",
        scale="minor",
        style="melodic_hook",
        total_bars=4.0
    )
    assert res["status"] == "SUCCESS"
    assert res["chops_count"] > 0
    assert res["pan_points_count"] > 0
    cmd_names = [c[0] for c in adapter.commands]
    assert "create_clip" in cmd_names
    assert "add_notes_to_clip" in cmd_names
    assert "create_arrangement_automation_envelope" in cmd_names
