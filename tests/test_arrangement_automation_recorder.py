"""
tests/test_arrangement_automation_recorder.py
Unit tests for ArrangementAutomationRecorder.
Verifies:
1. Musical math: bars to beats and beats to real-time seconds.
2. Correct command dispatch for single-curve live arrangement recording.
3. Multi-track parallel automation pass dispatch.
4. Tangible arrangement verification flags.
"""

import pytest
from typing import Dict, Any, List
from engine.arrangement.automation.recorder import ArrangementAutomationRecorder


class MockAbletonConn:
    def __init__(self, bpm=145.0):
        self.commands_sent: List[Dict[str, Any]] = []
        self.bpm = bpm

    def send_command(self, cmd: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        params = params or {}
        self.commands_sent.append({"cmd": cmd, "params": params})

        if cmd == "get_session_info":
            return {"tempo": self.bpm}
        elif cmd == "record_arrangement_automation":
            return {
                "status": "success",
                "result": {
                    "track_index": params.get("track_index"),
                    "device_index": params.get("device_index"),
                    "parameter": params.get("parameter"),
                    "automation_state": 1,
                    "tangible_arrangement_recorded": True
                }
            }
        elif cmd == "record_multi_automation_pass":
            return {
                "status": "success",
                "result": {
                    "automations_recorded": len(params.get("automations", [])),
                    "tangible_arrangement_recorded": True
                }
            }
        return {"status": "success"}


def test_musical_math_conversions():
    """Confirms bar-to-beat and beat-to-second calculations."""
    assert ArrangementAutomationRecorder.bars_to_beats(0.0) == 0.0
    assert ArrangementAutomationRecorder.bars_to_beats(4.0) == 16.0
    assert ArrangementAutomationRecorder.bars_to_beats(8.5) == 34.0

    # 120 BPM: 1 beat = 0.5s -> 16 beats = 8.0s
    assert ArrangementAutomationRecorder.beats_to_seconds(16.0, 120.0) == 8.0
    # 60 BPM: 1 beat = 1.0s -> 16 beats = 16.0s
    assert ArrangementAutomationRecorder.beats_to_seconds(16.0, 60.0) == 16.0
    # 145 BPM: 16 beats = (16/145)*60 = 6.620689...
    assert round(ArrangementAutomationRecorder.beats_to_seconds(16.0, 145.0), 2) == 6.62


def test_record_curve_dispatch():
    """Confirms record_curve prepares duration and dispatches record_arrangement_automation."""
    conn = MockAbletonConn(bpm=145.0)

    res = ArrangementAutomationRecorder.record_curve(
        conn=conn,
        track_index=10,
        device_index=0,
        parameter="P1 Brightness",
        start_bar=16.0,
        duration_bars=4.0,
        start_val=0.20,
        end_val=0.90,
        curve="exponential",
        steps=35
    )

    assert res["status"] == "SUCCESS"
    assert res["tangible_arrangement_recorded"] is True
    assert res["visible_with_A_key"] is True
    assert res["start_beat"] == 64.0
    assert res["duration_beats"] == 16.0
    assert res["duration_sec"] == 6.62

    # Check commands sent
    cmds = [c for c in conn.commands_sent if c["cmd"] == "record_arrangement_automation"]
    assert len(cmds) == 1
    p = cmds[0]["params"]
    assert p["track_index"] == 10
    assert p["device_index"] == 0
    assert p["parameter"] == "P1 Brightness"
    assert p["start_val"] == 0.20
    assert p["end_val"] == 0.90
    assert p["start_beat"] == 64.0
    assert p["curve"] == "exponential"
    assert p["steps"] == 35


def test_record_multi_pass_dispatch():
    """Confirms record_multi_pass handles parallel tracks in a single recording sweep."""
    conn = MockAbletonConn(bpm=145.0)

    automations = [
        {"track_index": 10, "device_index": 0, "parameter": "P1 Brightness", "start_val": 0.2, "end_val": 0.9, "curve": "exponential"},
        {"track_index": 4, "device_index": 0, "parameter": "Cutoff", "start_val": 0.8, "end_val": 0.1, "curve": "drop_vacuum"},
        {"track_index": -1, "device_index": None, "parameter": "Volume", "start_val": 0.85, "end_val": 0.70, "curve": "linear"}
    ]

    res = ArrangementAutomationRecorder.record_multi_pass(
        conn=conn,
        automations=automations,
        start_bar=28.0,
        duration_bars=4.0,
        steps=50
    )

    assert res["status"] == "SUCCESS"
    assert res["automations_count"] == 3
    assert res["start_beat"] == 112.0
    assert res["duration_beats"] == 16.0
    assert res["tangible_arrangement_recorded"] is True

    cmds = [c for c in conn.commands_sent if c["cmd"] == "record_multi_automation_pass"]
    assert len(cmds) == 1
    assert len(cmds[0]["params"]["automations"]) == 3
    assert cmds[0]["params"]["start_beat"] == 112.0
