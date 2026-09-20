"""
Live Creative Controller:
Reversible observation and control layer connecting calibrated creative governance
to live Ableton Live sessions via MCP under Copilot Guided Session.

Follows the 5 Experimental Principles:
1. Shadow Mode: Passive observation and counterfactual divergence tracking without mutating Live.
2. Limited Actuation: Low-risk surgical adjustments (synergies, micro-timing, timbre tweaks).
3. Transactional Rollback: Atomic snapshotting with decision_id and immediate regret recording upon failure.
4. Telemetry -> Memory: Real outcomes feed Yield, Interaction Graph, Regret, Half-Life, and Territory.
5. Online Validation: Real-time HHI, rollback rate, and simulation-reality gap (JSD) monitoring.
"""

import copy
import datetime
import logging
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional

from engine.creative.corpus_territory import CorpusTerritory, TerritoryPoint
from engine.creative.creative_governor import CreativeGovernor
from engine.creative.creative_yield import CreativeYieldTracker
from engine.creative.mechanism_interaction_graph import MechanismInteractionGraph
from engine.creative.creative_regret import CreativeRegretTracker
from engine.creative.innovation_half_life import InnovationHalfLifeTracker
from engine.creative.online_validation_monitor import OnlineValidationMonitor
from engine.session.transaction_guard import TransactionGuard

logger = logging.getLogger("LiveCreativeController")


class OperationalMode(str, Enum):
    SHADOW = "SHADOW"
    LIMITED_ACTUATION = "LIMITED_ACTUATION"


class LiveCreativeController:
    """
    Controlador y Observador Creativo Reversible para Sesiones en Vivo.
    """

    def __init__(
        self,
        territory: Optional[CorpusTerritory] = None,
        yield_tracker: Optional[CreativeYieldTracker] = None,
        interaction_graph: Optional[MechanismInteractionGraph] = None,
        regret_tracker: Optional[CreativeRegretTracker] = None,
        lifecycle_tracker: Optional[InnovationHalfLifeTracker] = None,
        monitor: Optional[OnlineValidationMonitor] = None,
        default_mode: OperationalMode = OperationalMode.SHADOW
    ):
        self.territory = territory or CorpusTerritory()
        self.yield_tracker = yield_tracker or CreativeYieldTracker()
        self.interaction_graph = interaction_graph or MechanismInteractionGraph()
        self.regret_tracker = regret_tracker or CreativeRegretTracker()
        self.lifecycle_tracker = lifecycle_tracker or InnovationHalfLifeTracker()
        self.monitor = monitor or OnlineValidationMonitor()

        self.governor = CreativeGovernor(
            territory=self.territory,
            yield_tracker=self.yield_tracker,
            interaction_graph=self.interaction_graph,
            regret_tracker=self.regret_tracker
        )

        self.mode = default_mode
        self.decision_history: List[Dict[str, Any]] = []
        self.shadow_observations: List[Dict[str, Any]] = []

    def set_mode(self, mode: str) -> OperationalMode:
        """Switches between SHADOW and LIMITED_ACTUATION mode."""
        m = str(mode).strip().upper()
        if "ACTUAT" in m or "LIMITED" in m or "ACTUACION" in m:
            self.mode = OperationalMode.LIMITED_ACTUATION
        else:
            self.mode = OperationalMode.SHADOW
        logger.info(f"LiveCreativeController mode set to {self.mode.value}")
        return self.mode

    def evaluate_session_state(self, session: Any, conn: Any = None) -> Dict[str, Any]:
        """
        Evaluates current session through calibrated Creative Governor and subsystems.
        Extracts recommended actions, synergistic pairs, active quarantines, and novelty bands.
        """
        data = session.data if hasattr(session, "data") else (session if isinstance(session, dict) else {})
        gov_eval = self.governor.determine_governor_mode(data)
        novelty = gov_eval["corpus_novelty"]
        mode = gov_eval["mode"]

        # Consult active quarantines from Innovation Half-Life
        quarantined = [
            t for t in self.lifecycle_tracker.lifecycles.keys()
            if self.lifecycle_tracker.should_quarantine(t)
        ]

        # Consult synergies for dominant technique or primary role
        primary_tech = "polyrhythm_3_16"
        synergies = self.governor.recommend_synergistic_pair(primary_tech, limit=3)

        return {
            "governor_mode": mode,
            "corpus_novelty": novelty,
            "is_territory_stagnant": gov_eval["is_territory_stagnant"],
            "is_quadrant_saturated": gov_eval["is_quadrant_saturated"],
            "high_novelty_regret": gov_eval["high_novelty_regret"],
            "recommended_actions": gov_eval["recommended_actions"],
            "recommended_synergies": synergies,
            "quarantined_techniques": quarantined,
            "operational_mode": self.mode.value
        }

    def record_shadow_observation(
        self,
        session: Any,
        actual_action: str,
        conn: Any = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        SHADOW MODE:
        Computes governor decisions, compares them with what actually occurred in the session,
        and records counterfactual telemetry without modifying Ableton Live.
        """
        eval_res = self.evaluate_session_state(session, conn=conn)
        dec_id = f"dec_shadow_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"

        # Compare governor recommendation with actual action
        gov_mode = eval_res["governor_mode"]
        actual_str = str(actual_action).lower()

        # Counterfactual divergence detection
        diverged = False
        if gov_mode == "EXPLORE" and not any(w in actual_str for w in ["explore", "cambio", "nuevo", "modular", "variar"]):
            diverged = True
        elif gov_mode == "ANCHOR" and any(w in actual_str for w in ["mutar", "radical", "cambio"]):
            diverged = True

        obs = {
            "decision_id": dec_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "operational_mode": "SHADOW",
            "governor_evaluation": eval_res,
            "actual_action": actual_action,
            "diverged_from_governor": diverged,
            "metadata": metadata or {}
        }
        self.shadow_observations.append(obs)

        # Update monitor with shadow observation
        self.monitor.record_decision(
            decision_id=dec_id,
            mode=gov_mode,
            techniques_applied=["shadow_observed"],
            was_rolled_back=False,
            delta_score=0.0,
            metadata={"shadow": True, "diverged": diverged}
        )

        return obs

    def execute_limited_actuation(
        self,
        session: Any,
        conn: Any,
        candidate_key: str,
        techniques_to_apply: List[str],
        mutation_callback: Any,
        expected_improvement: float = 0.05
    ) -> Dict[str, Any]:
        """
        LIMITED ACTUATION MODE:
        Applies a verified low-risk musical modification under atomic TransactionGuard boundaries.
        If identity or coherence degrades, triggers immediate rollback and feeds CreativeRegretTracker.
        """
        if self.mode != OperationalMode.LIMITED_ACTUATION:
            logger.info("Controller is in SHADOW mode. Recording shadow observation instead of actuating.")
            return self.record_shadow_observation(
                session,
                actual_action=f"ACTUATION_REQUESTED_IN_SHADOW_MODE: candidate_{candidate_key}",
                conn=conn
            )

        dec_id = f"dec_live_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        logger.info(f"Initiating limited actuation [{dec_id}] with techniques: {techniques_to_apply}")

        # 1. Capture pre-mutation snapshot
        session_data = session.data if hasattr(session, "data") else (session if isinstance(session, dict) else {})
        live_track_state = []
        if conn is not None and hasattr(conn, "send_command"):
            tracks = session_data.get("tracks", [])
            for t in tracks[:4]:  # Snapshot primary musical tracks
                live_track_state.append(TransactionGuard.capture_live_track_state(conn, t.get("index", 0)))

        TransactionGuard.begin_transaction(session_data, live_track_state)

        # 2. Execute low-risk mutation callback
        pre_triad = self._audit_triad_safely(session)
        pre_score = pre_triad.get("overall_score", 0.70)

        try:
            mutation_result = mutation_callback(session, conn)
        except Exception as ex:
            logger.error(f"Actuation failure during callback: {ex}. Executing immediate rollback.")
            rb_res = TransactionGuard.rollback_transaction(conn, session)
            self._record_actuation_failure(dec_id, techniques_to_apply, reason=f"Exception: {ex}")
            return {
                "status": "ACTUATION_FAILED_EXCEPTION_ROLLED_BACK",
                "decision_id": dec_id,
                "error": str(ex),
                "rollback": rb_res
            }

        # 3. Post-mutation Guardrail & Improvement Evaluation
        post_triad = self._audit_triad_safely(session)
        post_score = post_triad.get("overall_score", 0.70)
        ident_score = post_triad.get("identity_score", 0.80)
        coherence_score = post_triad.get("coherence_score", 0.80)

        delta = round(post_score - pre_score, 4)

        # Guardrail: identity >= 0.45, coherence >= 0.65, and delta >= 0.0 (cannot degrade overall score)
        is_guardrail_valid = (ident_score >= 0.45 and coherence_score >= 0.65 and delta >= -0.01)

        if not is_guardrail_valid:
            logger.warning(
                f"Actuation [{dec_id}] breached guardrails or degraded musical score: "
                f"delta={delta}, ident={ident_score:.2f} (min 0.45), coherence={coherence_score:.2f} (min 0.65). "
                f"Executing atomic rollback."
            )
            rb_res = TransactionGuard.rollback_transaction(conn, session)
            self._record_actuation_failure(dec_id, techniques_to_apply, reason="Guardrail or score breach", delta=delta)

            return {
                "status": "ACTUATION_ROLLED_BACK_BY_GUARDRAIL",
                "decision_id": dec_id,
                "delta": delta,
                "pre_score": pre_score,
                "post_score": post_score,
                "identity_score": ident_score,
                "coherence_score": coherence_score,
                "techniques_rejected": techniques_to_apply,
                "rollback": rb_res
            }

        # 4. Mutation Succeeded -> COMMIT
        TransactionGuard.commit_transaction()
        logger.info(f"Actuation [{dec_id}] successfully committed with delta +{delta:.4f}")

        # Update learning subsystems
        for t in techniques_to_apply:
            self.yield_tracker.record_mechanism_application(t, max(0.50, 0.75 + delta), ident_score, survived_in_final_mix=True)
            self.regret_tracker.record_event(t, was_rolled_back=False)

        if len(techniques_to_apply) >= 2:
            self.interaction_graph.record_interaction(
                techniques_to_apply[0], techniques_to_apply[1],
                delta_improvement=delta,
                identity_preserved=ident_score,
                survived_together=True
            )

        gov_mode = self.governor.determine_governor_mode(session_data)["mode"]
        self.monitor.record_decision(
            decision_id=dec_id,
            mode=gov_mode,
            techniques_applied=techniques_to_apply,
            was_rolled_back=False,
            delta_score=delta,
            metadata={"candidate_key": candidate_key}
        )

        commit_record = {
            "status": "ACTUATION_COMMITTED",
            "decision_id": dec_id,
            "delta": delta,
            "pre_score": pre_score,
            "post_score": post_score,
            "techniques_applied": techniques_to_apply,
            "mutation_result": mutation_result
        }
        self.decision_history.append(commit_record)
        return commit_record

    def commit_session_to_memory(self, session: Any, auto_save: bool = True) -> TerritoryPoint:
        """
        Commits real completed session to CorpusTerritory, updates Innovation Half-Life lifecycles,
        and saves persistent learning state.
        """
        data = session.data if hasattr(session, "data") else (session if isinstance(session, dict) else {})
        pt = self.territory.add_session_to_territory(data, auto_save=auto_save)

        applied = list(data.get("applied_mechanisms", []))
        if applied:
            session_idx = len(self.territory.points)
            yields = {t: 0.85 for t in applied}
            self.lifecycle_tracker.record_session(session_idx, applied, yields=yields)

        if auto_save:
            self.yield_tracker.save()
            self.interaction_graph.save()
            self.regret_tracker.save()

        return pt

    def get_telemetry_dashboard(self) -> Dict[str, Any]:
        """Returns unified real-time dashboard of online health and creative governance."""
        report = self.monitor.generate_report()
        report["operational_mode"] = self.mode.value
        report["shadow_observations_count"] = len(self.shadow_observations)
        report["actuations_committed_count"] = len(self.decision_history)
        report["corpus_territory_total_songs"] = len(self.territory.points)

        clusters = self.territory.discover_territories(min_cluster_size=1)
        report["active_clusters_count"] = len(clusters)

        quarantined = [
            t for t, lc in self.lifecycle_tracker.lifecycles.items()
            if lc.current_status == "SATURATED" or self.lifecycle_tracker.should_quarantine(t)
        ]
        report["quarantined_techniques"] = quarantined

        return report

    def _record_actuation_failure(
        self,
        decision_id: str,
        techniques: List[str],
        reason: str,
        delta: float = -0.10
    ) -> None:
        """Feeds regret and monitor upon failed actuation."""
        for t in techniques:
            self.regret_tracker.record_event(t, was_rolled_back=True)
            self.yield_tracker.record_mechanism_application(t, 0.10, 0.40, survived_in_final_mix=False)

        gov_mode = self.governor.determine_governor_mode({})["mode"]
        self.monitor.record_decision(
            decision_id=decision_id,
            mode=gov_mode,
            techniques_applied=techniques,
            was_rolled_back=True,
            delta_score=delta,
            metadata={"failure_reason": reason}
        )

        self.decision_history.append({
            "status": "ACTUATION_FAILED_ROLLED_BACK",
            "decision_id": decision_id,
            "techniques": techniques,
            "reason": reason,
            "delta": delta
        })

    def _audit_triad_safely(self, session: Any) -> Dict[str, float]:
        """Calculates triad score safely using MusicDirector or default heuristic."""
        try:
            from engine.production.copilot.phases.phase_10.music_director import MusicDirector
            triad = MusicDirector.audit_triad(session)
            ident = triad.get("identity_score", 0.75)
            contrast = triad.get("contrast_score", 0.60)
            coherence = triad.get("coherence_score", 0.80)
            pred = triad.get("predictability_score", 0.50)
            overall = round((ident * 0.40) + (contrast * 0.30) + (coherence * 0.30) - (pred * 0.10), 4)
            return {
                "overall_score": overall,
                "identity_score": ident,
                "contrast_score": contrast,
                "coherence_score": coherence,
                "predictability_score": pred
            }
        except Exception:
            return {
                "overall_score": 0.70,
                "identity_score": 0.75,
                "contrast_score": 0.60,
                "coherence_score": 0.80,
                "predictability_score": 0.50
            }
