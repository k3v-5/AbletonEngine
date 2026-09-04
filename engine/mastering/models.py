"""
Domain models and dataclasses for Mastering Engine, Reference Matching, and Final QC.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple


class DeliveryTarget(str, Enum):
    STREAMING = "STREAMING"               # Target -14 to -10 LUFS, -1.0 dBTP
    CLUB = "CLUB"                         # Target -8 to -6.5 LUFS, -0.3 dBTP
    DIGITAL_DOWNLOAD = "DIGITAL_DOWNLOAD" # Target -10 to -8 LUFS, -0.5 dBTP
    VIDEO = "VIDEO"                       # Target -16 to -14 LUFS, -1.0 dBTP
    PREMASTER = "PREMASTER"               # Target analysis only (-3.0 dBTP headroom)


class MasteringMode(str, Enum):
    SAFE = "SAFE"             # Analysis & recommendations only
    ASSISTED = "ASSISTED"     # Low-risk adjustments with confirmation
    AUTONOMOUS = "AUTONOMOUS" # Closed loop analyze -> plan -> apply -> evaluate -> rollback/commit
    BALANCED = "BALANCED"     # Default balanced mastering mode


class QualityGate(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    WARN = "WARNING"
    FAIL = "FAIL"


@dataclass
class MasterReadiness:
    is_ready: bool
    status: str  # READY, NOT_READY, MIX_PROBLEM
    issues: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    mix_problems: List[str] = field(default_factory=list)
    is_already_compliant: bool = False
    headroom_db: float = 0.0
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_ready": self.is_ready,
            "status": self.status,
            "issues": self.issues,
            "reasons": self.reasons,
            "mix_problems": self.mix_problems,
            "is_already_compliant": self.is_already_compliant,
            "headroom_db": round(self.headroom_db, 1),
            "recommendation": self.recommendation
        }


@dataclass
class TonalDifferenceMap:
    deltas: Dict[str, float] = field(default_factory=dict)
    rms_spectral_gap: float = 0.0
    # Standard 7 bands: sub (20-60Hz), low (60-250Hz), low_mid (250-500Hz), mid (500-2kHz),
    # high_mid (2k-6kHz), presence (6k-10kHz), brilliance (10k-20kHz)

    def to_dict(self) -> Dict[str, Any]:
        return {k: round(v, 2) for k, v in self.deltas.items()}


@dataclass
class FinalQualityScore:
    overall: float
    tonal: float
    dynamics: float
    loudness: float
    stereo: float
    translation: float
    qc: float
    quality_gate: QualityGate
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def overall_score(self) -> float:
        return self.overall

    @property
    def tonal_balance_score(self) -> float:
        return self.tonal

    @property
    def dynamic_preservation_score(self) -> float:
        return self.dynamics

    @property
    def loudness_compliance_score(self) -> float:
        return self.loudness

    @property
    def stereo_integrity_score(self) -> float:
        return self.stereo

    @property
    def translation_score(self) -> float:
        return self.translation

    @property
    def gate(self) -> QualityGate:
        return self.quality_gate

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": round(self.overall, 1),
            "overall_score": round(self.overall, 1),
            "tonal": round(self.tonal, 1),
            "tonal_balance_score": round(self.tonal, 1),
            "dynamics": round(self.dynamics, 1),
            "dynamic_preservation_score": round(self.dynamics, 1),
            "loudness": round(self.loudness, 1),
            "loudness_compliance_score": round(self.loudness, 1),
            "stereo": round(self.stereo, 1),
            "stereo_integrity_score": round(self.stereo, 1),
            "translation": round(self.translation, 1),
            "translation_score": round(self.translation, 1),
            "qc": round(self.qc, 1),
            "quality_gate": self.quality_gate.value,
            "gate": self.quality_gate.value,
            "details": self.details
        }


@dataclass
class MasteringProfile:
    genre: str
    delivery_target: DeliveryTarget
    target_lufs_min: float
    target_lufs_max: float
    target_true_peak: float
    max_gain_reduction: float
    stereo_width_target: float
    sub_mono_cutoff_hz: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "genre": self.genre,
            "delivery_target": self.delivery_target.value,
            "target_lufs_range": [self.target_lufs_min, self.target_lufs_max],
            "target_true_peak": self.target_true_peak,
            "max_gain_reduction": self.max_gain_reduction,
            "stereo_width_target": self.stereo_width_target,
            "sub_mono_cutoff_hz": self.sub_mono_cutoff_hz
        }


@dataclass
class MasterAction:
    action_type: str  # EQ, COMPRESSOR, SATURATION, STEREO, LIMITER, DO_NOTHING
    device_name: str  # e.g. [MCP] Master EQ
    parameter_name: str
    target_value: float
    delta: float
    applied: bool = False
    parameters: Dict[str, Any] = field(default_factory=dict)
    bypass: bool = False
    rationale: str = ""
    expected_impact: str = ""

    def __post_init__(self):
        if not self.parameters and self.parameter_name:
            self.parameters = {self.parameter_name: self.target_value}

    @property
    def target_device(self) -> str:
        return self.device_name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "device_name": self.device_name,
            "target_device": self.device_name,
            "parameter_name": self.parameter_name,
            "target_value": round(self.target_value, 2) if isinstance(self.target_value, (int, float)) else self.target_value,
            "delta": round(self.delta, 2) if isinstance(self.delta, (int, float)) else self.delta,
            "applied": self.applied,
            "parameters": self.parameters,
            "bypass": self.bypass,
            "rationale": self.rationale,
            "expected_impact": self.expected_impact
        }


@dataclass
class MasterPlan:
    plan_id: str
    delivery_target: DeliveryTarget
    mode: MasteringMode
    actions: List[MasterAction] = field(default_factory=list)
    estimated_loudness_gain: float = 0.0
    estimated_dynamic_loss: float = 0.0
    is_do_nothing: bool = False
    target_lufs: float = -14.0
    tp_ceiling_dbtp: float = -1.0
    is_applied: bool = False

    @property
    def target(self) -> DeliveryTarget:
        return self.delivery_target

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "delivery_target": self.delivery_target.value,
            "target": self.delivery_target.value,
            "mode": self.mode.value,
            "actions": [a.to_dict() for a in self.actions],
            "estimated_loudness_gain": round(self.estimated_loudness_gain, 2),
            "estimated_dynamic_loss": round(self.estimated_dynamic_loss, 2),
            "is_do_nothing": self.is_do_nothing,
            "target_lufs": round(self.target_lufs, 1),
            "tp_ceiling_dbtp": round(self.tp_ceiling_dbtp, 2),
            "is_applied": self.is_applied
        }


@dataclass
class MasterHistoryEntry:
    version: str
    timestamp: float
    input_hash: str
    output_hash: str
    committed_changes: List[str]
    score_before: float
    score_after: float
    snapshot_id: str = ""
    target: Optional[DeliveryTarget] = None
    mode: Optional[MasteringMode] = None
    plan: Optional[MasterPlan] = None
    pre_features: Dict[str, Any] = field(default_factory=dict)
    post_features: Dict[str, Any] = field(default_factory=dict)
    score: Optional[FinalQualityScore] = None
    applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "timestamp": self.timestamp,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "committed_changes": self.committed_changes,
            "score_before": round(self.score_before, 1),
            "score_after": round(self.score_after, 1),
            "snapshot_id": self.snapshot_id,
            "applied": self.applied
        }
