# tests/test_arrangement_intelligence_and_motif_dev.py
"""
Comprehensive Test Suite for Levels J, K, and L:
- Level J: Arrangement Intelligence (LayerOrchestrator, AnticipationAndSilenceWeaver, ArrangementIntelligenceEngine)
- Level K: Motif Development Engine & CompositoryMemory (4-dimensional transformation, genealogy)
- Level L: Emotional Arc Engine & NarrativeStagnationDetector (9D tensor, novelty delta, stagnation detection)
"""
import pytest
from engine.music.models import Motif, NoteEvent
from engine.music.motifs.motif_development_engine import MotifDevelopmentEngine, TransformationDimension
from engine.music.motifs.compository_memory import CompositoryMemory, MotifLineage, MotifEvolutionNode
from engine.arrangement.emotional_arc_engine import EmotionalArcEngine, EmotionalStateVector, SectionEmotionalProfile
from engine.arrangement.narrative_stagnation_detector import NarrativeStagnationDetector, StagnationIssue, StagnationAuditReport
from engine.arrangement.intelligence.layer_orchestrator import LayerOrchestrator, LayerOrchestrationPlan, SectionLayerPlan
from engine.arrangement.intelligence.anticipation_and_silence_weaver import AnticipationAndSilenceWeaver, AnticipationType
from engine.arrangement.intelligence.arrangement_intelligence_engine import ArrangementIntelligenceEngine, ArrangementIntelligenceAuditReport


@pytest.fixture
def sample_hook_motif():
    """A 4-bar melodic hook motif in Eb Minor."""
    return Motif(
        id="MOTIF_HOOK_LEAD",
        name="Alright Hook Lead",
        length_beats=16.0,
        intervals=[0, 3, 5, 7, 10, 12, 10, 7],  # Eb - Gb - Ab - Bb - Db - Eb - Db - Bb
        rhythm=[1.0, 1.0, 1.5, 0.5, 2.0, 2.0, 1.0, 1.0],
        offsets=[0.0, 1.0, 2.0, 3.5, 4.0, 6.0, 8.0, 10.0],
        accents=[1.0, 0.6, 0.9, 0.5, 1.0, 0.8, 0.7, 0.6],
        role="melody",
        section="Hook 1"
    )


@pytest.fixture
def standard_song_sections():
    """Classic modern commercial arrangement structure."""
    return [
        {"name": "Intro", "bars": 8},
        {"name": "Verse 1", "bars": 16},
        {"name": "Hook 1", "bars": 8},
        {"name": "Verse 2", "bars": 16},
        {"name": "Hook 2", "bars": 8},
        {"name": "Bridge", "bars": 8},
        {"name": "Hook 3", "bars": 8},
        {"name": "Outro", "bars": 8},
    ]


# ==============================================================================
# LEVEL K: MOTIF DEVELOPMENT & COMPOSITORY MEMORY TESTS
# ==============================================================================

def test_diatonic_inversion(sample_hook_motif):
    """Test mirroring intervals around a melodic pivot."""
    inverted = MotifDevelopmentEngine.apply_diatonic_inversion(sample_hook_motif, pivot_interval=0)
    assert len(inverted.intervals) == len(sample_hook_motif.intervals)
    # Original: [0, 3, 5, 7, 10, 12, 10, 7]
    # Inverted around 0: [0, -3, -5, -7, -10, -12, -10, -7]
    assert inverted.intervals[0] == 0
    assert inverted.intervals[1] == -3
    assert inverted.intervals[5] == -12
    assert "inverted" in inverted.name


def test_rhythmic_displacement(sample_hook_motif):
    """Test syncopated metric displacement."""
    displaced = MotifDevelopmentEngine.apply_rhythmic_displacement(sample_hook_motif, shift_beats=0.5)
    assert len(displaced.offsets) == len(sample_hook_motif.offsets)
    # Each offset shifted by +0.5 beats
    assert displaced.offsets[0] == 0.5
    assert displaced.offsets[1] == 1.5
    assert displaced.intervals == sample_hook_motif.intervals


def test_head_fragmentation(sample_hook_motif):
    """Test isolating the thematic head of the motif."""
    fragmented = MotifDevelopmentEngine.apply_head_fragmentation(sample_hook_motif, fraction=0.25)
    # Length is 16.0 * 0.25 = 4.0 beats
    assert fragmented.length_beats == 4.0
    assert len(fragmented.intervals) < len(sample_hook_motif.intervals)
    assert "head_frag" in fragmented.name


def test_augmentation_and_diminution(sample_hook_motif):
    """Test metric dilation and compression."""
    augmented = MotifDevelopmentEngine.apply_augmentation(sample_hook_motif, factor=2.0)
    assert augmented.length_beats == 32.0
    assert augmented.rhythm[0] == 2.0  # Was 1.0

    diminished = MotifDevelopmentEngine.apply_diminution(sample_hook_motif, factor=0.5)
    assert diminished.length_beats == 8.0
    assert diminished.rhythm[0] == 0.5


def test_role_transmutation(sample_hook_motif):
    """Test adapting a melodic motif to bass and texture roles."""
    bass_motif = MotifDevelopmentEngine.transmute_role(sample_hook_motif, target_role="bass")
    assert bass_motif.role == "bass"
    assert all(r >= 0.75 for r in bass_motif.rhythm)

    pad_motif = MotifDevelopmentEngine.transmute_role(sample_hook_motif, target_role="texture")
    assert pad_motif.role == "texture"
    assert pad_motif.rhythm[0] == 3.0  # 3x sustain for pad bed


def test_compository_memory_and_evolution_cycle(sample_hook_motif):
    """Test the full 4-stage narrative evolution cycle and memory registration."""
    memory = CompositoryMemory(song_id="alright_kendrick")
    evolutions = MotifDevelopmentEngine.synthesize_sectional_evolution_cycle(
        seed_motif=sample_hook_motif,
        memory=memory,
        key="Eb",
        scale="minor"
    )

    assert "Hook 1" in evolutions
    assert "Verse 2" in evolutions
    assert "Bridge" in evolutions
    assert "Hook 3" in evolutions

    # Check memory audit
    audit = memory.audit_compository_memory()
    assert audit["total_motifs"] == 1
    assert audit["is_thematically_developed"] is True
    assert audit["verdict"] == "THEMATIC_CONTINUITY"

    lineage = memory.get_lineage(sample_hook_motif.id)
    assert lineage is not None
    assert lineage.evolution_count == 4
    assert lineage.sections_visited == ["Hook 1", "Verse 2", "Bridge", "Hook 3"]


# ==============================================================================
# LEVEL L: EMOTIONAL ARC & STAGNATION DETECTOR TESTS
# ==============================================================================

def test_emotional_state_vector_math():
    """Test 9D emotional vector math, distance, and cosine similarity."""
    v1 = EmotionalStateVector(tension=0.2, release=0.1, density=0.3)
    v2 = EmotionalStateVector(tension=0.9, release=0.1, density=0.3)
    dist = v1.distance_to(v2)
    assert dist == pytest.approx(0.7, abs=0.01)

    cos_sim = v1.cosine_similarity(v1)
    assert cos_sim == pytest.approx(1.0, abs=0.001)


def test_emotional_arc_engine_timeline(standard_song_sections):
    """Test building 9D narrative arc across all sections."""
    profiles = EmotionalArcEngine.build_narrative_arc(standard_song_sections)
    assert len(profiles) == len(standard_song_sections)

    bridge_prof = [p for p in profiles if p.section_name == "Bridge"][0]
    hook3_prof = [p for p in profiles if p.section_name == "Hook 3"][0]

    # Bridge should have high tension and expectation
    assert bridge_prof.vector.tension >= 0.85
    assert bridge_prof.vector.expectation >= 0.90

    # Hook 3 should have peak release and density
    assert hook3_prof.vector.release >= 0.90
    assert hook3_prof.vector.density >= 0.90


def test_narrative_stagnation_detector_detects_identical():
    """Test that identical repeating hooks trigger stagnation alert."""
    h1 = SectionEmotionalProfile("Hook 1", (21, 28), EmotionalStateVector(tension=0.5, density=0.8), "Seed")
    h2_identical = SectionEmotionalProfile("Hook 2", (45, 52), EmotionalStateVector(tension=0.5, density=0.8), "Duplicate")

    issue = NarrativeStagnationDetector.compare_sections(h1, h2_identical, threshold=0.25)
    assert issue.is_stagnant is True
    assert issue.novelty_score == 0.0
    assert "Alerta de Estancamiento" in issue.diagnosis
    assert len(issue.suggested_interventions) >= 3


def test_narrative_stagnation_detector_approves_dynamic():
    """Test that evolved repeating hooks pass with healthy novelty."""
    h1 = SectionEmotionalProfile("Hook 1", (21, 28), EmotionalStateVector(tension=0.5, density=0.7, movement=0.6), "Seed")
    h3_evolved = SectionEmotionalProfile("Hook 3", (61, 68), EmotionalStateVector(tension=0.8, density=0.95, movement=0.95), "Climax")

    issue = NarrativeStagnationDetector.compare_sections(h1, h3_evolved, threshold=0.25)
    assert issue.is_stagnant is False
    assert issue.novelty_score >= 0.25
    assert "Evolución Saludable" in issue.diagnosis


# ==============================================================================
# LEVEL J: ARRANGEMENT INTELLIGENCE TESTS
# ==============================================================================

def test_layer_orchestrator_plans_and_contrast(standard_song_sections):
    """Test that layer orchestration ensures distinct instrument configurations."""
    plan = LayerOrchestrator.generate_orchestration_plan(standard_song_sections)
    assert len(plan.section_plans) == len(standard_song_sections)

    verse1_plan = [p for p in plan.section_plans if p.section_name == "Verse 1"][0]
    hook1_plan = [p for p in plan.section_plans if p.section_name == "Hook 1"][0]
    bridge_plan = [p for p in plan.section_plans if p.section_name == "Bridge"][0]

    # Hook 1 has Lead active, Verse 1 does not
    assert "LEAD" in hook1_plan.active_roles
    assert "LEAD" in verse1_plan.muted_roles

    # Bridge drops drums and kick
    assert "KICK" in bridge_plan.muted_roles
    assert "DRUMS" in bridge_plan.muted_roles

    # Audit contrast
    contrast = LayerOrchestrator.audit_contrast_between_sections(verse1_plan, hook1_plan)
    assert contrast["is_distinct"] is True
    assert contrast["verdict"] == "DIFFERENTIATED"


def test_anticipation_and_silence_weaver(standard_song_sections):
    """Test weaving pre-drop vacuums and phrase breaths at boundaries."""
    events = AnticipationAndSilenceWeaver.weave_anticipations(standard_song_sections)
    assert len(events) >= 2

    # Verify vacuum event before Hook 1 and before Hook 3
    vac_types = [e.event_type for e in events]
    assert AnticipationType.PRE_DROP_VACUUM in vac_types

    climax_event = [e for e in events if "Hook 3" in e.transition_name or "Bridge" in e.transition_name]
    assert len(climax_event) >= 1
    assert "KICK" in climax_event[0].affected_roles


def test_arrangement_intelligence_engine_full_audit(standard_song_sections):
    """Test end-to-end arrangement intelligence audit and scoring."""
    report = ArrangementIntelligenceEngine.analyze_and_orchestrate(
        sections=standard_song_sections,
        song_id="alright_kendrick_arr"
    )

    assert report.evolution_score >= 0.70
    assert report.is_development_complete is True
    assert report.verdict == "DYNAMIC_NARRATIVE_DEVELOPMENT"
    assert len(report.anticipations) >= 2
    assert len(report.emotional_profiles) == len(standard_song_sections)
    assert report.stagnation_audit.is_arrangement_dynamic is True
