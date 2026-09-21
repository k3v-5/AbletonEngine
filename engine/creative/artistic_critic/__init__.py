# engine/creative/artistic_critic/__init__.py
"""
Artistic Critic Engine Package:
The internal judicial court evaluating proposals across 7 dimensions:
1. Identity
2. Memorability
3. Predictability
4. Emotional Perception
5. Human Plausibility
6. Sonic Signature
7. Cultural / Genre Plausibility
"""
from .critic_verdict import CriticDimension, VetoSeverity, CriticScore, CriticVerdict
from .identity_critic import IdentityCritic
from .memorability_critic import MemorabilityCritic
from .predictability_critic import PredictabilityCritic
from .emotional_critic import EmotionalCritic
from .human_plausibility_critic import HumanPlausibilityCritic
from .sonic_signature_critic import SonicSignatureCritic
from .genre_plausibility_critic import CulturalGenrePlausibilityCritic
from .artistic_critic_engine import ArtisticCriticEngine

__all__ = [
    "CriticDimension",
    "VetoSeverity",
    "CriticScore",
    "CriticVerdict",
    "IdentityCritic",
    "MemorabilityCritic",
    "PredictabilityCritic",
    "EmotionalCritic",
    "HumanPlausibilityCritic",
    "SonicSignatureCritic",
    "CulturalGenrePlausibilityCritic",
    "ArtisticCriticEngine",
]
