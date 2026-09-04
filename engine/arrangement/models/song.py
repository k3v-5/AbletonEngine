# engine/arrangement/models/song.py
from typing import Dict, Any, List, Optional
from .section import Section

class SongArrangement:
    """Represents a complete musical arrangement model."""
    def __init__(
        self,
        title: str = "Untitled Song",
        genre: str = "melodic_techno",
        tempo: float = 128.0,
        key: str = "F",
        scale: str = "natural_minor",
        meter: str = "4/4",
        duration_bars: int = 160,
        sections: Optional[List[Section]] = None,
        energy_curve: Optional[Any] = None,
        role_matrix: Optional[Any] = None,
        transitions: Optional[List[Any]] = None,
        motifs: Optional[List[Dict[str, Any]]] = None,
        variation_rules: Optional[Dict[str, Any]] = None,
        narrative_arc: Optional[Any] = None,
        seed: int = 2026,
        engine_version: str = "3.0.0",
        template_version: str = "1.0.0",
        locked_elements: Optional[List[str]] = None,
        name: Optional[str] = None,
        **kwargs
    ):
        self.title = name if name is not None else title
        self.genre = genre
        self.tempo = float(tempo)
        self.key = key
        self.scale = scale
        self.meter = meter
        self.sections = sections or []
        self.duration_bars = sum(s.bars for s in self.sections) if self.sections else duration_bars
        self.energy_curve = energy_curve
        self.role_matrix = role_matrix
        self.transitions = transitions or []
        self.motifs = motifs or []
        self.variation_rules = variation_rules or {}
        self.narrative_arc = narrative_arc
        self.seed = int(seed)
        self.engine_version = engine_version
        self.template_version = template_version
        self.locked_elements = locked_elements or []

    @property
    def name(self) -> str:
        return self.title

    @name.setter
    def name(self, val: str):
        self.title = val

    @property
    def total_bars(self) -> int:
        if self.sections:
            return sum(s.bars for s in self.sections)
        return self.duration_bars

    @property
    def duration_seconds(self) -> float:
        bars = self.total_bars
        return round((bars * 4.0 * 60.0) / self.tempo, 2)

    def get_section(self, section_id: str) -> Optional[Section]:
        for s in self.sections:
            if s.id == section_id or s.name.lower() == section_id.lower():
                return s
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "genre": self.genre,
            "tempo": self.tempo,
            "key": self.key,
            "scale": self.scale,
            "meter": self.meter,
            "duration_bars": self.total_bars,
            "duration_seconds": self.duration_seconds,
            "sections": [s.to_dict() for s in self.sections],
            "energy_curve": self.energy_curve.to_dict() if hasattr(self.energy_curve, "to_dict") else None,
            "role_matrix": self.role_matrix.to_dict() if hasattr(self.role_matrix, "to_dict") else None,
            "transitions": [t.to_dict() if hasattr(t, "to_dict") else t for t in self.transitions],
            "motifs": self.motifs,
            "variation_rules": self.variation_rules,
            "narrative_arc": self.narrative_arc.to_dict() if hasattr(self.narrative_arc, "to_dict") else None,
            "seed": self.seed,
            "engine_version": self.engine_version,
            "template_version": self.template_version,
            "locked_elements": list(self.locked_elements)
        }

    def summary(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "genre": self.genre,
            "tempo": self.tempo,
            "key": f"{self.key} {self.scale}",
            "bars": self.total_bars,
            "duration_minutes": round(self.duration_seconds / 60.0, 2),
            "section_count": len(self.sections),
            "sections_outline": [
                {
                    "id": s.id,
                    "name": s.name,
                    "type": s.type.value if hasattr(s.type, "value") else str(s.type),
                    "bars": f"{s.start_bar}-{s.end_bar} ({s.duration_bars}b)",
                    "energy": s.energy,
                    "density": s.density,
                    "active_roles": len(s.active_roles)
                }
                for s in self.sections
            ]
        }

Song = SongArrangement
