# engine/vocal/spectral_chop_harmonizer.py
"""
Spectral Vocal Chop Harmonizer:
Intelligent pitch estimation, scale-snapping, harmonic transposition,
and rhythmic arrangement of vocal slices conformed to song key and frequency.

Provides:
- f0 Fundamental Frequency Estimation (autocorrelation in human vocal range 80Hz-900Hz)
- Musical Scale Snapping (Tonic, Minor/Major 3rd, 5th, Octave Up/Down)
- Section-Specific Chop Arrangement (Buildup Stutters, Drop Melodic Pockets, Ambient Washes)
- Ableton Live Clip Pitch & Warping Integration
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import logging

logger = logging.getLogger("SpectralChopHarmonizer")

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

SCALE_INTERVALS = {
    "minor": [0, 2, 3, 5, 7, 8, 10],       # Natural minor (Aeolian)
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "major": [0, 2, 4, 5, 7, 9, 11],       # Major (Ionian)
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "pentatonic_minor": [0, 3, 5, 7, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
}


class SpectralChopHarmonizer:
    """Harmonic and spectral intelligence engine for professional vocal chops."""

    @staticmethod
    def hz_to_midi(f0_hz: float) -> float:
        """Converts frequency in Hertz to continuous MIDI note number."""
        if f0_hz <= 0:
            return 60.0
        return 69.0 + 12.0 * np.log2(f0_hz / 440.0)

    @staticmethod
    def midi_to_note_name(midi_pitch: float) -> str:
        """Converts continuous or integer MIDI note number to note name string (e.g. F3, Ab4)."""
        rounded = int(round(midi_pitch))
        name = NOTE_NAMES[rounded % 12]
        octave = (rounded // 12) - 1
        return f"{name}{octave}"

    @classmethod
    def estimate_fundamental_pitch(
        cls,
        audio_data: np.ndarray,
        sr: int = 44100,
        min_hz: float = 80.0,
        max_hz: float = 900.0
    ) -> Dict[str, Any]:
        """
        Estimates the dominant fundamental frequency (f0) of a vocal slice using normalized autocorrelation.
        Restricted to standard human singing pitch ranges (80Hz to 900Hz, E2 to A5).
        """
        if audio_data is None or len(audio_data) < 100:
            return {
                "f0_hz": 174.61,  # Default F3
                "midi_pitch": 53.0,
                "note_name": "F3",
                "confidence": 0.0,
                "is_voiced": False
            }

        # Convert to float mono
        if audio_data.ndim > 1:
            signal = np.mean(audio_data, axis=1)
        else:
            signal = audio_data.astype(np.float32)

        # Remove DC offset
        signal = signal - np.mean(signal)

        # Check for near silence
        rms = np.sqrt(np.mean(signal ** 2))
        if rms < 1e-4:
            return {
                "f0_hz": 174.61,
                "midi_pitch": 53.0,
                "note_name": "F3",
                "confidence": 0.0,
                "is_voiced": False
            }

        # Focus analysis window on the sustained middle portion (avoid attack transient & release tail)
        n = len(signal)
        w_start = int(n * 0.15)
        w_end = int(n * 0.85)
        if w_end - w_start > 512:
            chunk = signal[w_start:w_end]
        else:
            chunk = signal

        # Apply Hanning window
        windowed = chunk * np.hanning(len(chunk))

        # Normalized autocorrelation via FFT
        n_fft = 1 << (len(windowed) * 2 - 1).bit_length()
        fx = np.fft.rfft(windowed, n=n_fft)
        autocorr = np.fft.irfft(fx * np.conj(fx))[:len(windowed)]

        if autocorr[0] <= 0:
            return {
                "f0_hz": 174.61,
                "midi_pitch": 53.0,
                "note_name": "F3",
                "confidence": 0.0,
                "is_voiced": False
            }

        autocorr = autocorr / autocorr[0]

        # Determine lag indices matching search frequency bounds
        min_lag = max(1, int(sr / max_hz))
        max_lag = min(len(autocorr) - 1, int(sr / min_hz))

        if min_lag >= max_lag:
            return {
                "f0_hz": 174.61,
                "midi_pitch": 53.0,
                "note_name": "F3",
                "confidence": 0.0,
                "is_voiced": False
            }

        search_region = autocorr[min_lag:max_lag]
        best_peak_idx = np.argmax(search_region)
        best_lag = min_lag + best_peak_idx
        confidence = float(autocorr[best_lag])

        # Parabolic interpolation around peak for microtonal precision
        if 0 < best_lag < len(autocorr) - 1:
            alpha = autocorr[best_lag - 1]
            beta = autocorr[best_lag]
            gamma = autocorr[best_lag + 1]
            denom = 2 * (2 * beta - alpha - gamma)
            if denom != 0:
                delta = (alpha - gamma) / denom
                best_lag = best_lag + delta

        f0 = sr / best_lag
        midi = cls.hz_to_midi(f0)
        note_name = cls.midi_to_note_name(midi)
        is_voiced = bool(confidence >= 0.35 and (min_hz <= f0 <= max_hz))

        return {
            "f0_hz": round(float(f0), 2),
            "midi_pitch": round(float(midi), 2),
            "note_name": note_name,
            "confidence": round(confidence, 3),
            "is_voiced": is_voiced
        }

    @classmethod
    def snap_to_scale(
        cls,
        midi_pitch: float,
        key: str = "F",
        scale: str = "minor"
    ) -> Dict[str, Any]:
        """
        Quantizes an estimated vocal pitch to the closest note in the target song scale.
        Calculates the semitone transposition required.
        """
        norm_key = key.strip().upper()
        norm_key = norm_key.replace("DB", "C#").replace("EB", "D#").replace("GB", "F#").replace("AB", "G#").replace("BB", "A#")
        root_pitch_class = NOTE_NAMES.index(norm_key) if norm_key in NOTE_NAMES else 5 # F default

        scale_name = scale.lower().replace(" ", "_")
        intervals = SCALE_INTERVALS.get(scale_name, SCALE_INTERVALS["minor"])

        scale_pitch_classes = [(root_pitch_class + interval) % 12 for interval in intervals]

        curr_pc = int(round(midi_pitch)) % 12
        curr_octave = int(round(midi_pitch)) // 12

        # Find closest scale pitch class
        best_target = None
        min_dist = 999.0
        for spc in scale_pitch_classes:
            # Distance in semitones accounting for circle of 12
            diff = (spc - curr_pc + 6) % 12 - 6
            if abs(diff) < abs(min_dist):
                min_dist = diff
                best_target = spc

        target_pitch = int(round(midi_pitch)) + min_dist
        semitone_shift = target_pitch - int(round(midi_pitch))
        target_note_name = cls.midi_to_note_name(target_pitch)
        in_scale = (curr_pc in scale_pitch_classes)

        return {
            "original_midi": round(midi_pitch, 2),
            "original_note": cls.midi_to_note_name(midi_pitch),
            "target_midi": int(target_pitch),
            "target_note": target_note_name,
            "semitone_shift": int(semitone_shift),
            "in_scale": in_scale,
            "key": key,
            "scale": scale
        }

    @classmethod
    def generate_harmonic_intervals(
        cls,
        base_midi: int = 53, # F3
        key: str = "F",
        scale: str = "minor"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculates the 6 fundamental harmonic interval layers used in professional vocal chop design:
        1. Tonic Root (0 st)
        2. Minor/Major 3rd (+3 st in minor, +4 in major)
        3. Perfect 5th (+7 st)
        4. Octave Up (+12 st)
        5. Octave Down (-12 st)
        6. Minor 7th (+10 st in minor)
        """
        is_major = "maj" in scale.lower()
        third_interval = 4 if is_major else 3
        seventh_interval = 11 if is_major else 10

        intervals = {
            "root": {"shift": 0, "role": "Anchor Tonic", "desc": "Solid harmonic foundation"},
            "third": {"shift": third_interval, "role": "Color / Emotion", "desc": "Expressive melodic flavor"},
            "fifth": {"shift": 7, "role": "Power / Brightness", "desc": "Consonant energy lift"},
            "seventh": {"shift": seventh_interval, "role": "Neo-Soul Tension", "desc": "Sophisticated modern touch"},
            "octave_up": {"shift": 12, "role": "Air & Pop Sparkle", "desc": "Bright airy vocal ear candy"},
            "octave_down": {"shift": -12, "role": "Sub-Tonic Dark", "desc": "Tyler / Travis chopped & screwed depth"}
        }

        result = {}
        for k, v in intervals.items():
            target_pitch = base_midi + v["shift"]
            result[k] = {
                "semitone_shift": v["shift"],
                "target_midi": target_pitch,
                "note_name": cls.midi_to_note_name(target_pitch),
                "role": v["role"],
                "description": v["desc"]
            }

        return result

    @classmethod
    def create_buildup_stutter_pattern(
        cls,
        chop_path: str,
        start_beat: float,
        duration_beats: float = 8.0, # Typically 2 bars of buildup
        key: str = "F",
        scale: str = "minor"
    ) -> List[Dict[str, Any]]:
        """
        Generates an accelerating stutter sequence for buildups:
        - Bar 1 (beats 0-4): 1/4 and 1/8 note chops with rising pitch (+0 -> +3 st)
        - Bar 2 (beats 4-7): 1/16 note rapid stutter with +7 st
        - Final beat (beats 7-8): 1/32 micro-roll pitching up to +12 st octave climax!
        """
        stutter_events: List[Dict[str, Any]] = []

        # Segment 1: Half-note / Quarter-note pulse
        stutter_events.append({
            "name": "buildup_chop_q1",
            "file_path": chop_path,
            "start_beat": start_beat + 0.0,
            "length_beats": 1.0,
            "pitch_shift": 0,
            "velocity": 85,
            "stage": "pulse"
        })
        stutter_events.append({
            "name": "buildup_chop_q2",
            "file_path": chop_path,
            "start_beat": start_beat + 2.0,
            "length_beats": 1.0,
            "pitch_shift": 0,
            "velocity": 90,
            "stage": "pulse"
        })

        # Segment 2: Eighth-note acceleration (beats 4 to 6)
        for i in range(4):
            beat = start_beat + 4.0 + (i * 0.5)
            stutter_events.append({
                "name": f"buildup_chop_8th_{i}",
                "file_path": chop_path,
                "start_beat": beat,
                "length_beats": 0.45,
                "pitch_shift": 3, # Minor 3rd lift
                "velocity": 95 + (i * 3),
                "stage": "8th_acceleration"
            })

        # Segment 3: 16th-note rapid roll (beats 6 to 7)
        for i in range(4):
            beat = start_beat + 6.0 + (i * 0.25)
            stutter_events.append({
                "name": f"buildup_chop_16th_{i}",
                "file_path": chop_path,
                "start_beat": beat,
                "length_beats": 0.22,
                "pitch_shift": 7, # Perfect 5th lift
                "velocity": 105 + (i * 2),
                "stage": "16th_roll"
            })

        # Segment 4: 32nd-note pre-drop climax (beats 7 to 8)
        for i in range(8):
            beat = start_beat + 7.0 + (i * 0.125)
            stutter_events.append({
                "name": f"buildup_chop_32nd_{i}",
                "file_path": chop_path,
                "start_beat": beat,
                "length_beats": 0.10,
                "pitch_shift": 12, # Octave climax
                "velocity": 115 + min(12, i),
                "stage": "32nd_climax"
            })

        return stutter_events

    @classmethod
    def create_drop_melodic_chops(
        cls,
        chops: List[Dict[str, Any]],
        start_beat: float,
        length_bars: int = 8,
        beats_per_bar: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Distributes chops across drop sections in a syncopated call-and-response rhythm:
        - Call: Root chop on beat 1.3 / 2.1
        - Response: Harmonized chop (+3 or +7 st) on syncopated offbeats (and of 3, and of 4)
        """
        if not chops:
            return []

        placements: List[Dict[str, Any]] = []
        c_root = chops[0]
        c_alt = chops[1] if len(chops) > 1 else chops[0]

        for bar in range(length_bars):
            bar_start = start_beat + (bar * beats_per_bar)

            if bar % 2 == 0:
                # Call Bar: Statement on beat 1.5 and 2.5
                placements.append({
                    "name": f"drop_call_a_bar{bar}",
                    "file_path": c_root.get("file_path", ""),
                    "start_beat": bar_start + 1.5,
                    "length_beats": 0.75,
                    "pitch_shift": 0,
                    "role": "call_root"
                })
                placements.append({
                    "name": f"drop_call_b_bar{bar}",
                    "file_path": c_alt.get("file_path", ""),
                    "start_beat": bar_start + 2.5,
                    "length_beats": 0.75,
                    "pitch_shift": 3,
                    "role": "call_third"
                })
            else:
                # Response Bar: Syncopated energetic answer on beat 2.0 and 3.5
                placements.append({
                    "name": f"drop_resp_a_bar{bar}",
                    "file_path": c_alt.get("file_path", ""),
                    "start_beat": bar_start + 2.0,
                    "length_beats": 0.50,
                    "pitch_shift": 7,
                    "role": "resp_fifth"
                })
                placements.append({
                    "name": f"drop_resp_b_bar{bar}",
                    "file_path": c_root.get("file_path", ""),
                    "start_beat": bar_start + 3.5,
                    "length_beats": 0.50,
                    "pitch_shift": 12,
                    "role": "resp_octave"
                })

        return placements
