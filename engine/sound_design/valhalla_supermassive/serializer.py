# engine/sound_design/valhalla_supermassive/serializer.py
"""
Serializer and Parser for Valhalla Supermassive .vpreset Files.

Handles bidirectional translation between SupermassiveModel,
XML strings, and .vpreset files on disk or clipboard.
"""

from typing import Optional, Union
import xml.etree.ElementTree as ET
from pathlib import Path
import os
import subprocess

from .schema import ValhallaSupermassiveSchema
from .model import SupermassiveModel
from .sanitizer import SupermassiveSanitizer


class ValhallaSupermassiveSerializer:
    """Serializes and parses Valhalla Supermassive XML presets."""

    DEFAULT_USER_DIR = Path("C:/ProgramData/Valhalla DSP, LLC/ValhallaSupermassive/Presets/User")

    @classmethod
    def to_xml_element(cls, model: SupermassiveModel) -> ET.Element:
        """Convert SupermassiveModel to xml.etree.ElementTree.Element."""
        attribs = model.to_xml_attribs()
        return ET.Element(ValhallaSupermassiveSchema.PLUGIN_NAME, attribs)

    @classmethod
    def to_xml_string(cls, model: SupermassiveModel, sanitize: bool = True) -> str:
        """
        Convert SupermassiveModel to a single-line XML string formatted
        identically to official Valhalla .vpreset files.
        """
        target = model
        if sanitize:
            target, _ = SupermassiveSanitizer.sanitize(model)

        attribs = target.to_xml_attribs()
        parts = [f'<{ValhallaSupermassiveSchema.PLUGIN_NAME}']
        for k, v in attribs.items():
            parts.append(f'{k}="{v}"')
        return " ".join(parts) + "/>\n"

    @classmethod
    def from_xml_element(cls, elem: ET.Element) -> SupermassiveModel:
        """Parse an Element into SupermassiveModel."""
        if elem.tag != ValhallaSupermassiveSchema.PLUGIN_NAME:
            raise ValueError(
                f"Invalid XML root '{elem.tag}'. Expected '{ValhallaSupermassiveSchema.PLUGIN_NAME}'."
            )

        model = SupermassiveModel()
        attribs = elem.attrib

        if "presetName" in attribs:
            model.preset_name = attribs["presetName"]
        if "pluginVersion" in attribs:
            model.plugin_version = attribs["pluginVersion"]

        mapping = {
            "Mix": "mix",
            "DelaySync": "delay_sync",
            "DelayNote": "delay_note",
            "Delay_Ms": "delay_ms",
            "DelayWarp": "delay_warp",
            "Clear": "clear",
            "Feedback": "feedback",
            "Density": "density",
            "Width": "width",
            "LowCut": "low_cut",
            "HighCut": "high_cut",
            "ModRate": "mod_rate",
            "ModDepth": "mod_depth",
            "Mode": "mode",
            "Reserved1": "reserved1",
            "Reserved2": "reserved2",
            "Reserved3": "reserved3",
            "Reserved4": "reserved4",
        }

        for xml_attr, model_field in mapping.items():
            if xml_attr in attribs:
                try:
                    setattr(model, model_field, float(attribs[xml_attr]))
                except ValueError:
                    pass

        return model

    @classmethod
    def from_xml_string(cls, xml_text: str) -> SupermassiveModel:
        """Parse raw XML string into SupermassiveModel."""
        root = ET.fromstring(xml_text.strip())
        return cls.from_xml_element(root)

    @classmethod
    def save_preset_file(
        cls,
        model: SupermassiveModel,
        destination_path: Optional[Union[str, Path]] = None,
        category: Optional[str] = None,
    ) -> Path:
        """
        Save preset as .vpreset file. If destination_path is omitted,
        saves to Valhalla's User presets directory:
        C:/ProgramData/Valhalla DSP, LLC/ValhallaSupermassive/Presets/User/<Category>/<PresetName>.vpreset
        """
        if destination_path is None:
            base_dir = cls.DEFAULT_USER_DIR
            if category:
                base_dir = base_dir / category
            dest = base_dir / f"{model.preset_name}.vpreset"
        else:
            dest = Path(destination_path)
            if dest.suffix != ".vpreset":
                dest = dest.with_suffix(".vpreset")

        dest.parent.mkdir(parents=True, exist_ok=True)
        xml_content = cls.to_xml_string(model)
        dest.write_text(xml_content, encoding="utf-8")
        return dest

    # Ergonomic alias
    save_preset = save_preset_file

    @classmethod
    def load_preset_file(cls, path: Union[str, Path]) -> SupermassiveModel:
        """Load and parse a .vpreset file from disk."""
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"Valhalla preset file not found: {p}")
        text = p.read_text(encoding="utf-8", errors="ignore")
        return cls.from_xml_string(text)

    @classmethod
    def copy_to_clipboard(cls, model_or_xml: Union[SupermassiveModel, str]) -> bool:
        """
        Copies the preset XML to the Windows clipboard for instant
        paste inside Ableton Live / Supermassive GUI.
        """
        if isinstance(model_or_xml, str):
            xml_str = model_or_xml.strip()
        else:
            xml_str = cls.to_xml_string(model_or_xml).strip()
        try:
            cmd = f"Set-Clipboard -Value '{xml_str}'"
            subprocess.run(["powershell", "-Command", cmd], check=True, capture_output=True)
            return True
        except Exception:
            return False
