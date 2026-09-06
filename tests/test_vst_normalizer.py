# tests/test_vst_normalizer.py
import pytest
from engine.instruments.plugins.models import PluginSemanticRole, PluginProfile
from engine.instruments.plugins.registry import PluginRegistry
from engine.instruments.plugins.normalizer import VSTParameterNormalizer

def test_registry_profiles_retrieval():
    reg = PluginRegistry()
    assert reg.get_profile("Vital") is not None
    assert reg.get_profile("Vital VST3") is not None
    assert reg.get_profile("Omnisphere") is not None
    assert reg.get_profile("Analog Lab V") is not None
    assert reg.get_profile("Kontakt 8") is not None
    assert reg.get_profile("Output Thermal") is not None
    assert reg.get_profile("Sausage Fattener") is not None
    assert reg.get_profile("The God Particle") is not None
    assert reg.get_profile("Arturia Efx REFRACT") is not None
    assert reg.get_profile("Arturia Efx MOTIONS") is not None
    assert reg.get_profile("Drift") is not None
    assert reg.get_profile("Glue Compressor") is not None

def test_vital_parameter_resolution():
    norm = VSTParameterNormalizer()
    vital_params = [
        {"index": 0, "name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
        {"index": 1, "name": "filter_1_cutoff", "value": 64.0, "min": 0.0, "max": 127.0},
        {"index": 2, "name": "filter_1_resonance", "value": 0.5, "min": 0.0, "max": 1.0},
        {"index": 3, "name": "distortion_drive", "value": 12.0, "min": 0.0, "max": 40.0},
        {"index": 4, "name": "env_1_attack", "value": 0.01, "min": 0.0, "max": 10.0}
    ]
    
    # Test Cutoff
    res_cutoff = norm.resolve_parameter("Vital", vital_params, PluginSemanticRole.CUTOFF)
    assert res_cutoff.found is True
    assert res_cutoff.parameter_name == "filter_1_cutoff"
    assert res_cutoff.parameter_index == 1
    assert round(res_cutoff.normalized_value, 2) == pytest.approx(0.50, abs=0.01)
    
    # Test Drive
    res_drive = norm.resolve_parameter("Vital", vital_params, PluginSemanticRole.DRIVE)
    assert res_drive.found is True
    assert res_drive.parameter_name == "distortion_drive"
    assert res_drive.parameter_index == 3

def test_omnisphere_parameter_resolution():
    norm = VSTParameterNormalizer()
    omni_params = [
        {"index": 0, "name": "Master Vol", "value": 0.8, "min": 0.0, "max": 1.0},
        {"index": 1, "name": "Filter Freq A", "value": 2000.0, "min": 20.0, "max": 20000.0},
        {"index": 2, "name": "Filter Res A", "value": 0.3, "min": 0.0, "max": 1.0}
    ]
    res_vol = norm.resolve_parameter("Omnisphere 2", omni_params, PluginSemanticRole.VOLUME)
    assert res_vol.found is True
    assert res_vol.parameter_name == "Master Vol"
    
    res_cut = norm.resolve_parameter("Omnisphere", omni_params, PluginSemanticRole.CUTOFF)
    assert res_cut.found is True
    assert res_cut.parameter_name == "Filter Freq A"

def test_analog_lab_parameter_resolution():
    norm = VSTParameterNormalizer()
    al_params = [
        {"index": 0, "name": "Macro 1", "value": 0.6, "min": 0.0, "max": 1.0},
        {"index": 1, "name": "Macro 2", "value": 0.4, "min": 0.0, "max": 1.0},
        {"index": 2, "name": "FX1 Dry/Wet", "value": 0.25, "min": 0.0, "max": 1.0}
    ]
    res_m1 = norm.resolve_parameter("Analog Lab V", al_params, PluginSemanticRole.MACRO_1)
    assert res_m1.found is True
    assert res_m1.parameter_name == "Macro 1"
    
    res_dw = norm.resolve_parameter("Analog Lab V", al_params, PluginSemanticRole.DRY_WET)
    assert res_dw.found is True
    assert res_dw.parameter_name == "FX1 Dry/Wet"

def test_sausage_fattener_and_god_particle():
    norm = VSTParameterNormalizer()
    sausage_params = [
        {"index": 0, "name": "Fatness", "value": 45.0, "min": 0.0, "max": 100.0},
        {"index": 1, "name": "Color", "value": 20.0, "min": 0.0, "max": 100.0},
        {"index": 2, "name": "Gain", "value": 0.0, "min": -24.0, "max": 24.0}
    ]
    res_fat = norm.resolve_parameter("Sausage Fattener", sausage_params, PluginSemanticRole.FATNESS)
    assert res_fat.found is True
    assert res_fat.parameter_name == "Fatness"
    assert round(res_fat.normalized_value, 2) == 0.45
    
    gp_params = [
        {"index": 0, "name": "Input Level", "value": 0.0, "min": -18.0, "max": 18.0},
        {"index": 1, "name": "Amount", "value": 100.0, "min": 0.0, "max": 200.0},
        {"index": 2, "name": "Limiter Ceiling", "value": -0.1, "min": -12.0, "max": 0.0}
    ]
    res_ceil = norm.resolve_parameter("The God Particle", gp_params, PluginSemanticRole.LIMITER_CEILING)
    assert res_ceil.found is True
    assert res_ceil.parameter_name == "Limiter Ceiling"

def test_generic_unknown_plugin_fuzzy_resolution():
    norm = VSTParameterNormalizer()
    # Hypothetical unknown 3rd party synthesizer "Quantum Synth VST3"
    unknown_params = [
        {"index": 0, "name": "Bypass", "value": 0.0, "min": 0.0, "max": 1.0},
        {"index": 1, "name": "Cutoff Frequency", "value": 1200.0, "min": 20.0, "max": 20000.0},
        {"index": 2, "name": "Overdrive Gain", "value": 3.0, "min": 0.0, "max": 10.0},
        {"index": 3, "name": "Wet / Dry Mix", "value": 0.5, "min": 0.0, "max": 1.0}
    ]
    
    # Should resolve Cutoff via fuzzy/substring fallback
    res_cut = norm.resolve_parameter("Quantum Synth VST3", unknown_params, PluginSemanticRole.CUTOFF)
    assert res_cut.found is True
    assert res_cut.parameter_name == "Cutoff Frequency"
    assert res_cut.source in ["canonical_substring", "fuzzy_fallback"]
    
    # Should resolve Drive via fuzzy/substring fallback
    res_drv = norm.resolve_parameter("Quantum Synth VST3", unknown_params, PluginSemanticRole.DRIVE)
    assert res_drv.found is True
    assert res_drv.parameter_name == "Overdrive Gain"

def test_normalization_and_denormalization():
    norm = VSTParameterNormalizer()
    # Normalize
    assert norm.normalize_value(50.0, 0.0, 100.0) == 0.5
    assert norm.normalize_value(-6.0, -12.0, 0.0) == 0.5
    assert norm.normalize_value(200.0, 0.0, 100.0) == 1.0  # clamp
    
    # Denormalize
    assert norm.denormalize_value(0.5, 0.0, 100.0) == 50.0
    assert norm.denormalize_value(0.25, 0.0, 100.0) == 25.0
    with pytest.raises(ValueError):
        norm.denormalize_value(1.5, 0.0, 1.0)


def test_arsenal_plugins_resolution():
    norm = VSTParameterNormalizer()

    # 1. Decapitator
    decap_params = [
        {"index": 0, "name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
        {"index": 3, "name": "Drive", "value": 3.5, "min": 0.0, "max": 10.0},
        {"index": 4, "name": "Punish", "value": 0.0, "min": 0.0, "max": 1.0},
        {"index": 6, "name": "Tone", "value": 0.0, "min": -10.0, "max": 10.0},
    ]
    res = norm.resolve_parameter("Decapitator", decap_params, PluginSemanticRole.DRIVE)
    assert res.found is True
    assert res.parameter_name == "Drive"
    assert res.description != ""

    res_punish = norm.resolve_parameter("Decapitator", decap_params, PluginSemanticRole.PUNISH)
    assert res_punish.found is True
    assert res_punish.parameter_name == "Punish"

    # 2. LittleAlterBoy
    alter_params = [
        {"index": 0, "name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
        {"index": 2, "name": "Pitch", "value": 0.0, "min": -12.0, "max": 12.0},
        {"index": 3, "name": "Formant", "value": 0.0, "min": -12.0, "max": 12.0}
    ]
    res_formant = norm.resolve_parameter("LittleAlterBoy", alter_params, PluginSemanticRole.FORMANT)
    assert res_formant.found is True
    assert res_formant.parameter_name == "Formant"

    # 3. EchoBoy
    echo_params = [
        {"index": 0, "name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
        {"index": 4, "name": "Mix", "value": 0.4, "min": 0.0, "max": 1.0},
        {"index": 12, "name": "Feedback", "value": 0.3, "min": 0.0, "max": 1.0}
    ]
    res_feed = norm.resolve_parameter("EchoBoy", echo_params, PluginSemanticRole.FEEDBACK)
    assert res_feed.found is True
    assert res_feed.parameter_name == "Feedback"

    # 4. soothe2
    soothe_params = [
        {"index": 0, "name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
        {"index": 2, "name": "depth", "value": 0.5, "min": 0.0, "max": 1.0},
        {"index": 3, "name": "sharpness", "value": 0.6, "min": 0.0, "max": 1.0}
    ]
    res_depth = norm.resolve_parameter("soothe2", soothe_params, PluginSemanticRole.SOOTHE_DEPTH)
    assert res_depth.found is True
    assert res_depth.parameter_name == "depth"

    # 5. Serum 2
    serum_params = [
        {"index": 0, "name": "Device On", "value": 1.0, "min": 0.0, "max": 1.0},
        {"index": 15, "name": "A WT Pos", "value": 12.0, "min": 0.0, "max": 256.0},
        {"index": 64, "name": "Filter 1 Freq", "value": 800.0, "min": 20.0, "max": 20000.0},
        {"index": 77, "name": "Macro 1", "value": 0.5, "min": 0.0, "max": 1.0}
    ]
    res_wt = norm.resolve_parameter("Serum 2", serum_params, PluginSemanticRole.WAVETABLE_POS)
    assert res_wt.found is True
    assert res_wt.parameter_name == "A WT Pos"

