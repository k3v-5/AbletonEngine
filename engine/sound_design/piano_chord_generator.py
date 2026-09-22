# engine/sound_design/piano_chord_generator.py
"""
High-Fidelity Acoustic Piano Chord Synthesizer & Renderer.
Generates an authentic, sustained grand piano chord (Fm9) with:
- Physical string stiffness inharmonicity: f_n = n * f_0 * sqrt(1 + B * n^2)
- Hammer felt strike impulse and velocity-dependent attack transients
- Multi-string detune beating (chorusing of triple unison strings)
- Sympathetic soundboard resonance and stereo acoustic diffusion
- Duration: 16 beats at 120 BPM = 8.0 seconds (24-bit 44.1kHz stereo WAV)
"""

import numpy as np
from pathlib import Path
import soundfile as sf


def generate_source_piano_chord(
    output_path: str,
    duration_sec: float = 8.0,
    sample_rate: int = 44100
) -> str:
    """Renders a pristine, rich, prolonged grand piano chord (Fm9) to WAV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    num_samples = int(duration_sec * sample_rate)
    t = np.linspace(0.0, duration_sec, num_samples, endpoint=False)

    # Piano chord notes: Fm9 (F2, C3, F3, Ab3, C4, Eb4, G4)
    # MIDI pitches and root frequencies
    notes = [
        {"midi": 41, "freq": 87.31,  "vel": 0.95, "pan": -0.40},  # F2 (Deep Root)
        {"midi": 48, "freq": 130.81, "vel": 0.88, "pan": -0.25},  # C3 (5th)
        {"midi": 53, "freq": 174.61, "vel": 0.92, "pan": -0.10},  # F3 (Octave)
        {"midi": 56, "freq": 207.65, "vel": 0.85, "pan":  0.10},  # Ab3 (Minor 3rd)
        {"midi": 60, "freq": 261.63, "vel": 0.90, "pan":  0.25},  # C4 (5th)
        {"midi": 63, "freq": 311.13, "vel": 0.82, "pan":  0.35},  # Eb4 (Minor 7th)
        {"midi": 67, "freq": 392.00, "vel": 0.86, "pan":  0.45},  # G4 (9th - emotional color)
    ]

    left_channel = np.zeros(num_samples, dtype=np.float32)
    right_channel = np.zeros(num_samples, dtype=np.float32)

    # Inharmonicity constant for steel piano strings
    B = 0.00015

    for note in notes:
        f0 = note["freq"]
        vel = note["vel"]
        pan = note["pan"]
        l_gain = np.cos((pan + 1.0) * np.pi / 4.0) * vel
        r_gain = np.sin((pan + 1.0) * np.pi / 4.0) * vel

        # String unison detuning (3 strings per key on grand piano)
        detunes = [-0.6, 0.0, +0.6]  # in cents

        note_signal = np.zeros(num_samples, dtype=np.float32)

        for detune_cents in detunes:
            detuned_f0 = f0 * (2.0 ** (detune_cents / 1200.0))
            # Generate up to 24 partials
            num_partials = min(24, int(sample_rate / (2.2 * detuned_f0)))
            for n in range(1, num_partials + 1):
                # Piano inharmonicity
                fn = n * detuned_f0 * np.sqrt(1.0 + B * (n ** 2))
                if fn >= sample_rate * 0.48:
                    break

                # High partials decay exponentially faster than low partials
                decay_rate = 0.45 * (1.0 + 0.18 * (n ** 1.25))
                env = np.exp(-decay_rate * t)

                # Amplitude roll-off per harmonic
                harmonic_amp = (1.0 / (n ** 1.15)) * (0.8 + 0.2 * np.cos(n))

                # Phase randomization per partial
                phase = (n * 1.618033) % (2.0 * np.pi)
                note_signal += harmonic_amp * env * np.sin(2.0 * np.pi * fn * t + phase)

        # Add felt hammer strike impact (percussive wooden attack)
        hammer_env = np.exp(-t * 95.0)
        hammer_click = (np.random.randn(num_samples) * 0.18) * hammer_env
        note_signal += hammer_click

        left_channel += note_signal * l_gain
        right_channel += note_signal * r_gain

    # Add sympathetic soundboard acoustic resonance
    from scipy.signal import fftconvolve
    ir_len = int(sample_rate * 0.35)
    ir_t = np.linspace(0, 0.35, ir_len)
    ir = (np.sin(2.0 * np.pi * 185.0 * ir_t) * 0.3 + np.sin(2.0 * np.pi * 320.0 * ir_t) * 0.2) * np.exp(-ir_t * 18.0)
    ir /= (np.max(np.abs(ir)) + 1e-6)

    left_body = fftconvolve(left_channel, ir, mode="same") * 0.25
    right_body = fftconvolve(right_channel, ir, mode="same") * 0.25

    left_channel += left_body
    right_channel += right_body

    # Normalize to -1.0 dBFS
    max_val = max(np.max(np.abs(left_channel)), np.max(np.abs(right_channel)))
    if max_val > 0:
        target = 10.0 ** (-1.0 / 20.0)  # -1.0 dB
        left_channel = (left_channel / max_val) * target
        right_channel = (right_channel / max_val) * target

    # Stack to stereo
    stereo_audio = np.stack([left_channel, right_channel], axis=-1)

    # Write 24-bit WAV file
    sf.write(str(path), stereo_audio, sample_rate, subtype="PCM_24")
    return str(path.resolve())


if __name__ == "__main__":
    out = "cache/uhts_resampled/source_piano_chord.wav"
    res_path = generate_source_piano_chord(out, duration_sec=8.0)
    print(f"Rendered source piano chord to: {res_path}")
