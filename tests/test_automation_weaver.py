# tests/test_automation_weaver.py
import pytest
from engine.arrangement.automation.weaver import ArrangementAutomationWeaver, TransitionAutomationType


def test_filter_sweep_up_curve():
    points = ArrangementAutomationWeaver.generate_filter_sweep(
        start_bar=16.0,
        duration_bars=4.0,
        direction="up",
        min_val=0.2,
        max_val=0.9,
        curve="exponential",
        steps_per_bar=4
    )

    assert len(points) == 17
    assert points[0]["time"] == 64.0  # 16 * 4
    assert points[-1]["time"] == 80.0 # 20 * 4
    assert points[0]["value"] == 0.2
    assert points[-1]["value"] == 0.9
    # Exponential curve starts gradual and accelerates upward
    mid_point = points[len(points) // 2]
    linear_mid = 0.2 + (0.9 - 0.2) * 0.5
    assert mid_point["value"] < linear_mid


def test_reverb_washout_reset():
    points = ArrangementAutomationWeaver.generate_reverb_washout(
        start_bar=24.0,
        duration_bars=4.0,
        start_wet=0.1,
        max_wet=0.8,
        reset_wet=0.0
    )

    # Peak wet right before the end
    assert points[-2]["value"] == pytest.approx(0.8, abs=0.01)
    # Instant snap to 0.0 on downbeat of next section
    assert points[-1]["value"] == 0.0
    assert points[-1]["time"] > points[-2]["time"]


def test_sub_cleanup():
    points = ArrangementAutomationWeaver.generate_sub_cleanup(
        start_bar=31.0,
        duration_bars=1.0,
        normal_gain=0.85,
        cut_gain=0.0
    )

    assert len(points) == 4
    assert points[0]["value"] == 0.85
    # Cut gain right before drop
    assert points[2]["value"] == 0.0
    # Restores on drop
    assert points[3]["value"] == 0.85
