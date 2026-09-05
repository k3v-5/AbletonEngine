# tests/test_resonance_hunter.py
import pytest
import numpy as np
from engine.mix.eq.resonance import ResonanceHunter, ResonantPeak


def test_detect_synthetic_resonance():
    sr = 44100
    t = np.linspace(0, 1.0, sr)
    # Pink noise base + loud harsh harmonic peak at 3200 Hz
    rng = np.random.RandomState(42)
    noise = rng.randn(len(t)) * 0.2
    harsh_tone = np.sin(2 * np.pi * 3200.0 * t) * 1.5
    signal = noise + harsh_tone

    peaks = ResonanceHunter.detect_resonances(
        audio_samples=signal,
        sample_rate=sr,
        sensitivity=0.8,
        max_notches=2
    )

    assert len(peaks) >= 1
    detected_freq = peaks[0].frequency_hz
    # Peak should be identified near 3200 Hz
    assert abs(detected_freq - 3200.0) < 50.0
    assert peaks[0].q_factor >= 6.0
    assert peaks[0].recommended_gain_db < 0.0


def test_resonance_guardrail_cap():
    sr = 44100
    t = np.linspace(0, 1.0, sr)
    # Multiple harsh peaks: 2500, 3100, 4200
    signal = np.sin(2 * np.pi * 2500 * t) + np.sin(2 * np.pi * 3100 * t) + np.sin(2 * np.pi * 4200 * t)

    peaks = ResonanceHunter.detect_resonances(
        audio_samples=signal,
        sample_rate=sr,
        max_notches=2
    )

    # Strictly cannot exceed max_notches=2 per policy
    assert len(peaks) <= 2


def test_generate_eq_eight_parameters():
    peaks = [
        ResonantPeak(frequency_hz=3100.0, prominence_db=9.2, q_factor=8.5, recommended_gain_db=-3.5, band_type="notch")
    ]
    eq_configs = ResonanceHunter.generate_eq_eight_parameters(peaks)
    assert len(eq_configs) == 1
    assert eq_configs[0]["band"] == 1
    assert eq_configs[0]["frequency"] == 3100.0
    assert eq_configs[0]["gain"] == -3.5
    assert eq_configs[0]["q"] == 8.5
