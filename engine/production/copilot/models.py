# engine/production/copilot/models.py
"""
Executive Copilot Data Models:
Defines the 7 formal production phases, decision status lifecycles,
and state snapshots that prevent selective amnesia and tool sprawl in LLMs.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


class ProductionPhase(str, Enum):
    PHASE_1_DNA = "PHASE_1_DNA"                              # Tempo, key, scale, genre, length
    PHASE_2_COMPOSITION = "PHASE_2_COMPOSITION"              # Chords, bassline, rhythm patterns, hook
    PHASE_3_SOUND_DESIGN = "PHASE_3_SOUND_DESIGN"            # VST3 plugins, Vital presets, drum kits
    PHASE_4_HUMANIZATION_GROOVE = "PHASE_4_HUMANIZATION_GROOVE" # Micro-timing, strumming, phrase evolver
    PHASE_5_ARRANGEMENT_TRANSITIONS = "PHASE_5_ARRANGEMENT_TRANSITIONS" # 64-bar timeline, ear candy, sweeps
    PHASE_6_MIX_ACOUSTICS = "PHASE_6_MIX_ACOUSTICS"          # Auto-sidechain, 3D depth, resonance hunter
    PHASE_7_MASTER_DELIVERY = "PHASE_7_MASTER_DELIVERY"      # 5-device chain, LUFS compliance, stem manifest


class DecisionStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    APPLIED = "APPLIED"


@dataclass
class ProductionDecision:
    id: str
    phase: ProductionPhase
    title: str
    description: str
    recommendation: str
    options: List[str] = field(default_factory=lambda: ["YES", "NO", "CUSTOM"])
    status: DecisionStatus = DecisionStatus.PENDING
    target_track: Optional[int] = None
    target_clip: Optional[int] = None
    action_tool: str = ""
    action_args: Dict[str, Any] = field(default_factory=dict)
    justification_if_rejected: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "phase": self.phase.value,
            "title": self.title,
            "description": self.description,
            "recommendation": self.recommendation,
            "options": self.options,
            "status": self.status.value,
            "target_track": self.target_track,
            "target_clip": self.target_clip,
            "action_tool": self.action_tool,
            "action_args": self.action_args,
            "justification_if_rejected": self.justification_if_rejected,
            "result": self.result
        }


@dataclass
class CopilotState:
    current_phase: ProductionPhase
    completed_phases: List[ProductionPhase] = field(default_factory=list)
    pending_decisions: List[ProductionDecision] = field(default_factory=list)
    resolved_decisions: List[ProductionDecision] = field(default_factory=list)
    progress_pct: float = 0.0
    blockers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_phase": self.current_phase.value,
            "completed_phases": [p.value for p in self.completed_phases],
            "pending_decisions_count": len(self.pending_decisions),
            "pending_decisions": [d.to_dict() for d in self.pending_decisions],
            "resolved_decisions_count": len(self.resolved_decisions),
            "progress_pct": round(self.progress_pct, 1),
            "blockers": self.blockers,
            "ready_for_master": len(self.blockers) == 0 and len(self.pending_decisions) == 0
        }
