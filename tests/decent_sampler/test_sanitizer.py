# tests/decent_sampler/test_sanitizer.py
"""
Unit tests for DecentSamplerSanitizer (Resilient Auto-Corrector).
"""

from engine.sound_design.decent_sampler.model import (
    InstrumentModel,
    GroupModel,
    SampleZoneModel,
    EffectModel,
)
from engine.sound_design.decent_sampler.sanitizer import DecentSamplerSanitizer
from engine.sound_design.decent_sampler.policies import AudioSafetyPolicy


class TestDecentSamplerSanitizer:
    def test_effect_type_lowercasing(self):
        inst = InstrumentModel()
        grp = GroupModel()
        grp.add_sample(SampleZoneModel(path="s.wav", root_note=60, lo_note=0, hi_note=127))
        inst.add_group(grp)
        inst.add_effect(EffectModel(type="LOWPASS"))

        sanitized, corrections = DecentSamplerSanitizer.sanitize(inst)
        assert sanitized.effects[0].type == "lowpass"
        assert len(corrections) > 0

    def test_path_backslash_and_drive_letter_cleaning(self):
        inst = InstrumentModel()
        grp = GroupModel()
        grp.add_sample(SampleZoneModel(path="D:\\Proyectos\\Samples\\piano.wav", root_note=60, lo_note=0, hi_note=127))
        inst.add_group(grp)

        sanitized, corrections = DecentSamplerSanitizer.sanitize(inst)
        path = sanitized.groups[0].samples[0].path
        assert "\\" not in path
        assert not path.startswith("D:")
        assert "Proyectos/Samples/piano.wav" in path

    def test_note_inversion_and_root_clamping(self):
        inst = InstrumentModel()
        grp = GroupModel()
        # Inverted notes: lo=80, hi=40. Root=20 (outside range)
        grp.add_sample(SampleZoneModel(path="s.wav", root_note=20, lo_note=80, hi_note=40))
        inst.add_group(grp)

        sanitized, corrections = DecentSamplerSanitizer.sanitize(inst)
        sample = sanitized.groups[0].samples[0]
        assert sample.lo_note == 40
        assert sample.hi_note == 80
        assert sample.root_note == 40  # Clamped to new lo_note

    def test_envelope_anti_click_floor_enforcement(self):
        inst = InstrumentModel()
        grp = GroupModel(attack=0.0, release=0.001)
        grp.add_sample(SampleZoneModel(path="s.wav", root_note=60, lo_note=0, hi_note=127))
        inst.add_group(grp)

        sanitized, corrections = DecentSamplerSanitizer.sanitize(inst)
        assert sanitized.groups[0].attack == AudioSafetyPolicy.RECOMMENDED_MIN_ATTACK_SEC
        assert sanitized.groups[0].release == AudioSafetyPolicy.RECOMMENDED_MIN_RELEASE_SEC

    def test_migrate_group_reverb_to_global(self):
        inst = InstrumentModel()
        grp = GroupModel()
        grp.add_sample(SampleZoneModel(path="s.wav", root_note=60, lo_note=0, hi_note=127))
        grp.effects.append(EffectModel(type="reverb", parameters={"roomSize": 0.5}))
        inst.add_group(grp)

        assert len(inst.effects) == 0
        assert len(inst.groups[0].effects) == 1

        sanitized, corrections = DecentSamplerSanitizer.sanitize(inst)

        # Reverb should have migrated from group to instrument level
        assert len(sanitized.groups[0].effects) == 0
        assert len(sanitized.effects) == 1
        assert sanitized.effects[0].type == "reverb"
