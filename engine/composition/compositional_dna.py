# engine/composition/compositional_dna.py
"""
Compositional DNA & Identity System (Phase P):
Establishes an unrepeatable musical genetic identity for each song before generation.
Encapsulates:
- Primary theme motif & signature interval language
- Signature rhythmic clave / syncopated footprint
- Harmonic palette & allowed modal tensions
- Instrumentation rules & sectional density limits
- Emotional curve targets across the narrative arc
- Timbral palette & acoustic environment
- 1-2 Recurring signature gestures exclusive to this work
- Explicit Negative Constraints (what the AI is forbidden to do)
- Generative constraint validation
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Set
import copy
import logging

logger = logging.getLogger("CompositionalDNA")


class NegativeConstraint(str, Enum):
    """Specific artistic anti-patterns strictly forbidden for this piece."""
    NO_STRAIGHT_FOUR_FLOOR_HATS = "no_straight_four_floor_hats"
    NO_UNEXTENDED_MAJOR_TRIADS = "no_unextended_major_triads"
    NO_CRASH_ON_BEAT_1 = "no_crash_on_beat_1"
    NO_IDENTICAL_HOOK_REPETITION = "no_identical_hook_repetition"
    NO_DEFAULT_OCTAVE_DOUBLING = "no_default_octave_doubling"
    NO_STATIC_VELOCITIES = "no_static_velocities"
    NO_OVERLAPPING_LOW_END = "no_overlapping_low_end"


@dataclass
class MotifNote:
    pitch: int
    start_time: float
    duration: float
    velocity: int = 90

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pitch": self.pitch,
            "start_time": round(self.start_time, 4),
            "duration": round(self.duration, 4),
            "velocity": self.velocity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MotifNote:
        return cls(
            pitch=int(data.get("pitch", 60)),
            start_time=float(data.get("start_time", 0.0)),
            duration=float(data.get("duration", 0.25)),
            velocity=int(data.get("velocity", 90)),
        )


@dataclass
class PrimaryMotif:
    """Core melodic or thematic statement of the song."""
    name: str = "Core Motif"
    notes: List[MotifNote] = field(default_factory=list)
    contour: str = "ascending_arch"  # "ascending_arch", "pendulum", "descending_cascade", "jagged_syncopated"
    tonal_center: str = "Eb"
    scale_degrees: List[int] = field(default_factory=lambda: [1, 3, 5, 7, 9])

    @property
    def interval_signature(self) -> List[int]:
        """Calculates melodic intervals in semitones between successive notes."""
        if len(self.notes) < 2:
            return []
        return [self.notes[i+1].pitch - self.notes[i].pitch for i in range(len(self.notes) - 1)]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "notes": [n.to_dict() for n in self.notes],
            "contour": self.contour,
            "tonal_center": self.tonal_center,
            "scale_degrees": self.scale_degrees,
            "interval_signature": self.interval_signature,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PrimaryMotif:
        return cls(
            name=data.get("name", "Core Motif"),
            notes=[MotifNote.from_dict(n) for n in data.get("notes", [])],
            contour=data.get("contour", "ascending_arch"),
            tonal_center=data.get("tonal_center", "Eb"),
            scale_degrees=data.get("scale_degrees", [1, 3, 5, 7, 9]),
        )


@dataclass
class SignatureRhythm:
    """Distinctive rhythmic cell / clave defining the song's pocket."""
    name: str = "tresillo_syncopated"
    time_signature: str = "4/4"
    hit_positions: List[float] = field(default_factory=lambda: [0.0, 0.75, 1.5, 2.25, 3.0])  # in beats
    swing_ratio: float = 0.58
    microtiming_jitter: float = 0.015

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "time_signature": self.time_signature,
            "hit_positions": self.hit_positions,
            "swing_ratio": round(self.swing_ratio, 3),
            "microtiming_jitter": round(self.microtiming_jitter, 3),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SignatureRhythm:
        return cls(
            name=data.get("name", "tresillo_syncopated"),
            time_signature=data.get("time_signature", "4/4"),
            hit_positions=data.get("hit_positions", [0.0, 0.75, 1.5, 2.25, 3.0]),
            swing_ratio=float(data.get("swing_ratio", 0.58)),
            microtiming_jitter=float(data.get("microtiming_jitter", 0.015)),
        )


@dataclass
class HarmonicPalette:
    """Tonal foundation and allowable harmonic extensions."""
    key_root: str = "Eb"
    scale: str = "minor"
    allowed_modes: List[str] = field(default_factory=lambda: ["dorian", "aeolian", "phrygian"])
    allowed_qualities: List[str] = field(default_factory=lambda: [
        "minor7", "minor9", "minor11", "dominant7", "dominant9", "dominant7_b13", "major7", "major9"
    ])
    require_extensions: bool = True  # Reject bare unextended triads
    allow_modal_borrowing: bool = True
    allow_tritone_substitutions: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key_root": self.key_root,
            "scale": self.scale,
            "allowed_modes": self.allowed_modes,
            "allowed_qualities": self.allowed_qualities,
            "require_extensions": self.require_extensions,
            "allow_modal_borrowing": self.allow_modal_borrowing,
            "allow_tritone_substitutions": self.allow_tritone_substitutions,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HarmonicPalette:
        return cls(
            key_root=data.get("key_root", "Eb"),
            scale=data.get("scale", "minor"),
            allowed_modes=data.get("allowed_modes", ["dorian", "aeolian", "phrygian"]),
            allowed_qualities=data.get("allowed_qualities", ["minor7", "minor9", "minor11"]),
            require_extensions=bool(data.get("require_extensions", True)),
            allow_modal_borrowing=bool(data.get("allow_modal_borrowing", True)),
            allow_tritone_substitutions=bool(data.get("allow_tritone_substitutions", True)),
        )


@dataclass
class InstrumentationRules:
    """Governs arrangement density and role allocations."""
    max_concurrent_harmonic_layers: int = 2
    max_simultaneous_leads: int = 1
    exclusive_sub_bass: bool = True  # Only one track produces < 80 Hz
    priority_order: List[str] = field(default_factory=lambda: ["BASS", "DRUMS", "KEYS", "LEAD", "TEXTURE", "FOLEY"])
    forbidden_combinations: List[Tuple[str, str]] = field(default_factory=lambda: [
        ("SUB_808", "ACOUSTIC_BASS"),  # No clashing low-end sources simultaneously
    ])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_concurrent_harmonic_layers": self.max_concurrent_harmonic_layers,
            "max_simultaneous_leads": self.max_simultaneous_leads,
            "exclusive_sub_bass": self.exclusive_sub_bass,
            "priority_order": self.priority_order,
            "forbidden_combinations": self.forbidden_combinations,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InstrumentationRules:
        return cls(
            max_concurrent_harmonic_layers=int(data.get("max_concurrent_harmonic_layers", 2)),
            max_simultaneous_leads=int(data.get("max_simultaneous_leads", 1)),
            exclusive_sub_bass=bool(data.get("exclusive_sub_bass", True)),
            priority_order=data.get("priority_order", ["BASS", "DRUMS", "KEYS", "LEAD", "TEXTURE", "FOLEY"]),
            forbidden_combinations=[tuple(c) for c in data.get("forbidden_combinations", [])],
        )


@dataclass
class TimbralPalette:
    """Aesthetic sound design identity."""
    aesthetic_mood: str = "neo_soul_groove"
    warmth_factor: float = 0.78          # 0.0 (cold clean) to 1.0 (heavy tape/tube warmth)
    acoustic_environment: str = "intimate_warm_room"
    dominant_textures: List[str] = field(default_factory=lambda: ["vinyl_dust", "analog_saturation", "tape_drift"])
    foley_preference: str = "organic_room_creaks"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "aesthetic_mood": self.aesthetic_mood,
            "warmth_factor": round(self.warmth_factor, 2),
            "acoustic_environment": self.acoustic_environment,
            "dominant_textures": self.dominant_textures,
            "foley_preference": self.foley_preference,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TimbralPalette:
        return cls(
            aesthetic_mood=data.get("aesthetic_mood", "neo_soul_groove"),
            warmth_factor=float(data.get("warmth_factor", 0.78)),
            acoustic_environment=data.get("acoustic_environment", "intimate_warm_room"),
            dominant_textures=data.get("dominant_textures", ["vinyl_dust"]),
            foley_preference=data.get("foley_preference", "organic_room_creaks"),
        )


@dataclass
class SignatureGesture:
    """A unique production move that explicitly belongs to this song."""
    id: str = "gesture_001"
    name: str = "Signature Gesture"
    trigger_section: str = "hook"
    bar_offset: float = 0.0
    description: str = ""
    musical_role: str = "CADENTIAL_PICKUP"  # "CADENTIAL_PICKUP", "PRE_DROP_VACUUM", "OCTAVE_FANFARE", "SUB_GLIDE"
    bar_frequency: int = 4

    def __post_init__(self):
        if not self.name or self.name == "Signature Gesture":
            self.name = self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "trigger_section": self.trigger_section,
            "bar_offset": self.bar_offset,
            "description": self.description,
            "musical_role": self.musical_role,
            "bar_frequency": self.bar_frequency,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SignatureGesture:
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            trigger_section=data.get("trigger_section", "hook"),
            bar_offset=float(data.get("bar_offset", 0.0)),
            description=data.get("description", ""),
            musical_role=data.get("musical_role", "CADENTIAL_PICKUP"),
            bar_frequency=int(data.get("bar_frequency", 4)),
        )


@dataclass
class CompositionalDNA:
    """
    Master Compositional DNA specification.
    Acts as the inviolable musical constitution and generative constraint for a song.
    """
    song_id: str
    title: str = "Untitled Work"
    bpm: float = 110.0
    tempo_bpm: Optional[float] = None
    primary_motif: PrimaryMotif = field(default_factory=PrimaryMotif)
    signature_intervals: List[int] = field(default_factory=lambda: [3, 4, 7, 10, 14])
    signature_rhythm: SignatureRhythm = field(default_factory=SignatureRhythm)
    harmonic_palette: HarmonicPalette = field(default_factory=HarmonicPalette)
    instrumentation_rules: InstrumentationRules = field(default_factory=InstrumentationRules)
    timbral_palette: TimbralPalette = field(default_factory=TimbralPalette)
    signature_gestures: List[SignatureGesture] = field(default_factory=list)
    signature_gesture: Optional[SignatureGesture] = None
    forbidden_constraints: Optional[List[NegativeConstraint]] = None
    negative_constraints: List[NegativeConstraint] = field(default_factory=lambda: [
        NegativeConstraint.NO_STRAIGHT_FOUR_FLOOR_HATS,
        NegativeConstraint.NO_UNEXTENDED_MAJOR_TRIADS,
        NegativeConstraint.NO_CRASH_ON_BEAT_1,
        NegativeConstraint.NO_IDENTICAL_HOOK_REPETITION,
        NegativeConstraint.NO_STATIC_VELOCITIES,
        NegativeConstraint.NO_OVERLAPPING_LOW_END,
    ])
    artistic_intent: Optional[Any] = None
    provenance_records: List[Dict[str, Any]] = field(default_factory=list)
    sonic_families: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if self.tempo_bpm is not None:
            self.bpm = self.tempo_bpm
        else:
            self.tempo_bpm = self.bpm

        if self.signature_gesture is not None and self.signature_gesture not in self.signature_gestures:
            self.signature_gestures.append(self.signature_gesture)

        if self.forbidden_constraints is not None:
            self.negative_constraints = list(self.forbidden_constraints)

    def validate_constraint(self, entity_type: str, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Enforces negative constraints and DNA invariants on proposed musical material.
        entity_type: 'CHORD', 'DRUM_PATTERN', 'SECTION_REPETITION', 'VELOCITY', 'CRASH'
        Returns: (is_valid, violation_message)
        """
        # 1. Check Unextended Major Triads
        if entity_type == "CHORD":
            quality = data.get("quality", "").lower()
            extensions = data.get("extensions", [])
            if NegativeConstraint.NO_UNEXTENDED_MAJOR_TRIADS in self.negative_constraints:
                if quality in ("major", "maj") and not extensions:
                    return False, "Constraint violation: Bare unextended major triads are forbidden by Song DNA."

        # 2. Check Straight Four-On-The-Floor Hi-Hats
        if entity_type == "DRUM_PATTERN":
            role = data.get("role", "")
            notes = data.get("notes", [])
            if NegativeConstraint.NO_STRAIGHT_FOUR_FLOOR_HATS in self.negative_constraints:
                if role in ("HATS", "HI_HAT", "CLOSED_HAT") and len(notes) >= 4:
                    # If hat notes are strictly on integer beats with no syncopation
                    is_straight_quarters = all(abs(n.get("start_time", 0.0) % 1.0) < 0.01 for n in notes)
                    if is_straight_quarters and len(notes) == 4:
                        return False, "Constraint violation: Straight 4-on-the-floor hi-hats forbidden by Song DNA."

        # 3. Check Crash on Beat 1
        if entity_type == "CRASH":
            beat = float(data.get("beat", 0.0))
            if NegativeConstraint.NO_CRASH_ON_BEAT_1 in self.negative_constraints:
                if abs(beat % 4.0) < 0.05:
                    return False, "Constraint violation: Crash cymbal on downbeat beat 1 is forbidden by Song DNA."

        # 4. Check Identical Hook Repetition
        if entity_type == "SECTION_REPETITION":
            section_a = data.get("section_a", "")
            section_b = data.get("section_b", "")
            similarity = float(data.get("similarity", 1.0))
            if NegativeConstraint.NO_IDENTICAL_HOOK_REPETITION in self.negative_constraints:
                if "hook" in section_a.lower() and "hook" in section_b.lower() and similarity > 0.90:
                    return False, f"Constraint violation: {section_b} is {similarity*100:.1f}% identical to {section_a}. Evolution required."

        # 5. Check Static Velocities (Humanization invariant)
        if entity_type == "VELOCITY":
            velocities = data.get("velocities", [])
            if NegativeConstraint.NO_STATIC_VELOCITIES in self.negative_constraints:
                if len(velocities) >= 6 and len(set(velocities)) == 1:
                    return False, "Constraint violation: Robotic static velocity sequence forbidden by Song DNA."

        # 6. Check Low-End Overlap
        if entity_type == "LOW_END":
            active_bass_roles = data.get("active_bass_roles", [])
            if NegativeConstraint.NO_OVERLAPPING_LOW_END in self.negative_constraints:
                if len(active_bass_roles) > 1 and "808" in str(active_bass_roles).lower() and "sub" in str(active_bass_roles).lower():
                    return False, "Constraint violation: Simultaneous conflicting sub-bass roles forbidden by Song DNA."

        return True, None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_id": self.song_id,
            "title": self.title,
            "bpm": self.bpm,
            "primary_motif": self.primary_motif.to_dict(),
            "signature_intervals": self.signature_intervals,
            "signature_rhythm": self.signature_rhythm.to_dict(),
            "harmonic_palette": self.harmonic_palette.to_dict(),
            "instrumentation_rules": self.instrumentation_rules.to_dict(),
            "timbral_palette": self.timbral_palette.to_dict(),
            "signature_gestures": [g.to_dict() for g in self.signature_gestures],
            "negative_constraints": [c.value for c in self.negative_constraints],
            "provenance_records": list(self.provenance_records),
            "sonic_families": list(self.sonic_families),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CompositionalDNA:
        constraints = []
        for c in data.get("negative_constraints", []):
            try:
                constraints.append(NegativeConstraint(c))
            except ValueError:
                pass

        return cls(
            song_id=data.get("song_id", "song_001"),
            title=data.get("title", "Untitled Work"),
            bpm=float(data.get("bpm", 110.0)),
            primary_motif=PrimaryMotif.from_dict(data.get("primary_motif", {})),
            signature_intervals=data.get("signature_intervals", [3, 4, 7, 10, 14]),
            signature_rhythm=SignatureRhythm.from_dict(data.get("signature_rhythm", {})),
            harmonic_palette=HarmonicPalette.from_dict(data.get("harmonic_palette", {})),
            instrumentation_rules=InstrumentationRules.from_dict(data.get("instrumentation_rules", {})),
            timbral_palette=TimbralPalette.from_dict(data.get("timbral_palette", {})),
            signature_gestures=[SignatureGesture.from_dict(g) for g in data.get("signature_gestures", [])],
            negative_constraints=constraints,
            provenance_records=data.get("provenance_records", []),
            sonic_families=data.get("sonic_families", []),
        )
