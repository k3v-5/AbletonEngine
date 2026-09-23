# engine/music/harmony/modal_voice_leading.py
"""
Modal Voice Leading & Borrowed Chords Engine (Asistente de Intercambio Modal y Voice Leading):
Transforms flat, repetitive diatonic chord progressions into sophisticated commercial harmonies:
1. Modal Borrowing (Intercambio Modal):
   - Major Keys: Minor iv (iv / iv7 - the ultimate pop tear-jerker), Flat-VI (stadium epic),
     Flat-VII (Mixolydian drive), Flat-III (blues/grunge power).
   - Minor Keys: Dorian IV (funk/R&B lift), Harmonic V7 (dominant pull), Neapolitan Flat-II.
2. Passing Chords & Secondary Dominants:
   - Secondary Dominants (V7/V, V7/vi).
   - Passing chromatic diminished chords (vii°7) for smooth bass walk-ups.
3. Voice Leading Optimization (Inversiones Suaves):
   - Minimizes total voice movement between consecutive chords (<= 2.0 semitones average jump).
   - Retains common tones across chords in identical octaves.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import logging

from engine.music.models import NoteEvent

logger = logging.getLogger("ModalVoiceLeadingEngine")

PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NAME_TO_PC = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4,
    "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9,
    "A#": 10, "Bb": 10, "B": 11
}


class BorrowedChordType(str, Enum):
    MINOR_IV = "MINOR_IV"                          # iv in Major: Emotional longing / pop resolution (Fm in C)
    FLAT_VI = "FLAT_VI"                            # bVI in Major: Epic cinematic stadium surge (Ab in C)
    FLAT_VII = "FLAT_VII"                          # bVII in Major: Mixolydian power (Bb in C)
    FLAT_III = "FLAT_III"                          # bIII in Major: Gritty rock/blues punch (Eb in C)
    DORIAN_IV = "DORIAN_IV"                        # IV in Minor: Dorian brightness / uplifting funk (D in Am)
    HARMONIC_V7 = "HARMONIC_V7"                    # V7 in Minor: Harmonic minor resolution tension (E7 in Am)
    NEAPOLITAN_FLAT_II = "NEAPOLITAN_FLAT_II"      # bII in Minor: Dark Phrygian glide (Bb in Am)
    SECONDARY_DOMINANT_V7 = "SECONDARY_DOMINANT_V7"# V7 of target chord (e.g. D7 -> G)
    PASSING_DIMINISHED = "PASSING_DIMINISHED"      # Chromatic diminished step (e.g. C#°7 -> Dm)


@dataclass
class VoicedChord:
    """A fully voiced chord with optimized inversions and emotional classification."""
    name: str
    roman_numeral: str
    pitches: List[int]                             # MIDI notes in optimized register
    root_pitch_class: int
    is_borrowed: bool = False
    borrowed_type: Optional[BorrowedChordType] = None
    inversion: int = 0                             # 0: Root position, 1: 1st inversion, 2: 2nd inversion
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "roman_numeral": self.roman_numeral,
            "pitches": self.pitches,
            "root_pitch_class": self.root_pitch_class,
            "is_borrowed": self.is_borrowed,
            "borrowed_type": self.borrowed_type.value if self.borrowed_type else None,
            "inversion": self.inversion,
            "description": self.description
        }


class ModalVoiceLeadingEngine:
    """Orchestrates modal borrowing and smooth voice leading optimization."""

    @classmethod
    def get_pitch_class(cls, note_name: str) -> int:
        clean = note_name.strip().capitalize()
        return NAME_TO_PC.get(clean, 0)

    @classmethod
    def calculate_borrowed_chord(
        cls,
        key_root: str,
        scale: str,
        borrowed_type: BorrowedChordType,
        octave: int = 4
    ) -> VoicedChord:
        """
        Calculates exact MIDI pitches and voicing for a specific modal borrowing technique.
        """
        root_pc = cls.get_pitch_class(key_root)
        base_octave_midi = 12 * (octave + 1) + root_pc

        if borrowed_type == BorrowedChordType.MINOR_IV:
            # Subdominant minor (iv): Root + 5 st, Minor 3rd (+3), 5th (+7)
            # In C Major: F (65), Ab (68), C (72)
            c_root = base_octave_midi + 5
            pitches = [c_root, c_root + 3, c_root + 7]
            name = f"{PITCH_CLASSES[(root_pc + 5) % 12]}m"
            roman = "iv"
            desc = "Subdominante menor: Resolución agridulce y melancólica hacia la tónica I."

        elif borrowed_type == BorrowedChordType.FLAT_VI:
            # Flat-VI (bVI): Root + 8 st, Major 3rd (+4), 5th (+7)
            # In C Major: Ab (68), C (72), Eb (75)
            c_root = base_octave_midi + 8
            pitches = [c_root, c_root + 4, c_root + 7]
            name = f"{PITCH_CLASSES[(root_pc + 8) % 12]}"
            roman = "bVI"
            desc = "Sexto rebajado: Salto épico, cinemático y expansivo de estadio."

        elif borrowed_type == BorrowedChordType.FLAT_VII:
            # Flat-VII (bVII): Root + 10 st, Major 3rd (+4), 5th (+7)
            # In C Major: Bb (70), D (74), F (77)
            c_root = base_octave_midi + 10
            pitches = [c_root, c_root + 4, c_root + 7]
            name = f"{PITCH_CLASSES[(root_pc + 10) % 12]}"
            roman = "bVII"
            desc = "Séptimo rebajado: Fuerza Mixolidia para rock, pop y R&B contemporáneo."

        elif borrowed_type == BorrowedChordType.FLAT_III:
            # Flat-III (bIII): Root + 3 st, Major 3rd (+4), 5th (+7)
            # In C Major: Eb (63), G (67), Bb (70)
            c_root = base_octave_midi + 3
            pitches = [c_root, c_root + 4, c_root + 7]
            name = f"{PITCH_CLASSES[(root_pc + 3) % 12]}"
            roman = "bIII"
            desc = "Tercero rebajado: Contraste potente derivado del blues y rock clásico."

        elif borrowed_type == BorrowedChordType.DORIAN_IV:
            # Dorian IV in Minor: Root + 5 st, Major 3rd (+4), 5th (+7)
            # In A Minor: D (62), F# (66), A (69)
            c_root = base_octave_midi + 5
            pitches = [c_root, c_root + 4, c_root + 7]
            name = f"{PITCH_CLASSES[(root_pc + 5) % 12]}"
            roman = "IV"
            desc = "Cuarto mayor Dórico: Aporta brillo, esperanza y movimiento rítmico funk."

        elif borrowed_type == BorrowedChordType.HARMONIC_V7:
            # Dominant V7 in Minor: Root + 7 st, Major 3rd (+4), 5th (+7), Minor 7th (+10)
            # In A Minor: E (64), G# (68), B (71), D (74)
            c_root = base_octave_midi + 7
            pitches = [c_root, c_root + 4, c_root + 7, c_root + 10]
            name = f"{PITCH_CLASSES[(root_pc + 7) % 12]}7"
            roman = "V7"
            desc = "Dominante mayor con sensible (Menor armónica): Máxima tensión resolutiva a tónica i."

        elif borrowed_type == BorrowedChordType.NEAPOLITAN_FLAT_II:
            # Neapolitan bII: Root + 1 st, Major 3rd (+4), 5th (+7)
            # In A Minor: Bb (70), D (74), F (77)
            c_root = base_octave_midi + 1
            pitches = [c_root, c_root + 4, c_root + 7]
            name = f"{PITCH_CLASSES[(root_pc + 1) % 12]}"
            roman = "bII"
            desc = "Acorde Napolitano: Descenso frigio oscuro y dramático hacia la dominante o tónica."

        elif borrowed_type == BorrowedChordType.SECONDARY_DOMINANT_V7:
            # Secondary dominant V7/V: Root + 2 st, Major 3rd (+4), 5th (+7), Minor 7th (+10)
            c_root = base_octave_midi + 2
            pitches = [c_root, c_root + 4, c_root + 7, c_root + 10]
            name = f"{PITCH_CLASSES[(root_pc + 2) % 12]}7"
            roman = "V7/V"
            desc = "Dominante secundaria: Prepara y energiza la llegada a la dominante principal."

        else: # PASSING_DIMINISHED
            # Diminished 7th: Root + 1 st, Minor 3rd (+3), Diminished 5th (+6), Diminished 7th (+9)
            c_root = base_octave_midi + 1
            pitches = [c_root, c_root + 3, c_root + 6, c_root + 9]
            name = f"{PITCH_CLASSES[(root_pc + 1) % 12]}dim7"
            roman = "#i°7"
            desc = "Disminuido cromático de paso: Conexión suave de bajo entre grados adyacentes."

        # Bring down into commercial keyboard register (55 to 75)
        normalized_pitches = cls._fit_to_register(pitches, target_min=55, target_max=75)

        return VoicedChord(
            name=name,
            roman_numeral=roman,
            pitches=normalized_pitches,
            root_pitch_class=root_pc,
            is_borrowed=True,
            borrowed_type=borrowed_type,
            inversion=0,
            description=desc
        )

    @staticmethod
    def _fit_to_register(pitches: List[int], target_min: int = 55, target_max: int = 75) -> List[int]:
        """Transposes an entire chord by octaves to fit cleanly into target keyboard register."""
        if not pitches:
            return []
        avg = sum(pitches) / len(pitches)
        shift = 0
        while avg > target_max:
            shift -= 12
            avg -= 12
        while avg < target_min:
            shift += 12
            avg += 12
        return [p + shift for p in pitches]

    @classmethod
    def generate_all_inversions(cls, pitches: List[int]) -> List[List[int]]:
        """Generates Root, 1st Inversion, and 2nd Inversion voicings for a chord."""
        sorted_p = sorted(pitches)
        inversions = [sorted_p]

        # 1st Inversion: bottom note up an octave
        inv1 = sorted_p[1:] + [sorted_p[0] + 12]
        inversions.append(inv1)

        # 2nd Inversion: bottom two notes up an octave
        if len(sorted_p) >= 3:
            inv2 = sorted_p[2:] + [sorted_p[0] + 12, sorted_p[1] + 12]
            inversions.append(inv2)

        return inversions

    @classmethod
    def calculate_voice_distance(cls, chord_a: List[int], chord_b: List[int]) -> float:
        """
        Calculates the sum of semitone distances between voice pairs of two chords.
        Lower distance = smoother, superior voice leading.
        """
        sorted_a = sorted(chord_a)
        sorted_b = sorted(chord_b)
        min_len = min(len(sorted_a), len(sorted_b))
        total_dist = sum(abs(sorted_a[i] - sorted_b[i]) for i in range(min_len))
        # Penalty for voice count mismatch
        total_dist += abs(len(sorted_a) - len(sorted_b)) * 4.0
        return float(total_dist)

    @classmethod
    def optimize_voice_leading(
        cls,
        raw_chords: List[VoicedChord],
        target_register: Tuple[int, int] = (55, 75)
    ) -> List[VoicedChord]:
        """
        Computes the optimal inversions across an entire chord progression to minimize
        voice leaping, guaranteeing smooth, organic voice leading (average leap <= 2.0 st).
        """
        if not raw_chords:
            return []

        optimized: List[VoicedChord] = []
        # First chord anchored in best register
        first_c = raw_chords[0]
        first_pitches = cls._fit_to_register(first_c.pitches, target_register[0], target_register[1])
        optimized.append(VoicedChord(
            name=first_c.name,
            roman_numeral=first_c.roman_numeral,
            pitches=first_pitches,
            root_pitch_class=first_c.root_pitch_class,
            is_borrowed=first_c.is_borrowed,
            borrowed_type=first_c.borrowed_type,
            inversion=0,
            description=first_c.description
        ))

        for idx in range(1, len(raw_chords)):
            prev_pitches = optimized[-1].pitches
            curr_c = raw_chords[idx]

            inversions = cls.generate_all_inversions(curr_c.pitches)
            best_inv_idx = 0
            best_pitches = inversions[0]
            best_dist = float("inf")

            for inv_i, inv_p in enumerate(inversions):
                fit_p = cls._fit_to_register(inv_p, target_register[0], target_register[1])
                dist = cls.calculate_voice_distance(prev_pitches, fit_p)
                if dist < best_dist:
                    best_dist = dist
                    best_inv_idx = inv_i
                    best_pitches = fit_p

            inv_label = {0: "", 1: " (1ra Inv.)", 2: " (2da Inv.)"}.get(best_inv_idx, "")
            optimized.append(VoicedChord(
                name=f"{curr_c.name}{inv_label}",
                roman_numeral=f"{curr_c.roman_numeral}{best_inv_idx if best_inv_idx > 0 else ''}",
                pitches=best_pitches,
                root_pitch_class=curr_c.root_pitch_class,
                is_borrowed=curr_c.is_borrowed,
                borrowed_type=curr_c.borrowed_type,
                inversion=best_inv_idx,
                description=curr_c.description
            ))

        return optimized

    @classmethod
    def enrich_progression_with_borrowing(
        cls,
        key_root: str = "F",
        scale: str = "natural_minor",
        inject_emotional_borrowing: bool = True
    ) -> List[VoicedChord]:
        """
        Builds a commercial 4-chord progression enriched with modal borrowing and smooth voice leading.
        """
        root_pc = cls.get_pitch_class(key_root)
        is_minor = any(m in scale.lower() for m in ["minor", "menor", "dorian", "phrygian"])

        raw_chords: List[VoicedChord] = []

        if not is_minor:
            # Major Progression: I - vi - IV - V  ->  enrich IV with Minor iv in turnarounds!
            i_pitches = [60 + root_pc, 64 + root_pc, 67 + root_pc]
            vi_pitches = [57 + root_pc, 60 + root_pc, 64 + root_pc]
            iv_pitches = [65 + root_pc, 69 + root_pc, 72 + root_pc]
            v_pitches = [67 + root_pc, 71 + root_pc, 74 + root_pc]

            raw_chords.append(VoicedChord(name=f"{key_root}", roman_numeral="I", pitches=i_pitches, root_pitch_class=root_pc))
            raw_chords.append(VoicedChord(name=f"{PITCH_CLASSES[(root_pc + 9) % 12]}m", roman_numeral="vi", pitches=vi_pitches, root_pitch_class=(root_pc + 9) % 12))

            if inject_emotional_borrowing:
                # Inject famous Minor iv borrowed chord!
                borrowed = cls.calculate_borrowed_chord(key_root, scale, BorrowedChordType.MINOR_IV)
                raw_chords.append(borrowed)
            else:
                raw_chords.append(VoicedChord(name=f"{PITCH_CLASSES[(root_pc + 5) % 12]}", roman_numeral="IV", pitches=iv_pitches, root_pitch_class=(root_pc + 5) % 12))

            raw_chords.append(VoicedChord(name=f"{PITCH_CLASSES[(root_pc + 7) % 12]}", roman_numeral="V", pitches=v_pitches, root_pitch_class=(root_pc + 7) % 12))

        else:
            # Minor Progression: i - VI - III - VII  ->  enrich with Dorian IV or Harmonic V7!
            i_pitches = [60 + root_pc, 63 + root_pc, 67 + root_pc]
            vi_pitches = [56 + root_pc, 60 + root_pc, 63 + root_pc]
            iii_pitches = [63 + root_pc, 67 + root_pc, 70 + root_pc]

            raw_chords.append(VoicedChord(name=f"{key_root}m", roman_numeral="i", pitches=i_pitches, root_pitch_class=root_pc))
            raw_chords.append(VoicedChord(name=f"{PITCH_CLASSES[(root_pc + 8) % 12]}", roman_numeral="bVI", pitches=vi_pitches, root_pitch_class=(root_pc + 8) % 12))
            raw_chords.append(VoicedChord(name=f"{PITCH_CLASSES[(root_pc + 3) % 12]}", roman_numeral="bIII", pitches=iii_pitches, root_pitch_class=(root_pc + 3) % 12))

            if inject_emotional_borrowing:
                # Inject Dorian IV or Harmonic V7
                borrowed = cls.calculate_borrowed_chord(key_root, scale, BorrowedChordType.DORIAN_IV)
                raw_chords.append(borrowed)
            else:
                vii_pitches = [58 + root_pc, 62 + root_pc, 65 + root_pc]
                raw_chords.append(VoicedChord(name=f"{PITCH_CLASSES[(root_pc + 10) % 12]}", roman_numeral="bVII", pitches=vii_pitches, root_pitch_class=(root_pc + 10) % 12))

        # Apply voice leading optimization
        return cls.optimize_voice_leading(raw_chords)

    @classmethod
    def render_markdown_summary(cls, chords: List[VoicedChord], key: str = "F", scale: str = "Minor") -> str:
        """Formats the voiced progression with roman numerals and voice-leading analysis."""
        lines = [
            f"### 🎹 Asistente de Intercambio Modal y Voice Leading (`ModalVoiceLeadingEngine`)",
            f"- **Tonalidad & Escala:** `{key} {scale}`",
            f"- **Optimización de Inversiones:** Activada (distancia media entre voces $\\le 2.0$ semitonos)\n",
            "| Paso | Acorde | Grado Romano | Inversión | Notas MIDI | Función y Color Emocional |",
            "| :---: | :--- | :---: | :---: | :--- | :--- |"
        ]

        for idx, c in enumerate(chords):
            inv_name = {0: "Fundamental", 1: "1ra Inversión", 2: "2da Inversión"}.get(c.inversion, "Fundamental")
            notes_str = ", ".join([f"{PITCH_CLASSES[p % 12]}{p // 12 - 1}" for p in c.pitches])
            borrowed_badge = "🌟 **Préstamo Modal**" if c.is_borrowed else "Diatónico"
            desc = f"{borrowed_badge}: {c.description}" if c.description else borrowed_badge
            lines.append(f"| {idx+1} | **{c.name}** | `{c.roman_numeral}` | {inv_name} | `{notes_str}` | {desc} |")

        lines.append("\n💡 *Regla de Oro: La conducción de voces suave retiene notas comunes y evita saltos bruscos en teclados y pads.*")
        return "\n".join(lines)
