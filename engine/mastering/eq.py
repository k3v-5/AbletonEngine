"""
Conservative Mastering EQ Engine.
Restricted to subtle surgical adjustments (typically ±0.5 dB to ±1.0 dB, top 2 bands).
"""
from typing import List, Dict, Any, Optional
from .models import MasterAction, TonalDifferenceMap


class MasterEQEngine:
    """Generates conservative mastering EQ moves."""

    MAX_EQ_DELTA = 1.0  # dB

    @classmethod
    def plan_eq_actions(cls, diff_map: TonalDifferenceMap) -> List[MasterAction]:
        actions = []
        for band_name, delta in diff_map.deltas.items():
            if abs(delta) >= 1.2:
                eq_delta = -round(delta * 0.4, 1)
                eq_delta = max(-cls.MAX_EQ_DELTA, min(cls.MAX_EQ_DELTA, eq_delta))
                if abs(eq_delta) >= 0.4:
                    actions.append(MasterAction(
                        action_type="EQ",
                        device_name="[MCP] Master EQ",
                        parameter_name=f"Gain {band_name}",
                        target_value=eq_delta,
                        delta=eq_delta,
                        parameters={f"Gain {band_name}": eq_delta}
                    ))
        actions.sort(key=lambda x: abs(x.delta), reverse=True)
        return actions[:2]

    @classmethod
    def calculate_eq(cls, current_tonal: Dict[str, float], target_tonal: Dict[str, float]) -> MasterAction:
        deltas = {}
        for b in ["sub", "low", "low_mid", "mid", "high_mid", "presence", "brilliance"]:
            cur = current_tonal.get(b, 0.0)
            tgt = target_tonal.get(b, 0.0)
            deltas[b] = cur - tgt

        diff_map = TonalDifferenceMap(deltas=deltas)
        sub_actions = cls.plan_eq_actions(diff_map)
        if sub_actions:
            first = sub_actions[0]
            params = {a.parameter_name: a.target_value for a in sub_actions}
            return MasterAction(
                action_type="EQ",
                device_name="[MCP] Master EQ",
                parameter_name=first.parameter_name,
                target_value=first.target_value,
                delta=first.delta,
                parameters=params,
                rationale="Conservative corrective EQ adjustment on dominant tonal deviations."
            )
        return MasterAction(
            action_type="EQ",
            device_name="[MCP] Master EQ",
            parameter_name="Bypass",
            target_value=1.0,
            delta=0.0,
            bypass=True,
            parameters={"Bypass": True},
            rationale="Tonal balance is already within tolerance; EQ bypassed."
        )
