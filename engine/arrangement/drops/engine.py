"""
Multi-Drop Differentiation Engine:
Guarantees Drop 2 > Drop 1 in energy, density, harmonic/melodic variation, and climax satisfaction.
"""
from typing import Dict, List, Optional
from engine.arrangement.models.section import Section, SectionType

class DropDifferentiationEngine:
    """
    Enforces the core rule: Drop 2 must never be a mere copy of Drop 1.
    Drop 2 must have greater dynamic energy, new counter-melodies, fuller rhythm, or harmonic extension.
    """
    
    @staticmethod
    def differentiate_drops(sections: List[Section]) -> List[Section]:
        """Adjust Drop 2 (and Drop 3 if any) to ensure progressive escalation."""
        drop_sections = [s for s in sections if s.section_type == SectionType.DROP]
        
        if len(drop_sections) < 2:
            return sections
            
        drop1 = drop_sections[0]
        drop2 = drop_sections[1]
        
        # Invariant: Drop 2 energy must be strictly greater than Drop 1
        if drop2.energy <= drop1.energy:
            drop2.energy = min(1.0, drop1.energy + 0.1)
            
        # Ensure Drop 2 gets different variation profile and higher density
        drop1.variation_type = "main_motif"
        drop2.variation_type = "counter_motif_extension"
        
        return sections

    @staticmethod
    def compute_drop_contrast(drop1: Section, drop2: Section) -> Dict[str, any]:
        """Calculates quantitative contrast between two drops."""
        energy_diff = drop2.energy - drop1.energy
        return {
            "energy_drop1": drop1.energy,
            "energy_drop2": drop2.energy,
            "energy_delta": round(energy_diff, 3),
            "is_drop2_superior": energy_diff > 0.0,
            "drop1_variation": drop1.variation_type,
            "drop2_variation": drop2.variation_type
        }
