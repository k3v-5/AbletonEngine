# tests/test_vocal_slicer_and_acoustics.py
import pytest
import numpy as np
from unittest.mock import MagicMock

from engine.vocal.vocal_take_slicer import VocalTakeSlicer
from engine.vocal.room_acoustics_cleaner import RoomAcousticsCleaner
from engine.mix.mix_auditor_gate import MixAuditorGate
from engine.production.copilot.guided_session import CopilotGuidedSession


# -------------------------------------------------------------------------
# 1. CONTINUOUS TAKE VOCAL SLICER TESTS
# -------------------------------------------------------------------------

def test_vocal_take_slicer_phrase_detection():
    sr = 44100
    # Create 10 seconds of audio:
    # 0.0 - 1.0s: Silence
    # 1.0 - 3.0s: Phrase 1 (Sine speech)
    # 3.0 - 4.5s: Silence
    # 4.5 - 6.5s: Phrase 2 (Sine speech)
    # 6.5 - 8.0s: Silence
    # 8.0 - 9.5s: Phrase 3 (Sine speech)
    # 9.5 - 10.0s: Silence
    total_samples = 10 * sr
    audio = np.zeros(total_samples)

    t1 = np.linspace(0, 2.0, int(2.0 * sr), endpoint=False)
    audio[int(1.0 * sr) : int(3.0 * sr)] = 0.4 * np.sin(2 * np.pi * 220 * t1)

    t2 = np.linspace(0, 2.0, int(2.0 * sr), endpoint=False)
    audio[int(4.5 * sr) : int(6.5 * sr)] = 0.5 * np.sin(2 * np.pi * 330 * t2)

    t3 = np.linspace(0, 1.5, int(1.5 * sr), endpoint=False)
    audio[int(8.0 * sr) : int(9.5 * sr)] = 0.6 * np.sin(2 * np.pi * 440 * t3)

    phrases = VocalTakeSlicer.detect_vocal_phrases(audio, sr=sr, silence_thresh_db=-30.0)
    assert len(phrases) == 3

    assert 0.8 <= phrases[0]["start_time_sec"] <= 1.2
    assert 2.8 <= phrases[0]["end_time_sec"] <= 3.2

    assert 4.3 <= phrases[1]["start_time_sec"] <= 4.7
    assert 6.3 <= phrases[1]["end_time_sec"] <= 6.7

    assert 7.8 <= phrases[2]["start_time_sec"] <= 8.2
    assert 9.3 <= phrases[2]["end_time_sec"] <= 9.7


def test_vocal_take_slicer_cue_alignment():
    phrases = [
        {"index": 0, "start_time_sec": 1.0, "end_time_sec": 3.0, "duration_sec": 2.0, "peak_db": -6.0, "rms_db": -14.0},
        {"index": 1, "start_time_sec": 4.5, "end_time_sec": 6.5, "duration_sec": 2.0, "peak_db": -5.0, "rms_db": -13.0},
        {"index": 2, "start_time_sec": 8.0, "end_time_sec": 9.5, "duration_sec": 1.5, "peak_db": -4.0, "rms_db": -12.0}
    ]

    cues = [
        {"name": "Intro Whisper", "time": 8.0},
        {"name": "Build-up Chant", "time": 24.0},
        {"name": "PRE-DROP VACUUM", "time": 30.0}
    ]

    aligned = VocalTakeSlicer.align_phrases_to_song_cues(phrases, cues, bpm=120.0)
    assert len(aligned) == 3
    assert aligned[0]["destination_beat"] == 8.0
    assert aligned[0]["target_cue"] == "Intro Whisper"
    assert aligned[1]["destination_beat"] == 24.0
    assert aligned[1]["target_cue"] == "Build-up Chant"
    assert aligned[2]["destination_beat"] == 30.0
    assert aligned[2]["target_cue"] == "PRE-DROP VACUUM"

    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {"status": "ok"}
    deploy_res = VocalTakeSlicer.deploy_aligned_slices_to_arrangement(mock_conn, track_index=12, aligned_slices=aligned)
    assert deploy_res["status"] == "SLICES_ALIGNED_AND_DEPLOYED"
    assert deploy_res["slices_deployed"] == 3


# -------------------------------------------------------------------------
# 2. ROOM ACOUSTICS CLEANER TESTS
# -------------------------------------------------------------------------

def test_room_acoustics_diagnosis_and_chain():
    sr = 44100
    # Generate audio with elevated room noise floor (-30 dB) and boxy resonance at 420 Hz
    t = np.linspace(0, 2.0, 2 * sr, endpoint=False)
    signal = 0.3 * np.sin(2 * np.pi * 200 * t) + 0.4 * np.sin(2 * np.pi * 420 * t)
    noise = 0.03 * np.random.normal(0, 1, 2 * sr) # -30 dB noise floor
    room_audio = signal + noise

    diag = RoomAcousticsCleaner.diagnose_room_reverb(room_audio, sr=sr)
    assert diag["status"] == "ANALYSIS_COMPLETE"
    assert diag["room_echo_detected"] is True
    assert 380.0 <= diag["boxy_resonance_hz"] <= 460.0
    assert len(diag["recommendations"]) == 3

    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {"status": "ok"}
    chain_res = RoomAcousticsCleaner.deploy_anti_room_chain(mock_conn, track_index=12, diagnosis=diag)
    assert chain_res["status"] == "ANTI_ROOM_CHAIN_DEPLOYED"
    assert chain_res["devices_applied"] == 2
    assert chain_res["modal_frequency_cut_hz"] == diag["boxy_resonance_hz"]


# -------------------------------------------------------------------------
# 3. PRESCRIPTIVE MIX AUDITOR GATE TESTS
# -------------------------------------------------------------------------

def test_mix_auditor_masking_detection_and_enforcement():
    tracks = [
        {"index": 0, "name": "Drums Group", "role": "BUS", "volume": 0.85, "is_foldable": True},
        {"index": 2, "name": "Drums", "role": "DRUMS", "volume": 0.85}, # Offending (> 0.70)
        {"index": 4, "name": "Lead 1", "role": "LEAD", "volume": 0.85},  # Offending (> 0.62)
        {"index": 6, "name": "Synth 1", "role": "BASS", "volume": 0.85}, # Offending (> 0.68)
        {"index": 10, "name": "Pad 1", "role": "PAD", "volume": 0.85},   # Offending (> 0.58)
        {"index": 12, "name": "Lead Vocal", "role": "VOCALS", "volume": 0.85}
    ]

    mock_conn = MagicMock()
    audit_report = MixAuditorGate.audit_session_balance(mock_conn, tracks)
    assert audit_report["passed"] is False
    assert audit_report["status"] == "CRITICAL_MASKING_DETECTED"
    assert audit_report["offending_tracks_count"] >= 4
    assert len(audit_report["prescriptions"]) >= 4

    # Enforce prescriptions
    mock_conn.send_command.return_value = {"status": "ok"}
    enforce_res = MixAuditorGate.enforce_mix_prescriptions(mock_conn, audit_report)
    assert enforce_res["status"] == "PRESCRIPTIONS_ENFORCED"
    assert enforce_res["tracks_calibrated"] >= 4
    assert enforce_res["mix_headroom_secured"] is True


# -------------------------------------------------------------------------
# 4. GUIDED SESSION INTEGRATION TEST
# -------------------------------------------------------------------------

def test_guided_session_continuous_take_and_mix_balance(tmp_path, monkeypatch):
    test_state_file = tmp_path / "guided_session.json"
    monkeypatch.setattr(CopilotGuidedSession, "STATE_FILE", test_state_file)

    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {"status": "ok"}

    session = CopilotGuidedSession()
    session.data["current_phase"] = "PHASE_9_COMPLETED"
    session.data["phase_index"] = 9
    session.data["tracks"] = [
        {"index": 2, "name": "Drums", "role": "DRUMS", "volume": 0.85},
        {"index": 4, "name": "Lead 1", "role": "LEAD", "volume": 0.85},
        {"index": 6, "name": "Synth 1", "role": "BASS", "volume": 0.85},
        {"index": 10, "name": "Pad 1", "role": "PAD", "volume": 0.85},
        {"index": 12, "name": "Lead Vocal", "role": "VOCALS", "volume": 0.85}
    ]
    session.data["sections"] = [
        {"name": "Intro", "time": 8.0},
        {"name": "Build-up", "time": 24.0},
        {"name": "Pre-Drop", "time": 30.0}
    ]
    session.data["genre"] = "CYBERPUNK"
    session.data["bpm"] = 128.0
    session._save_state()

    # User announces long-take recording with room echo and mix imbalance
    res = session.step(conn=mock_conn, user_input="Toma continua grabada, hay mucho eco en mi habitacion y la musica ahoga la voz")
    assert res["status"] == "VOCALS_PROCESSED"
    assert "TOMA CONTINUA REBANADA" in res["current_step"]
    assert "Rebanado y Auto-Alineación" in res["question"]
    assert "Tratamiento Anti-Eco" in res["question"]
    assert "Auditor de Mezcla Prescriptivo" in res["question"]
    assert "aligned_slices" in res
    assert len(res["aligned_slices"]) == 3
