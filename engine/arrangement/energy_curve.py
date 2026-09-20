"""
Global Energy Curve Engine:
Defines, tracks, and evaluates the master 0.0 to 1.0 macro-energy curve
across all sections of the arrangement timeline:
Intro (0.25) -> Verse (0.45) -> Build (0.75) -> Drop 1 (0.95) -> Break (0.35) -> Drop 2 (1.00) -> Outro (0.15).
Drives arrangement density, layer activation, and micro-automation intensity.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class EnergyPoint:
    time_beats: float
    energy: float       # 0.0 to 1.0
    section_name: str
    curve_type: str = "linear"  # "linear", "exponential", "step"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "time_beats": round(self.time_beats, 2),
            "energy": round(self.energy, 3),
            "section_name": self.section_name,
            "curve_type": self.curve_type
        }


class EnergyCurveEngine:
    """
    Manages arrangement energy profiles and verifies dynamic contrast across the song.
    """

    SECTION_ENERGY_BASELINES = {
        "intro": 0.25,
        "verse": 0.45,
        "pre-chorus": 0.65,
        "buildup": 0.75,
        "build": 0.75,
        "drop": 0.95,
        "chorus": 0.90,
        "climax": 1.00,
        "break": 0.35,
        "puente": 0.35,
        "bridge": 0.35,
        "drop 2": 1.00,
        "drop2": 1.00,
        "outro": 0.15
    }

    @classmethod
    def get_section_energy(cls, section_name: str) -> float:
        """Determines target energy level for a section by name."""
        s_low = str(section_name or "").lower().strip()
        if "drop 2" in s_low or "drop2" in s_low or "climax" in s_low:
            return 1.00
        for k, v in cls.SECTION_ENERGY_BASELINES.items():
            if k in s_low:
                return v
        return 0.50

    @classmethod
    def build_song_energy_curve(
        cls,
        sections: List[Dict[str, Any]]
    ) -> List[EnergyPoint]:
        """
        Calculates a continuous energy envelope across all sections in the arrangement.
        """
        curve: List[EnergyPoint] = []
        cur_beat = 0.0

        for sec in sections:
            s_name = sec.get("name", "Section")
            s_bars = int(sec.get("bars", 8))
            s_beats = float(s_bars * 4.0)
            target_e = cls.get_section_energy(s_name)
            s_low = s_name.lower()

            if any(w in s_low for w in ["build", "subida", "pre"]):
                # Buildup: Ramps from previous energy up to target
                start_e = curve[-1].energy if curve else 0.45
                curve.append(EnergyPoint(cur_beat, start_e, s_name, "exponential"))
                curve.append(EnergyPoint(cur_beat + s_beats, target_e, s_name, "step"))
            elif any(w in s_low for w in ["outro", "final"]):
                # Outro: Decays down to 0.10
                start_e = curve[-1].energy if curve else 0.50
                curve.append(EnergyPoint(cur_beat, start_e, s_name, "linear"))
                curve.append(EnergyPoint(cur_beat + s_beats, 0.10, s_name, "step"))
            else:
                # Sustained section
                curve.append(EnergyPoint(cur_beat, target_e, s_name, "step"))
                curve.append(EnergyPoint(cur_beat + s_beats, target_e, s_name, "step"))

            cur_beat += s_beats

        return curve

    @classmethod
    def evaluate_contrast(
        cls,
        sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluates dynamic contrast to prevent flat arrangement energy.
        """
        energies = [cls.get_section_energy(s.get("name", "")) for s in sections]
        if not energies:
            return {"status": "EMPTY", "dynamic_range": 0.0, "is_balanced": False}

        min_e = min(energies)
        max_e = max(energies)
        dynamic_range = round(max_e - min_e, 2)

        # Ensure dynamic range is at least 0.50 for modern commercial appeal
        is_balanced = dynamic_range >= 0.50

        return {
            "status": "BALANCED" if is_balanced else "COMPRESSED_DYNAMICS",
            "dynamic_range": dynamic_range,
            "min_energy": min_e,
            "max_energy": max_e,
            "is_balanced": is_balanced,
            "recommendation": "Maintain dynamic valley in Bridge/Break to heighten Drop impact." if not is_balanced else "Dynamic energy contrast is optimal."
        }
