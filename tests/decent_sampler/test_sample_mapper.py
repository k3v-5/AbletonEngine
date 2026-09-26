# tests/decent_sampler/test_sample_mapper.py
"""
Unit tests for SampleMapPlanner (Mathematical mapping intelligence).
"""

from engine.sound_design.decent_sampler.sample_analyzer import SampleAsset
from engine.sound_design.decent_sampler.sample_mapper import SampleMapPlanner, PlannedLayer
from engine.sound_design.decent_sampler.model import InstrumentModel


class TestSampleMapPlanner:
    def test_calculate_note_boundaries_gapless(self):
        """Verifies note intervals cover min_note to max_note without gaps or overlaps."""
        roots = [36, 48, 60, 72]  # C2, C3, C4, C5
        boundaries = SampleMapPlanner.calculate_note_boundaries(roots, min_note=21, max_note=108)

        assert len(boundaries) == 4

        # First zone starts at min_note
        assert boundaries[0][0] == 21

        # Check contiguity: boundaries[i][1] + 1 == boundaries[i+1][0]
        for i in range(len(boundaries) - 1):
            hi_current = boundaries[i][1]
            lo_next = boundaries[i + 1][0]
            assert hi_current + 1 == lo_next, f"Gap or overlap detected between {hi_current} and {lo_next}"

        # Last zone ends at max_note
        assert boundaries[-1][1] == 108

    def test_velocity_layers_planning(self):
        """Verifies 3 velocity layers are split cleanly from 0 to 127."""
        layers = SampleMapPlanner.plan_velocity_layers(3)
        assert len(layers) == 3
        assert layers[0].lo_vel == 0
        assert layers[0].hi_vel == 42
        assert layers[1].lo_vel == 43
        assert layers[1].hi_vel == 84
        assert layers[2].lo_vel == 85
        assert layers[2].hi_vel == 127

    def test_plan_with_multi_velocity_and_release(self):
        """Plans complete instrument with multi-velocity and release samples."""
        assets = [
            SampleAsset(path="piano_c3_soft.wav", root_note=48, velocity_layer="soft"),
            SampleAsset(path="piano_c4_soft.wav", root_note=60, velocity_layer="soft"),
            SampleAsset(path="piano_c3_hard.wav", root_note=48, velocity_layer="hard"),
            SampleAsset(path="piano_c4_hard.wav", root_note=60, velocity_layer="hard"),
            SampleAsset(path="pedal_up_c3.wav", root_note=48, is_release_sample=True),
        ]

        planned = SampleMapPlanner.plan(assets, min_note=21, max_note=108)

        # 4 regular zones (2 soft, 2 hard) + 1 release zone = 5 planned zones
        assert len(planned) == 5

        soft_zones = [z for z in planned if z.group_name == "Layer_soft"]
        hard_zones = [z for z in planned if z.group_name == "Layer_hard"]
        rel_zones = [z for z in planned if z.is_release]

        assert len(soft_zones) == 2
        assert len(hard_zones) == 2
        assert len(rel_zones) == 1

        # Check soft velocity range vs hard velocity range
        assert soft_zones[0].hi_vel < hard_zones[0].lo_vel
        assert rel_zones[0].lo_note == 21
        assert rel_zones[0].hi_note == 108

    def test_apply_to_instrument(self):
        """Translates planned zones into an InstrumentModel."""
        assets = [
            SampleAsset(path="cello_c2.wav", root_note=36),
            SampleAsset(path="cello_c3.wav", root_note=48),
        ]
        planned = SampleMapPlanner.plan(assets, min_note=36, max_note=84)
        inst = InstrumentModel(name="Solo Cello")
        SampleMapPlanner.apply_to_instrument(inst, planned)

        assert len(inst.groups) == 1
        assert len(inst.groups[0].samples) == 2
        assert inst.groups[0].samples[0].lo_note == 36
        assert inst.groups[0].samples[1].hi_note == 84
