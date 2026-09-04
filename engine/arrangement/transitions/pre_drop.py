"""
Pre-Drop Tension Generator:
Creates silence gaps, cutoff filters, drum roll accelerations, and vocal chops right before a drop.
"""
from typing import Optional
from engine.arrangement.transitions.models import TransitionDescriptor, TransitionType

class PreDropGenerator:
    """Specialized tension builder for sections transitioning into a DROP."""
    
    @staticmethod
    def create_pre_drop(
        from_section_idx: int,
        to_section_idx: int,
        transition_bar: int,
        silence_duration_beats: float = 2.0,
        include_fill: bool = True
    ) -> TransitionDescriptor:
        """
        Creates a pre-drop transition descriptor that cuts off low-end and creates
        a silence tension gap right before the drop hits bar 1.
        """
        desc = (
            f"Pre-drop tension: cut sub-frequencies, {silence_duration_beats} beats silence/fill, "
            f"impact crash on arrival."
        )
        return TransitionDescriptor(
            from_section_idx=from_section_idx,
            to_section_idx=to_section_idx,
            start_bar=transition_bar,
            duration_bars=1.0,
            transition_type=TransitionType.SILENCE_GAP if silence_duration_beats >= 1.0 else TransitionType.DRUM_FILL,
            affected_roles=["kick", "bass", "sub_bass", "snare"],
            pre_drop_silence_beats=silence_duration_beats,
            intensity=1.0,
            description=desc
        )
