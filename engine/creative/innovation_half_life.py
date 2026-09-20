"""
Innovation Half-Life & Technique Lifecycle Tracker:
Monitors the temporal lifespan, fatigue, and resurgence of musical mechanisms.

Models the full creative lifecycle of each technique:
First Appearance -> Initial Yield -> Peak Frequency -> Saturation Onset -> Decay/Fatigue -> Dormancy -> Resurgence

Enables the engine to understand:
"Technique X produces strong returns initially, but exhibits diminishing returns
after ~N sessions and requires a fallow/dormancy period before re-emerging in new contexts."
"""

import os
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

logger = logging.getLogger("InnovationHalfLifeTracker")

DEFAULT_LIFECYCLE_STORAGE_PATH = os.path.join("state", "learned", "technique_lifecycles.json")


@dataclass
class TechniqueLifecycle:
    """Temporal lifecycle metrics for an individual production technique."""
    technique_name: str
    birth_session: int = 0
    occurrences: List[int] = field(default_factory=list)
    yields: List[float] = field(default_factory=list)
    peak_session: int = 0
    peak_frequency: float = 0.0
    saturation_session: Optional[int] = None
    dormancy_start_session: Optional[int] = None
    resurgence_sessions: List[int] = field(default_factory=list)
    current_status: str = "EMERGING"  # EMERGING, PEAK, SATURATING, DECAYING, DORMANT, RESURGENT

    @property
    def total_usages(self) -> int:
        return len(self.occurrences)

    @property
    def average_yield(self) -> float:
        if not self.yields:
            return 0.50
        return round(sum(self.yields) / len(self.yields), 3)

    @property
    def recent_yield(self) -> float:
        if not self.yields:
            return 0.50
        sample = self.yields[-5:]
        return round(sum(sample) / len(sample), 3)

    def calculate_frequency_in_window(self, current_session: int, window: int = 20) -> float:
        """Calculates usage frequency in the last 'window' sessions."""
        if current_session <= 0:
            return 0.0
        start = max(0, current_session - window)
        count = sum(1 for s in self.occurrences if start <= s <= current_session)
        return round(count / min(window, max(1, current_session)), 3)

    @property
    def half_life_sessions(self) -> Optional[int]:
        """
        Sessions elapsed from peak frequency until usage frequency or yield dropped by 50%.
        Returns None if peak not yet reached or technique hasn't decayed.
        """
        if self.peak_session == 0 or self.peak_frequency < 0.20:
            return None

        # Look for the session where frequency fell to half of peak
        for s in self.occurrences:
            if s > self.peak_session:
                freq = self.calculate_frequency_in_window(s, window=15)
                if freq <= self.peak_frequency * 0.50:
                    return s - self.peak_session

        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "technique_name": self.technique_name,
            "birth_session": self.birth_session,
            "total_usages": self.total_usages,
            "peak_session": self.peak_session,
            "peak_frequency": self.peak_frequency,
            "saturation_session": self.saturation_session,
            "dormancy_start": self.dormancy_start_session,
            "resurgence_count": len(self.resurgence_sessions),
            "current_status": self.current_status,
            "average_yield": self.average_yield,
            "recent_yield": self.recent_yield,
            "half_life_sessions": self.half_life_sessions,
            "recent_occurrences": self.occurrences[-15:]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TechniqueLifecycle":
        return cls(
            technique_name=str(data.get("technique_name", "")),
            birth_session=int(data.get("birth_session", 0)),
            occurrences=list(data.get("recent_occurrences", [])),
            yields=[],
            peak_session=int(data.get("peak_session", 0)),
            peak_frequency=float(data.get("peak_frequency", 0.0)),
            saturation_session=data.get("saturation_session"),
            dormancy_start_session=data.get("dormancy_start"),
            resurgence_sessions=[],
            current_status=str(data.get("current_status", "EMERGING"))
        )


class InnovationHalfLifeTracker:
    """
    Tracks and analyzes the lifecycle of all musical mechanisms across large cohorts.
    Advises on technique fatigue, mandatory fallow periods, and optimal re-emergence.
    """

    def __init__(self, storage_path: str = DEFAULT_LIFECYCLE_STORAGE_PATH, fallow_period: int = 15):
        self.storage_path = storage_path
        self.fallow_period = fallow_period  # Sessions a fatigued technique must rest
        self.lifecycles: Dict[str, TechniqueLifecycle] = {}
        self.current_session_index: int = 0
        self.load()

    def record_session(
        self,
        session_index: int,
        techniques_applied: List[str],
        yields: Optional[Dict[str, float]] = None,
        auto_save: bool = False
    ) -> None:
        """
        Records the application of techniques in a session and updates their lifecycle states.
        """
        self.current_session_index = max(self.current_session_index, session_index)
        yields_map = yields or {}

        for tech in techniques_applied:
            norm_name = tech.lower().strip()
            if norm_name not in self.lifecycles:
                self.lifecycles[norm_name] = TechniqueLifecycle(
                    technique_name=norm_name,
                    birth_session=session_index
                )

            lc = self.lifecycles[norm_name]
            lc.occurrences.append(session_index)

            # Record yield if provided
            y_val = yields_map.get(norm_name, yields_map.get(tech))
            if y_val is not None:
                lc.yields.append(min(1.0, max(0.0, y_val)))

            # Update rolling frequency
            freq = lc.calculate_frequency_in_window(session_index, window=20)
            if freq > lc.peak_frequency:
                lc.peak_frequency = freq
                lc.peak_session = session_index

            # Check if this is a resurgence from dormancy
            if lc.current_status == "DORMANT":
                lc.current_status = "RESURGENT"
                lc.resurgence_sessions.append(session_index)
                lc.dormancy_start_session = None

        # Update statuses for all tracked techniques
        for name, lc in self.lifecycles.items():
            self._update_status(lc, session_index)

        if auto_save:
            self.save()

    def _update_status(self, lc: TechniqueLifecycle, current_session: int) -> None:
        """Evaluates lifecycle stage transitions."""
        if lc.current_status == "RESURGENT":
            last_used = lc.occurrences[-1] if lc.occurrences else 0
            if (current_session - last_used) <= 5:
                return

        if lc.total_usages < 3:
            lc.current_status = "EMERGING"
            return

        recent_freq = lc.calculate_frequency_in_window(current_session, window=15)
        recent_yield = lc.recent_yield

        # Saturation condition: used too heavily with declining yield
        if recent_freq >= 0.50 and (recent_yield < 0.40 or len(lc.occurrences) >= 20):
            if lc.saturation_session is None:
                lc.saturation_session = current_session
            lc.current_status = "SATURATING"

        # Decay / Fatigue condition
        elif lc.saturation_session and recent_freq < lc.peak_frequency * 0.50:
            lc.current_status = "DECAYING"

        # Dormancy condition: absent for >= fallow_period sessions after saturation/decay
        if lc.current_status in ("SATURATING", "DECAYING"):
            last_used = lc.occurrences[-1] if lc.occurrences else 0
            if (current_session - last_used) >= (self.fallow_period // 2):
                lc.current_status = "DORMANT"
                if lc.dormancy_start_session is None:
                    lc.dormancy_start_session = current_session

    def should_quarantine(self, technique_name: str) -> bool:
        """Returns True if a technique is fatigued/saturating and should be rested."""
        norm_name = technique_name.lower().strip()
        lc = self.lifecycles.get(norm_name)
        if not lc:
            return False
        return lc.current_status == "SATURATING"

    def is_eligible_for_resurgence(self, technique_name: str) -> bool:
        """Returns True if a dormant technique has rested sufficiently and can re-emerge."""
        norm_name = technique_name.lower().strip()
        lc = self.lifecycles.get(norm_name)
        if not lc or lc.current_status != "DORMANT":
            return False

        dormancy_duration = (
            self.current_session_index - (lc.dormancy_start_session or lc.occurrences[-1])
        )
        return dormancy_duration >= self.fallow_period

    def get_lifecycle_report(self) -> Dict[str, Any]:
        """Comprehensive audit of technique lifecycles, half-lives, and status distribution."""
        if not self.lifecycles:
            return {"status": "NO_LIFECYCLE_DATA", "total_techniques": 0}

        table = [lc.to_dict() for lc in self.lifecycles.values()]
        saturating = [lc.technique_name for lc in self.lifecycles.values() if lc.current_status == "SATURATING"]
        dormant = [lc.technique_name for lc in self.lifecycles.values() if lc.current_status == "DORMANT"]
        resurgent = [lc.technique_name for lc in self.lifecycles.values() if lc.current_status == "RESURGENT"]

        half_lives = [lc.half_life_sessions for lc in self.lifecycles.values() if lc.half_life_sessions is not None]
        avg_half_life = round(sum(half_lives) / len(half_lives), 1) if half_lives else None

        return {
            "status": "LIFECYCLES_AUDITED",
            "current_session": self.current_session_index,
            "total_tracked_techniques": len(self.lifecycles),
            "average_half_life_sessions": avg_half_life,
            "techniques_saturating": saturating,
            "techniques_dormant": dormant,
            "techniques_resurgent": resurgent,
            "lifecycles": table
        }

    def save(self, filepath: Optional[str] = None) -> None:
        """Persists lifecycles to JSON."""
        target = filepath or self.storage_path
        os.makedirs(os.path.dirname(target), exist_ok=True)
        data = {
            "version": "1.0",
            "current_session_index": self.current_session_index,
            "lifecycles": {k: v.to_dict() for k, v in self.lifecycles.items()}
        }
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(self.lifecycles)} technique lifecycles to {target}")

    def load(self, filepath: Optional[str] = None) -> None:
        """Loads lifecycles from JSON if present."""
        target = filepath or self.storage_path
        if not os.path.exists(target):
            return
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.current_session_index = int(data.get("current_session_index", 0))
            self.lifecycles = {
                k: TechniqueLifecycle.from_dict(v)
                for k, v in data.get("lifecycles", {}).items()
            }
            logger.info(f"Loaded {len(self.lifecycles)} lifecycles from {target}")
        except Exception as e:
            logger.warning(f"Failed to load technique lifecycles from {target}: {e}")
