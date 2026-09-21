# engine/sound_design/frankenstein_v2.py
"""
Frankenstein 2.0 (Autogenous Hybrid Construction):
Enforces strict autogeny: constructs brand new drums, basses, and lead textures
strictly from the 6 deconstructed components (Attack, Transient, Body, Harmonics,
Noise, Tail) of the song's own existing tracks.

A Frankenstein 2.0 instrument cannot exist in any other song because its DNA
is 100% forged from the unique audio material of this specific production.
"""
from __future__ import annotations
import uuid
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import logging

from .resynthesis_engine import ComponentBand

logger = logging.getLogger("FrankensteinV2")


@dataclass
class AutogenousComponentSource:
    """A physical component harvested from a track currently in the project."""
    source_track_name: str
    band: ComponentBand
    time_window_ms: Tuple[float, float]
    gain_trim_db: float
    filter_range_hz: Tuple[Optional[float], Optional[float]]
    pan: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_track_name": self.source_track_name,
            "band": self.band.value if isinstance(self.band, ComponentBand) else str(self.band),
            "time_window_ms": list(self.time_window_ms),
            "gain_trim_db": round(self.gain_trim_db, 1),
            "filter_range_hz": [
                round(self.filter_range_hz[0], 1) if self.filter_range_hz[0] else None,
                round(self.filter_range_hz[1], 1) if self.filter_range_hz[1] else None,
            ],
            "pan": round(self.pan, 2),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AutogenousComponentSource:
        b_str = data.get("band", "BODY")
        try:
            band = ComponentBand(b_str)
        except ValueError:
            band = ComponentBand.BODY
        f_range = data.get("filter_range_hz", [None, None])
        t_win = data.get("time_window_ms", [0.0, 50.0])
        return cls(
            source_track_name=data.get("source_track_name", "Unknown"),
            band=band,
            time_window_ms=(float(t_win[0]), float(t_win[1])),
            gain_trim_db=float(data.get("gain_trim_db", 0.0)),
            filter_range_hz=(
                float(f_range[0]) if f_range[0] is not None else None,
                float(f_range[1]) if f_range[1] is not None else None
            ),
            pan=float(data.get("pan", 0.0)),
        )


@dataclass
class FrankensteinV2Object:
    """A hybrid composite constructed exclusively from the project's autogenous components."""
    object_id: str
    name: str
    target_role: str  # SNARE, BASS, LEAD_LAYER, EAR_CANDY
    components: List[AutogenousComponentSource] = field(default_factory=list)
    glue_device_chain: List[str] = field(default_factory=list)
    uniqueness_hash: str = ""
    narrative_thesis: str = ""

    def validate_100_percent_autogenous(self, active_session_track_names: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Verifies that every single component comes from an existing track in the active session.
        """
        session_tracks_lower = [t.lower() for t in active_session_track_names]

        for comp in self.components:
            comp_src = comp.source_track_name.lower()
            if not any(st in comp_src or comp_src in st for st in session_tracks_lower):
                return False, (
                    f"Violación de autogenia: el componente '{comp.band.value}' proviene de "
                    f"'{comp.source_track_name}', que no existe en las pistas de la sesión."
                )
        return True, None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "object_id": self.object_id,
            "name": self.name,
            "target_role": self.target_role,
            "components": [c.to_dict() for c in self.components],
            "glue_device_chain": list(self.glue_device_chain),
            "uniqueness_hash": self.uniqueness_hash,
            "narrative_thesis": self.narrative_thesis,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FrankensteinV2Object:
        return cls(
            object_id=data.get("object_id", str(uuid.uuid4())[:8]),
            name=data.get("name", "Frankenstein Object"),
            target_role=data.get("target_role", "SNARE"),
            components=[AutogenousComponentSource.from_dict(c) for c in data.get("components", [])],
            glue_device_chain=data.get("glue_device_chain", []),
            uniqueness_hash=data.get("uniqueness_hash", ""),
            narrative_thesis=data.get("narrative_thesis", ""),
        )


class FrankensteinV2Engine:
    """
    Factory creating Frankenstein 2.0 autogenous composites.
    """

    @classmethod
    def craft_autogenous_snare(
        cls,
        clap_track: str = "808 Core Kit",
        snare_track: str = "Boom Bap Kit",
        foley_track: str = "Ableton Simpler",
        rhodes_track: str = "Stage-73 Rhodes",
        bass_track: str = "SubLab XL"
    ) -> FrankensteinV2Object:
        """
        Synthesizes a 100% autogenous Snare:
        - Attack: Clap snap from Track 1
        - Body: Acoustic snare crack from Track 2
        - Noise: Vinyl dust from Track 8
        - Harmonics: Upper mid bite from SubLab XL bass (Track 4)
        - Tail: Reverse harmonic resonance from Stage-73 Rhodes (Track 5)
        """
        components = [
            AutogenousComponentSource(clap_track, ComponentBand.ATTACK, (0.0, 15.0), -1.0, (1200.0, None), pan=-0.1),
            AutogenousComponentSource(snare_track, ComponentBand.BODY, (15.0, 120.0), 0.0, (160.0, 7500.0), pan=0.0),
            AutogenousComponentSource(foley_track, ComponentBand.NOISE, (0.0, 350.0), -16.0, (600.0, None), pan=0.2),
            AutogenousComponentSource(bass_track, ComponentBand.HARMONICS, (15.0, 80.0), -12.0, (400.0, 1800.0), pan=0.0),
            AutogenousComponentSource(rhodes_track, ComponentBand.TAIL, (60.0, 450.0), -8.5, (800.0, None), pan=0.3),
        ]

        raw_str = f"SNARE_{clap_track}_{snare_track}_{rhodes_track}_{bass_track}"
        u_hash = hashlib.sha256(raw_str.encode()).hexdigest()[:12]

        return FrankensteinV2Object(
            object_id=f"FRANK_V2_SNARE_{u_hash}",
            name="Autogenous Frankenstein Snare 2.0",
            target_role="SNARE",
            components=components,
            glue_device_chain=[
                "Glue Compressor (Attack 30ms, Release Auto, Threshold -18dB)",
                "Saturator (Soft Sine, Drive +2.0dB)",
                "EQ Eight (High Shelf @ 9.5 kHz: +1.5dB)"
            ],
            uniqueness_hash=u_hash,
            narrative_thesis="Forged out of the project's own clap snap, acoustic body, 808 mid harmonics, and reversed Rhodes decay."
        )

    @classmethod
    def craft_autogenous_bass(
        cls,
        sub_track: str = "SubLab XL",
        rhodes_track: str = "Stage-73 Rhodes",
        kick_track: str = "808 Core Kit"
    ) -> FrankensteinV2Object:
        """
        Synthesizes an autogenous Bass:
        - Attack: Kick transient click from Track 1
        - Body / Sub: Pristine 808 fundamental from SubLab XL
        - Harmonics: Saturated mid bite from Rhodes chords
        """
        components = [
            AutogenousComponentSource(kick_track, ComponentBand.ATTACK, (0.0, 12.0), -4.0, (1500.0, None), pan=0.0),
            AutogenousComponentSource(sub_track, ComponentBand.BODY, (12.0, 350.0), 0.0, (35.0, 90.0), pan=0.0),
            AutogenousComponentSource(rhodes_track, ComponentBand.HARMONICS, (15.0, 250.0), -7.0, (180.0, 950.0), pan=0.0),
        ]

        raw_str = f"BASS_{sub_track}_{rhodes_track}_{kick_track}"
        u_hash = hashlib.sha256(raw_str.encode()).hexdigest()[:12]

        return FrankensteinV2Object(
            object_id=f"FRANK_V2_BASS_{u_hash}",
            name="Autogenous Frankenstein Bass 2.0",
            target_role="BASS",
            components=components,
            glue_device_chain=[
                "Utility (Bass Mono @ 110 Hz)",
                "Saturator (Analog Clip, Drive +3.0dB)"
            ],
            uniqueness_hash=u_hash,
            narrative_thesis="Subterranean pure 808 sine anchored with kick transient snap and saturated Rhodes mid overtones."
        )
