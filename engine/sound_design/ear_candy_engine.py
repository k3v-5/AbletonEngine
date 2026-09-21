# engine/sound_design/ear_candy_engine.py
"""
Ear Candy Engine (Family 17):
Scans the arrangement for density valleys and transition gaps to strategically place
1-2 unforgettable micro-events without cluttering or fatiguing the mix.
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
import logging

from engine.production.contract.sonic_identity import SonicIdentityBudget

logger = logging.getLogger("EarCandyEngine")


class EarCandyType(str, Enum):
    REVERSE_PIANO_SWELL = "REVERSE_PIANO_SWELL"
    VOCAL_WHISPER_CHOP = "VOCAL_WHISPER_CHOP"
    DELAY_THROW_SPLASH = "DELAY_THROW_SPLASH"
    PITCH_DROP_GLIDE = "PITCH_DROP_GLIDE"
    BUFFER_GLITCH_BURST = "BUFFER_GLITCH_BURST"
    NOISE_SWEEP_VACUUM = "NOISE_SWEEP_VACUUM"
    MICRO_PERCUSSION_FILL = "MICRO_PERCUSSION_FILL"


@dataclass
class EarCandyOpportunity:
    """A detected gap in the arrangement where an ear candy micro-event can shine."""
    id: str
    section_name: str
    target_bar: int
    target_beat: float
    gap_duration_beats: float
    density_score: float         # 0.0 (total silence) to 1.0 (dense wall of sound)
    suggested_type: EarCandyType
    recipe_description: str
    narrative_justification: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "section_name": self.section_name,
            "target_bar": self.target_bar,
            "target_beat": round(self.target_beat, 1),
            "gap_duration_beats": round(self.gap_duration_beats, 1),
            "density_score": round(self.density_score, 2),
            "suggested_type": self.suggested_type.value if isinstance(self.suggested_type, EarCandyType) else str(self.suggested_type),
            "recipe_description": self.recipe_description,
            "narrative_justification": self.narrative_justification,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EarCandyOpportunity:
        type_str = data.get("suggested_type", "DELAY_THROW_SPLASH")
        try:
            cand_type = EarCandyType(type_str)
        except ValueError:
            cand_type = EarCandyType.DELAY_THROW_SPLASH
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            section_name=data.get("section_name", "Section"),
            target_bar=int(data.get("target_bar", 1)),
            target_beat=float(data.get("target_beat", 0.0)),
            gap_duration_beats=float(data.get("gap_duration_beats", 2.0)),
            density_score=float(data.get("density_score", 0.3)),
            suggested_type=cand_type,
            recipe_description=data.get("recipe_description", ""),
            narrative_justification=data.get("narrative_justification", ""),
        )


class EarCandyEngine:
    """
    Scans arrangement section diagnostics to locate structural valleys.
    Generates high-impact, non-repetitive micro-events strictly rationed
    against the SonicIdentityBudget.
    """

    MAX_SUGGESTED_EVENTS = 2  # Rule of gold: 1 or 2 memorable events, never saturation

    @classmethod
    def scan_for_valleys(
        cls,
        section_diagnostics: List[Dict[str, Any]],
        budget: Optional[SonicIdentityBudget] = None,
        max_events: int = MAX_SUGGESTED_EVENTS
    ) -> List[EarCandyOpportunity]:
        """
        Locates structural transitions where track density drops (e.g. pre-drops,
        bridge ends, verse tails) and suggests targeted ear candy.
        """
        opportunities: List[EarCandyOpportunity] = []

        for idx, sec in enumerate(section_diagnostics):
            density = float(sec.get("density_ratio", 0.8))
            s_name = sec.get("name", f"Section {idx + 1}")
            s_bars = int(sec.get("bars", 8))
            start_bar = int(sec.get("start_bar", idx * 8))

            # Valley detected if density is below 0.65 or if it's the last 2 bars of a section before a Hook
            is_transition_valley = False
            next_sec_name = section_diagnostics[idx + 1].get("name", "").lower() if idx + 1 < len(section_diagnostics) else ""

            if "hook" in next_sec_name or "chorus" in next_sec_name:
                is_transition_valley = True
            elif density <= 0.60:
                is_transition_valley = True

            if is_transition_valley:
                target_bar = start_bar + s_bars - 1  # Last bar before section boundary
                target_beat = float(target_bar) * 4.0

                if "bridge" in s_name.lower():
                    # Bridge to climax transition: vacuum noise sweep or reverse swell
                    cand = EarCandyOpportunity(
                        id=f"EC_VALLEY_BAR_{target_bar}",
                        section_name=s_name,
                        target_bar=target_bar,
                        target_beat=target_beat,
                        gap_duration_beats=4.0,
                        density_score=density,
                        suggested_type=EarCandyType.NOISE_SWEEP_VACUUM,
                        recipe_description="Pre-drop reverse vacuum suction created by reversing a reverb tail with HPF sweep.",
                        narrative_justification="Creates negative space directly preceding the Hook 3 climax drop."
                    )
                    opportunities.append(cand)
                elif "verse" in s_name.lower():
                    # Verse to hook: delay throw splash or pitch glide
                    cand = EarCandyOpportunity(
                        id=f"EC_VALLEY_BAR_{target_bar}",
                        section_name=s_name,
                        target_bar=target_bar,
                        target_beat=target_beat + 2.0,  # last 2 beats of the verse
                        gap_duration_beats=2.0,
                        density_score=density,
                        suggested_type=EarCandyType.DELAY_THROW_SPLASH,
                        recipe_description="1/8D Ping-pong delay throw splash on the final chord of the verse fading into the hook.",
                        narrative_justification="Bridges the conversational verse into the broad anthemic chorus."
                    )
                    opportunities.append(cand)

        # Enforce budget limit: maximum 1 or 2 events
        selected = opportunities[:max_events]

        if budget:
            # Check remaining ear candy budget
            remaining = max(0, budget.max_ear_candy_events - budget.used_ear_candy_events)
            selected = selected[:remaining]

        return selected
