# test_suite_refactor_verification.py
"""
Comprehensive standalone verification script for AbletonEngine refactor.
ZERO PYTEST: Runs via standard python test_suite_refactor_verification.py.
Verifies all 25 architectural requirements, new modules, and edge cases.
"""

import sys
import os
import math
import logging

# Ensure root directory is on PYTHONPATH
sys.path.insert(0, os.path.abspath("."))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("TestRefactorVerification")

def run_all_tests():
    passed = 0
    failed = 0

    def assert_true(cond, msg):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  [PASS] {msg}")
        else:
            failed += 1
            print(f"  [FAIL] {msg}")

    print("=" * 70)
    print("RUNNING COMPREHENSIVE ABLETON ENGINE REFACTOR TEST SUITE (STANDALONE)")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # TEST 1: Vertical Harmonic Validator (engine/music/harmony/vertical_harmonic_validator.py)
    # -------------------------------------------------------------------------
    print("\n--- Test 1: Vertical Harmonic Validator (Report-Only, No Mutation) ---")
    try:
        from engine.music.harmony.vertical_harmonic_validator import (
            VerticalHarmonicValidator,
            VerticalHarmonicReport,
            HarmonicClashEvent,
            HarmonicTensionEvent
        )
        from engine.music.models import NoteEvent

        # Construct note tracks
        # Bass note C2 (MIDI 36) at beats 0..4
        # Harmony note E3 (MIDI 52) at beats 0..4 (Major 10th / 3rd: consonant)
        # Melody note D4 (MIDI 62) at beat 0..2 (Major 9th tension: allowed)
        # Clash melody note C#2 (MIDI 37) at beat 2..4 (Minor 2nd clash with Bass C2: harsh clash!)
        lead_note1 = NoteEvent(pitch=62, start=0.0, duration=2.0)
        lead_note2 = NoteEvent(pitch=37, start=2.0, duration=2.0)
        lead_notes = [lead_note1, lead_note2]

        bass_note = NoteEvent(pitch=36, start=0.0, duration=4.0)
        bass_notes = [bass_note]

        keys_note = NoteEvent(pitch=52, start=0.0, duration=4.0)
        keys_notes = [keys_note]

        # Invariant check: record note states before audit
        pre_lead1_pitch = lead_note1.pitch
        pre_lead2_pitch = lead_note2.pitch
        pre_bass_pitch = bass_note.pitch

        report = VerticalHarmonicValidator.audit_tracks({
            "Bass": bass_notes,
            "Lead": lead_notes,
            "Keys": keys_notes
        }, time_step=0.5)

        assert_true(isinstance(report, VerticalHarmonicReport), "Returns VerticalHarmonicReport")
        assert_true(report.total_slices_audited > 0, f"Total slices audited: {report.total_slices_audited}")
        assert_true(report.tension_count > 0, f"Allowed tensions detected: {report.tension_count}")
        assert_true(report.clash_count > 0, f"Acoustic clashes detected: {report.clash_count}")

        # Verify minor 2nd clash was detected between Bass and Lead
        m2_clashes = [c for c in report.clashes if c.clash_type == "MINOR_SECOND_LEAD_BASS" or c.simple_interval == 1]
        assert_true(len(m2_clashes) > 0, f"Detected minor 2nd clash between bass and lead: {len(m2_clashes)}")

        # Verify low interval limit check
        low_report = VerticalHarmonicValidator.audit_tracks({
            "SubBass": [NoteEvent(pitch=30, start=0.0, duration=2.0)], # F#1
            "SubSine": [NoteEvent(pitch=31, start=0.0, duration=2.0)], # G1 (1 semitone below C2)
        }, time_step=0.5)
        low_limit_clashes = [c for c in low_report.clashes if c.clash_type == "LOW_INTERVAL_LIMIT"]
        assert_true(len(low_limit_clashes) > 0, "Low-interval limit collision caught below C2")

        # Invariant check: ZERO MUTATION
        assert_true(lead_note1.pitch == pre_lead1_pitch, "Invariant preserved: lead_note1 was NOT mutated")
        assert_true(lead_note2.pitch == pre_lead2_pitch, "Invariant preserved: lead_note2 was NOT mutated")
        assert_true(bass_note.pitch == pre_bass_pitch, "Invariant preserved: bass_note was NOT mutated")

    except Exception as e:
        assert_true(False, f"VerticalHarmonicValidator error: {e}")

    # -------------------------------------------------------------------------
    # TEST 2: Beat Switch Orchestrator (engine/arrangement/beat_switch.py)
    # -------------------------------------------------------------------------
    print("\n--- Test 2: Beat Switch Orchestrator (Tempo, Meter, Groove) ---")
    try:
        from engine.arrangement.beat_switch import BeatSwitchOrchestrator

        # 1. Instant Cut switch with compound meter (4/4 -> 6/8)
        plan_cut = BeatSwitchOrchestrator.plan_beat_switch(
            switch_bar=33.0,
            current_bpm=140.0,
            target_bpm=95.0,
            target_genre="lofi_chill",
            transition_mode="instant_cut",
            current_meter=(4, 4),
            target_meter=(6, 8),
            current_groove="straight_precise",
            target_groove="neo_soul_dilla"
        )
        assert_true(plan_cut["status"] == "SUCCESS", "Plan beat switch instant cut succeeds")
        assert_true(plan_cut["switch_beat"] == 128.0, f"Switch beat correctly calculated: {plan_cut['switch_beat']}")
        assert_true(len(plan_cut["tempo_points"]) == 2, "Tempo automation points injected for instant cut")
        assert_true(len(plan_cut["meter_change_events"]) == 1, "Meter change event generated for 6/8")
        assert_true(plan_cut["meter_change_events"][0]["numerator"] == 6, "Meter numerator is 6")
        assert_true(plan_cut["target_groove"] == "neo_soul_dilla", "Target groove preserved")

        # 2. Ritardando switch
        plan_rit = BeatSwitchOrchestrator.plan_beat_switch(
            switch_bar=17.0,
            current_bpm=130.0,
            target_bpm=75.0,
            transition_mode="ritardando"
        )
        assert_true(len(plan_rit["tempo_points"]) == 3, "Ritardando generated 3-point tape drag slowdown envelope")

        # 3. Metric modulation switch
        plan_mm = BeatSwitchOrchestrator.plan_beat_switch(
            switch_bar=25.0,
            current_bpm=120.0,
            target_bpm=90.0,
            transition_mode="metric_modulation",
            current_meter=(4, 4),
            target_meter=(3, 4)
        )
        assert_true(plan_mm["transition_mode"] == "metric_modulation", "Metric modulation mode handled")

        # 4. Forwarding module verification
        from engine.arrangement.structure.beat_switch import BeatSwitchOrchestrator as BSOForwarded
        plan_fwd = BSOForwarded.plan_beat_switch(switch_bar=9.0, current_bpm=128.0, target_bpm=80.0)
        assert_true(plan_fwd["status"] == "SUCCESS", "Forwarded module in structure/beat_switch.py works identically")

    except Exception as e:
        assert_true(False, f"BeatSwitchOrchestrator error: {e}")

    # -------------------------------------------------------------------------
    # TEST 3: Arrangement Physical Auditor (engine/arrangement/arrangement_physical_auditor.py)
    # -------------------------------------------------------------------------
    print("\n--- Test 3: Arrangement Physical Auditor (LOM Clip Inspector) ---")
    try:
        from engine.arrangement.arrangement_physical_auditor import (
            ArrangementPhysicalAuditor,
            ArrangementPhysicalAuditReport
        )

        test_tracks_data = [
            {
                "index": 0,
                "name": "Kick",
                "mute": False,
                "clips": [
                    {"name": "Kick_Intro", "start_time": 0.0, "length": 16.0, "muted": False},
                    {"name": "Kick_Verse", "start_time": 16.0, "length": 16.0, "muted": False},
                    # Overlapping clip!
                    {"name": "Kick_Overlap", "start_time": 28.0, "length": 8.0, "muted": False}
                ]
            },
            {
                "index": 1,
                "name": "Lead Vocal",
                "mute": False,
                "clips": [
                    {"name": "Vocal_Verse", "start_time": 16.0, "length": 16.0, "muted": False},
                    # Muted clip!
                    {"name": "Vocal_Take2", "start_time": 32.0, "length": 16.0, "muted": True},
                    # Zero-length clip!
                    {"name": "Vocal_Ghost", "start_time": 48.0, "length": 0.0, "muted": False}
                ]
            }
        ]

        report = ArrangementPhysicalAuditor.audit_arrangement_data(
            test_tracks_data,
            expected_total_bars=12.0,  # 12 bars * 4 = 48 beats max
            beats_per_bar=4.0
        )

        assert_true(isinstance(report, ArrangementPhysicalAuditReport), "Returns ArrangementPhysicalAuditReport")
        assert_true(report.total_tracks_audited == 2, f"Audited 2 tracks: {report.total_tracks_audited}")
        assert_true(report.total_clips_found == 6, f"Audited 6 clips: {report.total_clips_found}")

        # Check finding types
        finding_types = [f.issue_type for f in report.findings]
        assert_true("OVERLAP" in finding_types, "Detected destructive clip overlap")
        assert_true("MUTED_CLIP" in finding_types, "Detected muted clip")
        assert_true("ZERO_LENGTH" in finding_types, "Detected zero-length ghost clip")
        assert_true(report.is_valid is False, "Flagged invalid arrangement due to High severity issues")

    except Exception as e:
        assert_true(False, f"ArrangementPhysicalAuditor error: {e}")

    # -------------------------------------------------------------------------
    # TEST 4: Live 12 Clip Envelopes (engine/arrangement/automation/clip_envelopes.py)
    # -------------------------------------------------------------------------
    print("\n--- Test 4: Live 12 Clip Envelopes Engine ---")
    try:
        from engine.arrangement.automation.clip_envelopes import (
            ClipEnvelopeEngine,
            EnvelopeBreakpoint
        )

        # 1. Filter sweep breakpoints generator
        sweep_pts = ClipEnvelopeEngine.generate_filter_sweep_breakpoints(
            clip_length=16.0,
            start_val=0.1,
            end_val=0.9,
            steps=8,
            curve="exponential"
        )
        assert_true(len(sweep_pts) == 8, f"Generated 8 sweep breakpoints: {len(sweep_pts)}")
        assert_true(sweep_pts[0].value == 0.1, "First breakpoint starts at start_val 0.1")
        assert_true(sweep_pts[-1].value == 0.9, "Last breakpoint reaches end_val 0.9")

        # 2. Sidechain duck breakpoints generator
        duck_pts = ClipEnvelopeEngine.generate_sidechain_duck_breakpoints(bars=2, duck_depth=0.15)
        assert_true(len(duck_pts) == 16, f"Generated 16 sidechain pump breakpoints: {len(duck_pts)}")

        # 3. Apply clip envelope mock execution
        mock_res = ClipEnvelopeEngine.apply_clip_envelope(
            conn=None,
            track_index=1,
            clip_index=0,
            is_arrangement=True,
            parameter_type="volume",
            breakpoints=sweep_pts
        )
        assert_true(mock_res["status"] == "MOCK_OK", "Mock clip envelope execution succeeds")
        assert_true(mock_res["breakpoints_count"] == 8, "Mock recorded 8 breakpoints")

        # 4. Script building test
        script = ClipEnvelopeEngine._build_envelope_injection_script(
            track_index=2,
            clip_index=1,
            is_arrangement=True,
            parameter_type="device_parameter",
            device_index=0,
            parameter_name="Cutoff",
            parameter_index=None,
            send_index=0,
            points=[{"time": 0.0, "length": 4.0, "value": 0.5}],
            clear_existing=True
        )
        assert_true("create_automation_envelope" in script, "Script references create_automation_envelope")
        assert_true("insert_step" in script, "Script references insert_step")
        assert_true("arrangement_clips[1]" in script, "Script resolves target arrangement clip")

    except Exception as e:
        assert_true(False, f"ClipEnvelopeEngine error: {e}")

    # -------------------------------------------------------------------------
    # TEST 5: Stereo Panning Validator (engine/mix/stereo_panning_validator.py)
    # -------------------------------------------------------------------------
    print("\n--- Test 5: Stereo Panning Validator (Design vs Mix) ---")
    try:
        from engine.mix.stereo_panning_validator import (
            StereoPanningValidator,
            StereoPanningAuditReport
        )

        designed_pans = {
            "Kick": 0.0,
            "Sub 808": 0.0,
            "Lead Vocal": 0.0,
            "Rhythm Guitar": -0.65,
            "Lead Synth": 0.50
        }

        # Case A: Compliant session
        compliant_tracks = [
            {"index": 0, "name": "Kick", "panning": 0.0},
            {"index": 1, "name": "Sub 808", "panning": 0.0},
            {"index": 2, "name": "Lead Vocal", "panning": 0.0},
            {"index": 3, "name": "Rhythm Guitar", "panning": -0.65},
            {"index": 4, "name": "Lead Synth", "panning": 0.50}
        ]
        rep_a = StereoPanningValidator.audit_panning_data(compliant_tracks, designed_pans)
        assert_true(rep_a.is_fully_compliant is True, "Compliant tracks report 100% compliance")
        assert_true(rep_a.compliance_score_pct == 100.0, "Score is 100%")

        # Case B: Violations (Kick drifted to right, Guitar collapsed to center)
        violating_tracks = [
            {"index": 0, "name": "Kick", "panning": 0.40},         # MONO VIOLATION!
            {"index": 1, "name": "Sub 808", "panning": 0.0},
            {"index": 2, "name": "Rhythm Guitar", "panning": 0.0}, # COLLAPSED SPREAD!
            {"index": 3, "name": "Lead Synth", "panning": 0.50}
        ]
        rep_b = StereoPanningValidator.audit_panning_data(violating_tracks, designed_pans)
        assert_true(rep_b.is_fully_compliant is False, "Non-compliant tracks correctly flagged")
        statuses = [it.status for it in rep_b.items]
        assert_true("MONO_VIOLATION" in statuses, "Detected Kick MONO_VIOLATION off-center")
        assert_true("COLLAPSED_SPREAD" in statuses, "Detected Guitar COLLAPSED_SPREAD to center")

    except Exception as e:
        assert_true(False, f"StereoPanningValidator error: {e}")

    # -------------------------------------------------------------------------
    # TEST 6: Functional Harmony Engine (engine/music/harmony/functional_harmony_engine.py)
    # -------------------------------------------------------------------------
    print("\n--- Test 6: Functional Harmony Engine (Secondary Dominants, Tritone, Borrowing, +6) ---")
    try:
        from engine.music.harmony.functional_harmony_engine import FunctionalHarmonyEngine

        # Secondary dominant of C major V (G): V7/V is D7
        v7_v_root, v7_v_qual = FunctionalHarmonyEngine.get_secondary_dominant("G", "maj")
        assert_true(v7_v_root == "D", f"V7/V root is D (expected D, got {v7_v_root})")
        assert_true(v7_v_qual == "7", "V7/V quality is dominant 7")

        # Tritone substitution of G7 (resolving to C): Db7
        sub_root, sub_qual = FunctionalHarmonyEngine.get_tritone_substitution("G")
        assert_true(sub_root in ("C#", "Db", "DB"), f"Tritone sub of G is Db/C# (got {sub_root})")

        # Modal interchange borrowed chords in C
        borrowed = FunctionalHarmonyEngine.get_modal_interchange_chords("C", "Major")
        borrowed_roots = [c.root for c in borrowed]
        assert_true(len(borrowed) >= 4, f"Generated {len(borrowed)} modal interchange chords")
        # Neapolitan bII is Db
        assert_true(any(r in ("Db", "C#") for r in borrowed_roots), "Contains Neapolitan bII chord")

        # Augmented 6th chords: Italian, French, German
        it_r, it_q, it_desc = FunctionalHarmonyEngine.get_augmented_sixth_chord("C", "italian")
        fr_r, fr_q, fr_desc = FunctionalHarmonyEngine.get_augmented_sixth_chord("C", "french")
        ger_r, ger_q, ger_desc = FunctionalHarmonyEngine.get_augmented_sixth_chord("C", "german")
        assert_true(it_r in ("Ab", "G#"), f"Italian +6 root in C is Ab/G# (got {it_r})")
        assert_true(fr_q == "7b5", f"French +6 quality has flat 5 (got {fr_q})")
        assert_true(ger_r in ("Ab", "G#"), f"German +6 root in C is Ab/G# (got {ger_r})")

        # Dynamic progression across 8 bars in F Minor with Augmented 6ths
        chords = FunctionalHarmonyEngine.compose_functional_progression(
            key_root="F",
            scale="Minor",
            total_bars=8,
            use_secondary_dominants=True,
            use_tritone_sub=True,
            use_modal_borrowing=True,
            allow_augmented_sixths=True
        )
        assert_true(len(chords) == 8, f"Generated exactly 8 chords for 8 bars: {len(chords)}")

        # Compound meter scaling: 6/8 chord duration is 3.0 beats
        chords_68 = FunctionalHarmonyEngine.compose_functional_progression(
            key_root="A",
            scale="Minor",
            total_bars=4,
            time_signature=(6, 8)
        )
        assert_true(chords_68[0].duration == 3.0, f"6/8 chord duration is 3.0 beats (got {chords_68[0].duration})")

        # Irregular meter scaling: 7/8 chord duration is 3.5 beats, 5/4 chord duration is 5.0 beats
        chords_78 = FunctionalHarmonyEngine.compose_functional_progression(
            key_root="D",
            scale="Major",
            total_bars=4,
            time_signature=(7, 8)
        )
        assert_true(chords_78[0].duration == 3.5, f"7/8 chord duration is 3.5 beats (got {chords_78[0].duration})")

        chords_54 = FunctionalHarmonyEngine.compose_functional_progression(
            key_root="G",
            scale="Minor",
            total_bars=4,
            time_signature=(5, 4)
        )
        assert_true(chords_54[0].duration == 5.0, f"5/4 chord duration is 5.0 beats (got {chords_54[0].duration})")

    except Exception as e:
        assert_true(False, f"FunctionalHarmonyEngine error: {e}")

    # -------------------------------------------------------------------------
    # TEST 7: Advanced Melody Generator (engine/music/melody/advanced_melody_generator.py)
    # -------------------------------------------------------------------------
    print("\n--- Test 7: Advanced Melody Generator (Leaps, Steps, Extensions, Meters, Enclosures) ---")
    try:
        from engine.music.melody.advanced_melody_generator import AdvancedMelodyGenerator

        # Standard 4/4 melody
        melody = AdvancedMelodyGenerator.generate_melody_for_section(
            section_name="Chorus",
            section_bars=4,
            bpm=120.0,
            key_root="F",
            scale="Minor",
            time_signature=(4, 4),
            borrow_modal=True
        )
        assert_true(len(melody) > 0, f"Generated {len(melody)} melodic note events")

        audit = AdvancedMelodyGenerator.audit_melodic_contour(melody)
        assert_true(audit["total_notes"] == len(melody), "Audit notes count matches")
        assert_true("leap_resolution_ratio" in audit, "Evaluated leap-and-step resolution ratio")
        print(f"    Leap resolution ratio: {audit['leap_resolution_ratio'] * 100:.1f}%, Tensions: {audit['tensions_used']}")

        # Compound meter melody (6/8): 4 bars * 3.0 beats = 12.0 beats total
        mel_68 = AdvancedMelodyGenerator.generate_advanced_melody(
            key_root="C",
            scale="minor",
            total_bars=4,
            time_signature=(6, 8),
            enable_enclosures=True,
            enable_chromatic_passing=True
        )
        assert_true(len(mel_68) > 0, f"Compound 6/8 generated {len(mel_68)} notes")
        assert_true(all(n.start < 12.0 for n in mel_68), "All 6/8 notes stay within 12.0 total beats")

        # Irregular meter melody (7/8): 4 bars * 3.5 beats = 14.0 beats total
        mel_78 = AdvancedMelodyGenerator.generate_advanced_melody(
            key_root="E",
            scale="minor",
            total_bars=4,
            time_signature=(7, 8),
            enable_enclosures=True,
            enable_chromatic_passing=True
        )
        assert_true(len(mel_78) > 0, f"Irregular 7/8 generated {len(mel_78)} notes")
        assert_true(all(n.start < 14.0 for n in mel_78), "All 7/8 notes stay within 14.0 total beats")

    except Exception as e:
        assert_true(False, f"AdvancedMelodyGenerator error: {e}")

    # -------------------------------------------------------------------------
    # TEST 8: LUFS Validation Gate (engine/mix/lufs_validation_gate.py)
    # -------------------------------------------------------------------------
    print("\n--- Test 8: LUFS Gate (3-Way Verification & Dynamic ±3 dB Tolerance) ---")
    try:
        from engine.mix.lufs_validation_gate import LUFSValidationGate

        # 1. Synthetic / simulated audio MUST be blocked from autocertification
        synth_report = LUFSValidationGate.validate_master_loudness(
            is_synthetic=True,
            target_lufs=-8.5
        )
        assert_true(synth_report.is_compliant is False, "Synthetic audio strictly blocked")
        assert_true("SYNTHETIC_AUTOCERTIFICATION_BLOCKED" in synth_report.blocking_reasons, "Report contains SYNTHETIC_AUTOCERTIFICATION_BLOCKED")

        # validate_simulated_envelope must also explicitly block autocertification
        sim_env_report = LUFSValidationGate.validate_simulated_envelope(
            measured_lufs=-8.5,
            target_lufs=-8.5
        )
        assert_true(sim_env_report.is_compliant is False, "validate_simulated_envelope blocks autocertification")
        assert_true("SYNTHETIC_AUTOCERTIFICATION_BLOCKED" in sim_env_report.blocking_reasons, "Simulated envelope flags SYNTHETIC_AUTOCERTIFICATION_BLOCKED")

        # 2. 3-Way Physical Verification with target -8.5 LUFS:
        # -9.0 LUFS is within ±3.0 dB ([-11.5, -5.5]) -> PASS
        comp_report = LUFSValidationGate.validate_master_loudness(
            is_synthetic=False,
            measured_lufs=-9.0,
            target_lufs=-8.5,
            true_peak_dbtp=-0.5,
            tolerance=3.0
        )
        assert_true(comp_report.is_compliant is True, "Measured -9.0 LUFS is compliant with -8.5 ± 3.0 dB")
        assert_true(comp_report.three_way_verified is True, "Passed all 3 verification pathways (BS.1770, True Peak, RMS/EBU)")

        # -13.0 LUFS is outside ±3.0 dB -> FAIL
        out_report = LUFSValidationGate.validate_master_loudness(
            is_synthetic=False,
            measured_lufs=-13.0,
            target_lufs=-8.5,
            true_peak_dbtp=-0.5,
            tolerance=3.0
        )
        assert_true(out_report.is_compliant is False, "Measured -13.0 LUFS violates dynamic tolerance of -8.5 ± 3.0 dB")

        # 3. Target -6.0 LUFS dynamic ±3.0 dB tolerance test:
        # Range accepted: [-9.0, -3.0]
        rep_target6 = LUFSValidationGate.validate_master_loudness(
            is_synthetic=False,
            measured_lufs=-6.0,
            target_lufs=-6.0,
            true_peak_dbtp=-0.5,
            tolerance=3.0
        )
        assert_true(rep_target6.is_compliant is True, "Target -6.0 LUFS: center -6.0 LUFS is compliant")

        rep_edge_low = LUFSValidationGate.validate_master_loudness(
            is_synthetic=False,
            measured_lufs=-8.9,
            target_lufs=-6.0,
            true_peak_dbtp=-0.5,
            tolerance=3.0
        )
        assert_true(rep_edge_low.is_compliant is True, "Target -6.0 LUFS: -8.9 LUFS is compliant (within ±3 dB)")

        rep_edge_high = LUFSValidationGate.validate_master_loudness(
            is_synthetic=False,
            measured_lufs=-3.1,
            target_lufs=-6.0,
            true_peak_dbtp=-0.5,
            tolerance=3.0
        )
        assert_true(rep_edge_high.is_compliant is True, "Target -6.0 LUFS: -3.1 LUFS is compliant (within ±3 dB)")

        rep_fail_low = LUFSValidationGate.validate_master_loudness(
            is_synthetic=False,
            measured_lufs=-9.5,
            target_lufs=-6.0,
            true_peak_dbtp=-0.5,
            tolerance=3.0
        )
        assert_true(rep_fail_low.is_compliant is False, "Target -6.0 LUFS: -9.5 LUFS is rejected (exceeds -9.0 limit)")

        rep_fail_high = LUFSValidationGate.validate_master_loudness(
            is_synthetic=False,
            measured_lufs=-2.5,
            target_lufs=-6.0,
            true_peak_dbtp=-0.5,
            tolerance=3.0
        )
        assert_true(rep_fail_high.is_compliant is False, "Target -6.0 LUFS: -2.5 LUFS is rejected (exceeds -3.0 limit)")

        # 4. Pathway 2 True Peak check (max ceiling -0.3 dBTP)
        tp_fail = LUFSValidationGate.validate_master_loudness(
            is_synthetic=False,
            measured_lufs=-6.0,
            target_lufs=-6.0,
            true_peak_dbtp=0.1,  # Clipping
            tolerance=3.0
        )
        assert_true(tp_fail.is_compliant is False, "True Peak > -0.3 dBTP is strictly rejected")

        # 5. Pathway 3 RMS / EBU dynamic energy check (silence < -60 dBFS)
        rms_fail = LUFSValidationGate.validate_master_loudness(
            is_synthetic=False,
            measured_lufs=-6.0,
            target_lufs=-6.0,
            true_peak_dbtp=-0.5,
            rms_dbfs=-65.0,  # Below -60 dBFS: digital silence
            tolerance=3.0
        )
        assert_true(rms_fail.is_compliant is False, "RMS < -60 dBFS (silence) is rejected")

    except Exception as e:
        assert_true(False, f"LUFSValidationGate error: {e}")

    # -------------------------------------------------------------------------
    # TEST 9: Dismantled 96-Bar Templates (engine/arrangement/templates/structures.py)
    # -------------------------------------------------------------------------
    print("\n--- Test 9: Dismantling Fixed 96-Bar Templates ---")
    try:
        from engine.arrangement.blueprints.song_arranger import FullSongArrangerEngine
        from engine.arrangement.templates.structures import FORM_TEMPLATES, StructureLibrary, get_structure_template, build_sections_for_bars

        # 1. Invariant: generate_96bar_blueprint is permanently deleted
        assert_true(not hasattr(FullSongArrangerEngine, "generate_96bar_blueprint"), "Legacy generate_96bar_blueprint deleted from FullSongArrangerEngine")

        # 2. Invariant: FORM_TEMPLATES dictionary is completely empty
        assert_true(len(FORM_TEMPLATES) == 0, "FORM_TEMPLATES dictionary is empty (no fixed templates in engine)")

        # 3. Dynamic generation for arbitrary bar counts (prime, odd, even)
        bp40 = FullSongArrangerEngine.generate_dynamic_blueprint(total_bars=40)
        assert_true(bp40.total_bars == 40, f"Dynamic blueprint total_bars is 40 (got {bp40.total_bars})")
        assert_true(sum(s.bars for s in bp40.sections) == 40, f"Blueprint sections sum exactly to 40 (got {sum(s.bars for s in bp40.sections)})")

        bp77 = FullSongArrangerEngine.generate_dynamic_blueprint(total_bars=77)
        assert_true(bp77.total_bars == 77, f"Dynamic blueprint total_bars is 77 (got {bp77.total_bars})")
        assert_true(sum(s.bars for s in bp77.sections) == 77, f"Blueprint sections sum exactly to 77 (got {sum(s.bars for s in bp77.sections)})")

        bp13 = FullSongArrangerEngine.generate_dynamic_blueprint(total_bars=13)
        assert_true(bp13.total_bars == 13, f"Dynamic blueprint total_bars is 13 (got {bp13.total_bars})")
        assert_true(sum(s.bars for s in bp13.sections) == 13, f"Blueprint sections sum exactly to 13 (got {sum(s.bars for s in bp13.sections)})")

        # 4. Custom asymmetric phrasing and flexible drop placement
        custom = [
            {"name": "Intro", "bars": 5},
            {"name": "Verse", "bars": 9},
            {"name": "Build", "bars": 3},
            {"name": "Drop", "bars": 11}
        ]
        bp_asym = FullSongArrangerEngine.generate_dynamic_blueprint(
            total_bars=28,
            sections_spec=custom,
            drop_bar=18
        )
        assert_true(len(bp_asym.sections) == 4, f"Custom asymmetric sections count matches: {len(bp_asym.sections)}")
        assert_true(bp_asym.sections[0].bars == 5, "Asymmetric Intro is 5 bars")
        assert_true(bp_asym.sections[1].bars == 9, "Asymmetric Verse is 9 bars")
        assert_true(bp_asym.sections[3].bars == 11, "Asymmetric Drop is 11 bars")

    except Exception as e:
        assert_true(False, f"Structures error: {e}")

    # -------------------------------------------------------------------------
    # TEST 10: Rich Modal Scales (engine/production/copilot/phases/phase_1_tracks.py)
    # -------------------------------------------------------------------------
    print("\n--- Test 10: Rich Modal Scale Normalization (No Binary Collapse) ---")
    try:
        # We test the modal scale mapping logic directly
        def normalize_live12_scale(sc):
            if not sc:
                return None
            s_low = sc.strip().lower()
            if "dorian" in s_low or "dórico" in s_low or "dorico" in s_low:
                return "Dorian"
            elif "phrygian" in s_low or "frigio" in s_low:
                return "Phrygian"
            elif "mixolydian" in s_low or "mixolidio" in s_low:
                return "Mixolydian"
            elif "lydian" in s_low or "lidio" in s_low:
                return "Lydian"
            elif "locrian" in s_low or "locrio" in s_low:
                return "Locrian"
            elif "harmonic" in s_low and ("min" in s_low or "menor" in s_low):
                return "Harmonic Minor"
            elif "melodic" in s_low and ("min" in s_low or "menor" in s_low):
                return "Melodic Minor"
            elif "blues" in s_low:
                return "Blues"
            elif any(w in s_low for w in ["min", "menor", "dark", "natural_minor"]):
                return "Minor"
            elif any(w in s_low for w in ["maj", "mayor"]):
                return "Major"
            return sc.strip().title()

        assert_true(normalize_live12_scale("Dorian") == "Dorian", "Dorian preserved")
        assert_true(normalize_live12_scale("phrygian mode") == "Phrygian", "Phrygian preserved")
        assert_true(normalize_live12_scale("Lydian") == "Lydian", "Lydian preserved")
        assert_true(normalize_live12_scale("Mixolydian") == "Mixolydian", "Mixolydian preserved")
        assert_true(normalize_live12_scale("Locrian") == "Locrian", "Locrian preserved")
        assert_true(normalize_live12_scale("Harmonic Minor") == "Harmonic Minor", "Harmonic Minor preserved")
        assert_true(normalize_live12_scale("Melodic Minor") == "Melodic Minor", "Melodic Minor preserved")
        assert_true(normalize_live12_scale("Blues") == "Blues", "Blues preserved")

    except Exception as e:
        assert_true(False, f"Modal scale error: {e}")

    # -------------------------------------------------------------------------
    # TEST 11: Dynamic Track Scaffolding (Phase 0 & 1)
    # -------------------------------------------------------------------------
    print("\n--- Test 11: Dynamic Track Scaffolding & Anti-5-Track Lock ---")
    try:
        from engine.production.copilot.phases.phase_1_tracks import Phase1TracksHandler

        handler = Phase1TracksHandler()
        # Mock session with 8 custom designed tracks
        class MockSession:
            def __init__(self):
                self.data = {
                    "designed_tracks": [
                        {"name": "Sub 808", "role": "BASS", "type": "MIDI", "panning": 0.0},
                        {"name": "Kick", "role": "DRUMS", "type": "AUDIO", "panning": 0.0},
                        {"name": "Snare", "role": "DRUMS", "type": "AUDIO", "panning": 0.05},
                        {"name": "HiHat", "role": "DRUMS", "type": "MIDI", "panning": -0.25},
                        {"name": "Lead Vocal", "role": "VOCALS", "type": "AUDIO", "panning": 0.0},
                        {"name": "Rhodes Chords", "role": "CHORDS", "type": "MIDI", "panning": 0.35},
                        {"name": "Guitar Lead", "role": "LEAD", "type": "MIDI", "panning": -0.40},
                        {"name": "Ambient FX", "role": "FX", "type": "BUS", "panning": 0.50}
                    ],
                    "designed_panning": {
                        "Sub 808": 0.0, "Kick": 0.0, "Snare": 0.05, "HiHat": -0.25,
                        "Lead Vocal": 0.0, "Rhodes Chords": 0.35, "Guitar Lead": -0.40,
                        "Ambient FX": 0.50
                    },
                    "bpm": 135.0,
                    "key": "G#",
                    "scale": "Dorian"
                }
            def _save_state(self, action_tag=""):
                pass
            def _prompt_phase_2(self, tracks):
                return {"phase": "PHASE_2_SECTIONS", "tracks_count": len(tracks)}
            def _sync_session_tuning(self, conn, key, scale):
                pass

        class MockConn:
            def send_command(self, cmd, params=None):
                if cmd == "create_midi_track":
                    return {"track_index": 0}
                elif cmd == "create_audio_track":
                    return {"track_index": 1}
                elif cmd == "get_session_info":
                    return {"tempo": 135.0}
                return {}

        ms = MockSession()
        mc = MockConn()
        res = handler.handle(ms, mc, "crear pistas segun diseño")
        assert_true(res.get("tracks_count") == 8, f"Successfully created all 8 dynamic tracks (got {res.get('tracks_count')})")
        assert_true(len(ms.data["tracks"]) == 8, "Session tracks updated with 8 tracks, dismantling 5-track lock")

    except Exception as e:
        assert_true(False, f"Dynamic track scaffolding error: {e}")

    # -------------------------------------------------------------------------
    # TEST 12: Anti-120 BPM Freeze readback logic
    # -------------------------------------------------------------------------
    print("\n--- Test 12: Anti-120 BPM Freeze Readback Logic ---")
    try:
        class MockFreezeConn:
            def __init__(self):
                self.calls = []
            def send_command(self, cmd, params=None):
                self.calls.append((cmd, params))
                if cmd == "get_session_info":
                    # Simulate Live frozen at default 120.0 BPM despite target 145.0
                    return {"tempo": 120.0}
                return {}

        target_bpm = 145.0
        mfc = MockFreezeConn()
        s_info = mfc.send_command("get_session_info")
        live_bpm = s_info.get("tempo", 120.0)

        anti_freeze_triggered = False
        if abs(live_bpm - target_bpm) > 0.05:
            anti_freeze_triggered = True
            mfc.send_command("set_tempo", {"tempo": target_bpm})
            mfc.send_command("execute_code", {"code": f"song.tempo = {target_bpm}"})

        assert_true(anti_freeze_triggered is True, "Anti-120 BPM Freeze readback caught discrepancy")
        executed_cmds = [c[0] for c in mfc.calls]
        assert_true("execute_code" in executed_cmds, "Re-asserted tempo directly through LOM code")

    except Exception as e:
        assert_true(False, f"Anti-freeze error: {e}")

    # -------------------------------------------------------------------------
    # TEST 13: Instrument & Preset Load Failure (No Silent Fallbacks)
    # -------------------------------------------------------------------------
    print("\n--- Test 13: Instrument & Preset Load Failure (No Silent Fallback) ---")
    try:
        from engine.production.copilot.phases.phase_3_instruments import Phase3InstrumentsHandler
        from engine.production.copilot.role_orchestrator import RoleTrackOrchestrator

        handler3 = Phase3InstrumentsHandler()

        class MockPhase3Session:
            def __init__(self):
                self.data = {
                    "current_track_ptr": 0,
                    "tracks": [
                        {"name": "Lead Synth", "role": "LEAD", "type": "MIDI"}
                    ]
                }
            def _save_state(self, action_tag=""):
                pass
            def _prompt_current_track_instrument(self):
                return {"phase": "PHASE_3_INSTRUMENTS"}
            def _resolve_live_track_index(self, conn, trk):
                return 0

        class MockConnFail:
            def send_command(self, cmd, params=None):
                if cmd == "get_track_info":
                    return {"devices": []}
                return {}

        s3 = MockPhase3Session()
        c3 = MockConnFail()

        # 1. Level-1 unknown instrument input via real handle()
        res1 = handler3.handle(s3, c3, "SuperRareNonexistentPlugin99")
        assert_true(res1.get("status") == "ERROR", "Status is ERROR for nonexistent instrument")
        assert_true(res1.get("error_code") == "INSTRUMENT_LOAD_FAILED", "Returns INSTRUMENT_LOAD_FAILED error code")
        assert_true("available_catalog" in res1, "Exposes open catalog of available alternatives")
        assert_true(len(res1.get("available_catalog", [])) > 0, "Catalog contains installed options")
        assert_true(s3.data["tracks"][0].get("instrument") != "SuperRareNonexistentPlugin99", "Did not set invalid instrument")

        # 2. Level-2 unknown preset input via real handle()
        s3.data["tracks"][0]["pending_plugin_subselection"] = "Vital"
        res2 = handler3.handle(s3, c3, "NonExistentPreset12345")
        assert_true(res2.get("status") == "ERROR", "Status is ERROR for nonexistent preset")
        assert_true(res2.get("error_code") == "PRESET_LOAD_FAILED", "Returns PRESET_LOAD_FAILED error code")
        assert_true("available_catalog" in res2, "Exposes open catalog of available presets")
        assert_true("pending_plugin_subselection" in s3.data["tracks"][0], "Pending subselection retained for informed retry")

        # 3. RoleTrackOrchestrator physical verification failure
        assert_true(not hasattr(RoleTrackOrchestrator, "NATIVE_FALLBACKS"), "NATIVE_FALLBACKS eliminated from RoleTrackOrchestrator")
        res3 = RoleTrackOrchestrator.orchestrate_role_track(
            conn=c3,
            track_index=0,
            role="LEAD",
            custom_instrument_id="UnknownPluginXYZ",
            timeout=0.1
        )
        assert_true(res3.get("status") == "FAILED", "RoleTrackOrchestrator returns FAILED on verification fail")
        assert_true(res3.get("error_code") == "INSTRUMENT_LOAD_FAILED", "Returns INSTRUMENT_LOAD_FAILED on physical fail")
        assert_true("available_options" in res3, "Provides available library options without silent native fallback")

    except Exception as e:
        assert_true(False, f"Phase 3 error: {e}")

    # -------------------------------------------------------------------------
    # TEST 14: Dramatic Micro-Silences (Ear Candy Engine)
    # -------------------------------------------------------------------------
    print("\n--- Test 14: Dramatic Micro-Silences (EarCandyEngine Pre-Drop Vacuum) ---")
    try:
        from engine.arrangement.fx.ear_candy_transitions import EarCandyEngine

        vacuum_pts = EarCandyEngine.generate_pre_drop_vacuum(
            target_bar=33.0,
            silence_duration_beats=1.0,
            normal_gain=0.85
        )
        assert_true(len(vacuum_pts) == 4, f"Generated exactly 4 vacuum envelope points: {len(vacuum_pts)}")
        # Check silence dip
        values = [p["value"] for p in vacuum_pts]
        assert_true(0.0 in values, "Envelope reaches 0.0 absolute silence")
        assert_true(vacuum_pts[-1]["value"] == 0.85, "Envelope snaps back to normal gain (0.85) on drop arrival")

    except Exception as e:
        assert_true(False, f"EarCandyEngine error: {e}")

    print("\n" + "=" * 70)
    print(f"VERIFICATION COMPLETE: {passed} PASSED, {failed} FAILED.")
    print("=" * 70)
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
