# tests/test_dedicated_plugin_configurator.py
import json
from pathlib import Path
import pytest
from unittest.mock import MagicMock
from engine.sound_design.dedicated_plugin_configurator import DedicatedPluginConfigurator
from engine.production.copilot.phases.phase_4_param_sculpting import Phase4ParamSculptingHandler
from engine.production.copilot.phases.phase_5_insert_effects import Phase5InsertEffectsHandler


class DummySession:
    def __init__(self, tracks, bpm=160.0):
        self.data = {
            "bpm": bpm,
            "song_name": "TestSong",
            "tracks": tracks,
            "current_param_ptr": 0,
            "current_fx_track_ptr": 0,
            "current_fx_dev_ptr": 0,
            "current_fx_ptr": 0,
            "phase_index": 4,
            "current_phase": "PHASE_4_PARAM_SCULPTING"
        }
        self._conn = None

    def _save_state(self):
        pass

    def _resolve_live_track_index(self, conn, trk):
        return trk.get("index", 0)

    def _prompt_current_track_params(self):
        handler = Phase4ParamSculptingHandler()
        return handler.prompt(self)

    def _prompt_current_fx_device(self):
        handler = Phase5InsertEffectsHandler()
        return handler.prompt(self)

    def _prompt_phase_6(self):
        return {"phase": "PHASE_6_COMPOSITION", "status": "READY"}


def test_is_dedicated_instrument():
    assert DedicatedPluginConfigurator.is_dedicated_instrument("Decent Sampler (DR Cathedral Piano)") is True
    assert DedicatedPluginConfigurator.is_dedicated_instrument("Surge Synth Team Surge XT") is True
    assert DedicatedPluginConfigurator.is_dedicated_instrument("Vital Audio Vital") is True
    assert DedicatedPluginConfigurator.is_dedicated_instrument("Surge XT Effects") is False
    assert DedicatedPluginConfigurator.is_dedicated_instrument("Serum 2") is False


def test_is_dedicated_effect():
    assert DedicatedPluginConfigurator.is_dedicated_effect("ValhallaSupermassive") is True
    assert DedicatedPluginConfigurator.is_dedicated_effect("ValhallaVintageVerb") is True
    assert DedicatedPluginConfigurator.is_dedicated_effect("Surge XT Effects") is True
    assert DedicatedPluginConfigurator.is_dedicated_effect("EQ Eight") is False
    assert DedicatedPluginConfigurator.is_dedicated_effect("Glue Compressor") is False


def test_instrument_sculpting_prompts():
    session = DummySession([], bpm=168.0)

    # 1. Vital Prompt
    trk_v = {"name": "Sub 808", "role": "BASS", "instrument": "Vital Audio Vital", "index": 0}
    p_v = DedicatedPluginConfigurator.get_instrument_sculpting_prompt(trk_v, session)
    assert p_v["dedicated_plugin"] == "vital"
    assert "Vital Audio Vital" in p_v["question"]
    assert "BASS_808" in p_v["question"]
    assert "Invariantes 1-8" in p_v["question"]

    # 2. Surge XT Prompt
    trk_s = {"name": "Arp Lead", "role": "LEAD", "instrument": "Surge XT", "index": 1}
    p_s = DedicatedPluginConfigurator.get_instrument_sculpting_prompt(trk_s, session)
    assert p_s["dedicated_plugin"] == "surge_xt_synth"
    assert "Surge XT Synth" in p_s["question"]
    assert "Arquitectura Analógica Clásica" in p_s["question"]

    # 3. Decent Sampler Prompt
    trk_d = {"name": "Piano", "role": "KEYS", "instrument": "Decent Sampler", "index": 2}
    p_d = DedicatedPluginConfigurator.get_instrument_sculpting_prompt(trk_d, session)
    assert p_d["dedicated_plugin"] == "decent_sampler"
    assert "Decent Sampler" in p_d["question"]
    assert "Librerías auditadas" in p_d["question"]


def test_effect_sculpting_prompts():
    session = DummySession([], bpm=168.0)
    trk = {"name": "Synth Lead", "role": "LEAD", "index": 0}

    # 1. Supermassive
    eff_sm = {"name": "ValhallaSupermassive", "uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaSupermassive"}
    p_sm = DedicatedPluginConfigurator.get_effect_sculpting_prompt(trk, eff_sm, dev_ptr=0, session=session)
    assert p_sm["dedicated_plugin"] == "valhalla_supermassive"
    assert "Gemini" in p_sm["question"]
    assert "Hydra" in p_sm["question"]
    assert "Mix <= 15%" in p_sm["question"]

    # 2. VintageVerb
    eff_vv = {"name": "ValhallaVintageVerb", "uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb"}
    p_vv = DedicatedPluginConfigurator.get_effect_sculpting_prompt(trk, eff_vv, dev_ptr=1, session=session)
    assert p_vv["dedicated_plugin"] == "valhalla_vintage_verb"
    assert "1980s" in p_vv["question"]
    assert "Concert Hall" in p_vv["question"]

    # 3. Surge XT Effects
    eff_sfx = {"name": "Surge XT Effects", "uri": "query:Plugins#VST3:Surge%20Synth%20Team:Surge%20XT%20Effects"}
    p_sfx = DedicatedPluginConfigurator.get_effect_sculpting_prompt(trk, eff_sfx, dev_ptr=2, session=session)
    assert p_sfx["dedicated_plugin"] == "surge_xt_effects"
    assert "Analog Tape Bus" in p_sfx["question"]


def test_configure_instrument_vital_with_ai_modeling_and_limits():
    session = DummySession([], bpm=160.0)
    trk = {"name": "808 Bass", "role": "BASS", "instrument": "Vital", "index": 1}

    # AI models the sound as Opción 1 (BASS_808 Saturado)
    res = DedicatedPluginConfigurator.configure_instrument(trk, session, ai_input="Opción 1")
    assert res["status"] == "CONFIGURED"
    assert res["plugin"] == "Vital"
    assert trk.get("vital_archetype") == "BASS_808"
    assert trk.get("sculpted") is True
    assert trk.get("is_vital") is True
    # Engine limits: Bass stereo width must be strictly mono
    assert trk["timbre_dna"]["stereo_width"] <= 0.10


def test_configure_instrument_vital_ai_decides_custom_sound_design():
    session = DummySession([], bpm=160.0)
    trk = {"name": "Hyper Lead", "role": "LEAD", "instrument": "Vital", "index": 2}

    # The AI DECIDES how the sound will be heard (custom natural language design)
    ai_design = (
        "Quiero un lead vocal formante super brillante (0.90), con punch láser agresivo (0.95), "
        "saturación analógica cálida (0.60) y apertura estéreo supersaw amplia para cortar en el drop"
    )
    res = DedicatedPluginConfigurator.configure_instrument(trk, session, ai_input=ai_design)
    assert res["status"] == "CONFIGURED"
    assert trk["sculpted"] is True

    # The AI's decisions are materialized in the sound
    assert trk["timbre_dna"]["brightness"] >= 0.85
    assert trk["timbre_dna"]["transient_strength"] >= 0.90
    assert trk["timbre_dna"]["stereo_width"] >= 0.80

    # The compiled .vital preset physically exists on disk and has content
    preset_p = Path(trk["vital_preset_path"])
    assert preset_p.exists()
    preset_data = json.loads(preset_p.read_text(encoding="utf-8"))
    assert "settings" in preset_data
    # Invariant checks: volume safe, filter cutoff safe
    assert preset_data["settings"]["volume"] >= 0.65
    assert preset_data["settings"]["filter_1_cutoff"] >= 18.0


def test_configure_instrument_surge_xt_with_ai_modeling():
    session = DummySession([], bpm=160.0)
    trk = {"name": "Lead Track", "role": "LEAD", "instrument": "Surge XT", "index": 2}

    # AI models the sound as Opción 2 (Wavetable)
    res = DedicatedPluginConfigurator.configure_instrument(trk, session, ai_input="Opción 2")
    assert res["status"] == "CONFIGURED"
    assert res["plugin"] == "Surge XT"
    assert trk.get("sculpted") is True
    assert trk.get("is_surge_synth") is True
    assert "surge_synth_patch_path" in trk


def test_configure_instrument_decent_sampler_with_ai_modeling():
    session = DummySession([], bpm=160.0)
    trk = {"name": "Acoustic Keys", "role": "KEYS", "instrument": "Decent Sampler", "index": 3}

    # AI models the sound with specific library
    res = DedicatedPluginConfigurator.configure_instrument(trk, session, ai_input="Librería: Cathedral Piano, Opción 1")
    assert res["status"] == "CONFIGURED"
    assert res["plugin"] == "Decent Sampler"
    assert trk.get("sculpted") is True
    assert trk.get("is_decent_sampler") is True
    # Anti-click safety: attack >= 0.005s
    assert trk["decent_sampler_parameters"]["AMP_ATTACK"] >= 0.005


def test_configure_effect_supermassive_with_ai_modeling_and_policy_limits():
    session = DummySession([], bpm=160.0)
    trk = {"name": "Drop Lead", "role": "LEAD", "index": 4}
    eff = {"name": "ValhallaSupermassive", "uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaSupermassive"}

    # AI models the effect as Opción 2 (Hydra Shimmer)
    res = DedicatedPluginConfigurator.configure_effect(trk, eff, dev_idx=1, session=session, ai_input="Opción 2")
    assert res["status"] == "CONFIGURED"
    assert trk.get("supermassive_clipboard_ready") is True
    # Policy limit: lead in drop must have Mix clamped <= 15% (CRASHPOP Rule)
    assert res["parameters"]["Mix"] <= 0.15
    # Feedback safety limit: feedback < 0.95
    assert res["parameters"]["Feedback"] < 0.95
    # Low-cut safety: subbass protected >= 150 Hz (0.15)
    assert res["parameters"]["LowCut"] >= 0.15


def test_configure_effect_vintage_verb_with_ai_modeling():
    session = DummySession([], bpm=160.0)
    trk = {"name": "Vocal Track", "role": "VOCALS", "index": 5}
    eff = {"name": "ValhallaVintageVerb", "uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb"}

    # AI models the effect as Opción 1 (1980s Concert Hall)
    res = DedicatedPluginConfigurator.configure_effect(trk, eff, dev_idx=2, session=session, ai_input="Opción 1")
    assert res["status"] == "CONFIGURED"
    assert trk.get("vintage_verb_clipboard_ready") is True
    assert trk["vintage_verb_color"] in ("1980s", "1970s", "Now")
    assert res["parameters"]["LowCut"] >= 0.18


def test_phase4_interactive_flow_with_dedicated_instrument():
    """Verifies that Phase 4 prompts for AI modeling of dedicated plugins and processes the AI response."""
    tracks = [
        {"name": "Vital Lead", "role": "LEAD", "instrument": "Vital Audio Vital", "index": 0},
        {"name": "Standard Track", "role": "KEYS", "instrument": "Drift", "index": 1}
    ]
    session = DummySession(tracks)
    handler = Phase4ParamSculptingHandler()

    # 1. First prompt must be the Vital dedicated modeling step
    prompt_1 = handler.prompt(session)
    assert prompt_1["phase"] == "PHASE_4_PARAM_SCULPTING"
    assert prompt_1["dedicated_plugin"] == "vital"
    assert "Vital Audio Vital" in prompt_1["question"]

    # 2. AI submits modeling decision ("Opción 1")
    resp_step = handler.handle(session, None, "Opción 1")
    assert tracks[0].get("sculpted") is True
    assert tracks[0].get("vital_archetype") == "LEAD_SAW"
    assert session.data["current_param_ptr"] == 1

    # 3. Next prompt is for the standard instrument on Track 1
    assert "Drift" in resp_step["action_taken"] or "Vital" in resp_step["action_taken"]


def test_phase5_interactive_flow_with_dedicated_effect():
    """Verifies that Phase 5 prompts for AI modeling of dedicated effects and processes the AI response."""
    from engine.fx.role_fx_catalog import ROLE_INSERT_EFFECTS
    tracks = [
        {"name": "Lead Track", "role": "LEAD", "instrument": "Drift", "index": 0}
    ]
    # Temporarily prepend Supermassive to LEAD insert effects for this test
    original_fx = list(ROLE_INSERT_EFFECTS.get("LEAD", []))
    sm_fx = {"name": "ValhallaSupermassive", "uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaSupermassive", "params": []}
    ROLE_INSERT_EFFECTS["LEAD"] = [sm_fx] + original_fx

    try:
        session = DummySession(tracks)
        session.data["phase_index"] = 5
        session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
        handler = Phase5InsertEffectsHandler()

        # 1. First prompt must be Supermassive dedicated spatial modeling step
        prompt_1 = handler.prompt(session)
        assert prompt_1["phase"] == "PHASE_5_INSERT_EFFECTS"
        assert prompt_1["dedicated_plugin"] == "valhalla_supermassive"
        assert "Valhalla Supermassive" in prompt_1["question"]

        # 2. AI submits modeling decision ("Opción 2")
        resp_step = handler.handle(session, None, "Opción 2")
        assert len(tracks[0].get("insert_effects", [])) == 1
        assert tracks[0]["insert_effects"][0]["name"] == "ValhallaSupermassive"
        assert session.data["current_fx_dev_ptr"] == 1
    finally:
        ROLE_INSERT_EFFECTS["LEAD"] = original_fx
