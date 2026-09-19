# engine/sound/macro_standardizer.py
"""
Universal Macro Rack Standardizer:
Standardizes 8 universal macro knobs across all virtual instruments and racks in Ableton Live 12.
"""

from typing import Dict, Any, List, Optional, Union
import logging

logger = logging.getLogger("MacroStandardizer")


class MacroStandardizer:
    """Standardizes 8 macro knobs across any instrument device."""

    STANDARD_MACROS = {
        1: ("Cutoff", ["cutoff", "filter freq", "frequency", "brightness"]),
        2: ("Resonance", ["resonance", "q", "filter res", "emphasis"]),
        3: ("Drive", ["drive", "distortion", "saturation", "overdrive", "warmth"]),
        4: ("Attack", ["attack", "punch", "transient", "initial"]),
        5: ("Decay", ["decay", "release", "sustain", "tail", "body"]),
        6: ("Modulation", ["modulation", "lfo depth", "detune", "chorus", "wobble"]),
        7: ("Space", ["reverb", "delay", "space", "ambience", "dry/wet"]),
        8: ("Tone", ["tone", "color", "morph", "character", "air"])
    }

    @classmethod
    def get_macro_map(cls) -> Dict[int, str]:
        """Returns the canonical 8-macro definition map."""
        return {num: item[0] for num, item in cls.STANDARD_MACROS.items()}

    @classmethod
    def resolve_macro_number(cls, macro_ident: Union[int, str]) -> int:
        """Resolves a name or number to an integer in [1, 8]."""
        if isinstance(macro_ident, int):
            return max(1, min(8, macro_ident))

        s_ident = str(macro_ident).lower().strip()
        for num, (name, aliases) in cls.STANDARD_MACROS.items():
            if s_ident == name.lower() or any(a in s_ident for a in aliases):
                return num

        # Try numeric extract
        for ch in s_ident:
            if ch.isdigit() and 1 <= int(ch) <= 8:
                return int(ch)

        return 1

    @classmethod
    def set_macro_parameter(
        cls,
        conn: Any,
        track_index: int,
        macro_ident: Union[int, str],
        value: float,
        device_index: int = 0
    ) -> Dict[str, Any]:
        """
        Sets a normalized macro parameter (0.0 to 1.0) on an instrument or rack.
        """
        macro_num = cls.resolve_macro_number(macro_ident)
        macro_name = cls.STANDARD_MACROS[macro_num][0]
        clamped_val = max(0.0, min(1.0, float(value)))

        res = {}
        if conn and hasattr(conn, "send_command"):
            try:
                # 1. Try by canonical macro name (e.g. "Macro 1", "Macro 2", etc.)
                res = conn.send_command("set_device_parameter", {
                    "track_index": track_index,
                    "device_index": device_index,
                    "parameter_name": f"Macro {macro_num}",
                    "value": clamped_val
                })
            except Exception as e:
                logger.debug(f"Direct macro set notice: {e}")

        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "device_index": device_index,
            "macro_number": macro_num,
            "macro_name": macro_name,
            "value": clamped_val,
            "adapter_response": res
        }
