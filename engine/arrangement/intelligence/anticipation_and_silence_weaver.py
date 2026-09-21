# engine/arrangement/intelligence/anticipation_and_silence_weaver.py
"""
Anticipation & Silence Weaver (Level J - Arrangement Intelligence):
Designs and inserts structural anticipations, dramatic silences, and phrase modulations.

Enforces the physical law of tension and release:
"El mayor impacto de un Drop no proviene de añadir más volumen,
sino de vaciar el compás previo para que el oído experimente la caída libre."
"""
from __future__ import annotations
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger("AnticipationAndSilenceWeaver")


class AnticipationType(str, Enum):
    PRE_DROP_VACUUM = "PRE_DROP_VACUUM"            # 1-2 beats of total drum/bass silence before hook
    PHRASE_BREATH = "PHRASE_BREATH"                # Organic foley or vocal inhalation cutoff
    CADENCE_EXTENSION = "CADENCE_EXTENSION"        # +1 bar harmonic elongation delaying arrival
    ACCELERATED_CONTRACTION = "ACCELERATED_CONTRACTION"  # -1 bar urgency acceleration
    FILTER_CHOKE_REVERSE = "FILTER_CHOKE_REVERSE"  # Lowpass cutoff clamping right before impact


@dataclass
class AnticipationEvent:
    """A planned structural anticipation or silence event in the arrangement."""
    event_id: str
    transition_name: str
    target_bar: int
    target_beat_offset: float     # Beat offset within the target bar (e.g. 2.0 = beats 3-4)
    duration_beats: float         # Length of the anticipation event
    event_type: AnticipationType
    affected_roles: List[str]     # e.g. ["KICK", "DRUMS", "BASS"]
    narrative_justification: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "transition_name": self.transition_name,
            "target_bar": self.target_bar,
            "target_beat_offset": self.target_beat_offset,
            "duration_beats": self.duration_beats,
            "event_type": self.event_type.value if isinstance(self.event_type, AnticipationType) else str(self.event_type),
            "affected_roles": list(self.affected_roles),
            "narrative_justification": self.narrative_justification,
        }


class AnticipationAndSilenceWeaver:
    """
    Scans arrangement transitions and weaves intentional pre-drop silences and pickups.
    """

    @classmethod
    def weave_anticipations(
        cls,
        sections: List[Dict[str, Any]]
    ) -> List[AnticipationEvent]:
        """
        Scans section boundaries and introduces strategic tension/silence drops.
        """
        events: List[AnticipationEvent] = []
        cur_bar = 1

        for idx, sec in enumerate(sections):
            s_name = sec.get("name", "Section")
            s_bars = int(sec.get("bars", 8))
            boundary_bar = cur_bar + s_bars - 1
            cur_bar += s_bars

            # Check what the next section is
            if idx + 1 < len(sections):
                next_sec = sections[idx + 1]
                next_name = str(next_sec.get("name", "")).lower()

                # Transition into Hook 1: Standard 2-beat vacuum cut
                if "hook 1" in next_name or ("hook" in next_name and idx == 1):
                    events.append(AnticipationEvent(
                        event_id=f"vac_{boundary_bar}",
                        transition_name=f"{s_name} ➔ {next_sec.get('name')}",
                        target_bar=boundary_bar,
                        target_beat_offset=2.0,  # Beats 3 and 4
                        duration_beats=2.0,
                        event_type=AnticipationType.PRE_DROP_VACUUM,
                        affected_roles=["KICK", "DRUMS", "BASS"],
                        narrative_justification="Vacuum dropout clears low-end air allowing Hook 1 to slam with visceral weight"
                    ))

                # Transition out of Bridge into Hook 3: Climax pre-drop vacuum + breath
                elif "hook 3" in next_name or ("hook" in next_name and "bridge" in s_name.lower()):
                    events.append(AnticipationEvent(
                        event_id=f"vac_climax_{boundary_bar}",
                        transition_name=f"{s_name} ➔ {next_sec.get('name')}",
                        target_bar=boundary_bar,
                        target_beat_offset=2.0,
                        duration_beats=2.0,
                        event_type=AnticipationType.PRE_DROP_VACUUM,
                        affected_roles=["KICK", "DRUMS", "BASS", "KEYS"],
                        narrative_justification="Complete arrangements vacuum: all accompaniment cuts to leave a single suspended vocal/shimmer breath"
                    ))
                    events.append(AnticipationEvent(
                        event_id=f"breath_{boundary_bar}",
                        transition_name=f"{s_name} ➔ {next_sec.get('name')}",
                        target_bar=boundary_bar,
                        target_beat_offset=3.5,  # Final 8th note
                        duration_beats=0.5,
                        event_type=AnticipationType.PHRASE_BREATH,
                        affected_roles=["TEXTURE"],
                        narrative_justification="Inhaled breath pickup immediately preceding the full arrangement explosion"
                    ))

        return events
