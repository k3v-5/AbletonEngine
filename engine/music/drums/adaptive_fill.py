# engine/music/drums/adaptive_fill.py
"""
Adaptive Drum Fill Generator:
Generates high-fidelity, organic, and non-repetitive drum fills and turnarounds.
Structured across 4 frequency layers:
1. Low-End Melodic Movement: Tuned toms (Floor -> Mid -> High) with velocity crescendos.
2. Mid Snap & Flams: Snare flams, ghost-note buzzes, and syncopated rolls (1/16T, 1/32).
3. High Splash & Accents: Hi-hat chokes, splash cymbals, and reverse crash tails.
4. Kick Dropout: Silences the kick on beats 3-4 to clear the acoustic space for the fill.
"""

from typing import Dict, Any, List, Optional, Tuple
import math
import random
import logging

logger = logging.getLogger("AdaptiveDrumFillGenerator")


class AdaptiveDrumFillGenerator:
    """
    High-fidelity drum fill generator adapted to genre, tempo, and turnaround bars.
    """

    # General MIDI standard drum pitches
    PAD_KICK = 36
    PAD_RIM = 37
    PAD_SNARE = 38
    PAD_CLAP = 39
    PAD_SNARE_ELEC = 40
    PAD_FLOOR_TOM_LOW = 41
    PAD_CLOSED_HAT = 42
    PAD_FLOOR_TOM_HIGH = 43
    PAD_PEDAL_HAT = 44
    PAD_LOW_MID_TOM = 45
    PAD_OPEN_HAT = 46
    PAD_MID_HIGH_TOM = 47
    PAD_HIGH_TOM = 48
    PAD_CRASH_1 = 49
    PAD_RIDE_1 = 51
    PAD_SPLASH = 55

    @classmethod
    def generate_turnaround_fill(
        cls,
        section_length_beats: float,
        fill_duration_beats: float = 4.0,  # Typically 1 full bar (4 beats) or half bar (2 beats)
        genre: str = "POP",
        intensity_level: int = 3,
        bpm: float = 120.0
    ) -> Dict[str, Any]:
        """
        Generates a premium drum fill placed right at the end of the section:
        start_beat = section_length_beats - fill_duration_beats.
        """
        start_beat = max(0.0, section_length_beats - fill_duration_beats)
        g_up = str(genre or "POP").upper()

        notes: List[Dict[str, Any]] = []

        if fill_duration_beats <= 2.0:
            # Half-bar fill (beats 3.0 and 4.0)
            # Beat 3: Snare flam + Tom hit
            notes.append({"pitch": cls.PAD_SNARE, "start_time": round(start_beat + 0.0, 3), "duration": 0.25, "velocity": 90})
            notes.append({"pitch": cls.PAD_LOW_MID_TOM, "start_time": round(start_beat + 0.5, 3), "duration": 0.25, "velocity": 95})
            notes.append({"pitch": cls.PAD_HIGH_TOM, "start_time": round(start_beat + 0.75, 3), "duration": 0.25, "velocity": 105})
            # Beat 4: Triplet roll / flam into crash
            notes.append({"pitch": cls.PAD_SNARE, "start_time": round(start_beat + 1.0, 3), "duration": 0.15, "velocity": 110})
            notes.append({"pitch": cls.PAD_SNARE, "start_time": round(start_beat + 1.25, 3), "duration": 0.15, "velocity": 115})
            notes.append({"pitch": cls.PAD_FLOOR_TOM_LOW, "start_time": round(start_beat + 1.5, 3), "duration": 0.20, "velocity": 120})
            notes.append({"pitch": cls.PAD_HIGH_TOM, "start_time": round(start_beat + 1.75, 3), "duration": 0.20, "velocity": 125})
            notes.append({"pitch": cls.PAD_CRASH_1, "start_time": round(start_beat + 1.95, 3), "duration": 0.5, "velocity": 115})

        else:
            # Full 1-bar fill (4.0 beats)
            if "TRAP" in g_up or "DRILL" in g_up or "URBANO" in g_up:
                # Trap / Drill Style: Fast snare rolls, pitch stutter hats and rim accents
                # Beat 1: Syncopated rim & open hat choke
                notes.append({"pitch": cls.PAD_RIM, "start_time": round(start_beat + 0.0, 3), "duration": 0.25, "velocity": 85})
                notes.append({"pitch": cls.PAD_OPEN_HAT, "start_time": round(start_beat + 0.5, 3), "duration": 0.20, "velocity": 90})
                notes.append({"pitch": cls.PAD_PEDAL_HAT, "start_time": round(start_beat + 0.75, 3), "duration": 0.10, "velocity": 100})
                # Beat 2: Snare accent + ghost roll
                notes.append({"pitch": cls.PAD_SNARE, "start_time": round(start_beat + 1.0, 3), "duration": 0.25, "velocity": 100})
                notes.append({"pitch": cls.PAD_SNARE, "start_time": round(start_beat + 1.33, 3), "duration": 0.15, "velocity": 75})
                notes.append({"pitch": cls.PAD_SNARE, "start_time": round(start_beat + 1.66, 3), "duration": 0.15, "velocity": 85})
                # Beat 3: 1/32 roll crescendo on snare
                for i in range(8):
                    t = start_beat + 2.0 + (i * 0.125)
                    v = int(70 + (i * 6))
                    notes.append({"pitch": cls.PAD_SNARE, "start_time": round(t, 3), "duration": 0.10, "velocity": v})
                # Beat 4: High tom to floor tom drop + splash
                notes.append({"pitch": cls.PAD_HIGH_TOM, "start_time": round(start_beat + 3.0, 3), "duration": 0.25, "velocity": 115})
                notes.append({"pitch": cls.PAD_MID_HIGH_TOM, "start_time": round(start_beat + 3.25, 3), "duration": 0.25, "velocity": 118})
                notes.append({"pitch": cls.PAD_FLOOR_TOM_LOW, "start_time": round(start_beat + 3.5, 3), "duration": 0.25, "velocity": 124})
                notes.append({"pitch": cls.PAD_SPLASH, "start_time": round(start_beat + 3.75, 3), "duration": 0.5, "velocity": 120})

            elif "SYNTHWAVE" in g_up or "ROCK" in g_up:
                # Big Phil Collins / 80s Gated Tom Cascade
                # Beat 1-2: Snare hits with ghost flams
                notes.append({"pitch": cls.PAD_SNARE, "start_time": round(start_beat + 0.0, 3), "duration": 0.3, "velocity": 105})
                notes.append({"pitch": cls.PAD_SNARE, "start_time": round(start_beat + 0.5, 3), "duration": 0.2, "velocity": 90})
                notes.append({"pitch": cls.PAD_SNARE, "start_time": round(start_beat + 1.0, 3), "duration": 0.3, "velocity": 110})
                # Beat 2.5 to 4.0: High Tom -> Mid Tom -> Low Tom -> Floor Tom cascade
                toms = [cls.PAD_HIGH_TOM, cls.PAD_MID_HIGH_TOM, cls.PAD_LOW_MID_TOM, cls.PAD_FLOOR_TOM_HIGH, cls.PAD_FLOOR_TOM_LOW]
                step = 2.0 / len(toms)
                for idx, tom_p in enumerate(toms):
                    t = start_beat + 1.5 + (idx * step)
                    notes.append({"pitch": tom_p, "start_time": round(t, 3), "duration": round(step * 0.9, 3), "velocity": int(95 + idx * 6)})
                # Crash accent at end
                notes.append({"pitch": cls.PAD_CRASH_1, "start_time": round(start_beat + 3.75, 3), "duration": 0.5, "velocity": 125})

            else:
                # Modern Pop / House / Electronic: Hybrid tom & syncopated snare fill
                # Beat 1: Snare hit + Floor Tom
                notes.append({"pitch": cls.PAD_SNARE, "start_time": round(start_beat + 0.0, 3), "duration": 0.25, "velocity": 95})
                notes.append({"pitch": cls.PAD_FLOOR_TOM_LOW, "start_time": round(start_beat + 0.25, 3), "duration": 0.25, "velocity": 90})
                # Beat 2: Low-mid tom pair
                notes.append({"pitch": cls.PAD_LOW_MID_TOM, "start_time": round(start_beat + 1.0, 3), "duration": 0.25, "velocity": 100})
                notes.append({"pitch": cls.PAD_LOW_MID_TOM, "start_time": round(start_beat + 1.25, 3), "duration": 0.25, "velocity": 102})
                # Beat 3: High tom + Snare flam
                notes.append({"pitch": cls.PAD_HIGH_TOM, "start_time": round(start_beat + 2.0, 3), "duration": 0.25, "velocity": 108})
                notes.append({"pitch": cls.PAD_SNARE, "start_time": round(start_beat + 2.5, 3), "duration": 0.20, "velocity": 112})
                # Beat 4: Rápido redoble sextillo final
                for i in range(4):
                    t = start_beat + 3.0 + (i * 0.25)
                    p = cls.PAD_SNARE if i % 2 == 0 else cls.PAD_HIGH_TOM
                    notes.append({"pitch": p, "start_time": round(t, 3), "duration": 0.20, "velocity": int(105 + i * 5)})
                notes.append({"pitch": cls.PAD_CRASH_1, "start_time": round(start_beat + 3.9, 3), "duration": 0.5, "velocity": 120})

        # Filter out Kick from fill duration to enforce Kick Dropout
        kick_dropout_window = (start_beat, section_length_beats)

        return {
            "status": "FILL_GENERATED",
            "start_beat": start_beat,
            "duration_beats": fill_duration_beats,
            "fill_notes": notes,
            "note_count": len(notes),
            "kick_dropout_window": kick_dropout_window,
            "style_applied": g_up
        }
