"""
Audio capture abstraction and engine.
Decouples audio source acquisition from DSP analysis.
Supports RenderedFileSource, StemSource, M4LSource, and ExternalCaptureSource.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import numpy as np
import soundfile as sf

from .bridge import AudioBridge, RenderedFileAudioBridge, M4LAudioBridge


class AudioSource(ABC):
    """Abstract base class for audio sources."""

    @abstractmethod
    def get_audio_data(self, start_sec: float = 0.0, duration_sec: Optional[float] = None) -> Tuple[np.ndarray, int]:
        """
        Returns audio as float32 ndarray with shape (channels, samples) and sample rate.
        Channels are normalized to 2 (stereo) or 1 (mono).
        """
        pass

    @abstractmethod
    def get_duration(self) -> float:
        """Returns duration in seconds."""
        pass


class RenderedFileSource(AudioSource):
    """Source that reads an audio file (.wav, .aiff, .flac) from disk."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        # Validate format
        info = sf.info(str(self.file_path))
        self.duration = info.duration
        self.sample_rate = info.samplerate
        self.channels = info.channels

    def get_audio_data(self, start_sec: float = 0.0, duration_sec: Optional[float] = None) -> Tuple[np.ndarray, int]:
        start_frame = int(start_sec * self.sample_rate)
        frames = int(duration_sec * self.sample_rate) if duration_sec is not None else -1
        
        data, sr = sf.read(str(self.file_path), start=start_frame, frames=frames, dtype="float32")
        if data.ndim == 1:
            audio = data[np.newaxis, :]
        else:
            audio = data.T
        return audio, sr

    def get_duration(self) -> float:
        return self.duration


class StemSource(AudioSource):
    """Source containing multiple role-specific stem audio files."""

    def __init__(self, stem_map: Dict[str, str]):
        self.stem_map = stem_map
        self.sources: Dict[str, RenderedFileSource] = {}
        for role, p in stem_map.items():
            self.sources[role] = RenderedFileSource(p)

    def get_audio_data(self, start_sec: float = 0.0, duration_sec: Optional[float] = None) -> Tuple[np.ndarray, int]:
        # Mix down all stems into a single stereo master
        if not self.sources:
            return np.zeros((2, 0), dtype="float32"), 44100
            
        stems_data = []
        sr = 44100
        for src in self.sources.values():
            data, sr = src.get_audio_data(start_sec, duration_sec)
            stems_data.append(data)
            
        min_len = min(d.shape[1] for d in stems_data)
        mixed = np.zeros((2, min_len), dtype="float32")
        for d in stems_data:
            if d.shape[0] == 1:
                mixed[0, :min_len] += d[0, :min_len]
                mixed[1, :min_len] += d[0, :min_len]
            else:
                mixed[0, :min_len] += d[0, :min_len]
                mixed[1, :min_len] += d[1, :min_len]
        return mixed, sr

    def get_stem(self, role: str) -> Optional[RenderedFileSource]:
        return self.sources.get(role)

    def get_duration(self) -> float:
        if not self.sources:
            return 0.0
        return max(s.get_duration() for s in self.sources.values())


class M4LSource(AudioSource):
    """Source connected to a Max for Live streaming device bridge."""

    def __init__(self, bridge: AudioBridge):
        self.bridge = bridge

    def get_audio_data(self, start_sec: float = 0.0, duration_sec: Optional[float] = None) -> Tuple[np.ndarray, int]:
        return self.bridge.get_audio_data(start_sec, duration_sec)

    def get_duration(self) -> float:
        return 0.0


class ExternalCaptureSource(RenderedFileSource):
    """Source recorded or captured from an external soundcard or interface."""
    pass


class AudioCaptureEngine:
    """Orchestrates audio capture in different operational modes."""

    def __init__(self, render_manager=None):
        self.render_manager = render_manager

    def capture(self, mode: str, target: Any = None, start_bar: int = 0,
                end_bar: int = 16, tempo: float = 120.0) -> AudioSource:
        """
        Captures audio according to specified mode:
        SECTION, LOOP, STEM, FULL_MIX, MASTER, TRACK.
        """
        mode = mode.upper()
        if isinstance(target, str) and Path(target).exists():
            return RenderedFileSource(target)
            
        if mode == "STEM" and isinstance(target, dict):
            return StemSource(target)
            
        # Fallback: if render_manager is present and target can be rendered
        if self.render_manager is not None:
            rendered_path = self.render_manager.render_analysis_target(
                mode=mode, target=target, start_bar=start_bar, end_bar=end_bar, tempo=tempo
            )
            if rendered_path and Path(rendered_path).exists():
                return RenderedFileSource(rendered_path)
                
        raise ValueError(f"Unable to capture audio for mode '{mode}' with target '{target}'")
