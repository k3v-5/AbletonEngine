# tests/decent_sampler/test_dual_layer_pad.py
"""Tests for the dual-layer atmospheric pad template."""

import pytest
from engine.sound_design.decent_sampler.templates import create_dual_layer_pad
from engine.sound_design.decent_sampler import (
    DecentSamplerValidator,
    InstrumentCompletenessAuditor,
    DSPresetSerializer,
)


def test_create_dual_layer_pad_template():
    """Verifies that create_dual_layer_pad compiles a production-ready preset."""
    builder = create_dual_layer_pad(name="Test Ambient Pad")

    # Audit production readiness
    report = builder.ensure_production_ready(auto_complete=True)
    assert report.is_production_ready is True
    assert len(report.missing_configurations) == 0

    # Verify model structure
    model = builder.instrument
    assert len(model.groups) == 2
    assert model.groups[0].name == "Dry Layer"
    assert model.groups[1].name == "Shimmer Layer"
    assert model.groups[0].seq_mode == "always"
    assert model.groups[1].seq_mode == "always"

    # Verify effects and controls
    assert len(model.effects) == 2
    assert model.effects[0].type == "lowpass"
    assert model.effects[1].type == "reverb"

    # Verify Cutoff knob uses the 7-point logarithmic table
    cutoff_knob = next(c for c in model.ui.controls if c.label == "Lowpass")
    assert cutoff_knob.bindings[0].translation == "table"
    assert "0,33;0.3,150" in cutoff_knob.bindings[0].translation_table

    # Verify XML compilation and round-trip
    xml_str = builder.compile(strict=True)
    assert "<DecentSampler" in xml_str
    assert 'label="Shimmer"' in xml_str

    # Round trip deserialize
    re_model = DSPresetSerializer.deserialize(xml_str)
    assert len(re_model.groups) == 2
    assert re_model.total_samples() == 10
