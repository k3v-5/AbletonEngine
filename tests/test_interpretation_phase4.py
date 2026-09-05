# tests/test_interpretation_phase4.py
"""
Test Suite for Phase 4: Interpretation, Dynamics & Human Groove.
Validates:
1. DynamicGrooveHumanizer: Micro-timing, MPC 60 58% swing, Gaussian velocity variance.
2. PhysicalChordStrummer: Polyphonic chord grouping, finger-roll staggering, velocity tilt.
3. MPEExpressionEngine: Attack scoops, delayed vibrato curves, expressive note modifiers.
4. DrumGhostNoteInjector: Turnaround ghost snares, hi-hat 4-step velocity waves.
5. ExecutiveCopilotEngine: Phase 4 decision discovery and interactive execution.
"""

import pytest
import math
from engine.music.models import NoteEvent
from engine.music.groove.humanizer import DynamicGrooveHumanizer
from engine.music.harmony.strum import PhysicalChordStrummer
from engine.music.expression.mpe import MPEExpressionEngine, PitchBendPoint, ExpressiveNoteModifier
from engine.music.drums.ghost_notes import DrumGhostNoteInjector
from engine.production.copilot.stepper import ExecutiveCopilotEngine, ProductionPhase


class TestDynamicGrooveHumanizer:
    """Tests for MPC 60 hardware swing and micro-timing humanization."""

    def test_mpc60_swing_timing_displacement(self):
        # Create a straight 16th-note pattern (0.0, 0.25, 0.50, 0.75, 1.0...)
        notes = [
            NoteEvent(pitch=42, start=float(i) * 0.25, duration=0.20, velocity=100)
            for i in range(16)
        ]
        humanized = DynamicGrooveHumanizer.humanize_notes(
            notes=notes,
            role="drums",
            pocket_style="atlanta_trap",
            tempo=142.0,
            strength=1.0,
            swing_percentage=58.0,
            seed=42
        )
        assert len(humanized) == 16
        # Even 16th steps (0, 2, 4...) stay near grid; odd steps (1, 3, 5...) are delayed
        for i in range(len(humanized)):
            step = i % 4
            if step in [1, 3]:  # off-beat 16ths
                # Should have positive delay relative to straight grid
                assert humanized[i].start >= notes[i].start

    def test_velocity_humanization_range(self):
        notes = [
            NoteEvent(pitch=42, start=float(i) * 0.25, duration=0.20, velocity=100)
            for i in range(16)
        ]
        humanized = DynamicGrooveHumanizer.humanize_notes(notes=notes, strength=1.0, seed=42)
        vels = [n.velocity for n in humanized]
        # Not all velocities should be identical
        assert len(set(vels)) > 1
        # All velocities must be within valid MIDI range
        assert all(1 <= v <= 127 for v in vels)

    def test_dict_notes_roundtrip(self):
        dict_notes = [
            {"pitch": 36, "start_time": 0.0, "duration": 0.5, "velocity": 100},
            {"pitch": 38, "start_time": 1.0, "duration": 0.5, "velocity": 100}
        ]
        res = DynamicGrooveHumanizer.humanize_clip_dict_notes(dict_notes)
        assert len(res) == 2
        assert "start_time" in res[0]
        assert "velocity" in res[0]


class TestPhysicalChordStrummer:
    """Tests for physical keyboard finger-roll chord strumming and velocity tilt."""

    def test_chord_staggering(self):
        # 4-note chord starting at beat 0.0
        chord = [
            NoteEvent(pitch=53, start=0.0, duration=2.0, velocity=90),  # F3
            NoteEvent(pitch=60, start=0.0, duration=2.0, velocity=90),  # C4
            NoteEvent(pitch=65, start=0.0, duration=2.0, velocity=90),  # F4
            NoteEvent(pitch=68, start=0.0, duration=2.0, velocity=90),  # Ab4
        ]
        strummed = PhysicalChordStrummer.strum_notes(
            notes=chord,
            tempo=142.0,
            strum_ms=14.0,
            direction="up"
        )
        assert len(strummed) == 4
        # Notes should have distinct, ascending start times
        starts = [n.start for n in strummed]
        assert starts[0] < starts[1] < starts[2] < starts[3]
        # Duration should be adjusted so chord ends together
        assert strummed[-1].duration < strummed[0].duration

    def test_alternating_strum_direction(self):
        # Chord 1 at bar 0 (beat 0.0) -> UP strum
        # Chord 2 at bar 1 (beat 4.0) -> DOWN strum
        notes = [
            # Bar 0
            NoteEvent(pitch=53, start=0.0, duration=2.0, velocity=90),
            NoteEvent(pitch=65, start=0.0, duration=2.0, velocity=90),
            # Bar 1
            NoteEvent(pitch=53, start=4.0, duration=2.0, velocity=90),
            NoteEvent(pitch=65, start=4.0, duration=2.0, velocity=90),
        ]
        strummed = PhysicalChordStrummer.strum_notes(notes=notes, direction="alternating")
        assert len(strummed) == 4

        bar0_notes = [n for n in strummed if n.start < 2.0]
        bar1_notes = [n for n in strummed if n.start >= 4.0]

        # Bar 0 (even bar): up-strum -> lower pitch starts first
        bar0_sorted_by_time = sorted(bar0_notes, key=lambda n: n.start)
        assert bar0_sorted_by_time[0].pitch < bar0_sorted_by_time[1].pitch

        # Bar 1 (odd bar): down-strum -> higher pitch starts first
        bar1_sorted_by_time = sorted(bar1_notes, key=lambda n: n.start)
        assert bar1_sorted_by_time[0].pitch > bar1_sorted_by_time[1].pitch

    def test_strum_dict_notes(self):
        d_notes = [
            {"pitch": 60, "start_time": 0.0, "duration": 1.0, "velocity": 85},
            {"pitch": 64, "start_time": 0.0, "duration": 1.0, "velocity": 85}
        ]
        res = PhysicalChordStrummer.strum_dict_notes(d_notes)
        assert len(res) == 2
        assert res[0]["start_time"] != res[1]["start_time"]


class TestMPEExpressionEngine:
    """Tests for continuous pitch bend, vocal scoops, and vibrato."""

    def test_note_scoop_and_vibrato_generation(self):
        # Long sustained note (3 beats long)
        bends = MPEExpressionEngine.generate_pitch_bend_envelope_for_note(
            start_beat=0.0,
            duration=3.0,
            tempo=142.0,
            enable_scoop=True,
            enable_vibrato=True
        )
        assert len(bends) > 10
        # First point should be negative (attack scoop below target)
        assert bends[0].bend_semitones < 0.0
        # Must return to 0.0 at the end
        assert bends[-1].bend_semitones == 0.0

    def test_melody_expression_processing(self):
        melody = [
            NoteEvent(pitch=72, start=0.0, duration=0.75, velocity=100),
            NoteEvent(pitch=75, start=1.0, duration=2.5, velocity=105),  # Sustained
            NoteEvent(pitch=70, start=4.0, duration=0.5, velocity=95),
        ]
        expr_notes, all_bends = MPEExpressionEngine.add_expression_to_melody(melody)
        assert len(expr_notes) == 3
        assert len(all_bends) > 0
        # Sustained note at index 1 should have rich vibrato points
        assert len(expr_notes[1].pitch_bend_points) > 5


class TestDrumGhostNoteInjector:
    """Tests for ghost snares and hi-hat velocity waves."""

    def test_ghost_notes_in_turnaround_bars(self):
        # 8-bar standard drum pattern with a snare on beat 2 and 4 (beats 1.0 and 3.0)
        notes = []
        for bar in range(8):
            notes.append(NoteEvent(pitch=38, start=float(bar * 4) + 1.0, duration=0.25, velocity=100))
            notes.append(NoteEvent(pitch=38, start=float(bar * 4) + 3.0, duration=0.25, velocity=100))

        augmented = DrumGhostNoteInjector.inject_ghost_notes(notes, total_bars=8)
        # Turnaround bars (bars 3 and 7 -> 4th and 8th bars) should have extra ghost notes
        assert len(augmented) > len(notes)
        ghost_notes = [n for n in augmented if n.velocity < 50]
        assert len(ghost_notes) > 0
        # All ghost notes must have lower velocity
        for g in ghost_notes:
            assert g.velocity <= 45

    def test_hihat_velocity_shaping(self):
        # 16 flat 16th-note hats
        hats = [
            NoteEvent(pitch=42, start=float(i) * 0.25, duration=0.15, velocity=100)
            for i in range(16)
        ]
        shaped = DrumGhostNoteInjector.shape_hihat_velocities(hats)
        assert len(shaped) == 16
        # Downbeat hats should be louder than pickup hats
        vel_0 = shaped[0].velocity  # Step 0 (downbeat)
        vel_3 = shaped[3].velocity  # Step 3 (pickup)
        assert vel_0 > vel_3

    def test_combined_drum_processing(self):
        notes = [
            NoteEvent(pitch=38, start=1.0, duration=0.25, velocity=100),
            NoteEvent(pitch=42, start=0.0, duration=0.15, velocity=100),
            NoteEvent(pitch=42, start=0.25, duration=0.15, velocity=100),
        ]
        processed = DrumGhostNoteInjector.process_drum_track_notes(notes, total_bars=4)
        assert len(processed) >= len(notes)


class TestCopilotPhase4Integration:
    """Tests for Copilot discovering and executing Phase 4 decisions."""

    def test_copilot_discovers_phase4_decisions(self):
        copilot = ExecutiveCopilotEngine()
        mock_tracks = [
            {"name": "Kick (808)", "track_index": 0},
            {"name": "Snare & Clap", "track_index": 1},
            {"name": "Hi-Hats", "track_index": 2},
            {"name": "Rhodes Piano", "track_index": 3},
            {"name": "Lead Synth", "track_index": 4},
        ]
        state = copilot.inspect_session(tracks=mock_tracks)
        pending_ids = [d.id for d in state.pending_decisions]

        # Verify Phase 4 decisions registered
        assert any(d.startswith("DEC-P4-01-MPC-GROOVE-POOL") for d in pending_ids)
        assert any(d.startswith("DEC-P4-02-CHORD-STRUMMING") for d in pending_ids)
        assert any(d.startswith("DEC-P4-03-LEAD-MPE-EXPRESSION") for d in pending_ids)
        assert any(d.startswith("DEC-P4-04-DRUM-GHOST-NOTES") for d in pending_ids)

        for d in state.pending_decisions:
            if d.id.startswith("DEC-P4-0"):
                assert d.phase == ProductionPhase.PHASE_4_HUMANIZATION_GROOVE

    def test_copilot_executes_phase4_decision_yes_and_no(self):
        copilot = ExecutiveCopilotEngine()
        mock_tracks = [
            {"name": "Snare & Clap", "track_index": 0},
            {"name": "Rhodes Piano", "track_index": 1},
        ]
        state = copilot.inspect_session(tracks=mock_tracks)

        # Execute chord strumming with YES
        dec_id = "DEC-P4-02-CHORD-STRUMMING-T1"
        res = copilot.execute_decision(dec_id, choice="YES")
        assert res["status"] == "success"
        assert res["action"] == "APPLIED"
        assert dec_id in copilot.resolved_decisions

        # Execute groove pool with NO (rejection)
        dec_id_no = "DEC-P4-01-MPC-GROOVE-POOL-T0"
        res_no = copilot.execute_decision(dec_id_no, choice="NO", justification="Producer requested straight robotic grid")
        assert res_no["status"] == "success"
        assert res_no["action"] == "REJECTED"
        assert res_no["justification"] == "Producer requested straight robotic grid"
        assert dec_id_no in copilot.resolved_decisions
