# engine/music/harmony/vertical_harmonic_validator.py
"""
Vertical Harmonic Validator:
Report-only validator that inspects simultaneous sounding notes across active tracks.
CRITICAL INVARIANT: This module is strictly read-only and NEVER mutates note events.

Capabilities:
1. Detects consonances (unisons, octaves, 3rds, 5ths, 6ths).
2. Distinguishes allowed musical tensions (9ths, 11ths, 13ths, maj7ths) from harsh clashes.
3. Detects harsh acoustic collisions (minor 2nds/flat 9ths between bass and melody,
   unresolved minor 9ths, low-interval limit violations below C2/MIDI 36).
4. Generates a comprehensive, transparent audit report with consonance ratio,
   detailed clash list, severity ratings, and actionable arrangement suggestions.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Union
import math
import logging

from engine.music.models import NoteEvent

logger = logging.getLogger("VerticalHarmonicValidator")


@dataclass
class HarmonicClashEvent:
    """Detailed record of a vertical acoustic clash between sounding notes."""
    beat: float
    track_a: str
    track_b: str
    pitch_a: int
    pitch_b: int
    pitch_name_a: str
    pitch_name_b: str
    interval_semitones: int
    simple_interval: int
    severity: str  # "HIGH", "MEDIUM", "LOW"
    clash_type: str  # "MINOR_SECOND_LEAD_BASS", "LOW_INTERVAL_LIMIT", "HARSH_DISSONANCE", "UNRESOLVED_FLAT_NINE"
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "beat": round(self.beat, 3),
            "track_a": self.track_a,
            "track_b": self.track_b,
            "pitch_a": self.pitch_a,
            "pitch_b": self.pitch_b,
            "pitch_name_a": self.pitch_name_a,
            "pitch_name_b": self.pitch_name_b,
            "interval_semitones": self.interval_semitones,
            "simple_interval": self.simple_interval,
            "severity": self.severity,
            "clash_type": self.clash_type,
            "description": self.description
        }


@dataclass
class HarmonicTensionEvent:
    """Record of an intentional musical tension (e.g. 9th, 11th, 13th, maj7)."""
    beat: float
    track_a: str
    track_b: str
    pitch_a: int
    pitch_b: int
    tension_type: str  # "MAJOR_NINTH", "PERFECT_ELEVENTH", "MAJOR_THIRTEENTH", "MAJOR_SEVENTH", "TRITONE"
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "beat": round(self.beat, 3),
            "track_a": self.track_a,
            "track_b": self.track_b,
            "pitch_a": self.pitch_a,
            "pitch_b": self.pitch_b,
            "tension_type": self.tension_type,
            "description": self.description
        }


@dataclass
class VerticalHarmonicReport:
    """Immutable report summarizing vertical harmonic audit across tracks."""
    total_slices_audited: int = 0
    consonant_slices: int = 0
    consonance_ratio: float = 1.0
    clash_count: int = 0
    tension_count: int = 0
    clashes: List[HarmonicClashEvent] = field(default_factory=list)
    tensions: List[HarmonicTensionEvent] = field(default_factory=list)
    is_acceptable: bool = True
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_slices_audited": self.total_slices_audited,
            "consonant_slices": self.consonant_slices,
            "consonance_ratio": round(self.consonance_ratio, 4),
            "clash_count": self.clash_count,
            "tension_count": self.tension_count,
            "is_acceptable": self.is_acceptable,
            "clashes": [c.to_dict() for c in self.clashes],
            "tensions": [t.to_dict() for t in self.tensions],
            "summary": self.summary
        }


class VerticalHarmonicValidator:
    """
    Simultaneous sounding note auditor.
    Strictly report-only: evaluates vertical harmony without modifying note data.
    """

    NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    # Low Interval Limits: below these MIDI note numbers, specific intervals sound muddy/distorted
    LOW_INTERVAL_LIMITS: Dict[int, int] = {
        1: 48,   # Minor 2nd: muddy below C3 (MIDI 48)
        2: 45,   # Major 2nd: muddy below A2 (MIDI 45)
        3: 41,   # Minor 3rd: muddy below F2 (MIDI 41)
        4: 38,   # Major 3rd: muddy below D2 (MIDI 38)
        5: 36,   # Perfect 4th: muddy below C2 (MIDI 36)
        6: 38,   # Tritone: muddy below D2 (MIDI 38)
        7: 31,   # Perfect 5th: clear down to G1 (MIDI 31)
    }

    @classmethod
    def midi_to_name(cls, midi_pitch: int) -> str:
        """Converts MIDI pitch (0-127) to standard note name with octave (e.g. C3, F#4)."""
        octave = (midi_pitch // 12) - 1
        name = cls.NOTE_NAMES[midi_pitch % 12]
        return f"{name}{octave}"

    @classmethod
    def classify_interval(cls, pitch_low: int, pitch_high: int) -> Dict[str, Any]:
        """
        Classifies the acoustic interval between two pitches.
        Returns interval semitones, pitch class distance, and acoustic category.
        """
        if pitch_low > pitch_high:
            pitch_low, pitch_high = pitch_high, pitch_low
        diff = pitch_high - pitch_low
        simple_interval = diff % 12
        compound_octaves = diff // 12

        # Categories: CONSONANCE, ALLOWED_TENSION, CLASH
        is_unison_or_octave = simple_interval == 0
        is_perfect_fifth = simple_interval == 7
        is_third = simple_interval in (3, 4)
        is_sixth = simple_interval in (8, 9)
        is_fourth = simple_interval == 5
        is_second = simple_interval in (1, 2)
        is_seventh = simple_interval in (10, 11)
        is_tritone = simple_interval == 6

        return {
            "total_semitones": diff,
            "simple_interval": simple_interval,
            "compound_octaves": compound_octaves,
            "is_unison_or_octave": is_unison_or_octave,
            "is_perfect_fifth": is_perfect_fifth,
            "is_third": is_third,
            "is_sixth": is_sixth,
            "is_fourth": is_fourth,
            "is_second": is_second,
            "is_seventh": is_seventh,
            "is_tritone": is_tritone,
        }

    @classmethod
    def audit_tracks(
        cls,
        track_notes: Dict[str, List[Union[NoteEvent, Dict[str, Any]]]],
        time_step: float = 0.5,
        max_beat: Optional[float] = None,
        min_consonance_ratio: float = 0.70
    ) -> VerticalHarmonicReport:
        """
        Audits vertical harmony across tracks at uniform beat slices.
        DOES NOT mutate any note objects. Returns an immutable VerticalHarmonicReport.

        Args:
            track_notes: Mapping of track_name -> list of NoteEvents or note dicts.
            time_step: Beat resolution for vertical time slicing (default 0.5 beats = 8th notes).
            max_beat: Optional arrangement end beat bound.
            min_consonance_ratio: Threshold for flagging arrangement acceptability.
        """
        if not track_notes:
            return VerticalHarmonicReport(
                total_slices_audited=0,
                consonant_slices=0,
                consonance_ratio=1.0,
                clash_count=0,
                tension_count=0,
                is_acceptable=True,
                summary="No track notes provided for vertical harmonic audit."
            )

        # Normalize notes into standard tuples: (start, end, pitch)
        normalized_tracks: Dict[str, List[Tuple[float, float, int]]] = {}
        highest_end = 0.0

        for t_name, n_list in track_notes.items():
            norm_list = []
            for n in n_list:
                if isinstance(n, NoteEvent):
                    if n.mute:
                        continue
                    start = float(n.start)
                    dur = max(0.01, float(n.duration))
                    p = int(n.pitch)
                elif isinstance(n, dict):
                    if n.get("mute", False):
                        continue
                    start = float(n.get("start", n.get("time", 0.0)))
                    dur = max(0.01, float(n.get("duration", 1.0)))
                    p = int(n.get("pitch", 60))
                else:
                    continue
                end = start + dur
                norm_list.append((start, end, p))
                if end > highest_end:
                    highest_end = end
            normalized_tracks[t_name] = norm_list

        end_beat = max_beat if max_beat is not None else highest_end
        if end_beat <= 0.0:
            return VerticalHarmonicReport(
                total_slices_audited=0,
                consonant_slices=0,
                consonance_ratio=1.0,
                clash_count=0,
                tension_count=0,
                is_acceptable=True,
                summary="Track notes duration is 0 beats."
            )

        total_slices = 0
        consonant_slices = 0
        all_clashes: List[HarmonicClashEvent] = []
        all_tensions: List[HarmonicTensionEvent] = []

        curr_beat = 0.0
        while curr_beat < end_beat:
            total_slices += 1
            # Gather all sounding notes at this beat slice: list of (track_name, pitch)
            sounding: List[Tuple[str, int]] = []
            for t_name, n_list in normalized_tracks.items():
                for start, end, p in n_list:
                    if start <= curr_beat < end:
                        sounding.append((t_name, p))

            # Audit slice if 2 or more notes sound simultaneously
            slice_clashes, slice_tensions = cls._audit_sounding_slice(curr_beat, sounding)
            all_clashes.extend(slice_clashes)
            all_tensions.extend(slice_tensions)

            if len(slice_clashes) == 0:
                consonant_slices += 1

            curr_beat += time_step

        consonance_ratio = (consonant_slices / total_slices) if total_slices > 0 else 1.0
        is_acceptable = (consonance_ratio >= min_consonance_ratio) and (
            len([c for c in all_clashes if c.severity == "HIGH"]) == 0
        )

        summary_parts = [
            f"Audited {total_slices} time slices across {len(track_notes)} tracks.",
            f"Consonance ratio: {consonance_ratio * 100:.1f}%.",
            f"Total vertical clashes detected: {len(all_clashes)} (High severity: {len([c for c in all_clashes if c.severity == 'HIGH'])}).",
            f"Musical tension events: {len(all_tensions)} (allowed extensions/borrowings)."
        ]
        if not is_acceptable:
            summary_parts.append("WARNING: Vertical harmonic audit flagged acoustic clashes exceeding acceptable tolerance.")
        else:
            summary_parts.append("PASS: Vertical harmonic structure conforms to acoustic consonance standards.")

        return VerticalHarmonicReport(
            total_slices_audited=total_slices,
            consonant_slices=consonant_slices,
            consonance_ratio=consonance_ratio,
            clash_count=len(all_clashes),
            tension_count=len(all_tensions),
            clashes=all_clashes,
            tensions=all_tensions,
            is_acceptable=is_acceptable,
            summary=" ".join(summary_parts)
        )

    @classmethod
    def _audit_sounding_slice(
        cls,
        beat: float,
        sounding: List[Tuple[str, int]]
    ) -> Tuple[List[HarmonicClashEvent], List[HarmonicTensionEvent]]:
        """Audits pairwise sounding notes in a single time slice."""
        clashes: List[HarmonicClashEvent] = []
        tensions: List[HarmonicTensionEvent] = []
        if len(sounding) < 2:
            return clashes, tensions

        # Sort by pitch ascending
        sorted_sounding = sorted(sounding, key=lambda x: x[1])

        # Pairwise comparison
        for i in range(len(sorted_sounding)):
            t_a, p_a = sorted_sounding[i]
            for j in range(i + 1, len(sorted_sounding)):
                t_b, p_b = sorted_sounding[j]

                # If same track and same pitch, it's unison on same track - ignore
                if t_a == t_b and p_a == p_b:
                    continue

                diff = p_b - p_a
                simple = diff % 12
                name_a = cls.midi_to_name(p_a)
                name_b = cls.midi_to_name(p_b)

                # Identify track roles heuristically from names
                role_a = cls._heuristic_role(t_a)
                role_b = cls._heuristic_role(t_b)

                # 1. Low Interval Limit Violation
                # When low notes (< MIDI 48) form small intervals, it causes acoustic muddiness
                if p_a < 48 and simple in cls.LOW_INTERVAL_LIMITS:
                    limit_floor = cls.LOW_INTERVAL_LIMITS[simple]
                    if p_a < limit_floor and diff <= 12:
                        clashes.append(HarmonicClashEvent(
                            beat=beat,
                            track_a=t_a,
                            track_b=t_b,
                            pitch_a=p_a,
                            pitch_b=p_b,
                            pitch_name_a=name_a,
                            pitch_name_b=name_b,
                            interval_semitones=diff,
                            simple_interval=simple,
                            severity="HIGH" if p_a < 36 else "MEDIUM",
                            clash_type="LOW_INTERVAL_LIMIT",
                            description=(
                                f"Low Interval Limit violated below {cls.midi_to_name(limit_floor)}: "
                                f"{name_a} and {name_b} ({diff} semitones) muddy the low-end definition."
                            )
                        ))
                        continue

                # 2. Minor Second Clash (1 semitone difference)
                if diff == 1:
                    # Minor 2nd between Bass and Lead/Melody is fatal
                    is_bass_lead = ("BASS" in (role_a, role_b)) and ("LEAD" in (role_a, role_b) or "VOCAL" in (role_a, role_b))
                    severity = "HIGH" if is_bass_lead else "MEDIUM"
                    clashes.append(HarmonicClashEvent(
                        beat=beat,
                        track_a=t_a,
                        track_b=t_b,
                        pitch_a=p_a,
                        pitch_b=p_b,
                        pitch_name_a=name_a,
                        pitch_name_b=name_b,
                        interval_semitones=diff,
                        simple_interval=1,
                        severity=severity,
                        clash_type="MINOR_SECOND_LEAD_BASS" if is_bass_lead else "HARSH_DISSONANCE",
                        description=f"Harsh Minor 2nd clash between {t_a} ({name_a}) and {t_b} ({name_b})."
                    ))
                    continue

                # 3. Flat 9th Clash (13 or compound 13 semitones difference)
                if diff in (13, 25) or (simple == 1 and diff > 1):
                    is_bass_lead = ("BASS" in (role_a, role_b))
                    clashes.append(HarmonicClashEvent(
                        beat=beat,
                        track_a=t_a,
                        track_b=t_b,
                        pitch_a=p_a,
                        pitch_b=p_b,
                        pitch_name_a=name_a,
                        pitch_name_b=name_b,
                        interval_semitones=diff,
                        simple_interval=1,
                        severity="HIGH" if is_bass_lead else "MEDIUM",
                        clash_type="UNRESOLVED_FLAT_NINE",
                        description=f"Acoustic flat 9th collision ({diff} st) between {t_a} ({name_a}) and {t_b} ({name_b})."
                    ))
                    continue

                # 4. Major 2nd / 9th (2, 14, 26 semitones) -> Allowed musical tension
                if simple == 2:
                    tensions.append(HarmonicTensionEvent(
                        beat=beat,
                        track_a=t_a,
                        track_b=t_b,
                        pitch_a=p_a,
                        pitch_b=p_b,
                        tension_type="MAJOR_NINTH" if diff >= 14 else "MAJOR_SECOND",
                        description=f"Pleasing musical color/tension: 9th ({diff} st) between {name_a} and {name_b}."
                    ))
                    continue

                # 5. Tritone (6 semitones, 18 semitones)
                if simple == 6:
                    tensions.append(HarmonicTensionEvent(
                        beat=beat,
                        track_a=t_a,
                        track_b=t_b,
                        pitch_a=p_a,
                        pitch_b=p_b,
                        tension_type="TRITONE",
                        description=f"Harmonic tension: tritone between {name_a} and {name_b}."
                    ))
                    continue

                # 6. Major 7th (11 or 23 semitones)
                if simple == 11:
                    tensions.append(HarmonicTensionEvent(
                        beat=beat,
                        track_a=t_a,
                        track_b=t_b,
                        pitch_a=p_a,
                        pitch_b=p_b,
                        tension_type="MAJOR_SEVENTH",
                        description=f"Expressive jazz/neo-soul tension: Maj7 between {name_a} and {name_b}."
                    ))
                    continue

                # 7. Perfect 11th (17, 29 semitones) or 13th (21, 33 semitones)
                if simple == 5 and diff > 5:
                    tensions.append(HarmonicTensionEvent(
                        beat=beat,
                        track_a=t_a,
                        track_b=t_b,
                        pitch_a=p_a,
                        pitch_b=p_b,
                        tension_type="PERFECT_ELEVENTH",
                        description=f"Allowed modern tension: 11th between {name_a} and {name_b}."
                    ))
                    continue
                elif simple == 9 and diff > 9:
                    tensions.append(HarmonicTensionEvent(
                        beat=beat,
                        track_a=t_a,
                        track_b=t_b,
                        pitch_a=p_a,
                        pitch_b=p_b,
                        tension_type="MAJOR_THIRTEENTH",
                        description=f"Lush modern tension: 13th between {name_a} and {name_b}."
                    ))
                    continue

        return clashes, tensions

    @classmethod
    def _heuristic_role(cls, track_name: str) -> str:
        """Categorizes track into broad musical role from name."""
        tn = track_name.upper()
        if any(k in tn for k in ["BASS", "808", "SUB"]):
            return "BASS"
        elif any(k in tn for k in ["LEAD", "TOPLINE", "SOLO", "MELODY"]):
            return "LEAD"
        elif any(k in tn for k in ["VOCAL", "VOZ", "VOX"]):
            return "VOCAL"
        elif any(k in tn for k in ["CHORD", "PAD", "PIANO", "KEYS", "SYNTH", "HARMONY"]):
            return "HARMONY"
        elif any(k in tn for k in ["DRUM", "KICK", "SNARE", "HAT", "PERC"]):
            return "DRUMS"
        return "OTHER"
