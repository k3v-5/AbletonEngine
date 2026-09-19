# engine/music/modular_generator.py
"""
Modular section note generator and genre drum style resolution.
"""
from typing import List, Dict, Optional, Tuple, Any
from engine.music.models import NoteEvent
from engine.music.drums.evolver import DrumPatternEvolver
from engine.music.drums.genre_grooves import GenreRhythmGrooveEngine, GenreDrumStyle
from engine.music.drums.ghost_notes import DrumGhostNoteInjector
from engine.music.harmony.full_song import FullSongHarmonyEngine
from engine.music.harmony.strum import PhysicalChordStrummer
from engine.music.melody.topline import TopLineMelodyEngine
from engine.knowledge.composition.chords import PROGRESSION_DEFINITIONS, get_progression_chords

KEY_OFFSETS: Dict[str, int] = {
    "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3,
    "E": 4, "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8,
    "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11
}
SEMITONE_TO_KEY: List[str] = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def resolve_genre_style(genre_input: Optional[str], bpm: float = 120.0) -> GenreDrumStyle:
    """Resolves genre name or bpm into canonical GenreDrumStyle enum."""
    if genre_input:
        g_clean = str(genre_input).lower().strip().replace("-", "_").replace(" ", "_")
        try:
            return GenreDrumStyle(g_clean)
        except ValueError:
            for style in GenreDrumStyle:
                if style.value in g_clean or g_clean in style.value:
                    return style
            if "hip_hop" in g_clean or "hiphop" in g_clean or "drill" in g_clean:
                return GenreDrumStyle.TRAP
            elif "lofi" in g_clean or "lo_fi" in g_clean:
                return GenreDrumStyle.BOOM_BAP
            elif "rnb" in g_clean or "soul" in g_clean:
                return GenreDrumStyle.NEO_SOUL
            elif "dembow" in g_clean or "latin" in g_clean:
                return GenreDrumStyle.REGGAETON
            elif "dnb" in g_clean or "jungle" in g_clean:
                return GenreDrumStyle.DRUM_AND_BASS

    # Fallback inference by tempo (BPM)
    if bpm < 95.0:
        return GenreDrumStyle.BOOM_BAP
    elif bpm <= 115.0:
        return GenreDrumStyle.REGGAETON
    elif bpm <= 130.0:
        return GenreDrumStyle.HOUSE
    elif bpm <= 165.0:
        return GenreDrumStyle.TRAP
    else:
        return GenreDrumStyle.DRUM_AND_BASS


def generate_modular_section_notes(
    role: str,
    section_index: int,
    section_name: str,
    section_bars: int,
    key: str = "F",
    scale: str = "natural_minor",
    bpm: float = 120.0,
    genre: Optional[str] = None
) -> List[NoteEvent]:
    r = role.upper().strip()
    s_lower = section_name.lower()
    total_beats = float(section_bars * 4.0)
    notes: List[NoteEvent] = []

    root = KEY_OFFSETS.get(key.upper().strip(), 5)
    scale_clean = scale.lower().strip()

    # Harmonic matrix mapped from PROGRESSION_DEFINITIONS and modal scales
    prog_specs = {
        "royal_road": [(5, "maj7"), (7, "dom7"), (4, "min7"), (9, "min7")],
        "jpop": [(5, "maj7"), (7, "dom7"), (4, "min7"), (9, "min7")],
        "dorian": [(0, "min7"), (5, "dom7"), (10, "maj7"), (0, "min7")],
        "harmonic_minor": [(0, "minor"), (8, "major"), (5, "minor"), (7, "dom7")],
        "major": [(0, "major"), (7, "major"), (9, "minor"), (5, "major")],
        "natural_minor": [(0, "minor"), (8, "major"), (3, "major"), (10, "major")],
    }
    for k, p in PROGRESSION_DEFINITIONS.items():
        prog_specs[k] = p["chords"]

    selected_spec = None
    for p_name, spec in prog_specs.items():
        if p_name in scale_clean or (p_name == "harmonic_minor" and ("harmonic" in scale_clean or "armonica" in scale_clean)):
            selected_spec = spec
            break
    if selected_spec is None:
        selected_spec = prog_specs["natural_minor"]

    # Generate Drop-2 Voicings with optimal voice leading
    bass_roots: List[int] = []
    chords_voicing: List[List[int]] = []
    pad_voicings: List[List[int]] = []
    prev_v: Optional[List[int]] = None

    for interval, qual in selected_spec:
        semi = (root + interval) % 12
        r_name = SEMITONE_TO_KEY[semi]
        bass_roots.append(root + interval)
        v = FullSongHarmonyEngine.build_drop2_voicing(r_name, qual, target_center_pitch=60)
        if prev_v is not None:
            v = FullSongHarmonyEngine.optimize_voice_leading(prev_v, v)
        prev_v = v
        chords_voicing.append(v)
        pad_voicings.append([p + 12 for p in v[:3]])

    # Map bass roots to safe low range (MIDI 24-38)
    bass_pitches: List[int] = []
    for br in bass_roots:
        p = (br % 12) + 24
        if p < 24:
            p += 12
        if p > 38:
            p -= 12
        bass_pitches.append(p)

    # 1. DRUMS
    if "DRUM" in r:
        if "bridge" in s_lower or "puente" in s_lower or "calma" in s_lower or section_index == 4:
            return []  # Structural silence in bridge/calma!

        elif "build" in s_lower or "pre" in s_lower or section_index == 2:
            # Snare accelerando roll with progressive crescendo and pre-drop silence
            for bar in range(section_bars):
                b = bar * 4.0
                progress = bar / max(1.0, float(section_bars - 1))
                vel = int(72 + (progress * 52))
                if bar < section_bars - 2:
                    for beat in range(4):
                        notes.append(NoteEvent(pitch=38, start=b + beat, duration=0.25, velocity=vel))
                elif bar < section_bars - 1:
                    for beat in range(8):
                        notes.append(NoteEvent(pitch=38, start=b + (beat * 0.5), duration=0.18, velocity=vel))
                else:
                    # Accelerando to 1/32 with 1-beat silence at the end for drop impact
                    for step in range(24):
                        notes.append(NoteEvent(pitch=38, start=b + (step * 0.125), duration=0.08, velocity=min(127, 90 + step)))
                    notes.append(NoteEvent(pitch=49, start=b + 2.75, duration=0.25, velocity=127))

        elif "intro" in s_lower or section_index == 0:
            for bar in range(section_bars):
                b = bar * 4.0
                if bar % 2 == 0:
                    notes.append(NoteEvent(pitch=36, start=b, duration=0.35, velocity=90))
                for h in range(8):
                    notes.append(NoteEvent(pitch=42, start=b + (h * 0.5), duration=0.15, velocity=68 if h % 2 == 0 else 48))

        elif "outro" in s_lower or section_index == 6:
            active_bars = min(4, section_bars)
            for bar in range(active_bars):
                b = bar * 4.0
                vel_fade = int(100 * (1.0 - (bar / float(active_bars))))
                notes.append(NoteEvent(pitch=36, start=b + 0.0, duration=0.3, velocity=max(40, vel_fade)))
                notes.append(NoteEvent(pitch=42, start=b + 1.0, duration=0.15, velocity=max(30, vel_fade - 10)))
                notes.append(NoteEvent(pitch=38, start=b + 2.0, duration=0.3, velocity=max(35, vel_fade - 5)))
                notes.append(NoteEvent(pitch=42, start=b + 3.0, duration=0.15, velocity=max(30, vel_fade - 10)))

        else:
            is_drop = ("drop" in s_lower or "chorus" in s_lower or "climax" in s_lower or section_index in (3, 5))
            style = resolve_genre_style(genre, bpm=bpm)
            raw_groove = GenreRhythmGrooveEngine.generate_rhythm_pattern(
                genre=style,
                length_bars=section_bars,
                tempo=bpm,
                swing_amount=0.15 if style in (GenreDrumStyle.BOOM_BAP, GenreDrumStyle.NEO_SOUL) else 0.0,
                humanize_ms=6.0
            )
            # Ensure accent to 127 in drops
            if raw_groove and is_drop:
                max_v = max(n.velocity for n in raw_groove)
                if max_v < 127:
                    for n in raw_groove:
                        if n.pitch in (36, 38, 39) and n.velocity == max_v:
                            n.velocity = 127
            # Density guard for 16-bar drop (require >= 200 notes per production standard)
            if is_drop and section_bars >= 16 and len(raw_groove) < 200:
                raw_groove = DrumGhostNoteInjector.inject_ghost_notes(raw_groove, total_bars=section_bars)
                if len(raw_groove) < 200:
                    for bar in range(section_bars):
                        b = bar * 4.0
                        for h in range(4):
                            raw_groove.append(NoteEvent(pitch=46, start=b + h + 0.5, duration=0.2, velocity=105))
            # Inject bar 8 fill if 8+ bars
            if section_bars >= 8 and raw_groove:
                raw_groove = DrumPatternEvolver.inject_bar_8_fill(raw_groove, loop_bars=float(section_bars))
            notes = raw_groove

    # 1.1 KICK (Isolated Kick Drum)
    elif "KICK" in r:
        if "bridge" in s_lower or "puente" in s_lower or "calma" in s_lower or section_index == 4:
            return []  # Structural silence in bridge/calma
        elif "build" in s_lower or "pre" in s_lower or section_index == 2:
            # 4-on-the-floor driving buildup with 1-beat silence before the drop impact
            for bar in range(section_bars):
                b = bar * 4.0
                if bar < section_bars - 1:
                    for beat in range(4):
                        notes.append(NoteEvent(pitch=36, start=b + beat, duration=0.25, velocity=int(85 + bar * 6)))
                else:
                    for beat in range(3):  # Leave last beat silent for drop impact
                        notes.append(NoteEvent(pitch=36, start=b + beat, duration=0.25, velocity=115))
        elif "intro" in s_lower or section_index == 0:
            for bar in range(section_bars):
                b = bar * 4.0
                if bar % 2 == 0:
                    notes.append(NoteEvent(pitch=36, start=b, duration=0.35, velocity=95))
        elif "outro" in s_lower or section_index == 6:
            active_bars = min(4, section_bars)
            for bar in range(active_bars):
                b = bar * 4.0
                vel_fade = int(100 * (1.0 - (bar / float(active_bars))))
                notes.append(NoteEvent(pitch=36, start=b + 0.0, duration=0.3, velocity=max(40, vel_fade)))
        else:
            is_drop = ("drop" in s_lower or "chorus" in s_lower or "climax" in s_lower or section_index in (3, 5))
            style = resolve_genre_style(genre, bpm=bpm)
            raw_groove = GenreRhythmGrooveEngine.generate_rhythm_pattern(
                genre=style,
                length_bars=section_bars,
                tempo=bpm,
                swing_amount=0.15 if style in (GenreDrumStyle.BOOM_BAP, GenreDrumStyle.NEO_SOUL) else 0.0,
                humanize_ms=6.0
            )
            kick_hits = [n for n in raw_groove if n.pitch in (35, 36)]
            if not kick_hits:
                for bar in range(section_bars):
                    b = bar * 4.0
                    notes.append(NoteEvent(pitch=36, start=b + 0.0, duration=0.35, velocity=122 if is_drop else 105))
                    if bar % 2 == 1:
                        notes.append(NoteEvent(pitch=36, start=b + 2.5, duration=0.35, velocity=115 if is_drop else 98))
            else:
                for n in kick_hits:
                    n.pitch = 36
                    if is_drop:
                        n.velocity = min(127, n.velocity + 8)
                notes = kick_hits

    # 2. BASS
    elif "BASS" in r:
        if "intro" in s_lower or "build" in s_lower or "pre" in s_lower or "bridge" in s_lower or "puente" in s_lower or "calma" in s_lower:
            return []  # Structural silence in Intro, Buildup and Bridge!
        elif "outro" in s_lower:
            notes.append(NoteEvent(pitch=bass_pitches[0], start=0.0, duration=16.0, velocity=85))
        else:
            is_heavy = ("drop" in s_lower or "climax" in s_lower or section_index in (3, 5))
            vel = 126 if is_heavy else 105
            for bar in range(0, section_bars, 2):
                b = bar * 4.0
                p = bass_pitches[(bar // 2) % len(bass_pitches)]
                p_next = bass_pitches[((bar // 2) + 1) % len(bass_pitches)]
                # Hit 1: Downbeat bar 1
                notes.append(NoteEvent(pitch=p, start=b + 0.0, duration=1.4, velocity=vel))
                # Hit 2: Syncopated bounce on beat 2.5
                notes.append(NoteEvent(pitch=p, start=b + 1.5, duration=2.0, velocity=vel - 6))
                # Hit 3: Downbeat bar 2
                notes.append(NoteEvent(pitch=p_next, start=b + 4.0, duration=1.5, velocity=vel - 4))
                # Hit 4: Turnaround octave leap on beat 6.5
                if is_heavy and (bar % 4 == 2):
                    notes.append(NoteEvent(pitch=p_next + 12, start=b + 6.5, duration=0.75, velocity=vel - 10))
                # Hit 5: Chromatic approach leading tone
                if p_next != p:
                    leading_tone = p_next - 1 if p_next > 24 else p_next + 1
                    notes.append(NoteEvent(pitch=leading_tone, start=b + 7.5, duration=0.45, velocity=vel - 12))

    # 3. KEYS
    elif "KEY" in r:
        is_calm = ("intro" in s_lower or "bridge" in s_lower or "puente" in s_lower or "calma" in s_lower or "outro" in s_lower)
        vel = 72 if is_calm else 102
        step_len = 8.0 if is_calm else 4.0
        for step_idx in range(int(total_beats / step_len)):
            b = step_idx * step_len
            v = chords_voicing[step_idx % len(chords_voicing)]
            for p in v:
                notes.append(NoteEvent(pitch=p, start=b, duration=step_len - 0.25, velocity=vel))
        if notes:
            notes = PhysicalChordStrummer.strum_notes(notes, tempo=bpm, strum_ms=12.0, direction="alternating")

    # 4. PAD / STRINGS
    elif "PAD" in r or "STRING" in r:
        step_len = 16.0 if total_beats >= 16.0 else 8.0
        for step_idx in range(max(1, int(total_beats / step_len))):
            b = step_idx * step_len
            v = pad_voicings[step_idx % len(pad_voicings)]
            for p in v:
                notes.append(NoteEvent(pitch=p, start=b, duration=step_len - 0.5, velocity=78))

    # 5. LEAD
    elif "LEAD" in r:
        if "intro" in s_lower or "build" in s_lower or "bridge" in s_lower or "puente" in s_lower or "calma" in s_lower:
            return []
        elif "outro" in s_lower:
            # Outro sustained drone / chord bed (the synthesizer must NEVER be silenced in the outro!)
            root_pitch = root + 48  # e.g. E3 = 52
            fifth_pitch = root_pitch + 7  # e.g. B3 = 59
            oct_pitch = root_pitch + 12  # e.g. E4 = 64
            tension_pitch = root_pitch + (1 if "phrygian" in scale_clean else 3)
            # Bar 0-4 (beats 0-16): Root power chord drone
            notes.append(NoteEvent(pitch=root_pitch, start=0.0, duration=min(15.8, total_beats - 0.2), velocity=105))
            notes.append(NoteEvent(pitch=fifth_pitch, start=0.0, duration=min(15.8, total_beats - 0.2), velocity=95))
            notes.append(NoteEvent(pitch=oct_pitch, start=0.0, duration=min(15.8, total_beats - 0.2), velocity=110))
            if total_beats > 16.0:
                # Bar 4+ (beats 16+): Tension / dissonance shift for saturation breakdown
                notes.append(NoteEvent(pitch=tension_pitch, start=16.0, duration=min(15.8, total_beats - 16.2), velocity=105))
                notes.append(NoteEvent(pitch=fifth_pitch - 1, start=16.0, duration=min(15.8, total_beats - 16.2), velocity=95))
                notes.append(NoteEvent(pitch=oct_pitch, start=16.0, duration=min(15.8, total_beats - 16.2), velocity=110))
        else:
            is_climax = ("climax" in s_lower or "drop 2" in s_lower or section_index == 5)
            oct_shift = 12 if is_climax else 0
            key_semi_offset = (KEY_OFFSETS.get(key.upper().strip(), 5) - 5) % 12
            phrase_seed = (section_index + 1) * 101
            for bar in range(0, section_bars, 8):
                b = bar * 4.0
                phrase_notes = TopLineMelodyEngine.generate_8bar_phrase(
                    start_beat=b,
                    key_root=key,
                    scale=scale,
                    energy_level=0.95 if is_climax else 0.80,
                    phrase_seed=phrase_seed + bar
                )
                for pn in phrase_notes:
                    notes.append(NoteEvent(
                        pitch=pn.pitch + key_semi_offset + oct_shift,
                        start=pn.start,
                        duration=pn.duration,
                        velocity=min(127, pn.velocity + (10 if is_climax else 0))
                    ))

    return notes



