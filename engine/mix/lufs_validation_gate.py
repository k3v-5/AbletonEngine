# engine/mix/lufs_validation_gate.py
"""
ITU-R BS.1770-5 LUFS & True Peak End-of-Chain Validation Gate:
Audits integrated loudness, short-term dynamic range, and inter-sample True Peak.
Enforces broadcast and streaming compliance (e.g. Spotify/Apple -14.0 LUFS / -1.0 dBTP),
and calculates automatic trim compensation to prevent digital summing overload and clipping.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple
import numpy as np

from .loudness_analyzer import LoudnessAnalyzer
from .loudness_standards import ProfileRegistry, LoudnessProfile


@dataclass
class LoudnessAuditResult:
    passed: bool
    integrated_lufs: float
    short_term_max_lufs: float
    momentary_max_lufs: float
    true_peak_dbtp: float
    target_lufs: float
    max_true_peak_dbtp: float
    lufs_deviation_db: float
    headroom_margin_db: float
    required_trim_db: float
    violations: list[str] = field(default_factory=list)
    certificate: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "integrated_lufs": round(self.integrated_lufs, 2),
            "short_term_max_lufs": round(self.short_term_max_lufs, 2),
            "momentary_max_lufs": round(self.momentary_max_lufs, 2),
            "true_peak_dbtp": round(self.true_peak_dbtp, 2),
            "target_lufs": round(self.target_lufs, 2),
            "max_true_peak_dbtp": round(self.max_true_peak_dbtp, 2),
            "lufs_deviation_db": round(self.lufs_deviation_db, 2),
            "headroom_margin_db": round(self.headroom_margin_db, 2),
            "required_trim_db": round(self.required_trim_db, 2),
            "violations": self.violations,
            "certificate": self.certificate,
        }


class LUFSValidationGate:
    """End-of-chain automated loudness and inter-sample peak compliance validator."""

    def __init__(self, profile: Optional[LoudnessProfile] = None):
        self.profile = profile or ProfileRegistry.STREAMING

    def audit(self, audio: np.ndarray, sr: int = 44100) -> LoudnessAuditResult:
        """
        Runs complete ITU-R BS.1770-5 and Annex 2 True Peak analysis on audio array.
        Audio shape: (channels, samples) or (samples,).
        """
        if audio.ndim == 1:
            audio = np.expand_dims(audio, axis=0)

        # 1. Acoustic measurements
        int_lufs, st_lufs, mom_lufs, _, _ = LoudnessAnalyzer.calculate_lufs_with_blocks(audio, sr)
        tp_dbtp = LoudnessAnalyzer.calculate_true_peak(audio)

        target_lufs = self.profile.integrated_target
        max_tp = self.profile.max_true_peak
        tolerance = self.profile.integrated_tolerance

        lufs_deviation = int_lufs - target_lufs
        headroom_margin = max_tp - tp_dbtp

        violations = []
        # Check True Peak ceiling
        if tp_dbtp > max_tp:
            violations.append(
                f"True Peak overload: {round(tp_dbtp, 2)} dBTP exceeds limit of {max_tp} dBTP (Inter-sample clipping!)"
            )

        # Check Integrated LUFS
        if int_lufs > target_lufs + tolerance:
            violations.append(
                f"Loudness exceeded: {round(int_lufs, 2)} LUFS exceeds {target_lufs} LUFS target (+{round(lufs_deviation, 2)} dB penalty)"
            )
        elif int_lufs < target_lufs - tolerance:
            violations.append(
                f"Loudness undershoot: {round(int_lufs, 2)} LUFS is quieter than allowed target of {target_lufs} LUFS"
            )

        # Calculate required compensation trim
        required_trim_db = 0.0
        if violations:
            # If peak clips, trim must pull peak below ceiling
            tp_needed_trim = max_tp - tp_dbtp if tp_dbtp > max_tp else 0.0
            # If LUFS is too loud, trim must pull integrated to target
            lufs_needed_trim = target_lufs - int_lufs if int_lufs > target_lufs + tolerance else 0.0
            
            # The more restrictive trim takes precedence to prevent clipping
            required_trim_db = min(tp_needed_trim, lufs_needed_trim)

        passed = len(violations) == 0
        cert = (
            "ITU-R BS.1770-5 / EBU R 128 COMPLIANT"
            if passed
            else f"NON-COMPLIANT: Requires {round(required_trim_db, 2)} dB attenuation."
        )

        return LoudnessAuditResult(
            passed=passed,
            integrated_lufs=int_lufs,
            short_term_max_lufs=st_lufs,
            momentary_max_lufs=mom_lufs,
            true_peak_dbtp=tp_dbtp,
            target_lufs=target_lufs,
            max_true_peak_dbtp=max_tp,
            lufs_deviation_db=lufs_deviation,
            headroom_margin_db=headroom_margin,
            required_trim_db=required_trim_db,
            violations=violations,
            certificate=cert,
        )

    def apply_loudness_compensation(
        self,
        audio: np.ndarray,
        sr: int = 44100
    ) -> Tuple[np.ndarray, LoudnessAuditResult]:
        """
        Audits the audio signal, and if non-compliant, applies exact linear gain trim
        and re-certifies compliance.
        """
        initial_audit = self.audit(audio, sr)
        if initial_audit.passed or abs(initial_audit.required_trim_db) < 0.05:
            return audio, initial_audit

        # Apply gain trim
        trim_linear = 10.0 ** (initial_audit.required_trim_db / 20.0)
        compensated_audio = audio * trim_linear

        # Re-audit
        final_audit = self.audit(compensated_audio, sr)
        return compensated_audio, final_audit
