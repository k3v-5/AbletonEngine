# engine/sound_design/frankenstein_engine.py
"""
Frankenstein Engine (Family 6):
Constructs unrepeatable hybrid instruments by grafting specific acoustic components
(Transient, Body, Sub, Texture, Tail) from multiple separate tracks in the project.
"""
from __future__ import annotations
import uuid
import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("FrankensteinEngine")


class ComponentRole(str, Enum):
    """The functional role of an extracted component within the composite sound."""
    TRANSIENT = "TRANSIENT"      # Initial strike / snap / crack
    BODY = "BODY"                # Fundamental tonal impact & mid punch
    LOW_BODY = "LOW_BODY"        # Low-mid acoustic foundation (120-250 Hz)
    SUB = "SUB"                  # Pure low-frequency anchor (30-80 Hz)
    TEXTURE = "TEXTURE"          # Noise, dust, or organic timbral layer
    TAIL = "TAIL"                # Reverb release, reverse swell, or resonance


@dataclass
class FrankensteinLayer:
    """A discrete slice borrowed from a project stem to form part of a hybrid entity."""
    source_track_name: str
    source_element_desc: str
    component_role: ComponentRole
    time_offset_ms: float = 0.0
    gain_db: float = 0.0
    highpass_hz: Optional[float] = None
    lowpass_hz: Optional[float] = None
    pan: float = 0.0  # -1.0 (L) to +1.0 (R)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_track_name": self.source_track_name,
            "source_element_desc": self.source_element_desc,
            "component_role": self.component_role.value if isinstance(self.component_role, ComponentRole) else str(self.component_role),
            "time_offset_ms": round(self.time_offset_ms, 1),
            "gain_db": round(self.gain_db, 1),
            "highpass_hz": round(self.highpass_hz, 1) if self.highpass_hz else None,
            "lowpass_hz": round(self.lowpass_hz, 1) if self.lowpass_hz else None,
            "pan": round(self.pan, 2),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FrankensteinLayer:
        role_str = data.get("component_role", "BODY")
        try:
            role = ComponentRole(role_str)
        except ValueError:
            role = ComponentRole.BODY
        return cls(
            source_track_name=data.get("source_track_name", "Unknown"),
            source_element_desc=data.get("source_element_desc", ""),
            component_role=role,
            time_offset_ms=float(data.get("time_offset_ms", 0.0)),
            gain_db=float(data.get("gain_db", 0.0)),
            highpass_hz=float(data["highpass_hz"]) if data.get("highpass_hz") is not None else None,
            lowpass_hz=float(data["lowpass_hz"]) if data.get("lowpass_hz") is not None else None,
            pan=float(data.get("pan", 0.0)),
        )


@dataclass
class FrankensteinComposite:
    """A fully assembled hybrid composite instrument."""
    id: str
    name: str
    target_category: str  # e.g. "DRUM", "BASS", "LEAD"
    layers: List[FrankensteinLayer] = field(default_factory=list)
    glue_processing_chain: List[str] = field(default_factory=list)
    narrative_thesis: str = ""
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "target_category": self.target_category,
            "layers": [l.to_dict() for l in self.layers],
            "glue_processing_chain": list(self.glue_processing_chain),
            "narrative_thesis": self.narrative_thesis,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FrankensteinComposite:
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", "Hybrid Composite"),
            target_category=data.get("target_category", "MISC"),
            layers=[FrankensteinLayer.from_dict(l) for l in data.get("layers", [])],
            glue_processing_chain=data.get("glue_processing_chain", []),
            narrative_thesis=data.get("narrative_thesis", ""),
            created_at=data.get("created_at", ""),
        )


class FrankensteinEngine:
    """
    Factory for designing multi-source Frankenstein composite instruments.
    """

    @classmethod
    def assemble_hybrid_snare(
        cls,
        clap_track: str = "Boom Bap Kit",
        snare_track: str = "Acoustic Snare",
        tom_track: str = "Percussion",
        texture_track: str = "Ambient Foley",
        tail_resample_track: str = "Stage-73 Rhodes"
    ) -> FrankensteinComposite:
        """
        Builds the classic Frankenstein Snare:
        - Transient: Crisp clap snap (HPF @ 1.2 kHz)
        - Body: Acoustic snare crack (200 Hz fundamental)
        - Low-Body: Floor tom thud (120-180 Hz)
        - Texture: Vinyl/tape noise floor
        - Tail: Micro-reversed piano decay (HPF @ 800 Hz)
        """
        layers = [
            FrankensteinLayer(
                source_track_name=clap_track,
                source_element_desc="Clap initial snap",
                component_role=ComponentRole.TRANSIENT,
                time_offset_ms=-2.0,  # 2ms flam pre-transient for width
                gain_db=-1.5,
                highpass_hz=1200.0,
                pan=-0.15
            ),
            FrankensteinLayer(
                source_track_name=snare_track,
                source_element_desc="Center acoustic snare punch",
                component_role=ComponentRole.BODY,
                time_offset_ms=0.0,
                gain_db=0.0,
                highpass_hz=160.0,
                lowpass_hz=8500.0,
                pan=0.0
            ),
            FrankensteinLayer(
                source_track_name=tom_track,
                source_element_desc="Low-mid wooden thud",
                component_role=ComponentRole.LOW_BODY,
                time_offset_ms=3.0,
                gain_db=-4.0,
                highpass_hz=100.0,
                lowpass_hz=350.0,
                pan=0.0
            ),
            FrankensteinLayer(
                source_track_name=texture_track,
                source_element_desc="Ambient vinyl room dust",
                component_role=ComponentRole.TEXTURE,
                time_offset_ms=0.0,
                gain_db=-14.0,
                highpass_hz=500.0,
                pan=0.25
            ),
            FrankensteinLayer(
                source_track_name=tail_resample_track,
                source_element_desc="Reversed Rhodes harmonic tail",
                component_role=ComponentRole.TAIL,
                time_offset_ms=45.0,
                gain_db=-8.0,
                highpass_hz=800.0,
                pan=0.35
            ),
        ]

        glue_chain = [
            "Glue Compressor (Attack: 30ms, Release: Auto, Threshold: -16 dB, Makeup: +2.5 dB)",
            "Saturator (Soft Sine, Drive: +1.8 dB for composite cohesion)",
            "EQ Eight (High Shelf @ 10 kHz: +1.5 dB, Low Cut @ 90 Hz: 48dB/oct)"
        ]

        return FrankensteinComposite(
            id="FRANK_SNARE_HYBRID",
            name="Frankenstein Signature Snare",
            target_category="DRUM",
            layers=layers,
            glue_processing_chain=glue_chain,
            narrative_thesis="Unique organic snare forged from clap, acoustic punch, tom weight, and reversed Rhodes dust."
        )

    @classmethod
    def assemble_hybrid_bass(
        cls,
        pluck_track: str = "Acoustic / Electric Pick",
        sub_track: str = "SubLab XL (808 Sub)",
        harmonic_resample_track: str = "Stage-73 Keys"
    ) -> FrankensteinComposite:
        """
        Builds a Frankenstein Bass:
        - Attack: Plucked transient click (HPF @ 800 Hz)
        - Sub: Pristine sine wave sub-bass (LPF @ 90 Hz mono)
        - Body/Texture: Saturated midrange harmonics derived from Rhodes chords
        """
        layers = [
            FrankensteinLayer(
                source_track_name=pluck_track,
                source_element_desc="Attack pick transient",
                component_role=ComponentRole.TRANSIENT,
                time_offset_ms=0.0,
                gain_db=-2.0,
                highpass_hz=750.0,
                pan=0.0
            ),
            FrankensteinLayer(
                source_track_name=sub_track,
                source_element_desc="Pure 808 sub fundamental (40-75 Hz)",
                component_role=ComponentRole.SUB,
                time_offset_ms=5.0,
                gain_db=0.0,
                lowpass_hz=85.0,
                pan=0.0
            ),
            FrankensteinLayer(
                source_track_name=harmonic_resample_track,
                source_element_desc="Overdriven mid-bass texture",
                component_role=ComponentRole.BODY,
                time_offset_ms=2.0,
                gain_db=-5.5,
                highpass_hz=140.0,
                lowpass_hz=1200.0,
                pan=0.0
            ),
        ]

        glue_chain = [
            "Utility (Bass Mono @ 110 Hz)",
            "Saturator (Analog Clip, Drive: +2.5 dB)",
            "Glue Compressor (Fast Peak Limiting)"
        ]

        return FrankensteinComposite(
            id="FRANK_BASS_HYBRID",
            name="Frankenstein Dual-Character Bass",
            target_category="BASS",
            layers=layers,
            glue_processing_chain=glue_chain,
            narrative_thesis="Punchy acoustic attack locked with subterranean 808 sine wave and saturated mid bite."
        )
