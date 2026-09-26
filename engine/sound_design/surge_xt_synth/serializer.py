# engine/sound_design/surge_xt_synth/serializer.py
"""
Surge XT Synthesizer Serializer & Patch File Exporter.

Serializes SurgeSynthPatchModel to native .surgepatch XML files on disk,
compatible with Surge XT's user library directory structure.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Union

from .model import SurgeSynthPatchModel
from .validator import SurgeSynthValidator
from .sanitizer import SurgeSynthSanitizer

logger = logging.getLogger(__name__)


class SurgeSynthSerializer:
    """Serializes Surge XT Synthesizer patches to structured XML files."""

    DEFAULT_WINDOWS_PATCH_DIR = Path.home() / "Documents" / "Surge XT" / "Patches"
    FALLBACK_LOCAL_PATCH_DIR = Path("state/presets/surge_xt_synth")

    @classmethod
    def get_patch_directory(cls, category: Optional[str] = None) -> Path:
        """Determines the destination folder for Surge XT patches."""
        cat_folder = category or "AbletonEngine"
        base_dir = cls.DEFAULT_WINDOWS_PATCH_DIR
        try:
            target = base_dir / cat_folder
            target.mkdir(parents=True, exist_ok=True)
            return target
        except Exception as e:
            logger.debug(f"Notice accessing Documents/Surge XT: {e}. Using local fallback.")
            local_target = cls.FALLBACK_LOCAL_PATCH_DIR / cat_folder
            local_target.mkdir(parents=True, exist_ok=True)
            return local_target

    @classmethod
    def to_xml_string(cls, patch: SurgeSynthPatchModel, sanitize_first: bool = True) -> str:
        """Converts patch model to XML string."""
        if sanitize_first:
            SurgeSynthSanitizer.sanitize_patch(patch)
        return patch.to_xml_string()

    @classmethod
    def save_patch(
        cls,
        patch: SurgeSynthPatchModel,
        target_path: Optional[Union[str, Path]] = None,
        category: Optional[str] = None
    ) -> Path:
        """
        Saves a .surgepatch file to disk with complete XML structure.
        """
        SurgeSynthSanitizer.sanitize_patch(patch)
        v_rep = SurgeSynthValidator.validate_patch(patch, strict=False)
        if not v_rep.is_valid:
            logger.warning(f"Notice during Surge XT patch validation: {v_rep.errors}")

        if target_path is not None:
            dest = Path(target_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
        else:
            p_dir = cls.get_patch_directory(category or patch.category)
            safe_name = "".join(c for c in patch.patch_name if c.isalnum() or c in ("_", "-")).strip() or "Patch"
            dest = p_dir / f"{safe_name}.surgepatch"

        xml_content = patch.to_xml_string()
        with open(dest, "w", encoding="utf-8") as f:
            f.write(xml_content)

        logger.info(f"Saved Surge XT Synthesizer patch: {dest}")
        return dest
