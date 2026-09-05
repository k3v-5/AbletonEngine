# tests/test_arrangement_automation_injection.py
import pytest
from engine.arrangement.transitions.automation import TransitionAutomationEngine

def test_transition_filter_sweep_injection_payload():
    points = TransitionAutomationEngine.generate_filter_sweep(
        start_bar=17.0,
        duration_bars=4.0,
        direction="up",
        min_freq=200.0,
        max_freq=18000.0,
        curve="exponential",
        resolution_beats=0.25
    )
    
    assert len(points) == 65
    assert points[0]["time"] == 68.0  # 17 * 4.0
    assert points[-1]["time"] == 84.0 # 68 + 16
    assert points[0]["value"] == 200.0
    assert points[-1]["value"] == 18000.0

    # Test serialization format suitable for Ableton LOM remote script
    payload = {
        "track_index": 3,
        "device_index": 0,
        "parameter": "Frequency",
        "points": points
    }
    assert payload["track_index"] == 3
    assert len(payload["points"]) == 65

def test_transition_volume_swell_with_silence_payload():
    points = TransitionAutomationEngine.generate_volume_swell(
        start_bar=31.0,
        duration_bars=2.0,
        start_vol=0.2,
        end_vol=0.9,
        pre_drop_silence_beats=1.0,
        curve="ease_in"
    )
    # The silence gap before the drop is at 0.0
    assert points[-2]["value"] == 0.0
    assert points[-3]["value"] == 0.0
    # Downbeat of the drop restores volume
    assert points[-1]["value"] == pytest.approx(0.9, abs=0.01)
    # Peak swell before silence gap
    non_zero_pts = [p for p in points[:-1] if p["value"] > 0]
    assert max(p["value"] for p in non_zero_pts) == pytest.approx(0.9, abs=0.01)
