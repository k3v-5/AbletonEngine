# engine/session/color_palette.py
"""
Unified Track & Clip Visual Color Palette:
Applies coherent, professional color schemes across tracks and clips in Ableton Live 12
based on acoustic role standards.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("ColorPalette")


class ColorPaletteManager:
    """Assigns standardized Live 12 color indices to tracks and clips."""

    # Ableton Live 12 standard palette color indices (0-69)
    ROLE_COLOR_INDICES: Dict[str, int] = {
        "DRUMS": 60,       # Vibrant Orange
        "PERCUSSION": 59,  # Coral / Rust
        "BASS": 13,        # Bright Amber Yellow
        "808": 14,         # Gold / Ochre
        "LEAD": 27,        # Cyan / Electric Blue
        "SYNTH": 28,       # Sky Blue
        "KEYS": 18,        # Emerald Green
        "PIANO": 19,       # Mint Green
        "GUITAR": 20,      # Olive / Sage
        "PAD": 44,         # Deep Violet / Purple
        "STRINGS": 45,     # Indigo / Lavender
        "VOCALS": 49,      # Hot Pink / Magenta
        "FX": 69,          # Crisp White / Silver
        "BUS": 68          # Neutral Charcoal Grey
    }

    @classmethod
    def get_role_color_index(cls, role: str) -> int:
        """Returns the canonical color index for an acoustic role."""
        role_upper = str(role).upper()
        return cls.ROLE_COLOR_INDICES.get(role_upper, 27)

    @classmethod
    def apply_role_colors_to_session(
        cls,
        conn: Any,
        tracks: List[Dict[str, Any]],
        sections_count: int = 8
    ) -> Dict[str, Any]:
        """
        Applies color coding to every track and its clips directly inside Live 12.
        """
        colored_tracks = []
        if conn and hasattr(conn, "send_command"):
            for trk in tracks:
                t_idx = trk.get("index", 0)
                role = trk.get("role", "OTHER")
                c_idx = cls.get_role_color_index(role)

                # Set color on track in Live via execute_code or direct command
                try:
                    code = f"""
t = song.tracks[{t_idx}]
if hasattr(t, 'color_index'):
    t.color_index = {c_idx}
for c_slot in t.clip_slots:
    if c_slot.has_clip and hasattr(c_slot.clip, 'color_index'):
        c_slot.clip.color_index = {c_idx}
"""
                    conn.send_command("execute_code", {"code": code})
                    trk["color_index"] = c_idx
                    colored_tracks.append({"track_index": t_idx, "role": role, "color_index": c_idx})
                except Exception as e:
                    logger.debug(f"Color application notice on track {t_idx}: {e}")

        return {
            "status": "SUCCESS",
            "tracks_colored": len(colored_tracks),
            "details": colored_tracks
        }
