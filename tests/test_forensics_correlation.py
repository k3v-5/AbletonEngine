"""
Tests for Cross-Track Correlation & Attribution Engine (PIE Phase 7).
Validates Pearson correlation, lag alignment, and event source attribution.
"""
import pytest
import numpy as np

from engine.forensics.correlation import CorrelationEngine
from engine.forensics.models import ForensicEvent, ForensicEventType, Severity


class TestForensicsCorrelation:

    def test_pearson_correlation_properties(self):
        t = np.linspace(0, 1.0, 1000)
        x = np.sin(2 * np.pi * 5 * t)

        # Identical
        assert abs(CorrelationEngine.calculate_pearson_correlation(x, x) - 1.0) < 1e-4

        # Inverted
        assert abs(CorrelationEngine.calculate_pearson_correlation(x, -x) - (-1.0)) < 1e-4

        # Orthogonal (cos vs sin)
        y = np.cos(2 * np.pi * 5 * t)
        assert abs(CorrelationEngine.calculate_pearson_correlation(x, y)) < 1e-2

    def test_lag_correlation(self):
        sr = 44100
        n_samples = 4410
        np.random.seed(42)
        noise = np.random.randn(n_samples)

        # Shift noise by 10ms (441 samples)
        lag_samples = 441
        shifted = np.zeros(n_samples)
        shifted[lag_samples:] = noise[:-lag_samples]

        max_corr, best_lag_ms = CorrelationEngine.calculate_lag_correlation(
            noise, shifted, sr, max_lag_ms=30.0
        )
        assert max_corr > 0.85
        assert abs(best_lag_ms - 10.0) < 1.0

    def test_attribute_event_to_sources(self):
        sr = 44100
        n_samples = 44100
        t = np.linspace(0, 1.0, n_samples, endpoint=False)

        # Event occurs between 0.3s and 0.4s
        ev = ForensicEvent(
            event_id="ev_master_clip_01",
            event_type=ForensicEventType.CLIPPING,
            start_time_seconds=0.3,
            end_time_seconds=0.4,
            duration_seconds=0.1,
            severity=Severity.ERROR,
            confidence=0.9,
            channels=("L", "R")
        )

        # Stem A has high burst energy during the event interval
        stem_a = np.zeros(n_samples)
        stem_a[int(0.3 * sr):int(0.4 * sr)] = 0.9 * np.sin(2 * np.pi * 100 * t[int(0.3 * sr):int(0.4 * sr)])

        # Stem B is quiet / inactive
        stem_b = 0.01 * np.random.randn(n_samples)

        stems = {"Snare": stem_a, "AcousticGuitar": stem_b}
        ranking = CorrelationEngine.attribute_event_to_sources(ev, stems, sr)

        assert len(ranking) == 2
        top_stem, top_score, stats = ranking[0]
        assert top_stem == "Snare"
        assert top_score > ranking[1][1]
