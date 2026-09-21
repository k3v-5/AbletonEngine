# tests/test_sonic_dna_and_gen2.py
"""
Test suite for Generation 2 of the Sound Design & Sonic Identity System:
Verifies:
1. SonicDNA acoustic genome extraction, timbral hierarchy, and genetic loyalty gating.
2. Candidate moment location, 6-band envelope decomposition, and 4-branch DestructionPass.
3. Frankenstein 2.0 100% autogenous validation and alien source rejection.
4. Signature Sound Registry quota enforcement (strictly 1 to 3 sounds) and recipe hashing.
5. Contrast Engine 8-polarity dynamic delta auditing.
6. Producer Taste Model 7-dimensional perceptual evaluation and ranking.
7. Sonic Identity Audit 10-point checklist execution and abstention discipline.
"""
import pytest
from engine.sound_design.sonic_dna import (
    SonicDNA,
    HarmonicDNA,
    RhythmicDNA,
    TimbralDNA,
    TextureDNA,
    SpatialDNA,
    MotifFingerprint,
)
from engine.sound_design.resynthesis_engine import (
    ComponentBand,
    DestructionBranch,
    CandidateMoment,
    DecomposedComponent,
    DestructionVariant,
    FabricatedInstrument,
    ResynthesisEngine,
)
from engine.sound_design.frankenstein_v2 import (
    AutogenousComponentSource,
    FrankensteinV2Object,
    FrankensteinV2Engine,
)
from engine.sound_design.signature_sound_generator import (
    SignatureAppearance,
    SignatureSoundRecord,
    SignatureSoundRegistry,
)
from engine.sound_design.contrast_engine import (
    ContrastPolarity,
    SectionPolarityState,
    ContrastEngine,
)
from engine.sound_design.producer_taste_model import (
    TasteMetrics,
    ProducerTasteEvaluation,
    ProducerTasteModel,
)
from engine.sound_design.sonic_identity_audit_v2 import (
    AuditPointResult,
    SonicIdentityAuditV2Report,
    SonicIdentityAuditV2,
)
from engine.sound_design.ear_candy_engine import EarCandyOpportunity, EarCandyType


class TestSonicDNA:
    """Verifies acoustic genome extraction and genetic loyalty enforcement."""

    def test_dna_extraction_from_session_state(self):
        session_data = {
            "key": "Eb",
            "scale": "minor",
            "bpm": 110.0,
            "genre": "neo-soul/hip-hop",
            "tracks": [
                {"name": "Stage-73 Rhodes", "role": "keys"},
                {"name": "Analog Lab Horns", "role": "horns"},
                {"name": "SubLab XL", "role": "bass"},
                {"name": "Boom Bap Kit", "role": "drums"},
            ]
        }
        dna = SonicDNA.extract_from_session(session_data)
        assert dna.harmonic.key == "Eb"
        assert dna.harmonic.scale == "minor"
        assert dna.rhythmic.bpm == 110.0
        assert dna.rhythmic.swing_pct == 54.0  # 54% 16th swing for hip-hop
        assert "rhodes" in dna.timbral.primary_timbre.lower()
        assert "horns" in dna.timbral.secondary_timbre.lower()
        assert len(dna.key_motifs) >= 3

    def test_genetic_loyalty_enforcement(self):
        session_data = {
            "key": "Eb",
            "scale": "minor",
            "bpm": 110.0,
            "genre": "hip-hop",
            "tracks": [
                {"name": "Stage-73 Rhodes", "role": "keys"},
                {"name": "SubLab XL", "role": "bass"},
            ]
        }
        dna = SonicDNA.extract_from_session(session_data)

        # Legitimate autogenous mutation derived from Rhodes
        valid, err = dna.validate_mutation_compatibility("SIGNATURE", "Stage-73 Rhodes chord")
        assert valid is True
        assert err is None

        # Orphan mutation from an alien source not in the DNA
        invalid, err = dna.validate_mutation_compatibility("SIGNATURE", "Downloaded Rave RaveSynth Sample")
        assert invalid is False
        assert "Mutación huérfana" in err


class TestResynthesisEngineAndDestructionPass:
    """Verifies candidate discovery, envelope decomposition, and destruction branches."""

    def test_candidate_moment_discovery(self):
        dna = SonicDNA.extract_from_session({"key": "Eb", "scale": "minor", "bpm": 110.0})
        moments = ResynthesisEngine.locate_candidate_moments(dna)
        assert len(moments) >= 2
        moment_ids = [m.moment_id for m in moments]
        assert "MOMENT_HOOK1_RHODES_CHORD" in moment_ids

    def test_envelope_decomposition_6_bands(self):
        dna = SonicDNA.extract_from_session({"key": "Eb", "scale": "minor", "bpm": 110.0})
        moment = ResynthesisEngine.locate_candidate_moments(dna)[0]
        components = ResynthesisEngine.decompose_envelope(moment)
        assert len(components) == 6

        bands = [c.band for c in components]
        assert ComponentBand.ATTACK in bands
        assert ComponentBand.TRANSIENT in bands
        assert ComponentBand.BODY in bands
        assert ComponentBand.HARMONICS in bands
        assert ComponentBand.NOISE in bands
        assert ComponentBand.TAIL in bands

    def test_destruction_pass_four_branches(self):
        dna = SonicDNA.extract_from_session({"key": "Eb", "scale": "minor", "bpm": 110.0})
        moment = ResynthesisEngine.locate_candidate_moments(dna)[0]
        variants = ResynthesisEngine.run_destruction_pass(moment)
        assert len(variants) == 4

        branches = [v.branch for v in variants]
        assert DestructionBranch.CLEAN in branches
        assert DestructionBranch.DEGRADED in branches
        assert DestructionBranch.DESTROYED in branches
        assert DestructionBranch.RECONSTRUCTED in branches

        # Verify degraded branch has 12-bit depth
        degraded = next(v for v in variants if v.branch == DestructionBranch.DEGRADED)
        assert degraded.bit_depth == 12
        assert degraded.drive_db > 0.0

        # Verify reconstructed has reverse tail with shimmer
        reconstructed = next(v for v in variants if v.branch == DestructionBranch.RECONSTRUCTED)
        assert reconstructed.reverse is True
        assert reconstructed.time_stretch >= 4.0

    def test_fabricate_new_instrument(self):
        dna = SonicDNA.extract_from_session({"key": "Eb", "scale": "minor", "bpm": 110.0})
        moment = ResynthesisEngine.locate_candidate_moments(dna)[0]
        inst = ResynthesisEngine.fabricate_new_instrument(
            moment=moment,
            category="PAD",
            branch=DestructionBranch.RECONSTRUCTED,
            target_section="Bridge",
            target_bars=(53, 60)
        )
        assert "PAD" in inst.target_category
        assert inst.placement_section == "Bridge"
        assert inst.active_branch == DestructionBranch.RECONSTRUCTED


class TestFrankensteinV2:
    """Verifies strict 100% autogeny and alien source rejection."""

    def test_autogenous_snare_crafting_and_validation(self):
        session_tracks = [
            "808 Core Kit",
            "Boom Bap Kit",
            "Ableton Simpler",
            "Stage-73 Rhodes",
            "SubLab XL"
        ]

        snare = FrankensteinV2Engine.craft_autogenous_snare(
            clap_track="808 Core Kit",
            snare_track="Boom Bap Kit",
            foley_track="Ableton Simpler",
            rhodes_track="Stage-73 Rhodes",
            bass_track="SubLab XL"
        )
        assert snare.target_role == "SNARE"
        assert len(snare.components) == 5
        assert len(snare.uniqueness_hash) > 0

        # Validate autogeny against session tracks
        is_autogenous, err = snare.validate_100_percent_autogenous(session_tracks)
        assert is_autogenous is True
        assert err is None

    def test_autogeny_violation_rejection(self):
        # Session missing the foley track
        incomplete_session_tracks = ["808 Core Kit", "Boom Bap Kit", "SubLab XL"]

        snare = FrankensteinV2Engine.craft_autogenous_snare(
            clap_track="808 Core Kit",
            snare_track="Boom Bap Kit",
            foley_track="Alien Foley Library",
            rhodes_track="Alien Rhodes",
            bass_track="SubLab XL"
        )
        is_autogenous, err = snare.validate_100_percent_autogenous(incomplete_session_tracks)
        assert is_autogenous is False
        assert "Violación de autogenia" in err


class TestSignatureSoundRegistry:
    """Verifies strict quota (1-3 sounds) and multi-section evolution."""

    def test_quota_limits_min1_max3(self):
        registry = SignatureSoundRegistry(song_id="kendrick_alright")
        assert registry.validate_quota()["is_compliant"] is False  # 0 is below min 1

        # Register 1st signature
        app1 = [SignatureAppearance("Bridge", (53, 60), "BIRTH", "400Hz HPF", "tension")]
        ok, rec1, _ = registry.register_signature("Ghost Rhodes", "Stage-73", "reverse+stretch", "TRANSITION", app1)
        assert ok is True
        assert registry.validate_quota()["is_compliant"] is True

        # Register 2nd signature
        ok, rec2, _ = registry.register_signature("SubLab Growl", "SubLab", "harmonic drive", "BASS_ACCENT", [])
        assert ok is True

        # Register 3rd signature (reaches maximum)
        ok, rec3, _ = registry.register_signature("Horn Freeze", "Analog Lab", "granular freeze", "EAR_CANDY", [])
        assert ok is True
        assert registry.validate_quota()["signature_count"] == 3
        assert registry.can_register() is False

        # Attempt 4th signature (must be rejected!)
        ok, rec4, err = registry.register_signature("Excess Sound", "Drums", "stutter", "MISC", [])
        assert ok is False
        assert "Límite de cuota alcanzado" in err


class TestContrastEngine:
    """Verifies 8-polarity tracking and vibrant dynamic contrast."""

    def test_contrast_arc_auditing(self):
        arc = ContrastEngine.build_rhodes_contrast_arc("Stage-73 Rhodes")
        assert len(arc) == 4

        audit = ContrastEngine.audit_contrast_arc(arc)
        assert audit["is_dynamic"] is True
        assert audit["verdict"] == "VIBRANT_DYNAMIC_CONTRAST"
        assert audit["width_delta"] >= 1.0  # -0.8 in Bridge vs +0.9 in Hook 3 = 1.7 delta!
        assert audit["space_delta"] >= 1.0  # -0.7 in Verse 1 vs +0.8 in Bridge = 1.5 delta!


class TestProducerTasteModel:
    """Verifies 7-dimensional perceptual evaluation of sonic identity."""

    def test_evaluate_candidate_identifies_exceptional_identity(self):
        dna = SonicDNA.extract_from_session({
            "key": "Eb",
            "scale": "minor",
            "bpm": 110.0,
            "tracks": [{"name": "Stage-73 Rhodes", "role": "keys"}]
        })

        eval_report = ProducerTasteModel.evaluate_candidate(
            candidate_id="SIG_RHODES_GHOST",
            name="Reverse Ghost Halo",
            source_desc="Stage-73 Rhodes chord",
            mutation_desc="Reverse + time-stretch 4x + 10s spectral shimmer",
            target_section="Bridge",
            sonic_dna=dna
        )
        assert eval_report.verdict == "EXCEPTIONAL_IDENTITY"
        assert eval_report.metrics.coherence >= 0.90
        assert eval_report.metrics.composite_identity_score >= 0.85

    def test_evaluate_candidate_rejects_alien_source(self):
        dna = SonicDNA.extract_from_session({
            "key": "Eb",
            "scale": "minor",
            "bpm": 110.0,
            "tracks": [{"name": "Stage-73 Rhodes", "role": "keys"}]
        })

        eval_report = ProducerTasteModel.evaluate_candidate(
            candidate_id="ALIEN_SAMPLE",
            name="Random Trance Sweep",
            source_desc="Unrelated Dance Sample Pack",
            mutation_desc="Default preset",
            target_section="Verse 1",
            sonic_dna=dna
        )
        assert eval_report.verdict == "REJECTED"
        assert eval_report.metrics.coherence < 0.50


class TestSonicIdentityAuditV2:
    """Verifies the 10-point audit checklist and abstention rule."""

    def test_10_point_audit_complete_success(self):
        dna = SonicDNA.extract_from_session({"key": "Eb", "scale": "minor", "bpm": 110.0})
        registry = SignatureSoundRegistry(song_id="alright_test")
        app = [
            SignatureAppearance("Hook 1", (21, 28), "BIRTH", "400Hz HPF", "subtle entry"),
            SignatureAppearance("Bridge", (53, 60), "DEVELOPMENT", "reverse swell", "tension"),
            SignatureAppearance("Hook 3", (61, 68), "CLIMAX", "full frontal halo", "payoff"),
        ]
        registry.register_signature("Ghost Rhodes", "Stage-73 Rhodes", "reverse + stretch 4x", "TRANSITION", app)

        contrast_arc = ContrastEngine.build_rhodes_contrast_arc("Stage-73 Rhodes")
        ear_candies = [
            EarCandyOpportunity(
                id="EC_1",
                section_name="Bridge",
                target_bar=60,
                target_beat=240.0,
                gap_duration_beats=4.0,
                density_score=0.45,
                suggested_type=EarCandyType.NOISE_SWEEP_VACUUM,
                recipe_description="Pre-drop vacuum",
                narrative_justification="Builds drop anticipation"
            )
        ]

        report = SonicIdentityAuditV2.audit(
            sonic_dna=dna,
            signature_registry=registry,
            contrast_arc=contrast_arc,
            ear_candies=ear_candies,
            has_generic_spam=False,
            is_recipe_duplicated=False
        )

        assert report.total_score_out_of_10 == 10
        assert report.is_identity_complete is True
        assert report.verdict == "AUTHENTIC_SONIC_IDENTITY"
        assert report.abstention_honored is True
        assert len(report.points) == 10
        assert all(p.passed for p in report.points)
