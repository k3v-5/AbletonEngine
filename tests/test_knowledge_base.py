# tests/test_knowledge_base.py
import pytest
from engine.knowledge import (
    get_scale_notes, get_progression_chords, pattern_to_midi_notes,
    get_patch_recipe, get_eq_preset, get_compressor_preset,
    get_ozone_chain, get_vocal_chain, get_producer_profile,
    get_drum_machine_emulation, get_chopping_guide, PLUGIN_CHAINS
)

def test_scales_and_chords():
    notes = get_scale_notes("C", "minor_natural")
    assert len(notes) >= 7
    chords = get_progression_chords("classic_dark", "C")
    assert len(chords) > 0

def test_serum_patch_recipes():
    recipe = get_patch_recipe("808_sub")
    assert "808 Sub Limpio" in recipe or "Oscillador A" in recipe

def test_fabfilter_presets():
    eq = get_eq_preset("kick")
    assert eq is not None
    assert "Pro-Q" in eq and "Kick" in eq

def test_ozone12_mastering():
    chain = get_ozone_chain("trap")
    assert chain is not None
    assert "Ozone 12" in chain and "Trap" in chain

def test_vocal_chain_10_slots():
    chain = get_vocal_chain("bright_trap")
    assert chain is not None
    assert "Bright Trap" in chain

def test_producers_profiles():
    dilla = get_producer_profile("j_dilla")
    assert dilla is not None
    assert "Dilla" in dilla or "Jay Dee" in dilla
    premier = get_producer_profile("dj_premier")
    assert premier is not None
    assert "Premier" in premier

def test_hardware_emulations():
    sp1200 = get_drum_machine_emulation("sp_1200")
    assert sp1200 is not None
    assert "12-bit" in str(sp1200) or "26" in str(sp1200)
    mpc3000 = get_drum_machine_emulation("mpc_3000")
    assert mpc3000 is not None
