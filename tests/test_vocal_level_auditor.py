# tests/test_vocal_level_auditor.py
import pytest
import numpy as np
from unittest.mock import MagicMock
from engine.vocal.vocal_level_auditor import VocalLevelAuditor


def test_analyze_audio_levels_metrics():
    sr = 44100
    t = np.linspace(0, 0.5, int(sr * 0.5))
    # 0.5 amplitude sine wave -> peak is 0.5 (-6.02 dBFS), RMS is ~0.3535 (-9.03 dBFS)
    signal = 0.5 * np.sin(2 * np.pi * 1000.0 * t)

    metrics = VocalLevelAuditor.analyze_audio_levels(signal, sr=sr)
    assert metrics["peak_dbfs"] == pytest.approx(-6.02, abs=0.2)
    assert metrics["rms_dbfs"] == pytest.approx(-9.03, abs=0.2)
    assert metrics["crest_factor_db"] == pytest.approx(3.01, abs=0.3)
    assert metrics["is_clipping"] is False
    assert metrics["is_silent"] is False


def test_audit_vocal_level_nominal_and_overload():
    sr = 44100
    t = np.linspace(0, 0.5, int(sr * 0.5))

    # 1. Hot signal (-9 dBFS RMS) -> should flag TOO_LOUD and recommend ~ -9 dB trim
    hot_sig = 0.5 * np.sin(2 * np.pi * 500.0 * t)
    hot_rep = VocalLevelAuditor.audit_vocal_level(hot_sig, sr=sr, target_rms_dbfs=-18.0)
    assert hot_rep["status"] in ["TOO_LOUD", "NEEDS_CALIBRATION"]
    assert hot_rep["recommended_trim_db"] < -5.0

    # 2. Perfectly leveled signal at -18 dBFS RMS
    # 10^(-18/20) * sqrt(2) ~= 0.178 amplitude
    perfect_sig = 0.178 * np.sin(2 * np.pi * 500.0 * t)
    perfect_rep = VocalLevelAuditor.audit_vocal_level(perfect_sig, sr=sr, target_rms_dbfs=-18.0)
    assert perfect_rep["nominal_aligned"] is True
    assert abs(perfect_rep["recommended_trim_db"]) <= 2.0


def test_audit_vocal_to_playback_smr():
    sr = 44100
    t = np.linspace(0, 0.5, int(sr * 0.5))
    # Test with 2kHz tone in the intelligibility band
    vocal = 0.5 * np.sin(2 * np.pi * 2000.0 * t)
    # Backing at 0.38 amplitude gives ~ +2.4 dB SMR
    backing = 0.38 * np.sin(2 * np.pi * 2000.0 * t)

    smr_rep = VocalLevelAuditor.audit_vocal_to_playback_smr(vocal, backing, sr=sr)
    assert smr_rep["smr_db"] == pytest.approx(2.4, abs=0.5)
    assert smr_rep["passed"] is True
    assert smr_rep["status"] == "OPTIMAL_BALANCE"


def test_calibrate_live_vocal_gain():
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {
        "result": {
            "devices": [
                {"name": "Utility", "class_name": "StereoGain"}
            ]
        }
    }

    sr = 44100
    t = np.linspace(0, 0.5, int(sr * 0.5))
    signal = 0.5 * np.sin(2 * np.pi * 500.0 * t)

    res = VocalLevelAuditor.calibrate_live_vocal_gain(mock_conn, track_index=12, audio_data=signal, sr=sr)
    assert res["status"] == "SUCCESS"
    assert "audit" in res
    assert res["trim_applied_db"] < 0.0 # Attenuation applied
