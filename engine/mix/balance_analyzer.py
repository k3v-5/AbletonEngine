"""
Role Balance and Energy Distribution Analyzer.
Examines multi-track stems across the arrangement.
"""
from typing import Dict, Any, List
import numpy as np


class RoleBalanceAnalyzer:
    """Estimates energy occupation, priority, and frequency allocation per role."""

    ROLE_PRIORITIES = {
        "KICK": 1.0,
        "SUB": 0.95,
        "BASS": 0.90,
        "VOCAL": 0.88,
        "LEAD": 0.85,
        "DRUMS": 0.80,
        "CHORDS": 0.75,
        "PAD": 0.65,
        "FX": 0.50
    }

    @classmethod
    def evaluate_role_balances(cls, stem_energies: Dict[str, float]) -> Dict[str, Any]:
        total_energy = sum(stem_energies.values()) + 1e-12
        balances = {}
        for role, energy in stem_energies.items():
            rel = energy / total_energy
            priority = cls.ROLE_PRIORITIES.get(role.upper(), 0.70)
            balances[role] = {
                "relative_energy": round(rel, 4),
                "energy_db": round(float(10.0 * np.log10(max(1e-12, energy))), 2),
                "priority": priority,
                "balanced": bool(0.02 <= rel <= 0.45)
            }
        return balances
