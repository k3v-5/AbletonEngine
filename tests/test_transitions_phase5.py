# tests/test_transitions_phase5.py
"""
Test Suite for Phase 5: Transitions, Risers, Impacts & Macro Narrative.
Validates:
1. SectionImpactEngine: 7-section impacts, sub-booms, crash downlifters.
2. TransitionRisersEngine: Exponential snare rolls, pitch bends, filter sweeps.
3. PreDropVacuumEngine & PreDropGenerator: Acoustic silence windows, volume mute envelopes, transition descriptors.
4. EarCandyTransitionEngine: Reverse vocal/cymbal swells, tape stops, reverb freeze wash.
5. ExecutiveCopilotEngine: Phase 5 transition decisions discovery and interactive execution.
"""

import pytest
from engine.music.models import NoteEvent
from engine.arrangement.transitions.impacts import SectionImpactEngine
from engine.arrangement.transitions.risers import TransitionRisersEngine, SweepFilterType
from engine.arrangement.transitions.pre_drop import PreDropVacuumEngine, PreDropGenerator
from engine.arrangement.fx.ear_candy_transitions import EarCandyTransitionEngine
from engine.production.copilot.stepper import ExecutiveCopilotEngine, ProductionPhase


class TestSectionImpactEngine:
    """Tests for section arrival impacts and downlifter triggers."""

    def test_section_impact_manifest_completeness(self):
        manifest = SectionImpactEngine.get_section_impact_manifest()
        assert manifest["status"] == "SUCCESS"
        assert manifest["total_impacts"] == 7
        sections = [e["section"] for e in manifest["events"]]
        assert "Intro" in sections
        assert "Chorus 1" in sections
        assert "Final Chorus" in sections
        assert "Outro" in sections

    def test_generate_impact_notes(self):
        notes = SectionImpactEngine.generate_impact_notes()
        assert len(notes) > 0
        pitches = {n.pitch for n in notes}
        assert 49 in pitches  # Crash
        assert 36 in pitches  # Sub-boom
        # Chorus 1 downbeat at bar 32 = beat 128.0
        chorus1_notes = [n for n in notes if abs(n.start - 128.0) < 0.1]
        assert len(chorus1_notes) == 2  # Both crash and sub-boom
        # Max velocity on Chorus 1
        assert any(n.velocity == 127 for n in chorus1_notes)


class TestTransitionRisersEngine:
    """Tests for procedural tension risers and snare rolls."""

    def test_procedural_snare_roll_acceleration(self):
        roll_notes = TransitionRisersEngine.generate_procedural_snare_roll(
            target_bar=33.0,
            duration_bars=1.0,
            snare_pitch=38,
            base_velocity=50,
            max_velocity=127
        )
        assert len(roll_notes) > 10
        # Velocities should strictly crescendo
        first_half = roll_notes[:len(roll_notes)//2]
        second_half = roll_notes[len(roll_notes)//2:]
        avg_vel1 = sum(n.velocity for n in first_half) / len(first_half)
        avg_vel2 = sum(n.velocity for n in second_half) / len(second_half)
        assert avg_vel2 > avg_vel1
        # Intervals between consecutive notes must shrink (accelerando)
        durations = [roll_notes[i+1].start - roll_notes[i].start for i in range(len(roll_notes)-2)]
        assert durations[0] > durations[-1]

    def test_noise_pitch_riser(self):
        riser = TransitionRisersEngine.generate_noise_pitch_riser(
            target_bar=33.0,
            duration_bars=2.0
        )
        assert "volume_envelope" in riser
        assert "pitch_bend_envelope" in riser
        vol = riser["volume_envelope"]
        pitch = riser["pitch_bend_envelope"]
        assert len(vol) >= 16
        assert len(pitch) >= 16
        # Pitch rises towards +8191
        max_pitch = max(p["value"] for p in pitch)
        assert max_pitch == 8191.0

    def test_filter_sweep(self):
        sweep = TransitionRisersEngine.generate_filter_sweep(
            target_bar=33.0,
            duration_bars=2.0,
            sweep_type=SweepFilterType.LOW_PASS_RISE,
            min_freq=250.0,
            max_freq=18000.0
        )
        assert len(sweep) >= 16
        assert sweep[0]["value"] == 250.0
        assert sweep[-1]["value"] == 18000.0

    def test_apply_transition_riser_dry(self):
        res = TransitionRisersEngine.apply_transition_riser(
            conn=None,
            track_index=13,
            target_bar=33.0,
            duration_bars=2.0
        )
        assert res["status"] == "SUCCESS"
        assert res["sweep_points_count"] > 0
        assert res["snare_notes_count"] > 0


class TestPreDropVacuumEngine:
    """Tests for pre-drop tension micro-silence gaps."""

    def test_vacuum_windows_detection(self):
        windows = PreDropVacuumEngine.get_vacuum_windows()
        assert len(windows) == 2
        drop1 = windows[0]
        assert drop1["drop_bar"] == 32
        assert drop1["drop_beat"] == 128.0
        assert drop1["vacuum_start_beat"] == 127.0
        assert drop1["vacuum_end_beat"] == 128.0
        assert "kick" in drop1["mute_tracks"]
        assert "bass" in drop1["mute_tracks"]

    def test_vacuum_mute_envelope(self):
        env = PreDropVacuumEngine.generate_vacuum_mute_envelope(
            drop_beat=128.0,
            duration_beats=1.0
        )
        assert len(env) == 4
        # Volume drops to 0.0 inside vacuum
        assert env[1][1] == 0.0
        assert env[2][1] == 0.0
        # Recovers to 1.0 at drop beat 128.0
        assert env[3][1] == 1.0
        assert env[3][0] == 128.0

    def test_pre_drop_descriptor(self):
        desc = PreDropGenerator.create_pre_drop(
            from_section_idx=2,
            to_section_idx=3,
            transition_bar=32,
            silence_duration_beats=2.0
        )
        assert desc.start_bar == 32
        assert desc.pre_drop_silence_beats == 2.0
        assert "kick" in desc.affected_roles


class TestEarCandyTransitionEngine:
    """Tests for organic ear candy transition sweeps and tape stops."""

    def test_full_ear_candy_manifest(self):
        manifest = EarCandyTransitionEngine.get_full_ear_candy_manifest()
        assert manifest["status"] == "SUCCESS"
        assert manifest["total_micro_fx"] == 5
        names = [item["name"] for item in manifest["items"]]
        assert any("Tape Stop" in n for n in names)
        assert any("Reverse Vocal Swell" in n for n in names)
        assert any("Reverb Freeze Wash" in n for n in names)

    def test_tape_stop_transition(self):
        stop = EarCandyTransitionEngine.generate_tape_stop_transition(
            target_bar=33,
            duration_beats=1.0
        )
        assert stop["status"] == "SUCCESS"
        assert len(stop["pitch_bend_points"]) > 0
        assert len(stop["volume_points"]) > 0
        # Lowest pitch bend reaches plunge level
        min_pitch = min(p["value"] for p in stop["pitch_bend_points"])
        assert min_pitch <= -4000.0

    def test_reverse_vocal_swell(self):
        swell = EarCandyTransitionEngine.generate_reverse_vocal_swell(
            drop_bar=33,
            duration_beats=2.0
        )
        assert swell["status"] == "SUCCESS"
        assert swell["start_beat"] == 126.0
        assert swell["end_beat"] == 128.0
        # Volume ramp ends at 1.0
        assert swell["volume_ramp"][-1][1] == 1.0

    def test_reverb_freeze_wash(self):
        wash = EarCandyTransitionEngine.generate_reverb_freeze_wash(
            bar=24,
            duration_beats=4.0
        )
        assert wash["status"] == "SUCCESS"
        assert wash["reverb_decay_time_sec"] == 12.0
        assert wash["dry_wet"][-1][1] == 1.0


class TestExecutiveCopilotPhase5:
    """Tests Phase 5 interactive copilot decision stepping."""

    def test_copilot_discovers_phase5_decisions(self):
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

        # Verify Phase 5 decisions registered
        assert "DEC-P5-TRANSITION-RISERS" in pending_ids
        assert "DEC-P5-IMPACTS-DOWNLIFTERS" in pending_ids
        assert "DEC-P5-PHYSICAL-ARRANGEMENT-AUTOMATIONS" in pending_ids

        for d in state.pending_decisions:
            if d.id.startswith("DEC-P5-"):
                assert d.phase == ProductionPhase.PHASE_5_ARRANGEMENT_TRANSITIONS

    def test_copilot_executes_phase5_decisions(self):
        copilot = ExecutiveCopilotEngine()
        mock_tracks = [
            {"name": "Kick (808)", "track_index": 0},
            {"name": "Snare & Clap", "track_index": 1},
            {"name": "Rhodes Piano", "track_index": 2},
        ]
        copilot.inspect_session(tracks=mock_tracks)

        # Execute Risers with YES
        dec_risers = "DEC-P5-TRANSITION-RISERS"
        res1 = copilot.execute_decision(dec_risers, choice="YES")
        assert res1["status"] == "success"
        assert res1["action"] == "APPLIED"
        assert dec_risers in copilot.resolved_decisions

        # Execute Impacts with NO (conscious producer opt-out)
        dec_impacts = "DEC-P5-IMPACTS-DOWNLIFTERS"
        res2 = copilot.execute_decision(dec_impacts, choice="NO", justification="Producer requested dry transition")
        assert res2["status"] == "success"
        assert res2["action"] == "REJECTED"
        assert res2["justification"] == "Producer requested dry transition"
        assert dec_impacts in copilot.resolved_decisions
