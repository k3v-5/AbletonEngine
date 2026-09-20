"""
Timbre DNA Engine:
Defines multi-dimensional sound identity vectors (brightness, roughness, inharmonicity,
stereo width, transient strength, movement, pitch instability) and provides
an inter-channel timbre relationship matrix to prevent acoustic and spectral collisions.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import math


@dataclass
class TimbreDNA:
    """7-dimensional timbre representation for an instrument or sound role."""
    brightness: float = 0.50          # 0.0 (dark/sub) to 1.0 (cutting/crisp)
    roughness: float = 0.25           # 0.0 (pure sine/harmonic) to 1.0 (harsh FM/distortion)
    inharmonicity: float = 0.15       # 0.0 (strictly harmonic) to 1.0 (bell/metallic/noise)
    stereo_width: float = 0.40        # 0.0 (mono center) to 1.0 (ultra-wide Haas/sides)
    transient_strength: float = 0.60  # 0.0 (slow pad) to 1.0 (snappy percussion)
    movement: float = 0.35            # 0.0 (static) to 1.0 (intense LFO/filter modulation)
    pitch_instability: float = 0.05   # 0.0 (locked) to 1.0 (tape flutter/drift)

    def to_dict(self) -> Dict[str, float]:
        return {
            "brightness": round(self.brightness, 3),
            "roughness": round(self.roughness, 3),
            "inharmonicity": round(self.inharmonicity, 3),
            "stereo_width": round(self.stereo_width, 3),
            "transient_strength": round(self.transient_strength, 3),
            "movement": round(self.movement, 3),
            "pitch_instability": round(self.pitch_instability, 3)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimbreDNA":
        return cls(
            brightness=float(data.get("brightness", 0.5)),
            roughness=float(data.get("roughness", 0.25)),
            inharmonicity=float(data.get("inharmonicity", 0.15)),
            stereo_width=float(data.get("stereo_width", 0.4)),
            transient_strength=float(data.get("transient_strength", 0.6)),
            movement=float(data.get("movement", 0.35)),
            pitch_instability=float(data.get("pitch_instability", 0.05))
        )

    def to_synthesis_parameters(self) -> Dict[str, float]:
        """
        Translates the 7 TimbreDNA dimensions into concrete Ableton / VST synth parameters:
        WAVETABLE_POS, UNISON_DETUNE, FILTER_CUTOFF, FILTER_RESONANCE, DRIVE, AMP_ATTACK, AMP_RELEASE.
        """
        # Brightness -> Filter Cutoff & Wavetable Pos
        filter_cutoff = max(0.15, min(0.98, self.brightness * 0.90 + 0.05))
        wavetable_pos = max(0.0, min(1.0, self.brightness * 0.60 + self.inharmonicity * 0.40))
        
        # Roughness -> Drive & Filter Resonance
        drive = max(0.0, min(0.90, self.roughness * 0.70))
        resonance = max(0.05, min(0.85, 0.15 + self.roughness * 0.40))
        
        # Stereo Width -> Unison Detune
        unison_detune = max(0.0, min(0.95, self.stereo_width * 0.75))
        
        # Transient Strength -> Amp Attack
        amp_attack = max(0.001, min(0.80, (1.0 - self.transient_strength) * 0.40))
        
        # Movement & Instability -> Amp Release
        amp_release = max(0.05, min(0.90, 0.15 + self.movement * 0.35 + (1.0 - self.transient_strength) * 0.30))

        return {
            "FILTER_CUTOFF": round(filter_cutoff, 3),
            "FILTER_RESONANCE": round(resonance, 3),
            "DRIVE": round(drive, 3),
            "WAVETABLE_POS": round(wavetable_pos, 3),
            "UNISON_DETUNE": round(unison_detune, 3),
            "AMP_ATTACK": round(amp_attack, 3),
            "AMP_RELEASE": round(amp_release, 3)
        }


class TimbreRelationshipMatrix:
    """
    Evaluates timbre collisions across tracks and calculates complementary profiles.
    """

    ROLE_DEFAULTS: Dict[str, TimbreDNA] = {
        "KICK": TimbreDNA(brightness=0.35, roughness=0.20, inharmonicity=0.10, stereo_width=0.0, transient_strength=0.95, movement=0.05, pitch_instability=0.0),
        "SUB": TimbreDNA(brightness=0.15, roughness=0.10, inharmonicity=0.02, stereo_width=0.0, transient_strength=0.70, movement=0.10, pitch_instability=0.0),
        "BASS": TimbreDNA(brightness=0.30, roughness=0.35, inharmonicity=0.05, stereo_width=0.0, transient_strength=0.75, movement=0.20, pitch_instability=0.02),
        "SNARE": TimbreDNA(brightness=0.65, roughness=0.45, inharmonicity=0.40, stereo_width=0.15, transient_strength=0.92, movement=0.10, pitch_instability=0.0),
        "HI_HATS": TimbreDNA(brightness=0.85, roughness=0.30, inharmonicity=0.60, stereo_width=0.45, transient_strength=0.90, movement=0.25, pitch_instability=0.0),
        "KEYS": TimbreDNA(brightness=0.55, roughness=0.20, inharmonicity=0.15, stereo_width=0.60, transient_strength=0.65, movement=0.40, pitch_instability=0.05),
        "PAD": TimbreDNA(brightness=0.40, roughness=0.15, inharmonicity=0.10, stereo_width=0.85, transient_strength=0.15, movement=0.70, pitch_instability=0.12),
        "LEAD": TimbreDNA(brightness=0.75, roughness=0.45, inharmonicity=0.20, stereo_width=0.50, transient_strength=0.75, movement=0.60, pitch_instability=0.10),
        "COUNTER_LEAD": TimbreDNA(brightness=0.60, roughness=0.30, inharmonicity=0.15, stereo_width=0.65, transient_strength=0.60, movement=0.75, pitch_instability=0.08),
        "EAR_CANDY": TimbreDNA(brightness=0.85, roughness=0.40, inharmonicity=0.50, stereo_width=0.80, transient_strength=0.85, movement=0.80, pitch_instability=0.20),
        "TEXTURE_FOLEY": TimbreDNA(brightness=0.30, roughness=0.70, inharmonicity=0.80, stereo_width=0.90, transient_strength=0.20, movement=0.85, pitch_instability=0.30),
        "DRUMS": TimbreDNA(brightness=0.60, roughness=0.40, inharmonicity=0.40, stereo_width=0.50, transient_strength=0.90, movement=0.10, pitch_instability=0.0),
        "VOCALS": TimbreDNA(brightness=0.70, roughness=0.25, inharmonicity=0.10, stereo_width=0.20, transient_strength=0.65, movement=0.50, pitch_instability=0.05),
    }

    @classmethod
    def get_default_for_role(cls, role: str) -> TimbreDNA:
        """Returns the canonical TimbreDNA baseline for a given acoustic role."""
        r_clean = str(role or "").upper().replace(" ", "_")
        if r_clean in cls.ROLE_DEFAULTS:
            return cls.ROLE_DEFAULTS[r_clean]
        for k, v in cls.ROLE_DEFAULTS.items():
            if k in r_clean or r_clean in k:
                return v
        return TimbreDNA()

    @classmethod
    def evaluate_collision(
        cls,
        role_a: str,
        dna_a: TimbreDNA,
        role_b: str,
        dna_b: TimbreDNA
    ) -> Dict[str, Any]:
        """
        Audits potential timbre collisions between two tracks.
        Collisions occur when two tracks occupying similar registers share
        excessive brightness, roughness, and width without frequency pocketing.
        """
        # Distance calculation across dimensions
        brightness_diff = abs(dna_a.brightness - dna_b.brightness)
        width_diff = abs(dna_a.stereo_width - dna_b.stereo_width)
        transient_diff = abs(dna_a.transient_strength - dna_b.transient_strength)

        collision_risk = False
        reasons: List[str] = []

        # High brightness + High stereo width overlap
        if dna_a.brightness > 0.65 and dna_b.brightness > 0.65 and brightness_diff < 0.15:
            if dna_a.stereo_width > 0.50 and dna_b.stereo_width > 0.50:
                collision_risk = True
                reasons.append(
                    f"Colisión de brillo y amplitud estéreo entre {role_a} y {role_b} (ambos > 0.65 brillo y > 0.50 width)."
                )

        # Transient competition in low-end
        if role_a in ("KICK", "BASS", "SUB") and role_b in ("KICK", "BASS", "SUB"):
            if dna_a.transient_strength > 0.70 and dna_b.transient_strength > 0.70:
                collision_risk = True
                reasons.append(
                    f"Conflicto de pegada transiente en graves entre {role_a} y {role_b}."
                )

        return {
            "collision_detected": collision_risk,
            "roles": [role_a, role_b],
            "brightness_diff": round(brightness_diff, 2),
            "width_diff": round(width_diff, 2),
            "transient_diff": round(transient_diff, 2),
            "reasons": reasons
        }
