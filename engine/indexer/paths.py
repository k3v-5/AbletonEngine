# Paths for Ableton sample library and manifest storage
from pathlib import Path
import os

def default_samples_root() -> Path:
    env = os.environ.get("ABLETON_SAMPLES_ROOT")
    if env:
        return Path(env)
    user_docs = Path(os.environ.get("USERPROFILE", "C:/Users/sasuk")) / "Documents" / "Ableton" / "User Library"
    if user_docs.exists():
        return user_docs
    return Path("C:/Users/sasuk/Documents/Ableton/User Library")

def default_manifest_path() -> Path:
    env = os.environ.get("ABLETON_SAMPLE_MANIFEST")
    if env:
        return Path(env)
    return Path(os.environ.get("USERPROFILE", "C:/Users/sasuk")) / ".ableton_mcp" / "library_index" / "manifest.parquet"
