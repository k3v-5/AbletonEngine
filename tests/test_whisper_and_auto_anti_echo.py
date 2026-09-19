# tests/test_whisper_and_auto_anti_echo.py
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

from engine.vocal.room_acoustics_cleaner import RoomAcousticsCleaner
from engine.vocal.whisper_take_slicer import WhisperTakeSlicer
from engine.vocal.vocal_take_slicer import VocalTakeSlicer


# -------------------------------------------------------------------------
# 1. AUTOMATED ROOM ACOUSTICS TUNING TESTS
# -------------------------------------------------------------------------

def test_room_acoustics_auto_tune_live_vocal_chain():
    sr = 44100
    t = np.linspace(0, 1.5, int(1.5 * sr), endpoint=False)
    # 380 Hz room resonance + -36 dB noise floor
    signal = 0.3 * np.sin(2 * np.pi * 380 * t) + 0.015 * np.random.normal(0, 1, len(t))

    mock_conn = MagicMock()
    mock_conn._send_raw.return_value = {
        "status": "success",
        "res_applied": [
            "Gate Threshold set to 0.43 (~-32.5 dBFS)",
            "Gate Release set to 0.20 (~60ms fast cutoff)",
            "EQ Eight Band 2 Freq centered on 380.0 Hz",
            "EQ Eight Band 2 Gain set to -4.5 dB notch cut",
            "Send A (Reverb) clamped to 0.18"
        ]
    }

    res = RoomAcousticsCleaner.auto_tune_live_vocal_chain(
        conn=mock_conn,
        track_index=12,
        audio_data=signal,
        sr=sr
    )

    assert res["status"] == "AUTOMATED_ROOM_ACOUSTICS_TUNED"
    assert res["track_index"] == 12
    assert "tuned_parameters" in res
    assert res["tuned_parameters"]["gate_release_ms"] == 60.0
    assert res["tuned_parameters"]["modal_notch_gain_db"] == -4.5
    assert res["tuned_parameters"]["max_reverb_send"] == 0.18
    assert len(res["live_actions"]) == 5
    assert mock_conn._send_raw.called


# -------------------------------------------------------------------------
# 2. WHISPER TAKE SLICER SEGMENTATION & REFINEMENT TESTS
# -------------------------------------------------------------------------

def test_whisper_take_slicer_fallback_and_zero_crossing():
    sr = 44100
    total_len = int(6.0 * sr)
    audio = np.zeros(total_len, dtype=np.float32)

    # 1.0 - 2.5s: Phrase 1
    t1 = np.linspace(0, 1.5, int(1.5 * sr), endpoint=False)
    audio[int(1.0 * sr) : int(2.5 * sr)] = 0.5 * np.sin(2 * np.pi * 300 * t1)

    # 3.5 - 5.0s: Phrase 2
    t2 = np.linspace(0, 1.5, int(1.5 * sr), endpoint=False)
    audio[int(3.5 * sr) : int(5.0 * sr)] = 0.4 * np.sin(2 * np.pi * 450 * t2)

    # Segment without whisper network call (RMS fallback)
    segments, mono, actual_sr = WhisperTakeSlicer.transcribe_and_segment(audio, sr=sr, model_name="dummy_nonexistent")
    assert len(segments) >= 2
    assert segments[0]["start_sec"] >= 0.8
    assert segments[0]["end_sec"] <= 2.8

    # Refine boundaries with zero-crossing
    refined = WhisperTakeSlicer.refine_slice_boundaries_zero_crossing(mono, actual_sr, segments)
    assert len(refined) == len(segments)
    for r in refined:
        assert "audio" in r
        assert len(r["audio"]) > 0
        # Verify first and last samples are attenuated by micro-fade (close to 0.0)
        assert abs(r["audio"][0]) < 0.05
        assert abs(r["audio"][-1]) < 0.05


def test_whisper_take_slicer_export_and_align(tmp_path):
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    slice_audio = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

    refined = [
        {"index": 0, "text": "Sistema reboot", "start_sec": 0.5, "end_sec": 1.5, "duration_sec": 1.0, "audio": slice_audio, "confidence": 0.95},
        {"index": 1, "text": "Drop the bass", "start_sec": 2.0, "end_sec": 3.0, "duration_sec": 1.0, "audio": slice_audio, "confidence": 0.92}
    ]

    exported = WhisperTakeSlicer.export_slices(sr, refined, output_dir=tmp_path)
    assert len(exported) == 2
    assert Path(exported[0]["file_path"]).exists()
    assert Path(exported[1]["file_path"]).exists()

    cues = [
        {"name": "Intro Hook", "time": 16.0},
        {"name": "Pre-Drop Vacuum", "time": 60.0}
    ]
    aligned = WhisperTakeSlicer.align_slices_to_song_cues(exported, cues=cues, bpm=128.0)
    assert len(aligned) == 2
    assert aligned[0]["destination_beat"] == 16.0
    assert aligned[0]["target_cue"] == "Intro Hook"
    assert aligned[1]["destination_beat"] == 60.0
    assert aligned[1]["target_cue"] == "Pre-Drop Vacuum"


def test_whisper_take_slicer_deploy_to_live():
    mock_conn = MagicMock()
    mock_conn._send_raw.return_value = {"status": "success"}

    aligned = [
        {
            "index": 0,
            "text": "Cyberpunk hook",
            "file_path": "C:/fake/path/vocal_00.wav",
            "file_name": "vocal_00.wav",
            "destination_beat": 32.0,
            "duration_sec": 2.0
        }
    ]

    deploy_res = WhisperTakeSlicer.deploy_slices_to_live(mock_conn, track_index=12, aligned_slices=aligned)
    assert deploy_res["status"] == "SLICES_DEPLOYED_TO_ARRANGEMENT"
    assert deploy_res["deployed_count"] == 1
    assert mock_conn._send_raw.called


def test_vocal_take_slicer_whisper_delegation(tmp_path):
    mock_conn = MagicMock()
    mock_conn._send_raw.return_value = {"status": "success"}

    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    synthetic_take = 0.5 * np.sin(2 * np.pi * 350 * t)

    res = VocalTakeSlicer.process_take_with_whisper(
        conn=mock_conn,
        track_index=12,
        audio_path_or_data=synthetic_take,
        sr=sr,
        cues=[{"name": "Intro", "time": 8.0}],
        bpm=128.0,
        output_dir=str(tmp_path)
    )

    assert "status" in res
    assert res["track_index"] == 12
    assert "aligned_slices" in res


# -------------------------------------------------------------------------
# 3. DOUBLE-WHISPER VERIFICATION GATE & DYNAMIC MULTI-VOICE TESTS
# -------------------------------------------------------------------------

def test_whisper_double_whisper_verification_gate():
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    synthetic_slice = (0.4 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

    # 1. Mock whisper transcribe returning expected text
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "Sistema reboot"}

    with patch.object(WhisperTakeSlicer, "get_whisper_model", return_value=mock_model):
        res = WhisperTakeSlicer.verify_slice_double_whisper(
            slice_audio=synthetic_slice,
            sr=sr,
            expected_text="Sistema reboot"
        )
        assert res["verified"] is True
        assert res["match_ratio"] >= 0.80
        assert res["pass1_text"] == "Sistema reboot"
        assert res["pass2_text"] == "Sistema reboot"

    # 2. Test clipped text (missing word)
    mock_model_clipped = MagicMock()
    mock_model_clipped.transcribe.return_value = {"text": "reboot"}

    with patch.object(WhisperTakeSlicer, "get_whisper_model", return_value=mock_model_clipped):
        res_clipped = WhisperTakeSlicer.verify_slice_double_whisper(
            slice_audio=synthetic_slice,
            sr=sr,
            expected_text="Sistema total reboot sequence"
        )
        assert res_clipped["word_recall"] < 0.70
        assert res_clipped["verified"] is False


def test_whisper_resolve_vocal_track_dynamic():
    mock_conn = MagicMock()
    # Mock finding an existing Backing Vocal track at index 5
    mock_conn._send_raw.return_value = {
        "found": {"index": 5, "name": "Backing Vocal [vocals:backing]", "matched_keyword": True}
    }

    res_backing = WhisperTakeSlicer.resolve_vocal_track(mock_conn, vocal_role="backing")
    assert res_backing["status"] == "TRACK_RESOLVED"
    assert res_backing["track_index"] == 5
    assert "backing" in res_backing["track_name"].lower()
    assert res_backing["role"] == "backing"

    # Mock creating a new track at index 9 for harmony
    mock_conn._send_raw.return_value = {
        "found": {"index": 9, "name": "Harmony Vocal [vocals:harmony]", "created": True}
    }
    res_harmony = WhisperTakeSlicer.resolve_vocal_track(mock_conn, vocal_role="harmony")
    assert res_harmony["track_index"] == 9
    assert res_harmony["was_created"] is True


def test_whisper_export_slices_structured_manifest(tmp_path):
    sr = 44100
    t = np.linspace(0, 0.5, int(0.5 * sr), endpoint=False)
    slice_audio = (0.2 * np.sin(2 * np.pi * 500 * t)).astype(np.float32)

    refined = [{
        "index": 0,
        "text": "Cyber voice",
        "start_sec": 0.0,
        "end_sec": 0.5,
        "duration_sec": 0.5,
        "audio": slice_audio,
        "confidence": 0.95,
        "double_whisper": {"verified": True, "match_ratio": 1.0}
    }]

    exported = WhisperTakeSlicer.export_slices(
        sr=sr,
        refined_slices=refined,
        output_dir=tmp_path,
        take_id="test_take_01",
        role="backing"
    )

    assert len(exported) == 1
    wav_path = Path(exported[0]["file_path"])
    assert wav_path.exists()
    assert "test_take_01_backing" in str(wav_path)

    # Verify take_manifest.json created
    manifest_path = wav_path.parent.parent / "take_manifest.json"
    assert manifest_path.exists()
    import json
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["take_id"] == "test_take_01"
    assert data["role"] == "backing"
    assert data["total_slices"] == 1
    assert data["slices"][0]["double_whisper_verified"] is True


def test_room_acoustics_backing_role():
    mock_conn = MagicMock()
    mock_conn._send_raw.return_value = {
        "status": "success",
        "res_applied": [
            "Gate Threshold set to 0.45",
            "EQ Eight Band 1 High-Pass set to 180 Hz",
            "Send A (Reverb) set to 0.30",
            "Backing track volume attenuated to 0.72 (-4.5 dB)"
        ]
    }

    res = RoomAcousticsCleaner.auto_tune_live_vocal_chain(
        conn=mock_conn,
        track_index=8,
        role="backing"
    )

    assert res["status"] == "AUTOMATED_ROOM_ACOUSTICS_TUNED"
    assert res["role"] == "backing"
    assert res["tuned_parameters"]["max_reverb_send"] == 0.30
    assert res["tuned_parameters"]["depth_attenuation_db"] == -4.5
    assert res["tuned_parameters"]["modal_notch_gain_db"] == -5.0

