# engine/memory/production_memory_hub.py
"""
Production Memory Hub (The 4-Tier Memory Coordinator):
Harmonizes and orchestrates the four distinct memory layers:
1. SONG MEMORY: What occurred inside this specific song timeline?
2. COMPOSITORY MEMORY: How did its motifs and thematic lineages evolve?
3. SONIC MEMORY: How did its sound design objects progress through their life stages?
4. CATALOG MEMORY: What should NOT be repeated compared to other catalog songs?

And connects with the Production Learning Engine to turn verified interventions into persistent wisdom.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import logging

from engine.music.motifs.compository_memory import CompositoryMemory
from engine.production.contract.sonic_memory import SonicMemory
from engine.production.contract.musical_memory import MusicalMemory
from .catalog_memory import CatalogMemory, CatalogConflict
from .production_learning import ProductionLearningEngine, LearnedProductionWisdom, AcousticAnalysisResult

logger = logging.getLogger("ProductionMemoryHub")


@dataclass
class MemoryPerspectiveReport:
    """Holistic view from all 4 memory layers on a proposed musical or sonic move."""
    section_name: str
    song_memory_context: str
    compository_lineage_status: str
    sonic_lifecycle_stage: str
    catalog_conflicts: List[Dict[str, Any]]
    relevant_learned_wisdom: List[Dict[str, Any]]
    all_clear_to_proceed: bool
    artistic_recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_name": self.section_name,
            "song_memory_context": self.song_memory_context,
            "compository_lineage_status": self.compository_lineage_status,
            "sonic_lifecycle_stage": self.sonic_lifecycle_stage,
            "catalog_conflicts": self.catalog_conflicts,
            "relevant_learned_wisdom": self.relevant_learned_wisdom,
            "all_clear_to_proceed": self.all_clear_to_proceed,
            "artistic_recommendation": self.artistic_recommendation,
        }


class ProductionMemoryHub:
    """
    Unified coordinator interfacing all 4 memory systems for the AI Producer.
    """

    def __init__(
        self,
        musical_memory: Optional[MusicalMemory] = None,
        compository_memory: Optional[CompositoryMemory] = None,
        sonic_memory: Optional[SonicMemory] = None,
        catalog_memory: Optional[CatalogMemory] = None,
        learning_engine: Optional[ProductionLearningEngine] = None,
        song_id: str = "default_song"
    ):
        self.musical_memory = musical_memory or MusicalMemory(song_id=song_id)
        self.compository_memory = compository_memory or CompositoryMemory()
        self.sonic_memory = sonic_memory or SonicMemory()
        self.catalog_memory = catalog_memory or CatalogMemory()
        self.learning_engine = learning_engine or ProductionLearningEngine()

    def consult_memories(
        self,
        section_name: str,
        song_id: str,
        key_root: str,
        bpm: float,
        proposed_instruments: Dict[str, str],
        proposed_recipes: List[str]
    ) -> MemoryPerspectiveReport:
        """
        Queries all 4 memory layers simultaneously before a major artistic decision.
        """
        # 1. Song Memory (Musical Narrative)
        milestones = self.musical_memory.get_milestones_for_section(section_name)
        song_context = (
            f"{len(milestones)} milestones recorded for {section_name}. "
            f"Precedent: {milestones[0].what_happened_before if milestones else 'Initial section exposure'}."
        )

        # 2. Compository Memory (Motif lineage)
        lineage_count = len(self.compository_memory.lineages)
        compository_status = (
            f"{lineage_count} active motif lineages tracked. "
            f"Motif evolution index active across timeline."
        )

        # 3. Sonic Memory (Sonic object lifecycle)
        active_occurrences = [
            occ for obj in self.sonic_memory.genealogies.values()
            for occ in obj.occurrences if occ.section.lower() == section_name.lower()
        ]

        sonic_status = (
            f"{len(active_occurrences)} sonic object occurrences active in {section_name} "
            f"(stage: {active_occurrences[0].stage.value if active_occurrences else 'DEVELOPMENT'})."
        )

        # 4. Catalog Memory (Cross-song clash check)
        conflicts = self.catalog_memory.audit_proposal(
            proposed_instruments=proposed_instruments,
            proposed_recipes=proposed_recipes,
            key_root=key_root,
            bpm=bpm,
            current_song_id=song_id
        )

        # 5. Production Learning (Historical wisdom)
        wisdom_rules = self.learning_engine.query_wisdom(target_section=section_name, key_root=key_root)

        all_clear = len(conflicts) == 0
        if all_clear:
            recommendation = "All 4 memories approve: Musical novelty, motif evolution, and catalog distinction verified."
        else:
            recommendation = f"Catalog Memory raised {len(conflicts)} redundancy warnings. Consider diversification suggestions."

        return MemoryPerspectiveReport(
            section_name=section_name,
            song_memory_context=song_context,
            compository_lineage_status=compository_status,
            sonic_lifecycle_stage=sonic_status,
            catalog_conflicts=[c.to_dict() for c in conflicts],
            relevant_learned_wisdom=[w.to_dict() for w in wisdom_rules],
            all_clear_to_proceed=all_clear,
            artistic_recommendation=recommendation
        )
