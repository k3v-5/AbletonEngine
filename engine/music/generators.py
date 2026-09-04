# engine/music/generators.py
import random
import math
from typing import List, Dict, Any, Optional
from .models import NoteEvent, Chord
from .intent import MusicalIntent
from .theory.notes import normalize_pitch_class, midi_to_note
from .theory.scales import (
    get_scale_pitch_classes, scale_degree_to_midi,
    snap_to_scale, get_scale_intervals
)
from .harmony.generator import generate_harmonic_structure
from .harmony.roman import parse_progression_string
from .voicing.voice_leading import optimize_voice_leading
from .voicing.profiles import apply_voicing_profile
from .groove.profiles import apply_groove_to_notes
from .humanizer.engine import humanize_notes

# --- BASS GENERATOR ---

def generate_bassline(
    intent: MusicalIntent,
    chords: Optional[List[Chord]] = None
) -> List[NoteEvent]:
    """
    Generates a genre-appropriate bassline (rolling, offbeat, acid, sustained)
    harmonically aligned with chords and register-constrained.
    """
    rng = random.Random(intent.seed)
    total_beats = intent.bars * 4.0

    # If chords not provided, generate baseline progression
    if not chords:
        chords = generate_harmonic_structure(
            key=intent.key,
            scale=intent.scale,
            progression="i - VI - III - VII",
            bars=intent.bars
        )

    root_pc = normalize_pitch_class(intent.key)
    scale_pcs = get_scale_pitch_classes(intent.key, intent.scale)
    base_octave = 1 if intent.role.upper() == "SUB_BASS" else 2

    notes: List[NoteEvent] = []
    style = intent.style.lower()

    # Match each beat to the active chord
    current_time = 0.0
    chord_idx = 0

    while current_time < total_beats:
        # Find active chord at current_time
        accum = 0.0
        active_chord = chords[0]
        for c in chords:
            if accum <= current_time < accum + c.duration:
                active_chord = c
                break
            accum += c.duration

        chord_root_pc = normalize_pitch_class(active_chord.root)
        fundamental_pitch = (base_octave + 1) * 12 + chord_root_pc

        # Clamp fundamental to [28, 48] for sub / [28, 55] for bass
        while fundamental_pitch < 28: fundamental_pitch += 12
        while fundamental_pitch > (46 if intent.role.upper() == "SUB_BASS" else 55): fundamental_pitch -= 12

        # Style A: Rolling Melodic Techno (continuous 16th notes with octave / 5th movement)
        if style == "rolling":
            # 4 sixteenth notes per beat
            step_dur = 0.25
            for step in range(4):
                step_time = current_time + step * step_dur
                if step_time >= total_beats:
                    break

                # Groove: downbeat is root, 16ths can alternate octave or 5th
                pitch = fundamental_pitch
                vel = int(80 + 35 * intent.energy)
                accent = 0.0

                if step == 0:
                    vel += 12
                    accent = 0.8
                elif step == 2 and intent.movement > 0.4 and rng.random() < 0.6:
                    # Octave jump on 3rd sixteenth
                    pitch = fundamental_pitch + 12
                    vel -= 5
                elif step == 3 and intent.movement > 0.6 and rng.random() < 0.4:
                    # Fifth of chord or diatonic neighbor
                    pitch = fundamental_pitch + 7
                    pitch = snap_to_scale(intent.key, intent.scale, pitch)
                    vel -= 10

                notes.append(NoteEvent.from_pitch_and_time(pitch, step_time, duration=0.22, velocity=vel, accent=accent))
            current_time += 1.0

        # Style B: Offbeat Bass (classic driving house/techno offbeat on .5)
        elif style == "offbeat" or style == "offbeat_sub":
            # Place note on every eighth-note offbeat (0.5, 1.5, 2.5, etc.)
            offbeat_time = current_time + 0.5
            vel = int(90 + 30 * intent.energy)
            notes.append(NoteEvent.from_pitch_and_time(fundamental_pitch, offbeat_time, duration=0.45, velocity=vel, accent=0.7))
            current_time += 1.0

        # Style C: Sustained / Pad Bass (long notes following chord durations)
        elif style == "sustained":
            chord_dur = active_chord.duration
            vel = int(85 + 25 * intent.energy)
            notes.append(NoteEvent.from_pitch_and_time(fundamental_pitch, current_time, duration=chord_dur - 0.1, velocity=vel, accent=0.5))
            current_time += chord_dur

        # Style D: Syncopated Acid / Funk
        else:
            # Syncopated 16th groove with ties
            for off in [0.0, 0.75, 1.5, 2.25, 3.0, 3.5]:
                step_time = current_time + off
                if step_time >= total_beats: break
                pitch = fundamental_pitch
                if off in [0.75, 2.25] and rng.random() < 0.5:
                    pitch = snap_to_scale(intent.key, intent.scale, fundamental_pitch + 3)
                vel = int(85 + 30 * intent.energy)
                notes.append(NoteEvent.from_pitch_and_time(pitch, step_time, duration=0.35, velocity=vel, accent=0.6))
            current_time += 4.0

    # Apply groove and humanization
    grooved = apply_groove_to_notes(notes, profile=intent.groove, tempo=intent.tempo)
    humanized = humanize_notes(grooved, role=intent.role, strength=intent.humanization, tempo=intent.tempo, seed=intent.seed)
    return humanized

# --- CHORDS GENERATOR ---

def generate_chords(
    intent: MusicalIntent,
    progression: str = "i - VI - III - VII",
    voicing_style: str = "drop_2"
) -> List[NoteEvent]:
    """
    Generates fully voiced chords with smooth voice leading and rhythmic humanization.
    """
    total_beats = intent.bars * 4.0
    chords = generate_harmonic_structure(
        key=intent.key,
        scale=intent.scale,
        progression=progression,
        bars=intent.bars,
        chord_density=intent.density,
        extensions=(intent.tension > 0.5),
        tension=intent.tension
    )

    # Compute optimal voice leading
    voicings = optimize_voice_leading(
        chords,
        style=voicing_style,
        register="mid",
        min_pitch=45,
        max_pitch=84
    )

    notes: List[NoteEvent] = []
    current_time = 0.0

    for chord, voice_pitches in zip(chords, voicings):
        dur = chord.duration
        # Style: sustained chords vs rhythmic stabs
        if intent.style == "staccato" or intent.style == "chabs":
            # Play short corcheas on downbeats
            sub_step = 1.0  # every beat
            sub_curr = 0.0
            while sub_curr < dur:
                for p in voice_pitches:
                    vel = int(80 + 30 * intent.energy)
                    notes.append(NoteEvent.from_pitch_and_time(p, current_time + sub_curr, duration=0.45, velocity=vel, accent=0.5))
                sub_curr += sub_step
        else:
            # Sustained pad / chord
            for p in voice_pitches:
                vel = int(75 + 35 * intent.energy)
                notes.append(NoteEvent.from_pitch_and_time(p, current_time, duration=dur - 0.1, velocity=vel, accent=0.3))

        current_time += dur

    grooved = apply_groove_to_notes(notes, profile=intent.groove, tempo=intent.tempo)
    humanized = humanize_notes(grooved, role=intent.role, strength=intent.humanization, tempo=intent.tempo, seed=intent.seed)
    return humanized

# --- MELODY / LEAD GENERATOR ---

def generate_melody(
    intent: MusicalIntent,
    contour: str = "arch"
) -> List[NoteEvent]:
    """
    Generates a melodic lead motif with phrasing, contour shaping, and rhythmic syncopation.
    """
    rng = random.Random(intent.seed)
    total_beats = intent.bars * 4.0
    scale_pcs = get_scale_pitch_classes(intent.key, intent.scale)
    base_pitch = scale_degree_to_midi(intent.key, intent.scale, degree=1, octave=4)

    notes: List[NoteEvent] = []
    current_time = 0.0

    # We build phrases in 4-bar blocks
    phrase_bars = 4
    phrase_beats = phrase_bars * 4.0

    while current_time < total_beats:
        block_end = min(total_beats, current_time + phrase_beats)
        block_len = block_end - current_time

        # Rhythmic step options: 1/8 (0.5), 1/16 (0.25), dotted 1/8 (0.75), 1/4 (1.0)
        t = current_time
        step_idx = 0
        while t < block_end - 0.5:
            # Contour shape calculation (0.0 to 1.0 within phrase)
            phase = (t - current_time) / block_len
            if contour == "arch":
                contour_offset = math.sin(phase * math.pi) * 12.0
            elif contour == "ascending":
                contour_offset = phase * 14.0
            elif contour == "descending":
                contour_offset = (1.0 - phase) * 14.0
            else:
                contour_offset = math.sin(phase * 4 * math.pi) * 7.0

            # Degree jump
            jump = rng.choice([0, 2, 4, -1, 3])
            target_pitch = int(base_pitch + contour_offset + jump)
            target_pitch = snap_to_scale(intent.key, intent.scale, target_pitch)

            dur = rng.choice([0.25, 0.5, 0.75, 1.0])
            vel = int(85 + 30 * intent.energy + rng.randint(-8, 8))

            notes.append(NoteEvent.from_pitch_and_time(target_pitch, t, duration=dur * 0.9, velocity=vel, accent=0.5))

            # Move forward in time (some rests to breathe)
            rest = 0.25 if rng.random() < 0.25 else 0.0
            t += (dur + rest)
            step_idx += 1

        current_time = block_end

    grooved = apply_groove_to_notes(notes, profile=intent.groove, tempo=intent.tempo)
    humanized = humanize_notes(grooved, role=intent.role, strength=intent.humanization, tempo=intent.tempo, seed=intent.seed)
    return humanized
