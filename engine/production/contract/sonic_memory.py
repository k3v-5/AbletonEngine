# engine/production/contract/sonic_memory.py
"""
Sonic Memory (Level H -> Level G):
Tracks the temporal genealogy and narrative lifecycle of sonic objects
across song sections.

Binds sound design transformations to musical causality:
a signature sound is not an isolated random sample, but an evolving acoustic entity
with birth, development, climax, and decay stages across the song's timeline.
"""
from __future__ import annotations
import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("SonicMemory")


class SonicLifeStage(str, Enum):
    """The lifecycle stage of a sonic object within the song's narrative arc."""
    BIRTH = "BIRTH"                # Subtle, filtered, or distant initial glimpse
    DEVELOPMENT = "DEVELOPMENT"    # Transformative variation (e.g. in the Bridge)
    CLIMAX = "CLIMAX"              # Full, unfiltered, front-and-center statement (e.g. Final Hook)
    DECAY = "DECAY"                # Degraded relic, tape residue, or whisper in the Outro


@dataclass
class SonicOccurrence:
    """An appearance of a sonic object at a specific point in the arrangement."""
    section: str
    start_bar: int
    end_bar: int
    stage: SonicLifeStage
    form_description: str
    narrative_purpose: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section": self.section,
            "start_bar": self.start_bar,
            "end_bar": self.end_bar,
            "stage": self.stage.value if isinstance(self.stage, SonicLifeStage) else str(self.stage),
            "form_description": self.form_description,
            "narrative_purpose": self.narrative_purpose,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SonicOccurrence:
        stage_str = data.get("stage", "BIRTH")
        try:
            stage = SonicLifeStage(stage_str)
        except ValueError:
            stage = SonicLifeStage.BIRTH
        return cls(
            section=data.get("section", ""),
            start_bar=int(data.get("start_bar", 0)),
            end_bar=int(data.get("end_bar", 0)),
            stage=stage,
            form_description=data.get("form_description", ""),
            narrative_purpose=data.get("narrative_purpose", ""),
            timestamp=data.get("timestamp", ""),
        )


@dataclass
class SonicObjectGenealogy:
    """
    The lineage and evolution history of a unique sound across the entire track.
    """
    object_id: str
    name: str
    parent_track_name: str
    parent_motif_desc: str
    occurrences: List[SonicOccurrence] = field(default_factory=list)

    def add_occurrence(
        self,
        section: str,
        start_bar: int,
        end_bar: int,
        stage: SonicLifeStage,
        form_desc: str,
        narrative_purpose: str
    ) -> SonicOccurrence:
        occ = SonicOccurrence(
            section=section,
            start_bar=start_bar,
            end_bar=end_bar,
            stage=stage,
            form_description=form_desc,
            narrative_purpose=narrative_purpose
        )
        self.occurrences.append(occ)
        return occ

    def has_stage(self, stage: SonicLifeStage) -> bool:
        return any(o.stage == stage for o in self.occurrences)

    def get_sections(self) -> List[str]:
        return [o.section for o in self.occurrences]

    def has_contrast(self) -> bool:
        """
        Verifies that the object does not appear identically in all sections.
        Requires either varied life stages or varied form descriptions.
        """
        if len(self.occurrences) <= 1:
            return True
        stages = {o.stage for o in self.occurrences}
        forms = {o.form_description for o in self.occurrences}
        return len(stages) > 1 or len(forms) > 1

    def get_evolution_arc(self) -> str:
        if not self.occurrences:
            return "No occurrences recorded."
        parts = [
            f"{o.section} [{o.stage.value}]: {o.form_description}"
            for o in self.occurrences
        ]
        return " ➔ ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "object_id": self.object_id,
            "name": self.name,
            "parent_track_name": self.parent_track_name,
            "parent_motif_desc": self.parent_motif_desc,
            "occurrences": [o.to_dict() for o in self.occurrences],
            "evolution_arc": self.get_evolution_arc(),
            "has_contrast": self.has_contrast(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SonicObjectGenealogy:
        return cls(
            object_id=data.get("object_id", ""),
            name=data.get("name", "Sonic Object"),
            parent_track_name=data.get("parent_track_name", ""),
            parent_motif_desc=data.get("parent_motif_desc", ""),
            occurrences=[SonicOccurrence.from_dict(o) for o in data.get("occurrences", [])],
        )


@dataclass
class SonicMemory:
    """
    Master repository linking sound design entities with musical narrative memory.
    Ensures that sounds tell a story across time and maintain aesthetic contrast.
    """
    genealogies: Dict[str, SonicObjectGenealogy] = field(default_factory=dict)

    def register_object(
        self,
        object_id: str,
        name: str,
        parent_track_name: str,
        parent_motif_desc: str
    ) -> SonicObjectGenealogy:
        if object_id not in self.genealogies:
            self.genealogies[object_id] = SonicObjectGenealogy(
                object_id=object_id,
                name=name,
                parent_track_name=parent_track_name,
                parent_motif_desc=parent_motif_desc
            )
        return self.genealogies[object_id]

    def record_occurrence(
        self,
        object_id: str,
        section: str,
        start_bar: int,
        end_bar: int,
        stage: SonicLifeStage,
        form_description: str,
        narrative_purpose: str
    ) -> Optional[SonicOccurrence]:
        gen = self.genealogies.get(object_id)
        if not gen:
            logger.warning(f"SonicMemory: Object '{object_id}' not found. Auto-registering.")
            gen = self.register_object(object_id, object_id, "Unknown Track", "Unknown Motif")
        return gen.add_occurrence(section, start_bar, end_bar, stage, form_description, narrative_purpose)

    def audit_narrative_continuity(self, song_sections: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Audits the narrative progression and contrast across all tracked sonic genealogies.
        """
        song_sections = song_sections or ["Intro", "Verse 1", "Hook 1", "Verse 2", "Hook 2", "Bridge", "Hook 3", "Outro"]
        total_objects = len(self.genealogies)
        contrast_failures: List[str] = []
        static_loop_warnings: List[str] = []

        for obj_id, gen in self.genealogies.items():
            if not gen.has_contrast():
                contrast_failures.append(f"El objeto '{gen.name}' ({obj_id}) suena repetitivo sin variación de forma ni etapa.")
            # Check if an object plays in every single section (loss of contrast)
            occ_sections = set(gen.get_sections())
            if len(occ_sections) >= len(song_sections) - 1:
                static_loop_warnings.append(f"El objeto '{gen.name}' está presente en {len(occ_sections)}/{len(song_sections)} secciones. Falta contraste.")

        is_coherent = len(contrast_failures) == 0 and len(static_loop_warnings) == 0

        return {
            "total_objects_tracked": total_objects,
            "is_narratively_coherent": is_coherent,
            "contrast_failures": contrast_failures,
            "static_loop_warnings": static_loop_warnings,
            "genealogies_summary": [g.to_dict() for g in self.genealogies.values()],
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "genealogies": {k: v.to_dict() for k, v in self.genealogies.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SonicMemory:
        genealogies_raw = data.get("genealogies", {})
        genealogies = {}
        for k, v in genealogies_raw.items():
            genealogies[k] = SonicObjectGenealogy.from_dict(v)
        return cls(genealogies=genealogies)
