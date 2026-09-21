# engine/arrangement/intelligence/layer_orchestrator.py
"""
Layer Orchestrator (Level J - Arrangement Intelligence):
Manages the dynamic entry, exit, and density of instrument layers across the arrangement timeline.

Enforces the law:
"No dos secciones análogas deben poseer exactamente la misma instrumentación o densidad."
- Verse 1: Minimalist foundation (Piano + Bass + Drums)
- Hook 1: Full statement (+ Lead Hook)
- Verse 2: Re-orchestration (Mutated piano + bass rhythmic shift, sans Lead)
- Hook 2: Elevated accent (Lead variation + secondary texture)
- Bridge: Radical reduction (Drums muted, sub in reserve, filtered solo instrument)
- Hook 3: Climax payoff (All layers active + Signature Sound + Climactic Motif)
- Outro: Structured layer peeling towards silence.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
import logging

logger = logging.getLogger("LayerOrchestrator")


@dataclass
class SectionLayerPlan:
    """The intended active layers and density target for a single section."""
    section_name: str
    bar_range: tuple[int, int]
    active_roles: Set[str]
    muted_roles: Set[str]
    target_density: float          # 0.0 to 1.0
    orchestration_rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_name": self.section_name,
            "bar_range": list(self.bar_range),
            "active_roles": sorted(list(self.active_roles)),
            "muted_roles": sorted(list(self.muted_roles)),
            "target_density": round(self.target_density, 2),
            "orchestration_rationale": self.orchestration_rationale,
        }


@dataclass
class LayerOrchestrationPlan:
    """Master blueprint for layer orchestration across all sections."""
    song_id: str
    section_plans: List[SectionLayerPlan] = field(default_factory=list)
    available_roles: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "song_id": self.song_id,
            "available_roles": sorted(list(self.available_roles)),
            "section_plans": [p.to_dict() for p in self.section_plans],
        }


class LayerOrchestrator:
    """
    Orchestrates layer activation, prevents monotony, and enforces sectional contrast.
    """

    STANDARD_ROLE_TEMPLATES = {
        "intro": {
            "active": {"KEYS", "TEXTURE"},
            "muted": {"KICK", "DRUMS", "BASS", "LEAD", "STRINGS", "SIGNATURE"},
            "density": 0.25,
            "rationale": "Sparse atmospheric opening establishing harmony and tone"
        },
        "verse 1": {
            "active": {"KEYS", "KICK", "DRUMS", "BASS"},
            "muted": {"LEAD", "STRINGS", "SIGNATURE"},
            "density": 0.50,
            "rationale": "Groove foundation leaving ample vocal lane space"
        },
        "hook 1": {
            "active": {"KEYS", "KICK", "DRUMS", "BASS", "LEAD", "SIGNATURE"},
            "muted": {"STRINGS"},
            "density": 0.80,
            "rationale": "Full energy hook anthem with lead vocal/instrument celebration"
        },
        "verse 2": {
            "active": {"KEYS", "KICK", "BASS", "TEXTURE"},
            "muted": {"DRUMS", "LEAD", "SIGNATURE"},
            "density": 0.55,
            "rationale": "Re-orchestrated verse: drum loops pulled back, bass syncopation highlighted"
        },
        "hook 2": {
            "active": {"KEYS", "KICK", "DRUMS", "BASS", "LEAD", "STRINGS"},
            "muted": {},
            "density": 0.85,
            "rationale": "Enriched hook adding orchestral strings to heighten emotional investment"
        },
        "bridge": {
            "active": {"KEYS", "STRINGS", "SIGNATURE"},
            "muted": {"KICK", "DRUMS", "BASS", "LEAD"},
            "density": 0.30,
            "rationale": "Radical vacuum reduction: rhythm dropped out to build unbearable anticipation"
        },
        "hook 3": {
            "active": {"KEYS", "KICK", "DRUMS", "BASS", "LEAD", "STRINGS", "SIGNATURE", "TEXTURE"},
            "muted": {},
            "density": 0.95,
            "rationale": "Ultimate climax: every layer firing in harmonic cohesion"
        },
        "outro": {
            "active": {"KEYS", "TEXTURE", "SIGNATURE"},
            "muted": {"KICK", "DRUMS", "BASS", "LEAD", "STRINGS"},
            "density": 0.20,
            "rationale": "Layer peeling: decaying reverb tails and quiet resolution"
        },
    }

    @classmethod
    def generate_orchestration_plan(
        cls,
        sections: List[Dict[str, Any]],
        available_roles: Optional[Set[str]] = None,
        song_id: str = "default_song"
    ) -> LayerOrchestrationPlan:
        """
        Creates a coherent, non-static orchestration roadmap across the song timeline.
        """
        roles = available_roles or {"KICK", "DRUMS", "BASS", "KEYS", "LEAD", "STRINGS", "TEXTURE", "SIGNATURE"}
        plans: List[SectionLayerPlan] = []
        cur_bar = 1

        for sec in sections:
            s_name = sec.get("name", "Section")
            s_bars = int(sec.get("bars", 8))
            end_bar = cur_bar + s_bars - 1
            s_low = s_name.lower().strip()

            matched_template = None
            for k, tmpl in cls.STANDARD_ROLE_TEMPLATES.items():
                if k in s_low:
                    matched_template = tmpl
                    break

            if not matched_template:
                matched_template = {
                    "active": set(roles),
                    "muted": set(),
                    "density": 0.60,
                    "rationale": f"Custom balanced orchestration for {s_name}"
                }

            active = set(matched_template["active"]).intersection(roles)
            muted = roles - active

            plans.append(SectionLayerPlan(
                section_name=s_name,
                bar_range=(cur_bar, end_bar),
                active_roles=active,
                muted_roles=muted,
                target_density=float(matched_template["density"]),
                orchestration_rationale=matched_template["rationale"],
            ))
            cur_bar = end_bar + 1

        return LayerOrchestrationPlan(
            song_id=song_id,
            section_plans=plans,
            available_roles=roles
        )

    @classmethod
    def audit_contrast_between_sections(
        cls,
        plan_a: SectionLayerPlan,
        plan_b: SectionLayerPlan
    ) -> Dict[str, Any]:
        """
        Checks if two sections are differentiated in their layer orchestration.
        """
        active_diff = plan_a.active_roles.symmetric_difference(plan_b.active_roles)
        density_delta = abs(plan_a.target_density - plan_b.target_density)
        is_distinct = len(active_diff) > 0 or density_delta >= 0.15

        return {
            "section_a": plan_a.section_name,
            "section_b": plan_b.section_name,
            "role_differences": sorted(list(active_diff)),
            "density_delta": round(density_delta, 2),
            "is_distinct": is_distinct,
            "verdict": "DIFFERENTIATED" if is_distinct else "STATIC_LAYER_DUPLICATE"
        }
