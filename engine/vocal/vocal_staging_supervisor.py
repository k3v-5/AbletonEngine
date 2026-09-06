# engine/vocal/vocal_staging_supervisor.py
"""
Vocal Lead Staging & Multitrack Ducking Supervisor:
Orchestrates spectral slotting (-3 dB dip in harmonic accompaniment at 2.5-3.0 kHz),
dynamic sidechain ducking of instrumental beds when vocal or lead is active,
and stage gain-riding to maintain vocal primacy in commercial mixes.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from engine.vocal.pipeline import VocalProductionEngine, VocalStyle
from engine.mix.frequency_slotting import FrequencySlottingEngine

logger = logging.getLogger("VocalStagingSupervisor")


class VocalStagingSupervisor:
    """Supervises vocal presence carving, dynamic ducking, and staging matrix."""

    @classmethod
    def calculate_vocal_staging_plan(
        cls,
        track_names: List[str],
        vocal_ranges_beats: Optional[List[Tuple[float, float]]] = None,
        song_length_beats: float = 128.0,
        duck_amount_db: float = -2.5,
        vocal_style: Union[str, VocalStyle] = VocalStyle.MODERN_RAP
    ) -> Dict[str, Any]:
        """
        Builds complete staging blueprint:
        1. Identifies accompaniment tracks that compete with vocal presence (keys, pads, chords, synths).
        2. Generates complementary EQ Eight/Pro-Q notch cuts (-3.0 dB at 2.8 kHz, Q=1.4) for accompaniment.
        3. Calculates time-continuous ducking envelope for accompaniment busses.
        4. Provides recommended channel strip settings for the vocal track itself.
        """
        vocal_profile = VocalProductionEngine.get_vocal_profile(vocal_style)
        duck_targets = VocalProductionEngine.identify_ducking_targets(track_names)

        # 1. Frequency carving plans for all competing accompaniment tracks
        carving_plans = []
        for target_idx in duck_targets:
            target_name = track_names[target_idx]
            carving = FrequencySlottingEngine.calculate_complementary_carving(
                role_primary="vocal",
                role_secondary=target_name
            )
            carving_plans.append({
                "track_index": target_idx,
                "track_name": target_name,
                "frequency_hz": 2800.0,
                "cut_gain_db": -3.0,
                "q": 1.4,
                "carving_spec": carving
            })

        # 2. Dynamic ducking envelope calculation
        ducking_envelope = []
        if vocal_ranges_beats:
            ducking_envelope = VocalProductionEngine.calculate_ducking_envelope(
                vocal_ranges_beats=vocal_ranges_beats,
                song_length_beats=song_length_beats,
                duck_amount_db=duck_amount_db,
                baseline_volume=0.85
            )

        return {
            "status": "SUCCESS",
            "vocal_style": vocal_profile.style.value,
            "competing_tracks_count": len(duck_targets),
            "competing_track_indices": duck_targets,
            "frequency_carvings": carving_plans,
            "ducking_envelope_points_count": len(ducking_envelope),
            "ducking_envelope": ducking_envelope,
            "vocal_chain_stages": [
                {
                    "stage": s.stage_name,
                    "device": s.suggested_native,
                    "vst": s.suggested_vst,
                    "rationale": s.rationale
                } for s in vocal_profile.chain
            ]
        }

    @classmethod
    def apply_staging_to_session(
        cls,
        conn: Any,
        vocal_track_index: int,
        accompaniment_track_indices: List[int]
    ) -> Dict[str, Any]:
        """
        Applies live parametric carving or volume trim to accompaniment tracks in Live.
        """
        if conn is None or not hasattr(conn, "send_command"):
            return {
                "status": "MOCK_OK",
                "vocal_track": vocal_track_index,
                "carved_tracks": accompaniment_track_indices
            }

        applied = []
        for t_idx in accompaniment_track_indices:
            try:
                # Set slight volume dip or carve EQ
                conn.send_command("set_track_volume", {
                    "track_index": t_idx,
                    "volume": 0.80  # Ducking trim
                })
                applied.append(t_idx)
            except Exception as e:
                logger.warning(f"Failed to apply ducking on track {t_idx}: {e}")

        return {
            "status": "SUCCESS",
            "vocal_track": vocal_track_index,
            "carved_tracks": applied
        }
