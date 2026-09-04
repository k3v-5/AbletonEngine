"""
Narrative Arc:
Models song progression as a 5-stage dramatic narrative arc:
1. Exposition (Intro/Verse)
2. Rising Action (Build)
3. Climax I (Drop 1)
4. Falling Action / Reflection (Breakdown)
5. Climax II (Drop 2 - Main Peak)
6. Resolution (Outro)
"""
from dataclasses import dataclass
from typing import List, Dict
from engine.arrangement.models.section import Section, SectionType

@dataclass
class NarrativeStage:
    name: str
    target_energy_range: tuple
    sections: List[str]

class NarrativeArc:
    """Evaluates narrative tension and pacing throughout the song."""
    
    STAGES = [
        NarrativeStage("Exposition", (0.1, 0.5), ["intro", "verse"]),
        NarrativeStage("Rising Action", (0.5, 0.85), ["build"]),
        NarrativeStage("Climax I", (0.8, 0.95), ["drop"]),
        NarrativeStage("Reflection", (0.2, 0.6), ["breakdown"]),
        NarrativeStage("Main Climax", (0.9, 1.0), ["drop"]),
        NarrativeStage("Resolution", (0.1, 0.4), ["outro"])
    ]

    @classmethod
    def evaluate_narrative(cls, sections: List[Section]) -> Dict[str, any]:
        """Scores how well the section sequence conforms to a compelling narrative arc."""
        sec_types = [s.section_type.value for s in sections]
        energies = [s.energy for s in sections]
        
        has_intro = "intro" in sec_types
        has_build = "build" in sec_types
        has_drop = "drop" in sec_types
        has_outro = "outro" in sec_types
        
        # Check dynamic range
        dynamic_range = max(energies) - min(energies) if energies else 0.0
        
        score = 100.0
        feedback = []
        
        if not has_drop:
            score -= 40.0
            feedback.append("Missing Climax (no Drop section found).")
        if not has_build:
            score -= 15.0
            feedback.append("Missing Rising Action (no Build section found).")
        if dynamic_range < 0.4:
            score -= 20.0
            feedback.append("Low dynamic energy range (flat arrangement).")
            
        return {
            "narrative_score": max(0.0, score),
            "dynamic_range": round(dynamic_range, 2),
            "total_sections": len(sections),
            "has_climax": has_drop,
            "feedback": feedback
        }
