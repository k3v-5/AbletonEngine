"""
AudioBridge abstraction for Level 3 / real-time / M4L integration.
Allows Mix Engine to interface with either rendered audio files or real-time Max for Live bridges.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import numpy as np
import soundfile as sf
from pathlib import Path


class AudioBridge(ABC):
    """Abstract interface for audio capture bridges."""

    @abstractmethod
    def connect(self) -> bool:
        """Establishes connection with the audio bridge."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnects the audio bridge."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Returns connection status."""
        pass

    @abstractmethod
    def get_audio_data(self, start_sec: float = 0.0, duration_sec: Optional[float] = None) -> Tuple[np.ndarray, int]:
        """Returns audio data as (channels, samples) array in float32 and sample_rate."""
        pass

    @abstractmethod
    def get_rms(self) -> float:
        """Returns overall RMS in dBFS."""
        pass

    @abstractmethod
    def get_peak(self) -> float:
        """Returns peak in dBFS."""
        pass


class RenderedFileAudioBridge(AudioBridge):
    """Bridge that loads audio from rendered wav/aiff files on disk."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self._connected = False
        self._audio: Optional[np.ndarray] = None
        self._sr: int = 44100

    def connect(self) -> bool:
        if not self.file_path.exists():
            return False
        try:
            data, sr = sf.read(str(self.file_path), dtype="float32")
            if data.ndim == 1:
                # Shape (1, samples)
                self._audio = data[np.newaxis, :]
            else:
                # Transpose (samples, channels) to (channels, samples)
                self._audio = data.T
            self._sr = sr
            self._connected = True
            return True
        except Exception:
            self._connected = False
            return False

    def disconnect(self) -> None:
        self._audio = None
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected and self._audio is not None

    def get_audio_data(self, start_sec: float = 0.0, duration_sec: Optional[float] = None):
        if not self.is_connected() or self._audio is None:
            raise RuntimeError("Bridge not connected or audio not loaded")
        
        start_idx = int(start_sec * self._sr)
        if duration_sec is not None:
            end_idx = start_idx + int(duration_sec * self._sr)
            sliced = self._audio[:, start_idx:end_idx]
        else:
            sliced = self._audio[:, start_idx:]
        return sliced, self._sr

    def get_rms(self) -> float:
        if not self.is_connected() or self._audio is None:
            return -100.0
        rms = np.sqrt(np.mean(self._audio**2) + 1e-12)
        return float(20.0 * np.log10(rms))

    def get_peak(self) -> float:
        if not self.is_connected() or self._audio is None:
            return -100.0
        peak = np.max(np.abs(self._audio)) + 1e-12
        return float(20.0 * np.log10(peak))


class M4LAudioBridge(AudioBridge):
    """
    Max for Live bridge stub ready for UDP/OSC or socket streaming.
    Returns status: UNAVAILABLE until M4L device is inserted in Live session.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 9880):
        self.host = host
        self.port = port
        self._connected = False

    def connect(self) -> bool:
        # Prepared for real-time UDP socket connection with Live's M4L device
        return False

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def get_audio_data(self, start_sec: float = 0.0, duration_sec: Optional[float] = None):
        raise NotImplementedError("M4L real-time audio bridge requires the Ableton M4L AudioBridge.amxd device")

    def get_rms(self) -> float:
        return -100.0

    def get_peak(self) -> float:
        return -100.0
