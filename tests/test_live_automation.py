# tests/test_live_automation.py
import pytest
from engine.arrangement.automation.live_automation import LiveAutomationEngine


class MockAutomationConnection:
    def __init__(self):
        self.commands = []

    def send_command(self, cmd: str, params: dict):
        self.commands.append((cmd, params))
        if cmd == "get_track_info":
            return {
                "status": "success",
                "result": {"devices": [{"name": "Drift"}]}
            }
        if cmd == "get_device_parameters":
            return {
                "status": "success",
                "result": {
                    "parameters": [
                        {"name": "Device On", "index": 0, "value": 1.0},
                        {"name": "LP Freq", "index": 1, "value": 0.5},
                        {"name": "LP Res", "index": 2, "value": 0.0}
                    ]
                }
            }
        if cmd == "set_device_parameter":
            return {"status": "success", "result": {"new_value": params.get("value")}}
        return {"status": "success", "result": {}}


def test_detect_device_parameter():
    conn = MockAutomationConnection()
    detected = LiveAutomationEngine.detect_device_parameter(
        conn=conn,
        track_index=4,
        candidates=["LP Freq", "Cutoff"]
    )
    assert detected is not None
    d_idx, p_idx, p_name = detected
    assert d_idx == 0
    assert p_idx == 1
    assert p_name == "LP Freq"


def test_apply_filter_sweep():
    conn = MockAutomationConnection()
    res = LiveAutomationEngine.apply_filter_sweep(
        conn=conn,
        track_index=4,
        start_bar=29.0,
        duration_bars=4.0,
        direction="up"
    )
    assert res["status"] == "SUCCESS"
    assert res["automation_type"] == "FILTER_SWEEP"
    assert res["points_count"] > 10
    assert res["detected_parameter"] is not None


def test_apply_pre_drop_vacuum():
    conn = MockAutomationConnection()
    res = LiveAutomationEngine.apply_pre_drop_vacuum(
        conn=conn,
        track_indices=[2, 3, 4, 7],
        drop_bar=33.0,
        vacuum_beats=2.0
    )
    assert res["status"] == "SUCCESS"
    assert res["operation"] == "PRE_DROP_VACUUM"
    assert res["tracks_processed"] == 4
    assert res["drop_bar"] == 33.0
