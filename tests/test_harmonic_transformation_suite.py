# tests/test_harmonic_transformation_suite.py
"""
Test Suite for Universal Harmonic Transformation Suite (UHTS):
Validates that ANY instrument or plugin can initiate a sound and be transformed
into rich harmonic overtones, non-linear wavefolding, formant resonance, and OTT dynamics.
"""

import os
from pathlib import Path
import pytest

from engine.sound_design.harmonic_transformation_suite import (
    HarmonicTransformationSuite,
    HarmonicProfile,
    HarmonicSuiteConfig,
)
from engine.sound_design.technique_catalog import TechniqueCatalog, ProductionTechniqueFamily
from engine.composition.compositional_dna import (
    CompositionalDNA,
    PrimaryMotif,
    MotifNote,
    HarmonicPalette,
)


@pytest.fixture
def mock_dna():
    return CompositionalDNA(
        song_id="uhts_song",
        title="Harmonic Suite Project",
        bpm=100.0,
        primary_motif=PrimaryMotif(
            name="Dark Lead FM",
            notes=[
                MotifNote(pitch=65, start_time=0.0, duration=1.0),  # F
                MotifNote(pitch=66, start_time=1.0, duration=1.0),  # Gb
                MotifNote(pitch=68, start_time=2.0, duration=1.0),  # Ab
                MotifNote(pitch=72, start_time=3.0, duration=1.0),  # C
            ]
        ),
        harmonic_palette=HarmonicPalette(
            key_root="F",
            scale="phrygian"
        )
    )


def test_all_six_profiles_have_valid_configs():
    for profile in HarmonicProfile:
        cfg = HarmonicTransformationSuite.get_config(profile)
        assert isinstance(cfg, HarmonicSuiteConfig)
        assert cfg.drive_db >= 0.0
        assert 300.0 <= cfg.formant_freq_hz <= 4000.0
        assert 0.0 <= cfg.ott_depth <= 1.0
        assert cfg.hpf_cutoff_hz >= 20.0
        assert 0.0 <= cfg.space_wet <= 1.0
        assert 0.0 <= cfg.stereo_spread <= 1.0


def test_sub_safe_bass_protects_low_end_and_enforces_mono():
    cfg = HarmonicTransformationSuite.get_config(HarmonicProfile.SUB_SAFE_BASS, source_instrument_type="sublab")
    assert cfg.hpf_cutoff_hz <= 40.0
    assert cfg.stereo_spread == 0.0  # Mono protection
    assert cfg.space_wet == 0.0      # Zero reverb wash on sub

    chain = HarmonicTransformationSuite.build_device_chain(HarmonicProfile.SUB_SAFE_BASS, source_instrument_type="sublab")
    device_names = [d.device_name for d in chain]
    assert "Saturator" in device_names
    assert "Utility" in device_names


def test_pad_atmosphere_chain_contains_complete_hrp_suite():
    chain = HarmonicTransformationSuite.build_device_chain(
        HarmonicProfile.PAD_ATMOSPHERE,
        source_instrument_type="pigments",
        prefer_vst=True
    )
    device_names = [d.device_name for d in chain]
    assert "EQ Eight" in device_names
    assert "Saturator" in device_names
    assert "Auto Filter" in device_names
    assert "Multiband Dynamics" in device_names
    assert "Utility" in device_names
    assert any("Verb" in d or "Reverb" in d for d in device_names)


def test_technique_catalog_registers_uhts():
    tech = TechniqueCatalog.get_technique("UNIVERSAL_HARMONIC_TRANSFORMATION_SUITE")
    assert tech is not None
    assert tech.family == ProductionTechniqueFamily.SPECTRAL_DESIGN
    assert len(tech.recipes) >= 5
    recipe_names = [r.device_name for r in tech.recipes]
    assert "Saturator" in recipe_names
    assert "EQ Eight" in recipe_names
    assert "Multiband Dynamics" in recipe_names


def test_transform_source_to_layer_offline_pipeline(mock_dna, tmp_path):
    # Test that any plugin / instrument can initiate a phrase and be transformed
    res = HarmonicTransformationSuite.transform_source_to_layer(
        source_track_index=6,
        target_role="TEXTURE_FOLEY",
        song_dna=mock_dna,
        profile=HarmonicProfile.PAD_ATMOSPHERE,
        source_instrument_name="Arturia Pigments",
        conn=None
    )

    assert res["status"] == "SUCCESS"
    assert res["source_track_index"] == 6
    assert res["source_instrument"] == "Arturia Pigments"
    assert res["profile"] == HarmonicProfile.PAD_ATMOSPHERE.value
    assert Path(res["audio_path"]).exists()
    assert os.path.getsize(res["audio_path"]) > 1000
    assert "mut_b_" in res["transformed_sample_id"]
