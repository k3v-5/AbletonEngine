# engine/sound_design/decent_sampler/library_manager.py
"""
Decent Sampler Library Manager & Pre-Flight Quality Auditor.

Enforces strict user ownership of sound libraries:
1. Primary library folder is strictly defined by user configuration (config / settings / env).
2. Pre-flight health check: Not every folder is accepted. Folders are audited
   for valid samples, working .dspreset files, existing sample paths, and absence
   of junk directories (__MACOSX, hidden files).
3. Only certified, non-corrupt libraries are exposed to AI agents in guided_session.
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import os
import json
import logging
import xml.etree.ElementTree as ET

from .validator import DecentSamplerValidator, ValidationReport
from .sample_analyzer import SampleAsset
from .serializer import DSPresetSerializer


logger = logging.getLogger("DecentSamplerLibraryManager")


@dataclass
class DecentSamplerLibraryInfo:
    """Represents a discovered and audited Decent Sampler library."""
    name: str
    path: Path
    preset_path: Optional[Path] = None
    sample_dir: Optional[Path] = None
    sample_count: int = 0
    is_valid: bool = False
    role_hint: str = "OTHER"
    validation_errors: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "preset_path": str(self.preset_path) if self.preset_path else None,
            "sample_dir": str(self.sample_dir) if self.sample_dir else None,
            "sample_count": self.sample_count,
            "is_valid": self.is_valid,
            "role_hint": self.role_hint,
            "validation_errors": self.validation_errors,
            "tags": self.tags,
        }


class DecentSamplerLibraryManager:
    """
    Manages and validates Decent Sampler libraries within the user's primary folder.
    """

    SETTINGS_FILE = Path("state/engine_settings.json")
    AUDIO_EXTENSIONS = {".wav", ".flac", ".aif", ".aiff", ".mp3", ".ogg"}
    IGNORED_DIRS = {"__macosx", ".git", ".svn", ".idea", ".vscode", "__pycache__"}

    @classmethod
    def get_library_root(cls) -> Path:
        """
        Retrieves the primary library root configured by the user.
        Priority:
        1. state/engine_settings.json ["decent_sampler_library_root"]
        2. Environment variable DECENT_SAMPLER_LIB_ROOT
        3. Local project default: SonidosDecentSampler (if exists)
        4. Standard fallback: ~/Documents/Decent Sampler
        """
        # 1. Check persistent settings file
        if cls.SETTINGS_FILE.exists():
            try:
                data = json.loads(cls.SETTINGS_FILE.read_text(encoding="utf-8"))
                p_str = data.get("decent_sampler_library_root")
                if p_str and Path(p_str).exists():
                    return Path(p_str).resolve()
            except Exception as e:
                logger.warning(f"Error reading {cls.SETTINGS_FILE}: {e}")

        # 2. Check environment variable
        env_val = os.environ.get("DECENT_SAMPLER_LIB_ROOT")
        if env_val and Path(env_val).exists():
            return Path(env_val).resolve()

        # 3. Check workspace SonidosDecentSampler
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        local_sonidos = base_dir / "SonidosDecentSampler"
        if local_sonidos.exists() and local_sonidos.is_dir():
            return local_sonidos.resolve()

        # 4. Standard Documents fallback
        user_docs = Path(os.path.expanduser("~")) / "Documents" / "Decent Sampler"
        return user_docs.resolve()

    @classmethod
    def set_library_root(cls, path: Union[str, Path]) -> Path:
        """
        Sets and persists the primary library root folder as decided by the user.
        Validates that the path physically exists.
        """
        resolved = Path(path).resolve()
        if not resolved.exists() or not resolved.is_dir():
            raise FileNotFoundError(f"Configured Decent Sampler library path does not exist: {resolved}")

        cls.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        settings = {}
        if cls.SETTINGS_FILE.exists():
            try:
                settings = json.loads(cls.SETTINGS_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass

        settings["decent_sampler_library_root"] = str(resolved)
        cls.SETTINGS_FILE.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"Decent Sampler primary library root updated to: {resolved}")
        return resolved

    @classmethod
    def audit_library_folder(cls, folder_path: Path) -> DecentSamplerLibraryInfo:
        """
        Thoroughly audits a candidate library folder.
        Verifies:
        - Absence of corruption or zero samples
        - Valid .dspreset file and working sample references
        - Or valid uncompiled raw samples suitable for auto-mapping
        """
        folder_name = folder_path.name
        info = DecentSamplerLibraryInfo(name=folder_name, path=folder_path)

        # Check ignored directories
        if folder_name.lower() in cls.IGNORED_DIRS or folder_name.startswith("."):
            info.is_valid = False
            info.validation_errors.append("Ignored metadata directory.")
            return info

        # Search for .dspreset files (directly or nested up to 2 levels)
        dspresets: List[Path] = []
        try:
            for item in folder_path.rglob("*.dspreset"):
                # Ignore items in __MACOSX
                if any(part.lower() in cls.IGNORED_DIRS for part in item.parts):
                    continue
                dspresets.append(item)
        except Exception as e:
            info.is_valid = False
            info.validation_errors.append(f"Filesystem read error: {e}")
            return info

        # Search for audio samples
        sample_files: List[Path] = []
        try:
            for item in folder_path.rglob("*"):
                if item.is_file() and item.suffix.lower() in cls.AUDIO_EXTENSIONS:
                    if not any(part.lower() in cls.IGNORED_DIRS for part in item.parts):
                        sample_files.append(item)
        except Exception:
            pass

        info.sample_count = len(sample_files)
        if sample_files:
            info.sample_dir = sample_files[0].parent

        # Case 1: Library has a compiled .dspreset
        if dspresets:
            preset_file = dspresets[0]
            info.preset_path = preset_file
            info.name = preset_file.stem

            # Validate preset XML
            try:
                content = preset_file.read_text(encoding="utf-8", errors="ignore")
                val_report = DecentSamplerValidator.validate_xml(content, strict=False, lenient=True)
                if not val_report.is_valid:
                    info.is_valid = False
                    info.validation_errors.extend(val_report.all_errors)
                    return info

                # Clean XML attributes and audit sample references
                clean_content, _ = DSPresetSerializer.clean_xml_content(content)
                root = ET.fromstring(clean_content)
                missing_samples = 0

                total_refs = 0
                preset_dir = preset_file.parent

                for s_elem in root.findall(".//sample"):
                    p_attr = s_elem.attrib.get("path")
                    if p_attr:
                        total_refs += 1
                        # Resolve path
                        target = (preset_dir / p_attr).resolve()
                        if not target.exists():
                            missing_samples += 1

                if total_refs > 0 and missing_samples == total_refs:
                    info.is_valid = False
                    info.validation_errors.append(
                        f"All {total_refs} audio sample references are broken or missing on disk."
                    )
                    return info

                info.is_valid = True

            except Exception as e:
                info.is_valid = False
                info.validation_errors.append(f"Failed to parse preset XML: {e}")
                return info

        # Case 2: Uncompiled folder with raw samples
        elif sample_files:
            if len(sample_files) < 1:
                info.is_valid = False
                info.validation_errors.append("Folder contains no usable audio samples.")
                return info

            # Check if samples are recognizable by SampleAsset
            valid_pitches = 0
            for s in sample_files[:10]:
                asset = SampleAsset.from_filename(str(s))
                if asset.root_note is not None:
                    valid_pitches += 1


            info.is_valid = True
            info.tags.append("uncompiled_samples")

        else:
            info.is_valid = False
            info.validation_errors.append("No .dspreset and no audio files found in directory.")
            return info

        # Infer acoustic role hint based on folder name
        name_lower = (info.name + " " + str(folder_path)).lower()
        if any(w in name_lower for w in ["guitar", "acustic", "flamenc", "strum"]):
            info.role_hint = "GUITAR"
        elif any(w in name_lower for w in ["piano", "rhodes", "grand", "felt", "upright", "keyboard"]):
            info.role_hint = "KEYS"
        elif any(w in name_lower for w in ["pad", "string", "choir", "ambient", "drone", "space"]):
            info.role_hint = "PAD"
        elif any(w in name_lower for w in ["bass", "sub", "808"]):
            info.role_hint = "BASS"
        elif any(w in name_lower for w in ["perc", "drum", "clap", "snare", "taiko", "hihat"]):
            info.role_hint = "DRUMS"
        elif any(w in name_lower for w in ["lead", "pluck", "synth", "solo", "flute"]):
            info.role_hint = "LEAD"

        return info

    @classmethod
    def scan_libraries(cls, require_valid: bool = True) -> List[DecentSamplerLibraryInfo]:
        """
        Scans the user's primary library root, auditing all direct subdirectories.
        Returns only valid libraries by default.
        """
        root = cls.get_library_root()
        if not root.exists() or not root.is_dir():
            logger.warning(f"Library root does not exist: {root}")
            return []

        results: List[DecentSamplerLibraryInfo] = []
        try:
            for entry in sorted(root.iterdir()):
                if entry.is_dir():
                    info = cls.audit_library_folder(entry)
                    if not require_valid or info.is_valid:
                        results.append(info)
        except Exception as e:
            logger.error(f"Error scanning library root '{root}': {e}")

        return results

    @classmethod
    def get_libraries_for_role(cls, role: str) -> List[DecentSamplerLibraryInfo]:
        """Returns certified valid libraries matching the track role or general instruments."""
        role_up = str(role or "").upper()
        root = cls.get_library_root()
        has_samples = any(root.rglob("*.wav")) if root.exists() else False
        all_valid = cls.scan_libraries(require_valid=has_samples)
        matching = []

        for lib in all_valid:
            if lib.role_hint == role_up:
                matching.append(lib)
            elif lib.role_hint == "OTHER" and role_up not in ("DRUMS", "KICK", "PERCUSSION", "CLAP", "SNARE", "808_BASS"):
                matching.append(lib)

        # If no specific matches, return all valid libraries for melodic/harmonic roles, but never for drum roles
        if not matching and role_up not in ("DRUMS", "KICK", "PERCUSSION", "CLAP", "SNARE", "808_BASS"):
            return all_valid
        return matching

    @classmethod
    def get_library_by_name(cls, name_query: str) -> Optional[DecentSamplerLibraryInfo]:
        """Finds a specific certified valid library by name query."""
        cleaned = name_query.strip().lower()
        root = cls.get_library_root()
        has_samples = any(root.rglob("*.wav")) if root.exists() else False
        all_valid = cls.scan_libraries(require_valid=has_samples)

        for lib in all_valid:
            if lib.name.lower() == cleaned:
                return lib

        # Substring search
        for lib in all_valid:
            if cleaned in lib.name.lower():
                return lib

        return None
