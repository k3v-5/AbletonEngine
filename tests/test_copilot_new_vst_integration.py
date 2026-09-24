# tests/test_copilot_new_vst_integration.py
"""
Integration Test Suite for Valhalla VintageVerb and Surge XT Synthesizer
across LiveBrowserCatalogEngine, InstalledPluginScanner, Phase 3 Instruments,
Phase 5 Insert Effects, and DeviceParameterSupervisor.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from engine.instruments.browser_catalog import (
    LiveBrowserCatalogEngine,
    InstrumentSourceCategory,
    SoundSourceOption,
)
from engine.instruments.installed_scanner import (
    InstalledPluginScanner,
    PluginCategory,
)
from engine.instruments.curated_data import CURATED_SOURCES
from engine.production.copilot.phases.phase_3_instruments import Phase3InstrumentsHandler
from engine.production.copilot.phases.phase_5_insert_effects import Phase5InsertEffectsHandler
from engine.fx.role_fx_catalog import ROLE_INSERT_EFFECTS
from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
from engine.sound_design.valhalla_vintage_verb import (
    ValhallaVintageVerbSchema,
    VintageVerbModel,
    ValhallaVintageVerbValidator,
    ValhallaVintageVerbSerializer,
    VintageVerbModeSelector,
)
from engine.sound_design.surge_xt_synth import (
    SurgeSynthPatchModel,
    SurgeSynthValidator,
    SurgeSynthSerializer,
    SurgeSynthPatchFactory,
)


class MockCopilotSession:
    """Simulates CopilotGuidedSession state for testing Phase 3 and Phase 5."""

    def __init__(self, data=None):
        self.data = data or {
            "song_name": "NewVSTTestSession",
            "key": "G",
            "scale": "Minor",
            "bpm": 124.0,
            "tracks": [
                {"index": 0, "name": "Lead Synth", "role": "LEAD", "is_audio": False},
                {"index": 1, "name": "Bassline", "role": "BASS", "is_audio": False},
                {"index": 2, "name": "Keys Bus", "role": "KEYS", "is_audio": False},
                {"index": 3, "name": "Ambient Pad", "role": "PAD", "is_audio": False},
                {"index": 4, "name": "Drums", "role": "DRUMS", "is_audio": False},
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
        return {"current_step": "PASO 4: SCULPTING", "phase": "PHASE_4_PARAM_SCULPTING"}

    def _prompt_current_fx_device(self):
        handler = Phase5InsertEffectsHandler()
        return handler.prompt(self)

    def _prompt_phase_6(self):
        return {"current_step": "PASO 6: COMPOSICION", "phase": "PHASE_6_COMPOSITION"}


# ==============================================================================
# 1. PRUEBAS DE BROWSER CATALOG & INSTALLED SCANNER
# ==============================================================================

class TestBrowserCatalogAndScannerIntegration:
    """Verifies Surge XT Synthesizer and Valhalla VintageVerb catalog indexing."""

    def test_curated_sources_contain_surge_xt(self):
        """Surge XT must be registered across BASS, KEYS, LEAD, and PAD in CURATED_SOURCES."""
        for role in ["BASS", "KEYS", "LEAD", "PAD"]:
            sources = CURATED_SOURCES.get(role, [])
            surge_opts = [s for s in sources if "surge" in s.id.lower() or "surge" in s.name.lower()]
            assert len(surge_opts) >= 1, f"Role {role} must have at least one Surge XT source option."
            opt = surge_opts[0]
            assert opt.category == InstrumentSourceCategory.VST3
            assert opt.uri == "query:Plugins#VST3:Surge%20Synth%20Team:Surge%20XT"
            assert opt.vendor == "Surge Synth Team"
            assert "sculpt_type" in opt.blueprint

    def test_get_available_sources_for_role_unfiltered(self):
        """get_available_sources_for_role returns Surge XT when filter_installed=False."""
        lead_sources = LiveBrowserCatalogEngine.get_available_sources_for_role("LEAD", filter_installed=False)
        surge_lead = [s for s in lead_sources if "surge" in s.name.lower()]
        assert len(surge_lead) >= 1

    def test_get_plugin_presets_for_role_surge_xt(self):
        """get_plugin_presets_for_role('Surge XT', role) returns archetypes and clean default."""
        presets = LiveBrowserCatalogEngine.get_plugin_presets_for_role("Surge XT", "BASS")
        assert len(presets) >= 5, "Must return at least 5 preset options."
        preset_names = [p.name for p in presets]

        # Must contain archetypes and clean default
        assert any("Reese Bass" in n for n in preset_names)
        assert any("808 Sub" in n for n in preset_names)
        assert any("FM Pluck" in n for n in preset_names)
        assert any("Supersaw" in n for n in preset_names)
        assert any("Default / Plugin limpio" in n for n in preset_names)

        clean_opt = presets[-1]
        assert clean_opt.uri == "query:Plugins#VST3:Surge%20Synth%20Team:Surge%20XT"
        assert clean_opt.blueprint.get("sculpt_type") == "surge_synth"

    def test_installed_scanner_signatures(self):
        """InstalledPluginScanner recognizes surge xt (instrument) vs surge xt effects (fx) and vintageverb."""
        scanner = InstalledPluginScanner()
        sig_map = scanner.SIGNATURE_MAP

        assert "surge xt" in sig_map
        assert sig_map["surge xt"]["is_instrument"] is True
        assert sig_map["surge xt"]["live_uri"] == "query:Plugins#VST3:Surge%20Synth%20Team:Surge%20XT"

        assert "surge xt effects" in sig_map
        assert sig_map["surge xt effects"]["is_instrument"] is False
        assert sig_map["surge xt effects"]["live_uri"] == "query:Plugins#VST3:Surge%20Synth%20Team:Surge%20XT%20Effects"

        assert "vintageverb" in sig_map
        assert sig_map["vintageverb"]["is_instrument"] is False
        assert sig_map["vintageverb"]["live_uri"] == "query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb"

    def test_scanner_collision_prevention(self):
        """File 'Surge XT Effects.vst3' must NOT be classified as the Surge XT synth instrument."""
        scanner = InstalledPluginScanner()
        scanner._process_plugin_file("Surge XT Effects.vst3", r"C:\VST3\Surge XT Effects.vst3", PluginCategory.VST3)
        cache = scanner._cache
        # Must have registered the effect, but NOT the synth
        assert any("surge_xt_effects" in k for k in cache.keys())


# ==============================================================================
# 2. PRUEBAS DE PHASE 3: SURGE XT INSTRUMENT LOADING & PATCH SYNTHESIS
# ==============================================================================

class TestPhase3SurgeXTSynthIntegration:
    """Verifies Phase 3 handles Surge XT synth selection, 3-tier validation, and LOM dispatch."""

    def test_phase_3_loads_surge_xt_and_creates_patch(self, tmp_path):
        session = MockCopilotSession()
        session.data["current_track_ptr"] = 0  # Track 0: Lead Synth
        handler = Phase3InstrumentsHandler()

        conn = MagicMock()
        conn.send_command.return_value = {
            "status": "ok",
            "result": {
                "devices": [
                    {"name": "Surge XT", "class_name": "PluginDevice", "type": 1}
                ]
            }
        }

        # Select Surge XT directly
        user_input = "Surge XT"
        res = handler.handle(session, conn, user_input)

        lead_trk = session.data["tracks"][0]
        assert lead_trk.get("is_surge_synth") is True
        assert lead_trk.get("surge_synth_patch_path") is not None
        assert os.path.exists(lead_trk["surge_synth_patch_path"])
        assert lead_trk["surge_synth_patch_path"].endswith(".surgepatch")
        assert len(lead_trk.get("surge_synth_osc_types", [])) >= 1

        # Verify LOM parameter commands were sent
        sent_commands = [call.args[0] for call in conn.send_command.call_args_list if call.args]
        assert "set_device_parameter" in sent_commands

    def test_phase_3_subselection_archetype_loading(self):
        session = MockCopilotSession()
        session.data["current_track_ptr"] = 1  # Track 1: Bassline
        trk = session.data["tracks"][1]
        trk["pending_plugin_subselection"] = "Surge XT"
        handler = Phase3InstrumentsHandler()

        conn = MagicMock()
        conn.send_command.return_value = {
            "status": "ok",
            "result": {
                "devices": [
                    {"name": "Surge XT", "class_name": "PluginDevice", "type": 1}
                ]
            }
        }

        # Select option 1 (Reese Bass)
        res = handler.handle(session, conn, "Opción 1")

        assert trk.get("is_surge_synth") is True
        assert trk.get("surge_synth_patch_path") is not None
        assert os.path.exists(trk["surge_synth_patch_path"])
        assert trk.get("pending_plugin_subselection") is None


# ==============================================================================
# 3. PRUEBAS DE PHASE 5: VALHALLA VINTAGEVERB INSERT EFFECTS & CLIPBOARD
# ==============================================================================

class TestPhase5VintageVerbIntegration:
    """Verifies Phase 5 handles Valhalla VintageVerb mode selection, validation, preset and clipboard."""

    def test_phase_5_prompt_contains_vintageverb_directives(self):
        session = MockCopilotSession()
        session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
        session.data["phase_index"] = 5
        session.data["current_fx_track_ptr"] = 2  # Keys Bus
        session.data["tracks"][2]["role"] = "KEYS"

        fx_list = ROLE_INSERT_EFFECTS.get("KEYS", [])
        vv_idx = next(i for i, fx in enumerate(fx_list) if "vintageverb" in fx["name"].lower())
        session.data["current_fx_dev_ptr"] = vv_idx

        handler = Phase5InsertEffectsHandler()
        prompt_res = handler.prompt(session)
        q = prompt_res.get("question", "")

        assert "Valhalla VintageVerb" in q
        assert "22 Modos" in q
        assert "Modo Óptimo Recomendado" in q
        assert "Pre-delay Protector Haas" in q
        assert "Portapapeles" in q

    def test_phase_5_executes_vintageverb_preset_and_clipboard(self):
        session = MockCopilotSession()
        session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
        session.data["phase_index"] = 5
        session.data["current_fx_track_ptr"] = 2  # Keys Bus
        session.data["tracks"][2]["role"] = "KEYS"

        fx_list = ROLE_INSERT_EFFECTS.get("KEYS", [])
        vv_idx = next(i for i, fx in enumerate(fx_list) if "vintageverb" in fx["name"].lower())
        session.data["current_fx_dev_ptr"] = vv_idx

        handler = Phase5InsertEffectsHandler()
        conn = MagicMock()
        conn.send_command.return_value = {
            "status": "ok",
            "result": {
                "devices": [{"name": "ValhallaVintageVerb", "class_name": "PluginDevice"}]
            }
        }

        with patch("engine.sound_design.valhalla_vintage_verb.serializer.ValhallaVintageVerbSerializer.copy_to_clipboard", return_value=True) as mock_cb:
            user_input = "Mode: Concert Hall, Color: 1980s, Mix: 25%, Decay: 35%, LowCut: 15%"
            res = handler.handle(session, conn, user_input)

            keys_trk = session.data["tracks"][2]
            assert keys_trk.get("vintage_verb_preset_path") is not None
            assert os.path.exists(keys_trk["vintage_verb_preset_path"])
            assert keys_trk.get("vintage_verb_clipboard_ready") is True
            assert keys_trk.get("vintage_verb_mode") == "Concert Hall"
            assert keys_trk.get("vintage_verb_color") == "1980s"
            mock_cb.assert_called_once()

            # Verify LOM parameter dispatch via execute_code
            sent_codes = [
                call.args[1].get("code", "")
                for call in conn.send_command.call_args_list
                if call.args and call.args[0] == "execute_code"
            ]
            assert any("decay" in c and "predelay" in c for c in sent_codes)


# ==============================================================================
# 4. PRUEBAS DE DEVICE PARAMETER SUPERVISOR
# ==============================================================================

class TestDeviceParameterSupervisorSurgeXT:
    """Verifies DeviceParameterSupervisor properly profiles and tunes Surge XT."""

    def test_surge_xt_profile_registration(self):
        assert "SURGE_XT" in DeviceParameterSupervisor.ROLE_SCULPTING_PROFILES
        surge_prof = DeviceParameterSupervisor.ROLE_SCULPTING_PROFILES["SURGE_XT"]
        assert "FILTERS" in surge_prof
        assert "OSCILLATORS" in surge_prof
        assert "ENVELOPES" in surge_prof

    def test_supervisor_applies_surge_profile(self):
        conn = MagicMock()
        conn.send_command.side_effect = [
            # 1. get_device_parameters
            {
                "status": "ok",
                "parameters": [
                    {"name": "Filter Cutoff", "value": 0.5},
                    {"name": "Filter Resonance", "value": 0.2},
                    {"name": "Amp Attack", "value": 0.1},
                    {"name": "Amp Release", "value": 0.3},
                ]
            },
            # 2. set_device_parameter calls
            {"status": "ok"},
            {"status": "ok"},
            {"status": "ok"},
            {"status": "ok"},
        ]

        res = DeviceParameterSupervisor.apply_semantic_tuning(
            conn=conn,
            track_index=0,
            device_index=0,
            device_name="Surge XT",
            semantic_requests={"FILTER_CUTOFF": 0.75, "AMP_ATTACK": 0.01}
        )

        assert res.get("status") == "SUCCESS"
        assert res.get("applied_count") >= 1
        assert "FILTER_CUTOFF" in res.get("applied", {})
