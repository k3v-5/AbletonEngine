# tests/test_super_vst_deepening.py
"""
Exhaustive Test Suite for Advanced Multi-Slot Surge XT Racks,
Valhalla Supermassive Psychoacoustic Mode Intelligence, and Super-Channel Strip Synergy.
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from engine.sound_design.surge_xt_fx import (
    FXType,
    FXChain,
    SurgeFXSchema,
    SurgeFXSlotModel,
    SurgeFXRackModel,
    SurgeFXValidator,
    SurgeFXSerializer,
    SurgeFXRackFactory,
)
from engine.sound_design.valhalla_supermassive import (
    ValhallaSupermassiveSchema,
    SupermassiveModel,
    ValhallaSupermassiveValidator,
    ValhallaSupermassiveSerializer,
    SupermassiveModeSelector,
)
from engine.production.copilot.phases.phase_5_insert_effects import Phase5InsertEffectsHandler
from engine.fx.role_fx_catalog import ROLE_INSERT_EFFECTS


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
            "song_name": "DeepeningSession",
            "key": "F",
            "scale": "Minor",
            "bpm": 128.0,
            "tracks": [
                {"index": 0, "name": "Keys", "role": "KEYS", "is_audio": False},
                {"index": 1, "name": "Drums", "role": "DRUMS", "is_audio": False},
                {"index": 2, "name": "Bass", "role": "BASS", "is_audio": False},
                {"index": 3, "name": "Lead", "role": "LEAD", "is_audio": False},
                {"index": 4, "name": "Pad", "role": "PAD", "is_audio": False},
            ],
            "current_track_ptr": 0,
            "current_param_ptr": 0,
            "current_fx_track_ptr": 0,
            "current_fx_dev_ptr": 0,
            "current_fx_ptr": 0,
            "current_phase": "PHASE_5_INSERT_EFFECTS",
            "phase_index": 5,
        }

    def _save_state(self):
        pass

    def _resolve_live_track_index(self, conn, trk):
        return trk.get("index", 0)

    def _prompt_current_fx_device(self):
        handler = Phase5InsertEffectsHandler()
        return handler.prompt(self)

    def _prompt_phase_6(self):
        return {"current_step": "PASO 6 DE 7: COMPOSICION", "phase": "PHASE_6_COMPOSITION"}


# ==============================================================================
# 1. PRUEBAS DE SURGE XT MULTI-SLOT RACK FACTORY
# ==============================================================================

class TestSurgeFXRackFactory:
    """Tests multi-slot sound design rack generation for Surge XT."""

    def test_bass_power_rack_structure_and_validation(self):
        rack = SurgeFXRackFactory.build_bass_power_rack(bpm=128.0, drive=0.30, mono_sub=True)
        assert isinstance(rack, SurgeFXRackModel)
        active = rack.get_active_slots()
        assert len(active) == 4, "Bass power rack must have 4 active slots."

        # Verify slot types: CHOW -> EQ -> Conditioner -> Mid-Side
        assert active[0].type == FXType.CHOW
        assert active[1].type == FXType.EQ
        assert active[2].type == FXType.CONDITIONER
        assert active[3].type == FXType.MID_SIDE

        # Verify 3-tier validation passes cleanly
        v_rep = SurgeFXValidator.validate_rack(rack, strict=False)
        assert v_rep.is_valid
        assert len(v_rep.all_errors) == 0

    def test_drum_glue_rack_structure_and_validation(self):
        rack = SurgeFXRackFactory.build_drum_glue_rack(bpm=128.0, drive=0.35, punch=True)
        active = rack.get_active_slots()
        assert len(active) == 3, "Drum glue rack must have 3 active slots."

        # Verify slot types: Tape -> Exciter -> Conditioner
        assert active[0].type == FXType.TAPE
        assert active[1].type == FXType.EXCITER
        assert active[2].type == FXType.CONDITIONER

        v_rep = SurgeFXValidator.validate_rack(rack, strict=False)
        assert v_rep.is_valid

    def test_keys_vintage_rack_structure_and_validation(self):
        rack = SurgeFXRackFactory.build_keys_vintage_rack(bpm=120.0)
        active = rack.get_active_slots()
        assert len(active) == 4, "Keys vintage rack must have 4 active slots."

        assert active[0].type == FXType.ENSEMBLE
        assert active[1].type == FXType.TAPE
        assert active[2].type == FXType.EQ
        assert active[3].type == FXType.MID_SIDE

        v_rep = SurgeFXValidator.validate_rack(rack, strict=False)
        assert v_rep.is_valid

    def test_ambient_pad_rack_structure_and_validation(self):
        rack = SurgeFXRackFactory.build_ambient_pad_rack(bpm=95.0)
        active = rack.get_active_slots()
        assert len(active) == 3, "Pad rack must have 3 active slots."

        assert active[0].type == FXType.NIMBUS
        assert active[1].type == FXType.CHORUS
        assert active[2].type == FXType.REVERB2

        v_rep = SurgeFXValidator.validate_rack(rack, strict=False)
        assert v_rep.is_valid

    def test_lead_overdrive_rack_structure_and_validation(self):
        rack = SurgeFXRackFactory.build_lead_overdrive_rack(bpm=140.0, drive=0.40)
        active = rack.get_active_slots()
        assert len(active) == 3, "Lead rack must have 3 active slots."

        assert active[0].type == FXType.CHOW
        assert active[1].type == FXType.TAPE
        assert active[2].type == FXType.FLOATY_DELAY

        v_rep = SurgeFXValidator.validate_rack(rack, strict=False)
        assert v_rep.is_valid

    def test_to_lom_command_list_generation(self):
        rack = SurgeFXRackFactory.build_bass_power_rack()
        lom_cmds = rack.to_lom_command_list(only_active=True)
        assert len(lom_cmds) > 0

        keys = [k for k, _ in lom_cmds]
        # Must have both canonical LOM name and short alias
        assert "A Insert FX 1 Type" in keys
        assert "FX A1 Type" in keys
        assert "A Insert FX 1 Param 1" in keys
        assert "FX A1 Param 1" in keys
        assert "A Insert FX 2 Type" in keys
        assert "FX A2 Type" in keys

    def test_dynamic_create_role_rack(self):
        for role in ["DRUMS", "BASS", "KEYS", "PAD", "LEAD", "VOCALS", "STRINGS"]:
            rack = SurgeFXRackFactory.create_role_rack(role, bpm=124.0, applied_params={"FX A1 Mix": 0.85})
            assert isinstance(rack, SurgeFXRackModel)
            active = rack.get_active_slots()
            assert len(active) >= 3, f"Role {role} should have at least 3 active slots."
            v_rep = SurgeFXValidator.validate_rack(rack)
            assert v_rep.is_valid


# ==============================================================================
# 2. PRUEBAS DE VALHALLA SUPERMASSIVE PSYCHOACOUSTIC MODE SELECTOR
# ==============================================================================

class TestSupermassiveModeSelector:
    """Tests psychoacoustic mode mapping and mathematical tempo calculations."""

    def test_all_22_modes_registered_and_valid(self):
        assert len(ValhallaSupermassiveSchema.MODE_NAMES) == 22
        for i, name in enumerate(ValhallaSupermassiveSchema.MODE_NAMES):
            f_val = ValhallaSupermassiveSchema.mode_to_float(name)
            assert 0.0 <= f_val <= 1.0
            assert ValhallaSupermassiveSchema.float_to_mode(f_val) == name

    def test_recommend_mode_for_various_roles(self):
        assert SupermassiveModeSelector.recommend_mode_for_role("DRUMS") in ("Lyra", "Capricorn", "Gemini")
        assert SupermassiveModeSelector.recommend_mode_for_role("PAD") in ("Great Annihilator", "Sagittarius", "Andromeda")
        assert SupermassiveModeSelector.recommend_mode_for_role("VOCALS") in ("Virgo", "Centaurus", "Andromeda", "Gemini")
        assert SupermassiveModeSelector.recommend_mode_for_role("FX") in ("Pleiades", "Sirius", "Great Annihilator")

    def test_calculate_bpm_delay_ms_exact_math(self):
        # 120 BPM: quarter note is 500ms
        assert SupermassiveModeSelector.calculate_bpm_delay_ms(120.0, "1/4", "straight") == 500.0
        assert SupermassiveModeSelector.calculate_bpm_delay_ms(120.0, "1/8", "straight") == 250.0
        assert SupermassiveModeSelector.calculate_bpm_delay_ms(120.0, "1/8", "dotted") == 375.0
        assert round(SupermassiveModeSelector.calculate_bpm_delay_ms(120.0, "1/8", "triplet"), 2) == 166.67

        # 140 BPM: quarter note is 60000 / 140 = 428.57ms, 1/8 note = 214.29ms
        assert SupermassiveModeSelector.calculate_bpm_delay_ms(140.0, "1/8", "straight") == 214.29

    def test_calculate_haas_pre_delay(self):
        drum_haas = SupermassiveModeSelector.calculate_haas_pre_delay(120.0, "DRUMS")
        assert drum_haas == 12.0

        vocal_haas = SupermassiveModeSelector.calculate_haas_pre_delay(120.0, "VOCALS")
        assert vocal_haas == 28.0

        pad_haas = SupermassiveModeSelector.calculate_haas_pre_delay(120.0, "PAD")
        assert 30.0 <= pad_haas <= 80.0

    def test_build_role_preset_acoustics_and_validation(self):
        for role in ["KEYS", "PAD", "LEAD", "BASS", "DRUMS"]:
            preset = SupermassiveModeSelector.build_role_preset(
                preset_name=f"Test_{role}",
                role=role,
                bpm=128.0,
                applied_params={"Mix": 0.25, "Feedback": 0.55}
            )
            assert isinstance(preset, SupermassiveModel)
            assert preset.low_cut >= 0.05, "Low cut safety must be enforced."
            assert preset.feedback <= 0.95, "Feedback runaway protection must be enforced."
            v_rep = ValhallaSupermassiveValidator.validate(preset)
            assert v_rep.is_valid, f"Role preset for {role} must be valid."


# ==============================================================================
# 3. PRUEBAS DE INTEGRACIÓN EN PHASE 5 CON LOM DISPATCHING
# ==============================================================================

class TestPhase5DeepeningIntegration:
    """Tests Phase 5 insert effect sculpting with multi-slot Surge XT and intelligent Supermassive."""

    def test_phase_5_prompt_contains_deepened_directives(self):
        session = MockSession()
        handler = Phase5InsertEffectsHandler()

        # Check Surge XT on Drums
        session.data["current_fx_track_ptr"] = 1  # Drums
        fx_list = ROLE_INSERT_EFFECTS.get("DRUMS", [])
        srg_idx = next(i for i, fx in enumerate(fx_list) if fx["name"] == "Surge XT Effects")
        session.data["current_fx_dev_ptr"] = srg_idx

        prompt_res = handler.prompt(session)
        q = prompt_res.get("question", "")
        assert "Surge XT Effects" in q
        assert "Matriz Multi-Slot" in q or "Chow Tape" in q
        assert "3 a 4 procesadores" in q

        # Check Supermassive on Keys
        session.data["current_fx_track_ptr"] = 0  # Keys
        fx_list_keys = ROLE_INSERT_EFFECTS.get("KEYS", [])
        sm_idx = next(i for i, fx in enumerate(fx_list_keys) if fx["name"] == "ValhallaSupermassive")
        session.data["current_fx_dev_ptr"] = sm_idx

        prompt_res_sm = handler.prompt(session)
        q_sm = prompt_res_sm.get("question", "")
        assert "Valhalla Supermassive" in q_sm
        assert "Inteligencia Acústica" in q_sm
        assert "Modo Óptimo Recomendado" in q_sm
        assert "Pre-delay" in q_sm

    def test_phase_5_executes_surge_xt_multi_slot_lom_and_file(self):
        session = MockSession()
        session.data["current_fx_track_ptr"] = 1  # Drums
        fx_list = ROLE_INSERT_EFFECTS.get("DRUMS", [])
        srg_idx = next(i for i, fx in enumerate(fx_list) if fx["name"] == "Surge XT Effects")
        session.data["current_fx_dev_ptr"] = srg_idx

        handler = Phase5InsertEffectsHandler()
        conn = MagicMock()
        conn.send_command.return_value = {"status": "ok", "devices": [{"name": "Surge XT Effects", "class_name": "PluginDevice"}]}

        user_input = "FX A1 Mix: 0.80, Drive: 0.35"
        res = handler.handle(session, conn, user_input)

        drum_trk = session.data["tracks"][1]
        assert drum_trk.get("surge_xt_chain_path") is not None
        assert os.path.exists(drum_trk["surge_xt_chain_path"])
        assert drum_trk.get("surge_xt_active_slots", 0) >= 3

        # Verify LOM parameter calls were sent for multiple slots
        sent_commands = [call.args[0] for call in conn.send_command.call_args_list]
        assert "set_device_parameter" in sent_commands

    def test_phase_5_executes_supermassive_mode_and_clipboard(self):
        session = MockSession()
        session.data["current_fx_track_ptr"] = 0  # Keys
        fx_list_keys = ROLE_INSERT_EFFECTS.get("KEYS", [])
        sm_idx = next(i for i, fx in enumerate(fx_list_keys) if fx["name"] == "ValhallaSupermassive")
        session.data["current_fx_dev_ptr"] = sm_idx

        handler = Phase5InsertEffectsHandler()
        conn = MagicMock()
        conn.send_command.return_value = {"status": "ok", "devices": [{"name": "ValhallaSupermassive", "class_name": "PluginDevice"}]}

        with patch("engine.sound_design.valhalla_supermassive.serializer.ValhallaSupermassiveSerializer.copy_to_clipboard", return_value=True) as mock_cb:
            res = handler.handle(session, conn, "Mix: 25%, Feedback: 50%, Mode: Andromeda")
            keys_trk = session.data["tracks"][0]
            assert keys_trk.get("supermassive_preset_path") is not None
            assert keys_trk.get("supermassive_clipboard_ready") is True
            assert keys_trk.get("supermassive_mode") == "Andromeda"
            mock_cb.assert_called_once()
