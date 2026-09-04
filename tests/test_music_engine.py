# tests/test_music_engine.py
import unittest
import time
from engine.music.models import NoteEvent, Chord, Motif, PartFingerprint
from engine.music.intent import MusicalIntent
from engine.music.theory.notes import (
    note_to_midi, midi_to_note, pitch_class_to_name,
    get_enharmonic, normalize_pitch_class
)
from engine.music.theory.scales import (
    get_scale_notes, get_scale_pitch_classes,
    scale_degree_to_midi, midi_to_scale_degree,
    snap_to_scale, is_in_scale
)
from engine.music.harmony.roman import parse_roman_numeral, roman_progression_to_chords
from engine.music.harmony.generator import generate_harmonic_structure
from engine.music.voicing.profiles import apply_voicing_profile
from engine.music.voicing.voice_leading import optimize_voice_leading, voice_leading_cost
from engine.music.rhythm.generator import generate_drums
from engine.music.groove.profiles import apply_groove_to_notes, GROOVE_PROFILES
from engine.music.humanizer.engine import humanize_notes, apply_velocity_curve
from engine.music.motifs.motif import create_motif_from_notes
from engine.music.motifs.transformations import transform_motif, realize_motif_as_notes
from engine.music.motifs.memory import motif_memory
from engine.music.variation.engine import apply_variation
from engine.music.validation.constraints import validate_notes
from engine.music.validation.repair import repair_notes
from engine.music.midi.compiler import (
    compile_notes_to_ableton_format, compute_part_fingerprint, compare_fingerprints
)
from engine.music import music_engine
from engine.adapters.mock_adapter import MockAbletonAdapter
from engine.session.graph import SessionShadowGraph
from engine.models.session import TrackNode
from engine.transactions.manager import TransactionManager

class TestMusicTheory(unittest.TestCase):
    def test_note_midi_conversions(self):
        self.assertEqual(note_to_midi("C4"), 60)
        self.assertEqual(note_to_midi("A4"), 69)
        self.assertEqual(note_to_midi("F#3"), 54)
        self.assertEqual(note_to_midi("Bb1"), 34)
        self.assertEqual(midi_to_note(60), "C4")
        self.assertEqual(midi_to_note(69), "A4")

    def test_scales_and_degrees(self):
        c_major = get_scale_notes("C", "major")
        self.assertEqual(c_major, ["C", "D", "E", "F", "G", "A", "B"])
        
        a_minor = get_scale_notes("A", "natural_minor")
        self.assertEqual(a_minor, ["A", "B", "C", "D", "E", "F", "G"])

        # Scale degree to midi
        self.assertEqual(scale_degree_to_midi("C", "major", 1, 4), 60) # C4
        self.assertEqual(scale_degree_to_midi("C", "major", 5, 4), 67) # G4

        # Scale snapping
        self.assertTrue(is_in_scale("C", "major", 60))  # C
        self.assertFalse(is_in_scale("C", "major", 61)) # C#
        snapped = snap_to_scale("C", "major", 61)
        self.assertIn(snapped, [60, 62])


class TestHarmonyAndVoiceLeading(unittest.TestCase):
    def test_roman_numeral_parsing(self):
        # i in C minor -> Cm
        c1 = parse_roman_numeral("i", "C", "minor", duration=4.0)
        self.assertEqual(c1.root, "C")
        self.assertEqual(c1.quality, "minor")

        # VI in C minor -> Ab major
        c2 = parse_roman_numeral("VI", "C", "minor", duration=4.0)
        self.assertEqual(c2.root, "G#")  # G#/Ab enharmonic
        self.assertEqual(c2.quality, "major")

    def test_progression_generation(self):
        chords = roman_progression_to_chords("i - VI - III - VII", key="F", scale="natural_minor", bars=4)
        self.assertEqual(len(chords), 4)
        self.assertEqual(chords[0].root, "F")
        self.assertEqual(chords[0].quality, "minor")

    def test_voice_leading_optimization(self):
        chords = roman_progression_to_chords("i - VI - III - VII", key="C", scale="natural_minor", bars=4)
        # Unvoiced root positions
        raw_voicings = [apply_voicing_profile(ch, "close", register_center=60) for ch in chords]
        unoptimized_cost = sum(voice_leading_cost(raw_voicings[i], raw_voicings[i+1]) for i in range(len(raw_voicings)-1))

        # Optimized voice leading
        smooth_voicings = optimize_voice_leading(chords, register_center=60)
        optimized_cost = sum(voice_leading_cost(smooth_voicings[i], smooth_voicings[i+1]) for i in range(len(smooth_voicings)-1))

        self.assertLessEqual(optimized_cost, unoptimized_cost)


class TestRhythmGrooveAndHumanization(unittest.TestCase):
    def test_drum_generator(self):
        notes = generate_drums(genre="techno", bars=4, density=0.7, energy=0.8, seed=100)
        self.assertGreater(len(notes), 16)
        # Check that kick hits on quarter notes (start % 1.0 == 0.0)
        kick_notes = [n for n in notes if n.pitch == 36]
        self.assertGreaterEqual(len(kick_notes), 16)
        for kn in kick_notes:
            self.assertAlmostEqual(kn.start % 1.0, 0.0, places=3)

    def test_groove_application(self):
        notes = [NoteEvent.from_pitch_and_time(60, start=i*0.25, duration=0.2) for i in range(16)]
        grooved = apply_groove_to_notes(notes, profile_name="swing_16th_heavy", strength=1.0)
        # Step 1 (start 0.25) should be delayed due to swing
        self.assertGreater(grooved[1].start, notes[1].start)

    def test_humanization_seed_reproducibility(self):
        notes1 = [NoteEvent.from_pitch_and_time(60, start=i*0.25, duration=0.2, velocity=90) for i in range(8)]
        notes2 = [NoteEvent.from_pitch_and_time(60, start=i*0.25, duration=0.2, velocity=90) for i in range(8)]

        h1 = humanize_notes(notes1, role="LEAD", profile_name="pocket", strength=0.8, seed=999)
        h2 = humanize_notes(notes2, role="LEAD", profile_name="pocket", strength=0.8, seed=999)

        # Exact reproducibility
        for ev1, ev2 in zip(h1, h2):
            self.assertEqual(ev1.pitch, ev2.pitch)
            self.assertEqual(ev1.start, ev2.start)
            self.assertEqual(ev1.velocity, ev2.velocity)

    def test_velocity_curves(self):
        notes = [NoteEvent.from_pitch_and_time(60, start=i*1.0, duration=0.5, velocity=80) for i in range(4)]
        curved = apply_velocity_curve(notes, curve_type="linear", start_vel=50, end_vel=110)
        self.assertEqual(curved[0].velocity, 50)
        self.assertEqual(curved[-1].velocity, 110)


class TestMotifsAndTransformations(unittest.TestCase):
    def test_motif_creation_and_transformations(self):
        source_notes = [
            NoteEvent.from_pitch_and_time(60, start=0.0, duration=0.5, velocity=100),
            NoteEvent.from_pitch_and_time(63, start=0.5, duration=0.5, velocity=90),
            NoteEvent.from_pitch_and_time(65, start=1.0, duration=1.0, velocity=95),
        ]
        motif = create_motif_from_notes(name="test_motif", notes=source_notes, role="LEAD")
        self.assertEqual(motif.intervals, [0, 3, 5])
        self.assertEqual(len(motif.rhythm), 3)

        # Transpose
        transposed = transform_motif(motif, "transpose", {"semitones": 2})
        self.assertEqual(transposed.intervals, [2, 5, 7])

        # Invert around pivot 0
        inverted = transform_motif(motif, "invert", {"pivot": 0})
        self.assertEqual(inverted.intervals, [0, -3, -5])

        # Retrograde
        retro = transform_motif(motif, "retrograde")
        self.assertEqual(retro.intervals, [5, 3, 0])

        # Augmentation (half-time stretch)
        aug = transform_motif(motif, "augmentation", {"factor": 2.0})
        self.assertEqual(aug.length_beats, motif.length_beats * 2.0)

        # Realize as notes
        realized = realize_motif_as_notes(transposed, root_pitch=60, key="C", scale="natural_minor")
        self.assertEqual(len(realized), 3)
        self.assertEqual(realized[0].pitch, 62)  # 60 + 2

    def test_motif_memory(self):
        motif = Motif(id="m_unique_1", name="lead_hook", length_beats=4.0, intervals=[0, 2, 4], rhythm=[1, 1, 2], offsets=[0, 1, 2], accents=[0, 0, 0], role="lead")
        motif_memory.store_motif(motif)
        fetched = motif_memory.get_motif("lead_hook")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, "m_unique_1")


class TestValidationAndRepair(unittest.TestCase):
    def test_sub_bass_monophony_repair(self):
        # Two overlapping notes in sub-bass role
        poly_sub = [
            NoteEvent.from_pitch_and_time(36, start=0.0, duration=2.0),
            NoteEvent.from_pitch_and_time(40, start=1.0, duration=2.0),
        ]
        is_valid, warnings = validate_notes(poly_sub, role="SUB_BASS", key="C", scale="natural_minor")
        self.assertFalse(is_valid)

        repaired, actions = repair_notes(poly_sub, role="SUB_BASS", key="C", scale="natural_minor")
        self.assertTrue(len(actions) > 0)
        # Check that monophony was restored
        re_valid, _ = validate_notes(repaired, role="SUB_BASS", key="C", scale="natural_minor")
        self.assertTrue(re_valid)

    def test_register_bounds_repair(self):
        # Bass note way too high (pitch 80)
        high_bass = [NoteEvent.from_pitch_and_time(80, start=0.0, duration=1.0)]
        is_valid, warnings = validate_notes(high_bass, role="BASS", key="C", scale="natural_minor")
        self.assertFalse(is_valid)

        repaired, actions = repair_notes(high_bass, role="BASS", key="C", scale="natural_minor")
        self.assertLessEqual(repaired[0].pitch, 60)


class TestBatchCompilationAndFingerprinting(unittest.TestCase):
    def test_batch_compilation_performance(self):
        # Generate >1000 notes and benchmark compiler
        large_note_list = [
            NoteEvent.from_pitch_and_time(pitch=40 + (i % 30), start=i * 0.125, duration=0.1)
            for i in range(1500)
        ]
        t0 = time.perf_counter()
        compiled = compile_notes_to_ableton_format(large_note_list)
        t_elapsed = (time.perf_counter() - t0) * 1000  # ms

        self.assertEqual(len(compiled), 1500)
        self.assertLess(t_elapsed, 50.0, f"Compilation took {t_elapsed:.2f}ms, expected < 50ms")

    def test_part_fingerprint_and_similarity(self):
        notes_a = [NoteEvent.from_pitch_and_time(60 + (i%7), start=i*0.5, duration=0.4) for i in range(16)]
        notes_b = [NoteEvent.from_pitch_and_time(60 + (i%7), start=i*0.5, duration=0.4) for i in range(16)]
        notes_c = [NoteEvent.from_pitch_and_time(36, start=i*1.0, duration=0.2) for i in range(4)]

        fp_a = compute_part_fingerprint(notes_a)
        fp_b = compute_part_fingerprint(notes_b)
        fp_c = compute_part_fingerprint(notes_c)

        sim_identical = compare_fingerprints(fp_a, fp_b)
        self.assertAlmostEqual(sim_identical["overall_similarity"], 1.0, places=2)

        sim_different = compare_fingerprints(fp_a, fp_c)
        self.assertLess(sim_different["overall_similarity"], 0.8)


class TestTransactionsWithNotes(unittest.TestCase):
    def setUp(self):
        self.adapter = MockAbletonAdapter()
        self.graph = SessionShadowGraph()
        self.tm = TransactionManager(self.graph, self.adapter)

        # Add track 0 to mock adapter and graph
        self.adapter.create_midi_track()
        self.adapter.set_track_name(0, "Bassline")
        track_node = TrackNode(id="track_bass_01", ableton_index=0, name="Bassline", type="midi")
        track_node.metadata.role = "BASS"
        self.graph.add_track(track_node)

    def test_atomic_add_notes_and_rollback(self):
        # 1. Initial clip has 1 note
        initial_notes = [{"pitch": 36, "start_time": 0.0, "duration": 1.0, "velocity": 100}]
        self.adapter.add_notes_to_clip(0, 0, initial_notes)

        # 2. Stage transaction to replace with 8 rolling bass notes
        new_notes = [
            {"pitch": 41, "start_time": i * 0.25, "duration": 0.2, "velocity": 90}
            for i in range(8)
        ]
        tx = self.tm.begin(name="update_bass_notes")
        tx_id = tx.id if hasattr(tx, "id") else tx
        self.tm.stage_add_notes(tx_id, track_id="track_bass_01", clip_index=0, notes=new_notes, mode="replace")

        # 3. Commit transaction
        res = self.tm.commit(tx_id)
        self.assertEqual(res["status"], "COMMITTED")
        current_notes = self.adapter.get_clip_notes(0, 0)
        self.assertEqual(len(current_notes), 8)

        # 4. Rollback transaction and verify initial note is restored
        self.tm.rollback(tx_id)
        restored_notes = self.adapter.get_clip_notes(0, 0)
        self.assertEqual(len(restored_notes), 1)
        self.assertEqual(restored_notes[0]["pitch"], 36)


class TestMilestoneMultiTrackGeneration(unittest.TestCase):
    """
    Milestone verification: generates a coherent 16-bar section across
    Drums, Bass, Chords, and Melody (~60s at 128 BPM).
    """
    def test_milestone_multi_track_coordination(self):
        intent_drums = MusicalIntent(role="DRUMS", genre="melodic_techno", bars=16, energy=0.85, density=0.75, seed=42)
        intent_bass = MusicalIntent(role="BASS", style="rolling", key="F", scale="natural_minor", bars=16, seed=42)
        intent_chords = MusicalIntent(role="CHORDS", key="F", scale="natural_minor", bars=16, style="spread", seed=42)
        intent_lead = MusicalIntent(role="LEAD", key="F", scale="natural_minor", bars=16, style="arch", seed=42)

        # Generate each part
        drums_notes, drums_meta = music_engine.generate_part("DRUMS", intent_drums)
        bass_notes, bass_meta = music_engine.generate_part("BASS", intent_bass)
        chords_notes, chords_meta = music_engine.generate_part("CHORDS", intent_chords)
        lead_notes, lead_meta = music_engine.generate_part("LEAD", intent_lead)

        # Verification of generation counts
        self.assertGreater(len(drums_notes), 60)
        self.assertGreater(len(bass_notes), 50)
        self.assertGreater(len(chords_notes), 20)
        self.assertGreater(len(lead_notes), 20)

        # Validation checks
        self.assertTrue(drums_meta["validation"]["valid"])
        self.assertTrue(bass_meta["validation"]["valid"])
        self.assertTrue(chords_meta["validation"]["valid"])
        self.assertTrue(lead_meta["validation"]["valid"])

        # Quality scoring checks
        self.assertGreaterEqual(bass_meta["quality"]["harmonic"], 0.95)
        self.assertGreaterEqual(chords_meta["quality"]["harmonic"], 0.90)
        self.assertGreaterEqual(lead_meta["quality"]["harmonic"], 0.95)

if __name__ == "__main__":
    unittest.main()
