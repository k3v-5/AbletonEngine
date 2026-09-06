# tests/test_preset_catalog.py
import pytest
from engine.presets.catalog import PresetCatalog, preset_catalog
from engine.midi.program_change import MIDIProgramChangeDispatcher, program_change_dispatcher

def test_preset_catalog_initialization():
    cat = PresetCatalog()
    assert cat is not None

def test_preset_catalog_search_arturia():
    results = preset_catalog.search_presets(query="Rhodes", limit=5)
    assert isinstance(results, list)
    if results:
        first = results[0]
        assert "preset_name" in first
        assert "plugin" in first
        assert "loading_method" in first
        assert first["loading_method"] in ["midi_program_change", "user_library_adv"]

def test_preset_catalog_search_fraction():
    results = preset_catalog.search_presets(plugin="Fraction", role="bass", limit=5)
    assert isinstance(results, list)
    if results:
        first = results[0]
        assert first["plugin"] == "Fraction"
        assert first["family"] == "Prototype Audio"
        assert first["loading_method"] == "user_library_adv"

def test_preset_catalog_search_omnisphere():
    results = preset_catalog.search_presets(plugin="Omnisphere", limit=5)
    assert isinstance(results, list)
    assert len(results) > 0
    first = results[0]
    assert first["plugin"] == "Omnisphere"
    assert first["loading_method"] == "midi_program_change"
    assert "program_change_id" in first

def test_preset_catalog_search_massive():
    results = preset_catalog.search_presets(plugin="Massive", limit=5)
    assert isinstance(results, list)
    assert len(results) > 0
    first = results[0]
    assert first["plugin"] == "Massive"
    assert first["loading_method"] == "midi_program_change"

def test_preset_catalog_search_zenology():
    results = preset_catalog.search_presets(plugin="ZENOLOGY", limit=5)
    assert isinstance(results, list)
    assert len(results) > 0
    first = results[0]
    assert first["plugin"] == "ZENOLOGY"
    assert first["loading_method"] == "midi_program_change"

def test_program_change_dispatcher_analog_lab():
    res = program_change_dispatcher.resolve_program_change("Analog Lab V", 12, playlist_or_bank=1)
    assert res["plugin"] == "Analog Lab V"
    assert res["program"] == 12
    assert res["bank_msb"] == 1
    assert res["bank_lsb"] == 0
    assert "Playlist #2" in res["description"]

def test_program_change_dispatcher_omnisphere():
    res = program_change_dispatcher.resolve_program_change("Omnisphere", 3)
    assert res["plugin"] == "Omnisphere"
    assert res["program"] == 3
    assert res["bank_msb"] is None

def test_program_change_dispatcher_massive():
    res = program_change_dispatcher.resolve_program_change("Massive", 10)
    assert res["plugin"] == "Massive"
    assert res["program"] == 10

def test_program_change_dispatcher_zenology():
    res = program_change_dispatcher.resolve_program_change("ZENOLOGY", 5, playlist_or_bank=2)
    assert res["plugin"] == "ZENOLOGY"
    assert res["program"] == 5
    assert res["bank_msb"] == 2
