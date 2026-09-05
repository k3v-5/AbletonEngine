# tests/test_browser_catalog.py
import pytest
from engine.instruments.browser_catalog import BrowserCatalogEngine


class MockConnection:
    def __init__(self):
        self.commands = []

    def send_command(self, cmd: str, params: dict):
        self.commands.append((cmd, params))
        if cmd == "get_browser_tree":
            return {
                "status": "success",
                "result": {
                    "children": [
                        {"name": "plugins", "children": [
                            {"name": "VST3", "children": [
                                {"name": "Arturia", "children": [
                                    {"name": "Analog Lab V.vst3", "uri": "query:Plugins#AnalogLab"}
                                ]},
                                {"name": "Vital Audio", "children": [
                                    {"name": "Vital.vst3", "uri": "query:Plugins#Vital"}
                                ]}
                            ]}
                        ]},
                        {"name": "drums", "children": [
                            {"name": "808 Core Kit.adg", "uri": "query:Drums#FileId_5422"}
                        ]}
                    ]
                }
            }
        return {"status": "success", "result": {}}


def test_browser_catalog_all():
    conn = MockConnection()
    res = BrowserCatalogEngine.list_all_available_instruments(conn)
    assert res["status"] == "SUCCESS"
    assert "role_catalog" in res
    assert "vst3_plugins" in res
    assert "native_presets" in res
    assert len(res["vst3_plugins"]) >= 2
    assert any("Analog Lab" in p for p in res["vst3_plugins"])
    assert any("Vital" in p for p in res["vst3_plugins"])


def test_browser_catalog_role_filter():
    conn = MockConnection()
    res = BrowserCatalogEngine.list_all_available_instruments(conn, role="bass")
    assert res["status"] == "SUCCESS"
    assert "role_filter" in res
    assert res["role_filter"] == "bass"
    assert "items" in res
    names = [item["name"] for item in res["items"]]
    assert any("Vital" in n or "Analog Lab" in n or "Drift" in n for n in names)
