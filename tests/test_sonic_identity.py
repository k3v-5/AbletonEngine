# tests/test_sonic_identity.py
"""
Comprehensive test suite for Level H: Sonic Identity (Identidad Sonora & Resampling Recursivo).
Verifies:
1. SonicIdentityBudget strict enforcement & anti-saturation gating.
2. SoundDesignEngine deterministic archetype synthesis (damaged, enormous, ghostly, tape, granular).
3. ResamplingEngine recursive mutation branches & psychoacoustic MutationFilter rejection.
4. SonicMemory genealogy tracking, life stage arc (Birth -> Dev -> Climax -> Decay), & contrast audits.
5. SongContract & CreativeXRay integration across Level H.
"""
import pytest
from engine.production.contract.sonic_identity import (
    SoundDesignRole,
    SonicIdentityBudget,
    SonicObject,
    SonicIdentityAudit,
    SonicIdentityAuditReport,
)
from engine.production.contract.sound_design_engine import (
    DestructionArchetype,
    SoundDesignStep,
    SoundDesignChain,
    SoundDesignEngine,
)
from engine.production.contract.resampling_engine import (
    MutationBranch,
    MaterialMutation,
    MutationFilter,
    RecursiveResamplingEngine,
)
from engine.production.contract.sonic_memory import (
    SonicLifeStage,
    SonicOccurrence,
    SonicObjectGenealogy,
    SonicMemory,
)
from engine.production.contract.song_contract import (
    SongContract,
    ObligationCategory,
    ObligationStatus,
)
from engine.production.contract.creative_xray import CreativeXRay


class TestSonicIdentityBudget:
    """Verifies strict budget discipline to protect structural contrast."""

    def test_budget_limits_and_exhaustion(self):
        budget = SonicIdentityBudget(
            max_signature_sounds=2,
            max_major_transformations=3,
            max_ear_candy_events=4,
            max_extreme_processing_events=1,
        )
        assert budget.is_within_budget()

        # Add 2 signature sounds (reaches limit)
        assert budget.record_signature_sound() is True
        assert budget.record_signature_sound() is True
        # 3rd signature sound must be blocked
        assert budget.can_add_signature_sound() is False
        assert budget.record_signature_sound() is False

        # Add transformations
        assert budget.record_transformation() is True
        assert budget.record_transformation() is True
        assert budget.record_transformation() is True
        # 4th transformation must be blocked
        assert budget.can_add_transformation() is False
        assert budget.record_transformation() is False

        # Add extreme processing
        assert budget.record_extreme_processing() is True
        assert budget.can_add_extreme_processing() is False
        assert budget.record_extreme_processing() is False

    def test_budget_serialization_roundtrip(self):
        budget = SonicIdentityBudget(max_signature_sounds=1, max_major_transformations=2)
        budget.record_signature_sound()
        budget.record_transformation()
        data = budget.to_dict()

        restored = SonicIdentityBudget.from_dict(data)
        assert restored.max_signature_sounds == 1
        assert restored.used_signature_sounds == 1
        assert restored.max_major_transformations == 2
        assert restored.used_major_transformations == 1
        assert restored.is_within_budget() is True


class TestSoundDesignEngine:
    """Verifies intentional aesthetic transformation archetypes."""

    def test_make_it_damaged_archetype(self):
        chain = SoundDesignEngine.build_chain(DestructionArchetype.MAKE_IT_DAMAGED, intensity=0.8)
        assert chain.archetype == DestructionArchetype.MAKE_IT_DAMAGED
        assert chain.reverse is False
        assert len(chain.steps) == 3

        device_names = [s.device_name for s in chain.steps]
        assert "Saturator" in device_names
        assert "Redux" in device_names
        assert "EQ Eight" in device_names

        # Check SP-1200 lo-fi bitcrush parameter
        redux_step = next(s for s in chain.steps if s.device_name == "Redux")
        assert redux_step.parameters.get("Bit Depth") in [10, 12]

    def test_make_it_enormous_archetype(self):
        chain = SoundDesignEngine.build_chain(DestructionArchetype.MAKE_IT_ENORMOUS, intensity=0.9)
        assert chain.archetype == DestructionArchetype.MAKE_IT_ENORMOUS
        assert chain.time_stretch_ratio >= 3.0

        device_names = [s.device_name for s in chain.steps]
        assert "Chorus-Ensemble" in device_names
        assert "Reverb" in device_names

        reverb_step = next(s for s in chain.steps if s.device_name == "Reverb")
        assert "s" in reverb_step.parameters.get("Decay Time", "")

    def test_make_it_ghostly_archetype(self):
        chain = SoundDesignEngine.build_chain(DestructionArchetype.MAKE_IT_GHOSTLY, intensity=0.7)
        assert chain.archetype == DestructionArchetype.MAKE_IT_GHOSTLY
        assert chain.reverse is True  # Ghost requires reverse rendering
        assert chain.time_stretch_ratio >= 4.0

        # EQ Eight must high pass to clear fundamental frequencies
        eq_step = next(s for s in chain.steps if s.device_name == "EQ Eight")
        assert "High Pass" in eq_step.parameters.get("Band 1 Mode", "")
        assert "420 Hz" in eq_step.parameters.get("Band 1 Freq", "")

    def test_tape_degradation_archetype(self):
        chain = SoundDesignEngine.build_chain(DestructionArchetype.TAPE_DEGRADATION)
        assert chain.archetype == DestructionArchetype.TAPE_DEGRADATION
        device_names = [s.device_name for s in chain.steps]
        assert "Chorus-Ensemble" in device_names  # Wow & flutter vibrato
        assert "Saturator" in device_names
        assert "EQ Eight" in device_names

    def test_granular_scatter_archetype(self):
        chain = SoundDesignEngine.build_chain(DestructionArchetype.GRANULAR_SCATTER)
        assert chain.archetype == DestructionArchetype.GRANULAR_SCATTER
        device_names = [s.device_name for s in chain.steps]
        assert "Grain Delay" in device_names
        assert "Reverb" in device_names


class TestResamplingEngineAndPsychoacousticFilter:
    """Verifies candidate mutation filtering and ranking."""

    def test_vocal_masking_filter_rejection(self):
        budget = SonicIdentityBudget()

        # Safe branch (energy in vocal band is low)
        safe_branch = MutationBranch(
            generation=1,
            transform_name="Sub-bass Rumble",
            archetype=DestructionArchetype.MAKE_IT_ENORMOUS,
            parameters={},
            audio_ref="safe.wav",
            frequency_peak_hz=60.0,
            energy_vocal_band_db=-25.0,
            transient_clarity_score=0.7,
            description="Safe deep sub",
        )
        safe_mutation = MaterialMutation(
            id="SAFE_1",
            name="Sub Swell",
            role=SoundDesignRole.ATMOSPHERE,
            source_track_index=1,
            source_track_name="Bass",
            source_section="Hook 1",
            source_bars=(1, 4),
            root_motif_description="808 root",
            branches=[safe_branch],
        )

        passed, reason = MutationFilter.evaluate_candidate(
            safe_mutation, budget, target_section_has_lead_vocal=True
        )
        assert passed is True
        assert reason is None

        # Toxic branch (piercing mid energy directly clashing with lead vocal)
        toxic_branch = MutationBranch(
            generation=1,
            transform_name="Harsh Screamer",
            archetype=DestructionArchetype.MAKE_IT_DAMAGED,
            parameters={},
            audio_ref="toxic.wav",
            frequency_peak_hz=2500.0,
            energy_vocal_band_db=-6.5,  # Exceeds -14 dBFS threshold
            transient_clarity_score=0.8,
            description="Aggressive vocal range screamer",
        )
        toxic_mutation = MaterialMutation(
            id="TOXIC_1",
            name="Vocal Clasher",
            role=SoundDesignRole.EAR_CANDY,
            source_track_index=2,
            source_track_name="Synth",
            source_section="Verse 1",
            source_bars=(5, 8),
            root_motif_description="Lead stab",
            branches=[toxic_branch],
        )

        passed, reason = MutationFilter.evaluate_candidate(
            toxic_mutation, budget, target_section_has_lead_vocal=True
        )
        assert passed is False
        assert "Enmascaramiento psicoacústico vocal" in reason

    def test_groove_destruction_filter_rejection(self):
        budget = SonicIdentityBudget()
        # Diffused blur placed on an IMPACT role
        muddy_branch = MutationBranch(
            generation=1,
            transform_name="Diffuse Mush",
            archetype=DestructionArchetype.MAKE_IT_ENORMOUS,
            parameters={},
            audio_ref="mush.wav",
            frequency_peak_hz=120.0,
            energy_vocal_band_db=-22.0,
            transient_clarity_score=0.15,  # Below 0.40 minimum for impact/transition
            description="Muddy tail",
        )
        impact_mutation = MaterialMutation(
            id="MUDDY_IMPACT",
            name="Mush Impact",
            role=SoundDesignRole.IMPACT,
            source_track_index=0,
            source_track_name="Kick",
            source_section="Hook 1",
            source_bars=(1, 1),
            root_motif_description="Kick transient",
            branches=[muddy_branch],
        )
        passed, reason = MutationFilter.evaluate_candidate(
            impact_mutation, budget, target_section_has_lead_vocal=False
        )
        assert passed is False
        assert "Pérdida de impacto rítmico" in reason

    def test_recursive_resampling_generation_and_ranking(self):
        budget = SonicIdentityBudget()
        proposals = RecursiveResamplingEngine.generate_proposals(
            source_track_index=5,
            source_track_name="Stage-73 Rhodes",
            source_section="Hook 1",
            source_bars=(21, 29),
            root_motif_desc="F#m9 - B7 - Emaj9 chord sequence",
            target_section="Bridge",
            target_bars=(53, 61),
            budget=budget,
            target_has_vocal=True
        )
        # Should return top clean proposals (excluding toxic candidate 4)
        assert len(proposals) > 0
        assert len(proposals) <= 3
        # Candidate 4 (MUT_REJECT_5) must have been filtered out
        ids = [p.id for p in proposals]
        assert "MUT_REJECT_5" not in ids


class TestSonicMemoryAndGenealogy:
    """Verifies sonic object lifecycles across the song narrative."""

    def test_genealogy_life_stage_arc(self):
        memory = SonicMemory()
        gen = memory.register_object(
            object_id="GHOST_RHODES_1",
            name="Ghostly Rhodes Halo",
            parent_track_name="Keys (Stage-73)",
            parent_motif_desc="Hook 1 chord progression"
        )
        assert gen.object_id == "GHOST_RHODES_1"

        # Record Birth in Bridge
        memory.record_occurrence(
            object_id="GHOST_RHODES_1",
            section="Bridge",
            start_bar=53,
            end_bar=60,
            stage=SonicLifeStage.DEVELOPMENT,
            form_description="Reverse 400% stretch with 420Hz HPF shimmer",
            narrative_purpose="Ethereal tension bridge leading to final hook"
        )
        # Record Climax in Hook 3
        memory.record_occurrence(
            object_id="GHOST_RHODES_1",
            section="Hook 3",
            start_bar=61,
            end_bar=68,
            stage=SonicLifeStage.CLIMAX,
            form_description="Frontal unfiltered stereo ghost layer supporting main melody",
            narrative_purpose="Maximum emotional payoff"
        )
        # Record Decay in Outro
        memory.record_occurrence(
            object_id="GHOST_RHODES_1",
            section="Outro",
            start_bar=69,
            end_bar=72,
            stage=SonicLifeStage.DECAY,
            form_description="Distorted tape relic fading into vinyl crackle",
            narrative_purpose="Nostalgic dissolution"
        )

        assert gen.has_stage(SonicLifeStage.DEVELOPMENT) is True
        assert gen.has_stage(SonicLifeStage.CLIMAX) is True
        assert gen.has_stage(SonicLifeStage.DECAY) is True
        assert gen.has_contrast() is True

        audit = memory.audit_narrative_continuity()
        assert audit["is_narratively_coherent"] is True
        assert len(audit["contrast_failures"]) == 0

    def test_genealogy_contrast_failure_detection(self):
        memory = SonicMemory()
        memory.register_object("STATIC_BLEEP", "Static Bleep", "Synth", "Arp")

        # Record identical appearances everywhere
        for sec in ["Intro", "Verse 1", "Hook 1", "Verse 2", "Hook 2", "Bridge", "Hook 3", "Outro"]:
            memory.record_occurrence(
                object_id="STATIC_BLEEP",
                section=sec,
                start_bar=1,
                end_bar=4,
                stage=SonicLifeStage.BIRTH,
                form_description="identical unvaried bleep",
                narrative_purpose="none"
            )

        audit = memory.audit_narrative_continuity()
        assert audit["is_narratively_coherent"] is False
        assert len(audit["static_loop_warnings"]) > 0


class TestSongContractAndCreativeXRayIntegration:
    """Verifies end-to-end integration with SongContract and CreativeXRay."""

    def test_song_contract_holds_sonic_identity(self):
        contract = SongContract(song_id="kendrick_alright_test")
        assert contract.sonic_budget is not None
        assert contract.sonic_memory is not None

        # Register a sonic obligation
        ob = contract.register_obligation(
            id="SIGNATURE_SOUND_RHODES",
            title="Design Hook 1 Resampled Ghost Signature",
            category=ObligationCategory.SONIC_IDENTITY,
            due_phase="PHASE_6_COMPOSITION",
            is_critical=True,
            intent={"archetype": "MAKE_IT_GHOSTLY", "target_section": "Bridge"}
        )
        assert ob.category == ObligationCategory.SONIC_IDENTITY

        # Register SonicObject
        obj = SonicObject(
            id="OBJ_GHOST_1",
            name="Rhodes Reverse Ghost",
            role=SoundDesignRole.SIGNATURE,
            source_track="Keys",
            source_material_desc="Hook 1 Rhodes chords",
            archetype="MAKE_IT_GHOSTLY",
            target_sections=["Bridge", "Hook 3"],
            placement_bars=[53, 61],
        )
        contract.sonic_objects.append(obj)
        contract.sonic_budget.record_signature_sound()

        # Serialization roundtrip
        contract_dict = contract.to_dict()
        restored = SongContract.from_dict(contract_dict)
        assert len(restored.sonic_objects) == 1
        assert restored.sonic_objects[0].role == SoundDesignRole.SIGNATURE
        assert restored.sonic_budget.used_signature_sounds == 1

    def test_creative_xray_renders_level_h(self):
        contract = SongContract(song_id="test_xray_song")
        obj = SonicObject(
            id="OBJ_SIGNATURE_TEST",
            name="Spectral Ghost Pad",
            role=SoundDesignRole.SIGNATURE,
            source_track="Keys",
            source_material_desc="Hook 1 Rhodes chords",
            archetype="MAKE_IT_GHOSTLY",
            target_sections=["Bridge", "Hook 3"],
        )
        contract.sonic_objects.append(obj)
        contract.sonic_budget.record_signature_sound()

        session_data = {
            "bpm": 110.0,
            "key": "Eb",
            "scale": "minor",
            "genre": "hip-hop",
            "tracks": [{"name": "Keys", "role": "keys", "notes": [60, 63, 67]}],
            "sections": [
                {"name": "Intro", "bars": 4, "start_bar": 0},
                {"name": "Verse 1", "bars": 16, "start_bar": 4},
                {"name": "Hook 1", "bars": 8, "start_bar": 20},
                {"name": "Bridge", "bars": 8, "start_bar": 28},
                {"name": "Hook 3", "bars": 8, "start_bar": 36},
            ]
        }

        xray = CreativeXRay.generate_xray(session_data=session_data, contract=contract)
        assert xray["status"] == "CREATIVE_XRAY_GENERATED"
        assert "sonic_identity" in xray
        assert xray["sonic_identity"]["has_signature_sound"] is True
        assert xray["sonic_identity"]["signature_sound_count"] == 1

        md = xray["markdown_report"]
        assert "NIVEL H: IDENTIDAD SONORA & SOUND DESIGN" in md
        assert "Presupuesto:" in md
        assert "Contraste Sónico:" in md
