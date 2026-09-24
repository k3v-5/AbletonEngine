# tests/decent_sampler/test_golden_presets.py
"""
Golden File & Archetype Snapshot Tests.
"""

from pathlib import Path
import xml.etree.ElementTree as ET

from engine.sound_design.decent_sampler.templates import (
    create_acoustic_piano,
    create_orchestral_strings,
    create_drum_kit,
    create_808_sub_bass,
)
from engine.sound_design.decent_sampler.validator import DecentSamplerValidator


def normalize_xml(xml_content: str) -> str:
    """Normalizes whitespace and attribute ordering for canonical comparison."""
    root = ET.fromstring(xml_content)
    return ET.tostring(root, encoding="utf-8").decode("utf-8")


class TestGoldenPresets:
    def test_golden_piano_matches_snapshot(self):
        """Verifies programmatic concert grand piano exactly matches the golden fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "golden_piano.dspreset"
        golden_xml = fixture_path.read_text(encoding="utf-8")

        builder = create_acoustic_piano()
        generated_xml = builder.compile(strict=True, sanitize=True)

        assert normalize_xml(generated_xml) == normalize_xml(golden_xml)

    def test_all_archetypes_compile_and_pass_strict_validation(self):
        """Verifies Piano, Strings, Drum Kit, and 808 compile and pass strict 3-tier validation."""
        archetypes = [
            ("Piano", create_acoustic_piano()),
            ("Strings", create_orchestral_strings()),
            ("DrumKit", create_drum_kit()),
            ("808", create_808_sub_bass()),
        ]

        for name, builder in archetypes:
            xml_str = builder.compile(strict=True, sanitize=True)
            assert len(xml_str) > 0

            # Validate generated XML tree
            report_xml = DecentSamplerValidator.validate_xml(xml_str, strict=True)
            assert report_xml.is_valid is True, f"Archetype {name} failed XML validation"

            # Validate underlying model
            report_model = DecentSamplerValidator.validate_model(builder.instrument, strict=True)
            assert report_model.is_valid is True, f"Archetype {name} failed Model validation"
