# tests/test_compositional_dna_and_taste_engine.py
"""
Comprehensive Test Suite for:
1. Compositional DNA & Negative Constraints (Phase P)
2. Composition Mutation Engine (Phase M)
3. Expectation & Deviation Engine (Phase N)
4. Catalog Identity & Memory (Phase O)
5. Generative Taste Engine (Phase P+)
6. Audio ➔ Analysis ➔ Learning & Production Memory Hub
"""
import pytest
from typing import Dict, List, Any

# 1. Compositional DNA Imports
from engine.composition import (
    CompositionalDNA,
    NegativeConstraint,
    PrimaryMotif,
    MotifNote,
    SignatureRhythm,
    HarmonicPalette,
    InstrumentationRules,
    TimbralPalette,
    SignatureGesture
)

# 2. Composition Mutation Imports
from engine.music.models import Chord
from engine.music.composition_mutation_engine import (
    CompositionMutationEngine,
    MutationType,
    MutationResult
)

# 3. Expectation & Deviation Imports
from engine.arrangement.expectation_deviation_engine import (
    ExpectationDeviationEngine,
    ExpectationStage,
    DeviationMechanism,
    ConsequenceReward,
    DeviationPlan
)

# 4. Catalog Identity Imports
from engine.memory.catalog_memory import (
    CatalogMemory,
    SongCatalogRecord,
    CatalogConflict,
    ConflictSeverity
)

# 5. Generative Taste Engine Imports
from engine.creative.generative_taste_engine import (
    GenerativeTasteEngine,
    CandidateType,
    TasteScoreCard,
    ArtisticCandidate,
    AuditionDecision
)

# 6. Learning & Hub Imports
from engine.memory.production_learning import (
    ProductionLearningEngine,
    AcousticAnalysisResult,
    LearnedProductionWisdom
)
from engine.memory.production_memory_hub import (
    ProductionMemoryHub,
    MemoryPerspectiveReport
)


# ============================================================================
# 1. Compositional DNA & Negative Constraints Tests
# ============================================================================

def test_compositional_dna_creation_and_intervals():
    motif_notes = [
        MotifNote(pitch=63, start_time=0.0, duration=0.5),   # Eb4
        MotifNote(pitch=66, start_time=0.5, duration=0.5),   # Gb4 (+3)
        MotifNote(pitch=70, start_time=1.0, duration=1.0),   # Bb4 (+4)
        MotifNote(pitch=73, start_time=2.0, duration=0.75),  # Db5 (+3)
        MotifNote(pitch=75, start_time=3.0, duration=1.0),   # Eb5 (+2)
    ]
    motif = PrimaryMotif(name="Alright Lead Theme", notes=motif_notes, tonal_center="Eb")
    assert motif.interval_signature == [3, 4, 3, 2]

    gesture = SignatureGesture(
        id="gest_01",
        name="Pre-Hook Vacuum Drop",
        trigger_section="Hook 3",
        bar_offset=3.0,
        description="2-beat silence before explosive drop",
        musical_role="PRE_DROP_VACUUM"
    )

    dna = CompositionalDNA(
        song_id="song_kendrick_alright",
        title="Alright Neo-Soul Reinterpretation",
        bpm=110.0,
        primary_motif=motif,
        signature_gestures=[gesture]
    )

    assert dna.bpm == 110.0
    assert len(dna.signature_gestures) == 1
    assert NegativeConstraint.NO_UNEXTENDED_MAJOR_TRIADS in dna.negative_constraints


def test_dna_negative_constraints_rejection():
    dna = CompositionalDNA(song_id="test_dna", title="Constraint Test")

    # 1. Reject bare major triad
    valid, msg = dna.validate_constraint("CHORD", {"quality": "major", "extensions": []})
    assert not valid
    assert "Bare unextended major triads are forbidden" in msg

    # Allowed if extended
    valid_ext, _ = dna.validate_constraint("CHORD", {"quality": "major9", "extensions": ["9"]})
    assert valid_ext

    # 2. Reject straight four-on-the-floor hats
    straight_hats = [
        {"start_time": 0.0, "pitch": 42},
        {"start_time": 1.0, "pitch": 42},
        {"start_time": 2.0, "pitch": 42},
        {"start_time": 3.0, "pitch": 42},
    ]
    valid_hats, msg_hats = dna.validate_constraint("DRUM_PATTERN", {"role": "HATS", "notes": straight_hats})
    assert not valid_hats
    assert "Straight 4-on-the-floor hi-hats forbidden" in msg_hats

    # 3. Reject downbeat crash
    valid_crash, msg_crash = dna.validate_constraint("CRASH", {"beat": 0.0})
    assert not valid_crash
    assert "Crash cymbal on downbeat beat 1 is forbidden" in msg_crash

    # 4. Reject identical hook repetition
    valid_rep, msg_rep = dna.validate_constraint(
        "SECTION_REPETITION",
        {"section_a": "Hook 1", "section_b": "Hook 3", "similarity": 0.95}
    )
    assert not valid_rep
    assert "Evolution required" in msg_rep


def test_dna_serialization_roundtrip():
    dna = CompositionalDNA(song_id="dna_ser_01", title="Serialization Test", bpm=115.0)
    data = dna.to_dict()
    restored = CompositionalDNA.from_dict(data)
    assert restored.song_id == dna.song_id
    assert restored.bpm == 115.0
    assert len(restored.negative_constraints) == len(dna.negative_constraints)


# ============================================================================
# 2. Composition Mutation Engine Tests
# ============================================================================

def test_composition_mutation_tritone_substitution():
    chords = [
        Chord(root="Eb", quality="minor7", duration=4.0),
        Chord(root="Bb", quality="dominant7", duration=4.0),
    ]
    # Tritone sub of Bb7 is E7 (half-step above Eb target)
    mutated = CompositionMutationEngine.apply_tritone_substitution(chords, target_idx=1)
    assert mutated[1].root == "E"
    assert mutated[1].quality == "dominant7"
    assert "SubV7/E" in mutated[1].roman_numeral


def test_composition_mutation_modal_borrowing_and_extensions():
    chords = [
        Chord(root="Eb", quality="minor7", duration=4.0),
        Chord(root="Ab", quality="minor7", duration=4.0),
    ]
    # Dorian modal borrowing converts minor Ab into major Ab7 (IV in Eb Dorian)
    mutated_dorian = CompositionMutationEngine.apply_modal_borrowing(chords, source_mode="dorian", borrow_idx=1)
    assert mutated_dorian[1].quality == "major7"
    assert "IV_dorian" in mutated_dorian[1].roman_numeral

    # Extensions
    extended = CompositionMutationEngine.apply_extensions(chords, ["9", "11"])
    assert "9" in extended[0].extensions
    assert "11" in extended[0].extensions
    assert extended[0].quality == "minor9"


def test_composition_mutation_pedal_bass_and_turnaround():
    chords = [
        Chord(root="Eb", quality="minor7", duration=4.0),
        Chord(root="Ab", quality="minor7", duration=4.0),
        Chord(root="Db", quality="major7", duration=4.0),
        Chord(root="Bb", quality="dominant7", duration=4.0),
    ]
    # Pedal bass locks bass notes to Eb
    pedal_chords = CompositionMutationEngine.apply_pedal_bass(chords, pedal_pitch="Eb")
    for c in pedal_chords:
        assert c.bass_note == "Eb"

    # Turnaround reharmonization appends subV7 chord on final bar
    reharm = CompositionMutationEngine.reharmonize_turnaround(chords, tension=0.8)
    assert len(reharm) == 5
    assert reharm[-1].duration == 1.0
    assert reharm[-1].root == "E"  # SubV7 of Eb


def test_composition_mutation_narrative_context():
    chords = [
        Chord(root="Eb", quality="minor7", duration=4.0),
        Chord(root="Bb", quality="dominant7", duration=4.0),
    ]
    # Hook 3 climax mutation
    res = CompositionMutationEngine.mutate_for_narrative_context(chords, "Hook 3", emotional_intensity=0.85)
    assert res.dna_coherence_score >= 0.90
    assert MutationType.SELECTIVE_TURNAROUND_REHARM in res.techniques_applied
    assert MutationType.RESOLUTION_DISPLACEMENT in res.techniques_applied
    assert "Climactic turnaround reharmonization" in res.narrative_justification


# ============================================================================
# 3. Expectation & Deviation Engine Tests
# ============================================================================

def test_expectation_deviation_design():
    # Hook 1: Pattern building (no deviation yet)
    assert not ExpectationDeviationEngine.should_trigger_deviation("Hook 1", repetition_count=1)

    # Hook 3: Pattern broken
    assert ExpectationDeviationEngine.should_trigger_deviation("Hook 3", repetition_count=3)
    plan = ExpectationDeviationEngine.design_deviation("Hook 3", repetition_count=3)

    assert plan.mechanism == DeviationMechanism.RHYTHMIC_VACUUM
    assert plan.consequence == ConsequenceReward.CLIMACTIC_BRASS_FANFARE
    assert plan.tension_multiplier >= 1.50
    assert "rhythmic absence" in plan.narrative_rule.lower()


def test_expectation_deviation_vacuum_and_consequence():
    drum_notes = [
        {"pitch": 36, "start_time": 12.0, "duration": 0.25},  # Kick bar 4 beat 1
        {"pitch": 36, "start_time": 13.0, "duration": 0.25},  # Kick bar 4 beat 2 (in vacuum!)
        {"pitch": 38, "start_time": 14.0, "duration": 0.25},  # Snare bar 4 beat 3 (in vacuum!)
        {"pitch": 42, "start_time": 13.5, "duration": 0.25},  # Hat (allowed or kept)
        {"pitch": 38, "start_time": 15.0, "duration": 0.25},  # Snare bar 4 beat 4
    ]

    vacuum_applied = ExpectationDeviationEngine.apply_rhythmic_vacuum(
        drum_notes, vacuum_bar_start=3.0, vacuum_beat_duration=2.0
    )
    # Kicks and snares in beats [13.0, 15.0) must be excised
    starts = [n["start_time"] for n in vacuum_applied if n["pitch"] in (36, 38)]
    assert 13.0 not in starts
    assert 14.0 not in starts
    assert 12.0 in starts
    assert 15.0 in starts

    # Generate high fanfare consequence
    fanfare = ExpectationDeviationEngine.synthesize_consequence_fanfare(tonal_center="Eb", start_beat=14.5)
    assert len(fanfare) == 5
    assert fanfare[-1]["pitch"] == 87  # Eb6 soaring climax


# ============================================================================
# 4. Catalog Identity & Memory Tests
# ============================================================================

def test_catalog_memory_cliche_detection():
    catalog = CatalogMemory()

    # Register Song 1
    song_01 = SongCatalogRecord(
        song_id="song_01",
        title="Midnight Rhodes",
        key_root="Eb",
        scale="minor",
        bpm=110.0,
        instrument_roles={"KEYS": "Rhodes Stage-73", "BASS": "SubLab 808"},
        sound_design_recipes=["vinyl_dust", "reverse_vocal"]
    )
    catalog.register_song(song_01)
    assert len(catalog.records) == 1

    # Propose Song 2 with identical recipe
    conflicts = catalog.audit_proposal(
        proposed_instruments={"KEYS": "Rhodes Stage-73", "BASS": "SubLab 808"},
        proposed_recipes=["vinyl_dust", "reverse_vocal"],
        key_root="Eb",
        bpm=110.0,
        current_song_id="song_02"
    )

    assert len(conflicts) >= 1
    conflict = conflicts[0]
    assert conflict.severity in (ConflictSeverity.WARNING, ConflictSeverity.CRITICAL_CLICHE)
    assert "Catalog Redundancy Conflict" in conflict.warning_message
    assert len(conflict.suggested_alternatives) > 0

    # Propose Song 3 with divergent recipe (no conflict)
    clean_proposal = catalog.audit_proposal(
        proposed_instruments={"KEYS": "FM Bells Synthesizer", "BASS": "Moog Ladder Bass"},
        proposed_recipes=["cassette_hiss", "foley_water"],
        key_root="G",
        bpm=140.0,
        current_song_id="song_03"
    )
    assert len(clean_proposal) == 0


def test_catalog_diversity_index():
    catalog = CatalogMemory()
    song_a = SongCatalogRecord(song_id="a", title="Song A", key_root="Eb", scale="minor", bpm=110.0)
    song_b = SongCatalogRecord(song_id="b", title="Song B", key_root="F#", scale="minor", bpm=135.0)
    catalog.register_song(song_a)
    catalog.register_song(song_b)

    index = catalog.calculate_catalog_diversity_index()
    assert 0.0 < index <= 1.0


# ============================================================================
# 5. Generative Taste Engine Tests
# ============================================================================

def test_generative_taste_multi_candidates_and_ten_dimensions():
    dna = CompositionalDNA(song_id="taste_dna", title="Taste Test Song", bpm=110.0)
    base_notes = [
        {"pitch": 63, "start_time": 0.0, "duration": 1.0, "velocity": 90},
        {"pitch": 66, "start_time": 1.0, "duration": 1.0, "velocity": 90},
        {"pitch": 70, "start_time": 2.0, "duration": 2.0, "velocity": 90},
        {"pitch": 73, "start_time": 12.0, "duration": 2.0, "velocity": 90},
    ]

    # Generate 3 concurrent hypotheses
    candidates = GenerativeTasteEngine.generate_hook_candidates("Hook 3", base_notes, dna)
    assert len(candidates) == 3
    types = {c.type for c in candidates}
    assert CandidateType.HARMONIC_MUTATION in types
    assert CandidateType.RHYTHMIC_DISPLACEMENT in types
    assert CandidateType.TIMBRAL_TEXTURE in types

    # Evaluate each candidate
    for cand in candidates:
        card = GenerativeTasteEngine.evaluate_candidate(cand, dna, is_final_climax=True)
        assert 0.0 <= card.musical_taste_score <= 1.0
        assert 0.0 <= card.sonic_taste_score <= 1.0
        assert 0.0 <= card.composite_artistic_score() <= 1.0

    # Adjudicate winner with risk appetite
    decision = GenerativeTasteEngine.adjudicate_taste(candidates, dna, risk_appetite=0.75)
    assert decision.selected_winner is not None
    assert decision.runner_up is not None
    assert "selected as artistic winner" in decision.artistic_justification
    assert "Risk index" in decision.risk_reward_rationale
    assert "clip slot 7" in decision.ab_audition_guidance


# ============================================================================
# 6. Production Learning & Memory Hub Tests
# ============================================================================

def test_production_learning_wisdom_extraction():
    learner = ProductionLearningEngine()
    acoustic_data = AcousticAnalysisResult(
        rms_dbfs=-16.99,
        true_peak_dbtp=-13.20,
        crest_factor_db=3.79,
        mono_compatibility_loss_db=0.00,
        novelty_surprise_score=0.35
    )

    wisdom = learner.evaluate_and_learn(
        song_id="song_alright",
        section="Hook 3",
        key_root="Eb",
        intervention_applied="2-beat rhythmic vacuum followed by high fanfare",
        acoustic_evidence=acoustic_data,
        taste_score=0.94
    )

    assert "Zero phase cancellation" in wisdom.why_it_worked
    assert "Hook 3" in wisdom.generalizable_rule
    assert wisdom.confidence_score >= 0.90

    # Query wisdom
    queried = learner.query_wisdom(target_section="Hook 3", key_root="Eb")
    assert len(queried) == 1
    assert queried[0].wisdom_id == wisdom.wisdom_id


def test_production_memory_hub_consultation():
    hub = ProductionMemoryHub()

    # Pre-register a song in catalog
    past_song = SongCatalogRecord(
        song_id="past_01",
        title="Old Song",
        key_root="Eb",
        scale="minor",
        bpm=110.0,
        instrument_roles={"KEYS": "Analog Lab V Rhodes"},
        sound_design_recipes=["vinyl_dust"]
    )
    hub.catalog_memory.register_song(past_song)

    # Consult hub with distinct non-colliding proposal
    report = hub.consult_memories(
        section_name="Hook 3",
        song_id="new_song_02",
        key_root="F#",
        bpm=130.0,
        proposed_instruments={"KEYS": "FM Bells"},
        proposed_recipes=["cassette_hiss"]
    )

    assert report.all_clear_to_proceed
    assert "All 4 memories approve" in report.artistic_recommendation
    assert report.section_name == "Hook 3"
