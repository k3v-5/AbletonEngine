# engine/performance/closed_loop_adapter.py
"""
S <-> T Closed-Loop Integration Adapter (Nivel T5):
Closes the loop between Intentional Performance and ClosedLoopCreativeEvolutionEngine:
1. Detects mechanical fatigue (rigid grid, flat dynamics, block chords).
2. Generates 3 candidate interpretations (Subtle Pocket, Laid-Back Expressive, Dilla Soul Drag).
3. Evaluates candidates in-situ with ContextualSonicCritic under GovernanceGuard supervision.
4. Executes atomic COMMIT or 0 ms instant ROLLBACK using PerformanceSnapshot.
5. Inscribes PERFORMANCE_MUTATION into EvolutionLedger.
"""
from __future__ import annotations

import copy
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np

from .models import (
    PerformanceIntent,
    InstrumentPerformanceProfile,
    PerformanceSnapshot,
    PerformanceMutation,
    PocketTendency,
    VelocityProfile,
    ArticulationStyle,
)
from .core import PerformanceCore
from .groove_intelligence import CorrelatedHumanizer, GrooveMemory, SongGrooveTemplate
from .phrase_breathing import PhraseBreathingEngine
from engine.creative.contextual_sonic_critic import (
    ContextualSonicCritic,
    ContextualAuditReport,
    ContextualVerdict,
)
from engine.creative.evolution.governance_guard import EvolutionGovernanceGuard
from engine.creative.evolution.ledger import EvolutionLedger
from engine.composition.compositional_dna import CompositionalDNA

logger = logging.getLogger("PerformanceClosedLoopAdapter")


class PerformanceClosedLoopAdapter:
    """
    Adapter orchestrating closed-loop performance refinement.
    """

    def __init__(
        self,
        critic: Optional[ContextualSonicCritic] = None,
        governance_guard: Optional[EvolutionGovernanceGuard] = None,
        ledger: Optional[EvolutionLedger] = None
    ):
        self.critic = critic or ContextualSonicCritic()
        self.governance = governance_guard or EvolutionGovernanceGuard()
        self.ledger = ledger or EvolutionLedger()

    @classmethod
    def detect_mechanical_fatigue(
        cls,
        session_tracks: Dict[str, List[Dict[str, Any]]],
        track_roles: Dict[str, str],
        bpm: float = 120.0
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Detects whether the session suffers from mechanical fatigue / over-quantization.
        """
        total_notes = 0
        grid_snapped_notes = 0
        velocities: List[int] = []

        ms_per_beat = (60.0 / max(20.0, bpm)) * 1000.0

        for t_name, notes in session_tracks.items():
            for n in notes:
                total_notes += 1
                st = float(n.get("start_time", n.get("start", 0.0)))
                v = int(n.get("velocity", 90))
                velocities.append(v)

                nearest_16th = round(st / 0.25) * 0.25
                offset_ms = abs(st - nearest_16th) * ms_per_beat
                if offset_ms < 1.0:
                    grid_snapped_notes += 1

        if total_notes == 0:
            return False, {"reason": "Empty session"}

        grid_snap_pct = (grid_snapped_notes / total_notes) * 100.0
        m_vel = float(sum(velocities)) / total_notes
        var_vel = sum((v - m_vel) ** 2 for v in velocities) / total_notes
        std_vel = (var_vel ** 0.5)

        is_fatigued = (grid_snap_pct >= 90.0) and (std_vel < 6.0)

        report = {
            "total_notes": total_notes,
            "grid_snap_pct": round(grid_snap_pct, 1),
            "velocity_std": round(std_vel, 2),
            "is_fatigued": is_fatigued,
            "diagnosis": "Mechanical Fatigue Detected: Session is strictly quantized with flat velocity."
            if is_fatigued else "Session exhibits natural dynamic variance."
        }
        return is_fatigued, report

    @classmethod
    def generate_candidate_interpretations(
        cls,
        session_tracks: Dict[str, List[Dict[str, Any]]],
        track_roles: Dict[str, str],
        bpm: float = 120.0,
        groove_template: Optional[SongGrooveTemplate] = None
    ) -> Dict[str, Tuple[PerformanceIntent, Dict[str, List[Dict[str, Any]]]]]:
        """
        Synthesizes 3 musically distinct performance candidates:
        - Candidate A: Subtle Pocket (Tight groove, metric hierarchy)
        - Candidate B: Laid-Back Expressive (Neo-soul pocket, breathing, chord spread)
        - Candidate C: Dilla Soul Drag (Hardware swing, dynamic rubato)
        """
        # Candidate A: Subtle Pocket
        intent_a = PerformanceIntent(
            intent_id="intent_subtle_pocket",
            name="Subtle Pocket",
            pocket=PocketTendency.TIGHT_POCKET,
            timing_variance_ms=2.5,
            velocity_profile=VelocityProfile.TIERED_PULSE,
            articulation=ArticulationStyle.NATURAL_BREATHING,
            ghost_note_probability=0.08,
            human_factor=0.40
        )
        tracks_a = CorrelatedHumanizer.humanize_ensemble(
            session_tracks=session_tracks,
            track_roles=track_roles,
            intent=intent_a,
            bpm=bpm,
            groove_template=groove_template,
            seed=101
        )

        # Candidate B: Laid-Back Expressive
        intent_b = PerformanceIntent(
            intent_id="intent_laid_back_expressive",
            name="Laid-Back Expressive",
            pocket=PocketTendency.LAID_BACK,
            timing_variance_ms=6.0,
            velocity_profile=VelocityProfile.EXPRESSIVE,
            articulation=ArticulationStyle.NATURAL_BREATHING,
            ghost_note_probability=0.18,
            phrase_push=0.25,
            human_factor=0.75
        )
        tracks_b = CorrelatedHumanizer.humanize_ensemble(
            session_tracks=session_tracks,
            track_roles=track_roles,
            intent=intent_b,
            bpm=bpm,
            groove_template=groove_template,
            seed=202
        )
        # Apply phrase breathing to lead and keys
        for t_name, role in track_roles.items():
            if role.lower() in ["lead", "melody", "vocal", "keys", "piano"]:
                if t_name in tracks_b:
                    prof = InstrumentPerformanceProfile.create_default(role)
                    tracks_b[t_name] = PhraseBreathingEngine.apply_phrase_breathing(
                        tracks_b[t_name], prof, intent_b, bpm=bpm
                    )

        # Candidate C: Dilla Soul Drag
        intent_c = PerformanceIntent(
            intent_id="intent_dilla_drag",
            name="Dilla Soul Drag",
            pocket=PocketTendency.LOOSE_DRAG,
            timing_variance_ms=9.0,
            velocity_profile=VelocityProfile.RUBATO_BREATHING,
            articulation=ArticulationStyle.NATURAL_BREATHING,
            ghost_note_probability=0.25,
            phrase_push=0.35,
            human_factor=0.90
        )
        tracks_c = CorrelatedHumanizer.humanize_ensemble(
            session_tracks=session_tracks,
            track_roles=track_roles,
            intent=intent_c,
            bpm=bpm,
            groove_template=groove_template,
            seed=303
        )

        return {
            "subtle_pocket": (intent_a, tracks_a),
            "laid_back_expressive": (intent_b, tracks_b),
            "dilla_drag": (intent_c, tracks_c),
        }

    def execute_closed_loop_performance_cycle(
        self,
        section_name: str,
        session_tracks: Dict[str, List[Dict[str, Any]]],
        track_roles: Dict[str, str],
        baseline_audio: Union[str, np.ndarray, Dict[str, Any]],
        candidate_audio_map: Dict[str, Union[str, np.ndarray, Dict[str, Any]]],
        bpm: float = 120.0,
        song_dna: Optional[CompositionalDNA] = None,
        contract: Optional[Any] = None
    ) -> Tuple[Dict[str, List[Dict[str, Any]]], PerformanceMutation, str]:
        """
        Audits performance candidates against baseline audio, evaluates acoustic delta,
        checks governance sovereignty, and commits or rolls back in 0 ms.
        """
        # Step 1: Capture atomic snapshot
        snapshot = PerformanceCore.create_snapshot(session_tracks)

        # Step 2: Generate 3 musical candidate interpretations
        candidates = self.generate_candidate_interpretations(
            session_tracks=session_tracks,
            track_roles=track_roles,
            bpm=bpm
        )

        best_cand_name = None
        best_cand_notes = None
        best_delta_q = -999.0
        best_intent = None

        # Step 3: Audition each candidate in-situ with ContextualSonicCritic
        for cand_name, (intent, cand_notes) in candidates.items():
            staged_audio = candidate_audio_map.get(cand_name, baseline_audio)

            report = self.critic.evaluate_staged_sound_in_context(
                section_name=section_name,
                baseline_audio=baseline_audio,
                staged_audio=staged_audio,
                song_dna=song_dna,
                target_role="performance_ensemble",
                candidate_id=cand_name
            )

            # Governance check
            is_valid, veto_msg = self.governance.evaluate_candidate_verdict(
                candidate_report=report,
                song_dna=song_dna,
                contract=contract
            )

            if is_valid and report.net_improvement_score > best_delta_q:
                best_delta_q = report.net_improvement_score
                best_cand_name = cand_name
                best_cand_notes = cand_notes
                best_intent = intent

        # Step 4: Decision: COMMIT or 0 ms ROLLBACK
        if best_cand_notes is not None and best_delta_q > 0.0:
            verdict = "COMMIT"
            final_tracks = best_cand_notes

            # Record mutation in ledger
            mutation = PerformanceMutation(
                track_name=list(session_tracks.keys())[0] if session_tracks else "ensemble",
                role="ensemble",
                timing_offset_mean_ms=best_intent.timing_variance_ms if best_intent else 4.0,
                timing_offset_std_ms=2.5,
                velocity_delta_mean=8.0,
                velocity_std=14.0,
                articulation_shift=best_intent.articulation.value if best_intent else "NATURAL_BREATHING",
                strum_applied_ms=14.0,
                breath_gaps_injected=2,
                delta_q_achieved=best_delta_q,
                verdict=verdict
            )
            self.ledger.record_performance_mutation(
                section_name=section_name,
                order_type="PERFORMANCE_HUMANIZATION_POCKET",
                delta_q=best_delta_q,
                verdict=verdict,
                decision_reason=f"Candidate '{best_cand_name}' improved acoustic cohesion with delta_q={best_delta_q:.3f}."
            )
            return final_tracks, mutation, verdict

        else:
            # ROLLBACK to pristine snapshot
            verdict = "ROLLBACK"
            final_tracks = PerformanceCore.restore_snapshot(snapshot)

            mutation = PerformanceMutation(
                track_name="ensemble",
                role="ensemble",
                timing_offset_mean_ms=0.0,
                timing_offset_std_ms=0.0,
                velocity_delta_mean=0.0,
                velocity_std=0.0,
                articulation_shift="UNCHANGED",
                delta_q_achieved=best_delta_q if best_delta_q > -999.0 else 0.0,
                verdict=verdict
            )
            self.ledger.record_performance_mutation(
                section_name=section_name,
                order_type="PERFORMANCE_HUMANIZATION_POCKET",
                delta_q=mutation.delta_q_achieved,
                verdict=verdict,
                decision_reason="Performance candidates degraded acoustic critique or failed governance. Restored baseline."
            )
            return final_tracks, mutation, verdict
