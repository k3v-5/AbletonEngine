# tests/test_dedicated_plugin_configurator.py
import pytest
from unittest.mock import MagicMock
from engine.sound_design.dedicated_plugin_configurator import DedicatedPluginConfigurator
from engine.production.copilot.phases.phase_4_param_sculpting import Phase4ParamSculptingHandler
from engine.production.copilot.phases.phase_5_insert_effects import Phase5InsertEffectsHandler


class DummySession:
    def __init__(self, tracks):
        self.data = {
            "bpm": 160.0,
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


def test_configure_instrument_decent_sampler():
    session = DummySession([])
    trk = {"name": "Keys Track", "role": "KEYS", "instrument": "Decent Sampler", "index": 1}
    res = DedicatedPluginConfigurator.configure_instrument(trk, session)
    assert res["status"] == "CONFIGURED"
    assert trk.get("sculpted") is True
    assert trk.get("is_decent_sampler") is True
    assert "decent_sampler_library" in trk


def test_configure_instrument_surge_xt():
    session = DummySession([])
    trk = {"name": "Lead Track", "role": "LEAD", "instrument": "Surge XT", "index": 2}
    res = DedicatedPluginConfigurator.configure_instrument(trk, session)
    assert res["status"] == "CONFIGURED"
    assert trk.get("sculpted") is True
    assert trk.get("is_surge_synth") is True
    assert "surge_synth_patch_path" in trk


def test_configure_instrument_vital():
    session = DummySession([])
    trk = {"name": "Pad Track", "role": "PAD", "instrument": "Vital", "index": 3}
    res = DedicatedPluginConfigurator.configure_instrument(trk, session)
    assert res["status"] == "CONFIGURED"
    assert trk.get("sculpted") is True
    assert trk.get("is_vital") is True
    assert "vital_preset_path" in trk


def test_configure_effect_supermassive():
    session = DummySession([])
    trk = {"name": "Space Pad", "role": "PAD", "index": 4}
    eff = {"name": "ValhallaSupermassive", "uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaSupermassive"}
    res = DedicatedPluginConfigurator.configure_effect(trk, eff, dev_idx=1, session=session)
    assert res["status"] == "CONFIGURED"
    assert trk.get("supermassive_clipboard_ready") is True
    assert "supermassive_mode" in trk


def test_configure_effect_vintage_verb():
    session = DummySession([])
    trk = {"name": "Lead Solo", "role": "LEAD", "index": 5}
    eff = {"name": "ValhallaVintageVerb", "uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb"}
    res = DedicatedPluginConfigurator.configure_effect(trk, eff, dev_idx=2, session=session)
    assert res["status"] == "CONFIGURED"
    assert trk.get("vintage_verb_clipboard_ready") is True
    assert "vintage_verb_mode" in trk


def test_configure_effect_surge_xt_effects():
    session = DummySession([])
    trk = {"name": "FX Riser", "role": "FX", "index": 6}
    eff = {"name": "Surge XT Effects", "uri": "query:Plugins#VST3:Surge%20Synth%20Team:Surge%20XT%20Effects"}
    res = DedicatedPluginConfigurator.configure_effect(trk, eff, dev_idx=3, session=session)
    assert res["status"] == "CONFIGURED"
    assert "surge_xt_chain_path" in trk


def test_phase4_skips_parameter_prompt_for_dedicated_instruments():
    # If session has dedicated instruments, phase 4 configures them and immediately transitions
    tracks = [
        {"name": "Piano", "role": "KEYS", "instrument": "Decent Sampler (DR Cathedral Piano)", "index": 0},
        {"name": "Synth", "role": "LEAD", "instrument": "Surge XT (Lead)", "index": 1},
        {"name": "Atmosphere", "role": "PAD", "instrument": "Vital", "index": 2}
    ]
    session = DummySession(tracks)
    handler = Phase4ParamSculptingHandler()
    prompt = handler.prompt(session)

    # Phase 4 should autonomously configure all 3 and advance to Phase 5 without asking parameter questions!
    assert session.data["current_param_ptr"] == 3
    assert session.data["current_phase"] == "PHASE_5_INSERT_EFFECTS"
    for trk in tracks:
        assert trk.get("sculpted") is True
