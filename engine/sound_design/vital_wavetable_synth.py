# engine/sound_design/vital_wavetable_synth.py
"""
Vital Algorithmic Wavetable Synthesizer.

Programmatic generator of 2,048-sample single-cycle waveforms and multi-frame
wavetable tables encoded in IEEE-754 32-bit floating point Base64 (Vital native format),
plus 16-bit PCM transient/noise buffers for the Vital Sampler.
"""

from typing import List, Dict, Any, Callable, Optional
import struct
import base64
import math
import random
import logging

logger = logging.getLogger("VitalWavetableSynth")

POINTS_PER_CYCLE = 2048


class WavetableSynthesizer:
    """
    Mathematical synthesis engine producing native Vital wavetable buffers.
    Every single-cycle wave consists of exactly 2,048 float32 little-endian points,
    normalized between -1.0 and +1.0.
    """

    @staticmethod
    def encode_wave_floats(samples: List[float]) -> str:
        """
        Packs a list of floats into 32-bit little-endian binary and encodes to Base64.
        """
        if len(samples) != POINTS_PER_CYCLE:
            # Resample or pad/truncate to exact POINTS_PER_CYCLE
            if len(samples) < POINTS_PER_CYCLE:
                step = len(samples) / POINTS_PER_CYCLE
                resampled = [samples[int(i * step)] for i in range(POINTS_PER_CYCLE)]
                samples = resampled
            else:
                samples = samples[:POINTS_PER_CYCLE]

        # Normalize to [-1.0, 1.0] with headroom protection
        peak = max(abs(s) for s in samples) if samples else 1.0
        if peak > 0.0001:
            norm_factor = 0.98 / peak
            samples = [s * norm_factor for s in samples]
        else:
            samples = [0.0] * POINTS_PER_CYCLE

        raw_bytes = struct.pack(f"<{POINTS_PER_CYCLE}f", *samples)
        return base64.b64encode(raw_bytes).decode("ascii")

    @classmethod
    def generate_sine(cls) -> str:
        """Generates a pure mathematical sine cycle."""
        floats = [math.sin(2.0 * math.pi * (i / POINTS_PER_CYCLE)) for i in range(POINTS_PER_CYCLE)]
        return cls.encode_wave_floats(floats)

    @classmethod
    def generate_saw(cls) -> str:
        """Generates a band-limited or analog-style downward saw."""
        floats = [1.0 - 2.0 * (i / POINTS_PER_CYCLE) for i in range(POINTS_PER_CYCLE)]
        return cls.encode_wave_floats(floats)

    @classmethod
    def generate_triangle(cls) -> str:
        """Generates a symmetric triangle wave."""
        floats = []
        for i in range(POINTS_PER_CYCLE):
            phase = i / POINTS_PER_CYCLE
            if phase < 0.25:
                val = 4.0 * phase
            elif phase < 0.75:
                val = 2.0 - 4.0 * phase
            else:
                val = -4.0 + 4.0 * phase
            floats.append(val)
        return cls.encode_wave_floats(floats)

    @classmethod
    def generate_pulse(cls, pulse_width: float = 0.5) -> str:
        """Generates a pulse/square wave with adjustable duty cycle (PWM)."""
        pw = max(0.05, min(0.95, pulse_width))
        floats = [1.0 if (i / POINTS_PER_CYCLE) < pw else -1.0 for i in range(POINTS_PER_CYCLE)]
        return cls.encode_wave_floats(floats)

    @classmethod
    def generate_fm(cls, carrier_ratio: float = 1.0, mod_ratio: float = 2.0, index: float = 2.0) -> str:
        """
        Synthesizes a 2-operator Phase Modulation / FM cycle.
        y = sin(2*pi*carrier*t + index * sin(2*pi*mod*t))
        """
        floats = []
        for i in range(POINTS_PER_CYCLE):
            t = i / POINTS_PER_CYCLE
            modulator = index * math.sin(2.0 * math.pi * mod_ratio * t)
            carrier = math.sin(2.0 * math.pi * carrier_ratio * t + modulator)
            floats.append(carrier)
        return cls.encode_wave_floats(floats)

    @classmethod
    def generate_chebyshev_warmth(cls, order: int = 3, drive: float = 0.6) -> str:
        """
        Uses Chebyshev polynomials of the 1st kind to inject musical harmonic saturation.
        T_2(x) = 2x^2 - 1 (2nd harmonic / octave warmth)
        T_3(x) = 4x^3 - 3x (3rd harmonic / tube grit)
        """
        floats = []
        d = max(0.0, min(1.0, drive))
        for i in range(POINTS_PER_CYCLE):
            x = math.sin(2.0 * math.pi * (i / POINTS_PER_CYCLE))
            if order == 2:
                # Add 2nd harmonic warmth
                y = (1.0 - d) * x + d * (2.0 * x * x - 1.0)
            elif order == 3:
                # Add 3rd harmonic analog saturation
                y = (1.0 - d) * x + d * (4.0 * x * x * x - 3.0 * x)
            elif order == 4:
                # Add 4th harmonic
                t2 = 2.0 * x * x - 1.0
                y = (1.0 - d) * x + d * (2.0 * t2 * t2 - 1.0)
            else:
                y = x
            floats.append(y)
        return cls.encode_wave_floats(floats)

    @classmethod
    def generate_formant_vocal(cls, vowel: str = "A") -> str:
        """
        Synthesizes an acoustic vowel formant table using additive harmonic filtering.
        Vowel spectral peaks (harmonics based on typical vocal tract resonances):
        """
        vowel_upper = vowel.upper().strip()
        # Relative harmonic weights for vowels:
        # Harmonics [1st, 2nd, 3rd, 4th, 5th, 6th, 7th, 8th, 9th, 10th]
        formant_profiles = {
            "A": [1.0, 0.9, 0.7, 0.4, 0.8, 0.6, 0.3, 0.2, 0.1, 0.05],   # Open throat, dual peak
            "E": [1.0, 0.8, 0.3, 0.1, 0.2, 0.7, 0.9, 0.5, 0.2, 0.1],   # High 2nd formant
            "I": [1.0, 0.5, 0.2, 0.1, 0.1, 0.4, 0.8, 1.0, 0.6, 0.3],   # Bright high formant
            "O": [1.0, 1.0, 0.6, 0.2, 0.1, 0.05, 0.0, 0.0, 0.0, 0.0],  # Round, dark low formants
            "U": [1.0, 0.7, 0.2, 0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]   # Deep sub-dominant vowel
        }
        weights = formant_profiles.get(vowel_upper, formant_profiles["A"])
        return cls.generate_harmonic_additive(weights)

    @classmethod
    def generate_harmonic_additive(cls, harmonic_weights: List[float]) -> str:
        """
        Synthesizes a waveform from explicit Fourier harmonic series amplitudes.
        """
        floats = [0.0] * POINTS_PER_CYCLE
        for h_idx, weight in enumerate(harmonic_weights, start=1):
            if abs(weight) < 0.0001:
                continue
            for i in range(POINTS_PER_CYCLE):
                floats[i] += weight * math.sin(2.0 * math.pi * h_idx * (i / POINTS_PER_CYCLE))

        return cls.encode_wave_floats(floats)

    @classmethod
    def build_wavetable_structure(
        cls,
        name: str,
        keyframes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Assembles a full Vital wavetable object with multiple keyframes.
        keyframes should be a list of dicts: [{'position': int, 'wave_data': b64_str}]
        """
        # Ensure keyframe positions are sorted and clamped
        sorted_kfs = sorted(keyframes, key=lambda k: k.get("position", 0))

        return {
            "author": "AbletonEngine Algorithmic Synth",
            "full_normalize": True,
            "groups": [
                {
                    "components": [
                        {
                            "interpolation": 1,
                            "interpolation_style": 0,
                            "keyframes": sorted_kfs,
                            "type": "Wave Source"
                        }
                    ]
                }
            ],
            "name": name,
            "remove_all_dc": True,
            "version": "1.0.7"
        }

    @classmethod
    def build_morphing_wavetable(cls, wt_type: str = "BASIC_SHAPES") -> Dict[str, Any]:
        """
        Produces a complete morphing wavetable table across 256 positions.
        """
        wt_type_upper = wt_type.upper()

        if "FM" in wt_type_upper:
            # Morphs from pure sine to complex FM metallic grit
            kfs = [
                {"position": 0, "wave_data": cls.generate_sine()},
                {"position": 64, "wave_data": cls.generate_fm(1.0, 1.0, 0.75)},
                {"position": 128, "wave_data": cls.generate_fm(1.0, 2.0, 1.5)},
                {"position": 192, "wave_data": cls.generate_fm(1.0, 3.5, 2.2)},
                {"position": 256, "wave_data": cls.generate_fm(1.0, 7.0, 3.5)}
            ]
            name = "Algorithmic FM Spectrum"

        elif "VOCAL" in wt_type_upper or "TALK" in wt_type_upper:
            # Morphs through vocal vowels: U -> O -> A -> E -> I
            kfs = [
                {"position": 0, "wave_data": cls.generate_formant_vocal("U")},
                {"position": 64, "wave_data": cls.generate_formant_vocal("O")},
                {"position": 128, "wave_data": cls.generate_formant_vocal("A")},
                {"position": 192, "wave_data": cls.generate_formant_vocal("E")},
                {"position": 256, "wave_data": cls.generate_formant_vocal("I")}
            ]
            name = "Algorithmic Vocal Formants"

        elif "ANALOG" in wt_type_upper or "WARM" in wt_type_upper:
            # Morphs from pure sine to Chebyshev saturated warmth, then soft saw
            kfs = [
                {"position": 0, "wave_data": cls.generate_sine()},
                {"position": 85, "wave_data": cls.generate_chebyshev_warmth(order=2, drive=0.7)},
                {"position": 170, "wave_data": cls.generate_chebyshev_warmth(order=3, drive=0.85)},
                {"position": 256, "wave_data": cls.generate_saw()}
            ]
            name = "Algorithmic Analog Saturation"

        else:
            # Standard Basic Shapes (Sine -> Triangle -> Saw -> Pulse)
            kfs = [
                {"position": 0, "wave_data": cls.generate_sine()},
                {"position": 85, "wave_data": cls.generate_triangle()},
                {"position": 170, "wave_data": cls.generate_saw()},
                {"position": 256, "wave_data": cls.generate_pulse(0.5)}
            ]
            name = "Algorithmic Basic Shapes"

        return cls.build_wavetable_structure(name=name, keyframes=kfs)

    @classmethod
    def generate_sampler_buffer(
        cls,
        sample_type: str = "WHITE_NOISE",
        duration_sec: float = 1.0,
        sample_rate: int = 44100
    ) -> Dict[str, Any]:
        """
        Synthesizes raw 16-bit PCM little-endian audio for Vital's internal Sampler.
        """
        num_samples = int(duration_sec * sample_rate)
        sample_type_upper = sample_type.upper()
        int16_samples = []

        if "VINYL" in sample_type_upper:
            # Low rumble + occasional pop clicks
            for _ in range(num_samples):
                rumble = random.gauss(0, 800)
                click = random.choice([0, 0, 0, 0, 0, 12000, -10000]) if random.random() < 0.005 else 0
                sample = int(max(-32767, min(32767, rumble + click)))
                int16_samples.append(sample)
            name = "Algorithmic Vinyl Texture"

        elif "CLICK" in sample_type_upper or "TRANSIENT" in sample_type_upper:
            # Short 10ms transient attack click followed by silence
            click_len = int(0.015 * sample_rate)
            for i in range(num_samples):
                if i < click_len:
                    env = math.exp(-i / (0.003 * sample_rate))
                    val = env * math.sin(2 * math.pi * 1200 * (i / sample_rate)) * 28000
                else:
                    val = 0
                int16_samples.append(int(max(-32767, min(32767, val))))
            name = "Algorithmic Punch Transient"

        elif "PINK" in sample_type_upper:
            # 1/f Pink noise simulation (Paul Kellet's filter)
            b0 = b1 = b2 = b3 = b4 = b5 = b6 = 0.0
            for _ in range(num_samples):
                white = random.uniform(-1.0, 1.0)
                b0 = 0.99886 * b0 + white * 0.0555179
                b1 = 0.99332 * b1 + white * 0.0750759
                b2 = 0.96900 * b2 + white * 0.1538520
                b3 = 0.86650 * b3 + white * 0.3104856
                b4 = 0.55000 * b4 + white * 0.5329522
                b5 = -0.7616 * b5 - white * 0.0168980
                pink = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362
                b6 = white * 0.115926
                int16_samples.append(int(max(-32767, min(32767, pink * 3500))))
            name = "Algorithmic Pink Noise"

        else:
            # Standard Gaussian White Noise
            for _ in range(num_samples):
                val = int(random.gauss(0, 6000))
                int16_samples.append(max(-32767, min(32767, val)))
            name = "Algorithmic White Noise"

        raw_bytes = struct.pack(f"<{num_samples}h", *int16_samples)
        b64_str = base64.b64encode(raw_bytes).decode("ascii")

        return {
            "length": num_samples,
            "name": name,
            "sample_rate": sample_rate,
            "samples": b64_str
        }
