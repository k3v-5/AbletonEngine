# tests/test_physical_snapshots.py
import pytest
from pathlib import Path
from engine.snapshots.physical_snapshot import PhysicalSnapshotManager
from engine.production.doctor.session_doctor import CopilotSessionDoctor


class MockLOMConnection:
    """Simulates Live TCP connection returning LOM structures for testing snapshots."""
    def __init__(self):
        self.commands = []
        self.live_state = {
            "tempo": 124.0,
            "tracks": [
                {
                    "index": 0,
                    "name": "Drums",
                    "is_group": False,
                    "volume": 0.85,
                    "panning": 0.0,
                    "mute": False,
                    "solo": False,
                    "arm": False,
                    "clips_count": 2,
                    "arrangement_clips": [
                        {
                            "name": "KickLoop",
                            "start_time": 0.0,
                            "length": 16.0,
                            "is_audio": False,
                            "muted": False,
                            "notes": [
                                {"pitch": 36, "start_time": 0.0, "duration": 0.5, "velocity": 100, "mute": False},
                                {"pitch": 36, "start_time": 1.0, "duration": 0.5, "velocity": 100, "mute": False}
                            ]
                        }
                    ],
                    "devices": [{"index": 0, "name": "Drum Buss", "class_name": "DrumBuss"}]
                },
                {
                    "index": 1,
                    "name": "Pad Roto",
                    "is_group": False,
                    "volume": 0.70,
                    "panning": -0.20,
                    "mute": False,
                    "solo": False,
                    "arm": False,
                    "clips_count": 2,
                    "arrangement_clips": [
                        {
                            "name": "PadPartA",
                            "start_time": 16.0,
                            "length": 32.0,
                            "is_audio": False,
                            "muted": False,
                            "notes": [
                                {"pitch": 48, "start_time": 0.0, "duration": 4.0, "velocity": 80, "mute": False},
                                {"pitch": 52, "start_time": 0.0, "duration": 4.0, "velocity": 80, "mute": False},
                                {"pitch": 55, "start_time": 0.0, "duration": 4.0, "velocity": 80, "mute": False}
                            ]
                        },
                        {
                            "name": "PadPartB",
                            "start_time": 48.0,
                            "length": 32.0,
                            "is_audio": False,
                            "muted": False,
                            "notes": [
                                {"pitch": 50, "start_time": 0.0, "duration": 4.0, "velocity": 85, "mute": False}
                            ]
                        }
                    ],
                    "devices": [{"index": 0, "name": "Reverb", "class_name": "Reverb"}]
                }
            ]
        }

    def send_command(self, cmd: str, params: dict = None):
        params = params or {}
        self.commands.append((cmd, params))

        if cmd == "execute_code":
            code = params.get("code", "")
            if "tracks_out = []" in code:
                # Capture snapshot command
                return {
                    "status": "success",
                    "result": {
                        "result": {
                            "tempo": self.live_state["tempo"],
                            "tracks": self.live_state["tracks"]
                        }
                    }
                }
            elif "clips_to_restore" in code:
                # restore_track command
                return {
                    "status": "success",
                    "result": {
                        "result": {
                            "found": True,
                            "track_name": "Pad Roto",
                            "recreated_clips": 2,
                            "recreated_notes": 4
                        }
                    }
                }
            elif "c_info = json.loads" in code:
                # restore_clip command
                return {
                    "status": "success",
                    "result": {
                        "result": {
                            "found_track": True,
                            "clip_restored": True,
                            "notes_count": 3
                        }
                    }
                }
            return {"status": "success", "result": {}}

        return {"status": "success"}


def test_physical_snapshot_capture():
    mgr = PhysicalSnapshotManager()
    conn = MockLOMConnection()
    snap = mgr.capture_snapshot(conn, name="Unit Test Snapshot")

    assert snap["id"].startswith("snap_phys_")
    assert snap["name"] == "Unit Test Snapshot"
    assert len(snap["tracks"]) == 2
    pad_track = next(t for t in snap["tracks"] if t["name"] == "Pad Roto")
    assert len(pad_track["arrangement_clips"]) == 2
    assert sum(len(c["notes"]) for c in pad_track["arrangement_clips"]) == 4


def test_physical_snapshot_restore_track():
    mgr = PhysicalSnapshotManager()
    conn = MockLOMConnection()
    snap = mgr.capture_snapshot(conn, name="Unit Test Snapshot")

    # Restore Pad Roto specifically
    res = mgr.restore_track(conn, snap, "Pad Roto")
    assert res["status"] == "SUCCESS"
    assert res["track_name"] == "Pad Roto"
    assert res["clips_restored"] == 2
    assert res["notes_restored"] == 4

    # Verify restore command was executed
    exec_cmds = [p for c, p in conn.commands if c == "execute_code" and "clips_to_restore" in p.get("code", "")]
    assert len(exec_cmds) == 1
    code = exec_cmds[0]["code"]
    assert "Pad Roto" in code
    assert "recreated_clips" in code


def test_physical_snapshot_restore_clip():
    mgr = PhysicalSnapshotManager()
    conn = MockLOMConnection()
    snap = mgr.capture_snapshot(conn, name="Unit Test Snapshot")

    # Restore single clip by start_time 16.0
    res = mgr.restore_clip(conn, snap, "Pad Roto", 16.0)
    assert res["status"] == "SUCCESS"
    assert res["clip_name"] == "PadPartA"
    assert res["start_time"] == 16.0
    assert res["notes_restored"] == 3


def test_doctor_on_demand_restore_track(tmp_path):
    state_file = tmp_path / "doctor_test_state.json"
    doctor = CopilotSessionDoctor(state_file=state_file)
    conn = MockLOMConnection()

    # Capture pre-repair snapshot
    snap = doctor._create_pre_repair_snapshot(conn, conn.live_state["tracks"])

    # User says "restaurar pista Pad Roto"
    step_res = doctor.step(conn, user_input="restaurar pista Pad Roto")
    assert step_res["status"] == "TRACK_RESTORED"
    assert "Pad Roto" in step_res["action_taken"]
    assert "Clips restaurados" in step_res["action_taken"]


def test_doctor_on_demand_restore_clip(tmp_path):
    state_file = tmp_path / "doctor_test_state.json"
    doctor = CopilotSessionDoctor(state_file=state_file)
    conn = MockLOMConnection()

    # Pre-repair snapshot
    doctor._create_pre_repair_snapshot(conn, conn.live_state["tracks"])

    # User says "restaurar clip 16.0 de pista Pad Roto"
    step_res = doctor.step(conn, user_input="restaurar clip 16.0 de pista Pad Roto")
    assert step_res["status"] == "CLIP_RESTORED"
    assert "PadPartA" in step_res["action_taken"]
