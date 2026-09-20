"""
Organic Rhythm Layer & Hybrid Drum Engine:
Integrates organic foley textures into rhythmic drum patterns through dynamic inheritance
and Timbre DNA complementarity:
- Foley hits inherit velocity, microtiming, and accents from parent drum hits.
- Drum hits are complemented rather than mechanically doubled (beat 2 wood crack, beat 4 metal hit, turnaround door slam).
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import random
import logging

from engine.music.models import NoteEvent
from engine.sound.timbre_dna import TimbreDNA

logger = logging.getLogger("OrganicRhythm")


@dataclass
class OrganicFoleySample:
    name: str
    category: str              # "wood_crack", "metal_hit", "door_thump", "cloth_rip", "vocal_chop"
    midi_pitch: int            # Target pitch in drum rack / sampler
    dna: TimbreDNA
    preferred_beats: List[float] = field(default_factory=lambda: [2.0, 4.0])
    microtiming_offset_beats: float = 0.002



class OrganicRhythmCoordinator:
    """
    Coordinates hybrid drums and organic foley layers.
    Binds foley hits directly to host drum events with proportional dynamics and micro-timing.
    """

    FOLEY_PALETTE: Dict[str, OrganicFoleySample] = {
        "wood_crack": OrganicFoleySample(
            name="Wood Crack (Organic Snap)",
            category="wood_crack",
            midi_pitch=56,
            dna=TimbreDNA(brightness=0.55, roughness=0.70, inharmonicity=0.30, transient_strength=0.85),
            preferred_beats=[2.0]
        ),
        "wood_snap_dry": OrganicFoleySample(
            name="Wood Snap Dry",
            category="wood_crack",
            midi_pitch=56,
            dna=TimbreDNA(brightness=0.55, roughness=0.70, inharmonicity=0.30, transient_strength=0.85),
            preferred_beats=[2.0]
        ),

        "metal_hit": OrganicFoleySample(
            name="Metal Click (High Tail)",
            category="metal_hit",
            midi_pitch=57,
            dna=TimbreDNA(brightness=0.85, roughness=0.45, inharmonicity=0.60, transient_strength=0.75),
            preferred_beats=[4.0]
        ),
        "door_thump": OrganicFoleySample(
            name="Door Thump (Low Resonance)",
            category="door_thump",
            midi_pitch=58,
            dna=TimbreDNA(brightness=0.30, roughness=0.50, inharmonicity=0.20, transient_strength=0.90),
            preferred_beats=[1.0, 3.5]
        ),
        "cloth_rip": OrganicFoleySample(
            name="Cloth Rip (Transient Noise)",
            category="cloth_rip",
            midi_pitch=59,
            dna=TimbreDNA(brightness=0.60, roughness=0.65, inharmonicity=0.40, transient_strength=0.60),
            preferred_beats=[1.5, 3.0]
        ),
        "vocal_texture": OrganicFoleySample(
            name="Processed Vocal Grain",
            category="vocal_texture",
            midi_pitch=60,
            dna=TimbreDNA(brightness=0.68, roughness=0.30, inharmonicity=0.15, transient_strength=0.50),
            preferred_beats=[3.75, 4.0]
        )
    }

    @classmethod
    def generate_hybrid_organic_layer(
        cls,
        drum_notes: List[Any],
        parent_role: str = "snare",
        velocity_ratio: float = 0.78,
        microtiming_bias_ms: float = 1.0,
        bpm: float = 120.0,
        seed: int = 42,
        foley_sample: Optional[OrganicFoleySample] = None
    ) -> List[Any]:
        """
        Generates an organic foley companion layer where every foley hit inherits
        its musical properties (start time, velocity, duration) from the host drum.
        Accepts List[NoteEvent] or List[Dict[str, Any]].
        """
        if not drum_notes:
            return []

        rng = random.Random(seed)
        ms_per_beat = (60.0 / max(20.0, bpm)) * 1000.0
        beats_per_ms = 1.0 / ms_per_beat

        organic_notes: List[Any] = []
        is_dict_input = isinstance(drum_notes[0], dict)

        for item in drum_notes:
            if isinstance(item, dict):
                start = float(item.get("start", item.get("start_time", 0.0)))
                dur = float(item.get("duration", 0.25))
                vel = int(item.get("velocity", 90))
                chan = int(item.get("channel", 0))
                prob = float(item.get("probability", 1.0))
                acc = float(item.get("accent", 0.0))
            else:
                start = float(item.start)
                dur = float(item.duration)
                vel = int(item.velocity)
                chan = int(item.channel)
                prob = float(item.probability)
                acc = float(item.accent)

            sub_beat = round(start % 4.0, 2)

            # Select complementary foley based on beat location or override
            if foley_sample is not None:
                sample = foley_sample
            elif sub_beat in (1.0, 2.0):
                sample = cls.FOLEY_PALETTE["wood_crack"]
            elif sub_beat in (3.0, 4.0, 0.0):
                sample = cls.FOLEY_PALETTE["metal_hit"]
            elif sub_beat in (3.5, 3.75):
                sample = cls.FOLEY_PALETTE["vocal_texture"]
            else:
                sample = cls.FOLEY_PALETTE["cloth_rip"]

            # Dynamic inheritance: Foley is slightly softer than host drum, never masking it
            inherited_vel = max(15, min(120, int(vel * velocity_ratio + rng.randint(-3, 3))))

            # Micro-timing inheritance: tightly glued with subtle displacement
            offset_beats = (microtiming_bias_ms + rng.gauss(0.0, 1.2)) * beats_per_ms
            new_start = max(0.0, round(start + offset_beats, 5))
            new_dur = max(0.08, round(dur * 0.85, 4))

            if is_dict_input:
                organic_notes.append({
                    "pitch": sample.midi_pitch,
                    "pitch_class": sample.midi_pitch % 12,
                    "octave": sample.midi_pitch // 12 - 1,
                    "start": new_start,
                    "duration": new_dur,
                    "velocity": inherited_vel,
                    "channel": chan,
                    "probability": prob,
                    "accent": acc
                })
            else:
                organic_notes.append(NoteEvent(
                    pitch=sample.midi_pitch,
                    pitch_class=sample.midi_pitch % 12,
                    octave=sample.midi_pitch // 12 - 1,
                    start=new_start,
                    duration=new_dur,
                    velocity=inherited_vel,
                    channel=chan,
                    probability=prob,
                    accent=acc
                ))

        return organic_notes

    @classmethod
    def evaluate_timbre_complement(
        cls,
        drum_dna: TimbreDNA,
        foley_or_dna: Any
    ) -> float:
        """
        Calculates how well a foley sample complements a drum hit in the frequency/texture spectrum.
        Higher score (0.0 to 1.0) indicates ideal complementary balance without masking.
        """
        foley_dna = foley_or_dna.dna if hasattr(foley_or_dna, "dna") else foley_or_dna
        # Contrast in roughness and balanced brightness
        roughness_contrast = abs(drum_dna.roughness - foley_dna.roughness)
        brightness_balance = 1.0 - abs((drum_dna.brightness + foley_dna.brightness) / 2.0 - 0.65)
        complement_score = (roughness_contrast * 0.5) + (brightness_balance * 0.5)
        return round(max(0.0, min(1.0, complement_score)), 3)


# Top-level aliases for convenience
FOLEY_PALETTE = OrganicRhythmCoordinator.FOLEY_PALETTE
generate_hybrid_organic_layer = OrganicRhythmCoordinator.generate_hybrid_organic_layer
evaluate_timbre_complement = OrganicRhythmCoordinator.evaluate_timbre_complement

