# Paths for Ableton sample library and manifest storage
from pathlib import Path
import os

def default_samples_root() -> Path:
    env = os.environ.get("ABLETON_SAMPLES_ROOT")
    if env:
        return Path(env)
    personal_lap = Path("F:/Lap/Music")
    if personal_lap.exists():
        return personal_lap
    user_docs = Path(os.environ.get("USERPROFILE", "C:/Users/sasuk")) / "Documents" / "Ableton" / "User Library"
    if user_docs.exists():
        return user_docs
    return Path("C:/Users/sasuk/Documents/Ableton/User Library")

def get_personal_samples_roots() -> list[Path]:
    """Returns all detected personal sound directories on the user machine."""
    roots = []
    custom = os.environ.get("ABLETON_SAMPLES_ROOT")
    if custom and Path(custom).exists():
        roots.append(Path(custom))
    lap_music = Path("F:/Lap/Music")
    if lap_music.exists():
        roots.append(lap_music)
    lap_vocales = Path("F:/Lap/Music/Vocales")
    if lap_vocales.exists():
        roots.append(lap_vocales)
    user_docs = Path(os.environ.get("USERPROFILE", "C:/Users/sasuk")) / "Documents" / "Ableton" / "User Library"
    if user_docs.exists():
        roots.append(user_docs)
    if not roots:
        roots.append(default_samples_root())
    return roots


def default_manifest_path() -> Path:
    env = os.environ.get("ABLETON_SAMPLE_MANIFEST")
    if env:
        return Path(env)
    return Path(os.environ.get("USERPROFILE", "C:/Users/sasuk")) / ".ableton_mcp" / "library_index" / "manifest.parquet"
