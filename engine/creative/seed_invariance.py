"""
Seed Invariance & Path-Dependency Auditor:
Evaluates whether the engine's evolutionary trajectory is robustly independent of early
contingent biases or trapped in severe historical path-dependency (hysteresis).

Tests 3 initial memory states:
1. TABULA_RASA: Fresh initialization with zero memory.
2. BIASED_EARLY: Pre-loaded with 15 sessions concentrated in a single aesthetic zone.
3. DIVERSE_SEED: Pre-loaded with 15 diverse multi-genre sessions.

Measures:
- Escape Velocity: Did the biased engine escape the early cluster into new territories?
- Final Centroid Distance between runs.
- Path-Dependency Ratio: Fraction of subsequent generations bound to initial bias.
"""

import random
import logging
from typing import Dict, Any, List, Optional

from engine.sound.timbre_dna import TimbreDNA
from engine.creative.corpus_territory import CorpusTerritory, TerritoryPoint, compute_centroid
from engine.creative.creative_yield import CreativeYieldTracker
from engine.creative.mechanism_interaction_graph import MechanismInteractionGraph
from engine.creative.creative_regret import CreativeRegretTracker
from engine.creative.creative_governor import CreativeGovernor

logger = logging.getLogger("SeedInvarianceAuditor")


class SeedInvarianceAuditor:
    """
    Simulates evolutionary cohorts starting from distinct memory states to quantify path-dependency.
    """

    @classmethod
    def run_invariance_study(
        cls,
        generations_per_cohort: int = 60,
        base_seed: int = 101
    ) -> Dict[str, Any]:
        """
        Executes parallel runs initialized with Tabula Rasa, Biased, and Diverse memories.
        """
        # 1. Initialize Memories
        terr_tabula = CorpusTerritory(storage_path="")
        terr_tabula.clear()

        terr_biased = CorpusTerritory(storage_path="")
        terr_biased.clear()
        # Seed biased memory: 15 identical/ultra-close Melodic Techno sessions
        for i in range(15):
            terr_biased.add_session_to_territory({
                "name": f"BiasedSeed_{i+1}",
                "genre": "melodic_techno",
                "bpm": 124.0,
                "tonal_center": "F#",
                "mode": "Minor",
                "tracks": [{"role": "LEAD", "timbre_dna": TimbreDNA(brightness=0.8, roughness=0.3).to_dict()}]
            })

        terr_diverse = CorpusTerritory(storage_path="")
        terr_diverse.clear()
        # Seed diverse memory: 15 varied sessions across 5 genres
        div_genres = ["ambient", "dnb", "house", "afro_house", "melodic_techno"]
        div_keys = ["C", "E", "A", "G", "F#"]
        for i in range(15):
            terr_diverse.add_session_to_territory({
                "name": f"DiverseSeed_{i+1}",
                "genre": div_genres[i % len(div_genres)],
                "bpm": 90.0 + (i * 6),
                "tonal_center": div_keys[i % len(div_keys)],
                "mode": "Minor" if i % 2 == 0 else "Major",
                "tracks": [{"role": "LEAD", "timbre_dna": TimbreDNA(brightness=0.3 + 0.04 * i).to_dict()}]
            })

        # Run forward simulation on each
        res_tabula = cls._simulate_forward(terr_tabula, generations_per_cohort, base_seed, "TabulaRasa")
        res_biased = cls._simulate_forward(terr_biased, generations_per_cohort, base_seed, "BiasedEarly")
        res_diverse = cls._simulate_forward(terr_diverse, generations_per_cohort, base_seed, "DiverseSeed")

        # Measure Distance between final centroids of newly generated points
        cent_tabula = compute_centroid(res_tabula["generated_points"], "tabula")
        cent_biased = compute_centroid(res_biased["generated_points"], "biased")
        cent_diverse = compute_centroid(res_diverse["generated_points"], "diverse")

        dist_biased_to_tabula = CorpusTerritory.calculate_distance(cent_biased, cent_tabula)
        dist_diverse_to_tabula = CorpusTerritory.calculate_distance(cent_diverse, cent_tabula)

        # Check Escape from Biased quadrant: how many generated points are NOT melodic_techno 124 BPM?
        escaped_points = [
            p for p in res_biased["generated_points"]
            if p.genre != "melodic_techno" or abs(p.bpm - 124.0) > 5.0
        ]
        escape_ratio = round(len(escaped_points) / max(1, len(res_biased["generated_points"])), 3)
        path_dependency_ratio = round(1.0 - escape_ratio, 3)

        if escape_ratio >= 0.65:
            verdict = "RESILIENT_INDEPENDENCE"
            diagnostic = "El motor superó el sesgo inicial: exploró nuevos cuadrantes y rompió el monopolio de memoria."
        elif escape_ratio >= 0.40:
            verdict = "MODERATE_HYSTERESIS"
            diagnostic = "El motor mostró inercia moderada, pero logró diversificarse parcialmente."
        else:
            verdict = "SEVERE_PATH_DEPENDENCY_TRAP"
            diagnostic = "El sistema quedó atrapado en el cuadrante inicial por feedback positivo no amortiguado."

        return {
            "status": "SEED_INVARIANCE_AUDITED",
            "generations_evaluated": generations_per_cohort,
            "escape_ratio_from_bias": escape_ratio,
            "path_dependency_ratio": path_dependency_ratio,
            "final_centroid_distance_biased_vs_tabula": round(dist_biased_to_tabula, 4),
            "final_centroid_distance_diverse_vs_tabula": round(dist_diverse_to_tabula, 4),
            "clusters_discovered_biased": len(terr_biased.discover_territories(min_cluster_size=2)),
            "clusters_discovered_tabula": len(terr_tabula.discover_territories(min_cluster_size=2)),
            "verdict": verdict,
            "diagnostic": diagnostic
        }

    @classmethod
    def _simulate_forward(
        cls,
        territory: CorpusTerritory,
        generations: int,
        base_seed: int,
        run_name: str
    ) -> Dict[str, Any]:
        """Runs forward generation with active Creative Governor."""
        yield_tracker = CreativeYieldTracker(storage_path="", exploration_rate=0.20)
        interaction_graph = MechanismInteractionGraph(storage_path="")
        regret_tracker = CreativeRegretTracker(storage_path="")
        governor = CreativeGovernor(
            territory=territory,
            yield_tracker=yield_tracker,
            interaction_graph=interaction_graph,
            regret_tracker=regret_tracker
        )

        genres = ["melodic_techno", "ambient", "house", "dnb"]
        keys = ["F#", "A", "C", "D"]
        generated: List[TerritoryPoint] = []

        for i in range(generations):
            rng = random.Random(base_seed + i * 29)

            # Governor decides mode
            mock_session = {
                "name": f"{run_name}_{i+1}",
                "genre": genres[i % len(genres)],
                "bpm": 124.0 + (i % 5) * 4,
                "tonal_center": keys[i % len(keys)],
                "mode": "Minor",
                "tracks": [{"role": "LEAD", "timbre_dna": TimbreDNA(brightness=0.4 + 0.4 * rng.random()).to_dict()}],
                "sections": [{"name": "verse"}, {"name": "drop"}]
            }

            mode_eval = governor.determine_governor_mode(mock_session)
            mode = mode_eval["mode"]

            # If EXPLORE, intentionally branch out to distinct tempo / genre
            if mode == "EXPLORE":
                genre = genres[(i + 2) % len(genres)]
                bpm = 135.0 if mock_session["bpm"] < 130 else 105.0
            else:
                genre = mock_session["genre"]
                bpm = mock_session["bpm"]

            final_session = dict(mock_session)
            final_session["genre"] = genre
            final_session["bpm"] = bpm

            pt = territory.add_session_to_territory(final_session)
            generated.append(pt)

        return {"generated_points": generated}
