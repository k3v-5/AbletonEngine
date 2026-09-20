"""
Leitmotif Engine:
Defines primary and secondary recurring musical motifs with interval/rhythm vectors
and algorithmic mutation rules across song sections (Intro, Verse, Build, Drop, Drop 2, Outro).
Ensures coherent thematic identity throughout the composition.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import random
from .music_dna import MusicDNA


@dataclass
class Leitmotif:
    """Representation of a recurring musical leitmotif."""
    id: str
    name: str
    motif_type: str = "primary"  # "primary" or "secondary"
    intervals: List[int] = field(default_factory=lambda: [0, 3, 5, 7, 10, 7, 5])  # Semitone offsets from root
    rhythm: List[float] = field(default_factory=lambda: [0.5, 0.5, 1.0, 0.5, 0.5, 1.0, 2.0])  # Durations in beats
    offsets: List[float] = field(default_factory=lambda: [0.0, 0.5, 1.0, 2.0, 2.5, 3.0, 4.0]) # Start beat positions
    accents: List[float] = field(default_factory=lambda: [1.0, 0.7, 0.9, 0.8, 0.7, 0.95, 0.6]) # Velocity scales
    length_beats: float = 8.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "motif_type": self.motif_type,
            "intervals": self.intervals,
            "rhythm": self.rhythm,
            "offsets": self.offsets,
            "accents": self.accents,
            "length_beats": self.length_beats,
        }


class LeitmotifEngine:
    """
    Orchestrates the creation, mutation, and distribution of persistent leitmotifs across song sections.
    """

    # Section-specific transformation rules
    SECTION_RULES = {
        "intro": "texture",          # Sparse, filtered, atmospheric fragments
        "verse": "bass",             # Carried by bassline / low counter-melody
        "build": "vocal_arp",        # Arpeggiated / rising pitch tension
        "drop": "lead",              # Full melodic focal statement
        "drop2": "reharmonization",  # Altered intervals, syncopated phrasing
        "break": "texture",          # Stripped back, ambient echoes
        "outro": "drone"             # Decaying echoes, sustained root with motif fragments
    }

    def __init__(self, dna: Optional[MusicDNA] = None):
        self.dna = dna or MusicDNA()
        self.primary_motif: Optional[Leitmotif] = None
        self.secondary_motif: Optional[Leitmotif] = None
        self._initialize_motifs()

    def _initialize_motifs(self):
        """Generates primary and secondary leitmotifs based on MusicDNA."""
        # Primary motif intervals from DNA
        if self.dna.melody.interval_language == "fourths_and_minor_sixths":
            primary_intervals = [0, 5, 8, 5, 10, 8, 7]
            primary_rhythm = [0.75, 0.25, 1.0, 0.75, 0.25, 1.0, 2.0]
            primary_offsets = [0.0, 0.75, 1.0, 2.0, 2.75, 3.0, 4.0]
        elif self.dna.melody.interval_language == "chromatic_slipping":
            primary_intervals = [0, 1, 3, 2, 5, 4, 7]
            primary_rhythm = [0.5, 0.5, 0.5, 0.5, 1.0, 1.0, 2.0]
            primary_offsets = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0]
        else:  # pentatonic / default
            primary_intervals = [0, 3, 5, 7, 10, 7, 0]
            primary_rhythm = [0.5, 0.5, 1.0, 0.5, 0.5, 1.0, 2.0]
            primary_offsets = [0.0, 0.5, 1.0, 2.0, 2.5, 3.0, 4.0]

        # Syncopated 3-3-2 timing adjustments if specified in DNA
        if self.dna.rhythm.signature_pattern == "3-3-2":
            primary_offsets = [0.0, 0.75, 1.5, 2.0, 2.75, 3.5, 4.0]

        self.primary_motif = Leitmotif(
            id="motif_primary_core",
            name="Primary Core Leitmotif",
            motif_type="primary",
            intervals=primary_intervals[:self.dna.melody.motif_length],
            rhythm=primary_rhythm[:self.dna.melody.motif_length],
            offsets=primary_offsets[:self.dna.melody.motif_length],
            accents=[0.95, 0.75, 0.9, 0.8, 0.7, 1.0, 0.6][:self.dna.melody.motif_length],
            length_beats=8.0
        )

        # Secondary counter-motif (answering phrase)
        sec_intervals = [p - 12 if p > 7 else p + 7 for p in primary_intervals[::-1]]
        sec_rhythm = [r * 0.5 for r in primary_rhythm]
        sec_offsets = [o + 0.5 for o in primary_offsets]

        self.secondary_motif = Leitmotif(
            id="motif_secondary_counter",
            name="Secondary Counter Leitmotif",
            motif_type="secondary",
            intervals=sec_intervals[:self.dna.melody.motif_length],
            rhythm=sec_rhythm[:self.dna.melody.motif_length],
            offsets=sec_offsets[:self.dna.melody.motif_length],
            accents=[0.8, 0.65, 0.85, 0.7, 0.6, 0.9, 0.5][:self.dna.melody.motif_length],
            length_beats=8.0
        )

    def realize_for_section(
        self,
        section_name: str,
        root_pitch: int = 60,
        motif_type: str = "primary",
        bar_offset_beats: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Renders the leitmotif into Ableton-compatible note events transformed
        according to the target section's emotional and structural role.
        """
        base_motif = self.primary_motif if motif_type == "primary" else self.secondary_motif
        if not base_motif:
            return []

        sec_key = section_name.lower().strip()
        rule = "lead"
        for key, r in self.SECTION_RULES.items():
            if key in sec_key:
                rule = r
                break

        notes: List[Dict[str, Any]] = []

        if rule == "texture":
            # Intro/Break: Sparse, high register (+12 or +24), low velocity (40-60)
            for i, (interval, dur, off, acc) in enumerate(zip(
                base_motif.intervals, base_motif.rhythm, base_motif.offsets, base_motif.accents
            )):
                if i % 2 == 0:  # Sparse: skip half the notes
                    notes.append({
                        "pitch": root_pitch + 12 + interval,
                        "time": bar_offset_beats + off,
                        "duration": dur * 1.5,
                        "velocity": int(50 * acc)
                    })

        elif rule == "bass":
            # Verse: Shift down 2 octaves (-24), punchy, focus on root & fifth
            for interval, dur, off, acc in zip(
                base_motif.intervals, base_motif.rhythm, base_motif.offsets, base_motif.accents
            ):
                bass_interval = interval if interval in [0, 7, 5, 3] else 0
                notes.append({
                    "pitch": root_pitch - 24 + bass_interval,
                    "time": bar_offset_beats + off,
                    "duration": max(0.25, dur * 0.75),
                    "velocity": int(90 * acc)
                })

        elif rule == "vocal_arp":
            # Build: Double speed (diminution), rising velocities to create tension
            for i, (interval, dur, off, acc) in enumerate(zip(
                base_motif.intervals, base_motif.rhythm, base_motif.offsets, base_motif.accents
            )):
                ramp = 0.6 + (i / max(1, len(base_motif.intervals))) * 0.4
                notes.append({
                    "pitch": root_pitch + interval,
                    "time": bar_offset_beats + (off * 0.5),
                    "duration": max(0.125, dur * 0.5),
                    "velocity": int(110 * acc * ramp)
                })

        elif rule == "reharmonization":
            # Drop 2: Invert some intervals, shift chord extensions (+3 or +4 semitones)
            for interval, dur, off, acc in zip(
                base_motif.intervals, base_motif.rhythm, base_motif.offsets, base_motif.accents
            ):
                reharm_interval = (interval + 3) % 12
                notes.append({
                    "pitch": root_pitch + reharm_interval,
                    "time": bar_offset_beats + off + 0.25,  # Syncopated displacement
                    "duration": dur,
                    "velocity": int(105 * acc)
                })

        elif rule == "drone":
            # Outro: Sustained root with trailing motif fragment
            notes.append({
                "pitch": root_pitch,
                "time": bar_offset_beats,
                "duration": 6.0,
                "velocity": 70
            })
            if base_motif.intervals:
                notes.append({
                    "pitch": root_pitch + base_motif.intervals[-1],
                    "time": bar_offset_beats + 6.0,
                    "duration": 2.0,
                    "velocity": 50
                })

        else:
            # Drop / Lead: Bold full statement
            for interval, dur, off, acc in zip(
                base_motif.intervals, base_motif.rhythm, base_motif.offsets, base_motif.accents
            ):
                notes.append({
                    "pitch": root_pitch + interval,
                    "time": bar_offset_beats + off,
                    "duration": dur,
                    "velocity": int(100 * acc)
                })

        return notes
