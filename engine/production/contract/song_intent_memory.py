# engine/production/contract/song_intent_memory.py
"""
Song Intent Memory:
Maintains the artistic and sonic continuity of the specific song throughout all phases of production.
Tracks emotional axis, sonic thesis, identity anchors, forbidden drift patterns, evolution targets,
and unresolved creative questions.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("SongIntentMemory")


@dataclass
class EmotionalAxis:
    """Progression of emotional energy and character across narrative sections."""
    start: str = "intimate"
    middle: str = "uneasy"
    peak: str = "expansive"
    ending: str = "unresolved"
    custom_mappings: Dict[str, str] = field(default_factory=dict)

    def get_for_section(self, section_name: str) -> str:
        s_lower = str(section_name).lower()
        if s_lower in self.custom_mappings:
            return self.custom_mappings[s_lower]
        if any(w in s_lower for w in ["intro", "verse 1", "verso 1"]):
            return self.start
        if any(w in s_lower for w in ["bridge", "puente", "verse 2", "break"]):
            return self.middle
        if any(w in s_lower for w in ["climax", "drop", "hook 2", "hook 3"]):
            return self.peak
        if any(w in s_lower for w in ["outro", "final"]):
            return self.ending
        return "balanced"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start,
            "middle": self.middle,
            "peak": self.peak,
            "ending": self.ending,
            "custom_mappings": self.custom_mappings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EmotionalAxis:
        return cls(
            start=data.get("start", "intimate"),
            middle=data.get("middle", "uneasy"),
            peak=data.get("peak", "expansive"),
            ending=data.get("ending", "unresolved"),
            custom_mappings=data.get("custom_mappings", {})
        )


@dataclass
class SonicThesis:
    """The central artistic statement of the piece."""
    statement: str = "warm harmony against degraded texture"
    genre: str = "rap/neo-soul"
    reference_artist: str = "Tyler, The Creator"
    bpm: float = 90.0
    key: str = "F#"
    scale: str = "minor"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "statement": self.statement,
            "genre": self.genre,
            "reference_artist": self.reference_artist,
            "bpm": self.bpm,
            "key": self.key,
            "scale": self.scale,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SonicThesis:
        return cls(
            statement=data.get("statement", "warm harmony against degraded texture"),
            genre=data.get("genre", "rap/neo-soul"),
            reference_artist=data.get("reference_artist", "Tyler, The Creator"),
            bpm=float(data.get("bpm", 90.0)),
            key=data.get("key", "F#"),
            scale=data.get("scale", "minor")
        )


@dataclass
class SongIntentMemory:
    """
    Living artistic memory of the song currently being produced.
    Ensures that technical execution remains loyal to the original creative premise.
    """
    thesis: SonicThesis = field(default_factory=SonicThesis)
    emotional_axis: EmotionalAxis = field(default_factory=EmotionalAxis)
    identity_anchors: List[str] = field(default_factory=lambda: [
        "F# harmonic center (Neo-Soul modal chords)",
        "humanized unquantized pocket (boom-bap swing)",
        "dry/intimate vocal with analog character",
        "degraded dust/vinyl texture baseline",
        "warm analog bass contrasting aggressive sub-slides"
    ])
    forbidden_drift: List[str] = field(default_factory=lambda: [
        "generic EDM build or riser clichés",
        "100% mechanical quantization",
        "overly clean or sterilized drum transients",
        "pop 4-chord loop without harmonic extensions",
        "static repetitions across recurring hooks"
    ])
    evolution_targets: List[Dict[str, Any]] = field(default_factory=lambda: [
        {
            "id": "HOOK_EVOLUTION",
            "source": "Hook 1",
            "target": "Hook 3",
            "dimension": "harmonic_and_melodic_density",
            "expected": "Final hook must contain variation in voicings or counter-melody"
        },
        {
            "id": "BASS_DYNAMICS",
            "source": "Verse 1",
            "target": "Bridge",
            "dimension": "sub_presence",
            "expected": "Bridge must strip down or alter bass presence for tension"
        }
    ])
    unresolved_questions: List[str] = field(default_factory=lambda: [
        "Vocal climax placement in final chorus",
        "Texture foley fadeout treatment in outro"
    ])

    def check_forbidden_drift(self, description_or_intent: str) -> List[str]:
        """Detects if a planned action violates forbidden aesthetic drift."""
        desc_l = str(description_or_intent).lower()
        warnings = []
        drift_keywords = {
            "generic EDM build or riser clichés": ["white noise riser", "snare roll build", "edm build", "uplifter 16 bars"],
            "100% mechanical quantization": ["quantize 100", "cuantizar 100%", "perfect grid", "robotic snap"],
            "overly clean or sterilized drum transients": ["clinical punch", "ultra clean sterile", "hyper polished edm"],
            "pop 4-chord loop without harmonic extensions": ["four chords", "i-v-vi-iv", "pop loop", "progression simple"],
        }
        for drift_rule, keywords in drift_keywords.items():
            if any(k in desc_l for k in keywords):
                warnings.append(f"Forbidden Drift Detected: '{drift_rule}' matching context: '{description_or_intent}'")
        return warnings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "thesis": self.thesis.to_dict(),
            "emotional_axis": self.emotional_axis.to_dict(),
            "identity_anchors": list(self.identity_anchors),
            "forbidden_drift": list(self.forbidden_drift),
            "evolution_targets": list(self.evolution_targets),
            "unresolved_questions": list(self.unresolved_questions),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SongIntentMemory:
        if not data or not isinstance(data, dict):
            return cls()
        return cls(
            thesis=SonicThesis.from_dict(data.get("thesis", {})),
            emotional_axis=EmotionalAxis.from_dict(data.get("emotional_axis", {})),
            identity_anchors=list(data.get("identity_anchors", [])),
            forbidden_drift=list(data.get("forbidden_drift", [])),
            evolution_targets=list(data.get("evolution_targets", [])),
            unresolved_questions=list(data.get("unresolved_questions", []))
        )

    @classmethod
    def create_for_style(
        cls,
        genre: str = "rap/neo-soul",
        artist: str = "Tyler, The Creator",
        key: str = "F#",
        scale: str = "minor",
        bpm: float = 90.0
    ) -> SongIntentMemory:
        """Factory generating authentic intent defaults customized for a specific artist/genre."""
        thesis_stmt = f"Warm raw neo-soul harmonic depth balanced by grimy analog texture and dynamic sub-bass"
        anchors = [
            f"{key} {scale} harmonic center with extended 7th/9th jazz voicings",
            "Unquantized humanized boom-bap pocket with micro-timing lag",
            "Analog synth warmth and physical foley vinyl dust",
            "Dry, up-front vocal staging with controlled saturation and dynamic ducking"
        ]
        forbidden = [
            "Generic EDM build or snare roll buildups",
            "Sterile 100% grid quantization",
            "Static, unvarying hook repetitions without textural/melodic evolution",
            "Unconfigured factory init synth presets"
        ]
        evols = [
            {
                "id": "HOOK_EVOLUTION",
                "source": "Hook 1",
                "target": "Hook 3",
                "dimension": "harmonic_expansion",
                "expected": "Hook 3 must present added layers, topline counterpoint or octave lift"
            },
            {
                "id": "BRIDGE_VACUUM",
                "source": "Verse 2",
                "target": "Bridge",
                "dimension": "acoustic_contrast",
                "expected": "Bridge must contrast rhythmically and strip low-end to create tension before drop"
            }
        ]
        return cls(
            thesis=SonicThesis(
                statement=thesis_stmt,
                genre=genre,
                reference_artist=artist,
                bpm=bpm,
                key=key,
                scale=scale
            ),
            emotional_axis=EmotionalAxis(
                start="intimate and introspective",
                middle="tense and uneasy",
                peak="expansive and soulful",
                ending="warm, lingering unresolved"
            ),
            identity_anchors=anchors,
            forbidden_drift=forbidden,
            evolution_targets=evols,
            unresolved_questions=[
                "Final chorus vocal energy development",
                "Vinyl dust tail behavior during final fadeout"
            ]
        )
