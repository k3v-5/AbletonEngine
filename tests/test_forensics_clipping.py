"""
Tests for Clipping & True Peak Detection Engine (PIE Phase 7).
Validates sample clipping clustering, ITU-R BS.1770-5 4x True Peak oversampling,
and severity determination.
"""
import pytest
import numpy as np

from engine.forensics.clipping import ClippingEngine
from engine.forensics.models import ForensicEventType, Severity, AnalysisConfig


class TestForensicsClipping:

    def test_detect_sample_clipping(self):
        sr = 44100
        n_samples = 44100
        audio = np.zeros((1, n_samples), dtype=np.float64)

        # Insert 30 consecutive clipped samples (1.0 = 0 dBFS) at sample 10000 (~0.226s)
        clip_start = 10000
        clip_len = 30
        audio[0, clip_start:clip_start + clip_len] = 1.0

        events = ClippingEngine.detect_sample_clipping(
            audio=audio,
            sample_rate=sr,
            threshold_dbfs=-0.01
        )

        assert len(events) == 1
        ev = events[0]
        assert ev.event_type == ForensicEventType.CLIPPING
        assert ev.severity in (Severity.ERROR, Severity.CRITICAL)
        assert ev.channels == ("M",)
        assert abs(ev.start_time_seconds - (clip_start / sr)) < 1e-4
        assert ev.details["sample_count"] == clip_len

    def test_inter_sample_peak_overshoot(self):
        """
        Synthesizes a classic pathological ISP signal: high-amplitude alternating
        peaks that reconstruct to > 0.0 dBTP via sinc interpolation even when all
        discrete samples are strictly <= -0.1 dBFS.
        """
        sr = 44100
        n_samples = 4410
        audio = np.zeros((1, n_samples), dtype=np.float64)

        # 4 consecutive samples at 0.988 (-0.1 dBFS) in alternating pattern
        # Sinc interpolation will reconstruct an inter-sample analog peak exceeding 0.0 dBTP
        center = 2000
        pattern = np.array([0.0, 0.99, -0.99, 0.99, -0.99, 0.0])
        audio[0, center:center + len(pattern)] = pattern

        events = ClippingEngine.detect_true_peak_clipping(
            audio=audio,
            sample_rate=sr,
            threshold_dbtp=0.0,
            oversample_factor=4
        )

        assert len(events) >= 1
        ev = events[0]
        assert ev.event_type == ForensicEventType.INTER_SAMPLE_PEAK
        assert ev.details["true_peak_dbtp"] > 0.0
        assert ev.details["is_inter_sample"] is True

    def test_clean_audio_has_no_clipping(self):
        sr = 44100
        t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
        audio = 0.5 * np.sin(2 * np.pi * 440.0 * t)  # -6 dBFS

        events = ClippingEngine.analyze(audio, sr)
        assert len(events) == 0
