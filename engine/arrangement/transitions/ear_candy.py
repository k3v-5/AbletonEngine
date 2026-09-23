# engine/arrangement/transitions/ear_candy.py
"""
Smart Ear Candy & Micro-Transitional Texture Injector:
Generates non-repetitive organic micro-textures and transitional ear candy across the arrangement:
- Reverse reverb splashes/swells
- Vinyl crackle / analog tape flutter
- Foley percussive taps & wooden clicks
- Pitch-drop tape stops (-12 st)
- Metallic rimshot snaps
- Ambient vocal chop formant stabs

STRICT ACOUSTIC RULE:
Strict peripheral panning (+/-35% to +/-65% L/R), keeping the central acoustic corridor (Pan 0.0)
completely transparent for Lead Vocal, Kick, and Sub-Bass.
Governed by 5 distinct density levels.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import random
import logging

from engine.music.models import NoteEvent

logger = logging.getLogger("SmartEarCandyEngine")


class EarCandyGestureType(str, Enum):
    REVERSE_REVERB_THROW = "REVERSE_REVERB_THROW"  # Reverse swell on beat 4 before section boundary
    VINYL_CRACKLE_SPUTTER = "VINYL_CRACKLE_SPUTTER" # Analog vinyl dust / tape flutter for 1-2 beats
    FOLEY_ORGANIC_CLICK = "FOLEY_ORGANIC_CLICK"     # Organic wood/metal clicks on syncopated offbeats
    TAPE_STOP_PITCH_DROP = "TAPE_STOP_PITCH_DROP"   # Brief 1/4-beat pitch descent (-12 st)
    METALLIC_RIM_SNAP = "METALLIC_RIM_SNAP"         # Sharp metallic transient snap on beat 1 turnaround
    CHORD_VOX_STAB = "CHORD_VOX_STAB"               # Ambient formant vocal stab in background


@dataclass
class EarCandyEvent:
    """A discrete micro-transitional gesture placed on the timeline."""
    gesture_type: EarCandyGestureType
    start_beat: float
    duration_beats: float
    pan: float                                     # -0.65 to -0.35 (Left) or +0.35 to +0.65 (Right), never 0.0
    velocity: int                                  # Subtle dynamic range (35 to 85)
    target_role: str = "EAR_CANDY"
    description: str = ""
    pitch: Optional[int] = None                    # MIDI pitch if tonal

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gesture_type": self.gesture_type.value,
            "start_beat": round(self.start_beat, 3),
            "duration_beats": round(self.duration_beats, 3),
            "pan": round(self.pan, 2),
            "pan_display": f"{int(abs(self.pan) * 100)}{'L' if self.pan < 0 else 'R'}",
            "velocity": self.velocity,
            "target_role": self.target_role,
            "description": self.description,
            "pitch": self.pitch
        }


class SmartEarCandyEngine:
    """Generates and schedules organic ear candy textures across the song arrangement."""

    # 5 discrete density scalers
    DENSITY_CONFIG: Dict[int, Dict[str, Any]] = {
        1: {
            "name": "Minimalista",
            "interval_bars": 16,     # Only at major section transitions
            "gestures_per_event": 1,
            "max_volume_db": -16.0,
            "description": "Texturas mínimas exclusivas en transiciones mayores de 16 compases."
        },
        2: {
            "name": "Comercial Estándar",
            "interval_bars": 8,      # Classic pop turnaround every 8 bars
            "gestures_per_event": 1,
            "max_volume_db": -14.0,
            "description": "Detalles sutiles cada 8 compases en los turnarounds de frase."
        },
        3: {
            "name": "Dinámico Pop / Urbano",
            "interval_bars": 4,      # Every 4 to 8 bars alternating
            "gestures_per_event": 1,
            "max_volume_db": -12.0,
            "description": "Gestos dinámicos alternados cada 4-8 compases para máxima frescura auditiva."
        },
        4: {
            "name": "Hiper-Detallado",
            "interval_bars": 4,
            "gestures_per_event": 2, # Layered micro-events (e.g. foley + reverse swell)
            "max_volume_db": -10.0,
            "description": "Capas combinadas de foley, tape stop y swells cada 4 compases."
        },
        5: {
            "name": "Glitch / Complextro",
            "interval_bars": 2,      # Frequent micro-gestures
            "gestures_per_event": 2,
            "max_volume_db": -9.0,
            "description": "Alta densidad de micro-eventos texturales y rítmicos para electrónica compleja."
        }
    }

    @classmethod
    def calculate_peripheral_pan(cls, rng: random.Random, last_pan: Optional[float] = None) -> float:
        """
        Calculates a strictly peripheral stereo pan position (+/-0.35 to +/-0.65).
        Guarantees that Pan = 0.0 (center) is NEVER used.
        Alternates sides if last_pan is provided.
        """
        if last_pan is not None and last_pan < 0:
            # Shift to right pocket
            side = 1.0
        elif last_pan is not None and last_pan > 0:
            # Shift to left pocket
            side = -1.0
        else:
            side = 1.0 if rng.random() > 0.5 else -1.0

        magnitude = rng.uniform(0.35, 0.65)
        return round(side * magnitude, 2)

    @classmethod
    def generate_ear_candy_package(
        cls,
        sections: List[Dict[str, Any]],
        total_bars: int = 64,
        density_level: int = 2,
        seed: Optional[int] = 42
    ) -> List[EarCandyEvent]:
        """
        Generates a non-repetitive timeline schedule of ear candy gestures.
        Aligns strategically with section boundaries and phrase turnarounds.
        """
        clamped_level = max(1, min(5, int(density_level)))
        config = cls.DENSITY_CONFIG.get(clamped_level, cls.DENSITY_CONFIG[2])
        interval_bars = config["interval_bars"]

        rng = random.Random(seed)
        events: List[EarCandyEvent] = []
        last_pan = None

        # Build list of turnaround bars
        turnaround_bars: List[float] = []
        cur_bar = 1.0
        for sec in sections:
            sec_bars = sec.get("bars", 8)
            # Add section end turnaround
            sec_end_bar = cur_bar + sec_bars
            turnaround_bars.append(sec_end_bar)
            cur_bar += sec_bars

        # Also add grid intervals based on density level
        bar_step = interval_bars
        grid_bars = [b for b in range(bar_step, total_bars + 1, bar_step)]
        all_trigger_bars = sorted(list(set(turnaround_bars + grid_bars)))

        available_gestures = list(EarCandyGestureType)

        for t_bar in all_trigger_bars:
            if t_bar > total_bars:
                continue

            target_beat = (t_bar - 1.0) * 4.0
            n_gestures = config["gestures_per_event"]

            # Sample non-repeating gesture types
            selected_gestures = rng.sample(available_gestures, min(n_gestures, len(available_gestures)))

            for g_type in selected_gestures:
                pan_val = cls.calculate_peripheral_pan(rng, last_pan=last_pan)
                last_pan = pan_val

                if g_type == EarCandyGestureType.REVERSE_REVERB_THROW:
                    # Occurs on final beat before bar arrival (e.g. beat 3.0 to 4.0)
                    start_b = max(0.0, target_beat - 1.0)
                    dur_b = 1.0
                    vel = rng.randint(55, 75)
                    desc = f"Reverse reverb swell previo al compás {int(t_bar)} ({vel} vel, Pan {pan_val})."
                    pitch = None

                elif g_type == EarCandyGestureType.VINYL_CRACKLE_SPUTTER:
                    # 2-beat atmospheric crackle
                    start_b = max(0.0, target_beat - 2.0)
                    dur_b = 2.0
                    vel = rng.randint(40, 60)
                    desc = f"Textura de vinilo / flutter analógico previo al compás {int(t_bar)}."
                    pitch = None

                elif g_type == EarCandyGestureType.FOLEY_ORGANIC_CLICK:
                    # Offbeat click on beat 3.5
                    start_b = max(0.0, target_beat - 0.5)
                    dur_b = 0.25
                    vel = rng.randint(60, 85)
                    desc = f"Click orgánico de madera/foley en contratiempo (compás {int(t_bar)})."
                    pitch = 60

                elif g_type == EarCandyGestureType.TAPE_STOP_PITCH_DROP:
                    # 1/2 beat tape stop
                    start_b = max(0.0, target_beat - 0.75)
                    dur_b = 0.75
                    vel = rng.randint(65, 85)
                    desc = f"Tape stop micro-descendente (-12 st) cerrando frase en compás {int(t_bar)}."
                    pitch = 65

                elif g_type == EarCandyGestureType.METALLIC_RIM_SNAP:
                    # Sharp snap on beat 1
                    start_b = target_beat
                    dur_b = 0.50
                    vel = rng.randint(70, 90)
                    desc = f"Snap metálico percusivo acentuando llegada al compás {int(t_bar)}."
                    pitch = 37

                else: # CHORD_VOX_STAB
                    start_b = max(0.0, target_beat - 1.5)
                    dur_b = 1.0
                    vel = rng.randint(50, 70)
                    desc = f"Stab vocal con formante ambiental en compás {int(t_bar)}."
                    pitch = 72

                events.append(EarCandyEvent(
                    gesture_type=g_type,
                    start_beat=round(start_b, 3),
                    duration_beats=dur_b,
                    pan=pan_val,
                    velocity=vel,
                    target_role="EAR_CANDY",
                    description=desc,
                    pitch=pitch
                ))

        return sorted(events, key=lambda e: e.start_beat)

    @classmethod
    def render_markdown_summary(cls, events: List[EarCandyEvent], density_level: int = 2) -> str:
        """Formats ear candy placement schedule into a clear Markdown summary table."""
        config = cls.DENSITY_CONFIG.get(density_level, cls.DENSITY_CONFIG[2])
        lines = [
            f"### 🍬 Inyector de Ear Candy y Micro-Transiciones Orgánicas (`SmartEarCandyEngine`)",
            f"- **Nivel de Densidad:** **{density_level}/5 ({config['name']})**",
            f"- **Descripción:** {config['description']}",
            f"- **Total Micro-Eventos Programados:** `{len(events)}` gestos\n",
            "| Compás Aprox. | Tiempo (Beats) | Tipo de Gesto | Paneo Estéreo | Velocidad | Función en el Arreglo |",
            "| :---: | :---: | :--- | :---: | :---: | :--- |"
        ]

        for e in events[:12]: # Show first 12 for compact readability
            bar_approx = int(e.start_beat / 4.0) + 1
            lines.append(
                f"| Compás {bar_approx} | {e.start_beat:.2f} | `{e.gesture_type.value}` | `{e.pan:+.2f}` ({'L' if e.pan < 0 else 'R'}) | {e.velocity} | {e.description} |"
            )

        if len(events) > 12:
            lines.append(f"| ... | ... | *({len(events) - 12} eventos adicionales programados en la línea de tiempo)* | ... | ... | ... |")

        lines.append("\n🔒 *Regla Acústica: El canal central (Pan 0.0) se mantiene completamente libre para Lead Vocal, Kick y 808.*")
        return "\n".join(lines)
