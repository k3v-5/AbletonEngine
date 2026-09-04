"""
Mix Linter: automated rule-based production mix auditing.
Checks headroom, low-end stereo, mono compatibility, masking, and spectral balance.
"""
from typing import List, Dict, Any, Optional
import numpy as np

from .models import AudioFeatures, MixContext, MixIssue, Severity, HeadroomClassification
from .masking_detector import MaskingDetector


class MixLinter:
    """Audits audio features against professional production standards."""

    @classmethod
    def lint_mix(cls, features: AudioFeatures, context: MixContext,
                 kick_audio: Optional[np.ndarray] = None,
                 bass_audio: Optional[np.ndarray] = None) -> Dict[str, Any]:
        errors: List[MixIssue] = []
        warnings: List[MixIssue] = []
        info: List[MixIssue] = []
        passes: List[str] = []

        prof = context.reference_profile

        # 1. Master Clipping / Headroom Check
        if features.true_peak_db > 0.0 or features.peak_db > 0.0:
            errors.append(MixIssue(
                issue_id="MIX-001-CLIPPING",
                category="HEADROOM",
                severity=Severity.CRITICAL,
                severity_score=1.0,
                confidence=1.0,
                target_roles=["MASTER"],
                description=f"True Peak exceeds 0.0 dBFS (True Peak: {features.true_peak_db:.2f} dBFS, Peak: {features.peak_db:.2f} dBFS). Risk of inter-sample clipping.",
                evidence=[f"True peak measurement: {features.true_peak_db:.2f} dBFS (> 0.0 dBFS)"],
                probable_causes=["Master output gain or limiter ceiling too high", "Accumulative bus summation exceeding 0 dBFS"],
                recommended_actions=["Lower master fader or track gains by at least " + f"{abs(features.true_peak_db)+0.5:.1f} dB", "Engage true peak limiter with ceiling at -0.5 dBFS"]
            ))
        elif features.headroom_class == HeadroomClassification.NEAR_CLIPPING:
            warnings.append(MixIssue(
                issue_id="MIX-001-NEAR-CLIPPING",
                category="HEADROOM",
                severity=Severity.MEDIUM,
                severity_score=0.60,
                confidence=0.95,
                target_roles=["MASTER"],
                description=f"Audio is close to 0 dBFS margin (True Peak: {features.true_peak_db:.2f} dBFS).",
                evidence=[f"True peak: {features.true_peak_db:.2f} dBFS (margin < 0.5 dB)"],
                probable_causes=["Tight peak limiting without safety margin"],
                recommended_actions=["Reduce ceiling to -0.5 dBFS or lower track summation"]
            ))
        else:
            passes.append("MASTER_HEADROOM")

        # 2. Low-Frequency Stereo & Mono Compatibility
        max_low_width = prof.max_low_end_width if prof else 0.08
        if features.stereo.low_end_width > max_low_width:
            sev_score = min(1.0, features.stereo.low_end_width * 2.0)
            sev = Severity.CRITICAL if sev_score >= 0.85 else Severity.HIGH
            warnings.append(MixIssue(
                issue_id="MIX-002-LOW-FREQ-STEREO",
                category="STEREO",
                severity=sev,
                severity_score=sev_score,
                confidence=0.92,
                target_roles=["SUB", "BASS"],
                description=f"Sub-bass frequencies below 120Hz contain excessive stereo width ({features.stereo.low_end_width:.2f} > target {max_low_width:.2f}).",
                evidence=[
                    f"Low-end stereo width: {features.stereo.low_end_width:.3f}",
                    f"Genre threshold: {max_low_width:.3f}"
                ],
                probable_causes=["Stereo chorus/unison or widener applied directly on sub-bass track", "Stereo reverb on kick or low-frequency pads"],
                recommended_actions=["Engage Mono/Bass Mono on Utility device below 120Hz", "Remove stereo chorus or dimension expanders from sub-bass"]
            ))
        else:
            passes.append("SUB_BASS_MONO")

        if features.stereo.mono_compatibility_warning:
            warnings.append(MixIssue(
                issue_id="MIX-003-MONO-INCOMPATIBILITY",
                category="STEREO",
                severity=Severity.HIGH,
                severity_score=0.75,
                confidence=0.90,
                target_roles=["MASTER", "CHORDS", "LEAD"],
                description=f"High risk of destructive phase cancellation when collapsed to mono (energy loss: {features.stereo.mono_energy_loss_db:.2f} dB, correlation: {features.stereo.correlation:.2f}).",
                evidence=[
                    f"Mono sum energy loss: {features.stereo.mono_energy_loss_db:.2f} dB (> 2.0 dB)",
                    f"Stereo correlation: {features.stereo.correlation:.2f}"
                ],
                probable_causes=["Out-of-phase stereo widening on chords/pads", "Severe Haas effect or stereo micro-delays"],
                recommended_actions=["Reduce stereo separation width on mid-range synth tracks", "Check phase alignment of multi-mic / stereo sources"]
            ))
        else:
            passes.append("MONO_COMPATIBILITY")

        # 3. Low-End Masking (Kick vs Bass)
        if kick_audio is not None and bass_audio is not None:
            masking = MaskingDetector.detect_low_end_conflict(kick_audio, bass_audio, features.sample_rate)
            if masking.masking_score >= 0.50:
                warnings.append(MixIssue(
                    issue_id="MIX-004-LOW-END-MASKING",
                    category="LOW_END",
                    severity=masking.severity,
                    severity_score=masking.masking_score,
                    confidence=0.88,
                    target_roles=["KICK", "BASS", "SUB"],
                    description=f"High low-end masking conflict between kick and bass (masking score: {masking.masking_score:.2f}).",
                    evidence=masking.evidence,
                    probable_causes=masking.probable_causes,
                    recommended_actions=masking.recommended_actions
                ))
            else:
                passes.append("LOW_END_SEPARATION")
        else:
            passes.append("LOW_END_SEPARATION")

        # 4. Over-Compression / Flat Dynamics
        if features.crest_factor < 6.0 and context.section in ("DROP_1", "DROP_2", "BUILD_2"):
            warnings.append(MixIssue(
                issue_id="MIX-005-OVER-COMPRESSED",
                category="DYNAMICS",
                severity=Severity.MEDIUM,
                severity_score=0.65,
                confidence=0.85,
                target_roles=["MASTER", "DRUM_BUS"],
                description=f"Mix exhibits low dynamic crest factor ({features.crest_factor:.1f} dB). Transients appear squashed.",
                evidence=[f"Crest factor: {features.crest_factor:.1f} dB (< 6.0 dB)"],
                probable_causes=["Excessive limiter or bus compressor ratio", "Too fast attack times on drum compressors"],
                recommended_actions=["Slow down compressor attack to 30ms to allow transients through", "Back off master limiter threshold"]
            ))
        else:
            passes.append("DYNAMIC_PUNCH")

        # Compute mix health score [0.0, 100.0]
        penalty = 0.0
        for err in errors:
            penalty += err.severity_score * 35.0
        for warn in warnings:
            penalty += warn.severity_score * 15.0
        for inf in info:
            penalty += inf.severity_score * 5.0
            
        health_score = max(0.0, min(100.0, 100.0 - penalty))

        return {
            "valid": len(errors) == 0,
            "mix_health_score": round(health_score, 1),
            "errors": [e.to_dict() for e in errors],
            "warnings": [w.to_dict() for w in warnings],
            "info": [i.to_dict() for i in info],
            "passes": passes,
            "total_issues": len(errors) + len(warnings) + len(info)
        }
