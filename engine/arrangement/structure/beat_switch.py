# engine/arrangement/structure/beat_switch.py
"""
Beat Switch Orchestrator (Forwarding Module):
Re-exports the core BeatSwitchOrchestrator from engine.arrangement.beat_switch.
"""

from engine.arrangement.beat_switch import (
    BeatSwitchOrchestrator,
    plan_beat_switch,
    apply_beat_switch
)

__all__ = ["BeatSwitchOrchestrator", "plan_beat_switch", "apply_beat_switch"]
