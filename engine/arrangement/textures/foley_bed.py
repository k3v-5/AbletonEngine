# engine/arrangement/textures/foley_bed.py
"""
Atmospheric Foley Bed Generator:
Generates and manages subliminal organic background textures (vinyl crackle, rain diffuse, tape hiss).
Calibrated strictly to subliminal gain staging (-28 dBFS to -34 dBFS) with dynamic sidechain ducking,
adding analog depth, spatial realism, and emotional warmth to virtual instrument productions.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("AtmosphericFoleyBedGenerator")


class AtmosphericFoleyBedGenerator:
    """
    Coordinates subliminal texture bed synthesis and dynamic sidechain routing.
    """

    FOLEY_PRESETS = {
        "VINYL_WARMTH": {
            "name": "Vintage Vinyl Crackle & Dust",
            "base_gain_dbfs": -30.0,
            "hp_filter_hz": 120.0,
            "lp_filter_hz": 9500.0,
            "stereo_width": 1.20,
            "ducking_depth_db": -2.5,
            "best_for": ["LOFI", "BOOM_BAP", "R&B", "POP", "BALLAD"]
        },
        "RAIN_DIFFUSE": {
            "name": "Diffuse Window Rain & Urban Fog",
            "base_gain_dbfs": -32.0,
            "hp_filter_hz": 200.0,
            "lp_filter_hz": 8000.0,
            "stereo_width": 1.45,
            "ducking_depth_db": -3.0,
            "best_for": ["TRAP", "DRILL", "MELODIC_TECHNO", "CHILL", "AMBIENT"]
        },
        "TAPE_CONSOLE_HISS": {
            "name": "1/2-inch Analog Tape & Console Room",
            "base_gain_dbfs": -34.0,
            "hp_filter_hz": 150.0,
            "lp_filter_hz": 11000.0,
            "stereo_width": 1.10,
            "ducking_depth_db": -2.0,
            "best_for": ["SYNTHWAVE", "INDIE_ROCK", "DISCO", "HOUSE", "DOWNTEMPO"]
        },
        "FOREST_RUSTLE": {
            "name": "Forest Rustle & Distant Acoustic Air",
            "base_gain_dbfs": -33.0,
            "hp_filter_hz": 250.0,
            "lp_filter_hz": 8500.0,
            "stereo_width": 1.35,
            "ducking_depth_db": -2.5,
            "best_for": ["AFROBEAT", "REGGAETON", "ORGANIC_HOUSE", "FOLK"]
        }
    }

    @classmethod
    def resolve_preset_by_genre(cls, genre: str = "POP") -> str:
        """Determines best foley preset match based on song genre."""
        g_up = str(genre or "POP").upper()
        for preset_key, cfg in cls.FOLEY_PRESETS.items():
            if any(b in g_up for b in cfg["best_for"]):
                return preset_key
        return "VINYL_WARMTH"

    @classmethod
    def generate_foley_bed_profile(
        cls,
        genre: str = "POP",
        preset_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates calibrated atmospheric foley bed specification.
        """
        chosen_key = preset_key if preset_key in cls.FOLEY_PRESETS else cls.resolve_preset_by_genre(genre)
        preset = cls.FOLEY_PRESETS[chosen_key]

        return {
            "status": "FOLEY_BED_GENERATED",
            "preset_key": chosen_key,
            "preset": chosen_key,
            "preset_name": preset["name"],
            "base_gain_dbfs": preset["base_gain_dbfs"],
            "target_level_dbfs": preset["base_gain_dbfs"],
            "duck_depth_db": preset["ducking_depth_db"],
            "duck_source_role": ["KICK", "VOCALS"],
            "eq_filter": {
                "high_pass_hz": preset["hp_filter_hz"],
                "low_pass_hz": preset["lp_filter_hz"]
            },
            "stereo_width": preset["stereo_width"],
            "sidechain_ducking": {
                "active": True,
                "duck_depth_db": preset["ducking_depth_db"],
                "trigger_sources": ["KICK", "VOCALS"],
                "attack_ms": 10.0,
                "release_ms": 180.0
            },
            "recommended_track_name": "Texture Bed (Foley Subliminal)"
        }

    @classmethod
    def generate_foley_bed_prescription(
        cls,
        genre: str = "POP",
        target_level_dbfs: float = -30.0,
        preset_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convenience method generating foley profile with target gain staging."""
        res = cls.generate_foley_bed_profile(genre=genre, preset_key=preset_key)
        res["status"] = "FOLEY_BED_PRESCRIBED"
        res["target_level_dbfs"] = target_level_dbfs
        res["base_gain_dbfs"] = target_level_dbfs
        return res

    @classmethod
    def render_markdown_summary(cls, result: Dict[str, Any]) -> str:
        """Renders clear, human-readable markdown summary."""
        return (
            "🍂 **Inyector de Texturas Atmosféricas y Capas Foley Subliminales (Foley Bed)**\n\n"
            f"• **Textura Seleccionada:** `{result.get('preset_name', 'Vintage Vinyl')}`\n"
            f"• **Ganancia Subliminal:** `{result.get('base_gain_dbfs', -30.0):.1f} dBFS` (Presencia inconsciente de calidez)\n"
            f"• **Filtrado Espectral:** HPF {result.get('eq_filter', {}).get('high_pass_hz', 120)} Hz | LPF {result.get('eq_filter', {}).get('low_pass_hz', 9500)} Hz\n"
            f"• **Sidechain Ducking:** -{abs(result.get('sidechain_ducking', {}).get('duck_depth_db', 2.5))} dB ducking ante Bombo y Voz líder\n"
            "• **Beneficio:** Elimina la esterilidad digital aportando profundidad y pegamento orgánico analógico."
        )
