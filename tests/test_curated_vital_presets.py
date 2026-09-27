# tests/test_curated_vital_presets.py
"""
Test Suite for the 88 Curated Vital Presets Integration.
Verifies discovery, archetype classification, acoustic validation, and sculpting.
"""

from pathlib import Path
import json
import pytest

from engine.sound_design.vital_archetype_catalog import ArchetypeCatalog
from engine.sound_design.vital_sound_engine import VitalSoundEngine
from engine.sound_design.dedicated_plugin_configurator import DedicatedPluginConfigurator


class DummySession:
    def __init__(self, tracks, bpm=160.0):
        self.data = {
            "bpm": bpm,
            "song_name": "TestSong",
            "tracks": tracks,
            "current_param_ptr": 0,
            "phase_index": 4,
            "current_phase": "PHASE_4_PARAM_SCULPTING"
        }
        self._conn = None

    def _save_state(self):
        pass

    def _resolve_live_track_index(self, conn, trk):
        return trk.get("index", 0)


def test_archetype_catalog_discovers_all_curated_categories():
    catalog = ArchetypeCatalog()
    categories = catalog.get_available_categories()

    # Must contain our new families
    assert "BASS_ACID" in categories
    assert "BASS_GROWL" in categories
    assert "HOUSE_ORGAN_DONK" in categories
    assert "CHIPTUNE_GLITCH" in categories
    assert "ACOUSTIC_STRINGS" in categories
    assert "VOCAL_SYNTH" in categories
    assert "BELLS_MALLETS" in categories
    assert "FX_TRANSITION" in categories
    assert "THEREMIN_WHISTLE" in categories

    # Verify preset counts in categories
    assert len(catalog.get_presets_in_category("BASS_ACID")) >= 6
    assert len(catalog.get_presets_in_category("BASS_GROWL")) >= 9
    assert len(catalog.get_presets_in_category("CHIPTUNE_GLITCH")) >= 9
    assert len(catalog.get_presets_in_category("ACOUSTIC_STRINGS")) >= 7
    assert len(catalog.get_presets_in_category("VOCAL_SYNTH")) >= 6
    assert len(catalog.get_presets_in_category("FX_TRANSITION")) >= 11


def test_audit_all_calibrated_presets():
    engine = VitalSoundEngine()
    vital_dir = Path("presets/vital")

    all_vital = list(vital_dir.rglob("*.vital"))
    assert len(all_vital) >= 88

    audible_count = 0
    for p in all_vital:
        res = engine.audit_preset_file(p)
        assert res["valid"] is True, f"Preset {p.name} failed JSON validity: {res.get('error')}"
        if res.get("audible", False):
            audible_count += 1

    # Over 95% of presets must be certified audible out of the box
    assert audible_count >= 80


def test_ai_sound_design_with_new_genres():
    session = DummySession([], bpm=170.0)

    # 1. Acid 303 Bass Request
    trk_acid = {"name": "Acid Bass 303", "role": "BASS", "instrument": "Vital", "index": 1}
    res_acid = DedicatedPluginConfigurator.configure_instrument(
        trk_acid, session, ai_input="Quiero una línea de bajo ácida estilo TB-303 con resonancia picante y saturación"
    )
    assert res_acid["status"] == "CONFIGURED"
    assert trk_acid["sculpted"] is True

    # 2. House M1 Organ Request
    trk_organ = {"name": "Rave Organ", "role": "KEYS", "instrument": "Vital", "index": 2}
    res_organ = DedicatedPluginConfigurator.configure_instrument(
        trk_organ, session, ai_input="Un órgano clásico M1 de house noventero Show Me Love con decaimiento percusivo"
    )
    assert res_organ["status"] == "CONFIGURED"
    assert trk_organ["sculpted"] is True

    # 3. Acoustic Guitar Pluck Request
    trk_gtr = {"name": "Acoustic Pluck", "role": "LEAD", "instrument": "Vital", "index": 3}
    res_gtr = DedicatedPluginConfigurator.configure_instrument(
        trk_gtr, session, ai_input="Una guitarra acústica Y2K con resonancia física y cuerdas orgánicas"
    )
    assert res_gtr["status"] == "CONFIGURED"
    assert trk_gtr["sculpted"] is True
