# tests/test_foley_texture.py
import pytest
from engine.sound.foley.texture import (
    TextureType,
    OrganicTextureProfile,
    OrganicTextureGenerator
)


class MockAdapter:
    def __init__(self):
        self.commands = []

    def send_command(self, cmd, params):
        self.commands.append((cmd, params))
        return {"status": "ok"}


def test_foley_profiles():
    prof_vinyl = OrganicTextureGenerator.get_profile(TextureType.VINYL_CRACKLE)
    assert prof_vinyl.texture_type == TextureType.VINYL_CRACKLE
    assert prof_vinyl.high_pass_hz >= 120.0
    assert prof_vinyl.low_pass_hz <= 9500.0
    assert prof_vinyl.stereo_width_pct >= 100.0

    prof_rain = OrganicTextureGenerator.get_profile("rain_natural")
    assert prof_rain.texture_type == TextureType.RAIN_NATURAL


def test_foley_breathing_envelope():
    points = OrganicTextureGenerator.calculate_breathing_envelope(
        tempo=120.0,
        total_bars=4.0,
        rate="1/2",
        depth_db=3.0,
        base_gain=0.5
    )
    assert len(points) > 0
    # Values should stay within reasonable amplitude bounds
    for p in points:
        assert 0.0 <= p["value"] <= 1.0
        assert p["time"] >= 0.0


def test_foley_rhythmic_ducking():
    kicks = [0.0, 2.0, 4.0]
    points = OrganicTextureGenerator.calculate_rhythmic_ducking(
        kick_strikes=kicks,
        snare_strikes=[1.0, 3.0],
        tempo=120.0,
        ducking_depth_db=-9.0,
        base_gain=0.6
    )
    assert len(points) >= len(kicks)
    # Check that hit points are ducked below base_gain
    hit_0 = next(p for p in points if abs(p["time"] - 0.0) < 0.05)
    assert hit_0["value"] < 0.6


def test_foley_live_device_chain():
    prof = OrganicTextureGenerator.get_profile(TextureType.TAPE_HISS)
    chain = OrganicTextureGenerator.build_live_device_chain(prof)
    names = [d["device_name"] for d in chain]
    assert "EQ Eight" in names
    assert "Utility" in names
    assert "Auto Filter" in names


def test_foley_configure_track_with_adapter():
    adapter = MockAdapter()
    res = OrganicTextureGenerator.configure_foley_bed(
        conn=adapter,
        track_index=15,
        texture_type="vinyl_crackle",
        total_bars=16.0,
        bpm=120.0,
        apply_breathing=True
    )
    assert res["status"] == "SUCCESS"
    assert res["track_index"] == 15
    assert res["envelope_points_count"] > 0
    cmd_names = [c[0] for c in adapter.commands]
    assert "set_track_name" in cmd_names
    assert "set_track_volume" in cmd_names
    assert "create_arrangement_automation_envelope" in cmd_names
