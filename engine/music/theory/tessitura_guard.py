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
            "min_brass_pitch": 55,
            "max_brass_pitch": 84,
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
        min_brass = settings.get("min_brass_pitch", 55)
        max_brass = settings.get("max_brass_pitch", 84)

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
            elif any(k in r for k in ("brass", "trumpet", "trompeta", "horn", "flugelhorn")):
                if n.pitch < min_brass:
                    violations.append({
                        "pitch": n.pitch,
                        "time": n.start,
                        "reason": f"Brass/Trumpet pitch {n.pitch} dips below acoustic cutoff {min_brass} (G3)"
                    })
                if n.pitch > max_brass:
                    violations.append({
                        "pitch": n.pitch,
                        "time": n.start,
                        "reason": f"Brass/Trumpet pitch {n.pitch} exceeds standard acoustic ceiling {max_brass} (C6)"
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
    def clamp_single_pitch(
        cls,
        pitch: int,
        role: str,
        strictness_level: Optional[str] = None
    ) -> int:
        """
        Clamps a single MIDI pitch into the safe acoustic tessitura for the given role.
        Preserves pitch-class via octave transposition (+/- 12 semitones).
        """
        settings = cls.get_level_settings(strictness_level)
        r = role.lower()
        p = int(pitch)

        # 1. Bass / 808 / Sub
        if "sub" in r:
            min_p, max_p = 24, 46  # C1 to Bb2
        elif "808" in r or "bass" in r:
            min_p, max_p = 28, settings.get("max_bass_pitch", 48)  # E1 to C3
        # 2. Brass Family
        elif any(k in r for k in ("trombone", "trombón")):
            min_p, max_p = 40, 65  # E2 to F4
        elif any(k in r for k in ("french horn", "corno", "horn")):
            min_p, max_p = 41, 69  # F2 to A4
        elif any(k in r for k in ("brass", "trumpet", "trompeta", "flugelhorn")):
            min_p, max_p = settings.get("min_brass_pitch", 55), settings.get("max_brass_pitch", 84)  # G3 to C6
        # 3. Woodwinds & Reeds
        elif any(k in r for k in ("tenor sax", "saxo tenor")):
            min_p, max_p = 44, 75  # Ab2 to Eb5
        elif any(k in r for k in ("alto sax", "saxo alto", "sax")):
            min_p, max_p = 49, 80  # Db3 to Ab5
        elif any(k in r for k in ("flute", "flauta")):
            min_p, max_p = 60, 96  # C4 to C7
        # 4. Strings Family
        elif any(k in r for k in ("cello", "violonchelo")):
            min_p, max_p = 36, 72  # C2 to C5
        elif any(k in r for k in ("viola",)):
            min_p, max_p = 48, 88  # C3 to E6
        elif any(k in r for k in ("violin", "violín", "strings", "cuerdas")):
            min_p, max_p = 55, 100  # G3 to E7
        # 5. Leads / Melodies / Toplines
        elif any(k in r for k in ("lead", "melody", "topline", "vocal_chop", "hook")):
            min_p, max_p = settings.get("min_lead_pitch", 55), 100
        # 6. Keys / Chords / Pads
        elif any(k in r for k in ("pad", "choir", "atmosphere")):
            min_p, max_p = 48, 88  # C3 to E6
        elif any(k in r for k in ("piano", "keys", "rhodes", "guitar", "acorde")):
            min_p, max_p = 36, 96  # C2 to C7
        else:
            return p

        while p < min_p:
            p += 12
        while p > max_p:
            p -= 12
        return p

    @classmethod
    def enforce_safe_tessitura_dict(
        cls,
        dict_notes: List[Dict[str, Any]],
        role: str,
        strictness_level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Safely transposes dictionary notes into valid acoustic tessituras without mutating original references.
        """
        if not dict_notes:
            return []
        corrected = []
        for n in dict_notes:
            n_copy = dict(n)
            raw_pitch = n_copy.get("pitch", 60)
            n_copy["pitch"] = cls.clamp_single_pitch(raw_pitch, role, strictness_level)
            corrected.append(n_copy)
        return corrected

    @classmethod
    def enforce_safe_tessitura(
        cls,
        notes: Any,
        role: str,
        strictness_level: Optional[str] = None
    ) -> Any:
        """
        Automatically transposes offending notes into safe tessitura boundaries.
        Supports both NoteEvent instances and dictionaries.
        """
        if not notes:
            return []

        # Check if first item is dict
        first = notes[0]
        if isinstance(first, dict):
            return cls.enforce_safe_tessitura_dict(notes, role, strictness_level)

        corrected = []
        for n in notes:
            if hasattr(n, "pitch"):
                clamped_p = cls.clamp_single_pitch(n.pitch, role, strictness_level)
                corrected.append(NoteEvent(
                    pitch=clamped_p,
                    start=n.start,
                    duration=n.duration,
                    velocity=n.velocity,
                    channel=getattr(n, "channel", 0),
                    accent=getattr(n, "accent", 0.0)
                ))
            elif isinstance(n, dict):
                n_copy = dict(n)
                n_copy["pitch"] = cls.clamp_single_pitch(n_copy.get("pitch", 60), role, strictness_level)
                corrected.append(n_copy)
            else:
                corrected.append(n)

        return corrected
