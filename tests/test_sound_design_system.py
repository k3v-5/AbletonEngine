# tests/test_sound_design_system.py
"""
Comprehensive test suite for the Sound Design System (Level H):
Verifies:
1. 18 production technique families catalog completeness and device mappings.
2. Spatial Narrative width timeline progression across sections and contrast audit.
3. Transient Sculptor 4-stage envelope isolation (Attack, Transient, Body, Tail).
4. Frankenstein Engine multi-source hybrid instrument assembly.
5. Ear Candy Engine valley scanning and strict anti-saturation rationing.
6. Sonic Mutation Lab candidate generation, psychoacoustic safety gates, and top-3 ranking.
"""
import pytest
from engine.sound_design.technique_catalog import (
    ProductionTechniqueFamily,
    TechniqueCatalog,
    TechniqueDefinition,
    DeviceRecipe,
)
from engine.sound_design.spatial_narrative import (
    SpatialPoint,
    SpatialNarrativePlan,
    SpatialNarrativeEngine,
)
from engine.sound_design.transient_sculptor import (
    EnvelopeZone,
    ZoneSculptConfig,
    TransientSculptProfile,
    TransientSculptor,
)
from engine.sound_design.frankenstein_engine import (
    ComponentRole,
    FrankensteinLayer,
    FrankensteinComposite,
    FrankensteinEngine,
)
from engine.sound_design.ear_candy_engine import (
    EarCandyType,
    EarCandyOpportunity,
    EarCandyEngine,
)
from engine.sound_design.sonic_mutation_lab import (
    MutationCandidate,
    SonicMutationLab,
)
from engine.production.contract.sonic_identity import SonicIdentityBudget, SoundDesignRole


class TestTechniqueCatalog18Families:
    """Verifies that all 18 production technique families are fully codified."""

    def test_all_18_families_exist_and_enumerated(self):
        families = TechniqueCatalog.get_all_families()
        assert len(families) == 18
        expected_names = [
            "TEMPORAL_TRANSFORM", "PITCH_HARMONIC", "TRANSIENT_DESIGN",
            "SATURATION_DISTORTION", "CREATIVE_FILTER", "FRANKENSTEIN_LAYERING",
            "TEXTURE_AND_NOISE", "CREATIVE_SPACE", "SPATIAL_NARRATIVE",
            "SPECTRAL_DESIGN", "CONVOLUTION_RECONTEXT", "MICRO_CHOPPING",
            "MODULATION_MATRIX", "AUDIO_TO_MIDI_CYCLE", "BASS_LAB",
            "DRUM_LAB", "EAR_CANDY_ENGINE", "SONIC_MUTATION_LAB"
        ]
        for name in expected_names:
            assert any(f.value == name for f in families)

    def test_catalog_recipes_and_parameters(self):
        all_techs = TechniqueCatalog.get_all_techniques()
        assert len(all_techs) >= 18

        # Test extreme stretch reverse recipe
        rev_tech = TechniqueCatalog.get_technique("EXTREME_STRETCH_REVERSE")
        assert rev_tech is not None
        assert rev_tech.reverse is True
        assert rev_tech.time_stretch_ratio >= 4.0
        assert len(rev_tech.recipes) >= 2

        # Test tri-band bass lab recipe
        bass_tech = TechniqueCatalog.get_technique("TRI_BAND_BASS_SCULPTOR")
        assert bass_tech is not None
        device_names = [r.device_name for r in bass_tech.recipes]
        assert "Utility" in device_names
        assert "Saturator" in device_names


class TestSpatialNarrative:
    """Verifies architectural stereo width timeline and dynamic spatial contrast."""

    def test_spatial_narrative_generation_for_8_sections(self):
        sections = [
            {"name": "Intro", "bars": 4, "start_bar": 0},
            {"name": "Verse 1", "bars": 16, "start_bar": 4},
            {"name": "Hook 1", "bars": 8, "start_bar": 20},
            {"name": "Verse 2", "bars": 16, "start_bar": 28},
            {"name": "Hook 2", "bars": 8, "start_bar": 44},
            {"name": "Bridge", "bars": 8, "start_bar": 52},
            {"name": "Hook 3", "bars": 8, "start_bar": 60},
            {"name": "Outro", "bars": 4, "start_bar": 68},
        ]
        plan = SpatialNarrativeEngine.build_narrative_for_sections(sections)
        assert len(plan.points) == 8

        # Verify width progression
        assert plan.get_width_for_section("Intro") == 40.0
        assert plan.get_width_for_section("Verse 1") == 70.0
        assert plan.get_width_for_section("Hook 1") == 115.0
        # Bridge must collapse toward mono for vacuum tension
        assert plan.get_width_for_section("Bridge") == 30.0
        # Hook 3 must expand to maximum panoramic width
        assert plan.get_width_for_section("Hook 3") == 140.0
        # Outro dissolves to center
        assert plan.get_width_for_section("Outro") == 25.0

    def test_spatial_contrast_audit_and_envelope(self):
        sections = [
            {"name": "Verse 1", "bars": 16, "start_bar": 0},
            {"name": "Bridge", "bars": 8, "start_bar": 16},
            {"name": "Hook 3", "bars": 8, "start_bar": 24},
        ]
        plan = SpatialNarrativeEngine.build_narrative_for_sections(sections)
        audit = plan.audit_spatial_contrast()
        assert audit["has_spatial_contrast"] is True
        assert audit["verdict"] == "DYNAMIC_SPATIAL_ARC"
        assert audit["dynamic_width_range"] >= 70.0  # 140% - 30% = 110%

        envelope = plan.to_automation_envelope()
        assert len(envelope) == 6  # 2 points per section
        for pt in envelope:
            assert "time" in pt
            assert "value" in pt
            assert pt["value"] > 0.0


class TestTransientSculptor:
    """Verifies independent multi-stage envelope zone sculpting."""

    def test_sculpt_kick_four_stages(self):
        kick_prof = TransientSculptor.sculpt_kick(is_aggressive=True)
        assert kick_prof.element_name == "Kick Drum"
        assert len(kick_prof.zones) == 4

        attack = kick_prof.get_zone(EnvelopeZone.ATTACK)
        assert attack is not None
        assert attack.brightness_tilt_db > 0.0  # high click boost

        transient = kick_prof.get_zone(EnvelopeZone.TRANSIENT)
        assert transient is not None
        assert transient.drive_db >= 4.0  # chest-punch saturation

        body = kick_prof.get_zone(EnvelopeZone.BODY)
        assert body is not None
        assert body.drive_db == 0.0  # zero distortion to preserve pristine sub sine

        tail = kick_prof.get_zone(EnvelopeZone.TAIL)
        assert tail is not None
        assert "Gate" in str(tail.suggested_devices)

    def test_sculpt_piano_four_stages(self):
        piano_prof = TransientSculptor.sculpt_piano()
        assert piano_prof.element_name == "Neo-Soul Rhodes"

        attack = piano_prof.get_zone(EnvelopeZone.ATTACK)
        assert attack.brightness_tilt_db == 2.0  # tactile hammer articulation

        body = piano_prof.get_zone(EnvelopeZone.BODY)
        assert body.brightness_tilt_db < 0.0  # warm dark body

        tail = piano_prof.get_zone(EnvelopeZone.TAIL)
        assert tail.stereo_width_pct == 135.0  # expansive reverb release


class TestFrankensteinEngine:
    """Verifies assembly of multi-source hybrid composite instruments."""

    def test_assemble_hybrid_snare(self):
        hybrid_snare = FrankensteinEngine.assemble_hybrid_snare(
            clap_track="808 Core Kit",
            snare_track="Boom Bap Kit",
            tom_track="Percussion",
            texture_track="Ambient Foley",
            tail_resample_track="Stage-73 Rhodes"
        )
        assert hybrid_snare.id == "FRANK_SNARE_HYBRID"
        assert hybrid_snare.target_category == "DRUM"
        assert len(hybrid_snare.layers) == 5

        roles = [l.component_role for l in hybrid_snare.layers]
        assert ComponentRole.TRANSIENT in roles
        assert ComponentRole.BODY in roles
        assert ComponentRole.LOW_BODY in roles
        assert ComponentRole.TEXTURE in roles
        assert ComponentRole.TAIL in roles

        # Serialization roundtrip
        snare_dict = hybrid_snare.to_dict()
        restored = FrankensteinComposite.from_dict(snare_dict)
        assert restored.name == hybrid_snare.name
        assert len(restored.layers) == 5

    def test_assemble_hybrid_bass(self):
        hybrid_bass = FrankensteinEngine.assemble_hybrid_bass(
            pluck_track="Electric Pick",
            sub_track="SubLab XL",
            harmonic_resample_track="Stage-73 Keys"
        )
        assert hybrid_bass.target_category == "BASS"
        assert len(hybrid_bass.layers) == 3

        roles = [l.component_role for l in hybrid_bass.layers]
        assert ComponentRole.TRANSIENT in roles
        assert ComponentRole.SUB in roles
        assert ComponentRole.BODY in roles


class TestEarCandyEngine:
    """Verifies density valley scanning and anti-saturation rationing."""

    def test_scan_for_valleys_detects_pre_drop_and_verse_gaps(self):
        diagnostics = [
            {"name": "Verse 1", "bars": 16, "start_bar": 0, "density_ratio": 0.50},
            {"name": "Hook 1", "bars": 8, "start_bar": 16, "density_ratio": 0.88},
            {"name": "Verse 2", "bars": 16, "start_bar": 24, "density_ratio": 0.55},
            {"name": "Bridge", "bars": 8, "start_bar": 40, "density_ratio": 0.40},
            {"name": "Hook 3", "bars": 8, "start_bar": 48, "density_ratio": 0.95},
        ]

        opportunities = EarCandyEngine.scan_for_valleys(diagnostics, max_events=2)
        # Must enforce strict limit of at most 2 events to prevent saturation
        assert len(opportunities) <= 2
        assert len(opportunities) > 0

        types = [o.suggested_type for o in opportunities]
        assert any(t in [EarCandyType.NOISE_SWEEP_VACUUM, EarCandyType.DELAY_THROW_SPLASH] for t in types)

    def test_budget_exhaustion_blocks_excess_ear_candy(self):
        budget = SonicIdentityBudget(max_ear_candy_events=2)
        budget.record_ear_candy()
        budget.record_ear_candy()  # Budget exhausted!

        diagnostics = [
            {"name": "Verse 1", "bars": 16, "start_bar": 0, "density_ratio": 0.40},
            {"name": "Hook 1", "bars": 8, "start_bar": 16, "density_ratio": 0.90},
        ]
        opportunities = EarCandyEngine.scan_for_valleys(diagnostics, budget=budget)
        assert len(opportunities) == 0  # Zero allowed when budget is exhausted


class TestSonicMutationLab:
    """Verifies candidate generation, psychoacoustic filtering, and top-3 ranking."""

    def test_experiment_filters_vocal_masking_and_diffuse_impact(self):
        budget = SonicIdentityBudget()
        top_proposals = SonicMutationLab.run_experiment(
            source_track_index=5,
            source_track_name="Stage-73 Rhodes",
            source_section="Hook 1",
            target_section="Bridge",
            target_has_vocal=True,
            budget=budget,
            candidate_count=12
        )

        # Must return exactly the top 3 clean candidates
        assert len(top_proposals) == 3

        ids = [p.candidate_id for p in top_proposals]
        # Piercing screamer (c6) and diffuse impact sludge (c7) must be rejected
        assert "MUT_06_HARSH_SCREAMER" not in ids
        assert "MUT_07_DIFFUSE_SLUDGE" not in ids

        # Proposals must be sorted descending by rank score
        assert top_proposals[0].rank_score >= top_proposals[1].rank_score
        assert top_proposals[1].rank_score >= top_proposals[2].rank_score

        # Check that top candidate is safe for lead vocal
        top_cand = top_proposals[0]
        assert top_cand.energy_vocal_band_db <= -14.0
        assert top_cand.is_approved is True
