# tests/test_vital_modular_designer.py
"""
Test Suite for VitalDesignValidator, VitalModularDesigner,
and Granular Sound Design in VitalSoundEngine.
"""

import pytest
import json
from pathlib import Path

from engine.sound_design.vital_design_validator import (
    VitalDesignValidator,
    VitalValidationError,
    ValidationReport
)
from engine.sound_design.vital_modular_designer import VitalModularDesigner
from engine.sound_design.vital_sound_engine import VitalSoundEngine


class TestVitalDesignValidator:
    """Verifies input auditing, diagnostic reporting, and auto-corrections."""

    def test_valid_specification(self):
        spec = {
            "oscillators": {
                "osc_1": {"waveform": "SAW", "octave": 0, "unison": 7, "level": 0.8},
                "osc_2": {"waveform": "FM", "fm_carrier": 1.0, "fm_mod": 3.0, "octave": 1}
            },
            "filter": {
                "model": "DIODE_303",
                "mode": "LOW_PASS",
                "cutoff_hz": 1200.0,
                "resonance": 0.45
            },
            "modulations": [
                {"source": "LFO_1", "destination": "FILTER_CUTOFF", "shape": "STEPPED_RANDOM", "rate": "1/16", "amount": 0.5}
            ],
            "variation": 0.2
        }

        report = VitalDesignValidator.validate_specification(spec, strict=False)
        assert report.is_valid is True
        assert len(report.errors) == 0
        assert report.sanitized_spec["filter"]["model"] == "DIODE_303"
        assert report.sanitized_spec["oscillators"]["osc_1"]["unison"] == 7

    def test_invalid_waveform_autocorrection(self):
        spec = {
            "oscillators": {
                "osc_1": {"waveform": "SUPER_SAW_EXTRA"}  # Invalid name
            }
        }

        report = VitalDesignValidator.validate_specification(spec, strict=False)
        assert report.is_valid is True
        # Should detect unrecognized waveform, emit warning, and auto-correct to valid wave
        assert len(report.warnings) > 0
        assert report.sanitized_spec["oscillators"]["osc_1"]["waveform"] in VitalDesignValidator.VALID_WAVEFORMS

    def test_subsonic_cutoff_protection(self):
        spec = {
            "filter": {
                "cutoff_hz": 6.5  # Dangerous 6.5 Hz infrasonic cutoff
            }
        }

        report = VitalDesignValidator.validate_specification(spec, strict=False)
        assert report.is_valid is True
        # Must be clamped to safe audible frequency
        assert report.sanitized_spec["filter"]["cutoff_hz"] >= 45.0
        assert any("subsonic" in w.lower() for w in report.warnings)

    def test_high_resonance_protection(self):
        spec = {
            "filter": {
                "resonance": 0.98  # Ear-damaging howl risk
            }
        }

        report = VitalDesignValidator.validate_specification(spec, strict=False)
        assert report.is_valid is True
        assert report.sanitized_spec["filter"]["resonance"] <= 0.65
        assert any("howl" in w.lower() or "dangerously high" in w.lower() for w in report.warnings)

    def test_strict_mode_raises_exception(self):
        spec = "This is not a dict"  # Fatal error

        with pytest.raises(VitalValidationError) as exc_info:
            VitalDesignValidator.validate_specification(spec, strict=True)

        assert "must be a dictionary" in str(exc_info.value)


class TestVitalModularDesigner:
    """Verifies synthesis of granular components into physical Vital settings."""

    @pytest.fixture
    def engine(self):
        return VitalSoundEngine()

    def test_filter_models_materialization(self, engine, tmp_path):
        # 1. DIODE_303
        out_diode, rep1 = engine.design_granular_preset(
            preset_name="Acid_Diode_303",
            spec={
                "filter": {"model": "DIODE_303", "cutoff_hz": 800, "resonance": 0.50}
            },
            output_dir=tmp_path
        )
        data_diode = json.loads(out_diode.read_text(encoding="utf-8"))
        assert data_diode["settings"]["filter_1_model"] == 4.0  # Diode model in Vital

        # 2. COMB Filter
        out_comb, rep2 = engine.design_granular_preset(
            preset_name="Neuro_Comb_Bass",
            spec={
                "filter": {"model": "COMB", "cutoff_hz": 1200}
            },
            output_dir=tmp_path
        )
        data_comb = json.loads(out_comb.read_text(encoding="utf-8"))
        assert data_comb["settings"]["filter_1_model"] == 6.0  # Comb model in Vital

        # 3. DIRTY Filter
        out_dirty, rep3 = engine.design_granular_preset(
            preset_name="Dirty_Ladder_Lead",
            spec={
                "filter": {"model": "DIRTY", "cutoff_hz": 2000}
            },
            output_dir=tmp_path
        )
        data_dirty = json.loads(out_dirty.read_text(encoding="utf-8"))
        assert data_dirty["settings"]["filter_1_model"] == 1.0  # Dirty model in Vital

    def test_lfo_stepped_random_modulation(self, engine, tmp_path):
        out_lfo, _ = engine.design_granular_preset(
            preset_name="Sample_And_Hold_Pluck",
            spec={
                "modulations": [
                    {
                        "source": "LFO_1",
                        "destination": "FILTER_CUTOFF",
                        "shape": "STEPPED_RANDOM",
                        "rate": "1/16",
                        "amount": 0.65
                    }
                ]
            },
            output_dir=tmp_path
        )

        data = json.loads(out_lfo.read_text(encoding="utf-8"))
        s = data["settings"]
        lfo0 = s["lfos"][0]
        assert lfo0["name"] == "Sample & Hold"
        assert lfo0["num_points"] == 16
        assert s["lfo_1_tempo"] == 11.0  # 1/16 rate
        assert s["modulation_1_amount"] == 0.65

    def test_custom_waveform_stacking(self, engine, tmp_path):
        out_custom, _ = engine.design_granular_preset(
            preset_name="Vocal_FM_Hybrid",
            spec={
                "oscillators": {
                    "osc_1": {"waveform": "VOCAL_FORMANT_O", "octave": -1, "unison": 7},
                    "osc_2": {"waveform": "FM", "fm_carrier": 1.0, "fm_mod": 3.5, "octave": 1},
                    "osc_3": {"waveform": "ANALOG_WARM", "octave": 0}
                }
            },
            output_dir=tmp_path
        )

        data = json.loads(out_custom.read_text(encoding="utf-8"))
        s = data["settings"]
        wts = s["wavetables"]
        assert len(wts) >= 3
        assert "Vocal Formant O" in wts[0]["name"]
        assert "FM 1.0:3.5" in wts[1]["name"]
        assert "Analog Chebyshev" in wts[2]["name"]
        assert s["osc_1_transpose"] == -12.0
        assert s["osc_2_transpose"] == 12.0


class TestOrganicVariationEngine:
    """Verifies that stochastic variation generates unique presets from identical prompts."""

    def test_stochastic_variation_diversity(self, tmp_path):
        engine = VitalSoundEngine()
        spec = {
            "oscillators": {
                "osc_1": {"waveform": "SAW", "unison": 7, "detune_cents": 0.0}
            },
            "filter": {
                "model": "DIODE_303",
                "cutoff_hz": 1500.0
            },
            "variation": 0.50  # 50% analog variation
        }

        # Generate 3 takes with different seeds
        out1, _ = engine.design_granular_preset("Take_1", spec, output_dir=tmp_path)
        out2, _ = engine.design_granular_preset("Take_2", spec, output_dir=tmp_path)
        out3, _ = engine.design_granular_preset("Take_3", spec, output_dir=tmp_path)

        data1 = json.loads(out1.read_text(encoding="utf-8"))["settings"]
        data2 = json.loads(out2.read_text(encoding="utf-8"))["settings"]
        data3 = json.loads(out3.read_text(encoding="utf-8"))["settings"]

        # Cutoff and detune should exhibit micro-drift between takes
        cutoffs = {data1["filter_1_cutoff"], data2["filter_1_cutoff"], data3["filter_1_cutoff"]}
        tunes = {data1["osc_1_tune"], data2["osc_1_tune"], data3["osc_1_tune"]}

        # Must have variation (not all identical)
        assert len(cutoffs) > 1
        assert len(tunes) > 1

        # All takes must be valid and audible
        for out_file in (out1, out2, out3):
            audit = engine.audit_preset_file(out_file)
            assert audit["valid"] is True
            assert audit["audible"] is True


class TestCreativeFreedomAndPermissiveSafety:
    """
    Verifies that the engine acts as a universal sound synthesizer,
    permitting any audible, physically valid sound without artistic censorship.
    """

    @pytest.fixture
    def engine(self):
        return VitalSoundEngine()

    def test_sub_bass_permissive_low_cutoff(self, engine, tmp_path):
        """Deep sub-bass cutoffs (25-35 Hz) must NOT be clamped up to 73 Hz."""
        out_sub, rep = engine.design_granular_preset(
            preset_name="Permissive_Deep_Sub",
            spec={
                "oscillators": {
                    "osc_1": {"waveform": "SINE", "octave": -2, "level": 0.9}
                },
                "filter": {
                    "model": "ANALOG_24",
                    "mode": "LOW_PASS",
                    "cutoff_hz": 32.7  # C1 fundamental (approx 24 MIDI note)
                }
            },
            role_archetype="BASS_SUB",
            output_dir=tmp_path
        )
        assert rep["is_valid"] is True
        data = json.loads(out_sub.read_text(encoding="utf-8"))["settings"]

        # Cutoff must reflect the deep sub range (around 24.0), not forced to 38.0
        assert 22.0 <= data["filter_1_cutoff"] <= 26.0
        audit = engine.audit_preset_file(out_sub)
        assert audit["audible"] is True

    def test_snappy_percussive_transient_click(self, engine, tmp_path):
        """Fast 35ms percussive clicks with 0 sustain must NOT be inflated to 250ms."""
        out_click, rep = engine.design_granular_preset(
            preset_name="Snappy_Click_Transient",
            spec={
                "oscillators": {
                    "osc_1": {"waveform": "SAW", "level": 0.8}
                },
                "envelopes": {
                    "attack": 0.001,
                    "decay": 0.035,  # 35ms sharp click
                    "sustain": 0.0,
                    "release": 0.02
                }
            },
            output_dir=tmp_path
        )
        assert rep["is_valid"] is True
        data = json.loads(out_click.read_text(encoding="utf-8"))["settings"]

        # Snappy decay must be preserved
        assert data["env_1_decay"] == pytest.approx(0.035, abs=0.002)
        assert data["env_1_sustain"] == 0.0
        audit = engine.audit_preset_file(out_click)
        assert audit["audible"] is True

    def test_expansive_ambient_pad_with_sampler(self, engine, tmp_path):
        """Ambient pad with 3.5s attack, lush reverb, and vinyl sampler texture."""
        out_pad, rep = engine.design_granular_preset(
            preset_name="Ambient_Cosmic_Pad",
            spec={
                "oscillators": {
                    "osc_1": {"waveform": "ANALOG_WARM", "unison": 7, "level": 0.7},
                    "osc_2": {"waveform": "SINE", "octave": 1, "level": 0.5}
                },
                "envelopes": {
                    "attack": 3.5,
                    "decay": 5.0,
                    "sustain": 0.85,
                    "release": 4.0
                },
                "sampler": {
                    "on": True,
                    "sample_type": "VINYL",
                    "level": 0.22,
                    "loop": True
                },
                "effects": {
                    "reverb": {"on": True, "mix": 0.65},
                    "delay": {"on": True, "mix": 0.30, "feedback": 0.5}
                }
            },
            output_dir=tmp_path
        )
        assert rep["is_valid"] is True
        data = json.loads(out_pad.read_text(encoding="utf-8"))["settings"]

        assert data["env_1_attack"] == pytest.approx(3.5, abs=0.01)
        assert data["sample_on"] == 1.0
        assert data["sample_level"] == pytest.approx(0.22, abs=0.01)
        assert data["reverb_dry_wet"] == pytest.approx(0.65, abs=0.01)
        assert data["delay_on"] == 1.0
        audit = engine.audit_preset_file(out_pad)
        assert audit["audible"] is True

    def test_high_pass_permissive_and_safe(self, engine, tmp_path):
        """High-Pass filter permits wide open cutoffs and protects against ultrasonic wipeout."""
        # 1. Wide open High-Pass (35 Hz cutoff = passes everything above 35 Hz)
        out_hp, rep = engine.design_granular_preset(
            preset_name="Permissive_High_Pass",
            spec={
                "filter": {
                    "model": "ANALOG_12",
                    "mode": "HIGH_PASS",
                    "cutoff_hz": 35.0
                }
            },
            output_dir=tmp_path
        )
        data = json.loads(out_hp.read_text(encoding="utf-8"))["settings"]
        assert data["filter_1_blend"] == 2.0  # High pass mode
        assert 22.0 <= data["filter_1_cutoff"] <= 28.0

        # 2. Ultrasonic High-Pass protection
        out_hp_ultra, _ = engine.design_granular_preset(
            preset_name="Protected_Ultra_High_Pass",
            spec={
                "filter": {
                    "model": "ANALOG_12",
                    "mode": "HIGH_PASS",
                    "cutoff_hz": 18000.0  # Ultrasonic
                }
            },
            output_dir=tmp_path
        )
        data_ultra = json.loads(out_hp_ultra.read_text(encoding="utf-8"))["settings"]
        # Must be clamped to safe max to prevent wiping out musical fundamentals
        assert data_ultra["filter_1_cutoff"] <= 118.0

    def test_metallic_bell_inharmonic_synthesis(self, engine, tmp_path):
        """Verifies algorithmic synthesis of metallic inharmonic bell waveforms."""
        out_bell, rep = engine.design_granular_preset(
            preset_name="Metallic_Gong_Bell",
            spec={
                "oscillators": {
                    "osc_1": {"waveform": "METALLIC", "level": 0.8}
                },
                "filter": {
                    "model": "COMB",
                    "cutoff_hz": 1800.0,
                    "resonance": 0.60
                }
            },
            output_dir=tmp_path
        )
        data = json.loads(out_bell.read_text(encoding="utf-8"))["settings"]
        assert data["filter_1_model"] == 6.0  # Comb model
        wt_name = data["wavetables"][0]["name"]
        assert "Metallic" in wt_name
