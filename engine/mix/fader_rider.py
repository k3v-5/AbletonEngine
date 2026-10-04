# engine/mix/fader_rider.py
"""
Vocal & Lead Fader Riding Automation Engine:
Computes section-aware dynamic fader riding curves across arbitrary arrangement lengths
(default 96 bars or dynamically parameterized structures), maintaining constant vocal intelligibility
and emotional climax presence without over-compression.
"""

import math
import logging
from typing import Dict, Any, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class VocalLeadFaderRider:
    """Generates continuous fader rides across arrangement sections for vocal hooks and lead melodies."""

    SECTION_FADER_MAP = [
        ("Intro", 0, 8, -2.5, "Atmospheric vocal chops tucked behind Rhodes chords."),
        ("Verse 1", 8, 24, -1.2, "Intimate conversational presence sitting inside the groove."),
        ("Pre-Chorus 1", 24, 32, +0.5, "Gradual volume swell building emotional tension."),
        ("Chorus 1", 32, 48, +2.0, "Commanding upfront vocal hook punching through heavy 808."),
        ("Verse 2", 48, 64, -0.8, "Slightly energetic verse momentum."),
        ("Bridge", 64, 72, 0.0, "Isolated spotlight on the melody over Dorian chords."),
        ("Final Chorus", 72, 88, +2.8, "Maximum energy climax fader boost with dual lead layers."),
        ("Outro", 88, 96, -3.0, "Gentle decompression fade into vinyl atmosphere."),
    ]

    ROLE_DEFAULT_GAINS: Dict[str, Dict[str, float]] = {
        "vocal": {
            "intro": -2.5,
            "verse": -1.2,
            "pre-chorus": +0.5,
            "chorus": +2.0,
            "hook": +2.2,
            "drop": +2.5,
            "bridge": 0.0,
            "climax": +2.8,
            "final chorus": +2.8,
            "solo": +1.5,
            "outro": -3.0
        },
        "lead": {
            "intro": -2.0,
            "verse": -1.5,
            "pre-chorus": +0.0,
            "chorus": +1.8,
            "hook": +2.0,
            "drop": +2.2,
            "bridge": +0.5,
            "climax": +2.5,
            "final chorus": +2.5,
            "solo": +2.5,
            "outro": -2.5
        }
    }

    BASE_FADER_VAL = 0.85  # Ableton 0 dB nominal level

    @classmethod
    def db_to_fader_val(cls, db_offset: float) -> float:
        """Converts dB fader adjustment into Ableton Live normalized volume fader value."""
        # 0.85 is Ableton 0.0 dB. +6dB is 1.0 (approx)
        gain_mult = 10.0 ** (db_offset / 20.0)
        norm_val = cls.BASE_FADER_VAL * gain_mult
        return round(max(0.0, min(1.0, norm_val)), 4)

    @classmethod
    def _resolve_section_tuple(
        cls,
        sec: Union[Tuple, Dict[str, Any]],
        role: str = "vocal",
        default_index: int = 0
    ) -> Tuple[str, float, float, float, str]:
        """Normalizes a section specification into (name, start_bar, end_bar, db_gain, description)."""
        if isinstance(sec, (tuple, list)):
            name = str(sec[0])
            s_bar = float(sec[1])
            e_bar = float(sec[2])
            db_gain = float(sec[3]) if len(sec) > 3 else 0.0
            desc = str(sec[4]) if len(sec) > 4 else f"{name} section riding."
            return name, s_bar, e_bar, db_gain, desc

        if isinstance(sec, dict):
            name = str(sec.get("name", sec.get("section", f"Section {default_index + 1}")))
            s_bar = float(sec.get("start_bar", sec.get("bar", default_index * 8)))
            length_bars = float(sec.get("length_bars", sec.get("bars", 8)))
            e_bar = float(sec.get("end_bar", s_bar + length_bars))

            # Resolve db offset
            db_gain = sec.get("db_offset", sec.get("db_gain"))
            if db_gain is None:
                # Infer from name
                name_lower = name.lower()
                gains_table = cls.ROLE_DEFAULT_GAINS.get(role.lower(), cls.ROLE_DEFAULT_GAINS["vocal"])
                matched = 0.0
                for k, v in gains_table.items():
                    if k in name_lower:
                        matched = v
                        break
                db_gain = matched
            else:
                db_gain = float(db_gain)

            desc = str(sec.get("desc", sec.get("rationale", f"Dynamic fader riding for {name} ({db_gain:+.1f} dB).")))
            return name, s_bar, e_bar, db_gain, desc

        raise ValueError(f"Unsupported section format: {sec}")

    @classmethod
    def generate_fader_automation_envelope(
        cls,
        role: str = "vocal",
        crossfade_beats: float = 2.0,
        sections: Optional[Union[List[Dict[str, Any]], List[Tuple]]] = None,
        beats_per_bar: float = 4.0
    ) -> List[Dict[str, float]]:
        """
        Generates continuous volume breakpoint automation points across all arrangement sections.
        Crossfades smoothly across section boundaries to eliminate sudden volume jumps.
        If sections is None, defaults to the canonical 96-bar map (384 beats).
        """
        raw_sections = sections if sections is not None else cls.SECTION_FADER_MAP
        normalized_sections = [
            cls._resolve_section_tuple(s, role=role, default_index=i)
            for i, s in enumerate(raw_sections)
        ]

        if not normalized_sections:
            return [{"time": 0.0, "value": cls.BASE_FADER_VAL}]

        points: List[Dict[str, float]] = []

        for idx, (sec_name, start_bar, end_bar, db_gain, desc) in enumerate(normalized_sections):
            start_beat = start_bar * beats_per_bar
            end_beat = end_bar * beats_per_bar
            target_val = cls.db_to_fader_val(db_gain)

            if idx == 0:
                # Initial point
                points.append({"time": 0.0, "value": target_val})
            else:
                # Smooth ramp into new section
                ramp_start = max(0.0, start_beat - crossfade_beats)
                prev_val = points[-1]["value"]
                points.append({"time": round(ramp_start, 3), "value": prev_val})
                points.append({"time": round(start_beat, 3), "value": target_val})

            # Section steady point before next ramp
            steady_end = max(start_beat, end_beat - crossfade_beats)
            points.append({"time": round(steady_end, 3), "value": target_val})

        # Final end point
        last_end_beat = normalized_sections[-1][2] * beats_per_bar
        last_val = cls.db_to_fader_val(normalized_sections[-1][3])
        points.append({"time": round(last_end_beat, 3), "value": last_val})
        return points

    @classmethod
    def get_fader_riding_manifest(
        cls,
        role: str = "vocal",
        sections: Optional[Union[List[Dict[str, Any]], List[Tuple]]] = None,
        beats_per_bar: float = 4.0
    ) -> Dict[str, Any]:
        """Returns the complete fader riding manifest with section descriptions and automation envelope."""
        raw_sections = sections if sections is not None else cls.SECTION_FADER_MAP
        normalized_sections = [
            cls._resolve_section_tuple(s, role=role, default_index=i)
            for i, s in enumerate(raw_sections)
        ]

        envelope = cls.generate_fader_automation_envelope(
            role=role,
            sections=raw_sections,
            beats_per_bar=beats_per_bar
        )

        sections_summary = [
            {
                "section": sec,
                "bars": f"{int(s_bar)}-{int(e_bar)}",
                "db_offset": db,
                "fader_value": cls.db_to_fader_val(db),
                "rationale": desc
            }
            for sec, s_bar, e_bar, db, desc in normalized_sections
        ]

        total_bars = normalized_sections[-1][2] if normalized_sections else 0.0

        return {
            "status": "SUCCESS",
            "phase": "PHASE_6_MIX_SURGICAL",
            "role": role,
            "total_bars": total_bars,
            "total_sections": len(sections_summary),
            "total_automation_points": len(envelope),
            "sections": sections_summary,
            "automation_envelope": envelope
        }

    @classmethod
    def apply_to_track(
        cls,
        conn: Any,
        track_index: int,
        role: str = "vocal",
        sections: Optional[Union[List[Dict[str, Any]], List[Tuple]]] = None,
        beats_per_bar: float = 4.0
    ) -> Dict[str, Any]:
        """
        Dispatches generated fader riding automation points to Ableton Live track volume.
        """
        manifest = cls.get_fader_riding_manifest(role=role, sections=sections, beats_per_bar=beats_per_bar)
        envelope = manifest["automation_envelope"]

        if conn is None or not hasattr(conn, "send_command"):
            return {
                "status": "MOCK_OK",
                "track_index": track_index,
                "role": role,
                "points_applied": len(envelope),
                "manifest": manifest
            }

        try:
            conn.send_command("create_arrangement_automation_envelope", {
                "track_index": track_index,
                "parameter": "Volume",
                "points": envelope
            })
            logger.info(f"Dispatched fader riding envelope ({len(envelope)} points) to Track {track_index}")
        except Exception as e:
            logger.warning(f"Failed to dispatch fader riding to Track {track_index}: {e}")

        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "role": role,
            "points_applied": len(envelope),
            "manifest": manifest
        }
