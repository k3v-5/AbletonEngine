"""
Transition Engine:
Computes and injects transition descriptors between sections across the arrangement.
"""
from typing import List, Optional
from engine.arrangement.models.section import Section, SectionType
from engine.arrangement.transitions.models import TransitionDescriptor, TransitionType
from engine.arrangement.transitions.pre_drop import PreDropGenerator

class TransitionEngine:
    """Plans and applies seamless musical transitions based on section energy delta."""
    
    def plan_transitions(self, sections: List[Section]) -> List[TransitionDescriptor]:
        transitions: List[TransitionDescriptor] = []
        if len(sections) < 2:
            return transitions
            
        for i in range(len(sections) - 1):
            curr_sec = sections[i]
            next_sec = sections[i + 1]
            
            energy_delta = next_sec.energy - curr_sec.energy
            trans_bar = curr_sec.start_bar + curr_sec.bars - 1
            
            # Case 1: Entering a Drop (High tension transition)
            if next_sec.section_type == SectionType.DROP:
                # 2-beat or 4-beat pre-drop silence + snare fill
                t = PreDropGenerator.create_pre_drop(
                    from_section_idx=i,
                    to_section_idx=i + 1,
                    transition_bar=trans_bar,
                    silence_duration_beats=2.0
                )
                transitions.append(t)
                
            # Case 2: Entering a Build (Rising energy)
            elif next_sec.section_type == SectionType.BUILD:
                t = TransitionDescriptor(
                    from_section_idx=i,
                    to_section_idx=i + 1,
                    start_bar=trans_bar,
                    duration_bars=1.0,
                    transition_type=TransitionType.SWEEP_UP,
                    affected_roles=["riser", "fx", "hihat_closed"],
                    intensity=0.7,
                    description=f"Sweep up into Build section {i+1}."
                )
                transitions.append(t)
                
            # Case 3: Entering Breakdown (Energy drop / de-escalation)
            elif next_sec.section_type == SectionType.BREAKDOWN:
                t = TransitionDescriptor(
                    from_section_idx=i,
                    to_section_idx=i + 1,
                    start_bar=trans_bar,
                    duration_bars=1.0,
                    transition_type=TransitionType.FILTER_FADE,
                    affected_roles=["kick", "bass"],
                    intensity=0.8,
                    description=f"Filter fade and reverb tail into Breakdown {i+1}."
                )
                transitions.append(t)
                
            # Case 4: Entering Outro
            elif next_sec.section_type == SectionType.OUTRO:
                t = TransitionDescriptor(
                    from_section_idx=i,
                    to_section_idx=i + 1,
                    start_bar=trans_bar,
                    duration_bars=1.0,
                    transition_type=TransitionType.SWEEP_DOWN,
                    affected_roles=["lead", "chords"],
                    intensity=0.5,
                    description=f"De-escalation sweep down into Outro."
                )
                transitions.append(t)
                
            # Default / Phrase transition
            else:
                t = TransitionDescriptor(
                    from_section_idx=i,
                    to_section_idx=i + 1,
                    start_bar=trans_bar,
                    duration_bars=1.0,
                    transition_type=TransitionType.DRUM_FILL if energy_delta >= 0 else TransitionType.CROSSFADE,
                    affected_roles=["snare", "percussion"],
                    intensity=0.6,
                    description=f"Standard 1-bar fill transition."
                )
                transitions.append(t)
                
        return transitions
