# engine/music/composition_mutation_engine.py
"""
Composition Mutation Engine (Phase M):
Enables musical and harmonic evolution without loss of genetic DNA.
Applies:
- Dominant substitutions (tritone substitutions, secondary dominants V7/X, altered dominants)
- Modal interchange / borrowed chords (Dorian, Phrygian, Lydian, Aeolian)
- Smooth voice leading & inversions (stepwise bass lines, slash chords)
- Sophisticated extensions (9ths, 11ths, 13ths)
- Pedal tones & common-tone bass movement
- Selective phrase / turnaround reharmonization (bars 7-8)
- Delayed resolutions & suspension displacements (4-3, 9-8)

Fundamental Law:
"No mutar por mutar. La mutación debe responder a la narrativa y al Song Contract."
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
import copy
import logging

from engine.music.models import Chord, NoteEvent
from engine.composition.compositional_dna import CompositionalDNA

logger = logging.getLogger("CompositionMutationEngine")

PITCH_NAMES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
EQUIVALENTS = {"C#": "Db", "D#": "Eb", "F#": "Gb", "G#": "Ab", "A#": "Bb"}


def normalize_pitch(p: str) -> str:
    clean = p.capitalize()
    return EQUIVALENTS.get(clean, clean)


class MutationType(str, Enum):
    DOMINANT_SUBSTITUTION = "dominant_substitution"
    MODAL_BORROWING = "modal_borrowing"
    VOICE_LEADING_INVERSION = "voice_leading_inversion"
    EXTENSION_COLORING = "extension_coloring"
    PEDAL_BASS_TENSION = "pedal_bass_tension"
    SELECTIVE_TURNAROUND_REHARM = "selective_turnaround_reharm"
    RESOLUTION_DISPLACEMENT = "resolution_displacement"


@dataclass
class MutationResult:
    """The outcome of a narrative musical mutation."""
    original_chords: List[Chord]
    mutated_chords: List[Chord]
    techniques_applied: List[MutationType]
    narrative_justification: str
    dna_coherence_score: float = 0.95
    tension_delta: float = 0.25

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_chord_count": len(self.original_chords),
            "mutated_chord_count": len(self.mutated_chords),
            "techniques_applied": [t.value for t in self.techniques_applied],
            "narrative_justification": self.narrative_justification,
            "dna_coherence_score": round(self.dna_coherence_score, 2),
            "tension_delta": round(self.tension_delta, 2),
            "mutated_progression": [c.__dict__ for c in self.mutated_chords],
        }


class CompositionMutationEngine:
    """
    Transforms harmonic and melodic progressions along the narrative timeline.
    Guarantees structural freshness while anchoring thematic DNA.
    """

    @classmethod
    def get_sub_v7_root(cls, target_root: str) -> str:
        """Returns the root note a half-step (1 semitone) above target root (SubV7)."""
        norm = normalize_pitch(target_root)
        try:
            idx = PITCH_NAMES.index(norm)
            return PITCH_NAMES[(idx + 1) % 12]
        except ValueError:
            return "E"

    @classmethod
    def get_tritone_sub_root(cls, root: str) -> str:
        """Returns the root note a tritone (6 semitones) away."""
        norm = normalize_pitch(root)
        try:
            idx = PITCH_NAMES.index(norm)
            return PITCH_NAMES[(idx + 6) % 12]
        except ValueError:
            return "A"

    @classmethod
    def get_secondary_dominant_root(cls, target_root: str) -> str:
        norm = normalize_pitch(target_root)
        try:
            idx = PITCH_NAMES.index(norm)
            return PITCH_NAMES[(idx + 7) % 12]
        except ValueError:
            return "G"

    @classmethod
    def apply_tritone_substitution(
        cls,
        chords: List[Chord],
        target_idx: Optional[int] = None
    ) -> List[Chord]:
        """Substitutes a V7 chord with its tritone SubV7 (half-step above target)."""
        result = [copy.deepcopy(c) for c in chords]
        if not result:
            return result

        idx_to_sub = target_idx if target_idx is not None else (len(result) - 1)
        if 0 <= idx_to_sub < len(result):
            curr = result[idx_to_sub]
            sub_root = cls.get_tritone_sub_root(curr.root)
            curr.root = sub_root
            curr.quality = "dominant7"
            curr.extensions = ["9", "#11"]
            curr.roman_numeral = f"SubV7/{sub_root}"
        return result

    @classmethod
    def apply_secondary_dominant(
        cls,
        chords: List[Chord],
        target_idx: int = 1
    ) -> List[Chord]:
        """Inserts a V7/X secondary dominant right before the target chord."""
        result: List[Chord] = []
        for i, c in enumerate(chords):
            if i == target_idx and c.duration >= 2.0:
                # Borrow time from preceding chord if possible, or split
                prev_dur = c.duration / 2.0
                c.duration = prev_dur
                sec_root = cls.get_secondary_dominant_root(c.root)
                sec_chord = Chord(
                    root=sec_root,
                    quality="dominant7",
                    extensions=["9", "b13"],
                    duration=prev_dur,
                    roman_numeral=f"V7/{c.root}"
                )
                result.append(sec_chord)
            result.append(copy.deepcopy(c))
        return result

    @classmethod
    def apply_modal_borrowing(
        cls,
        chords: List[Chord],
        source_mode: str = "dorian",
        borrow_idx: int = 1
    ) -> List[Chord]:
        """Injects a borrowed chord from a parallel mode (e.g. IV in natural minor, or bVI in major)."""
        result = [copy.deepcopy(c) for c in chords]
        if 0 <= borrow_idx < len(result):
            target = result[borrow_idx]
            if source_mode == "dorian":
                # Dorian raises 6th: Major IV in minor key
                target.quality = "dominant7" if "dom" in target.quality else "major7"
                target.extensions = list(set(target.extensions + ["9", "13"]))
                target.roman_numeral = f"IV_{source_mode}"
            elif source_mode == "phrygian":
                # Phrygian lowers 2nd: Major bII (Neapolitan flavor)
                target.quality = "major7"
                target.extensions = list(set(target.extensions + ["#11"]))
                target.roman_numeral = f"bII_{source_mode}"
        return result

    @classmethod
    def apply_inversions_and_voice_leading(
        cls,
        chords: List[Chord]
    ) -> List[Chord]:
        """Applies slash-chords and smooth step-wise bass motion across the progression."""
        result = [copy.deepcopy(c) for c in chords]
        if len(result) >= 3:
            # First inversion on chord 2 for ascending bass line
            norm_root = normalize_pitch(result[1].root)
            try:
                root_idx = PITCH_NAMES.index(norm_root)
                # Third is +3 or +4 semitones
                third_idx = (root_idx + (3 if "min" in result[1].quality else 4)) % 12
                result[1].inversion = 1
                result[1].bass_note = PITCH_NAMES[third_idx]
            except ValueError:
                pass
        return result

    @classmethod
    def apply_extensions(
        cls,
        chords: List[Chord],
        extensions: Optional[List[str]] = None
    ) -> List[Chord]:
        """Elevates simple chords to sophisticated 9th, 11th, and 13th voicings."""
        exts = extensions or ["9", "11"]
        result = [copy.deepcopy(c) for c in chords]
        for c in result:
            c.extensions = sorted(list(set(c.extensions + exts)))
            if "min" in c.quality:
                c.quality = "minor9"
            elif "maj" in c.quality:
                c.quality = "major9"
        return result

    @classmethod
    def apply_pedal_bass(
        cls,
        chords: List[Chord],
        pedal_pitch: str = "Eb"
    ) -> List[Chord]:
        """Locks all bass notes to a continuous pedal tone, creating rich harmonic tension."""
        result = [copy.deepcopy(c) for c in chords]
        pedal_norm = normalize_pitch(pedal_pitch)
        for c in result:
            c.bass_note = pedal_norm
            c.roman_numeral = f"{c.roman_numeral or c.root}/{pedal_norm}"
        return result

    @classmethod
    def reharmonize_turnaround(
        cls,
        chords: List[Chord],
        tension: float = 0.7
    ) -> List[Chord]:
        """Replaces or enriches the turnaround (final bar) with high-tension resolution preparation."""
        result = [copy.deepcopy(c) for c in chords]
        if not result:
            return result

        last = result[-1]
        if last.duration >= 3.0:
            main_dur = round(last.duration - 1.0, 2)
            pass_dur = 1.0
            last.duration = main_dur

            first_root = result[0].root
            sub_root = cls.get_sub_v7_root(first_root)

            turnaround = Chord(
                root=sub_root,
                quality="dominant7",
                extensions=["9", "#11"] if tension > 0.5 else ["7"],
                duration=pass_dur,
                roman_numeral=f"SubV7/{first_root}"
            )
            result.append(turnaround)
        return result

    @classmethod
    def displace_resolution(
        cls,
        chords: List[Chord],
        delay_beats: float = 1.0
    ) -> List[Chord]:
        """Delays the expected harmonic resolution by extending cadential suspension."""
        result = [copy.deepcopy(c) for c in chords]
        if len(result) >= 2:
            penultimate = result[-2]
            ultimate = result[-1]
            if ultimate.duration > delay_beats:
                penultimate.duration = round(penultimate.duration + delay_beats, 2)
                ultimate.duration = round(ultimate.duration - delay_beats, 2)
                penultimate.extensions = sorted(list(set(penultimate.extensions + ["sus4", "9"])))
        return result

    @classmethod
    def mutate_for_narrative_context(
        cls,
        chords: List[Chord],
        section_name: str,
        dna: Optional[CompositionalDNA] = None,
        emotional_intensity: float = 0.7
    ) -> MutationResult:
        """
        Applies musical mutation governed by narrative section purpose:
        - Verse 2: Inversions & subtle 9th extensions (intimate, moving).
        - Bridge: Modal borrowing + Pedal tone tension (contrast & suspension).
        - Hook 3: Tritone turnaround + resolution displacement + 11th/13th extensions (climactic release).
        """
        sec_lower = section_name.lower()
        applied: List[MutationType] = []
        mutated = [copy.deepcopy(c) for c in chords]

        if "verse" in sec_lower:
            # Verse 2: Add smooth voice leading and 9th extensions
            mutated = cls.apply_inversions_and_voice_leading(mutated)
            applied.append(MutationType.VOICE_LEADING_INVERSION)
            mutated = cls.apply_extensions(mutated, ["9"])
            applied.append(MutationType.EXTENSION_COLORING)
            justification = f"{section_name}: Smooth voice leading with 9th extensions to maintain narrative intimacy."
            coherence = 0.96
            delta = 0.15

        elif "bridge" in sec_lower:
            # Bridge: Dramatic contrast via modal borrowing and pedal tone
            pedal_root = dna.primary_motif.tonal_center if dna else (chords[0].root if chords else "Eb")
            mutated = cls.apply_modal_borrowing(mutated, source_mode="dorian", borrow_idx=1)
            applied.append(MutationType.MODAL_BORROWING)
            mutated = cls.apply_pedal_bass(mutated, pedal_pitch=pedal_root)
            applied.append(MutationType.PEDAL_BASS_TENSION)
            justification = f"{section_name}: Modal borrowing with {pedal_root} pedal tone for introspective dynamic tension."
            coherence = 0.91
            delta = 0.35

        elif "hook" in sec_lower or "chorus" in sec_lower:
            # Hook 3 / Final Climax: Turnaround reharm + resolution displacement + rich extensions
            mutated = cls.apply_extensions(mutated, ["9", "11", "13"])
            applied.append(MutationType.EXTENSION_COLORING)
            mutated = cls.reharmonize_turnaround(mutated, tension=emotional_intensity)
            applied.append(MutationType.SELECTIVE_TURNAROUND_REHARM)
            mutated = cls.displace_resolution(mutated, delay_beats=1.0)
            applied.append(MutationType.RESOLUTION_DISPLACEMENT)
            justification = f"{section_name}: Climactic turnaround reharmonization with delayed tonic resolution and 13th extensions."
            coherence = 0.94
            delta = 0.42

        else:
            # General subtle elevation
            mutated = cls.apply_extensions(mutated, ["9"])
            applied.append(MutationType.EXTENSION_COLORING)
            justification = f"{section_name}: DNA-consistent extension enrichment."
            coherence = 0.95
            delta = 0.10

        return MutationResult(
            original_chords=chords,
            mutated_chords=mutated,
            techniques_applied=applied,
            narrative_justification=justification,
            dna_coherence_score=coherence,
            tension_delta=delta
        )
