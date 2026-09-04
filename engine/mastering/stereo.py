"""
Master Stereo and Low-End Mono Protection Engine.
"""
from typing import Dict, Any, Optional
from .models import MasterAction


class MasterStereoEngine:
    """Ensures solid mono sub-bass (<100 Hz) and healthy correlation."""

    @classmethod
    def evaluate_stereo(cls, features: Any) -> Dict[str, Any]:
        if isinstance(features, dict):
            overall_width = features.get("stereo_width", 1.0)
            low_width = features.get("low_end_width", 0.05)
            high_width = features.get("high_end_width", 1.1)
            correlation = features.get("stereo_correlation", 0.92)
        else:
            overall_width = getattr(features.stereo, "width", 1.0)
            low_width = getattr(features.stereo, "low_end_width", 0.05)
            high_width = getattr(features.stereo, "high_end_width", 1.1)
            correlation = getattr(features.stereo, "correlation", 0.92)

        low_end_risk = bool(low_width > 0.15)
        phase_risk = bool(correlation < 0.2)

        return {
            "overall_width": round(overall_width, 2),
            "low_end_width": round(low_width, 3),
            "high_end_width": round(high_width, 2),
            "correlation": round(correlation, 2),
            "low_end_risk": low_end_risk,
            "phase_risk": phase_risk
        }

    @classmethod
    def suggest_stereo_action(cls, features: Any) -> Optional[MasterAction]:
        st_eval = cls.evaluate_stereo(features)
        if st_eval["low_end_risk"] or st_eval["phase_risk"]:
            return MasterAction(
                action_type="STEREO",
                device_name="[MCP] Master Stereo",
                parameter_name="Bass Mono",
                target_value=1.0,
                delta=1.0,
                parameters={"Bass Mono": True, "Bass Mono Frequency": 100.0, "Width": 100.0}
            )
        return None

    @classmethod
    def calculate_settings(cls, correlation: float, width: float) -> MasterAction:
        needs_mono = correlation < 0.85 or width > 1.2
        return MasterAction(
            action_type="STEREO",
            device_name="[MCP] Master Stereo",
            parameter_name="Bass Mono",
            target_value=1.0 if needs_mono else 0.0,
            delta=1.0 if needs_mono else 0.0,
            parameters={
                "Bass Mono": True,
                "Bass Mono Frequency": 100.0,
                "Width": round(min(110.0, max(95.0, width * 100.0)), 1)
            }
        )
