"""
Master Bus Glue Compressor Engine.
Focuses on dynamic stabilization, groove cohesion, and glue, NOT volume maximization.
"""
from typing import Optional, Dict, Any
from .models import MasterAction, MasteringMode


class MasterCompressorEngine:
    """Evaluates need for gentle bus compression glue."""

    @classmethod
    def plan_compression(cls, features: Any) -> Optional[MasterAction]:
        crest = getattr(features, "crest_factor", features.get("crest_factor_db", 12.0) if isinstance(features, dict) else 12.0)
        lra = getattr(features, "lra", features.get("dynamic_range", 5.0) if isinstance(features, dict) else 5.0)

        if crest >= 13.0 and lra > 4.5:
            return MasterAction(
                action_type="COMPRESSOR",
                device_name="[MCP] Master Glue",
                parameter_name="Threshold",
                target_value=-16.0,
                delta=-2.0,
                parameters={"Threshold": -16.0, "Attack": 30.0, "Ratio": 1.5, "Release": "Auto"}
            )
        return None

    @classmethod
    def calculate_settings(cls, crest_factor: float, mode: MasteringMode = MasteringMode.BALANCED) -> MasterAction:
        if crest_factor >= 12.5:
            return MasterAction(
                action_type="COMPRESSOR",
                device_name="[MCP] Master Glue",
                parameter_name="Threshold",
                target_value=-16.0,
                delta=-2.0,
                parameters={"Threshold": -16.0, "Attack": 30.0, "Ratio": 1.5, "Release": "Auto"},
                rationale="Subtle bus glue compression for cohesion (1.0 dB gain reduction)."
            )
        return MasterAction(
            action_type="COMPRESSOR",
            device_name="[MCP] Master Glue",
            parameter_name="Bypass",
            target_value=1.0,
            delta=0.0,
            bypass=True,
            parameters={"Bypass": True},
            rationale="Mix dynamics are already compact; compressor bypassed to preserve transients."
        )
