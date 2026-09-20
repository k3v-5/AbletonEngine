"""
Online Validation Monitor:
Real-time telemetry auditor evaluating live Ableton production sessions against
empirical simulation benchmarks (HHI, territorial drift, rollback rate, and simulation-reality gap).
"""

import math
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from engine.creative.creative_ablation import calculate_jensen_shannon_divergence, calculate_shannon_entropy


@dataclass
class OnlineTelemetrySnapshot:
    """Snapshot of real-time production telemetry."""
    timestamp: str
    total_decisions: int
    mode_counts: Dict[str, int]
    herfindahl_index: float
    simulation_reality_gap_jsd: float
    rollback_rate: float
    dominant_mode: str
    is_monopoly_risk: bool
    diagnostic: str


class OnlineValidationMonitor:
    """
    Rastrea métricas de salud creativa en sesiones reales o guiadas:
    - Concentración HHI de técnicas
    - Tasa real de rollback frente a la tasa simulada (~12%)
    - Dispersión y deriva territorial
    - Divergencia (JSD) frente a la distribución meta simulada (65.2% EVOLVE / 34.7% EXPLORE / 0.1% ANCHOR)
    """

    DEFAULT_SIMULATED_TARGET = {
        "EVOLVE": 0.652,
        "EXPLORE": 0.347,
        "ANCHOR": 0.001
    }

    def __init__(self, simulated_target: Optional[Dict[str, float]] = None):
        self.simulated_target = simulated_target or dict(self.DEFAULT_SIMULATED_TARGET)
        self.decision_log: List[Dict[str, Any]] = []
        self.technique_counts: Dict[str, int] = {}
        self.mode_counts: Dict[str, int] = {"EXPLORE": 0, "ANCHOR": 0, "EVOLVE": 0}
        self.rollbacks_count: int = 0
        self.total_actuations: int = 0

    def record_decision(
        self,
        decision_id: str,
        mode: str,
        techniques_applied: List[str],
        was_rolled_back: bool = False,
        delta_score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Records a single live decision and updates online telemetry."""
        mode_upper = str(mode).upper()
        if mode_upper in self.mode_counts:
            self.mode_counts[mode_upper] += 1
        else:
            self.mode_counts[mode_upper] = 1

        self.total_actuations += 1
        if was_rolled_back:
            self.rollbacks_count += 1

        for t in techniques_applied:
            self.technique_counts[t] = self.technique_counts.get(t, 0) + 1

        entry = {
            "decision_id": decision_id,
            "mode": mode_upper,
            "techniques": list(techniques_applied),
            "was_rolled_back": was_rolled_back,
            "delta_score": round(delta_score, 4),
            "metadata": metadata or {}
        }
        self.decision_log.append(entry)
        return entry

    def calculate_herfindahl_index(self) -> float:
        """
        Calculates Herfindahl-Hirschman Index (HHI) for applied techniques in [0.0, 1.0].
        < 0.18: Diversidad saludable
        0.18 - 0.25: Concentración moderada
        > 0.25: Riesgo de monopolio / fórmula cliché
        """
        total = sum(self.technique_counts.values())
        if total == 0:
            return 0.0
        shares = [c / total for c in self.technique_counts.values()]
        return round(sum(s ** 2 for s in shares), 4)

    def calculate_simulation_reality_gap(self) -> float:
        """
        Calculates Jensen-Shannon Divergence (JSD) between real mode distribution
        and the empirical simulated target benchmark.
        """
        tot_modes = sum(self.mode_counts.values())
        if tot_modes == 0:
            return 0.0

        real_dist = {
            k: self.mode_counts.get(k, 0) / tot_modes
            for k in self.simulated_target.keys()
        }

        # Normalize target to sum to 1.0
        tot_tgt = sum(self.simulated_target.values()) or 1.0
        tgt_dist = {k: v / tot_tgt for k, v in self.simulated_target.items()}

        jsd = calculate_jensen_shannon_divergence(real_dist, tgt_dist)
        return round(jsd, 4)

    def get_rollback_rate(self) -> float:
        """Calculates current rollback percentage."""
        if self.total_actuations == 0:
            return 0.0
        return round(self.rollbacks_count / self.total_actuations, 4)

    def generate_report(self) -> Dict[str, Any]:
        """Generates comprehensive online health audit."""
        hhi = self.calculate_herfindahl_index()
        gap_jsd = self.calculate_simulation_reality_gap()
        rb_rate = self.get_rollback_rate()
        entropy = calculate_shannon_entropy(self.technique_counts)

        tot_modes = sum(self.mode_counts.values()) or 1
        mode_ratios = {k: round(v / tot_modes, 3) for k, v in self.mode_counts.items()}

        # Diagnostic synthesis
        is_monopoly = hhi > 0.22
        if is_monopoly:
            diagnostic = "Advertencia de monotonía técnica: El índice HHI supera 0.22. Se recomienda forzar EXPLORE."
        elif gap_jsd > 0.15:
            diagnostic = "Divergencia simulación-realidad elevada: La distribución de modos en vivo difiere significativamente del benchmark."
        elif rb_rate > 0.35:
            diagnostic = "Tasa de rollback inusualmente alta: Más del 35% de las intervenciones degradaron coherencia/identidad."
        else:
            diagnostic = "Operación online saludable: Balance evolutivo estable, diversidad técnica preservada y baja tasa de arrepentimiento."

        top_techs = sorted(self.technique_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "status": "ONLINE_MONITOR_HEALTHY" if not is_monopoly and rb_rate <= 0.35 else "ONLINE_MONITOR_ATTENTION_REQUIRED",
            "total_decisions_tracked": len(self.decision_log),
            "total_actuations": self.total_actuations,
            "rollbacks_count": self.rollbacks_count,
            "rollback_rate": rb_rate,
            "herfindahl_index": hhi,
            "shannon_entropy": round(entropy, 3),
            "is_monopoly_risk": is_monopoly,
            "simulation_reality_gap_jsd": gap_jsd,
            "mode_distribution": mode_ratios,
            "simulated_target_benchmark": self.simulated_target,
            "top_techniques_applied": top_techs,
            "diagnostic": diagnostic
        }
