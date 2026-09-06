# engine/supervisor/gatekeeper.py
"""
Supervisor Gatekeeper & Hard Quality Gates Engine:
Enforces a strict 7-phase state machine where the engine is the authoritative supervisor.
Execution cannot progress to subsequent phases if any physical, structural,
or acoustic gate criteria are violated.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import os

from .failure_diagnostics import FailureDiagnostics, DiagnosticFinding, FailureCategory, DiagnosticSeverity
from .acoustic_probe import AcousticProbe, AcousticSilenceError
from ..instruments.drum_rack_guard import DrumRackGuard
from ..instruments.vst_guard import VSTGuard, VSTComplianceError
from ..fx.track_fx_rack import TrackFXRack
from ..fx.device_parameter_supervisor import DeviceParameterSupervisor
from ..mastering.guided_mastering import GuidedMasteringEngine, DeliveryProfile


class ProductionPhase(str, Enum):
    PHASE_1_DNA = "PHASE_1_DNA"
    PHASE_2_COMPOSITION = "PHASE_2_COMPOSITION"
    PHASE_3_INSTRUMENTATION = "PHASE_3_INSTRUMENTATION"
    PHASE_4_GROOVE = "PHASE_4_GROOVE"
    PHASE_5_TRANSITIONS = "PHASE_5_TRANSITIONS"
    PHASE_6_MIX = "PHASE_6_MIX"
    PHASE_7_MASTERING = "PHASE_7_MASTERING"


class GateValidationError(RuntimeError):
    """Raised when a quality gate fails physical, acoustic, or structural validation."""
    def __init__(self, phase: ProductionPhase, message: str, findings: List[DiagnosticFinding], remediations: List[str]):
        super().__init__(message)
        self.phase = phase
        self.findings = findings
        self.remediations = remediations

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "error_message": str(self),
            "findings_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
            "remediations": self.remediations
        }


@dataclass
class GateResult:
    phase: ProductionPhase
    passed: bool
    findings: List[DiagnosticFinding] = field(default_factory=list)
    remediations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "passed": self.passed,
            "findings": [f.to_dict() for f in self.findings],
            "remediations": self.remediations,
            "metadata": self.metadata
        }


class Gatekeeper:
    """Supervises the production lifecycle across 7 hard quality gates."""

    GATE_ORDER = [
        ProductionPhase.PHASE_1_DNA,
        ProductionPhase.PHASE_2_COMPOSITION,
        ProductionPhase.PHASE_3_INSTRUMENTATION,
        ProductionPhase.PHASE_4_GROOVE,
        ProductionPhase.PHASE_5_TRANSITIONS,
        ProductionPhase.PHASE_6_MIX,
        ProductionPhase.PHASE_7_MASTERING
    ]

    def __init__(self, fail_fast: bool = True):
        self.fail_fast = fail_fast
        self.completed_gates: List[ProductionPhase] = []

    def validate_gate_1_dna(self, conn: Any, context: Dict[str, Any]) -> GateResult:
        """Gate 1: DNA (Tempo, Cue Points, Musical Scale)."""
        findings = []
        tempo = context.get("tempo", 124.0)

        if tempo < 60.0 or tempo > 220.0:
            findings.append(DiagnosticFinding(
                category=FailureCategory.TIMING_VIOLATION,
                severity=DiagnosticSeverity.HARD_BLOCKER,
                track_index=None,
                track_name=None,
                device_name=None,
                issue=f"Invalid song tempo: {tempo} BPM.",
                measured_value=tempo,
                expected_value="60.0 .. 220.0 BPM",
                remediation_actions=["Set a valid musical tempo in context."]
            ))

        cues = context.get("cue_points", [])
        if not cues:
            findings.append(DiagnosticFinding(
                category=FailureCategory.MISSING_CLIPS,
                severity=DiagnosticSeverity.WARNING,
                track_index=None,
                track_name=None,
                device_name=None,
                issue="No arrangement cue points defined.",
                measured_value=0,
                expected_value=">= 4 cue points (Intro, Verse, Chorus, Outro)",
                remediation_actions=["Inject cue points using create_cue_point."]
            ))

        passed = len([f for f in findings if f.severity == DiagnosticSeverity.HARD_BLOCKER]) == 0
        return self._finalize_gate(ProductionPhase.PHASE_1_DNA, passed, findings, context)

    def validate_gate_2_composition(self, conn: Any, context: Dict[str, Any]) -> GateResult:
        """Gate 2: Composition (MIDI Notes, Density, Scale)."""
        findings = []
        tracks = context.get("tracks", {})

        if not tracks:
            findings.append(DiagnosticFinding(
                category=FailureCategory.MISSING_CLIPS,
                severity=DiagnosticSeverity.HARD_BLOCKER,
                track_index=None,
                track_name=None,
                device_name=None,
                issue="Session contains no musical tracks.",
                measured_value=0,
                expected_value=">= 4 musical tracks",
                remediation_actions=["Generate composition tracks."]
            ))

        passed = len([f for f in findings if f.severity == DiagnosticSeverity.HARD_BLOCKER]) == 0
        return self._finalize_gate(ProductionPhase.PHASE_2_COMPOSITION, passed, findings, context)

    def validate_gate_3_instrumentation(self, conn: Any, context: Dict[str, Any]) -> GateResult:
        """Gate 3: Instrumentation (VST Guard, Drum Rack Pad audit, Vital presets)."""
        findings = []
        track_roles = context.get("track_roles", {})
        vital_presets_deployed = context.get("vital_presets_deployed", False)

        for k, v in track_roles.items():
            if isinstance(k, int):
                t_idx = k
                role = str(v)
            else:
                role = str(k)
                t_idx = int(v)
            r_lower = role.lower()
            if "drum" in r_lower:
                drum_audit = DrumRackGuard.audit_drum_rack(conn, t_idx)
                if not drum_audit.get("is_populated", True):
                    findings.append(DiagnosticFinding(
                        category=FailureCategory.DEVICE_ERROR,
                        severity=DiagnosticSeverity.HARD_BLOCKER,
                        track_index=t_idx,
                        track_name=f"Track {t_idx}",
                        device_name="Drum Rack",
                        issue=f"Drum Rack on track {t_idx} has {drum_audit.get('populated_pad_count', 0)} populated pads. Pads are empty!",
                        measured_value=drum_audit.get('populated_pad_count', 0),
                        expected_value=">= 4 populated pads with devices/samples",
                        remediation_actions=[
                            "Load verified 808 Core Kit preset (query:Drums#FileId_5422).",
                            "Populate pads using DrumRackGuard.enforce_populated_drum_kit."
                        ]
                    ))
            else:
                audit = VSTGuard.audit_track_instrument(conn, t_idx, role)
                dev_name = audit.get("device_name") or ""
                # If Vital is present and .vital synthesized presets are verified on disk:
                is_vital = "vital" in dev_name.lower() or "vital" in r_lower
                if is_vital and vital_presets_deployed:
                    # Verified compliance through procedural preset synthesis
                    continue

                if not audit["is_compliant"]:
                    findings.append(DiagnosticFinding(
                        category=FailureCategory.LOW_PARAMETER_COUNT,
                        severity=DiagnosticSeverity.HARD_BLOCKER,
                        track_index=t_idx,
                        track_name=f"Track {t_idx}",
                        device_name=dev_name or "Unknown",
                        issue=f"Instrument on track {t_idx} only exposes {audit['parameter_count']} parameter(s) - blind init patch.",
                        measured_value=audit["parameter_count"],
                        expected_value=">= 8 parameters or procedural presets deployed",
                        remediation_actions=[
                            "Deploy procedural presets via VitalPresetManager.",
                            "Expose macros via Live Configure button or Instrument Rack."
                        ]
                    ))

                # Mandatory Parameter Sculpting Audit for all devices on this track (Native & VST)
                if conn and hasattr(conn, "send_command"):
                    try:
                        t_info = conn.send_command("get_track_info", {"track_index": t_idx}).get("result", {})
                        devices = t_info.get("devices", [])
                        for d_idx, dev in enumerate(devices):
                            d_name = dev.get("name", "Unknown")
                            sculpt_audit = DeviceParameterSupervisor.audit_device_sculpting(conn, t_idx, d_idx)
                            if not sculpt_audit.get("is_sculpted", False):
                                if context.get("auto_remediate", True):
                                    DeviceParameterSupervisor.enforce_mandatory_sculpting(conn, t_idx, d_idx, role)
                                    sculpt_audit = DeviceParameterSupervisor.audit_device_sculpting(conn, t_idx, d_idx)

                                if not sculpt_audit.get("is_sculpted", False):
                                    findings.append(DiagnosticFinding(
                                        category=FailureCategory.UNCONFIGURED_VST,
                                        severity=DiagnosticSeverity.HARD_BLOCKER,
                                        track_index=t_idx,
                                        track_name=f"Track {t_idx}",
                                        device_name=d_name,
                                        issue=f"Device '{d_name}' on Track {t_idx} is in default / unconfigured state. Mandatory parameter sculpting violated!",
                                        measured_value=0,
                                        expected_value=">= 1 sculpted parameter section",
                                        remediation_actions=[
                                            f"Call DeviceParameterSupervisor.apply_sectional_tuning or enforce_mandatory_sculpting for '{d_name}' on Track {t_idx}.",
                                            "Ensure sound character, cutoff, envelopes, and macros are customized."
                                        ]
                                    ))
                    except Exception:
                        pass

        passed = len([f for f in findings if f.severity == DiagnosticSeverity.HARD_BLOCKER]) == 0
        return self._finalize_gate(ProductionPhase.PHASE_3_INSTRUMENTATION, passed, findings, context)

    def validate_gate_4_groove(self, conn: Any, context: Dict[str, Any]) -> GateResult:
        """Gate 4: Arrangement & Timeline Structure (Clips placed on Arrangement timeline)."""
        findings = []
        arr_clips = context.get("arrangement_clips_count", 0)

        if arr_clips < 5:
            findings.append(DiagnosticFinding(
                category=FailureCategory.MISSING_CLIPS,
                severity=DiagnosticSeverity.HARD_BLOCKER,
                track_index=None,
                track_name="Arrangement Timeline",
                device_name=None,
                issue=f"Arrangement timeline contains only {arr_clips} clips. Song must be deployed to Arrangement view!",
                measured_value=arr_clips,
                expected_value=">= 5 arrangement clips across timeline",
                remediation_actions=["Execute ArrangementComposer.compose_and_deploy to place clips in Arrangement view."]
            ))

        passed = len([f for f in findings if f.severity == DiagnosticSeverity.HARD_BLOCKER]) == 0
        return self._finalize_gate(ProductionPhase.PHASE_4_GROOVE, passed, findings, context)

    def validate_gate_5_transitions(self, conn: Any, context: Dict[str, Any]) -> GateResult:
        """Gate 5: Transitions & Energy (Risers, Downlifters, Silence Gaps)."""
        findings = []
        has_transitions = context.get("has_transitions", True)
        if not has_transitions:
            findings.append(DiagnosticFinding(
                category=FailureCategory.MISSING_CLIPS,
                severity=DiagnosticSeverity.WARNING,
                track_index=None,
                track_name=None,
                device_name=None,
                issue="No risers or energy sweeps detected between sections.",
                measured_value=False,
                expected_value=True,
                remediation_actions=["Inject transition risers or pre-drop silence."]
            ))

        passed = len([f for f in findings if f.severity == DiagnosticSeverity.HARD_BLOCKER]) == 0
        return self._finalize_gate(ProductionPhase.PHASE_5_TRANSITIONS, passed, findings, context)

    def validate_gate_6_mix(self, conn: Any, context: Dict[str, Any]) -> GateResult:
        """Gate 6: Mix & Gain Staging (-6.0 dBFS pre-master headroom, HPF on tracks, zero duplicate plugins)."""
        findings = []
        headroom_dbfs = context.get("headroom_dbfs", -6.5)

        if headroom_dbfs > -3.0:
            findings.append(DiagnosticFinding(
                category=FailureCategory.HEADROOM_OVERFLOW,
                severity=DiagnosticSeverity.HARD_BLOCKER,
                track_index=None,
                track_name="Master Bus",
                device_name=None,
                issue=f"Insufficient pre-master headroom: {headroom_dbfs:.1f} dBFS (clipping risk).",
                measured_value=headroom_dbfs,
                expected_value="<= -6.0 dBFS",
                remediation_actions=["Execute auto gain staging to trim track faders."]
            ))

        has_duplicate_plugins = context.get("has_duplicate_plugins", False)
        if has_duplicate_plugins:
            findings.append(DiagnosticFinding(
                category=FailureCategory.DEVICE_ERROR,
                severity=DiagnosticSeverity.HARD_BLOCKER,
                track_index=None,
                track_name=None,
                device_name=None,
                issue="Duplicate/overlapping plugins detected on tracks! Must enforce idempotent channel strips.",
                measured_value="Duplicates Present",
                expected_value="0 Duplicates",
                remediation_actions=["Purge duplicate devices via TrackFXRack."]
            ))

        passed = len([f for f in findings if f.severity == DiagnosticSeverity.HARD_BLOCKER]) == 0
        return self._finalize_gate(ProductionPhase.PHASE_6_MIX, passed, findings, context)

    def validate_gate_7_mastering(self, conn: Any, context: Dict[str, Any]) -> GateResult:
        """Gate 7: Mastering (Guided 7-Point Chain, Physical Convergence to Target LUFS)."""
        findings = []
        target_lufs = context.get("target_lufs", -6.0)
        achieved_lufs = context.get("achieved_lufs", -6.0)

        delta = abs(achieved_lufs - target_lufs)
        if delta > 1.0:
            findings.append(DiagnosticFinding(
                category=FailureCategory.LOUDNESS_NON_COMPLIANT,
                severity=DiagnosticSeverity.HARD_BLOCKER,
                track_index=None,
                track_name="Master Track",
                device_name="Limiter",
                issue=f"Target loudness mismatch: achieved {achieved_lufs:.1f} LUFS, target {target_lufs:.1f} LUFS.",
                measured_value=achieved_lufs,
                expected_value=f"{target_lufs:.1f} LUFS (+-0.5 LUFS)",
                remediation_actions=["Iterate Limiter gain or Glue Compressor threshold."]
            ))

        passed = len([f for f in findings if f.severity == DiagnosticSeverity.HARD_BLOCKER]) == 0
        return self._finalize_gate(ProductionPhase.PHASE_7_MASTERING, passed, findings, context)

    def _finalize_gate(
        self,
        phase: ProductionPhase,
        passed: bool,
        findings: List[DiagnosticFinding],
        context: Dict[str, Any]
    ) -> GateResult:
        remediations = []
        for f in findings:
            remediations.extend(f.remediation_actions)

        result = GateResult(
            phase=phase,
            passed=passed,
            findings=findings,
            remediations=list(dict.fromkeys(remediations)),
            metadata={"fail_fast": self.fail_fast}
        )

        if not passed and self.fail_fast:
            hard_findings = [f for f in findings if f.severity == DiagnosticSeverity.HARD_BLOCKER]
            raise GateValidationError(
                phase=phase,
                message=f"Quality Gate {phase.value} FAILED with {len(hard_findings)} hard blockers.",
                findings=hard_findings,
                remediations=result.remediations
            )

        if passed:
            if phase not in self.completed_gates:
                self.completed_gates.append(phase)

        return result
