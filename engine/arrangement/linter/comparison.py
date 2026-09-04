"""
Section Comparison Engine:
Computes structural, harmonic, and rhythmic similarity between sections.
Calculates repetition index (0.0 = completely unique, 1.0 = duplicate copy).
"""
from typing import Dict, List, Any
from engine.arrangement.models.section import Section

class SectionComparator:
    """Computes similarity index between sections to prevent copy-paste arrangements."""
    
    @staticmethod
    def compare_sections(sec_a: Section, sec_b: Section) -> Dict[str, Any]:
        """Calculates similarity metrics between two sections."""
        # 1. Type similarity
        type_match = 1.0 if sec_a.section_type == sec_b.section_type else 0.0
        
        # 2. Energy similarity (1.0 = identical energy)
        energy_sim = 1.0 - abs(sec_a.energy - sec_b.energy)
        
        # 3. Bar length similarity
        len_sim = 1.0 - min(1.0, abs(sec_a.bars - sec_b.bars) / max(1, max(sec_a.bars, sec_b.bars)))
        
        # 4. Variation profile match
        var_match = 1.0 if sec_a.variation_type == sec_b.variation_type else 0.0
        
        # Composite similarity
        composite = (type_match * 0.3) + (energy_sim * 0.3) + (len_sim * 0.2) + (var_match * 0.2)
        composite = round(min(1.0, max(0.0, composite)), 3)
        
        is_identical = (sec_a.section_type == sec_b.section_type and 
                        abs(sec_a.energy - sec_b.energy) < 0.01 and 
                        sec_a.variation_type == sec_b.variation_type)
                        
        return {
            "section_a": sec_a.name,
            "section_b": sec_b.name,
            "similarity_index": composite,
            "is_identical_copy": is_identical,
            "energy_delta": round(sec_b.energy - sec_a.energy, 3)
        }
