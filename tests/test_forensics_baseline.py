"""
Tests for Baseline Statistical Calibration Engine (PIE Phase 7).
Validates dynamic percentile distributions (p10, p50, p90, mean, std) across bands.
"""
import pytest
import numpy as np

from engine.forensics.baseline import BaselineEngine
from engine.forensics.temporal import TemporalEngine
from engine.forensics.models import AnalysisConfig, TrackBaseline


class TestForensicsBaseline:

    def test_distribution_stats_percentiles(self):
        # Known distribution: 0 to 100 linearly
        values = np.linspace(0.0, 100.0, 101)
        stats = BaselineEngine.compute_distribution_stats(values)

        assert abs(stats["mean"] - 50.0) < 1e-3
        assert abs(stats["median"] - 50.0) < 1e-3
        assert abs(stats["p10"] - 10.0) < 1.0
        assert abs(stats["p50"] - 50.0) < 1.0
        assert abs(stats["p90"] - 90.0) < 1.0
        assert stats["p90"] > stats["p10"]

    def test_compute_baseline_on_audio(self):
        sr = 44100
        n_samples = 44100
        t = np.linspace(0, 1.0, n_samples, endpoint=False)

        # Dynamic sine wave with changing amplitude
        audio = (0.2 + 0.3 * np.sin(2 * np.pi * 2 * t)) * np.sin(2 * np.pi * 440 * t)
        stereo = np.stack([audio, audio], axis=0)

        cfg = AnalysisConfig(fft_size=1024, hop_size=256)
        frames = TemporalEngine.analyze_frames(stereo, sr, cfg)

        baseline = BaselineEngine.compute_baseline(
            audio=stereo,
            sample_rate=sr,
            frames=frames,
            config=cfg,
            track_id="synth_lead"
        )

        assert isinstance(baseline, TrackBaseline)
        assert baseline.track_id == "synth_lead"
        assert "mean" in baseline.rms_stats
        assert "p90" in baseline.rms_stats
        assert len(baseline.band_baselines) == 14
        assert "SUB_LOW" in baseline.band_baselines
        assert "PRESENCE_1" in baseline.band_baselines
