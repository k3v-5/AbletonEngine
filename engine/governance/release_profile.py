"""
Release Profiles and Metric Governance Policies for AbletonEngine.
Deterministic metric evaluation across delivery targets (Streaming, Club, Dynamic).
"""

from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field


class ComparisonMode(str, Enum):
    MAXIMUM = "MAXIMUM"  # value <= threshold
    MINIMUM = "MINIMUM"  # value >= threshold
    RANGE = "RANGE"      # threshold <= value <= upper_bound
    TARGET = "TARGET"    # abs(value - threshold) <= tolerance


class MetricPolicy(BaseModel):
    metric_name: str
    mode: ComparisonMode
    threshold: float
    upper_bound: Optional[float] = None
    tolerance: float = 0.0

    def evaluate(self, value: float) -> bool:
        if self.mode == ComparisonMode.MAXIMUM:
            return value <= self.threshold
        elif self.mode == ComparisonMode.MINIMUM:
            return value >= self.threshold
        elif self.mode == ComparisonMode.RANGE:
            high = self.upper_bound if self.upper_bound is not None else self.threshold
            return self.threshold <= value <= high
        elif self.mode == ComparisonMode.TARGET:
            return abs(value - self.threshold) <= self.tolerance
        return False


class ReleaseProfile(BaseModel):
    profile_name: str
    metrics: Dict[str, MetricPolicy] = Field(default_factory=dict)

    def evaluate_all(self, observed: Dict[str, float]) -> Dict[str, bool]:
        results = {}
        for name, policy in self.metrics.items():
            if name in observed:
                results[name] = policy.evaluate(observed[name])
            else:
                results[name] = False
        return results
