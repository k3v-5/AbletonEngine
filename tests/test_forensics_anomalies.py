"""
Tests for Acoustic Anomalies Detection Engine (PIE Phase 7).
Validates DC offset, clicks/pops, dropouts, channel loss, and stereo phase anomalies.
"""
import pytest
import numpy as np

from engine.forensics.anomalies import AnomalyEngine
from engine.forensics.models import ForensicEventType, Severity


class TestForensicsAnomalies:

    def test_dc_offset_detection(self):
        sr = 44100
        n_samples = 22050
        # Audio with +0.02 DC offset
        audio = 0.02 + 0.001 * np.random.randn(1, n_samples)

        events = AnomalyEngine.detect_dc_offset(audio, sr, threshold=0.005)
        assert len(events) == 1
        ev = events[0]
        assert ev.event_type == ForensicEventType.DC_OFFSET
        assert ev.details["dc_offset_linear"] >= 0.015

    def test_click_and_pop_detection(self):
        sr = 44100
        n_samples = 44100
        audio = 0.01 * np.random.randn(1, n_samples)

        # Inject single-sample spike (click) at sample 10000
        audio[0, 10000] = 0.95

        events = AnomalyEngine.detect_clicks_and_pops(audio, sr, diff_threshold=0.4)
        assert len(events) >= 1
        ev = events[0]
        assert ev.event_type in (ForensicEventType.CLICK, ForensicEventType.POP)
        assert abs(ev.start_time_seconds - (10000 / sr)) < 0.01

    def test_dropout_detection(self):
        sr = 44100
        duration_s = 1.0
        n_samples = int(sr * duration_s)
        t = np.linspace(0, duration_s, n_samples, endpoint=False)

        # 0.5 amplitude continuous tone
        audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        # Drop to silence for 60ms between 0.4s and 0.46s
        start_zero = int(0.40 * sr)
        end_zero = int(0.46 * sr)
        audio[start_zero:end_zero] = 0.0

        events = AnomalyEngine.detect_dropouts(audio, sr, min_duration_ms=40.0)
        assert len(events) >= 1
        ev = events[0]
        assert ev.event_type == ForensicEventType.DROPOUT
        assert abs(ev.start_time_seconds - 0.40) < 0.05
        assert ev.details["is_recovered"] is True

    def test_channel_loss_detection(self):
        sr = 44100
        n_samples = 44100
        t = np.linspace(0, 1.0, n_samples, endpoint=False)

        # Left channel has active signal, Right is completely silent
        left = 0.5 * np.sin(2 * np.pi * 200 * t)
        right = np.zeros(n_samples)
        stereo = np.stack([left, right], axis=0)

        events = AnomalyEngine.detect_channel_loss(stereo, sr, min_duration_ms=100.0)
        assert len(events) >= 1
        ev = events[0]
        assert ev.event_type == ForensicEventType.CHANNEL_LOSS
        assert ev.details["lost_channel"] == "R"
        assert ev.details["active_channel"] == "L"

    def test_stereo_phase_anomaly_detection(self):
        sr = 44100
        n_samples = 44100
        t = np.linspace(0, 1.0, n_samples, endpoint=False)

        # Left and Right are 180 degrees out of phase (R = -L)
        left = 0.5 * np.sin(2 * np.pi * 300 * t)
        right = -left
        stereo = np.stack([left, right], axis=0)

        events = AnomalyEngine.detect_phase_anomalies(stereo, sr, correlation_threshold=-0.3)
        assert len(events) >= 1
        ev = events[0]
        assert ev.event_type == ForensicEventType.PHASE_ANOMALY
        assert ev.details["min_correlation"] < -0.9
        assert ev.severity == Severity.CRITICAL
