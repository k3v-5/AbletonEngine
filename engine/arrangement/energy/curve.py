# engine/arrangement/energy/curve.py
import math
from typing import Dict, Any, List, Tuple, Optional
from .dimensions import EnergyDimensions
from engine.arrangement.models.section import Section

class EnergyCurve:
    """Piecewise multi-point energy curve with continuous interpolation across song bars."""
    def __init__(self, keypoints: Optional[List[Tuple[int, EnergyDimensions]]] = None):
        self.keypoints = sorted(keypoints or [], key=lambda k: k[0])

    def add_keypoint(self, bar: int, dimensions: EnergyDimensions):
        self.keypoints.append((bar, dimensions))
        self.keypoints.sort(key=lambda k: k[0])

    def get_at_bar(self, bar: int) -> EnergyDimensions:
        """Returns interpolated EnergyDimensions at any arbitrary bar."""
        if not self.keypoints:
            return EnergyDimensions()
        if bar <= self.keypoints[0][0]:
            return self.keypoints[0][1]
        if bar >= self.keypoints[-1][0]:
            return self.keypoints[-1][1]

        for i in range(len(self.keypoints) - 1):
            b_start, d_start = self.keypoints[i]
            b_end, d_end = self.keypoints[i + 1]

            if b_start <= bar <= b_end:
                span = float(b_end - b_start)
                if span <= 0:
                    return d_start
                t = (bar - b_start) / span
                t_smooth = 0.5 * (1.0 - math.cos(t * math.pi))

                return EnergyDimensions(
                    energy=d_start.energy + (d_end.energy - d_start.energy) * t_smooth,
                    density=d_start.density + (d_end.density - d_start.density) * t_smooth,
                    tension=d_start.tension + (d_end.tension - d_start.tension) * t_smooth,
                    brightness=d_start.brightness + (d_end.brightness - d_start.brightness) * t_smooth,
                    rhythmic_activity=d_start.rhythmic_activity + (d_end.rhythmic_activity - d_start.rhythmic_activity) * t_smooth,
                    harmonic_activity=d_start.harmonic_activity + (d_end.harmonic_activity - d_start.harmonic_activity) * t_smooth,
                    spectral_activity=d_start.spectral_activity + (d_end.spectral_activity - d_start.spectral_activity) * t_smooth
                )

        return self.keypoints[-1][1]

    def find_climaxes(self) -> Dict[str, Any]:
        """Detect primary and secondary energy peaks in the curve."""
        if not self.keypoints:
            return {"primary_climax": None, "secondary_climax": None}

        peaks = []
        for i in range(1, len(self.keypoints) - 1):
            prev_e = self.keypoints[i - 1][1].energy
            curr_e = self.keypoints[i][1].energy
            next_e = self.keypoints[i + 1][1].energy
            if curr_e >= prev_e and curr_e >= next_e and curr_e > 0.7:
                peaks.append((self.keypoints[i][0], curr_e))

        if not peaks:
            sorted_by_e = sorted(self.keypoints, key=lambda k: k[1].energy, reverse=True)
            peaks = [(sorted_by_e[0][0], sorted_by_e[0][1].energy)]
            if len(sorted_by_e) > 1:
                peaks.append((sorted_by_e[1][0], sorted_by_e[1][1].energy))

        peaks.sort(key=lambda p: p[1], reverse=True)
        primary = peaks[0] if len(peaks) > 0 else None
        secondary = peaks[1] if len(peaks) > 1 else None

        return {
            "primary_climax": {"bar": primary[0], "energy": round(primary[1], 3)} if primary else None,
            "secondary_climax": {"bar": secondary[0], "energy": round(secondary[1], 3)} if secondary else None
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "keypoints": [
                {"bar": b, "dimensions": d.to_dict()}
                for b, d in self.keypoints
            ],
            "climaxes": self.find_climaxes()
        }

class EnergyCurveGenerator:
    """Generates continuous energy curves for arrangements and synchronizes section values."""

    @classmethod
    def generate_curve(cls, sections: List[Section], template: str = "melodic_techno") -> List[Section]:
        curve = EnergyCurve()
        for s in sections:
            midpoint_bar = s.start_bar + (s.duration_bars // 2)
            dims = EnergyDimensions(
                energy=s.energy,
                density=s.density,
                tension=s.tension,
                brightness=s.energy * 0.9,
                rhythmic_activity=s.density,
                harmonic_activity=0.6,
                spectral_activity=s.energy
            )
            curve.add_keypoint(midpoint_bar, dims)

        # Smooth sections
        for s in sections:
            mid = s.start_bar + (s.duration_bars // 2)
            interp = curve.get_at_bar(mid)
            # Reconcile section energy with smoothed curve
            s.energy = round(interp.energy, 3)
            s.density = round(interp.density, 3)
            s.tension = round(interp.tension, 3)

        return sections
