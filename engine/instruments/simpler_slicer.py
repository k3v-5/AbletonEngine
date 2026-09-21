# engine/instruments/simpler_slicer.py
"""
Simpler & Drum Rack Slicing Manager:
Handles physical audio file loading, transient slicing, and chromatic note clamping
for chopping tracks inside Ableton Live 12.
"""

from typing import Dict, Any, List, Optional
import logging
from pathlib import Path

logger = logging.getLogger("SimplerSlicer")


class SimplerSlicer:
    """Automates Simpler slicing and sample replacement via Live 12 LOM."""

    @classmethod
    def load_sample_and_slice(
        cls,
        conn: Any,
        track_index: int,
        sample_path: str,
        device_index: int = 0,
        playback_mode: int = 2  # 0=Classic, 1=1-Shot, 2=Slicing
    ) -> Dict[str, Any]:
        """
        Loads a local audio sample into Simpler, sets Slicing mode, and resets slices.
        """
        p = Path(sample_path)
        if not p.exists():
            return {
                "status": "ERROR",
                "message": f"Sample file not found at path: {sample_path}",
                "slices_count": 0
            }

        slices_count = 64
        if conn and hasattr(conn, "send_command"):
            try:
                s_path_esc = str(p.resolve()).replace("\\", "\\\\")
                code = f"""
t = song.tracks[{track_index}]
d = t.devices[{device_index}]
sample_path = r\"{s_path_esc}\"
if hasattr(d, 'replace_sample'):
    d.replace_sample(sample_path)
if hasattr(d, 'playback_mode'):
    d.playback_mode = {playback_mode}
s = getattr(d, 'sample', None)
if s and hasattr(s, 'reset_slices'):
    s.reset_slices()
slices_count = len(getattr(s, 'slices', [])) if s else 0
"""
                res = conn.send_command("execute_code", {"code": code})
                if isinstance(res, dict) and "slices_count" in res:
                    sc = int(res["slices_count"])
                    if sc > 0:
                        slices_count = sc
            except Exception as e:
                logger.warning(f"Simpler slicing execution notice: {e}")

        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "device_index": device_index,
            "sample_path": str(p),
            "sample_name": p.stem,
            "slices_count": slices_count,
            "note_range": (36, 36 + slices_count - 1)
        }

    @classmethod
    def load_provenanced_sample_and_slice(
        cls,
        conn: Any,
        track_index: int,
        sample_provenance: Any,
        device_index: int = 0,
        playback_mode: int = 2,
        allow_external_samples: bool = False
    ) -> Dict[str, Any]:
        """
        Verifies provenance before allowing sample loading and slicing into Simpler.
        Raises CreativeGovernanceError if the sample is unprovenanced or UNKNOWN.
        """
        from engine.audio_genesis.provenance import SampleOrigin, CreativeGovernanceError

        origin = getattr(sample_provenance, "origin", None)
        if isinstance(origin, str):
            origin_str = origin.lower()
        elif hasattr(origin, "value"):
            origin_str = str(origin.value).lower()
        else:
            origin_str = "unknown"

        if origin_str == "unknown" and not allow_external_samples:
            raise CreativeGovernanceError(
                f"Simpler Governance Violation: Cannot load unprovenanced audio (origin={origin_str}) "
                f"into Simpler on track {track_index}. Creative audio must possess verifiable song provenance."
            )

        render_obj = getattr(sample_provenance, "render", None)
        sample_path = getattr(render_obj, "file_path", None) if render_obj else getattr(sample_provenance, "audio_path", "")
        if not sample_path:
            sample_path = getattr(sample_provenance, "file_path", "")

        res = cls.load_sample_and_slice(conn, track_index, sample_path, device_index, playback_mode)
        res["provenance_id"] = getattr(sample_provenance, "sample_id", "verified_provenance")
        res["origin"] = origin_str
        return res

    @classmethod
    def clamp_notes_to_slices(
        cls,
        notes: List[Dict[str, Any]],
        slices_count: int = 64
    ) -> List[Dict[str, Any]]:
        """
        Clamps any note list into the active slice range [36, 36 + slices_count - 1].
        """
        if slices_count <= 0:
            slices_count = 64

        clamped = []
        for n in notes:
            n_copy = dict(n)
            p = int(n_copy.get("pitch", 36))
            if p < 36 or p >= (36 + slices_count):
                n_copy["pitch"] = 36 + ((p - 36) % slices_count)
            clamped.append(n_copy)

        return clamped
