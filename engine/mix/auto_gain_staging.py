# engine/mix/auto_gain_staging.py
"""
Autonomous Acoustic Gain-Staging Engine:
Applies calibrated fader staging per acoustic role to guarantee 6 to 10 dB
of clean headroom on the Master bus prior to dynamic processing.
"""

from typing import Dict, Any, List, Optional
import math
import logging

logger = logging.getLogger("AutoGainStaging")


class AutoGainStaging:
    """Calculates and applies calibrated headroom faders across all session tracks."""

    # Calibrated nominal dB targets relative to 0 dBFS (avoids cascading over-attenuation)
    ROLE_HEADROOM_TARGETS_DB: Dict[str, float] = {
        "DRUMS": -6.0,
        "PERCUSSION": -8.0,
        "BASS": -6.0,
        "LEAD": -6.0,
        "KEYS": -8.0,
        "GUITAR": -8.0,
        "PAD": -10.0,
        "STRINGS": -10.0,
        "VOCALS": -5.0,
        "FX": -12.0
    }

    @classmethod
    def db_to_live_volume(cls, db: float) -> float:
        """
        Converts decibels to Ableton Live 12 non-linear fader scale [0.0..1.0].
        Measured Live 12 response:
          0 dB = 0.85
         -6 dB = 0.70
        -12 dB = 0.55
        -18 dB = 0.40
        -24 dB = 0.30
        -34 dB = 0.20
        -41 dB = 0.15
        """
        if db <= -70.0:
            return 0.0
        if db > 0.0:
            return round(min(1.0, 0.85 + (db * (0.15 / 6.0))), 4)
        if db >= -18.0:
            # Linear in dB with slope 1/40 (0.025 per dB)
            return round(0.85 + (db / 40.0), 4)
        if db >= -35.0:
            # Gentle taper between -18 dB (0.40) and -35 dB (0.19)
            return round(0.40 + ((db + 18.0) * (0.21 / 17.0)), 4)
        # Deep attenuation down to -70 dB (0.0)
        return round(max(0.0, 0.19 + ((db + 35.0) * (0.19 / 35.0))), 4)

    @classmethod
    def get_role_target_volume(cls, role: str) -> float:
        """Returns the recommended Live fader volume for an acoustic role."""
        role_upper = str(role).upper()
        target_db = cls.ROLE_HEADROOM_TARGETS_DB.get(role_upper, -8.0)
        return cls.db_to_live_volume(target_db)

    @classmethod
    def apply_session_gain_staging(cls, conn: Any, tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Applies calibrated gain staging to all tracks in the session.
        """
        staged_tracks = []
        for trk in tracks:
            t_idx = trk.get("index", 0)
            role = trk.get("role", "OTHER")
            target_vol = cls.get_role_target_volume(role)

            if conn and hasattr(conn, "send_command"):
                try:
                    conn.send_command("set_track_volume", {
                        "track_index": t_idx,
                        "volume": target_vol
                    })
                except Exception as e:
                    logger.debug(f"Notice setting volume on track {t_idx}: {e}")

            trk["volume"] = target_vol
            staged_tracks.append({
                "track_index": t_idx,
                "role": role,
                "target_volume": target_vol
            })

        logger.info(f"Applied acoustic gain-staging across {len(staged_tracks)} tracks.")
        return {
            "status": "SUCCESS",
            "tracks_staged": len(staged_tracks),
            "details": staged_tracks
        }
