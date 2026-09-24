# engine/fx/__init__.py
"""
Audio Effects, Role-Based Insert Chains, Parameter Supervision, and Channel Strip Engines.
"""

from .role_fx_catalog import (
    ROLE_INSERT_EFFECTS,
    ROLE_FREQUENCY_GUIDE,
    VALHALLA_VINTAGE_VERB_PARAMS,
)
from .device_parameter_supervisor import DeviceParameterSupervisor
from .track_fx_rack import TrackFXRack

__all__ = [
    "ROLE_INSERT_EFFECTS",
    "ROLE_FREQUENCY_GUIDE",
    "VALHALLA_VINTAGE_VERB_PARAMS",
    "DeviceParameterSupervisor",
    "TrackFXRack",
]
