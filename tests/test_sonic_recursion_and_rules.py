# tests/test_sonic_recursion_and_rules.py
"""
Unit tests for Sonic Recursion & Self-Sampling Rules:
- Regla 1: Anti-literal recycling vs Anti-chaos degradation (0.25 <= Dist <= 0.88).
- Regla 2: Musical significance seed prioritization.
- Regla 3: Role-dependent mutator specialization (Bass, Pad, Percussion, Riser, Ear Candy).
- Regla 4: Generation depth guard (max_depth = 3).
- Regla 5: Sonic Family Registry memory.
"""

import pytest
from engine.audio_genesis.provenance import (
    SampleProvenanceRecord,
    SampleOrigin,
    AudioSourceLocation,
    InstrumentProvenance,
    ProcessingStep,
    CreativeGovernanceError,
)
from engine.audio_genesis.sonic_recursion import (
    RecursiveTargetRole,
    SonicFamily,
    SonicFamilyRegistry,
    SeedMusicalSignificance,
    PerceptualDistanceAuditor,
    RoleDependentMutator,
    GenerationDepthGuard,
)


def test_regla_1_anti_literal_copy_and_anti_chaos():
    parent = SampleProvenanceRecord(
        sample_id="parent_rhodes",
        origin=SampleOrigin.ORIGINAL_GENERATED,
        source=AudioSourceLocation(track="Rhodes"),
        instrument=InstrumentProvenance(device="Stage-73 V2"),
        generation_depth=0
    )
    child = SampleProvenanceRecord(
        sample_id="child_rhodes",
        origin=SampleOrigin.DERIVED_FROM_SONG,
        source=AudioSourceLocation(track="Rhodes"),
        instrument=InstrumentProvenance(device="Stage-73 V2"),
        parent_sample_id="parent_rhodes",
        generation_depth=1
    )

    # 1. Literal copy (distance < 0.25) -> VETO
    approved, dist, rej = PerceptualDistanceAuditor.audit_distance(parent, child, simulated_distance=0.15)
    assert not approved
    assert "Veto Regla 1 (Reciclaje literal)" in rej

    # 2. Chaos / Extreme degradation (distance > 0.88) -> VETO
    approved, dist, rej = PerceptualDistanceAuditor.audit_distance(parent, child, simulated_distance=0.92)
    assert not approved
    assert "Veto Regla 1 (Caos degenerado)" in rej

    # 3. Sweet spot of audible genetic kinship (0.25 <= dist <= 0.88) -> APPROVED
    approved, dist, rej = PerceptualDistanceAuditor.audit_distance(parent, child, simulated_distance=0.65)
    assert approved
    assert rej is None
    assert dist == 0.65


def test_regla_2_musical_significance_prioritization():
    # Primary Motif has highest weight (1.0)
    score_motif = SeedMusicalSignificance.rate_significance("Main Melody", is_primary_motif=True)
    assert score_motif == 1.0

    # Key chords / Rhodes bed has 0.90
    score_chords = SeedMusicalSignificance.rate_significance("Rhodes Keys", role="KEYS", has_chords=True)
    assert score_chords == 0.90

    # Signature Gesture has 0.85
    score_gesture = SeedMusicalSignificance.rate_significance("Vacuum Riser", has_signature_gesture=True)
    assert score_gesture == 0.85

    # Core drums has 0.80
    score_drums = SeedMusicalSignificance.rate_significance("Acoustic Snare", role="DRUMS")
    assert score_drums == 0.80

    # Background foley has low significance as a raw seed (0.40)
    score_foley = SeedMusicalSignificance.rate_significance("Vinyl Noise Bed", role="FOLEY")
    assert score_foley == 0.40


def test_regla_3_role_dependent_mutator_specialization():
    # 1. BASS specialization
    bass_recipe = RoleDependentMutator.get_role_recipe(RecursiveTargetRole.BASS, "Rhodes")
    assert bass_recipe["pipeline"] == "micro_sample"
    assert "low_pass_filter_110hz" in bass_recipe["recipe_steps"]
    assert bass_recipe["target_destination"] == "simpler_melodic"

    # 2. PAD_TEXTURE specialization
    pad_recipe = RoleDependentMutator.get_role_recipe(RecursiveTargetRole.PAD_TEXTURE, "Rhodes")
    assert pad_recipe["pipeline"] == "freeze_pad"
    assert "time_stretch_600%" in pad_recipe["recipe_steps"]
    assert pad_recipe["target_destination"] == "audio_clip"

    # 3. PERCUSSION specialization
    perc_recipe = RoleDependentMutator.get_role_recipe(RecursiveTargetRole.PERCUSSION, "Rhodes")
    assert perc_recipe["pipeline"] == "micro_sample"
    assert "transient_attack_isolate" in perc_recipe["recipe_steps"]
    assert perc_recipe["target_destination"] == "transient_layer"

    # 4. TRANSITION_RISER specialization
    riser_recipe = RoleDependentMutator.get_role_recipe(RecursiveTargetRole.TRANSITION_RISER, "Rhodes")
    assert riser_recipe["pipeline"] == "melodic_resample"
    assert "reverse_audio_phrase" in riser_recipe["recipe_steps"]

    # 5. EAR_CANDY specialization
    candy_recipe = RoleDependentMutator.get_role_recipe(RecursiveTargetRole.EAR_CANDY, "Rhodes")
    assert candy_recipe["pipeline"] == "audio_to_midi_cycle"
    assert "micro_chopping_32nd_grid" in candy_recipe["recipe_steps"]


def test_regla_4_generation_depth_guard_raises_at_max_depth():
    # Generation 0, 1, 2 are valid
    rec_gen0 = SampleProvenanceRecord("s0", SampleOrigin.ORIGINAL_GENERATED, AudioSourceLocation(), InstrumentProvenance(), generation_depth=0)
    rec_gen1 = SampleProvenanceRecord("s1", SampleOrigin.DERIVED_FROM_SONG, AudioSourceLocation(), InstrumentProvenance(), generation_depth=1)
    rec_gen2 = SampleProvenanceRecord("s2", SampleOrigin.DERIVED_FROM_SONG, AudioSourceLocation(), InstrumentProvenance(), generation_depth=2)

    assert GenerationDepthGuard.validate_depth(rec_gen0) is True
    assert GenerationDepthGuard.validate_depth(rec_gen1) is True
    assert GenerationDepthGuard.validate_depth(rec_gen2) is True

    # Generation 3 is at the max ceiling and cannot be further re-mutated
    rec_gen3 = SampleProvenanceRecord("s3", SampleOrigin.DERIVED_FROM_SONG, AudioSourceLocation(), InstrumentProvenance(), generation_depth=3)
    with pytest.raises(CreativeGovernanceError) as excinfo:
        GenerationDepthGuard.validate_depth(rec_gen3)

    assert "Veto Regla 4 (Límite generacional)" in str(excinfo.value)
    assert "profundidad generacional 3 >= 3" in str(excinfo.value)


def test_regla_5_sonic_family_registry_storage_and_query():
    registry = SonicFamilyRegistry()

    fam = registry.register_family(
        name="Ghost Rhodes Halo",
        dominant_timbre="Harmonic Shimmer 600%",
        source_instrument="Stage-73 V2",
        target_role=RecursiveTargetRole.PAD_TEXTURE,
        transformation_recipe=["granular_freeze", "time_stretch_600%"],
        ancestor_sample_id="render_rhodes_01",
        recommended_sections=["bridge", "outro"],
        tags=["rhodes", "ambient", "shimmer"]
    )

    assert fam.family_id.startswith("fam_ghost_rhodes_halo_")
    assert registry.get_family(fam.family_id) is not None

    pads = registry.find_families_for_role(RecursiveTargetRole.PAD_TEXTURE)
    assert len(pads) == 1
    assert pads[0].name == "Ghost Rhodes Halo"

    basses = registry.find_families_for_role(RecursiveTargetRole.BASS)
    assert len(basses) == 0

    d = registry.to_dict()
    assert d["family_count"] == 1
