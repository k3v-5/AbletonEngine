"""
Spatial Energy Curve Engine:
Models the dynamic three-dimensional breathing of the song across the arrangement timeline:
Intro (25%) -> Verse (40%) -> Build (75%) -> Pre-Drop Collapse (15%) -> Drop Explosion (115%-130%).
Controls stereo width, reverb size, early reflections, pre-delay, and M/S tilt in Live.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger("SpatialEnergyCurve")


@dataclass
class SpatialProfile:
    section_name: str
    stereo_width: float        # 0.0 (mono) to 1.40 (hyper-wide)
    reverb_dry_wet: float      # 0.0 to 1.0
    reverb_decay_s: float      # 0.5 to 8.0 seconds
    delay_feedback: float      # 0.0 to 0.80
    mid_side_tilt: float       # -1.0 (strict mid/mono) to +1.0 (heavy sides)
    depth_character: str = "balanced"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_name": self.section_name,
            "stereo_width": round(self.stereo_width, 3),
            "reverb_dry_wet": round(self.reverb_dry_wet, 3),
            "reverb_decay_s": round(self.reverb_decay_s, 2),
            "delay_feedback": round(self.delay_feedback, 3),
            "mid_side_tilt": round(self.mid_side_tilt, 3),
            "depth_character": self.depth_character
        }


class SpatialEnergyCurveEngine:
    """
    Coordinates multi-parameter spatial automation across sections.
    Ensures the song breathes in width and depth rather than relying solely on volume.
    """

    CANONICAL_PROFILES: Dict[str, SpatialProfile] = {
        "intro": SpatialProfile("intro", stereo_width=0.25, reverb_dry_wet=0.20, reverb_decay_s=2.2, delay_feedback=0.25, mid_side_tilt=-0.40, depth_character="intimate"),
        "verse": SpatialProfile("verse", stereo_width=0.40, reverb_dry_wet=0.15, reverb_decay_s=1.8, delay_feedback=0.20, mid_side_tilt=-0.30, depth_character="focused"),
        "pre_chorus": SpatialProfile("pre_chorus", stereo_width=0.55, reverb_dry_wet=0.25, reverb_decay_s=2.5, delay_feedback=0.30, mid_side_tilt=0.10, depth_character="expanding"),
        "buildup": SpatialProfile("buildup", stereo_width=0.75, reverb_dry_wet=0.38, reverb_decay_s=3.2, delay_feedback=0.45, mid_side_tilt=0.35, depth_character="elevating"),
        "build": SpatialProfile("build", stereo_width=0.70, reverb_dry_wet=0.35, reverb_decay_s=3.0, delay_feedback=0.40, mid_side_tilt=0.30, depth_character="elevating"),
        "pre_drop": SpatialProfile("pre_drop", stereo_width=0.15, reverb_dry_wet=0.05, reverb_decay_s=0.6, delay_feedback=0.05, mid_side_tilt=-0.80, depth_character="mono_vacuum"),
        "drop": SpatialProfile("drop", stereo_width=1.18, reverb_dry_wet=0.22, reverb_decay_s=2.8, delay_feedback=0.32, mid_side_tilt=0.45, depth_character="panoramic_explosion"),
        "chorus": SpatialProfile("chorus", stereo_width=1.10, reverb_dry_wet=0.24, reverb_decay_s=2.6, delay_feedback=0.30, mid_side_tilt=0.40, depth_character="wide_commercial"),
        "break": SpatialProfile("break", stereo_width=0.35, reverb_dry_wet=0.35, reverb_decay_s=3.8, delay_feedback=0.40, mid_side_tilt=-0.10, depth_character="ambient_cave"),
        "bridge": SpatialProfile("bridge", stereo_width=0.50, reverb_dry_wet=0.30, reverb_decay_s=3.0, delay_feedback=0.35, mid_side_tilt=0.00, depth_character="diffuse"),
        "final_drop": SpatialProfile("final_drop", stereo_width=1.28, reverb_dry_wet=0.28, reverb_decay_s=3.2, delay_feedback=0.38, mid_side_tilt=0.55, depth_character="colossal_impact"),
        "outro": SpatialProfile("outro", stereo_width=0.30, reverb_dry_wet=0.42, reverb_decay_s=4.5, delay_feedback=0.25, mid_side_tilt=-0.20, depth_character="fading_distance")
    }

    @classmethod
    def get_section_spatial_profile(cls, section_name: str) -> SpatialProfile:
        """Resolves target spatial profile for a section."""
        s_low = str(section_name or "").lower().replace("-", "_").replace(" ", "_")
        if "final" in s_low and "drop" in s_low or "drop_2" in s_low:
            return cls.CANONICAL_PROFILES["final_drop"]
        if "pre_drop" in s_low or "vacuum" in s_low:
            return cls.CANONICAL_PROFILES["pre_drop"]
        for k, prof in cls.CANONICAL_PROFILES.items():
            if k in s_low:
                return prof
        return cls.CANONICAL_PROFILES["verse"]

    @classmethod
    def build_spatial_envelope(
        cls,
        sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Builds automation point trajectories for stereo width, reverb, and delay across all sections.
        """
        timeline_points: List[Dict[str, Any]] = []
        cur_beat = 0.0

        for sec in sections:
            s_name = sec.get("name", "Section")
            bars = int(sec.get("bars", 8))
            beats = bars * 4.0
            prof = cls.get_section_spatial_profile(s_name)

            # Record section start point
            timeline_points.append({
                "section": s_name,
                "start_beat": cur_beat,
                "end_beat": cur_beat + beats,
                "profile": prof.to_dict()
            })
            cur_beat += beats

        # Validate Pre-Drop to Drop contrast
        contrast_ok, contrast_delta = cls.verify_drop_expansion_contrast(timeline_points)

        return {
            "status": "SPATIAL_ENVELOPE_BUILT",
            "total_beats": cur_beat,
            "section_count": len(sections),
            "timeline": timeline_points,
            "pre_drop_to_drop_contrast_delta": contrast_delta,
            "has_proper_spatial_explosion": contrast_ok
        }

    @classmethod
    def verify_drop_expansion_contrast(
        cls,
        timeline_or_pre_width: Any = None,
        drop_width: Optional[float] = None,
        pre_drop_width: Optional[float] = None
    ) -> Any:
        """
        Validates that the transition into a Drop exhibits a dramatic spatial expansion (>= 0.70 width jump).
        Supports either a list of timeline points or direct (pre_drop_width, drop_width) floats.
        """
        p_width = pre_drop_width if pre_drop_width is not None else timeline_or_pre_width
        if drop_width is not None or isinstance(p_width, (int, float)):
            pre_w = float(p_width if p_width is not None else 0.0)
            drp_w = float(drop_width if drop_width is not None else 1.0)
            diff = round(drp_w - pre_w, 3)
            return {
                "contrast_sufficient": diff >= 0.70,
                "delta_width": diff
            }


        timeline_points = timeline_or_pre_width or []
        max_jump = 0.0
        for i in range(len(timeline_points) - 1):
            curr_p = timeline_points[i]["profile"]
            next_p = timeline_points[i + 1]["profile"]
            if "drop" in timeline_points[i + 1]["section"].lower():
                width_diff = next_p["stereo_width"] - curr_p["stereo_width"]
                max_jump = max(max_jump, width_diff)

        return (max_jump >= 0.70, round(max_jump, 3))


# Top-level aliases for convenience
CANONICAL_PROFILES = SpatialEnergyCurveEngine.CANONICAL_PROFILES
build_spatial_envelope = SpatialEnergyCurveEngine.build_spatial_envelope
verify_drop_expansion_contrast = SpatialEnergyCurveEngine.verify_drop_expansion_contrast

