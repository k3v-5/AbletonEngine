# engine/mix/space_ducking.py
"""
Dynamic Space Ducker (Reverbs & Delays Duckeados Inteligentes):
Solves the acoustic conflict where big wet reverbs and delays drown out the lead vocals or solo instruments.
- Ducks the Reverb/Delay wet return track by -2.0 dB to -5.0 dB while the dry voice/lead is playing.
- When the dry phrase ends, the compressor releases smoothly (250 ms to 480 ms), allowing the reverb tail
  to 'bloom' / expand into the silence.
- Keeps vocals in-your-face, dry, and intimate during lyrics, with a massive cinematic space in pauses.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger("DynamicSpaceDucker")


class SpaceDuckingMode(str, Enum):
    TRANSPARENT = "TRANSPARENT"                    # -2.0 dB duck, 250ms release. Transparent, gentle wash.
    COMMERCIAL_STANDARD = "COMMERCIAL_STANDARD"    # -3.5 dB duck, 350ms release. Modern radio pop/trap standard.
    DEEP_BLOOM = "DEEP_BLOOM"                      # -5.0 dB duck, 480ms release. High contrast, dramatic ballads & R&B.


class DynamicSpaceDucker:
    """Calculates ducking envelopes and configures Ableton Live sidechain on space returns."""

    RECIPES: Dict[SpaceDuckingMode, Dict[str, Any]] = {
        SpaceDuckingMode.TRANSPARENT: {
            "mode": "TRANSPARENT",
            "name": "Sutil Transparente",
            "duck_amount_db": -2.0,
            "attack_ms": 5.0,
            "release_ms": 250.0,
            "ratio": 2.5,
            "threshold_db": -26.0,
            "description": "Atenuación transparente que mantiene el balance sin efecto bombeo audible."
        },
        SpaceDuckingMode.COMMERCIAL_STANDARD: {
            "mode": "COMMERCIAL_STANDARD",
            "name": "Comercial Estándar",
            "duck_amount_db": -3.5,
            "attack_ms": 4.0,
            "release_ms": 350.0,
            "ratio": 3.5,
            "threshold_db": -24.0,
            "description": "Voz in-your-face y articulada con florecimiento atmosférico natural en cada respiración."
        },
        SpaceDuckingMode.DEEP_BLOOM: {
            "mode": "DEEP_BLOOM",
            "name": "Florecimiento Profundo (Deep Bloom)",
            "duck_amount_db": -5.0,
            "attack_ms": 3.0,
            "release_ms": 480.0,
            "ratio": 4.0,
            "threshold_db": -22.0,
            "description": "Contraste dramático: sequedad íntima durante la frase y explosión espacial expansiva al callar."
        }
    }

    @classmethod
    def get_recipe(cls, mode: SpaceDuckingMode = SpaceDuckingMode.COMMERCIAL_STANDARD) -> Dict[str, Any]:
        """Returns the calibration recipe for a given space ducking mode."""
        return cls.RECIPES.get(mode, cls.RECIPES[SpaceDuckingMode.COMMERCIAL_STANDARD])

    @classmethod
    def calculate_space_ducking_envelope(
        cls,
        vocal_ranges_beats: List[Tuple[float, float]],
        song_length_beats: float,
        mode: SpaceDuckingMode = SpaceDuckingMode.COMMERCIAL_STANDARD,
        tempo: float = 120.0
    ) -> List[Dict[str, float]]:
        """
        Generates volume automation breakpoints for a Utility/Gain device on the Reverb return.
        - Value = 1.0 (0 dB / unity) during silences/pauses (reverb blooms).
        - Value = duck_factor (-2 to -5 dB) while vocal phrase is active.
        """
        recipe = cls.get_recipe(mode)
        duck_db = recipe["duck_amount_db"]
        duck_factor = 10.0 ** (duck_db / 20.0)

        ms_per_beat = (60.0 / tempo) * 1000.0
        beats_per_ms = 1.0 / ms_per_beat

        attack_beats = recipe["attack_ms"] * beats_per_ms
        release_beats = recipe["release_ms"] * beats_per_ms

        points: List[Dict[str, float]] = []
        # Initial point at 0.0 beats (unity gain)
        points.append({"time": 0.0, "value": 1.0, "gain_db": 0.0})

        for start_b, end_b in vocal_ranges_beats:
            if start_b >= song_length_beats:
                break

            # 1. Approach to vocal onset: drops from unity to ducked level
            duck_start = max(0.0, start_b)
            duck_onset = min(song_length_beats, duck_start + attack_beats)
            
            if points and (duck_start - points[-1]["time"]) > 0.05:
                points.append({"time": round(duck_start, 3), "value": 1.0, "gain_db": 0.0})

            points.append({"time": round(duck_onset, 3), "value": round(duck_factor, 3), "gain_db": duck_db})

            # 2. End of vocal phrase: hold ducked until end_b, then bloom
            phrase_end = min(song_length_beats, end_b)
            bloom_end = min(song_length_beats, phrase_end + release_beats)

            points.append({"time": round(phrase_end, 3), "value": round(duck_factor, 3), "gain_db": duck_db})
            points.append({"time": round(bloom_end, 3), "value": 1.0, "gain_db": 0.0})

        # Final guard point
        if points and points[-1]["time"] < song_length_beats:
            points.append({"time": round(song_length_beats, 3), "value": 1.0, "gain_db": 0.0})

        return points

    @classmethod
    def configure_space_ducking_device(
        cls,
        conn: Any,
        reverb_track_index: int,
        vocal_track_index: int,
        mode: SpaceDuckingMode = SpaceDuckingMode.COMMERCIAL_STANDARD
    ) -> Dict[str, Any]:
        """
        Configures Compressor or Utility sidechain on a return or bus track in Live.
        Preserves non-destructive routing.
        """
        recipe = cls.get_recipe(mode)

        if conn is None or not hasattr(conn, "send_command"):
            return {
                "status": "SIMULATED",
                "reverb_track_index": reverb_track_index,
                "vocal_track_index": vocal_track_index,
                "recipe": recipe
            }

        try:
            from engine.mix.sidechain_manager import SidechainManager
            comp_res = SidechainManager.find_or_load_compressor(conn, reverb_track_index)
            d_idx = comp_res.get("device_index", 0)

            # Map parameters: attack, release, ratio, threshold
            conn.send_command("set_device_parameter", {
                "track_index": reverb_track_index,
                "device_index": d_idx,
                "parameter_name": "Attack",
                "value": round(recipe["attack_ms"] / 100.0, 4)
            })
            conn.send_command("set_device_parameter", {
                "track_index": reverb_track_index,
                "device_index": d_idx,
                "parameter_name": "Release",
                "value": round(recipe["release_ms"] / 1000.0, 4)
            })

            # Route sidechain source to vocal track
            SidechainManager.route_compressor_sidechain_source(conn, reverb_track_index, d_idx, vocal_track_index)

            return {
                "status": "CONFIGURED",
                "reverb_track_index": reverb_track_index,
                "vocal_track_index": vocal_track_index,
                "recipe": recipe
            }
        except Exception as ex:
            logger.debug(f"Space ducking configuration notice: {ex}")
            return {
                "status": "FAILED_OR_FALLBACK",
                "reverb_track_index": reverb_track_index,
                "vocal_track_index": vocal_track_index,
                "recipe": recipe,
                "error": str(ex)
            }

    @classmethod
    def render_markdown_summary(cls, recipe: Dict[str, Any]) -> str:
        """Renders space ducking status for conversational output."""
        return (
            f"### 🌊 Reverbs y Delays Duckeados Inteligentes (`DynamicSpaceDucker`)\n\n"
            f"- **Modo Seleccionado:** **{recipe['name']}** (`{recipe['mode']}`)\n"
            f"- **Atenuación Activa (Ducking Depth):** `{recipe['duck_amount_db']:.1f} dB`\n"
            f"- **Constantes de Tiempo:** Ataque `{recipe['attack_ms']:.1f} ms` | Relajación `{recipe['release_ms']:.1f} ms`\n"
            f"- **Comportamiento Acústico:** {recipe['description']}\n\n"
            f"💡 *Beneficio: Las palabras de la voz permanecen cristalinas y al frente; la cola espacial florece automáticamente en los silencios.*"
        )
