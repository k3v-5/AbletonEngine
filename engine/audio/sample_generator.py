# engine/audio/sample_generator.py
"""
Procedural Audio Sample Generator:
Generates studio-grade 44.1kHz 16-bit PCM WAV audio samples in memory or disk:
- Vocal vowel chants / hooks (synthesized formant filtering with human vibrato).
- Organic foley beds (band-limited pink/brown noise texture with subtle atmospheric resonance).
- Transition risers & sweeps (exponential frequency sweep + high-pass filtered noise).
- Transition impacts / sub drops (transient attack punch + exponential sub decay).
"""

import os
import math
import struct
import wave
from pathlib import Path
from typing import Optional


class ProceduralSampleGenerator:
    """Generates standalone standard PCM WAV audio files for Ableton Live audio tracks."""

    DEFAULT_SAMPLE_RATE = 44100

    @classmethod
    def get_cache_dir(cls) -> Path:
        """Returns the default directory for caching generated samples."""
        cache_dir = Path(__file__).resolve().parent.parent.parent / "cache" / "samples"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    @classmethod
    def generate_sample(
        cls,
        sample_type: str = "vocal",
        output_path: Optional[str] = None,
        duration_sec: float = 4.0,
        sample_rate: int = DEFAULT_SAMPLE_RATE
    ) -> str:
        """
        Generates a 16-bit Mono WAV audio file based on sample_type.
        Supported types: 'vocal', 'vocal_chop', 'foley', 'ambient', 'riser', 'sweep', 'impact', 'sub_drop'.
        Returns the absolute path to the generated WAV file.
        """
        st = sample_type.lower().strip()
        if output_path is None:
            cache_dir = cls.get_cache_dir()
            filename = f"gen_{st}_{int(duration_sec)}s_{sample_rate}.wav"
            output_path = str(cache_dir / filename)

        out_file = Path(output_path).resolve()
        out_file.parent.mkdir(parents=True, exist_ok=True)

        if out_file.exists() and out_file.stat().st_size > 44:
            return str(out_file)

        n_frames = int(sample_rate * duration_sec)
        frames = bytearray()

        if "vocal" in st:
            # Vocal Formant Synthesis (simulating 'Ah' vowel with 220Hz root and vibrato)
            f0 = 220.0  # A3 root
            for i in range(n_frames):
                t = i / float(sample_rate)
                vibrato = 1.0 + 0.015 * math.sin(2.0 * math.pi * 5.5 * t)
                phase_fund = 2.0 * math.pi * (f0 * vibrato) * t
                phase_f1 = 2.0 * math.pi * (800.0 * vibrato) * t   # First formant ~800 Hz
                phase_f2 = 2.0 * math.pi * (1200.0 * vibrato) * t  # Second formant ~1200 Hz
                phase_f3 = 2.0 * math.pi * (2600.0 * vibrato) * t  # Singer's formant ~2600 Hz

                raw = (
                    0.45 * math.sin(phase_fund)
                    + 0.25 * math.sin(phase_f1)
                    + 0.18 * math.sin(phase_f2)
                    + 0.12 * math.sin(phase_f3)
                )
                # ADSR Envelope
                attack = min(1.0, t / 0.08)
                release = min(1.0, (duration_sec - t) / 0.12)
                env = attack * release
                sample_val = int(14000 * env * raw)
                clamped = max(-32767, min(32767, sample_val))
                frames += struct.pack("<h", clamped)

        elif "foley" in st or "ambient" in st:
            # Band-limited organic textured noise (pink-like approximation)
            b0, b1, b2 = 0.0, 0.0, 0.0
            import random
            rng = random.Random(42)  # Deterministic seed for reproducible foley
            for i in range(n_frames):
                t = i / float(sample_rate)
                white = rng.uniform(-1.0, 1.0)
                b0 = 0.99886 * b0 + white * 0.0555179
                b1 = 0.99332 * b1 + white * 0.0750759
                b2 = 0.96900 * b2 + white * 0.1538520
                pink = (b0 + b1 + b2 + white * 0.5362) * 0.15
                breath = 0.7 + 0.3 * math.sin(2.0 * math.pi * 0.25 * t)
                sample_val = int(8000 * breath * pink)
                clamped = max(-32767, min(32767, sample_val))
                frames += struct.pack("<h", clamped)

        elif "riser" in st or "sweep" in st:
            # Exponential pitch riser (100Hz -> 2000Hz) with noise build
            import random
            rng = random.Random(1337)
            for i in range(n_frames):
                t = i / float(sample_rate)
                progress = t / float(duration_sec)
                freq = 100.0 * math.pow(20.0, progress)
                phase = 2.0 * math.pi * freq * t
                tone = math.sin(phase)
                noise = rng.uniform(-1.0, 1.0) * (progress * 0.6)
                amp = math.pow(progress, 1.5)
                sample_val = int(16000 * amp * (0.6 * tone + 0.4 * noise))
                clamped = max(-32767, min(32767, sample_val))
                frames += struct.pack("<h", clamped)

        elif "impact" in st or "sub_drop" in st:
            # Sub bass drop with transient punch
            f_start = 140.0
            f_end = 38.0
            for i in range(n_frames):
                t = i / float(sample_rate)
                decay = math.exp(-2.5 * t)
                pitch_decay = math.exp(-6.0 * t)
                freq = f_end + (f_start - f_end) * pitch_decay
                phase = 2.0 * math.pi * freq * t
                sub = math.sin(phase)
                transient = math.sin(2.0 * math.pi * 800.0 * t) * math.exp(-80.0 * t) if t < 0.05 else 0.0
                sample_val = int(18000 * (decay * sub + 0.5 * transient))
                clamped = max(-32767, min(32767, sample_val))
                frames += struct.pack("<h", clamped)

        else:
            for i in range(n_frames):
                t = i / float(sample_rate)
                env = min(1.0, t / 0.05) * min(1.0, (duration_sec - t) / 0.1)
                val = int(12000 * env * math.sin(2.0 * math.pi * 440.0 * t))
                frames += struct.pack("<h", max(-32767, min(32767, val)))

        with wave.open(str(out_file), "w") as wav_out:
            wav_out.setnchannels(1)
            wav_out.setsampwidth(2)
            wav_out.setframerate(sample_rate)
            wav_out.writeframes(frames)

        return str(out_file)
