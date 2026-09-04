# engine/adapters/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseAbletonAdapter(ABC):
    """Abstract interface for communicating with Ableton Live"""

    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def get_session_info(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_track_info(self, track_index: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_midi_track(self, index: int = -1) -> Dict[str, Any]:
        pass

    @abstractmethod
    def set_track_name(self, track_index: int, name: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def delete_track(self, track_index: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_clip(self, track_index: int, clip_index: int, length: float = 4.0) -> Dict[str, Any]:
        pass

    @abstractmethod
    def delete_clip(self, track_index: int, clip_index: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def set_track_volume(self, track_index: int, volume: float) -> Dict[str, Any]:
        pass

    @abstractmethod
    def set_track_panning(self, track_index: int, panning: float) -> Dict[str, Any]:
        pass

    @abstractmethod
    def set_track_mute(self, track_index: int, mute: bool) -> Dict[str, Any]:
        pass

    @abstractmethod
    def set_track_solo(self, track_index: int, solo: bool) -> Dict[str, Any]:
        pass

    @abstractmethod
    def set_tempo(self, tempo: float) -> Dict[str, Any]:
        pass

    @abstractmethod
    def add_notes_to_clip(self, track_index: int, clip_index: int, notes: List[Dict[str, Any]], mode: str = "create") -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_clip_notes(self, track_index: int, clip_index: int) -> List[Dict[str, Any]]:
        pass

    def fire_clip(self, track_index: int, clip_index: int) -> Dict[str, Any]:
        return {}

    def stop_clip(self, track_index: int, clip_index: int) -> Dict[str, Any]:
        return {}

    def start_playback(self) -> Dict[str, Any]:
        return {}

    def stop_playback(self) -> Dict[str, Any]:
        return {}
