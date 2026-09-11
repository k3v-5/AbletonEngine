# engine/audio/deconstruction/expressive_transcriber.py
"""
Expressive Audio-to-MIDI Transcriber.
Transcribes monophonic audio signals (vocals, humming, whistling, solo guitars, synth leads)
into quantized MIDI NoteEvents with velocity dynamics and continuous pitch bend detection.
Powered by PyTorch/torchaudio F0 detection with deterministic DSP autocorrelation fallback.
"""

import math
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import soundfile as sf
from scipy import signal

from engine.music.models import NoteEvent

logger = logging.getLogger("ExpressiveAudioTranscriber")


@dataclass
class ExpressiveNoteEvent:
    """NoteEvent enriched with microtonal pitch bends and dynamic velocity."""
    pitch: int
    start_time_beats: float
    duration_beats: float
    velocity: int
    pitch_bends_cents: List[float]  # continuous cents deviation (-100 to +100)

    def to_note_event(self) -> NoteEvent:
        return NoteEvent(
            pitch=self.pitch,
            start_time=self.start_time_beats,
            duration=self.duration_beats,
            velocity=self.velocity
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pitch": self.pitch,
            "start_time": round(float(self.start_time_beats), 3),
            "duration": round(float(self.duration_beats), 3),
            "velocity": self.velocity,
            "pitch_bends_cents": [round(float(c), 1) for c in self.pitch_bends_cents[:10]]
        }


class ExpressiveAudioTranscriber:
    """Converts audio recordings into expressive MIDI note events."""

    def __init__(self, min_freq_hz: float = 65.0, max_freq_hz: float = 1800.0):
        self.min_freq_hz = min_freq_hz
        self.max_freq_hz = max_freq_hz
        self._has_torchaudio = self._check_torchaudio()

    def _check_torchaudio(self) -> bool:
        try:
            import torchaudio.functional as F
            return hasattr(F, "detect_pitch_frequency")
        except Exception:
            return False

    @staticmethod
    def hz_to_midi_pitch(freq_hz: float) -> Tuple[int, float]:
        """
        Converts frequency in Hz to closest MIDI note number and microtonal deviation in cents.
        Returns: (midi_pitch, cents_deviation)
        """
        if freq_hz <= 0.0:
            return (0, 0.0)
        exact_midi = 69.0 + 12.0 * math.log2(max(1e-4, freq_hz) / 440.0)
        round_pitch = int(round(exact_midi))
        cents = float((exact_midi - round_pitch) * 100.0)
        return (round_pitch, cents)

    def extract_f0_curve(self, audio_mono: np.ndarray, sr: int) -> Tuple[np.ndarray, float]:
        """
        Extracts fundamental frequency curve (F0 in Hz) frame by frame.
        Returns (f0_array, frame_rate_hz).
        """
        if self._has_torchaudio:
            try:
                import torch
                import torchaudio.functional as F
                waveform = torch.tensor(audio_mono, dtype=torch.float32).unsqueeze(0)
                # Frame rate defaults to 100 Hz (hop_length = sr / 100)
                frame_time_ms = 10.0
                hop_len = max(1, int(sr * (frame_time_ms / 1000.0)))
                f0_tensor = F.detect_pitch_frequency(waveform, sr, frame_time=frame_time_ms / 1000.0)
                f0_curve = f0_tensor.squeeze(0).cpu().numpy()
                frame_rate_hz = 1000.0 / frame_time_ms
                return f0_curve, frame_rate_hz
            except Exception as ex:
                logger.warning(f"Torchaudio pitch detection failed: {ex}. Using DSP autocorrelation fallback.")

        # DSP Autocorrelation Fallback
        frame_time_ms = 10.0
        hop_len = max(1, int(sr * (frame_time_ms / 1000.0)))
        frame_len = max(1, int(sr * 0.040))  # 40ms window
        n_frames = max(1, (len(audio_mono) - frame_len) // hop_len)
        f0_curve = np.zeros(n_frames, dtype=np.float32)

        min_lag = max(1, int(sr / self.max_freq_hz))
        max_lag = min(frame_len - 1, int(sr / self.min_freq_hz))

        for i in range(n_frames):
            frame = audio_mono[i * hop_len : i * hop_len + frame_len] * np.hanning(frame_len)
            # Energy check
            rms = np.sqrt(np.mean(frame ** 2))
            if rms < 0.01:
                continue

            corr = signal.correlate(frame, frame, mode="full")
            corr = corr[len(corr) // 2 :]
            if len(corr) > max_lag and max_lag > min_lag:
                peak_lag = min_lag + int(np.argmax(corr[min_lag:max_lag]))
                if corr[peak_lag] > 0.30 * (corr[0] + 1e-12):
                    f0_curve[i] = float(sr / peak_lag)

        return f0_curve, 1000.0 / frame_time_ms

    def transcribe(
        self,
        audio_mono: np.ndarray,
        sr: int,
        tempo_bpm: float = 120.0,
        min_note_duration_beats: float = 0.25
    ) -> List[ExpressiveNoteEvent]:
        """
        Transcribes continuous F0 curve and energy novelty into discrete ExpressiveNoteEvents.
        Quantizes start times and durations to the musical grid based on tempo_bpm.
        """
        if len(audio_mono) < 512:
            return []

        # Peak normalize
        peak = float(np.max(np.abs(audio_mono)))
        if peak > 1e-5:
            norm_audio = audio_mono / peak
        else:
            return []

        f0_curve, frame_rate = self.extract_f0_curve(norm_audio, sr)
        sec_per_beat = 60.0 / max(30.0, tempo_bpm)
        sec_per_frame = 1.0 / frame_rate

        # Frame energy envelope
        hop_len = max(1, int(sr * sec_per_frame))
        n_frames = min(len(f0_curve), len(norm_audio) // hop_len)
        energies = np.zeros(n_frames, dtype=np.float32)
        for i in range(n_frames):
            frame = norm_audio[i * hop_len : (i + 1) * hop_len]
            energies[i] = float(np.sqrt(np.mean(frame ** 2) + 1e-12))

        # Discretize segments into note intervals
        events: List[ExpressiveNoteEvent] = []
        in_note = False
        cur_pitch = 0
        cur_cents: List[float] = []
        cur_energies: List[float] = []
        start_frame = 0

        # Pitch stability threshold: max 1.5 semitones variation for same note
        pitch_tolerance_semitones = 1.5

        for f_idx in range(n_frames):
            f0 = float(f0_curve[f_idx])
            energy = float(energies[f_idx])
            is_voiced = (self.min_freq_hz <= f0 <= self.max_freq_hz) and (energy >= 0.035)

            if is_voiced:
                p, cents = self.hz_to_midi_pitch(f0)
                if not in_note:
                    in_note = True
                    cur_pitch = p
                    cur_cents = [cents]
                    cur_energies = [energy]
                    start_frame = f_idx
                else:
                    # Check if note changed
                    if abs(p - cur_pitch) > pitch_tolerance_semitones:
                        # Close previous note
                        duration_sec = (f_idx - start_frame) * sec_per_frame
                        dur_beats = duration_sec / sec_per_beat
                        if dur_beats >= min_note_duration_beats:
                            start_beat = (start_frame * sec_per_frame) / sec_per_beat
                            # Quantize start to 16th grid (0.25 beats)
                            quant_start = round(start_beat * 4.0) / 4.0
                            quant_dur = max(min_note_duration_beats, round(dur_beats * 4.0) / 4.0)
                            avg_vel = int(np.clip(np.mean(cur_energies) * 127.0 * 1.5, 40, 127))
                            events.append(ExpressiveNoteEvent(
                                pitch=cur_pitch,
                                start_time_beats=quant_start,
                                duration_beats=quant_dur,
                                velocity=avg_vel,
                                pitch_bends_cents=list(cur_cents)
                            ))
                        # Start new note
                        cur_pitch = p
                        cur_cents = [cents]
                        cur_energies = [energy]
                        start_frame = f_idx
                    else:
                        cur_cents.append(cents)
                        cur_energies.append(energy)
            else:
                if in_note:
                    in_note = False
                    duration_sec = (f_idx - start_frame) * sec_per_frame
                    dur_beats = duration_sec / sec_per_beat
                    if dur_beats >= min_note_duration_beats:
                        start_beat = (start_frame * sec_per_frame) / sec_per_beat
                        quant_start = round(start_beat * 4.0) / 4.0
                        quant_dur = max(min_note_duration_beats, round(dur_beats * 4.0) / 4.0)
                        avg_vel = int(np.clip(np.mean(cur_energies) * 127.0 * 1.5, 40, 127))
                        events.append(ExpressiveNoteEvent(
                            pitch=cur_pitch,
                            start_time_beats=quant_start,
                            duration_beats=quant_dur,
                            velocity=avg_vel,
                            pitch_bends_cents=list(cur_cents)
                        ))
                    cur_cents = []
                    cur_energies = []

        return events

    def transcribe_file(
        self,
        file_path: Union[str, Path],
        tempo_bpm: float = 120.0
    ) -> List[ExpressiveNoteEvent]:
        """Transcribes an audio file on disk to ExpressiveNoteEvents."""
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            return []
        try:
            audio, sr = sf.read(str(p), always_2d=False, dtype="float32")
            if audio.ndim > 1:
                audio = np.mean(audio, axis=1)
            return self.transcribe(audio, sr, tempo_bpm=tempo_bpm)
        except Exception as ex:
            logger.error(f"Error transcribing file {file_path}: {ex}")
            return []
