# engine/production/contract/sonic_identity.py
"""
Sonic Identity (Level H):
Defines the sound design thesis, identity budget, sound design roles, and
sonic identity audit for the song in production.

Transforms the engine from composing purely MIDI notes to composing unique,
unrepeatable sonic material, enforcing that identity emerges from contrast,
narrative purpose, and strict anti-saturation budgets.
"""
from __future__ import annotations
import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("SonicIdentity")


class SoundDesignRole(str, Enum):
    """Categorization of sound design elements according to their narrative function."""
    SIGNATURE = "SIGNATURE"              # The unique, unmistakable auditory fingerprint of this song
    ATMOSPHERE = "ATMOSPHERE"            # Living organic floor bed (vinyl, tape hiss, natural foley)
    TRANSITION = "TRANSITION"            # Tension bridge, riser, or vacuum between sections
    IMPACT = "IMPACT"                    # Physical weight anchoring section boundaries
    EAR_CANDY = "EAR_CANDY"              # Ephemeral momentary micro-event (plays 1-2 times max)
    COUNTER_MELODY = "COUNTER_MELODY"    # Sonic secondary line dialoguing with lead
    TEXTURE = "TEXTURE"                  # Timbral layer enriching an existing acoustic voice
    RISER = "RISER"                      # Rising tension curve
    DOWNLIFTER = "DOWNLIFTER"            # Post-drop energy dispersion
    GLITCH = "GLITCH"                    # Micro-rhythmic or buffer-stutter fragmentation
    DRONE = "DRONE"                      # Harmonic or dissonant tonal anchor
    SUBSTITUTION = "SUBSTITUTION"        # Unexpected sonic replacement of a customary element
    RESONANCE = "RESONANCE"              # Tuned acoustic or spectral ringing


@dataclass
class SonicIdentityBudget:
    """
    Budget constraint system preventing sound design oversaturation.
    A song's sonic identity depends on contrast; if everything is extraordinary,
    nothing is extraordinary.
    """
    max_signature_sounds: int = 2
    max_major_transformations: int = 3
    max_ear_candy_events: int = 8
    max_extreme_processing_events: int = 1

    used_signature_sounds: int = 0
    used_major_transformations: int = 0
    used_ear_candy_events: int = 0
    used_extreme_processing_events: int = 0

    def can_add_signature_sound(self) -> bool:
        return self.used_signature_sounds < self.max_signature_sounds

    def can_add_transformation(self) -> bool:
        return self.used_major_transformations < self.max_major_transformations

    def can_add_ear_candy(self) -> bool:
        return self.used_ear_candy_events < self.max_ear_candy_events

    def can_add_extreme_processing(self) -> bool:
        return self.used_extreme_processing_events < self.max_extreme_processing_events

    def record_signature_sound(self) -> bool:
        if not self.can_add_signature_sound():
            logger.warning("SonicIdentityBudget: Signature sound limit exceeded!")
            return False
        self.used_signature_sounds += 1
        return True

    def record_transformation(self) -> bool:
        if not self.can_add_transformation():
            logger.warning("SonicIdentityBudget: Major transformation limit exceeded!")
            return False
        self.used_major_transformations += 1
        return True

    def record_ear_candy(self) -> bool:
        if not self.can_add_ear_candy():
            logger.warning("SonicIdentityBudget: Ear candy event limit exceeded!")
            return False
        self.used_ear_candy_events += 1
        return True

    def record_extreme_processing(self) -> bool:
        if not self.can_add_extreme_processing():
            logger.warning("SonicIdentityBudget: Extreme processing limit exceeded!")
            return False
        self.used_extreme_processing_events += 1
        return True

    def is_within_budget(self) -> bool:
        return (
            self.used_signature_sounds <= self.max_signature_sounds and
            self.used_major_transformations <= self.max_major_transformations and
            self.used_ear_candy_events <= self.max_ear_candy_events and
            self.used_extreme_processing_events <= self.max_extreme_processing_events
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_signature_sounds": self.max_signature_sounds,
            "max_major_transformations": self.max_major_transformations,
            "max_ear_candy_events": self.max_ear_candy_events,
            "max_extreme_processing_events": self.max_extreme_processing_events,
            "used_signature_sounds": self.used_signature_sounds,
            "used_major_transformations": self.used_major_transformations,
            "used_ear_candy_events": self.used_ear_candy_events,
            "used_extreme_processing_events": self.used_extreme_processing_events,
            "is_within_budget": self.is_within_budget(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SonicIdentityBudget:
        budget = cls(
            max_signature_sounds=int(data.get("max_signature_sounds", 2)),
            max_major_transformations=int(data.get("max_major_transformations", 3)),
            max_ear_candy_events=int(data.get("max_ear_candy_events", 8)),
            max_extreme_processing_events=int(data.get("max_extreme_processing_events", 1)),
        )
        budget.used_signature_sounds = int(data.get("used_signature_sounds", 0))
        budget.used_major_transformations = int(data.get("used_major_transformations", 0))
        budget.used_ear_candy_events = int(data.get("used_ear_candy_events", 0))
        budget.used_extreme_processing_events = int(data.get("used_extreme_processing_events", 0))
        return budget


@dataclass
class SonicObject:
    """
    A concrete sound-designed entity introduced into the song.
    Possesses an explicit emotional intent, role, source origin, and lifecycle.
    """
    id: str
    name: str
    role: SoundDesignRole
    source_track: str
    source_material_desc: str
    archetype: str
    target_sections: List[str]
    placement_bars: List[int] = field(default_factory=list)
    processing_chain: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    is_extreme: bool = False
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value if isinstance(self.role, SoundDesignRole) else str(self.role),
            "source_track": self.source_track,
            "source_material_desc": self.source_material_desc,
            "archetype": self.archetype,
            "target_sections": list(self.target_sections),
            "placement_bars": list(self.placement_bars),
            "processing_chain": list(self.processing_chain),
            "parameters": dict(self.parameters),
            "is_extreme": self.is_extreme,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SonicObject:
        role_str = data.get("role", "SIGNATURE")
        try:
            role = SoundDesignRole(role_str)
        except ValueError:
            role = SoundDesignRole.SIGNATURE
        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Unnamed Sonic Object"),
            role=role,
            source_track=data.get("source_track", ""),
            source_material_desc=data.get("source_material_desc", ""),
            archetype=data.get("archetype", "custom"),
            target_sections=data.get("target_sections", []),
            placement_bars=data.get("placement_bars", []),
            processing_chain=data.get("processing_chain", []),
            parameters=data.get("parameters", {}),
            is_extreme=bool(data.get("is_extreme", False)),
            created_at=data.get("created_at", ""),
        )


@dataclass
class SonicIdentityAuditReport:
    """Diagnostic report of the song's sonic identity and sound design."""
    has_signature_sound: bool
    signature_sound_count: int
    objects_by_role: Dict[str, int]
    budget_report: Dict[str, Any]
    contrast_ratio: float
    is_oversaturated: bool
    sections_with_signature: List[str]
    clean_sections: List[str]
    recommendations: List[str]
    verdict: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_signature_sound": self.has_signature_sound,
            "signature_sound_count": self.signature_sound_count,
            "objects_by_role": self.objects_by_role,
            "budget_report": self.budget_report,
            "contrast_ratio": round(self.contrast_ratio, 3),
            "is_oversaturated": self.is_oversaturated,
            "sections_with_signature": self.sections_with_signature,
            "clean_sections": self.clean_sections,
            "recommendations": self.recommendations,
            "verdict": self.verdict,
        }


class SonicIdentityAudit:
    """
    Audits the song's sonic identity layer (Level H).
    Verifies that the piece has a unique auditory footprint, that the signature
    material is rationed for contrast, and that budget boundaries are strictly maintained.
    """

    @classmethod
    def audit(
        cls,
        sonic_objects: List[SonicObject],
        budget: SonicIdentityBudget,
        all_sections: Optional[List[str]] = None
    ) -> SonicIdentityAuditReport:
        if all_sections is None:
            all_sections = ["Intro", "Verse 1", "Hook 1", "Verse 2", "Hook 2", "Bridge", "Hook 3", "Outro"]

        objects_by_role: Dict[str, int] = {}
        for obj in sonic_objects:
            r = obj.role.value if isinstance(obj.role, SoundDesignRole) else str(obj.role)
            objects_by_role[r] = objects_by_role.get(r, 0) + 1

        sig_objects = [
            obj for obj in sonic_objects
            if obj.role == SoundDesignRole.SIGNATURE
        ]
        sig_count = len(sig_objects)
        has_signature = sig_count > 0

        # Sections where signature sounds appear
        sections_with_sig = set()
        for obj in sig_objects:
            for s in obj.target_sections:
                sections_with_sig.add(s)

        sections_with_sig_list = sorted(list(sections_with_sig))
        clean_sections = [s for s in all_sections if s not in sections_with_sig]

        total_secs = max(1, len(all_sections))
        # Contrast ratio: percentage of clean sections that give relief to the listener
        contrast_ratio = len(clean_sections) / total_secs

        # Oversaturation checks
        is_oversaturated = False
        recs = []

        if not budget.is_within_budget():
            is_oversaturated = True
            recs.append("CRITICAL: El presupuesto de identidad sónica está sobregirado. Reduce mutaciones o ear candy.")

        if sig_count > budget.max_signature_sounds:
            is_oversaturated = True
            recs.append(f"Demasiados Signature Sounds ({sig_count} vs máx {budget.max_signature_sounds}). Diluye la identidad.")

        if contrast_ratio < 0.25 and has_signature:
            is_oversaturated = True
            recs.append(f"Poco contraste ({int(contrast_ratio*100)}% secciones limpias). El sonido firma suena en casi todo el tema.")

        if not has_signature:
            recs.append("La canción carece de un Signature Sound identificable. Corre el riesgo de sonar a preset MIDI genérico.")

        if is_oversaturated:
            verdict = "OVERSATURATED"
        elif not has_signature:
            verdict = "MISSING_IDENTITY"
        else:
            verdict = "COHERENT_IDENTITY"

        return SonicIdentityAuditReport(
            has_signature_sound=has_signature,
            signature_sound_count=sig_count,
            objects_by_role=objects_by_role,
            budget_report=budget.to_dict(),
            contrast_ratio=contrast_ratio,
            is_oversaturated=is_oversaturated,
            sections_with_signature=sections_with_sig_list,
            clean_sections=clean_sections,
            recommendations=recs,
            verdict=verdict,
        )
