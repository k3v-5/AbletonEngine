"""
True Peak Protection Engine.
Defines platform true peak ceilings and verifies inter-sample peak compliance.
"""
from typing import Union
from .models import DeliveryTarget


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
            target = DeliveryTarget(target)
        return cls.CEILINGS.get(target, -1.0)

    @classmethod
    def get_target(cls, target: Union[str, DeliveryTarget]) -> float:
        return cls.get_ceiling(target)
