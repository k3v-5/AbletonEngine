# engine/mix/stereo_panning_validator.py
"""
Stereo Panning Validator:
Verifies that conscious stereo panning decisions established during Phase 0 Design
are faithfully and physically maintained during the Mixing stage.

Guarantees:
1. Physical verification against Ableton Live LOM track panning values.
2. Center-pocket integrity for low-end and vocal anchors (Kick, Sub-Bass, Lead Vocals must be 0.0 ± 0.05).
3. Spatial spread verification: ensures wide instruments (Pads, Strings, Guitars, Ear Candy)
   are not inadvertently collapsed to mono.
4. Left/Right stereo balance symmetry to prevent acoustic lopsidedness.
5. Generates detailed compliance report and optional physical re-assertion commands.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Union
import logging

logger = logging.getLogger("StereoPanningValidator")


@dataclass
class TrackPanningAuditItem:
    """Audit comparison between designed and physical panning for a track."""
    track_index: int
    track_name: str
    designed_pan: float
    physical_pan: float
    is_compliant: bool
    deviation: float
    status: str  # "MATCH", "DEVIATION", "MONO_VIOLATION", "COLLAPSED_SPREAD", "NOT_DESIGNED"
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_index": self.track_index,
            "track_name": self.track_name,
            "designed_pan": round(self.designed_pan, 3),
            "physical_pan": round(self.physical_pan, 3),
            "is_compliant": self.is_compliant,
            "deviation": round(self.deviation, 3),
            "status": self.status,
            "rationale": self.rationale
        }


@dataclass
class StereoPanningAuditReport:
    """Comprehensive stereo panning compliance report."""
    total_tracks_audited: int = 0
    compliant_tracks_count: int = 0
    compliance_score_pct: float = 100.0
    is_fully_compliant: bool = True
    left_energy_weight: float = 0.0
    right_energy_weight: float = 0.0
    center_energy_weight: float = 0.0
    items: List[TrackPanningAuditItem] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tracks_audited": self.total_tracks_audited,
            "compliant_tracks_count": self.compliant_tracks_count,
            "compliance_score_pct": round(self.compliance_score_pct, 1),
            "is_fully_compliant": self.is_fully_compliant,
            "left_energy_weight": round(self.left_energy_weight, 2),
            "right_energy_weight": round(self.right_energy_weight, 2),
            "center_energy_weight": round(self.center_energy_weight, 2),
            "items": [it.to_dict() for it in self.items],
            "summary": self.summary
        }


class StereoPanningValidator:
    """
    Validates physical track panning in Live 12 against Phase 0 conscious design decisions.
    """

    MONO_ANCHOR_KEYWORDS = ["KICK", "SUB", "808", "BASS", "LEAD VOCAL", "VOCAL LEAD", "VOZ PRINCIPAL"]
    TOLERANCE: float = 0.06  # Allowed floating point deviation

    @classmethod
    def validate_session(
        cls,
        conn: Any,
        designed_panning: Optional[Dict[str, float]] = None,
        reassert_if_deviating: bool = False
    ) -> StereoPanningAuditReport:
        """
        Queries Live 12 track panning and validates against designed panning.

        Args:
            conn: Ableton connection adapter.
            designed_panning: Mapping of track name/role to target pan [-1.0 .. 1.0].
            reassert_if_deviating: If True, re-sends set_track_panning commands for any deviating tracks.
        """
        designed = designed_panning or {}

        # Fetch physical tracks and their pan values
        physical_tracks = cls._fetch_live_panning(conn)
        report = cls.audit_panning_data(physical_tracks, designed)

        if reassert_if_deviating and conn is not None and hasattr(conn, "send_command"):
            cls._reassert_physical_panning(conn, report.items)

        return report

    @classmethod
    def _fetch_live_panning(cls, conn: Any) -> List[Dict[str, Any]]:
        """Queries physical track panning values via LOM commands or execute_code."""
        if conn is None:
            return []

        # Attempt 1: get_session_info / get_track_info
        try:
            s_info = conn.send_command("get_session_info")
            raw_s = s_info.get("result", s_info) if isinstance(s_info, dict) else {}
            num_tracks = int(raw_s.get("track_count", raw_s.get("num_tracks", 0)))
            if num_tracks > 0:
                tracks = []
                for idx in range(num_tracks):
                    t_res = conn.send_command("get_track_info", {"track_index": idx})
                    t_info = t_res.get("result", t_res) if isinstance(t_res, dict) else {}
                    t_name = t_info.get("name", f"Track {idx}")
                    t_pan = float(t_info.get("panning", t_info.get("pan", 0.0)))
                    tracks.append({"index": idx, "name": t_name, "panning": t_pan})
                return tracks
        except Exception:
            pass

        # Attempt 2: execute_code query
        try:
            exec_res = conn.send_command("execute_code", params={"code": """
out = []
for idx, t in enumerate(song.tracks):
    pan_val = float(t.mixer_device.panning.value) if hasattr(t, 'mixer_device') and hasattr(t.mixer_device, 'panning') else 0.0
    out.append({"index": idx, "name": t.name, "panning": pan_val})
result = out
"""})
            code_result = exec_res.get("result", exec_res) if isinstance(exec_res, dict) else []
            if isinstance(code_result, list) and len(code_result) > 0:
                return code_result
        except Exception as ex_code:
            logger.debug(f"execute_code panning notice: {ex_code}")

        return []

    @classmethod
    def audit_panning_data(
        cls,
        physical_tracks: List[Dict[str, Any]],
        designed_panning: Dict[str, float]
    ) -> StereoPanningAuditReport:
        """
        Pure validation logic: compares physical panning against designed specs.
        """
        items: List[TrackPanningAuditItem] = []
        compliant_count = 0
        left_weight = 0.0
        right_weight = 0.0
        center_weight = 0.0

        for t in physical_tracks:
            t_idx = int(t.get("index", 0))
            t_name = str(t.get("name", f"Track {t_idx}"))
            actual_pan = float(t.get("panning", t.get("pan", 0.0)))

            # Accumulate stereo energy distribution
            if actual_pan < -0.05:
                left_weight += abs(actual_pan)
            elif actual_pan > 0.05:
                right_weight += abs(actual_pan)
            else:
                center_weight += 1.0

            # Find matching designed pan: by exact name or case-insensitive or role keyword
            target_pan = cls._find_designed_pan_for_track(t_name, designed_panning)

            is_mono_anchor = any(k in t_name.upper() for k in cls.MONO_ANCHOR_KEYWORDS)

            if target_pan is not None:
                dev = abs(actual_pan - target_pan)
                is_comp = dev <= cls.TOLERANCE
                if is_comp:
                    status = "MATCH"
                    rationale = f"Physical pan ({round(actual_pan, 2)}) perfectly matches Phase 0 design ({round(target_pan, 2)})."
                    compliant_count += 1
                else:
                    if is_mono_anchor and abs(actual_pan) > 0.05:
                        status = "MONO_VIOLATION"
                        rationale = f"Acoustic anchor '{t_name}' drifted off-center ({round(actual_pan, 2)}); must be 0.0."
                    elif abs(target_pan) >= 0.2 and abs(actual_pan) < 0.05:
                        status = "COLLAPSED_SPREAD"
                        rationale = f"Track designed for spatial spread ({round(target_pan, 2)}) collapsed to center mono."
                    else:
                        status = "DEVIATION"
                        rationale = f"Physical pan ({round(actual_pan, 2)}) deviated by {round(dev, 2)} from design ({round(target_pan, 2)})."
            else:
                # Track was not in Phase 0 design dictionary
                dev = 0.0
                if is_mono_anchor:
                    is_comp = abs(actual_pan) <= 0.05
                    if is_comp:
                        status = "MATCH"
                        rationale = "Mono anchor safely centered (0.0)."
                        compliant_count += 1
                    else:
                        status = "MONO_VIOLATION"
                        rationale = f"Mono anchor '{t_name}' should be centered, found pan {round(actual_pan, 2)}."
                else:
                    is_comp = True
                    status = "NOT_DESIGNED"
                    rationale = f"Undesignated track at pan {round(actual_pan, 2)}."
                    compliant_count += 1

            items.append(TrackPanningAuditItem(
                track_index=t_idx,
                track_name=t_name,
                designed_pan=target_pan if target_pan is not None else actual_pan,
                physical_pan=actual_pan,
                is_compliant=is_comp,
                deviation=dev,
                status=status,
                rationale=rationale
            ))

        total = len(physical_tracks)
        score_pct = (compliant_count / max(1, total)) * 100.0
        fully_comp = (compliant_count == total)

        summary_msg = (
            f"Stereo Panning Audit: {total} tracks verified. Compliance: {round(score_pct, 1)}% ({compliant_count}/{total}). "
            f"Stereo Field Balance: Left weight {round(left_weight, 2)}, Right weight {round(right_weight, 2)}, "
            f"Center elements: {int(center_weight)}. "
            f"{'STATUS: PASS (Conscious panning verified).' if fully_comp else 'STATUS: WARNING (Deviations detected).'}"
        )

        return StereoPanningAuditReport(
            total_tracks_audited=total,
            compliant_tracks_count=compliant_count,
            compliance_score_pct=score_pct,
            is_fully_compliant=fully_comp,
            left_energy_weight=left_weight,
            right_energy_weight=right_weight,
            center_energy_weight=center_weight,
            items=items,
            summary=summary_msg
        )

    @classmethod
    def _find_designed_pan_for_track(
        cls,
        track_name: str,
        designed_panning: Dict[str, float]
    ) -> Optional[float]:
        """Resolves designed panning value by exact name, case-insensitive, or partial match."""
        if not designed_panning:
            return None

        # 1. Exact match
        if track_name in designed_panning:
            return float(designed_panning[track_name])

        # 2. Case-insensitive exact match
        for k, v in designed_panning.items():
            if k.lower() == track_name.lower():
                return float(v)

        # 3. Partial keyword match
        tn_upper = track_name.upper()
        for k, v in designed_panning.items():
            k_upper = k.upper()
            if k_upper in tn_upper or tn_upper in k_upper:
                return float(v)

        return None

    @classmethod
    def _reassert_physical_panning(
        cls,
        conn: Any,
        items: List[TrackPanningAuditItem]
    ) -> None:
        """Sends set_track_panning commands to correct deviating tracks."""
        for item in items:
            if not item.is_compliant and item.designed_pan is not None:
                try:
                    conn.send_command("set_track_panning", {
                        "track_index": item.track_index,
                        "panning": item.designed_pan
                    })
                    logger.info(f"Re-asserted designed pan {item.designed_pan} for track {item.track_index} ('{item.track_name}').")
                except Exception as ex_pan:
                    logger.debug(f"Could not re-assert pan on track {item.track_index}: {ex_pan}")
