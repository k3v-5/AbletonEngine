"""
Forensic Report Generation & Fingerprinting Engine (PIE Phase 7).
Compiles ForensicReport instances with deterministic SHA-256 provenance hashes
and human-readable diagnostic summaries.
"""
from typing import Sequence, Optional, Dict, Any, List
import hashlib
import json
import time

from .models import ForensicReport, ForensicEvent, CausalHypothesis, TrackBaseline, AnalysisConfig, Severity
from .config import DEFAULT_ANALYSIS_CONFIG
from .exceptions import ForensicsIntegrityError


class ForensicReportGenerator:
    """
    Assembles comprehensive ForensicReport data structures and calculates
    deterministic cryptographic provenance signatures.
    """

    @classmethod
    def compute_deterministic_hash(
        cls,
        report_data: Dict[str, Any]
    ) -> str:
        """
        Calculates SHA-256 checksum over a normalized, alphabetically sorted JSON
        representation of the report data (excluding dynamic processing time or existing hash).
        """
        data_to_hash = {
            "analysis_version": report_data.get("analysis_version"),
            "sample_rate": report_data.get("sample_rate"),
            "duration_seconds": report_data.get("duration_seconds"),
            "channels": report_data.get("channels"),
            "config": report_data.get("config"),
            "frames_analyzed": report_data.get("frames_analyzed"),
            "events": report_data.get("events"),
            "hypotheses": report_data.get("hypotheses"),
            "baseline": report_data.get("baseline"),
        }
        canonical_json = json.dumps(data_to_hash, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    @classmethod
    def create_report(
        cls,
        report_id: str,
        sample_rate: int,
        duration_seconds: float,
        channels: int,
        frames_analyzed: int,
        measurements_count: int,
        events: Sequence[ForensicEvent],
        hypotheses: Sequence[CausalHypothesis] = (),
        baseline: Optional[TrackBaseline] = None,
        config: Optional[AnalysisConfig] = None,
        processing_time_seconds: float = 0.0,
        analysis_version: str = "1.0.0",
    ) -> ForensicReport:
        """
        Constructs and seals a complete ForensicReport with verifiable deterministic hash.
        """
        cfg = config or DEFAULT_ANALYSIS_CONFIG

        temp_dict = {
            "report_id": report_id,
            "analysis_version": analysis_version,
            "sample_rate": sample_rate,
            "duration_seconds": round(duration_seconds, 4),
            "channels": channels,
            "config": cfg.to_dict(),
            "frames_analyzed": frames_analyzed,
            "measurements_count": measurements_count,
            "events": [e.to_dict() for e in events],
            "hypotheses": [h.to_dict() for h in hypotheses],
            "baseline": baseline.to_dict() if baseline else None,
        }

        det_hash = cls.compute_deterministic_hash(temp_dict)

        return ForensicReport(
            report_id=report_id,
            analysis_version=analysis_version,
            sample_rate=sample_rate,
            duration_seconds=duration_seconds,
            channels=channels,
            config=cfg,
            frames_analyzed=frames_analyzed,
            measurements_count=measurements_count,
            events=tuple(events),
            hypotheses=tuple(hypotheses),
            baseline=baseline,
            processing_time_seconds=round(processing_time_seconds, 4),
            deterministic_hash=det_hash
        )

    @staticmethod
    def generate_markdown_summary(report: ForensicReport) -> str:
        """
        Produces human-readable markdown summary of the forensic report.
        """
        lines = [
            f"# Audio Forensic Diagnostic Report: `{report.report_id}`",
            f"- **Analysis Version:** {report.analysis_version}",
            f"- **Sample Rate:** {report.sample_rate} Hz | **Channels:** {report.channels}",
            f"- **Duration:** {report.duration_seconds:.3f} s | **Frames Analyzed:** {report.frames_analyzed}",
            f"- **Total Events Detected:** {len(report.events)}",
            f"- **Causal Hypotheses:** {len(report.hypotheses)}",
            f"- **Deterministic SHA-256:** `{report.deterministic_hash}`",
            "",
            "## Severity Breakdown",
        ]

        sev_counts: Dict[str, int] = {}
        for ev in report.events:
            sev_counts[ev.severity] = sev_counts.get(ev.severity, 0) + 1

        for sev in (Severity.CRITICAL.value, Severity.ERROR.value, Severity.WARNING.value, Severity.INFO.value):
            count = sev_counts.get(sev, 0)
            lines.append(f"- **{sev}:** {count}")

        lines.extend(["", "## Detected Forensic Events"])
        if not report.events:
            lines.append("_No anomalies or compliance violations detected._")
        else:
            lines.append("| Time (s) | Type | Severity | Channels | Confidence | Summary |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for ev in report.events:
                summary_snippet = ""
                if ev.details.get("peak_dbfs") is not None:
                    summary_snippet += f"Peak: {ev.details['peak_dbfs']} dBFS "
                if ev.details.get("true_peak_dbtp") is not None:
                    summary_snippet += f"TP: {ev.details['true_peak_dbtp']} dBTP "
                if ev.frequency_min_hz is not None and ev.frequency_max_hz is not None:
                    summary_snippet += f"[{ev.frequency_min_hz:.0f}-{ev.frequency_max_hz:.0f}Hz] "
                lines.append(
                    f"| {ev.start_time_seconds:.3f} - {ev.end_time_seconds:.3f} | {ev.event_type} "
                    f"| {ev.severity} | {','.join(ev.channels)} | {ev.confidence:.2f} | {summary_snippet.strip()} |"
                )

        if report.hypotheses:
            lines.extend(["", "## Causal Hypotheses & Explanations"])
            for h in report.hypotheses:
                lines.append(f"### Hypothesis `{h.hypothesis_id}`: {h.likely_cause} (Conf: {h.confidence:.2f})")
                lines.append(f"- **Summary:** {h.summary}")
                if h.supporting_evidence:
                    lines.append("- **Supporting Evidence:**")
                    for ev_item in h.supporting_evidence:
                        lines.append(f"  - {ev_item}")
                if h.competing_explanations:
                    lines.append("- **Competing Explanations:**")
                    for alt in h.competing_explanations:
                        lines.append(f"  - {alt}")
                lines.append("")

        return "\n".join(lines)
