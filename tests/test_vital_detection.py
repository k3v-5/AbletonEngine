# tests/test_vital_detection.py
"""
Regression test suite for Vital Audio detection and availability in AbletonEngine.
Ensures Vital Audio is detected via user AppData/Documents, classified into all supported roles
(BASS, KEYS, PAD, LEAD, COUNTER_LEAD), and available in LiveBrowserCatalogEngine with filter_installed=True.
"""

import pytest
from engine.instruments.installed_scanner import InstalledPluginScanner, PluginCategory
from engine.instruments.browser_catalog import (
    LiveBrowserCatalogEngine,
    InstrumentSourceCategory,
)


def test_vital_scanner_detection():
    """Validates that InstalledPluginScanner detects Vital Audio on the system."""
    scanner = InstalledPluginScanner()
    scanned = scanner.scan()
    assert "vst3_vital" in scanned, "vst3_vital not found in scanner cache!"
    vital_plugin = scanned["vst3_vital"]
    assert vital_plugin.vendor == "Vital Audio"
    assert vital_plugin.category == PluginCategory.VST3
    assert vital_plugin.uri == "query:Plugins#VST3:Vital%20Audio:Vital"
    assert "KEYS" in vital_plugin.supported_roles
    assert "PAD" in vital_plugin.supported_roles
    assert "LEAD" in vital_plugin.supported_roles
    assert "BASS" in vital_plugin.supported_roles
    assert "COUNTER_LEAD" in vital_plugin.supported_roles


@pytest.mark.parametrize("role", ["BASS", "KEYS", "PAD", "LEAD", "COUNTER_LEAD"])
def test_vital_returned_for_roles_in_scanner(role):
    """Validates that get_plugins_for_role returns Vital for all core synth roles."""
    scanner = InstalledPluginScanner()
    plugins = scanner.get_plugins_for_role(role)
    vital_matches = [p for p in plugins if "vital" in p.id.lower() or "vital" in p.name.lower()]
    assert len(vital_matches) > 0, f"Vital not returned by get_plugins_for_role for {role}"


@pytest.mark.parametrize("role", ["BASS", "KEYS", "PAD", "LEAD", "COUNTER_LEAD"])
def test_vital_available_in_curated_sources_filtered(role):
    """Validates that LiveBrowserCatalogEngine includes Vital with filter_installed=True."""
    sources = LiveBrowserCatalogEngine.get_available_sources_for_role(role, filter_installed=True)
    vital_sources = [
        s for s in sources 
        if "vital" in s.id.lower() or "vital" in s.name.lower() or "vital" in s.uri.lower()
    ]
    assert len(vital_sources) > 0, f"Vital sound source not available for role {role} with filter_installed=True!"
    top_vital = vital_sources[0]
    assert top_vital.category == InstrumentSourceCategory.VST3
    assert top_vital.uri == "query:Plugins#VST3:Vital%20Audio:Vital"
