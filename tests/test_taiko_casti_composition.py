# tests/test_taiko_casti_composition.py
import pytest
from pathlib import Path
import soundfile as sf
import numpy as np

from engine.composition.taiko_casti_composer import TaikoCastiComposer


def test_composer_scenes_count():
    assert TaikoCastiComposer.get_scene_count() == 20
    assert len(TaikoCastiComposer.SCENES) == 20


def test_composer_taiko_notes_validity():
    for idx in range(1, 21):
        notes = TaikoCastiComposer.get_taiko_notes_for_scene(idx)
        assert len(notes) > 0, f"Scene {idx} Taiko notes should not be empty"
        for n in notes:
            assert 0.0 <= n["start_time"] < 16.0
            assert n["duration"] > 0
            assert 1 <= n["velocity"] <= 127
            assert n["pitch"] in [
                TaikoCastiComposer.O_DAIKO,
                TaikoCastiComposer.NAGADO_HIT,
                TaikoCastiComposer.NAGADO_RIM,
                TaikoCastiComposer.SHIME_OPEN,
                TaikoCastiComposer.SHIME_RIM,
                TaikoCastiComposer.BACHI_CLICK,
            ]


def test_composer_harmonic_roles_validity():
    for role in ["bass", "lead", "chords"]:
        for idx in range(1, 21):
            if role == "bass":
                notes = TaikoCastiComposer.get_bass_notes_for_scene(idx)
            elif role == "lead":
                notes = TaikoCastiComposer.get_lead_notes_for_scene(idx)
            else:
                notes = TaikoCastiComposer.get_chord_notes_for_scene(idx)
            
            for n in notes:
                assert 0.0 <= n["start_time"] < 16.0
                assert n["duration"] > 0
                assert 1 <= n["velocity"] <= 127


def test_full_arrangement_timeline_length():
    taiko_arr = TaikoCastiComposer.get_full_arrangement_notes("taiko")
    bass_arr = TaikoCastiComposer.get_full_arrangement_notes("bass")
    lead_arr = TaikoCastiComposer.get_full_arrangement_notes("lead")
    chord_arr = TaikoCastiComposer.get_full_arrangement_notes("chords")

    assert len(taiko_arr) > 100
    assert len(chord_arr) > 50

    # Max start_time should be in the last scene (< 320 beats)
    assert max(n["start_time"] for n in taiko_arr) < 320.0
    assert max(n["start_time"] for n in chord_arr) < 320.0


def test_all_20_pad_assets_exist_and_valid():
    cache_dir = Path(__file__).resolve().parent.parent / "cache" / "resampled_mutations"
    assert cache_dir.exists()

    for item in TaikoCastiComposer.SCENES:
        idx = item["idx"]
        pattern = f"taiko_casti_uhts_{idx:02d}_*.wav"
        matches = list(cache_dir.glob(pattern))
        assert len(matches) == 1, f"Missing asset for scene {idx}: {pattern}"
        
        wav_path = matches[0]
        data, sr = sf.read(str(wav_path))
        assert sr == 44100
        assert len(data) > 0
        peak = np.max(np.abs(data))
        assert 0.1 <= peak <= 1.05, f"Audio signal peak {peak} out of expected range in {wav_path.name}"
