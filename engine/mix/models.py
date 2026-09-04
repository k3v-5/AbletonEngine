"""
Domain models and dataclasses for Mix Intelligence Engine (Digital Ear).
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple


class Severity(str, Enum):
    INFO = "INFO"           # 0.00 - 0.29
    LOW = "LOW"             # 0.30 - 0.49
    MEDIUM = "MEDIUM"       # 0.50 - 0.69
    HIGH = "HIGH"           # 0.70 - 0.84
    CRITICAL = "CRITICAL"   # 0.85 - 1.00


def severity_from_score(score: float) -> Severity:
    score = max(0.0, min(1.0, float(score)))
    if score < 0.30:
        return Severity.INFO
    elif score < 0.50:
        return Severity.LOW
    elif score < 0.70:
        return Severity.MEDIUM
    elif score < 0.85:
        return Severity.HIGH
    else:
        return Severity.CRITICAL


class HeadroomClassification(str, Enum):
    MASTER_CLIPPING = "master_clipping"     # Peak or True Peak > 0.0 dBFS
    NEAR_CLIPPING = "near_clipping"         # -0.5 to 0.0 dBFS
    HEALTHY_HEADROOM = "healthy_headroom"   # -6.0 to -1.0 dBFS
    EXCESSIVE_HEADROOM = "excessive_headroom" # < -12.0 dBFS


class DynamicClassification(str, Enum):
    OVER_COMPRESSED = "over_compressed"
    HIGHLY_DYNAMIC = "highly_dynamic"
    TRANSIENT_HEAVY = "transient_heavy"
    BALANCED = "balanced"
    FLAT = "flat"


@dataclass
class FrequencyBandData:
    band_name: str
    f_min: float
    f_max: float
    energy_db: float
    relative_energy: float  # [0.0, 1.0] normalized to total energy
    peak_energy: float
    average_energy: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "band_name": self.band_name,
            "f_min": self.f_min,
            "f_max": self.f_max,
            "energy_db": round(self.energy_db, 2),
            "relative_energy": round(self.relative_energy, 4),
            "peak_energy": round(self.peak_energy, 2),
            "average_energy": round(self.average_energy, 2)
        }


@dataclass
class SpectralProfile:
    classification: str  # dark, bright, mid-heavy, sub-heavy, air-heavy, thin, dense
    confidence: float    # [0.0, 1.0]
    spectral_centroid: float # Hz
    spectral_rolloff: float  # Hz (85% energy)
    spectral_flatness: float # [0.0, 1.0]
    zero_crossing_rate: float
    band_energies: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "classification": self.classification,
            "confidence": round(self.confidence, 3),
            "spectral_centroid": round(self.spectral_centroid, 1),
            "spectral_rolloff": round(self.spectral_rolloff, 1),
            "spectral_flatness": round(self.spectral_flatness, 4),
            "zero_crossing_rate": round(self.zero_crossing_rate, 5),
            "band_energies": {k: round(v, 2) for k, v in self.band_energies.items()}
        }


@dataclass
class StereoFeatures:
    correlation: float          # [-1.0, 1.0]
    mid_energy_db: float
    side_energy_db: float
    width: float                # side_rms / mid_rms
    low_end_width: float        # stereo width below 120Hz
    high_end_width: float       # stereo width above 2kHz
    mono_energy_loss_db: float  # loss when summed to mono
    low_frequency_stereo_severity: float # [0.0, 1.0]
    mono_compatibility_warning: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correlation": round(self.correlation, 3),
            "mid_energy_db": round(self.mid_energy_db, 2),
            "side_energy_db": round(self.side_energy_db, 2),
            "width": round(self.width, 3),
            "low_end_width": round(self.low_end_width, 3),
            "high_end_width": round(self.high_end_width, 3),
            "mono_energy_loss_db": round(self.mono_energy_loss_db, 2),
            "low_frequency_stereo_severity": round(self.low_frequency_stereo_severity, 3),
            "mono_compatibility_warning": self.mono_compatibility_warning
        }


@dataclass
class TransientFeatures:
    attack_time_ms: float
    decay_time_ms: float
    transient_strength: float # [0.0, 1.0]
    body_energy: float
    peak_to_body_ratio: float
    onsets_per_second: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attack_time_ms": round(self.attack_time_ms, 2),
            "decay_time_ms": round(self.decay_time_ms, 2),
            "transient_strength": round(self.transient_strength, 3),
            "body_energy": round(self.body_energy, 4),
            "peak_to_body_ratio": round(self.peak_to_body_ratio, 3),
            "onsets_per_second": round(self.onsets_per_second, 2)
        }


@dataclass
class KickAnalysis:
    fundamental_hz: float
    transient_strength: float
    sub_energy_db: float
    body_energy_db: float
    click_energy_db: float
    decay_ms: float
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fundamental_hz": round(self.fundamental_hz, 1),
            "transient_strength": round(self.transient_strength, 3),
            "sub_energy_db": round(self.sub_energy_db, 2),
            "body_energy_db": round(self.body_energy_db, 2),
            "click_energy_db": round(self.click_energy_db, 2),
            "decay_ms": round(self.decay_ms, 1),
            "confidence": round(self.confidence, 3)
        }


@dataclass
class BassAnalysis:
    fundamental_hz: float
    harmonics_energy_ratio: float
    sub_energy_db: float
    low_end_stereo_width: float
    dynamic_variation_db: float
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fundamental_hz": round(self.fundamental_hz, 1),
            "harmonics_energy_ratio": round(self.harmonics_energy_ratio, 3),
            "sub_energy_db": round(self.sub_energy_db, 2),
            "low_end_stereo_width": round(self.low_end_stereo_width, 3),
            "dynamic_variation_db": round(self.dynamic_variation_db, 2),
            "confidence": round(self.confidence, 3)
        }


@dataclass
class VocalAnalysis:
    presence_db: float
    low_mid_energy_db: float
    sibilance_ratio: float
    dynamic_range_db: float
    stereo_width: float
    reverb_energy_estimate: float
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "presence_db": round(self.presence_db, 2),
            "low_mid_energy_db": round(self.low_mid_energy_db, 2),
            "sibilance_ratio": round(self.sibilance_ratio, 3),
            "dynamic_range_db": round(self.dynamic_range_db, 2),
            "stereo_width": round(self.stereo_width, 3),
            "reverb_energy_estimate": round(self.reverb_energy_estimate, 3),
            "confidence": round(self.confidence, 3)
        }


@dataclass
class AudioFeatures:
    duration: float
    sample_rate: int
    channels: int
    rms_db: float
    peak_db: float
    true_peak_db: float
    crest_factor: float
    lufs_integrated: float
    lufs_short_term: float
    lufs_momentary: float
    dynamic_range: float
    lra: float
    spectral_profile: SpectralProfile
    stereo: StereoFeatures
    transients: TransientFeatures
    headroom_class: HeadroomClassification
    dynamics_class: DynamicClassification

    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration": round(self.duration, 3),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "rms_db": round(self.rms_db, 2),
            "peak_db": round(self.peak_db, 2),
            "true_peak_db": round(self.true_peak_db, 2),
            "crest_factor": round(self.crest_factor, 2),
            "lufs_integrated": round(self.lufs_integrated, 2),
            "lufs_short_term": round(self.lufs_short_term, 2),
            "lufs_momentary": round(self.lufs_momentary, 2),
            "dynamic_range": round(self.dynamic_range, 2),
            "lra": round(self.lra, 2),
            "spectral_profile": self.spectral_profile.to_dict(),
            "stereo": self.stereo.to_dict(),
            "transients": self.transients.to_dict(),
            "headroom_class": self.headroom_class.value,
            "dynamics_class": self.dynamics_class.value
        }


@dataclass
class MaskingResult:
    masking_score: float              # [0.0, 1.0]
    frequency_overlap: float          # [0.0, 1.0] in 20-120Hz
    temporal_overlap: float           # [0.0, 1.0] kick transient vs bass onset
    energy_overlap: float             # [0.0, 1.0]
    phase_correlation: float          # [-1.0, 1.0] in low-end
    conflict_frequency_hz: float      # peak collision frequency
    severity: Severity
    evidence: List[str] = field(default_factory=list)
    probable_causes: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "masking_score": round(self.masking_score, 3),
            "frequency_overlap": round(self.frequency_overlap, 3),
            "temporal_overlap": round(self.temporal_overlap, 3),
            "energy_overlap": round(self.energy_overlap, 3),
            "phase_correlation": round(self.phase_correlation, 3),
            "conflict_frequency_hz": round(self.conflict_frequency_hz, 1),
            "severity": self.severity.value,
            "evidence": self.evidence,
            "probable_causes": self.probable_causes,
            "recommended_actions": self.recommended_actions
        }


@dataclass
class GenreProfile:
    name: str
    target_lufs: float
    target_true_peak: float
    target_crest_factor: float
    target_spectral_balance: Dict[str, float]  # relative band energy targets
    max_low_end_width: float
    sub_bass_mono_threshold: float

GENRE_PROFILES: Dict[str, GenreProfile] = {
    "melodic_techno": GenreProfile(
        name="melodic_techno",
        target_lufs=-8.5,
        target_true_peak=-0.5,
        target_crest_factor=8.0,
        target_spectral_balance={"20-60Hz": 0.22, "60-120Hz": 0.20, "120-400Hz": 0.18, "400-2kHz": 0.20, "2k-8kHz": 0.12, "8k-20kHz": 0.08},
        max_low_end_width=0.08,
        sub_bass_mono_threshold=0.10
    ),
    "house": GenreProfile(
        name="house",
        target_lufs=-9.0,
        target_true_peak=-0.5,
        target_crest_factor=9.0,
        target_spectral_balance={"20-60Hz": 0.18, "60-120Hz": 0.22, "120-400Hz": 0.20, "400-2kHz": 0.20, "2k-8kHz": 0.12, "8k-20kHz": 0.08},
        max_low_end_width=0.10,
        sub_bass_mono_threshold=0.12
    ),
    "tech_house": GenreProfile(
        name="tech_house",
        target_lufs=-8.0,
        target_true_peak=-0.3,
        target_crest_factor=7.5,
        target_spectral_balance={"20-60Hz": 0.20, "60-120Hz": 0.24, "120-400Hz": 0.18, "400-2kHz": 0.20, "2k-8kHz": 0.11, "8k-20kHz": 0.07},
        max_low_end_width=0.06,
        sub_bass_mono_threshold=0.08
    ),
    "deep_house": GenreProfile(
        name="deep_house",
        target_lufs=-10.0,
        target_true_peak=-0.8,
        target_crest_factor=10.0,
        target_spectral_balance={"20-60Hz": 0.20, "60-120Hz": 0.20, "120-400Hz": 0.22, "400-2kHz": 0.18, "2k-8kHz": 0.12, "8k-20kHz": 0.08},
        max_low_end_width=0.12,
        sub_bass_mono_threshold=0.15
    ),
    "trap": GenreProfile(
        name="trap",
        target_lufs=-7.5,
        target_true_peak=-0.2,
        target_crest_factor=7.0,
        target_spectral_balance={"20-60Hz": 0.28, "60-120Hz": 0.18, "120-400Hz": 0.14, "400-2kHz": 0.18, "2k-8kHz": 0.13, "8k-20kHz": 0.09},
        max_low_end_width=0.05,
        sub_bass_mono_threshold=0.05
    ),
    "drill": GenreProfile(
        name="drill",
        target_lufs=-7.0,
        target_true_peak=-0.1,
        target_crest_factor=6.5,
        target_spectral_balance={"20-60Hz": 0.30, "60-120Hz": 0.16, "120-400Hz": 0.14, "400-2kHz": 0.18, "2k-8kHz": 0.13, "8k-20kHz": 0.09},
        max_low_end_width=0.05,
        sub_bass_mono_threshold=0.05
    ),
    "phonk": GenreProfile(
        name="phonk",
        target_lufs=-6.5,
        target_true_peak=-0.1,
        target_crest_factor=5.5,
        target_spectral_balance={"20-60Hz": 0.25, "60-120Hz": 0.22, "120-400Hz": 0.18, "400-2kHz": 0.16, "2k-8kHz": 0.11, "8k-20kHz": 0.08},
        max_low_end_width=0.08,
        sub_bass_mono_threshold=0.08
    ),
    "hip_hop": GenreProfile(
        name="hip_hop",
        target_lufs=-9.0,
        target_true_peak=-0.5,
        target_crest_factor=8.5,
        target_spectral_balance={"20-60Hz": 0.24, "60-120Hz": 0.20, "120-400Hz": 0.18, "400-2kHz": 0.18, "2k-8kHz": 0.12, "8k-20kHz": 0.08},
        max_low_end_width=0.08,
        sub_bass_mono_threshold=0.10
    ),
    "pop": GenreProfile(
        name="pop",
        target_lufs=-8.5,
        target_true_peak=-0.5,
        target_crest_factor=8.5,
        target_spectral_balance={"20-60Hz": 0.16, "60-120Hz": 0.20, "120-400Hz": 0.20, "400-2kHz": 0.22, "2k-8kHz": 0.14, "8k-20kHz": 0.08},
        max_low_end_width=0.10,
        sub_bass_mono_threshold=0.10
    ),
    "cinematic": GenreProfile(
        name="cinematic",
        target_lufs=-14.0,
        target_true_peak=-1.0,
        target_crest_factor=14.0,
        target_spectral_balance={"20-60Hz": 0.20, "60-120Hz": 0.18, "120-400Hz": 0.20, "400-2kHz": 0.20, "2k-8kHz": 0.12, "8k-20kHz": 0.10},
        max_low_end_width=0.20,
        sub_bass_mono_threshold=0.20
    )
}


@dataclass
class MixContext:
    tempo: float = 124.0
    key: str = "C"
    genre: str = "melodic_techno"
    section: str = "DROP_1"
    active_roles: List[str] = field(default_factory=lambda: ["KICK", "BASS", "LEAD", "PAD", "DRUMS"])
    target_energy: float = 0.85
    reference_profile: Optional[GenreProfile] = None

    def __post_init__(self):
        if self.reference_profile is None:
            self.reference_profile = GENRE_PROFILES.get(self.genre, GENRE_PROFILES["melodic_techno"])


@dataclass
class MixIssue:
    issue_id: str
    category: str
    severity: Severity
    severity_score: float
    confidence: float
    target_roles: List[str]
    description: str
    evidence: List[str]
    probable_causes: List[str]
    recommended_actions: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "category": self.category,
            "severity": self.severity.value,
            "severity_score": round(self.severity_score, 3),
            "confidence": round(self.confidence, 3),
            "target_roles": self.target_roles,
            "description": self.description,
            "evidence": self.evidence,
            "probable_causes": self.probable_causes,
            "recommended_actions": self.recommended_actions
        }


@dataclass
class CorrectionAction:
    action_type: str  # SIDECHAIN, EQ_CUT, EQ_BOOST, GAIN_STAGING, BASS_ENVELOPE, STEREO_MONOING
    target_role: str
    parameter_name: str
    current_value: float
    target_value: float
    delta: float
    frequency: Optional[float] = None
    q: Optional[float] = None
    applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "target_role": self.target_role,
            "parameter_name": self.parameter_name,
            "current_value": round(self.current_value, 2),
            "target_value": round(self.target_value, 2),
            "delta": round(self.delta, 2),
            "frequency": round(self.frequency, 1) if self.frequency is not None else None,
            "q": round(self.q, 2) if self.q is not None else None,
            "applied": self.applied
        }


@dataclass
class CorrectionPlan:
    plan_id: str
    mode: str  # SAFE, ASSISTED, AUTONOMOUS
    target_issue: str
    actions: List[CorrectionAction]
    max_risk: float
    estimated_improvement: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "mode": self.mode,
            "target_issue": self.target_issue,
            "actions": [a.to_dict() for a in self.actions],
            "max_risk": round(self.max_risk, 3),
            "estimated_improvement": round(self.estimated_improvement, 3)
        }


@dataclass
class CorrectionEvaluation:
    plan_id: str
    target_issue: str
    before_score: float
    after_score: float
    score_delta: float
    metrics_improved: List[str]
    metrics_regressed: List[str]
    accepted: bool
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "target_issue": self.target_issue,
            "before_score": round(self.before_score, 3),
            "after_score": round(self.after_score, 3),
            "score_delta": round(self.score_delta, 3),
            "metrics_improved": self.metrics_improved,
            "metrics_regressed": self.metrics_regressed,
            "accepted": self.accepted,
            "reason": self.reason
        }
