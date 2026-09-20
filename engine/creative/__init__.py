# engine/creative/__init__.py
"""
Phase 1 Creative Direction & Song DNA Package.
"""

from .models import (
    SongCreativeDNA,
    SonicWorld,
    AestheticMood,
    ReferenceProfile,
    SpectralTargetBand,
    HarmonicDNA,
    ModalFlavor,
    TrackRoleAllocation,
    ArrangementBlueprint,
    ArrangementSectionBlueprint
)
from .dna_engine import CreativeDirectionEngine
from .music_dna import (
    MusicDNA,
    MusicDNAIdentity,
    MusicDNARhythm,
    MusicDNAHarmony,
    MusicDNAMelody,
    MusicDNAStructure,
    MusicDNASoundIdentity,
    MusicDNANovelty
)
from .leitmotif_engine import Leitmotif, LeitmotifEngine
from .cliche_detector import ClicheDetector, ClicheAuditReport

__all__ = [
    "SongCreativeDNA",
    "SonicWorld",
    "AestheticMood",
    "ReferenceProfile",
    "SpectralTargetBand",
    "HarmonicDNA",
    "ModalFlavor",
    "TrackRoleAllocation",
    "ArrangementBlueprint",
    "ArrangementSectionBlueprint",
    "CreativeDirectionEngine",
    "MusicDNA",
    "MusicDNAIdentity",
    "MusicDNARhythm",
    "MusicDNAHarmony",
    "MusicDNAMelody",
    "MusicDNAStructure",
    "MusicDNASoundIdentity",
    "MusicDNANovelty",
    "Leitmotif",
    "LeitmotifEngine",
    "ClicheDetector",
    "ClicheAuditReport"
]

