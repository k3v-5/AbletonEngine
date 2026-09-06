# engine/supervisor/failure_diagnostics.py
"""
Failure Diagnostics & Root Cause Analyzer:
Performs deep physical and structural diagnostics when quality gates or acoustic probes fail,
providing clear actionable remediation options rather than vague error messages.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional


class FailureCategory(str, Enum):
    SILENCE = "ACOUSTIC_SILENCE"
    UNCONFIGURED_VST = "UNCONFIGURED_BLIND_VST"
    MISSING_CLIPS = "MISSING_OR_EMPTY_CLIPS"
    TRANSPORT_STOPPED = "TRANSPORT_NOT_PLAYING"
    ARRANGEMENT_SUPPRESSED = "ARRANGEMENT_SUPPRESSED_BY_SESSION"
    TRACK_MUTED = "TRACK_MUTED_OR_INACTIVE"
    HEADROOM_OVERFLOW = "HEADROOM_OVERFLOW"
    LOUDNESS_NON_COMPLIANT = "LOUDNESS_NON_COMPLIANT"
    LOW_PARAMETER_COUNT = "LOW_PARAMETER_COUNT"
    TIMING_VIOLATION = "TIMING_OR_TEMPO_VIOLATION"


class DiagnosticSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    HARD_BLOCKER = "HARD_BLOCKER"


@dataclass
class DiagnosticFinding:
    category: FailureCategory
    severity: DiagnosticSeverity
    track_index: Optional[int]
    track_name: Optional[str]
    device_name: Optional[str]
    issue: str
    measured_value: Any
    expected_value: Any
    remediation_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "track_index": self.track_index,
            "track_name": self.track_name,
            "device_name": self.device_name,
            "issue": self.issue,
            "measured_value": self.measured_value,
            "expected_value": self.expected_value,
            "remediation_actions": self.remediation_actions
        }


class FailureDiagnostics:
    """Performs structured diagnosis of playback, plugin, mixing, and mastering anomalies."""

    @classmethod
    def diagnose_silence(
        cls,
        track_index: int,
        track_name: str,
        is_playing: bool,
        is_muted: bool,
        volume: float,
        clip_count: int,
        device_count: int,
        parameter_count: int
    ) -> List[DiagnosticFinding]:
        """Diagnoses why a specific track is silent during playback."""
        findings = []

        if not is_playing:
            findings.append(DiagnosticFinding(
                category=FailureCategory.TRANSPORT_STOPPED,
                severity=DiagnosticSeverity.HARD_BLOCKER,
                track_index=track_index,
                track_name=track_name,
                device_name=None,
                issue="Ableton transport is stopped; no clips are actively rendering audio.",
                measured_value="is_playing=False",
                expected_value="is_playing=True",
                remediation_actions=[
                    "Send start_playback command to Ableton transport.",
                    "Verify arrangement playhead is located within valid song timeline."
                ]
            ))

        if is_muted:
            findings.append(DiagnosticFinding(
                category=FailureCategory.TRACK_MUTED,
                severity=DiagnosticSeverity.HARD_BLOCKER,
                track_index=track_index,
                track_name=track_name,
                device_name=None,
                issue=f"Track {track_index} ({track_name}) is physically MUTED in Live.",
                measured_value="mute=True",
                expected_value="mute=False",
                remediation_actions=[
                    f"Send set_track_mute(track_index={track_index}, mute=False)."
                ]
            ))

        if volume < 0.05:
            findings.append(DiagnosticFinding(
                category=FailureCategory.TRACK_MUTED,
                severity=DiagnosticSeverity.HARD_BLOCKER,
                track_index=track_index,
                track_name=track_name,
                device_name=None,
                issue=f"Track volume fader is down near zero ({volume:.4f}).",
                measured_value=round(volume, 4),
                expected_value=">= 0.15",
                remediation_actions=[
                    f"Set track volume to nominal staging level (-12 dBFS / norm ~0.65)."
                ]
            ))

        if clip_count == 0:
            findings.append(DiagnosticFinding(
                category=FailureCategory.MISSING_CLIPS,
                severity=DiagnosticSeverity.HARD_BLOCKER,
                track_index=track_index,
                track_name=track_name,
                device_name=None,
                issue=f"Track {track_index} has NO MIDI or Audio clips loaded.",
                measured_value=0,
                expected_value=">= 1",
                remediation_actions=[
                    f"Create clip and populate notes for track {track_index} ({track_name})."
                ]
            ))

        if device_count == 0:
            findings.append(DiagnosticFinding(
                category=FailureCategory.UNCONFIGURED_VST,
                severity=DiagnosticSeverity.HARD_BLOCKER,
                track_index=track_index,
                track_name=track_name,
                device_name=None,
                issue=f"Track {track_index} has NO instrument device loaded to synthesize MIDI notes.",
                measured_value=0,
                expected_value=">= 1",
                remediation_actions=[
                    f"Load an instrument or instrument rack on track {track_index}."
                ]
            ))

        if parameter_count <= 1:
            findings.append(DiagnosticFinding(
                category=FailureCategory.LOW_PARAMETER_COUNT,
                severity=DiagnosticSeverity.HARD_BLOCKER,
                track_index=track_index,
                track_name=track_name,
                device_name="Primary Instrument",
                issue=f"Instrument on track {track_index} only exposes {parameter_count} parameter(s) ('Device On') - blind init patch.",
                measured_value=parameter_count,
                expected_value=">= 8 mapped parameters",
                remediation_actions=[
                    f"Wrap plugin in an Ableton Instrument Rack to expose 8 Macro controls.",
                    f"Or replace with a native synth (Wavetable, Drift, Operator) with fully exposed parameter tree."
                ]
            ))

        return findings

    @classmethod
    def format_diagnostic_report(cls, findings: List[DiagnosticFinding]) -> str:
        """Generates a markdown diagnostic report from findings."""
        if not findings:
            return "✅ All physical and structural supervisor checks passed. No anomalies detected."

        lines = ["## 🚨 Ableton Supervisor Diagnostic Report\n"]
        lines.append(f"Detected **{len(findings)}** blocking or warning issues:\n")

        for idx, f in enumerate(findings, 1):
            icon = "🔴" if f.severity == DiagnosticSeverity.HARD_BLOCKER else "⚠️"
            lines.append(f"### {icon} Issue {idx}: {f.category.value} [{f.severity.value}]")
            if f.track_name:
                lines.append(f"- **Target Track**: Track {f.track_index} ('{f.track_name}')")
            if f.device_name:
                lines.append(f"- **Device**: {f.device_name}")
            lines.append(f"- **Problem**: {f.issue}")
            lines.append(f"- **Measured**: `{f.measured_value}` | **Expected**: `{f.expected_value}`")
            lines.append("- **Recommended Remediations**:")
            for action in f.remediation_actions:
                lines.append(f"  - {action}")
            lines.append("")

        return "\n".join(lines)
