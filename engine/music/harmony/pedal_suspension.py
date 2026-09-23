# engine/music/harmony/pedal_suspension.py
"""
Pedal Point & Suspension Weaver Engine:
Generates intense harmonic tension in build-ups, pre-choruses, and cinematic bridges
by anchoring a persistent pedal bass tone (tonic or dominant) while modulating upper
harmonies with suspended chord voicings (sus2, sus4, add9).
"""

from typing import Dict, Any, List, Optional, Union
import copy
import logging

logger = logging.getLogger("PedalPointSuspensionWeaver")


class PedalPointSuspensionWeaver:
    """
    Weaves harmonic pedal points and suspension tensions into musical sections.
    """

    NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    @classmethod
    def pitch_to_name(cls, pitch: int) -> str:
        """Converts MIDI pitch to note name with octave."""
        octave = (pitch // 12) - 1
        name = cls.NOTE_NAMES[pitch % 12]
        return f"{name}{octave}"

    @classmethod
    def name_to_pitch(cls, name: str, default_octave: int = 1) -> int:
        """Converts note name (e.g. 'C', 'G#2') to MIDI pitch."""
        clean = name.strip().upper()
        octave = default_octave
        pitch_name = clean
        if clean and clean[-1].isdigit():
            octave = int(clean[-1])
            pitch_name = clean[:-1]

        if pitch_name in cls.NOTE_NAMES:
            pc = cls.NOTE_NAMES.index(pitch_name)
            return (octave + 1) * 12 + pc
        return (default_octave + 1) * 12  # Fallback to C

    @classmethod
    def weave_pedal_point_progression(
        cls,
        chords_or_notes: List[Any],
        pedal_pitch: Union[int, str] = 36,  # C2
        section_name: str = "pre_chorus",
        suspension_type: str = "AUTO",
        pulse_subdivision: str = "1/4",  # "HOLD", "1/4", "1/8"
        total_duration_beats: float = 16.0
    ) -> Dict[str, Any]:
        """
        Transforms input chords or notes by anchoring the bass to a pedal point and weaving
        suspensions (sus2, sus4, add9) in the harmonic layer.
        """
        # Resolve pedal pitch
        if isinstance(pedal_pitch, str):
            pedal_midi = cls.name_to_pitch(pedal_pitch, default_octave=1)
        else:
            pedal_midi = int(pedal_pitch)

        pedal_name = cls.pitch_to_name(pedal_midi)
        suspensions_count = 0
        pedal_notes: List[Dict[str, Any]] = []
        transformed_notes: List[Dict[str, Any]] = []
        transformed_chords: List[Dict[str, Any]] = []

        # Determine section duration
        duration = total_duration_beats
        if chords_or_notes:
            # Check if input is notes
            first = chords_or_notes[0]
            if isinstance(first, dict) and ("start_time" in first or "start" in first):
                last = max(chords_or_notes, key=lambda n: float(n.get("start_time", n.get("start", 0.0))))
                duration = float(last.get("start_time", last.get("start", 0.0))) + float(last.get("duration", 4.0))

        # 1. Generate Pedal Bass Line
        pulse_map = {
            "HOLD": duration,
            "1/2": 2.0,
            "1/4": 1.0,
            "1/8": 0.5
        }
        step_len = pulse_map.get(pulse_subdivision, 1.0)
        curr_beat = 0.0
        while curr_beat < duration:
            # Add subtle driving groove velocity dynamics
            beat_pos = curr_beat % 4.0
            vel = 105 if beat_pos == 0.0 else (95 if beat_pos == 2.0 else 88)
            pedal_notes.append({
                "pitch": pedal_midi,
                "start_time": round(curr_beat, 3),
                "duration": round(step_len * 0.95, 3),
                "velocity": vel,
                "role": "PEDAL_BASS",
                "pedal": True
            })
            curr_beat += step_len

        # 2. Process and Weave Suspensions into Chords / Notes
        if not chords_or_notes:
            # Generate default 4-bar pre-chorus progression if empty
            default_chords = [
                {"root": "F", "quality": "major", "duration": 4.0},
                {"root": "G", "quality": "major", "duration": 4.0},
                {"root": "Am", "quality": "minor", "duration": 4.0},
                {"root": "G", "quality": "sus4", "duration": 4.0}
            ]
            chords_or_notes = default_chords

        for idx, item in enumerate(chords_or_notes):
            if isinstance(item, dict):
                # Is it a chord dict?
                if "root" in item or "quality" in item:
                    chord_copy = copy.deepcopy(item)
                    root = chord_copy.get("root", "C")
                    qual = chord_copy.get("quality", "major")
                    exts = chord_copy.get("extensions", [])

                    # Apply suspension on bars 2 and 4 (idx 1 and 3)
                    if suspension_type in ["SUS4", "AUTO"] and idx % 2 == 1:
                        chord_copy["original_quality"] = qual
                        chord_copy["quality"] = "sus4"
                        chord_copy["pedal_bass"] = pedal_name
                        suspensions_count += 1
                    elif suspension_type == "SUS2":
                        chord_copy["quality"] = "sus2"
                        chord_copy["pedal_bass"] = pedal_name
                        suspensions_count += 1
                    else:
                        chord_copy["pedal_bass"] = pedal_name

                    transformed_chords.append(chord_copy)

                # Or is it a note dict?
                elif "pitch" in item:
                    n_copy = copy.deepcopy(item)
                    p = int(n_copy.get("pitch", 60))
                    # If it's a bass note (< 48), lock it to pedal pitch
                    if p < 48:
                        n_copy["pitch"] = pedal_midi
                        n_copy["role"] = "PEDAL_BASS"
                    else:
                        # Upper voice: check if note creates a suspension
                        # E.g. if suspension requested, nudge 3rds up 1 semitone to 4th
                        rel_pc = (p - pedal_midi) % 12
                        if suspension_type in ["SUS4", "AUTO"] and rel_pc in [3, 4] and (idx % 3 == 0):
                            n_copy["pitch"] = p + (2 if rel_pc == 3 else 1)  # Nudge to 4th (interval 5)
                            n_copy["suspended"] = True
                            suspensions_count += 1

                    transformed_notes.append(n_copy)

        return {
            "status": "APPLIED",
            "section": section_name,
            "pedal_pitch": pedal_midi,
            "pedal_name": pedal_name,
            "pulse_subdivision": pulse_subdivision,
            "total_duration_beats": duration,
            "suspensions_count": suspensions_count,
            "harmonic_tension_score": round(min(0.95, 0.65 + (suspensions_count * 0.08)), 2),
            "pedal_notes": pedal_notes,
            "transformed_chords": transformed_chords,
            "transformed_notes": transformed_notes
        }

    @classmethod
    def render_markdown_summary(cls, result: Dict[str, Any]) -> str:
        """Renders clear, human-readable markdown summary."""
        lines = [
            "🎼 **Tensión Armónica por Notas Pedal y Suspensiones (Pedal Point Weaver)**\n",
            f"• **Sección Aplicada:** `{result.get('section', 'pre_chorus').upper()}`",
            f"• **Nota Pedal Ancla:** `{result.get('pedal_name', 'C1')}` (MIDI: {result.get('pedal_pitch', 36)})",
            f"• **Subdivisión de Pulso Pedal:** `{result.get('pulse_subdivision', '1/4')}` ({len(result.get('pedal_notes', []))} notas drone/pulse)",
            f"• **Suspensiones Aplicadas:** {result.get('suspensions_count', 0)} acordes/voces alteradas (sus2/sus4)",
            f"• **Índice de Tensión Armónica:** {int(result.get('harmonic_tension_score', 0.8) * 100)}% de acumulación de energía\n",
            "• **Efecto Psicoacústico:** Retiene la resolución tonal con un bajo monolítico mientras las voces superiores flotan en suspensión, detonando una catarsis masiva en el drop."
        ]
        return "\n".join(lines)
