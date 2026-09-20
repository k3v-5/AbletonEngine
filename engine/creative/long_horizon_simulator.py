"""
Long-Horizon Creative Simulator:
Executes large-scale in-memory simulations (N = 1,000 to 5,000 sessions) to observe
asymptotic behavior, territorial expansion, and evaluate the "Meta-Cliché of the Governor".

Answers the supreme empirical question:
"¿El sistema continúa evolucionando o finalmente encuentra otra forma de convergencia?"
"""

import math
import random
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

from engine.sound.timbre_dna import TimbreDNA
from engine.creative.corpus_territory import CorpusTerritory, TerritoryPoint
from engine.creative.creative_yield import CreativeYieldTracker
from engine.creative.mechanism_interaction_graph import MechanismInteractionGraph
from engine.creative.creative_regret import CreativeRegretTracker
from engine.creative.creative_governor import CreativeGovernor
from engine.creative.innovation_half_life import InnovationHalfLifeTracker

logger = logging.getLogger("LongHorizonSimulator")


@dataclass
class WindowMetric:
    """Metrics snapshot for a chronological window of N sessions."""
    window_index: int
    session_start: int
    session_end: int
    cluster_count: int
    average_step_distance: float
    governor_mode_ratios: Dict[str, float]
    top_techniques: List[str]
    herfindahl_index: float  # < 0.18 = healthy diversity, > 0.25 = concentration


class LongHorizonSimulator:
    """
    High-throughput headless simulator tracking long-term macro-evolutionary trajectories.
    """

    TECHNIQUE_CATALOG = [
        "polyrhythm_3_16", "foley_texture", "pre_drop_vacuum", "timbre_distortion",
        "sub_glide", "reverse_verb", "stereo_widening", "turnaround_syncopation",
        "dynamic_sidechain", "ghost_notes", "spectral_freeze", "fm_bell_mod"
    ]

    @classmethod
    def run_simulation(
        cls,
        n_sessions: int = 1000,
        window_size: int = 100,
        seed: int = 42
    ) -> Dict[str, Any]:
        """
        Runs an accelerated simulation of N sequential sessions.
        Computes sliding window metrics, asymptotic convergence, and meta-cliché detection.
        """
        start_time = time.time()
        rng = random.Random(seed)

        territory = CorpusTerritory(storage_path="")
        territory.clear()

        yield_tracker = CreativeYieldTracker(storage_path="", exploration_rate=0.20)
        interaction_graph = MechanismInteractionGraph(storage_path="")
        regret_tracker = CreativeRegretTracker(storage_path="")
        lifecycle_tracker = InnovationHalfLifeTracker(storage_path="")

        governor = CreativeGovernor(
            territory=territory,
            yield_tracker=yield_tracker,
            interaction_graph=interaction_graph,
            regret_tracker=regret_tracker
        )

        genres = ["melodic_techno", "ambient", "house", "dnb", "breakbeat", "afro_house"]
        keys = ["F#", "A", "C", "D", "E", "G", "B"]
        modes = ["Minor", "Dorian", "Aeolian", "Major", "Phrygian"]

        # Track history
        mode_history: List[str] = []
        technique_usages: Dict[str, int] = {t: 0 for t in cls.TECHNIQUE_CATALOG}
        window_metrics: List[WindowMetric] = []

        curr_window_modes: Dict[str, int] = {"EXPLORE": 0, "ANCHOR": 0, "EVOLVE": 0}
        curr_window_techniques: Dict[str, int] = {t: 0 for t in cls.TECHNIQUE_CATALOG}

        # Dynamic state progression
        curr_genre_idx = 0
        curr_key_idx = 0
        curr_mode_idx = 0
        curr_bpm = 124.0
        curr_brightness = 0.60
        curr_roughness = 0.40

        for idx in range(n_sessions):
            genre = genres[curr_genre_idx % len(genres)]
            key = keys[curr_key_idx % len(keys)]
            scale_mode = modes[curr_mode_idx % len(modes)]

            # Organic within-territory variations
            c_bright = min(0.95, max(0.10, curr_brightness + rng.uniform(-0.08, 0.08)))
            c_rough = min(0.95, max(0.10, curr_roughness + rng.uniform(-0.08, 0.08)))
            c_bpm = min(175.0, max(80.0, curr_bpm + rng.uniform(-2.5, 2.5)))
            c_notes = rng.randint(20, 36)

            session = {
                "name": f"SimSong_{idx+1}",
                "genre": genre,
                "bpm": round(c_bpm, 1),
                "tonal_center": key,
                "mode": scale_mode,
                "tracks": [
                    {"role": "LEAD", "has_leitmotif": True, "timbre_dna": TimbreDNA(brightness=c_bright, roughness=c_rough).to_dict()},
                    {"role": "DRUMS", "notes_count": c_notes},
                    {"role": "TEXTURE_FOLEY"}
                ],
                "spatial_energy_curve": [{"stereo_width": rng.uniform(0.1, 0.3)}, {"stereo_width": rng.uniform(1.1, 1.4)}],
                "sections": [{"name": "verse"}, {"name": "drop", "is_pre_drop_transition": True}]
            }

            # 1. Governor Decision
            gov_eval = governor.determine_governor_mode(session)
            mode = gov_eval["mode"]
            mode_history.append(mode)
            curr_window_modes[mode] = curr_window_modes.get(mode, 0) + 1

            # When in EXPLORE mode, execute exploratory jump to new territory
            if mode == "EXPLORE":
                curr_genre_idx = (curr_genre_idx + rng.randint(1, 3)) % len(genres)
                curr_key_idx = (curr_key_idx + rng.randint(1, 4)) % len(keys)
                curr_mode_idx = (curr_mode_idx + 1) % len(modes)
                curr_bpm = rng.choice([95.0, 110.0, 126.0, 140.0, 172.0])
                curr_brightness = rng.uniform(0.20, 0.85)
                curr_roughness = rng.uniform(0.20, 0.85)
                session["genre"] = genres[curr_genre_idx % len(genres)]
                session["bpm"] = round(curr_bpm, 1)
                session["tonal_center"] = keys[curr_key_idx % len(keys)]
                session["tracks"][0]["timbre_dna"] = TimbreDNA(brightness=curr_brightness, roughness=curr_roughness).to_dict()
            elif mode == "ANCHOR":
                curr_bpm = round(curr_bpm)
                curr_brightness = 0.50
                curr_roughness = 0.40
            else:  # EVOLVE: smooth drift in current aesthetic pocket
                curr_brightness = c_bright
                curr_roughness = c_rough
                curr_bpm = c_bpm
                if rng.random() < 0.12:
                    curr_key_idx = (curr_key_idx + 1) % len(keys)

            # 2. Select Mechanisms based on Governor Mode & Innovation Half-Life
            k_mech = rng.randint(2, 4)
            weights = []
            for t in cls.TECHNIQUE_CATALOG:
                # Quarantined techniques get severe penalty
                if lifecycle_tracker.should_quarantine(t):
                    w = 0.05
                else:
                    base_p = 0.50
                    force_exp = (mode == "EXPLORE")
                    w, _ = yield_tracker.modulate_probability_with_budget(t, base_p, force_explore=force_exp)
                weights.append(w)

            chosen = list(set(rng.choices(cls.TECHNIQUE_CATALOG, weights=weights, k=k_mech)))

            # 3. Filter conflicts via Graph
            if len(chosen) >= 2:
                filtered = [chosen[0]]
                for t in chosen[1:]:
                    if not governor.is_destructive_pair(filtered[0], t):
                        filtered.append(t)
                chosen = filtered

            for t in chosen:
                technique_usages[t] += 1
                curr_window_techniques[t] = curr_window_techniques.get(t, 0) + 1

            # 4. Simulate Outcome & Updates
            is_rollback = (rng.random() < 0.12)
            if is_rollback:
                for t in chosen:
                    regret_tracker.record_event(t, was_rolled_back=True)
                    yield_tracker.record_mechanism_application(t, 0.15, 0.70, False)
            else:
                for t in chosen:
                    regret_tracker.record_event(t, was_rolled_back=False)
                    yield_tracker.record_mechanism_application(t, 0.85, 0.85, True)

            # Update lifecycles
            lifecycle_tracker.record_session(
                session_index=idx + 1,
                techniques_applied=chosen,
                yields={t: (0.15 if is_rollback else 0.85) for t in chosen}
            )

            # Record interaction pairs
            if len(chosen) >= 2:
                interaction_graph.record_interaction(
                    chosen[0], chosen[1],
                    delta_improvement=0.10 if is_rollback else 0.88,
                    identity_preserved=0.80,
                    survived_together=not is_rollback
                )

            # Add to territory
            territory.add_session_to_territory(session)

            # End of window snapshot
            if (idx + 1) % window_size == 0 or idx == n_sessions - 1:
                w_idx = len(window_metrics) + 1
                w_clusters = territory.discover_territories(min_cluster_size=2)

                # Herfindahl-Hirschman index of techniques in window
                tot_uses = sum(curr_window_techniques.values()) or 1
                shares = [c / tot_uses for c in curr_window_techniques.values()]
                hhi = round(sum(s ** 2 for s in shares), 4)

                tot_m = sum(curr_window_modes.values()) or 1
                m_ratios = {k: round(v / tot_m, 3) for k, v in curr_window_modes.items()}

                top_t = sorted(curr_window_techniques.items(), key=lambda x: x[1], reverse=True)[:3]

                step_dists = [
                    territory.calculate_distance(territory.points[j], territory.points[j + 1])
                    for j in range(max(0, idx - window_size), idx)
                ]
                avg_step = round(sum(step_dists) / len(step_dists), 4) if step_dists else 0.0

                window_metrics.append(WindowMetric(
                    window_index=w_idx,
                    session_start=max(0, idx - window_size + 1),
                    session_end=idx + 1,
                    cluster_count=len(w_clusters),
                    average_step_distance=avg_step,
                    governor_mode_ratios=m_ratios,
                    top_techniques=[t[0] for t in top_t],
                    herfindahl_index=hhi
                ))

                # Reset window counters
                curr_window_modes = {"EXPLORE": 0, "ANCHOR": 0, "EVOLVE": 0}
                curr_window_techniques = {t: 0 for t in cls.TECHNIQUE_CATALOG}

        # Long-Horizon Analysis
        elapsed_sec = round(time.time() - start_time, 2)
        total_clusters = len(territory.discover_territories(min_cluster_size=2))
        temporal_eval = territory.track_temporal_evolution(window_size=min(50, n_sessions // 4))

        # Check for Meta-Cliché / Periodic cycle in governor states
        is_periodic, cycle_period = cls._detect_periodic_limit_cycle(mode_history)

        # Global mode distribution
        tot_modes = len(mode_history)
        global_modes = {
            "EXPLORE": round(mode_history.count("EXPLORE") / tot_modes, 3),
            "ANCHOR": round(mode_history.count("ANCHOR") / tot_modes, 3),
            "EVOLVE": round(mode_history.count("EVOLVE") / tot_modes, 3)
        }

        # Determine Asymptotic Evolution Verdict
        if is_periodic:
            asymptotic_verdict = "META_CLICHE_DETECTED_PERIODIC_OSCILLATION"
        elif total_clusters >= 6 and temporal_eval["centroid_drift"] >= 0.20:
            asymptotic_verdict = "HEALTHY_OPEN_ENDED_EVOLUTION"
        elif total_clusters >= 3:
            asymptotic_verdict = "STABLE_MULTI_TERRITORY_ATTRACTOR"
        else:
            asymptotic_verdict = "PREMATURE_CONVERGENCE_TRAP"

        return {
            "status": "LONG_HORIZON_SIMULATION_COMPLETED",
            "total_sessions": n_sessions,
            "elapsed_seconds": elapsed_sec,
            "discovered_territories_count": total_clusters,
            "centroid_drift": temporal_eval["centroid_drift"],
            "evolutionary_velocity": temporal_eval["evolutionary_velocity"],
            "global_governor_modes": global_modes,
            "is_governor_meta_cliche_detected": is_periodic,
            "periodic_cycle_period": cycle_period,
            "asymptotic_verdict": asymptotic_verdict,
            "window_snapshots": [
                {
                    "window": w.window_index,
                    "sessions": f"{w.session_start}-{w.session_end}",
                    "clusters": w.cluster_count,
                    "herfindahl_index": w.herfindahl_index,
                    "modes": w.governor_mode_ratios,
                    "top_techniques": w.top_techniques
                }
                for w in window_metrics
            ]
        }

    @classmethod
    def _detect_periodic_limit_cycle(cls, sequence: List[str], max_period: int = 12) -> Tuple[bool, Optional[int]]:
        """
        Checks if the tail of the sequence repeats a fixed cycle with period p <= max_period.
        Detects if the Governor fell into an invariant mechanical loop.
        """
        if len(sequence) < 20:
            return (False, None)

        tail_len = min(60, len(sequence))
        tail = sequence[-tail_len:]
        for p in range(2, max_period + 1):
            pattern = tail[:p]
            if len(set(pattern)) <= 1:
                # Monotonous constant sequence is not a multi-state limit cycle
                continue
            reconstructed = (pattern * (len(tail) // p + 1))[:len(tail)]
            matches = sum(1 for a, b in zip(tail, reconstructed) if a == b)
            if matches / len(tail) >= 0.95:
                return (True, p)

        return (False, None)
