# engine/sound_design/valhalla_vintage_verb/sanitizer.py
"""
Valhalla VintageVerb Sanitizer.

Auto-corrects out-of-bound parameters, resolves fuzzy mode and color aliases,
and eliminates spectral inversions to guarantee that every configuration is strictly valid.
"""

from typing import Dict, Any, Optional

from .model import VintageVerbModel
from .schema import ValhallaVintageVerbSchema, VintageVerbColor


class ValhallaVintageVerbSanitizer:
    """Sanitizes raw parameters and models to ensure compliance with Valhalla VintageVerb specifications."""

    MODE_ALIASES: Dict[str, str] = {
        "concert": "Concert Hall",
        "concerthall": "Concert Hall",
        "hall": "Concert Hall",
        "brighthall": "Bright Hall",
        "bright": "Bright Hall",
        "plate": "Plate",
        "room": "Room",
        "chamber": "Chamber",
        "random": "Random Space",
        "randomspace": "Random Space",
        "chorus": "Chorus Space",
        "chorusspace": "Chorus Space",
        "ambience": "Ambience",
        "ambient": "Ambience",
        "sanctuary": "Sanctuary",
        "dirtyhall": "Dirty Hall",
        "dirtyplate": "Dirty Plate",
        "smoothplate": "Smooth Plate",
        "smoothroom": "Smooth Room",
        "smoothrandom": "Smooth Random",
        "nonlin": "Nonlin",
        "gated": "Nonlin",
        "reverse": "Nonlin",
        "chaotichall": "Chaotic Hall",
        "chaoticchamber": "Chaotic Chamber",
        "chaoticneutral": "Chaotic Neutral",
        "cathedral": "Cathedral",
        "palace": "Palace",
        "chamber1979": "Chamber1979",
        "hall1984": "Hall1984",
    }

    COLOR_ALIASES: Dict[str, str] = {
        "70": "1970s",
        "70s": "1970s",
        "1970": "1970s",
        "1970s": "1970s",
        "80": "1980s",
        "80s": "1980s",
        "1980": "1980s",
        "1980s": "1980s",
        "now": "Now",
        "modern": "Now",
        "clean": "Now",
    }

    @classmethod
    def resolve_mode(cls, mode_input: Any) -> str:
        """Resolves fuzzy mode name or float to canonical mode name."""
        if isinstance(mode_input, (int, float)):
            return ValhallaVintageVerbSchema.float_to_mode(float(mode_input))
        if isinstance(mode_input, str):
            clean = mode_input.strip()
            # Direct match
            for m in ValhallaVintageVerbSchema.MODES:
                if m.lower() == clean.lower():
                    return m
            # Alias match
            clean_sub = clean.lower().replace(" ", "").replace("-", "").replace("_", "")
            if clean_sub in cls.MODE_ALIASES:
                return cls.MODE_ALIASES[clean_sub]
        return "Concert Hall"

    @classmethod
    def resolve_color(cls, color_input: Any) -> str:
        """Resolves fuzzy color name or float to canonical color name."""
        if isinstance(color_input, (int, float)):
            return ValhallaVintageVerbSchema.float_to_color(float(color_input))
        if isinstance(color_input, str):
            clean = color_input.strip().lower().replace(" ", "")
            for alias_key, target in cls.COLOR_ALIASES.items():
                if alias_key in clean:
                    return target
        return VintageVerbColor.COLOR_1980S.value

    @classmethod
    def sanitize(
        cls,
        model: VintageVerbModel,
        role: Optional[str] = None
    ) -> VintageVerbModel:
        """Sanitizes model fields in place, guaranteeing 100% validity."""
        # 1. Clamp all continuous parameters to [0.0, 1.0]
        model.mix = max(0.0, min(1.0, float(model.mix)))
        model.predelay = max(0.0, min(1.0, float(model.predelay)))
        model.decay = max(0.0, min(1.0, float(model.decay)))
        model.size = max(0.05, min(1.0, float(model.size)))  # Min size 0.05
        model.attack = max(0.0, min(1.0, float(model.attack)))
        model.bass_mult = max(0.0, min(1.0, float(model.bass_mult)))
        model.bass_xover = max(0.0, min(1.0, float(model.bass_xover)))
        model.high_shelf = max(0.0, min(1.0, float(model.high_shelf)))
        model.high_cut = max(0.10, min(1.0, float(model.high_cut)))
        model.low_cut = max(0.0, min(0.90, float(model.low_cut)))
        model.early_diffusion = max(0.0, min(1.0, float(model.early_diffusion)))
        model.late_diffusion = max(0.0, min(1.0, float(model.late_diffusion)))
        model.mod_rate = max(0.0, min(1.0, float(model.mod_rate)))
        model.mod_depth = max(0.0, min(1.0, float(model.mod_depth)))

        # 2. Spectral ordering: LowCut must be strictly < HighCut
        if model.low_cut >= model.high_cut:
            if model.low_cut >= 0.5:
                model.low_cut = 0.20
            model.high_cut = max(model.high_cut, model.low_cut + 0.15)

        # 3. Role-based anti-mud safety enforcement
        norm_role = str(role).strip().upper() if role else None
        if norm_role in ("DRUMS", "PERCUSSION", "BASS"):
            model.low_cut = max(0.08, model.low_cut)
            model.bass_mult = min(0.60, model.bass_mult)  # Avoid bloated bass decay
        elif norm_role in ("KEYS", "PIANO"):
            model.low_cut = max(0.05, model.low_cut)

        # 4. Mode and color validation
        model.mode_name = cls.resolve_mode(model.mode_name)
        model.color_name = cls.resolve_color(model.color_name)

        if not model.preset_name or not str(model.preset_name).strip():
            model.preset_name = "VintageVerb_Sanitized"

        return model
