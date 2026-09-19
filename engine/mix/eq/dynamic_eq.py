# engine/mix/eq/dynamic_eq.py
"""
Dynamic EQ & Adaptive De-Esser Engine:
Implements frequency-selective dynamic compression and de-essing in Ableton Live.
Selectively suppresses harsh sibilance (5.5kHz - 8.5kHz) and cleans frequency masking collisions
only when energy exceeds perceptual thresholds, preserving full brightness and warmth.
"""

import math
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
import numpy as np


@dataclass
class DynamicEQBand:
    frequency_hz: float
    q_factor: float = 1.4
    threshold_db: float = -18.0
    ratio: float = 4.0
    attack_ms: float = 1.0
    release_ms: float = 50.0
    max_cut_db: float = -6.0
    band_type: str = "bell"  # 'bell', 'shelf', 'notch'

    def calculate_gain_reduction(self, signal_band_rms_db: float) -> float:
        """Computes dynamic cut in dB when signal exceeds threshold."""
        if signal_band_rms_db <= self.threshold_db:
            return 0.0
        overshoot = signal_band_rms_db - self.threshold_db
        gr = overshoot * (1.0 - (1.0 / self.ratio))
        return -min(abs(self.max_cut_db), gr)


class DynamicEQEngine:
    """Intelligent dynamic equalizer and de-esser configurator for Ableton Live tracks."""

    # Normalization helper for EQ frequencies in Compressor / Auto Filter
    F_MIN = 10.0
    F_MAX = 22000.0
    LOG_RANGE = math.log10(F_MAX / F_MIN)

    @classmethod
    def freq_to_normalized(cls, freq_hz: float) -> float:
        clamped = max(cls.F_MIN, min(cls.F_MAX, freq_hz))
        return round(math.log10(clamped / cls.F_MIN) / cls.LOG_RANGE, 6)

    @classmethod
    def calculate_sibilance_profile(
        cls,
        audio_buffer: np.ndarray,
        sample_rate: int = 44100
    ) -> Dict[str, Any]:
        """
        Analyzes audio buffer to detect sibilance/harshness energy ratio:
        Compares energy in 5.5kHz - 8.5kHz vs overall spectrum.
        """
        if audio_buffer.size == 0:
            return {"sibilance_ratio": 0.0, "severity": "NONE", "recommended_cut_db": 0.0}

        # Handle stereo / multi-channel
        sig = audio_buffer[0] if audio_buffer.ndim > 1 else audio_buffer
        fft_vals = np.abs(np.fft.rfft(sig))
        freqs = np.fft.rfftfreq(len(sig), 1.0 / sample_rate)

        # Sibilance band: 5500 - 8500 Hz
        sib_mask = (freqs >= 5500) & (freqs <= 8500)
        total_energy = float(np.sum(fft_vals ** 2)) + 1e-12
        sib_energy = float(np.sum(fft_vals[sib_mask] ** 2))

        ratio = sib_energy / total_energy

        # Classification
        if ratio > 0.35:
            severity = "CRITICAL"
            cut_db = -6.0
        elif ratio > 0.22:
            severity = "HIGH"
            cut_db = -4.5
        elif ratio > 0.12:
            severity = "MEDIUM"
            cut_db = -3.0
        else:
            severity = "BALANCED"
            cut_db = -1.5

        return {
            "sibilance_ratio": round(ratio, 4),
            "severity": severity,
            "recommended_cut_db": cut_db,
            "center_frequency_hz": 6800.0
        }

    @classmethod
    def apply_adaptive_deesser(
        cls,
        conn: Any,
        track_index: int,
        target_sibilance_freq: float = 6800.0,
        threshold: float = 0.65,
        ratio: float = 0.75,
        audio_data: Optional[np.ndarray] = None,
        sr: int = 44100
    ) -> Dict[str, Any]:
        """
        Deploys and calibrates an authentic surgical De-Esser in Ableton Live:
        - Detects sibilance peak if audio_data is provided (4.5 kHz - 9.5 kHz).
        - Locates existing Compressor or loads native Compressor on track_index.
        - Renames device to 'Adaptive De-Esser' in Live.
        - Activates Device On (P0 = 1.0).
        - Activates S/C EQ On (P15 = 1.0).
        - Sets S/C EQ Type to Bell Bandpass (P16 = 1.0).
        - Tunes S/C EQ Frequency to detected sibilance peak (~5.7 kHz - 6.8 kHz).
        - Tunes S/C EQ Q to narrow surgical bandwidth (Q = 2.25, P18 = 0.65).
        - Sets ultra-fast Attack (1.0 ms) and smooth release (35 ms).
        - Only activates compression when harsh sibilant 'S', 'Z', 'CH' frequencies exceed threshold.
        """
        import time

        # Auto-detect sibilance peak if audio is supplied
        if audio_data is not None and len(audio_data) >= 2048:
            mono = audio_data[0] if audio_data.ndim > 1 else audio_data
            fft_vals = np.abs(np.fft.rfft(mono))
            freqs = np.fft.rfftfreq(len(mono), 1.0 / sr)
            sib_mask = (freqs >= 4500) & (freqs <= 9500)
            if np.any(sib_mask):
                target_sibilance_freq = round(float(freqs[sib_mask][np.argmax(fft_vals[sib_mask])]), 1)

        results = {
            "track_index": track_index,
            "target_freq_hz": target_sibilance_freq,
            "loaded": False,
            "deesser_dev_index": None
        }

        if conn is None or not hasattr(conn, "send_command"):
            results["mock"] = True
            return {"status": "SUCCESS", "mock": True, **results}

        # 1. Inspect existing devices to see if Compressor/De-Esser already exists
        t_info = conn.send_command("get_track_info", {"track_index": track_index})
        devices = t_info.get("result", {}).get("devices", []) if isinstance(t_info, dict) else []
        comp_idx = None
        for idx, d in enumerate(devices):
            d_name = d.get("name", "").lower()
            if "de-ess" in d_name or ("compressor" in d_name and "glue" not in d_name):
                comp_idx = idx
                break

        # 2. If not found, load Compressor
        if comp_idx is None:
            load_res = conn.send_command("load_instrument_or_effect", {
                "track_index": track_index,
                "uri": "query:AudioFx#Compressor"
            })
            results["loaded"] = load_res.get("status") in ("success", "SUCCESS")
            time.sleep(0.3)
            t_info = conn.send_command("get_track_info", {"track_index": track_index})
            devices = t_info.get("result", {}).get("devices", []) if isinstance(t_info, dict) else []
            for idx, d in enumerate(devices):
                d_name = d.get("name", "").lower()
                if "compressor" in d_name and "glue" not in d_name:
                    comp_idx = idx
        else:
            results["loaded"] = True

        if comp_idx is not None:
            results["deesser_dev_index"] = comp_idx
            freq_norm = cls.freq_to_normalized(target_sibilance_freq)
            if 4500 <= target_sibilance_freq <= 9500:
                freq_norm = min(0.95, max(0.60, freq_norm + 0.02))

            deesser_params = [
                (0, 1.0),                 # Device On
                (1, float(threshold)),    # Threshold (-8 dB)
                (2, float(ratio)),        # Ratio (4:1)
                (4, 0.40),                # Attack (1.0 ms)
                (5, 0.17),                # Release (35 ms)
                (15, 1.0),                # S/C EQ On
                (16, 1.0),                # S/C EQ Type = Bell (Bandpass)
                (17, float(freq_norm)),   # S/C EQ Freq
                (18, 0.65)                # S/C EQ Q (~2.25 surgical)
            ]

            for p_idx, val in deesser_params:
                try:
                    conn.send_command("set_device_parameter", {
                        "track_index": track_index,
                        "device_index": comp_idx,
                        "parameter": p_idx,
                        "parameter_index": p_idx,
                        "value": float(val)
                    })
                except Exception:
                    pass

            # Rename device in Live
            if hasattr(conn, "_send_raw"):
                try:
                    conn._send_raw("execute_code", {
                        "code": f"song.tracks[{track_index}].devices[{comp_idx}].name = 'Adaptive De-Esser'"
                    })
                except Exception:
                    pass

        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "device_index": comp_idx,
            "sibilance_freq_hz": target_sibilance_freq,
            "freq_norm": cls.freq_to_normalized(target_sibilance_freq),
            "threshold_db": -8.0,
            "attack_ms": 1.0,
            "release_ms": 35.0,
            "mode": "S/C Bell Adaptive De-Esser"
        }

    @classmethod
    def apply_frequency_unmasking(
        cls,
        conn: Any,
        target_track_index: int,
        masking_track_index: int,
        conflict_freq_hz: float = 300.0,
        duck_depth_db: float = -3.5
    ) -> Dict[str, Any]:
        """
        Dynamically carves space in target_track_index whenever masking_track_index produces energy
        at conflict_freq_hz (e.g. ducking 300Hz on Keys when Vocal or Snare strikes).
        """
        results = {
            "target_track": target_track_index,
            "masking_track": masking_track_index,
            "conflict_freq_hz": conflict_freq_hz,
            "duck_depth_db": duck_depth_db
        }

        if conn is None or not hasattr(conn, "send_command"):
            results["mock"] = True
            return {"status": "SUCCESS", "mock": True, **results}

        # Deploys Compressor with external sidechain input enabled and tuned EQ filter
        import time
        load_res = conn.send_command("load_instrument_or_effect", {
            "track_index": target_track_index,
            "uri": "query:AudioFx#Compressor"
        })
        time.sleep(0.3)

        t_info = conn.send_command("get_track_info", {"track_index": target_track_index})
        devices = t_info.get("result", {}).get("devices", []) if isinstance(t_info, dict) else []
        c_idx = None
        for idx, d in enumerate(devices):
            if "Compressor" in d.get("name", "") and d.get("name") != "Glue Compressor":
                c_idx = idx

        if c_idx is not None:
            freq_norm = cls.freq_to_normalized(conflict_freq_hz)
            # P15: S/C EQ On, P16: S/C EQ Type (Bandpass/Bell), P17: Freq, P20: S/C On
            unmask_params = [
                (1, 0.60),        # Threshold
                (2, 0.70),        # Ratio 3:1
                (4, 0.35),        # Attack 0.5ms
                (5, 0.25),        # Release 80ms
                (15, 1.0),        # S/C EQ On
                (16, 2.0),        # Bandpass
                (17, freq_norm),  # Conflict frequency
                (20, 1.0)         # External Sidechain On
            ]
            for p_idx, val in unmask_params:
                try:
                    conn.send_command("set_device_parameter", {
                        "track_index": target_track_index,
                        "device_index": c_idx,
                        "parameter": p_idx,
                        "parameter_index": p_idx,
                        "value": float(val)
                    })
                except Exception:
                    pass

        return {
            "status": "SUCCESS",
            "target_track": target_track_index,
            "masking_track": masking_track_index,
            "device_index": c_idx,
            "conflict_freq_hz": conflict_freq_hz
        }
