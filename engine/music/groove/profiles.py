# engine/music/groove/profiles.py
from typing import List
from ..models import NoteEvent

GROOVE_SWING_RATIOS = {
    "straight": 0.50,
    "light_swing": 0.54,
    "medium_swing": 0.58,
    "heavy_swing": 0.64,
    "swing_16th_light": 0.54,
    "swing_16th_medium": 0.58,
    "swing_16th_heavy": 0.64,
    "swing_8th": 0.58,
    "laid_back": 0.50,
    "pushing": 0.50,
    "human": 0.53
}

GROOVE_PROFILES = GROOVE_SWING_RATIOS

def apply_groove_to_notes(
    notes: List[NoteEvent],
    profile: str = "straight",
    tempo: float = 120.0,
    strength: float = 1.0,
    profile_name: str = None
) -> List[NoteEvent]:
    """
    Applies musical swing and timing offsets (push/pull) to a list of NoteEvents.
    Preserves determinism and note ordering.
    """
    prof = (profile_name or profile).lower()
    swing_ratio = GROOVE_SWING_RATIOS.get(prof, 0.50)
    
    # Milliseconds per beat = (60 / tempo) * 1000
    ms_per_beat = (60.0 / tempo) * 1000.0
    beats_per_ms = 1.0 / ms_per_beat

    # Fixed push / pull offsets in ms
    push_pull_ms = 0.0
    if prof == "laid_back":
        push_pull_ms = 6.0 * strength   # delayed slightly
    elif prof == "pushing":
        push_pull_ms = -4.0 * strength  # anticipated slightly

    offset_beats = push_pull_ms * beats_per_ms

    adjusted: List[NoteEvent] = []
    for note in notes:
        # Calculate position within the current beat (0.0 to 1.0)
        beat_phase = note.start % 1.0
        new_start = note.start + offset_beats

        # Check if note sits on the 2nd or 4th sixteenth note of a beat (0.25 or 0.75)
        # Swing delays the off-sixteenth
        is_swingable = abs(beat_phase - 0.25) < 0.03 or abs(beat_phase - 0.75) < 0.03
        if is_swingable and swing_ratio > 0.50:
            # Shift = (swing_ratio - 0.5) * 0.5 beats * strength
            swing_shift = (swing_ratio - 0.50) * 0.5 * strength
            new_start += swing_shift

        adj_ev = NoteEvent(
            pitch=note.pitch,
            pitch_class=note.pitch_class,
            octave=note.octave,
            start=max(0.0, round(new_start, 5)),
            duration=note.duration,
            velocity=note.velocity,
            channel=note.channel,
            probability=note.probability,
            accent=note.accent
        )
        adjusted.append(adj_ev)

    return adjusted
