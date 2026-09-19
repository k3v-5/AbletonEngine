# tests/test_vst_vocal_chain_detection.py
import pytest
from unittest.mock import MagicMock
from engine.instruments.installed_scanner import InstalledPluginScanner, ScannedPlugin, PluginCategory
from engine.vocal.vocal_chain_processor import VocalChainProcessor


def test_installed_scanner_detects_autotune_and_vocal_vsts():
    scanner = InstalledPluginScanner()
    plugins = scanner.scan()

    # Verify Auto-Tune variants are indexed
    autotune_matches = [
        p for p in plugins.values()
        if "auto-tune" in p.name.lower() or "autotune" in p.name.lower() or p.vendor.lower() == "antares"
    ]
    assert len(autotune_matches) >= 1, "Expected at least one Antares Auto-Tune plugin discovered"
    
    # Verify primary role and supported roles
    at_artist = next((p for p in autotune_matches if "artist" in p.name.lower() or "auto-tune" in p.name.lower()), None)
    assert at_artist is not None
    assert "VOCALS" in at_artist.supported_roles or at_artist.primary_role == "VOCALS"

    # Verify FabFilter and Valhalla are detected
    ff_matches = [p for p in plugins.values() if "fabfilter" in p.name.lower() or p.vendor.lower() == "fabfilter"]
    valhalla_matches = [p for p in plugins.values() if "valhalla" in p.name.lower() or "valhalla" in p.vendor.lower()]
    assert len(ff_matches) >= 1, "Expected FabFilter suite discovered"
    assert len(valhalla_matches) >= 1, "Expected Valhalla DSP discovered"


def test_build_hybrid_vocal_chain_with_autotune_and_companion_vsts():
    chain = VocalChainProcessor.build_hybrid_vocal_chain(
        song_key="F",
        song_scale="Minor",
        style="modern_trap",
        retune_speed=0.0
    )

    assert len(chain) >= 5
    roles = [d["role"] for d in chain]
    assert "PITCH_CORRECTION" in roles
    assert "SURGICAL_EQ" in roles
    assert "DE_ESSER" in roles
    assert "DUAL_COMP_PEAK" in roles
    assert "HARMONIC_WARMTH" in roles

    # Check Slot 1 (Auto-Tune parameters)
    slot1 = chain[0]
    assert slot1["role"] == "PITCH_CORRECTION"
    assert "auto-tune" in slot1["name"].lower()
    assert slot1["params"]["Key"] == pytest.approx(0.48, abs=0.02) # F
    assert slot1["params"]["Scale"] == pytest.approx(0.05, abs=0.02) # Minor
    assert slot1["params"]["Retune Speed"] == 1.0 # Trap snap (0 ms in Live LOM)

    # Check companion VSTs
    eq_slot = next(d for d in chain if d["role"] == "SURGICAL_EQ")
    assert "pro-q" in eq_slot["name"].lower() or eq_slot["name"] == "EQ Eight"


def test_deploy_hybrid_vocal_chain_configures_parameters():
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {
        "result": {
            "devices": [
                {"name": "Utility", "class_name": "StereoGain"},
                {"name": "Antares Auto-Tune Artist", "class_name": "PluginDevice"}
            ]
        }
    }

    res = VocalChainProcessor.deploy_hybrid_vocal_chain(
        conn=mock_conn,
        track_index=12,
        song_key="F",
        song_scale="Minor",
        retune_speed=0.0
    )

    assert res["status"] == "SUCCESS"
    assert res["song_key"] == "F"
    assert res["song_scale"] == "Minor"
    assert res["has_autotune"] is True
    assert res["devices_configured"] >= 5

    # Check set_device_parameter calls were sent for Key, Scale, and Retune Speed
    calls = mock_conn.send_command.call_args_list
    param_calls = [c for c in calls if c[0][0] == "set_device_parameter"]
    assert len(param_calls) >= 3
