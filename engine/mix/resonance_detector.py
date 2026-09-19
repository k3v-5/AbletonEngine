# engine/mix/resonance_detector.py
"""
Closed-Loop Resonance Detector & Spectral Ear:
Performs high-resolution FFT spectral analysis to detect narrow-band harsh resonant peaks
(piercing metallic growls, boxy mud, harsh vocal sibilance) and calculates surgical EQ Eight notches.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import logging

logger = logging.getLogger("ResonanceDetector")


class ResonanceDetector:
    """Detects sharp acoustic resonances and generates surgical notch filter parameters."""

    ZONE_DEFINITIONS = {
        "LOW_RUMBLE": (20.0, 100.0),
        "MUD_BOX": (200.0, 500.0),
        "NASAL_MID": (800.0, 1800.0),
        "HARSH_MID": (2500.0, 4800.0),
        "PIERCING_HIGHS": (6000.0, 9500.0)
    }

    @classmethod
    def classify_frequency_zone(cls, freq_hz: float) -> str:
        """Determines the perceptual acoustic zone of a frequency peak."""
        for zone, (f_low, f_high) in cls.ZONE_DEFINITIONS.items():
            if f_low <= freq_hz <= f_high:
                return zone
        return "OTHER"

    @classmethod
    def analyze_spectrum_resonances(
        cls,
        audio_data: np.ndarray,
        sr: int = 44100,
        threshold_db: float = 3.5,
        min_q: float = 5.0,
        max_peaks: int = 5
    ) -> Dict[str, Any]:
        """
        Scans audio buffer and detects narrow-band frequency spikes exceeding local spectrum.
        """
        if audio_data is None or len(audio_data) == 0:
            return {"status": "NO_AUDIO", "resonances_count": 0, "resonances": []}

        # Convert to mono if stereo
        if audio_data.ndim == 2:
            mono = np.mean(audio_data, axis=0) if audio_data.shape[0] < audio_data.shape[1] else np.mean(audio_data, axis=1)
        else:
            mono = audio_data

        if len(mono) < 1024:
            return {"status": "BUFFER_TOO_SHORT", "resonances_count": 0, "resonances": []}

        # FFT Analysis
        n_fft = min(8192, 2 ** int(np.floor(np.log2(len(mono)))))
        windowed = mono[:n_fft] * np.hanning(n_fft)
        fft_vals = np.abs(np.fft.rfft(windowed))
        freqs = np.fft.rfftfreq(n_fft, d=1.0 / sr)

        # Convert to dB magnitude
        mag_db = 20.0 * np.log10(np.maximum(fft_vals, 1e-7))

        # Calculate smoothed spectral baseline via moving average filter
        kernel_size = max(5, int(n_fft / 128))
        kernel = np.ones(kernel_size) / kernel_size
        smooth_mag = np.convolve(mag_db, kernel, mode="same")

        # Spectral prominence delta
        prominence = mag_db - smooth_mag

        detected_resonances: List[Dict[str, Any]] = []

        # Scan for local maxima where prominence >= threshold_db and freq in audible range [150 Hz .. 14 kHz]
        for i in range(2, len(prominence) - 2):
            freq = float(freqs[i])
            if freq < 150.0 or freq > 14000.0:
                continue

            # Local peak condition
            if prominence[i] > threshold_db and prominence[i] > prominence[i - 1] and prominence[i] > prominence[i + 1]:
                peak_prom = float(prominence[i])

                # Estimate bandwidth / Q factor: find -3dB points relative to peak
                half_prom = peak_prom - 3.0
                i_left = i
                while i_left > 1 and prominence[i_left] > half_prom:
                    i_left -= 1
                i_right = i
                while i_right < len(prominence) - 2 and prominence[i_right] > half_prom:
                    i_right += 1

                bw_hz = max(10.0, float(freqs[i_right] - freqs[i_left]))
                q_est = round(freq / bw_hz, 2)

                if q_est >= min_q:
                    zone = cls.classify_frequency_zone(freq)
                    notch_cut = -round(min(6.0, peak_prom * 0.9), 1)

                    detected_resonances.append({
                        "frequency_hz": round(freq, 1),
                        "prominence_db": round(peak_prom, 2),
                        "estimated_q": q_est,
                        "zone": zone,
                        "recommended_notch": {
                            "filter_type": "NOTCH",
                            "frequency": round(freq, 1),
                            "gain_db": notch_cut,
                            "q": max(4.0, min(14.0, q_est))
                        }
                    })

        # Sort by prominence and limit
        detected_resonances.sort(key=lambda r: r["prominence_db"], reverse=True)
        top_resonances = detected_resonances[:max_peaks]

        logger.info(f"Resonance analysis complete: {len(top_resonances)} harsh peaks identified.")
        return {
            "status": "RESONANCES_DETECTED" if top_resonances else "SPECTRUM_CLEAN",
            "resonances_count": len(top_resonances),
            "resonances": top_resonances,
            "has_harsh_peaks": len(top_resonances) > 0
        }

    @classmethod
    def analyze_temporal_ringing(
        cls,
        audio_data: np.ndarray,
        sr: int = 44100,
        min_decay_time_ms: float = 300.0,
        max_peaks: int = 4
    ) -> Dict[str, Any]:
        """
        Punto 20: Temporal Decay (T60) Resonance Buster.
        Distinguishes static tonal balance from true ringing acoustic resonances.
        Measures the persistence of narrow-band energy across consecutive time slices.
        Resonances with T60 > 300ms are flagged as physical/room ringing.
        """
        if audio_data is None or len(audio_data) < int(sr * 0.4):
            return {"status": "BUFFER_TOO_SHORT", "ringing_resonances_count": 0, "ringing_peaks": []}

        mono = np.mean(audio_data, axis=0) if audio_data.ndim == 2 else audio_data

        # Window parameters for STFT
        win_size = min(4096, 2 ** int(np.floor(np.log2(len(mono) // 4))))
        if win_size < 1024:
            win_size = 1024
        hop_size = win_size // 2

        num_frames = (len(mono) - win_size) // hop_size
        if num_frames < 3:
            return {"status": "NOT_ENOUGH_FRAMES", "ringing_resonances_count": 0, "ringing_peaks": []}

        spectrogram = []
        for f_idx in range(num_frames):
            frame = mono[f_idx * hop_size : f_idx * hop_size + win_size] * np.hanning(win_size)
            mag = np.abs(np.fft.rfft(frame))
            mag_db = 20.0 * np.log10(np.maximum(mag, 1e-8))
            spectrogram.append(mag_db)

        spectrogram = np.array(spectrogram)  # shape: (num_frames, num_bins)
        freqs = np.fft.rfftfreq(win_size, d=1.0 / sr)
        frame_time_sec = hop_size / sr

        ringing_peaks: List[Dict[str, Any]] = []

        # Analyze persistence for each audible bin
        for b_idx in range(2, len(freqs) - 2):
            freq = float(freqs[b_idx])
            if freq < 180.0 or freq > 11000.0:
                continue

            bin_energy = spectrogram[:, b_idx]
            max_idx = np.argmax(bin_energy)
            peak_energy = bin_energy[max_idx]

            # Only analyze if peak has sufficient volume
            if peak_energy < -45.0:
                continue

            # Check post-peak decay
            tail = bin_energy[max_idx:]
            if len(tail) < 3:
                continue

            # Linear regression on decay tail: energy = slope * time + c
            t_axis = np.arange(len(tail)) * frame_time_sec
            try:
                slope, _ = np.polyfit(t_axis, tail, 1)
            except Exception:
                slope = 0.0

            # True ringing has very shallow or flat decay slope (decays slower than -20 dB/sec)
            # T60 = -60 / slope
            if -35.0 < slope < -0.5:
                t60_sec = round(-60.0 / slope, 3)
                t60_ms = t60_sec * 1000.0

                if t60_ms >= min_decay_time_ms:
                    # Compare to neighborhood bins to ensure it's a narrow resonance, not broad swell
                    local_avg = np.mean([spectrogram[max_idx, b_idx - 2], spectrogram[max_idx, b_idx + 2]])
                    prominence = peak_energy - local_avg
                    if prominence >= 2.5:
                        ringing_peaks.append({
                            "frequency_hz": round(freq, 1),
                            "t60_decay_ms": round(t60_ms, 1),
                            "prominence_db": round(float(prominence), 2),
                            "decay_slope_db_per_sec": round(float(slope), 2),
                            "recommended_notch": {
                                "filter_type": "NOTCH",
                                "frequency": round(freq, 1),
                                "gain_db": -round(min(5.5, max(2.0, prominence * 0.8)), 1),
                                "q": 8.0
                            }
                        })

        # Deduplicate close frequencies (within 5%)
        deduped = []
        ringing_peaks.sort(key=lambda p: p["t60_decay_ms"], reverse=True)
        for p in ringing_peaks:
            if not any(abs(p["frequency_hz"] - d["frequency_hz"]) / p["frequency_hz"] < 0.05 for d in deduped):
                deduped.append(p)

        top_ringing = deduped[:max_peaks]

        return {
            "status": "RINGING_DETECTED" if top_ringing else "DECAY_CLEAN",
            "ringing_resonances_count": len(top_ringing),
            "ringing_peaks": top_ringing,
            "has_ringing": len(top_ringing) > 0
        }

    @classmethod
    def clean_low_mid_resonances(
        cls,
        conn: Any,
        tracks: List[Dict[str, Any]],
        audio_data: Optional[np.ndarray] = None,
        sr: int = 44100,
        target_center_freq: float = 441.4,
        cut_db: float = -3.5,
        q: float = 12.0,
        master_track_index: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Post-vocal surgical resonance cleaning:
        Targets the low-mid 'Mud Box' (200 Hz - 500 Hz), specifically eradicating
        the narrow 441.4 Hz boxy resonance on harmonic instrument tracks (Keys, Pad, Brass)
        and configuring Band 3 notch/bell cut on the Master EQ Eight.
        """
        import math

        F_MIN = 10.0
        F_MAX = 22000.0
        LOG_RANGE = math.log10(F_MAX / F_MIN)
        clamped = max(F_MIN, min(F_MAX, target_center_freq))
        norm_freq = round(math.log10(clamped / F_MIN) / LOG_RANGE, 6)

        detected_peak = target_center_freq
        if audio_data is not None and len(audio_data) > 1024:
            res_analysis = cls.analyze_spectrum_resonances(audio_data, sr=sr, threshold_db=2.5)
            mud_peaks = [r for r in res_analysis.get("resonances", []) if r.get("zone") == "MUD_BOX"]
            if mud_peaks:
                detected_peak = mud_peaks[0]["frequency_hz"]
                clamped = max(F_MIN, min(F_MAX, detected_peak))
                norm_freq = round(math.log10(clamped / F_MIN) / LOG_RANGE, 6)

        actions = []
        applied_tracks = []
        harmonic_roles = ("KEYS", "PAD", "BRASS", "SYNTH", "LEAD", "OTHER")

        for trk in tracks:
            r = str(trk.get("role", "")).upper()
            t_name = str(trk.get("name", "")).lower()
            if r in harmonic_roles or any(w in t_name for w in ["key", "piano", "rhodes", "pad", "brass", "sax", "horn", "synth"]):
                t_idx = trk.get("index")
                if t_idx is not None:
                    applied_tracks.append({"index": t_idx, "name": trk.get("name", f"Track {t_idx}"), "role": r})
                    if conn is not None and hasattr(conn, "send_command"):
                        try:
                            t_info = conn.send_command("get_track_info", {"track_index": t_idx})
                            t_data = t_info.get("result", t_info) if isinstance(t_info, dict) else {}
                            devs = t_data.get("devices", [])
                            eq_idx = next((i for i, d in enumerate(devs) if "EQ" in d.get("name", "")), None)
                            if eq_idx is not None:
                                for p_idx, p_val in [
                                    (24, 1.0),
                                    (25, 3.0),
                                    (26, norm_freq),
                                    (27, float(cut_db)),
                                    (28, float(q / 20.0))
                                ]:
                                    conn.send_command("set_device_parameter", {
                                        "track_index": t_idx,
                                        "device_index": eq_idx,
                                        "parameter": p_idx,
                                        "parameter_index": p_idx,
                                        "value": p_val
                                    })
                                actions.append(f"Notch {detected_peak:.1f} Hz ({cut_db:.1f} dB, Q={q:.1f}) inyectado en EQ Eight de '{trk.get('name')}'")
                        except Exception as ex_t:
                            actions.append(f"Aviso en pista {t_idx}: {ex_t}")

        # Master EQ Eight Band 3
        m_idx = master_track_index if master_track_index is not None else 0
        if conn is not None and hasattr(conn, "send_command"):
            try:
                t_info = conn.send_command("get_track_info", {"track_index": m_idx})
                t_data = t_info.get("result", t_info) if isinstance(t_info, dict) else {}
                devs = t_data.get("devices", [])
                eq_idx = next((i for i, d in enumerate(devs) if "EQ" in d.get("name", "")), None)
                if eq_idx is not None:
                    for p_idx, p_val in [
                        (24, 1.0),
                        (25, 3.0),
                        (26, norm_freq),
                        (27, float(cut_db)),
                        (28, float(q / 20.0))
                    ]:
                        conn.send_command("set_device_parameter", {
                            "track_index": m_idx,
                            "device_index": eq_idx,
                            "parameter": p_idx,
                            "parameter_index": p_idx,
                            "value": p_val
                        })
                    actions.append(f"Master EQ Eight Band 3 configurado: Notch en {detected_peak:.1f} Hz ({cut_db:.1f} dB, Q={q:.1f})")
            except Exception as ex_m:
                actions.append(f"Aviso en Master EQ: {ex_m}")
        else:
            actions.append(f"Simulada limpieza de Mud Box en {detected_peak:.1f} Hz ({cut_db:.1f} dB, Q={q:.1f}) sobre {len(applied_tracks)} pistas armónicas")

        return {
            "status": "LOW_MID_RESONANCES_CLEANED",
            "zone": "MUD_BOX",
            "center_frequency_hz": detected_peak,
            "gain_cut_db": cut_db,
            "q_factor": q,
            "tracks_processed": applied_tracks,
            "actions": actions,
            "summary": f"Limpieza completada: Notch quirúrgico en {detected_peak:.1f} Hz ({cut_db:.1f} dB, Q={q:.1f}) aplicado tras la fase vocal."
        }


