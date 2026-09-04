"""
Failure Injection & Security Integrity Tests for Audio Forensics Engine (PIE Phase 7).
Tests system resilience against malformed inputs, NaN/Inf poisoning, buffer tampering,
hash integrity failures, and guarantees the READ-ONLY invariant (State_before == State_after).
"""
import pytest
import os
import json
import tempfile
import numpy as np

from engine.forensics import (
    AudioForensicsEngine,
    ForensicsStorage,
    AnalysisConfig,
    ForensicReport,
    ForensicsIntegrityError,
    InvalidAudioError,
    ForensicsPersistenceError,
)


class TestForensicsFailureInjection:

    def test_read_only_audio_invariant(self):
        """Guarantees that input audio buffer is NEVER mutated in-place during analysis."""
        engine = AudioForensicsEngine()
        sr = 44100
        n_samples = 44100
        audio = np.random.randn(2, n_samples).astype(np.float64)
        audio_copy = audio.copy()

        # Run full analysis
        engine.analyze_track(audio, sr, track_id="invariant_check", save_report=False)

        # Assert byte-for-byte exact equality
        np.testing.assert_array_equal(audio, audio_copy)

    def test_nan_and_inf_poisoning_rejection(self):
        engine = AudioForensicsEngine()
        sr = 44100

        # NaN injection
        nan_audio = np.zeros((1, 1000))
        nan_audio[0, 250] = np.nan
        with pytest.raises(InvalidAudioError):
            engine.analyze_track(nan_audio, sr)

        # Positive Infinity
        pos_inf_audio = np.zeros((1, 1000))
        pos_inf_audio[0, 500] = np.inf
        with pytest.raises(InvalidAudioError):
            engine.analyze_track(pos_inf_audio, sr)

        # Negative Infinity
        neg_inf_audio = np.zeros((1, 1000))
        neg_inf_audio[0, 750] = -np.inf
        with pytest.raises(InvalidAudioError):
            engine.analyze_track(neg_inf_audio, sr)

    def test_unsupported_channel_configurations(self):
        engine = AudioForensicsEngine()
        sr = 44100

        # 5.1 surround (6 channels)
        surround = np.zeros((6, 1000))
        with pytest.raises(InvalidAudioError):
            engine.analyze_track(surround, sr)

    def test_tampered_hash_detection(self):
        """Guarantees that modifying a report JSON file triggers ForensicsIntegrityError on reload."""
        with tempfile.TemporaryDirectory() as td:
            storage = ForensicsStorage(base_dir=td)
            engine = AudioForensicsEngine(storage=storage)

            audio = 0.5 * np.ones((1, 44100))
            report = engine.analyze_track(audio, 44100, track_id="tamper_test", save_report=True)
            report_file = os.path.join(storage.reports_dir, f"{report.report_id}.json")

            # Read JSON, tamper with the duration, write back
            with open(report_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Tamper duration
            data["duration_seconds"] = 999.999

            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(data, f)

            # Loading with verify_hash=True MUST raise ForensicsIntegrityError
            with pytest.raises(ForensicsIntegrityError) as exc_info:
                storage.load_report(report.report_id, verify_hash=True)

            assert "hash mismatch" in str(exc_info.value).lower()

    def test_corrupted_json_loading(self):
        with tempfile.TemporaryDirectory() as td:
            storage = ForensicsStorage(base_dir=td)
            bad_file = os.path.join(storage.reports_dir, "corrupt.json")
            with open(bad_file, "w", encoding="utf-8") as f:
                f.write("{this is not valid json")

            with pytest.raises(ForensicsPersistenceError):
                storage.load_report("corrupt")

    def test_load_nonexistent_report(self):
        with tempfile.TemporaryDirectory() as td:
            storage = ForensicsStorage(base_dir=td)
            with pytest.raises(ForensicsPersistenceError):
                storage.load_report("does_not_exist")
