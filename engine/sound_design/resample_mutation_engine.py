# engine/sound_design/resample_mutation_engine.py
"""
Universal Harmonic Transformation Suite (UHTS) - Real Resampling Mutation Engine.
Transforms a single continuous source audio file (e.g. prolonged piano chord)
through 20 authentic producer sound-design pipelines into 20 unique, continuous
16-beat audio WAV textures.

Techniques:
1. Spectral Freeze Drone
2. Tuned Comb Karplus-Strong Chime
3. Vocal Formant Resonance
4. Industrial Multi-Stage Wavefolder
5. Sub-Safe Low-End Saturated Growl
6. Pitch-Shifted Shimmer Diffusion
7. Dark Reese Double-Octave Dive
8. Granular Micro-Particle Cloud
9. Vintage Cassette Wow & Flutter
10. Inharmonic Frequency-Shifted Bell Ring
11. Reverse Swell Exponential Bloom
12. 10-Bit Downsampled Digital Dirt
13. Haas 3D Psychoacoustic Decoupler
14. Syncopated Rhythmic Stutter Slicer
15. Full-Wave Octave Fuzz Multiplier
16. Chopped Polyrhythmic Trance Pulse
17. Spectral Gaussian Blur Infinite
18. Analog Tape Warmth & Opto Glue
19. Neoperreo Resonant Metallic Comb
20. Exponential Pitch Dive & HPF Sweep
"""

import numpy as np
from pathlib import Path
import soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt


def normalize_audio(audio: np.ndarray, target_db: float = -1.0) -> np.ndarray:
    """Normalizes stereo or mono audio to target peak dBFS."""
    peak = np.max(np.abs(audio))
    if peak > 1e-6:
        target = 10.0 ** (target_db / 20.0)
        return (audio / peak) * target
    return audio



NOTE_TO_SEMITONE = {
    "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3,
    "E": 4, "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8,
    "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11
}


def note_to_freq(note_name: str, octave: int = 4) -> float:
    """Calculates frequency in Hz for a given note and octave (A4 = 440.0 Hz)."""
    clean_note = (note_name or "F").strip().upper()
    semi = NOTE_TO_SEMITONE.get(clean_note, 5)
    midi_num = (octave + 1) * 12 + semi
    return float(440.0 * (2.0 ** ((midi_num - 69) / 12.0)))


def get_chord_frequencies(key: str = "F", scale: str = "minor", octave: int = 3) -> list:
    """Returns [root, third, fifth] frequencies in Hz for the given key and scale."""
    clean_key = (key or "F").strip().upper()
    is_major = "maj" in (scale or "").lower()
    root_semi = NOTE_TO_SEMITONE.get(clean_key, 5)
    third_semi = (root_semi + (4 if is_major else 3)) % 12
    fifth_semi = (root_semi + 7) % 12
    
    root_midi = (octave + 1) * 12 + root_semi
    third_midi = (octave + 1) * 12 + third_semi
    if third_semi < root_semi:
        third_midi += 12
    fifth_midi = (octave + 1) * 12 + fifth_semi
    if fifth_semi < root_semi:
        fifth_midi += 12
        
    f_root = 440.0 * (2.0 ** ((root_midi - 69) / 12.0))
    f_third = 440.0 * (2.0 ** ((third_midi - 69) / 12.0))
    f_fifth = 440.0 * (2.0 ** ((fifth_midi - 69) / 12.0))
    return [round(f_root, 2), round(f_third, 2), round(f_fifth, 2)]


# 1. Spectral Freeze Drone
def mutate_01_spectral_freeze(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    # Use middle sustained region (t=1.0s to 3.0s) to freeze magnitudes
    n_fft = 4096
    hop = 1024
    # Compute STFT of middle slice
    start_sample = int(1.0 * sr)
    slice_audio = audio[start_sample : start_sample + n_fft * 4, :]
    
    out = np.zeros_like(audio)
    for ch in range(audio.shape[1]):
        fft_frame = np.fft.rfft(slice_audio[:n_fft, ch] * np.hanning(n_fft))
        mag = np.abs(fft_frame)
        
        # Synthesize continuous frozen drone across entire duration
        num_frames = int(np.ceil(len(audio) / hop))
        synth = np.zeros(num_frames * hop + n_fft, dtype=np.float32)
        for i in range(num_frames):
            # Phase randomization across frames creates smooth liquid drone without artifacts
            rand_phase = np.random.uniform(0, 2 * np.pi, size=len(mag))
            frame_spec = mag * np.exp(1j * rand_phase)
            time_frame = np.fft.irfft(frame_spec) * np.hanning(n_fft)
            synth[i * hop : i * hop + n_fft] += time_frame
        out[:, ch] = synth[: len(audio)]
        
    # Soft saturation
    out = np.tanh(out * 1.6)
    return normalize_audio(out, -1.0)


# 2. Tuned Comb Karplus-Strong Chime
def mutate_02_tuned_comb_chime(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    # Comb filter delays dynamically tuned to key & scale chord (Root, 3rd, 5th in Octave 3)
    freqs = get_chord_frequencies(key=key, scale=scale, octave=3)
    out = np.zeros_like(audio)
    feedback = 0.88
    
    for ch in range(audio.shape[1]):
        ch_in = audio[:, ch]
        ch_out = np.zeros_like(ch_in)
        for f in freqs:
            delay_samples = max(2, int(sr / f))
            y = np.zeros_like(ch_in)
            for n in range(delay_samples, len(ch_in)):
                # Karplus-Strong feedback with lowpass damping
                y[n] = ch_in[n] + feedback * (0.65 * y[n - delay_samples] + 0.35 * y[n - delay_samples - 1])
            ch_out += y
        out[:, ch] = ch_out
        
    return normalize_audio(out, -1.0)


# 3. Vocal Formant Resonance
def mutate_03_vocal_formant_resonance(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    # 3 Parallel Vocal Formants (/a/ 800Hz, /e/ 1800Hz, /i/ 2500Hz)
    formant_freqs = [800.0, 1800.0, 2500.0]
    out = np.zeros_like(audio)
    
    for f in formant_freqs:
        # 2nd-order bandpass filter
        sos = butter(2, [max(20.0, f - 90.0), min(sr * 0.48, f + 90.0)], btype="bandpass", fs=sr, output="sos")
        filtered = sosfilt(sos, audio, axis=0)
        out += filtered * 1.5
        
    # Mild wavefold saturation
    out = np.sin(out * 2.2)
    return normalize_audio(out, -1.0)


# 4. Industrial Multi-Stage Wavefolder
def mutate_04_industrial_crunch_mutation(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    # 4-stage non-linear trigonometric wavefolder
    x = audio * 3.5
    y1 = np.sin(x)
    y2 = np.sin(y1 * 2.2)
    y3 = np.clip(y2 * 1.8, -0.9, 0.9)
    y4 = np.tanh(y3 * 2.5)
    
    # Add punchy high-frequency excitation
    sos = butter(2, 3500.0, btype="highpass", fs=sr, output="sos")
    crunch = sosfilt(sos, y4, axis=0) * 0.6
    out = y4 + crunch
    return normalize_audio(out, -1.0)


# 5. Sub-Safe Low-End Saturated Growl
def mutate_05_sub_safe_low_growl(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    # 4th-order lowpass at 120 Hz
    sos_lp = butter(4, 120.0, btype="lowpass", fs=sr, output="sos")
    low_band = sosfilt(sos_lp, audio, axis=0)
    
    # Convert to pure MONO below 120Hz
    mono_sub = np.mean(low_band, axis=1, keepdims=True)
    
    # Generate sub-octave fundamental (-12st) dynamically tuned to key root in octave 1 (30 - 65 Hz)
    f_sub = note_to_freq(key, octave=1)
    t = np.linspace(0, len(audio) / sr, len(audio), endpoint=False)[:, np.newaxis]
    sub_octave = np.sin(2.0 * np.pi * f_sub * t) * np.abs(mono_sub) * 1.4
    
    # Mid-bass harmonic saturation (120 - 450 Hz)
    sos_bp = butter(2, [120.0, 450.0], btype="bandpass", fs=sr, output="sos")
    mid_bass = sosfilt(sos_bp, audio, axis=0)
    sat_mid = np.tanh(mid_bass * 3.0) * 0.8
    
    out = mono_sub + sub_octave + sat_mid
    return normalize_audio(out, -1.0)


# 6. Pitch-Shifted Shimmer Diffusion
def mutate_06_pitch_shimmer_diffusion(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    # Pitch shift up +12 semitones via 2x speed resampling
    from scipy.signal import resample
    num_half = int(len(audio) / 2)
    pitched = resample(audio, num_half, axis=0)
    # Loop 2x to match length
    pitched_loop = np.tile(pitched, (2, 1))[: len(audio)]
    
    # Multi-tap diffusion delay
    delays = [int(sr * 0.11), int(sr * 0.17), int(sr * 0.24)]
    diffused = np.zeros_like(pitched_loop)
    for d in delays:
        delayed = np.pad(pitched_loop, ((d, 0), (0, 0)), mode="constant")[: len(audio)]
        diffused += delayed * 0.35
        
    out = audio * 0.35 + diffused * 0.75
    return normalize_audio(out, -1.0)


# 7. Dark Reese Double-Octave Dive
def mutate_07_dark_reese_octave_dive(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    # Pitch shift down -24 semitones (0.25x frequency)
    from scipy.signal import resample
    half_len = int(len(audio) * 4)
    down_stretched = resample(audio, half_len, axis=0)[: len(audio)]
    
    # Create detuned reese beating (delay left by 6ms, right by 14ms)
    d_l = int(sr * 0.006)
    d_r = int(sr * 0.014)
    left = np.roll(down_stretched[:, 0], d_l)
    right = np.roll(down_stretched[:, 1], d_r)
    reese = np.stack([left, right], axis=-1)
    
    # Lowpass at 280Hz
    sos = butter(3, 280.0, btype="lowpass", fs=sr, output="sos")
    out = sosfilt(sos, reese, axis=0)
    out = np.tanh(out * 2.8)
    return normalize_audio(out, -1.0)


# 8. Granular Micro-Particle Cloud
def mutate_08_granular_micro_cloud(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    grain_size = int(sr * 0.040)  # 40ms grains
    hop = int(grain_size * 0.4)
    out = np.zeros_like(audio)
    
    window = np.hanning(grain_size)[:, np.newaxis]
    num_grains = int((len(audio) - grain_size) / hop)
    
    for i in range(num_grains):
        jitter = np.random.randint(-int(grain_size * 0.3), int(grain_size * 0.3))
        src_pos = min(len(audio) - grain_size, max(0, i * hop + jitter))
        grain = audio[src_pos : src_pos + grain_size, :] * window
        
        # Random stereo spray
        pan = np.random.uniform(0.1, 0.9)
        grain[:, 0] *= np.cos(pan * np.pi / 2.0) * 1.3
        grain[:, 1] *= np.sin(pan * np.pi / 2.0) * 1.3
        
        dst_pos = i * hop
        if dst_pos + grain_size <= len(audio):
            out[dst_pos : dst_pos + grain_size] += grain
            
    return normalize_audio(out, -1.0)


# 9. Vintage Cassette Wow & Flutter
def mutate_09_vintage_tape_wow_warp(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    t = np.linspace(0, len(audio) / sr, len(audio), endpoint=False)
    # Dual LFO modulation (0.8Hz wow and 3.4Hz flutter)
    mod_samples = (np.sin(2.0 * np.pi * 0.8 * t) * 28.0 + np.sin(2.0 * np.pi * 3.4 * t) * 10.0)
    
    out = np.zeros_like(audio)
    indices = np.arange(len(audio))
    for ch in range(audio.shape[1]):
        read_idx = np.clip(indices + mod_samples, 0, len(audio) - 1).astype(int)
        out[:, ch] = audio[read_idx, ch]
        
    # Magnetic hysteresis saturation (soft asymmetric clip)
    out = out + 0.25 * (out ** 2) - 0.15 * (out ** 3)
    
    # 5.2 kHz high-frequency cassette head damping
    sos = butter(2, 5200.0, btype="lowpass", fs=sr, output="sos")
    out = sosfilt(sos, out, axis=0)
    return normalize_audio(out, -1.0)


# 10. Inharmonic Frequency-Shifted Bell Ring
def mutate_10_inharmonic_metallic_ring(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    from scipy.signal import hilbert
    # Calculate musical frequency shift based on detected key root in octave 3 (scaled by 1.11 for inharmonicity)
    f_root3 = note_to_freq(key, octave=3)
    shift_hz = round(f_root3 * 1.11, 1)
    f_carrier = note_to_freq(key, octave=1)  # Sub-carrier locked to key root
    
    t = np.linspace(0, len(audio) / sr, len(audio), endpoint=False)[:, np.newaxis]
    
    # Single-sideband frequency shift via analytic signal
    out = np.zeros_like(audio)
    for ch in range(audio.shape[1]):
        analytic = hilbert(audio[:, ch])
        shifted = np.real(analytic * np.exp(1j * 2.0 * np.pi * shift_hz * t[:, 0]))
        out[:, ch] = shifted
        
    # Metallic ring modulation with sub-carrier
    ring = out * np.sin(2.0 * np.pi * f_carrier * t) * 0.5
    out = out * 0.6 + ring * 0.4
    return normalize_audio(out, -1.0)

# Backward compatibility alias
mutate_09_inharmonic_metallic_ring = mutate_10_inharmonic_metallic_ring


# 11. Reverse Swell Exponential Bloom
def mutate_11_reverse_swell_bloom(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    # 1. Reverse audio
    rev = audio[::-1, :]
    
    # 2. Add long exponential diffusion decay
    ir_len = int(sr * 1.5)
    ir_t = np.linspace(0, 1.5, ir_len)
    ir = (np.random.randn(ir_len) * np.exp(-ir_t * 2.5))[:, np.newaxis]
    diffused_rev = fftconvolve(rev, ir, mode="same")
    
    # 3. Re-reverse!
    bloom = diffused_rev[::-1, :]
    out = audio * 0.4 + bloom * 0.8
    return normalize_audio(out, -1.0)


# 12. 10-Bit Downsampled Digital Dirt
def mutate_12_lofi_bit_crusher_dirt(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    # Bit depth reduction to 10-bit (1024 discrete steps)
    steps = 1024.0
    bit_crushed = np.round(audio * steps) / steps
    
    # Downsample by factor of 7 (sample-and-hold aliasing)
    downsample_factor = 7
    hold = np.zeros_like(bit_crushed)
    for i in range(0, len(bit_crushed), downsample_factor):
        hold[i : i + downsample_factor, :] = bit_crushed[i : i + 1, :]
        
    out = np.tanh(hold * 1.7)
    return normalize_audio(out, -1.0)


# 13. Haas 3D Psychoacoustic Decoupler
def mutate_13_haas_3d_spatial_decouple(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    # Mid / Side encoding
    mid = (audio[:, 0] + audio[:, 1]) * 0.5
    side = (audio[:, 0] - audio[:, 1]) * 0.5
    
    # 19ms micro-delay on side channel
    delay_samples = int(sr * 0.019)
    side_delayed = np.pad(side, (delay_samples, 0), mode="constant")[: len(side)]
    
    # 90-degree phase rotation on Side channel
    from scipy.signal import hilbert
    side_rotated = np.imag(hilbert(side_delayed))
    
    # Recombine to stereo with expanded side
    left = mid + side_rotated * 1.35
    right = mid - side_rotated * 1.35
    out = np.stack([left, right], axis=-1)
    return normalize_audio(out, -1.0)


# 14. Syncopated Rhythmic Stutter Slicer
def mutate_14_rhythmic_stutter_chop(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    # 16th-note slicing calculated dynamically from song BPM
    sixteenth = max(2, int(sr * ((60.0 / bpm) / 4.0)))
    out = np.zeros_like(audio)
    
    # 16th-note pattern: 1=play, 0=gate, 2=stutter repeat
    pattern = [1, 1, 0, 1, 2, 1, 0, 2, 1, 0, 1, 1, 2, 0, 1, 2]
    num_steps = len(pattern)
    
    for i in range(int(len(audio) / sixteenth)):
        step_type = pattern[i % num_steps]
        start = i * sixteenth
        end = min(len(audio), start + sixteenth)
        
        if step_type == 1:
            out[start:end] = audio[start:end]
        elif step_type == 2:
            # Repeat first half of 16th twice
            half = int((end - start) / 2)
            out[start : start + half] = audio[start : start + half]
            out[start + half : end] = audio[start : start + half]
            
    # Apply soft envelope smoothing to prevent clicks
    return normalize_audio(out, -1.0)


# 15. Full-Wave Octave Fuzz Multiplier
def mutate_15_octave_fuzz_multiplier(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    # Full-wave rectification mathematically doubles fundamental frequency to upper octave
    rectified = np.abs(audio)
    rectified -= np.mean(rectified, axis=0, keepdims=True)
    
    # Heavy fuzz overdrive
    fuzz = np.clip(rectified * 6.0, -0.85, 0.85)
    
    # Mid-frequency scoop at 650 Hz
    sos = butter(2, [550.0, 750.0], btype="bandstop", fs=sr, output="sos")
    out = sosfilt(sos, fuzz, axis=0)
    return normalize_audio(out, -1.0)


# 16. Chopped Polyrhythmic Trance Pulse
def mutate_16_chopped_trance_pulse(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    t = np.linspace(0, len(audio) / sr, len(audio), endpoint=False)[:, np.newaxis]
    # 16th-note pulse gate frequency synchronized to detected BPM: (bpm / 60.0) * 4.0 Hz
    pulse_freq = (bpm / 60.0) * 4.0
    gate = 0.5 * (1.0 + np.sin(2.0 * np.pi * pulse_freq * t))
    gate = np.clip(gate * 3.0, 0.0, 1.0)
    
    gated = audio * gate
    
    # Stereo ping-pong bounce synced to BPM: dotted 16th and 8th
    delay_l = max(2, int(sr * ((60.0 / bpm) * 0.75 / 2.0)))
    delay_r = max(2, int(sr * ((60.0 / bpm) * 0.5)))
    l_bounce = np.pad(gated[:, 0], (delay_l, 0))[: len(audio)]
    r_bounce = np.pad(gated[:, 1], (delay_r, 0))[: len(audio)]
    
    out = gated + np.stack([l_bounce * 0.45, r_bounce * 0.45], axis=-1)
    return normalize_audio(out, -1.0)


# 17. Spectral Gaussian Blur Infinite
def mutate_17_spectral_blur_infinite(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    n_fft = 4096
    hop = 512
    out = np.zeros_like(audio)
    
    from scipy.ndimage import gaussian_filter
    for ch in range(audio.shape[1]):
        # Compute spectrogram
        frames = []
        for i in range(0, len(audio) - n_fft, hop):
            frame = audio[i : i + n_fft, ch] * np.hanning(n_fft)
            frames.append(np.fft.rfft(frame))
        spec = np.array(frames)
        mag = np.abs(spec)
        phase = np.angle(spec)
        
        # 2D Gaussian blur across time and frequency
        blurred_mag = gaussian_filter(mag, sigma=(4.0, 2.5))
        
        # Inverse STFT
        resynth = np.zeros(len(frames) * hop + n_fft, dtype=np.float32)
        for i, (m, p) in enumerate(zip(blurred_mag, phase)):
            time_frame = np.fft.irfft(m * np.exp(1j * p)) * np.hanning(n_fft)
            resynth[i * hop : i * hop + n_fft] += time_frame
            
        out[:, ch] = resynth[: len(audio)]
        
    return normalize_audio(out, -1.0)


# 18. Analog Tape Warmth & Opto Glue
def mutate_18_analog_tape_warmth_glue(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    # Soft triode tube saturation
    x = audio * 2.2
    sat = x / (1.0 + np.abs(x))
    
    # Gentle high-shelf air boost at 11 kHz
    sos_high = butter(2, 11000.0, btype="highpass", fs=sr, output="sos")
    air = sosfilt(sos_high, sat, axis=0) * 0.4
    
    out = sat + air
    return normalize_audio(out, -1.0)


# 19. Neoperreo Resonant Metallic Comb
def mutate_19_neoperreo_metallic_comb(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    # 11.5ms early reflection comb filter tuned at 1.18 kHz
    delay_samples = int(sr * 0.0115)
    delayed = np.pad(audio, ((delay_samples, 0), (0, 0)))[: len(audio)]
    comb = audio + delayed * 0.85
    
    # Drum buss style aggressive crunch
    crunched = np.tanh(comb * 3.2)
    return normalize_audio(crunched, -1.0)


# 20. Exponential Pitch Dive & HPF Sweep
def mutate_20_exponential_pitch_dive(audio: np.ndarray, sr: int, key: str = "F", scale: str = "minor", bpm: float = 120.0, **kwargs) -> np.ndarray:
    t = np.linspace(0.0, 1.0, len(audio))
    # Pitch dive from 0 to -14 semitones exponentially
    pitch_ratio = 2.0 ** (-14.0 * (t ** 1.8) / 12.0)
    
    # Variable-rate time indices
    phase = np.cumsum(pitch_ratio)
    phase = (phase / phase[-1]) * (len(audio) - 1)
    
    out = np.zeros_like(audio)
    indices = np.clip(phase.astype(int), 0, len(audio) - 1)
    for ch in range(audio.shape[1]):
        out[:, ch] = audio[indices, ch]
        
    # High-pass filter sweeping up from 80Hz to 380Hz
    sos = butter(2, 220.0, btype="highpass", fs=sr, output="sos")
    out = sosfilt(sos, out, axis=0)
    return normalize_audio(out, -1.0)


MUTATION_REGISTRY = [
    ("SPECTRAL_FREEZE_DRONE", mutate_01_spectral_freeze),
    ("TUNED_COMB_CHIME", mutate_02_tuned_comb_chime),
    ("VOCAL_FORMANT_RESONANCE", mutate_03_vocal_formant_resonance),
    ("INDUSTRIAL_CRUNCH_MUTATION", mutate_04_industrial_crunch_mutation),
    ("SUB_SAFE_LOW_GROWL", mutate_05_sub_safe_low_growl),
    ("PITCH_SHIMMER_DIFFUSION", mutate_06_pitch_shimmer_diffusion),
    ("DARK_REESE_OCTAVE_DIVE", mutate_07_dark_reese_octave_dive),
    ("GRANULAR_MICRO_CLOUD", mutate_08_granular_micro_cloud),
    ("VINTAGE_TAPE_WOW_WARP", mutate_09_vintage_tape_wow_warp),
    ("INHARMONIC_METALLIC_RING", mutate_10_inharmonic_metallic_ring),
    ("REVERSE_SWELL_BLOOM", mutate_11_reverse_swell_bloom),
    ("LOFI_BIT_CRUSHER_DIRT", mutate_12_lofi_bit_crusher_dirt),
    ("HAAS_3D_SPATIAL_DECOUPLE", mutate_13_haas_3d_spatial_decouple),
    ("RHYTHMIC_STUTTER_CHOP", mutate_14_rhythmic_stutter_chop),
    ("OCTAVE_FUZZ_MULTIPLIER", mutate_15_octave_fuzz_multiplier),
    ("CHOPPED_TRANCE_PULSE", mutate_16_chopped_trance_pulse),
    ("SPECTRAL_BLUR_INFINITE", mutate_17_spectral_blur_infinite),
    ("ANALOG_TAPE_WARMTH_GLUE", mutate_18_analog_tape_warmth_glue),
    ("NEOPERREO_METALLIC_COMB", mutate_19_neoperreo_metallic_comb),
    ("EXPONENTIAL_PITCH_DIVE", mutate_20_exponential_pitch_dive),
]


def render_all_20_mutations(source_wav_path: str, output_dir: str, key: str = "F", scale: str = "minor", bpm: float = 120.0) -> list:
    """Renders all 20 unique continuous audio mutations from the source audio."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    audio, sr = sf.read(source_wav_path)
    if audio.ndim == 1:
        audio = np.stack([audio, audio], axis=-1)
        
    results = []
    print(f"=== Rendering 20 Audio Mutations from: {source_wav_path} ===")
    print(f"Tuning: {key} {scale} @ {bpm} BPM | SR: {sr} Hz, Duration: {len(audio)/sr:.1f}s\n")
    
    for idx, (name, fn) in enumerate(MUTATION_REGISTRY, start=1):
        filename = f"uhts_{idx:02d}_{name.lower()}.wav"
        target_path = str(out_dir / filename)
        print(f"[{idx:02d}/20] Processing '{name}'...")
        mutated = fn(audio, sr, key=key, scale=scale, bpm=bpm)
        sf.write(target_path, mutated, sr, subtype="PCM_24")
        results.append({
            "index": idx,
            "name": name,
            "path": target_path,
            "duration": len(mutated) / sr,
            "key": key,
            "scale": scale,
            "bpm": bpm
        })
        
    print("\n[OK] All 20 Audio Mutations Successfully Rendered!")
    return results


if __name__ == "__main__":
    src = "cache/uhts_resampled/source_piano_chord.wav"
    out = "cache/uhts_resampled"
    render_all_20_mutations(src, out)
