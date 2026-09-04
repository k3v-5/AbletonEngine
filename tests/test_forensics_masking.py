"""
Tests for Dynamic Spectral Masking Engine (PIE Phase 7).
Validates time-frequency masking detection between stems in standard frequency bands.
"""
import pytest
import numpy as np

from engine.forensics.masking import MaskingEngine
from engine.forensics.models import ForensicEventType, Severity


class TestForensicsMasking:

    def test_kick_vs_bass_masking(self):
        sr = 44100
        duration_s = 1.0
        n_samples = int(sr * duration_s)
        t = np.linspace(0, duration_s, n_samples, endpoint=False)

        # Kick has 60 Hz tone with 0.8 amplitude from 0.2s to 0.6s
        kick = np.zeros(n_samples)
        kick_start = int(0.2 * sr)
        kick_end = int(0.6 * sr)
        kick[kick_start:kick_end] = 0.8 * np.sin(2 * np.pi * 60.0 * t[kick_start:kick_end])

        # Bass has 60 Hz tone with 0.7 amplitude from 0.1s to 0.7s (overlapping with Kick)
        bass = np.zeros(n_samples)
        bass_start = int(0.1 * sr)
        bass_end = int(0.7 * sr)
        bass[bass_start:bass_end] = 0.7 * np.sin(2 * np.pi * 60.0 * t[bass_start:bass_end])

        events = MaskingEngine.detect_masking(
            stem_a=kick,
            stem_b=bass,
            sample_rate=sr,
            stem_a_name="Kick",
            stem_b_name="Bass",
            clash_threshold_db=6.0
        )

        assert len(events) >= 1
        matching_events = [e for e in events if e.frequency_min_hz <= 60.0 <= e.frequency_max_hz]
        assert len(matching_events) >= 1
        ev = matching_events[0]
        assert ev.event_type == ForensicEventType.MASKING
        assert ev.details["stem_a"] == "Kick"
        assert ev.details["stem_b"] == "Bass"
        assert ev.duration_seconds >= 0.2


    def test_non_overlapping_frequencies_do_not_mask(self):
        sr = 44100
        n_samples = 44100
        t = np.linspace(0, 1.0, n_samples, endpoint=False)

        # Stem A at 80 Hz (BASS_LOW)
        stem_a = 0.5 * np.sin(2 * np.pi * 80.0 * t)
        # Stem B at 5000 Hz (PRESENCE_2)
        stem_b = 0.5 * np.sin(2 * np.pi * 5000.0 * t)

        events = MaskingEngine.detect_masking(
            stem_a=stem_a,
            stem_b=stem_b,
            sample_rate=sr,
            stem_a_name="Bass",
            stem_b_name="HiHat"
        )
        assert len(events) == 0

    def test_multitrack_masking(self):
        sr = 44100
        n_samples = 44100
        t = np.linspace(0, 1.0, n_samples, endpoint=False)

        stems = {
            "Kick": 0.6 * np.sin(2 * np.pi * 65.0 * t),
            "808_Sub": 0.5 * np.sin(2 * np.pi * 65.0 * t),
            "Lead": 0.5 * np.sin(2 * np.pi * 2500.0 * t)
        }

        events = MaskingEngine.analyze_multitrack(stems, sr)
        # Should detect clash between Kick and 808_Sub, but not with Lead
        assert len(events) >= 1
        stem_pairs = [(e.details.get("stem_a"), e.details.get("stem_b")) for e in events]
        assert any(("808_Sub" in pair and "Kick" in pair) for pair in stem_pairs)
