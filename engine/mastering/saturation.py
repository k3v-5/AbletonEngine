"""
Master Saturation and Harmonic Exciter Engine.
Conservative analog tape/tube warmth; automatically bypassed if distortion is detected.
"""
from typing import Optional, Any
from .models import MasterAction, MasteringMode


class MasterSaturationEngine:
    """Generates subtle analog saturation if spectral profile is thin."""

    @classmethod
    def plan_saturation(cls, features: Any) -> Optional[MasterAction]:
        if isinstance(features, dict):
            classification = features.get("spectral_classification", "balanced")
        else:
            classification = getattr(features.spectral_profile, "classification", "balanced")

        if classification == "thin":
            return MasterAction(
                action_type="SATURATION",
                device_name="[MCP] Master Saturation",
                parameter_name="Drive",
                target_value=1.0,
                delta=1.0,
                parameters={"Drive": 1.0, "Curve": "Warm", "Dry/Wet": 100.0}
            )
        return None

    @classmethod
    def calculate_settings(cls, mode: MasteringMode = MasteringMode.BALANCED, clipping_detected: bool = False) -> MasterAction:
        if clipping_detected:
            return MasterAction(
                action_type="SATURATION",
                device_name="[MCP] Master Saturation",
                parameter_name="Bypass",
                target_value=1.0,
                delta=0.0,
                bypass=True,
                parameters={"Bypass": True},
                rationale="Clipping detected in source; saturation strictly bypassed to avoid distortion."
            )
        return MasterAction(
            action_type="SATURATION",
            device_name="[MCP] Master Saturation",
            parameter_name="Drive",
            target_value=0.8,
            delta=0.8,
            parameters={"Drive": 0.8, "Curve": "Warm", "Dry/Wet": 100.0},
            rationale="Subtle tape saturation for harmonic density."
        )
