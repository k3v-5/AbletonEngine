# engine/music/motifs/memory.py
from typing import Dict, List, Optional
from ..models import Motif

class MotifMemory:
    """Stores and catalogs musical motifs linked with roles, tracks, and sections"""
    def __init__(self):
        self._motifs: Dict[str, Motif] = {}

    def store_motif(self, motif: Motif) -> Motif:
        self._motifs[motif.id] = motif
        return motif

    def get_motif(self, id_or_name: str) -> Optional[Motif]:
        if id_or_name in self._motifs:
            return self._motifs[id_or_name]
        # Search by name
        for m in self._motifs.values():
            if m.name.lower() == id_or_name.lower():
                return m
        return None

    def list_motifs(self) -> List[Dict]:
        return [m.to_dict() for m in self._motifs.values()]

    def find_by_role(self, role: str) -> List[Motif]:
        r_low = role.lower()
        return [m for m in self._motifs.values() if m.role and m.role.lower() == r_low]

    def find_by_section(self, section: str) -> List[Motif]:
        s_low = section.lower()
        return [m for m in self._motifs.values() if m.section and m.section.lower() == s_low]

motif_memory = MotifMemory()
