# engine/sound_design/pad_sound_generator.py
"""
Atmospheric Synthesizer Pad Generator:
Synthesizes a lush, warm, multi-voice ambient analog pad progression in D Minor.
Features:
- Multi-oscillator detuned unison (dual detuned saws + warm triangle/sine sub).
- 4-pole resonant low-pass filter with slow sinusoidal LFO movement (0.2 Hz).
- Stereo dimensional widening with gentle chorusing.
- Chords: Dm9 -> Ebmaj7#11 -> Gm9 -> Asus4(b9) in D Minor Phrygian/Insen.
- Output: 24-bit 44.1kHz stereo WAV.
"""

import numpy as np
from pathlib import Path
import soundfile as sf


def generate_source_ambient_pad(
    output_path: str,
    duration_sec: float = 16.0,
    sample_rate: int = 44100,
    key: str = "D",
    scale: str = "Minor",
    bpm: float = 105.0
) -> str:
    """
    Renders a sustained, evolving stereo analog pad chord progression to WAV.
    Duration defaults to 16.0 seconds (approx 4 bars @ 105 BPM = 9.14s, or 8 bars = 18.28s).
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    num_samples = int(duration_sec * sample_rate)
    t = np.linspace(0.0, duration_sec, num_samples, endpoint=False)

    # 4 Harmonic Chords in D Minor Phrygian / Insen
    # Chord 1 (0.0 to 0.25): Dm9 (D3=146.83, F3=174.61, A3=220.00, C4=261.63, E4=329.63)
    # Chord 2 (0.25 to 0.50): Ebmaj7#11 (Eb3=155.56, G3=196.00, Bb3=233.08, D4=293.66, A4=440.00)
    # Chord 3 (0.50 to 0.75): Gm9 (G2=98.00, D3=146.83, Bb3=233.08, F4=349.23, A4=440.00)
    # Chord 4 (0.75 to 1.00): Asus4(b9) (A2=110.00, G3=196.00, Bb3=233.08, D4=293.66, F4=349.23)
    chords = [
        {"freqs": [146.83, 174.61, 220.00, 261.63, 329.63], "start": 0.00, "end": 0.25},
        {"freqs": [155.56, 196.00, 233.08, 293.66, 440.00], "start": 0.25, "end": 0.50},
        {"freqs": [98.00, 146.83, 233.08, 349.23, 440.00],  "start": 0.50, "end": 0.75},
        {"freqs": [110.00, 196.00, 233.08, 293.66, 349.23], "start": 0.75, "end": 1.00},
    ]

    left_raw = np.zeros(num_samples, dtype=np.float32)
    right_raw = np.zeros(num_samples, dtype=np.float32)

    # Detune offsets in cents for lush supersaw spread
    unison_detunes = [-9.0, -3.0, 0.0, +3.0, +9.0]
    unison_pans = [-0.65, -0.25, 0.0, +0.25, +0.65]

    for chord_info in chords:
        c_start_sample = int(chord_info["start"] * num_samples)
        c_end_sample = int(chord_info["end"] * num_samples)
        c_len = c_end_sample - c_start_sample
        if c_len <= 0:
            continue

        c_t = t[c_start_sample:c_end_sample] - t[c_start_sample]

        # Smooth attack & release envelope for pad swelling
        attack_len = min(int(0.6 * sample_rate), c_len // 4)
        release_len = min(int(0.6 * sample_rate), c_len // 4)
        env = np.ones(c_len, dtype=np.float32)
        if attack_len > 0:
            env[:attack_len] = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, attack_len)))
        if release_len > 0:
            env[-release_len:] *= 0.5 * (1.0 + np.cos(np.linspace(0, np.pi, release_len)))

        for f0 in chord_info["freqs"]:
            for detune_cents, pan in zip(unison_detunes, unison_pans):
                f_detuned = f0 * (2.0 ** (detune_cents / 1200.0))

                # Add warm harmonics (sawtooth partials 1..14 with 1/n roll-off)
                voice_sig = np.zeros(c_len, dtype=np.float32)
                for h in range(1, 15):
                    fh = f_detuned * h
                    if fh >= sample_rate * 0.45:
                        break
                    h_amp = (1.0 / (h ** 0.85)) * (0.8 + 0.2 * np.sin(h * 1.5))
                    # Phase offset per partial
                    phase = (h * 1.618033 + detune_cents) % (2.0 * np.pi)
                    voice_sig += h_amp * np.sin(2.0 * np.pi * fh * c_t + phase)

                # Slow warm filter sweep LFO (0.18 Hz)
                lfo = 0.75 + 0.25 * np.sin(2.0 * np.pi * 0.18 * c_t + pan)
                voice_sig *= lfo * env

                # Stereo panning
                l_gain = np.cos((pan + 1.0) * np.pi / 4.0)
                r_gain = np.sin((pan + 1.0) * np.pi / 4.0)

                left_raw[c_start_sample:c_end_sample] += voice_sig * l_gain
                right_raw[c_start_sample:c_end_sample] += voice_sig * r_gain

    # Add deep warm sub-foundation (D1 = 36.7Hz)
    sub_osc = 0.35 * np.sin(2.0 * np.pi * 36.71 * t) * (0.8 + 0.2 * np.sin(2.0 * np.pi * 0.1 * t))
    left_raw += sub_osc
    right_raw += sub_osc

    # 4-pole low-pass butterworth filter around 2200 Hz
    from scipy.signal import butter, sosfilt
    sos = butter(4, 2200.0, btype="lowpass", fs=sample_rate, output="sos")
    left_filtered = sosfilt(sos, left_raw)
    right_filtered = sosfilt(sos, right_raw)

    # Subtle dimensional stereo delay (Haas 14ms on right channel)
    delay_samples = int(0.014 * sample_rate)
    right_delayed = np.zeros_like(right_filtered)
    right_delayed[delay_samples:] = right_filtered[:-delay_samples]
    right_filtered = 0.7 * right_filtered + 0.3 * right_delayed

    # Stereo normalizer to -3 dBFS (0.707) peak
    stereo_sig = np.vstack([left_filtered, right_filtered]).T
    peak = np.max(np.abs(stereo_sig))
    if peak > 1e-5:
        stereo_sig = (stereo_sig / peak) * 0.707

    sf.write(str(path), stereo_sig, sample_rate, subtype="PCM_24")
    return str(path.resolve())
