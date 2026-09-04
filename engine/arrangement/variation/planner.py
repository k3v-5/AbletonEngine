"""
Variation Planner:
Assigns transformational strategies to musical motifs across song sections.
Prevents monotony by scheduling musical operations: inversion, retrograde, rhythmic augmentation/diminution.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
from engine.arrangement.models.section import Section, SectionType

@dataclass
class VariationDirective:
    section_index: int
    role: str
    technique: str  # "original", "inversion", "retrograde", "augmentation", "diminution", "rhythmic_syncopation", "octave_shift"
    intensity: float  # 0.0 to 1.0
    notes: str = ""

class VariationPlanner:
    """Plans how musical motifs evolve across the song sections."""
    
    TECHNIQUES = [
        "original", "rhythmic_syncopation", "octave_shift",
        "inversion", "retrograde", "augmentation", "diminution"
    ]
    
    def plan_variations(self, sections: List[Section], active_roles: List[str]) -> Dict[int, List[VariationDirective]]:
        """Assigns variation directives per section to maintain progressive interest."""
        directives: Dict[int, List[VariationDirective]] = {}
        drop_count = 0
        
        for idx, sec in enumerate(sections):
            directives[idx] = []
            if sec.section_type == SectionType.DROP:
                drop_count += 1
                if drop_count == 1:
                    # Drop 1: Present primary theme / groove
                    for r in active_roles:
                        directives[idx].append(VariationDirective(
                            section_index=idx, role=r, technique="original", intensity=0.0,
                            notes="Primary motif statement."
                        ))
                else:
                    # Drop 2+: Add rhythmic syncopation, octave shift, or melodic variation
                    for r in active_roles:
                        tech = "octave_shift" if r in ["lead", "arp"] else "rhythmic_syncopation"
                        directives[idx].append(VariationDirective(
                            section_index=idx, role=r, technique=tech, intensity=0.8,
                            notes="Escalated variation with counter-accents."
                        ))
            elif sec.section_type == SectionType.BUILD:
                for r in active_roles:
                    if r in ["snare", "hihat_closed", "arp"]:
                        directives[idx].append(VariationDirective(
                            section_index=idx, role=r, technique="diminution", intensity=0.7,
                            notes="Rhythmic acceleration (subdivisions cut in half)."
                        ))
            elif sec.section_type == SectionType.BREAKDOWN:
                for r in active_roles:
                    if r in ["chords", "pad", "lead"]:
                        directives[idx].append(VariationDirective(
                            section_index=idx, role=r, technique="augmentation", intensity=0.5,
                            notes="Elongated sustains and atmospheric voicing."
                        ))
                        
        return directives
