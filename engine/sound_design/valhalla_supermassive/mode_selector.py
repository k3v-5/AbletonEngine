# engine/sound_design/valhalla_supermassive/mode_selector.py
"""
Valhalla Supermassive Psychoacoustic Mode Selector & BPM-Aligned Engine.

Maps the 22 proprietary algorithmic modes to musical roles and acoustic functions:
- PERCUSSIVE_TIGHT: Lyra, Capricorn, Gemini (short attack, discrete echoes, clean room)
- SOLO_DEFINITION: Centaurus, Hydra, Virgo (sustained melodic halo without wash)
- LUSH_ORCHESTRAL: Andromeda, Cassiopeia, Triangulum (silky diffusion, concert tails)
- INFINITE_COSMIC: Great Annihilator, Sagittarius, Large Magellanic Cloud (ambient drones, swells)
- CELESTIAL_SHIMMER: Pleiades, Sirius (sparkling multi-tap reflections, pitch shimmer)

Calculates mathematical pre-delays and Haas offsets based on track tempo (BPM).
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import logging

from .schema import ValhallaSupermassiveSchema
from .model import SupermassiveModel
from .builder import SupermassiveBuilder

logger = logging.getLogger("SupermassiveModeSelector")


class SupermassiveModeSelector:
    """Intelligent mode selector and tempo-aligned preset architect for Valhalla Supermassive."""

    ROLE_MODE_RECOMMENDATIONS: Dict[str, List[str]] = {
        "DRUMS": ["Lyra", "Capricorn", "Gemini"],
        "PERCUSSION": ["Lyra", "Capricorn", "Gemini"],
        "BASS": ["Gemini", "Lyra", "Capricorn"],
        "KEYS": ["Andromeda", "Cassiopeia", "Lyra", "Hydra"],
        "PIANO": ["Cassiopeia", "Andromeda", "Virgo"],
        "E_PIANO": ["Andromeda", "Hydra", "Lyra"],
        "GUITAR": ["Lyra", "Centaurus", "Hydra"],
        "LEAD": ["Centaurus", "Hydra", "Cassiopeia", "Virgo"],
        "PAD": ["Great Annihilator", "Sagittarius", "Andromeda", "Large Magellanic Cloud"],
        "STRINGS": ["Andromeda", "Cassiopeia", "Triangulum"],
        "VOCALS": ["Virgo", "Centaurus", "Andromeda", "Gemini"],
        "FX": ["Pleiades", "Sirius", "Great Annihilator"],
        "TEXTURE_FOLEY": ["Pleiades", "Sirius", "Andromeda"],
    }

    DIVISION_MULTIPLIERS: Dict[str, float] = {
        "1/1": 4.0,
        "1/2": 2.0,
        "1/4": 1.0,
        "1/8": 0.5,
        "1/16": 0.25,
        "1/32": 0.125,
    }

    SYNC_TYPE_FACTORS: Dict[str, float] = {
        "straight": 1.0,
        "dotted": 1.5,
        "triplet": 2.0 / 3.0,
    }

    @classmethod
    def recommend_mode_for_role(
        cls,
        role: str,
        style_hint: str = "balanced"
    ) -> str:
        """
        Selects the optimal mode among the 22 algorithms based on role and style.
        Style hints: 'tight', 'balanced', 'lush', 'infinite', 'shimmer'.
        """
        norm_role = str(role).strip().upper()
        candidates = cls.ROLE_MODE_RECOMMENDATIONS.get(norm_role, ["Andromeda", "Cassiopeia", "Lyra"])

        if style_hint == "tight":
            for m in ["Lyra", "Capricorn", "Gemini", "Virgo"]:
                if m in candidates or m in ValhallaSupermassiveSchema.MODE_NAMES:
                    return m
        elif style_hint == "infinite":
            for m in ["Great Annihilator", "Sagittarius", "Large Magellanic Cloud"]:
                if m in candidates or m in ValhallaSupermassiveSchema.MODE_NAMES:
                    return m
        elif style_hint == "shimmer":
            for m in ["Pleiades", "Sirius"]:
                if m in candidates or m in ValhallaSupermassiveSchema.MODE_NAMES:
                    return m
        elif style_hint == "lush":
            for m in ["Andromeda", "Cassiopeia", "Triangulum"]:
                if m in candidates or m in ValhallaSupermassiveSchema.MODE_NAMES:
                    return m

        return candidates[0] if candidates else "Andromeda"

    @classmethod
    def calculate_bpm_delay_ms(
        cls,
        bpm: float,
        division: str = "1/8",
        sync_type: str = "straight"
    ) -> float:
        """
        Calculates exact delay time in milliseconds matched to song tempo.
        Formula: (60,000 / BPM) * division_mult * sync_factor
        """
        safe_bpm = max(20.0, min(300.0, float(bpm or 120.0)))
        div_mult = cls.DIVISION_MULTIPLIERS.get(division, 0.5)
        sync_factor = cls.SYNC_TYPE_FACTORS.get(sync_type, 1.0)

        ms = (60000.0 / safe_bpm) * div_mult * sync_factor
        return round(ms, 2)

    @classmethod
    def calculate_haas_pre_delay(cls, bpm: float, role: str) -> float:
        """
        Calculates protective pre-delay (10ms - 90ms) based on role and tempo.
        Protects dry transient attack from being smeared by early reflections.
        """
        norm_role = str(role).strip().upper()
        if norm_role in ("DRUMS", "PERCUSSION", "BASS"):
            # Tight 12ms pre-delay
            return 12.0
        elif norm_role in ("LEAD", "VOCALS", "GUITAR"):
            # 28ms Haas pre-delay
            return 28.0
        elif norm_role in ("KEYS", "PIANO"):
            # 20ms pre-delay
            return 20.0
        else:
            # Lush 50ms - 80ms slow swell
            ms_16th = (60000.0 / max(40.0, bpm)) * 0.25
            return round(min(80.0, max(30.0, ms_16th * 0.40)), 2)

    @classmethod
    def build_role_preset(
        cls,
        preset_name: str,
        role: str,
        bpm: float = 120.0,
        applied_params: Optional[Dict[str, Any]] = None
    ) -> SupermassiveModel:
        """
        Constructs a complete, acoustically calibrated SupermassiveModel
        molded for the specific instrument role and tempo.
        """
        applied = applied_params or {}
        norm_role = str(role).strip().upper()

        # 1. Mode resolution
        user_mode = applied.get("Mode")
        if user_mode is not None:
            if isinstance(user_mode, str) and user_mode in ValhallaSupermassiveSchema.MODE_NAMES:
                chosen_mode = user_mode
            elif isinstance(user_mode, (int, float)):
                idx = int(round(float(user_mode) * 21.0))
                chosen_mode = ValhallaSupermassiveSchema.MODE_NAMES[min(max(0, idx), 21)]
            else:
                chosen_mode = cls.recommend_mode_for_role(norm_role)
        else:
            chosen_mode = cls.recommend_mode_for_role(norm_role)

        # 2. Delay sync & timing
        is_synced = bool(float(applied.get("DelaySync", 1.0)) >= 0.5)
        division = "1/8"
        sync_type = "straight"

        if norm_role in ("PAD", "STRINGS"):
            division = "1/4"
            sync_type = "dotted"
        elif norm_role in ("LEAD", "GUITAR"):
            division = "1/8"
            sync_type = "dotted"
        elif norm_role in ("DRUMS", "PERCUSSION"):
            division = "1/16"
            sync_type = "straight"

        # 3. Acoustic parameters molded by role
        default_mix = 0.22
        default_feedback = 0.50
        default_lowcut = 0.18
        default_highcut = 0.70
        default_density = 0.60
        default_warp = 0.50

        if norm_role in ("BASS", "808"):
            default_mix = 0.12
            default_feedback = 0.30
            default_lowcut = 0.35  # Extreme low cut protection for bass
            default_highcut = 0.50
        elif norm_role in ("PAD", "STRINGS"):
            default_mix = 0.40
            default_feedback = 0.75
            default_lowcut = 0.12
            default_highcut = 0.85
            default_density = 0.85
            default_warp = 0.65
        elif norm_role in ("DRUMS", "PERCUSSION"):
            default_mix = 0.15
            default_feedback = 0.25
            default_density = 0.30
            default_lowcut = 0.25

        mix_val = float(applied.get("Mix", default_mix))
        feedback_val = min(0.95, float(applied.get("Feedback", default_feedback)))
        lowcut_val = max(0.05, float(applied.get("LowCut", default_lowcut)))
        highcut_val = float(applied.get("HighCut", default_highcut))
        density_val = float(applied.get("Density", default_density))
        warp_val = float(applied.get("Warp", default_warp))

        builder = (
            SupermassiveBuilder(preset_name=preset_name)
            .with_mode(chosen_mode)
            .with_mix(mix_val)
            .with_decay(feedback=feedback_val, density=density_val, warp=warp_val)
            .with_tone(low_cut=lowcut_val, high_cut=highcut_val)
            .with_modulation(rate=0.35, depth=0.45)
            .with_width(1.0)
        )

        if is_synced:
            builder.with_synced_delay(division=division, sync_type=sync_type)
        else:
            delay_ms = cls.calculate_bpm_delay_ms(bpm=bpm, division=division, sync_type=sync_type)
            builder.with_free_delay(delay_ms=delay_ms / 1000.0)

        return builder.build()
