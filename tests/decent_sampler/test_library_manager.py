# tests/decent_sampler/test_library_manager.py
"""
Unit tests for DecentSamplerLibraryManager & pre-flight library health auditor.
"""

import pytest
import tempfile
import json
from pathlib import Path

from engine.sound_design.decent_sampler.library_manager import (
    DecentSamplerLibraryManager,
    DecentSamplerLibraryInfo,
)


class TestDecentSamplerLibraryManager:
    def test_get_and_set_library_root(self, tmp_path, monkeypatch):
        # Point settings file to temp dir
        test_settings = tmp_path / "engine_settings.json"
        monkeypatch.setattr(DecentSamplerLibraryManager, "SETTINGS_FILE", test_settings)

        custom_lib = tmp_path / "MyCustomSamples"
        custom_lib.mkdir()

        # Set root
        saved_root = DecentSamplerLibraryManager.set_library_root(custom_lib)
        assert saved_root == custom_lib.resolve()

        # Retrieve root
        retrieved = DecentSamplerLibraryManager.get_library_root()
        assert retrieved == custom_lib.resolve()

    def test_set_nonexistent_root_raises(self, tmp_path):
        bad_path = tmp_path / "Does_Not_Exist"
        with pytest.raises(FileNotFoundError):
            DecentSamplerLibraryManager.set_library_root(bad_path)

    def test_audit_ignores_macosx_and_junk(self, tmp_path):
        junk_dir = tmp_path / "__MACOSX"
        junk_dir.mkdir()
        info = DecentSamplerLibraryManager.audit_library_folder(junk_dir)
        assert not info.is_valid
        assert any("Ignored" in e for e in info.validation_errors)

    def test_audit_valid_compiled_library(self, tmp_path):
        lib_dir = tmp_path / "Vintage Piano"
        samples_dir = lib_dir / "Samples"
        samples_dir.mkdir(parents=True)

        # Create dummy sample
        sample_file = samples_dir / "piano_C4.wav"
        sample_file.write_bytes(b"RIFF....WAVEfmt ....data....")

        # Create valid .dspreset referencing the sample
        preset_file = lib_dir / "Vintage Piano.dspreset"
        xml_content = (
            '<DecentSampler minVersion="1.0.0">\n'
            '  <ui width="812" height="375">\n'
            '    <tab name="main">\n'
            '      <labeled-knob x="0" y="0" label="Volume">\n'
            '        <binding type="amp" level="instrument" position="0" parameter="AMP_VOLUME" />\n'
            '      </labeled-knob>\n'
            '    </tab>\n'
            '  </ui>\n'
            '  <groups>\n'
            '    <group>\n'
            '      <sample path="Samples/piano_C4.wav" rootNote="60" loNote="0" hiNote="127" />\n'
            '    </group>\n'
            '  </groups>\n'
            '</DecentSampler>\n'
        )
        preset_file.write_text(xml_content, encoding="utf-8")

        info = DecentSamplerLibraryManager.audit_library_folder(lib_dir)
        assert info.is_valid
        assert info.sample_count == 1
        assert info.role_hint == "KEYS"
        assert info.preset_path == preset_file

    def test_audit_broken_sample_reference_fails(self, tmp_path):
        lib_dir = tmp_path / "Broken Library"
        lib_dir.mkdir()

        # Preset references non-existent sample
        preset_file = lib_dir / "Broken.dspreset"
        xml_content = (
            '<DecentSampler minVersion="1.0.0">\n'
            '  <groups>\n'
            '    <group>\n'
            '      <sample path="Samples/ghost_file.wav" rootNote="60" loNote="0" hiNote="127" />\n'
            '    </group>\n'
            '  </groups>\n'
            '</DecentSampler>\n'
        )
        preset_file.write_text(xml_content, encoding="utf-8")

        info = DecentSamplerLibraryManager.audit_library_folder(lib_dir)
        assert not info.is_valid
        assert any("broken or missing" in e for e in info.validation_errors)

    def test_scan_real_sonidos_decent_sampler(self):
        # Test against real project folder if present
        root = DecentSamplerLibraryManager.get_library_root()
        if (root / "DR Acoustic Guitar DS v1").exists():
            has_samples = any(root.rglob("*.wav"))
            libs = DecentSamplerLibraryManager.scan_libraries(require_valid=has_samples)
            names = [lib.name for lib in libs]
            assert any("Acoustic Guitar" in n for n in names)
            assert any("Cathedral Piano" in n for n in names)
            assert any("Godly Pad" in n for n in names)
