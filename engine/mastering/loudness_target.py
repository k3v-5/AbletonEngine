"""
Loudness Target Calculator for delivery standards.
Consolidates delivery targets by consuming canonical profiles directly from engine.mix.loudness_standards.
"""
from typing import Dict, Any, Union
from .models import DeliveryTarget
from ..mix.loudness_standards import get_loudness_profile


def _build_delivery_specs() -> Dict[DeliveryTarget, Dict[str, Any]]:
    """Builds delivery specifications dynamically from the single canonical source of truth."""
    mapping = {
        DeliveryTarget.STREAMING: "STREAMING",
        DeliveryTarget.CLUB: "CLUB",
        DeliveryTarget.DIGITAL_DOWNLOAD: "DIGITAL_DOWNLOAD",
        DeliveryTarget.VIDEO: "VIDEO",
        DeliveryTarget.PREMASTER: "PREMASTER"
    }
    specs = {}
    for target, prof_name in mapping.items():
        prof = get_loudness_profile(prof_name)
        specs[target] = {
            "target_lufs": prof.target_lufs,
            "lufs_min": round(prof.target_lufs - prof.tolerance_lufs, 2),
            "lufs_max": round(prof.target_lufs + prof.tolerance_lufs, 2),
            "tp_ceiling": prof.max_true_peak_dbtp,
            "description": prof.description,
            "max_gain_reduction_db": prof.max_gain_reduction_db
        }
    return specs


DELIVERY_SPECS = _build_delivery_specs()


class LoudnessTargetCalculator:
    """Calculates delivery targets and loudness specs from the unified standards registry."""

    @classmethod
    def get_target_specs(cls, target: Union[str, DeliveryTarget]) -> Dict[str, Any]:
        if isinstance(target, str):
            try:
                target = DeliveryTarget(target)
            except ValueError:
                target = DeliveryTarget.STREAMING
        return DELIVERY_SPECS.get(target, DELIVERY_SPECS[DeliveryTarget.STREAMING])

    @classmethod
    def get_target_lufs(cls, target: Union[str, DeliveryTarget]) -> float:
        return cls.get_target_specs(target)["target_lufs"]
