# engine/production/contract/advanced_production_executor.py
"""
Advanced Production Executor:
Decoupled, modular execution engine coordinating the 6 advanced production modules
(TurnaroundEngine, DynamicGrooveHumanizer, SpatialNarrativePlan, MicroStutterEngine,
MultiLayerCrossoverStacker, MicroAutomationsPass, and MasterDynamics).
"""

from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional

from engine.production.contract.advanced_production_spec import (
    AdvancedProductionSpec,
    TurnaroundsAndSilencesConfig,
    GrooveAndPocketConfig,
    SpatialNarrativeConfig,
    EarCandyConfig,
    MasterDynamicsConfig,
    CrossoverStackingConfig,
)
from engine.production.copilot.phases.phase_6.turnaround_engine import TurnaroundEngine
from engine.music.groove.humanizer import DynamicGrooveHumanizer
from engine.music.groove.pocket import GroovePocketEngine, PocketStyle
from engine.sound_design.spatial_narrative import SpatialNarrativePlan, SpatialPoint
from engine.arrangement.transitions.micro_stutter import MicroStutterEngine
from engine.production.copilot.phases.phase_7.micro_automations import MicroAutomationsPass

logger = logging.getLogger("AdvancedProductionExecutor")


class AdvancedProductionExecutor:
    """Orchestrates modular physical execution of advanced production directives."""

    @classmethod
    def apply_groove_and_pocket_to_notes(
        cls,
        notes: List[Dict[str, Any]],
        role: str,
        config: GrooveAndPocketConfig,
        bpm: float = 120.0,
    ) -> List[Dict[str, Any]]:
        """
        Applies asymmetric laid-back snare dragging, sub dragging, and MPC swing to MIDI notes.
        """
        if not notes:
            return []

        r_up = str(role or "").upper()
        beats_per_ms = (bpm / 60.0) / 1000.0

        processed: List[Dict[str, Any]] = []
        for n in notes:
            n_copy = dict(n)
            start_t = float(n_copy.get("start_time", n_copy.get("start", 0.0)))
            pitch = int(n_copy.get("pitch", 60))
            vel = int(n_copy.get("velocity", 100))

            # 1. Asymmetric Snare Dragging (+12 to +18ms laid back)
            if config.snare_dragging_ms != 0.0 and r_up in ("DRUMS", "PERCUSSION", "SNARE"):
                # Pitches 38, 40 are standard snares; 80, 86, 87 are auxiliary percussion
                if pitch in (38, 40):
                    start_t += (config.snare_dragging_ms * beats_per_ms)

            # 2. Sub Dragging (+4 to +6ms)
            if config.sub_dragging_ms != 0.0 and any(k in r_up for k in ("BASS", "SUB", "808")):
                start_t += (config.sub_dragging_ms * beats_per_ms)

            # 3. Hi-Hat & Percussion hardware swing (supports both 16th-note and 8th-note pockets)
            if config.hihat_swing_pct != 50.0 and r_up in ("DRUMS", "PERCUSSION", "HATS"):
                if pitch in (42, 44, 46, 86, 87, 80, 81):  # Closed/pedal/open hat, shakers, auxiliary percs
                    pos_in_beat = start_t % 1.0
                    # 16th-note offbeats (e.g. 0.25, 0.75)
                    if 0.20 <= pos_in_beat <= 0.30 or 0.70 <= pos_in_beat <= 0.80:
                        swing_offset_beats = ((config.hihat_swing_pct - 50.0) / 100.0) * 0.25
                        start_t += swing_offset_beats
                    # 8th-note offbeats (e.g. 0.50) in classic Funk, French Pump, MPC 60, Boom Bap
                    elif 0.45 <= pos_in_beat <= 0.55:
                        swing_offset_beats = ((config.hihat_swing_pct - 50.0) / 100.0) * 0.35
                        start_t += swing_offset_beats

            # 4. Strict Acoustic Tesitura Clamping for Brass/Trumpets (G3 to C6, MIDI 55-84)
            if any(k in r_up for k in ("BRASS", "TRUMPET", "HORN")):
                while pitch < 55:
                    pitch += 12
                while pitch > 84:
                    pitch -= 12

            # 5. Velocity jitter
            jitter_amount = getattr(config, "humanize_velocity_jitter", 0)
            if jitter_amount > 0:
                import random
                jitter = int(random.gauss(0, jitter_amount))
                vel = max(1, min(127, vel + jitter))

            n_copy["pitch"] = pitch
            n_copy["start_time"] = round(max(0.0, start_t), 4)
            n_copy["velocity"] = vel
            processed.append(n_copy)

        return processed

    @classmethod
    def apply_turnaround_and_silences(
        cls,
        notes: List[Dict[str, Any]],
        role: str,
        config: TurnaroundsAndSilencesConfig,
        total_bars: int = 8,
        beats_per_bar: float = 4.0,
    ) -> List[Dict[str, Any]]:
        """
        Injects bar 8 turnaround variations, vacuum stops, and drum fills.
        """
        if not config.enabled or not notes:
            return notes

        r_up = str(role or "").upper()
        b_total = total_bars * beats_per_bar
        b8_start = (total_bars - 1) * beats_per_bar

        # A) Vacuum Stop: Silence accompaniment on the final beats of bar 8
        if config.vacuum_stops:
            vacuum_start = b_total - config.vacuum_duration_beats
            if any(k in r_up for k in ("BASS", "SUB", "808", "PAD", "KEYS", "GUITAR", "SYNTH")):
                # Strip out any notes falling into the vacuum window
                notes = [
                    n for n in notes
                    if not (vacuum_start <= float(n.get("start_time", 0.0)) < b_total)
                ]

        # B) Drum fills with kick dropout
        if config.drum_fills and r_up in ("DRUMS", "PERCUSSION"):
            if config.kick_dropout_in_fill:
                # Strip kick notes (pitch 35, 36) in the last 2 beats of bar 8
                fill_window_start = b_total - 2.0
                notes = [
                    n for n in notes
                    if not (n.get("pitch") in (35, 36) and fill_window_start <= float(n.get("start_time", 0.0)) < b_total)
                ]
            # Use TurnaroundEngine for the drum fill roll with rising crescendo
            notes = TurnaroundEngine.apply_turnaround(
                notes=notes,
                role=role,
                turnaround_type="drum_fill",
                beats_per_bar=beats_per_bar,
                total_bars=total_bars,
            )

        return notes

    @classmethod
    def generate_spatial_width_envelope(
        cls,
        sections: List[Dict[str, Any]],
        config: SpatialNarrativeConfig,
    ) -> List[Dict[str, Any]]:
        """
        Builds dynamic stereo width riding automation points across sections.
        """
        if not config.enabled or not sections:
            return []

        plan = SpatialNarrativePlan()
        for s in sections:
            s_name = str(s.get("name", "Section"))
            start_b = float(s.get("start_bar", 0)) * 4.0
            dur_b = float(s.get("bars", 8)) * 4.0
            end_b = start_b + dur_b

            s_lower = s_name.lower()
            if any(k in s_lower for k in ("chorus", "coro", "climax", "drop")):
                width_pct = config.chorus_width_pct
            elif any(k in s_lower for k in ("verse", "verso", "intro")):
                width_pct = config.verse_width_pct
            elif any(k in s_lower for k in ("bridge", "puente")):
                width_pct = config.bridge_width_pct
            else:
                width_pct = 100.0

            plan.points.append(SpatialPoint(
                section_name=s_name,
                start_beat=start_b,
                end_beat=end_b,
                stereo_width_pct=width_pct,
                mid_side_ratio=0.5,
                bass_mono_cutoff_hz=config.bass_mono_cutoff_hz,
                narrative_purpose=f"Spatial expansion for {s_name}",
            ))

        return plan.to_automation_envelope("Width")

    @classmethod
    def generate_tape_stop_points(
        cls,
        drop_beat: float,
        config: TurnaroundsAndSilencesConfig,
    ) -> Dict[str, Any]:
        """
        Generates volume and pitch deceleration points for an analog tape stop.
        """
        if not config.analog_tape_stop:
            return {}

        return MicroStutterEngine.generate_tape_stop_envelope(
            drop_start_beat=drop_beat,
            duration_beats=1.0,
            semitone_drop=config.tape_stop_semitones,
            preserve_drum_fills=True,
        )
