# engine/creative/evolution/models.py
"""
Data models and budget constraints for Closed-Loop Creative Evolution (Nivel S).
Defines:
- InterventionDomain & InterventionType (Strict multi-domain specialization).
- EvolutionBudget (Prevents endless destructive thrashing, bounded iterations).
- EvolutionSnapshot (Immutable state checkpoints for instant rollback).
- InterventionOrder & EvolutionResult.
"""

from __future__ import annotations
import uuid
import datetime
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional

from engine.creative.contextual_sonic_critic import ContextualAuditReport


class InterventionDomain(str, Enum):
    """The creative and technical domains capable of receiving intervention permission."""
    COMPOSITION = "composition"    # Motifs, pitch range, voicing, interval motion
    SOUND = "sound"                # Synthesis, DSP filtering, octave shift, sample re-mutation
    ARRANGEMENT = "arrangement"    # Layer muting, space yielding, sectional density
    MIX = "mix"                    # Fader balance, dynamic sidechain, stereo width narrowing
    PERFORMANCE = "performance"    # Intentional microtiming, pocket, velocity hierarchy, breathing


class InterventionType(str, Enum):
    """Specific corrective interventions dispatched to address root causes without relying solely on EQ."""
    # Arrangement Interventions
    ARRANGEMENT_SPACE_YIELDING = "arrangement_space_yielding"       # Mute/thin competing layers during vocal/lead
    ARRANGEMENT_DENSITY_THINNING = "arrangement_density_thinning"   # Remove redundant backing elements
    ARRANGEMENT_CONTRAST_LIFT = "arrangement_contrast_lift"         # Introduce new layer or structural drop

    # Sound Interventions
    SOUND_OCTAVE_TRANSPOSE = "sound_octave_transpose"               # Transpose instrument out of mud/vocal zone
    SOUND_MUD_CLEANSE = "sound_mud_cleanse"                         # Surgical high-pass or notch filter on sample
    SOUND_SAMPLE_REMUTATION = "sound_sample_remutation"             # Re-mutate sample using an alternate recipe
    SOUND_MONO_SUB_COLLAPSE = "sound_mono_sub_collapse"             # Collapse frequencies <120 Hz to mono

    # Composition Interventions
    COMPOSITION_MOTIF_DEVELOPMENT = "composition_motif_development" # Apply inversion, diminution or restatement
    COMPOSITION_VOICING_SPREAD = "composition_voicing_spread"       # Open harmonic voicings to clear frequency corridor

    # Mix Interventions
    MIX_DYNAMIC_SIDECHAIN = "mix_dynamic_sidechain"                 # Ducking triggered by vocal or kick
    MIX_STEREO_NARROW = "mix_stereo_narrow"                         # Narrow excessive stereo spread

    # Performance Interventions (Nivel T)
    PERFORMANCE_HUMANIZATION_POCKET = "performance_humanization_pocket" # Apply correlated groove pocket
    PERFORMANCE_PHRASE_BREATHING = "performance_phrase_breathing"       # Enforce phrase rubato and breath gaps
    PERFORMANCE_CHORD_STRUM = "performance_chord_strum"                 # Apply chord strumming with top voice accent


@dataclass
class EvolutionBudget:
    """
    Limits iterations and destructive interventions.
    Turns the engine into an optimizer with memory that halts when budget is exhausted.
    """
    max_iterations: int = 5
    max_structural_changes: int = 2
    max_sound_mutations: int = 3
    max_composition_mutations: int = 2
    max_layer_removals: int = 2

    consumed_iterations: int = 0
    consumed_structural_changes: int = 0
    consumed_sound_mutations: int = 0
    consumed_composition_mutations: int = 0
    consumed_layer_removals: int = 0

    def is_exhausted(self) -> bool:
        return self.consumed_iterations >= self.max_iterations

    def can_perform(self, intervention_type: InterventionType) -> bool:
        if self.is_exhausted():
            return False

        if intervention_type == InterventionType.ARRANGEMENT_CONTRAST_LIFT:
            return self.consumed_structural_changes < self.max_structural_changes
        elif intervention_type in [InterventionType.ARRANGEMENT_SPACE_YIELDING, InterventionType.ARRANGEMENT_DENSITY_THINNING]:
            return self.consumed_layer_removals < self.max_layer_removals
        elif intervention_type in [InterventionType.SOUND_OCTAVE_TRANSPOSE, InterventionType.SOUND_MUD_CLEANSE, InterventionType.SOUND_SAMPLE_REMUTATION]:
            return self.consumed_sound_mutations < self.max_sound_mutations
        elif intervention_type in [InterventionType.COMPOSITION_MOTIF_DEVELOPMENT, InterventionType.COMPOSITION_VOICING_SPREAD]:
            return self.consumed_composition_mutations < self.max_composition_mutations
        return True

    def record_consumption(self, intervention_type: InterventionType):
        self.consumed_iterations += 1
        if intervention_type == InterventionType.ARRANGEMENT_CONTRAST_LIFT:
            self.consumed_structural_changes += 1
        elif intervention_type in [InterventionType.ARRANGEMENT_SPACE_YIELDING, InterventionType.ARRANGEMENT_DENSITY_THINNING]:
            self.consumed_layer_removals += 1
        elif intervention_type in [InterventionType.SOUND_OCTAVE_TRANSPOSE, InterventionType.SOUND_MUD_CLEANSE, InterventionType.SOUND_SAMPLE_REMUTATION]:
            self.consumed_sound_mutations += 1
        elif intervention_type in [InterventionType.COMPOSITION_MOTIF_DEVELOPMENT, InterventionType.COMPOSITION_VOICING_SPREAD]:
            self.consumed_composition_mutations += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_iterations": self.max_iterations,
            "consumed_iterations": self.consumed_iterations,
            "max_structural_changes": self.max_structural_changes,
            "consumed_structural_changes": self.consumed_structural_changes,
            "max_sound_mutations": self.max_sound_mutations,
            "consumed_sound_mutations": self.consumed_sound_mutations,
            "max_composition_mutations": self.max_composition_mutations,
            "consumed_composition_mutations": self.consumed_composition_mutations,
            "max_layer_removals": self.max_layer_removals,
            "consumed_layer_removals": self.consumed_layer_removals,
            "is_exhausted": self.is_exhausted()
        }


@dataclass
class EvolutionSnapshot:
    """
    Immutable snapshot capturing the exact state of the section before an intervention.
    Guarantees deterministic rollback if an intervention degrades acoustic quality.
    """
    snapshot_id: str
    iteration: int
    section_name: str
    composition_hash: str
    arrangement_hash: str
    sonic_family_hash: str
    audio_hash: str
    critic_report: Optional[ContextualAuditReport]
    state_payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    @property
    def net_score(self) -> float:
        if self.critic_report:
            return self.critic_report.net_improvement_score
        return 0.0

    def compute_overall_fingerprint(self) -> str:
        combined = f"{self.composition_hash}|{self.arrangement_hash}|{self.sonic_family_hash}|{self.audio_hash}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "iteration": self.iteration,
            "section_name": self.section_name,
            "composition_hash": self.composition_hash,
            "arrangement_hash": self.arrangement_hash,
            "sonic_family_hash": self.sonic_family_hash,
            "audio_hash": self.audio_hash,
            "net_score": round(self.net_score, 3),
            "critic_verdict": self.critic_report.verdict.value if self.critic_report else None,
            "timestamp": self.timestamp,
        }


@dataclass
class InterventionOrder:
    """A formal order authorizing a specific domain to execute a bounded intervention."""
    order_id: str
    target_section: str
    domain: InterventionDomain
    intervention_type: InterventionType
    target_track_or_role: str
    reasoning: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "target_section": self.target_section,
            "domain": self.domain.value,
            "intervention_type": self.intervention_type.value,
            "target_track_or_role": self.target_track_or_role,
            "reasoning": self.reasoning,
            "parameters": dict(self.parameters),
            "timestamp": self.timestamp,
        }


@dataclass
class EvolutionResult:
    """The outcome of a multi-iteration creative evolution cycle."""
    success: bool
    section_name: str
    total_iterations: int
    best_snapshot: EvolutionSnapshot
    initial_snapshot: EvolutionSnapshot
    final_verdict: str
    budget_state: EvolutionBudget
    history: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def net_quality_delta(self) -> float:
        return round(self.best_snapshot.net_score - self.initial_snapshot.net_score, 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "section_name": self.section_name,
            "total_iterations": self.total_iterations,
            "initial_net_score": round(self.initial_snapshot.net_score, 3),
            "best_net_score": round(self.best_snapshot.net_score, 3),
            "net_quality_delta": self.net_quality_delta,
            "final_verdict": self.final_verdict,
            "budget": self.budget_state.to_dict(),
            "history": self.history,
        }
