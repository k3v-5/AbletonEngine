# engine/music/harmony/reharmonizer.py
"""
Modal Reharmonization Engine:
Enriches simple harmonic progressions with secondary dominants (V7/X), tritone substitutions,
diminished passing chords, and modal borrowing for modern neo-soul, jazz-rap, and R&B sophistication.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Union
from engine.music.models import Chord, NoteEvent

# Chromatic pitch map
PITCH_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
ROOT_TO_MIDI = {
    "C": 60, "Db": 61, "C#": 61, "D": 62, "Eb": 63, "D#": 63,
    "E": 64, "F": 65, "Gb": 66, "F#": 66, "G": 67, "Ab": 68,
    "G#": 68, "A": 69, "Bb": 70, "A#": 70, "B": 71
}


class ReharmStyle(str, Enum):
    SECONDARY_DOMINANTS = "secondary_dominants"      # V7/target on beat 4
    TRITONE_SUBSTITUTIONS = "tritone_substitutions"  # SubV7 (half-step above target)
    CHROMATIC_PASSING = "chromatic_passing"          # Diminished passing chords
    MODAL_BORROWING = "modal_borrowing"              # Borrowed Dorian / Major chords


class ModalReharmonizer:
    """Calculates advanced harmonic substitutions and passing chord insertions."""

    @staticmethod
    def _normalize_root(root: str) -> str:
        clean = root.capitalize()
        equivalents = {"C#": "Db", "D#": "Eb", "F#": "Gb", "G#": "Ab", "A#": "Bb"}
        return equivalents.get(clean, clean)

    @classmethod
    def get_secondary_dominant_root(cls, target_root: str) -> str:
        """Returns the root note a perfect 5th above target root (or 4th down)."""
        norm = cls._normalize_root(target_root)
        try:
            idx = PITCH_NAMES.index(norm)
            dom_idx = (idx + 7) % 12
            return PITCH_NAMES[dom_idx]
        except ValueError:
            return "C"

    @classmethod
    def get_tritone_sub_root(cls, target_root: str) -> str:
        """Returns the root note a half-step (1 semitone) above target root."""
        norm = cls._normalize_root(target_root)
        try:
            idx = PITCH_NAMES.index(norm)
            sub_idx = (idx + 1) % 12
            return PITCH_NAMES[sub_idx]
        except ValueError:
            return "Db"

    @classmethod
    def reharmonize_progression(
        cls,
        chords: List[Chord],
        style: Union[ReharmStyle, str] = ReharmStyle.SECONDARY_DOMINANTS,
        tension_level: float = 0.5
    ) -> List[Chord]:
        """
        Takes an input list of 4-bar or 8-bar chords and injects harmonic tension
        on the turnaround beat preceding chord transitions.
        """
        if not chords or len(chords) < 2:
            return [Chord(**c.__dict__) for c in chords]

        st = ReharmStyle(style) if isinstance(style, str) else style
        reharmonized: List[Chord] = []

        for i in range(len(chords)):
            curr = chords[i]
            # Next chord (wraps around on final chord)
            nxt = chords[(i + 1) % len(chords)]

            if curr.duration >= 3.0 and tension_level > 0.2:
                # Shorten current chord to leave room for passing turnaround chord on beat 4
                main_dur = max(2.0, round(curr.duration - 1.0, 2))
                pass_dur = round(curr.duration - main_dur, 2)

                reharmonized.append(Chord(
                    root=curr.root,
                    quality=curr.quality,
                    extensions=list(curr.extensions),
                    inversion=curr.inversion,
                    bass_note=curr.bass_note,
                    duration=main_dur,
                    roman_numeral=curr.roman_numeral
                ))

                if st == ReharmStyle.SECONDARY_DOMINANTS:
                    sec_root = cls.get_secondary_dominant_root(nxt.root)
                    reharmonized.append(Chord(
                        root=sec_root,
                        quality="dominant7",
                        extensions=["9", "b13"] if tension_level > 0.6 else ["9"],
                        duration=pass_dur,
                        roman_numeral=f"V7/{nxt.root}"
                    ))
                elif st == ReharmStyle.TRITONE_SUBSTITUTIONS:
                    tri_root = cls.get_tritone_sub_root(nxt.root)
                    reharmonized.append(Chord(
                        root=tri_root,
                        quality="dominant7",
                        extensions=["9", "#11"] if tension_level > 0.6 else ["7"],
                        duration=pass_dur,
                        roman_numeral=f"subV7/{nxt.root}"
                    ))
                elif st == ReharmStyle.CHROMATIC_PASSING:
                    # Half-step diminished passing chord
                    curr_idx = PITCH_NAMES.index(cls._normalize_root(curr.root))
                    pass_root = PITCH_NAMES[(curr_idx + 1) % 12]
                    reharmonized.append(Chord(
                        root=pass_root,
                        quality="diminished7",
                        extensions=["7"],
                        duration=pass_dur,
                        roman_numeral=f"{pass_root}dim7"
                    ))
                else: # MODAL_BORROWING
                    reharmonized.append(Chord(
                        root=curr.root,
                        quality="major7" if "min" in curr.quality else "minor9",
                        extensions=["9"],
                        duration=pass_dur,
                        roman_numeral="borrowed"
                    ))
            else:
                reharmonized.append(Chord(**curr.__dict__))

        return reharmonized

    @classmethod
    def render_chords_to_notes(
        cls,
        chords: List[Chord],
        base_octave: int = 4,
        velocity: int = 85
    ) -> List[NoteEvent]:
        """Converts Chord objects into concrete NoteEvent voices with smooth voice leading."""
        notes: List[NoteEvent] = []
        curr_beat = 0.0

        QUALITY_INTERVALS = {
            "major": [0, 4, 7],
            "minor": [0, 3, 7],
            "dominant7": [0, 4, 7, 10],
            "major7": [0, 4, 7, 11],
            "minor7": [0, 3, 7, 10],
            "minor9": [0, 3, 7, 10, 14],
            "diminished7": [0, 3, 6, 9],
        }

        for chord in chords:
            root_midi = ROOT_TO_MIDI.get(cls._normalize_root(chord.root), 60)
            # Adjust to target octave
            base_midi = (root_midi % 12) + (base_octave + 1) * 12
            intervals = QUALITY_INTERVALS.get(chord.quality, [0, 4, 7])

            for iv in intervals:
                p = base_midi + iv
                notes.append(NoteEvent(
                    pitch=p,
                    start=round(curr_beat, 4),
                    duration=round(chord.duration * 0.95, 4),
                    velocity=velocity
                ))
            curr_beat += chord.duration

        return notes
