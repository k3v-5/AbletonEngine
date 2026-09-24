# tests/decent_sampler/test_model.py
"""
Unit tests for InstrumentModel (Intermediate Representation).
"""

from engine.sound_design.decent_sampler.model import (
    InstrumentModel,
    GroupModel,
    SampleZoneModel,
    EffectModel,
    ControlModel,
    BindingModel,
)


class TestInstrumentModel:
    def test_model_composition_and_counting(self):
        inst = InstrumentModel(name="Test Piano")
        grp1 = GroupModel(name="Soft")
        grp1.add_sample(SampleZoneModel(path="soft_c3.wav", root_note=48, lo_note=36, hi_note=59))
        grp1.add_sample(SampleZoneModel(path="soft_c4.wav", root_note=60, lo_note=60, hi_note=84))

        grp2 = GroupModel(name="Hard")
        grp2.add_sample(SampleZoneModel(path="hard_c3.wav", root_note=48, lo_note=36, hi_note=59))

        inst.add_group(grp1).add_group(grp2)

        assert inst.total_samples() == 3
        assert len(inst.groups) == 2

    def test_model_deep_clone(self):
        inst = InstrumentModel(name="Original")
        grp = GroupModel(name="G1")
        grp.add_sample(SampleZoneModel(path="sample.wav", root_note=60))
        inst.add_group(grp)

        cloned = inst.clone()
        cloned.name = "Cloned"
        cloned.groups[0].samples[0].root_note = 62

        assert inst.name == "Original"
        assert inst.groups[0].samples[0].root_note == 60
        assert cloned.groups[0].samples[0].root_note == 62
