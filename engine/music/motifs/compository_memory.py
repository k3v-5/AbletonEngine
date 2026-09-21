# engine/music/motifs/compository_memory.py
"""
Compository Memory (Level K - Motif Development):
Tracks and preserves the thematic genealogy of musical motifs across the arrangement timeline.

Ensures that the song tells an evolving, unified musical story rather than repeating static loops:
Seed Motif (Hook 1) ➔ Variation (Verse 2) ➔ Inverted/Sub-Bass (Bridge) ➔ Climactic Payoff (Hook 3).
"""
from __future__ import annotations
import uuid
import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..models import Motif

logger = logging.getLogger("CompositoryMemory")


@dataclass
class MotifEvolutionNode:
    """A specific evolutionary manifestation of a motif in the song timeline."""
    node_id: str
    motif_id: str
    seed_id: str
    section_name: str
    bar_range: Tuple[int, int]
    role: str
    transformation_name: str
    narrative_function: str
    intervals_summary: List[int]
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "motif_id": self.motif_id,
            "seed_id": self.seed_id,
            "section_name": self.section_name,
            "bar_range": list(self.bar_range),
            "role": self.role,
            "transformation_name": self.transformation_name,
            "narrative_function": self.narrative_function,
            "intervals_summary": list(self.intervals_summary),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MotifEvolutionNode:
        br = data.get("bar_range", [1, 8])
        return cls(
            node_id=data.get("node_id", str(uuid.uuid4())[:8]),
            motif_id=data.get("motif_id", "motif_1"),
            seed_id=data.get("seed_id", "seed_1"),
            section_name=data.get("section_name", "Hook 1"),
            bar_range=(int(br[0]), int(br[1])),
            role=data.get("role", "melody"),
            transformation_name=data.get("transformation_name", "ORIGINAL"),
            narrative_function=data.get("narrative_function", ""),
            intervals_summary=list(data.get("intervals_summary", [])),
            created_at=data.get("created_at", ""),
        )


@dataclass
class MotifLineage:
    """The complete developmental journey of a single foundational motif."""
    seed_id: str
    name: str
    initial_role: str
    nodes: List[MotifEvolutionNode] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed_id": self.seed_id,
            "name": self.name,
            "initial_role": self.initial_role,
            "nodes": [n.to_dict() for n in self.nodes],
        }

    @property
    def evolution_count(self) -> int:
        return len(self.nodes)

    @property
    def sections_visited(self) -> List[str]:
        return [n.section_name for n in self.nodes]


class CompositoryMemory:
    """
    Guards and audits the musical memory of all motifs across the piece.
    Prevents thematic amnesia (motifs that appear once and are forgotten)
    and static repetition (motifs repeated without evolution).
    """

    def __init__(self, song_id: str = "default_song"):
        self.song_id = song_id
        self._lineages: Dict[str, MotifLineage] = {}

    def register_seed_motif(
        self,
        seed_id: str,
        name: str,
        initial_role: str,
        section_name: str,
        bar_range: Tuple[int, int],
        intervals: List[int],
        narrative_function: str = "Primary thematic seed statement"
    ) -> MotifLineage:
        """Establishes a foundational musical seed."""
        node = MotifEvolutionNode(
            node_id=f"node_{seed_id}_v0",
            motif_id=seed_id,
            seed_id=seed_id,
            section_name=section_name,
            bar_range=bar_range,
            role=initial_role,
            transformation_name="ORIGINAL_STATEMENT",
            narrative_function=narrative_function,
            intervals_summary=intervals,
        )
        lineage = MotifLineage(seed_id=seed_id, name=name, initial_role=initial_role, nodes=[node])
        self._lineages[seed_id] = lineage
        logger.info(f"Registered seed motif '{name}' ({seed_id}) in section '{section_name}'")
        return lineage

    def register_evolution(
        self,
        seed_id: str,
        derived_motif_id: str,
        section_name: str,
        bar_range: Tuple[int, int],
        role: str,
        transformation_name: str,
        intervals: List[int],
        narrative_function: str
    ) -> Optional[MotifEvolutionNode]:
        """Appends a new evolutionary branch to an existing motif lineage."""
        lineage = self._lineages.get(seed_id)
        if not lineage:
            logger.warning(f"Cannot evolve non-existent seed motif '{seed_id}'")
            return None

        version_num = len(lineage.nodes)
        node = MotifEvolutionNode(
            node_id=f"node_{seed_id}_v{version_num}",
            motif_id=derived_motif_id,
            seed_id=seed_id,
            section_name=section_name,
            bar_range=bar_range,
            role=role,
            transformation_name=transformation_name,
            narrative_function=narrative_function,
            intervals_summary=intervals,
        )
        lineage.nodes.append(node)
        logger.info(f"Evolved motif '{seed_id}' -> version {version_num} ({transformation_name}) in '{section_name}'")
        return node

    @property
    def lineages(self) -> Dict[str, MotifLineage]:
        return self._lineages

    def get_lineage(self, seed_id: str) -> Optional[MotifLineage]:
        return self._lineages.get(seed_id)

    def audit_compository_memory(self) -> Dict[str, Any]:
        """
        Audits the thematic cohesion of the arrangement:
        - Are key motifs developed across at least 2 or 3 sections?
        - Do repeating sections show developmental variance?
        """
        results: List[Dict[str, Any]] = []
        overall_developed = True

        for s_id, lin in self._lineages.items():
            count = len(lin.nodes)
            is_developed = count >= 2
            if not is_developed:
                overall_developed = False

            has_role_shift = len(set(n.role for n in lin.nodes)) > 1
            has_structural_variation = len(set(n.transformation_name for n in lin.nodes)) > 1

            results.append({
                "seed_id": s_id,
                "name": lin.name,
                "evolution_count": count,
                "sections": lin.sections_visited,
                "has_role_transmutation": has_role_shift,
                "has_structural_variation": has_structural_variation,
                "status": "HEALTHY_DEVELOPMENT" if is_developed else "STATIC_OR_ORPHAN",
            })

        return {
            "total_motifs": len(self._lineages),
            "is_thematically_developed": overall_developed,
            "motifs": results,
            "verdict": "THEMATIC_CONTINUITY" if overall_developed else "NEEDS_DEVELOPMENT",
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_id": self.song_id,
            "lineages": {k: v.to_dict() for k, v in self._lineages.items()},
            "audit": self.audit_compository_memory(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CompositoryMemory:
        cm = cls(song_id=data.get("song_id", "default_song"))
        lineages_data = data.get("lineages", {})
        for s_id, l_data in lineages_data.items():
            nodes = [MotifEvolutionNode.from_dict(n) for n in l_data.get("nodes", [])]
            cm._lineages[s_id] = MotifLineage(
                seed_id=l_data.get("seed_id", s_id),
                name=l_data.get("name", "Motif"),
                initial_role=l_data.get("initial_role", "melody"),
                nodes=nodes,
            )
        return cm
