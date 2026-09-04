"""
True Peak Protection Engine.
Defines platform true peak ceilings and verifies inter-sample peak compliance.
Consolidates ceiling limits from engine.mix.loudness_standards.
"""
from typing import Union
from .models import DeliveryTarget
from ..mix.loudness_standards import get_loudness_profile


class TruePeakEngine:
    """Platform True Peak limit definitions and verification."""

    CEILINGS = {
        DeliveryTarget.STREAMING: -1.0,
        DeliveryTarget.CLUB: -0.3,
        DeliveryTarget.DIGITAL_DOWNLOAD: -0.5,
        DeliveryTarget.VIDEO: -1.0,
        DeliveryTarget.PREMASTER: -3.0
    }

    @classmethod
    def get_ceiling(cls, target: Union[str, DeliveryTarget]) -> float:
        if isinstance(target, str):
            try:
                target = DeliveryTarget(target)
            except ValueError:
                target = DeliveryTarget.STREAMING
        profile_map = {
            DeliveryTarget.STREAMING: "STREAMING",
            DeliveryTarget.CLUB: "CLUB",
            DeliveryTarget.DIGITAL_DOWNLOAD: "DIGITAL_DOWNLOAD",
            DeliveryTarget.VIDEO: "VIDEO",
            DeliveryTarget.PREMASTER: "PREMASTER"
        }
        prof_name = profile_map.get(target, "STREAMING")
        try:
            return get_loudness_profile(prof_name).max_true_peak_dbtp
        except Exception:
            return cls.CEILINGS.get(target, -1.0)

    @classmethod
    def get_target(cls, target: Union[str, DeliveryTarget]) -> float:
        return cls.get_ceiling(target)
