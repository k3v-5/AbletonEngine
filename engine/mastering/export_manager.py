"""
Export Manager with SHA256 Hashing and Versioning.
Saves versioned masters (v001, v002) without destructive overwriting.
"""
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import numpy as np
import soundfile as sf

from .models import MasterHistoryEntry, DeliveryTarget


class MasterExportManager:
    """Manages audio file export, version numbering, and sample integrity hashing."""

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            self.export_dir = Path.home() / ".mcp_mastering"
        else:
            self.export_dir = Path(base_dir) / ".mcp_mastering"
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.history: List[MasterHistoryEntry] = []

    @staticmethod
    def compute_audio_hash(audio: np.ndarray) -> str:
        """Computes deterministic SHA256 hash of float32 sample data."""
        data_bytes = audio.astype(np.float32).tobytes()
        return hashlib.sha256(data_bytes).hexdigest()

    def get_next_version(self, project_name: str) -> str:
        existing = list(self.export_dir.glob(f"{project_name}_v*.wav"))
        next_num = len(existing) + 1
        return f"v{next_num:03d}"

    def export_master(
        self,
        delivery_target: Union[str, DeliveryTarget] = DeliveryTarget.STREAMING,
        file_format: str = "WAV",
        sample_rate: int = 44100,
        bit_depth: int = 24,
        destination_dir: Optional[str] = None,
        audio_data: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        target_name = delivery_target.value if isinstance(delivery_target, DeliveryTarget) else str(delivery_target)
        save_dir = Path(destination_dir) if destination_dir else self.export_dir
        save_dir.mkdir(parents=True, exist_ok=True)

        existing = list(save_dir.glob(f"Master_{target_name}_v*.wav"))
        version = f"v{len(existing) + 1:03d}"
        file_name = f"Master_{target_name}_{version}.wav"
        file_path = save_dir / file_name

        if audio_data is None:
            # Generate 2.0 second test tone if no live buffer
            t = np.linspace(0, 2.0, int(sample_rate * 2.0), endpoint=False)
            tone = 0.2 * np.sin(2 * np.pi * 440.0 * t)
            audio_data = np.stack([tone, tone], axis=0)

        if audio_data.ndim == 1:
            save_data = audio_data
        elif audio_data.shape[0] < audio_data.shape[1]:
            save_data = audio_data.T
        else:
            save_data = audio_data

        subtype = f"PCM_{bit_depth}" if bit_depth in [16, 24] else "FLOAT"
        sf.write(str(file_path), save_data, sample_rate, subtype=subtype)
        audio_hash = self.compute_audio_hash(audio_data)

        return {
            "status": "SUCCESS",
            "version": version,
            "file_name": file_name,
            "file_path": str(file_path),
            "sha256_hash": audio_hash,
            "delivery_target": target_name,
            "format": file_format,
            "sample_rate": sample_rate,
            "bit_depth": bit_depth
        }

    def export(self, audio: np.ndarray, sr: int, project_name: str = "Master",
               changes: Optional[List[str]] = None,
               score_before: float = 80.0, score_after: float = 88.0) -> Dict[str, Any]:
        res = self.export_master(
            delivery_target=DeliveryTarget.STREAMING,
            sample_rate=sr,
            destination_dir=str(self.export_dir),
            audio_data=audio
        )
        entry = MasterHistoryEntry(
            version=res["version"],
            timestamp=time.time(),
            input_hash="",
            output_hash=res["sha256_hash"],
            committed_changes=changes or [],
            score_before=score_before,
            score_after=score_after
        )
        self.history.append(entry)
        res["audio_hash"] = res["sha256_hash"]
        return res
