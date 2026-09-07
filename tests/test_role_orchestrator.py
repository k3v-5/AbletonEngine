# tests/test_role_orchestrator.py
"""
Unit tests for Atomic Role Orchestrator (Capa 3: Operaciones Atómicas de Rol)
and Orphaned Track Governance Guard.
"""

import pytest
from unittest.mock import MagicMock
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.production.copilot.role_orchestrator import RoleTrackOrchestrator
from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
from server import AbletonConnection, GovernanceViolationError


def test_role_orchestrator_keys_atomic_success():
    """Test full atomic orchestration for KEYS role using MockAbletonAdapter."""
    adapter = MockAbletonAdapter()

    # Track 0: scaffolded MIDI track
    res = RoleTrackOrchestrator.orchestrate_role_track(
        conn=adapter,
        track_index=0,
        role="KEYS",
        genre="hip_hop_neo_soul",
        bpm=120.0,
        key="F",
        scale="natural_minor",
        arrange_bars=96
    )

    assert res["status"] == "SUCCESS"
    assert res["role"] == "KEYS"
    assert res["notes_written"] > 0
    assert res["arranged_bars"] == 96
    assert (0, 0) in DeviceParameterSupervisor._SCULPTED_REGISTRY

    # Check that track has clips in session and arrangement
    trk = adapter.tracks[0]
    assert trk["clip_slots"][0]["has_clip"] is True
    arr_clips = trk.get("arrangement_clips", [])
    assert len(arr_clips) > 0


def test_role_orchestrator_bass_atomic_success():
    """Test full atomic orchestration for BASS role."""
    adapter = MockAbletonAdapter()

    res = RoleTrackOrchestrator.orchestrate_role_track(
        conn=adapter,
        track_index=1,
        role="BASS",
        genre="trap",
        key="F",
        scale="natural_minor",
        arrange_bars=96
    )

    assert res["status"] == "SUCCESS"
    assert res["role"] == "BASS"
    assert res["notes_written"] > 0
    assert (1, 0) in DeviceParameterSupervisor._SCULPTED_REGISTRY
    assert adapter.tracks[1]["clip_slots"][0]["has_clip"] is True


def test_role_orchestrator_lead_atomic_success():
    """Test full atomic orchestration for LEAD role."""
    adapter = MockAbletonAdapter()
    adapter.create_midi_track() # creates track 2

    res = RoleTrackOrchestrator.orchestrate_role_track(
        conn=adapter,
        track_index=2,
        role="LEAD",
        key="F",
        scale="natural_minor"
    )

    assert res["status"] == "SUCCESS"
    assert res["role"] == "LEAD"
    assert res["notes_written"] > 0
    assert adapter.tracks[2]["clip_slots"][0]["has_clip"] is True


def test_role_orchestrator_strings_atomic_success():
    """Test full atomic orchestration for STRINGS role."""
    adapter = MockAbletonAdapter()
    adapter.create_midi_track() # track 2
    adapter.create_midi_track() # track 3

    res = RoleTrackOrchestrator.orchestrate_role_track(
        conn=adapter,
        track_index=3,
        role="STRINGS",
        key="F",
        scale="natural_minor"
    )

    assert res["status"] == "SUCCESS"
    assert res["role"] == "STRINGS"
    assert res["notes_written"] > 0
    assert adapter.tracks[3]["clip_slots"][0]["has_clip"] is True


def test_role_orchestrator_drums_atomic_success():
    """Test full atomic orchestration for DRUMS role with loop duplication."""
    adapter = MockAbletonAdapter()
    for _ in range(3):
        adapter.create_midi_track() # tracks 2, 3, 4

    res = RoleTrackOrchestrator.orchestrate_role_track(
        conn=adapter,
        track_index=4,
        role="DRUMS",
        genre="hip_hop_neo_soul",
        arrange_bars=96
    )

    assert res["status"] == "SUCCESS"
    assert res["role"] == "DRUMS"
    assert res["notes_written"] > 0
    assert res["clip_length_beats"] == 16.0
    # Arrangement timeline should have multiple duplicated clips
    arr_clips = adapter.tracks[4].get("arrangement_clips", [])
    assert len(arr_clips) >= 20


def test_role_orchestrator_aborts_on_verification_failure():
    """Test that transaction aborts if instrument is not detected in LOM."""
    class FailingConn:
        def send_command(self, cmd, params=None):
            if cmd == "get_track_info":
                # Returns device list with only an EQ (no instrument)
                return {
                    "name": "Midi Track",
                    "devices": [{"name": "EQ Eight", "class_name": "AudioEffectGroupDevice"}]
                }
            return {}

    conn = FailingConn()
    res = RoleTrackOrchestrator.orchestrate_role_track(
        conn=conn,
        track_index=0,
        role="KEYS"
    )

    assert res["status"] == "FAILED"
    assert res["phase"] == "PHYSICAL_VERIFICATION"
    assert "FAILED" in res["error"]


def test_socket_governance_blocks_start_playback_on_orphaned_track():
    """
    Test that _enforce_immutable_governance intercepts start_playback
    and blocks with ORPHANED_TRACK_DETECTED when a track has an instrument
    but 0 clips.
    """
    class MockConnWithOrphan(AbletonConnection):
        def __init__(self):
            pass
        def _send_raw(self, cmd, params=None):
            if cmd == "get_session_info":
                return {
                    "tracks": [
                        {
                            "name": "Orphaned Strings",
                            "is_midi_track": True,
                            "devices": [{"name": "Ac Strings Orch", "class_name": "InstrumentGroupDevice"}],
                            "clip_slots": [{"has_clip": False}]
                        }
                    ]
                }
            elif cmd == "get_arrangement_clips":
                return {"clips": []}
            return {}

    conn = MockConnWithOrphan()
    with pytest.raises(GovernanceViolationError) as exc_info:
        conn._enforce_immutable_governance("start_playback", {})

    assert "ORPHANED_TRACK_DETECTED" in str(exc_info.value)
    assert "Orphaned Strings" in str(exc_info.value)


def test_socket_governance_allows_playback_when_track_has_clips():
    """
    Test that _enforce_immutable_governance allows playback when
    tracks with instruments have clips.
    """
    class MockConnWithClips(AbletonConnection):
        def __init__(self):
            pass
        def _send_raw(self, cmd, params=None):
            if cmd == "get_session_info":
                return {
                    "tracks": [
                        {
                            "name": "Populated Keys",
                            "is_midi_track": True,
                            "devices": [{"name": "Analog Lab V", "class_name": "PluginDevice"}],
                            "clip_slots": [{"has_clip": True}]
                        }
                    ]
                }
            elif cmd == "get_arrangement_clips":
                return {"clips": [{"name": "Clip_0", "start_time": 0.0}]}
            return {}

    conn = MockConnWithClips()
    # Should not raise exception
    conn._enforce_immutable_governance("start_playback", {})


def test_copilot_stepper_detects_orphaned_track_as_blocker():
    """
    Test that Copilot Stepper preflight_check flags an orphaned track
    as a critical blocker.
    """
    from engine.production.copilot.stepper import ExecutiveCopilotEngine

    copilot = ExecutiveCopilotEngine()
    test_tracks = [
        {
            "track_index": 0,
            "name": "Orphaned Synth",
            "is_midi_track": True,
            "devices": [{"name": "Serum 2", "class_name": "PluginDevice"}],
            "clip_slots": [{"has_clip": False}],
            "arrangement_clips": []
        }
    ]

    copilot.inspect_session(tracks=test_tracks)
    check = copilot.preflight_check()

    assert check["ready_for_export"] is False
    assert any("CRITICAL_ORPHANED_TRACK" in b for b in check["blockers"])
    assert any("Orphaned Synth" in b for b in check["blockers"])
