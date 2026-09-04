"""
Tests for Temporal Analysis Engine (PIE Phase 7).
Validates RMS, peak, crest factor, and frame sequence generation.
"""
import pytest
import numpy as np

from engine.forensics.temporal import TemporalEngine
from engine.forensics.models import AnalysisConfig, AudioFrame


class TestForensicsTemporal:

    def test_rms_and_peak_calculations(self):
        # 0.5 amplitude square wave: RMS = 0.5, peak = 0.5
        square = 0.5 * np.ones(1000)
        rms = TemporalEngine.calculate_frame_rms(square)
        peak = TemporalEngine.calculate_frame_peak(square)

        expected_db = 20.0 * np.log10(0.5)
        assert abs(rms - expected_db) < 1e-3
        assert abs(peak - expected_db) < 1e-3

        # Crest factor for square wave should be ~0 dB
        cf = TemporalEngine.calculate_crest_factor(peak, rms)
        assert abs(cf) < 1e-2

        # Sine wave: RMS = peak / sqrt(2) -> Crest factor ~ 3.01 dB
        t = np.linspace(0, 1.0, 1000, endpoint=False)
        sine = 0.8 * np.sin(2 * np.pi * 10 * t)
        sine_rms = TemporalEngine.calculate_frame_rms(sine)
        sine_peak = TemporalEngine.calculate_frame_peak(sine)
        sine_cf = TemporalEngine.calculate_crest_factor(sine_peak, sine_rms)
        assert abs(sine_cf - 3.01) < 0.2

    def test_analyze_frames_sequence(self):
        sr = 44100
        n_samples = 44100 // 2  # 0.5s
        t = np.linspace(0, 0.5, n_samples, endpoint=False)
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)

        cfg = AnalysisConfig(fft_size=1024, hop_size=256)
        frames = TemporalEngine.analyze_frames(audio, sr, cfg)

        assert len(frames) > 0
        assert isinstance(frames[0], AudioFrame)

        # Monotonicity checks
        for i in range(len(frames) - 1):
            assert frames[i].index == i
            assert frames[i + 1].start_sample > frames[i].start_sample
            assert frames[i + 1].start_time_seconds > frames[i].start_time_seconds
            assert frames[i].end_time_seconds > frames[i].start_time_seconds

        # Sanity check values
        for f in frames:
            assert -40.0 < f.rms_dbfs < 0.0
            assert -40.0 < f.peak_dbfs <= 0.0
            assert f.spectral_centroid_hz > 0.0
