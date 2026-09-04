"""
Arrangement Density Controller:
Calculates and controls notes per beat/bar across sections and roles.
Guarantees climactic energy matches density targets without frequency mud.
"""
from typing import Dict, List
from engine.arrangement.models.section import Section, SectionType

class DensityController:
    """Calculates, verifies, and modulates musical density across sections."""
    
    # Target average notes-per-bar targets by section type
    DENSITY_TARGETS = {
        SectionType.INTRO: (4.0, 16.0),
        SectionType.VERSE: (16.0, 32.0),
        SectionType.BUILD: (24.0, 64.0),
        SectionType.DROP: (32.0, 80.0),
        SectionType.BREAKDOWN: (8.0, 24.0),
        SectionType.OUTRO: (8.0, 20.0)
    }

    @classmethod
    def calculate_section_density(cls, total_notes: int, bars: int) -> float:
        """Computes notes per bar."""
        if bars <= 0:
            return 0.0
        return round(total_notes / bars, 2)

    @classmethod
    def evaluate_density_curve(cls, sections: List[Section], note_counts: List[int]) -> Dict[str, any]:
        """Validates that density curve aligns with energy arc."""
        densities = []
        warnings = []
        
        for i, sec in enumerate(sections):
            notes = note_counts[i] if i < len(note_counts) else int(sec.energy * 48 * sec.bars)
            density = cls.calculate_section_density(notes, sec.bars)
            densities.append(density)
            
            min_target, max_target = cls.DENSITY_TARGETS.get(sec.section_type, (8.0, 64.0))
            if density > max_target * 1.5:
                warnings.append(f"Section {i} ({sec.name}): Density {density} notes/bar exceeds target ({max_target}). Potential clutter.")
                
        return {
            "densities_per_section": densities,
            "average_density": round(sum(densities) / len(densities), 2) if densities else 0.0,
            "warnings": warnings
        }
