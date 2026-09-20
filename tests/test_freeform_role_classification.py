# tests/test_freeform_role_classification.py
"""
Unit tests for freeform role classification and resilient instrument resolution:
1. Verifies that specialized sub-roles (COUNTER_LEAD, EAR_CANDY, TEXTURE_FOLEY, SUB_BASS)
   have non-empty, authentic sound sources in the catalog.
2. Verifies that completely arbitrary or creative role names never produce empty lists,
   never raise IndexError, and resolve safely through the 4-tier acoustic hierarchy.
3. Verifies that RoleTrackOrchestrator.resolve_instrument always returns a valid URI.
4. Verifies that get_plugin_presets_for_role handles specialized and unknown roles gracefully.
5. Verifies end-to-end Copilot flow across Phase 1 and Phase 3 with 'Counter Lead'.
"""

import pytest
from unittest.mock import MagicMock
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.instruments.browser_catalog import (
    LiveBrowserCatalogEngine,
    InstrumentSourceCategory,
    SoundSourceOption,
    INSTRUMENT_ROLE_CATALOG
)
from engine.instruments.installed_scanner import InstalledPluginScanner
from engine.production.copilot.role_orchestrator import RoleTrackOrchestrator
from engine.production.copilot.guided_session import CopilotGuidedSession


def test_counter_lead_in_catalogs():
    """Validates COUNTER_LEAD is registered in role catalog and has curated sources."""
    assert "COUNTER_LEAD" in INSTRUMENT_ROLE_CATALOG
    sources = LiveBrowserCatalogEngine.get_available_sources_for_role("COUNTER_LEAD", filter_installed=False)
    assert len(sources) > 0, "COUNTER_LEAD must have available sources in catalog"
    names = [s.name.lower() for s in sources]
    assert any("pigments" in n or "serum" in n or "vital" in n or "agenda" in n for n in names)


def test_ear_candy_and_texture_foley_in_catalogs():
    """Validates EAR_CANDY and TEXTURE_FOLEY have curated sources."""
    assert "EAR_CANDY" in INSTRUMENT_ROLE_CATALOG
    assert "TEXTURE_FOLEY" in INSTRUMENT_ROLE_CATALOG
    
    candy_sources = LiveBrowserCatalogEngine.get_available_sources_for_role("EAR_CANDY", filter_installed=False)
    assert len(candy_sources) > 0, "EAR_CANDY must have available sources"
    
    foley_sources = LiveBrowserCatalogEngine.get_available_sources_for_role("TEXTURE_FOLEY", filter_installed=False)
    assert len(foley_sources) > 0, "TEXTURE_FOLEY must have available sources"


def test_parent_acoustic_role_resolution():
    """Validates that sub-roles correctly map to their primary acoustic families."""
    assert LiveBrowserCatalogEngine.get_parent_acoustic_role("COUNTER_LEAD") == "LEAD"
    assert LiveBrowserCatalogEngine.get_parent_acoustic_role("ARPS") == "LEAD"
    assert LiveBrowserCatalogEngine.get_parent_acoustic_role("EAR_CANDY") == "LEAD"
    assert LiveBrowserCatalogEngine.get_parent_acoustic_role("TEXTURE_FOLEY") == "PAD"
    assert LiveBrowserCatalogEngine.get_parent_acoustic_role("SUB_BASS") == "BASS"
    assert LiveBrowserCatalogEngine.get_parent_acoustic_role("PLUCK") == "KEYS"


def test_arbitrary_creative_roles_never_empty_and_no_index_error():
    """Validates that completely arbitrary/exotic role names never return empty lists or crash."""
    exotic_roles = [
        "XyloGlitch 9000",
        "Super Fantasy Synth",
        "Cosmic Dust Texture",
        "Sub Atomic Boom",
        "Ethereal Whispers",
        "Flamenco Strum 80s",
        "UNKNOWN_ROLE_XYZ"
    ]
    for r in exotic_roles:
        sources = LiveBrowserCatalogEngine.get_available_sources_for_role(r, filter_installed=True)
        assert len(sources) > 0, f"Role '{r}' returned an empty list of sources!"
        top_s = sources[0]
        assert top_s.uri is not None
        assert top_s.name != ""


def test_resolve_instrument_never_returns_none():
    """Validates RoleTrackOrchestrator.resolve_instrument never returns (None, ...)."""
    roles_to_test = ["COUNTER_LEAD", "EAR_CANDY", "TEXTURE_FOLEY", "SUB_BASS", "MY_WEIRD_ROLE"]
    for r in roles_to_test:
        uri, name = RoleTrackOrchestrator.resolve_instrument(r)
        assert uri is not None, f"resolve_instrument returned None uri for role '{r}'"
        assert name != "", f"resolve_instrument returned empty name for role '{r}'"


def test_plugin_presets_for_specialized_roles():
    """Validates get_plugin_presets_for_role handles specialized roles without IndexError."""
    sub_opts_counter = LiveBrowserCatalogEngine.get_plugin_presets_for_role("Analog Lab V", "COUNTER_LEAD")
    assert len(sub_opts_counter) >= 1
    assert sub_opts_counter[-1].category == InstrumentSourceCategory.VST3

    sub_opts_omni = LiveBrowserCatalogEngine.get_plugin_presets_for_role("Omnisphere", "EAR_CANDY")
    assert len(sub_opts_omni) >= 1
    assert sub_opts_omni[-1].category == InstrumentSourceCategory.VST3


def test_phase_1_and_phase_3_flow_with_counter_lead():
    """Simulates guided session through Phase 1 and Phase 3 with 'Counter Lead'."""
    adapter = MockAbletonAdapter()
    session = CopilotGuidedSession()
    session.reset()

    # Step 1: Initialize
    session.step(conn=adapter, user_input="")

    # Step 2: Phase 1 with explicit Counter Lead
    p1_input = "Batería, Bajo, Teclado, Counter Lead, FX (Audio)"
    session.step(conn=adapter, user_input=p1_input)
    
    tracks = session.data.get("tracks", [])
    assert len(tracks) >= 4
    counter_track = next((t for t in tracks if "counter" in t["name"].lower()), None)
    assert counter_track is not None, "Counter Lead track should have been created"
    assert counter_track["role"] == "COUNTER_LEAD"
    assert len(counter_track.get("available_sources", [])) > 0, "available_sources must not be empty"
    assert len(counter_track.get("top_recommendations", [])) > 0, "top_recommendations must not be empty"

    # Step 3: Phase 2 sections selection
    session.step(conn=adapter, user_input="Opción 1")

    # Now in Phase 3. Set track pointer to counter_track index
    counter_ptr = next(i for i, t in enumerate(session.data["tracks"]) if t["role"] == "COUNTER_LEAD")
    session.data["current_track_ptr"] = counter_ptr
    session._save_state()

    # Prompt Counter Lead track
    prompt_res = session.step(conn=adapter, user_input="")
    assert "COUNTER_LEAD" in prompt_res.get("question", "") or "Counter Lead" in prompt_res.get("question", "")

    # Select Option 1 for Counter Lead
    session.step(conn=adapter, user_input="Opción 1")
    # Verify no IndexError occurred and track received item_uri or instrument
    assert session.data["tracks"][counter_ptr].get("item_uri") or session.data["tracks"][counter_ptr].get("instrument")
