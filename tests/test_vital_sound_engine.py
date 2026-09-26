# tests/test_vital_sound_engine.py
"""
Test Suite for VitalSoundEngine, WavetableSynthesizer, ArchetypeCatalog,
VitalSoundSculptor, and VitalParameterSchema.
"""

import pytest
import struct
import base64
import json
from pathlib import Path

from engine.sound_design.vital_parameter_schema import VitalParameterSchema
from engine.sound_design.vital_wavetable_synth import WavetableSynthesizer, POINTS_PER_CYCLE
from engine.sound_design.vital_archetype_catalog import ArchetypeCatalog
from engine.sound_design.vital_sound_sculptor import VitalSoundSculptor
from engine.sound_design.vital_sound_engine import VitalSoundEngine


class TestWavetableSynthesizer:
    """Verifies mathematical cycle synthesis and Base64 packing."""

    def test_sine_generation(self):
        b64 = WavetableSynthesizer.generate_sine()
        raw = base64.b64decode(b64)
        assert len(raw) == POINTS_PER_CYCLE * 4  # 8192 bytes
        floats = struct.unpack(f"<{POINTS_PER_CYCLE}f", raw)
        assert len(floats) == 2048
        assert min(floats) >= -1.01
        assert max(floats) <= 1.01
        # Sine at index 0 should be ~0.0, at index 512 (pi/2) should be ~1.0
        assert abs(floats[0]) < 0.05
        assert floats[512] > 0.90

    def test_saw_and_triangle(self):
        for gen_fn in [WavetableSynthesizer.generate_saw, WavetableSynthesizer.generate_triangle]:
            b64 = gen_fn()
            raw = base64.b64decode(b64)
            assert len(raw) == 8192
            floats = struct.unpack(f"<{POINTS_PER_CYCLE}f", raw)
            assert min(floats) >= -1.01
            assert max(floats) <= 1.01

    def test_fm_synthesis(self):
        b64 = WavetableSynthesizer.generate_fm(carrier_ratio=1.0, mod_ratio=2.0, index=2.5)
        raw = base64.b64decode(b64)
        floats = struct.unpack(f"<{POINTS_PER_CYCLE}f", raw)
        assert len(floats) == 2048
        assert min(floats) >= -1.01
        assert max(floats) <= 1.01

    def test_formant_vowels(self):
        for v in ["A", "E", "I", "O", "U"]:
            b64 = WavetableSynthesizer.generate_formant_vocal(v)
            raw = base64.b64decode(b64)
            assert len(raw) == 8192

    def test_chebyshev_saturation(self):
        b64 = WavetableSynthesizer.generate_chebyshev_warmth(order=3, drive=0.8)
        raw = base64.b64decode(b64)
        assert len(raw) == 8192

    def test_morphing_wavetable_structure(self):
        wt = WavetableSynthesizer.build_morphing_wavetable("FM")
        assert wt["name"] == "Algorithmic FM Spectrum"
        assert wt["version"] in ("1.0.7", "0.8.6")
        kfs = wt["groups"][0]["components"][0]["keyframes"]
        assert len(kfs) == 5
        assert kfs[0]["position"] == 0
        assert kfs[-1]["position"] == 256

    def test_sampler_pcm_generation(self):
        sampler_buf = WavetableSynthesizer.generate_sampler_buffer("TRANSIENT_CLICK", duration_sec=0.5, sample_rate=44100)
        assert sampler_buf["sample_rate"] == 44100
        assert sampler_buf["length"] == 22050
        raw = base64.b64decode(sampler_buf["samples"])
        assert len(raw) == 22050 * 2  # 16-bit mono = 2 bytes per sample


class TestVitalParameterSchema:
    """Verifies parameter clamping and acoustic invariants."""

    def test_volume_clamp(self):
        assert VitalParameterSchema.clamp_parameter("volume", 0.8) == VitalParameterSchema.VOLUME_MIN
        assert VitalParameterSchema.clamp_parameter("volume", 5400.0) == 5400.0
        assert VitalParameterSchema.clamp_parameter("volume", 9999.0) == VitalParameterSchema.VOLUME_MAX

    def test_filter_cutoff_clamp(self):
        # MIDI note bounds
        assert VitalParameterSchema.clamp_parameter("filter_1_cutoff", 10.0) == VitalParameterSchema.FILTER_CUTOFF_SAFE_MIN
        assert VitalParameterSchema.clamp_parameter("filter_2_cutoff", 150.0) == VitalParameterSchema.FILTER_CUTOFF_MAX

    def test_enforce_anti_silence_invariants(self):
        broken_settings = {
            "volume": 0.0,
            "osc_1_on": 0.0,
            "osc_1_level": 0.0,
            "filter_1_on": 1.0,
            "filter_1_cutoff": 12.0,  # 12 Hz in low-pass = silence
            "filter_1_blend": 0.0,
            "filter_1_mix": 1.0,
            "env_1_sustain": 0.0,
            "env_1_decay": 0.01  # 10ms with zero sustain = instant silence
        }

        fixed = VitalParameterSchema.enforce_anti_silence_invariants(broken_settings)

        # Volume must be restored to nominal
        assert fixed["volume"] >= VitalParameterSchema.VOLUME_MIN
        # Oscillator 1 must be revived
        assert fixed["osc_1_on"] == 1.0
        assert fixed["osc_1_level"] >= 0.70
        # Cutoff must be raised above subsonic
        assert fixed["filter_1_cutoff"] >= VitalParameterSchema.FILTER_CUTOFF_SAFE_MIN
        # Decay must be extended so sound is audible
        assert fixed["env_1_decay"] >= 0.15

    def test_structural_integrity_invariants_6_7_8(self):
        """Verifies Invariants 6, 7, and 8 prevent 'Preset file is corrupted' errors in Vital."""
        settings = {
            "volume": 5400.0,
            "osc_1_on": 1.0,
            "osc_1_level": 0.8,
            "lfos": [
                {
                    "num_points": 4,
                    "points": [0.0, 0.0],  # Incomplete points (needs 8)
                    "powers": [0.0]        # Incomplete powers (needs 4)
                }
            ],
            "wavetables": [
                {
                    "version": "1.5.5",
                    "groups": [
                        {
                            "components": [
                                {
                                    "type": "Wave Source",
                                    "audio_file": "non_existent.wav"
                                }
                            ]
                        }
                    ]
                }
            ],
            "sample": {
                "name": "Invalid_Custom_Name_That_Crashes"
            }
        }

        fixed = VitalParameterSchema.enforce_anti_silence_invariants(settings)

        # Invariant 6: LFO vector lengths must strictly align to num_points
        lfo0 = fixed["lfos"][0]
        assert len(lfo0["points"]) == 2 * lfo0["num_points"]
        assert len(lfo0["powers"]) == lfo0["num_points"]

        # Invariant 7: Wavetable version normalized and audio_file removed
        wt0 = fixed["wavetables"][0]
        assert wt0["version"] == "1.0.7"
        comp0 = wt0["groups"][0]["components"][0]
        assert "audio_file" not in comp0
        assert comp0["interpolation"] == 1

        # Invariant 8: Sampler name sanitized to safe string
        assert fixed["sample"]["name"] == "White Noise"


class TestArchetypeCatalog:
    """Verifies preset discovery and archetype matching."""

    def test_catalog_indexing(self):
        catalog = ArchetypeCatalog()
        categories = catalog.get_available_categories()
        assert len(categories) > 0
        assert "BASS_PUNCH" in categories or "BASS_SUB" in categories or "BASS_808" in categories

    def test_select_archetype(self):
        catalog = ArchetypeCatalog()
        path, data = catalog.select_archetype(role="BASS_808")
        assert path.exists()
        assert "settings" in data
        assert len(data["settings"]) >= 700

    def test_select_lead_archetype(self):
        catalog = ArchetypeCatalog()
        path, data = catalog.select_archetype(role="LEAD_SAW")
        assert path.exists()
        assert "settings" in data


class TestVitalSoundSculptor:
    """Verifies macro sonic transformations."""

    def test_sculpt_brightness(self):
        catalog = ArchetypeCatalog()
        _, base_data = catalog.select_archetype("LEAD_SAW")

        sculpted_dark = VitalSoundSculptor.sculpt_preset(base_data, {"brightness": 0.0})
        sculpted_bright = VitalSoundSculptor.sculpt_preset(base_data, {"brightness": 1.0})

        cutoff_dark = sculpted_dark["settings"]["filter_1_cutoff"]
        cutoff_bright = sculpted_bright["settings"]["filter_1_cutoff"]
        assert cutoff_dark < cutoff_bright
        assert cutoff_dark >= VitalParameterSchema.FILTER_CUTOFF_SAFE_MIN

    def test_sculpt_bass_low_end_protection(self):
        catalog = ArchetypeCatalog()
        _, base_data = catalog.select_archetype("BASS_SUB")

        # Bass with heavy space request
        sculpted = VitalSoundSculptor.sculpt_preset(base_data, {
            "space_dimension": 0.9,
            "stereo_width": 1.0,
            "is_bass": True
        })

        # Low-end protection: unison must remain 1 (mono)
        assert sculpted["settings"]["osc_1_unison_voices"] == 1.0
        # Reverb pre-low cutoff must be active to protect sub
        assert sculpted["settings"]["reverb_pre_low_cutoff"] >= 40.0


class TestVitalSoundEngineE2E:
    """Verifies end-to-end preset creation, mutation, and disk persistence."""

    def test_create_and_audit_808(self, tmp_path):
        engine = VitalSoundEngine()
        out_file = engine.create_preset(
            preset_name="Engine_Heavy_808",
            role="BASS_808",
            directives={
                "warmth_drive": 0.85,
                "punch": 0.90,
                "brightness": 0.40,
                "is_bass": True
            },
            output_dir=tmp_path
        )

        assert out_file.exists()
        assert out_file.stat().st_size > 100000  # Preserves embedded wavetables (>100KB)

        # Audit preset
        audit = engine.audit_preset_file(out_file)
        assert audit["valid"] is True
        assert audit["audible"] is True
        assert audit["volume"] >= VitalParameterSchema.VOLUME_MIN

    def test_create_custom_vocal_lead(self, tmp_path):
        engine = VitalSoundEngine()
        out_file = engine.create_preset(
            preset_name="Engine_Vocal_Lead",
            role="LEAD_SAW",
            directives={
                "custom_wavetable": "VOCAL",
                "brightness": 0.75,
                "space_dimension": 0.60,
                "stereo_width": 0.70,
                "movement": 0.50
            },
            output_dir=tmp_path
        )

        assert out_file.exists()
        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert data["preset_name"] == "Engine_Vocal_Lead"
        wt_name = data["settings"]["wavetables"][0]["name"]
        assert "Vocal" in wt_name

        audit = engine.audit_preset_file(out_file)
        assert audit["valid"] is True
        assert audit["audible"] is True

    def test_mutate_preset(self, tmp_path):
        engine = VitalSoundEngine()
        base_file = engine.create_preset("Base_Chord", role="CHORD_SUPERAW", output_dir=tmp_path)

        mutated_file = engine.mutate_preset(
            source_path=base_file,
            directives={"decay_sustain": 0.1, "brightness": 0.9},  # Pluck mode
            new_name="Mutated_Chord_Pluck",
            output_dir=tmp_path
        )

        assert mutated_file.exists()
        mutated_data = json.loads(mutated_file.read_text(encoding="utf-8"))
        assert mutated_data["settings"]["env_1_sustain"] == 0.0  # Pluck sustain
        assert mutated_data["settings"]["env_1_decay"] < 0.60

    def test_create_ambient_drone_pad(self, tmp_path):
        engine = VitalSoundEngine()
        out_file = engine.create_preset(
            preset_name="Engine_Deep_Ambient_Pad",
            role="PAD_LUSH",
            directives={
                "attack": 3.0,
                "decay": 5.0,
                "sustain": 0.9,
                "release": 4.0,
                "space_dimension": 0.85,
                "stereo_width": 0.75,
                "brightness": 0.40
            },
            output_dir=tmp_path
        )
        assert out_file.exists()
        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert data["settings"]["env_1_attack"] == pytest.approx(3.0, abs=0.01)
        assert data["settings"]["reverb_dry_wet"] > 0.40

        audit = engine.audit_preset_file(out_file)
        assert audit["valid"] is True
        assert audit["audible"] is True
