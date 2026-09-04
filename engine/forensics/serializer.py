"""
Atomic Persistence & Serialization for Audio Forensics Engine (PIE Phase 7).
Ensures safe disk operations (flush + fsync + os.replace) and cryptographic
integrity verification upon deserialization.
"""
import os
import json
import tempfile
from typing import Optional, List, Dict, Any

from .models import (
    ForensicReport,
    ForensicEvent,
    CausalHypothesis,
    TrackBaseline,
    AnalysisConfig,
    ForensicEventType,
    Severity
)
from .report import ForensicReportGenerator
from .exceptions import ForensicsPersistenceError, ForensicsIntegrityError


DEFAULT_FORENSICS_STATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "state",
    "production",
    "forensics"
)


class ForensicsStorage:
    """
    Handles atomic serialization, disk storage, and integrity-verified loading
    of ForensicReports and acoustic diagnostic evidence.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or DEFAULT_FORENSICS_STATE_DIR
        self.reports_dir = os.path.join(self.base_dir, "reports")
        self.evidence_dir = os.path.join(self.base_dir, "evidence")
        self.indexes_dir = os.path.join(self.base_dir, "indexes")

        for d in (self.base_dir, self.reports_dir, self.evidence_dir, self.indexes_dir):
            os.makedirs(d, exist_ok=True)

    def _atomic_write(self, target_path: str, data: str):
        """Atomically writes data using temp file, flush, fsync, and replace."""
        dir_name = os.path.dirname(target_path)
        os.makedirs(dir_name, exist_ok=True)

        try:
            with tempfile.NamedTemporaryFile(mode="w", dir=dir_name, delete=False, encoding="utf-8") as tf:
                tf.write(data)
                tf.flush()
                os.fsync(tf.fileno())
                temp_name = tf.name

            os.replace(temp_name, target_path)
        except Exception as exc:
            raise ForensicsPersistenceError(f"Atomic write to '{target_path}' failed: {str(exc)}") from exc

    @classmethod
    def serialize_report(cls, report: ForensicReport) -> str:
        """Serializes a ForensicReport to deterministic canonical JSON."""
        d = report.to_dict()
        return json.dumps(d, indent=2, sort_keys=True)

    @classmethod
    def deserialize_report(cls, json_str: str, verify_hash: bool = True) -> ForensicReport:
        """
        Deserializes a JSON string into a validated, typed ForensicReport instance.
        If verify_hash is True, calculates SHA-256 and asserts match with deterministic_hash.
        """
        try:
            d = json.loads(json_str)
        except Exception as exc:
            raise ForensicsPersistenceError(f"Failed to parse forensic report JSON: {str(exc)}") from exc

        # Reconstruct config
        cfg_d = d.get("config", {})
        config = AnalysisConfig(
            fft_size=cfg_d.get("fft_size", 2048),
            hop_size=cfg_d.get("hop_size", 512),
            window=cfg_d.get("window", "hann"),
            min_frequency_hz=cfg_d.get("min_frequency_hz", 20.0),
            max_frequency_hz=cfg_d.get("max_frequency_hz", 20000.0),
            peak_threshold_db=cfg_d.get("peak_threshold_db", -0.1),
            resonance_threshold_db=cfg_d.get("resonance_threshold_db", 6.0),
            minimum_event_duration_ms=cfg_d.get("minimum_event_duration_ms", 50.0),
            maximum_event_gap_ms=cfg_d.get("maximum_event_gap_ms", 100.0),
            correlation_threshold=cfg_d.get("correlation_threshold", 0.75),
            clipping_threshold_dbfs=cfg_d.get("clipping_threshold_dbfs", -0.01),
            algorithm_version=cfg_d.get("algorithm_version", "1.0.0"),
        )

        # Reconstruct events
        events: List[ForensicEvent] = []
        for ev_d in d.get("events", []):
            events.append(ForensicEvent(
                event_id=ev_d["event_id"],
                event_type=ev_d["event_type"],
                start_time_seconds=ev_d["start_time_seconds"],
                end_time_seconds=ev_d["end_time_seconds"],
                duration_seconds=ev_d["duration_seconds"],
                severity=ev_d["severity"],
                confidence=ev_d["confidence"],
                channels=tuple(ev_d.get("channels", ())),
                frequency_min_hz=ev_d.get("frequency_min_hz"),
                frequency_max_hz=ev_d.get("frequency_max_hz"),
                evidence_ids=tuple(ev_d.get("evidence_ids", ())),
                details=ev_d.get("details", {}),
            ))

        # Reconstruct hypotheses
        hypotheses: List[CausalHypothesis] = []
        for hyp_d in d.get("hypotheses", []):
            hypotheses.append(CausalHypothesis(
                hypothesis_id=hyp_d["hypothesis_id"],
                likely_cause=hyp_d["likely_cause"],
                summary=hyp_d["summary"],
                confidence=hyp_d["confidence"],
                observation_ids=tuple(hyp_d.get("observation_ids", ())),
                supporting_evidence=tuple(hyp_d.get("supporting_evidence", ())),
                competing_explanations=tuple(hyp_d.get("competing_explanations", ())),
                details=hyp_d.get("details", {}),
            ))

        # Reconstruct baseline
        baseline = None
        base_d = d.get("baseline")
        if base_d:
            baseline = TrackBaseline(
                track_id=base_d.get("track_id", "unknown"),
                rms_stats=base_d.get("rms_stats", {}),
                peak_stats=base_d.get("peak_stats", {}),
                centroid_stats=base_d.get("centroid_stats", {}),
                band_baselines=base_d.get("band_baselines", {}),
                crest_factor_stats=base_d.get("crest_factor_stats", {}),
                stereo_correlation_stats=base_d.get("stereo_correlation_stats", {}),
            )

        report = ForensicReport(
            report_id=d["report_id"],
            analysis_version=d.get("analysis_version", "1.0.0"),
            sample_rate=d["sample_rate"],
            duration_seconds=d["duration_seconds"],
            channels=d["channels"],
            config=config,
            frames_analyzed=d["frames_analyzed"],
            measurements_count=d["measurements_count"],
            events=tuple(events),
            hypotheses=tuple(hypotheses),
            baseline=baseline,
            processing_time_seconds=d.get("processing_time_seconds", 0.0),
            deterministic_hash=d.get("deterministic_hash", "")
        )

        if verify_hash and report.deterministic_hash:
            expected_hash = ForensicReportGenerator.compute_deterministic_hash(d)
            if report.deterministic_hash != expected_hash:
                raise ForensicsIntegrityError(
                    f"Forensic report hash mismatch: recorded '{report.deterministic_hash}' "
                    f"does not match computed '{expected_hash}'. Integrity compromised."
                )

        return report

    def save_report(self, report: ForensicReport, filename: Optional[str] = None) -> str:
        """Atomically saves a ForensicReport to disk in reports directory."""
        fname = filename or f"{report.report_id}.json"
        if not fname.endswith(".json"):
            fname += ".json"
        target_path = os.path.join(self.reports_dir, fname)
        serialized = self.serialize_report(report)
        self._atomic_write(target_path, serialized)
        return target_path

    def load_report(self, report_id_or_path: str, verify_hash: bool = True) -> ForensicReport:
        """Loads and verifies a ForensicReport by ID or path."""
        if os.path.isfile(report_id_or_path):
            target_path = report_id_or_path
        else:
            fname = report_id_or_path if report_id_or_path.endswith(".json") else f"{report_id_or_path}.json"
            target_path = os.path.join(self.reports_dir, fname)

        if not os.path.exists(target_path):
            raise ForensicsPersistenceError(f"Forensic report file not found: '{target_path}'")

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()
            return self.deserialize_report(content, verify_hash=verify_hash)
        except Exception as exc:
            if isinstance(exc, ForensicsIntegrityError):
                raise
            raise ForensicsPersistenceError(f"Failed to read report '{target_path}': {str(exc)}") from exc

    def list_reports(self) -> List[str]:
        """Lists all stored report IDs."""
        if not os.path.exists(self.reports_dir):
            return []
        files = [f[:-5] for f in os.listdir(self.reports_dir) if f.endswith(".json")]
        return sorted(files)
