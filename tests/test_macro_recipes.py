# tests/test_macro_recipes.py
import pytest
from engine.production.copilot.recipes import MacroProductionRecipes


class MockLiveConnection:
    def __init__(self):
        self.commands = []

    def send_command(self, cmd: str, params: dict):
        self.commands.append((cmd, params))
        return {"status": "ok"}


def test_macro_produce_rhythm_offline():
    res = MacroProductionRecipes.produce_complete_rhythm_section(
        conn=None,
        genre="atlanta_trap",
        bpm=140.0,
        drum_track=13,
        bass_track=6,
        humanize=True,
        auto_sidechain=True,
        add_slides=True,
        timeline_bars=64.0
    )

    assert res["status"] == "SUCCESS"
    assert res["genre"] == "atlanta_trap"
    assert res["bpm"] == 140.0
    assert res["drum_notes_count"] > 20
    assert res["bass_notes_count"] > 5
    assert res["sidechain_points_count"] > 0
    assert res["humanized"] is True
    assert res["slides_injected"] is True


def test_macro_produce_rhythm_with_live_adapter():
    conn = MockLiveConnection()
    res = MacroProductionRecipes.produce_complete_rhythm_section(
        conn=conn,
        genre="detroit_minimal",
        bpm=135.0,
        drum_track=10,
        bass_track=5
    )

    assert res["status"] == "SUCCESS"
    cmd_names = [c[0] for c in conn.commands]
    assert "set_tempo" in cmd_names
    assert "create_clip" in cmd_names
    assert "add_notes_to_clip" in cmd_names
    assert "create_arrangement_automation_envelope" in cmd_names
    assert "duplicate_session_clip_to_arrangement" in cmd_names


def test_macro_produce_harmony_offline():
    res = MacroProductionRecipes.produce_complete_harmony_and_lead(
        conn=None,
        piano_track=9,
        lead_track=4,
        apply_strum=True,
        reharmonize=True,
        bpm=138.0
    )

    assert res["status"] == "SUCCESS"
    assert res["chords_count"] == 8
    assert res["notes_count"] > 0
    assert res["reharmonized"] is True
    assert res["strum_applied"] is True
    assert res["piano_depth"] == "midground"
    assert res["lead_depth"] == "foreground"


def test_macro_produce_harmony_with_live_adapter():
    conn = MockLiveConnection()
    res = MacroProductionRecipes.produce_complete_harmony_and_lead(
        conn=conn,
        piano_track=9,
        lead_track=4
    )

    assert res["status"] == "SUCCESS"
    cmd_names = [c[0] for c in conn.commands]
    assert "create_clip" in cmd_names
    assert "add_notes_to_clip" in cmd_names
    assert "duplicate_session_clip_to_arrangement" in cmd_names


def test_macro_finalize_song():
    conn = MockLiveConnection()
    res = MacroProductionRecipes.finalize_mix_and_master(
        conn=conn,
        target_profile="STREAMING",
        pre_drop_bar=33.0
    )

    assert res["status"] == "SUCCESS"
    assert res["target_profile"] == "STREAMING"
    assert res["pre_drop_vacuum_points"] > 0
    assert res["readiness_verdict"] == "READY"
    cmd_names = [c[0] for c in conn.commands]
    assert "create_arrangement_automation_envelope" in cmd_names
