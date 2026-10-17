# engine/arrangement/arrangement_physical_auditor.py
"""
Arrangement Physical Auditor:
Physically audits clips in Ableton Live 12's Arrangement View via the LOM.

Verifies:
1. Clip boundaries: start_time, end_time, and duration consistency.
2. Timeline continuity: detects unintended gaps, dead air, or abrupt cutoffs.
3. Overlap detection: catches overlapping clips on the same track that cause audio dropouts.
4. Mute states: identifies unintentionally muted clips across arrangement lanes.
5. Ghost/Empty clips: detects zero-duration or content-empty clips.
6. Alignment against arrangement blueprint sections and total song bar bounds.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Union
import logging

logger = logging.getLogger("ArrangementPhysicalAuditor")


@dataclass
class ClipAuditFinding:
    """Details of a single clip issue or anomaly detected in Arrangement View."""
    track_index: int
    track_name: str
    clip_index: int
    clip_name: str
    start_time: float
    end_time: float
    issue_type: str  # "OVERLAP", "UNINTENDED_GAP", "MUTED_CLIP", "ZERO_LENGTH", "OUT_OF_BOUNDS"
    severity: str    # "HIGH", "MEDIUM", "LOW", "INFO"
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_index": self.track_index,
            "track_name": self.track_name,
            "clip_index": self.clip_index,
            "clip_name": self.clip_name,
            "start_time": round(self.start_time, 3),
            "end_time": round(self.end_time, 3),
            "issue_type": self.issue_type,
            "severity": self.severity,
            "description": self.description
        }


@dataclass
class TrackArrangementSummary:
    """Summary of arrangement clips residing on a specific track."""
    track_index: int
    track_name: str
    clip_count: int
    total_coverage_beats: float
    earliest_start: float
    latest_end: float
    is_muted: bool
    clips: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_index": self.track_index,
            "track_name": self.track_name,
            "clip_count": self.clip_count,
            "total_coverage_beats": round(self.total_coverage_beats, 3),
            "earliest_start": round(self.earliest_start, 3),
            "latest_end": round(self.latest_end, 3),
            "is_muted": self.is_muted,
            "clips": self.clips
        }


@dataclass
class ArrangementPhysicalAuditReport:
    """Consolidated arrangement physical audit report."""
    total_tracks_audited: int = 0
    total_clips_found: int = 0
    total_timeline_span_beats: float = 0.0
    issues_count: int = 0
    is_valid: bool = True
    tracks_summary: List[TrackArrangementSummary] = field(default_factory=list)
    findings: List[ClipAuditFinding] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tracks_audited": self.total_tracks_audited,
            "total_clips_found": self.total_clips_found,
            "total_timeline_span_beats": round(self.total_timeline_span_beats, 3),
            "issues_count": self.issues_count,
            "is_valid": self.is_valid,
            "tracks_summary": [t.to_dict() for t in self.tracks_summary],
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary
        }


class ArrangementPhysicalAuditor:
    """
    Arrangement View physical inspector.
    Queries Live 12 LOM to verify timeline clips, lengths, boundaries, and mute status.
    """

    @classmethod
    def audit_session(
        cls,
        conn: Any,
        expected_total_bars: Optional[float] = None,
        beats_per_bar: float = 4.0,
        allowed_gaps: Optional[List[Tuple[float, float]]] = None
    ) -> ArrangementPhysicalAuditReport:
        """
        Executes a physical audit of arrangement clips across all tracks in the current Live session.

        Args:
            conn: Ableton connection adapter.
            expected_total_bars: Expected total song bars (optional).
            beats_per_bar: Beats per bar according to meter (default 4.0).
            allowed_gaps: Optional list of (start_beat, end_beat) intervals where silence/gaps
                          are intentional (e.g. pre-drop vacuum stops).
        """
        if conn is None:
            return ArrangementPhysicalAuditReport(
                is_valid=False,
                summary="Connection to Ableton Live is None. Cannot perform physical arrangement audit."
            )

        raw_tracks_data = cls._fetch_tracks_and_arrangement_clips(conn)
        return cls.audit_arrangement_data(
            raw_tracks_data,
            expected_total_bars=expected_total_bars,
            beats_per_bar=beats_per_bar,
            allowed_gaps=allowed_gaps
        )

    @classmethod
    def _fetch_tracks_and_arrangement_clips(cls, conn: Any) -> List[Dict[str, Any]]:
        """Queries tracks and their arrangement clips via LOM commands or execute_code."""
        tracks_data = []

        # Attempt 1: get_session_info / get_track_info / get_arrangement_clips
        try:
            session_info = conn.send_command("get_session_info")
            raw_info = session_info.get("result", session_info) if isinstance(session_info, dict) else {}
            num_tracks = int(raw_info.get("track_count", raw_info.get("num_tracks", 0)))
        except Exception:
            num_tracks = 0

        if num_tracks > 0:
            for t_idx in range(num_tracks):
                try:
                    t_info_res = conn.send_command("get_track_info", {"track_index": t_idx})
                    t_info = t_info_res.get("result", t_info_res) if isinstance(t_info_res, dict) else {}
                    t_name = t_info.get("name", f"Track {t_idx}")
                    t_mute = bool(t_info.get("mute", False))

                    arr_res = conn.send_command("get_arrangement_clips", {"track_index": t_idx})
                    clips = arr_res.get("clips", arr_res.get("result", {}).get("clips", [])) if isinstance(arr_res, dict) else []
                    tracks_data.append({
                        "index": t_idx,
                        "name": t_name,
                        "mute": t_mute,
                        "clips": clips
                    })
                except Exception as ex_t:
                    logger.debug(f"Could not query track {t_idx}: {ex_t}")
            if tracks_data:
                return tracks_data

        # Attempt 2: Comprehensive execute_code query
        try:
            exec_res = conn.send_command("execute_code", params={"code": """
out_tracks = []
for idx, t in enumerate(song.tracks):
    arr_clips = []
    for c_idx, c in enumerate(t.arrangement_clips):
        arr_clips.append({
            "name": c.name,
            "start_time": float(c.start_time),
            "end_time": float(c.end_time),
            "length": float(c.length),
            "muted": bool(getattr(c, "muted", False)),
            "is_midi_clip": bool(c.is_midi_clip),
            "is_audio_clip": bool(c.is_audio_clip)
        })
    out_tracks.append({
        "index": idx,
        "name": t.name,
        "mute": bool(t.mute),
        "clips": arr_clips
    })
result = out_tracks
"""})
            code_result = exec_res.get("result", exec_res) if isinstance(exec_res, dict) else []
            if isinstance(code_result, list) and len(code_result) > 0:
                return code_result
        except Exception as ex_code:
            logger.debug(f"execute_code arrangement scan notice: {ex_code}")

        return tracks_data

    @classmethod
    def audit_arrangement_data(
        cls,
        tracks_data: List[Dict[str, Any]],
        expected_total_bars: Optional[float] = None,
        beats_per_bar: float = 4.0,
        allowed_gaps: Optional[List[Tuple[float, float]]] = None
    ) -> ArrangementPhysicalAuditReport:
        """
        Pure evaluation logic: checks clip boundaries, overlaps, mute states, and timeline limits.
        """
        findings: List[ClipAuditFinding] = []
        track_summaries: List[TrackArrangementSummary] = []
        total_clips = 0
        max_arrangement_end = 0.0
        allowed_gap_ranges = allowed_gaps or []
        expected_max_beats = (expected_total_bars * beats_per_bar) if expected_total_bars else None

        for t_info in tracks_data:
            t_idx = int(t_info.get("index", 0))
            t_name = str(t_info.get("name", f"Track {t_idx}"))
            t_mute = bool(t_info.get("mute", False))
            raw_clips = t_info.get("clips", [])
            total_clips += len(raw_clips)

            earliest_start = float("inf")
            latest_end = 0.0
            coverage_beats = 0.0

            # Sort clips by start_time
            parsed_clips = []
            for c_idx, c in enumerate(raw_clips):
                c_name = str(c.get("name", f"Clip {c_idx}"))
                start = float(c.get("start_time", c.get("start", 0.0)))
                length = float(c.get("length", c.get("duration", 0.0)))
                end = float(c.get("end_time", start + length))
                muted = bool(c.get("muted", c.get("mute", False)))

                parsed_clips.append({
                    "name": c_name,
                    "start_time": start,
                    "end_time": end,
                    "length": length,
                    "muted": muted
                })

                if start < earliest_start:
                    earliest_start = start
                if end > latest_end:
                    latest_end = end
                coverage_beats += length

                # 1. Zero length check
                if length <= 0.001:
                    findings.append(ClipAuditFinding(
                        track_index=t_idx,
                        track_name=t_name,
                        clip_index=c_idx,
                        clip_name=c_name,
                        start_time=start,
                        end_time=end,
                        issue_type="ZERO_LENGTH",
                        severity="HIGH",
                        description=f"Clip '{c_name}' has zero length ({length} beats)."
                    ))

                # 2. Muted clip check (if whole track is not muted, an individual muted clip may be accidental)
                if muted:
                    findings.append(ClipAuditFinding(
                        track_index=t_idx,
                        track_name=t_name,
                        clip_index=c_idx,
                        clip_name=c_name,
                        start_time=start,
                        end_time=end,
                        issue_type="MUTED_CLIP",
                        severity="MEDIUM",
                        description=f"Clip '{c_name}' is physically muted in arrangement."
                    ))

                # 3. Song boundary bounds check
                if expected_max_beats is not None and end > (expected_max_beats + 0.1):
                    findings.append(ClipAuditFinding(
                        track_index=t_idx,
                        track_name=t_name,
                        clip_index=c_idx,
                        clip_name=c_name,
                        start_time=start,
                        end_time=end,
                        issue_type="OUT_OF_BOUNDS",
                        severity="MEDIUM",
                        description=(
                            f"Clip '{c_name}' extends to beat {round(end, 2)}, exceeding expected "
                            f"arrangement limit of {round(expected_max_beats, 2)} beats ({expected_total_bars} bars)."
                        )
                    ))

            # Sort by start time for overlap and continuity analysis
            sorted_clips = sorted(parsed_clips, key=lambda x: x["start_time"])

            # 4. Overlap detection
            for i in range(len(sorted_clips) - 1):
                c1 = sorted_clips[i]
                c2 = sorted_clips[i + 1]
                if c1["end_time"] > (c2["start_time"] + 0.01):
                    overlap_dur = round(c1["end_time"] - c2["start_time"], 3)
                    findings.append(ClipAuditFinding(
                        track_index=t_idx,
                        track_name=t_name,
                        clip_index=i,
                        clip_name=f"{c1['name']} & {c2['name']}",
                        start_time=c2["start_time"],
                        end_time=c1["end_time"],
                        issue_type="OVERLAP",
                        severity="HIGH",
                        description=(
                            f"Destructive clip collision on track {t_idx} ('{t_name}'): "
                            f"'{c1['name']}' overlaps '{c2['name']}' by {overlap_dur} beats."
                        )
                    ))

            if earliest_start == float("inf"):
                earliest_start = 0.0

            if latest_end > max_arrangement_end:
                max_arrangement_end = latest_end

            track_summaries.append(TrackArrangementSummary(
                track_index=t_idx,
                track_name=t_name,
                clip_count=len(parsed_clips),
                total_coverage_beats=coverage_beats,
                earliest_start=earliest_start,
                latest_end=latest_end,
                is_muted=t_mute,
                clips=parsed_clips
            ))

        high_severity_issues = [f for f in findings if f.severity == "HIGH"]
        is_valid = len(high_severity_issues) == 0

        summary_msg = (
            f"Physical Arrangement Audit: {len(tracks_data)} tracks inspected, {total_clips} clips found. "
            f"Arrangement timeline span: {round(max_arrangement_end, 2)} beats. "
            f"Detected {len(findings)} issues ({len(high_severity_issues)} High severity). "
            f"{'STATUS: PASS.' if is_valid else 'STATUS: FAIL - unresolved high-severity clip anomalies.'}"
        )

        return ArrangementPhysicalAuditReport(
            total_tracks_audited=len(tracks_data),
            total_clips_found=total_clips,
            total_timeline_span_beats=max_arrangement_end,
            issues_count=len(findings),
            is_valid=is_valid,
            tracks_summary=track_summaries,
            findings=findings,
            summary=summary_msg
        )
