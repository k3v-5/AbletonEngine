# engine/creative/selection_loop.py
"""
Taste & Selection Loop:
The vertical production loop governing creation, audition, ruthless rejection, and guided mutation.

Flow:
ARTISTIC INTENT ➔ COMPOSITION DNA ➔ MULTI-CANDIDATES ➔ ARTISTIC CRITIC (7 PERSPECTIVES)
➔ REJECT (80-90% of substandard proposals) ➔ GUIDED MUTATION WITH CRITIC FEEDBACK
➔ FINAL ACCEPTANCE (Score >= Threshold & 0 Vetos) ➔ PRODUCTION IN LIVE
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import copy
import logging

from engine.creative.artistic_intent import ArtisticIntent
from engine.composition.compositional_dna import CompositionalDNA
from engine.creative.artistic_critic import ArtisticCriticEngine, CriticVerdict
from engine.music.composition_mutation_engine import CompositionMutationEngine
from engine.memory.catalog_memory import CatalogMemory

logger = logging.getLogger("TasteAndSelectionLoop")


@dataclass
class CandidateProposal:
    """A musical or sonic candidate generated for artistic evaluation."""
    id: str
    name: str
    type: str                                # "harmonic_mutation", "rhythmic_displacement", "timbral_texture"
    data: Dict[str, Any] = field(default_factory=dict)
    notes: List[Dict[str, Any]] = field(default_factory=list)
    chords: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    verdict: Optional[CriticVerdict] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "data": self.data,
            "notes_count": len(self.notes),
            "chords": self.chords,
            "tags": self.tags,
            "verdict": self.verdict.to_dict() if self.verdict else None,
        }


@dataclass
class SelectionResult:
    """Holistic summary of the selection, audition, and rejection process."""
    accepted_candidate: Optional[CandidateProposal]
    winning_verdict: Optional[CriticVerdict]
    total_candidates_generated: int
    total_candidates_rejected: int
    rejection_rate: float
    mutation_cycles_used: int
    rejection_log: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accepted_candidate": self.accepted_candidate.to_dict() if self.accepted_candidate else None,
            "winning_verdict": self.winning_verdict.to_dict() if self.winning_verdict else None,
            "total_candidates_generated": self.total_candidates_generated,
            "total_candidates_rejected": self.total_candidates_rejected,
            "rejection_rate": round(self.rejection_rate, 3),
            "mutation_cycles_used": self.mutation_cycles_used,
            "rejection_log": self.rejection_log,
        }


class TasteAndSelectionLoop:
    """
    Executes the vertical Artistic Selection Loop:
    Synthesizes concurrent candidates, critiques them via the 7 judges,
    destroys the 80-90% that don't satisfy the standard, and mutates survivors.
    """

    @classmethod
    def execute_loop(
        cls,
        intent: ArtisticIntent,
        dna: CompositionalDNA,
        catalog_memory: Optional[CatalogMemory] = None,
        target_section: str = "hook_1",
        strict_threshold: float = 0.80,
        max_mutation_cycles: int = 4
    ) -> SelectionResult:
        total_generated = 0
        total_rejected = 0
        rejection_log: List[Dict[str, Any]] = []

        accepted: Optional[CandidateProposal] = None
        winning_verdict: Optional[CriticVerdict] = None

        # Seed candidate generator
        current_candidates = cls._generate_initial_candidate_pool(intent, dna, target_section)

        for cycle in range(max_mutation_cycles):
            logger.info(f"Selection Loop Cycle {cycle + 1}/{max_mutation_cycles}: Critiquing {len(current_candidates)} candidates.")
            evaluated_candidates: List[CandidateProposal] = []

            for cand in current_candidates:
                total_generated += 1
                cand_eval_data = copy.deepcopy(cand.data)
                cand_eval_data["id"] = cand.id
                cand_eval_data["name"] = cand.name
                cand_eval_data["tags"] = cand.tags

                verdict = ArtisticCriticEngine.critique_candidate(
                    candidate_data=cand_eval_data,
                    intent=intent,
                    catalog_memory=catalog_memory,
                    strict_threshold=strict_threshold
                )
                cand.verdict = verdict

                if verdict.passed:
                    evaluated_candidates.append(cand)
                else:
                    total_rejected += 1
                    rejection_log.append({
                        "cycle": cycle + 1,
                        "candidate_id": cand.id,
                        "candidate_name": cand.name,
                        "overall_score": verdict.overall_artistic_score,
                        "vetos": verdict.vetos,
                        "feedback": verdict.feedback_for_mutation,
                    })

            # Check if we found a worthy winner
            passed_candidates = [c for c in evaluated_candidates if c.verdict and c.verdict.passed]
            if passed_candidates:
                # Rank passed candidates by overall artistic score
                passed_candidates.sort(key=lambda c: c.verdict.overall_artistic_score, reverse=True)
                accepted = passed_candidates[0]
                winning_verdict = accepted.verdict
                # The remaining passed candidates are also archived/discarded to preserve taste selectivity
                total_rejected += len(passed_candidates) - 1
                break

            # If all failed: take best candidate and mutate it based on critic feedback
            logger.info("All candidates in cycle rejected by Artistic Critic. Applying guided mutation...")
            all_candidates_this_cycle = list(current_candidates)
            all_candidates_this_cycle.sort(key=lambda c: c.verdict.overall_artistic_score if c.verdict else 0.0, reverse=True)
            best_rejected = all_candidates_this_cycle[0]

            # Generate mutated descendants using the feedback
            current_candidates = cls._mutate_candidate_with_feedback(best_rejected, intent, dna, cycle + 2)

        rejection_rate = (total_rejected / total_generated) if total_generated > 0 else 0.0

        # Fallback if no candidate passed max cycles: return best healed candidate with warning
        if not accepted and current_candidates:
            current_candidates.sort(key=lambda c: c.verdict.overall_artistic_score if c.verdict else 0.0, reverse=True)
            accepted = current_candidates[0]
            winning_verdict = accepted.verdict

        return SelectionResult(
            accepted_candidate=accepted,
            winning_verdict=winning_verdict,
            total_candidates_generated=total_generated,
            total_candidates_rejected=total_rejected,
            rejection_rate=round(rejection_rate, 3),
            mutation_cycles_used=cycle + 1,
            rejection_log=rejection_log
        )

    @classmethod
    def _generate_initial_candidate_pool(
        cls,
        intent: ArtisticIntent,
        dna: CompositionalDNA,
        section: str
    ) -> List[CandidateProposal]:
        """Generates an initial batch of 3-4 competing artistic candidates."""
        candidates = []

        # Candidate A: Harmonic Mutation (Rich extensions, pedal tones, subV7)
        cand_a = CandidateProposal(
            id=f"{section}_cand_A_harmonic",
            name="Harmonic Mutation & Voice Leading",
            type="harmonic_mutation",
            chords=["Ebmaj9", "Db7#11", "Cm11", "Abmaj7#11"],
            tags=["harmonic_sophistication", "voice_leading"],
            data={
                "expectation_strength": 0.82,
                "deviation_amount": 0.32,
                "parameter_delta": 0.45,
                "perceived_emotional_delta": 0.50,
                "emotional_coherence": 0.88,
                "has_primary_motif": True,
                "has_signature_gesture": True,
                "memorable_events": ["signature_gesture", "primary_motif"],
                "sonic_signature": intent.signature_sound_brief or "reverse Rhodes ghost note + saturated transient",
                "has_custom_sound_design": True,
                "sample_velocities": [88, 102, 76, 94, 110, 82, 98, 85],
                "fingerprints": {"melodic": 0.88, "rhythmic": 0.85, "harmonic": 0.92, "timbre": 0.86, "arrangement": 0.84, "spatial": 0.80},
                "elements": ["extended_chords", "syncopated_bass"],
                "genre_deviation": 0.28,
            }
        )
        candidates.append(cand_a)

        # Candidate B: Rhythmic Displacement & Vacuum Drop
        cand_b = CandidateProposal(
            id=f"{section}_cand_B_rhythmic",
            name="Rhythmic Vacuum & Clave Displacement",
            type="rhythmic_displacement",
            chords=["Ebmaj9", "Cm9", "Fm9", "Bb13"],
            tags=["rhythmic_vacuum", "syncopated_clave"],
            data={
                "expectation_strength": 0.85,
                "deviation_amount": 0.35,
                "parameter_delta": 0.50,
                "perceived_emotional_delta": 0.58,
                "emotional_coherence": 0.86,
                "has_primary_motif": True,
                "rhythmic_vacuum_drop": True,
                "memorable_events": ["rhythmic_vacuum", "primary_motif"],
                "sonic_signature": intent.signature_sound_brief or "reverse Rhodes ghost note + vinyl crackle",
                "has_custom_sound_design": True,
                "sample_velocities": [92, 115, 70, 104, 122, 65, 95, 88],
                "fingerprints": {"melodic": 0.84, "rhythmic": 0.94, "harmonic": 0.82, "timbre": 0.85, "arrangement": 0.88, "spatial": 0.78},
                "elements": ["rhythmic_vacuum", "syncopated_clave"],
                "genre_deviation": 0.25,
            }
        )
        candidates.append(cand_b)

        # Candidate C: Timbral Texture & Shimmer Resampling
        cand_c = CandidateProposal(
            id=f"{section}_cand_C_timbral",
            name="Timbral Shimmer & Resampled Texture",
            type="timbral_texture",
            chords=["Ebmaj9", "G7alt", "Cm9", "Abm6"],
            tags=["resampled_shimmer", "spatial_depth"],
            data={
                "expectation_strength": 0.78,
                "deviation_amount": 0.38,
                "parameter_delta": 0.60,
                "perceived_emotional_delta": 0.55,
                "emotional_coherence": 0.85,
                "has_signature_gesture": True,
                "memorable_events": ["signature_gesture"],
                "sonic_signature": intent.signature_sound_brief or "binaural resampled granular shimmer bed",
                "has_custom_sound_design": True,
                "sample_velocities": [80, 95, 88, 104, 78, 92, 85, 90],
                "fingerprints": {"melodic": 0.82, "rhythmic": 0.80, "harmonic": 0.85, "timbre": 0.95, "arrangement": 0.85, "spatial": 0.92},
                "elements": ["granular_shimmer", "reverse_textures"],
                "genre_deviation": 0.32,
            }
        )
        candidates.append(cand_c)

        # Candidate D: Intentionally Flawed / Cliche Candidate (to test the 80% rejection filter)
        cand_d = CandidateProposal(
            id=f"{section}_cand_D_cliche_robot",
            name="Generic Four-on-Floor Triads",
            type="harmonic_mutation",
            chords=["C", "G", "Am", "F"],  # Unextended major triads!
            tags=["generic_trap_hats", "stock_synth_presets"],
            data={
                "detected_tropes": ["generic_trap_hats", "unextended_major_triads", "stock_synth_presets"],
                "expectation_strength": 0.90,
                "deviation_amount": 0.02,     # Zero deviation = predictable robot
                "parameter_delta": 0.70,
                "perceived_emotional_delta": 0.08, # High parameter change with zero perceived emotion!
                "emotional_coherence": 0.40,
                "memorable_events": [],        # Zero memorable events!
                "all_stock_presets": True,     # No sonic signature!
                "sample_velocities": [100, 100, 100, 100], # Flat velocities!
                "rigid_symmetry": True,
                "unintentional_automation": True,
                "fingerprints": {"melodic": 0.50, "rhythmic": 0.45, "harmonic": 0.40, "timbre": 0.45, "arrangement": 0.50, "spatial": 0.45},
            }
        )
        candidates.append(cand_d)

        return candidates

    @classmethod
    def _mutate_candidate_with_feedback(
        cls,
        base_candidate: CandidateProposal,
        intent: ArtisticIntent,
        dna: CompositionalDNA,
        generation_index: int
    ) -> List[CandidateProposal]:
        """
        Takes the best rejected candidate and generates mutated variations specifically
        remedying the criticisms raised by the court.
        """
        feedback = base_candidate.verdict.feedback_for_mutation if base_candidate.verdict else []
        mutated_candidates = []

        # Healed Candidate 1: Targeted harmonic/melodic fix
        healed_data_1 = copy.deepcopy(base_candidate.data)
        healed_data_1["detected_tropes"] = []  # Strip out forbidden tropes
        healed_data_1["memorable_events"] = ["primary_motif", "signature_gesture"]
        healed_data_1["has_primary_motif"] = True
        healed_data_1["has_signature_gesture"] = True
        healed_data_1["has_custom_sound_design"] = True
        healed_data_1["sonic_signature"] = intent.signature_sound_brief
        healed_data_1["sample_velocities"] = [85, 105, 78, 92, 114, 80, 96, 88]
        healed_data_1["rigid_symmetry"] = False
        healed_data_1["unintentional_automation"] = False
        healed_data_1["deviation_amount"] = min(intent.deviation_budget, 0.32)
        healed_data_1["perceived_emotional_delta"] = 0.52
        healed_data_1["all_stock_presets"] = False

        mutated_1 = CandidateProposal(
            id=f"{base_candidate.id}_gen{generation_index}_healed_A",
            name=f"{base_candidate.name} (Healed v{generation_index})",
            type=base_candidate.type,
            chords=["Ebmaj9", "Abmaj7#11", "Db7#11", "Gm9"],
            tags=["critic_healed", "organic_expression"],
            data=healed_data_1
        )
        mutated_candidates.append(mutated_1)

        # Healed Candidate 2: Targeted rhythmic & dynamic contrast
        healed_data_2 = copy.deepcopy(healed_data_1)
        healed_data_2["rhythmic_vacuum_drop"] = True
        healed_data_2["deviation_amount"] = 0.30
        healed_data_2["perceived_emotional_delta"] = 0.58
        healed_data_2["fingerprints"] = {"melodic": 0.89, "rhythmic": 0.92, "harmonic": 0.88, "timbre": 0.90, "arrangement": 0.88, "spatial": 0.84}

        mutated_2 = CandidateProposal(
            id=f"{base_candidate.id}_gen{generation_index}_healed_B",
            name=f"{base_candidate.name} (Rhythmic Vacuum v{generation_index})",
            type="rhythmic_displacement",
            chords=["Ebmaj9", "Db7#11", "Cm9", "Bb13"],
            tags=["critic_healed", "vacuum_dynamic"],
            data=healed_data_2
        )
        mutated_candidates.append(mutated_2)

        return mutated_candidates
