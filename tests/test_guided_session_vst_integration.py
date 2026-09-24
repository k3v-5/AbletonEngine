# tests/test_guided_session_vst_integration.py
"""
Integration tests for Decent Sampler, Valhalla Supermassive, and Surge XT Effects
within the Copilot Guided Session workflow (Phases 3, 4, 5, and Intercept Router).
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from engine.sound_design.decent_sampler.library_manager import DecentSamplerLibraryManager
from engine.production.copilot.guided_session import CopilotGuidedSession
from engine.production.copilot.phases.phase_3_instruments import Phase3InstrumentsHandler
from engine.production.copilot.phases.phase_4_param_sculpting import Phase4ParamSculptingHandler
from engine.production.copilot.phases.phase_5_insert_effects import Phase5InsertEffectsHandler
from engine.production.copilot.intercept_router import CopilotInterceptRouter
from engine.fx.role_fx_catalog import ROLE_INSERT_EFFECTS
from engine.instruments.browser_catalog import LiveBrowserCatalogEngine


@pytest.fixture(autouse=True)
def preserve_engine_settings():
    settings_file = Path("state/engine_settings.json")
    original = settings_file.read_text(encoding="utf-8") if settings_file.exists() else None
    yield
    if original is not None:
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(original, encoding="utf-8")
    elif settings_file.exists():
        settings_file.unlink()


class MockSession:
    """Mock session simulating CopilotGuidedSession state."""
    def __init__(self, data=None):
        self.data = data or {
            "song_name": "TestSong",
            "key": "F",
            "scale": "Minor",
            "bpm": 128.0,
            "tracks": [
                {"index": 0, "name": "Keys", "role": "KEYS", "is_audio": False},
                {"index": 1, "name": "Drums", "role": "DRUMS", "is_audio": False},
                {"index": 2, "name": "Lead", "role": "LEAD", "is_audio": False},
            ],
            "current_track_ptr": 0,
            "current_param_ptr": 0,
            "current_fx_track_ptr": 0,
            "current_fx_dev_ptr": 0,
            "current_fx_ptr": 0,
            "current_phase": "PHASE_3_INSTRUMENTS",
            "phase_index": 3,
        }

    def _save_state(self):
        pass

    def _resolve_live_track_index(self, conn, trk):
        return trk.get("index", 0)

    def _prompt_current_track_instrument(self):
        handler = Phase3InstrumentsHandler()
        return handler.prompt(self)

    def _prompt_current_track_params(self):
        handler = Phase4ParamSculptingHandler()
        return handler.prompt(self)

    def _prompt_current_fx_device(self):
        handler = Phase5InsertEffectsHandler()
        return handler.prompt(self)

    def _prompt_phase_6(self):
        return {"current_step": "PASO 6 DE 7: COMPOSICION", "phase": "PHASE_6_COMPOSITION"}


class TestDecentSamplerGuidedSessionIntegration:
    """Tests Decent Sampler integration into Phase 3 and Phase 4."""

    def test_browser_catalog_discovers_decent_sampler_libraries(self):
        sources = LiveBrowserCatalogEngine.get_available_sources_for_role("KEYS", filter_installed=True)
        ds_sources = [s for s in sources if "decent sampler" in s.name.lower()]
        assert len(ds_sources) > 0, "Decent Sampler should appear in available sources for KEYS."
        assert ds_sources[0].category.value == "vst3"
        assert "query:Plugins#VST3:Decent%20Samples:Decent%20Sampler" in ds_sources[0].uri

    def test_browser_catalog_decent_sampler_subselection(self):
        sub_opts = LiveBrowserCatalogEngine.get_plugin_presets_for_role("Decent Sampler", "KEYS")
        assert len(sub_opts) >= 2, "Should return discovered libraries and clean default."
        has_clean = any("Default / Plugin limpio" in o.name for o in sub_opts)
        assert has_clean, "Last option must be clean default Decent Sampler."

    def test_phase_3_select_decent_sampler_direct_library(self):
        session = MockSession()
        handler = Phase3InstrumentsHandler()
        conn = MagicMock()
        conn.send_command.return_value = {"status": "ok", "devices": [{"name": "Decent Sampler", "class_name": "PluginDevice"}]}

        # User chooses "Decent Sampler (DR Cathedral Piano DS v1)"
        res = handler.handle(session, conn, "DR Cathedral Piano")
        trk = session.data["tracks"][0]
        assert "Decent Sampler" in trk.get("instrument", "")
        assert trk.get("is_decent_sampler") is True
        assert trk.get("decent_sampler_library") is not None
        assert trk.get("decent_sampler_preset_path") is not None

    def test_phase_4_sculpts_decent_sampler_track(self):
        session = MockSession()
        session.data["current_phase"] = "PHASE_4_PARAM_SCULPTING"
        session.data["phase_index"] = 4
        trk = session.data["tracks"][0]
        trk["instrument"] = "Decent Sampler (DR Cathedral Piano DS v1)"
        trk["is_decent_sampler"] = True
        trk["decent_sampler_library"] = "DR Cathedral Piano DS v1"
        trk["decent_sampler_preset_path"] = "D:/dummy/Cathedral.dspreset"

        handler = Phase4ParamSculptingHandler()
        prompt_res = handler.prompt(session)

        assert "DECENT SAMPLER" in prompt_res.get("current_step", "")
        assert "DR Cathedral Piano DS v1" in prompt_res.get("question", "")
        assert "AMP_ATTACK" in prompt_res.get("question", "")

        # Sculpt parameters
        conn = MagicMock()
        conn.send_command.return_value = {"status": "ok"}
        handle_res = handler.handle(session, conn, "Attack: 0.05, Release: 0.50, Cutoff: 0.70")
        assert session.data["current_param_ptr"] == 1


class TestValhallaSupermassiveGuidedSessionIntegration:
    """Tests Valhalla Supermassive insert effect sculpting, validation, and clipboard injection."""

    def test_supermassive_in_role_fx_catalog(self):
        keys_fx = [fx["name"] for fx in ROLE_INSERT_EFFECTS.get("KEYS", [])]
        assert "ValhallaSupermassive" in keys_fx

        lead_fx = [fx["name"] for fx in ROLE_INSERT_EFFECTS.get("LEAD", [])]
        assert "ValhallaSupermassive" in lead_fx

        pad_fx = [fx["name"] for fx in ROLE_INSERT_EFFECTS.get("PAD", [])]
        assert "ValhallaSupermassive" in pad_fx

    def test_phase_5_prompt_contains_supermassive_anti_lazy_directives(self):
        session = MockSession()
        session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
        session.data["phase_index"] = 5
        # Set track to Lead and ptr to Supermassive
        lead_trk = session.data["tracks"][2]
        session.data["current_fx_track_ptr"] = 2
        fx_list = ROLE_INSERT_EFFECTS.get("LEAD", [])
        sm_idx = next(i for i, fx in enumerate(fx_list) if fx["name"] == "ValhallaSupermassive")
        session.data["current_fx_dev_ptr"] = sm_idx

        handler = Phase5InsertEffectsHandler()
        prompt_res = handler.prompt(session)

        q = prompt_res.get("question", "")
        assert "Valhalla Supermassive" in q
        assert "Anti-Arquetipos Vagos" in q
        assert "Portapapeles" in q
        assert "Andromeda Cloud" in q

    def test_phase_5_sculpts_and_serializes_supermassive_with_clipboard(self, tmp_path):
        session = MockSession()
        session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
        session.data["phase_index"] = 5
        session.data["current_fx_track_ptr"] = 2  # Lead track
        fx_list = ROLE_INSERT_EFFECTS.get("LEAD", [])
        sm_idx = next(i for i, fx in enumerate(fx_list) if fx["name"] == "ValhallaSupermassive")
        session.data["current_fx_dev_ptr"] = sm_idx

        handler = Phase5InsertEffectsHandler()
        conn = MagicMock()
        conn.send_command.return_value = {"status": "ok", "devices": [{"name": "ValhallaSupermassive", "class_name": "PluginDevice"}]}

        # Mold parameters with BPM tempo sync and safe feedback
        user_input = "Mix: 25%, Feedback: 60%, LowCut: 0.15, HighCut: 0.70, DelaySync: 1.0, Mode: Andromeda"
        with patch("engine.sound_design.valhalla_supermassive.serializer.ValhallaSupermassiveSerializer.copy_to_clipboard", return_value=True) as mock_cb:
            res = handler.handle(session, conn, user_input)
            lead_trk = session.data["tracks"][2]
            assert lead_trk.get("supermassive_preset_path") is not None
            assert lead_trk.get("supermassive_clipboard_ready") is True
            mock_cb.assert_called_once()


class TestSurgeXTEffectsGuidedSessionIntegration:
    """Tests Surge XT Effects insert effect sculpting, validation, and chain file saving."""

    def test_surge_xt_in_role_fx_catalog(self):
        drums_fx = [fx["name"] for fx in ROLE_INSERT_EFFECTS.get("DRUMS", [])]
        assert "Surge XT Effects" in drums_fx

        bass_fx = [fx["name"] for fx in ROLE_INSERT_EFFECTS.get("BASS", [])]
        assert "Surge XT Effects" in bass_fx

    def test_phase_5_prompt_contains_surge_xt_directives(self):
        session = MockSession()
        session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
        session.data["phase_index"] = 5
        session.data["current_fx_track_ptr"] = 1  # Drums track
        fx_list = ROLE_INSERT_EFFECTS.get("DRUMS", [])
        srg_idx = next(i for i, fx in enumerate(fx_list) if fx["name"] == "Surge XT Effects")
        session.data["current_fx_dev_ptr"] = srg_idx

        handler = Phase5InsertEffectsHandler()
        prompt_res = handler.prompt(session)

        q = prompt_res.get("question", "")
        assert "Surge XT Effects" in q
        assert "Chow Tape" in q or "Analog Tape Bus" in q

    def test_phase_5_sculpts_and_saves_surge_xt_chain(self):
        session = MockSession()
        session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
        session.data["phase_index"] = 5
        session.data["current_fx_track_ptr"] = 1  # Drums track
        fx_list = ROLE_INSERT_EFFECTS.get("DRUMS", [])
        srg_idx = next(i for i, fx in enumerate(fx_list) if fx["name"] == "Surge XT Effects")
        session.data["current_fx_dev_ptr"] = srg_idx

        handler = Phase5InsertEffectsHandler()
        conn = MagicMock()
        conn.send_command.return_value = {"status": "ok", "devices": [{"name": "Surge XT Effects", "class_name": "PluginDevice"}]}

        user_input = "FX A1 Type: fxt_tape, FX A1 Drive: 0.35, FX A1 Mix: 0.80"
        res = handler.handle(session, conn, user_input)
        drums_trk = session.data["tracks"][1]
        assert drums_trk.get("surge_xt_chain_path") is not None
        assert os.path.exists(drums_trk["surge_xt_chain_path"])


class TestInterceptRouterDecentSamplerCommands:
    """Tests conversational commands for querying and updating Decent Sampler library directory."""

    def test_intercept_query_libraries(self):
        session = MockSession()
        conn = MagicMock()
        res = CopilotInterceptRouter.intercept(session, conn, "ver librerias decent sampler")
        assert res is not None
        assert res.get("status") == "SUCCESS"
        assert "Carpeta de librerías Decent Sampler" in res.get("question", "")

    def test_intercept_change_library_root_valid(self, tmp_path):
        dummy_dir = tmp_path / "MisSonidos"
        dummy_dir.mkdir()
        session = MockSession()
        conn = MagicMock()

        cmd = f"cambiar carpeta de librerias a {dummy_dir}"
        res = CopilotInterceptRouter.intercept(session, conn, cmd)
        assert res is not None
        assert res.get("status") == "LIBRARY_ROOT_UPDATED"
        assert str(dummy_dir.resolve()) in res.get("new_library_root", "")

        # Verify manager reflects updated path
        assert DecentSamplerLibraryManager.get_library_root() == dummy_dir.resolve()

    def test_intercept_change_library_root_nonexistent(self):
        session = MockSession()
        conn = MagicMock()
        cmd = "cambiar carpeta de librerias a Z:/Ruta/Inexistente/Fantasma"
        res = CopilotInterceptRouter.intercept(session, conn, cmd)
        assert res is not None
        assert res.get("status") == "ERROR"
        assert "Error al configurar carpeta de librerías" in res.get("question", "")
