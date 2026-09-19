# tests/test_copilot_engine_upgrades.py
"""
Unit and integration tests for Copilot Engine Architectural Upgrades:
1. Bidirectional Role Aliasing (Keys <-> Pluck <-> Guitar <-> Synth <-> Lead)
2. Preflight Session Cleanup (Baseline guarantee, stop transport, wipe cues/devices/clips, reset faders/pan)
3. Personal Samples Chopping Mode in Phase 3 (Simpler/Drum Rack slicing, LOM verification, Delta >= 1)
4. Arrangement Navigation & Transport Jump in Phase 9 (Cue/bar/beat positioning & instant playback)
"""

import pytest
from unittest.mock import MagicMock
from pathlib import Path

from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.production.copilot.role_orchestrator import RoleTrackOrchestrator
from engine.production.copilot.guided_session import CopilotGuidedSession, get_personal_samples
from engine.indexer.paths import get_personal_samples_roots


@pytest.fixture
def clean_session():
    """Provides a fresh CopilotGuidedSession with reset state."""
    session = CopilotGuidedSession()
    session.reset()
    return session


# -------------------------------------------------------------------------
# 1. TEST ROLE ALIASES RESOLUTION
# -------------------------------------------------------------------------
def test_role_aliases_dictionary():
    """Verify bidirectional role alias mappings."""
    keys_aliases = RoleTrackOrchestrator.get_role_aliases("KEYS")
    assert "KEYS" in keys_aliases
    assert "PLUCK" in keys_aliases
    assert "GUITAR" in keys_aliases
    assert "HARMONY" in keys_aliases
    assert "SYNTH" in keys_aliases

    pluck_aliases = RoleTrackOrchestrator.get_role_aliases("PLUCK")
    assert "KEYS" in pluck_aliases
    assert "SYNTH" in pluck_aliases

    lead_aliases = RoleTrackOrchestrator.get_role_aliases("LEAD")
    assert "SYNTH" in lead_aliases
    assert "SOLO" in lead_aliases

    bass_aliases = RoleTrackOrchestrator.get_role_aliases("BASS")
    assert "808" in bass_aliases
    assert "SUB" in bass_aliases


def test_note_matching_with_role_aliases(clean_session):
    """Verify that custom AI composition notes written for PLUCK or Guitar match a track with role KEYS."""
    trk_keys = {"index": 1, "name": "Pluck Synth", "role": "KEYS"}

    custom_map = {
        ("PLUCK", 0): [{"pitch": 60, "start_time": 0.0, "duration": 0.5, "velocity": 100}],
        ("Guitar", 1): [{"pitch": 64, "start_time": 0.0, "duration": 1.0, "velocity": 90}],
    }

    # Should find notes for section 0 via alias PLUCK
    notes_sec0 = clean_session._find_custom_notes_for_track_section(
        custom_map=custom_map,
        trk=trk_keys,
        s_idx=0,
        s_name="Intro",
        s_beats=32.0
    )
    assert notes_sec0 is not None
    assert len(notes_sec0) == 1
    assert notes_sec0[0]["pitch"] == 60

    # Should find notes for section 1 via name alias Guitar
    notes_sec1 = clean_session._find_custom_notes_for_track_section(
        custom_map=custom_map,
        trk=trk_keys,
        s_idx=1,
        s_name="Drop 1",
        s_beats=64.0
    )
    assert notes_sec1 is not None
    assert len(notes_sec1) == 1
    assert notes_sec1[0]["pitch"] == 64


# -------------------------------------------------------------------------
# 2. TEST PREFLIGHT SESSION CLEANUP
# -------------------------------------------------------------------------
def test_preflight_clean_session():
    """Verify that preflight_clean_session resets playback, wipes cues, clips, devices and faders."""
    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = lambda cmd, args: (
        {"cue_points": [{"name": "Old Cue", "time": 16.0}]} if cmd == "get_cue_points"
        else {"track_count": 2} if cmd == "get_session_info"
        else {"devices": [{"name": "Old Synth"}], "is_foldable": False} if cmd == "get_track_info"
        else {"status": "success"}
    )

    report = CopilotGuidedSession.preflight_clean_session(mock_conn)

    assert report["playback_stopped"] is True
    assert report["cue_points_cleared"] >= 1
    assert report["tracks_cleaned"] == 2
    assert report["devices_removed"] >= 2
    assert report["clips_cleared"] >= 32
    assert report["playhead_reset"] is True

    # Check commands called
    calls = [c[0][0] for c in mock_conn.send_command.call_args_list]
    assert "stop_playback" in calls
    assert "delete_cue_point" in calls
    assert "delete_device" in calls
    assert "delete_clip" in calls
    assert "set_track_volume" in calls
    assert "jump_to_cue_point" in calls


# -------------------------------------------------------------------------
# 3. TEST PERSONAL SAMPLES & CHOPPING MODE
# -------------------------------------------------------------------------
def test_personal_samples_discovery():
    """Verify that personal sample roots exist and scan audio files."""
    roots = get_personal_samples_roots()
    assert any(Path("F:/Lap/Music") in [r, r.parent] for r in roots) or len(roots) > 0

    samples = get_personal_samples(max_results=10)
    assert isinstance(samples, list)
    if samples:
        s0 = samples[0]
        assert "name" in s0
        assert "path" in s0
        assert "folder" in s0


def test_chopping_mode_in_phase_3(clean_session):
    """Verify selecting Chopping mode in Phase 3 loads Simpler, sets slicing, and validates."""
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")  # Phase 1 -> 2
    clean_session.step(conn=adapter, user_input="Opción A")  # Phase 2 -> 3

    # Now in Phase 3, track 0 (Drums) or track 1 (Keys). Let's request Chopping mode
    prompt_p3 = clean_session._prompt_current_track_instrument()
    assert "Modo Chopping" in prompt_p3["question"]

    res_p3 = clean_session.step(conn=adapter, user_input="Chopping")
    # Track 0 configured with Simpler Chopping
    trk0 = clean_session.data["tracks"][0]
    assert trk0.get("chopping_mode") is True
    assert "Simpler" in trk0.get("instrument", "")


# -------------------------------------------------------------------------
# 4. TEST NAVIGATION & TRANSPORT JUMP IN PHASE 9
# -------------------------------------------------------------------------
def test_navigation_transport_jump(clean_session):
    """Verify that Phase 9 responds to section navigation commands, jumps playhead, and starts playback."""
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {"status": "success"}

    clean_session.data["current_phase"] = "PHASE_9_COMPLETED"
    clean_session.data["sections"] = [
        {"name": "Intro", "bars": 8, "start_bar": 0},
        {"name": "Drop 1", "bars": 16, "start_bar": 24},
        {"name": "Breakdown", "bars": 8, "start_bar": 40},
    ]
    clean_session._save_state()

    # 1. Jump to Drop 1
    res = clean_session.step(conn=mock_conn, user_input="Saltar al Drop 1")
    assert res.get("status") in ["NAVIGATED", "COMPLIANT_CERTIFIED"] or "PLAYHEAD" in res.get("current_step", "")
    assert "Drop 1" in res["question"]
    assert res["playback_position"]["beat"] == 96.0  # 24 bars * 4 = 96 beats

    mock_conn.send_command.assert_any_call("jump_to_cue_point", {"target": 96.0})
    mock_conn.send_command.assert_any_call("start_playback", {})

    # 2. Jump to Compás 40 (Breakdown)
    res2 = clean_session.step(conn=mock_conn, user_input="Ir al compás 40")
    assert res2["playback_position"]["beat"] == 160.0
    mock_conn.send_command.assert_any_call("jump_to_cue_point", {"target": 160.0})


# -------------------------------------------------------------------------
# 5. TEST CHOPPING NOTE CLAMPING TO ACTIVE SLICES
# -------------------------------------------------------------------------
def test_chopping_note_clamping_to_active_slices(clean_session):
    import json
    from engine.adapters.mock_adapter import MockAbletonAdapter
    adapter = MockAbletonAdapter()
    clean_session.step(conn=adapter, user_input="Opción A")  # Phase 1
    clean_session.step(conn=adapter, user_input="Opción B")  # Phase 2
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")  # Phase 3
    for _ in range(5):
        clean_session.step(conn=adapter, user_input="Opción 1")  # Phase 4
    for _ in range(10):
        clean_session.step(conn=adapter, user_input="Opción 1")  # Phase 5

    # Mark track 0 as chopping mode with 16 slices
    clean_session.data["tracks"][0]["chopping_mode"] = True
    clean_session.data["tracks"][0]["slices_count"] = 16
    clean_session._save_state()

    custom_comp = {
        "composition": [
            {
                "track_name": clean_session.data["tracks"][0]["name"],
                "section": "Intro",
                "notes": [
                    {"pitch": 72, "start_time": 0.0, "duration": 0.5, "velocity": 100},
                    {"pitch": 24, "start_time": 1.0, "duration": 0.5, "velocity": 90}
                ]
            }
        ]
    }
    clean_session.step(conn=adapter, user_input=json.dumps(custom_comp))
    t0_notes = adapter.get_clip_notes(clean_session.data["tracks"][0]["index"], 0)
    assert len(t0_notes) == 2
    assert 36 <= t0_notes[0]["pitch"] < (36 + 16)
    assert 36 <= t0_notes[1]["pitch"] < (36 + 16)


# -------------------------------------------------------------------------
# 6. TEST GROUP TRACKS IMMUNITY & DYNAMIC RESOLUTION
# -------------------------------------------------------------------------
def test_group_tracks_dynamic_resolution(clean_session):
    from unittest.mock import MagicMock
    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = lambda cmd, args: (
        {"track_count": 3} if cmd == "get_session_info"
        else {"name": "Group Drums", "is_foldable": True, "is_midi_track": False} if (cmd == "get_track_info" and args.get("track_index") == 0)
        else {"name": "[DRUMS] Percussion", "is_foldable": False, "is_midi_track": True} if (cmd == "get_track_info" and args.get("track_index") == 1)
        else {"name": "Other", "is_foldable": False, "is_midi_track": True}
    )

    trk = {"index": 0, "name": "Percussion", "role": "DRUMS"}
    resolved_idx = clean_session._resolve_live_track_index(mock_conn, trk)
    assert resolved_idx == 1
    assert trk["index"] == 1


# -------------------------------------------------------------------------
# 7. TEST CONFIGURED MASTERING PROFILE (-6.0 LUFS)
# -------------------------------------------------------------------------
def test_configured_mastering_profile():
    from engine.production.copilot.guided_session import get_configured_mastering_profile
    p_name, prof = get_configured_mastering_profile()
    assert prof.target_lufs == -6.0
    assert prof.max_true_peak_dbtp == -0.3
    assert prof.tolerance_lufs == 1.0

