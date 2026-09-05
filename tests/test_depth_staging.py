# tests/test_depth_staging.py
import pytest
from engine.mix.spatial.depth import DepthStagingEngine, DepthPlane
from engine.music.models import NoteEvent


def test_plane_profiles_contrast():
    fg = DepthStagingEngine.calculate_plane_parameters(DepthPlane.FOREGROUND, tempo=120.0)
    bg = DepthStagingEngine.calculate_plane_parameters(DepthPlane.BACKGROUND, tempo=120.0)

    # Foreground should be dryer, shorter reverb, transparent high end
    assert fg.dry_wet < bg.dry_wet
    assert fg.decay_time_s < bg.decay_time_s
    assert fg.pre_delay_ms < bg.pre_delay_ms
    # Background has air absorption roll-off
    assert bg.high_cut_hz < fg.high_cut_hz


def test_ducked_reverb_envelope():
    notes = [
        NoteEvent(pitch=60, start=0.0, duration=2.0, velocity=100),
        NoteEvent(pitch=62, start=4.0, duration=2.0, velocity=100),
    ]

    pts = DepthStagingEngine.calculate_ducked_reverb_envelope(
        notes=notes,
        tempo=120.0,
        active_gain_db=-8.0,
        release_ms=100.0,
        baseline_gain=1.0
    )

    assert len(pts) > 0
    # Ducked value for -8 dB is ~ 0.398
    ducked_pts = [p for p in pts if p["value"] < 0.5]
    assert len(ducked_pts) >= 2

    # In gap between beat 2.0 and 4.0, volume recovers to 1.0
    recovery_pts = [p for p in pts if p["value"] == 1.0 and 2.0 < p["time"] < 4.0]
    assert len(recovery_pts) >= 1
