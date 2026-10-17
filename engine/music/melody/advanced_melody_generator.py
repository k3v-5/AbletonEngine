# engine/music/melody/advanced_melody_generator.py
"""
Advanced Expressive Melody Generator:
Implements professional counterpoint and modern commercial songwriting techniques:
1. 6th and 7th dramatic leaps with strict contrary step resolution.
2. Harmonic tension notes (9ths, 11ths, 13ths) with purposeful metric placement.
3. Modal borrowing (préstamos modales) importing evocative color tones from parallel modes.
"""

from typing import List, Dict, Any, Optional, Tuple
import math
import random
from engine.music.models import NoteEvent
from engine.music.theory.notes import normalize_pitch_class, note_to_midi, midi_to_note


class AdvancedMelodyGenerator:
    """Generates expressive, hook-oriented melodies with modal borrowing and counterpoint resolutions."""

    PITCH_CLASS_MAP = {
        "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3,
        "E": 4, "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8,
        "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11
    }

    # Scale intervals relative to root
    SCALE_INTERVALS: Dict[str, List[int]] = {
        "minor": [0, 2, 3, 5, 7, 8, 10],
        "natural_minor": [0, 2, 3, 5, 7, 8, 10],
        "major": [0, 2, 4, 5, 7, 9, 11],
        "dorian": [0, 2, 3, 5, 7, 9, 10],
        "phrygian": [0, 1, 3, 5, 7, 8, 10],
        "lydian": [0, 2, 4, 6, 7, 9, 11],
        "mixolydian": [0, 2, 4, 5, 7, 9, 10],
        "locrian": [0, 1, 3, 5, 6, 8, 10],
        "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
        "melodic_minor": [0, 2, 3, 5, 7, 9, 11],
        "blues": [0, 3, 5, 6, 7, 10],
    }

    # Modal borrowing color tones relative to tonic: (interval, mode_source, name)
    MODAL_BORROW_INTERVALS: Dict[str, List[Tuple[int, str, str]]] = {
        "minor": [
            (9, "Dorian", "Major 6th"),       # Evocative Dorian warmth in minor
            (11, "Harmonic Minor", "Major 7th Leading Tone"), # Sharp leading tone
            (1, "Phrygian", "Minor 2nd"),     # Dark Phrygian tension
            (6, "Lydian/Blues", "Tritone (#4/b5)"), # Blues/Lydian blue note
            (4, "Parallel Major", "Picardy 3rd"),   # Major 3rd uplift
        ],
        "major": [
            (8, "Aeolian", "Minor 6th"),      # Romantic minor 6th drop
            (10, "Mixolydian", "Minor 7th"),  # Groovy Mixolydian subtonic
            (3, "Parallel Minor", "Minor 3rd Blue Note"), # Blues inflection
            (6, "Lydian", "Augmented 4th"),   # Dreamy #4
        ]
    }

    @classmethod
    def get_scale_pool(cls, key_root: str, scale_name: str, base_octave: int = 4, octaves: int = 2) -> List[int]:
        """Builds sorted MIDI pitch pool across specified octaves."""
        root_pc = cls.PITCH_CLASS_MAP.get(key_root.strip().upper(), 5)
        clean_scale = scale_name.strip().lower().replace(" ", "_")
        intervals = cls.SCALE_INTERVALS.get(clean_scale, cls.SCALE_INTERVALS["natural_minor"])

        pool = []
        for oct_idx in range(octaves):
            oct_base = (base_octave + oct_idx + 1) * 12 + root_pc
            for iv in intervals:
                pool.append(oct_base + iv)
        return sorted(list(set(pool)))

    @classmethod
    def generate_advanced_melody(
        cls,
        key_root: str = "F",
        scale: str = "natural_minor",
        total_bars: int = 8,
        start_beat: float = 0.0,
        energy_level: float = 0.85,
        enable_leaps: bool = True,
        enable_tensions: bool = True,
        enable_modal_borrowing: bool = True,
        enable_enclosures: bool = True,
        enable_chromatic_passing: bool = True,
        time_signature: Tuple[int, int] = (4, 4),
        seed: int = 42
    ) -> List[NoteEvent]:
        """
        Generates an expressive melody honoring:
        1. 6th/7th leaps followed immediately by contrary step resolution.
        2. Harmonic tension notes (9ths, 11ths, 13ths) on metric off-beats and suspensions.
        3. Modal borrowing introducing subtle borrowed color tones.
        4. Enclosures (cercamientos cromáticos) and chromatic passing notes.
        5. Native support for compound (6/8, 9/8, 12/8) and irregular (5/4, 7/8, 11/8) meters.
        """
        rng = random.Random(seed)
        root_pc = cls.PITCH_CLASS_MAP.get(key_root.strip().upper(), 5)
        root_midi_oct4 = 60 + root_pc
        if root_midi_oct4 > 71:
            root_midi_oct4 -= 12

        pool = cls.get_scale_pool(key_root, scale, base_octave=4, octaves=2)

        # Dynamic beats per bar based on time signature
        s_num, s_den = time_signature if time_signature else (4, 4)
        beats_per_bar = float(s_num * (4.0 / max(1, s_den)))
        total_beats = float(total_bars * beats_per_bar)
        notes: List[NoteEvent] = []

        curr_beat = start_beat
        prev_pitch = root_midi_oct4
        prev_leap_interval = 0  # Track interval of previous jump

        # Tensions relative to root
        tension_offsets = [14, 17, 21] # 9th, 11th, 13th

        # Borrowed intervals
        is_min = "min" in scale.lower()
        borrow_cand = cls.MODAL_BORROW_INTERVALS["minor"] if is_min else cls.MODAL_BORROW_INTERVALS["major"]

        while curr_beat < (start_beat + total_beats - 0.75):
            measure_pos = (curr_beat - start_beat) % beats_per_bar
            is_downbeat = measure_pos < (0.25 if beats_per_bar >= 3.0 else 0.15)
            is_offbeat = (0.25 * beats_per_bar) <= measure_pos <= (0.85 * beats_per_bar)

            # Check if previous move was a large leap (6th: 8-9 st, 7th: 10-11 st)
            if enable_leaps and abs(prev_leap_interval) in (8, 9, 10, 11):
                # RULE: Mandatory contrary step resolution (step in opposite direction: 1 or 2 semitones)
                step_dir = -1 if prev_leap_interval > 0 else 1
                cand_resolved = prev_pitch + (step_dir * rng.choice([1, 2]))
                # Snap to closest pitch in pool
                target_pitch = min(pool, key=lambda p: abs(p - cand_resolved))
                duration = rng.choice([0.75, 1.0, 1.5]) if beats_per_bar >= 4.0 else rng.choice([0.5, 0.75, 1.0])
                velocity = int(rng.randint(84, 96) * energy_level)
                notes.append(NoteEvent(pitch=target_pitch, start=curr_beat, duration=duration, velocity=velocity))

                prev_leap_interval = target_pitch - prev_pitch
                prev_pitch = target_pitch
                curr_beat += duration + (0.25 if rng.random() < 0.3 else 0.0)
                continue

            # Decide note type
            rand_choice = rng.random()

            # 1. Enclosure (cercamiento cromático - 10% chance)
            if enable_enclosures and rand_choice < 0.10 and not is_downbeat and (curr_beat + 1.25 < start_beat + total_beats):
                target_cand = min(pool, key=lambda p: abs(p - prev_pitch))
                enc_up = target_cand + 1
                enc_down = target_cand - 1
                step_d = 0.25 if beats_per_bar >= 3.0 else 0.33
                vel = int(rng.randint(84, 95) * energy_level)
                notes.append(NoteEvent(pitch=enc_up, start=curr_beat, duration=step_d, velocity=vel))
                notes.append(NoteEvent(pitch=enc_down, start=curr_beat + step_d, duration=step_d, velocity=vel))
                notes.append(NoteEvent(pitch=target_cand, start=curr_beat + (2 * step_d), duration=step_d * 2, velocity=int(vel * 1.1)))
                curr_beat += step_d * 4
                prev_leap_interval = 0
                prev_pitch = target_cand
                continue

            # 2. Chromatic Passing Tone (connecting whole steps - 12% chance)
            elif enable_chromatic_passing and rand_choice < 0.22 and not is_downbeat:
                curr_idx = pool.index(prev_pitch) if prev_pitch in pool else len(pool) // 2
                delta = rng.choice([-1, 1])
                next_idx = max(0, min(len(pool) - 1, curr_idx + delta))
                next_pool_pitch = pool[next_idx]
                if abs(next_pool_pitch - prev_pitch) == 2:
                    passing_pitch = min(prev_pitch, next_pool_pitch) + 1
                    dur_p = 0.25 if beats_per_bar >= 3.0 else 0.33
                    vel = int(rng.randint(80, 92) * energy_level)
                    notes.append(NoteEvent(pitch=passing_pitch, start=curr_beat, duration=dur_p, velocity=vel))
                    notes.append(NoteEvent(pitch=next_pool_pitch, start=curr_beat + dur_p, duration=dur_p * 2, velocity=int(vel * 1.05)))
                    curr_beat += dur_p * 3
                    prev_leap_interval = 0
                    prev_pitch = next_pool_pitch
                    continue

            # 3. Modal Borrowing (15% chance on expressive phrases)
            if enable_modal_borrowing and rand_choice < 0.35 and not is_downbeat:
                borrow_iv, b_source, b_name = rng.choice(borrow_cand)
                borrow_pitch = root_midi_oct4 + borrow_iv
                duration = rng.choice([0.5, 0.75, 1.0])
                velocity = int(rng.randint(92, 105) * energy_level)
                notes.append(NoteEvent(pitch=borrow_pitch, start=curr_beat, duration=duration, velocity=velocity))
                prev_leap_interval = borrow_pitch - prev_pitch
                prev_pitch = borrow_pitch
                curr_beat += duration
                continue

            # 4. Tension note (9th, 11th, 13th) on off-beats (18% chance)
            elif enable_tensions and rand_choice < 0.52 and is_offbeat:
                t_iv = rng.choice(tension_offsets)
                t_pitch = root_midi_oct4 + t_iv
                if t_pitch > 86:
                    t_pitch -= 12
                duration = rng.choice([0.75, 1.0, 1.5]) if beats_per_bar >= 4.0 else rng.choice([0.5, 0.75, 1.0])
                velocity = int(rng.randint(88, 100) * energy_level)
                notes.append(NoteEvent(pitch=t_pitch, start=curr_beat, duration=duration, velocity=velocity))
                prev_leap_interval = t_pitch - prev_pitch
                prev_pitch = t_pitch
                curr_beat += duration
                continue

            # 5. Dramatic 6th or 7th leap (18% chance)
            elif enable_leaps and rand_choice < 0.70 and prev_pitch < 74:
                leap_st = rng.choice([8, 9, 10, 11]) # 6th or 7th
                leap_pitch = prev_pitch + leap_st
                target_pitch = min(pool, key=lambda p: abs(p - leap_pitch))
                duration = rng.choice([0.75, 1.0, 1.25])
                velocity = int(rng.randint(98, 115) * energy_level)
                notes.append(NoteEvent(pitch=target_pitch, start=curr_beat, duration=duration, velocity=velocity))
                prev_leap_interval = target_pitch - prev_pitch
                prev_pitch = target_pitch
                curr_beat += duration
                continue

            # 6. Diatonic stepwise or 3rd motion (Standard melody flow)
            else:
                curr_idx = pool.index(prev_pitch) if prev_pitch in pool else len(pool) // 2
                delta_step = rng.choice([-2, -1, -1, 1, 1, 2])
                next_idx = max(0, min(len(pool) - 1, curr_idx + delta_step))
                target_pitch = pool[next_idx]
                duration = rng.choice([0.5, 0.75, 1.0])
                velocity = int(rng.randint(80, 95) * energy_level)
                notes.append(NoteEvent(pitch=target_pitch, start=curr_beat, duration=duration, velocity=velocity))
                prev_leap_interval = target_pitch - prev_pitch
                prev_pitch = target_pitch
                curr_beat += duration

            # Add occasional breath silence
            if rng.random() < 0.15 and (curr_beat - start_beat) % (beats_per_bar * 2) >= (beats_per_bar * 1.5):
                curr_beat += 0.5

        # Final cadential resolution to tonic
        if notes:
            last_n = notes[-1]
            tonic_res = root_midi_oct4 if energy_level < 0.8 else root_midi_oct4 + 12
            if abs(last_n.pitch - tonic_res) > 2:
                notes.append(NoteEvent(
                    pitch=tonic_res,
                    start=min(start_beat + total_beats - 1.5, last_n.start + last_n.duration + 0.25),
                    duration=max(1.0, beats_per_bar * 0.4),
                    velocity=int(95 * energy_level)
                ))

        return notes

    @classmethod
    def generate_melody_for_section(
        cls,
        section_name: str = "Chorus",
        section_bars: int = 8,
        bpm: float = 120.0,
        key_root: str = "F",
        scale: str = "natural_minor",
        time_signature: Tuple[int, int] = (4, 4),
        start_beat: float = 0.0,
        energy_level: float = 0.85,
        borrow_modal: bool = True,
        seed: int = 42
    ) -> List[NoteEvent]:
        """Generates an expressive melody tailored for a specific arrangement section."""
        return cls.generate_advanced_melody(
            key_root=key_root,
            scale=scale,
            total_bars=section_bars,
            start_beat=start_beat,
            energy_level=energy_level,
            enable_leaps=True,
            enable_tensions=True,
            enable_modal_borrowing=borrow_modal,
            time_signature=time_signature,
            seed=seed
        )

    @classmethod
    def audit_melodic_contour(cls, notes: List[NoteEvent], key_root: str = "F", scale: str = "natural_minor") -> Dict[str, Any]:
        """
        Audits a generated note sequence confirming leaps, resolutions, and tension presence.
        """
        if not notes:
            return {
                "total_notes": 0,
                "note_count": 0,
                "large_leaps_6th_7th": 0,
                "contrary_resolutions_verified": 0,
                "tension_notes_count": 0,
                "tensions_used": 0,
                "leap_resolution_ratio": 1.0,
                "counterpoint_compliance": 1.0
            }

        root_pc = cls.PITCH_CLASS_MAP.get(key_root.strip().upper(), 5)
        root_oct4 = 60 + root_pc

        large_leaps = 0
        resolved_contrary = 0
        tension_notes_count = 0
        borrowed_notes_count = 0

        scale_l = scale.lower()
        clean_scale = scale_l.replace(" ", "_")
        intervals = cls.SCALE_INTERVALS.get(clean_scale, cls.SCALE_INTERVALS["natural_minor"])

        for i in range(len(notes) - 1):
            p1 = notes[i].pitch
            p2 = notes[i + 1].pitch
            interval = p2 - p1
            abs_iv = abs(interval)

            # Check tension (9th, 11th, 13th)
            rel_semitones = (p1 - root_pc) % 12
            if rel_semitones in [2, 5, 9]: # 9th(2), 11th(5), 13th(9) relative to octave
                tension_notes_count += 1

            # Check if note is non-diatonic (borrowed)
            if rel_semitones not in intervals:
                borrowed_notes_count += 1

            # 6th or 7th leap
            if abs_iv in (8, 9, 10, 11):
                large_leaps += 1
                if i + 2 < len(notes):
                    p3 = notes[i + 2].pitch
                    res_iv = p3 - p2
                    # Contrary resolution: opposite sign and step (1 or 2 semitones)
                    if (interval > 0 and res_iv < 0 and abs(res_iv) <= 3) or (interval < 0 and res_iv > 0 and abs(res_iv) <= 3):
                        resolved_contrary += 1

        ratio = (resolved_contrary / max(1, large_leaps)) if large_leaps > 0 else 1.0
        return {
            "total_notes": len(notes),
            "note_count": len(notes),
            "large_leaps_6th_7th": large_leaps,
            "contrary_resolutions_verified": resolved_contrary,
            "tension_notes_count": tension_notes_count,
            "tensions_used": tension_notes_count,
            "borrowed_color_notes_count": borrowed_notes_count,
            "leap_resolution_ratio": ratio,
            "counterpoint_compliance": ratio
        }
