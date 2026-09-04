"""
Device Chain Models:
Defines semantic device identifiers and parameterized device chains.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

# Universal semantic device tags
DEVICE_PRIMARY_INSTRUMENT = "DEVICE:PRIMARY_INSTRUMENT"
DEVICE_SATURATION = "DEVICE:SATURATION"
DEVICE_EQ = "DEVICE:EQ"
DEVICE_COMPRESSOR = "DEVICE:COMPRESSOR"
DEVICE_REVERB = "DEVICE:REVERB"
DEVICE_DELAY = "DEVICE:DELAY"
DEVICE_UTILITY = "DEVICE:UTILITY"
DEVICE_SIDECHAIN = "DEVICE:SIDECHAIN"
DEVICE_CHORUS = "DEVICE:CHORUS"
DEVICE_DRUM_BUSS = "DEVICE:DRUM_BUSS"

@dataclass
class SemanticDevice:
    identifier: str
    preferred_name: str
    preferred_uri: str
    fallback_name: Optional[str] = None
    fallback_uri: Optional[str] = None
    optional: bool = False
    parameters: Dict[str, float] = field(default_factory=dict)
    bypassed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identifier": self.identifier,
            "preferred_name": self.preferred_name,
            "preferred_uri": self.preferred_uri,
            "fallback_name": self.fallback_name,
            "optional": self.optional,
            "parameters": self.parameters,
            "bypassed": self.bypassed
        }

@dataclass
class DeviceChain:
    role: str
    name: str
    devices: List[SemanticDevice] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "name": self.name,
            "device_count": len(self.devices),
            "devices": [d.to_dict() for d in self.devices]
        }
