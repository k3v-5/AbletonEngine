"""
Master True Peak Limiter Engine.
Controls inter-sample peaks with strict maximum gain reduction guardrails (<= 2.5 dB).
"""
from typing import Tuple, Dict, Any, Optional
from .models import MasterAction, DeliveryTarget
from .true_peak import TruePeakEngine


class MasterLimiterEngine:
    """Manages true peak brickwall limiting with gain reduction safety."""

    MAX_SAFE_GAIN_REDUCTION = 2.5  # dB

    @classmethod
    def plan_limiter(cls, features: Any, target_lufs: float, delivery: DeliveryTarget) -> Tuple[Optional[MasterAction], Dict[str, Any]]:
        ceiling = TruePeakEngine.get_target(delivery)
        current_lufs = getattr(features, "lufs_integrated", features.get("integrated_lufs", -18.0) if isinstance(features, dict) else -18.0)
        current_tp = getattr(features, "true_peak_db", features.get("true_peak_dbtp", -4.0) if isinstance(features, dict) else -4.0)

        needed_gain = target_lufs - current_lufs
        clamped_gain = max(0.0, min(3.0, needed_gain))
        expected_gr = max(0.0, current_tp + clamped_gain - ceiling)
        warning_triggered = expected_gr > cls.MAX_SAFE_GAIN_REDUCTION

        action = MasterAction(
            action_type="LIMITER",
            device_name="[MCP] Master Limiter",
            parameter_name="Gain",
            target_value=round(clamped_gain, 1),
            delta=round(clamped_gain, 1),
            parameters={"Gain": round(clamped_gain, 1), "Ceiling": ceiling, "Lookahead": 5.0}
        )

        metrics = {
            "target_ceiling_dbtp": ceiling,
            "gain_applied_db": round(clamped_gain, 1),
            "expected_gain_reduction_db": round(expected_gr, 1),
            "excessive_gain_reduction_warning": warning_triggered
        }
        return action, metrics

    @classmethod
    def calculate_settings(cls, current_lufs: float, target_lufs: float,
                           current_tp: float, tp_ceiling: float) -> MasterAction:
        needed_gain = target_lufs - current_lufs
        clamped_gain = max(0.0, min(3.5, needed_gain))
        expected_gr = max(0.0, current_tp + clamped_gain - tp_ceiling)

        # Cap gain reduction to guardrail
        if expected_gr > cls.MAX_SAFE_GAIN_REDUCTION:
            clamped_gain = max(0.0, tp_ceiling - current_tp + cls.MAX_SAFE_GAIN_REDUCTION)

        return MasterAction(
            action_type="LIMITER",
            device_name="[MCP] Master Limiter",
            parameter_name="Gain",
            target_value=round(clamped_gain, 1),
            delta=round(clamped_gain, 1),
            parameters={
                "Gain": round(clamped_gain, 1),
                "Ceiling": round(tp_ceiling, 2),
                "Lookahead": 5.0,
                "Release": 100.0
            },
            rationale=f"Brickwall True Peak limiter locked to platform ceiling {tp_ceiling:.1f} dBTP."
        )
