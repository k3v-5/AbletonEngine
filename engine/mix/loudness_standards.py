"""
Formal DSP Measurement & Loudness Compliance Contract.
Complies with ITU-R BS.1770-5 and EBU R 128 (2023).

Architectural Principle:
Strict separation of four distinct concepts:
1. AUDIO SIGNAL: Discrete PCM time-domain samples.
2. MEASUREMENT: What did the audio physically measure? (LoudnessMeasurement)
3. PROFILE: What delivery targets/guardrails are we evaluating against? (LoudnessProfile)
4. COMPLIANCE: Does the measurement meet the selected profile? (ProfileCompliance)

No mixing of concerns: LoudnessAnalyzer only measures; LoudnessProfile evaluates.
"""
import math
import json
from enum import Enum
from dataclasses import dataclass, FrozenInstanceError
from typing import Optional, List, Dict, Any, Tuple


class MeasurementStatus(str, Enum):
    """Execution status and diagnostic result of a DSP loudness measurement."""
    VALID = "VALID"
    INVALID_INPUT = "INVALID_INPUT"
    INSUFFICIENT_DURATION = "INSUFFICIENT_DURATION"
    UNSUPPORTED_CHANNEL_LAYOUT = "UNSUPPORTED_CHANNEL_LAYOUT"
    NUMERIC_FAILURE = "NUMERIC_FAILURE"


class ProfileType(str, Enum):
    """Classification of delivery target authority."""
    STANDARD = "STANDARD"                  # Formal international normative standard (e.g. ITU, EBU R 128)
    RECOMMENDATION = "RECOMMENDATION"      # Industry/platform distribution guidance (e.g. Spotify, Apple AES TD1004)
    PIE_POLICY = "PIE_POLICY"              # Internal production engine acoustic target (e.g. Club / High Energy)


class MeasurementWindow(str, Enum):
    """Closed set of normative measurement integration windows."""
    MOMENTARY = "momentary"
    SHORT_TERM = "short_term"
    INTEGRATED = "integrated"
    TRUE_PEAK = "true_peak"
    SAMPLE_PEAK = "sample_peak"


class ChannelLayout(str, Enum):
    """Explicit speaker and channel configurations."""
    MONO = "mono"
    STEREO = "stereo"
    SURROUND_5_1 = "5.1"
    SURROUND_7_1 = "7.1"
    UNKNOWN = "unknown"


ALLOWED_MEASUREMENT_WINDOWS = {w.value for w in MeasurementWindow}
ALLOWED_CHANNEL_LAYOUTS = {c.value for c in ChannelLayout}


class UnknownLoudnessProfileError(KeyError):
    """Raised when an unrecognized loudness profile name is requested from the registry."""
    pass


@dataclass(frozen=True)
class MeasurementMetadata:
    """
    Provenance, algorithmic context, and format parameters for a loudness measurement.
    Immutable to guarantee historical audit integrity.
    """
    standard: str = "ITU-R BS.1770-5"
    standard_version: str = "BS.1770-5 (2023)"
    algorithm_version: str = "1.0.0"
    sample_rate: int = 44100
    bit_depth: int = 24
    channel_layout: str = "stereo"
    duration_seconds: float = 0.0
    measurement_window: str = "integrated"
    measurement_id: str = ""
    channels: int = 2
    true_peak_method: str = "4x_sinc_fir_annex2"
    loudness_algorithm: str = "bs1770_5_dual_gated"
    gating_enabled: bool = True
    reference_channel_weights: Tuple[float, ...] = (1.0, 1.0)

    def __post_init__(self):
        # Numeric validation
        if not isinstance(self.sample_rate, int) or self.sample_rate <= 0:
            raise ValueError(f"sample_rate must be a positive integer > 0, got {self.sample_rate}")
        if not isinstance(self.bit_depth, int) or self.bit_depth <= 0:
            raise ValueError(f"bit_depth must be a positive integer > 0, got {self.bit_depth}")
        if not isinstance(self.duration_seconds, (int, float)) or not math.isfinite(self.duration_seconds) or self.duration_seconds < 0:
            raise ValueError(f"duration_seconds must be a finite non-negative number >= 0, got {self.duration_seconds}")

        # String validation
        str_fields = {
            "standard": self.standard,
            "standard_version": self.standard_version,
            "algorithm_version": self.algorithm_version,
            "channel_layout": self.channel_layout,
            "measurement_window": self.measurement_window
        }
        for fname, val in str_fields.items():
            if not isinstance(val, str) or not val.strip():
                raise ValueError(f"Field '{fname}' must be a non-empty, non-whitespace string, got {repr(val)}")

        # Closed set validation
        if self.measurement_window not in ALLOWED_MEASUREMENT_WINDOWS:
            raise ValueError(
                f"Invalid measurement_window '{self.measurement_window}'. "
                f"Allowed values: {sorted(ALLOWED_MEASUREMENT_WINDOWS)}"
            )
        if self.channel_layout not in ALLOWED_CHANNEL_LAYOUTS:
            raise ValueError(
                f"Invalid channel_layout '{self.channel_layout}'. "
                f"Allowed values: {sorted(ALLOWED_CHANNEL_LAYOUTS)}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic dictionary serialization."""
        return {
            "standard": self.standard,
            "standard_version": self.standard_version,
            "algorithm_version": self.algorithm_version,
            "sample_rate": self.sample_rate,
            "bit_depth": self.bit_depth,
            "channel_layout": self.channel_layout,
            "duration_seconds": float(self.duration_seconds),
            "measurement_window": self.measurement_window,
            "measurement_id": self.measurement_id,
            "channels": self.channels,
            "true_peak_method": self.true_peak_method,
            "loudness_algorithm": self.loudness_algorithm,
            "gating_enabled": self.gating_enabled,
            "reference_channel_weights": list(self.reference_channel_weights)
        }


@dataclass(frozen=True, init=False)
class LoudnessMeasurement:
    """
    Acoustic loudness measurement strictly describing objective audio characteristics.
    Does not dictate whether the audio is acceptable, compliant, or 'too loud'.
    Immutable (frozen=True) to prevent post-measurement state tampering.
    """
    integrated_lufs: float
    short_term_lufs: float
    momentary_lufs: float
    loudness_range_lra: float
    true_peak_dbfs: float
    sample_peak_dbfs: float
    crest_factor_db: float
    measurement_valid: bool
    metadata: MeasurementMetadata
    status: MeasurementStatus
    true_peak_dbtp: float

    def __init__(
        self,
        integrated_lufs: float,
        short_term_lufs: float,
        momentary_lufs: float,
        loudness_range_lra: float,
        true_peak_dbfs: Optional[float] = None,
        sample_peak_dbfs: float = 0.0,
        crest_factor_db: float = 0.0,
        measurement_valid: bool = True,
        metadata: Optional[MeasurementMetadata] = None,
        status: MeasurementStatus = MeasurementStatus.VALID,
        true_peak_dbtp: Optional[float] = None,
    ):
        # Resolve true peak canonical representation
        resolved_tp = true_peak_dbtp if true_peak_dbtp is not None else (
            true_peak_dbfs if true_peak_dbfs is not None else 0.0
        )

        # Validate numeric finite values (Section 10 & 31: math.isfinite check)
        numeric_checks = {
            "integrated_lufs": integrated_lufs,
            "short_term_lufs": short_term_lufs,
            "momentary_lufs": momentary_lufs,
            "loudness_range_lra": loudness_range_lra,
            "true_peak_dbtp": resolved_tp,
            "sample_peak_dbfs": sample_peak_dbfs,
            "crest_factor_db": crest_factor_db
        }
        for field_name, val in numeric_checks.items():
            if not isinstance(val, (int, float)) or not math.isfinite(val):
                raise ValueError(f"Numeric DSP field '{field_name}' must be finite, got {val}")

        resolved_meta = metadata if metadata is not None else MeasurementMetadata()
        if not isinstance(resolved_meta, MeasurementMetadata):
            raise TypeError(f"metadata must be an instance of MeasurementMetadata, got {type(resolved_meta)}")

        resolved_status = status if isinstance(status, MeasurementStatus) else MeasurementStatus(str(status))

        # Assign via object.__setattr__ to support frozen dataclass initialization
        object.__setattr__(self, "integrated_lufs", float(integrated_lufs))
        object.__setattr__(self, "short_term_lufs", float(short_term_lufs))
        object.__setattr__(self, "momentary_lufs", float(momentary_lufs))
        object.__setattr__(self, "loudness_range_lra", float(loudness_range_lra))
        object.__setattr__(self, "true_peak_dbfs", float(resolved_tp))
        object.__setattr__(self, "true_peak_dbtp", float(resolved_tp))
        object.__setattr__(self, "sample_peak_dbfs", float(sample_peak_dbfs))
        object.__setattr__(self, "crest_factor_db", float(crest_factor_db))
        object.__setattr__(self, "measurement_valid", bool(measurement_valid))
        object.__setattr__(self, "metadata", resolved_meta)
        object.__setattr__(self, "status", resolved_status)

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic dictionary serialization."""
        return {
            "integrated_lufs": self.integrated_lufs,
            "short_term_lufs": self.short_term_lufs,
            "momentary_lufs": self.momentary_lufs,
            "loudness_range_lra": self.loudness_range_lra,
            "true_peak_dbtp": self.true_peak_dbtp,
            "true_peak_dbfs": self.true_peak_dbfs,
            "sample_peak_dbfs": self.sample_peak_dbfs,
            "crest_factor_db": self.crest_factor_db,
            "measurement_valid": self.measurement_valid,
            "status": self.status.value,
            "metadata": self.metadata.to_dict()
        }

    @property
    def lra(self) -> float:
        return self.loudness_range_lra

    @property
    def true_peak(self) -> float:
        return self.true_peak_dbtp

    @property
    def sample_peak(self) -> float:
        return self.sample_peak_dbfs

    @property
    def crest_factor(self) -> float:
        return self.crest_factor_db


@dataclass(frozen=True)
class ProfileCompliance:
    """
    Formal, immutable compliance evaluation of a LoudnessMeasurement against a LoudnessProfile.
    Deterministic, side-effect free result object (Section 15).
    """
    profile_name: str
    compliant: bool
    loudness_pass: bool
    true_peak_pass: bool
    lra_pass: bool
    clipping_pass: bool
    reasons: Tuple[str, ...]
    measured_lufs: float
    target_lufs: float
    loudness_delta_lu: float
    measured_true_peak_dbtp: float
    max_true_peak_dbtp: float

    # Backward compatibility properties with LoudnessComplianceResult & ProfileEvaluationResult
    @property
    def profile_compliant(self) -> bool:
        return self.compliant

    @property
    def target_met(self) -> bool:
        return self.loudness_pass

    @property
    def true_peak_safe(self) -> bool:
        return self.true_peak_pass

    @property
    def lra_compliant(self) -> bool:
        return self.lra_pass

    @property
    def measurement_valid(self) -> bool:
        return not any("MEASUREMENT_INVALID" in r for r in self.reasons)

    @property
    def loudness_error_lu(self) -> float:
        return self.loudness_delta_lu

    @property
    def lufs_delta(self) -> float:
        return self.loudness_delta_lu

    @property
    def true_peak_margin_db(self) -> float:
        return round(self.max_true_peak_dbtp - self.measured_true_peak_dbtp, 4)

    @property
    def true_peak_headroom_db(self) -> float:
        return self.true_peak_margin_db

    @property
    def violations(self) -> Tuple[str, ...]:
        return self.reasons

    @property
    def warnings(self) -> Tuple[str, ...]:
        return ()

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic serialization in stable order."""
        return {
            "profile_name": self.profile_name,
            "compliant": self.compliant,
            "profile_compliant": self.compliant,
            "loudness_pass": self.loudness_pass,
            "target_met": self.loudness_pass,
            "true_peak_pass": self.true_peak_pass,
            "true_peak_safe": self.true_peak_safe,
            "lra_pass": self.lra_pass,
            "lra_compliant": self.lra_pass,
            "clipping_pass": self.clipping_pass,
            "reasons": list(self.reasons),
            "violations": list(self.reasons),
            "warnings": [],
            "measured_lufs": self.measured_lufs,
            "target_lufs": self.target_lufs,
            "loudness_delta_lu": self.loudness_delta_lu,
            "lufs_delta": self.loudness_delta_lu,
            "measured_true_peak_dbtp": self.measured_true_peak_dbtp,
            "max_true_peak_dbtp": self.max_true_peak_dbtp,
            "true_peak_margin_db": self.true_peak_margin_db,
            "true_peak_headroom_db": self.true_peak_margin_db,
            "measurement_valid": self.measurement_valid
        }


# Backward compatibility aliases
LoudnessComplianceResult = ProfileCompliance
ProfileEvaluationResult = ProfileCompliance


@dataclass(frozen=True)
class LoudnessProfile:
    """
    Delivery specification against which a LoudnessMeasurement is evaluated.
    Centralizes acoustic targets, tolerances, and ceiling guardrails.
    Immutable to guarantee safety across pipeline stages.
    """
    name: str
    target_lufs: float
    tolerance_lufs: float
    max_true_peak_dbtp: float
    max_gain_reduction_db: float
    lra_target_min: Optional[float] = None
    lra_target_max: Optional[float] = None
    allow_clipping: bool = False
    policy_id: str = "STANDARD_DELIVERY"
    profile_type: ProfileType = ProfileType.STANDARD
    description: str = ""

    def __post_init__(self):
        # Name and policy validation
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"Profile name must be a non-empty string, got {repr(self.name)}")
        if not isinstance(self.policy_id, str) or not self.policy_id.strip():
            raise ValueError(f"policy_id must be a non-empty string, got {repr(self.policy_id)}")

        # Numeric validations (Section 14)
        if not math.isfinite(self.target_lufs):
            raise ValueError(f"target_lufs must be finite, got {self.target_lufs}")
        if not math.isfinite(self.tolerance_lufs) or self.tolerance_lufs < 0:
            raise ValueError(f"tolerance_lufs must be a finite non-negative number >= 0, got {self.tolerance_lufs}")
        if not math.isfinite(self.max_true_peak_dbtp):
            raise ValueError(f"max_true_peak_dbtp must be finite, got {self.max_true_peak_dbtp}")
        if not math.isfinite(self.max_gain_reduction_db) or self.max_gain_reduction_db < 0:
            raise ValueError(f"max_gain_reduction_db must be a finite non-negative number >= 0, got {self.max_gain_reduction_db}")

        if self.lra_target_min is not None:
            if not math.isfinite(self.lra_target_min) or self.lra_target_min < 0:
                raise ValueError(f"lra_target_min must be finite >= 0, got {self.lra_target_min}")
        if self.lra_target_max is not None:
            if not math.isfinite(self.lra_target_max) or self.lra_target_max < 0:
                raise ValueError(f"lra_target_max must be finite >= 0, got {self.lra_target_max}")
        if self.lra_target_min is not None and self.lra_target_max is not None:
            if self.lra_target_min > self.lra_target_max:
                raise ValueError(
                    f"lra_target_min ({self.lra_target_min}) cannot be greater than lra_target_max ({self.lra_target_max})"
                )

        # allow_clipping policy check
        if self.allow_clipping and self.policy_id != "PERMITTED_CLIPPING":
            raise ValueError(
                f"allow_clipping=True is rejected without an explicit permitted policy "
                f"(policy_id='PERMITTED_CLIPPING' required, got '{self.policy_id}')"
            )

    def evaluate(self, measurement: LoudnessMeasurement) -> ProfileCompliance:
        """
        Pure, deterministic, side-effect free evaluation of a LoudnessMeasurement.
        Returns ProfileCompliance (Section 15).
        """
        if not measurement.measurement_valid:
            return ProfileCompliance(
                profile_name=self.name,
                compliant=False,
                loudness_pass=False,
                true_peak_pass=False,
                lra_pass=False,
                clipping_pass=False,
                reasons=("MEASUREMENT_INVALID: Measurement is invalid or uncomputable.",),
                measured_lufs=measurement.integrated_lufs,
                target_lufs=self.target_lufs,
                loudness_delta_lu=0.0,
                measured_true_peak_dbtp=measurement.true_peak_dbtp,
                max_true_peak_dbtp=self.max_true_peak_dbtp
            )

        reasons: List[str] = []

        # 1. Loudness calculation: delta = measured - target (unrounded for precision, Section 30)
        loudness_delta_lu = float(measurement.integrated_lufs - self.target_lufs)
        loudness_pass = abs(loudness_delta_lu) <= (self.tolerance_lufs + 1e-9)
        if not loudness_pass:
            if loudness_delta_lu > 0:
                reasons.append(
                    f"LOUDNESS_OUT_OF_RANGE: Integrated loudness ({measurement.integrated_lufs:.3f} LUFS) "
                    f"exceeds target ({self.target_lufs:.1f} ± {self.tolerance_lufs:.1f} LUFS by +{loudness_delta_lu:.3f} LU)."
                )
            else:
                reasons.append(
                    f"LOUDNESS_OUT_OF_RANGE: Integrated loudness ({measurement.integrated_lufs:.3f} LUFS) "
                    f"is below target ({self.target_lufs:.1f} ± {self.tolerance_lufs:.1f} LUFS by {loudness_delta_lu:.3f} LU)."
                )

        # 2. True Peak check: measured <= ceiling
        true_peak_pass = measurement.true_peak_dbtp <= (self.max_true_peak_dbtp + 1e-9)
        if not true_peak_pass:
            margin = round(self.max_true_peak_dbtp - measurement.true_peak_dbtp, 3)
            reasons.append(
                f"TRUE_PEAK_EXCEEDED: True Peak ({measurement.true_peak_dbtp:.3f} dBTP) exceeds "
                f"ceiling of {self.max_true_peak_dbtp:.2f} dBTP (margin: {margin:.3f} dB)."
            )

        # 3. LRA check: min / max bounds
        lra_pass = True
        if self.lra_target_min is not None and measurement.loudness_range_lra < (self.lra_target_min - 1e-9):
            lra_pass = False
            reasons.append(
                f"LRA_BELOW_MINIMUM: Loudness Range LRA ({measurement.loudness_range_lra:.2f} LU) "
                f"is below required minimum ({self.lra_target_min:.1f} LU)."
            )
        if self.lra_target_max is not None and measurement.loudness_range_lra > (self.lra_target_max + 1e-9):
            lra_pass = False
            reasons.append(
                f"LRA_ABOVE_MAXIMUM: Loudness Range LRA ({measurement.loudness_range_lra:.2f} LU) "
                f"exceeds allowed maximum ({self.lra_target_max:.1f} LU)."
            )

        # 4. Clipping check
        clipping_pass = True
        if not self.allow_clipping and measurement.true_peak_dbtp > 1e-9:
            clipping_pass = False
            reasons.append(
                f"CLIPPING: True Peak inter-sample clipping detected ({measurement.true_peak_dbtp:.3f} dBTP > 0.0 dBTP)."
            )

        compliant = loudness_pass and true_peak_pass and lra_pass and clipping_pass

        return ProfileCompliance(
            profile_name=self.name,
            compliant=compliant,
            loudness_pass=loudness_pass,
            true_peak_pass=true_peak_pass,
            lra_pass=lra_pass,
            clipping_pass=clipping_pass,
            reasons=tuple(reasons),
            measured_lufs=measurement.integrated_lufs,
            target_lufs=self.target_lufs,
            loudness_delta_lu=loudness_delta_lu,
            measured_true_peak_dbtp=measurement.true_peak_dbtp,
            max_true_peak_dbtp=self.max_true_peak_dbtp
        )

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic serialization in stable order."""
        return {
            "name": self.name,
            "profile_type": self.profile_type.value,
            "policy_id": self.policy_id,
            "target_lufs": self.target_lufs,
            "tolerance_lufs": self.tolerance_lufs,
            "max_true_peak_dbtp": self.max_true_peak_dbtp,
            "max_gain_reduction_db": self.max_gain_reduction_db,
            "lra_target_min": self.lra_target_min,
            "lra_target_max": self.lra_target_max,
            "allow_clipping": self.allow_clipping,
            "description": self.description
        }


# ==============================================================================
# CANONICAL PROFILES (Section 21, 22, 23, 24)
# ==============================================================================

# 1. EBU R 128 (European Broadcast Standard)
# max_gain_reduction_db is a PIE internal mastering guardrail, not an ITU/EBU law.
EBU_R128 = LoudnessProfile(
    name="EBU_R128",
    target_lufs=-23.0,
    tolerance_lufs=0.5,
    max_true_peak_dbtp=-1.0,
    max_gain_reduction_db=2.0,
    lra_target_max=14.0,
    allow_clipping=False,
    policy_id="EBU_R128_BROADCAST",
    profile_type=ProfileType.STANDARD,
    description="EBU R 128 Broadcast Standard (-23.0 LUFS ±0.5, Max -1.0 dBTP, LRA <= 14.0 LU, PIE GR limit 2.0 dB)"
)

# 2. STREAMING (Commercial Platform Target)
# -14 LUFS is a PIE operational target, not a universal streaming law.
STREAMING = LoudnessProfile(
    name="STREAMING",
    target_lufs=-14.0,
    tolerance_lufs=1.0,
    max_true_peak_dbtp=-1.0,
    max_gain_reduction_db=2.5,
    lra_target_min=4.0,
    allow_clipping=False,
    policy_id="STREAMING_RECOMMENDATION",
    profile_type=ProfileType.RECOMMENDATION,
    description="Commercial Streaming Target (-14.0 LUFS ±1.0, Max -1.0 dBTP, Max Limiter GR 2.5 dB)"
)

# 3. CLUB (High Acoustic Energy / Sound System Target)
# CLUB is an internal PIE production profile, not an international universal standard.
CLUB = LoudnessProfile(
    name="CLUB",
    target_lufs=-7.5,
    tolerance_lufs=1.0,
    max_true_peak_dbtp=-0.3,
    max_gain_reduction_db=3.0,
    lra_target_min=3.0,
    allow_clipping=False,
    policy_id="PIE_CLUB_HIGH_ENERGY",
    profile_type=ProfileType.PIE_POLICY,
    description="PIE Production Profile: Club / DJ Target (-7.5 LUFS ±1.0, Max -0.3 dBTP, Crest Factor Preservation)"
)

# Additional profiles preserved for complete backward compatibility
DIGITAL_DOWNLOAD = LoudnessProfile(
    name="DIGITAL_DOWNLOAD",
    target_lufs=-9.0,
    tolerance_lufs=1.0,
    max_true_peak_dbtp=-0.5,
    max_gain_reduction_db=2.5,
    lra_target_min=4.0,
    allow_clipping=False,
    policy_id="DIGITAL_DOWNLOAD_RECOMMENDATION",
    profile_type=ProfileType.RECOMMENDATION,
    description="Digital Master Direct Distribution (-9.0 LUFS ±1.0, Max -0.5 dBTP)"
)

VIDEO = LoudnessProfile(
    name="VIDEO",
    target_lufs=-15.0,
    tolerance_lufs=1.0,
    max_true_peak_dbtp=-1.0,
    max_gain_reduction_db=2.0,
    allow_clipping=False,
    policy_id="VIDEO_SYNC_RECOMMENDATION",
    profile_type=ProfileType.RECOMMENDATION,
    description="Video & Film Streaming / Web Sync (-15.0 LUFS ±1.0, Max -1.0 dBTP)"
)

PREMASTER = LoudnessProfile(
    name="PREMASTER",
    target_lufs=-18.0,
    tolerance_lufs=2.0,
    max_true_peak_dbtp=-3.0,
    max_gain_reduction_db=0.0,
    allow_clipping=False,
    policy_id="PREMASTER_POLICY",
    profile_type=ProfileType.PIE_POLICY,
    description="Pre-master Delivery for External Mastering (-18.0 LUFS, True Peak <= -3.0 dBTP)"
)

# Canonical aliases
EBU_R128_PROFILE = EBU_R128
STREAMING_PROFILE = STREAMING
CLUB_PROFILE = CLUB
DIGITAL_DOWNLOAD_PROFILE = DIGITAL_DOWNLOAD
VIDEO_PROFILE = VIDEO
PREMASTER_PROFILE = PREMASTER


LOUDNESS_PROFILES: Dict[str, LoudnessProfile] = {
    "EBU_R128": EBU_R128,
    "STREAMING": STREAMING,
    "CLUB": CLUB,
    "DIGITAL_DOWNLOAD": DIGITAL_DOWNLOAD,
    "VIDEO": VIDEO,
    "PREMASTER": PREMASTER
}


def get_loudness_profile(name: str) -> LoudnessProfile:
    """
    Retrieves a loudness profile from the central registry.
    Raises UnknownLoudnessProfileError if the requested profile is not registered.
    """
    normalized = name.upper().replace("-", "_").replace(" ", "_")
    if normalized in LOUDNESS_PROFILES:
        return LOUDNESS_PROFILES[normalized]
    raise UnknownLoudnessProfileError(
        f"Unknown loudness profile: '{name}'. Available profiles: {list_loudness_profiles()}"
    )


def list_loudness_profiles() -> List[str]:
    """Returns the list of registered profile names in deterministic, sorted order."""
    return sorted(LOUDNESS_PROFILES.keys())


class ProfileRegistry:
    """
    Registry accessor class maintaining backward compatibility with legacy calls.
    """
    EBU_R128 = EBU_R128
    STREAMING = STREAMING
    CLUB = CLUB
    DIGITAL_DOWNLOAD = DIGITAL_DOWNLOAD
    VIDEO = VIDEO
    PREMASTER = PREMASTER

    _REGISTRY = LOUDNESS_PROFILES

    @classmethod
    def get(cls, name: str) -> LoudnessProfile:
        return get_loudness_profile(name)

    get_profile = get

    @classmethod
    def list_profiles(cls) -> List[str]:
        return list_loudness_profiles()
