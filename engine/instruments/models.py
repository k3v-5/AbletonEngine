# engine/instruments/models.py
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from .roles import InstrumentRole

class InstrumentSource(str, Enum):
    SAMPLE = "sample"
    SIMPLER = "simpler"
    DRUM_RACK = "drum_rack"
    INSTRUMENT = "instrument"
    PRESET = "preset"
    EXTERNAL_PLUGIN = "external_plugin"

@dataclass
class InstrumentDescriptor:
    role: InstrumentRole
    sound_profile: str
    source: InstrumentSource
    uri: Optional[str] = None
    file_path: Optional[str] = None
    device_name: str = ""
    parameters: Dict[str, float] = field(default_factory=dict)
    warning: Optional[str] = None
    is_fallback: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role.value if isinstance(self.role, InstrumentRole) else str(self.role),
            "sound_profile": self.sound_profile,
            "source": self.source.value if isinstance(self.source, InstrumentSource) else str(self.source),
            "uri": self.uri,
            "file_path": self.file_path,
            "device_name": self.device_name,
            "parameters": self.parameters,
            "warning": self.warning,
            "is_fallback": self.is_fallback
        }

@dataclass
class PadAssignment:
    pad: int                          # MIDI pitch (e.g. 36 for C1)
    role: InstrumentRole
    sample: str                       # Resolved file path or URI
    sound_profile: str
    seed: int = 2026
    pad_name: str = ""
    confidence: float = 1.0
    is_fallback: bool = False
    warning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pad": self.pad,
            "role": self.role.value if isinstance(self.role, InstrumentRole) else str(self.role),
            "sample": self.sample,
            "sound_profile": self.sound_profile,
            "seed": self.seed,
            "pad_name": self.pad_name,
            "confidence": round(self.confidence, 3),
            "is_fallback": self.is_fallback,
            "warning": self.warning
        }

@dataclass
class InstrumentExecutionPlan:
    track_name: str
    track_id: str
    device_name: str
    action: str                       # 'create_and_populate', 'populate_existing', 'preview_only'
    operations: List[Dict[str, Any]] = field(default_factory=list)
    assignments: List[PadAssignment] = field(default_factory=list)
    preview: bool = False
    status: str = "READY"
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_name": self.track_name,
            "track_id": self.track_id,
            "device_name": self.device_name,
            "action": self.action,
            "operations_count": len(self.operations),
            "operations": self.operations,
            "assignments": [a.to_dict() for a in self.assignments],
            "preview": self.preview,
            "status": self.status,
            "warnings": self.warnings
        }

@dataclass
class RackInspectionReport:
    rack_exists: bool
    track_index: int
    track_name: str
    device_index: int = 0
    pads: int = 16
    populated: int = 0
    empty: int = 16
    status: str = "EMPTY"             # 'EMPTY', 'PARTIAL', 'POPULATED'
    active_pads: List[Dict[str, Any]] = field(default_factory=list)
    missing_roles: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rack_exists": self.rack_exists,
            "track_index": self.track_index,
            "track_name": self.track_name,
            "device_index": self.device_index,
            "pads": self.pads,
            "populated": self.populated,
            "empty": self.empty,
            "status": self.status,
            "active_pads": self.active_pads,
            "missing_roles": self.missing_roles
        }
