"""
Comprehensive Test Suite for "Canciones con Memoria" & Transversal Music Identity:
Tests all 6 architectural blocks:
1. Music Identity Layer & The 6 Production Motifs (engine/creative/music_identity.py)
2. Resampling Lab & GeneratedSource Genealogy (engine/creative/resampling_lab.py)
3. Spatial Energy Curve & Stereo Collapse/Explosion (engine/arrangement/spatial_curve.py)
4. Organic Rhythm Layer & Hybrid Drums by Timbre DNA (engine/music/drums/organic_rhythm.py)
5. Metric Tension, Euclidean Rhythms & DROP_BEAT_1 Resolution (engine/music/rhythm/metric_tension.py)
6. Music Director A/B Search, Triad Evaluation & Atomic Rollback (engine/production/copilot/phases/phase_10/music_director.py)
"""

import pytest
import copy
import random
from typing import Dict, Any, List

# Block 1 Imports
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

# Block 2 Imports
from engine.creative.resampling_lab import (
    ResamplingLab,
    GeneratedSource,
    RESAMPLING_RECIPES
)
from engine.instruments.browser_catalog import CURATED_SOURCES

# Block 3 Imports
from engine.arrangement.spatial_curve import (
    SpatialEnergyCurveEngine,
    SpatialProfile,
    CANONICAL_PROFILES,
    build_spatial_envelope,
    verify_drop_expansion_contrast
)

# Block 4 Imports
from engine.music.drums.organic_rhythm import (
    OrganicFoleySample,
    FOLEY_PALETTE,
    OrganicRhythmCoordinator,
    generate_hybrid_organic_layer,
    evaluate_timbre_complement
)
from engine.sound.timbre_dna import TimbreDNA

# Block 5 Imports
from engine.music.rhythm.metric_tension import (
    MetricTensionEvent,
    MetricTensionCoordinator,
    should_apply_metric_tension,
    is_role_allowed_metric_tension,
    bjorklund,
    generate_euclidean_pattern,
    generate_metric_tension_notes,
    SECTION_METRIC_TENSION_PROBABILITIES,
    ANCHOR_ROLES,
    ALLOWED_TENSION_ROLES
)

# Block 6 Imports
from engine.production.copilot.phases.phase_10.music_director import MusicDirector
from engine.session.transaction_guard import TransactionGuard


# ==============================================================================
# 1. Tests for Music Identity Layer & Production Motifs
# ==============================================================================

class TestMusicIdentityLayer:
    def test_music_identity_initialization_and_serialization(self):
        identity = MusicIdentity(
            song_title="Midnight Memory",
            concept="hipnótico y cinemático",
            tonal_center="D",
            mode="Aeolian",
            tempo=126.0
        )
        assert identity.song_title == "Midnight Memory"
        assert identity.melodic_motif.contour == "ascending_then_falling"
        assert identity.rhythmic_motif.pattern_name == "3-3-2"
        assert identity.spatial_motif.min_width == 0.15
        assert identity.spatial_motif.max_width == 1.25

        d = identity.to_dict()
        assert d["song_title"] == "Midnight Memory"
        assert d["tonal_center"] == "D"
        assert "melodic_motif" in d
        assert "spatial_motif" in d

        restored = MusicIdentity.from_dict(d)
        assert restored.song_title == identity.song_title
        assert restored.tempo == 126.0
        assert restored.spatial_motif.min_width == 0.15

    def test_identity_auditor_evaluation(self):
        # Empty session -> low identity score
        empty_session = {"tracks": [], "sections": []}
        audit_empty = IdentityAuditor.evaluate_identity(empty_session)
        assert audit_empty["identity_score"] < 0.5
        assert not audit_empty["is_signature_compliant"]
        assert len(audit_empty["missing_signatures"]) > 0

        # Rich session fulfilling all 6 motifs
        rich_session = {
            "tracks": [
                {"name": "Lead Synth", "role": "LEAD", "has_leitmotif": True},
                {"name": "Drums 3-3-2", "role": "DRUMS", "groove_cell": "3-3-2"},
                {"name": "Foley Bed", "role": "TEXTURE_FOLEY"}
            ],
            "sections": [
                {"name": "Buildup", "is_pre_drop_transition": True},
                {"name": "Drop 1", "energy": 0.95}
            ],
            "spatial_energy_curve": [{"section": "Drop 1", "width": 1.25}],
            "pre_drop_vacuum_verified": True
        }
        audit_rich = IdentityAuditor.evaluate_identity(rich_session)
        assert audit_rich["identity_score"] >= 0.8
        assert audit_rich["is_signature_compliant"]

    def test_genealogy_logging(self):
        identity = MusicIdentity()
        identity.record_genealogy(
            event_type="resampling_transformation",
            source_id="lead_drop_1",
            destination_id="ghost_lead_texture",
            section="Breakdown",
            transformations=["render", "reverse", "pitch_-12", "stretch_180"]
        )
        assert len(identity.genealogy_log) == 1
        assert identity.genealogy_log[0]["destination_id"] == "ghost_lead_texture"


# ==============================================================================
# 2. Tests for Resampling Lab & GeneratedSource Genealogy
# ==============================================================================

class TestResamplingLab:
    def test_resampling_transformation_and_registration(self):
        session_data: Dict[str, Any] = {
            "tracks": [
                {
                    "name": "Main Lead",
                    "role": "LEAD",
                    "notes": [{"pitch": 60, "start": 0.0, "duration": 1.0, "velocity": 100}]
                }
            ],
            "music_identity": MusicIdentity().to_dict()
        }

        generated = ResamplingLab.process_and_register_source(
            session_data=session_data,
            source_track_name="Main Lead",
            origin_section="Drop 1",
            recipe_name="ghost_lead_texture"
        )

        assert generated is not None
        assert isinstance(generated, GeneratedSource)
        assert generated.origin_track_name == "Main Lead"
        assert generated.origin_section == "Drop 1"
        assert any("reverse" in t for t in generated.transformations)
        assert any("pitch_shift_-12" in t for t in generated.transformations)

        # Check registration in CURATED_SOURCES under generated.role
        role_enum = generated.role
        sources_for_role = CURATED_SOURCES.get(role_enum, [])
        assert any(s.id == generated.id for s in sources_for_role)

        # Check genealogy log in session_data
        genealogy = session_data["music_identity"]["genealogy_log"]
        assert len(genealogy) > 0
        assert genealogy[-1]["destination_id"] == generated.id

    def test_generated_source_to_dict_and_restore(self):
        from engine.instruments.browser_catalog import InstrumentSourceCategory
        gen = GeneratedSource(
            id="test_gen_source",
            name="Test Ambient Drone",
            category=InstrumentSourceCategory.NATIVE_SYNTH,
            uri="query:test_gen_source",
            role="PAD",
            origin_track_name="Lead Track",
            origin_section="Build 1",
            transformations=["render", "stretch_200"]
        )
        d = gen.to_dict()
        assert d["id"] == "test_gen_source"
        assert d["origin_track_name"] == "Lead Track"
        assert "stretch_200" in d["transformations"]



# ==============================================================================
# 3. Tests for Spatial Energy Curve & Stereo Collapse/Explosion
# ==============================================================================

class TestSpatialEnergyCurve:
    def test_canonical_profiles(self):
        assert CANONICAL_PROFILES["intro"].stereo_width == 0.25
        assert CANONICAL_PROFILES["build"].stereo_width == 0.70
        assert CANONICAL_PROFILES["pre_drop"].stereo_width == 0.15  # Pre-drop collapse!
        assert CANONICAL_PROFILES["drop"].stereo_width >= 1.15      # Drop explosion!
        assert CANONICAL_PROFILES["break"].stereo_width == 0.35

    def test_build_spatial_envelope(self):
        sections = [
            {"name": "Intro", "bars": 8},
            {"name": "Buildup", "bars": 8},
            {"name": "Pre-Drop", "bars": 2},
            {"name": "Main Drop", "bars": 16}
        ]
        res = build_spatial_envelope(sections)
        timeline = res["timeline"]
        assert len(timeline) == 4
        # Verify pre-drop collapse and drop explosion
        pre_drop_pt = next(p for p in timeline if p["section"] == "Pre-Drop")
        drop_pt = next(p for p in timeline if p["section"] == "Main Drop")

        assert pre_drop_pt["profile"]["stereo_width"] == 0.15
        assert drop_pt["profile"]["stereo_width"] >= 1.15
        assert drop_pt["profile"]["stereo_width"] - pre_drop_pt["profile"]["stereo_width"] >= 1.0


    def test_verify_drop_expansion_contrast(self):
        contrast_ok = verify_drop_expansion_contrast(pre_drop_width=0.15, drop_width=1.25)
        assert contrast_ok["contrast_sufficient"] is True
        assert contrast_ok["delta_width"] >= 0.70

        contrast_bad = verify_drop_expansion_contrast(pre_drop_width=0.80, drop_width=1.00)
        assert contrast_bad["contrast_sufficient"] is False


# ==============================================================================
# 4. Tests for Organic Rhythm Layer & Hybrid Drums
# ==============================================================================

class TestOrganicRhythmLayer:
    def test_velocity_and_microtiming_inheritance(self):
        drum_hits = [
            {"pitch": 38, "start": 1.0, "velocity": 110, "is_accent": True},
            {"pitch": 38, "start": 3.0, "velocity": 70, "is_accent": False}
        ]
        foley = FOLEY_PALETTE["wood_snap_dry"]
        organic_notes = generate_hybrid_organic_layer(drum_hits, foley_sample=foley)

        assert len(organic_notes) == 2
        # Velocity should scale proportionally (scaled by foley.velocity_ratio ~0.78)
        assert organic_notes[0]["velocity"] > organic_notes[1]["velocity"]
        assert organic_notes[0]["velocity"] < 110  # Inherited scaled down
        # Microtiming offset applied (subtle displacement without drifting off grid)
        assert organic_notes[0]["start"] > 1.0
        assert organic_notes[0]["start"] < 1.05


    def test_timbre_complementarity(self):
        # Bright, sharp snare
        bright_snare_dna = TimbreDNA(brightness=0.85, roughness=0.15, stereo_width=0.2)
        # Complementary foley should prefer higher roughness and warmer brightness
        wood_sample = FOLEY_PALETTE["wood_snap_dry"]
        match_score = evaluate_timbre_complement(bright_snare_dna, wood_sample)
        assert 0.0 <= match_score <= 1.0
        assert match_score > 0.40  # Meaningful complementarity


# ==============================================================================
# 5. Tests for Metric Tension, Euclidean Rhythms & Resolution
# ==============================================================================

class TestMetricTension:
    def test_section_probabilities(self):
        assert SECTION_METRIC_TENSION_PROBABILITIES["build"] == 0.75
        assert SECTION_METRIC_TENSION_PROBABILITIES["break"] == 0.55
        assert SECTION_METRIC_TENSION_PROBABILITIES["drop"] == 0.05
        assert SECTION_METRIC_TENSION_PROBABILITIES["verse"] == 0.10

    def test_metric_anchor_constraint(self):
        # Anchor roles must NEVER be allowed metric tension
        for anchor in ANCHOR_ROLES:
            assert is_role_allowed_metric_tension(anchor) is False, f"Anchor role {anchor} was falsely allowed tension"

        # Secondary melodic/ornamental roles MUST be allowed
        for allowed in ALLOWED_TENSION_ROLES:
            assert is_role_allowed_metric_tension(allowed) is True, f"Role {allowed} was falsely blocked"

    def test_bjorklund_euclidean_algorithm(self):
        # E(5, 16): 5 pulses distributed across 16 steps
        e5_16 = bjorklund(16, 5)
        assert len(e5_16) == 16
        assert sum(e5_16) == 5

        # Rotation
        rotated = generate_euclidean_pattern(16, 5, rotation=2)
        assert len(rotated) == 16
        assert sum(rotated) == 5

    def test_metric_tension_notes_crescendo_and_resolution(self):
        event = MetricTensionEvent(
            source_role="arp",
            pattern_type="3/16",
            duration_bars=4.0,
            start_beat=0.0,
            intensity=0.9,
            resolution="DROP_BEAT_1"
        )
        section_beats = 16.0
        base_notes = [{"pitch": 60, "start": 0.0, "duration": 1.0, "velocity": 80}]

        notes = generate_metric_tension_notes(base_notes, event, section_beats=section_beats)
        assert len(notes) > 0

        # Verify 3/16 spacing (0.75 beats between successive note starts)
        diff = round(notes[1]["start"] - notes[0]["start"], 4)
        assert diff == 0.75

        # Verify crescendo: earlier notes have lower velocity than later notes
        first_vel = notes[0]["velocity"]
        last_vel = notes[-1]["velocity"]
        assert last_vel > first_vel

        # Verify DROP_BEAT_1 resolution: no note bleeds past section_beats
        for n in notes:
            assert n["start"] < section_beats
            assert round(n["start"] + n["duration"], 4) <= section_beats

    def test_metric_anchor_integrity_verification(self):
        valid_tracks = [
            {"name": "Kick", "role": "KICK", "notes": [{"pitch": 36, "start": 0.0, "is_metric_tension": False}]},
            {"name": "Sub Bass", "role": "BASS", "notes": [{"pitch": 36, "start": 0.0, "is_metric_tension": False}]},
            {"name": "Arp 3/16", "role": "ARP", "notes": [{"pitch": 67, "start": 0.0, "is_metric_tension": True}]}
        ]
        audit = MetricTensionCoordinator.verify_metric_anchor_integrity(valid_tracks)
        assert audit["anchor_integrity_preserved"] is True

        # Invalid scenario where bass was compromised
        invalid_tracks = [
            {"name": "Sub Bass", "role": "BASS", "notes": [{"pitch": 36, "start": 0.0, "is_metric_tension": True}]}
        ]
        audit_invalid = MetricTensionCoordinator.verify_metric_anchor_integrity(invalid_tracks)
        assert audit_invalid["anchor_integrity_preserved"] is False
        assert len(audit_invalid["violations"]) == 1


# ==============================================================================
# 6. Tests for Music Director A/B Search, Triad Evaluation & Rollback
# ==============================================================================

class TestMusicDirector:
    def test_audit_triad(self):
        session_mock = type("MockSession", (), {
            "data": {
                "tracks": [
                    {"name": "Kick", "role": "KICK", "notes_count": 16},
                    {"name": "Lead", "role": "LEAD", "notes_count": 8, "has_leitmotif": True}
                ],
                "sections": [
                    {"name": "Verse", "bars": 8, "energy": 0.4},
                    {"name": "Build", "bars": 8, "energy": 0.7},
                    {"name": "Drop", "bars": 16, "energy": 0.95}
                ]
            }
        })()

        triad = MusicDirector.audit_triad(session_mock)
        assert triad["status"] == "TRIAD_AUDITED"
        assert 0.0 <= triad["predictability_score"] <= 1.0
        assert 0.0 <= triad["identity_score"] <= 1.0
        assert 0.0 <= triad["contrast_score"] <= 1.0
        assert "needs_intervention" in triad

    def test_supreme_rule_no_forced_intervention_on_balanced_session(self):
        # A session with excellent contrast, high identity, and low predictability
        perfect_session = type("MockSession", (), {
            "data": {
                "tracks": [
                    {"name": "Kick", "role": "KICK", "notes_count": 17},  # Non-quantized
                    {"name": "Lead", "role": "LEAD", "has_leitmotif": True},
                    {"name": "Counter Lead", "role": "COUNTER_LEAD"},
                    {"name": "Ear Candy", "role": "EAR_CANDY"},
                    {"name": "Foley Bed", "role": "TEXTURE_FOLEY"}
                ],
                "sections": [
                    {"name": "Intro", "bars": 8, "energy": 0.3},
                    {"name": "Verse", "bars": 10, "energy": 0.5},  # Asymmetric!
                    {"name": "Build", "bars": 8, "energy": 0.75},
                    {"name": "Drop", "bars": 16, "energy": 1.0}
                ],
                "spatial_energy_curve": [{"section": "Drop", "width": 1.25}],
                "pre_drop_vacuum_verified": True
            }
        })()

        triad = MusicDirector.audit_triad(perfect_session)
        assert not triad["needs_intervention"]

        # evaluate_ab_mutations should respect the Supreme Rule and NOT mutate
        result = MusicDirector.evaluate_ab_mutations(perfect_session)
        assert result["status"] == "NO_INTERVENTION_NEEDED"
        assert result["action"] == "PRESERVED"
        assert result["winner"] is None

    def test_ab_mutation_evaluation_and_commitment(self):
        # A deficient session with high predictability and low contrast
        deficient_session = type("MockSession", (), {
            "data": {
                "tracks": [
                    {"name": "Kick", "role": "KICK", "notes_count": 16},  # Rigid
                    {"name": "Lead", "role": "LEAD", "notes_count": 16}   # Missing counter lead & ear candy
                ],
                "sections": [
                    {"name": "Verse", "bars": 8, "energy": 0.5},
                    {"name": "Chorus", "bars": 8, "energy": 0.55}         # Low contrast
                ]
            },
            "_save_state": lambda *args, **kwargs: None
        })()

        result = MusicDirector.evaluate_ab_mutations(
            deficient_session,
            candidate_keys=["B", "C"]  # Candidate B adds counter-lead
        )

        assert result["status"] == "MUTATION_COMMITTED"
        assert result["winner"] is not None
        assert result["winner"]["delta"] > 0.0
        # Check that session was updated with the winning candidate
        assert any(t.get("role") in ("COUNTER_LEAD", "TEXTURE_FOLEY") for t in deficient_session.data["tracks"])

    def test_ab_mutation_rollback_when_no_candidate_improves(self):
        # Session where intervention is needed, but we pass candidates that won't improve the score
        initial_data = {
            "tracks": [{"name": "Kick", "role": "KICK", "notes_count": 16}],
            "sections": [{"name": "Section A", "bars": 8, "energy": 0.5}]
        }
        session_mock = type("MockSession", (), {
            "data": copy.deepcopy(initial_data),
            "_save_state": lambda *args, **kwargs: None
        })()

        # Pass an empty or non-improving candidate list
        result = MusicDirector.evaluate_ab_mutations(session_mock, candidate_keys=[])
        assert result["status"] == "ROLLBACK_EXECUTED"
        assert result["winner"] is None
        assert result["action"] == "ROLLED_BACK"
        # Verify state is identical to initial
        assert len(session_mock.data["tracks"]) == 1
