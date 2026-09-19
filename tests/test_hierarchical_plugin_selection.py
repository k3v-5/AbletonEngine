# tests/test_hierarchical_plugin_selection.py
"""
Unit tests for two-level hierarchical plugin selection in AbletonEngine:
1. Strict third-party priority over native instruments.
2. FutureAudioWorkshop SubLab XL strictly as #1 in BASS.
3. Level 1 offers strictly plugins (no preset pollution).
4. Level 2 sub-selection for multi-preset plugins (Analog Lab V and Omnisphere)
   offering role presets and the clean/default base plugin as the last option.
5. Interactive flow in CopilotGuidedSession.
"""

import pytest
from unittest.mock import MagicMock
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.instruments.browser_catalog import (
    LiveBrowserCatalogEngine,
    InstrumentSourceCategory,
    SoundSourceOption
)
from engine.instruments.installed_scanner import InstalledPluginScanner
from engine.production.copilot.guided_session import CopilotGuidedSession


def test_sublab_xl_strictly_first_for_bass():
    """Validates that SubLab XL is strictly option #1 for the BASS role."""
    opts = LiveBrowserCatalogEngine.get_available_sources_for_role("BASS", filter_installed=True)
    assert len(opts) > 0
    top_opt = opts[0]
    assert top_opt.id == "vst3_sublab_xl"
    assert "SubLab XL" in top_opt.name
    assert top_opt.category == InstrumentSourceCategory.VST3
    assert top_opt.uri == "query:Plugins#VST3:FutureAudioWorkshop:SubLabXL"


def test_third_party_priority_over_native():
    """Validates that all third-party VST3 plugins precede native instruments across roles."""
    for role in ["BASS", "KEYS", "LEAD"]:
        opts = LiveBrowserCatalogEngine.get_available_sources_for_role(role, filter_installed=True)
        found_native = False
        for opt in opts:
            if opt.category in (InstrumentSourceCategory.NATIVE_SYNTH, InstrumentSourceCategory.DRUM_KIT):
                found_native = True
            elif opt.category in (InstrumentSourceCategory.VST3, InstrumentSourceCategory.VST2):
                assert not found_native, f"Found third-party VST {opt.name} AFTER a native instrument in role {role}!"


def test_no_preset_pollution_in_level_1_plugin_list():
    """Validates that no individual .adg user preset racks pollute the Level 1 plugin list."""
    opts = LiveBrowserCatalogEngine.get_available_sources_for_role("BASS", filter_installed=True)
    for opt in opts:
        assert not opt.uri.startswith("query:UserLibrary#Presets:Instruments:Instrument%20Rack:ANALOG%20LAB%20V"), \
            f"Found Analog Lab user rack preset in Level 1: {opt.name}"
        assert not opt.uri.startswith("query:UserLibrary#Presets:Instruments:Instrument%20Rack:Omnisphere"), \
            f"Found Omnisphere user rack preset in Level 1: {opt.name}"


def test_plugin_presets_for_role_analog_lab():
    """Validates get_plugin_presets_for_role returns presets and appends clean default VST3 at the end."""
    sub_opts = LiveBrowserCatalogEngine.get_plugin_presets_for_role("Analog Lab V", "BASS")
    assert len(sub_opts) >= 1
    last_opt = sub_opts[-1]
    assert "(Default / Plugin limpio)" in last_opt.name
    assert last_opt.category == InstrumentSourceCategory.VST3
    assert last_opt.uri == "query:Plugins#VST3:Arturia:Analog%20Lab%20V"


def test_plugin_presets_for_role_omnisphere():
    """Validates get_plugin_presets_for_role for Omnisphere returns clean default option."""
    sub_opts = LiveBrowserCatalogEngine.get_plugin_presets_for_role("Omnisphere", "BASS")
    assert len(sub_opts) >= 1
    last_opt = sub_opts[-1]
    assert "(Default / Plugin limpio)" in last_opt.name
    assert last_opt.category == InstrumentSourceCategory.VST3
    assert last_opt.uri == "query:Plugins#VST3:Spectrasonics:Omnisphere"


def test_copilot_sublab_direct_selection():
    """Tests choosing SubLab XL directly in Phase 3 of CopilotGuidedSession."""
    session = CopilotGuidedSession()
    session.reset()
    adapter = MockAbletonAdapter()

    # Step 1: Initialize
    session.step(conn=adapter, user_input="")
    # Step 2: Choose Phase 1 tracks
    session.step(conn=adapter, user_input="Opción A")
    # Step 3: Choose Phase 2 sections
    session.step(conn=adapter, user_input="Opción 1")

    # Now in Phase 3. Advance to BASS track
    tracks = session.data.get("tracks", [])
    bass_indices = [i for i, t in enumerate(tracks) if t.get("role") == "BASS"]
    assert len(bass_indices) > 0, "No BASS track found in session scaffolding"
    bass_ptr = bass_indices[0]
    session.data["current_track_ptr"] = bass_ptr
    session._save_state()

    # Prompt BASS track
    prompt_res = session.step(conn=adapter, user_input="")
    assert "FutureAudioWorkshop SubLab XL" in prompt_res["question"]

    # Select SubLab XL (Option 1)
    sel_res = session.step(conn=adapter, user_input="Opción 1")
    # Should advance to next track pointer
    assert session.data["current_track_ptr"] == bass_ptr + 1
    assert session.data["tracks"][bass_ptr]["instrument"] == "FutureAudioWorkshop SubLab XL"
    assert session.data["tracks"][bass_ptr]["item_uri"] == "query:Plugins#VST3:FutureAudioWorkshop:SubLabXL"


def test_copilot_analog_lab_subselection_flow():
    """Tests selecting Analog Lab V, navigating to Level 2 sub-selection, and picking clean default."""
    session = CopilotGuidedSession()
    session.reset()
    adapter = MockAbletonAdapter()

    # Advance to Phase 3
    session.step(conn=adapter, user_input="")
    session.step(conn=adapter, user_input="Opción A")
    session.step(conn=adapter, user_input="Opción 1")

    tracks = session.data.get("tracks", [])
    bass_indices = [i for i, t in enumerate(tracks) if t.get("role") == "BASS"]
    bass_ptr = bass_indices[0]
    session.data["current_track_ptr"] = bass_ptr
    session._save_state()

    # Prompt BASS track
    session.step(conn=adapter, user_input="")

    # Choose "Analog Lab V"
    sub_prompt = session.step(conn=adapter, user_input="Analog Lab V")

    # Must stay on the same track pointer in sub-selection mode
    assert session.data["current_track_ptr"] == bass_ptr
    assert session.data["tracks"][bass_ptr].get("pending_plugin_subselection") is not None
    assert sub_prompt.get("is_subselection") is True
    assert "Sub-nivel" in sub_prompt["question"]
    assert "Default / Plugin limpio" in sub_prompt["question"]

    # Choose clean default option
    clean_res = session.step(conn=adapter, user_input="Default")

    # Must advance to next track pointer and have clean Analog Lab V loaded
    assert session.data["current_track_ptr"] == bass_ptr + 1
    assert session.data["tracks"][bass_ptr].get("pending_plugin_subselection") is None
    assert "Analog Lab V (Default / Plugin limpio)" in session.data["tracks"][bass_ptr]["instrument"]
    assert session.data["tracks"][bass_ptr]["item_uri"] == "query:Plugins#VST3:Arturia:Analog%20Lab%20V"


def test_copilot_subselection_volver():
    """Tests backing out of Level 2 sub-selection with 'Volver'."""
    session = CopilotGuidedSession()
    session.reset()
    adapter = MockAbletonAdapter()

    # Advance to Phase 3
    session.step(conn=adapter, user_input="")
    session.step(conn=adapter, user_input="Opción A")
    session.step(conn=adapter, user_input="Opción 1")

    tracks = session.data.get("tracks", [])
    bass_indices = [i for i, t in enumerate(tracks) if t.get("role") == "BASS"]
    bass_ptr = bass_indices[0]
    session.data["current_track_ptr"] = bass_ptr
    session._save_state()

    session.step(conn=adapter, user_input="")
    # Enter subselection
    session.step(conn=adapter, user_input="Analog Lab V")
    assert session.data["tracks"][bass_ptr].get("pending_plugin_subselection") is not None

    # Say "Volver"
    back_prompt = session.step(conn=adapter, user_input="Volver")
    assert session.data["tracks"][bass_ptr].get("pending_plugin_subselection") is None
    assert session.data["current_track_ptr"] == bass_ptr
    assert back_prompt.get("is_subselection") is not True
    assert "FutureAudioWorkshop SubLab XL" in back_prompt["question"]
