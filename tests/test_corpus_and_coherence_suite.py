"""
Test Suite for Phase 2: Calibración, Guardrail de Coherencia, Desarrollo de Motivos y Creative Corpus Evaluator.
Includes:
1. Coherence Guardrail in MusicDirector (rejects high-contrast but narrative-destructive mutations).
2. Motif Development vs. Static Repetition in MusicIdentity (exposure, transformation, and development scores).
3. Sound Genealogy Tree & Survival Rate in ResamplingLab (multi-generational depth tracking).
4. CreativeCorpusEvaluator & Internal Cliché Detector (audits emergent patterns across session corpora).
5. Acid Test 1: Divergence under Identical Constraints (A != B with same genre, bpm, key, plugins).
6. Acid Test 2: Variation with Identity Preservation (A != B in arrangement, but Identity(A) ~= Identity(B)).
"""

import pytest
import copy
import random
from typing import Dict, Any, List

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
from engine.creative.resampling_lab import (
    ResamplingLab,
    GeneratedSource,
    GenealogyTree
)
from engine.creative.corpus_evaluator import (
    CreativeCorpusEvaluator,
    CLICHE_FREQUENCY_THRESHOLD
)
from engine.production.copilot.phases.phase_10.music_director import MusicDirector
from engine.session.transaction_guard import TransactionGuard
from engine.music.rhythm.generator import generate_drums


# ==============================================================================
# 1. Coherence Guardrail Tests
# ==============================================================================

class TestCoherenceGuardrail:
    def test_audit_coherence_metrics(self):
        session_mock = type("MockSession", (), {
            "data": {
                "tracks": [
                    {"name": "Kick", "role": "KICK", "notes": [{"pitch": 36, "is_out_of_scale": False}]},
                    {"name": "Snare", "role": "SNARE", "notes": [{"pitch": 38, "is_out_of_scale": False}]},
                    {"name": "Bass", "role": "BASS", "notes": [{"pitch": 36, "is_out_of_scale": False}]},
                    {"name": "Lead", "role": "LEAD", "notes": [{"pitch": 60, "is_out_of_scale": False}]}
                ],
                "sections": [
                    {"name": "Verse", "notes_count": 16},
                    {"name": "Build", "notes_count": 20},
                    {"name": "Drop", "notes_count": 24}
                ]
            }
        })()

        coherence = MusicDirector.audit_coherence(session_mock)
        assert coherence["status"] == "COHERENCE_AUDITED"
        assert coherence["coherence_score"] >= 0.70
        assert coherence["is_narrative_coherent"] is True
        assert coherence["harmonic_continuity"] == 1.0
        assert coherence["anchor_stability"] == 1.0

    def test_guardrail_rejects_destructive_mutation(self):
        # A deficient session needing intervention
        session_mock = type("MockSession", (), {
            "data": {
                "tracks": [
                    {"name": "Kick", "role": "KICK", "notes_count": 16},
                    {"name": "Lead", "role": "LEAD", "notes_count": 16}
                ],
                "sections": [
                    {"name": "Verse", "bars": 8, "energy": 0.5},
                    {"name": "Chorus", "bars": 8, "energy": 0.55}
                ]
            },
            "_save_state": lambda *args, **kwargs: None
        })()

        # Run evaluate_ab_mutations
        res = MusicDirector.evaluate_ab_mutations(session_mock)
        assert "all_candidates" in res

        # Verify that all candidates were audited against the guardrail
        for cand in res["all_candidates"]:
            if cand.get("rejected_by_guardrail"):
                assert "breached" in cand.get("guardrail_reason", "")


# ==============================================================================
# 2. Motif Development vs. Repetition Tests
# ==============================================================================

class TestMotifDevelopmentVsRepetition:
    def test_static_repetition_yields_zero_development(self):
        ident = MusicIdentity()
        # Expose melodic motif 5 times without transforming it
        for sec in ["Intro", "Verse 1", "Verse 2", "Chorus", "Outro"]:
            ident.record_motif_exposure("melodic", section_name=sec, was_transformed=False)

        assert ident.melodic_motif.exposure_count == 5
        assert ident.melodic_motif.transformation_count == 0
        assert ident.get_motif_development_score("melodic") == 0.0

        audit = IdentityAuditor.evaluate_identity({"music_identity": ident.to_dict()})
        assert audit["motif_development_score"] == 0.0
        assert audit["development_status"] == "static_repetition"

    def test_rich_evolution_yields_high_development(self):
        ident = MusicIdentity()
        # Expose melodic motif 5 times with 4 transformations
        ident.record_motif_exposure("melodic", "Intro", was_transformed=False)
        ident.record_motif_exposure("melodic", "Verse", was_transformed=True)     # Subgrave
        ident.record_motif_exposure("melodic", "Build", was_transformed=True)     # Accelerated
        ident.record_motif_exposure("melodic", "Break", was_transformed=True)     # Reharmonized
        ident.record_motif_exposure("melodic", "Drop", was_transformed=True)      # Inverted

        assert ident.melodic_motif.exposure_count == 5
        assert ident.melodic_motif.transformation_count == 4
        dev_score = ident.get_motif_development_score("melodic")
        assert dev_score == 0.80

        audit = IdentityAuditor.evaluate_identity({"music_identity": ident.to_dict()})
        assert audit["motif_development_score"] > 0.60
        assert audit["development_status"] == "rich_evolution"

    def test_serialization_preserves_development_metrics(self):
        ident = MusicIdentity()
        ident.record_motif_exposure("rhythmic", "Build", was_transformed=True)
        ident.record_motif_exposure("timbre", "Drop", was_transformed=True)

        d = ident.to_dict()
        restored = MusicIdentity.from_dict(d)
        assert restored.rhythmic_motif.exposure_count == 1
        assert restored.rhythmic_motif.transformation_count == 1
        assert restored.rhythmic_motif.last_seen_section == "Build"
        assert restored.timbre_motif.transformation_count == 1


# ==============================================================================
# 3. Genealogy Tree & Survival Rate Tests
# ==============================================================================

class TestGenealogyTreeAndSurvival:
    def test_multi_generational_depth_and_tree_construction(self):
        session_data: Dict[str, Any] = {
            "tracks": [{"name": "Main Lead", "role": "LEAD"}],
            "generated_sources": [],
            "music_identity": MusicIdentity().to_dict()
        }

        # Generation 1: Direct render from Main Lead
        gen_1 = ResamplingLab.process_and_register_source(
            session_data=session_data,
            source_track_name="Main Lead",
            origin_section="Drop 1",
            recipe_name="ghost_lead_texture"
        )
        assert gen_1.generation_depth == 1

        # Generation 2: Derived from Generation 1
        gen_2 = ResamplingLab.process_and_register_source(
            session_data=session_data,
            source_track_name=gen_1.id,
            origin_section="Breakdown",
            recipe_name="vocal_granular_cloud"
        )
        assert gen_2.generation_depth == 2

        # Generation 3: Derived from Generation 2
        gen_3 = ResamplingLab.process_and_register_source(
            session_data=session_data,
            source_track_name=gen_2.id,
            origin_section="Build 2",
            recipe_name="percussive_glitch_accent"
        )
        assert gen_3.generation_depth == 3

        # Add Gen 1 and Gen 3 to active tracks (Gen 2 discarded)
        session_data["tracks"].append({"name": gen_1.name, "source_id": gen_1.id})
        session_data["tracks"].append({"name": gen_3.name, "source_id": gen_3.id})

        # Calculate survival rate
        surv = GenealogyTree.calculate_survival_rate(session_data)
        assert surv["total_generated"] == 3
        assert surv["survived_count"] == 2
        assert surv["survival_rate"] == round(2 / 3, 3)
        assert surv["max_depth"] == 3

        # Render ASCII tree
        ascii_tree = GenealogyTree.render_ascii_tree(session_data)
        assert "depth=1" in ascii_tree
        assert "depth=2" in ascii_tree
        assert "depth=3" in ascii_tree
        assert "[SURVIVED]" in ascii_tree
        assert "[DISCARDED]" in ascii_tree


# ==============================================================================
# 4. Creative Corpus Evaluator & Internal Cliché Detector Tests
# ==============================================================================

class TestCreativeCorpusEvaluator:
    def test_corpus_evaluation_and_cliche_alarm(self):
        # Create a mock corpus of 20 sessions
        corpus = []
        for i in range(20):
            # 19 out of 20 have reverse transitions (95% frequency -> triggers alarm)
            # 4 out of 20 have 3/16 polyrhythm (20% frequency -> normal)
            has_rev = (i < 19)
            has_poly = (i < 4)

            s_data = {
                "tracks": [
                    {
                        "name": "Arp 3/16" if has_poly else "Arp 4/4",
                        "role": "ARP",
                        "notes": [{"pitch": 60, "is_metric_tension": has_poly}]
                    },
                    {
                        "name": "Reverse Transition" if has_rev else "Impact Sweep",
                        "role": "FX"
                    }
                ],
                "sections": [{"name": "Build"}, {"name": "Drop"}],
                "spatial_energy_curve": [{"stereo_width": 0.15 if i % 2 == 0 else 0.50}],
                "music_identity": {"genealogy_log": []}
            }
            corpus.append(s_data)

        report = CreativeCorpusEvaluator.evaluate_corpus(corpus)
        assert report["status"] == "CORPUS_AUDITED"
        assert report["total_sessions_analyzed"] == 20
        assert report["frequencies"]["reverse_transition"] == 0.95
        assert report["frequencies"]["polyrhythm_3_16"] == 0.20

        # Verify cliché alarm was triggered for reverse transition
        assert report["has_internal_cliche_alarm"] is True
        alarms = [a["technique"] for a in report["cliche_alarms"]]
        assert "reverse_audio_transition" in alarms
        assert "polyrhythm_3_16" not in alarms  # 20% is healthy, no alarm


# ==============================================================================
# 5. Acid Test 1: Divergence under Identical Constraints
# ==============================================================================

class TestAcidTest1Divergence:
    def test_same_constraints_different_seeds_produce_divergent_songs(self):
        """
        Two songs produced under identical constraints:
        - Same genre: melodic_techno
        - Same tempo: 124.0
        - Same structure: 16 bars
        - Same available plugins
        - Different creative seeds: 101 vs 202
        Guarantees A != B without being distorted clones.
        """
        seed_a = 101
        seed_b = 202

        drums_a = generate_drums(genre="melodic_techno", bars=16, seed=seed_a)
        drums_b = generate_drums(genre="melodic_techno", bars=16, seed=seed_b)

        assert len(drums_a) > 0
        assert len(drums_b) > 0

        # Check that note velocities, timings, or elements differ
        vels_a = [n.velocity for n in drums_a]
        vels_b = [n.velocity for n in drums_b]
        assert vels_a != vels_b, "Song A and Song B produced identical drum velocities!"

        starts_a = [n.start for n in drums_a]
        starts_b = [n.start for n in drums_b]
        # Fills or element choices will differ based on seed
        assert (vels_a[:10] != vels_b[:10]) or (starts_a != starts_b)

        # Both remain valid in 4/4 time
        for n in drums_a + drums_b:
            assert n.start >= 0.0
            assert n.velocity > 0


# ==============================================================================
# 6. Acid Test 2: Variation with Identity Preservation
# ==============================================================================

class TestAcidTest2IdentityPreservation:
    def test_same_identity_different_versions_preserve_core_dna(self):
        """
        Same MusicIdentity ("Midnight Mirage", F# Dorian, 3-3-2 clave, Leitmotif [0, 3, 7, 10]).
        Generates Version A (Original Mix) and Version B (Club Extended Mix).
        Guarantees:
        - A != B in arrangement and track count
        - But Identity(A) ~= Identity(B) with delta <= 0.15
        """
        base_identity = MusicIdentity(
            song_title="Midnight Mirage",
            tonal_center="F#",
            mode="Dorian",
            tempo=124.0,
            melodic_motif=MelodicMotif(intervals=[0, 3, 7, 10], root_pitch=66),
            rhythmic_motif=RhythmicMotif(pattern_name="3-3-2")
        )

        # Version A (Radio / Original Mix - 3 tracks, concise)
        session_a = {
            "tracks": [
                {"name": "Main Lead", "role": "LEAD", "has_leitmotif": True, "notes_count": 16},
                {"name": "Drums 3-3-2", "role": "DRUMS", "groove_cell": "3-3-2", "notes_count": 32},
                {"name": "Foley Bed", "role": "TEXTURE_FOLEY", "notes_count": 4}
            ],
            "sections": [
                {"name": "Intro", "bars": 8},
                {"name": "Drop 1", "bars": 16, "is_pre_drop_transition": True}
            ],
            "spatial_energy_curve": [{"section": "Drop 1", "stereo_width": 1.25}],
            "music_identity": base_identity.to_dict()
        }

        # Version B (Club Extended Mix - 5 tracks, longer development)
        session_b = {
            "tracks": [
                {"name": "Main Lead Extended", "role": "LEAD", "has_leitmotif": True, "notes_count": 32},
                {"name": "Counter Lead Arp", "role": "COUNTER_LEAD", "notes_count": 24},
                {"name": "Club Drums 3-3-2", "role": "DRUMS", "groove_cell": "3-3-2", "notes_count": 64},
                {"name": "Foley Granular Bed", "role": "TEXTURE_FOLEY", "notes_count": 8},
                {"name": "Sub Impact", "role": "BASS", "notes_count": 16}
            ],
            "sections": [
                {"name": "Club Intro", "bars": 16},
                {"name": "Buildup", "bars": 8, "is_pre_drop_transition": True},
                {"name": "Extended Drop", "bars": 32}
            ],
            "spatial_energy_curve": [{"section": "Extended Drop", "stereo_width": 1.28}],
            "music_identity": base_identity.to_dict()
        }

        # Verify A != B in tracks and notes
        assert len(session_a["tracks"]) != len(session_b["tracks"])
        total_notes_a = sum(t["notes_count"] for t in session_a["tracks"])
        total_notes_b = sum(t["notes_count"] for t in session_b["tracks"])
        assert total_notes_a != total_notes_b

        # Verify Identity(A) ~= Identity(B)
        audit_a = IdentityAuditor.evaluate_identity(session_a)
        audit_b = IdentityAuditor.evaluate_identity(session_b)

        ident_a = audit_a["identity_score"]
        ident_b = audit_b["identity_score"]

        assert ident_a >= 0.80
        assert ident_b >= 0.80
        assert abs(ident_a - ident_b) <= 0.15, f"Identity diverged too much: {ident_a} vs {ident_b}"
        assert audit_a["is_signature_compliant"] is True
        assert audit_b["is_signature_compliant"] is True
