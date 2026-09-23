# engine/session/track_resolver.py
"""
Live DAW Track Resolver Service (Single Responsibility Principle - SRP):
Encapsulates track index resolution heuristics against Ableton Live,
strictly prioritizing exact names and role tags to eliminate index drift
caused by template tracks, foldable groups, aux returns, or moved tracks.
"""

from typing import Dict, Any, Optional
import logging
from engine.production.copilot.role_orchestrator import RoleTrackOrchestrator

logger = logging.getLogger("LiveTrackResolver")


class LiveTrackResolver:
    """Service dedicated to resolving physical track indices in Ableton Live."""

    @classmethod
    def resolve_track_index(cls, conn: Any, trk: Dict[str, Any]) -> int:
        """
        Dynamically resolves the physical track index in Live for a tracked entity.
        Strictly prioritizes exact name and role tag matching over blind index access.
        Prevents index drift caused by pre-existing template tracks, aux/return buses,
        foldable group tracks, audio tracks, or moved tracks.
        """
        if conn is None or not hasattr(conn, "send_command"):
            return trk.get("index", 0)

        t_idx = trk.get("index", 0)
        t_name = str(trk.get("name", "")).strip()
        t_role = str(trk.get("role", "")).strip()

        try:
            # 1. Quick check: does the current index still match?
            ti = conn.send_command("get_track_info", {"track_index": t_idx})
            res_ti = ti.get("result", ti) if isinstance(ti, dict) else {}
            live_name = str(res_ti.get("name", "")).strip()
            is_foldable = res_ti.get("is_foldable", False)

            # If it's a foldable group track, or template/reference track, it is NOT our track
            is_unrelated_template = (
                any(ign in live_name.lower() for ign in ["reference", "guia", "guía", "plantilla", "template"])
                and not any(ign in t_name.lower() for ign in ["reference", "guia", "guía"])
            )

            if not is_foldable and not is_unrelated_template:
                # Exact name or role tag match on current index
                if (t_name and t_name.lower() == live_name.lower()) or (t_role and f"[{t_role.lower()}]" in live_name.lower()):
                    return t_idx
                # Substring match if name is sufficiently distinctive
                if t_name and len(t_name) >= 3 and t_name.lower() in live_name.lower():
                    return t_idx

            # 2. Index drifted or occupied by another track: scan all session tracks dynamically
            s_info = conn.send_command("get_session_info", {})
            res_s = s_info.get("result", s_info) if isinstance(s_info, dict) else {}
            t_count = int(res_s.get("track_count", 0))

            # Candidates pass 1: Exact name or role bracket tag
            for cand_idx in range(t_count):
                try:
                    c_ti = conn.send_command("get_track_info", {"track_index": cand_idx})
                    c_res = c_ti.get("result", c_ti) if isinstance(c_ti, dict) else {}
                    if c_res.get("is_foldable", False):
                        continue
                    c_name = str(c_res.get("name", "")).strip()
                    if any(ign in c_name.lower() for ign in ["reference", "guia", "guía", "plantilla"]) and not any(ign in t_name.lower() for ign in ["reference", "guia", "guía"]):
                        continue
                    # Check exact name
                    if t_name and c_name.lower() == t_name.lower():
                        trk["index"] = cand_idx
                        return cand_idx
                    # Check bracketed role
                    if t_role and f"[{t_role.lower()}]" in c_name.lower():
                        trk["index"] = cand_idx
                        return cand_idx
                except Exception:
                    continue

            # Candidates pass 2: Normalized role and prefix/substring match
            for cand_idx in range(t_count):
                try:
                    c_ti = conn.send_command("get_track_info", {"track_index": cand_idx})
                    c_res = c_ti.get("result", c_ti) if isinstance(c_ti, dict) else {}
                    if c_res.get("is_foldable", False):
                        continue
                    c_name = str(c_res.get("name", "")).strip()
                    if any(ign in c_name.lower() for ign in ["reference", "guia", "guía", "plantilla"]) and not any(ign in t_name.lower() for ign in ["reference", "guia", "guía"]):
                        continue
                    norm_c_role = RoleTrackOrchestrator.normalize_role(c_name)
                    if t_role and norm_c_role and norm_c_role == t_role:
                        trk["index"] = cand_idx
                        return cand_idx
                    if t_name and len(t_name) >= 3 and (c_name.lower().startswith(t_name.lower()) or t_name.lower() in c_name.lower()):
                        trk["index"] = cand_idx
                        return cand_idx
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Track resolution notice: {e}")

        return t_idx
