# engine/composition/__init__.py
"""
Composition Module:
Houses high-level compositional DNA, signature musical gestures, and generative constraint models.
"""

from .compositional_dna import (
    CompositionalDNA,
    NegativeConstraint,
    PrimaryMotif,
    MotifNote,
    SignatureRhythm,
    HarmonicPalette,
    InstrumentationRules,
    TimbralPalette,
    SignatureGesture,
)

__all__ = [
    "CompositionalDNA",
    "NegativeConstraint",
    "PrimaryMotif",
    "MotifNote",
    "SignatureRhythm",
    "HarmonicPalette",
    "InstrumentationRules",
    "TimbralPalette",
    "SignatureGesture",
]
