"""
Creative Governor:
Top-level executive coordinator overseeing the dual relationship between individual Song Identity
and the historical Corpus Territory Memory.

Answers the supreme evolutionary question:
"¿Esta canción está suficientemente bien Y aporta algo que el motor todavía no ha explorado?"

Coordinates:
- Song Identity & Coherence
- Corpus Territorial Distance, Saturation & Stagnation
- Creative Novelty vs. Cliché Prevention
- Trimodal Governance (EXPLORE / ANCHOR / EVOLVE)
- Mechanism Synergies & Destructive Interference Prevention
- Strategic Directives for Music Director
"""

import logging
from typing import Dict, Any, List, Optional

from engine.creative.music_identity import IdentityAuditor
from engine.creative.corpus_territory import CorpusTerritory, TerritoryPoint
from engine.creative.creative_yield import CreativeYieldTracker
from engine.creative.mechanism_interaction_graph import MechanismInteractionGraph
from engine.creative.creative_regret import CreativeRegretTracker
from engine.production.copilot.phases.phase_10.music_director import MusicDirector

logger = logging.getLogger("CreativeGovernor")


class CreativeGovernor:
    """
    Supervises creative admission, territorial expansion, and guided mutation directives.
    Operates across three dynamic modes:
    - EXPLORE: Spends exploration budget to discover new territories and unfreeze stagnation.
    - ANCHOR: Stabilizes identity anchors when chaos or high regret threatens cohesion.
    - EVOLVE: Applies validated mechanism synergies when territory and identity are healthy.
    """

    def __init__(
        self,
        territory: Optional[CorpusTerritory] = None,
        yield_tracker: Optional[CreativeYieldTracker] = None,
        interaction_graph: Optional[MechanismInteractionGraph] = None,
        regret_tracker: Optional[CreativeRegretTracker] = None
    ):
        self.territory = territory or CorpusTerritory()
        self.yield_tracker = yield_tracker or CreativeYieldTracker()
        self.interaction_graph = interaction_graph or MechanismInteractionGraph()
        self.regret_tracker = regret_tracker or CreativeRegretTracker()

    def assess_session_admission(
        self,
        session: Any,
        min_identity: float = 0.50,
        min_coherence: float = 0.65
    ) -> Dict[str, Any]:
        """
        Evaluates whether a candidate session meets the dual standard:
        1. Musical Quality & Coherence (Identity >= 0.50, Coherence >= 0.65)
        2. Territorial Contribution (Novelty & Absence of uncreative saturation)
        """
        data = session.data if hasattr(session, "data") else (session if isinstance(session, dict) else {})

        # 1. Internal Audits
        ident_audit = IdentityAuditor.evaluate_identity(data)
        ident_score = ident_audit.get("identity_score", 0.50)

        coherence_audit = MusicDirector.audit_coherence(session)
        coherence_score = coherence_audit.get("coherence_score", 0.80)

        # 2. Territorial Distance & Saturation
        novelty_score = self.territory.calculate_corpus_distance(session)
        saturation_audit = self.territory.detect_territory_saturation(session)

        # 3. Useful Novelty: novelty * (coherence / 0.65) * (identity / 0.45)
        coherence_factor = min(1.0, coherence_score / min_coherence) if min_coherence > 0 else 1.0
        identity_factor = min(1.0, ident_score / min_identity) if min_identity > 0 else 1.0
        useful_novelty = round(novelty_score * coherence_factor * identity_factor, 4)

        # 4. Determine Admission Verdict
        is_coherent = (ident_score >= min_identity and coherence_score >= min_coherence)
        is_saturated = saturation_audit["is_saturated"]

        if not is_coherent:
            verdict = "REJECTED_COHERENCE_BREACH"
            rationale = "La sesión no supera los umbrales mínimos de coherencia narrativa o identidad."
        elif is_saturated and novelty_score < 0.25:
            verdict = "REJECTED_SATURATED_CLICHE"
            rationale = f"La sesión habita un cuadrante sobresaturado ({saturation_audit['neighbor_count_in_radius']} canciones) sin aportar novedad suficiente."
        elif novelty_score >= 0.40:
            verdict = "ADMITTED_AS_NEW_TERRITORY"
            rationale = "La sesión expande el mapa territorial con identidad y coherencia comprobadas."
        else:
            verdict = "ADMITTED_AS_CANONICAL_VARIATION"
            rationale = "La sesión es coherente y añade una variación válida dentro de un territorio conocido."

        return {
            "status": "GOVERNANCE_AUDITED",
            "verdict": verdict,
            "admitted": verdict.startswith("ADMITTED"),
            "rationale": rationale,
            "metrics": {
                "identity_score": ident_score,
                "coherence_score": coherence_score,
                "corpus_novelty_score": novelty_score,
                "useful_novelty_score": useful_novelty,
                "is_territory_saturated": is_saturated
            },
            "saturation_details": saturation_audit,
            "identity_details": ident_audit,
            "coherence_details": coherence_audit
        }

    def determine_governor_mode(self, session: Any) -> Dict[str, Any]:
        """
        Determines the Trimodal operational state of the creative engine:
        1. EXPLORE: Gasto del presupuesto de exploración, evasión de cuadrantes saturados o estancamiento territorial.
        2. ANCHOR: Estabilización y preservación de identidad ante riesgo de caos o alto arrepentimiento.
        3. EVOLVE: Crecimiento balanceado aplicando sinergias validadas del grafo de interacción.
        """
        data = session.data if hasattr(session, "data") else (session if isinstance(session, dict) else {})
        ident_audit = IdentityAuditor.evaluate_identity(data)
        ident_score = ident_audit.get("identity_score", 0.50)
        novelty_score = self.territory.calculate_corpus_distance(session)

        # Check stagnation & saturation
        stagnation = self.territory.detect_territorial_stagnation()
        saturation = self.territory.detect_territory_saturation(session)

        # Check regret in high novelty
        band_regret = self.regret_tracker.get_regret_by_novelty_band()
        high_novelty_regret = band_regret.get("high_novelty", {}).get("regret_rate", 0.0)
        extreme_novelty_regret = band_regret.get("extreme_novelty", {}).get("regret_rate", 0.0)

        # 1. ANCHOR condition: Fragile identity, extreme novelty (> 0.85) or high regret (>= 0.40)
        if ident_score < 0.50 or novelty_score > 0.85 or high_novelty_regret >= 0.40 or extreme_novelty_regret >= 0.40:
            mode = "ANCHOR"
            reason = "Preservar y estabilizar anclas de identidad: riesgo de caos, novedad excesiva o alto arrepentimiento histórico."
            recommended_actions = [
                "Reforzar leitmotif melódico en versión literal",
                "Consolidar bolsillo de groove en drums",
                "Evitar mutaciones tímbricas destructivas"
            ]

        # 2. EXPLORE condition: Stagnation detected, quadrant saturated, or novelty too low (< 0.20)
        elif stagnation.get("is_stagnant") or saturation["is_saturated"] or novelty_score < 0.20:
            mode = "EXPLORE"
            reason = "Presupuesto de exploración activo: escapar de saturación o estancamiento territorial hacia nuevos cuadrantes."
            recommended_actions = [
                "Probar combinaciones no convencionales del presupuesto de exploración",
                "Levantar penalizaciones a técnicas de bajo rendimiento histórico en nuevos contextos",
                "Modificar centro tonal o tempo para abrir nuevo territorio estético"
            ]

        # 3. EVOLVE condition: Healthy identity and territory, apply graph synergies
        else:
            mode = "EVOLVE"
            reason = "Evolución armónica: territorio y coherencia saludables; explotar sinergias creativas comprobadas."
            recommended_actions = [
                "Aplicar pares de mecanismos con sinergia creativa comprobada (> +0.10)",
                "Evitar interferencias destructivas identificadas en el grafo",
                "Mantener la progresión de la ley narrativa"
            ]

        return {
            "mode": mode,
            "reason": reason,
            "identity_score": ident_score,
            "corpus_novelty": novelty_score,
            "is_territory_stagnant": stagnation.get("is_stagnant", False),
            "is_quadrant_saturated": saturation["is_saturated"],
            "high_novelty_regret": high_novelty_regret,
            "recommended_actions": recommended_actions
        }

    def guide_music_director(self, session: Any) -> Dict[str, Any]:
        """
        Supplies high-level strategic directives to MusicDirector before A/B mutation search,
        integrating trimodal governance (EXPLORE / ANCHOR / EVOLVE) and mechanism synergies.
        """
        gov_mode_eval = self.determine_governor_mode(session)
        mode = gov_mode_eval["mode"]
        novelty = gov_mode_eval["corpus_novelty"]
        is_saturated = gov_mode_eval["is_quadrant_saturated"]

        if mode == "EXPLORE":
            strategy = "EXPLORE_NOVELTY"
            recommendation = (
                "Modo EXPLORE: Favorecer mutaciones con mayor diferenciación tímbrica o polirritmia "
                "para escapar del clúster saturado o estancado."
            )
            preferred_candidates = ["C", "E"]
        elif mode == "ANCHOR":
            strategy = "ANCHOR_IDENTITY"
            recommendation = (
                "Modo ANCHOR: La identidad es frágil o el riesgo de arrepentimiento/caos es elevado. "
                "Favorecer anclaje rítmico y continuidad armónica."
            )
            preferred_candidates = ["A", "D"]
        else:
            strategy = "BALANCED_EVOLUTION"
            recommendation = (
                "Modo EVOLVE: Balance óptimo entre identidad y novedad territorial. "
                "Aplicar sinergias del grafo de mecanismos."
            )
            preferred_candidates = ["A", "B", "C", "D", "E"]

        return {
            "governor_mode": mode,
            "strategy": strategy,
            "corpus_novelty": novelty,
            "is_saturated": is_saturated,
            "preferred_candidates": preferred_candidates,
            "recommendation": recommendation,
            "mode_evaluation": gov_mode_eval
        }

    def recommend_synergistic_pair(self, base_technique: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Recommends complementary techniques that have high positive synergy with base_technique."""
        return self.interaction_graph.get_best_synergies(base_technique, self.yield_tracker, limit=limit)

    def is_destructive_pair(self, tech_a: str, tech_b: str) -> bool:
        """Checks whether two techniques cause destructive interference."""
        eval_res = self.interaction_graph.calculate_synergy(tech_a, tech_b, self.yield_tracker)
        return eval_res.get("status") == "DESTRUCTIVE_INTERFERENCE"

    def commit_session(self, session: Any, auto_save: bool = False) -> TerritoryPoint:
        """Registers an admitted session into the historical territory."""
        return self.territory.add_session_to_territory(session, auto_save=auto_save)
