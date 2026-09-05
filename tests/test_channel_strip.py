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
