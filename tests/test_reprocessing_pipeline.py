# tests/test_reprocessing_pipeline.py
"""
Unit tests for AudioReprocessingPipeline:
Validates Key & BPM detection, 20-algorithm catalog metadata, dynamic DSP frequency tuning,
audio rendering, and Live audio track deployment.
"""

import pytest
import numpy as np
import soundfile as sf
from pathlib import Path
from unittest.mock import MagicMock

from engine.sound_design.reprocessing_pipeline import (
    AudioReprocessingPipeline,
    CATALOG_METADATA,
    ROOT_INT_TO_NOTE,
    NOTE_TO_ROOT_INT
)
from engine.sound_design.resample_mutation_engine import (
    note_to_freq,
    get_chord_frequencies,
    MUTATION_REGISTRY
)


def test_catalog_completeness():
    """Validates that all 20 UHTS techniques are defined with rich metadata."""
    pipeline = AudioReprocessingPipeline(conn=None)
    catalog = pipeline.get_catalog()
    assert len(catalog) == 20
    assert len(MUTATION_REGISTRY) == 20

    for idx, item in enumerate(catalog, start=1):
        assert item["index"] == idx
        assert item["id"].startswith(f"MUT_{idx:02d}_")
        assert len(item["name"]) > 3
        assert len(item["description"]) > 15
        assert "best_suited_for" in item
        assert "category" in item
        assert "tuning_dependence" in item


def test_key_and_frequency_math():
    """Validates mathematical frequency calculation across notes and chords."""
    # A4 = 440.0 Hz
    assert abs(note_to_freq("A", octave=4) - 440.0) < 0.1
    # C4 = 261.63 Hz
    assert abs(note_to_freq("C", octave=4) - 261.63) < 0.1
    # F3 = 174.61 Hz
    assert abs(note_to_freq("F", octave=3) - 174.61) < 0.1
    # F1 (Sub bass) = 43.65 Hz
    assert abs(note_to_freq("F", octave=1) - 43.65) < 0.1
    # C1 (Sub bass) = 32.70 Hz
    assert abs(note_to_freq("C", octave=1) - 32.70) < 0.1

    # Fm chord in octave 3: F3 (174.61), Ab3 (207.65), C4 (261.63)
    fm_freqs = get_chord_frequencies(key="F", scale="minor", octave=3)
    assert len(fm_freqs) == 3
    assert abs(fm_freqs[0] - 174.61) < 0.5
    assert abs(fm_freqs[1] - 207.65) < 0.5
    assert abs(fm_freqs[2] - 261.63) < 0.5

    # C Major chord in octave 3: C3 (130.81), E3 (164.81), G3 (196.00)
    cmaj_freqs = get_chord_frequencies(key="C", scale="major", octave=3)
    assert len(cmaj_freqs) == 3
    assert abs(cmaj_freqs[0] - 130.81) < 0.5
    assert abs(cmaj_freqs[1] - 164.81) < 0.5
    assert abs(cmaj_freqs[2] - 196.00) < 0.5


def test_detect_project_key_and_bpm_from_live_conn():
    """Validates live LOM query and decoding for Key and BPM."""
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {
        "result": {
            "root_note": 5,      # 5 = F
            "scale_name": "Minor",
            "tempo": 128.0
        }
    }

    pipeline = AudioReprocessingPipeline(conn=mock_conn)
    tuning = pipeline.detect_project_key_and_bpm()
    assert tuning["key"] == "F"
    assert tuning["scale"] == "Minor"
    assert tuning["bpm"] == 128.0
    assert tuning["root_note_int"] == 5


def test_detect_project_key_and_bpm_from_session_data_fallback():
    """Validates fallback to GuidedSession state when live connection is absent."""
    pipeline = AudioReprocessingPipeline(conn=None)
    session_data = {"key": "Eb", "scale": "Major", "bpm": 140.0}
    tuning = pipeline.detect_project_key_and_bpm(session_data=session_data)
    assert tuning["key"] == "Eb"
    assert tuning["scale"] == "Major"
    assert tuning["bpm"] == 140.0


def test_technique_resolution_by_selectors():
    """Validates resolving techniques by number, ID, or partial name."""
    pipeline = AudioReprocessingPipeline(conn=None)

    # By integer / string number
    t2 = pipeline.get_technique_by_selector("2")
    assert t2 is not None
    assert t2["index"] == 2
    assert t2["registry_name"] == "TUNED_COMB_CHIME"

    # By ID
    t5 = pipeline.get_technique_by_selector("MUT_05_SUB_SAFE_LOW_GROWL")
    assert t5 is not None
    assert t5["index"] == 5

    # By partial name
    t14 = pipeline.get_technique_by_selector("stutter chop")
    assert t14 is not None
    assert t14["index"] == 14

    # By Spanish phrase
    t1 = pipeline.get_technique_by_selector("congelamiento espectral")
    assert t1 is not None
    assert t1["index"] == 1


def test_execute_mutation_and_file_generation(tmp_path):
    """Validates executing a mutation with custom Key & BPM and writing 24-bit WAV."""
    # Create test stereo audio
    sr = 44100
    duration_sec = 2.0
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
    sig = np.sin(2.0 * np.pi * 174.61 * t)[:, np.newaxis]
    stereo_sig = np.repeat(sig, 2, axis=1)

    src_file = tmp_path / "test_source.wav"
    sf.write(str(src_file), stereo_sig, sr, subtype="PCM_24")

    pipeline = AudioReprocessingPipeline(conn=None)
    pipeline.MUTATIONS_DIR = tmp_path

    # Execute Technique 2 (Tuned Comb Chime) tuned to C Minor @ 130 BPM
    res = pipeline.execute_mutation(
        source_wav_path=str(src_file),
        technique_selector=2,
        key="C",
        scale="Minor",
        bpm=130.0
    )

    assert res["status"] == "MUTATION_RENDERED"
    assert Path(res["output_path"]).exists()
    assert abs(res["duration"] - duration_sec) < 0.05
    assert res["key"] == "C"
    assert res["bpm"] == 130.0

    # Verify audio properties
    mut_audio, mut_sr = sf.read(res["output_path"])
    assert mut_sr == sr
    assert len(mut_audio) == len(stereo_sig)


def test_deploy_mutated_track_to_live():
    """Validates creating new audio track in Live and placing clip."""
    mock_conn = MagicMock()
    mock_conn.send_command.side_effect = lambda cmd, args: (
        {"result": {"index": 20, "name": "[RESAMPLE 02] Tuned Comb Chime (F Minor)"}} if cmd == "execute_code"
        else {"status": "success"}
    )

    pipeline = AudioReprocessingPipeline(conn=mock_conn)
    deploy_res = pipeline.deploy_mutated_track_to_live(
        mutated_wav_path="cache/resampled_mutations/dummy.wav",
        technique_name="Tuned Comb Chime",
        technique_index=2,
        key="F",
        scale="Minor",
        target_volume=0.75
    )

    assert deploy_res["status"] == "DEPLOYED"
    assert deploy_res["track_index"] == 20
    assert "[RESAMPLE 02]" in deploy_res["track_name"]
    assert deploy_res["clip_index"] == 0

    # Ensure execute_code called song.create_audio_track(-1)
    calls = mock_conn.send_command.call_args_list
    exec_call = [c for c in calls if c[0][0] == "execute_code"][0]
    assert "song.create_audio_track(-1)" in exec_call[0][1]["code"]
