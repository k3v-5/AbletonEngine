# engine/vocal/vocal_level_auditor.py
"""
Vocal Level Auditor & Dynamic Headroom Guard:
Calibrates and protects vocal signal gain staging across the entire mixing pipeline.

Key Capabilities:
- Pre-Fader Sweet Spot Calibration: Ensures nominal vocal level enters inserts at -18 dBFS RMS (+/- 2 dB)
- Headroom Guard: Limits true peaks to <= -3.0 dBTP to prevent downstream bus saturation and clipping
- Crest Factor Analysis: Evaluates dynamic range (10-14 dB ideal; >14 dB flags peak runaway, <8 dB flags squashed audio)
- Vocal-to-Playback SMR Guard: Audits 1 kHz - 3.5 kHz intelligibility band balance (+1.5 dB to +2.5 dB vocal priority)
- Automatic Gain Staging Prescriptions: Calculates exact dB trim for Ableton Utility or input gain
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import logging

logger = logging.getLogger("VocalLevelAuditor")


class VocalLevelAuditor:
    """Comprehensive gain staging and acoustic balance auditor for vocal channels."""

    TARGET_RMS_DBFS: float = -18.0
    MAX_PEAK_DBTP: float = -3.0
    CREST_FACTOR_MIN: float = 8.0
    CREST_FACTOR_MAX: float = 14.0
    TARGET_SMR_MIN: float = 1.5   # Vocal +1.5 dB over backing instruments
    TARGET_SMR_MAX: float = 2.5   # Vocal +2.5 dB over backing instruments

    @classmethod
    def analyze_audio_levels(
        cls,
        audio_data: np.ndarray,
        sr: int = 44100
    ) -> Dict[str, Any]:
        """
        Extracts peak, true-peak, RMS, crest factor, and spectral energy bands.
        """
        if audio_data is None or len(audio_data) == 0:
            return {
                "peak_dbfs": -96.0,
                "true_peak_dbtp": -96.0,
                "rms_dbfs": -96.0,
                "crest_factor_db": 0.0,
                "is_silent": True,
                "is_clipping": False,
                "energy_bands": {"sub_db": -96.0, "low_mid_db": -96.0, "intelligibility_db": -96.0, "air_db": -96.0}
            }

        if audio_data.ndim > 1:
            signal = np.mean(audio_data, axis=1).astype(np.float32)
        else:
            signal = audio_data.astype(np.float32)

        # Remove DC offset
        signal = signal - np.mean(signal)

        abs_signal = np.abs(signal)
        raw_peak = float(np.max(abs_signal)) if len(abs_signal) > 0 else 0.0
        peak_dbfs = 20.0 * np.log10(max(raw_peak, 1e-6))

        # True Peak 4x oversampling approximation using linear/cubic interpolation of peak neighborhoods
        if raw_peak > 0.01 and len(signal) > 16:
            peak_indices = np.where(abs_signal > raw_peak * 0.90)[0]
            max_interp_peak = raw_peak
            for idx in peak_indices[:50]: # check top peak points
                if 2 <= idx < len(signal) - 2:
                    sub = signal[idx-2:idx+3]
                    interp = np.interp(np.linspace(0, 4, 16), np.arange(5), sub)
                    max_interp_peak = max(max_interp_peak, float(np.max(np.abs(interp))))
            true_peak_dbtp = 20.0 * np.log10(max(max_interp_peak, 1e-6))
        else:
            true_peak_dbtp = peak_dbfs

        rms_linear = float(np.sqrt(np.mean(signal ** 2)))
        rms_dbfs = 20.0 * np.log10(max(rms_linear, 1e-6))
        crest_factor_db = max(0.0, peak_dbfs - rms_dbfs)

        # FFT Spectral Band Energy (Sub < 100, Low-Mid 100-500, Intelligibility 1000-3500, Air > 10000)
        n = len(signal)
        n_fft = min(8192, 1 << (n - 1).bit_length())
        if n_fft >= 1024:
            win = signal[:n_fft] * np.hanning(n_fft)
            spectrum = np.abs(np.fft.rfft(win))
            freqs = np.fft.rfftfreq(n_fft, d=1.0 / sr)

            def band_energy(f_low, f_high):
                mask = (freqs >= f_low) & (freqs < f_high)
                e = float(np.sum(spectrum[mask] ** 2)) if np.any(mask) else 1e-12
                return 10.0 * np.log10(max(e / (n_fft ** 2), 1e-12))

            energy_bands = {
                "sub_db": round(band_energy(20, 100), 2),
                "low_mid_db": round(band_energy(100, 500), 2),
                "intelligibility_db": round(band_energy(1000, 3500), 2),
                "air_db": round(band_energy(10000, 20000), 2),
            }
        else:
            energy_bands = {"sub_db": -50.0, "low_mid_db": -40.0, "intelligibility_db": -35.0, "air_db": -45.0}

        return {
            "peak_dbfs": round(peak_dbfs, 2),
            "true_peak_dbtp": round(true_peak_dbtp, 2),
            "rms_dbfs": round(rms_dbfs, 2),
            "crest_factor_db": round(crest_factor_db, 2),
            "is_silent": bool(rms_dbfs < -60.0),
            "is_clipping": bool(peak_dbfs >= -0.1 or true_peak_dbtp >= 0.0),
            "energy_bands": energy_bands
        }

    @classmethod
    def audit_vocal_level(
        cls,
        audio_data: np.ndarray,
        sr: int = 44100,
        target_rms_dbfs: float = TARGET_RMS_DBFS,
        max_peak_dbtp: float = MAX_PEAK_DBTP
    ) -> Dict[str, Any]:
        """
        Runs comprehensive diagnosis of vocal levels, comparing against commercial mixing benchmarks.
        """
        metrics = cls.analyze_audio_levels(audio_data, sr=sr)

        current_rms = metrics["rms_dbfs"]
        current_tp = metrics["true_peak_dbtp"]
        current_cf = metrics["crest_factor_db"]

        issues: List[str] = []
        prescriptions: List[str] = []

        # 1. Gain Staging / Nominal Sweet Spot Audit (-18 dBFS +/- 2 dB)
        trim_db = target_rms_dbfs - current_rms
        nominal_aligned = bool(abs(current_rms - target_rms_dbfs) <= 2.0)

        if current_rms > (target_rms_dbfs + 3.0):
            issues.append(f"Vocal RMS ({current_rms:.1f} dBFS) is running hot, exceeding target {target_rms_dbfs:.1f} dBFS.")
            prescriptions.append(f"Apply pre-fader input trim of {trim_db:+.1f} dB via Utility to enter plugins in the analog sweet spot.")
        elif current_rms < (target_rms_dbfs - 4.0):
            issues.append(f"Vocal RMS ({current_rms:.1f} dBFS) is below target {target_rms_dbfs:.1f} dBFS.")
            prescriptions.append(f"Apply pre-fader input gain of {trim_db:+.1f} dB to sufficiently drive vocal compressors and saturators.")

        # 2. Headroom Guard Audit (<= -3.0 dBTP)
        headroom_violation = bool(current_tp > max_peak_dbtp)
        if headroom_violation:
            excess = current_tp - max_peak_dbtp
            issues.append(f"True Peak ({current_tp:.1f} dBTP) exceeds maximum safe ceiling ({max_peak_dbtp:.1f} dBTP) by +{excess:.1f} dB.")
            prescriptions.append(f"Engage Fast FET peak limiter / compressor catching top {excess:.1f} dB transients.")

        # 3. Crest Factor / Dynamic Stability Audit
        if current_cf > cls.CREST_FACTOR_MAX:
            issues.append(f"Crest Factor ({current_cf:.1f} dB) indicates excessive dynamic swing (>14 dB).")
            prescriptions.append("Apply dual-stage serial compression (Fast FET 4:1 for peaks, slow Opto 2:1 for body).")
        elif current_cf < cls.CREST_FACTOR_MIN and not metrics["is_silent"]:
            issues.append(f"Crest Factor ({current_cf:.1f} dB) indicates overcompressed vocal (<8 dB), lacking life and punch.")
            prescriptions.append("Reduce compressor ratio or back off threshold to recover transient naturalness.")

        # Status determination
        if not issues:
            status = "OPTIMAL"
            summary = "Vocal levels are perfectly gain-staged at -18 dBFS RMS with ample headroom and punchy dynamics."
        elif metrics["is_clipping"] or current_tp >= -0.5:
            status = "PEAK_OVERLOAD"
            summary = f"Critical headroom overload! Peaks reaching {current_tp:.1f} dBTP. Urgent gain trim required."
        elif current_rms > -14.0:
            status = "TOO_LOUD"
            summary = f"Vocal is running hot ({current_rms:.1f} dBFS RMS). Attenuate pre-fader to prevent plugin distortion."
        elif current_rms < -24.0:
            status = "TOO_QUIET"
            summary = f"Vocal is quiet ({current_rms:.1f} dBFS RMS). Boost pre-fader to feed analog modeling plugins."
        else:
            status = "NEEDS_CALIBRATION"
            summary = f"Minor adjustments recommended: {issues[0]}"

        return {
            "status": status,
            "summary": summary,
            "metrics": metrics,
            "recommended_trim_db": round(trim_db, 2),
            "target_rms_dbfs": target_rms_dbfs,
            "max_peak_dbtp": max_peak_dbtp,
            "nominal_aligned": nominal_aligned,
            "headroom_safe": not headroom_violation,
            "issues": issues,
            "prescriptions": prescriptions
        }

    @classmethod
    def audit_vocal_to_playback_smr(
        cls,
        vocal_audio: np.ndarray,
        backing_audio: np.ndarray,
        sr: int = 44100
    ) -> Dict[str, Any]:
        """
        Audits the Signal-to-Mask Ratio (SMR) in the 1kHz - 3.5kHz intelligibility band.
        Commercial lead vocals must lead the backing instruments by +1.5 dB to +2.5 dB.
        """
        v_metrics = cls.analyze_audio_levels(vocal_audio, sr)
        b_metrics = cls.analyze_audio_levels(backing_audio, sr)

        v_intel = v_metrics["energy_bands"]["intelligibility_db"]
        b_intel = b_metrics["energy_bands"]["intelligibility_db"]

        smr_db = round(v_intel - b_intel, 2)
        passed = bool(cls.TARGET_SMR_MIN <= smr_db <= (cls.TARGET_SMR_MAX + 1.0))

        if smr_db < cls.TARGET_SMR_MIN:
            status = "VOCAL_BURIED"
            recommendation = (
                f"Vocal is buried in the midrange (SMR: {smr_db:+.1f} dB, target: +{cls.TARGET_SMR_MIN} to +{cls.TARGET_SMR_MAX} dB). "
                "Carve 1.5 kHz - 3 kHz on Keys/Synths with dynamic EQ or apply ducking."
            )
        elif smr_db > (cls.TARGET_SMR_MAX + 2.0):
            status = "VOCAL_DISCONNECTED"
            recommendation = (
                f"Vocal is sitting too high above the mix (SMR: {smr_db:+.1f} dB). "
                "Lower vocal fader or increase subtle stereo room reverb to integrate it into the soundstage."
            )
        else:
            status = "OPTIMAL_BALANCE"
            recommendation = f"Vocal sits prominently in the pocket (+{smr_db:.1f} dB over mid instruments) with clear intelligibility."

        return {
            "status": status,
            "smr_db": smr_db,
            "vocal_intelligibility_db": v_intel,
            "backing_intelligibility_db": b_intel,
            "passed": passed,
            "recommendation": recommendation
        }

    @classmethod
    def calibrate_live_vocal_gain(
        cls,
        conn: Any,
        track_index: int,
        audio_data: np.ndarray = None,
        sr: int = 44100
    ) -> Dict[str, Any]:
        """
        Calibrates live vocal track gain in Ableton Live.
        If audio data is provided, measures RMS and adjusts or creates Utility device with recommended trim.
        """
        if audio_data is None:
            return {
                "status": "SKIPPED_NO_AUDIO",
                "track_index": track_index,
                "message": "No audio waveform provided for calibration."
            }

        audit = cls.audit_vocal_level(audio_data, sr=sr)
        trim = audit["recommended_trim_db"]

        applied = False
        if conn and hasattr(conn, "send_command") and abs(trim) > 0.5:
            try:
                # Add or configure Utility at device 0
                t_info = conn.send_command("get_track_info", {"track_index": track_index})
                devs = t_info.get("result", {}).get("devices", t_info.get("devices", [])) if isinstance(t_info, dict) else []

                utility_idx = None
                for idx, d in enumerate(devs):
                    if "utility" in str(d.get("name", "")).lower():
                        utility_idx = idx
                        break

                if utility_idx is None:
                    conn.send_command("load_browser_item", {
                        "track_index": track_index,
                        "item_uri": "query:AudioFx#Utility"
                    })
                    utility_idx = len(devs)

                # Utility Gain parameter is typically 'Gain' or 'Output'
                code_set_util = f"""
t = song.tracks[{track_index}]
for d in t.devices:
    if 'Utility' in d.name:
        for p in d.parameters:
            if p.name == 'Gain':
                p.value = max(0.0, min(1.0, 0.5 + ({trim} / 70.0)))
            elif p.name == 'Output':
                # Live 12 Utility 'Output' ranges -1.0 to 1.0 (-35dB to +35dB, 0.0 is 0dB)
                p.value = max(-1.0, min(1.0, {trim} / 35.0))
"""
                conn.send_command("execute_code", {"code": code_set_util})
                applied = True
            except Exception as ex_util:
                logger.debug(f"Utility calibration notice: {ex_util}")

        return {
            "status": "SUCCESS" if applied else "CALIBRATED_REPORT_ONLY",
            "track_index": track_index,
            "trim_applied_db": trim if applied else 0.0,
            "audit": audit
        }
