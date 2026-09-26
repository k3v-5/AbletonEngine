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

    # In-memory and mtime-invalidated caches
    _folder_audit_cache: Dict[str, Any] = {}
    _scan_cache: Dict[Any, List[DecentSamplerLibraryInfo]] = {}
    _role_cache: Dict[Any, List[DecentSamplerLibraryInfo]] = {}

    @classmethod
    def clear_cache(cls) -> None:
        """Clears all in-memory audit, scan, and role caches."""
        cls._folder_audit_cache.clear()
        cls._scan_cache.clear()
        cls._role_cache.clear()

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
        Validates that the path physically exists and invalidates cached scans.
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

        # Invalidate in-memory caches upon root change
        cls.clear_cache()
        try:
            from engine.instruments.browser_catalog import LiveBrowserCatalogEngine
            LiveBrowserCatalogEngine.clear_cache()
        except Exception:
            pass

        return resolved

    @classmethod
    def audit_library_folder(cls, folder_path: Path) -> DecentSamplerLibraryInfo:
        """
        Thoroughly audits a candidate library folder.
        Verifies:
        - Absence of corruption or zero samples
        - Valid .dspreset file and working sample references
        - Or valid uncompiled raw samples suitable for auto-mapping
        Uses mtime-based in-memory caching and single-pass filesystem scanning.
        """
        folder_path = Path(folder_path).resolve()
        folder_name = folder_path.name
        info = DecentSamplerLibraryInfo(name=folder_name, path=folder_path)

        # Fast path: Check ignored metadata directories
        if folder_name.lower() in cls.IGNORED_DIRS or folder_name.startswith("."):
            info.is_valid = False
            info.validation_errors.append("Ignored metadata directory.")
            return info

        if not folder_path.exists() or not folder_path.is_dir():
            info.is_valid = False
            info.validation_errors.append(f"Folder does not exist or is not a directory: {folder_path}")
            return info

        try:
            mtime = folder_path.stat().st_mtime
        except Exception:
            mtime = 0.0

        cache_key = str(folder_path)
        if cache_key in cls._folder_audit_cache:
            cached_mtime, cached_info = cls._folder_audit_cache[cache_key]
            if cached_mtime == mtime:
                return cached_info

        # Single-pass scan for both .dspreset files and audio samples
        dspresets: List[Path] = []
        sample_files: List[Path] = []
        try:
            for root_dir, dirs, files in os.walk(folder_path):
                # Prune ignored and hidden directories from descent
                dirs[:] = [
                    d for d in dirs
                    if d.lower() not in cls.IGNORED_DIRS and not d.startswith(".")
                ]
                for f in files:
                    lower_f = f.lower()
                    if lower_f.endswith(".dspreset"):
                        dspresets.append(Path(root_dir) / f)
                    else:
                        ext = os.path.splitext(lower_f)[1]
                        if ext in cls.AUDIO_EXTENSIONS:
                            sample_files.append(Path(root_dir) / f)
        except Exception as e:
            info.is_valid = False
            info.validation_errors.append(f"Filesystem read error: {e}")
            cls._folder_audit_cache[cache_key] = (mtime, info)
            return info

        dspresets.sort()
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
                    cls._folder_audit_cache[cache_key] = (mtime, info)
                    return info

                # Clean XML attributes and audit sample references
                clean_content, _ = DSPresetSerializer.clean_xml_content(content)
                root = ET.fromstring(clean_content)

                preset_dir = preset_file.parent
                samples = root.findall(".//sample")
                sample_paths = [s.attrib.get("path") for s in samples if s.attrib.get("path")]
                total_refs = len(sample_paths)

                # Short-circuit check: only invalid when ALL referenced samples are missing
                if total_refs > 0:
                    at_least_one_exists = False
                    for p_attr in sample_paths:
                        target = (preset_dir / p_attr).resolve()
                        if target.exists():
                            at_least_one_exists = True
                            break

                    if not at_least_one_exists:
                        info.is_valid = False
                        info.validation_errors.append(
                            f"All {total_refs} audio sample references are broken or missing on disk."
                        )
                        cls._folder_audit_cache[cache_key] = (mtime, info)
                        return info

                info.is_valid = True

            except Exception as e:
                info.is_valid = False
                info.validation_errors.append(f"Failed to parse preset XML: {e}")
                cls._folder_audit_cache[cache_key] = (mtime, info)
                return info

        # Case 2: Uncompiled folder with raw samples
        elif sample_files:
            if len(sample_files) < 1:
                info.is_valid = False
                info.validation_errors.append("Folder contains no usable audio samples.")
                cls._folder_audit_cache[cache_key] = (mtime, info)
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
            cls._folder_audit_cache[cache_key] = (mtime, info)
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

        cls._folder_audit_cache[cache_key] = (mtime, info)
        return info

    @classmethod
    def scan_libraries(cls, require_valid: bool = True) -> List[DecentSamplerLibraryInfo]:
        """
        Scans the user's primary library root, auditing all direct subdirectories.
        Returns only valid libraries by default.
        Uses mtime-based in-memory caching to eliminate redundant scans.
        """
        root = cls.get_library_root()
        if not root.exists() or not root.is_dir():
            logger.warning(f"Library root does not exist: {root}")
            return []

        try:
            root_mtime = root.stat().st_mtime
        except Exception:
            root_mtime = 0.0

        cache_key = (str(root), root_mtime, require_valid)
        if cache_key in cls._scan_cache:
            return list(cls._scan_cache[cache_key])

        unfiltered_key = (str(root), root_mtime, False)
        if unfiltered_key in cls._scan_cache:
            all_entries = cls._scan_cache[unfiltered_key]
            res = [lib for lib in all_entries if lib.is_valid] if require_valid else all_entries
            cls._scan_cache[cache_key] = res
            return list(res)

        results: List[DecentSamplerLibraryInfo] = []
        try:
            for entry in sorted(root.iterdir()):
                if entry.is_dir():
                    info = cls.audit_library_folder(entry)
                    results.append(info)
        except Exception as e:
            logger.error(f"Error scanning library root '{root}': {e}")

        cls._scan_cache[unfiltered_key] = results
        res = [lib for lib in results if lib.is_valid] if require_valid else results
        cls._scan_cache[cache_key] = res
        return list(res)

    @classmethod
    def get_libraries_for_role(cls, role: str) -> List[DecentSamplerLibraryInfo]:
        """
        Returns certified valid libraries matching the track role or general instruments.
        Derives sample presence directly from audited library metadata instead of global recursive walk.
        """
        role_up = str(role or "").upper()
        root = cls.get_library_root()
        if not root.exists() or not root.is_dir():
            return []

        try:
            root_mtime = root.stat().st_mtime
        except Exception:
            root_mtime = 0.0

        cache_key = (str(root), root_mtime, role_up)
        if cache_key in cls._role_cache:
            return list(cls._role_cache[cache_key])

        all_libs = cls.scan_libraries(require_valid=False)
        has_samples = any(lib.sample_count > 0 for lib in all_libs)
        all_valid = [lib for lib in all_libs if lib.is_valid] if has_samples else all_libs
        matching = []

        for lib in all_valid:
            if lib.role_hint == role_up:
                matching.append(lib)
            elif lib.role_hint == "OTHER" and role_up not in ("DRUMS", "KICK", "PERCUSSION", "CLAP", "SNARE", "808_BASS"):
                matching.append(lib)

        # If no specific matches, return all valid libraries for melodic/harmonic roles, but never for drum roles
        if not matching and role_up not in ("DRUMS", "KICK", "PERCUSSION", "CLAP", "SNARE", "808_BASS"):
            matching = all_valid

        cls._role_cache[cache_key] = matching
        return list(matching)

    @classmethod
    def get_library_by_name(cls, name_query: str) -> Optional[DecentSamplerLibraryInfo]:
        """Finds a specific certified valid library by name query."""
        cleaned = name_query.strip().lower()
        root = cls.get_library_root()
        if not root.exists() or not root.is_dir():
            return None

        all_libs = cls.scan_libraries(require_valid=False)
        has_samples = any(lib.sample_count > 0 for lib in all_libs)
        all_valid = [lib for lib in all_libs if lib.is_valid] if has_samples else all_libs

        for lib in all_valid:
            if lib.name.lower() == cleaned:
                return lib

        # Substring search
        for lib in all_valid:
            if cleaned in lib.name.lower():
                return lib

        return None
