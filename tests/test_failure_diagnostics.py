# tests/test_failure_diagnostics.py
import pytest
from engine.supervisor.failure_diagnostics import (
    FailureDiagnostics,
    FailureCategory,
    DiagnosticSeverity,
    DiagnosticFinding
)


def test_diagnose_silence_detects_all_anomalies():
    # Test track that is stopped, muted, fader at zero, no clips, no devices, blind VST
    findings = FailureDiagnostics.diagnose_silence(
        track_index=1,
        track_name="2-808 Bass",
        is_playing=False,
        is_muted=True,
        volume=0.0,
        clip_count=0,
        device_count=0,
        parameter_count=1
    )

    categories = [f.category for f in findings]
    assert FailureCategory.TRANSPORT_STOPPED in categories
    assert FailureCategory.TRACK_MUTED in categories
    assert FailureCategory.MISSING_CLIPS in categories
    assert FailureCategory.UNCONFIGURED_VST in categories
    assert FailureCategory.LOW_PARAMETER_COUNT in categories


def test_diagnose_silence_clean_when_healthy():
    findings = FailureDiagnostics.diagnose_silence(
        track_index=2,
        track_name="1-Drums",
        is_playing=True,
        is_muted=False,
        volume=0.75,
        clip_count=4,
        device_count=2,
        parameter_count=93
    )
    assert len(findings) == 0


def test_format_diagnostic_report():
    finding = DiagnosticFinding(
        category=FailureCategory.LOW_PARAMETER_COUNT,
        severity=DiagnosticSeverity.HARD_BLOCKER,
        track_index=1,
        track_name="Bass Track",
        device_name="Vital",
        issue="Plugin only exposes 1 parameter (Device On).",
        measured_value=1,
        expected_value=">= 8 parameters",
        remediation_actions=["Wrap in Instrument Rack or swap to Wavetable."]
    )
    report = FailureDiagnostics.format_diagnostic_report([finding])
    assert "Supervisor Diagnostic Report" in report
    assert "Bass Track" in report
    assert "LOW_PARAMETER_COUNT" in report
    assert "Wrap in Instrument Rack" in report
