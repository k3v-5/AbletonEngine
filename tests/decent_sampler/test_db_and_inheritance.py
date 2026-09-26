# tests/decent_sampler/test_db_and_inheritance.py
"""Tests for decibels conversion, tolerant XML parsing, and <groups> inheritance."""

import pytest
from engine.sound_design.decent_sampler import (
    DecentSamplerSchema,
    DSPresetSerializer,
    InstrumentModel,
    GroupModel,
    SampleZoneModel,
    DecentSamplerValidator,
)


def test_db_conversion_math():
    """Verifies logarithmic and linear decibel conversion accuracy."""
    assert DecentSamplerSchema.db_to_gain(0.0) == 1.0
    assert abs(DecentSamplerSchema.db_to_gain(6.0) - 1.995262) < 0.001
    assert abs(DecentSamplerSchema.db_to_gain(-6.0) - 0.501187) < 0.001
    assert abs(DecentSamplerSchema.db_to_gain(2.0) - 1.258925) < 0.001

    assert DecentSamplerSchema.gain_to_db(1.0) == 0.0
    assert abs(DecentSamplerSchema.gain_to_db(2.0) - 6.02) < 0.05
    assert abs(DecentSamplerSchema.gain_to_db(0.5) - (-6.02)) < 0.05


def test_parse_volume_string_formats():
    """Verifies robust parsing of strings, integers, floats, dB suffixes, and noisy inputs."""
    assert DecentSamplerSchema.parse_volume_string(1.0) == 1.0
    assert DecentSamplerSchema.parse_volume_string("0dB") == 1.0
    assert abs(DecentSamplerSchema.parse_volume_string("2dB") - 1.2589) < 0.01
    assert abs(DecentSamplerSchema.parse_volume_string("-6dB") - 0.5012) < 0.01
    # Corrupted string from real files
    assert abs(DecentSamplerSchema.parse_volume_string("3\n  aadB") - 1.4125) < 0.01
    assert DecentSamplerSchema.parse_volume_string(None) == 1.0
    assert DecentSamplerSchema.parse_volume_string("invalid") == 1.0


def test_groups_envelope_inheritance_in_deserialize():
    """Verifies that child <group> tags inherit attack, decay, release, and volume from parent <groups>."""
    xml_data = """<DecentSampler minVersion="1.0.0">
  <groups attack="0.45" decay="3.5" sustain="0.8" release="2.1" volume="2dB">
    <group name="Inherited Group">
      <sample path="Samples/test.wav" rootNote="60" loNote="0" hiNote="127" />
    </group>
    <group name="Overridden Group" attack="0.01" release="0.5" volume="-6dB">
      <sample path="Samples/test2.wav" rootNote="60" loNote="0" hiNote="127" />
    </group>
  </groups>
</DecentSampler>"""

    model = DSPresetSerializer.deserialize(xml_data)
    assert len(model.groups) == 2

    # Group 1: Inherited
    g1 = model.groups[0]
    assert g1.attack == 0.45
    assert g1.decay == 3.5
    assert g1.sustain == 0.8
    assert g1.release == 2.1
    assert abs(g1.volume - 1.2589) < 0.01

    # Group 2: Overridden
    g2 = model.groups[1]
    assert g2.attack == 0.01
    assert g2.decay == 3.5  # Inherited decay
    assert g2.release == 0.5
    assert abs(g2.volume - 0.5012) < 0.01


def test_tolerant_xml_attribute_deduplication():
    """Verifies that duplicate attributes in a tag (like JUCE) overwrite gracefully without crashing."""
    corrupt_xml = """<DecentSampler minVersion="1.0.0">
  <ui width="812" height="375">
    <tab>
      <labeled-knob x="650" y="128" textColor="FFF9F9F9" label="Reverb" textColor="FFD1D1D1" value="0">
        <binding type="amp" level="instrument" position="0" parameter="AMP_VOLUME" />
      </labeled-knob>
    </tab>
  </ui>
  <groups>
    <group>
      <sample path="Samples/test.wav" rootNote="60" loNote="0" hiNote="127" />
    </group>
  </groups>
</DecentSampler>"""

    # Strict parser without tolerance would throw ET.ParseError: duplicate attribute
    # Tolerant validator cleans it and records warning
    report = DecentSamplerValidator.validate_xml(corrupt_xml, strict=False, lenient=True)
    assert report.is_valid is True
    assert any("Deduplicated attribute 'textColor'" in c for c in report.corrections)

    # Deserializer should also succeed and take the last value
    model = DSPresetSerializer.deserialize(corrupt_xml, tolerant=True)
    assert len(model.ui.controls) == 1
    assert model.ui.controls[0].text_color == "FFD1D1D1"
