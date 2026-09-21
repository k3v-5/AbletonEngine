# engine/arrangement/expectation_deviation_engine.py
"""
Expectation & Deviation Engine (Phase N):
Models musical psychology:
EXPECTATION ➔ PATTERN ESTABLISHED ➔ DEVIATION ➔ TENSION ➔ CONSEQUENCE ➔ RESOLUTION / NEW RULE

Transforms mechanical repetition into emotional storytelling:
Establishes clear rhythmic and harmonic patterns across repeated sections (e.g. Hooks 1 & 2),
then strategically shatters expectation on subsequent iterations (e.g. Hook 3),
instantly paying off the tension with an intentional, high-impact musical consequence.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
import copy
import logging

from engine.composition.compositional_dna import CompositionalDNA

logger = logging.getLogger("ExpectationDeviationEngine")


class ExpectationStage(str, Enum):
    EXPECTATION = "EXPECTATION"
    PATTERN_ESTABLISHED = "PATTERN_ESTABLISHED"
    DEVIATION = "DEVIATION"
    TENSION = "TENSION"
    CONSEQUENCE = "CONSEQUENCE"
    RESOLUTION_NEW_RULE = "RESOLUTION_NEW_RULE"


class DeviationMechanism(str, Enum):
    RHYTHMIC_VACUUM = "rhythmic_vacuum"                   # Sudden silence/void on expected beat (e.g. beat 2/3)
    HARMONIC_DECEPTIVE_TURN = "harmonic_deceptive_turn"   # Cadence deceptively broken to bVI or altered pivot
    MELODIC_REGISTER_DISPLACEMENT = "melodic_register"     # Melody vaults into soaring high octave
    TIMBRAL_STRIP = "timbral_strip"                       # Sudden muting of all midrange harmony


class ConsequenceReward(str, Enum):
    CLIMACTIC_BRASS_FANFARE = "climactic_brass_fanfare"   # Piercing brass/synth response answering the void
    EXPLOSIVE_808_DROP = "explosive_808_drop"             # Sub-bass detonation with delayed slide
    VOCAL_HOOK_EMBELLISHMENT = "vocal_hook_embellishment" # Soaring melismatic vocal answering the silence
    FULL_LAYER_EXPLOSION = "full_layer_explosion"         # Tutti release of all rhythmic & harmonic forces


@dataclass
class DeviationPlan:
    """The complete narrative strategy for breaking and rewarding expectation."""
    section_name: str
    repetition_index: int
    stage: ExpectationStage
    mechanism: DeviationMechanism
    deviation_description: str
    bar_offset: float
    duration_beats: float
    consequence: ConsequenceReward
    consequence_description: str
    tension_multiplier: float = 1.45
    narrative_rule: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_name": self.section_name,
            "repetition_index": self.repetition_index,
            "stage": self.stage.value,
            "mechanism": self.mechanism.value,
            "deviation_description": self.deviation_description,
            "bar_offset": self.bar_offset,
            "duration_beats": self.duration_beats,
            "consequence": self.consequence.value,
            "consequence_description": self.consequence_description,
            "tension_multiplier": round(self.tension_multiplier, 2),
            "narrative_rule": self.narrative_rule,
        }


class ExpectationDeviationEngine:
    """
    Directs psychological tension and surprise by tracking repeating musical structures.
    Enforces that ANY deviation from established expectations MUST deliver a commensurate payoff.
    """

    @classmethod
    def should_trigger_deviation(cls, section_name: str, repetition_count: int) -> bool:
        """
        Deviations are deployed once a pattern has been established (repetition >= 2).
        For example: Hook 1 and Hook 2 establish the pocket; Hook 3 introduces the rupture.
        """
        sec_lower = section_name.lower()
        if "hook" in sec_lower or "chorus" in sec_lower:
            return repetition_count >= 2
        elif "verse" in sec_lower:
            return repetition_count >= 2
        return False

    @classmethod
    def design_deviation(
        cls,
        section_name: str,
        repetition_count: int,
        dna: Optional[CompositionalDNA] = None
    ) -> DeviationPlan:
        """
        Creates a contextual deviation plan with an obligatory consequence.
        """
        sec_lower = section_name.lower()

        if "hook" in sec_lower or "chorus" in sec_lower:
            # Hook 3: The canonical Rhythmic Vacuum ➔ Brass Fanfare & Sub Detonation
            plan = DeviationPlan(
                section_name=section_name,
                repetition_index=repetition_count,
                stage=ExpectationStage.DEVIATION,
                mechanism=DeviationMechanism.RHYTHMIC_VACUUM,
                deviation_description=(
                    "El tercer hook utiliza ausencia rítmica (vacío total de kick y snare en compás 4, "
                    "tiempos 2 y 3) para romper la inercia hipnótica establecida en Hook 1 y Hook 2."
                ),
                bar_offset=3.0,  # At start of bar 4 (offset 3 bars from section start)
                duration_beats=2.0,
                consequence=ConsequenceReward.CLIMACTIC_BRASS_FANFARE,
                consequence_description=(
                    "Recompensa a la ruptura: En el tiempo 4 del vacío, estalla una fanfarria de brass "
                    "en octavas altas sincronizada con una detonación de 808 en el downbeat siguiente."
                ),
                tension_multiplier=1.60,
                narrative_rule="Hook 3 uses deliberate rhythmic absence as a high-impact tension trigger."
            )
        elif "verse" in sec_lower:
            # Verse 2: Harmonic Deceptive Turn ➔ Intimate Vocal Nakedness
            plan = DeviationPlan(
                section_name=section_name,
                repetition_index=repetition_count,
                stage=ExpectationStage.DEVIATION,
                mechanism=DeviationMechanism.HARMONIC_DECEPTIVE_TURN,
                deviation_description=(
                    "Verse 2 suspende la resolución esperada hacia la tónica en compás 6, "
                    "girando inesperadamente hacia el IV dórico con pedal tone de bajo."
                ),
                bar_offset=5.0,
                duration_beats=4.0,
                consequence=ConsequenceReward.VOCAL_HOOK_EMBELLISHMENT,
                consequence_description="Vocal melisma fills the suspended harmonic void with emotional intimacy.",
                tension_multiplier=1.35,
                narrative_rule="Verse 2 delays cadential closure to deepen narrative storytelling."
            )
        else:
            # General bridge/outro deviation: Timbral strip
            plan = DeviationPlan(
                section_name=section_name,
                repetition_index=repetition_count,
                stage=ExpectationStage.DEVIATION,
                mechanism=DeviationMechanism.TIMBRAL_STRIP,
                deviation_description="Sudden muting of midrange keys leaving bare foley and sub.",
                bar_offset=7.0,
                duration_beats=4.0,
                consequence=ConsequenceReward.FULL_LAYER_EXPLOSION,
                consequence_description="All tracks explode back at maximum dynamic velocity.",
                tension_multiplier=1.50,
                narrative_rule="Timbral contrast creates cathartic release."
            )

        return plan

    @classmethod
    def apply_rhythmic_vacuum(
        cls,
        drum_notes: List[Dict[str, Any]],
        vacuum_bar_start: float = 3.0,
        vacuum_beat_duration: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Cuts out kick and snare notes during the specified vacuum window,
        leaving either pure silence or subtle foley breath.
        """
        vacuum_start_beat = vacuum_bar_start * 4.0 + 1.0  # e.g. beat 13.0 (beat 2 of bar 4)
        vacuum_end_beat = vacuum_start_beat + vacuum_beat_duration

        filtered: List[Dict[str, Any]] = []
        for n in drum_notes:
            pitch = int(n.get("pitch", 36))
            start = float(n.get("start_time", 0.0))
            is_kick_or_snare = pitch in (36, 35, 38, 40, 37)

            if is_kick_or_snare and (vacuum_start_beat <= start < vacuum_end_beat):
                # Omit note (create the vacuum)
                continue
            filtered.append(copy.deepcopy(n))

        return filtered

    @classmethod
    def synthesize_consequence_fanfare(
        cls,
        tonal_center: str = "Eb",
        start_beat: float = 14.5,
        velocity: int = 112
    ) -> List[Dict[str, Any]]:
        """
        Generates the soaring brass fanfare answering the rhythmic vacuum.
        """
        # Eb minor pentatonic fanfare: Eb5, Gb5, Bb5, Db6, Eb6
        # Root MIDI for Eb5 = 75
        notes = [
            {"pitch": 75, "start_time": start_beat, "duration": 0.25, "velocity": velocity - 10},
            {"pitch": 78, "start_time": start_beat + 0.25, "duration": 0.25, "velocity": velocity - 5},
            {"pitch": 82, "start_time": start_beat + 0.50, "duration": 0.50, "velocity": velocity},
            {"pitch": 85, "start_time": start_beat + 1.00, "duration": 0.50, "velocity": velocity + 5},
            {"pitch": 87, "start_time": start_beat + 1.50, "duration": 1.50, "velocity": 125},
        ]
        return notes
