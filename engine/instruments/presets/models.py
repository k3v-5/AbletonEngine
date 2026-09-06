# engine/instruments/presets/models.py
"""
Data models for Universal VST Preset Indexer, Multi-Criteria Search Engine,
and Patch Decision System across all 3rd-party and native plugins.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional


class PresetCategory(str, Enum):
    # Instrument roles
    BASS = "BASS"
    SUB_BASS = "SUB_BASS"
    LEAD = "LEAD"
    PAD = "PAD"
    KEYS = "KEYS"
    PIANO = "PIANO"
    ORGAN = "ORGAN"
    PLUCK = "PLUCK"
    STRINGS = "STRINGS"
    BRASS = "BRASS"
    DRUMS = "DRUMS"
    VOCAL = "VOCAL"
    FX = "FX"
    
    # Effect roles
    EQ = "EQ"
    DYNAMICS = "DYNAMICS"
    COMPRESSOR = "COMPRESSOR"
    LIMITER = "LIMITER"
    SATURATION = "SATURATION"
    DISTORTION = "DISTORTION"
    REVERB = "REVERB"
    DELAY = "DELAY"
    MODULATION = "MODULATION"
    FILTER = "FILTER"
    CREATIVE_FX = "CREATIVE_FX"
    MASTERING = "MASTERING"
    OTHER = "OTHER"


@dataclass
class PresetRecord:
    """Represents an indexed preset from any vendor, file format, or internal database."""
    id: str
    name: str
    plugin_name: str
    vendor: str
    category: str
    subcategory: str = ""
    tags: List[str] = field(default_factory=list)
    file_path: Optional[str] = None
    format: str = "unknown"  # arturia_db, ffp, vital, fxp, nmsv, native_adv, algorithmic
    is_factory: bool = True
    author: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "plugin_name": self.plugin_name,
            "vendor": self.vendor,
            "category": self.category,
            "subcategory": self.subcategory,
            "tags": self.tags,
            "file_path": self.file_path,
            "format": self.format,
            "is_factory": self.is_factory,
            "author": self.author,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PresetRecord":
        return cls(
            id=data["id"],
            name=data["name"],
            plugin_name=data["plugin_name"],
            vendor=data["vendor"],
            category=data.get("category", "OTHER"),
            subcategory=data.get("subcategory", ""),
            tags=data.get("tags", []),
            file_path=data.get("file_path"),
            format=data.get("format", "unknown"),
            is_factory=data.get("is_factory", True),
            author=data.get("author", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SearchQuery:
    """Multi-criteria query for searching presets across all plugins."""
    query_text: Optional[str] = None
    plugin_filter: Optional[List[str]] = None
    vendor_filter: Optional[List[str]] = None
    category_filter: Optional[str] = None
    role_filter: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    max_results: int = 50


@dataclass
class SearchResult:
    """Individual search match with score and ranking rationale."""
    preset: PresetRecord
    relevance_score: float  # 0.0 to 1.0
    match_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preset": self.preset.to_dict(),
            "relevance_score": round(self.relevance_score, 3),
            "match_reasons": self.match_reasons,
        }


class DecisionAction(str, Enum):
    LOAD_EXISTING_PRESET = "LOAD_EXISTING_PRESET"
    SYNTHESIZE_PROCEDURAL_PATCH = "SYNTHESIZE_PROCEDURAL_PATCH"
    APPLY_SEMANTIC_MACROS = "APPLY_SEMANTIC_MACROS"
    FALLBACK_NATIVE = "FALLBACK_NATIVE"


@dataclass
class PatchDecision:
    """Final decision output for an instrument or effect role."""
    action: DecisionAction
    plugin_name: str
    vendor: str
    preset: Optional[PresetRecord] = None
    procedural_patch_path: Optional[str] = None
    macro_parameters: Dict[str, float] = field(default_factory=dict)
    confidence: float = 1.0
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.value,
            "plugin_name": self.plugin_name,
            "vendor": self.vendor,
            "preset": self.preset.to_dict() if self.preset else None,
            "procedural_patch_path": self.procedural_patch_path,
            "macro_parameters": self.macro_parameters,
            "confidence": round(self.confidence, 3),
            "rationale": self.rationale,
        }
