# engine/sound_design/resynthesis_engine.py
"""
Resynthesis Engine & Destruction Pass (Gen 2):
1. CandidateMomentDetector: Identifies singular, high-potential musical moments.
2. EnvelopeDecomposer: Deconstructs audio into 6 discrete components (Attack, Transient, Body, Harmonics, Noise, Tail).
3. DestructionPass: Generates 4 controlled physical variants (Clean, Degraded, Destroyed, Reconstructed).
4. NewInstrumentFabricator: Transmutes rendered audio into brand new autogenous instruments (Pads, Risers, Textures).
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import logging

from .sonic_dna import SonicDNA, MotifFingerprint

logger = logging.getLogger("ResynthesisEngine")


class ComponentBand(str, Enum):
    ATTACK = "ATTACK"          # 0 to 15 ms
    TRANSIENT = "TRANSIENT"    # 15 to 40 ms
    BODY = "BODY"              # 40 to 250 ms
    HARMONICS = "HARMONICS"    # High mid overtone partials
    NOISE = "NOISE"            # Acoustic air and breath
    TAIL = "TAIL"              # Reverb tail, release, or reverse swell


class DestructionBranch(str, Enum):
    CLEAN = "CLEAN"                    # Pristine original stem capture
    DEGRADED = "DEGRADED"              # Tape compression, 12-bit SP-1200 grit, warm wow & flutter
    DESTROYED = "DESTROYED"            # Spectral holes, heavy wavefolding, harsh clipping, dropouts
    RECONSTRUCTED = "RECONSTRUCTED"    # Clean transient grafted onto degraded body with spectral tail


@dataclass
class CandidateMoment:
    """A specific point in the arrangement identified as high potential for resynthesis."""
    moment_id: str
    track_name: str
    section: str
    bar_range: Tuple[int, int]
    musical_gesture_desc: str
    harmonic_root: str
    potential_instruments: List[str]  # e.g. ["Pads", "Risers", "Signature Ghost"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "moment_id": self.moment_id,
            "track_name": self.track_name,
            "section": self.section,
            "bar_range": list(self.bar_range),
            "musical_gesture_desc": self.musical_gesture_desc,
            "harmonic_root": self.harmonic_root,
            "potential_instruments": list(self.potential_instruments),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CandidateMoment:
        b_range = data.get("bar_range", [1, 8])
        return cls(
            moment_id=data.get("moment_id", "MOMENT_1"),
            track_name=data.get("track_name", "Keys"),
            section=data.get("section", "Hook 1"),
            bar_range=(int(b_range[0]), int(b_range[1])),
            musical_gesture_desc=data.get("musical_gesture_desc", ""),
            harmonic_root=data.get("harmonic_root", "Eb"),
            potential_instruments=data.get("potential_instruments", []),
        )


@dataclass
class DecomposedComponent:
    """An isolated component extracted from a candidate moment."""
    band: ComponentBand
    time_window_ms: Tuple[float, float]
    energy_ratio: float
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "band": self.band.value if isinstance(self.band, ComponentBand) else str(self.band),
            "time_window_ms": list(self.time_window_ms),
            "energy_ratio": round(self.energy_ratio, 2),
            "description": self.description,
        }


@dataclass
class DestructionVariant:
    """A distinct degradation state produced during the Destruction Pass."""
    branch: DestructionBranch
    drive_db: float
    bit_depth: Optional[int]
    frequency_cutoff_hz: Optional[float]
    time_stretch: float
    reverse: bool
    description: str
    device_chain: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch": self.branch.value if isinstance(self.branch, DestructionBranch) else str(self.branch),
            "drive_db": self.drive_db,
            "bit_depth": self.bit_depth,
            "frequency_cutoff_hz": self.frequency_cutoff_hz,
            "time_stretch": self.time_stretch,
            "reverse": self.reverse,
            "description": self.description,
            "device_chain": list(self.device_chain),
        }


@dataclass
class FabricatedInstrument:
    """A brand new instrument generated out of the song's own material."""
    instrument_id: str
    name: str
    target_category: str  # PAD, RISER, TEXTURE, PERCUSSION, SUB
    parent_moment: CandidateMoment
    active_branch: DestructionBranch
    recipe_summary: str
    placement_section: str
    placement_bars: Tuple[int, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "name": self.name,
            "target_category": self.target_category,
            "parent_moment": self.parent_moment.to_dict(),
            "active_branch": self.active_branch.value if isinstance(self.active_branch, DestructionBranch) else str(self.active_branch),
            "recipe_summary": self.recipe_summary,
            "placement_section": self.placement_section,
            "placement_bars": list(self.placement_bars),
        }


class ResynthesisEngine:
    """
    Orchestrates the entire candidate discovery -> envelope decomposition ->
    destruction pass -> new instrument fabrication pipeline.
    """

    @classmethod
    def locate_candidate_moments(cls, dna: SonicDNA) -> List[CandidateMoment]:
        """
        Discovers specific high-character musical moments using SonicDNA.
        """
        moments: List[CandidateMoment] = []

        for motif in dna.key_motifs:
            if motif.role == "keys":
                moments.append(CandidateMoment(
                    moment_id="MOMENT_HOOK1_RHODES_CHORD",
                    track_name=motif.track_name,
                    section="Hook 1",
                    bar_range=motif.bars,
                    musical_gesture_desc=f"Opening voicing ({motif.voicing_or_notes})",
                    harmonic_root=dna.harmonic.key,
                    potential_instruments=["Spectral Pad", "Reverse Shimmer", "Tape Relic Bed"]
                ))
            elif motif.role == "strings":
                moments.append(CandidateMoment(
                    moment_id="MOMENT_BRIDGE_STRING_CRESCENDO",
                    track_name=motif.track_name,
                    section="Bridge",
                    bar_range=motif.bars,
                    musical_gesture_desc="Sustained orchestral high-register swell",
                    harmonic_root=dna.harmonic.key,
                    potential_instruments=["Spectral Drone", "Granular Riser", "Vacuum Suction"]
                ))

        return moments

    @classmethod
    def decompose_envelope(cls, moment: CandidateMoment) -> List[DecomposedComponent]:
        """
        Deconstructs the candidate moment into 6 distinct physical zones.
        """
        return [
            DecomposedComponent(ComponentBand.ATTACK, (0.0, 15.0), 0.25, "Initial key/hammer strike"),
            DecomposedComponent(ComponentBand.TRANSIENT, (15.0, 45.0), 0.35, "Tonal punch and snap"),
            DecomposedComponent(ComponentBand.BODY, (45.0, 280.0), 0.70, "Fundamental Neo-Soul chord sustain"),
            DecomposedComponent(ComponentBand.HARMONICS, (280.0, 800.0), 0.40, "Warm 9th and 13th upper partials"),
            DecomposedComponent(ComponentBand.NOISE, (0.0, 1200.0), 0.15, "Tine mechanical friction and air"),
            DecomposedComponent(ComponentBand.TAIL, (800.0, 2400.0), 0.30, "Reverb dispersion and room decay"),
        ]

    @classmethod
    def run_destruction_pass(cls, moment: CandidateMoment) -> List[DestructionVariant]:
        """
        Generates the 4 controlled branches: Clean, Degraded, Destroyed, Reconstructed.
        """
        return [
            DestructionVariant(
                branch=DestructionBranch.CLEAN,
                drive_db=0.0,
                bit_depth=None,
                frequency_cutoff_hz=None,
                time_stretch=1.0,
                reverse=False,
                description="Pristine reference capture of original chord.",
                device_chain=["Utility (Unity Gain)"]
            ),
            DestructionVariant(
                branch=DestructionBranch.DEGRADED,
                drive_db=4.5,
                bit_depth=12,
                frequency_cutoff_hz=6800.0,
                time_stretch=1.0,
                reverse=False,
                description="Vintage SP-1200 12-bit resample with tape saturation and 0.75 Hz wow.",
                device_chain=["Saturator (Drive +4.5dB)", "Redux (Bit Depth 12)", "EQ Eight (High Cut 6.8 kHz)"]
            ),
            DestructionVariant(
                branch=DestructionBranch.DESTROYED,
                drive_db=14.0,
                bit_depth=8,
                frequency_cutoff_hz=3200.0,
                time_stretch=1.0,
                reverse=False,
                description="Extreme wavefolding distortion with harsh downsampling and narrow bandpass.",
                device_chain=["Saturator (Drive +14dB)", "Redux (Bit Depth 8)", "Auto Filter (Bandpass 1.5 kHz)"]
            ),
            DestructionVariant(
                branch=DestructionBranch.RECONSTRUCTED,
                drive_db=2.0,
                bit_depth=12,
                frequency_cutoff_hz=7200.0,
                time_stretch=4.0,
                reverse=True,
                description="Clean attack married to 12-bit saturated body and 400% reverse spectral shimmer tail.",
                device_chain=["EQ Eight (HPF @ 420 Hz)", "Echo (Shimmer)", "Reverb (Decay 8.5s)"]
            ),
        ]

    @classmethod
    def fabricate_new_instrument(
        cls,
        moment: CandidateMoment,
        category: str = "PAD",
        branch: DestructionBranch = DestructionBranch.RECONSTRUCTED,
        target_section: str = "Bridge",
        target_bars: Tuple[int, int] = (53, 60)
    ) -> FabricatedInstrument:
        """
        Transmutes the processed variant into a new named instrument for the arrangement.
        """
        inst_id = f"FAB_{category}_{moment.track_name.upper().replace(' ', '_')}"
        name = f"Autogenous {category.title()} ({moment.track_name})"

        return FabricatedInstrument(
            instrument_id=inst_id,
            name=name,
            target_category=category,
            parent_moment=moment,
            active_branch=branch,
            recipe_summary=f"Derived from {moment.musical_gesture_desc} via {branch.value} pass.",
            placement_section=target_section,
            placement_bars=target_bars,
        )
