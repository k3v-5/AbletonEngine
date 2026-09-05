import pytest
from engine.music.harmony.full_song import FullSongHarmonyEngine
from engine.music.bass.intelligent_808 import Intelligent808BassEngine
from engine.music.melody.topline import TopLineMelodyEngine
from engine.music.melody.vocal_hook import VocalHookChopEngine
from engine.production.copilot.stepper import ExecutiveCopilotEngine
from engine.production.copilot.models import ProductionPhase


class TestFullSongHarmonyEngine:
    def test_full_song_progression_structure(self):
        chords = FullSongHarmonyEngine.generate_full_song_progression(key_root="F", scale="natural_minor")
        assert len(chords) > 0
        total_beats = sum(c.duration for c in chords)
        # 96 bars * 4 beats/bar = 384 beats
        assert total_beats == 384.0

    def test_drop2_voicing_generation(self):
        voicing = FullSongHarmonyEngine.build_drop2_voicing("F", "min9")
        assert len(voicing) == 4
        # Notes should be sorted ascending
        assert voicing == sorted(voicing)
        # Centroid should be around middle register (48 - 72)
        centroid = sum(voicing) / len(voicing)
        assert 50 <= centroid <= 70

    def test_voice_leading_optimization(self):
        v1 = [53, 60, 63, 68] # Fm
        v2 = [51, 58, 63, 67] # Ebm
        smooth = FullSongHarmonyEngine.optimize_voice_leading(v1, v2)
        assert len(smooth) == 4
        # Displacement cost should be compact
        cost = sum(abs(s - p) for s, p in zip(sorted(smooth), sorted(v1)))
        assert cost < 24 # Average movement < 6 semitones per voice

    def test_harmony_notes_generation(self):
        notes = FullSongHarmonyEngine.generate_harmony_notes(key_root="F", scale="natural_minor")
        assert len(notes) > 100
        # Check last note ends near beat 384
        max_end = max(n.start + n.duration for n in notes)
        assert max_end >= 380.0
        # Check velocities are humanized within musical bounds
        for n in notes:
            assert 40 <= n.velocity <= 120


class TestIntelligent808BassEngine:
    def test_808_bass_pitch_clamping(self):
        # Must be within sub-bass range MIDI 24 - 44 (C1 - Ab2)
        for root in ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]:
            pitch = Intelligent808BassEngine.get_bass_pitch_for_root(root)
            assert 24 <= pitch <= 44

    def test_808_bassline_section_dynamics(self):
        notes = Intelligent808BassEngine.generate_808_bassline(
            key_root="F",
            scale="natural_minor",
            enable_slides=True,
            enable_chromatic_approach=True
        )
        assert len(notes) > 0

        # Verify Intro (beats 0 - 32) has NO bass notes
        intro_notes = [n for n in notes if n.start < 32.0]
        assert len(intro_notes) == 0

        # Verify Verse 1 first half (beats 32 - 64) has NO bass notes
        v1_early = [n for n in notes if 32.0 <= n.start < 64.0]
        assert len(v1_early) == 0

        # Verify Bass enters at bar 16 (beat 64)
        v1_late = [n for n in notes if 64.0 <= n.start < 96.0]
        assert len(v1_late) > 0

        # Verify Chorus (beats 128 - 192) has active driving bass
        chorus_notes = [n for n in notes if 128.0 <= n.start < 192.0]
        assert len(chorus_notes) >= 20

        # Verify chromatic approach notes exist
        # Chromatic approach notes are placed at beat offset 7.5 within 8-beat cycles
        approach_notes = [n for n in notes if abs((n.start % 8.0) - 7.5) < 0.01]
        assert len(approach_notes) > 0


class TestTopLineMelodyEngine:
    def test_8bar_call_and_response_phrasing(self):
        notes = TopLineMelodyEngine.generate_8bar_phrase(
            start_beat=0.0,
            energy_level=0.85,
            phrase_seed=42
        )
        assert len(notes) >= 10
        # Call notes (beats 0 - 8)
        call_notes = [n for n in notes if n.start < 8.0]
        assert len(call_notes) >= 3

        # Response notes (beats 8 - 16)
        resp_notes = [n for n in notes if 8.0 <= n.start < 16.0]
        assert len(resp_notes) >= 3

        # Check vocal respiration: breath gap between call and response (beats 6.75 - 8.5)
        gap_notes = [n for n in notes if 7.0 <= n.start < 8.2]
        assert len(gap_notes) == 0 # Clean breath!

    def test_full_song_melody_structure(self):
        melody = TopLineMelodyEngine.generate_full_song_melody(key_root="F", scale="natural_minor")
        assert len(melody) > 40
        # Verify active in Chorus (beat 128) and Final Chorus (beat 288)
        ch_notes = [n for n in melody if 128.0 <= n.start < 192.0]
        final_notes = [n for n in melody if 288.0 <= n.start < 352.0]
        assert len(ch_notes) > 0
        assert len(final_notes) > 0


class TestVocalHookChopEngine:
    def test_2bar_hook_motif(self):
        motif = VocalHookChopEngine.generate_2bar_hook_motif(start_beat=0.0, energy_level=0.90)
        assert len(motif) == 6
        # All pitches in minor pentatonic pool
        for n in motif:
            assert n.pitch in VocalHookChopEngine.CHOP_PITCH_POOL

    def test_full_song_vocal_hook(self):
        hook_notes = VocalHookChopEngine.generate_full_song_vocal_hook(key_root="F", scale="natural_minor")
        assert len(hook_notes) >= 50
        # Verify presence in Intro, Chorus, Bridge, Final Chorus
        intro_chops = [n for n in hook_notes if n.start < 32.0]
        chorus_chops = [n for n in hook_notes if 128.0 <= n.start < 192.0]
        assert len(intro_chops) > 0
        assert len(chorus_chops) > 0


class TestCopilotPhase2Integration:
    def test_copilot_discovers_phase2_decisions(self):
        copilot = ExecutiveCopilotEngine()
        mock_tracks = [
            {"name": "Kick (808)", "track_index": 0},
            {"name": "808 Sub Bass", "track_index": 1},
            {"name": "Snare & Clap", "track_index": 2},
            {"name": "Rhodes Piano", "track_index": 3},
            {"name": "Lead Synth", "track_index": 4},
            {"name": "Vocal Chops", "track_index": 5},
        ]
        state = copilot.inspect_session(conn=None, tracks=mock_tracks)
        dec_ids = [d.id for d in state.pending_decisions]

        # Verify Phase 2 decisions discovered
        assert "DEC-P2-01-HARMONY-T3" in dec_ids
        assert "DEC-P2-02-BASS-808-T1" in dec_ids
        assert "DEC-P2-03-TOPLINE-T4" in dec_ids
        assert "DEC-P2-04-VOCAL-HOOK-T5" in dec_ids

        # Verify correct phase
        for d in state.pending_decisions:
            if d.id.startswith("DEC-P2"):
                assert d.phase == ProductionPhase.PHASE_2_COMPOSITION
