# engine/arrangement/templates/structures.py
from typing import Dict, Any, List, Optional
from engine.arrangement.models.section import Section, SectionType

# Fixed structural templates dismantled. The engine exclusively listens to how many bars are requested.
FORM_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {}


def build_sections_for_bars(
    total_bars: int,
    custom_sections: Optional[List[Dict[str, Any]]] = None,
    drop_bar: Optional[int] = None
) -> List[Section]:
    """
    Constructs arrangement sections purely based on the exact number of bars requested,
    supporting asymmetric phrasing (e.g. 5, 7, 9, 11, 13 bars) and completely flexible drop location.
    The engine listens exclusively to how many bars the producer/AI requests.
    """
    sections: List[Section] = []

    if custom_sections:
        curr_bar = 1
        for s in custom_sections:
            bars = int(s.get("bars", 8))
            sec = Section(
                name=s.get("name", "Section"),
                type=SectionType.from_str(s.get("type", "VERSE")),
                start_bar=curr_bar,
                end_bar=curr_bar + bars - 1,
                duration_bars=bars,
                energy=float(s.get("energy", s.get("energy_target", 0.5))),
                density=float(s.get("density", 0.5)),
                tension=float(s.get("tension", 0.2))
            )
            sections.append(sec)
            curr_bar += bars
        return sections

    # Proportional dynamic distribution for any bar count (including odd / prime bar totals)
    effective_total = max(8, int(total_bars))
    d_bar = drop_bar or max(5, int(effective_total * 0.35))
    d_bar = min(d_bar, effective_total - 6)

    pre_drop_total = max(3, d_bar - 1) if drop_bar else max(3, int(effective_total * 0.35))
    intro_b = max(1, min(8, pre_drop_total // 3))
    build_b = max(1, min(8, (pre_drop_total - intro_b) // 2))
    verse1_b = max(1, pre_drop_total - intro_b - build_b)

    remaining = effective_total - (intro_b + verse1_b + build_b)
    drop_b = max(2, min(16, remaining // 3))
    rem = max(3, remaining - drop_b)
    outro_b = max(1, min(8, rem // 4))
    mid_b = rem - outro_b
    verse2_b = max(1, mid_b // 2)
    final_drop_b = mid_b - verse2_b

    # Guarantee sum(bars) == effective_total exactly
    alloc_sum = intro_b + verse1_b + build_b + drop_b + verse2_b + final_drop_b + outro_b
    diff = effective_total - alloc_sum
    final_drop_b += diff

    layout = [
        ("Intro", "INTRO", intro_b, 0.25, 0.30, 0.15),
        ("Verse 1", "VERSE", verse1_b, 0.50, 0.55, 0.25),
        ("Pre-Drop", "BUILD", build_b, 0.75, 0.70, 0.80),
        ("Drop 1", "DROP", drop_b, 0.95, 0.90, 0.30),
        ("Verse 2", "DEVELOPMENT", verse2_b, 0.60, 0.65, 0.30),
        ("Final Drop", "DROP", final_drop_b, 1.00, 0.95, 0.25),
        ("Outro", "OUTRO", outro_b, 0.20, 0.25, 0.10)
    ]

    curr_bar = 1
    for name, stype, bars, energy, density, tension in layout:
        if bars <= 0:
            continue
        sec = Section(
            name=name,
            type=SectionType.from_str(stype),
            start_bar=curr_bar,
            end_bar=curr_bar + bars - 1,
            duration_bars=bars,
            energy=energy,
            density=density,
            tension=tension
        )
        sections.append(sec)
        curr_bar += bars

    return sections


def get_structure_template(name: str = "dynamic", total_bars: int = 64) -> List[Dict[str, Any]]:
    key = str(name).strip().lower()
    if key in FORM_TEMPLATES:
        return FORM_TEMPLATES[key]
    # Dynamic fallback converting Section objects to dicts
    secs = build_sections_for_bars(total_bars=total_bars)
    return [
        {
            "name": s.name,
            "type": s.type.name if hasattr(s.type, "name") else str(s.type),
            "bars": s.duration_bars,
            "energy": s.energy,
            "density": s.density,
            "tension": s.tension
        }
        for s in secs
    ]


class StructureLibrary:
    TEMPLATES = FORM_TEMPLATES

    @classmethod
    def get_template(cls, name: str = "dynamic", total_bars: int = 64) -> List[Section]:
        clean = str(name).strip().lower()
        if clean in cls.TEMPLATES:
            raw = cls.TEMPLATES[clean]
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
        return build_sections_for_bars(total_bars=total_bars)

    @classmethod
    def get_dynamic_structure(
        cls,
        total_bars: int,
        custom_sections: Optional[List[Dict[str, Any]]] = None,
        drop_bar: Optional[int] = None
    ) -> List[Section]:
        return build_sections_for_bars(total_bars=total_bars, custom_sections=custom_sections, drop_bar=drop_bar)

