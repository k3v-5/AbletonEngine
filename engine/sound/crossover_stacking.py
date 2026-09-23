# engine/sound/crossover_stacking.py
"""
Multi-Layer Psicoacoustic Crossover Stacking Engine:
Splits bass and synthesizer sounds into 3 discrete frequency/acoustic layers:
1. Sub Layer (<90 Hz): Pure mono foundation, zero detune, heavy saturation for small speakers.
2. Body/Mid Layer (90 - 1200 Hz): Harmonic core, analog tape warmth, transient control, moderate stereo width.
3. Air/Top Layer (>1200 Hz): Extreme stereo widening (120%), micro-pitch detune, shimmer reverb.
Ensures mammoth commercial sound without low-end phase smearing or muddy summing.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger("MultiLayerCrossoverStacker")


@dataclass
class CrossoverLayerProfile:
    layer_name: str
    freq_range_hz: Tuple[float, float]
    stereo_width: float      # 0.0 = Pure Mono, 1.0 = Standard 100%, 1.5 = Ultra-wide 150%
    saturation_drive: float  # 0.0 to 1.0
    eq_filter_type: str      # "LOW_PASS", "BAND_PASS", "HIGH_PASS"
    modulation_depth: float  # 0.0 to 1.0


class MultiLayerCrossoverStacker:
    """
    Computes and formats psychoacoustic crossover layer configurations for Bass and Leads.
    """

    DEFAULT_CROSSOVERS = {
        "SUB_BODY": 90.0,     # Crossover between Sub and Body
        "BODY_AIR": 1200.0    # Crossover between Body and Air
    }

    @classmethod
    def generate_triple_crossover_stack(
        cls,
        role: str,
        sub_crossover_hz: float = 90.0,
        air_crossover_hz: float = 1200.0
    ) -> Dict[str, Any]:
        """
        Generates full 3-layer crossover specifications for a given role (e.g. BASS, LEAD, SYNTH).
        """
        r_up = str(role or "").upper()
        is_bass = any(k in r_up for k in ("BASS", "808", "SUB"))

        # Layer 1: Sub
        sub_layer = CrossoverLayerProfile(
            layer_name="SUB_FOUNDATION",
            freq_range_hz=(20.0, sub_crossover_hz),
            stereo_width=0.0,  # Strict mono
            saturation_drive=0.25 if is_bass else 0.15,
            eq_filter_type="LOW_PASS",
            modulation_depth=0.0  # Zero detuning/chorus in sub
        )

        # Layer 2: Body / Mid
        body_layer = CrossoverLayerProfile(
            layer_name="BODY_HARMONIC_CORE",
            freq_range_hz=(sub_crossover_hz, air_crossover_hz),
            stereo_width=0.55 if is_bass else 0.70,
            saturation_drive=0.40,
            eq_filter_type="BAND_PASS",
            modulation_depth=0.20
        )

        # Layer 3: Air / Top
        air_layer = CrossoverLayerProfile(
            layer_name="AIR_STEREO_DIMENSION",
            freq_range_hz=(air_crossover_hz, 20000.0),
            stereo_width=1.35 if not is_bass else 1.10,
            saturation_drive=0.10,
            eq_filter_type="HIGH_PASS",
            modulation_depth=0.65
        )

        summary_table = (
            f"| Capa Acústica | Rango de Frecuencias | Ancho Estéreo | Saturación | Tipo Filtro |\n"
            f"| :--- | :--- | :--- | :--- | :--- |\n"
            f"| **1. Sub Foundation** | 20 Hz - {sub_crossover_hz:.0f} Hz | Mono (0.0) | {sub_layer.saturation_drive*100:.0f}% | Low-Pass 24dB/oct |\n"
            f"| **2. Body Harmonic** | {sub_crossover_hz:.0f} Hz - {air_crossover_hz:.0f} Hz | Centrado ({body_layer.stereo_width*100:.0f}%) | {body_layer.saturation_drive*100:.0f}% | Band-Pass 12dB/oct |\n"
            f"| **3. Air & Space** | > {air_crossover_hz:.0f} Hz | Ultra-Wide ({air_layer.stereo_width*100:.0f}%) | {air_layer.saturation_drive*100:.0f}% | High-Pass 24dB/oct |"
        )

        return {
            "status": "CONFIGURED",
            "role": role,
            "architecture": "TRIPLE_CROSSOVER_STACK",
            "crossovers_hz": {
                "sub_body": sub_crossover_hz,
                "body_air": air_crossover_hz
            },
            "layers": {
                "sub": sub_layer.__dict__,
                "body": body_layer.__dict__,
                "air": air_layer.__dict__
            },
            "summary_table": summary_table
        }

    @classmethod
    def create_crossover_split(
        cls,
        source_track_name: str = "Source Track",
        role: str = "BASS",
        sub_crossover_hz: float = 90.0,
        air_crossover_hz: float = 1200.0
    ) -> Dict[str, Any]:
        """
        Creates a list of 3 crossover layer specifications with frequency cutoffs and stereo width.
        """
        raw = cls.generate_triple_crossover_stack(role, sub_crossover_hz, air_crossover_hz)
        sub_dict = raw["layers"]["sub"]
        body_dict = raw["layers"]["body"]
        air_dict = raw["layers"]["air"]
        layers = [
            {
                "layer_id": "SUB",
                "layer_name": sub_dict["layer_name"],
                "crossover_lp_hz": sub_crossover_hz,
                "crossover_hp_hz": 20.0,
                "stereo_width": sub_dict["stereo_width"],
                "saturation": sub_dict["saturation_drive"]
            },
            {
                "layer_id": "BODY",
                "layer_name": body_dict["layer_name"],
                "crossover_hp_hz": sub_crossover_hz,
                "crossover_lp_hz": air_crossover_hz,
                "stereo_width": body_dict["stereo_width"],
                "saturation": body_dict["saturation_drive"]
            },
            {
                "layer_id": "AIR",
                "layer_name": air_dict["layer_name"],
                "crossover_hp_hz": air_crossover_hz,
                "crossover_lp_hz": 20000.0,
                "stereo_width": air_dict["stereo_width"],
                "saturation": air_dict["saturation_drive"]
            }
        ]
        return {
            "source_track_name": source_track_name,
            "role": role,
            "layers": layers,
            "crossovers": {"sub_body": sub_crossover_hz, "body_air": air_crossover_hz}
        }

    @classmethod
    def generate_dual_crossover_stack(
        cls,
        role: str,
        crossover_hz: float = 120.0
    ) -> Dict[str, Any]:
        """
        Generates 2-layer split: Sub mono vs Upper Mid/Air wide.
        """
        sub_layer = CrossoverLayerProfile(
            layer_name="SUB_MONO",
            freq_range_hz=(20.0, crossover_hz),
            stereo_width=0.0,
            saturation_drive=0.20,
            eq_filter_type="LOW_PASS",
            modulation_depth=0.0
        )
        upper_layer = CrossoverLayerProfile(
            layer_name="UPPER_STEREO",
            freq_range_hz=(crossover_hz, 20000.0),
            stereo_width=1.0,
            saturation_drive=0.30,
            eq_filter_type="HIGH_PASS",
            modulation_depth=0.45
        )

        return {
            "status": "CONFIGURED",
            "role": role,
            "architecture": "DUAL_CROSSOVER_STACK",
            "crossover_hz": crossover_hz,
            "layers": {
                "sub": sub_layer.__dict__,
                "upper": upper_layer.__dict__
            }
        }
