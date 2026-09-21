# tests/test_artistic_critic_and_intent.py
"""
Unit and Integration Tests for:
1. Artistic Intent Manifesto (ArtisticIntent)
2. Artistic Critic Engine (7 Independent Perspectives)
3. Taste and Selection Loop (80-90% Ruthless Rejection & Guided Mutation)
"""
import pytest
from engine.creative.artistic_intent import ArtisticIntent, EmotionalJourney
from engine.creative.artistic_critic import (
    CriticDimension,
    VetoSeverity,
    CriticScore,
    CriticVerdict,
    IdentityCritic,
    MemorabilityCritic,
    PredictabilityCritic,
    EmotionalCritic,
    HumanPlausibilityCritic,
    SonicSignatureCritic,
    CulturalGenrePlausibilityCritic,
    ArtisticCriticEngine,
)
from engine.creative.selection_loop import TasteAndSelectionLoop, CandidateProposal, SelectionResult
from engine.composition.compositional_dna import CompositionalDNA, PrimaryMotif, NegativeConstraint
from engine.memory.catalog_memory import CatalogMemory, SongCatalogRecord


# =============================================================================
# 1. ARTISTIC INTENT TESTS
# =============================================================================

def test_artistic_intent_manifesto_initialization_and_serialization():
    intent = ArtisticIntent.create_minimal_intimate("Felt Solitude")
    assert intent.song_title == "Felt Solitude"
    assert "fragility" in intent.emotional_core
    assert "generic_trap_hats" in intent.forbidden_tropes
    assert intent.risk_tolerance == 0.55

    d = intent.to_dict()
    assert d["song_title"] == "Felt Solitude"
    assert "beginning" in d["listener_experience"]

    restored = ArtisticIntent.from_dict(d)
    assert restored.song_title == intent.song_title
    assert restored.emotional_core == intent.emotional_core
    assert restored.listener_experience.beginning == intent.listener_experience.beginning


def test_artistic_intent_serves_intent_veto_logic():
    intent = ArtisticIntent.create_minimal_intimate()

    # Good proposal: serves intent
    serves_good, _ = intent.serves_intent({
        "name": "Intimate Felt Piano Chords",
        "tags": ["acoustic_felt", "intimate"],
        "risk": 0.50,
        "density": 0.40
    })
    assert serves_good is True

    # Bad proposal 1: Contains strictly forbidden trope
    serves_bad_1, reason_1 = intent.serves_intent({
        "name": "Trap Beat with Generic Trap Hats",
        "tags": ["generic_trap_hats"],
        "risk": 0.50
    })
    assert serves_bad_1 is False
    assert "generic_trap_hats" in reason_1

    # Bad proposal 2: Wildly exceeds risk tolerance causing incoherence
    serves_bad_2, reason_2 = intent.serves_intent({
        "name": "Nuclear Distorted Noise Wall",
        "risk": 0.98  # intent.risk_tolerance is 0.55 -> delta > 0.35
    })
    assert serves_bad_2 is False
    assert "exceeds risk tolerance" in reason_2

    # Bad proposal 3: Constant maximal density
    serves_bad_3, reason_3 = intent.serves_intent({
        "name": "Wall of Sound Smashed",
        "density": 0.95,
        "duration_bars": 32.0
    })
    assert serves_bad_3 is False
    assert "maximal density" in reason_3


def test_artistic_intent_evaluate_alignment():
    intent = ArtisticIntent.create_aggressive_dense()
    high_align = intent.evaluate_alignment({
        "emotions": ["ferocity", "urgency"],
        "risk": 0.85,
        "detected_tropes": []
    })
    assert high_align >= 0.80

    low_align = intent.evaluate_alignment({
        "emotions": ["sweet_pastoral"],
        "risk": 0.20,
        "detected_tropes": ["unextended_major_triads", "sweet_chords"]
    })
    assert low_align < 0.40


# =============================================================================
# 2. SEVEN SPECIALIZED CRITICS TESTS
# =============================================================================

def test_identity_critic_vetos_catalog_clone():
    catalog = CatalogMemory()
    catalog.songs.clear()
    existing_rec = SongCatalogRecord(
        song_id="existing_01",
        title="Midnight Rhodes",
        genre="neo_soul",
        bpm=90.0,
        key="F#",
        scale="minor",
        instrument_plugins=["Rhodes", "RC20"],
        sound_design_recipes=["tape_rhodes_flutter"],
        signature_textures=["vinyl_hiss"],
        created_at="2026-09-01"
    )
    catalog.register_completed_song(existing_rec)

    # Candidate cloning the exact existing song
    clone_cand = {
        "key": "F#",
        "bpm": 90.0,
        "genre": "neo_soul",
        "plugins": ["Rhodes", "RC20"],
        "recipes": ["tape_rhodes_flutter"],
        "fingerprints": {"melodic": 0.40, "rhythmic": 0.45, "harmonic": 0.40, "timbre": 0.40, "arrangement": 0.40, "spatial": 0.40}
    }
    score = IdentityCritic.evaluate(clone_cand, catalog_memory=catalog)
    assert score.is_veto is True
    assert score.dimension == CriticDimension.IDENTITY
    assert "Canción intercambiable" in score.explanation


def test_memorability_critic_enforces_rule_of_one_or_two_events():
    # 0 events -> VETO
    zero_score = MemorabilityCritic.evaluate({"memorable_events": []})
    assert zero_score.is_veto is True
    assert "olvidable" in zero_score.explanation

    # >4 competing events -> VETO (Cognitive Overload)
    crowded_score = MemorabilityCritic.evaluate({"memorable_events": ["hook_1", "hook_2", "hook_3", "vocal_1", "ear_candy_1"]})
    assert crowded_score.is_veto is True
    assert "Saturación cognitiva" in crowded_score.explanation

    # 1 or 2 events -> PASS
    opt_score_1 = MemorabilityCritic.evaluate({"memorable_events": ["iconic_rhythmic_vacuum"]})
    assert opt_score_1.is_veto is False
    assert opt_score_1.score >= 0.85

    opt_score_2 = MemorabilityCritic.evaluate({"memorable_events": ["primary_motif", "reverse_vocal_hook"]})
    assert opt_score_2.is_veto is False
    assert opt_score_2.score >= 0.90


def test_predictability_critic_vetos_chaos_and_robotic_cliche():
    intent = ArtisticIntent(deviation_budget=0.35)

    # 1. Chaos VETO: Deviation far exceeds budget
    chaos_score = PredictabilityCritic.evaluate({
        "expectation_strength": 0.70,
        "deviation_amount": 0.75  # Budget 0.35 + 0.35 = 0.70 max
    }, intent=intent)
    assert chaos_score.is_veto is True
    assert "Caos musical" in chaos_score.explanation

    # 2. Cliche VETO: Zero deviation in repeated material
    cliche_score = PredictabilityCritic.evaluate({
        "expectation_strength": 0.85,
        "deviation_amount": 0.02,
        "has_repetitions": True
    }, intent=intent)
    assert cliche_score.is_veto is True
    assert "Predicibilidad robótica" in cliche_score.explanation

    # 3. Goldilocks balance -> PASS
    balanced_score = PredictabilityCritic.evaluate({
        "expectation_strength": 0.85,
        "deviation_amount": 0.28,
        "has_repetitions": True
    }, intent=intent)
    assert balanced_score.is_veto is False
    assert balanced_score.score >= 0.80


def test_emotional_critic_detects_empty_parameter_gymnastics():
    # High parameter volatility but flat perceived emotion -> VETO
    empty_gymnastics = {
        "parameter_delta": 0.85,
        "perceived_emotional_delta": 0.08,
        "emotional_coherence": 0.40
    }
    score = EmotionalCritic.evaluate(empty_gymnastics)
    assert score.is_veto is True
    assert "Gimnasia matemática vacía" in score.explanation

    # Authentic emotional impact -> PASS
    authentic = {
        "parameter_delta": 0.50,
        "perceived_emotional_delta": 0.65,
        "emotional_coherence": 0.92
    }
    pass_score = EmotionalCritic.evaluate(authentic)
    assert pass_score.is_veto is False
    assert pass_score.score >= 0.85


def test_human_plausibility_critic_detects_machine_signature():
    # Obvious machine generation: flat velocities + rigid symmetry + mechanical automation -> VETO
    machine_cand = {
        "sample_velocities": [100, 100, 100, 100],  # std dev = 0
        "rigid_symmetry": True,
        "unintentional_automation": True,
        "groove_pocket_affinity": 0.20
    }
    score = HumanPlausibilityCritic.evaluate(machine_cand)
    assert score.is_veto is True
    assert "Firma de máquina evidente" in score.explanation
    assert score.details["machine_signature_score"] >= 0.70

    # Human-like organic variation -> PASS
    human_cand = {
        "sample_velocities": [84, 102, 78, 115, 88, 96, 72, 108],  # dynamic organic phrasing
        "rigid_symmetry": False,
        "unintentional_automation": False,
        "groove_pocket_affinity": 0.90
    }
    human_score = HumanPlausibilityCritic.evaluate(human_cand)
    assert human_score.is_veto is False
    assert human_score.score >= 0.85


def test_sonic_signature_critic_demands_bespoke_sound():
    # All stock factory presets without sound design -> VETO
    stock_cand = {
        "all_stock_presets": True,
        "sonic_signature": None,
        "has_custom_sound_design": False
    }
    score = SonicSignatureCritic.evaluate(stock_cand)
    assert score.is_veto is True
    assert "Ausencia de firma sonora" in score.explanation

    # Bespoke sound design signature -> PASS
    bespoke_cand = {
        "all_stock_presets": False,
        "sonic_signature": "reverse Rhodes ghost note through tape delay and filtered vinyl dust",
        "has_custom_sound_design": True
    }
    bespoke_score = SonicSignatureCritic.evaluate(bespoke_cand)
    assert bespoke_score.is_veto is False
    assert bespoke_score.score >= 0.90


def test_cultural_genre_plausibility_critic_vetos_frankenstein_clash():
    intent = ArtisticIntent(genre_anchor="neo_soul", risk_tolerance=0.60, deviation_budget=0.35)

    # Incompatible clashing tropes -> VETO
    clash_cand = {
        "elements": ["drill_slides", "smooth_jazz_rhodes", "heavy_edm_white_noise"],
        "genre_deviation": 0.75
    }
    score = CulturalGenrePlausibilityCritic.evaluate(clash_cand, intent=intent)
    assert score.is_veto is True
    assert "Monstruo de Frankenstein" in score.explanation

    # Coherent style -> PASS
    coherent_cand = {
        "elements": ["extended_chords", "syncopated_bass", "foley_textures"],
        "genre_deviation": 0.20
    }
    coherent_score = CulturalGenrePlausibilityCritic.evaluate(coherent_cand, intent=intent)
    assert coherent_score.is_veto is False
    assert coherent_score.score >= 0.85


# =============================================================================
# 3. ARTISTIC CRITIC ENGINE ORCHESTRATION TESTS
# =============================================================================

def test_artistic_critic_engine_holistic_verdict():
    intent = ArtisticIntent.create_minimal_intimate("Whisper")

    # High quality candidate satisfying all 7 critics
    good_cand = {
        "id": "cand_01",
        "name": "Intimate Whisper Layer",
        "expectation_strength": 0.85,
        "deviation_amount": 0.25,
        "parameter_delta": 0.35,
        "perceived_emotional_delta": 0.55,
        "emotional_coherence": 0.90,
        "memorable_events": ["signature_gesture"],
        "sonic_signature": "felt piano hammer strike + room mic noise",
        "has_custom_sound_design": True,
        "sample_velocities": [68, 82, 60, 75, 70, 64],
        "fingerprints": {"melodic": 0.90, "rhythmic": 0.85, "harmonic": 0.88, "timbre": 0.90, "arrangement": 0.84, "spatial": 0.86},
        "elements": ["felt_keys", "room_tone"],
        "genre_deviation": 0.22,
    }

    verdict = ArtisticCriticEngine.critique_candidate(good_cand, intent=intent)
    assert verdict.passed is True
    assert verdict.overall_artistic_score >= 0.78
    assert len(verdict.vetos) == 0
    assert len(verdict.scores) == 7

    md = verdict.format_markdown_verdict()
    assert "ACEPTADO PARA PRODUCCIÓN" in md
    assert "Identity" in md


# =============================================================================
# 4. TASTE AND SELECTION LOOP (80-90% REJECTION) TESTS
# =============================================================================

def test_taste_and_selection_loop_enforces_ruthless_rejection_and_guided_healing():
    intent = ArtisticIntent.create_aggressive_dense("Kinetix Overload")
    dna = CompositionalDNA(
        song_id="song_kinetix",
        title="Kinetix Overload",
        tempo_bpm=155.0,
        primary_motif=PrimaryMotif(name="Screamer", tonal_center="F#"),
        negative_constraints=[NegativeConstraint.NO_UNEXTENDED_MAJOR_TRIADS]
    )

    # Execute loop
    result = TasteAndSelectionLoop.execute_loop(
        intent=intent,
        dna=dna,
        target_section="hook_1",
        strict_threshold=0.78
    )

    # 1. Must produce an accepted winning candidate
    assert result.accepted_candidate is not None
    assert result.winning_verdict is not None
    assert result.winning_verdict.passed is True

    # 2. Must reject substandard candidates (proves the rejection mechanism works)
    assert result.total_candidates_generated >= 4
    assert result.total_candidates_rejected >= 2
    assert result.rejection_rate >= 0.50

    # 3. Winning candidate has full 7-critic validation
    assert len(result.winning_verdict.scores) == 7
    assert len(result.winning_verdict.vetos) == 0
