"""
Semantic Sound Parameters:
Defines the universal acoustic descriptors and normalization scales.
"""
from dataclasses import dataclass
from typing import List

UNIVERSAL_SEMANTIC_PARAMETERS = [
    "brightness", "warmth", "weight", "punch", "grit",
    "movement", "space", "width", "depth", "aggression",
    "softness", "density", "transient", "air"
]

@dataclass
class SemanticParameter:
    name: str
    value: float  # [0.0, 1.0]
    description: str = ""

    def __post_init__(self):
        self.value = max(0.0, min(1.0, float(self.value)))
