# tests/test_channel_strip.py
import pytest
from engine.mix.channel_strip import ChannelStripEngine


def test_eq_frequency_normalization_accuracy():
    """Verify logarithmic mapping matches Live 12's EQ Eight frequency scale."""
    # 10 Hz is min (0.0), 22000 Hz is max (1.0)
    assert ChannelStripEngine.freq_to_normalized(10.0) == 0.0
    assert ChannelStripEngine.freq_to_normalized(22000.0) == 1.0

    # Test key musical inflection points
    v_30 = ChannelStripEngine.freq_to_normalized(30.0)
    assert 0.14 <= v_30 <= 0.15

    v_100 = ChannelStripEngine.freq_to_normalized(100.0)
    assert 0.29 <= v_100 <= 0.31

    v_1000 = ChannelStripEngine.freq_to_normalized(1000.0)
    assert 0.59 <= v_100 <= 0.61 or 0.59 <= v_1000 <= 0.61

    v_10000 = ChannelStripEngine.freq_to_normalized(10000.0)
    assert 0.89 <= v_10000 <= 0.91


def test_role_eq_settings():
    """Verify surgical HPF and shaping profiles are defined for all roles."""
    roles = ["kick", "808", "snare", "hats", "keys", "lead", "vocal", "foley"]
    for r in roles:
        s = ChannelStripEngine.get_role_eq_settings(r)
        assert "f1_on" in s
        assert "f1_type" in s
        assert "f1_freq" in s
        assert "f2_gain" in s
        assert "f4_gain" in s

    # 808/sub should have low HPF (around 25Hz) and LPF
    sub_s = ChannelStripEngine.get_role_eq_settings("808")
    assert sub_s["f1_freq"] < ChannelStripEngine.freq_to_normalized(35.0)

    # Hats should have high HPF (around 350Hz)
    hat_s = ChannelStripEngine.get_role_eq_settings("hats")
    assert hat_s["f1_freq"] > ChannelStripEngine.freq_to_normalized(300.0)


def test_apply_channel_strip_mock():
    """Verify apply_channel_strip returns SUCCESS and valid settings without live connection."""
    res = ChannelStripEngine.apply_channel_strip(conn=None, track_index=4, role="lead")
    assert res["status"] == "SUCCESS"
    assert res["track_index"] == 4
    assert res["role"] == "lead"
    assert "settings" in res


def test_apply_bus_processing_mock():
    """Verify apply_bus_processing handles both drum and synth busses in mock mode."""
    drum_res = ChannelStripEngine.apply_bus_processing(conn=None, group_track_index=0, bus_type="drums")
    assert drum_res["status"] == "SUCCESS"
    assert drum_res["group_track_index"] == 0

    synth_res = ChannelStripEngine.apply_bus_processing(conn=None, group_track_index=3, bus_type="synths")
    assert synth_res["status"] == "SUCCESS"
    assert synth_res["group_track_index"] == 3


def test_pitch_and_freq_conversions():
    """Verify musical pitch to physical frequency calculations."""
    assert ChannelStripEngine.pitch_to_hz(69) == 440.0   # A4 = 440 Hz
    assert ChannelStripEngine.pitch_to_hz(33) == 55.0    # A1 = 55 Hz (SubLab fundamental)
    assert ChannelStripEngine.pitch_to_hz(45) == 110.0   # A2 = 110 Hz (Piano fundamental)
    assert ChannelStripEngine.pitch_to_hz(57) == 220.0   # A3 = 220 Hz
    assert ChannelStripEngine.pitch_to_hz(81) == 880.0   # A5 = 880 Hz (Lead 1 fundamental)

    # Normalized round-trip test
    for hz in [25.0, 55.0, 110.0, 440.0, 1000.0, 5000.0, 12000.0]:
        norm = ChannelStripEngine.freq_to_normalized(hz)
        back = ChannelStripEngine.normalized_to_freq(norm)
        assert abs(back - hz) / hz < 0.05  # Within 5% accuracy


def test_adaptive_eq_protects_sublab_sub_bass():
    """Verify that SubLabXL sub-bass at 55 Hz receives HPF <= 25 Hz and preserves fundamental."""
    profile = {
        "track_index": 6,
        "track_name": "Synth 1",
        "devices": ["SubLabXL", "EQ Eight"],
        "note_count": 576,
        "min_pitch": 33,
        "max_pitch": 38,
        "dominant_pitch": 33,
        "min_hz": 55.0,
        "max_hz": 73.4,
        "dominant_hz": 55.0,
        "detected_role": "bass"
    }
    settings = ChannelStripEngine.get_adaptive_eq_settings(profile)
    assert settings["role"] == "bass"
    assert settings["hpf_hz"] <= 25.0  # Cut rumble ONLY, leaving 55 Hz 100% intact!
    assert settings["f1_freq"] <= ChannelStripEngine.freq_to_normalized(25.0)
    # Band 2 body boost centered at sub fundamental
    f2_hz = ChannelStripEngine.normalized_to_freq(settings["f2_freq"])
    assert 50.0 <= f2_hz <= 60.0


def test_adaptive_eq_piano_and_leads():
    """Verify that harmonic instruments preserve their lowest musical notes."""
    # Piano at 110 Hz
    piano_profile = {
        "track_name": "Piano",
        "devices": ["Omnisphere"],
        "min_hz": 110.0,
        "max_hz": 349.2,
        "detected_role": "piano"
    }
    piano_settings = ChannelStripEngine.get_adaptive_eq_settings(piano_profile)
    assert piano_settings["hpf_hz"] < 110.0  # HPF must be below fundamental 110 Hz
    assert 70.0 <= piano_settings["hpf_hz"] <= 90.0

    # Lead 1 at 880 Hz
    lead_profile = {
        "track_name": "Lead 1",
        "devices": ["Wavetable"],
        "min_hz": 880.0,
        "max_hz": 1760.0,
        "detected_role": "lead"
    }
    lead_settings = ChannelStripEngine.get_adaptive_eq_settings(lead_profile)
    assert lead_settings["hpf_hz"] <= 350.0
    assert lead_settings["hpf_hz"] < 880.0  # Leaves 880 Hz fundamental untouched

