# engine/sound_design/spatial_narrative.py
"""
Spatial Narrative (Family 9):
Architectural timeline of stereo width, spatial opening, and mono collapse across sections.
Ensures that the song physically expands and contracts to support narrative emotional impact.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("SpatialNarrative")


@dataclass
class SpatialPoint:
    """A spatial definition for a specific section of the arrangement."""
    section_name: str
    start_beat: float
    end_beat: float
    stereo_width_pct: float       # 0% (pure mono) to 200% (super-wide)
    mid_side_ratio: float         # 0.0 (all Mid) to 1.0 (all Side), 0.5 is standard
    bass_mono_cutoff_hz: float    # Frequency below which audio is forced to mono (typically 90-120 Hz)
    narrative_purpose: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_name": self.section_name,
            "start_beat": self.start_beat,
            "end_beat": self.end_beat,
            "stereo_width_pct": round(self.stereo_width_pct, 1),
            "mid_side_ratio": round(self.mid_side_ratio, 2),
            "bass_mono_cutoff_hz": round(self.bass_mono_cutoff_hz, 1),
            "narrative_purpose": self.narrative_purpose,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SpatialPoint:
        return cls(
            section_name=data.get("section_name", "Section"),
            start_beat=float(data.get("start_beat", 0.0)),
            end_beat=float(data.get("end_beat", 16.0)),
            stereo_width_pct=float(data.get("stereo_width_pct", 100.0)),
            mid_side_ratio=float(data.get("mid_side_ratio", 0.5)),
            bass_mono_cutoff_hz=float(data.get("bass_mono_cutoff_hz", 110.0)),
            narrative_purpose=data.get("narrative_purpose", ""),
        )


@dataclass
class SpatialNarrativePlan:
    """The complete macro spatial movement plan across the arrangement."""
    points: List[SpatialPoint] = field(default_factory=list)

    def get_width_for_section(self, section_name: str) -> float:
        for p in self.points:
            if p.section_name.lower() == section_name.lower():
                return p.stereo_width_pct
        return 100.0

    def audit_spatial_contrast(self) -> Dict[str, Any]:
        """
        Verifies that width varies sufficiently to create real spatial impact.
        A static width (e.g. 100% everywhere) fails the audit.
        """
        if len(self.points) < 2:
            return {
                "has_spatial_contrast": True,
                "min_width": 100.0,
                "max_width": 100.0,
                "dynamic_width_range": 0.0,
                "verdict": "MINIMAL_SECTIONS"
            }

        widths = [p.stereo_width_pct for p in self.points]
        min_w = min(widths)
        max_w = max(widths)
        diff = max_w - min_w

        has_contrast = diff >= 40.0  # At least 40% difference between narrowest and widest

        return {
            "has_spatial_contrast": has_contrast,
            "min_width": min_w,
            "max_width": max_w,
            "dynamic_width_range": diff,
            "verdict": "DYNAMIC_SPATIAL_ARC" if has_contrast else "STATIC_STEREO_FIELD",
        }

    def to_automation_envelope(self, parameter_name: str = "Width") -> List[Dict[str, Any]]:
        """
        Generates physical time-value points for Ableton Live automation on Utility.Width.
        In Ableton Live Utility, Width 100% is standard (val ~1.0), 0% is mono, 200% is max wide.
        """
        points = []
        for p in self.points:
            # Map percentage (e.g. 100%) to Ableton parameter scale (0.0 to 2.0 or 0 to 200)
            norm_val = p.stereo_width_pct / 100.0
            points.append({"time": p.start_beat, "value": norm_val})
            points.append({"time": p.end_beat - 0.05, "value": norm_val})
        return points

    def to_dict(self) -> Dict[str, Any]:
        return {
            "points": [p.to_dict() for p in self.points],
            "audit": self.audit_spatial_contrast(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SpatialNarrativePlan:
        points = [SpatialPoint.from_dict(p) for p in data.get("points", [])]
        return cls(points=points)


class SpatialNarrativeEngine:
    """
    Generates tailored spatial plans for arrangements based on section energy
    and narrative arcs.
    """

    @classmethod
    def build_narrative_for_sections(
        cls,
        sections: List[Dict[str, Any]],
        genre: str = "neo-soul/hip-hop"
    ) -> SpatialNarrativePlan:
        """
        Creates a custom spatial arc:
        - Intro: Narrow (40%) intimate focal point
        - Verse 1: Center focused (70%) room for vocal
        - Hook 1: Broad stereo expansion (115%)
        - Verse 2: Dynamic breath (80%)
        - Bridge: Mono collapse (30%) creating vacuum tension
        - Hook 3: Maximum cinematic expansion (140%)
        - Outro: Spatial dissolution into center (20%)
        """
        points: List[SpatialPoint] = []

        for sec in sections:
            s_name = sec.get("name", "Section")
            s_name_lower = s_name.lower()
            s_bars = int(sec.get("bars", 8))
            s_start_beat = float(sec.get("start_bar", 0)) * 4.0
            s_end_beat = s_start_beat + (s_bars * 4.0)

            if "intro" in s_name_lower:
                width = 40.0
                ms_ratio = 0.35
                purpose = "Intimate narrow aperture drawing listener into narrative focus"
            elif "bridge" in s_name_lower or "puente" in s_name_lower:
                width = 30.0
                ms_ratio = 0.25
                purpose = "Near-mono claustrophobic collapse creating dramatic vacuum tension"
            elif "hook 3" in s_name_lower or "climax" in s_name_lower:
                width = 140.0
                ms_ratio = 0.65
                purpose = "Maximum three-dimensional expansion across stereo horizon"
            elif "hook" in s_name_lower or "chorus" in s_name_lower:
                width = 115.0
                ms_ratio = 0.55
                purpose = "Wide lateral burst delivering anthemic impact"
            elif "outro" in s_name_lower:
                width = 25.0
                ms_ratio = 0.20
                purpose = "Centering fade and dissolution into analog mono dust"
            elif "verse 2" in s_name_lower:
                width = 80.0
                ms_ratio = 0.45
                purpose = "Moderate room breath allowing evolving counterpoint"
            else:
                # Default Verse 1 or standard section
                width = 70.0
                ms_ratio = 0.40
                purpose = "Centered stable corridor prioritized for lead vocal legibility"

            point = SpatialPoint(
                section_name=s_name,
                start_beat=s_start_beat,
                end_beat=s_end_beat,
                stereo_width_pct=width,
                mid_side_ratio=ms_ratio,
                bass_mono_cutoff_hz=110.0,
                narrative_purpose=purpose
            )
            points.append(point)

        return SpatialNarrativePlan(points=points)
