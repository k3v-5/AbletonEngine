# engine/performance/core.py
"""
Performance Core (Nivel T1):
Executes fundamental expressive humanization:
- Role-calibrated microtiming displacement.
- Velocity hierarchy (metric downbeats vs subdivisions).
- Chord strumming and top-voice melody accentuation.
- Articulation shaping (staccato, legato, breathing duration).
- Atomic PerformanceSnapshots with 0 ms instant rollback.
"""
from __future__ import annotations

import copy
import math
import random
import time
from typing import Dict, List, Any, Optional, Tuple

from .models import (
    PerformanceIntent,
    InstrumentPerformanceProfile,
    PerformanceSnapshot,
    PocketTendency,
    VelocityProfile,
    ArticulationStyle,
)


class PerformanceCore:
    """
    Core engine executing music-theoretically sound performance modeling on MIDI notes.
    """

    @classmethod
    def create_snapshot(
        cls,
        tracks_notes: Dict[str, List[Dict[str, Any]]]
    ) -> PerformanceSnapshot:
        """Captures an atomic, immutable snapshot of note collections."""
        copied = copy.deepcopy(tracks_notes)
        return PerformanceSnapshot(
            tracks_notes=copied,
            timestamp=time.time()
        )

    @classmethod
    def restore_snapshot(
        cls,
        snapshot: PerformanceSnapshot
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Restores the exact original note state in 0 ms."""
        return copy.deepcopy(snapshot.tracks_notes)

    @classmethod
    def apply_microtiming_intent(
        cls,
        notes: List[Dict[str, Any]],
        profile: InstrumentPerformanceProfile,
        intent: PerformanceIntent,
        bpm: float = 120.0,
        seed: Optional[int] = 42
    ) -> List[Dict[str, Any]]:
        """
        Displaces note start times based on intentional pocket, role constraints, and human factor.
        """
        if not notes:
            return []

        rng = random.Random(seed)
        ms_per_beat = (60.0 / max(20.0, bpm)) * 1000.0
        beats_per_ms = 1.0 / ms_per_beat

        # Base role variance scaled by intent
        effective_variance_ms = profile.timing_variance_ms * intent.human_factor
        if intent.pocket == PocketTendency.ON_THE_GRID:
            effective_variance_ms = min(effective_variance_ms, 1.0)
        elif intent.pocket == PocketTendency.LOOSE_DRAG:
            effective_variance_ms *= 1.3

        # Macro pocket offset in ms
        macro_offset_ms = 0.0
        if intent.pocket == PocketTendency.LAID_BACK:
            macro_offset_ms += (profile.laid_back_tendency_ms or 8.0) * intent.human_factor
        elif intent.pocket == PocketTendency.DRIVING_PUSH:
            macro_offset_ms -= 5.0 * intent.human_factor

        humanized = []
        for n in notes:
            new_n = dict(n)
            cur_start = float(n.get("start_time", n.get("start", n.get("time", 0.0))))
            vel = int(n.get("velocity", 90))

            # Anchors have strict jitter dampening
            if profile.is_groove_anchor:
                jitter_ms = rng.gauss(0.0, min(1.2, effective_variance_ms))
            else:
                # High velocity notes anticipate slightly; ghost notes have wider jitter
                vel_factor = 1.0 - (vel / 127.0 - 0.5) * 0.5
                jitter_ms = rng.gauss(0.0, effective_variance_ms * vel_factor)
                if vel > 105:
                    jitter_ms -= 1.5 * intent.human_factor

            total_offset_ms = macro_offset_ms + jitter_ms
            offset_beats = total_offset_ms * beats_per_ms

            new_start = max(0.0, cur_start + offset_beats)
            new_n["start_time"] = round(new_start, 5)
            new_n["time"] = round(new_start, 5)
            humanized.append(new_n)

        return humanized

    @classmethod
    def apply_velocity_hierarchy(
        cls,
        notes: List[Dict[str, Any]],
        profile: InstrumentPerformanceProfile,
        intent: PerformanceIntent,
        seed: Optional[int] = 42
    ) -> List[Dict[str, Any]]:
        """
        Applies musical velocity contours, metric pulse weighting, and role dynamics.
        """
        if not notes:
            return []

        rng = random.Random(seed)
        v_profile = intent.velocity_profile

        humanized = []
        for n in notes:
            new_n = dict(n)
            start_t = float(n.get("start_time", n.get("start", n.get("time", 0.0))))
            orig_vel = int(n.get("velocity", 90))

            if v_profile == VelocityProfile.FLAT_BED:
                # Narrow dispersion (pads/textures)
                delta = rng.gauss(0.0, min(2.5, profile.velocity_variance * 0.3))
                target_vel = orig_vel + delta

            elif v_profile == VelocityProfile.TIERED_PULSE:
                # Downbeat and metric hierarchy
                sub_beat = round(start_t % 1.0, 3)
                if sub_beat == 0.0:
                    accent = +12.0 * intent.human_factor
                elif sub_beat in [0.5, 0.25, 0.75]:
                    accent = +4.0 * intent.human_factor if sub_beat == 0.5 else -4.0 * intent.human_factor
                else:
                    accent = -8.0 * intent.human_factor

                delta = rng.gauss(accent, profile.velocity_variance * 0.5)
                target_vel = orig_vel + delta

            elif v_profile == VelocityProfile.EXPRESSIVE or v_profile == VelocityProfile.RUBATO_BREATHING:
                # Full dynamic range with wrist physics / human touch
                metric_weight = 8.0 if round(start_t % 1.0, 3) == 0.0 else 0.0
                delta = rng.gauss(metric_weight, profile.velocity_variance * intent.human_factor)
                target_vel = orig_vel + delta

            else:
                # SUBTLE_DYNAMIC default
                delta = rng.gauss(0.0, profile.velocity_variance * 0.4 * intent.human_factor)
                target_vel = orig_vel + delta

            final_vel = int(round(max(1, min(127, target_vel))))
            new_n["velocity"] = final_vel
            humanized.append(new_n)

        return humanized

    @classmethod
    def apply_chord_strumming(
        cls,
        notes: List[Dict[str, Any]],
        profile: InstrumentPerformanceProfile,
        bpm: float = 120.0,
        direction: str = "UP"  # "UP" = low to high, "DOWN" = high to low
    ) -> List[Dict[str, Any]]:
        """
        Micro-spreads simultaneous chord notes across time with physical touch hierarchy.
        The top melody note receives intentional velocity boost.
        """
        if not notes or profile.strum_spread_ms <= 0.0:
            return notes

        ms_per_beat = (60.0 / max(20.0, bpm)) * 1000.0
        beats_per_ms = 1.0 / ms_per_beat

        # Group notes by simultaneous start beat (tolerance 0.015 beats)
        clusters: Dict[float, List[Dict[str, Any]]] = {}
        for n in notes:
            st = float(n.get("start_time", n.get("start", n.get("time", 0.0))))
            # Snap to cluster key
            matched_key = None
            for k in clusters.keys():
                if abs(k - st) < 0.015:
                    matched_key = k
                    break
            if matched_key is None:
                matched_key = round(st, 4)
                clusters[matched_key] = []
            clusters[matched_key].append(n)

        result: List[Dict[str, Any]] = []
        for cluster_time, cluster_notes in clusters.items():
            if len(cluster_notes) <= 1:
                result.extend(cluster_notes)
                continue

            # Sort by pitch
            sorted_by_pitch = sorted(
                cluster_notes,
                key=lambda x: int(x.get("pitch", 60))
            )
            if direction == "DOWN":
                sorted_by_pitch.reverse()

            num_voices = len(sorted_by_pitch)
            step_spread_ms = profile.strum_spread_ms / max(1, num_voices - 1)
            highest_pitch = max(int(n.get("pitch", 60)) for n in cluster_notes)

            for idx, note in enumerate(sorted_by_pitch):
                new_n = dict(note)
                offset_ms = idx * step_spread_ms
                offset_beats = offset_ms * beats_per_ms

                cur_start = float(note.get("start_time", note.get("start", note.get("time", 0.0))))
                new_start = cur_start + offset_beats
                new_n["start_time"] = round(new_start, 5)
                new_n["time"] = round(new_start, 5)

                # Top-voice melody accentuation
                p = int(note.get("pitch", 60))
                if p == highest_pitch and profile.strum_top_note_accent > 0:
                    v = int(note.get("velocity", 90))
                    new_n["velocity"] = min(127, v + profile.strum_top_note_accent)

                result.append(new_n)

        # Preserve chronological order
        result.sort(key=lambda x: float(x.get("start_time", x.get("time", 0.0))))
        return result

    @classmethod
    def apply_articulation_shaping(
        cls,
        notes: List[Dict[str, Any]],
        profile: InstrumentPerformanceProfile,
        intent: PerformanceIntent,
        seed: Optional[int] = 42
    ) -> List[Dict[str, Any]]:
        """
        Shapes note durations to prevent hyper-quantized, rectangular gate feel.
        """
        if not notes:
            return []

        rng = random.Random(seed)
        style = intent.articulation

        humanized = []
        for n in notes:
            new_n = dict(n)
            dur = float(n.get("duration", 0.5))

            if style == ArticulationStyle.TIGHT_STACCATO:
                # Crisp release: 50% to 70% of nominal length
                dur_factor = rng.uniform(0.50, 0.70)
            elif style == ArticulationStyle.LEGATO_SLURRED:
                # Slight overlap: 102% to 110%
                dur_factor = rng.uniform(1.02, 1.10)
            elif style == ArticulationStyle.NATURAL_BREATHING:
                # Subtle organic variation (+/- 4%)
                dur_factor = rng.uniform(0.94, 1.02)
            else:
                dur_factor = 1.0

            new_dur = max(0.04, dur * dur_factor)
            new_n["duration"] = round(new_dur, 5)
            humanized.append(new_n)

        return humanized

    @classmethod
    def humanize_track_notes(
        cls,
        notes: List[Dict[str, Any]],
        role: str,
        profile: Optional[InstrumentPerformanceProfile] = None,
        intent: Optional[PerformanceIntent] = None,
        bpm: float = 120.0,
        seed: Optional[int] = 42
    ) -> List[Dict[str, Any]]:
        """
        Master pass over a single track's notes executing T1 humanization:
        Microtiming -> Velocity Hierarchy -> Chord Strumming -> Articulation Shaping.
        """
        prof = profile or InstrumentPerformanceProfile.create_default(role)
        intnt = intent or PerformanceIntent()

        step1 = cls.apply_microtiming_intent(notes, prof, intnt, bpm=bpm, seed=seed)
        step2 = cls.apply_velocity_hierarchy(step1, prof, intnt, seed=seed)
        step3 = cls.apply_chord_strumming(step2, prof, bpm=bpm)
        step4 = cls.apply_articulation_shaping(step3, prof, intnt, seed=seed)

        return step4
