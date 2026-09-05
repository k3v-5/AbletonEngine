# tests/test_physical_sidechain.py
import pytest
from engine.mix.sidechain_manager import SidechainManager


class MockSidechainConnection:
    def __init__(self, has_compressor=True):
        self.has_compressor = has_compressor
        self.commands = []

    def send_command(self, cmd: str, params: dict):
        self.commands.append((cmd, params))
        if cmd == "get_track_info":
            devs = [{"name": "Drift"}]
            if self.has_compressor:
                devs.append({"name": "Compressor"})
            return {"status": "success", "result": {"devices": devs}}
        if cmd == "load_instrument_or_effect":
            self.has_compressor = True
            return {"status": "success", "result": {}}
        if cmd == "set_device_parameter":
            return {"status": "success", "result": {"parameter_index": params.get("parameter"), "new_value": params.get("value")}}
        return {"status": "success", "result": {}}


def test_sidechain_find_existing():
    conn = MockSidechainConnection(has_compressor=True)
    res = SidechainManager.find_or_load_compressor(conn, track_index=7)
    assert res["status"] == "EXISTS"
    assert res["device_index"] == 1
    assert "Compressor" in res["device_name"]


def test_sidechain_load_missing():
    conn = MockSidechainConnection(has_compressor=False)
    res = SidechainManager.find_or_load_compressor(conn, track_index=7)
    assert res["status"] == "LOADED"
    assert res["device_index"] == 1


def test_sidechain_configure():
    conn = MockSidechainConnection(has_compressor=True)
    res = SidechainManager.configure_sidechain(
        conn=conn,
        bass_track_index=7,
        kick_track_index=2,
        threshold=0.55,
        ratio=0.75,
        attack=0.0,
        release=0.16
    )
    assert res["status"] == "SUCCESS"
    assert res["sidechain_active"] is True
    applied = res["applied_parameters"]
    names = [p["parameter"] for p in applied]
    assert "Device On" in names
    assert "S/C On" in names
    assert "Attack" in names
    assert "Threshold" in names
