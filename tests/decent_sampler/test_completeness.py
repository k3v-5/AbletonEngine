# tests/decent_sampler/test_completeness.py
"""Tests for InstrumentCompletenessAuditor, auto-completion, and definition of done."""

import pytest
from engine.sound_design.decent_sampler import (
    DecentSamplerBuilder,
    InstrumentModel,
    GroupModel,
    SampleZoneModel,
    EffectModel,
    ControlModel,
    BindingModel,
    InstrumentCompletenessAuditor,
    DecentSamplerSanitizer,
)


def test_orphaned_effect_detection():
    """Verifies that an effect added without a UI control is flagged as an omission."""
    builder = DecentSamplerBuilder("Test Instrument")
    builder.add_sample("Samples/test.wav", root_note=60, lo_note=0, hi_note=127)
    builder.add_effect("lowpass", frequency=1000.0)

    # Before auto-completion: Lowpass is orphaned
    report = InstrumentCompletenessAuditor.audit(builder.instrument)
    assert any("lowpass" in desc and "no UI control" in desc for desc in report.warnings)


def test_auto_complete_orphaned_effects():
    """Verifies that sanitize(auto_complete=True) synthesizes a 7-point log filter knob for orphaned lowpass."""
    builder = DecentSamplerBuilder("Test Instrument")
    builder.add_sample("Samples/test.wav", root_note=60, lo_note=0, hi_note=127)
    builder.add_effect("lowpass", frequency=1000.0)

    # Auto-complete
    report = builder.ensure_production_ready(auto_complete=True)
    assert report.is_production_ready is True
    assert any("Auto-completed UI knob 'Cutoff'" in fix for fix in report.auto_fixes_applied)

    # Check that a control with the 7-point log table was actually created
    controls = builder.instrument.ui.controls
    assert len(controls) == 1
    cutoff_ctrl = controls[0]
    assert cutoff_ctrl.label == "Cutoff"
    assert cutoff_ctrl.bindings[0].translation == "table"
    assert "0,33;0.3,150" in cutoff_ctrl.bindings[0].translation_table


def test_anti_click_envelope_audit():
    """Verifies that 0.0s attack or 0.0s release are flagged as acoustic click risks."""
    builder = DecentSamplerBuilder("Test Instrument")
    builder.add_sample("Samples/test.wav", root_note=60, lo_note=0, hi_note=127)
    builder.set_envelope(attack=0.0, release=0.0)

    report = InstrumentCompletenessAuditor.audit(builder.instrument)
    assert report.is_production_ready is False
    assert any("below 1ms anti-click threshold" in err for err in report.errors)
    assert any("Release time is 0.0s" in err for err in report.errors)

    # Auto-fix ensures production ready
    fixed_report = builder.ensure_production_ready(auto_complete=True)
    assert fixed_report.is_production_ready is True
    assert builder.instrument.groups[0].attack >= 0.001
    assert builder.instrument.groups[0].release >= 0.005


def test_silent_keyboard_gap_detection():
    """Verifies that unmapped holes in the keyboard are detected."""
    builder = DecentSamplerBuilder("Test Instrument")
    # Zone 1: 0..40, Zone 2: 60..127 -> Gap at 41..59
    builder.add_sample("Samples/low.wav", root_note=36, lo_note=0, hi_note=40)
    builder.add_sample("Samples/high.wav", root_note=72, lo_note=60, hi_note=127)

    report = InstrumentCompletenessAuditor.audit(builder.instrument)
    assert report.is_production_ready is False
    assert any("unmapped silent notes" in err for err in report.errors)


def test_gain_staging_headroom_normalization():
    """Verifies that simultaneous layers with excessive gain are scaled to prevent DAW clipping."""
    builder = DecentSamplerBuilder("Layered Beast")
    # 3 simultaneous groups with 1.0 volume each -> Total gain 3.0x (+9.5 dB)
    builder.instrument.groups.clear()
    for i in range(3):
        grp = GroupModel(name=f"Layer {i}", volume=1.0, seq_mode="always")
        grp.add_sample(SampleZoneModel(path=f"Samples/{i}.wav", root_note=60, lo_note=0, hi_note=127))
        builder.instrument.add_group(grp)

    # Audit flags risk
    raw_report = InstrumentCompletenessAuditor.audit(builder.instrument)
    assert any("exceeds safe headroom" in w for w in raw_report.warnings)

    # Sanitizer normalizes headroom
    _, fixes = DecentSamplerSanitizer.sanitize(builder.instrument, normalize_headroom=True)
    assert any("Normalized simultaneous group gains" in f for f in fixes)
    total_gain = sum(g.volume for g in builder.instrument.groups)
    assert total_gain <= 1.05
