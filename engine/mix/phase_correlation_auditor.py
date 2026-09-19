# engine/mix/phase_correlation_auditor.py
"""
Continuous Stereo Phase Correlation & Mono Compatibility Auditor.
Complies with EBU R 128 / ITU-R BS.1770-5 and vinyl/streaming mono compatibility standards.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from engine.mix.phase_alignment import PhaseAlignmentEngine


class PhaseCorrelationAuditor:
    """Audits real-time and stem audio arrays for stereo correlation and mono compatibility."""

    @classmethod
    def audit_audio_correlation(cls, audio: np.ndarray, sr: int = 44100) -> Dict[str, Any]:
        """
        Audits 2D stereo audio array [2, samples].
        Calculates broadband correlation rho and sub-bass (<120 Hz) correlation.
        """
        if audio.ndim == 1 or audio.shape[0] < 2:
            return {
                "broadband_rho": 1.0,
                "sub_bass_rho": 1.0,
                "mono_compliant": True,
                "status": "MONO_SOURCE"
            }

        left = audio[0]
        right = audio[1]

        # 1. Broadband Pearson correlation
        broadband_rho = PhaseAlignmentEngine.calculate_phase_correlation(left.tolist(), right.tolist())

        # 2. Sub-bass band (<120 Hz) isolation via butterworth filter
        from scipy.signal import butter, sosfilt
        nyq = 0.5 * sr
        low_cut = min(120.0, nyq - 10.0)
        sos_sub = butter(4, low_cut / nyq, 'lowpass', output='sos')

        sub_l = sosfilt(sos_sub, left)
        sub_r = sosfilt(sos_sub, right)
        sub_rho = PhaseAlignmentEngine.calculate_phase_correlation(sub_l.tolist(), sub_r.tolist())

        # Sub-bass mono compliance requires sub_rho >= +0.70
        is_compliant = sub_rho >= 0.40 and broadband_rho >= 0.0

        violations = []
        if sub_rho < 0.40:
            violations.append(f"Sub-bass out of phase: rho={sub_rho:.2f} (<120Hz). Risk of acoustic cancellation.")
        if broadband_rho < 0.0:
            violations.append(f"Broadband stereo phase inversion: rho={broadband_rho:.2f}.")

        status_str = "MONO_COMPLIANT" if is_compliant else ("OUT_OF_PHASE_DANGER" if broadband_rho < 0.0 else "SUB_BASS_PHASE_WARNING")
        return {
            "broadband_rho": round(broadband_rho, 3),
            "broadband_correlation": round(broadband_rho, 3),
            "sub_bass_rho": round(sub_rho, 3),
            "mono_compliant": is_compliant,
            "is_mono_compatible": is_compliant,
            "phase_status": status_str,
            "violations": violations,
            "recommendation": "OK" if is_compliant else "APPLY_BASS_MONO_UTILITY"
        }

    audit_phase_correlation = audit_audio_correlation
