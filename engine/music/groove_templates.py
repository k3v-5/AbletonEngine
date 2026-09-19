# engine/music/groove_templates.py
"""
Hardware Groove & Humanization Templates:
Applies authentic hardware swing, micro-timing offsets, and dynamic velocity modulation
(Akai MPC3000, E-mu SP-1200, J Dilla pocket) automatically to MIDI notes.
"""

from typing import Dict, Any, List, Optional
import math
import random
import logging

logger = logging.getLogger("GrooveTemplates")


class GrooveTemplateEngine:
    """Applies vintage hardware grooves and micro-timing dynamics to note streams."""

    TEMPLATES = {
        "AKAI_MPC3000": {
            "swing_factor": 0.58,   # 58% MPC swing
            "timing_jitter_ms": 3.0,
            "velocity_accent": 1.12,
            "description": "Crisp Roger Linn MPC3000 16-swing pocket"
        },
        "EMU_SP1200": {
            "swing_factor": 0.54,
            "timing_jitter_ms": 6.0,
            "velocity_accent": 1.18,
            "description": "Aggressive golden-era boom-bap crunch and drift"
        },
        "DILLA_POCKET": {
            "swing_factor": 0.62,
            "timing_jitter_ms": 14.0,  # Drifting unquantized feel
            "snare_delay_ms": 18.0,    # Laid-back snare
            "velocity_accent": 1.15,
            "description": "Soulquarians / J Dilla behind-the-beat humanized groove"
        },
        "MODERN_EDM": {
            "swing_factor": 0.50,
            "timing_jitter_ms": 1.5,
            "velocity_accent": 1.05,
            "description": "Rigid high-impact club quantization with micro-dynamics"
        }
    }

    @classmethod
    def apply_groove(
        cls,
        notes: List[Dict[str, Any]],
        template_name: str = "AKAI_MPC3000",
        intensity: float = 0.75,
        tempo: float = 120.0
    ) -> List[Dict[str, Any]]:
        """
        Applies timing swing and velocity curves from the selected template.
        """
        tmpl = cls.TEMPLATES.get(template_name.upper(), cls.TEMPLATES["AKAI_MPC3000"])
        swing = tmpl.get("swing_factor", 0.54)
        jitter_ms = tmpl.get("timing_jitter_ms", 3.0)
        snare_delay_ms = tmpl.get("snare_delay_ms", 0.0)
        v_accent = tmpl.get("velocity_accent", 1.10)

        ms_per_beat = (60.0 / tempo) * 1000.0
        beats_per_ms = 1.0 / ms_per_beat

        grooved_notes = []
        for n in notes:
            n_copy = dict(n)
            st = float(n_copy.get("start_time", n_copy.get("start", 0.0)))
            dur = float(n_copy.get("duration", 0.25))
            vel = int(n_copy.get("velocity", 100))
            pitch = int(n_copy.get("pitch", 36))

            # Determine 16th-note sub-beat position (0, 0.25, 0.50, 0.75)
            beat_sub = round(st % 1.0, 3)

            delta_beats = 0.0

            # 1. Swing on 2nd and 4th sixteenth notes (0.25, 0.75)
            if math.isclose(beat_sub, 0.25, abs_tol=0.04) or math.isclose(beat_sub, 0.75, abs_tol=0.04):
                # Swing shift in beats
                swing_shift = (swing - 0.50) * 0.50 * intensity
                delta_beats += swing_shift

            # 2. Laid-back snare delay (pitches 38, 40)
            if pitch in (38, 40) and snare_delay_ms > 0:
                delta_beats += (snare_delay_ms * beats_per_ms) * intensity

            # 3. Micro jitter
            rand_jitter = (random.uniform(-jitter_ms, jitter_ms) * beats_per_ms) * (intensity * 0.4)
            delta_beats += rand_jitter

            new_st = max(0.0, st + delta_beats)
            n_copy["start_time"] = round(new_st, 4)

            # Velocity dynamics
            if math.isclose(beat_sub, 0.0, abs_tol=0.04) or math.isclose(beat_sub, 0.50, abs_tol=0.04):
                # Downbeat accent
                new_vel = int(min(127, vel * (1.0 + (v_accent - 1.0) * intensity)))
            else:
                # Ghost sub-beat softening
                new_vel = int(max(40, vel * (1.0 - (v_accent - 1.0) * 0.5 * intensity)))

            n_copy["velocity"] = new_vel
            grooved_notes.append(n_copy)

        return grooved_notes
