# engine/arrangement/transitions/pre_drop.py
"""
Pre-Drop Tension & Acoustic Vacuum Generator:
Creates surgical silence gaps, low-end mutes, and tension windows right before drops hit.
"""

from typing import Optional, List, Dict, Any, Tuple
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


class PreDropVacuumEngine:
    """Calculates exact silence windows and low-end cut automation envelopes for drops."""

    @classmethod
    def get_vacuum_windows(cls) -> List[Dict[str, Any]]:
        """Returns the acoustic vacuum silence coordinates for Drop 1 and Final Chorus."""
        # Drop 1 is at bar 32 (beat 128.0). Vacuum is in beat 127.0 to 128.0 (1 beat silence)
        # Final Chorus is at bar 72 (beat 288.0). Vacuum is in beat 287.0 to 288.0
        return [
            {
                "target_section": "Chorus 1 (Drop 1)",
                "drop_bar": 32,
                "drop_beat": 128.0,
                "vacuum_start_beat": 127.0,
                "vacuum_end_beat": 128.0,
                "duration_beats": 1.0,
                "mute_tracks": ["kick", "bass", "808"],
                "filter_cutoff_drop_hz": 300.0,
            },
            {
                "target_section": "Final Chorus (Climax Drop)",
                "drop_bar": 72,
                "drop_beat": 288.0,
                "vacuum_start_beat": 287.0,
                "vacuum_end_beat": 288.0,
                "duration_beats": 1.0,
                "mute_tracks": ["kick", "bass", "808"],
                "filter_cutoff_drop_hz": 250.0,
            }
        ]

    @classmethod
    def generate_vacuum_mute_envelope(cls, drop_beat: float = 128.0, duration_beats: float = 1.0) -> List[Tuple[float, float]]:
        """
        Generates volume automation breakpoints:
        1.0 (unmuted) -> 0.0 (muted for vacuum) -> 1.0 (instant un-mute at drop downbeat).
        """
        start_beat = max(0.0, drop_beat - duration_beats)
        return [
            (round(start_beat - 0.05, 3), 1.0),
            (round(start_beat, 3), 0.0),
            (round(drop_beat - 0.02, 3), 0.0),
            (round(drop_beat, 3), 1.0),
        ]
