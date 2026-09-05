# engine/mix/multitrack_sidechain.py
"""
Multi-Track Sidechain Ducking Coordinator:
Coordinates physical sidechain compression routing and envelope ducking
across Kick-to-Bass, Vocal-to-Chords, and Kick-to-Reverb buses.
"""

import math
from typing import Dict, Any, List, Optional


class MultiTrackSidechainCoordinator:
    """Master architect for multitrack sidechain compression routing."""

    SIDECHAIN_ROUTING_PROFILES = [
        {
            "id": "SC-KICK-TO-BASS",
            "source_role": "kick",
            "target_role": "bass_808",
            "attack_ms": 0.1,
            "release_ms": 48.0,
            "ratio": 4.0,
            "threshold_db": -16.0,
            "ducking_depth_db": -7.5,
            "knee": 2.0,
            "description": "Essential sub-bass ducking: completely clears space for kick transient punch."
        },
        {
            "id": "SC-KICK-TO-REVERB",
            "source_role": "kick",
            "target_role": "fx_reverb",
            "attack_ms": 1.0,
            "release_ms": 120.0,
            "ratio": 3.0,
            "threshold_db": -14.0,
            "ducking_depth_db": -5.0,
            "knee": 3.0,
            "description": "Ducks reverb/delay tails during kick strikes to avoid muddy low-mid wash."
        },
        {
            "id": "SC-VOCAL-TO-CHORDS",
            "source_role": "vocal",
            "target_role": "chords_keys",
            "attack_ms": 15.0,
            "release_ms": 220.0,
            "ratio": 2.5,
            "threshold_db": -20.0,
            "ducking_depth_db": -2.5,
            "knee": 4.0,
            "description": "Subtle harmonic ducking on keys/pads while vocal is singing, maintaining vocal clarity."
        },
        {
            "id": "SC-SNARE-TO-SPACE",
            "source_role": "snare",
            "target_role": "foley_textures",
            "attack_ms": 0.5,
            "release_ms": 80.0,
            "ratio": 3.5,
            "threshold_db": -15.0,
            "ducking_depth_db": -4.0,
            "knee": 2.0,
            "description": "Ducks atmospheric textures during snare crack to preserve sharp transient bite."
        }
    ]

    @classmethod
    def get_multitrack_sidechain_matrix(cls) -> Dict[str, Any]:
        """Returns the complete sidechain routing blueprint with compressor calibrations."""
        return {
            "status": "SUCCESS",
            "phase": "PHASE_6_MIX_SURGICAL",
            "total_routes": len(cls.SIDECHAIN_ROUTING_PROFILES),
            "routes": cls.SIDECHAIN_ROUTING_PROFILES
        }

    @classmethod
    def generate_compressor_device_parameters(
        cls,
        route_id: str = "SC-KICK-TO-BASS"
    ) -> Dict[str, float]:
        """
        Calculates normalized device parameter values for Ableton Live's native Compressor:
        - Sidechain On: 1.0
        - Ratio: normalized [0.0..1.0]
        - Attack: normalized [0.0..1.0]
        - Release: normalized [0.0..1.0]
        - Threshold: normalized [0.0..1.0]
        """
        route = next((r for r in cls.SIDECHAIN_ROUTING_PROFILES if r["id"] == route_id), cls.SIDECHAIN_ROUTING_PROFILES[0])

        # Ableton Compressor normalized mappings
        # Threshold: -40dB..0dB -> norm = (thresh + 40) / 40
        t_db = max(-40.0, min(0.0, route["threshold_db"]))
        norm_thresh = round((t_db + 40.0) / 40.0, 4)

        # Ratio: 1..Infinity -> norm ~ log2(ratio) / log2(100)
        norm_ratio = round(min(1.0, math.log2(route["ratio"]) / 6.0), 4)

        # Attack: 0.1ms..100ms
        norm_attack = round(min(1.0, route["attack_ms"] / 50.0), 4)

        # Release: 1ms..1000ms
        norm_release = round(min(1.0, route["release_ms"] / 500.0), 4)

        return {
            "sidechain_on": 1.0,
            "threshold": norm_thresh,
            "ratio": norm_ratio,
            "attack": norm_attack,
            "release": norm_release,
            "knee": 0.5,
            "auto_release_on": 0.0
        }
