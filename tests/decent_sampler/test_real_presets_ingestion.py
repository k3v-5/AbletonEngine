# tests/decent_sampler/test_real_presets_ingestion.py
"""Tests for ingesting real third-party presets from SonidosDecentSampler."""

import pytest
from pathlib import Path
from engine.sound_design.decent_sampler import (
    DSPresetSerializer,
    DecentSamplerValidator,
    InstrumentCompletenessAuditor,
)

PRESETS_DIR = Path(__file__).resolve().parents[2] / "SonidosDecentSampler"


@pytest.mark.skipif(not PRESETS_DIR.exists(), reason="SonidosDecentSampler directory not present")
def test_ingest_all_real_presets():
    """Verifies that all third-party presets in SonidosDecentSampler can be ingested 100% cleanly."""
    preset_files = list(PRESETS_DIR.glob("**/*.dspreset"))
    assert len(preset_files) >= 3, f"Expected at least 3 presets, found {len(preset_files)}"

    for preset_path in preset_files:
        raw_xml = preset_path.read_text(encoding="utf-8")

        # 1. Tolerant XML validation passes
        report = DecentSamplerValidator.validate_xml(raw_xml, strict=False, lenient=True)
        assert report.is_valid is True, f"Failed XML validation for {preset_path.name}: {report.all_errors}"

        # 2. Deserialization into InstrumentModel passes
        model = DSPresetSerializer.deserialize(raw_xml, tolerant=True)
        assert model is not None
        assert model.total_samples() > 0, f"No samples found in {preset_path.name}"
        assert len(model.groups) >= 1

        # 3. Model validation passes
        model_report = DecentSamplerValidator.validate_model(model, strict=False)
        assert model_report.is_valid is True, f"Failed model validation for {preset_path.name}: {model_report.all_errors}"


@pytest.mark.skipif(not PRESETS_DIR.exists(), reason="SonidosDecentSampler directory not present")
def test_ingest_acoustic_guitar_specifics():
    """Checks details of DR Acoustic Guitar DS v1."""
    guitar_path = next(PRESETS_DIR.glob("**/DR Acoustic Guitar DS v1.dspreset"))
    model = DSPresetSerializer.deserialize(guitar_path.read_text(encoding="utf-8"))

    # 3 round-robin groups, 17 samples each (51 total)
    assert len(model.groups) == 3
    assert model.total_samples() == 51
    assert all(g.seq_mode == "round_robin" for g in model.groups)
    assert model.groups[0].attack == 0.03
    assert model.groups[0].release == 1.96


@pytest.mark.skipif(not PRESETS_DIR.exists(), reason="SonidosDecentSampler directory not present")
def test_ingest_godly_pad_specifics():
    """Checks details of DR Godly Pad v1."""
    pad_path = next(PRESETS_DIR.glob("**/DR Godly Pad v1.dspreset"))
    model = DSPresetSerializer.deserialize(pad_path.read_text(encoding="utf-8"))

    # 2 simultaneous layers (DRY1 + VERB1), 25 samples each (50 total)
    assert len(model.groups) == 2
    assert model.total_samples() == 50
    assert model.groups[0].seq_mode == "always"
    assert model.groups[1].seq_mode == "always"
    assert model.groups[0].attack == 0.42
    assert model.groups[0].release == 1.7
