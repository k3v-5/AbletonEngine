"""
Test Suite for Phase 4: Creative Governor, Territorial Corpus Space,
Dual Identity-Novelty Matrix, Creative Yield, and Narrative Evolution Law.

Includes:
1. CorpusTerritory: Multi-dimensional continuous embedding, distance, and saturation detection.
2. Identity vs Novelty Matrix: Sweet Spot (BALANCED_INNOVATION) vs REPLICA_CLICHE and CHAOTIC_NOISE.
3. CreativeYieldTracker: Empirical efficacy tracking and dynamic probability modulation.
4. NarrativeEvolutionLaw: 6-stage canonical ladder (A -> A -> A' -> A'' -> A''' -> A'''').
5. CreativeGovernor: Integration of song admission, directional guidance, and territorial expansion.
"""

import pytest
import os
import tempfile
from typing import Dict, Any, List

from engine.sound.timbre_dna import TimbreDNA
from engine.creative.music_identity import (
    MusicIdentity,
    MelodicMotif,
    IdentityAuditor,
    NarrativeStage,
    CANONICAL_NARRATIVE_LADDER
)
from engine.creative.corpus_territory import (
    CorpusTerritory,
    TerritoryPoint
)
from engine.creative.creative_yield import (
    CreativeYieldTracker,
    MechanismYieldRecord
)
from engine.creative.song_comparator import PerceptualComparator
from engine.creative.creative_governor import CreativeGovernor
from engine.production.copilot.phases.phase_10.music_director import MusicDirector


# ==============================================================================
# 1. Corpus Territory & Creative Space Tests
# ==============================================================================

class TestCorpusTerritory:
    def test_extract_and_add_territory_point(self):
        territory = CorpusTerritory(storage_path="")
        territory.clear()

        session_mock = {
            "name": "Techno Alpha",
            "genre": "melodic_techno",
            "bpm": 124.0,
            "tonal_center": "F#",
            "mode": "Dorian",
            "tracks": [
                {
                    "name": "Kick",
                    "role": "KICK",
                    "notes_count": 16,
                    "timbre_dna": TimbreDNA(brightness=0.5, roughness=0.3).to_dict()
                },
                {
                    "name": "Lead Synth",
                    "role": "LEAD",
                    "notes_count": 16,
                    "timbre_dna": TimbreDNA(brightness=0.75, roughness=0.6, stereo_width=0.75).to_dict()
                }
            ],
            "sections": [{"bars": 8}, {"bars": 8}],
            "spatial_energy_curve": [{"stereo_width": 0.15}, {"stereo_width": 1.25}]
        }

        pt = territory.add_session_to_territory(session_mock)
        assert pt.session_id == "Techno Alpha"
        assert pt.genre == "melodic_techno"
        assert pt.bpm == 124.0
        assert pt.tonal_center == "F#"
        assert pt.spatial_width_min == 0.15
        assert pt.spatial_width_max == 1.25
        assert len(territory.points) == 1

    def test_corpus_distance_and_novelty(self):
        territory = CorpusTerritory(storage_path="")
        territory.clear()

        # 1. Empty territory yields maximum novelty
        dummy_session = {"name": "First Song", "genre": "house", "bpm": 126.0}
        assert territory.calculate_corpus_distance(dummy_session) == 1.0

        # 2. Add base song to territory
        base_session = {
            "name": "Base House",
            "genre": "house",
            "bpm": 126.0,
            "tonal_center": "C",
            "mode": "Major",
            "tracks": [{"role": "LEAD", "timbre_dna": TimbreDNA(brightness=0.7, roughness=0.3).to_dict()}],
            "sections": [{"bars": 16}]
        }
        territory.add_session_to_territory(base_session)

        # 3. Near-identical session yields very low distance / novelty
        near_clone = {
            "name": "Clone House",
            "genre": "house",
            "bpm": 126.0,
            "tonal_center": "C",
            "mode": "Major",
            "tracks": [{"role": "LEAD", "timbre_dna": TimbreDNA(brightness=0.7, roughness=0.3).to_dict()}],
            "sections": [{"bars": 16}]
        }
        dist_clone = territory.calculate_corpus_distance(near_clone)
        assert dist_clone < 0.15

        # 4. Far session (Ambient, 80 BPM, F# Dorian, lush dark timbre) yields high novelty
        distant_session = {
            "name": "Dark Ambient",
            "genre": "ambient",
            "bpm": 80.0,
            "tonal_center": "F#",
            "mode": "Dorian",
            "tracks": [{"role": "LEAD", "timbre_dna": TimbreDNA(brightness=0.2, roughness=0.1, stereo_width=0.95).to_dict()}],
            "sections": [{"bars": 32}]
        }
        dist_far = territory.calculate_corpus_distance(distant_session)
        assert dist_far > 0.35
        assert dist_far > dist_clone * 2

    def test_territory_saturation_detection(self):
        territory = CorpusTerritory(storage_path="")
        territory.clear()

        # Populate territory with 5 very close sessions in the same acoustic quadrant
        for i in range(5):
            s = {
                "name": f"Deep House {i}",
                "genre": "house",
                "bpm": 124.0,
                "tonal_center": "A",
                "mode": "Minor",
                "tracks": [{"role": "LEAD", "timbre_dna": TimbreDNA(brightness=0.6, roughness=0.4).to_dict()}],
                "sections": [{"bars": 16}]
            }
            territory.add_session_to_territory(s)

        # Test another candidate in the exact same quadrant
        candidate = {
            "name": "Candidate Deep House",
            "genre": "house",
            "bpm": 124.0,
            "tonal_center": "A",
            "mode": "Minor",
            "tracks": [{"role": "LEAD", "timbre_dna": TimbreDNA(brightness=0.6, roughness=0.4).to_dict()}],
            "sections": [{"bars": 16}]
        }

        sat_audit = territory.detect_territory_saturation(candidate, radius=0.20, threshold_count=4)
        assert sat_audit["is_saturated"] is True
        assert sat_audit["neighbor_count_in_radius"] >= 4
        assert "Saturación de territorio" in sat_audit["warning"]
        assert sat_audit["recommendation"] is not None

    def test_territory_persistence(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            territory_a = CorpusTerritory(storage_path=tmp_path)
            territory_a.clear()
            territory_a.add_session_to_territory({"name": "Song 1", "genre": "techno", "bpm": 130.0})
            territory_a.add_session_to_territory({"name": "Song 2", "genre": "ambient", "bpm": 90.0})
            territory_a.save()

            territory_b = CorpusTerritory(storage_path=tmp_path)
            assert len(territory_b.points) == 2
            assert territory_b.points[0].session_id == "Song 1"
            assert territory_b.points[1].session_id == "Song 2"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


# ==============================================================================
# 2. Dual Identity-Novelty Matrix & Useful Novelty Tests
# ==============================================================================

class TestIdentityNoveltyMatrix:
    def test_sweet_spot_balanced_innovation(self):
        # Sweet Spot: Strong Identity (>= 0.60) + Healthy Novelty (0.40 - 0.85)
        res = PerceptualComparator.evaluate_identity_novelty_matrix(
            identity_score=0.82,
            novelty_score=0.65,
            coherence_score=0.85
        )
        assert res["quadrant"] == "BALANCED_INNOVATION"
        assert res["is_in_sweet_spot"] is True
        assert res["recommended_action"] == "PRESERVE_AND_PROCEED"
        assert res["useful_novelty"] > 0.60

    def test_replica_cliche_quadrant(self):
        # Cliché: High Identity but too close to corpus (Novelty < 0.40)
        res = PerceptualComparator.evaluate_identity_novelty_matrix(
            identity_score=0.90,
            novelty_score=0.20,
            coherence_score=0.90
        )
        assert res["quadrant"] == "REPLICA_CLICHE"
        assert res["is_in_sweet_spot"] is False
        assert res["recommended_action"] == "INJECT_CONTROLLED_NOVELTY"

    def test_chaotic_noise_quadrant(self):
        # Chaotic Noise: High Novelty but destroyed Identity (< 0.45)
        res = PerceptualComparator.evaluate_identity_novelty_matrix(
            identity_score=0.35,
            novelty_score=0.92,
            coherence_score=0.50
        )
        assert res["quadrant"] == "CHAOTIC_NOISE"
        assert res["is_in_sweet_spot"] is False
        assert res["recommended_action"] == "STABILIZE_IDENTITY_ANCHORS"

    def test_useful_novelty_attenuates_incoherent_novelty(self):
        # Extreme novelty (0.90) with very poor coherence (0.30)
        res = PerceptualComparator.evaluate_identity_novelty_matrix(
            identity_score=0.70,
            novelty_score=0.90,
            coherence_score=0.30  # poor coherence
        )
        # Useful novelty must be discounted: 0.90 * (0.30/0.65) * 1.0 ~= 0.415
        assert res["useful_novelty"] < 0.50
        assert res["useful_novelty"] < res["novelty_score"]


# ==============================================================================
# 3. Creative Yield Tracker Tests
# ==============================================================================

class TestCreativeYieldTracker:
    def test_high_yield_mechanism_boosts_priority(self):
        tracker = CreativeYieldTracker(storage_path="")

        # Mechanism with 100% survival, high identity preservation, and high improvement
        for _ in range(5):
            tracker.record_mechanism_application(
                technique_name="3_16_tension",
                delta_improvement=0.85,
                identity_preserved=0.90,
                survived_in_final_mix=True
            )

        yield_score = tracker.get_yield("3_16_tension")
        assert yield_score >= 0.70

        base_prob = 0.30
        modulated_prob = tracker.modulate_probability("3_16_tension", base_prob)
        assert modulated_prob > base_prob  # Priority boosted

    def test_low_yield_mechanism_penalizes_priority(self):
        tracker = CreativeYieldTracker(storage_path="")

        # Mechanism with poor survival (1 out of 5) and low improvement
        for i in range(5):
            tracker.record_mechanism_application(
                technique_name="reverse_audio_texture",
                delta_improvement=0.20,
                identity_preserved=0.60,
                survived_in_final_mix=(i == 0)  # only 1 survived
            )

        yield_score = tracker.get_yield("reverse_audio_texture")
        assert yield_score < 0.15

        base_prob = 0.40
        modulated_prob = tracker.modulate_probability("reverse_audio_texture", base_prob)
        assert modulated_prob < base_prob  # Priority penalized

    def test_yield_report_and_persistence(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            tracker_a = CreativeYieldTracker(storage_path=tmp_path)
            tracker_a.record_mechanism_application("pre_drop_vacuum", 0.9, 0.95, True)
            tracker_a.record_mechanism_application("pre_drop_vacuum", 0.85, 0.9, True)
            tracker_a.record_mechanism_application("pre_drop_vacuum", 0.8, 0.85, True)
            tracker_a.save()

            tracker_b = CreativeYieldTracker(storage_path=tmp_path)
            report = tracker_b.get_yield_report()
            assert report["status"] == "YIELD_AUDITED"
            assert report["total_tracked_mechanisms"] == 1
            assert "pre_drop_vacuum" in report["high_yield_recommendations"]
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


# ==============================================================================
# 4. Narrative Evolution Law (6 Stages) Tests
# ==============================================================================

class TestNarrativeEvolutionLaw:
    def test_canonical_ladder_compliance(self):
        """
        Validates the 6-stage canonical narrative progression:
        Intro (A, literal) -> Verse (A, literal) -> Build (A', mutated) ->
        Drop (A'', expanded) -> Break (A''', reinterpreted) -> Final Drop (A'''', integrated)
        """
        ident = MusicIdentity()
        ident.record_motif_exposure("melodic", "Intro", was_transformed=False)
        ident.record_motif_exposure("melodic", "Verse", was_transformed=False)
        ident.record_motif_exposure("melodic", "Build", was_transformed=True)
        ident.record_motif_exposure("melodic", "Drop", was_transformed=True)
        ident.record_motif_exposure("melodic", "Break", was_transformed=True)
        ident.record_motif_exposure("melodic", "Final Drop", was_transformed=True)

        audit = ident.audit_narrative_evolution("melodic")
        assert audit["status"] == "NARRATIVE_AUDITED"
        assert audit["is_narrative_compliant"] is True
        assert audit["narrative_score"] == 1.0
        assert audit["verdict"] == "CANONICAL_NARRATIVE_ARC"

    def test_premature_mutation_flagged(self):
        """Mutating prematurely in the first 2 sections breaches narrative anchoring."""
        ident = MusicIdentity()
        ident.record_motif_exposure("melodic", "Intro", was_transformed=True)
        ident.record_motif_exposure("melodic", "Verse", was_transformed=True)
        ident.record_motif_exposure("melodic", "Build", was_transformed=True)

        audit = ident.audit_narrative_evolution("melodic")
        assert audit["verdict"] == "PREMATURE_MUTATION"
        assert audit["is_narrative_compliant"] is False

    def test_static_repetition_flagged(self):
        """Failing to evolve after anchoring flags static repetition."""
        ident = MusicIdentity()
        ident.record_motif_exposure("melodic", "Intro", was_transformed=False)
        ident.record_motif_exposure("melodic", "Verse", was_transformed=False)
        ident.record_motif_exposure("melodic", "Build", was_transformed=False)
        ident.record_motif_exposure("melodic", "Drop", was_transformed=False)

        audit = ident.audit_narrative_evolution("melodic")
        assert audit["verdict"] == "STATIC_REPETITION"
        assert audit["narrative_score"] == 0.50  # 2 compliant (Intro, Verse), 2 stalled


# ==============================================================================
# 5. Creative Governor Integration Tests
# ==============================================================================

class TestCreativeGovernorIntegration:
    def test_governor_assesses_session_admission(self):
        governor = CreativeGovernor(territory=CorpusTerritory(storage_path=""))
        governor.territory.clear()

        # Session 1: High identity, high coherence, empty territory -> Admitted as new territory
        session_valid = {
            "name": "New World Techno",
            "tracks": [
                {"name": "Kick", "role": "KICK", "notes": [{"pitch": 36, "is_out_of_scale": False}]},
                {"name": "Snare", "role": "SNARE", "notes": [{"pitch": 38, "is_out_of_scale": False}]},
                {"name": "Bass", "role": "BASS", "notes": [{"pitch": 36, "is_out_of_scale": False}]},
                {"name": "Lead", "role": "LEAD", "notes": [{"pitch": 60, "is_out_of_scale": False}]}
            ],
            "sections": [{"name": "Intro"}, {"name": "Drop"}],
            "music_identity": MusicIdentity().to_dict()
        }

        assessment = governor.assess_session_admission(session_valid)
        assert assessment["status"] == "GOVERNANCE_AUDITED"
        assert assessment["admitted"] is True
        assert assessment["verdict"] == "ADMITTED_AS_NEW_TERRITORY"

        # Commit it to territory
        governor.commit_session(session_valid)
        assert len(governor.territory.points) == 1

    def test_governor_guides_music_director_strategy(self):
        governor = CreativeGovernor(territory=CorpusTerritory(storage_path=""))
        governor.territory.clear()

        # Populate with 4 close sessions
        for i in range(4):
            governor.territory.add_session_to_territory({
                "name": f"Club Track {i}",
                "genre": "melodic_techno",
                "bpm": 124.0,
                "tonal_center": "F#",
                "mode": "Dorian",
                "tracks": [{"role": "LEAD", "timbre_dna": TimbreDNA().to_dict()}]
            })

        # Test candidate in the same cluster
        similar_session = {
            "name": "Club Track 5",
            "genre": "melodic_techno",
            "bpm": 124.0,
            "tonal_center": "F#",
            "mode": "Dorian",
            "tracks": [{"role": "LEAD", "timbre_dna": TimbreDNA().to_dict()}]
        }

        guidance = governor.guide_music_director(similar_session)
        assert guidance["strategy"] == "EXPLORE_NOVELTY"
        assert "C" in guidance["preferred_candidates"] or "E" in guidance["preferred_candidates"]

    def test_music_director_uses_corpus_territory_in_ab_evaluation(self):
        territory = CorpusTerritory(storage_path="")
        territory.clear()
        territory.add_session_to_territory({"name": "Historic 1", "genre": "house", "bpm": 124.0})

        session_mock = type("MockSession", (), {
            "data": {
                "tracks": [
                    {"name": "Kick", "role": "KICK", "notes_count": 16, "notes": [{"pitch": 36, "is_out_of_scale": False}]},
                    {"name": "Snare", "role": "SNARE", "notes_count": 16, "notes": [{"pitch": 38, "is_out_of_scale": False}]},
                    {"name": "Bass", "role": "BASS", "notes_count": 16, "notes": [{"pitch": 36, "is_out_of_scale": False}]},
                    {"name": "Lead", "role": "LEAD", "notes_count": 16, "notes": [{"pitch": 60, "is_out_of_scale": False}]}
                ],
                "sections": [
                    {"name": "Verse", "bars": 8, "energy": 0.4},
                    {"name": "Chorus", "bars": 8, "energy": 0.45}
                ],
                "corpus_territory": territory,
                "music_director_history": []
            },
            "_save_state": lambda *args, **kwargs: None
        })()

        res = MusicDirector.evaluate_ab_mutations(session_mock)
        assert "all_candidates" in res
        for cand in res["all_candidates"]:
            if not cand.get("rejected_by_guardrail"):
                assert "useful_novelty" in cand
                assert "corpus_novelty" in cand
