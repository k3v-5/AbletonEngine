# engine/music/harmony/functional_harmony_engine.py
"""
Functional Harmony Engine:
Implements advanced harmonic theory and voice leading for modern production:
1. Secondary Dominants (V7/V, V7/ii, V7/iv, V7/vi).
2. Tritone Substitution (subV7 -> I).
3. Modal Interchange (borrowed chords from parallel minor/major and Neapolitan bII).
4. Altered Dominants (7b9, 7#9, 7alt).
5. Dynamic progression generation across arbitrary bar counts and section blueprints.
"""

from typing import List, Dict, Any, Optional, Tuple, NamedTuple
import math
import random
from engine.music.models import Chord, NoteEvent
from engine.music.theory.notes import normalize_pitch_class, note_to_midi, midi_to_note


class BorrowedChord(NamedTuple):
    root: str
    quality: str
    description: str = ""


class FunctionalHarmonyEngine:
    """Advanced chord progression composer with secondary dominants, tritone substitutions, and modal interchange."""

    SEMITONES = {
        "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3,
        "E": 4, "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8,
        "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11
    }

    PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    # Chord quality semitone structures relative to chord root
    CHORD_INTERVALS: Dict[str, List[int]] = {
        "maj": [0, 4, 7],
        "min": [0, 3, 7],
        "dim": [0, 3, 6],
        "aug": [0, 4, 8],
        "maj7": [0, 4, 7, 11],
        "min7": [0, 3, 7, 10],
        "7": [0, 4, 7, 10],            # Dominant 7th
        "min7b5": [0, 3, 6, 10],       # Half-diminished
        "dim7": [0, 3, 6, 9],          # Fully diminished
        "maj9": [0, 4, 7, 11, 14],
        "min9": [0, 3, 7, 10, 14],
        "9": [0, 4, 7, 10, 14],
        "min11": [0, 3, 7, 10, 14, 17],
        "11": [0, 4, 7, 10, 14, 17],
        "13": [0, 4, 7, 10, 14, 21],
        "7b9": [0, 4, 7, 10, 13],      # Altered minor 9th
        "7#9": [0, 4, 7, 10, 15],      # Hendrix chord
        "7alt": [0, 4, 10, 13, 15, 20],# Altered dominant (b9, #9, b13)
        "7sus4": [0, 5, 7, 10],
    }

    @classmethod
    def get_pitch_class_by_semitone(cls, semitone: int) -> str:
        """Returns standard enharmonic pitch class name."""
        return cls.PITCH_CLASSES[semitone % 12]

    @classmethod
    def get_secondary_dominant(cls, target_root: str, target_quality: str = "maj") -> Tuple[str, str]:
        """
        Calculates the secondary dominant (V7 of target) leading into target_root.
        Returns: (sec_dom_root, '7' or '7alt')
        """
        target_semi = cls.SEMITONES.get(target_root.upper(), 0)
        # V7 is 7 semitones above target (or 5 below)
        sec_root_semi = (target_semi + 7) % 12
        sec_root = cls.get_pitch_class_by_semitone(sec_root_semi)
        quality = "7alt" if "min" in target_quality else "7"
        return sec_root, quality

    @classmethod
    def get_tritone_substitution(cls, dominant_root: str) -> Tuple[str, str]:
        """
        Calculates the tritone substitution (subV7) of a dominant chord.
        subV7 is located 6 semitones (a tritone) away from dominant root.
        Resolves down by a half step to the intended target.
        """
        dom_semi = cls.SEMITONES.get(dominant_root.upper(), 0)
        sub_semi = (dom_semi + 6) % 12
        sub_root = cls.get_pitch_class_by_semitone(sub_semi)
        return sub_root, "7b9"

    @classmethod
    def get_modal_interchange_chords(cls, key_root: str, scale: str = "minor") -> List[BorrowedChord]:
        """
        Returns rich modal interchange chords borrowed from parallel modes:
        (chord_root, quality, borrowed_source_description)
        """
        root_semi = cls.SEMITONES.get(key_root.upper(), 5)

        if "min" in scale.lower():
            # In Minor: borrow Neapolitan bII (Phrygian), IV7 (Dorian), I maj7 (Picardy)
            bII_semi = (root_semi + 1) % 12
            IV_semi = (root_semi + 5) % 12
            v_semi = (root_semi + 7) % 12
            return [
                BorrowedChord(cls.get_pitch_class_by_semitone(bII_semi), "maj7", "Neapolitan bII (Phrygian)"),
                BorrowedChord(cls.get_pitch_class_by_semitone(IV_semi), "9", "IV9 Dorian Major Subdominant"),
                BorrowedChord(cls.get_pitch_class_by_semitone(root_semi), "maj9", "I maj9 Parallel Major Picardy"),
                BorrowedChord(cls.get_pitch_class_by_semitone(v_semi), "7alt", "V7alt Harmonic Minor Dominant")
            ]
        else:
            # In Major: borrow bII (Neapolitan), bVI maj7, iv min9, bVII9, bIII maj7 from parallel minor
            bII_semi = (root_semi + 1) % 12
            bVI_semi = (root_semi + 8) % 12
            iv_semi = (root_semi + 5) % 12
            bVII_semi = (root_semi + 10) % 12
            bIII_semi = (root_semi + 3) % 12
            return [
                BorrowedChord(cls.get_pitch_class_by_semitone(bII_semi), "maj7", "Neapolitan bII (Phrygian)"),
                BorrowedChord(cls.get_pitch_class_by_semitone(bVI_semi), "maj9", "bVI maj9 Borrowed from Aeolian"),
                BorrowedChord(cls.get_pitch_class_by_semitone(iv_semi), "min9", "iv min9 Subdominant Minor"),
                BorrowedChord(cls.get_pitch_class_by_semitone(bVII_semi), "9", "bVII9 Backdoor Dominant"),
                BorrowedChord(cls.get_pitch_class_by_semitone(bIII_semi), "maj7", "bIII maj7 Mediant Borrowing")
            ]

    @classmethod
    def get_augmented_sixth_chord(cls, key_root: str, augmented_type: str = "italian") -> Tuple[str, str, str]:
        """
        Calculates Augmented 6th chord (Italian, French, German) built on b6 resolving down to dominant V.
        Returns: (root, quality, description)
        """
        root_semi = cls.SEMITONES.get(key_root.upper(), 0)
        b6_semi = (root_semi + 8) % 12
        b6_root = cls.get_pitch_class_by_semitone(b6_semi)
        aug_type = augmented_type.lower()
        if "french" in aug_type:
            return b6_root, "7b5", "French +6 (Fr+6)"
        elif "german" in aug_type:
            return b6_root, "7", "German +6 (Ger+6)"
        else:
            return b6_root, "7", "Italian +6 (It+6)"

    @classmethod
    def compose_functional_progression(
        cls,
        key_root: str = "F",
        scale: str = "minor",
        total_bars: int = 16,
        time_signature: Tuple[int, int] = (4, 4),
        allow_secondary_dominants: bool = True,
        allow_tritone_sub: bool = True,
        allow_modal_interchange: bool = True,
        allow_augmented_sixths: bool = True,
        use_secondary_dominants: Optional[bool] = None,
        use_tritone_sub: Optional[bool] = None,
        use_modal_borrowing: Optional[bool] = None,
        seed: int = 42,
        **kwargs
    ) -> List[Chord]:
        """
        Composes a progressive functional harmonic sequence using secondary dominants,
        tritone substitutions, modal interchange, and augmented sixth chords,
        with strict time signature duration scaling for compound and irregular meters.
        """
        sec_dom = use_secondary_dominants if use_secondary_dominants is not None else allow_secondary_dominants
        tri_sub = use_tritone_sub if use_tritone_sub is not None else allow_tritone_sub
        mod_borr = use_modal_borrowing if use_modal_borrowing is not None else allow_modal_interchange
        rng = random.Random(seed)
        root_semi = cls.SEMITONES.get(key_root.upper(), 5)
        is_min = "min" in scale.lower()

        # Dynamic bar duration from time signature (e.g. 4/4 -> 4.0, 3/4 -> 3.0, 6/8 -> 3.0, 7/8 -> 3.5, 5/4 -> 5.0)
        s_num, s_den = time_signature if time_signature else (4, 4)
        bar_dur = float(s_num * (4.0 / max(1, s_den)))

        # Diatonic scale roots in semitones relative to tonic
        if is_min:
            # i, iiø, bIII, iv, v/V, bVI, bVII
            degrees = [0, 2, 3, 5, 7, 8, 10]
            qualities = ["min9", "min7b5", "maj9", "min11", "7alt", "maj9", "9"]
        else:
            # I, ii, iii, IV, V, vi, viiø
            degrees = [0, 2, 4, 5, 7, 9, 11]
            qualities = ["maj9", "min9", "min7", "maj9", "13", "min9", "min7b5"]

        chords: List[Chord] = []
        bar_cursor = 0

        borrowed_pool = cls.get_modal_interchange_chords(key_root, scale)

        while bar_cursor < total_bars:
            remaining_bars = total_bars - bar_cursor

            # Tonic chord on bar 0 or every 8-bar landmark
            if bar_cursor % 8 == 0:
                t_root = key_root
                t_qual = qualities[0]
                chords.append(Chord(root=t_root, quality=t_qual, duration=bar_dur))
                bar_cursor += 1
                continue

            # Approaching final cadence (last bar of an 8-bar phrase or song)
            if (bar_cursor % 8 == 7 or bar_cursor == total_bars - 1):
                # Decide cadence: V7, subV7 (tritone sub), Augmented 6th, or backdoor bVII
                dom_root_semi = (root_semi + 7) % 12
                dom_root = cls.get_pitch_class_by_semitone(dom_root_semi)

                cad_choice = rng.random()
                if tri_sub and cad_choice < 0.40:
                    # Tritone substitution subV7 -> I
                    sub_root, sub_qual = cls.get_tritone_substitution(dom_root)
                    chords.append(Chord(root=sub_root, quality=sub_qual, duration=bar_dur))
                elif allow_augmented_sixths and cad_choice < 0.65:
                    # Augmented 6th chord (+6 -> V -> I)
                    aug_r, aug_q, _ = cls.get_augmented_sixth_chord(key_root, rng.choice(["italian", "french", "german"]))
                    chords.append(Chord(root=aug_r, quality=aug_q, duration=bar_dur))
                else:
                    # Standard or altered dominant
                    chords.append(Chord(root=dom_root, quality="7alt", duration=bar_dur))
                bar_cursor += 1
                continue

            # Modal interchange injection (bars 2, 4, or 6)
            if mod_borr and (bar_cursor % 2 == 0) and rng.random() < 0.40:
                b_chord = rng.choice(borrowed_pool)
                chords.append(Chord(root=b_chord.root, quality=b_chord.quality, duration=bar_dur))
                bar_cursor += 1
                continue

            # Secondary dominant injection before target degree
            if sec_dom and (bar_cursor % 2 == 1) and rng.random() < 0.40:
                target_deg_idx = rng.choice([3, 4, 5]) # iv, V, or bVI
                tgt_semi = (root_semi + degrees[target_deg_idx]) % 12
                tgt_root = cls.get_pitch_class_by_semitone(tgt_semi)
                tgt_qual = qualities[target_deg_idx]

                # Secondary dominant (V7 of target)
                sec_root, sec_qual = cls.get_secondary_dominant(tgt_root, tgt_qual)
                chords.append(Chord(root=sec_root, quality=sec_qual, duration=bar_dur))
                bar_cursor += 1
                continue

            # Standard functional diatonic movement
            deg_idx = rng.choice([1, 2, 3, 5, 6])
            d_semi = (root_semi + degrees[deg_idx]) % 12
            d_root = cls.get_pitch_class_by_semitone(d_semi)
            d_qual = qualities[deg_idx]
            chords.append(Chord(root=d_root, quality=d_qual, duration=bar_dur))
            bar_cursor += 1

        return chords

    @classmethod
    def render_chords_to_notes(
        cls,
        chords: List[Chord],
        start_beat: float = 0.0,
        voicing_type: str = "drop2",
        humanize_velocity: bool = True
    ) -> List[NoteEvent]:
        """
        Renders an abstract Chord progression into concrete NoteEvents with smooth voice leading.
        """
        notes: List[NoteEvent] = []
        curr_beat = start_beat
        prev_voicing: List[int] = []

        for ch in chords:
            root_semi = cls.SEMITONES.get(ch.root.upper(), 5)
            octave_root = 48 + root_semi # Octave 3 (MIDI 48-59)
            intervals = cls.CHORD_INTERVALS.get(ch.quality, [0, 4, 7, 10])

            # Raw pitches
            raw_pitches = [octave_root + iv for iv in intervals[:4]]

            # Drop-2 Voicing: drop second highest note down by an octave
            if voicing_type == "drop2" and len(raw_pitches) >= 4:
                sorted_p = sorted(raw_pitches)
                dropped_note = sorted_p[-2] - 12
                voicing = sorted([sorted_p[0], dropped_note, sorted_p[1], sorted_p[-1]])
            else:
                voicing = raw_pitches

            # Voice leading smoothing: minimize distance from previous voicing
            if prev_voicing:
                smoothed_voicing = []
                for p in voicing:
                    # Shift octave if closer to prev voicing centroid
                    centroid = sum(prev_voicing) / len(prev_voicing)
                    cand_down = p - 12
                    cand_up = p + 12
                    best_p = min([p, cand_down, cand_up], key=lambda x: abs(x - centroid))
                    smoothed_voicing.append(best_p)
                voicing = sorted(smoothed_voicing)

            prev_voicing = voicing

            for v_idx, pitch in enumerate(voicing):
                vel = 84 + (v_idx * 3)
                if humanize_velocity:
                    vel += (v_idx % 3) * 2
                notes.append(NoteEvent(
                    pitch=pitch,
                    start=curr_beat,
                    duration=max(0.5, ch.duration - 0.1),
                    velocity=min(115, vel)
                ))

            curr_beat += ch.duration

        return notes
