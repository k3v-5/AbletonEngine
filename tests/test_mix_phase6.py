# tests/test_mix_phase6.py
"""
Test Suite for Phase 6: Surgical Mix & Frequency Balancing.
Validates:
1. FrequencySlottingEngine: 8-track HPF scaffolding, complementary notch carving (Kick vs 808, Vocal vs Chords).
2. PhaseAlignmentEngine: Pearson phase correlation, sub-bass mono collapse (<120Hz), micro-delay compensation.
3. VocalLeadFaderRider: Dynamic fader riding across 96 bars (-2.5dB Intro to +2.8dB Climax).
4. MultiTrackSidechainCoordinator: Routing matrix, Ableton compressor normalized parameter mappings.
5. ExecutiveCopilotEngine: Phase 6 mix intelligence decisions discovery and execution.
"""

import pytest
import math
import numpy as np
from engine.mix.frequency_slotting import FrequencySlottingEngine
from engine.mix.phase_alignment import PhaseAlignmentEngine
from engine.mix.fader_rider import VocalLeadFaderRider
from engine.mix.multitrack_sidechain import MultiTrackSidechainCoordinator
from engine.production.copilot.stepper import ExecutiveCopilotEngine, ProductionPhase


class TestFrequencySlottingEngine:
    """Tests for frequency separation and complementary EQ carving."""

    def test_multitrack_hpf_scaffold(self):
        hpf = FrequencySlottingEngine.get_multitrack_hpf_scaffold()
        assert len(hpf) == 8
        roles = ["sub_808", "kick", "snare", "hihats_perc", "chords_keys", "lead_synth", "vocals_chops", "foley_fx"]
        for r in roles:
            assert r in hpf
            assert hpf[r]["hpf_freq_hz"] > 0.0
            assert 0.0 <= hpf[r]["normalized"] <= 1.0
            assert hpf[r]["q"] > 0.0

        # Sub 808 HPF should be low (28Hz); Hi-hats should be high (320Hz)
        assert hpf["sub_808"]["hpf_freq_hz"] == 28.0
        assert hpf["hihats_perc"]["hpf_freq_hz"] == 320.0

    def test_complementary_carving_kick_bass(self):
        carving = FrequencySlottingEngine.calculate_complementary_carving("kick", "bass", 52.0, 38.0)
        assert carving["pair"] == "kick_vs_bass"
        primary_cuts = carving["primary"]["cuts"]
        secondary_cuts = carving["secondary"]["cuts"]

        assert len(primary_cuts) == 1
        assert primary_cuts[0]["freq_hz"] == 38.0
        assert primary_cuts[0]["gain_db"] < 0.0

        assert len(secondary_cuts) == 1
        assert secondary_cuts[0]["freq_hz"] == 52.0
        assert secondary_cuts[0]["gain_db"] < 0.0

    def test_complementary_carving_vocal_chords(self):
        carving = FrequencySlottingEngine.calculate_complementary_carving("vocal", "chords")
        cuts = carving["secondary"]["cuts"]
        assert len(cuts) == 1
        assert cuts[0]["freq_hz"] == 2800.0
        assert cuts[0]["gain_db"] == -3.0

    def test_full_session_slotting_plan(self):
        plan = FrequencySlottingEngine.generate_full_session_slotting_plan()
        assert plan["status"] == "SUCCESS"
        assert len(plan["complementary_carvings"]) == 3
        assert len(plan["hpf_enforcement"]) == 8


class TestPhaseAlignmentEngine:
    """Tests for phase correlation and mono compatibility auditing."""

    def test_phase_correlation_identical_and_inverted(self):
        t = np.linspace(0, 1, 1000)
        sig1 = np.sin(2 * np.pi * 50 * t).tolist()
        sig2 = sig1.copy()
        sig_inverted = (-np.array(sig1)).tolist()

        # Identical signals -> rho = 1.0
        rho_pos = PhaseAlignmentEngine.calculate_phase_correlation(sig1, sig2)
        assert abs(rho_pos - 1.0) < 0.001

        # Perfectly inverted -> rho = -1.0
        rho_neg = PhaseAlignmentEngine.calculate_phase_correlation(sig1, sig_inverted)
        assert abs(rho_neg - (-1.0)) < 0.001

    def test_sub_bass_mono_audit(self):
        # Case 1: Pure mono sub
        clean_sub = PhaseAlignmentEngine.audit_sub_bass_mono(sub_energy_mid=1.0, sub_energy_side=0.0)
        assert clean_sub["mono_compliant"] is True
        assert clean_sub["recommendation"] == "OK"

        # Case 2: Stereo sub leakage
        leaky_sub = PhaseAlignmentEngine.audit_sub_bass_mono(sub_energy_mid=0.7, sub_energy_side=0.3)
        assert leaky_sub["mono_compliant"] is False
        assert leaky_sub["recommendation"] == "APPLY_BASS_MONO_UTILITY"
        assert leaky_sub["utility_settings"]["bass_mono"] == 1.0
        assert leaky_sub["utility_settings"]["bass_mono_freq"] == 120.0

    def test_micro_delay_offset(self):
        # 441 samples at 44100 Hz = 10 ms
        delay = PhaseAlignmentEngine.calculate_micro_delay_offset(
            kick_attack_sample=1000,
            bass_attack_sample=1441,
            sample_rate=44100
        )
        assert delay["sample_offset"] == 441
        assert abs(delay["delay_ms"] - 10.0) < 0.1
        assert delay["direction"] == "DELAY_BASS"

    def test_phase_audit_report(self):
        report = PhaseAlignmentEngine.generate_phase_audit_report()
        assert report["status"] == "SUCCESS"
        assert "sub_bass_mono" in report
        assert len(report["stem_correlations"]) >= 2


class TestVocalLeadFaderRider:
    """Tests for dynamic vocal and lead fader riding across 96 bars."""

    def test_fader_envelope_points_across_96_bars(self):
        envelope = VocalLeadFaderRider.generate_fader_automation_envelope(role="vocal")
        assert len(envelope) > 10
        # First point at beat 0, last point at beat 384
        assert envelope[0]["time"] == 0.0
        assert envelope[-1]["time"] == 384.0
        # All values must be valid normalized Ableton fader levels
        assert all(0.0 <= p["value"] <= 1.0 for p in envelope)

    def test_chorus_fader_boost(self):
        # In the chorus (beat 128.0 to 192.0), fader should be louder than Intro (beat 0.0 to 32.0)
        envelope = VocalLeadFaderRider.generate_fader_automation_envelope(role="vocal")
        intro_val = [p["value"] for p in envelope if p["time"] == 0.0][0]
        chorus_val = [p["value"] for p in envelope if 128.0 <= p["time"] <= 190.0][0]
        assert chorus_val > intro_val

    def test_fader_riding_manifest(self):
        manifest = VocalLeadFaderRider.get_fader_riding_manifest()
        assert manifest["status"] == "SUCCESS"
        assert manifest["total_sections"] == 8
        sections = [s["section"] for s in manifest["sections"]]
        assert "Chorus 1" in sections
        assert "Final Chorus" in sections


class TestMultiTrackSidechainCoordinator:
    """Tests for session sidechain matrix and compressor mappings."""

    def test_sidechain_matrix_coverage(self):
        matrix = MultiTrackSidechainCoordinator.get_multitrack_sidechain_matrix()
        assert matrix["status"] == "SUCCESS"
        assert matrix["total_routes"] >= 4
        ids = [r["id"] for r in matrix["routes"]]
        assert "SC-KICK-TO-BASS" in ids
        assert "SC-KICK-TO-REVERB" in ids
        assert "SC-VOCAL-TO-CHORDS" in ids

    def test_compressor_device_parameter_mapping(self):
        params = MultiTrackSidechainCoordinator.generate_compressor_device_parameters("SC-KICK-TO-BASS")
        assert params["sidechain_on"] == 1.0
        assert 0.0 <= params["threshold"] <= 1.0
        assert 0.0 <= params["ratio"] <= 1.0
        assert 0.0 <= params["attack"] <= 1.0
        assert 0.0 <= params["release"] <= 1.0


class TestCopilotPhase6Integration:
    """Tests for Copilot discovering and executing Phase 6 mix decisions."""

    def test_copilot_discovers_phase6_decisions(self):
        copilot = ExecutiveCopilotEngine()
        mock_tracks = [
            {"name": "Kick (808)", "track_index": 0},
            {"name": "Snare & Clap", "track_index": 1},
            {"name": "Rhodes Piano", "track_index": 2},
            {"name": "Lead Synth", "track_index": 3},
        ]
        state = copilot.inspect_session(tracks=mock_tracks)
        pending_ids = [d.id for d in state.pending_decisions]

        assert "DEC-P6-FREQUENCY-SLOTTING" in pending_ids
        assert "DEC-P6-PHASE-MONO-AUDIT" in pending_ids
        assert "DEC-P6-FADER-RIDING" in pending_ids
        assert "DEC-P6-MULTITRACK-SIDECHAIN" in pending_ids

    def test_copilot_executes_phase6_decisions(self):
        copilot = ExecutiveCopilotEngine()
        mock_tracks = [
            {"name": "Kick (808)", "track_index": 0},
            {"name": "Snare & Clap", "track_index": 1},
        ]
        copilot.inspect_session(tracks=mock_tracks)

        # Execute frequency slotting with YES
        dec_id = "DEC-P6-FREQUENCY-SLOTTING"
        res1 = copilot.execute_decision(dec_id, choice="YES")
        assert res1["status"] == "success"
        assert res1["action"] == "APPLIED"
        assert dec_id in copilot.resolved_decisions

        # Execute Phase/Mono audit with NO (rejection)
        dec_phase = "DEC-P6-PHASE-MONO-AUDIT"
        res2 = copilot.execute_decision(dec_phase, choice="NO", justification="Stereo sub intended for wide soundscape")
        assert res2["status"] == "success"
        assert res2["action"] == "REJECTED"
        assert res2["justification"] == "Stereo sub intended for wide soundscape"
        assert dec_phase in copilot.resolved_decisions
