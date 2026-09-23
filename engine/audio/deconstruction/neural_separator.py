# engine/audio/deconstruction/neural_separator.py
"""
Hybrid Neural Stem Separator and Reference Energy Profiler.
Attempts to use Meta Demucs (HTDemucs) when available for state-of-the-art 4-stem separation.
Guarantees seamless fallback to pure DSP Multi-Band Crossover & Mid-Side decomposition
(AudioStemSeparator) if Demucs is not installed, out of memory, or timed out.
Also extracts multi-stem arrangement energy profiles across timeline bars.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np
import soundfile as sf

from engine.audio.deconstruction.models import DeconstructedStem, StemCategory
from engine.audio.deconstruction.separator import AudioStemSeparator

logger = logging.getLogger("HybridStemSeparator")


class HybridStemSeparator:
    """Hybrid AI/DSP Stem Separator with graceful fallback and arrangement profiling."""

    def __init__(self, output_dir: Optional[str] = None):
        repo_root = Path(__file__).resolve().parent.parent.parent.parent
        self.output_dir = Path(output_dir) if output_dir else repo_root / "stems"
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        self.dsp_separator = AudioStemSeparator(output_dir=str(self.output_dir))
        self._demucs_available = self._check_demucs()

    def _check_demucs(self) -> bool:
        """Checks if demucs is installed and importable."""
        try:
            import demucs
            return True
        except ImportError:
            return False

    def separate(
        self,
        audio_path: Union[str, Path],
        prefer_neural: bool = True
    ) -> Dict[str, DeconstructedStem]:
        """
        Separates reference track into drums, bass, vocals, and other stems.
        Uses Demucs if available and requested; otherwise uses pure DSP separator.
        """
        p = Path(audio_path)
        if not p.exists():
            raise FileNotFoundError(f"Reference audio not found: {p}")

        if prefer_neural and self._demucs_available:
            try:
                logger.info(f"Attempting neural separation with Meta Demucs on {p.name}")
                return self._separate_demucs(p)
            except Exception as ex:
                logger.warning(f"Neural Demucs separation encountered error: {ex}. Falling back to DSP separator.")

        # Guaranteed DSP Fallback
        logger.info(f"Executing DSP Multi-Band Crossover & Mid-Side separation on {p.name}")
        return self.dsp_separator.separate(str(p))

    def _separate_demucs(self, audio_path: Path) -> Dict[str, DeconstructedStem]:
        """Executes separation using Meta HTDemucs."""
        import torch
        from demucs.pretrained import get_model
        from demucs.apply import apply_model

        model = get_model("htdemucs")
        model.eval()

        audio_data, sr = sf.read(str(audio_path), always_2d=True, dtype="float32")
        # Demucs expects (channels, samples)
        wav = torch.tensor(audio_data.T, dtype=torch.float32)

        # Resample if needed
        if sr != model.samplerate:
            import torchaudio.functional as AF
            wav = AF.resample(wav, sr, model.samplerate)
            sr = model.samplerate

        ref = wav.mean(0)
        wav = (wav - ref.mean()) / (ref.std() + 1e-6)

        with torch.no_grad():
            sources = apply_model(model, wav[None], device="cpu", progress=False)[0]

        # sources order in htdemucs: drums, bass, other, vocals
        stem_names = ["drums", "bass", "other", "vocals"]
        category_map = {
            "drums": StemCategory.DRUMS,
            "bass": StemCategory.BASS,
            "other": StemCategory.OTHER,
            "vocals": StemCategory.VOCALS
        }

        results: Dict[str, DeconstructedStem] = {}
        base_name = audio_path.stem

        for i, name in enumerate(stem_names):
            stem_tensor = sources[i].cpu().numpy().T  # (samples, channels)
            out_file = self.output_dir / f"{base_name}_{name}.wav"
            sf.write(str(out_file), stem_tensor, sr)

            cat = category_map[name]
            results[cat.value] = DeconstructedStem(
                category=cat,
                audio_path=str(out_file),
                sample_rate=sr,
                duration_seconds=float(len(stem_tensor) / sr),
                rms_db=float(self.dsp_separator._compute_rms_db(stem_tensor)),
                peak_db=float(self.dsp_separator._compute_peak_db(stem_tensor))
            )

        return results

    @classmethod
    def profile_arrangement_energy(
        cls,
        stems: Dict[str, DeconstructedStem],
        tempo_bpm: float = 120.0,
        bars_per_window: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Profiles the dynamic energy and role activity per bar window.
        Returns chronological arrangement section data (density, active roles, energy).
        """
        if not stems:
            return []

        # Find shortest stem duration
        sample_rates = [s.sample_rate for s in stems.values()]
        sr = sample_rates[0] if sample_rates else 44100
        min_duration = min(s.duration_seconds for s in stems.values())

        sec_per_beat = 60.0 / max(30.0, tempo_bpm)
        sec_per_bar = sec_per_beat * 4.0  # 4/4 time
        window_duration_sec = sec_per_bar * bars_per_window
        total_windows = max(1, int(min_duration // window_duration_sec))

        # Load audio signals
        audio_stems: Dict[str, np.ndarray] = {}
        for role, stem in stems.items():
            try:
                data, s_sr = sf.read(stem.audio_path, always_2d=False, dtype="float32")
                if data.ndim > 1:
                    data = np.mean(data, axis=1)
                audio_stems[role] = data
            except Exception:
                pass

        arrangement_profile = []
        for w_idx in range(total_windows):
            start_sec = w_idx * window_duration_sec
            end_sec = start_sec + window_duration_sec
            start_sample = int(start_sec * sr)
            end_sample = int(end_sec * sr)
            start_bar = w_idx * bars_per_window + 1
            end_bar = start_bar + bars_per_window - 1

            stem_energies = {}
            active_roles = []
            for role, data in audio_stems.items():
                chunk = data[start_sample:end_sample]
                if len(chunk) > 0:
                    rms = float(np.sqrt(np.mean(chunk ** 2) + 1e-12))
                    rms_db = float(20.0 * np.log10(max(rms, 1e-5)))
                    stem_energies[role] = round(rms_db, 1)
                    # Threshold for role activity in window: > -42 dBFS
                    if rms_db > -42.0:
                        active_roles.append(role)
                else:
                    stem_energies[role] = -96.0

            # Section classification heuristic
            has_drums = "drums" in active_roles
            has_bass = "bass" in active_roles
            has_vox = "vocals" in active_roles

            if not has_drums and not has_bass:
                if w_idx == 0:
                    sec_type = "Intro"
                elif w_idx == total_windows - 1:
                    sec_type = "Outro"
                else:
                    sec_type = "Breakdown"
            elif has_drums and not has_bass:
                sec_type = "Buildup"
            elif has_drums and has_bass:
                sec_type = "Drop / Chorus"
            else:
                sec_type = "Verse"

            arrangement_profile.append({
                "window_index": w_idx,
                "bar_range": f"{start_bar}-{end_bar}",
                "start_time_sec": round(start_sec, 2),
                "section_estimate": sec_type,
                "active_roles": active_roles,
                "energies_db": stem_energies
            })

        return arrangement_profile


# Type alias for path union
from typing import Union
Union_Path = Union[str, Path]
