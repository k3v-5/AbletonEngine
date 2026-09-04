# engine/music/rhythm/generator.py
import random
from typing import List, Dict, Any, Optional
from ..models import NoteEvent
from .templates import GENRE_TEMPLATES, GM_DRUM_MAP

def generate_drums(
    genre: str = "melodic_techno",
    bars: int = 16,
    density: float = 0.7,
    energy: float = 0.8,
    seed: Optional[int] = 12345,
    fill_every_bars: int = 8
) -> List[NoteEvent]:
    """
    Generates a full multi-element drum arrangement across bars with dynamic velocity, fills, and accents.
    """
    rng = random.Random(seed)
    genre_key = genre.lower().replace("-", "_").replace(" ", "_")
    template = GENRE_TEMPLATES.get(genre_key, GENRE_TEMPLATES["melodic_techno"])

    events: List[NoteEvent] = []

    for bar in range(bars):
        bar_offset = bar * 4.0
        is_fill_bar = ((bar + 1) % fill_every_bars == 0)

        for element, offsets in template.items():
            pitch = GM_DRUM_MAP.get(element, 36)

            # Density filter: skip lighter elements if density is low
            if element in ["foley", "ride", "shaker"] and density < 0.6:
                continue

            for off in offsets:
                # If fill bar on the last 2 beats, modify kick/hats to let fill breathe
                if is_fill_bar and off >= 2.0 and element == "kick":
                    if rng.random() > 0.3:  # Drop kick occasionally in fill
                        continue

                # Base velocity calculation based on element role and energy
                if element == "kick":
                    base_vel = int(105 + 20 * energy)
                    accent = 1.0
                elif element in ["clap", "snare"]:
                    base_vel = int(95 + 25 * energy)
                    accent = 0.8
                elif element == "hat_open":
                    base_vel = int(85 + 25 * energy)
                    accent = 0.6
                elif element == "hat_closed":
                    # Velocity alternation (strong on 8ths, weaker on 16ths)
                    is_downbeat = (off % 0.5 == 0.0)
                    base_vel = int(80 + 20 * energy) if is_downbeat else int(50 + 25 * energy)
                    accent = 0.4 if is_downbeat else -0.2
                else:  # Foley / Perc
                    base_vel = int(60 + 30 * energy)
                    accent = 0.2

                # Micro velocity jitter
                vel = max(1, min(127, base_vel + rng.randint(-4, 4)))
                start_time = bar_offset + off

                ev = NoteEvent(
                    pitch=pitch,
                    pitch_class=pitch % 12,
                    octave=(pitch // 12) - 1,
                    start=start_time,
                    duration=0.25 if element != "hat_open" else 0.5,
                    velocity=vel,
                    accent=accent
                )
                events.append(ev)

        # Inject fill elements on fill bars (e.g. snare roll / toms on beats 3.0 to 4.0)
        if is_fill_bar:
            fill_steps = [2.5, 2.75, 3.0, 3.25, 3.5, 3.75]
            for step_idx, f_off in enumerate(fill_steps):
                # Snare / Tom crescendo
                crescendo_vel = int(70 + (step_idx / len(fill_steps)) * 45 * energy)
                f_pitch = GM_DRUM_MAP["snare"] if step_idx % 2 == 0 else GM_DRUM_MAP["tom_mid"]
                events.append(NoteEvent(
                    pitch=f_pitch,
                    pitch_class=f_pitch % 12,
                    octave=(f_pitch // 12) - 1,
                    start=bar_offset + f_off,
                    duration=0.2,
                    velocity=max(1, min(127, crescendo_vel)),
                    accent=0.9
                ))

    # Sort events by start time and pitch
    events.sort(key=lambda e: (e.start, e.pitch))
    return events
