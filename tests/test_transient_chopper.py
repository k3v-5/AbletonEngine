# tests/test_transient_chopper.py
import pytest
from engine.audio.chopper.transient import (
    BreakPatternStyle,
    TransientSlice,
    TransientBreakChopper
)


class MockAdapter:
    def __init__(self):
        self.commands = []

    def send_command(self, cmd, params):
        self.commands.append((cmd, params))
        return {"status": "ok"}


def test_slice_generation():
    slices = TransientBreakChopper.generate_slices(total_bars=2.0, subdivisions_per_bar=8)
    assert len(slices) == 16
    roles = {s.role_guess for s in slices}
    assert "kick" in roles
    assert "snare" in roles


def test_resequence_amen_shuffle():
    slices = TransientBreakChopper.generate_slices(total_bars=2.0)
    notes = TransientBreakChopper.resequence_break(
        slices=slices,
        style=BreakPatternStyle.AMEN_SHUFFLE,
        bars_out=4.0
    )
    assert len(notes) > 16
    for n in notes:
        assert 36 <= n.pitch <= 52
        assert n.duration > 0.0
        assert n.velocity > 0


def test_resequence_half_time():
    slices = TransientBreakChopper.generate_slices(total_bars=2.0)
    notes = TransientBreakChopper.resequence_break(
        slices=slices,
        style=BreakPatternStyle.HALF_TIME_BOUNCE,
        bars_out=2.0
    )
    assert len(notes) > 0


def test_resequence_jungle_dnb():
    slices = TransientBreakChopper.generate_slices(total_bars=2.0)
    notes = TransientBreakChopper.resequence_break(
        slices=slices,
        style=BreakPatternStyle.JUNGLE_DNB_FAST,
        bars_out=4.0
    )
    assert len(notes) > 0


def test_chop_and_resequence_adapter():
    adapter = MockAdapter()
    res = TransientBreakChopper.chop_and_resequence(
        conn=adapter,
        track_index=13,
        style="amen_shuffle",
        bars_out=4.0
    )
    assert res["status"] == "SUCCESS"
    assert res["notes_generated"] > 0
    cmd_names = [c[0] for c in adapter.commands]
    assert "create_clip" in cmd_names
    assert "add_notes_to_clip" in cmd_names
