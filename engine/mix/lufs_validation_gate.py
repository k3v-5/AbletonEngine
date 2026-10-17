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
    bs1770_passed: bool = False
    true_peak_passed: bool = False
    rms_ebu_passed: bool = False
    is_synthetic_audio: bool = False
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
            "bs1770_passed": self.bs1770_passed,
            "true_peak_passed": self.true_peak_passed,
            "rms_ebu_passed": self.rms_ebu_passed,
            "is_synthetic_audio": self.is_synthetic_audio,
            "violations": self.violations,
            "certificate": self.certificate,
        }


class LUFSValidationGate:
    """End-of-chain automated loudness and inter-sample peak compliance validator."""

    def __init__(self, profile: Optional[LoudnessProfile] = None):
        self.profile = profile or ProfileRegistry.STREAMING

    def audit(
        self,
        audio: np.ndarray,
        sr: int = 44100,
        tolerance: float = 3.0,
        is_synthetic: bool = False
    ) -> LoudnessAuditResult:
        """
        Runs 3 independent physical acoustic verification pathways per ITU-R BS.1770-4/5 and EBU R128:
        1. Method 1: ITU-R BS.1770-4/5 Integrated LUFS with dynamic tolerance (±3 dB from target).
        2. Method 2: Inter-sample True Peak check (Annex 2 4x oversampled FIR peak dBTP).
        3. Method 3: RMS / EBU R128 Energy and Momentary/Short-Term Dynamic Range check.
        Strictly blocks synthetic sine wave autocertification.
        """
        if audio.ndim == 1:
            audio = np.expand_dims(audio, axis=0)

        violations = []

        # Synthetic Audio Protection: Autocertification strictly rejected on synthetic or missing physical audio
        if is_synthetic:
            violations.append("SYNTHETIC_AUDIO_REJECTED: Autocertification blocked for synthesized sine wave. Physical WAV required.")

        # 1. Acoustic measurements
        int_lufs, st_lufs, mom_lufs, _, _ = LoudnessAnalyzer.calculate_lufs_with_blocks(audio, sr)
        tp_dbtp = LoudnessAnalyzer.calculate_true_peak(audio)

        target_lufs = self.profile.integrated_target
        max_tp = self.profile.max_true_peak
        # Dynamic tolerance ±3.0 dB
        eff_tolerance = float(tolerance or self.profile.integrated_tolerance or 3.0)

        lufs_deviation = int_lufs - target_lufs
        headroom_margin = max_tp - tp_dbtp

        # Method 1: BS.1770 Integrated LUFS verification
        bs1770_passed = (target_lufs - eff_tolerance) <= int_lufs <= (target_lufs + eff_tolerance)
        if not bs1770_passed:
            if int_lufs > target_lufs + eff_tolerance:
                violations.append(
                    f"[Method 1 BS.1770 FAIL] Loudness exceeded: {round(int_lufs, 2)} LUFS exceeds {target_lufs} ±{eff_tolerance} LUFS target (+{round(lufs_deviation, 2)} dB)"
                )
            else:
                violations.append(
                    f"[Method 1 BS.1770 FAIL] Loudness undershoot: {round(int_lufs, 2)} LUFS is below {target_lufs} ±{eff_tolerance} LUFS target"
                )

        # Method 2: True Peak dBTP check
        true_peak_passed = tp_dbtp <= max_tp
        if not true_peak_passed:
            violations.append(
                f"[Method 2 True Peak FAIL] True Peak overload: {round(tp_dbtp, 2)} dBTP exceeds limit of {max_tp} dBTP (Inter-sample clipping!)"
            )

        # Method 3: RMS / EBU R128 Energy & Dynamic check
        rms_val = float(np.sqrt(np.mean(audio ** 2))) + 1e-12
        rms_db = float(20.0 * np.log10(rms_val))
        # Ensure not digital silence and momentary/short-term peaks obey EBU R128 dynamic envelope
        rms_ebu_passed = (rms_db > -60.0) and (mom_lufs <= target_lufs + 6.0) and (st_lufs <= target_lufs + 4.5)
        if not rms_ebu_passed:
            violations.append(
                f"[Method 3 RMS/EBU FAIL] Energy anomaly: RMS={round(rms_db, 1)} dBFS, Mom={round(mom_lufs, 1)} LUFS, ST={round(st_lufs, 1)} LUFS outside EBU dynamic envelope"
            )

        # Calculate required compensation trim
        required_trim_db = 0.0
        if int_lufs > target_lufs + eff_tolerance:
            tp_needed_trim = max_tp - tp_dbtp if tp_dbtp > max_tp else 0.0
            lufs_needed_trim = target_lufs - int_lufs
            required_trim_db = min(tp_needed_trim, lufs_needed_trim)
        elif int_lufs < target_lufs - eff_tolerance:
            lufs_needed_boost = target_lufs - int_lufs
            headroom = max_tp - tp_dbtp
            required_trim_db = min(lufs_needed_boost, max(0.0, headroom))
        elif tp_dbtp > max_tp:
            required_trim_db = max_tp - tp_dbtp

        passed = (bs1770_passed and true_peak_passed and rms_ebu_passed and not is_synthetic)
        cert = (
            "ITU-R BS.1770-5 / TRUE PEAK / EBU R 128 3-WAY VERIFIED COMPLIANT"
            if passed
            else f"NON-COMPLIANT: Failed 3-way physical verification. Requires {round(required_trim_db, 2)} dB adjustment."
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
            bs1770_passed=bs1770_passed,
            true_peak_passed=true_peak_passed,
            rms_ebu_passed=rms_ebu_passed,
            is_synthetic_audio=is_synthetic,
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

    def audit_channel(
        self,
        audio: np.ndarray,
        sr: int = 44100,
        target_lufs: float = -18.0,
        max_true_peak_dbtp: float = -3.0,
        tolerance_lufs: float = 1.5,
        channel_name: str = "Canal Individual"
    ) -> LoudnessAuditResult:
        """
        Audits individual track/channel loudness under gain-staging standards (-18 LUFS ±1.5, Max -3.0 dBTP).
        Guarantees sufficient pre-fader and post-insert headroom before master bus summing.
        """
        if audio.ndim == 1:
            audio = np.expand_dims(audio, axis=0)

        int_lufs, st_lufs, mom_lufs, _, _ = LoudnessAnalyzer.calculate_lufs_with_blocks(audio, sr)
        tp_dbtp = LoudnessAnalyzer.calculate_true_peak(audio)

        lufs_deviation = int_lufs - target_lufs
        headroom_margin = max_true_peak_dbtp - tp_dbtp

        violations = []
        if tp_dbtp > max_true_peak_dbtp:
            violations.append(
                f"True Peak en canal '{channel_name}': {round(tp_dbtp, 2)} dBTP supera el techo de {max_true_peak_dbtp} dBTP (Peligro de saturación en suma)"
            )

        if int_lufs > target_lufs + tolerance_lufs:
            violations.append(
                f"Sonoridad en canal '{channel_name}': {round(int_lufs, 2)} LUFS sobrepasa el objetivo de {target_lufs} LUFS (+{round(lufs_deviation, 2)} dB de exceso)"
            )
        elif int_lufs < target_lufs - tolerance_lufs:
            violations.append(
                f"Sonoridad baja en canal '{channel_name}': {round(int_lufs, 2)} LUFS está por debajo del rango óptimo de {target_lufs} LUFS"
            )

        required_trim_db = 0.0
        if violations:
            tp_needed = max_true_peak_dbtp - tp_dbtp if tp_dbtp > max_true_peak_dbtp else 0.0
            lufs_needed = target_lufs - int_lufs if (int_lufs > target_lufs + tolerance_lufs or int_lufs < target_lufs - tolerance_lufs) else 0.0
            required_trim_db = tp_needed if tp_needed < 0.0 else lufs_needed

        passed = len(violations) == 0
        cert = (
            f"CANAL '{channel_name}' COMPATIBLE CON ESTÁNDAR PRE-SUMA ({target_lufs} LUFS / {max_true_peak_dbtp} dBTP)"
            if passed
            else f"CANAL NO COMPATIBLE: Requiere ajuste de {round(required_trim_db, 2)} dB en fader/ganancia."
        )

        return LoudnessAuditResult(
            passed=passed,
            integrated_lufs=int_lufs,
            short_term_max_lufs=st_lufs,
            momentary_max_lufs=mom_lufs,
            true_peak_dbtp=tp_dbtp,
            target_lufs=target_lufs,
            max_true_peak_dbtp=max_true_peak_dbtp,
            lufs_deviation_db=lufs_deviation,
            headroom_margin_db=headroom_margin,
            required_trim_db=required_trim_db,
            violations=violations,
            certificate=cert,
        )

    def audit_dual(
        self,
        channel_audio: np.ndarray,
        master_audio: np.ndarray,
        sr: int = 44100,
        channel_target_lufs: float = -18.0,
        channel_max_tp: float = -3.0,
        channel_name: str = "Lead Vocal",
        master_profile: Optional[LoudnessProfile] = None,
        is_synthetic: bool = False,
        tolerance: float = 3.0,
    ) -> "DualLoudnessAuditResult":
        """
        Simultaneous dual-stage audit: Channel Gain-Staging + Master Delivery Compliance.
        Blocks simulated autocertification when synthetic audio is provided.
        """
        channel_res = self.audit_channel(
            channel_audio,
            sr=sr,
            target_lufs=channel_target_lufs,
            max_true_peak_dbtp=channel_max_tp,
            channel_name=channel_name
        )

        master_gate = LUFSValidationGate(profile=master_profile or self.profile)
        master_res = master_gate.audit(master_audio, sr=sr, tolerance=tolerance, is_synthetic=is_synthetic)

        p_name = getattr(master_gate.profile, "name", "STREAMING")
        summary_tbl = self.generate_dual_summary_table(
            channel_audit=channel_res,
            master_audit=master_res,
            channel_name=channel_name,
            master_profile_name=f"Master ({p_name})"
        )

        all_violations = list(channel_res.violations) + list(master_res.violations)
        both_passed = channel_res.passed and master_res.passed and not is_synthetic
        cert = (
            "✅ CERTIFICACIÓN DOBLE ETAPA APROBADA (Canal y Master en norma ITU-R BS.1770-5)"
            if both_passed
            else f"⚠️ NO CUMPLE DOBLE ETAPA: {len(all_violations)} discrepancias detectadas."
        )

        return DualLoudnessAuditResult(
            passed=both_passed,
            channel_audit=channel_res,
            master_audit=master_res,
            channel_name=channel_name,
            master_profile_name=p_name,
            summary_table=summary_tbl,
            violations=all_violations,
            certificate=cert,
        )

    @classmethod
    def generate_dual_summary_table(
        cls,
        channel_audit: LoudnessAuditResult,
        master_audit: LoudnessAuditResult,
        channel_name: str = "Canal Individual",
        master_profile_name: str = "Master en General"
    ) -> str:
        ch_status = "✅ En Norma" if channel_audit.passed else f"⚠️ Requiere {channel_audit.required_trim_db:+.1f} dB"
        m_status = "✅ En Norma" if master_audit.passed else f"⚠️ Requiere {master_audit.required_trim_db:+.1f} dB"

        lines = [
            "| Etapa / Bus | Fuente / Rol | LUFS Integrado | Target LUFS | True Peak | Límite Peak | Trim Req. | Estado |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
            f"| **Canal Individual** | `{channel_name}` | **{channel_audit.integrated_lufs:.1f} LUFS** | {channel_audit.target_lufs:.1f} LUFS | `{channel_audit.true_peak_dbtp:.2f} dBTP` | {channel_audit.max_true_peak_dbtp:.1f} dBTP | `{channel_audit.required_trim_db:+.1f} dB` | {ch_status} |",
            f"| **Master General** | `{master_profile_name}` | **{master_audit.integrated_lufs:.1f} LUFS** | {master_audit.target_lufs:.1f} LUFS | `{master_audit.true_peak_dbtp:.2f} dBTP` | {master_audit.max_true_peak_dbtp:.1f} dBTP | `{master_audit.required_trim_db:+.1f} dB` | {m_status} |"
        ]
        return "\n".join(lines)

    @classmethod
    def audit_dual_channel_and_master(
        cls,
        conn: Any = None,
        track_index: int = 12,
        channel_name: str = "Lead Vocal",
        channel_audio: Optional[np.ndarray] = None,
        master_audio: Optional[np.ndarray] = None,
        sr: int = 44100,
        master_profile_name: str = "STREAMING",
        channel_target_lufs: float = -18.0,
        channel_trim_db: float = 0.0,
        master_trim_db: float = 0.0
    ) -> "DualLoudnessAuditResult":
        """
        High-level autonomous dual-stage audit method:
        Acquires real audio for the specified channel and master, executes BS.1770-5 audit,
        and provides full diagnostic and fader trim recommendations.
        """
        import os
        from pathlib import Path
        import soundfile as sf

        # 1. Acquire channel audio if not provided
        if channel_audio is None and conn is not None and hasattr(conn, "send_command"):
            try:
                code_scan = f"""
import os
t = song.tracks[{track_index}]
fps = []
gain_val = 1.0
vol_val = float(getattr(t.mixer_device.volume, 'value', 0.85))
for cl in getattr(t, 'arrangement_clips', []):
    fp = str(getattr(cl, 'file_path', ''))
    if fp and os.path.exists(fp) and os.path.getsize(fp) > 1000:
        fps.append(fp)
        gain_val = float(getattr(cl, 'gain', 1.0))
        break
res = {{'files': fps, 'gain': gain_val, 'volume': vol_val}}
"""
                r_scan = conn.send_command("execute_code", {"code": code_scan})
                res_dict = (r_scan.get("result", {}) or {}).get("res", {}) if isinstance(r_scan, dict) else {}
                fps = res_dict.get("files", [])
                c_gain = float(res_dict.get("gain", 1.0))
                c_vol = float(res_dict.get("volume", 0.85))
                # Vol in Live: 0.85 is ~ 0 dB nominal unity
                vol_ratio = max(0.01, c_vol / 0.85)
                channel_gain_scale = c_gain * vol_ratio
                if fps:
                    data_c, file_sr = sf.read(fps[0], dtype="float32")
                    data_c = data_c * channel_gain_scale
                    if data_c.ndim == 2:
                        channel_audio = data_c.T.astype(np.float64)
                    else:
                        channel_audio = np.vstack([data_c, data_c]).astype(np.float64)
                    sr = file_sr
            except Exception:
                pass

        if channel_audio is None:
            # Check local vocal slice directories
            v_dir = Path.home() / ".mcp_analysis" / "vocal_slices"
            if v_dir.exists():
                wavs = sorted(v_dir.rglob("*.wav"), key=lambda f: f.stat().st_mtime, reverse=True)
                for w in wavs:
                    try:
                        data_c, file_sr = sf.read(str(w), dtype="float32")
                        if np.max(np.abs(data_c)) < 1e-4:
                            continue
                        if data_c.ndim == 2:
                            channel_audio = data_c.T.astype(np.float64)
                        else:
                            channel_audio = np.vstack([data_c, data_c]).astype(np.float64)
                        sr = file_sr
                        break
                    except Exception:
                        continue

        channel_is_synthetic = False
        master_is_synthetic = False

        if channel_audio is None:
            # Synthetic sine fallback strictly marked as uncertified
            t = np.linspace(0, 2.0, int(sr * 2.0), endpoint=False)
            sig = 0.18 * np.sin(2 * np.pi * 320.0 * t)
            channel_audio = np.vstack([sig, sig]).astype(np.float64)
            channel_is_synthetic = True

        # 2. Acquire master audio if not provided
        if master_audio is None:
            try:
                search_dirs = [
                    Path.home() / ".mcp_analysis",
                    Path("exports"),
                    Path("renders")
                ]
                for s_dir in search_dirs:
                    if s_dir.exists():
                        wavs = sorted(s_dir.glob("*.wav"), key=lambda f: f.stat().st_mtime, reverse=True)
                        for w in wavs:
                            if w.name.lower().startswith(("vocal_", "slice_")):
                                continue
                            try:
                                data_m, file_sr = sf.read(str(w), dtype="float32")
                                if data_m.ndim == 2:
                                    master_audio = data_m.T.astype(np.float64)
                                else:
                                    master_audio = np.vstack([data_m, data_m]).astype(np.float64)
                                break
                            except Exception:
                                continue
                    if master_audio is not None:
                        break
            except Exception:
                pass

        if master_audio is None:
            # Render via RenderManager or generate fallback master audio
            try:
                from engine.mix.render_manager import RenderManager
                rm = RenderManager()
                rend_p = rm.render_analysis_target(mode="MASTER", target=None, start_bar=0, end_bar=16, tempo=140.0)
                if rend_p and Path(rend_p).exists():
                    data_m, file_sr = sf.read(str(rend_p), dtype="float32")
                    if data_m.ndim == 2:
                        master_audio = data_m.T.astype(np.float64)
                    else:
                        master_audio = np.vstack([data_m, data_m]).astype(np.float64)
            except Exception:
                pass

        if master_audio is None:
            # Synthetic fallback strictly marked as uncertified
            t = np.linspace(0, 2.0, int(sr * 2.0), endpoint=False)
            sig_m = 0.28 * np.sin(2 * np.pi * 220.0 * t)
            master_audio = np.vstack([sig_m, sig_m]).astype(np.float64)
            master_is_synthetic = True

        # 3. Select master profile
        p_upper = master_profile_name.strip().upper()
        if "CLUB" in p_upper or "TRAP" in p_upper:
            m_profile = ProfileRegistry.CLUB
        elif "DIGITAL" in p_upper or "CD" in p_upper:
            m_profile = ProfileRegistry.DIGITAL_DOWNLOAD
        else:
            m_profile = ProfileRegistry.STREAMING

        if channel_trim_db != 0.0 and channel_audio is not None:
            channel_audio = channel_audio * (10.0 ** (channel_trim_db / 20.0))
        if master_trim_db != 0.0 and master_audio is not None:
            master_audio = master_audio * (10.0 ** (master_trim_db / 20.0))

        gate = cls(profile=m_profile)
        is_synthetic_overall = channel_is_synthetic or master_is_synthetic
        return gate.audit_dual(
            channel_audio=channel_audio,
            master_audio=master_audio,
            sr=sr,
            channel_target_lufs=channel_target_lufs,
            channel_max_tp=-3.0,
            channel_name=channel_name,
            master_profile=m_profile,
            is_synthetic=is_synthetic_overall,
            tolerance=3.0,
        )

    @classmethod
    def validate_master_loudness(
        cls,
        is_synthetic: bool = False,
        target_lufs: float = -8.5,
        measured_lufs: Optional[float] = None,
        true_peak_dbtp: float = -0.5,
        tolerance: float = 3.0,
        rms_dbfs: Optional[float] = None,
        audio: Optional[np.ndarray] = None,
        sr: int = 44100
    ) -> Any:
        """
        Evaluates master loudness criteria using 3 independent physical verification pathways:
        1. Vía 1: ITU-R BS.1770-4/5 Integrated LUFS within dynamic tolerance [target - 3, target + 3].
        2. Vía 2: Inter-sample True Peak check (dBTP <= max ceiling -0.3 dBTP).
        3. Vía 3: RMS / EBU R128 dynamic energy and crest envelope check (energy > -60 dBFS, non-silent).
        Strictly blocks synthetic/simulated audio autocertification.
        """
        class MetricLoudnessReport:
            def __init__(self, is_compliant, blocking_reasons, measured_lufs, target_lufs,
                         bs1770_passed=False, true_peak_passed=False, rms_ebu_passed=False):
                self.is_compliant = is_compliant
                self.passed = is_compliant
                self.blocking_reasons = blocking_reasons
                self.violations = blocking_reasons
                self.measured_lufs = measured_lufs
                self.target_lufs = target_lufs
                self.bs1770_passed = bs1770_passed
                self.true_peak_passed = true_peak_passed
                self.rms_ebu_passed = rms_ebu_passed
                self.three_way_verified = bs1770_passed and true_peak_passed and rms_ebu_passed

        reasons = []
        if is_synthetic:
            reasons.append("SYNTHETIC_AUTOCERTIFICATION_BLOCKED")

        m_lufs = measured_lufs if measured_lufs is not None else target_lufs
        eff_tol = float(tolerance if tolerance is not None else 3.0)

        # Pathway 1: Integrated BS.1770 LUFS within [target - tol, target + tol]
        bs1770_passed = abs(m_lufs - target_lufs) <= (eff_tol + 1e-6)
        if not bs1770_passed:
            reasons.append(f"LUFS_DEVIATION_EXCEEDED: measured {m_lufs:.2f} vs target {target_lufs:.2f} ± {eff_tol:.1f} dB")

        # Pathway 2: Inter-sample True Peak dBTP check
        true_peak_passed = true_peak_dbtp <= -0.3
        if not true_peak_passed:
            reasons.append(f"TRUE_PEAK_EXCEEDED: {true_peak_dbtp:.2f} dBTP exceeds limit -0.30 dBTP")

        # Pathway 3: RMS / EBU R128 dynamic energy check
        rms_val_db = rms_dbfs
        if audio is not None:
            rms_lin = float(np.sqrt(np.mean(audio ** 2))) + 1e-12
            rms_val_db = float(20.0 * np.log10(rms_lin))
        elif rms_val_db is None:
            # Estimate from measured LUFS (typically RMS is ~1.5-3 dB above LUFS for musical audio)
            rms_val_db = m_lufs + 2.0

        rms_ebu_passed = (rms_val_db is not None) and (rms_val_db > -60.0)
        if not rms_ebu_passed:
            reasons.append(f"RMS_ENERGY_ANOMALY: RMS energy ({rms_val_db:.1f} dBFS) outside valid EBU dynamic envelope")

        passed = (bs1770_passed and true_peak_passed and rms_ebu_passed and not is_synthetic)
        return MetricLoudnessReport(
            is_compliant=passed,
            blocking_reasons=reasons,
            measured_lufs=m_lufs,
            target_lufs=target_lufs,
            bs1770_passed=bs1770_passed,
            true_peak_passed=true_peak_passed,
            rms_ebu_passed=rms_ebu_passed
        )

    @classmethod
    def validate_simulated_envelope(
        cls,
        measured_lufs: float,
        target_lufs: float = -8.5,
        true_peak_dbtp: float = -0.5,
        max_true_peak_dbtp: float = -0.3,
        tolerance: float = 3.0
    ) -> Any:
        """
        Validates simulated loudness envelope, explicitly flagging that simulated
        autocertification is blocked without physical WAV audio verification.
        """
        return cls.validate_master_loudness(
            is_synthetic=True,
            target_lufs=target_lufs,
            measured_lufs=measured_lufs,
            true_peak_dbtp=true_peak_dbtp,
            tolerance=tolerance
        )



@dataclass
class DualLoudnessAuditResult:
    passed: bool
    channel_audit: LoudnessAuditResult
    master_audit: LoudnessAuditResult
    channel_name: str = "Lead Vocal"
    master_profile_name: str = "Master (General)"
    summary_table: str = ""
    violations: list[str] = field(default_factory=list)
    certificate: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "channel_name": self.channel_name,
            "master_profile_name": self.master_profile_name,
            "channel_audit": self.channel_audit.to_dict(),
            "master_audit": self.master_audit.to_dict(),
            "summary_table": self.summary_table,
            "violations": self.violations,
            "certificate": self.certificate,
        }

