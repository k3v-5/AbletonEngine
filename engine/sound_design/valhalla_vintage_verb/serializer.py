# engine/sound_design/valhalla_vintage_verb/serializer.py
"""
Valhalla VintageVerb Serializer & Clipboard Integration.

Handles serializing VintageVerbModel to .vpreset files on Windows/macOS
and injecting XML preset strings directly into the Windows clipboard for
instant 1-click 'Paste from Clipboard' activation inside Ableton Live.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Union

from .model import VintageVerbModel
from .schema import ValhallaVintageVerbSchema
from .validator import ValhallaVintageVerbValidator
from .sanitizer import ValhallaVintageVerbSanitizer

logger = logging.getLogger(__name__)


class ValhallaVintageVerbSerializer:
    """Serializes Valhalla VintageVerb presets and integrates with OS clipboard."""

    DEFAULT_WINDOWS_PRESET_DIR = Path(r"C:\ProgramData\Valhalla DSP, LLC\ValhallaVintageVerb\Presets\User")
    FALLBACK_LOCAL_PRESET_DIR = Path("state/presets/valhalla_vintage_verb")

    @classmethod
    def get_preset_directory(cls, category: Optional[str] = None) -> Path:
        """Determines the active preset destination directory."""
        base_dir = cls.DEFAULT_WINDOWS_PRESET_DIR
        try:
            base_dir.mkdir(parents=True, exist_ok=True)
            target = base_dir / (category or "AbletonEngine")
            target.mkdir(parents=True, exist_ok=True)
            return target
        except Exception as e:
            logger.debug(f"Notice accessing ProgramData for VintageVerb: {e}. Using local fallback.")
            local_target = cls.FALLBACK_LOCAL_PRESET_DIR / (category or "AbletonEngine")
            local_target.mkdir(parents=True, exist_ok=True)
            return local_target

    @classmethod
    def to_xml_string(cls, model: VintageVerbModel, sanitize_first: bool = True) -> str:
        """Converts model to XML string."""
        if sanitize_first:
            ValhallaVintageVerbSanitizer.sanitize(model)
        return model.to_xml_string()

    @classmethod
    def save_preset(
        cls,
        model: VintageVerbModel,
        target_path: Optional[Union[str, Path]] = None,
        category: Optional[str] = None
    ) -> Path:
        """
        Saves a .vpreset file to disk.
        Validates model and ensures correct encoding.
        """
        ValhallaVintageVerbSanitizer.sanitize(model)
        v_rep = ValhallaVintageVerbValidator.validate(model, strict=False)
        if not v_rep.is_valid:
            logger.warning(f"Notice during VintageVerb validation: {v_rep.errors}")

        if target_path is not None:
            dest = Path(target_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
        else:
            p_dir = cls.get_preset_directory(category)
            safe_name = "".join(c for c in model.preset_name if c.isalnum() or c in ("_", "-")).strip() or "Preset"
            dest = p_dir / f"{safe_name}.vpreset"

        xml_content = model.to_xml_string()
        with open(dest, "w", encoding="utf-8") as f:
            f.write(xml_content)

        logger.info(f"Saved Valhalla VintageVerb preset: {dest}")
        return dest

    @classmethod
    def copy_to_clipboard(cls, xml_string: str) -> bool:
        """
        Injects XML preset string into the Windows clipboard using PowerShell Set-Clipboard.
        Allows immediate 1-click 'Paste from Clipboard' in Valhalla VintageVerb inside Ableton.
        """
        clean_xml = str(xml_string).strip()
        if not clean_xml:
            return False

        if os.name == "nt":
            try:
                # Use powershell Set-Clipboard with standard input
                proc = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "$input | Set-Clipboard"],
                    input=clean_xml,
                    text=True,
                    capture_output=True,
                    timeout=3
                )
                if proc.returncode == 0:
                    logger.debug("Successfully copied Valhalla VintageVerb preset to Windows clipboard.")
                    return True
                else:
                    logger.warning(f"PowerShell Set-Clipboard returned code {proc.returncode}: {proc.stderr}")
            except Exception as ex:
                logger.warning(f"Notice invoking PowerShell Set-Clipboard: {ex}")

        # Non-Windows or fallback
        try:
            import pyperclip
            pyperclip.copy(clean_xml)
            return True
        except ImportError:
            pass

        return False
