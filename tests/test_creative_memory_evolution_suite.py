"""
Test Suite: Fase 5 — Creative Memory & Evolution Engine
Verifies:
1. Exploration Budget (ExplorationPolicy & epsilon-greedy mechanism trials)
2. Mechanism Interaction Graph (Synergy vs Destructive Interference)
3. Creative Regret Tracker (Rollback rates, novelty band analysis, false positives)
4. Territory Clusters & Temporal Evolution (Centroid drift, stagnation detection)
5. Flexible Narrative Priors (Canonical, Inverted Hook, Modular Ambient)
6. Trimodal Creative Governor (EXPLORE, ANCHOR, EVOLVE operational modes)
"""

import os
import tempfile
import pytest

from engine.creative.creative_yield import CreativeYieldTracker, ExplorationPolicy
from engine.creative.mechanism_interaction_graph import MechanismInteractionGraph
from engine.creative.creative_regret import CreativeRegretTracker
from engine.creative.corpus_territory import CorpusTerritory, TerritoryPoint, TerritoryCluster
from engine.creative.music_identity import MusicIdentity, NARRATIVE_ARC_PROFILES
from engine.creative.creative_governor import CreativeGovernor
from engine.sound.timbre_dna import TimbreDNA


# ==============================================================================
# 1. Exploration Budget & Epsilon-Greedy Policy Tests
# ==============================================================================

class TestExplorationBudget:
    def test_exploration_policy_decisions(self):
        policy = ExplorationPolicy(exploration_rate=0.25, seed=42)
        decisions = [policy.decide_strategy() for _ in range(100)]
        explore_count = decisions.count("EXPLORE")
        exploit_count = decisions.count("EXPLOIT")

        assert explore_count + exploit_count == 100
        assert 15 <= explore_count <= 35  # Near 25%
        assert 0.15 <= policy.empirical_exploration_ratio <= 0.35

    def test_exploration_budget_modulates_low_yield_technique(self):
        tracker = CreativeYieldTracker(storage_path="", exploration_rate=0.20)

        # Heavily penalize a technique with multiple failures
        for _ in range(5):
            tracker.record_mechanism_application(
                technique_name="risky_flanger",
                delta_improvement=0.10,
                identity_preserved=0.20,
                survived_in_final_mix=False
            )

        assert tracker.get_yield("risky_flanger") < 0.10
        base_prob = 0.30

        # Normal exploit mode penalizes probability
        prob_exploit, mode_exploit = tracker.modulate_probability_with_budget(
            "risky_flanger", base_prob, force_exploit=True
        )
        # In EXPLORE mode, penalty is lifted to give technique an empirical trial
        prob_explore, mode_explore = tracker.modulate_probability_with_budget(
            "risky_flanger", base_prob, force_explore=True
        )

        assert mode_exploit == "EXPLOIT"
        assert mode_explore == "EXPLORE"
        assert prob_explore >= 0.45
        assert prob_exploit < base_prob
        assert prob_explore > prob_exploit


# ==============================================================================
# 2. Mechanism Interaction Graph Tests
# ==============================================================================

class TestMechanismInteractionGraph:
    def test_record_and_calculate_creative_synergy(self):
        graph = MechanismInteractionGraph(storage_path="")
        yield_tracker = CreativeYieldTracker(storage_path="")

        # Technique A alone has modest yield (0.40)
        for _ in range(3):
            yield_tracker.record_mechanism_application("foley_bed", 0.60, 0.70, True)

        # Technique B alone has modest yield (0.40)
        for _ in range(3):
            yield_tracker.record_mechanism_application("polyrhythm_3_16", 0.60, 0.70, True)

        # Combined together: exceptional perceptual synergy (0.85 improvement, 0.95 identity, 100% survival)
        for _ in range(4):
            graph.record_interaction(
                tech_a="foley_bed",
                tech_b="polyrhythm_3_16",
                delta_improvement=0.95,
                identity_preserved=0.95,
                survived_together=True
            )

        synergy_eval = graph.calculate_synergy("foley_bed", "polyrhythm_3_16", yield_tracker)
        assert synergy_eval["status"] == "CREATIVE_SYNERGY"
        assert synergy_eval["synergy"] > 0.10
        assert synergy_eval["pair_yield"] > synergy_eval["expected_yield"]

    def test_detect_destructive_interference(self):
        graph = MechanismInteractionGraph(storage_path="")
        yield_tracker = CreativeYieldTracker(storage_path="")

        # Both individually perform well
        for _ in range(3):
            yield_tracker.record_mechanism_application("heavy_distortion", 0.75, 0.80, True)
            yield_tracker.record_mechanism_application("sub_bass_glide", 0.75, 0.80, True)

        # Together they cause sonic mud and get rolled back / stripped
        for _ in range(4):
            graph.record_interaction(
                tech_a="heavy_distortion",
                tech_b="sub_bass_glide",
                delta_improvement=0.15,
                identity_preserved=0.30,
                survived_together=False
            )

        synergy_eval = graph.calculate_synergy("heavy_distortion", "sub_bass_glide", yield_tracker)
        assert synergy_eval["status"] == "DESTRUCTIVE_INTERFERENCE"
        assert synergy_eval["synergy"] < -0.15

        conflicts = graph.get_destructive_interferences(yield_tracker=yield_tracker)
        assert any(
            ("heavy_distortion" in (c["tech_a"], c["tech_b"]) and
             "sub_bass_glide" in (c["tech_a"], c["tech_b"]))
            for c in conflicts
        )

    def test_get_best_synergies(self):
        graph = MechanismInteractionGraph(storage_path="")
        for _ in range(3):
            graph.record_interaction("lead_resample", "reverse_verb", 0.9, 0.9, True)
            graph.record_interaction("lead_resample", "filter_sweep", 0.6, 0.7, True)
            graph.record_interaction("lead_resample", "bitcrush", 0.2, 0.3, False)

        best = graph.get_best_synergies("lead_resample")
        assert len(best) >= 2
        assert best[0]["partner"] == "reverse_verb"

    def test_interaction_persistence(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            graph_a = MechanismInteractionGraph(storage_path=tmp_path)
            graph_a.record_interaction("tape_saturation", "chorus_spread", 0.8, 0.85, True)
            graph_a.save()

            graph_b = MechanismInteractionGraph(storage_path=tmp_path)
            rec = graph_b.get_pair_record("chorus_spread", "tape_saturation")  # Order invariant
            assert rec is not None
            assert rec.co_invocations == 1
            assert rec.survived_together == 1
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


# ==============================================================================
# 3. Creative Regret Tracker Tests
# ==============================================================================

class TestCreativeRegretTracker:
    def test_record_event_and_regret_rate(self):
        tracker = CreativeRegretTracker(storage_path="")
        # 3 successes, 2 rollbacks
        tracker.record_event("polyrhythm", novelty_score=0.40, was_rolled_back=False)
        tracker.record_event("polyrhythm", novelty_score=0.45, was_rolled_back=False)
        tracker.record_event("polyrhythm", novelty_score=0.50, was_rolled_back=False)
        tracker.record_event("polyrhythm", novelty_score=0.75, was_rolled_back=True, rollback_reason="Coherence breach")
        tracker.record_event("polyrhythm", novelty_score=0.80, was_rolled_back=True, rollback_reason="Identity lost")

        assert tracker.get_regret_rate() == 0.40
        assert tracker.get_regret_rate("polyrhythm") == 0.40

    def test_regret_by_novelty_band(self):
        tracker = CreativeRegretTracker(storage_path="")
        # Low novelty: 0 rollbacks out of 3
        tracker.record_event("t1", novelty_score=0.20, was_rolled_back=False)
        tracker.record_event("t1", novelty_score=0.30, was_rolled_back=False)
        # High novelty: 2 rollbacks out of 2
        tracker.record_event("t2", novelty_score=0.70, was_rolled_back=True)
        tracker.record_event("t2", novelty_score=0.80, was_rolled_back=True)

        bands = tracker.get_regret_by_novelty_band()
        assert bands["low_novelty"]["total_events"] == 2
        assert bands["low_novelty"]["regret_rate"] == 0.0
        assert bands["high_novelty"]["total_events"] == 2
        assert bands["high_novelty"]["regret_rate"] == 1.0

    def test_false_positive_candidates(self):
        tracker = CreativeRegretTracker(storage_path="")
        for _ in range(4):
            tracker.record_event("random_pitch_morph", novelty_score=0.90, was_rolled_back=True, rollback_reason="Dissonance")

        report = tracker.get_regret_report()
        assert report["status"] == "REGRET_AUDITED"
        candidates = report["false_positive_candidates"]
        assert len(candidates) == 1
        assert candidates[0]["technique"] == "random_pitch_morph"
        assert candidates[0]["regret_rate"] == 1.0


# ==============================================================================
# 4. Territory Clusters & Temporal Evolution Tests
# ==============================================================================

class TestTerritoryClustersAndTemporalEvolution:
    def test_discover_territories(self):
        territory = CorpusTerritory(storage_path="")
        territory.clear()

        # Cluster 1: Melodic Techno (BPM 124, F# minor)
        for i in range(4):
            territory.add_session_to_territory({
                "name": f"Techno_{i}",
                "genre": "techno",
                "bpm": 124.0,
                "tonal_center": "F#",
                "mode": "Minor",
                "tracks": [{"role": "LEAD", "timbre_dna": TimbreDNA(brightness=0.7, roughness=0.3).to_dict()}]
            })

        # Cluster 2: Organic Ambient (BPM 90, C major)
        for i in range(4):
            territory.add_session_to_territory({
                "name": f"Ambient_{i}",
                "genre": "ambient",
                "bpm": 90.0,
                "tonal_center": "C",
                "mode": "Major",
                "tracks": [{"role": "LEAD", "timbre_dna": TimbreDNA(brightness=0.3, roughness=0.1).to_dict()}]
            })

        clusters = territory.discover_territories(min_cluster_size=3, max_radius=0.30)
        assert len(clusters) == 2
        cluster_genres = [c.centroid_point.genre for c in clusters]
        assert "techno" in cluster_genres
        assert "ambient" in cluster_genres

    def test_find_closest_cluster(self):
        territory = CorpusTerritory(storage_path="")
        territory.clear()

        for i in range(3):
            territory.add_session_to_territory({"name": f"House_{i}", "genre": "house", "bpm": 126.0, "tonal_center": "A", "mode": "Minor"})

        candidate = {"name": "Candidate", "genre": "house", "bpm": 125.0, "tonal_center": "A", "mode": "Minor"}
        result = territory.find_closest_cluster(candidate)
        assert result is not None
        closest_cluster, dist = result
        assert dist < 0.20
        assert "house" in closest_cluster.centroid_point.genre.lower()

    def test_track_temporal_evolution(self):
        territory = CorpusTerritory(storage_path="")
        territory.clear()

        # Early cohort: 120 BPM, C Major
        for i in range(4):
            territory.add_session_to_territory({"name": f"Early_{i}", "genre": "house", "bpm": 120.0, "tonal_center": "C", "mode": "Major"})

        # Late cohort: 140 BPM, F# Minor (Significant drift)
        for i in range(4):
            territory.add_session_to_territory({"name": f"Late_{i}", "genre": "trance", "bpm": 140.0, "tonal_center": "F#", "mode": "Minor"})

        evolution = territory.track_temporal_evolution(window_size=3)
        assert evolution["status"] == "EVOLUTION_TRACKED"
        assert evolution["centroid_drift"] >= 0.20
        assert evolution["evolutionary_velocity"] in ("EVOLVING", "EXPANDING")

    def test_detect_territorial_stagnation(self):
        territory = CorpusTerritory(storage_path="")
        territory.clear()

        # Generate 10 consecutive sessions in the exact same cluster
        for i in range(10):
            territory.add_session_to_territory({
                "name": f"Stagnant_{i}",
                "genre": "techno",
                "bpm": 124.0,
                "tonal_center": "F#",
                "mode": "Minor",
                "tracks": [{"role": "LEAD", "timbre_dna": TimbreDNA(brightness=0.7, roughness=0.3).to_dict()}]
            })

        stagnation = territory.detect_territorial_stagnation(window=8, max_dwell_ratio=0.70)
        assert stagnation["is_stagnant"] is True
        assert stagnation["dwell_ratio"] >= 0.70
        assert "Estancamiento territorial detectado" in stagnation["warning"]
        assert stagnation["recommendation"] is not None


# ==============================================================================
# 5. Flexible Narrative Priors Tests
# ==============================================================================

class TestFlexibleNarrativePriors:
    def test_canonical_arc_default(self):
        ident = MusicIdentity()
        ident.record_motif_exposure("melodic", "Intro", was_transformed=False)
        ident.record_motif_exposure("melodic", "Verse", was_transformed=False)
        ident.record_motif_exposure("melodic", "Build", was_transformed=True)
        ident.record_motif_exposure("melodic", "Drop", was_transformed=True)

        audit = ident.audit_narrative_evolution("melodic", arc_profile="canonical")
        assert audit["verdict"] == "CANONICAL_NARRATIVE_ARC"
        assert audit["arc_profile"] == "canonical"

    def test_inverted_hook_arc(self):
        # Inverted Hook: Starts with mutated hook teaser (A') in Intro, then anchored (A) in Verse
        ident = MusicIdentity()
        ident.record_motif_exposure("melodic", "Intro", was_transformed=True)   # Hook teaser
        ident.record_motif_exposure("melodic", "Verse", was_transformed=False)  # Anchoring
        ident.record_motif_exposure("melodic", "Build", was_transformed=True)   # Variation
        ident.record_motif_exposure("melodic", "Drop", was_transformed=False)   # Full hook literal
        ident.record_motif_exposure("melodic", "Break", was_transformed=True)   # Reinterpretation
        ident.record_motif_exposure("melodic", "Final Drop", was_transformed=True)

        audit = ident.audit_narrative_evolution("melodic", arc_profile="inverted_hook")
        assert audit["verdict"] == "INVERTED_HOOK_ARC_COMPLIANT"
        assert audit["is_narrative_compliant"] is True
        assert audit["narrative_score"] == 1.0

    def test_modular_ambient_arc(self):
        # Modular Ambient: A -> A' -> A -> A'' -> A''' -> A (periodic return to anchor)
        ident = MusicIdentity()
        ident.record_motif_exposure("melodic", "Intro", was_transformed=False)
        ident.record_motif_exposure("melodic", "PartA", was_transformed=True)
        ident.record_motif_exposure("melodic", "PartB", was_transformed=False)
        ident.record_motif_exposure("melodic", "PartC", was_transformed=True)
        ident.record_motif_exposure("melodic", "PartD", was_transformed=True)
        ident.record_motif_exposure("melodic", "Outro", was_transformed=False)

        audit = ident.audit_narrative_evolution("melodic", arc_profile="modular_ambient")
        assert audit["verdict"] == "MODULAR_AMBIENT_ARC_COMPLIANT"
        assert audit["is_narrative_compliant"] is True


# ==============================================================================
# 6. Trimodal Creative Governor Tests
# ==============================================================================

class TestTrimodalCreativeGovernor:
    def test_governor_explore_mode_triggered_by_stagnation(self):
        territory = CorpusTerritory(storage_path="")
        territory.clear()
        governor = CreativeGovernor(territory=territory)

        # 10 identical sessions trigger territorial stagnation
        for i in range(10):
            territory.add_session_to_territory({
                "name": f"Session_{i}",
                "genre": "techno",
                "bpm": 124.0,
                "tonal_center": "F#",
                "mode": "Minor",
                "tracks": [{"role": "LEAD", "timbre_dna": TimbreDNA().to_dict()}]
            })

        candidate = {
            "name": "Next_Candidate",
            "genre": "techno",
            "bpm": 124.0,
            "tonal_center": "F#",
            "mode": "Minor",
            "tracks": [{"role": "LEAD", "timbre_dna": TimbreDNA().to_dict()}]
        }

        mode_eval = governor.determine_governor_mode(candidate)
        assert mode_eval["mode"] == "EXPLORE"
        assert "Presupuesto de exploración activo" in mode_eval["reason"]

        guidance = governor.guide_music_director(candidate)
        assert guidance["governor_mode"] == "EXPLORE"
        assert guidance["strategy"] == "EXPLORE_NOVELTY"

    def test_governor_anchor_mode_triggered_by_fragile_identity_or_high_regret(self):
        territory = CorpusTerritory(storage_path="")
        territory.clear()
        regret_tracker = CreativeRegretTracker(storage_path="")
        governor = CreativeGovernor(territory=territory, regret_tracker=regret_tracker)

        # High regret in extreme novelty band
        for _ in range(4):
            regret_tracker.record_event("risky_technique", novelty_score=0.90, was_rolled_back=True)

        session = {
            "name": "Chaos_Risk",
            "genre": "experimental",
            "bpm": 160.0,
            "music_identity": {"melodic_motif": {}, "rhythmic_motif": {}},
            "tracks": []  # Empty identity
        }

        mode_eval = governor.determine_governor_mode(session)
        assert mode_eval["mode"] == "ANCHOR"
        assert "Preservar y estabilizar anclas de identidad" in mode_eval["reason"]

    def test_governor_evolve_mode_in_healthy_territory(self):
        territory = CorpusTerritory(storage_path="")
        territory.clear()
        governor = CreativeGovernor(territory=territory)

        # Seed moderate territory (3 diverse songs)
        territory.add_session_to_territory({"name": "S1", "genre": "house", "bpm": 124.0})
        territory.add_session_to_territory({"name": "S2", "genre": "techno", "bpm": 128.0})
        territory.add_session_to_territory({"name": "S3", "genre": "breakbeat", "bpm": 132.0})

        healthy_session = {
            "name": "Balanced_Track",
            "genre": "techno",
            "bpm": 126.0,
            "tonal_center": "D",
            "mode": "Minor",
            "tracks": [
                {"name": "Lead", "role": "LEAD", "has_leitmotif": True, "timbre_dna": TimbreDNA().to_dict()},
                {"name": "Drums", "role": "DRUMS", "groove_cell": "syncopated_16th", "notes_count": 32},
                {"name": "Texture", "role": "TEXTURE_FOLEY"}
            ],
            "spatial_energy_curve": [{"stereo_width": 0.2}, {"stereo_width": 1.2}],
            "sections": [{"name": "buildup", "is_pre_drop_transition": True}]
        }

        mode_eval = governor.determine_governor_mode(healthy_session)
        assert mode_eval["mode"] == "EVOLVE"
        assert "Evolución armónica" in mode_eval["reason"]

    def test_governor_recommends_synergies_and_detects_conflicts(self):
        interaction_graph = MechanismInteractionGraph(storage_path="")
        yield_tracker = CreativeYieldTracker(storage_path="")
        governor = CreativeGovernor(interaction_graph=interaction_graph, yield_tracker=yield_tracker)

        # Record synergy
        for _ in range(3):
            interaction_graph.record_interaction("sub_vacuum", "drop_impact", 0.95, 0.95, True)
            interaction_graph.record_interaction("sub_vacuum", "excessive_flanger", 0.1, 0.2, False)

        best_partners = governor.recommend_synergistic_pair("sub_vacuum")
        assert len(best_partners) >= 1
        assert best_partners[0]["partner"] == "drop_impact"

        assert governor.is_destructive_pair("sub_vacuum", "excessive_flanger") is True
        assert governor.is_destructive_pair("sub_vacuum", "drop_impact") is False
