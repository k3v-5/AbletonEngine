# engine/sound_design/valhalla_vintage_verb/mode_selector.py
"""
Valhalla VintageVerb Intelligent Mode & Acoustic Selector.

Selects the psychoacoustically optimal reverb algorithm and color era
for any instrument role, calculates tempo-synced pre-delays and decays,
and molds studio-grade acoustic parameters deterministically.
"""

from typing import Dict, Any, Optional, Tuple

from .model import VintageVerbModel
from .schema import ValhallaVintageVerbSchema, VintageVerbColor
from .sanitizer import ValhallaVintageVerbSanitizer


class VintageVerbModeSelector:
    """Intelligent selector and acoustic builder for Valhalla VintageVerb."""

    ROLE_ALGORITHM_PREFERENCES: Dict[str, Tuple[str, str]] = {
        "DRUMS": ("Plate", VintageVerbColor.COLOR_1980S.value),
        "PERCUSSION": ("Room", VintageVerbColor.COLOR_1980S.value),
        "SNARE": ("Plate", VintageVerbColor.COLOR_1980S.value),
        "VOCALS": ("Smooth Plate", VintageVerbColor.COLOR_1980S.value),
        "VOICE": ("Smooth Plate", VintageVerbColor.COLOR_1980S.value),
        "KEYS": ("Chamber", VintageVerbColor.COLOR_1980S.value),
        "PIANO": ("Smooth Room", VintageVerbColor.COLOR_NOW.value),
        "GUITAR": ("Concert Hall", VintageVerbColor.COLOR_1980S.value),
        "LEAD": ("Bright Hall", VintageVerbColor.COLOR_NOW.value),
        "PAD": ("Cathedral", VintageVerbColor.COLOR_1980S.value),
        "STRINGS": ("Palace", VintageVerbColor.COLOR_1970S.value),
        "BASS": ("Ambience", VintageVerbColor.COLOR_1980S.value),
        "FX": ("Chaotic Hall", VintageVerbColor.COLOR_1970S.value),
    }

    @classmethod
    def recommend_mode_and_color_for_role(
        cls,
        role: str,
        style_hint: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Returns the optimal (algorithm_mode, color_era) pair for the given musical role.
        """
        norm_role = str(role).strip().upper()

        if style_hint:
            hint = style_hint.strip().lower()
            if "vintage" in hint or "retro" in hint or "70" in hint:
                return ("Dirty Hall", VintageVerbColor.COLOR_1970S.value)
            elif "gated" in hint or "80" in hint or "phil collins" in hint:
                return ("Nonlin", VintageVerbColor.COLOR_1980S.value)
            elif "modern" in hint or "transparent" in hint or "clean" in hint:
                return ("Smooth Plate", VintageVerbColor.COLOR_NOW.value)
            elif "epic" in hint or "cathedral" in hint or "huge" in hint:
                return ("Cathedral", VintageVerbColor.COLOR_1980S.value)

        return cls.ROLE_ALGORITHM_PREFERENCES.get(
            norm_role,
            ("Concert Hall", VintageVerbColor.COLOR_1980S.value)
        )

    @classmethod
    def calculate_haas_pre_delay_ms(cls, bpm: float, role: str) -> float:
        """
        Calculates protective pre-delay in ms to preserve dry transient attack.
        Tight for drums, moderate for keys, upfront for vocals.
        """
        norm_role = str(role).strip().upper()
        if norm_role in ("DRUMS", "PERCUSSION", "BASS", "SNARE"):
            return 8.0  # Tight 8ms
        elif norm_role in ("LEAD", "VOCALS", "VOICE", "GUITAR"):
            return 32.0  # 32ms upfront vocal clarity
        elif norm_role in ("KEYS", "PIANO"):
            return 18.0  # 18ms natural acoustic chamber
        else:
            # 45ms swell for ambient pads
            return 45.0

    @classmethod
    def build_role_preset(
        cls,
        preset_name: str,
        role: str,
        bpm: float = 120.0,
        applied_params: Optional[Dict[str, Any]] = None
    ) -> VintageVerbModel:
        """
        Builds a complete, acoustically calibrated VintageVerbModel molded
        for the given role, tempo, and optional parameter overrides.
        """
        applied = applied_params or {}
        norm_role = str(role).strip().upper()

        rec_mode, rec_color = cls.recommend_mode_and_color_for_role(norm_role)

        # 1. Resolve Mode & Color
        user_mode = applied.get("Mode")
        if user_mode is not None:
            final_mode = ValhallaVintageVerbSanitizer.resolve_mode(user_mode)
        else:
            final_mode = rec_mode

        user_color = applied.get("ColorMode") or applied.get("Color")
        if user_color is not None:
            final_color = ValhallaVintageVerbSanitizer.resolve_color(user_color)
        else:
            final_color = rec_color

        # 2. Timing and Decay
        calc_predelay_ms = cls.calculate_haas_pre_delay_ms(bpm, norm_role)
        default_predelay_norm = ValhallaVintageVerbSchema.ms_to_predelay(calc_predelay_ms)

        # Role-based acoustic baseline defaults
        if norm_role in ("DRUMS", "PERCUSSION", "SNARE"):
            base_mix = 0.18
            base_decay = ValhallaVintageVerbSchema.seconds_to_decay(1.2)
            base_size = 0.40
            base_lowcut = 0.22  # High HPF to keep kick clean
            base_highcut = 0.60
            base_bassmult = 0.35  # Short bass decay
        elif norm_role in ("VOCALS", "VOICE"):
            base_mix = 0.22
            base_decay = ValhallaVintageVerbSchema.seconds_to_decay(2.6)
            base_size = 0.65
            base_lowcut = 0.18
            base_highcut = 0.70
            base_bassmult = 0.45
        elif norm_role in ("KEYS", "PIANO"):
            base_mix = 0.20
            base_decay = ValhallaVintageVerbSchema.seconds_to_decay(2.2)
            base_size = 0.55
            base_lowcut = 0.15
            base_highcut = 0.65
            base_bassmult = 0.50
        elif norm_role in ("PAD", "STRINGS"):
            base_mix = 0.35
            base_decay = ValhallaVintageVerbSchema.seconds_to_decay(5.5)
            base_size = 0.85
            base_lowcut = 0.12
            base_highcut = 0.75
            base_bassmult = 0.60
        elif norm_role in ("LEAD", "GUITAR"):
            base_mix = 0.24
            base_decay = ValhallaVintageVerbSchema.seconds_to_decay(2.8)
            base_size = 0.60
            base_lowcut = 0.16
            base_highcut = 0.68
            base_bassmult = 0.45
        else:
            base_mix = 0.20
            base_decay = 0.30
            base_size = 0.50
            base_lowcut = 0.15
            base_highcut = 0.65
            base_bassmult = 0.50

        # Construct model with overrides
        model = VintageVerbModel(
            preset_name=preset_name,
            mix=float(applied.get("Mix", base_mix)),
            predelay=float(applied.get("PreDelay", default_predelay_norm)),
            decay=float(applied.get("Decay", base_decay)),
            size=float(applied.get("Size", base_size)),
            attack=float(applied.get("Attack", 0.0)),
            bass_mult=float(applied.get("BassMult", base_bassmult)),
            bass_xover=float(applied.get("BassXover", 0.50)),
            high_shelf=float(applied.get("HighShelf", 0.0)),
            high_cut=float(applied.get("HighCut", base_highcut)),
            low_cut=float(applied.get("LowCut", base_lowcut)),
            early_diffusion=float(applied.get("EarlyDiffusion", 1.0)),
            late_diffusion=float(applied.get("LateDiffusion", 1.0)),
            mod_rate=float(applied.get("ModRate", 0.25)),
            mod_depth=float(applied.get("ModDepth", 0.50)),
            mode=ValhallaVintageVerbSchema.mode_to_float(final_mode),
            color_mode=ValhallaVintageVerbSchema.color_to_float(final_color),
        )

        ValhallaVintageVerbSanitizer.sanitize(model, role=norm_role)
        return model
