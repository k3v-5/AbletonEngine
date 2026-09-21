# engine/music/motifs/__init__.py
from .motif import create_motif_from_notes
from .transformations import transform_motif, realize_motif_as_notes
from .memory import MotifMemory, motif_memory
from .compository_memory import CompositoryMemory, MotifLineage, MotifEvolutionNode
from .motif_development_engine import MotifDevelopmentEngine, TransformationDimension

__all__ = [
    "create_motif_from_notes",
    "transform_motif",
    "realize_motif_as_notes",
    "MotifMemory",
    "motif_memory",
    "CompositoryMemory",
    "MotifLineage",
    "MotifEvolutionNode",
    "MotifDevelopmentEngine",
    "TransformationDimension",
]

