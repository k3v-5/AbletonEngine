# engine/performance/models.py
"""
Performance & Humanization Models (Nivel T):
Defines the expressive contracts, profiles, intent, snapshots, and mutations
for music-theoretically intentional performance modeling.

Key Tenet:
"Menos cuantización != más humano."
Human performance is governed by intention, mechanical consistency,
structural hierarchy, and collective correlated relationships across instruments.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple


class PocketTendency(str, Enum):
    """Macro temporal pocket posture."""
    ON_THE_GRID = "ON_THE_GRID"           # Tight, quantized anchor with zero lazy drift
    LAID_BACK = "LAID_BACK"               # Dragging slightly behind pulse (+8 to +16 ms)
    DRIVING_PUSH = "DRIVING_PUSH"         # Pushing ahead of pulse (-3 to -8 ms)
    LOOSE_DRAG = "LOOSE_DRAG"             # Relaxed Dilla/soul swing with dynamic lag
    TIGHT_POCKET = "TIGHT_POCKET"         # Strict MPC groove pocket with minimal jitter


class VelocityProfile(str, Enum):
    """Dynamic touch and velocity contour philosophy."""
    EXPRESSIVE = "EXPRESSIVE"             # Full dynamic range with emotional phrasing
    TIERED_PULSE = "TIERED_PULSE"         # Metric accenting (downbeats heavy, offbeats lighter)
    FLAT_BED = "FLAT_BED"                 # Narrow velocity envelope for steady pads / synth beds
    SUBTLE_DYNAMIC = "SUBTLE_DYNAMIC"     # Gentle micro-touch variations (+/- 4 to 8 vel)
    RUBATO_BREATHING = "RUBATO_BREATHING" # Dynamic swell correlated with tempo rubato


class ArticulationStyle(str, Enum):
    """Physical note duration and articulation posture."""
    NATURAL_BREATHING = "NATURAL_BREATHING" # Notes breathe naturally with phrase release gaps
    TIGHT_STACCATO = "TIGHT_STACCATO"       # Short crisp releases (50-70% of nominal length)
    LEGATO_SLURRED = "LEGATO_SLURRED"       # Notes overlap or connect seamlessly
    STRUMMED_POLY = "STRUMMED_POLY"         # Chords are articulated with micro-time spreads
    GHOSTED = "GHOSTED"                     # High prevalence of soft touch ghost notes


@dataclass
class PerformanceIntent:
    """
    Artistic declaration of who is performing and their expressive posture.
    Decided BEFORE touching any note.
    """
    intent_id: str = field(default_factory=lambda: f"intent_{uuid.uuid4().hex[:8]}")
    name: str = "Expressive Pocket"
    pocket: PocketTendency = PocketTendency.LAID_BACK
    timing_variance_ms: float = 6.0          # Base standard deviation in ms
    velocity_profile: VelocityProfile = VelocityProfile.EXPRESSIVE
    articulation: ArticulationStyle = ArticulationStyle.NATURAL_BREATHING
    ghost_note_probability: float = 0.15     # Chance of ghost note insertion on weak subdivisions
    phrase_push: float = 0.2                 # Positive = push climax, Negative = drag climax
    human_factor: float = 0.7                # Overall scale (0.0 = mechanical, 1.0 = full human)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "name": self.name,
            "pocket": self.pocket.value,
            "timing_variance_ms": round(self.timing_variance_ms, 2),
            "velocity_profile": self.velocity_profile.value,
            "articulation": self.articulation.value,
            "ghost_note_probability": round(self.ghost_note_probability, 3),
            "phrase_push": round(self.phrase_push, 2),
            "human_factor": round(self.human_factor, 2),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PerformanceIntent:
        return cls(
            intent_id=data.get("intent_id", f"intent_{uuid.uuid4().hex[:8]}"),
            name=data.get("name", "Expressive Pocket"),
            pocket=PocketTendency(data.get("pocket", PocketTendency.LAID_BACK.value)),
            timing_variance_ms=float(data.get("timing_variance_ms", 6.0)),
            velocity_profile=VelocityProfile(data.get("velocity_profile", VelocityProfile.EXPRESSIVE.value)),
            articulation=ArticulationStyle(data.get("articulation", ArticulationStyle.NATURAL_BREATHING.value)),
            ghost_note_probability=float(data.get("ghost_note_probability", 0.15)),
            phrase_push=float(data.get("phrase_push", 0.2)),
            human_factor=float(data.get("human_factor", 0.7)),
        )


@dataclass
class InstrumentPerformanceProfile:
    """
    Physical and acoustic behavior model for a specific musical role.
    Prevents applying identical Gaussian jitter to every instrument.
    """
    role: str                                # e.g. "kick", "snare", "hihat", "bass", "keys", "lead"
    timing_variance_ms: float = 4.0          # Role-specific timing variance ceiling
    velocity_variance: float = 10.0          # Role-specific velocity standard deviation
    is_groove_anchor: bool = False           # If True, other instruments anchor their timing to this
    coupled_anchor_role: Optional[str] = None# Role this instrument tracks (e.g. Bass -> Kick)
    anchor_coupling_offset_ms: float = 0.0   # Relative lag/advance from anchor (e.g. +2.0 ms)
    laid_back_tendency_ms: float = 0.0       # Snare/clap drag tendency in ms
    strum_spread_ms: float = 0.0             # Polyphonic spread for chords (Keys/Guitar)
    strum_top_note_accent: int = 0           # Velocity boost for uppermost melody note
    phrase_breathing_enabled: bool = False   # Whether to apply phrase detection and breath gaps
    min_breath_gap_ms: float = 35.0          # Guaranteed silence after phrase end
    ghost_note_velocity_range: Tuple[int, int] = (25, 45)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "timing_variance_ms": round(self.timing_variance_ms, 2),
            "velocity_variance": round(self.velocity_variance, 2),
            "is_groove_anchor": self.is_groove_anchor,
            "coupled_anchor_role": self.coupled_anchor_role,
            "anchor_coupling_offset_ms": round(self.anchor_coupling_offset_ms, 2),
            "laid_back_tendency_ms": round(self.laid_back_tendency_ms, 2),
            "strum_spread_ms": round(self.strum_spread_ms, 2),
            "strum_top_note_accent": self.strum_top_note_accent,
            "phrase_breathing_enabled": self.phrase_breathing_enabled,
            "min_breath_gap_ms": round(self.min_breath_gap_ms, 2),
            "ghost_note_velocity_range": list(self.ghost_note_velocity_range),
        }

    @classmethod
    def create_default(cls, role: str) -> InstrumentPerformanceProfile:
        """Factory for canonical musical instrument roles."""
        r = role.lower().strip()
        if r in ["kick", "bd", "bass_drum"]:
            return cls(
                role="kick",
                timing_variance_ms=1.2,
                velocity_variance=4.0,
                is_groove_anchor=True,
                coupled_anchor_role=None,
                anchor_coupling_offset_ms=0.0,
                laid_back_tendency_ms=0.0,
                phrase_breathing_enabled=False,
            )
        elif r in ["snare", "sd", "clap", "rim"]:
            return cls(
                role="snare",
                timing_variance_ms=5.0,
                velocity_variance=14.0,
                is_groove_anchor=False,
                coupled_anchor_role="kick",
                anchor_coupling_offset_ms=10.0,   # Laid back relative to kick
                laid_back_tendency_ms=10.0,
                phrase_breathing_enabled=False,
            )
        elif r in ["hihat", "hh", "hat", "hats", "shaker"]:
            return cls(
                role="hihat",
                timing_variance_ms=8.0,
                velocity_variance=18.0,
                is_groove_anchor=False,
                coupled_anchor_role="snare",
                anchor_coupling_offset_ms=-4.0,   # Push slightly before snare
                laid_back_tendency_ms=0.0,
                phrase_breathing_enabled=False,
            )
        elif r in ["bass", "808", "sub", "synth_bass"]:
            return cls(
                role="bass",
                timing_variance_ms=2.0,
                velocity_variance=6.0,
                is_groove_anchor=False,
                coupled_anchor_role="kick",
                anchor_coupling_offset_ms=1.5,    # Coupled tightly behind kick (+1.5 ms)
                laid_back_tendency_ms=0.0,
                phrase_breathing_enabled=True,
                min_breath_gap_ms=25.0,
            )
        elif r in ["keys", "piano", "rhodes", "guitar", "chords"]:
            return cls(
                role="keys",
                timing_variance_ms=6.0,
                velocity_variance=16.0,
                is_groove_anchor=False,
                coupled_anchor_role=None,
                strum_spread_ms=14.0,             # Micro-strum between notes of chord
                strum_top_note_accent=12,         # Top note voiced louder
                phrase_breathing_enabled=True,
                min_breath_gap_ms=40.0,
            )
        elif r in ["lead", "vocal", "melody", "solo", "sax"]:
            return cls(
                role="lead",
                timing_variance_ms=7.0,
                velocity_variance=20.0,
                is_groove_anchor=False,
                coupled_anchor_role=None,
                phrase_breathing_enabled=True,
                min_breath_gap_ms=50.0,
            )
        elif r in ["pad", "strings", "ambient"]:
            return cls(
                role="pad",
                timing_variance_ms=3.0,
                velocity_variance=4.0,
                is_groove_anchor=False,
                strum_spread_ms=20.0,
                phrase_breathing_enabled=False,
            )
        else:
            return cls(role=r)


@dataclass
class PerformanceSnapshot:
    """
    Immutable state capture of notes before performance intervention.
    Enables instant atomic rollback (0 ms) if contextual critique degrades.
    """
    snapshot_id: str = field(default_factory=lambda: f"perf_snap_{uuid.uuid4().hex[:8]}")
    tracks_notes: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    state_fingerprint: str = ""
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.state_fingerprint:
            self.state_fingerprint = self.compute_fingerprint()

    def compute_fingerprint(self) -> str:
        serialized = json.dumps(self.tracks_notes, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "state_fingerprint": self.state_fingerprint,
            "tracks_count": len(self.tracks_notes),
            "total_notes": sum(len(notes) for notes in self.tracks_notes.values()),
        }


@dataclass
class PerformanceMutation:
    """
    Audit ledger entry capturing exact performance deltas applied to an instrument.
    """
    track_name: str
    role: str
    timing_offset_mean_ms: float
    timing_offset_std_ms: float
    velocity_delta_mean: float
    velocity_std: float
    articulation_shift: str
    strum_applied_ms: float = 0.0
    breath_gaps_injected: int = 0
    delta_q_achieved: float = 0.0
    verdict: str = "PENDING"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_name": self.track_name,
            "role": self.role,
            "timing_offset_mean_ms": round(self.timing_offset_mean_ms, 2),
            "timing_offset_std_ms": round(self.timing_offset_std_ms, 2),
            "velocity_delta_mean": round(self.velocity_delta_mean, 2),
            "velocity_std": round(self.velocity_std, 2),
            "articulation_shift": self.articulation_shift,
            "strum_applied_ms": round(self.strum_applied_ms, 2),
            "breath_gaps_injected": self.breath_gaps_injected,
            "delta_q_achieved": round(self.delta_q_achieved, 4),
            "verdict": self.verdict,
        }
