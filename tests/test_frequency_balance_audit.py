# tests/test_frequency_balance_audit.py
"""
Test Suite for Gain Staging, Master Headroom Calibration, and Frequency Slotting:
Verifies that individual fader levels prevent summing overload (+2 to +3 dBFS)
and guarantee a clean -6.0 dBFS Master bus headroom margin before mastering.
Also verifies 5-band frequency zoning and HPF scaffolds.
"""

import math
import pytest
from engine.mix.gain_staging.auto_stager import AutoGainStagingEngine, TrackGainCalibration
from engine.mix.frequency_slotting import FrequencySlottingEngine


class TestGainStagingHeadroom:
    def test_fader_taper_conversion(self):
        # 0 dB should map to ~0.85 (Live unity)
        assert abs(AutoGainStagingEngine.db_to_linear(0.0) - 0.85) < 0.01

        # -6 dB should be lower (~0.60)
        assert 0.58 < AutoGainStagingEngine.db_to_linear(-6.0) < 0.62

        # -12 dB should be around ~0.42-0.43
        assert 0.41 < AutoGainStagingEngine.db_to_linear(-12.0) < 0.45

        # Silence (-70 dB or below)
        assert AutoGainStagingEngine.db_to_linear(-75.0) == 0.0

    def test_session_gain_staging_prevents_clipping(self):
        # Simulate 8 tracks in a full arrangement
        tracks = [
            {"track_index": 0, "name": "Kick 808 Main"},
            {"track_index": 1, "name": "808 Sub Bass"},
            {"track_index": 2, "name": "Snare Mainstream"},
            {"track_index": 3, "name": "HiHats Closed"},
            {"track_index": 4, "name": "Rhodes Piano Chords"},
            {"track_index": 5, "name": "Lead Synth Solo"},
            {"track_index": 6, "name": "Vocal Chops Hook"},
            {"track_index": 7, "name": "Foley Vinyl FX"},
        ]

        # Calculate calibrated faders for -6.0 dBFS master headroom
        calibrations = AutoGainStagingEngine.calculate_session_calibration(
            tracks=tracks,
            target_master_headroom_db=-6.0
        )

        assert len(calibrations) == 8

        # Calculate simulated acoustic summation: P = sum(10^(dB/10))
        total_power = sum(math.pow(10.0, c.target_peak_db / 10.0) for c in calibrations)
        estimated_master_peak = 10.0 * math.log10(total_power)

        # Master bus peak must not exceed -6.0 dBFS
        assert estimated_master_peak <= -6.0 + 0.05
        # Gain staging hierarchy: Kick & Snare should be louder than Foley
        kick_cal = next(c for c in calibrations if c.role == "kick")
        foley_cal = next(c for c in calibrations if c.role == "foley")
        assert kick_cal.target_peak_db > foley_cal.target_peak_db
        assert kick_cal.fader_gain_linear > foley_cal.fader_gain_linear


class TestFrequencyZoning:
    def test_normalized_frequency_conversion(self):
        # 10 Hz -> 0.0, 22000 Hz -> 1.0
        assert FrequencySlottingEngine.freq_to_normalized(10.0) == 0.0
        assert FrequencySlottingEngine.freq_to_normalized(22000.0) == 1.0

        # 1000 Hz should be around middle log scale (~0.60)
        norm_1k = FrequencySlottingEngine.freq_to_normalized(1000.0)
        assert 0.58 < norm_1k < 0.62

    def test_hpf_scaffold_hierarchy(self):
        scaffold = FrequencySlottingEngine.get_multitrack_hpf_scaffold()
        assert "sub_808" in scaffold
        assert "kick" in scaffold
        assert "chords_keys" in scaffold
        assert "hihats_perc" in scaffold

        # 808 HPF is sub-rumble cut (28 Hz)
        assert scaffold["sub_808"]["hpf_freq_hz"] == 28.0
        # Rhodes HPF clears space for bass (110 Hz)
        assert scaffold["chords_keys"]["hpf_freq_hz"] == 110.0
        # Hi-hats cleared all low end (320 Hz)
        assert scaffold["hihats_perc"]["hpf_freq_hz"] == 320.0

    def test_complementary_carving(self):
        plan = FrequencySlottingEngine.calculate_complementary_carving(
            role_primary="kick",
            role_secondary="sub_808",
            primary_fundamental_hz=55.0,
            secondary_fundamental_hz=35.0
        )
        assert plan["pair"] == "kick_vs_sub_808"
        assert "primary" in plan
        assert "secondary" in plan
