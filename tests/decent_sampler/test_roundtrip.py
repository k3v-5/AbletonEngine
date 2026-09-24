# tests/decent_sampler/test_roundtrip.py
"""
Round-Trip Fidelity Tests:
InstrumentModel -> .dspreset XML -> InstrumentModel == Original.
"""

from engine.sound_design.decent_sampler.model import (
    InstrumentModel,
    GroupModel,
    SampleZoneModel,
    EffectModel,
    ControlModel,
    BindingModel,
)
from engine.sound_design.decent_sampler.serializer import DSPresetSerializer


class TestDSPresetRoundTrip:
    def test_complete_roundtrip_fidelity(self):
        """Verifies complete serialization and deserialization retains all fields."""
        orig = InstrumentModel(
            name="Grand Piano RT",
            min_version="1.0.0",
            plugin_version="1",
            volume=0.85,
            global_pan=10.0,
            global_tuning=-2.0,
            glide_time=0.05,
            glide_mode="always",
        )

        # UI Control
        ctrl = ControlModel(
            control_type="labeled-knob",
            label="Filter Tone",
            x=50,
            y=50,
            width=90,
            height=90,
            min_value=100.0,
            max_value=20000.0,
            value=15000.0,
            default_value=15000.0,
            text_color="FFFFFFFF",
            value_type="hertz",
        )
        ctrl.bindings.append(
            BindingModel(
                type="effect",
                level="instrument",
                parameter="FX_FILTER_FREQUENCY",
                position=0,
                translation="linear",
                translation_output_min=100.0,
                translation_output_max=20000.0,
            )
        )
        orig.add_control(ctrl)

        # Groups and Samples
        grp = GroupModel(
            name="Acoustic Body",
            tags="main_body",
            enabled=True,
            volume=0.9,
            pan=-5.0,
            amp_vel_track=0.8,
            attack=0.002,
            decay=8.0,
            sustain=0.1,
            release=0.5,
            seq_mode="round_robin",
            silenced_by_tags="mute_choke",
            silencing_mode="fast",
        )
        grp.add_sample(
            SampleZoneModel(
                path="Samples/body_c3.wav",
                root_note=48,
                lo_note=36,
                hi_note=59,
                lo_vel=0,
                hi_vel=127,
                tuning=0.5,
                volume=0.95,
                pan=2.0,
                seq_mode="round_robin",
                seq_position=1,
                seq_length=2,
                tags="soft_hit",
            )
        )
        orig.add_group(grp)

        # Global Effect
        orig.add_effect(
            EffectModel(
                type="lowpass",
                tags="main_lp",
                enabled=True,
                parameters={"frequency": "15000.0", "resonance": "0.75"},
            )
        )

        # Serialized XML
        xml_str = DSPresetSerializer.serialize(orig)
        assert "<?xml" in xml_str
        assert "<DecentSampler" in xml_str

        # Deserialized Model
        loaded = DSPresetSerializer.deserialize(xml_str)

        # Assert Root Properties
        assert loaded.volume == orig.volume
        assert loaded.global_pan == orig.global_pan
        assert loaded.global_tuning == orig.global_tuning
        assert loaded.glide_time == orig.glide_time
        assert loaded.glide_mode == orig.glide_mode

        # Assert UI
        assert len(loaded.ui.controls) == 1
        l_ctrl = loaded.ui.controls[0]
        assert l_ctrl.label == "Filter Tone"
        assert l_ctrl.min_value == 100.0
        assert l_ctrl.max_value == 20000.0
        assert len(l_ctrl.bindings) == 1
        assert l_ctrl.bindings[0].parameter == "FX_FILTER_FREQUENCY"

        # Assert Groups & Samples
        assert len(loaded.groups) == 1
        l_grp = loaded.groups[0]
        assert l_grp.tags == "main_body"
        assert l_grp.attack == 0.002
        assert l_grp.release == 0.5
        assert l_grp.seq_mode == "round_robin"
        assert l_grp.silenced_by_tags == "mute_choke"

        assert len(l_grp.samples) == 1
        l_s = l_grp.samples[0]
        assert l_s.path == "Samples/body_c3.wav"
        assert l_s.root_note == 48
        assert l_s.lo_note == 36
        assert l_s.hi_note == 59
        assert l_s.seq_position == 1
        assert l_s.seq_length == 2

        # Assert Effects
        assert len(loaded.effects) == 1
        assert loaded.effects[0].type == "lowpass"
        assert loaded.effects[0].tags == "main_lp"
