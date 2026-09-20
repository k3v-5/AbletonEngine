"""
Creative Regret Tracker:
Quantifies creative rollbacks across production mechanisms, combinations, genres,
and novelty bands. Identifies "mathematical false positives" (decisions that scored
high in abstract novelty/contrast but collapsed upon perceptual audition or coherence checks).
"""

import os
import json
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

logger = logging.getLogger("CreativeRegretTracker")

DEFAULT_REGRET_STORAGE_PATH = os.path.join("state", "learned", "creative_regret.json")


@dataclass
class RegretEvent:
    """Record of a creative proposal and whether it resulted in a rollback."""
    technique_name: str
    combination: List[str] = field(default_factory=list)
    genre: str = "general"
    novelty_score: float = 0.50
    was_rolled_back: bool = False
    rollback_reason: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "technique_name": self.technique_name,
            "combination": self.combination,
            "genre": self.genre,
            "novelty_score": round(self.novelty_score, 3),
            "was_rolled_back": self.was_rolled_back,
            "rollback_reason": self.rollback_reason,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RegretEvent":
        return cls(
            technique_name=str(data.get("technique_name", "")),
            combination=list(data.get("combination", [])),
            genre=str(data.get("genre", "general")),
            novelty_score=float(data.get("novelty_score", 0.50)),
            was_rolled_back=bool(data.get("was_rolled_back", False)),
            rollback_reason=str(data.get("rollback_reason", "")),
            timestamp=float(data.get("timestamp", 0.0))
        )


class CreativeRegretTracker:
    """
    Tracks and analyzes rollbacks to diagnose when the engine is overreaching
    or generating unviable mutations.
    """

    def __init__(self, storage_path: str = DEFAULT_REGRET_STORAGE_PATH):
        self.storage_path = storage_path
        self.events: List[RegretEvent] = []
        self.load()

    def record_event(
        self,
        technique_name: str,
        combination: Optional[List[str]] = None,
        genre: str = "general",
        novelty_score: float = 0.50,
        was_rolled_back: bool = False,
        rollback_reason: str = "",
        auto_save: bool = False
    ) -> RegretEvent:
        """Records a creative action outcome."""
        norm_name = technique_name.lower().strip()
        norm_combo = [c.lower().strip() for c in (combination or [])]

        event = RegretEvent(
            technique_name=norm_name,
            combination=norm_combo,
            genre=genre.lower().strip(),
            novelty_score=min(1.0, max(0.0, novelty_score)),
            was_rolled_back=was_rolled_back,
            rollback_reason=rollback_reason
        )
        self.events.append(event)
        if auto_save:
            self.save()
        return event

    def get_regret_rate(self, technique_name: Optional[str] = None) -> float:
        """
        Calculates rollback rate (0.0 to 1.0).
        If technique_name provided, filters for events involving that technique.
        """
        if not self.events:
            return 0.0

        if technique_name:
            target = technique_name.lower().strip()
            relevant = [
                e for e in self.events
                if e.technique_name == target or target in e.combination
            ]
        else:
            relevant = self.events

        if not relevant:
            return 0.0

        rollbacks = sum(1 for e in relevant if e.was_rolled_back)
        return round(rollbacks / len(relevant), 3)

    def get_regret_by_novelty_band(self) -> Dict[str, Dict[str, Any]]:
        """
        Categorizes regret into 4 novelty tiers:
        - low: [0.0, 0.35)
        - medium: [0.35, 0.65)
        - high: [0.65, 0.85)
        - extreme: [0.85, 1.00]
        """
        bands = {
            "low_novelty": {"min": 0.0, "max": 0.35, "total": 0, "rollbacks": 0},
            "medium_novelty": {"min": 0.35, "max": 0.65, "total": 0, "rollbacks": 0},
            "high_novelty": {"min": 0.65, "max": 0.85, "total": 0, "rollbacks": 0},
            "extreme_novelty": {"min": 0.85, "max": 1.01, "total": 0, "rollbacks": 0}
        }

        for ev in self.events:
            for band_name, bounds in bands.items():
                if bounds["min"] <= ev.novelty_score < bounds["max"]:
                    bounds["total"] += 1
                    if ev.was_rolled_back:
                        bounds["rollbacks"] += 1
                    break

        result = {}
        for band_name, data in bands.items():
            tot = data["total"]
            rb = data["rollbacks"]
            rate = round(rb / tot, 3) if tot > 0 else 0.0
            result[band_name] = {
                "total_events": tot,
                "rollbacks": rb,
                "regret_rate": rate
            }
        return result

    def get_regret_report(self) -> Dict[str, Any]:
        """Comprehensive audit of engine regrets and false positives."""
        if not self.events:
            return {
                "status": "NO_REGRET_DATA",
                "total_events": 0,
                "global_regret_rate": 0.0
            }

        global_rate = self.get_regret_rate()
        novelty_bands = self.get_regret_by_novelty_band()

        # Group by technique
        tech_stats: Dict[str, Dict[str, int]] = {}
        for ev in self.events:
            t = ev.technique_name
            if t not in tech_stats:
                tech_stats[t] = {"total": 0, "rollbacks": 0}
            tech_stats[t]["total"] += 1
            if ev.was_rolled_back:
                tech_stats[t]["rollbacks"] += 1

        false_positives = []
        for t, stats in tech_stats.items():
            if stats["total"] >= 3:
                r_rate = stats["rollbacks"] / stats["total"]
                if r_rate >= 0.40:
                    false_positives.append({
                        "technique": t,
                        "total": stats["total"],
                        "rollbacks": stats["rollbacks"],
                        "regret_rate": round(r_rate, 3)
                    })

        false_positives.sort(key=lambda x: x["regret_rate"], reverse=True)

        return {
            "status": "REGRET_AUDITED",
            "total_events": len(self.events),
            "global_regret_rate": global_rate,
            "novelty_band_regret": novelty_bands,
            "false_positive_candidates": false_positives
        }

    def save(self, filepath: Optional[str] = None) -> None:
        """Persists regret events to JSON."""
        target = filepath or self.storage_path
        os.makedirs(os.path.dirname(target), exist_ok=True)
        data = {
            "version": "1.0",
            "events": [e.to_dict() for e in self.events]
        }
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(self.events)} regret events to {target}")

    def load(self, filepath: Optional[str] = None) -> None:
        """Loads regret events from JSON if present."""
        target = filepath or self.storage_path
        if not os.path.exists(target):
            return
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.events = [
                RegretEvent.from_dict(e)
                for e in data.get("events", [])
            ]
            logger.info(f"Loaded {len(self.events)} regret events from {target}")
        except Exception as e:
            logger.warning(f"Failed to load regret events from {target}: {e}")
