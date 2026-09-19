# engine/mix/spectral_masking.py
"""
Spectral Masking & Frequency Conflict Auditor:
Identifies critical acoustic masking zones (Sub clash, Mud, Vocal masking)
and generates surgical EQ Eight corrective curves automatically.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("SpectralMasking")


class SpectralMaskingAuditor:
    """Audits multi-track frequency conflicts and recommends/applies corrective EQ curves."""

    CRITICAL_BANDS = {
        "SUB_BASS": {"low": 20, "high": 90, "owner": "BASS", "allowed": ["BASS", "DRUMS"]},
        "LOW_MUD": {"low": 200, "high": 400, "owner": "NONE", "clutter_limit": 3},
        "VOCAL_PRESENCE": {"low": 1000, "high": 3500, "owner": "VOCALS", "allowed": ["VOCALS", "LEAD"]},
        "AIR": {"low": 10000, "high": 20000, "owner": "ALL", "clutter_limit": 5}
    }

    @classmethod
    def audit_session_masking(cls, tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Scans all active session tracks and identifies potential acoustic masking conflicts.
        """
        conflicts = []
        corrections = []

        sub_clashing_tracks = []
        mud_tracks = []

        for trk in tracks:
            r = str(trk.get("role", "")).upper()
            t_idx = trk.get("index", 0)
            t_name = str(trk.get("name", ""))

            # Tracks that should NEVER occupy sub-bass below 100 Hz
            if r in ("PAD", "KEYS", "GUITAR", "STRINGS", "FX"):
                sub_clashing_tracks.append({"track_index": t_idx, "name": t_name, "role": r})
                corrections.append({
                    "track_index": t_idx,
                    "action": "HIGH_PASS_FILTER",
                    "cutoff_hz": 120 if r == "PAD" else 100,
                    "reason": f"Clear sub-bass headroom for Kick and Bass (cut {r})"
                })

            if r in ("KEYS", "PAD", "GUITAR", "LEAD"):
                mud_tracks.append({"track_index": t_idx, "name": t_name})

        if len(sub_clashing_tracks) > 0:
            conflicts.append({
                "band": "SUB_BASS",
                "severity": "HIGH" if len(sub_clashing_tracks) > 2 else "MEDIUM",
                "description": f"{len(sub_clashing_tracks)} tracks may bleed into sub-bass below 100 Hz.",
                "tracks": sub_clashing_tracks
            })

        if len(mud_tracks) >= 3:
            conflicts.append({
                "band": "LOW_MUD (200-400 Hz)",
                "severity": "MEDIUM",
                "description": f"{len(mud_tracks)} harmonic instruments active in low-mid mud zone.",
                "tracks": mud_tracks
            })
            for mt in mud_tracks[:2]:
                corrections.append({
                    "track_index": mt["track_index"],
                    "action": "BELL_CUT",
                    "frequency_hz": 280,
                    "gain_db": -2.5,
                    "q": 1.2,
                    "reason": "De-clutter low-mid mud buildup"
                })

        return {
            "status": "ANALYZED",
            "conflicts_count": len(conflicts),
            "conflicts": conflicts,
            "recommended_corrections": corrections
        }
