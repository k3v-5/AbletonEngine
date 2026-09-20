"""
Test Suite for Phase 3: Empirical Creative Calibration, Multi-dimensional Perceptual Comparison,
and Emergent Behavior Auditing.

Includes:
1. PerceptualComparator: Multi-dimensional similarity (7 axes) and Aesthetic Monotony detection.
2. Contextual Mechanism Classification: HARD rules exempt from false alarms, OPTIONAL rules audited.
3. Memory Anchor Model & Continuous development_index in MusicIdentity.
4. EmpiricalCalibrationRunner: Multi-genre cohort simulation, rollback hotspots, and calibration reporting.
"""

import pytest
import math
from typing import Dict, Any, List

from engine.sound.timbre_dna import TimbreDNA
from engine.creative.music_identity import (
    MusicIdentity,
    MelodicMotif,
    RhythmicMotif,
    TimbreMotif,
    SpatialMotif,
    TextureMotif,
    TransitionMotif,
    IdentityAuditor
)
from engine.creative.song_comparator import (
    PerceptualComparator,
    SongComparison
)
from engine.creative.corpus_evaluator import (
    CreativeCorpusEvaluator,
    MechanismCategory
)
from engine.creative.empirical_calibration import (
    EmpiricalCalibrationRunner,
    SimulatedSession
)


# ==============================================================================
# 1. Perceptual Comparator & Aesthetic Monotony Tests
# ==============================================================================

class TestPerceptualComparator:
    def test_detects_aesthetic_monotony_different_notes_identical_dna(self):
        """
        Detects the subtle internal cliché:
        Two songs have completely different notes and melodies, but share an identical
        timbral aesthetic (timbral_similarity >= 0.88).
        """
        # Session A: Lead notes in C Major Scale
        session_a = {
            "name": "Song Alpha",
            "song_title": "Song Alpha",
            "tonal_center": "C",
            "mode": "Major",
            "tracks": [
                {
                    "name": "Lead Synth",
                    "role": "LEAD",
                    "notes": [{"pitch": p} for p in (60, 64, 67, 72)],  # C, E, G, C
                    "timbre_dna": TimbreDNA(brightness=0.75, roughness=0.60, stereo_width=0.70).to_dict()
                },
                {
                    "name": "Bass",
                    "role": "BASS",
                    "notes": [{"pitch": 36}],
                    "timbre_dna": TimbreDNA(brightness=0.40, roughness=0.50).to_dict()
                }
            ],
            "sections": [{"name": "Verse"}, {"name": "Drop"}],
            "music_identity": {"melodic_motif": {"intervals": [4, 3, 5]}}
        }

        # Session B: Lead notes in F# Minor Pentatonic (completely different pitch set)
        session_b = {
            "name": "Song Beta",
            "song_title": "Song Beta",
            "tonal_center": "F#",
            "mode": "Minor",
            "tracks": [
                {
                    "name": "Lead Synth",
                    "role": "LEAD",
                    "notes": [{"pitch": p} for p in (66, 69, 71, 73)],  # F#, A, B, C#
                    # Exactly identical sound aesthetic / TimbreDNA!
                    "timbre_dna": TimbreDNA(brightness=0.75, roughness=0.60, stereo_width=0.70).to_dict()
                },
                {
                    "name": "Bass",
                    "role": "BASS",
                    "notes": [{"pitch": 42}],
                    "timbre_dna": TimbreDNA(brightness=0.40, roughness=0.50).to_dict()
                }
            ],
            "sections": [{"name": "Verse"}, {"name": "Drop"}],
            "music_identity": {"melodic_motif": {"intervals": [3, 2, 2]}}
        }

        comparison = PerceptualComparator.compare_sessions(session_a, session_b)
        assert comparison.perceptual_verdict == "AESTHETICALLY_MONOTONOUS"
        assert comparison.timbral_similarity >= 0.88
        assert comparison.melodic_similarity < 0.60

        # Verify batch audit identifies the monotonous pair
        batch_audit = PerceptualComparator.audit_aesthetic_monotony([session_a, session_b])
        assert batch_audit["monotony_risk"] is True
        assert batch_audit["flagged_pairs_count"] == 1
        assert batch_audit["flagged_pairs"][0]["song_a"] == "Song Alpha"
        assert batch_audit["flagged_pairs"][0]["song_b"] == "Song Beta"

    def test_detects_distinct_songs_across_genres(self):
        """Two songs with different composition and different timbral profiles are DISTINCT_SONG."""
        ambient_session = {
            "name": "Deep Ambient",
            "tonal_center": "D",
            "mode": "Major",
            "tracks": [
                {
                    "name": "Lush Pad",
                    "role": "LEAD",
                    "notes": [{"pitch": 62}, {"pitch": 66}],
                    "timbre_dna": TimbreDNA(brightness=0.30, roughness=0.10, stereo_width=0.95, transient_strength=0.15).to_dict()
                }
            ],
            "sections": [{"name": "Intro"}, {"name": "Floating"}, {"name": "Outro"}]
        }

        dnb_session = {
            "name": "Neurofunk DnB",
            "tonal_center": "F#",
            "mode": "Minor",
            "tracks": [
                {
                    "name": "Reese Lead",
                    "role": "LEAD",
                    "notes": [{"pitch": 54}, {"pitch": 55}, {"pitch": 57}],
                    "timbre_dna": TimbreDNA(brightness=0.90, roughness=0.85, stereo_width=0.60, transient_strength=0.90).to_dict()
                },
                {
                    "name": "A violent break",
                    "role": "DRUMS",
                    "notes_count": 32
                }
            ],
            "sections": [{"name": "Buildup"}, {"name": "Drop 1"}, {"name": "Drop 2"}]
        }

        comp = PerceptualComparator.compare_sessions(ambient_session, dnb_session)
        assert comp.perceptual_verdict == "DISTINCT_SONG"
        assert comp.composite_similarity < 0.55
        assert comp.timbral_similarity < 0.88

    def test_detects_variation_of_same_identity(self):
        """Two sessions sharing the same core identity and motifs are VARIATION_OF_SAME_IDENTITY."""
        motif_mel = MelodicMotif(intervals=[2, 2, 1, 2], root_pitch=60)
        ident_core = MusicIdentity(tonal_center="A", mode="Minor", melodic_motif=motif_mel)

        session_original = {
            "name": "Original Version",
            "tonal_center": "A",
            "mode": "Minor",
            "tracks": [
                {
                    "name": "Lead",
                    "role": "LEAD",
                    "notes": [{"pitch": 60}, {"pitch": 62}, {"pitch": 64}],
                    "timbre_dna": TimbreDNA(brightness=0.70).to_dict()
                }
            ],
            "sections": [{"name": "Intro"}, {"name": "Drop"}],
            "music_identity": ident_core.to_dict()
        }

        session_club_mix = {
            "name": "Extended Club Mix",
            "tonal_center": "A",
            "mode": "Minor",
            "tracks": [
                {
                    "name": "Lead",
                    "role": "LEAD",
                    "notes": [{"pitch": 60}, {"pitch": 62}, {"pitch": 64}],
                    "timbre_dna": TimbreDNA(brightness=0.70).to_dict()
                },
                {
                    "name": "Extra Percussion",
                    "role": "PERCUSSION",
                    "notes_count": 16
                }
            ],
            "sections": [{"name": "Extended Intro"}, {"name": "Build"}, {"name": "Drop"}, {"name": "Outro"}],
            "music_identity": ident_core.to_dict()
        }

        comp = PerceptualComparator.compare_sessions(session_original, session_club_mix)
        assert comp.perceptual_verdict == "VARIATION_OF_SAME_IDENTITY"
        assert comp.motif_similarity >= 0.70
        assert comp.harmonic_similarity >= 0.75

    def test_detects_identical_sessions(self):
        session = {
            "name": "Master Track",
            "tonal_center": "F#",
            "mode": "Dorian",
            "tracks": [{"name": "Kick", "role": "KICK", "notes": [{"pitch": 36}]}],
            "sections": [{"name": "Drop"}]
        }
        comp = PerceptualComparator.compare_sessions(session, session)
        assert comp.perceptual_verdict == "IDENTICAL"
        assert comp.composite_similarity >= 0.95


# ==============================================================================
# 2. Contextual Mechanism Classification Tests
# ==============================================================================

class TestContextualMechanismClassification:
    def test_hard_rules_exempt_from_cliche_alarms(self):
        """
        A HARD canonical rule (e.g. pre_drop_vacuum or metric_anchor_4_4) used in 95%
        of sessions MUST NOT trigger an internal cliché alarm.
        """
        corpus = []
        for i in range(20):
            # 19 out of 20 sessions have pre-drop stereo collapse / vacuum (95% frequency)
            has_vacuum = (i < 19)
            s_data = {
                "tracks": [{"name": "Kick", "role": "KICK"}],
                "sections": [{"name": "Build"}, {"name": "Drop"}],
                "spatial_energy_curve": [{"stereo_width": 0.15 if has_vacuum else 0.80}],
                "applied_mechanisms": ["pre_drop_vacuum"] if has_vacuum else []
            }
            corpus.append(s_data)

        report = CreativeCorpusEvaluator.evaluate_corpus(corpus)
        assert report["frequencies"]["pre_drop_vacuum"] == 0.95

        # Verify no cliché alarm was raised because it is a HARD rule
        alarms = [a["technique"] for a in report["cliche_alarms"]]
        assert "pre_drop_vacuum" not in alarms
        assert "pre_drop_stereo_collapse" not in alarms
        assert report["mechanism_categories"]["pre_drop_vacuum"] == "HARD"

    def test_optional_techniques_trigger_cliche_alarm_when_overused(self):
        """
        An OPTIONAL discretionary technique (e.g. reverse_audio_transition) used in 95%
        of sessions MUST trigger an internal cliché alarm.
        """
        corpus = []
        for i in range(20):
            # 19 out of 20 have reverse transitions (95% frequency)
            # 1 out of 20 has polyrhythm (5% frequency)
            has_rev = (i < 19)
            has_poly = (i < 1)
            s_data = {
                "tracks": [
                    {"name": "Reverse Swell" if has_rev else "Impact", "role": "FX"},
                    {"name": "Arp", "role": "ARP", "notes": [{"pitch": 60, "is_metric_tension": has_poly}]}
                ],
                "sections": [{"name": "Verse"}, {"name": "Drop"}],
                "music_identity": {"genealogy_log": [{"transformations": ["reverse"]}] if has_rev else []}
            }
            corpus.append(s_data)

        report = CreativeCorpusEvaluator.evaluate_corpus(corpus)
        assert report["has_internal_cliche_alarm"] is True
        alarms = [a["technique"] for a in report["cliche_alarms"]]
        assert "reverse_audio_transition" in alarms
        assert "polyrhythm_3_16" not in alarms  # 5% is below threshold

    def test_section_distribution_and_co_occurrence_matrix(self):
        """Verifies that section distribution and co-occurrence are properly tracked."""
        corpus = []
        for i in range(10):
            s_data = {
                "tracks": [
                    {"name": "Arp 3/16", "role": "ARP", "section": "Build", "notes": [{"is_metric_tension": True}]},
                    {"name": "Reverse FX", "role": "FX", "section": "Build"}
                ],
                "sections": [{"name": "Build"}, {"name": "Drop"}],
                "spatial_energy_curve": [{"stereo_width": 0.15, "section": "pre_drop"}],
                "music_identity": {"genealogy_log": [{"transformations": ["reverse"]}]}
            }
            corpus.append(s_data)

        report = CreativeCorpusEvaluator.evaluate_corpus(corpus)
        assert "section_distribution" in report
        assert "co_occurrence_matrix" in report
        assert "build" in report["section_distribution"]["polyrhythm_3_16"]
        assert report["co_occurrence_matrix"]["polyrhythm_3_16"]["reverse_audio_transition"] == 1.0

    def test_custom_mechanism_registration(self):
        """Allows registering new techniques with designated categories."""
        CreativeCorpusEvaluator.register_mechanism("experimental_sub_flutter", MechanismCategory.OPTIONAL)
        cat = CreativeCorpusEvaluator.get_mechanism_category("experimental_sub_flutter")
        assert cat == MechanismCategory.OPTIONAL

        CreativeCorpusEvaluator.register_mechanism("kick_sub_sidechain_ducking", MechanismCategory.HARD)
        cat_hard = CreativeCorpusEvaluator.get_mechanism_category("kick_sub_sidechain_ducking")
        assert cat_hard == MechanismCategory.HARD


# ==============================================================================
# 3. Memory Anchor Model & Continuous Development Index Tests
# ==============================================================================

class TestMemoryAnchorModelAndDevelopmentIndex:
    def test_anchored_evolution_outperforms_unanchored_evolution(self):
        """
        Demonstrates the Memory Anchor Model:
        Establishing the motif verbatim first (A -> A) before mutating (A' -> A'')
        anchors the idea in listener memory, achieving a higher development_index
        than mutating prematurely before recognition.
        """
        # Case 1: Anchored progression (A -> A -> A' -> A'')
        ident_anchored = MusicIdentity()
        ident_anchored.record_motif_exposure("melodic", "Intro", was_transformed=False)
        ident_anchored.record_motif_exposure("melodic", "Verse", was_transformed=False)
        ident_anchored.record_motif_exposure("melodic", "Build", was_transformed=True)
        ident_anchored.record_motif_exposure("melodic", "Drop", was_transformed=True)

        # Case 2: Unanchored premature transformation (A' -> A'' -> A -> A)
        ident_unanchored = MusicIdentity()
        ident_unanchored.record_motif_exposure("melodic", "Intro", was_transformed=True)
        ident_unanchored.record_motif_exposure("melodic", "Verse", was_transformed=True)
        ident_unanchored.record_motif_exposure("melodic", "Build", was_transformed=False)
        ident_unanchored.record_motif_exposure("melodic", "Drop", was_transformed=False)

        score_anchored = ident_anchored.get_development_index("melodic")
        score_unanchored = ident_unanchored.get_development_index("melodic")

        # Both have 2 transformations out of 4 exposures (raw = 0.50)
        # Anchored receives the 1.15x memory anchor multiplier: 0.50 * 1.15 = 0.575
        assert score_anchored == 0.575
        assert score_unanchored == 0.500
        assert score_anchored > score_unanchored

    def test_static_repetition_yields_zero_development_index(self):
        ident = MusicIdentity()
        for sec in ["Intro", "Verse", "Build", "Drop"]:
            ident.record_motif_exposure("melodic", sec, was_transformed=False)

        assert ident.get_development_index("melodic") == 0.0

    def test_identity_auditor_reports_continuous_index(self):
        ident = MusicIdentity()
        ident.record_motif_exposure("melodic", "Intro", was_transformed=False)
        ident.record_motif_exposure("melodic", "Verse", was_transformed=False)
        ident.record_motif_exposure("melodic", "Drop", was_transformed=True)

        audit = IdentityAuditor.evaluate_identity({"music_identity": ident.to_dict()})
        assert "development_index" in audit
        assert audit["development_index"] > 0.0
        assert audit["development_status"] in ("rich_evolution", "developing")


# ==============================================================================
# 4. Empirical Calibration Runner Tests
# ==============================================================================

class TestEmpiricalCalibrationRunner:
    def test_simulate_production_cohort_and_generate_report(self):
        """
        Runs an empirical multi-genre cohort study (N = 25) and verifies
        the generation of the complete Empirical Calibration Report.
        """
        study = EmpiricalCalibrationRunner.run_calibration_study(
            count=25,
            genres=["melodic_techno", "house", "afro_house", "dnb", "ambient"]
        )

        assert "cohort_summary" in study
        assert study["cohort_summary"]["total_sessions"] == 25
        assert len(study["cohort_summary"]["genres_covered"]) == 5

        report = study["calibration_report"]
        assert report["status"] == "CALIBRATION_REPORT_GENERATED"
        assert report["total_cohort_sessions"] == 25

        # 1. Convergence section
        assert "convergence" in report
        assert "cliche_alarms_count" in report["convergence"]
        assert "canonical_rules_adherence" in report["convergence"]

        # 2. Underutilization section
        assert "underutilization" in report
        assert "underutilized_count" in report["underutilization"]

        # 3. Conflicts section
        assert "conflicts" in report
        assert "rollback_rate" in report["conflicts"]
        assert "primary_conflict_hotspot" in report["conflicts"]

        # 4. Timbral aesthetics section
        assert "timbral_aesthetics" in report
        assert "aesthetic_diversity_verdict" in report["timbral_aesthetics"]
        assert report["timbral_aesthetics"]["total_pairs_tested"] > 0

        # 5. Resampling diagnostics
        assert "resampling_diagnostics" in report

        # 6. Recommended calibrations
        assert "recommended_calibrations" in report
        assert len(report["recommended_calibrations"]) > 0

    def test_cohort_tracks_conflict_hotspots(self):
        """Verifies that rollback hotspots and mutation distributions are tracked."""
        cohort = EmpiricalCalibrationRunner.simulate_production_cohort(count=15)
        assert len(cohort["sessions"]) == 15
        assert cohort["status"] == "COHORT_SIMULATED"

        report = EmpiricalCalibrationRunner.generate_calibration_report(cohort)
        conflicts = report["conflicts"]
        assert "candidate_rollbacks" in conflicts
        assert "candidate_commits" in conflicts
        assert isinstance(conflicts["rollback_rate"], float)
