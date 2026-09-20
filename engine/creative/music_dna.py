"""
Music DNA Engine (Phase 0):
Structured creative DNA specification that governs how the song thinks musically:
emotional arc, rhythm signatures, modal harmony, melodic intervals, structural lengths,
timbre identity, and novelty scores.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import random


@dataclass
class MusicDNAIdentity:
    concept: str = "euforia nocturna con sensación de movimiento"
    emotional_arc: List[str] = field(default_factory=lambda: [
        "intriga",
        "anticipación",
        "euforia",
        "vacío",
        "segunda euforia",
        "resolución"
    ])


@dataclass
class MusicDNARhythm:
    groove: str = "syncopated"                 # "syncopated", "straight", "triplet", "swung"
    kick_behavior: str = "irregular_phrase_accents" # "four_on_the_floor", "syncopated_trap", "irregular_phrase_accents"
    hat_density: float = 0.63                  # 0.0 to 1.0
    microtiming: float = 0.18                  # Humanized timing variation ratio
    signature_pattern: str = "3-3-2"           # Clave/rhythmic cell: "3-3-2", "straight_4", "tresillo"


@dataclass
class MusicDNAHarmony:
    tonal_center: str = "F#"
    mode: str = "Dorian"                       # "Dorian", "Aeolian", "Phrygian", "Lydian", "Mixolydian"
    chord_language: str = "modal_extended"     # "triads", "seventh_chords", "modal_extended", "altered_clusters"
    progression_behavior: str = "non_looping"  # "looping_4bar", "non_looping", "evolving_stepwise"
    harmonic_surprise: float = 0.72            # 0.0 (predictable) to 1.0 (highly unexpected modulations)


@dataclass
class MusicDNAMelody:
    contour: str = "ascending_then_falling"    # "arch", "ascending_then_falling", "wave", "pendulum"
    interval_language: str = "fourths_and_minor_sixths" # "pentatonic_steps", "fourths_and_minor_sixths", "chromatic_slipping"
    repetition: float = 0.42                   # Ratio of motivic repetition
    motif_length: int = 7                      # Number of notes in core motif


@dataclass
class MusicDNAStructure:
    expected: bool = False                     # False = asymmetric / non-formulaic arrangement
    drop_similarity: float = 0.31              # Divergence between drops (< 0.40 avoids monotony)
    section_lengths: List[int] = field(default_factory=lambda: [8, 12, 8, 16, 10, 24, 8])


@dataclass
class MusicDNASoundIdentity:
    dominant_texture: str = "metallic_warm"    # "metallic_warm", "organic_dusty", "liquid_crystal", "gritty_analog"
    primary_synth_behavior: str = "unstable"   # "unstable", "locked_precise", "drifting_tape", "aggressive_fm"
    vocal_processing: str = "granular_fragments" # "granular_fragments", "dry_intimate", "hyper_tuned", "reverb_drenched"


@dataclass
class MusicDNANovelty:
    rhythmic: float = 0.75
    harmonic: float = 0.62
    melodic: float = 0.81
    structural: float = 0.68
    timbre: float = 0.57


@dataclass
class MusicDNA:
    """Master Music DNA specification defining the artistic and architectural identity of a song."""
    identity: MusicDNAIdentity = field(default_factory=MusicDNAIdentity)
    rhythm: MusicDNARhythm = field(default_factory=MusicDNARhythm)
    harmony: MusicDNAHarmony = field(default_factory=MusicDNAHarmony)
    melody: MusicDNAMelody = field(default_factory=MusicDNAMelody)
    structure: MusicDNAStructure = field(default_factory=MusicDNAStructure)
    sound_identity: MusicDNASoundIdentity = field(default_factory=MusicDNASoundIdentity)
    novelty: MusicDNANovelty = field(default_factory=MusicDNANovelty)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identity": {
                "concept": self.identity.concept,
                "emotional_arc": self.identity.emotional_arc
            },
            "rhythm": {
                "groove": self.rhythm.groove,
                "kick_behavior": self.rhythm.kick_behavior,
                "hat_density": self.rhythm.hat_density,
                "microtiming": self.rhythm.microtiming,
                "signature_pattern": self.rhythm.signature_pattern
            },
            "harmony": {
                "tonal_center": self.harmony.tonal_center,
                "mode": self.harmony.mode,
                "chord_language": self.harmony.chord_language,
                "progression_behavior": self.harmony.progression_behavior,
                "harmonic_surprise": self.harmony.harmonic_surprise
            },
            "melody": {
                "contour": self.melody.contour,
                "interval_language": self.melody.interval_language,
                "repetition": self.melody.repetition,
                "motif_length": self.melody.motif_length
            },
            "structure": {
                "expected": self.structure.expected,
                "drop_similarity": self.structure.drop_similarity,
                "section_lengths": self.structure.section_lengths
            },
            "sound_identity": {
                "dominant_texture": self.sound_identity.dominant_texture,
                "primary_synth_behavior": self.sound_identity.primary_synth_behavior,
                "vocal_processing": self.sound_identity.vocal_processing
            },
            "novelty": {
                "rhythmic": self.novelty.rhythmic,
                "harmonic": self.novelty.harmonic,
                "melodic": self.novelty.melodic,
                "structural": self.novelty.structural,
                "timbre": self.novelty.timbre
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MusicDNA":
        identity_d = data.get("identity", {})
        rhythm_d = data.get("rhythm", {})
        harmony_d = data.get("harmony", {})
        melody_d = data.get("melody", {})
        structure_d = data.get("structure", {})
        sound_d = data.get("sound_identity", {})
        novelty_d = data.get("novelty", {})

        return cls(
            identity=MusicDNAIdentity(
                concept=identity_d.get("concept", "euforia nocturna"),
                emotional_arc=identity_d.get("emotional_arc", ["intriga", "euforia", "resolución"])
            ),
            rhythm=MusicDNARhythm(
                groove=rhythm_d.get("groove", "syncopated"),
                kick_behavior=rhythm_d.get("kick_behavior", "irregular_phrase_accents"),
                hat_density=float(rhythm_d.get("hat_density", 0.63)),
                microtiming=float(rhythm_d.get("microtiming", 0.18)),
                signature_pattern=rhythm_d.get("signature_pattern", "3-3-2")
            ),
            harmony=MusicDNAHarmony(
                tonal_center=harmony_d.get("tonal_center", "F#"),
                mode=harmony_d.get("mode", "Dorian"),
                chord_language=harmony_d.get("chord_language", "modal_extended"),
                progression_behavior=harmony_d.get("progression_behavior", "non_looping"),
                harmonic_surprise=float(harmony_d.get("harmonic_surprise", 0.72))
            ),
            melody=MusicDNAMelody(
                contour=melody_d.get("contour", "ascending_then_falling"),
                interval_language=melody_d.get("interval_language", "fourths_and_minor_sixths"),
                repetition=float(melody_d.get("repetition", 0.42)),
                motif_length=int(melody_d.get("motif_length", 7))
            ),
            structure=MusicDNAStructure(
                expected=bool(structure_d.get("expected", False)),
                drop_similarity=float(structure_d.get("drop_similarity", 0.31)),
                section_lengths=structure_d.get("section_lengths", [8, 12, 8, 16, 10, 24, 8])
            ),
            sound_identity=MusicDNASoundIdentity(
                dominant_texture=sound_d.get("dominant_texture", "metallic_warm"),
                primary_synth_behavior=sound_d.get("primary_synth_behavior", "unstable"),
                vocal_processing=sound_d.get("vocal_processing", "granular_fragments")
            ),
            novelty=MusicDNANovelty(
                rhythmic=float(novelty_d.get("rhythmic", 0.75)),
                harmonic=float(novelty_d.get("harmonic", 0.62)),
                melodic=float(novelty_d.get("melodic", 0.81)),
                structural=float(novelty_d.get("structural", 0.68)),
                timbre=float(novelty_d.get("timbre", 0.57))
            )
        )

    @classmethod
    def generate_for_concept(
        cls,
        concept: str = "",
        genre: str = "hip_hop_neo_soul",
        bpm: float = 120.0,
        key: str = "F",
        mode: str = "Dorian"
    ) -> "MusicDNA":
        """Generates a coherent, rich MusicDNA tailored to user concept or genre."""
        concept_clean = concept.strip() if concept else f"atmósfera {genre} a {bpm:.0f} BPM"
        
        # Determine signature patterns based on genre
        g_lower = genre.lower()
        if "trap" in g_lower or "hip" in g_lower:
            sig = "3-3-2"
            groove = "swung"
            kick_b = "irregular_phrase_accents"
            micro = 0.22
        elif "brostep" in g_lower or "dubstep" in g_lower:
            sig = "syncopated_tearout"
            groove = "syncopated"
            kick_b = "heavy_downbeat_accents"
            micro = 0.12
        elif "house" in g_lower or "club" in g_lower:
            sig = "straight_4"
            groove = "straight"
            kick_b = "four_on_the_floor"
            micro = 0.08
        else:
            sig = "3-3-2"
            groove = "syncopated"
            kick_b = "irregular_phrase_accents"
            micro = 0.18

        return cls(
            identity=MusicDNAIdentity(
                concept=concept_clean,
                emotional_arc=["intriga", "anticipación", "euforia", "vacío", "segunda euforia", "resolución"]
            ),
            rhythm=MusicDNARhythm(
                groove=groove,
                kick_behavior=kick_b,
                hat_density=0.65,
                microtiming=micro,
                signature_pattern=sig
            ),
            harmony=MusicDNAHarmony(
                tonal_center=key,
                mode=mode,
                chord_language="modal_extended",
                progression_behavior="non_looping",
                harmonic_surprise=0.70
            ),
            melody=MusicDNAMelody(
                contour="ascending_then_falling",
                interval_language="fourths_and_minor_sixths",
                repetition=0.40,
                motif_length=7
            ),
            structure=MusicDNAStructure(
                expected=False,
                drop_similarity=0.32,
                section_lengths=[8, 12, 8, 16, 10, 24, 8]
            ),
            sound_identity=MusicDNASoundIdentity(
                dominant_texture="metallic_warm" if "step" in g_lower else "organic_dusty",
                primary_synth_behavior="unstable",
                vocal_processing="granular_fragments"
            ),
            novelty=MusicDNANovelty(
                rhythmic=0.75,
                harmonic=0.65,
                melodic=0.80,
                structural=0.68,
                timbre=0.60
            )
        )
