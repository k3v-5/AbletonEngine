# engine/performance/phrase_breathing.py
"""
Phrase Breathing Engine (Nivel T3):
Analyzes melodic and harmonic phrase morphology:
Preparation -> Tension/Ascent -> Climax/Arrival -> Resolution -> Breath Gap

Applies musical phrasing:
- Arrival/Target notes: increased velocity (+10-18), slight rubato lag (+3-8ms), longer sustain.
- Tension notes: subtle forward push (-2 to -4ms) and swell.
- Final phrase notes: trim release to enforce guaranteed breath gap (>= 35ms) before next phrase.
- Preserves structural melody integrity and functional chord harmony.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Dict, List, Any, Optional, Tuple

from .models import (
    PerformanceIntent,
    InstrumentPerformanceProfile,
)


@dataclass
class PhraseSegment:
    """Represents a coherent melodic or harmonic musical phrase."""
    phrase_id: int
    notes: List[Dict[str, Any]]
    start_beat: float
    end_beat: float
    climax_note_idx: int
    final_note_idx: int


class PhraseBreathingEngine:
    """
    Detects musical phrases and applies physiological breathing contours.
    """

    @classmethod
    def segment_into_phrases(
        cls,
        notes: List[Dict[str, Any]],
        min_rest_gap_beats: float = 0.75
    ) -> List[PhraseSegment]:
        """
        Groups chronological notes into phrases demarcated by rests or structural phrase lengths.
        """
        if not notes:
            return []

        sorted_notes = sorted(
            notes,
            key=lambda x: float(x.get("start_time", x.get("start", x.get("time", 0.0))))
        )

        phrases: List[List[Dict[str, Any]]] = []
        current_phrase: List[Dict[str, Any]] = [sorted_notes[0]]

        for i in range(1, len(sorted_notes)):
            prev_n = sorted_notes[i - 1]
            curr_n = sorted_notes[i]

            prev_start = float(prev_n.get("start_time", prev_n.get("start", 0.0)))
            prev_dur = float(prev_n.get("duration", 0.5))
            prev_end = prev_start + prev_dur

            curr_start = float(curr_n.get("start_time", curr_n.get("start", 0.0)))
            rest_gap = curr_start - prev_end

            # Boundary condition: rest gap exceeds threshold or phrase spans > 4 bars (16 beats)
            curr_phrase_span = curr_start - float(current_phrase[0].get("start_time", 0.0))
            if rest_gap >= min_rest_gap_beats or curr_phrase_span >= 16.0:
                phrases.append(current_phrase)
                current_phrase = [curr_n]
            else:
                current_phrase.append(curr_n)

        if current_phrase:
            phrases.append(current_phrase)

        segments: List[PhraseSegment] = []
        for idx, p_notes in enumerate(phrases):
            start_b = float(p_notes[0].get("start_time", 0.0))
            last_n = p_notes[-1]
            end_b = float(last_n.get("start_time", 0.0)) + float(last_n.get("duration", 0.5))

            # Climax note: prefer highest pitch; if tied, longest duration
            climax_idx = 0
            best_score = -1
            for n_i, n in enumerate(p_notes):
                pitch = int(n.get("pitch", 60))
                dur = float(n.get("duration", 0.5))
                score = pitch * 10 + dur
                if score > best_score:
                    best_score = score
                    climax_idx = n_i

            segments.append(PhraseSegment(
                phrase_id=idx,
                notes=p_notes,
                start_beat=start_b,
                end_beat=end_b,
                climax_note_idx=climax_idx,
                final_note_idx=len(p_notes) - 1
            ))

        return segments

    @classmethod
    def apply_phrase_breathing(
        cls,
        notes: List[Dict[str, Any]],
        profile: InstrumentPerformanceProfile,
        intent: PerformanceIntent,
        bpm: float = 120.0
    ) -> List[Dict[str, Any]]:
        """
        Applies melodic breathing, tension push, target note weight, and final breath gaps.
        """
        if not notes or not profile.phrase_breathing_enabled:
            return notes

        ms_per_beat = (60.0 / max(20.0, bpm)) * 1000.0
        beats_per_ms = 1.0 / ms_per_beat
        min_gap_beats = (profile.min_breath_gap_ms or 35.0) * beats_per_ms

        segments = cls.segment_into_phrases(notes)
        processed_notes: List[Dict[str, Any]] = []

        for seg_idx, segment in enumerate(segments):
            p_notes = [dict(n) for n in segment.notes]
            total_in_phrase = len(p_notes)
            climax_i = segment.climax_note_idx

            for i, n in enumerate(p_notes):
                cur_start = float(n.get("start_time", n.get("start", 0.0)))
                cur_dur = float(n.get("duration", 0.5))
                cur_vel = int(n.get("velocity", 90))

                # Check if it's an ornamental / ghost note
                is_ornamental = cur_vel <= 45 or cur_dur <= 0.125

                if is_ornamental:
                    # Ornamental: lighter velocity, no lag
                    n["velocity"] = max(1, min(127, int(cur_vel * 0.9)))
                    continue

                if i == climax_i:
                    # TARGET / ARRIVAL NOTE
                    # Higher velocity weight (+10 to +18)
                    vel_boost = int(14.0 * intent.human_factor)
                    n["velocity"] = min(127, cur_vel + vel_boost)

                    # Rubato lag (+3 to +8 ms)
                    lag_ms = 5.0 * intent.human_factor
                    new_start = cur_start + (lag_ms * beats_per_ms)
                    n["start_time"] = round(new_start, 5)
                    n["time"] = n["start_time"]

                    # Slight duration extension (+6%)
                    n["duration"] = round(cur_dur * 1.06, 5)

                elif i < climax_i:
                    # PREPARATION & TENSION / ASCENT
                    # Forward push (-2 to -4 ms) and gentle crescendo
                    progress = (i + 1) / max(1, climax_i + 1)
                    push_ms = (-3.0 * intent.phrase_push * progress) * intent.human_factor
                    new_start = max(0.0, cur_start + (push_ms * beats_per_ms))
                    n["start_time"] = round(new_start, 5)
                    n["time"] = n["start_time"]

                    vel_delta = int(progress * 8.0 * intent.human_factor)
                    n["velocity"] = max(1, min(127, cur_vel + vel_delta))

                else:
                    # RESOLUTION
                    # Natural diminuendo towards phrase resting point
                    resolve_progress = (i - climax_i) / max(1, total_in_phrase - climax_i)
                    vel_drop = int(resolve_progress * 8.0 * intent.human_factor)
                    n["velocity"] = max(1, min(127, cur_vel - vel_drop))

            # ENFORCE GUARANTEED BREATH GAP on the final note of the phrase
            final_note = p_notes[-1]
            final_start = float(final_note.get("start_time", final_note.get("start", 0.0)))
            final_dur = float(final_note.get("duration", 0.5))

            # Next phrase start time (if exists)
            if seg_idx < len(segments) - 1:
                next_seg = segments[seg_idx + 1]
                next_start = float(next_seg.notes[0].get("start_time", next_seg.notes[0].get("start", 0.0)))
                nominal_gap = next_start - (final_start + final_dur)

                if nominal_gap < min_gap_beats:
                    # Trim duration to leave guaranteed breath silence
                    available_space = next_start - final_start
                    new_final_dur = max(0.08, available_space - min_gap_beats)
                    final_note["duration"] = round(new_final_dur, 5)
            else:
                # Last phrase of section: shorten final note slightly so it doesn't slam into boundary
                shorten_beats = 0.04 * intent.human_factor
                final_note["duration"] = round(max(0.08, final_dur - shorten_beats), 5)

            processed_notes.extend(p_notes)

        return processed_notes
