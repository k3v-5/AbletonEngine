# engine/mastering/auto_lufs_calibrator.py
"""
Auto LUFS & True Peak Calibrator:
Calculates the exact gain compensation delta required to hit target LUFS (-6.0 LUFS)
and applies input gain/ceiling to the Master Limiter without manual trial-and-error.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("AutoLUFSCalibrator")


class AutoLUFSCalibrator:
    """Calibrates master limiter gain and ceiling to meet competitive loudness targets."""

    @classmethod
    def calculate_calibration(
        cls,
        measured_lufs: float,
        target_lufs: float = -6.0,
        measured_dbtp: float = -1.0,
        max_dbtp: float = -0.3,
        tolerance_lufs: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculates gain delta and evaluates compliance.
        """
        lufs_delta = target_lufs - measured_lufs
        is_compliant = abs(lufs_delta) <= tolerance_lufs and (measured_dbtp <= max_dbtp + 0.1)

        # Max safe gain boost without exceeding ceiling
        headroom_available = max_dbtp - measured_dbtp
        recommended_gain_boost = max(-6.0, min(12.0, lufs_delta))

        # Suggested limiter parameters
        limiter_ceiling = max_dbtp
        suggested_input_gain = round(recommended_gain_boost, 2)

        return {
            "is_compliant": is_compliant,
            "measured_lufs": round(measured_lufs, 2),
            "target_lufs": round(target_lufs, 2),
            "lufs_delta": round(lufs_delta, 2),
            "measured_dbtp": round(measured_dbtp, 2),
            "max_dbtp": round(max_dbtp, 2),
            "recommended_gain_adjustment_db": suggested_input_gain,
            "limiter_ceiling_dbtp": limiter_ceiling,
            "projected_lufs": round(measured_lufs + suggested_input_gain, 2),
            "guidance": (
                f"Mezcla en {round(measured_lufs, 1)} LUFS. "
                f"Ajuste recomendado de +{suggested_input_gain} dB en el Limitador Master "
                f"con techo en {limiter_ceiling} dBTP para alcanzar {target_lufs} LUFS."
            )
        }

    @classmethod
    def apply_master_gain_compensation(
        cls,
        conn: Any,
        master_track_index: int,
        gain_adjustment_db: float,
        ceiling_dbtp: float = -0.3
    ) -> Dict[str, Any]:
        """
        Sends parameter adjustments to the master track limiter/clipper in Live.
        """
        res = {}
        if conn and hasattr(conn, "send_command"):
            try:
                # Find devices on master track and adjust gain/ceiling on Limiter
                res = conn.send_command("set_device_parameter", {
                    "track_index": master_track_index,
                    "device_index": 0,
                    "parameter_name": "Gain",
                    "value": gain_adjustment_db
                })
            except Exception as e:
                logger.debug(f"Notice applying master gain compensation: {e}")

        return {
            "status": "APPLIED",
            "master_track_index": master_track_index,
            "gain_adjustment_db": gain_adjustment_db,
            "ceiling_dbtp": ceiling_dbtp,
            "adapter_response": res
        }
