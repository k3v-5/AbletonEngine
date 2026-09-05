# engine/instruments/plugins/models.py
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field

class PluginSemanticRole(str, Enum):
    # Filter & Frequency
    CUTOFF = "cutoff"
    RESONANCE = "resonance"
    FILTER_TYPE = "filter_type"
    FILTER_ENV = "filter_env"
    
    # Dynamics & Tone
    DRIVE = "drive"
    DRY_WET = "dry_wet"
    VOLUME = "volume"
    PANNING = "panning"
    WIDTH = "width"
    COLOR = "color"
    FATNESS = "fatness"
    LIMITER_CEILING = "limiter_ceiling"
    THRESHOLD = "threshold"
    
    # Envelope (ADSR)
    ATTACK = "attack"
    DECAY = "decay"
    SUSTAIN = "sustain"
    RELEASE = "release"
    
    # Modulation & Time
    RATE = "rate"
    DEPTH = "depth"
    FEEDBACK = "feedback"
    TIME = "time"
    MORPH = "morph"
    GLIDE = "glide"
    
    # Performance & Macros
    MACRO_1 = "macro_1"
    MACRO_2 = "macro_2"
    MACRO_3 = "macro_3"
    MACRO_4 = "macro_4"
    MACRO_5 = "macro_5"
    MACRO_6 = "macro_6"
    MACRO_7 = "macro_7"
    MACRO_8 = "macro_8"
    EXPRESSION = "expression"
    DYNAMICS = "dynamics"


@dataclass
class ParameterSpec:
    name: str
    min_val: float = 0.0
    max_val: float = 1.0
    default_val: float = 0.5
    unit: str = ""
    curve: str = "linear"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "min_val": self.min_val,
            "max_val": self.max_val,
            "default_val": self.default_val,
            "unit": self.unit,
            "curve": self.curve
        }


@dataclass
class PluginProfile:
    plugin_name: str
    category: str = "synth"  # synth, effect, sampler, mastering
    is_native: bool = False
    aliases: List[str] = field(default_factory=list)
    parameter_mappings: Dict[PluginSemanticRole, str] = field(default_factory=dict)
    semantic_aliases: Dict[PluginSemanticRole, List[str]] = field(default_factory=dict)
    range_scalers: Dict[str, Tuple[float, float]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_name": self.plugin_name,
            "category": self.category,
            "is_native": self.is_native,
            "aliases": self.aliases,
            "parameter_mappings": {k.value if isinstance(k, PluginSemanticRole) else str(k): v for k, v in self.parameter_mappings.items()},
            "semantic_aliases": {k.value if isinstance(k, PluginSemanticRole) else str(k): v for k, v in self.semantic_aliases.items()},
            "range_scalers": self.range_scalers
        }


@dataclass
class NormalizedParameterResult:
    found: bool
    parameter_name: str = ""
    parameter_index: int = -1
    raw_value: float = 0.0
    normalized_value: float = 0.0
    min_value: float = 0.0
    max_value: float = 1.0
    role: Optional[PluginSemanticRole] = None
    confidence: float = 0.0
    source: str = "none"
    matched_alias: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "found": self.found,
            "parameter_name": self.parameter_name,
            "parameter_index": self.parameter_index,
            "raw_value": round(self.raw_value, 4),
            "normalized_value": round(self.normalized_value, 4),
            "min_value": self.min_value,
            "max_value": self.max_value,
            "role": self.role.value if isinstance(self.role, PluginSemanticRole) else (str(self.role) if self.role else None),
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "matched_alias": self.matched_alias,
            "error": self.error
        }
