# engine/arrangement/templates/structures.py
from typing import Dict, Any, List
from engine.arrangement.models.section import Section, SectionType

FORM_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "progressive": [
        {"name": "Intro", "type": "INTRO", "bars": 16, "energy": 0.20, "density": 0.30, "tension": 0.15},
        {"name": "Development", "type": "DEVELOPMENT", "bars": 16, "energy": 0.45, "density": 0.50, "tension": 0.25},
        {"name": "Build 1", "type": "BUILD", "bars": 16, "energy": 0.70, "density": 0.65, "tension": 0.75},
        {"name": "Drop 1", "type": "DROP", "bars": 32, "energy": 0.90, "density": 0.85, "tension": 0.35},
        {"name": "Breakdown", "type": "BREAKDOWN", "bars": 16, "energy": 0.35, "density": 0.40, "tension": 0.50},
        {"name": "Build 2", "type": "BUILD", "bars": 16, "energy": 0.78, "density": 0.70, "tension": 0.85},
        {"name": "Drop 2", "type": "DROP", "bars": 32, "energy": 0.98, "density": 0.95, "tension": 0.30},
        {"name": "Outro", "type": "OUTRO", "bars": 16, "energy": 0.25, "density": 0.30, "tension": 0.10}
    ],
    "club": [
        {"name": "Intro", "type": "INTRO", "bars": 32, "energy": 0.30, "density": 0.40, "tension": 0.10},
        {"name": "Build 1", "type": "BUILD", "bars": 16, "energy": 0.65, "density": 0.60, "tension": 0.70},
        {"name": "Drop 1", "type": "DROP", "bars": 32, "energy": 0.88, "density": 0.85, "tension": 0.30},
        {"name": "Breakdown", "type": "BREAKDOWN", "bars": 16, "energy": 0.30, "density": 0.35, "tension": 0.45},
        {"name": "Build 2", "type": "BUILD", "bars": 16, "energy": 0.75, "density": 0.70, "tension": 0.85},
        {"name": "Drop 2", "type": "DROP", "bars": 32, "energy": 0.96, "density": 0.92, "tension": 0.25},
        {"name": "Outro", "type": "OUTRO", "bars": 32, "energy": 0.35, "density": 0.40, "tension": 0.10}
    ],
    "radio": [
        {"name": "Intro", "type": "INTRO", "bars": 8, "energy": 0.25, "density": 0.35, "tension": 0.10},
        {"name": "Verse 1", "type": "VERSE", "bars": 16, "energy": 0.45, "density": 0.50, "tension": 0.20},
        {"name": "Build 1", "type": "BUILD", "bars": 8, "energy": 0.70, "density": 0.65, "tension": 0.70},
        {"name": "Drop 1", "type": "DROP", "bars": 16, "energy": 0.90, "density": 0.85, "tension": 0.30},
        {"name": "Verse 2", "type": "VERSE", "bars": 16, "energy": 0.55, "density": 0.60, "tension": 0.25},
        {"name": "Build 2", "type": "BUILD", "bars": 8, "energy": 0.75, "density": 0.70, "tension": 0.80},
        {"name": "Drop 2", "type": "DROP", "bars": 16, "energy": 0.95, "density": 0.90, "tension": 0.25},
        {"name": "Outro", "type": "OUTRO", "bars": 8, "energy": 0.30, "density": 0.35, "tension": 0.10}
    ],
    "minimal": [
        {"name": "Intro", "type": "INTRO", "bars": 32, "energy": 0.25, "density": 0.30, "tension": 0.10},
        {"name": "Groove A", "type": "DEVELOPMENT", "bars": 32, "energy": 0.50, "density": 0.55, "tension": 0.20},
        {"name": "Build", "type": "BUILD", "bars": 16, "energy": 0.68, "density": 0.65, "tension": 0.60},
        {"name": "Main Groove", "type": "DROP", "bars": 32, "energy": 0.85, "density": 0.80, "tension": 0.25},
        {"name": "Stripped Break", "type": "BREAK", "bars": 16, "energy": 0.30, "density": 0.35, "tension": 0.30},
        {"name": "Main Groove Var", "type": "DROP", "bars": 32, "energy": 0.88, "density": 0.85, "tension": 0.20},
        {"name": "Outro", "type": "OUTRO", "bars": 32, "energy": 0.25, "density": 0.30, "tension": 0.10}
    ]
}

def get_structure_template(name: str = "progressive") -> List[Dict[str, Any]]:
    key = str(name).strip().lower()
    return FORM_TEMPLATES.get(key, FORM_TEMPLATES["progressive"])

class StructureLibrary:
    TEMPLATES = FORM_TEMPLATES

    @classmethod
    def get_template(cls, name: str = "progressive") -> List[Section]:
        raw = get_structure_template(name)
        sections: List[Section] = []
        curr_bar = 1
        for s in raw:
            bars = s.get("bars", 16)
            sec = Section(
                name=s["name"],
                type=SectionType.from_str(s["type"]),
                start_bar=curr_bar,
                end_bar=curr_bar + bars - 1,
                duration_bars=bars,
                energy=float(s.get("energy", 0.5)),
                density=float(s.get("density", 0.5)),
                tension=float(s.get("tension", 0.2))
            )
            sections.append(sec)
            curr_bar += bars
        return sections
