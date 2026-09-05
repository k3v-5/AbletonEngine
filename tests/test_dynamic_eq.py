# tests/test_dynamic_eq.py
import pytest
import numpy as np
from engine.mix.eq.dynamic_eq import DynamicEQEngine, DynamicEQBand


def test_dynamic_eq_band_gain_reduction():
    """Verify gain reduction obeys threshold, ratio, and max cut limits."""
    band = DynamicEQBand(frequency_hz=6800.0, threshold_db=-18.0, ratio=4.0, max_cut_db=-6.0)

    # Below threshold -> 0 dB cut
    assert band.calculate_gain_reduction(-24.0) == 0.0
    assert band.calculate_gain_reduction(-18.0) == 0.0

    # Overshoot 4 dB -> 4 * (1 - 1/4) = 4 * 0.75 = 3.0 dB cut
    gr = band.calculate_gain_reduction(-14.0)
    assert abs(gr - (-3.0)) < 0.01

    # Massive overshoot (0 dB) -> clamped to max_cut_db (-6.0 dB)
    gr_clamped = band.calculate_gain_reduction(0.0)
    assert gr_clamped == -6.0


def test_calculate_sibilance_profile():
    """Verify sibilance profile detection on harsh vs clean synthetic audio."""
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)

    # 1. Harsh audio: strong 7kHz tone
    harsh_signal = 0.5 * np.sin(2 * np.pi * 7000.0 * t) + 0.1 * np.sin(2 * np.pi * 400.0 * t)
    prof_harsh = DynamicEQEngine.calculate_sibilance_profile(harsh_signal, sample_rate=sr)
    assert prof_harsh["severity"] in ("CRITICAL", "HIGH")
    assert prof_harsh["recommended_cut_db"] <= -4.0

    # 2. Warm audio: mostly 200Hz
    warm_signal = 0.5 * np.sin(2 * np.pi * 200.0 * t)
    prof_warm = DynamicEQEngine.calculate_sibilance_profile(warm_signal, sample_rate=sr)
    assert prof_warm["severity"] == "BALANCED"


def test_apply_adaptive_deesser_mock():
    """Verify adaptive de-esser configuration in mock adapter mode."""
    res = DynamicEQEngine.apply_adaptive_deesser(conn=None, track_index=4, target_sibilance_freq=6800.0)
    assert res["status"] == "SUCCESS"
    assert res["track_index"] == 4
    assert res["target_freq_hz"] == 6800.0


def test_apply_frequency_unmasking_mock():
    """Verify frequency unmasking sidechain configuration in mock mode."""
    res = DynamicEQEngine.apply_frequency_unmasking(conn=None, target_track_index=9, masking_track_index=4, conflict_freq_hz=300.0)
    assert res["status"] == "SUCCESS"
    assert res["target_track"] == 9
    assert res["masking_track"] == 4
