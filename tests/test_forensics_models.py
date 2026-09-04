"""
Tests for Canonical Models of the Audio Forensics Engine (PIE Phase 7).
Validates immutability, defensive copies, parameter bounds, and JSON serialization.
"""
import pytest
import math
from dataclasses import FrozenInstanceError

from engine.forensics.models import (
    AnalysisConfig,
    AudioFrame,
    SpectralMeasurement,
    ForensicEvent,
    ForensicEventType,
    Severity,
    CausalHypothesis,
    TrackBaseline,
    ForensicReport,
)
from engine.forensics.exceptions import (
    InvalidAnalysisConfigError,
    InvalidAudioError,
    ForensicsIntegrityError
)


class TestForensicsModels:

    def test_analysis_config_defaults_and_validation(self):
        cfg = AnalysisConfig()
        assert cfg.fft_size == 2048
        assert cfg.hop_size == 512
        assert cfg.window == "hann"
        assert cfg.min_frequency_hz == 20.0
        assert cfg.max_frequency_hz == 20000.0

        # Immutability
        with pytest.raises(FrozenInstanceError):
            cfg.fft_size = 1024

        # Validation errors
        with pytest.raises(InvalidAnalysisConfigError):
            AnalysisConfig(fft_size=-1)

        with pytest.raises(InvalidAnalysisConfigError):
            AnalysisConfig(hop_size=4096, fft_size=2048)  # hop > fft

        with pytest.raises(InvalidAnalysisConfigError):
            AnalysisConfig(min_frequency_hz=-10.0)

        with pytest.raises(InvalidAnalysisConfigError):
            AnalysisConfig(min_frequency_hz=1000.0, max_frequency_hz=500.0)

        with pytest.raises(InvalidAnalysisConfigError):
            AnalysisConfig(correlation_threshold=1.5)

    def test_audio_frame_invariants(self):
        frame = AudioFrame(
            index=0,
            start_sample=0,
            end_sample=512,
            start_time_seconds=0.0,
            end_time_seconds=0.0116,
            rms_dbfs=-18.5,
            peak_dbfs=-12.0,
            spectral_centroid_hz=1500.0,
            spectral_flux=0.45
        )
        assert frame.rms_dbfs == -18.5
        d = frame.to_dict()
        assert d["index"] == 0
        assert d["rms_dbfs"] == -18.5

        # Nan or Inf validation
        with pytest.raises(InvalidAudioError):
            AudioFrame(
                index=0, start_sample=0, end_sample=512,
                start_time_seconds=0.0, end_time_seconds=0.01,
                rms_dbfs=float("nan"), peak_dbfs=0.0,
                spectral_centroid_hz=100.0, spectral_flux=0.1
            )

    def test_forensic_event_immutability_and_defensive_copies(self):
        details = {"peak": -0.1, "transient": True}
        event = ForensicEvent(
            event_id="ev_001",
            event_type=ForensicEventType.CLIPPING,
            start_time_seconds=1.2,
            end_time_seconds=1.25,
            duration_seconds=0.05,
            severity=Severity.ERROR,
            confidence=0.95,
            channels=("L", "R"),
            frequency_min_hz=20.0,
            frequency_max_hz=20000.0,
            evidence_ids=("evid_1",),
            details=details
        )
        # Verify normalization
        assert event.event_type == "CLIPPING"
        assert event.severity == "ERROR"

        # Mutating original details dictionary does not affect the event
        details["peak"] = 999.0
        assert event.details["peak"] == -0.1

        # Immutability
        with pytest.raises(FrozenInstanceError):
            event.confidence = 0.5

        # Integrity bounds
        with pytest.raises(ForensicsIntegrityError):
            ForensicEvent(
                event_id="",  # empty id
                event_type="CLIPPING",
                start_time_seconds=0.0,
                end_time_seconds=1.0,
                duration_seconds=1.0,
                severity="WARNING",
                confidence=0.5,
                channels=("L",)
            )

        with pytest.raises(ForensicsIntegrityError):
            ForensicEvent(
                event_id="ev_bad_conf",
                event_type="CLIPPING",
                start_time_seconds=0.0,
                end_time_seconds=1.0,
                duration_seconds=1.0,
                severity="WARNING",
                confidence=1.5,  # confidence > 1.0
                channels=("L",)
            )

    def test_causal_hypothesis_contracts(self):
        hypo = CausalHypothesis(
            hypothesis_id="hyp_001",
            likely_cause="Inter-sample peak overshoot",
            summary="True peak exceeded 0.0 dBTP",
            confidence=0.92,
            observation_ids=("ev_001",),
            supporting_evidence=("4x oversampling filter confirmed overshoot",),
            competing_explanations=("Limiter release distortion",)
        )
        assert hypo.confidence == 0.92
        assert len(hypo.observation_ids) == 1

        d = hypo.to_dict()
        assert d["hypothesis_id"] == "hyp_001"
        assert len(d["supporting_evidence"]) == 1

    def test_track_baseline_and_forensic_report(self):
        cfg = AnalysisConfig()
        baseline = TrackBaseline(
            track_id="lead_vocal",
            rms_stats={"mean": -20.0, "p50": -19.8},
            peak_stats={"mean": -4.0, "p50": -3.8}
        )
        report = ForensicReport(
            report_id="rep_test_01",
            analysis_version="1.0.0",
            sample_rate=44100,
            duration_seconds=3.5,
            channels=2,
            config=cfg,
            frames_analyzed=150,
            measurements_count=200,
            events=(),
            hypotheses=(),
            baseline=baseline,
            deterministic_hash="abc123"
        )
        assert report.sample_rate == 44100
        assert report.channels == 2
        assert report.baseline is not None

        d = report.to_dict()
        assert d["report_id"] == "rep_test_01"
        assert d["baseline"]["track_id"] == "lead_vocal"
