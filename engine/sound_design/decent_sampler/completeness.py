# engine/sound_design/decent_sampler/completeness.py
"""
AI Sound Design Completeness Auditor & "Definition of Done" for Decent Sampler.

Inspects Decent Sampler instruments created or modified by AI agents to guarantee:
1. No forgotten or orphaned configurations (e.g. effects without knobs, unbound modulators).
2. Acoustic hygiene (anti-click envelopes, sensible release tails).
3. Expressive musical response (velocity tracking, dynamic layers).
4. Physical mapping integrity (gapless keyboard coverage, safe transposition bounds).
5. Headroom & Gain-Staging safety (prevents digital clipping in DAW master bus).
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
import math

from .model import InstrumentModel, GroupModel, SampleZoneModel, EffectModel, ControlModel
from .schema import DecentSamplerSchema
from .policies import AudioSafetyPolicy


@dataclass
class CompletenessIssue:
    """Represents a specific design omission or acoustic risk found in an instrument."""
    category: str        # 'envelope', 'effects', 'mapping', 'dynamics', 'gain_staging'
    severity: str        # 'error' (must fix for production), 'warning' (sub-optimal)
    description: str
    auto_fixable: bool = True
    suggested_fix: str = ""


@dataclass
class CompletenessReport:
    """Detailed audit report describing instrument readiness for professional studio use."""
    is_production_ready: bool = True
    issues: List[CompletenessIssue] = field(default_factory=list)
    auto_fixes_applied: List[str] = field(default_factory=list)

    @property
    def errors(self) -> List[str]:
        return [i.description for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[str]:
        return [i.description for i in self.issues if i.severity == "warning"]

    @property
    def missing_configurations(self) -> List[str]:
        return [i.description for i in self.issues if i.category in ("effects", "envelope") and i.severity == "error"]

    @property
    def acoustic_risks(self) -> List[str]:
        return [i.description for i in self.issues if i.category in ("gain_staging", "mapping", "envelope") and i.severity in ("error", "warning")]

    def add_issue(self, category: str, severity: str, description: str, auto_fixable: bool = True, suggested_fix: str = ""):
        self.issues.append(CompletenessIssue(
            category=category,
            severity=severity,
            description=description,
            auto_fixable=auto_fixable,
            suggested_fix=suggested_fix,
        ))
        if severity == "error":
            self.is_production_ready = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_production_ready": self.is_production_ready,
            "total_issues": len(self.issues),
            "errors": [i.description for i in self.issues if i.severity == "error"],
            "warnings": [i.description for i in self.issues if i.severity == "warning"],
            "missing_configurations": self.missing_configurations,
            "acoustic_risks": self.acoustic_risks,
            "auto_fixes_applied": self.auto_fixes_applied,
        }


class InstrumentCompletenessAuditor:
    """
    Production Readiness Auditor.
    Acts as the final quality gate before exporting instruments to Ableton.
    """

    MAX_SAFE_TRANSPOSITION_SEMITONES = 24  # 2 octaves max pitch stretch
    MAX_SAFE_SUMMED_GAIN_FACTOR = 1.5      # ~ +3.5 dBFS before polyphony warning

    @classmethod
    def audit(cls, instrument: InstrumentModel) -> CompletenessReport:
        """Runs the complete suite of completeness and acoustic safety audits."""
        report = CompletenessReport()

        if not instrument.groups or instrument.total_samples() == 0:
            report.add_issue(
                category="mapping",
                severity="error",
                description="Instrument has no sample zones mapped.",
                auto_fixable=False,
                suggested_fix="Add at least one sample zone to a group."
            )
            return report

        cls._audit_envelopes(instrument, report)
        cls._audit_orphaned_effects(instrument, report)
        cls._audit_sample_mapping(instrument, report)
        cls._audit_dynamics_and_velocity(instrument, report)
        cls._audit_gain_staging(instrument, report)
        cls._audit_round_robin_balance(instrument, report)

        return report

    # ------------------------------------------------------------------------
    # 1. ENVELOPE AUDIT
    # ------------------------------------------------------------------------
    @classmethod
    def _audit_envelopes(cls, instrument: InstrumentModel, report: CompletenessReport):
        for idx, group in enumerate(instrument.groups):
            grp_name = group.name or f"Group[{idx}]"
            if not group.amp_env_enabled:
                report.add_issue(
                    category="envelope",
                    severity="warning",
                    description=f"{grp_name}: Amplitude envelope is disabled; voice will play unshaped audio.",
                    suggested_fix="Enable ampEnvEnabled='true'."
                )
                continue

            # Anti-click attack floor
            if group.attack < AudioSafetyPolicy.RECOMMENDED_MIN_ATTACK_SEC:
                report.add_issue(
                    category="envelope",
                    severity="error",
                    description=f"{grp_name}: Attack time ({group.attack:.5f}s) is below 1ms anti-click threshold; high risk of DC pop.",
                    suggested_fix=f"Set attack to at least {AudioSafetyPolicy.RECOMMENDED_MIN_ATTACK_SEC}s."
                )

            # Note-off release tail
            if group.release <= 0.0:
                report.add_issue(
                    category="envelope",
                    severity="error",
                    description=f"{grp_name}: Release time is 0.0s; note will cut off instantly with an audible click upon key release.",
                    suggested_fix="Set release to at least 0.005s (or 0.05s - 0.3s for natural instrument decay)."
                )

    # ------------------------------------------------------------------------
    # 2. ORPHANED EFFECTS AUDIT
    # ------------------------------------------------------------------------
    @classmethod
    def _audit_orphaned_effects(cls, instrument: InstrumentModel, report: CompletenessReport):
        """Checks if any effect has been instantiated without a corresponding UI control or binding."""
        # Collect all parameters bound in UI controls
        bound_effects: Set[int] = set()
        for ctrl in instrument.ui.controls:
            for b in ctrl.bindings:
                if b.type == "effect" and b.level == "instrument" and b.position is not None:
                    bound_effects.add(b.position)

        for idx, effect in enumerate(instrument.effects):
            eff_type = effect.type.lower()
            if idx not in bound_effects:
                # If an effect has static non-default parameters it might be intentional,
                # but adding an effect without a UI knob is typically an AI omission.
                report.add_issue(
                    category="effects",
                    severity="warning",
                    description=(
                        f"Instrument-level effect[{idx}] '{eff_type}' has no UI control binding. "
                        "The producer will not be able to tweak or automate this effect in the DAW."
                    ),
                    suggested_fix=f"Add a UI knob bound to effect position={idx}."
                )

    # ------------------------------------------------------------------------
    # 3. SAMPLE MAPPING INTEGRITY & PITCH STRETCH
    # ------------------------------------------------------------------------
    @classmethod
    def _audit_sample_mapping(cls, instrument: InstrumentModel, report: CompletenessReport):
        all_samples: List[SampleZoneModel] = []
        for g in instrument.groups:
            all_samples.extend(g.samples)

        covered_notes: Set[int] = set()
        extreme_stretch_count = 0

        for s in all_samples:
            covered_notes.update(range(s.lo_note, s.hi_note + 1))
            stretch_down = s.root_note - s.lo_note
            stretch_up = s.hi_note - s.root_note
            if max(stretch_down, stretch_up) > cls.MAX_SAFE_TRANSPOSITION_SEMITONES:
                extreme_stretch_count += 1

        if extreme_stretch_count > 0:
            report.add_issue(
                category="mapping",
                severity="warning",
                description=(
                    f"{extreme_stretch_count} sample zone(s) have root transposition > {cls.MAX_SAFE_TRANSPOSITION_SEMITONES} semitones. "
                    "Extreme pitching causes unnatural formant shift and metallic aliasing."
                ),
                suggested_fix="Narrow sample zone note spans or add intermediate pitch samples."
            )

        if covered_notes:
            min_note = min(covered_notes)
            max_note = max(covered_notes)
            missing_in_range = [n for n in range(min_note, max_note + 1) if n not in covered_notes]
            if missing_in_range:
                report.add_issue(
                    category="mapping",
                    severity="error",
                    description=(
                        f"Keyboard range [{min_note}..{max_note}] contains {len(missing_in_range)} unmapped silent notes "
                        f"(e.g. MIDI {missing_in_range[:5]}...)."
                    ),
                    suggested_fix="Expand adjacent sample loNote/hiNote bounds to eliminate silent dead zones."
                )

    # ------------------------------------------------------------------------
    # 4. DYNAMICS & VELOCITY RESPONSE
    # ------------------------------------------------------------------------
    @classmethod
    def _audit_dynamics_and_velocity(cls, instrument: InstrumentModel, report: CompletenessReport):
        for idx, group in enumerate(instrument.groups):
            grp_name = group.name or f"Group[{idx}]"
            # If amp_vel_track is 0 and there is only 1 velocity zone, instrument is static
            vel_layers = set((s.lo_vel, s.hi_vel) for s in group.samples)
            if group.amp_vel_track == 0.0 and len(vel_layers) <= 1:
                report.add_issue(
                    category="dynamics",
                    severity="warning",
                    description=(
                        f"{grp_name}: Has ampVelTrack='0.0' and only {len(vel_layers)} velocity layer. "
                        "Instrument will sound completely static regardless of how hard keys are played."
                    ),
                    suggested_fix="Set ampVelTrack to a value between 0.7 and 1.0, or create multi-velocity sample layers."
                )

    # ------------------------------------------------------------------------
    # 5. GAIN-STAGING & HEADROOM
    # ------------------------------------------------------------------------
    @classmethod
    def _audit_gain_staging(cls, instrument: InstrumentModel, report: CompletenessReport):
        # Calculate maximum potential linear amplitude across simultaneous groups
        simultaneous_gain = 0.0
        for group in instrument.groups:
            if not group.enabled:
                continue
            if group.seq_mode in ("always", "true_random"):
                simultaneous_gain += group.volume
            elif group.seq_mode == "round_robin":
                # Only 1 round robin group plays at a time
                simultaneous_gain = max(simultaneous_gain, group.volume)

        total_gain = simultaneous_gain * instrument.volume

        if total_gain > cls.MAX_SAFE_SUMMED_GAIN_FACTOR:
            excess_db = DecentSamplerSchema.gain_to_db(total_gain)
            report.add_issue(
                category="gain_staging",
                severity="warning",
                description=(
                    f"Combined group gain ({total_gain:.2f}x / +{excess_db} dBFS) exceeds safe headroom. "
                    "Polyphonic playback will likely clip/distort in the DAW master bus."
                ),
                suggested_fix="Normalize group volumes or reduce instrument master volume."
            )

    # ------------------------------------------------------------------------
    # 6. ROUND-ROBIN UNIFORMITY
    # ------------------------------------------------------------------------
    @classmethod
    def _audit_round_robin_balance(cls, instrument: InstrumentModel, report: CompletenessReport):
        rr_groups = [g for g in instrument.groups if g.seq_mode == "round_robin"]
        if len(rr_groups) > 1:
            sample_counts = [len(g.samples) for g in rr_groups]
            if len(set(sample_counts)) > 1:
                report.add_issue(
                    category="mapping",
                    severity="warning",
                    description=(
                        f"Round-robin groups have uneven sample counts {sample_counts}. "
                        "Alternating notes will have inconsistent timbres or silent dropouts."
                    ),
                    suggested_fix="Ensure all round-robin groups contain the same set of sampled pitches."
                )
