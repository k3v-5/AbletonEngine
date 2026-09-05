# engine/audio/deconstruction/transcriber.py
"""
Reference Audio Transcriber: Audio-to-MIDI Transcription Engine.
Performs:
1. Tempo estimation (Autocorrelation on onset energy envelope).
2. Key / Tonality detection (Krumhansl-Schmuckler chroma correlation).
3. Drum multi-band transcription (Kick 36, Snare 38, Closed Hat 42).
4. Bass pitch tracking (Autocorrelation F0 tracking in 35-260 Hz range).
5. Chord / Harmony chromagram transcription.
"""

import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import soundfile as sf

from engine.audio.deconstruction.models import (
    AudioTranscriptionResult,
    TranscribedNoteEvent,
    DeconstructedStem,
    StemCategory
)
from engine.audio.deconstruction.separator import AudioStemSeparator

# Krumhansl-Schmuckler key profiles
KEY_PROFILES_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KEY_PROFILES_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

class ReferenceTranscriber:
    """Extracts musical structures, stems, and MIDI notes from audio references."""

    def __init__(self, separator: Optional[AudioStemSeparator] = None):
        self.separator = separator or AudioStemSeparator()

    def detect_tempo(self, audio_mono: np.ndarray, sr: int) -> float:
        """
        Estimates BPM using autocorrelation of onset energy envelope.
        Restricted to standard musical tempo range 65.0 - 180.0 BPM.
        """
        hop = int(sr * 0.01)  # 10ms frame rate (100 Hz)
        n_frames = max(1, len(audio_mono) // hop)
        envelope = np.zeros(n_frames, dtype=np.float32)
        
        for i in range(n_frames):
            frame = audio_mono[i * hop : (i + 1) * hop]
            envelope[i] = np.sqrt(np.mean(frame ** 2) + 1e-12)
            
        # Half-wave rectified difference for novelty detection
        novelty = np.maximum(0.0, np.diff(envelope))
        novelty -= np.mean(novelty)
        
        if np.all(novelty == 0) or len(novelty) < 50:
            return 120.0
            
        # Autocorrelation
        autocorr = np.correlate(novelty, novelty, mode='full')
        autocorr = autocorr[len(novelty) - 1 :]
        
        # Search range in lags corresponding to 65 to 180 BPM
        # BPM = 60 * 100 / lag => lag = 6000 / BPM
        min_lag = int(round(6000.0 / 180.0))  # ~33
        max_lag = int(round(6000.0 / 65.0))   # ~92
        
        if max_lag >= len(autocorr):
            max_lag = len(autocorr) - 1
            
        search_region = autocorr[min_lag : max_lag + 1]
        if len(search_region) == 0:
            return 120.0
            
        peak_idx = int(np.argmax(search_region)) + min_lag
        estimated_bpm = 6000.0 / peak_idx
        return round(float(estimated_bpm), 1)

    def detect_key(self, audio_mono: np.ndarray, sr: int) -> str:
        """
        Estimates musical key using 12-semitone chromagram correlation
        with Krumhansl-Schmuckler tonal profiles.
        """
        n_fft = 8192
        if len(audio_mono) < n_fft:
            audio_mono = np.pad(audio_mono, (0, n_fft - len(audio_mono)))
            
        freqs = np.fft.rfftfreq(n_fft, d=1.0 / sr)
        fft_mag = np.abs(np.fft.rfft(audio_mono[:n_fft]))
        
        chroma = np.zeros(12, dtype=np.float32)
        for i, f in enumerate(freqs):
            if 55.0 <= f <= 2000.0:  # Musical pitch range A1 to B6
                midi_note = 69.0 + 12.0 * np.log2(f / 440.0)
                pitch_class = int(round(midi_note)) % 12
                chroma[pitch_class] += fft_mag[i]
                
        chroma_norm = chroma / (np.linalg.norm(chroma) + 1e-6)
        
        best_corr = -1.0
        best_key = "C Major"
        
        for root in range(12):
            # Major correlation
            rot_major = np.roll(KEY_PROFILES_MAJOR, root)
            rot_major_norm = rot_major / np.linalg.norm(rot_major)
            corr_maj = float(np.dot(chroma_norm, rot_major_norm))
            if corr_maj > best_corr:
                best_corr = corr_maj
                best_key = f"{NOTE_NAMES[root]} Major"
                
            # Minor correlation
            rot_minor = np.roll(KEY_PROFILES_MINOR, root)
            rot_minor_norm = rot_minor / np.linalg.norm(rot_minor)
            corr_min = float(np.dot(chroma_norm, rot_minor_norm))
            if corr_min > best_corr:
                best_corr = corr_min
                best_key = f"{NOTE_NAMES[root]} Minor"
                
        return best_key

    def transcribe_drums(
        self,
        drum_audio: np.ndarray,
        sr: int,
        tempo: float
    ) -> List[TranscribedNoteEvent]:
        """
        Transcribes rhythmic drum events into Kick (36), Snare (38), and Hat (42) notes.
        """
        if drum_audio.ndim == 2:
            mono = 0.5 * (drum_audio[:, 0] + drum_audio[:, 1])
        else:
            mono = drum_audio

        n_samples = len(mono)
        duration_sec = n_samples / sr
        notes: List[TranscribedNoteEvent] = []
        
        # Band filtering via FFT
        n_fft = 2048
        hop = 512
        freqs = np.fft.rfftfreq(n_fft, d=1.0 / sr)
        
        kick_bins = (freqs >= 35) & (freqs <= 140)
        snare_bins = (freqs >= 200) & (freqs <= 2000)
        hat_bins = (freqs >= 5000) & (freqs <= 16000)
        
        num_frames = max(1, (n_samples - n_fft) // hop + 1)
        
        kick_env = np.zeros(num_frames)
        snare_env = np.zeros(num_frames)
        hat_env = np.zeros(num_frames)
        
        win = np.hanning(n_fft)
        for i in range(num_frames):
            chunk = mono[i * hop : i * hop + n_fft] * win
            mag = np.abs(np.fft.rfft(chunk))
            kick_env[i] = np.sum(mag[kick_bins])
            snare_env[i] = np.sum(mag[snare_bins])
            hat_env[i] = np.sum(mag[hat_bins])

        # Detect peaks in each band
        def get_onsets(env: np.ndarray, threshold_ratio: float = 0.25, min_dist_frames: int = 4):
            max_val = np.max(env)
            if max_val < 1e-4:
                return []
            thresh = max_val * threshold_ratio
            onsets = []
            last_frame = -min_dist_frames
            for f_idx in range(1, len(env) - 1):
                if env[f_idx] > thresh and env[f_idx] > env[f_idx - 1] and env[f_idx] >= env[f_idx + 1]:
                    if f_idx - last_frame >= min_dist_frames:
                        onsets.append((f_idx, env[f_idx] / max_val))
                        last_frame = f_idx
            return onsets

        kick_onsets = get_onsets(kick_env, threshold_ratio=0.30, min_dist_frames=6)
        snare_onsets = get_onsets(snare_env, threshold_ratio=0.32, min_dist_frames=6)
        hat_onsets = get_onsets(hat_env, threshold_ratio=0.20, min_dist_frames=3)

        spb = 60.0 / tempo  # Seconds per beat

        def add_events(onset_list, midi_pitch, default_dur):
            for frame_idx, norm_amp in onset_list:
                time_sec = (frame_idx * hop) / sr
                raw_beat = 1.0 + (time_sec / spb)
                # Quantize to nearest 1/16th (0.25 beat) if close
                quantized_beat = round(raw_beat * 4.0) / 4.0
                beat = quantized_beat if abs(quantized_beat - raw_beat) < 0.12 else round(raw_beat, 2)
                vel = int(np.clip(50 + norm_amp * 70, 45, 127))
                notes.append(TranscribedNoteEvent(
                    pitch=midi_pitch,
                    start_beat=beat,
                    duration_beats=default_dur,
                    velocity=vel,
                    confidence=float(round(norm_amp, 2)),
                    articulation="transient"
                ))

        add_events(kick_onsets, 36, 0.5)     # Kick
        add_events(snare_onsets, 38, 0.5)    # Snare
        add_events(hat_onsets, 42, 0.25)     # Closed Hat

        notes.sort(key=lambda n: (n.start_beat, n.pitch))
        return notes

    def transcribe_bass(
        self,
        bass_audio: np.ndarray,
        sr: int,
        tempo: float
    ) -> List[TranscribedNoteEvent]:
        """
        Tracks bass fundamental frequency (35Hz - 260Hz) frame by frame
        using autocorrelation and segments into continuous MIDI bass notes.
        """
        if bass_audio.ndim == 2:
            mono = 0.5 * (bass_audio[:, 0] + bass_audio[:, 1])
        else:
            mono = bass_audio

        frame_len = 4096
        hop = 1024
        n_samples = len(mono)
        num_frames = max(1, (n_samples - frame_len) // hop + 1)
        
        spb = 60.0 / tempo
        min_lag = int(round(sr / 260.0))  # Max F0 = 260 Hz (~Middle C)
        max_lag = int(round(sr / 35.0))   # Min F0 = 35 Hz (~C#1)
        
        frame_pitches = []  # (frame_idx, pitch, amplitude)
        
        for i in range(num_frames):
            chunk = mono[i * hop : i * hop + frame_len]
            rms = np.sqrt(np.mean(chunk ** 2) + 1e-12)
            if rms < 0.015:
                frame_pitches.append((i, None, 0.0))
                continue
                
            corr = np.correlate(chunk, chunk, mode='full')
            corr = corr[len(chunk) - 1 :]
            
            if max_lag >= len(corr):
                f_max = len(corr) - 1
            else:
                f_max = max_lag
                
            region = corr[min_lag : f_max + 1]
            if len(region) == 0:
                frame_pitches.append((i, None, 0.0))
                continue
                
            peak_idx = int(np.argmax(region)) + min_lag
            f0 = sr / peak_idx
            
            if 32.0 <= f0 <= 270.0:
                midi_pitch = int(round(69.0 + 12.0 * np.log2(f0 / 440.0)))
                frame_pitches.append((i, midi_pitch, rms))
            else:
                frame_pitches.append((i, None, 0.0))

        # Segment continuous frames into notes
        notes: List[TranscribedNoteEvent] = []
        current_pitch = None
        start_frame = None
        max_amp = 0.0
        
        for f_idx, pitch, amp in frame_pitches:
            if pitch is not None:
                if current_pitch is None:
                    current_pitch = pitch
                    start_frame = f_idx
                    max_amp = amp
                elif pitch == current_pitch:
                    max_amp = max(max_amp, amp)
                else:
                    # Note ended, pitch changed
                    dur_frames = f_idx - start_frame
                    if dur_frames >= 2:  # Minimum note length ~46ms
                        start_sec = (start_frame * hop) / sr
                        dur_sec = (dur_frames * hop) / sr
                        start_beat = round(1.0 + (start_sec / spb), 2)
                        dur_beat = max(0.25, round(dur_sec / spb, 2))
                        vel = int(np.clip(60 + max_amp * 200, 50, 127))
                        notes.append(TranscribedNoteEvent(
                            pitch=current_pitch,
                            start_beat=start_beat,
                            duration_beats=dur_beat,
                            velocity=vel,
                            confidence=0.85
                        ))
                    current_pitch = pitch
                    start_frame = f_idx
                    max_amp = amp
            else:
                if current_pitch is not None:
                    dur_frames = f_idx - start_frame
                    if dur_frames >= 2:
                        start_sec = (start_frame * hop) / sr
                        dur_sec = (dur_frames * hop) / sr
                        start_beat = round(1.0 + (start_sec / spb), 2)
                        dur_beat = max(0.25, round(dur_sec / spb, 2))
                        vel = int(np.clip(60 + max_amp * 200, 50, 127))
                        notes.append(TranscribedNoteEvent(
                            pitch=current_pitch,
                            start_beat=start_beat,
                            duration_beats=dur_beat,
                            velocity=vel,
                            confidence=0.85
                        ))
                    current_pitch = None
                    start_frame = None
                    max_amp = 0.0

        # Flush final note if audio ends while sustained
        if current_pitch is not None and start_frame is not None:
            dur_frames = len(frame_pitches) - start_frame
            if dur_frames >= 2:
                start_sec = (start_frame * hop) / sr
                dur_sec = (dur_frames * hop) / sr
                start_beat = round(1.0 + (start_sec / spb), 2)
                dur_beat = max(0.25, round(dur_sec / spb, 2))
                vel = int(np.clip(60 + max_amp * 200, 50, 127))
                notes.append(TranscribedNoteEvent(
                    pitch=current_pitch,
                    start_beat=start_beat,
                    duration_beats=dur_beat,
                    velocity=vel,
                    confidence=0.85
                ))

        return notes

    def transcribe_chords(
        self,
        harmony_audio: np.ndarray,
        sr: int,
        tempo: float
    ) -> List[TranscribedNoteEvent]:
        """
        Estimates musical chords from the harmonic audio stem.
        Analyzes 2-beat chunks and extracts dominant triad notes.
        """
        if harmony_audio.ndim == 2:
            mono = 0.5 * (harmony_audio[:, 0] + harmony_audio[:, 1])
        else:
            mono = harmony_audio

        spb = 60.0 / tempo
        chunk_beats = 2.0  # Analyze every 2 beats
        chunk_samples = int(chunk_beats * spb * sr)
        if chunk_samples <= 0:
            return []

        num_chunks = max(1, len(mono) // chunk_samples)
        notes: List[TranscribedNoteEvent] = []

        for c_idx in range(num_chunks):
            start_s = c_idx * chunk_samples
            chunk = mono[start_s : start_s + chunk_samples]
            if np.sqrt(np.mean(chunk ** 2) + 1e-12) < 0.01:
                continue

            n_fft = 4096
            fft_mag = np.abs(np.fft.rfft(chunk[:n_fft]))
            freqs = np.fft.rfftfreq(n_fft, d=1.0 / sr)

            chroma = np.zeros(12)
            for i, f in enumerate(freqs):
                if 130.0 <= f <= 1500.0:
                    midi_p = int(round(69.0 + 12.0 * np.log2(f / 440.0)))
                    chroma[midi_p % 12] += fft_mag[i]

            # Top 3 pitch classes in this chunk
            top_pitches = np.argsort(chroma)[-3:]
            start_beat = round(1.0 + (c_idx * chunk_beats), 2)

            for p_class in top_pitches:
                if chroma[p_class] > 0.05 * np.max(chroma):
                    # Place in middle octave 4 (MIDI 60 + p_class)
                    notes.append(TranscribedNoteEvent(
                        pitch=60 + int(p_class),
                        start_beat=start_beat,
                        duration_beats=chunk_beats,
                        velocity=80,
                        confidence=0.75
                    ))

        return notes

    def transcribe(
        self,
        audio_input: Any,
        tempo: Optional[float] = None,
        key: Optional[str] = None,
        base_name: str = "reference"
    ) -> AudioTranscriptionResult:
        """
        Executes full reference deconstruction:
        1. Separates into 4 stems.
        2. Detects tempo & musical key.
        3. Transcribes drum MIDI, bassline MIDI, and chord progression.
        """
        if isinstance(audio_input, (str, Path)):
            p = Path(audio_input)
            data, sr = sf.read(str(p), always_2d=True)
            source_path = str(p)
            if not base_name or base_name == "reference":
                base_name = p.stem
        else:
            data = np.asarray(audio_input, dtype=np.float32)
            if data.ndim == 1:
                data = np.column_stack([data, data])
            sr = 44100
            source_path = "in-memory-audio"

        data = data.astype(np.float32)
        duration = len(data) / sr
        mono = 0.5 * (data[:, 0] + data[:, 1])

        # 1. Stems
        stems = self.separator.separate(data, sample_rate=sr, base_name=base_name)

        # 2. Tempo & Key
        detected_bpm = tempo if tempo else self.detect_tempo(mono, sr)
        detected_key = key if key else self.detect_key(mono, sr)

        # Load stems for transcription
        drum_audio, _ = sf.read(stems["drums"].audio_path)
        bass_audio, _ = sf.read(stems["bass"].audio_path)
        other_audio, _ = sf.read(stems["other"].audio_path)

        # 3. Transcribe MIDI
        drum_notes = self.transcribe_drums(drum_audio, sr, detected_bpm)
        bass_notes = self.transcribe_bass(bass_audio, sr, detected_bpm)
        chord_notes = self.transcribe_chords(other_audio, sr, detected_bpm)

        return AudioTranscriptionResult(
            source_path=source_path,
            detected_tempo=detected_bpm,
            detected_key=detected_key,
            duration_seconds=duration,
            sample_rate=sr,
            stems=stems,
            drum_notes=drum_notes,
            bass_notes=bass_notes,
            chord_notes=chord_notes,
            metadata={
                "drum_note_count": len(drum_notes),
                "bass_note_count": len(bass_notes),
                "chord_note_count": len(chord_notes)
            }
        )
