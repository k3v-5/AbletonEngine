# tests/test_transitions_engine.py
import unittest
from engine.arrangement.transitions.automation import TransitionAutomationEngine, AutomationCurveType

class TestTransitionsEngine(unittest.TestCase):

    def test_filter_sweep_up(self):
        """Filter sweep up ramps exponentially from 200 Hz to 20000 Hz."""
        points = TransitionAutomationEngine.generate_filter_sweep(
            start_bar=16.0,
            duration_bars=2.0,
            direction="up",
            min_freq=200.0,
            max_freq=20000.0,
            curve="exponential",
            resolution_beats=0.25
        )
        self.assertGreaterEqual(len(points), 8)
        self.assertAlmostEqual(points[0]["time"], 64.0, places=2)
        self.assertAlmostEqual(points[0]["value"], 200.0, delta=5.0)
        self.assertAlmostEqual(points[-1]["time"], 72.0, places=2)
        self.assertAlmostEqual(points[-1]["value"], 20000.0, delta=100.0)
        # Ensure values strictly increase
        self.assertLess(points[0]["value"], points[len(points)//2]["value"])
        self.assertLess(points[len(points)//2]["value"], points[-1]["value"])

    def test_filter_sweep_down(self):
        """Filter sweep down closes from 20000 Hz to 200 Hz for breakdowns/outros."""
        points = TransitionAutomationEngine.generate_filter_sweep(
            start_bar=32.0,
            duration_bars=1.0,
            direction="down",
            min_freq=200.0,
            max_freq=20000.0
        )
        self.assertAlmostEqual(points[0]["value"], 20000.0, delta=100.0)
        self.assertAlmostEqual(points[-1]["value"], 200.0, delta=5.0)
        self.assertGreater(points[0]["value"], points[-1]["value"])

    def test_reverb_washout_peaks_and_resets(self):
        """Reverb washout rises to max_wet and immediately snaps back to reset_wet at section start."""
        points = TransitionAutomationEngine.generate_reverb_washout(
            start_bar=15.0,
            duration_bars=1.0,
            start_wet=0.1,
            max_wet=0.85,
            reset_wet=0.0
        )
        self.assertGreater(len(points), 4)
        # Peak just before boundary
        penultimate = points[-2]
        self.assertAlmostEqual(penultimate["value"], 0.85, places=2)
        # Snap reset on boundary
        last = points[-1]
        self.assertAlmostEqual(last["time"], 64.0, places=2)
        self.assertEqual(last["value"], 0.0)

    def test_volume_swell_with_pre_drop_silence(self):
        """Volume swell builds tension and leaves 1 beat of silence before drop."""
        points = TransitionAutomationEngine.generate_volume_swell(
            start_bar=14.0,
            duration_bars=2.0,
            start_vol=0.2,
            end_vol=0.9,
            pre_drop_silence_beats=1.0
        )
        # Check start
        self.assertAlmostEqual(points[0]["time"], 56.0, places=2)
        self.assertAlmostEqual(points[0]["value"], 0.2, places=2)
        # Silence beat exists
        silence_points = [p for p in points if p["value"] == 0.0]
        self.assertTrue(len(silence_points) >= 2)
        # Drop impact restored
        self.assertAlmostEqual(points[-1]["value"], 0.9, places=2)

    def test_sidechain_pumping_cycles(self):
        """Sidechain pumping creates periodic volume ducking for each beat."""
        points = TransitionAutomationEngine.generate_sidechain_pump(
            start_bar=0.0,
            duration_bars=1.0,
            duck_depth=0.8,
            baseline_vol=0.85,
            rate_beats=1.0
        )
        # 1 bar = 4 beats = 4 cycles + final anchor
        self.assertGreaterEqual(len(points), 16)
        # Check that ducked values reach ~0.17 (0.85 * 0.2)
        min_v = min(p["value"] for p in points)
        self.assertAlmostEqual(min_v, 0.17, places=2)

    def test_energy_curve_across_sections(self):
        """Continuous energy curve scales parameters across multiple song sections."""
        sections = [
            {"name": "Intro", "start_bar": 0, "bars": 8, "energy": 0.3},
            {"name": "Verse", "start_bar": 8, "bars": 8, "energy": 0.5},
            {"name": "Build", "start_bar": 16, "bars": 4, "energy": 0.8},
            {"name": "Drop", "start_bar": 20, "bars": 8, "energy": 1.0}
        ]
        points = TransitionAutomationEngine.generate_energy_curve_automation(
            sections,
            min_val=0.2,
            max_val=1.0
        )
        self.assertGreaterEqual(len(points), 8)
        # Energy progression: Intro < Verse < Build < Drop
        intro_val = points[0]["value"]
        drop_val = points[-1]["value"]
        self.assertLess(intro_val, drop_val)
        self.assertAlmostEqual(drop_val, 1.0, places=2)

if __name__ == "__main__":
    unittest.main()
