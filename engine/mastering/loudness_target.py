"""
Loudness Target Calculator for delivery standards.
"""
from typing import Dict, Any, Union
from .models import DeliveryTarget

DELIVERY_SPECS = {
    DeliveryTarget.STREAMING: {
        "target_lufs": -14.0,
        "lufs_min": -14.0,
        "lufs_max": -10.0,
        "tp_ceiling": -1.0,
        "description": "Standard streaming platforms (Spotify, Apple Music, YouTube)"
    },
    DeliveryTarget.CLUB: {
        "target_lufs": -7.5,
        "lufs_min": -8.0,
        "lufs_max": -6.5,
        "tp_ceiling": -0.3,
        "description": "Club / DJ / Sound System play (maximum punch, controlled peaks)"
    },
    DeliveryTarget.DIGITAL_DOWNLOAD: {
        "target_lufs": -9.0,
        "lufs_min": -10.0,
        "lufs_max": -8.0,
        "tp_ceiling": -0.5,
        "description": "Bandcamp, Beatport, direct digital download"
    },
    DeliveryTarget.VIDEO: {
        "target_lufs": -15.0,
        "lufs_min": -16.0,
        "lufs_max": -14.0,
        "tp_ceiling": -1.0,
        "description": "Broadcast / Film / YouTube sync standards"
    },
    DeliveryTarget.PREMASTER: {
        "target_lufs": -18.0,
        "lufs_min": -20.0,
        "lufs_max": -16.0,
        "tp_ceiling": -3.0,
        "description": "Pre-master delivery for external mastering engineer"
    }
}


class LoudnessTargetCalculator:
    """Calculates delivery targets and loudness specs."""

    @classmethod
    def get_target_specs(cls, target: Union[str, DeliveryTarget]) -> Dict[str, Any]:
        if isinstance(target, str):
            target = DeliveryTarget(target)
        return DELIVERY_SPECS.get(target, DELIVERY_SPECS[DeliveryTarget.STREAMING])

    @classmethod
    def get_target_lufs(cls, target: Union[str, DeliveryTarget]) -> float:
        return cls.get_target_specs(target)["target_lufs"]
