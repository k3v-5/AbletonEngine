# engine/music/theory/tessitura_guard.py
"""
Tessitura & Spacing Guard:
Punto 30: Validates acoustic register tessituras, low-interval limits, and voice spacing.
Configurable via config/tessitura_config.json with 3 strictness levels (MINIMA default, MODERADA, ESTRICTA).
Prevents low-mid mud, harmonic masking, and unnatural vocal/instrument ranges.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from engine.music.models import NoteEvent


class TessituraGuard:
    """Audits and enforces acoustic tessitura boundaries and chord voice spacing."""

    _CONFIG_CACHE: Dict[str, Any] = {}

    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """Loads and caches tessitura strictness configuration."""
        if not cls._CONFIG_CACHE:
            config_path = Path(__file__).resolve().parent.parent.parent.parent / "config" / "tessitura_config.json"
            if config_path.exists():
                try:
                    cls._CONFIG_CACHE = json.loads(config_path.read_text(encoding="utf-8"))
                except Exception:
                    cls._CONFIG_CACHE = {}
        return cls._CONFIG_CACHE

    @classmethod
    def get_level_settings(cls, level: Optional[str] = None) -> Dict[str, Any]:
        """Retrieves rule parameters for the specified strictness level."""
        conf = cls.load_config()
        lvl = (level or conf.get("default_level", "MINIMA")).upper()
        levels = conf.get("strictness_levels", {})
        return levels.get(lvl, levels.get("MINIMA", {
            "max_bass_pitch": 48,
            "min_lead_pitch": 55,
            "forbid_low_interval_thirds_below_midi": 36,
            "max_adjacent_voice_gap_semitones": 19
        }))

    @classmethod
    def audit_role_notes(
        cls,
        role: str,
        notes: List[NoteEvent],
        strictness_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Audits a list of NoteEvents against role tessitura limits.
        """
        if not notes:
            return {"status": "EMPTY", "violations_count": 0, "violations": []}

        settings = cls.get_level_settings(strictness_level)
        r = role.lower()
        violations = []

        max_bass = settings.get("max_bass_pitch", 48)
        min_lead = settings.get("min_lead_pitch", 55)

        for n in notes:
            if "bass" in r or "808" in r or "sub" in r:
                if n.pitch > max_bass:
                    violations.append({
                        "pitch": n.pitch,
                        "time": n.start,
                        "reason": f"Bass pitch {n.pitch} exceeds maximum tessitura ceiling {max_bass} (C3)"
                    })
                if n.pitch < 24 and not settings.get("allow_sub_harmonics_below_c1", False):
                    violations.append({
                        "pitch": n.pitch,
                        "time": n.start,
                        "reason": f"Bass pitch {n.pitch} is below inaudible/sub-harmonic limit 24 (C1)"
                    })
            elif "lead" in r or "melody" in r or "topline" in r:
                if n.pitch < min_lead:
                    violations.append({
                        "pitch": n.pitch,
                        "time": n.start,
                        "reason": f"Lead pitch {n.pitch} dips below minimum clarity threshold {min_lead}"
                    })

        return {
            "status": "VIOLATIONS_FOUND" if violations else "TESSITURA_COMPLIANT",
            "role": role,
            "strictness_level": strictness_level or "MINIMA",
            "violations_count": len(violations),
            "violations": violations,
            "is_compliant": len(violations) == 0
        }

    @classmethod
    def audit_chord_spacing(
        cls,
        chord_pitches: List[int],
        strictness_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Punto 30: Audits vertical chord spacing and low-interval limits (LIL).
        Identifies muddy thirds in the low register or excessive gaps between inner voices.
        """
        if len(chord_pitches) < 2:
            return {"status": "INSUFFICIENT_VOICES", "violations": []}

        settings = cls.get_level_settings(strictness_level)
        low_third_limit = settings.get("forbid_low_interval_thirds_below_midi", 36)
        max_gap = settings.get("max_adjacent_voice_gap_semitones", 19)

        sorted_pitches = sorted(chord_pitches)
        violations = []

        # 1. Low Interval Limit check: minor/major thirds (3-4 semitones) in sub-bass
        for i in range(len(sorted_pitches) - 1):
            p1 = sorted_pitches[i]
            p2 = sorted_pitches[i + 1]
            interval = p2 - p1
            if interval in (3, 4) and p1 < low_third_limit:
                violations.append({
                    "interval": interval,
                    "pitches": (p1, p2),
                    "reason": f"Low-interval third ({interval} st) at MIDI {p1}-{p2} causes acoustic mud below threshold {low_third_limit}"
                })

            # 2. Adjacent voice gap check (inner voices shouldn't exceed max_gap)
            if i > 0 and interval > max_gap:
                violations.append({
                    "interval": interval,
                    "pitches": (p1, p2),
                    "reason": f"Voice gap of {interval} semitones exceeds maximum acoustic spread {max_gap}"
                })

        return {
            "status": "MUD_OR_GAP_DETECTED" if violations else "VOICING_BALANCED",
            "violations_count": len(violations),
            "violations": violations,
            "is_compliant": len(violations) == 0
        }

    @classmethod
    def enforce_safe_tessitura(
        cls,
        notes: List[NoteEvent],
        role: str,
        strictness_level: Optional[str] = None
    ) -> List[NoteEvent]:
        """
        Automatically transposes offending notes into safe tessitura boundaries.
        """
        settings = cls.get_level_settings(strictness_level)
        r = role.lower()
        corrected = []

        max_bass = settings.get("max_bass_pitch", 48)
        min_lead = settings.get("min_lead_pitch", 55)

        for n in notes:
            p = n.pitch
            if "bass" in r or "808" in r or "sub" in r:
                while p > max_bass:
                    p -= 12
                while p < 24:
                    p += 12
            elif "lead" in r or "melody" in r or "topline" in r:
                while p < min_lead:
                    p += 12
                while p > 100:
                    p -= 12

            corrected.append(NoteEvent(
                pitch=p,
                start=n.start,
                duration=n.duration,
                velocity=n.velocity,
                channel=n.channel
            ))

        return corrected
