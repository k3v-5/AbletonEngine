# tests/test_full_song_arranger.py
import pytest
from engine.arrangement.blueprints.song_arranger import (
    SectionSpec,
    FullSongBlueprint,
    FullSongArrangerEngine
)
from engine.production.copilot.recipes import MacroProductionRecipes


class MockAdapter:
    def __init__(self):
        self.commands = []

    def send_command(self, cmd, params):
        self.commands.append((cmd, params))
        return {"status": "ok"}


def test_blueprint_generation_96_bars():
    bp = FullSongArrangerEngine.generate_96bar_blueprint(
        bpm=138.0,
        key="F",
        scale="minor",
        genre="atlanta_trap"
    )

    assert bp.total_bars == 96
    assert len(bp.sections) == 8
    assert sum(s.bars for s in bp.sections) == 96
    assert round(bp.duration_seconds, 1) == round((96 * 4.0 / 138.0) * 60.0, 1)

    # Check contiguous sequence without holes or overlaps
    curr = 1
    for s in bp.sections:
        assert s.start_bar == curr
        assert s.end_bar == curr + s.bars - 1
        assert s.start_beat == (s.start_bar - 1) * 4.0
        assert s.end_beat == (s.start_bar - 1 + s.bars) * 4.0
        curr += s.bars

    assert bp.sections[-1].end_bar == 96


def test_section_role_matrix_distribution():
    bp = FullSongArrangerEngine.generate_96bar_blueprint()
    sec_map = {s.name: s for s in bp.sections}

    # 1. Intro: No heavy low-end
    intro = sec_map["Intro"]
    assert intro.roles["kick"] == "OFF"
    assert intro.roles["bass"] == "OFF"
    assert intro.roles["foley"] == "FULL"

    # 2. Verse 1: Vocal space (lead is OFF)
    verse1 = sec_map["Verse 1"]
    assert verse1.roles["kick"] == "PUNCH"
    assert verse1.roles["lead"] == "OFF"
    assert verse1.roles["drums"] == "FULL"

    # 3. Pre-Chorus: Cuts bass, builds tension
    pre_chorus = sec_map["Pre-Chorus"]
    assert pre_chorus.roles["bass"] == "CUT_AT_32"
    assert pre_chorus.roles["drums"] == "BUILD_ROLL"

    # 4. Drop 1: Maximum punch & hook
    drop1 = sec_map["Drop 1 (Chorus)"]
    assert drop1.energy_target >= 0.90
    assert drop1.roles["bass"] == "FULL_SLIDES"
    assert drop1.roles["lead"] == "FOREGROUND"

    # 5. Verse 2: Breakbeat variation
    verse2 = sec_map["Verse 2"]
    assert verse2.roles["break"] == "AMEN_SHUFFLE"

    # 6. Bridge: Atmospheric release, no drums/bass
    bridge = sec_map["Bridge"]
    assert bridge.roles["drums"] == "OFF"
    assert bridge.roles["bass"] == "OFF"
    assert bridge.roles["foley"] == "FULL"

    # 7. Final Drop: Climax (energy 1.0)
    final_drop = sec_map["Final Drop (Climax)"]
    assert final_drop.energy_target == 1.0
    assert final_drop.roles["break"] == "LAYERED_FULL"

    # 8. Outro: Decay
    outro = sec_map["Outro"]
    assert outro.roles["kick"] == "OFF"
    assert outro.roles["bass"] == "OFF"


def test_cue_points_generation():
    bp = FullSongArrangerEngine.generate_96bar_blueprint()
    assert len(bp.cue_points) == 8
    # Intro starts at beat 0.0
    assert bp.cue_points[0]["time"] == 0.0
    # Verse 1 starts at bar 9 -> beat 32.0
    assert bp.cue_points[1]["time"] == 32.0
    # Drop 1 starts at bar 33 -> beat 128.0
    assert bp.cue_points[3]["time"] == 128.0


def test_clip_placements_and_vacuums():
    bp = FullSongArrangerEngine.generate_96bar_blueprint()
    tracks_map = {
        "kick": 0, "drums": 13, "bass": 6, "piano": 9,
        "lead": 4, "foley": 15, "break": 14, "vocal_chops": 5
    }

    placements = FullSongArrangerEngine.calculate_clip_placements(bp, tracks_map)
    assert len(placements) > 20

    # Ensure no bass is placed during Bridge (bars 65-72 -> beats 256.0 to 288.0)
    bridge_bass = [p for p in placements if p["role"] == "bass" and 256.0 <= p["destination_time"] < 288.0]
    assert len(bridge_bass) == 0

    vacuums = FullSongArrangerEngine.calculate_pre_drop_vacuums(bp)
    assert len(vacuums) == 2  # Pre-Chorus into Drop 1, and Bridge into Final Drop
    assert vacuums[0]["target_bar"] == 33.0
    assert vacuums[1]["target_bar"] == 73.0


def test_orchestrate_full_song_with_mock_adapter():
    adapter = MockAdapter()
    res = FullSongArrangerEngine.orchestrate_full_song(
        conn=adapter,
        bpm=140.0,
        genre="atlanta_trap"
    )

    assert res["status"] == "SUCCESS"
    assert res["total_bars"] == 96
    assert res["sections_count"] == 8
    assert res["cue_points_created"] == 8
    assert res["clip_placements_count"] > 0
    assert res["commands_dispatched"] > 0

    cmd_names = [c[0] for c in adapter.commands]
    assert "set_tempo" in cmd_names
    assert "create_cue_point" in cmd_names
    assert "duplicate_session_clip_to_arrangement" in cmd_names
    assert "create_arrangement_automation_envelope" in cmd_names


def test_macro_recipes_orchestrate_full_song():
    adapter = MockAdapter()
    res = MacroProductionRecipes.orchestrate_complete_song(
        conn=adapter,
        genre="detroit_minimal",
        bpm=135.0,
        key="G",
        scale="minor"
    )

    assert res["status"] == "SUCCESS"
    assert res["total_bars"] == 96
