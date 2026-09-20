"""
Creative Evolution Suite Tests:
Validates MusicDNA, LeitmotifEngine, ClicheDetector, TimbreDNA,
TurnaroundEngine, HumanizerEngine, EnergyCurveEngine, MicroAutomationsPass,
and MusicDirector.
"""

import pytest
from engine.creative import (
    MusicDNA,
    LeitmotifEngine,
    ClicheDetector,
    ClicheAuditReport
)
from engine.sound.timbre_dna import TimbreDNA, TimbreRelationshipMatrix
from engine.production.copilot.phases.phase_6.turnaround_engine import TurnaroundEngine
from engine.music.humanizer import HumanizerEngine
from engine.arrangement.energy_curve import EnergyCurveEngine
from engine.production.copilot.phases.phase_7.micro_automations import MicroAutomationsPass
from engine.production.copilot.phases.phase_10.music_director import MusicDirector
from engine.core.roles import RoleClassifier, CanonicalRole
from engine.mix.gain_staging.auto_stager import AutoGainStagingEngine
from engine.mix.spatial_panning import InstrumentPanningEvaluator


def test_music_dna_generation_and_serialization():
    dna = MusicDNA.generate_for_concept("nocturnal trap in F minor", genre="trap", bpm=140.0, key="F", mode="Aeolian")
    assert dna.identity.concept == "nocturnal trap in F minor"
    assert dna.rhythm.signature_pattern == "3-3-2"
    assert dna.harmony.tonal_center == "F"
    
    d = dna.to_dict()
    assert "rhythm" in d and "harmony" in d and "structure" in d
    rebuilt = MusicDNA.from_dict(d)
    assert rebuilt.rhythm.signature_pattern == dna.rhythm.signature_pattern


def test_leitmotif_engine_section_mutations():
    engine = LeitmotifEngine()
    # Intro: sparse high-register texture
    intro_notes = engine.realize_for_section("Intro", root_pitch=60)
    assert len(intro_notes) > 0
    assert all(n["pitch"] >= 72 for n in intro_notes)

    # Verse: bass register
    verse_notes = engine.realize_for_section("Verse", root_pitch=60)
    assert len(verse_notes) > 0
    assert all(n["pitch"] <= 48 for n in verse_notes)

    # Drop: full lead statement
    drop_notes = engine.realize_for_section("Drop", root_pitch=60)
    assert len(drop_notes) >= len(intro_notes)


def test_cliche_detector_and_fitness_score():
    detector = ClicheDetector()
    
    # Robotic flat velocity notes
    robotic_notes = [{"pitch": 60, "time": float(i), "duration": 0.5, "velocity": 100} for i in range(16)]
    report = detector.audit_notes(robotic_notes, role="lead")
    assert "robotic_flat_velocity" in report.cliches_detected
    assert report.musical_quality < 1.0

    # Turnaround identical check
    b4 = [{"pitch": 60, "time": 0.0}, {"pitch": 62, "time": 1.0}]
    b8 = [{"pitch": 60, "time": 0.0}, {"pitch": 62, "time": 1.0}]
    t_report = detector.audit_turnaround(b4, b8)
    assert "identical_bar_8_and_4" in t_report.cliches_detected


def test_timbre_dna_and_collision_detection():
    # Role defaults
    kick_dna = TimbreRelationshipMatrix.get_default_for_role("KICK")
    assert kick_dna.transient_strength >= 0.90
    assert kick_dna.stereo_width == 0.0

    pad_dna = TimbreRelationshipMatrix.get_default_for_role("PAD")
    assert pad_dna.stereo_width >= 0.80

    # Synthesis parameters translation
    params = pad_dna.to_synthesis_parameters()
    assert "FILTER_CUTOFF" in params
    assert "UNISON_DETUNE" in params
    assert params["UNISON_DETUNE"] > 0.5

    # Collision detection
    bright_a = TimbreDNA(brightness=0.85, stereo_width=0.75)
    bright_b = TimbreDNA(brightness=0.80, stereo_width=0.70)
    collision = TimbreRelationshipMatrix.evaluate_collision("LEAD_A", bright_a, "LEAD_B", bright_b)
    assert collision["collision_detected"] is True


def test_turnaround_engine_variations():
    # 8-bar drum pattern (32 beats)
    notes = []
    for bar in range(8):
        notes.append({"pitch": 38, "start_time": bar * 4.0 + 1.0, "duration": 0.5, "velocity": 100})
        notes.append({"pitch": 38, "start_time": bar * 4.0 + 3.0, "duration": 0.5, "velocity": 100})

    assert TurnaroundEngine.is_bar_8_identical(notes) is True

    # Apply drum fill turnaround
    varied = TurnaroundEngine.apply_turnaround(notes, role="drums", turnaround_type="drum_fill", total_bars=8)
    # Check that bar 8 notes were replaced with fill crescendo
    b8_notes = [n for n in varied if 28.0 <= n["start_time"] < 32.0]
    assert len(b8_notes) > 2


def test_humanizer_engine_physics_and_microtiming():
    notes = [{"pitch": 60, "start_time": float(i) * 0.25, "duration": 0.20, "velocity": 100} for i in range(16)]
    humanized = HumanizerEngine.humanize_clip(notes, bpm=120.0, role="drums")
    
    # Velocities should have variation
    vels = [n["velocity"] for n in humanized]
    assert len(set(vels)) > 1

    # Timings should have subtle displacement
    times = [n["start_time"] for n in humanized]
    assert any(abs(t - round(t, 2)) > 0.0001 for t in times)


def test_energy_curve_and_contrast():
    sections = [
        {"name": "Intro", "bars": 8},
        {"name": "Verse", "bars": 16},
        {"name": "Buildup", "bars": 8},
        {"name": "Drop 1", "bars": 16},
        {"name": "Puente", "bars": 8},
        {"name": "Drop 2 (Climax)", "bars": 16},
        {"name": "Outro", "bars": 8}
    ]
    curve = EnergyCurveEngine.build_song_energy_curve(sections)
    assert len(curve) > 0
    contrast = EnergyCurveEngine.evaluate_contrast(sections)
    assert contrast["is_balanced"] is True
    assert contrast["dynamic_range"] >= 0.50


def test_new_roles_classification_and_staging():
    # Taxonomy
    assert RoleClassifier.classify("Synth Arp Pluck") == CanonicalRole.COUNTER_LEAD
    assert RoleClassifier.classify("Vinyl Rain Foley") == CanonicalRole.TEXTURE_FOLEY
    assert RoleClassifier.classify("Ear Candy Bells") == CanonicalRole.EAR_CANDY

    # Gain staging
    assert AutoGainStagingEngine.classify_role("Counter Lead") == "counter_lead"
    assert AutoGainStagingEngine.HIERARCHY_TARGETS["counter_lead"] == -17.0
    assert AutoGainStagingEngine.HIERARCHY_TARGETS["ear_candy"] == -19.0
    assert AutoGainStagingEngine.HIERARCHY_TARGETS["foley"] == -24.0

    # Panning
    assert InstrumentPanningEvaluator.DEFAULT_ROLE_PAN_TARGETS["COUNTER_LEAD"] == -0.22
    assert InstrumentPanningEvaluator.DEFAULT_ROLE_PAN_TARGETS["EAR_CANDY"] == 0.35


def test_music_director_predictability_and_mutation():
    class MockSession:
        def __init__(self):
            self.data = {
                "tracks": [
                    {"name": "Kick", "role": "KICK", "notes_count": 64},
                    {"name": "Lead", "role": "LEAD", "notes_count": 32}
                ],
                "sections": [
                    {"name": "Intro", "bars": 8},
                    {"name": "Verse", "bars": 16},
                    {"name": "Drop", "bars": 16}
                ]
            }

    session = MockSession()
    audit = MusicDirector.audit_predictability(session)
    assert "missing_call_and_response" in audit["issues_detected"]
    assert "lacks_ear_candy_transients" in audit["issues_detected"]

    # Surgical mutation
    mutation = MusicDirector.mutate_layer(session, conn=None, layer="melody")
    assert mutation["status"] == "MUTATION_COMPLETED"
    assert "Lead" in mutation["mutated_elements"]
