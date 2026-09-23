# engine/music/melody/hook_contour.py
"""
Hook Contour & Melodic Psychology Engine (Hook Theory Architecture):
Evaluates and synthesizes commercial-grade topline melodies based on cognitive retention rules:
- Leap-then-Step rule (broad leaps >= 5 semitones resolve by step in opposite direction).
- Vocal range confinement (<= 18 semitones / 1.5 octaves for singable commercial hooks).
- Geometric melodic contours (Arch, Inverted Arch, Ascending Climax, Cascade).
- Mandatory phrasing respiration (breathing pauses between conversational motifs).
- Hook Factor Score (0 to 100) auditing memorability, symmetry, and rhythmic contrast.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import math
import random
import logging

from engine.music.models import NoteEvent
from engine.knowledge.composition.scales import get_scale_notes

logger = logging.getLogger("HookContourEngine")


class HookContourType(str, Enum):
    ARCH = "ARCH"                        # Rises to an emotional crest and resolves down (classic pop/anthem)
    INVERTED_ARCH = "INVERTED_ARCH"      # Dips into intimate low register and surges back up
    ASCENDING_CLIMAX = "ASCENDING_CLIMAX"# Steadily climbs toward apex note before drop/chorus release
    CASCADE = "CASCADE"                  # Starts at peak energy and tumbles down melodically (EDM lead/trap drop)


@dataclass
class HookEvaluationReport:
    """Detailed audit of melodic hook memorability and commercial compliance."""
    score: float                         # 0.0 to 100.0
    is_valid_commercial_hook: bool
    vocal_range_semitones: int
    leap_step_violations: int
    detected_contour: HookContourType
    has_breathing_space: bool
    motif_symmetry_ratio: float          # Ratio of repeating rhythmic/interval patterns
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 1),
            "is_valid_commercial_hook": self.is_valid_commercial_hook,
            "vocal_range_semitones": self.vocal_range_semitones,
            "leap_step_violations": self.leap_step_violations,
            "detected_contour": self.detected_contour.value,
            "has_breathing_space": self.has_breathing_space,
            "motif_symmetry_ratio": round(self.motif_symmetry_ratio, 2),
            "recommendations": self.recommendations
        }


class HookContourEngine:
    """Orchestrates commercial hook synthesis and psychoperceptual melodic validation."""

    MAX_VOCAL_RANGE_SEMITONES: int = 18  # 1.5 octaves
    MIN_BREATHING_BEATS: float = 0.5     # Minimum silence between conversational phrases

    @classmethod
    def detect_contour(cls, notes: List[NoteEvent]) -> HookContourType:
        """Determines the geometric shape of the melodic trajectory."""
        if not notes or len(notes) < 3:
            return HookContourType.ARCH

        pitches = [n.pitch for n in notes]
        n_len = len(pitches)
        first_third = sum(pitches[:n_len // 3]) / max(1, n_len // 3)
        mid_third = sum(pitches[n_len // 3: 2 * n_len // 3]) / max(1, n_len // 3)
        last_third = sum(pitches[2 * n_len // 3:]) / max(1, len(pitches) - (2 * n_len // 3))

        if mid_third > first_third and mid_third > last_third:
            return HookContourType.ARCH
        elif mid_third < first_third and mid_third < last_third:
            return HookContourType.INVERTED_ARCH
        elif last_third > first_third:
            return HookContourType.ASCENDING_CLIMAX
        else:
            return HookContourType.CASCADE

    @classmethod
    def evaluate_hook(
        cls,
        notes: List[NoteEvent],
        scale_pitches: Optional[List[int]] = None
    ) -> HookEvaluationReport:
        """
        Audits a melody against commercial hook standards.
        Returns score from 0.0 to 100.0 and actionable diagnoses.
        """
        if not notes:
            return HookEvaluationReport(
                score=0.0,
                is_valid_commercial_hook=False,
                vocal_range_semitones=0,
                leap_step_violations=0,
                detected_contour=HookContourType.ARCH,
                has_breathing_space=False,
                motif_symmetry_ratio=0.0,
                recommendations=["No hay notas para evaluar el gancho."]
            )

        sorted_notes = sorted(notes, key=lambda n: n.start)
        pitches = [n.pitch for n in sorted_notes]
        p_min, p_max = min(pitches), max(pitches)
        vocal_range = p_max - p_min

        recommendations = []
        score = 100.0

        # 1. Range Check (max 18 semitones / 1.5 octaves)
        if vocal_range > cls.MAX_VOCAL_RANGE_SEMITONES:
            penalty = min(25.0, (vocal_range - cls.MAX_VOCAL_RANGE_SEMITONES) * 4.0)
            score -= penalty
            recommendations.append(
                f"Rango melódico excesivo ({vocal_range} semitonos > 18 permitidos). Dificulta la retención y canto comercial."
            )

        # 2. Leap-then-Step Rule
        # A leap of >= 5 semitones (fourth or wider) must be followed by a step in opposite direction
        violations = 0
        for i in range(len(pitches) - 2):
            interval_1 = pitches[i + 1] - pitches[i]
            interval_2 = pitches[i + 2] - pitches[i + 1]
            if abs(interval_1) >= 5:
                # If leap was upward, step should be downward (interval_2 < 0) and small (abs <= 4)
                if interval_1 > 0 and (interval_2 >= 0 or abs(interval_2) > 4):
                    violations += 1
                # If leap was downward, step should be upward (interval_2 > 0) and small (abs <= 4)
                elif interval_1 < 0 and (interval_2 <= 0 or abs(interval_2) > 4):
                    violations += 1

        if violations > 0:
            score -= min(30.0, violations * 8.0)
            recommendations.append(
                f"Se detectaron {violations} violaciones de la regla 'salto y paso' (saltos amplios sin resolución contraria)."
            )

        # 3. Phrasing Respiration (gaps between notes)
        has_breath = False
        for i in range(len(sorted_notes) - 1):
            curr_end = sorted_notes[i].start + sorted_notes[i].duration
            next_start = sorted_notes[i + 1].start
            gap = next_start - curr_end
            if gap >= cls.MIN_BREATHING_BEATS:
                has_breath = True
                break

        if not has_breath and len(sorted_notes) >= 6:
            score -= 20.0
            recommendations.append("Melodía continua sin respiración mecánica. Falta de silencios para articulación vocal.")

        # 4. Motif Symmetry & Repetition
        # Evaluate rhythmic interval matching across 2-bar cells
        durations = [round(n.duration, 2) for n in sorted_notes]
        half = len(durations) // 2
        symmetry_matches = 0
        if half >= 2:
            for j in range(half):
                if abs(durations[j] - durations[half + j]) < 0.1:
                    symmetry_matches += 1
            symmetry_ratio = symmetry_matches / float(half)
        else:
            symmetry_ratio = 0.5

        if symmetry_ratio < 0.35 and len(sorted_notes) >= 8:
            score -= 15.0
            recommendations.append("Baja simetría rítmica entre motivos. Disminuye la memorabilidad del gancho.")

        contour = cls.detect_contour(sorted_notes)
        final_score = max(0.0, min(100.0, score))
        is_valid = final_score >= 65.0 and vocal_range <= cls.MAX_VOCAL_RANGE_SEMITONES

        return HookEvaluationReport(
            score=final_score,
            is_valid_commercial_hook=is_valid,
            vocal_range_semitones=vocal_range,
            leap_step_violations=violations,
            detected_contour=contour,
            has_breathing_space=has_breath,
            motif_symmetry_ratio=symmetry_ratio,
            recommendations=recommendations
        )

    @classmethod
    def generate_hook_motif(
        cls,
        key_root: str = "F",
        scale: str = "natural_minor",
        start_beat: float = 0.0,
        contour: HookContourType = HookContourType.ARCH,
        energy_level: float = 0.85,
        phrase_seed: int = 42
    ) -> List[NoteEvent]:
        """
        Synthesizes an 8-bar (32-beat) commercial hook strictly obeying Hook Theory:
        - Symmetric Call-and-Response structure with breathing gaps.
        - Governed Leap-then-Step mechanics on apex leaps.
        - Guaranteed vocal range confinement (<= 16 semitones).
        """
        rng = random.Random(phrase_seed)
        notes: List[NoteEvent] = []

        # Build scale note pool in octave 4 & 5
        clean_scale = str(scale or "minor_natural").lower().replace("-", "_")
        if clean_scale in ("natural_minor", "minor", "menor"):
            clean_scale = "minor_natural"
        elif clean_scale in ("major", "mayor"):
            clean_scale = "major"
        elif clean_scale not in ("minor_natural", "pentatonic_minor", "blues", "dorian", "harmonic_minor", "phrygian", "major", "pentatonic_major"):
            clean_scale = "minor_natural"
        try:
            scale_degree_names = get_scale_notes(key_root, clean_scale)
        except Exception:
            scale_degree_names = []
        name_to_midi = {
            "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4,
            "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9,
            "A#": 10, "Bb": 10, "B": 11
        }
        root_pitch_class = name_to_midi.get(key_root.upper(), 5) # Default F

        oct4_base = 60 + root_pitch_class
        if oct4_base > 71:
            oct4_base -= 12 # Keep root in 60-71 range

        # Scale degrees relative to root: 1, 2, b3/3, 4, 5, b6/6, b7/7
        scale_intervals = [0, 2, 3 if "minor" in scale.lower() else 4, 5, 7, 8 if "minor" in scale.lower() else 9, 10 if "minor" in scale.lower() else 11]
        pool = []
        for oct_shift in [0, 12]:
            for iv in scale_intervals:
                p = oct4_base + oct_shift + iv
                if p not in pool:
                    pool.append(p)
        pool = sorted(pool)

        # Tonic, 3rd, 5th, Apex
        deg_1 = pool[0] # Root
        deg_2 = pool[1]
        deg_3 = pool[2]
        deg_4 = pool[3]
        deg_5 = pool[4]
        deg_apex = pool[min(len(pool) - 1, 7)] # Upper register octave tonic or 7th

        # 1. QUESTION / CALL (Bars 1-2, Beats 0 to 7.0)
        # Upward motif ending on unstable degree 2 or 5
        notes.append(NoteEvent(pitch=deg_1, start=start_beat + 0.5, duration=0.75, velocity=int(85 * energy_level)))
        notes.append(NoteEvent(pitch=deg_3, start=start_beat + 1.5, duration=1.00, velocity=int(90 * energy_level)))
        notes.append(NoteEvent(pitch=deg_4, start=start_beat + 3.0, duration=0.75, velocity=int(88 * energy_level)))
        notes.append(NoteEvent(pitch=deg_5, start=start_beat + 4.5, duration=2.00, velocity=int(98 * energy_level)))
        # Breath gap: 6.5 to 8.0 (1.5 beats)

        # 2. ANSWER / RESPONSE (Bars 3-4, Beats 8 to 15.0)
        # Symmetrical downward resolution resolving to tonic with trailing breath
        notes.append(NoteEvent(pitch=deg_5, start=start_beat + 8.5, duration=0.75, velocity=int(92 * energy_level)))
        notes.append(NoteEvent(pitch=deg_4, start=start_beat + 9.5, duration=1.00, velocity=int(88 * energy_level)))
        notes.append(NoteEvent(pitch=deg_3, start=start_beat + 11.0, duration=1.25, velocity=int(85 * energy_level)))
        notes.append(NoteEvent(pitch=deg_1, start=start_beat + 12.5, duration=2.25, velocity=int(95 * energy_level)))
        # Breath gap: 14.75 to 16.0 (1.25 beats)

        # 3. CLIMAX / APEX with Leap-then-Step (Bars 5-6, Beats 16 to 23.0)
        # Leaps to apex, immediately resolves downward by step
        notes.append(NoteEvent(pitch=deg_4, start=start_beat + 16.5, duration=0.50, velocity=int(90 * energy_level)))
        # Leap upward (deg_4 -> deg_apex >= 5 st)
        notes.append(NoteEvent(pitch=deg_apex, start=start_beat + 17.5, duration=1.75, velocity=min(127, int(112 * energy_level))))
        # Governed Step downward in opposite direction
        deg_step_down = pool[max(0, pool.index(deg_apex) - 1)]
        notes.append(NoteEvent(pitch=deg_step_down, start=start_beat + 20.0, duration=0.75, velocity=int(96 * energy_level)))
        notes.append(NoteEvent(pitch=deg_5, start=start_beat + 21.25, duration=1.75, velocity=int(94 * energy_level)))
        # Breath gap: 23.0 to 24.0 (1.0 beat)

        # 4. RESOLUTION CADENCE (Bars 7-8, Beats 24 to 31.0)
        notes.append(NoteEvent(pitch=deg_3, start=start_beat + 24.5, duration=0.75, velocity=int(88 * energy_level)))
        notes.append(NoteEvent(pitch=deg_2, start=start_beat + 25.5, duration=0.75, velocity=int(84 * energy_level)))
        notes.append(NoteEvent(pitch=deg_1, start=start_beat + 26.75, duration=3.25, velocity=int(96 * energy_level)))
        # Breath gap: 30.0 to 32.0 (2.0 beats trailing breath)

        return notes
