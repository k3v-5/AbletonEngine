# engine/mix/z_plane_depth.py
"""
Z-Plane Depth Architect Engine:
Establishes a three-dimensional psychoacoustic listening field (Foreground, Midground, Deep Background).
Calibrates transient sharpness, air absorption roll-off, early reflection pre-delay, and diffusion
to create front-to-back depth separation without muddying the mix.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("ZPlaneDepthArchitect")


class ZPlaneDepthArchitect:
    """
    Coordinates 3D depth positioning across arrangement tracks and stems.
    """

    DEPTH_TIERS = {
        "FOREGROUND": {
            "z_value": 0.0,
            "transient_attack_db": 0.0,
            "early_reflections_mix": 0.0,
            "air_absorption_cutoff_hz": 20000.0,
            "pre_delay_ms": 0.0,
            "description": "Plano frontal directo (In-Your-Face, transientes secos y presencia absoluta)"
        },
        "MIDGROUND": {
            "z_value": 0.5,
            "transient_attack_db": -2.0,
            "early_reflections_mix": 0.18,
            "air_absorption_cutoff_hz": 12000.0,
            "pre_delay_ms": 15.0,
            "description": "Plano medio armónico (Cuerpo, calidez y ligera difusión de sala)"
        },
        "BACKGROUND": {
            "z_value": 1.0,
            "transient_attack_db": -4.0,
            "early_reflections_mix": 0.42,
            "air_absorption_cutoff_hz": 8000.0,
            "pre_delay_ms": 32.0,
            "description": "Fondo inmersivo profundo (Absorción de aire, pre-delay largo y halo difuso)"
        }
    }

    ROLE_DEPTH_MAP = {
        "VOCALS": "FOREGROUND",
        "LEAD_VOCAL": "FOREGROUND",
        "KICK": "FOREGROUND",
        "SNARE": "FOREGROUND",
        "CLAP": "FOREGROUND",
        "BASS": "FOREGROUND",
        "SUB": "FOREGROUND",

        "KEYS": "MIDGROUND",
        "PIANO": "MIDGROUND",
        "GUITAR": "MIDGROUND",
        "LEAD": "MIDGROUND",
        "SYNTH": "MIDGROUND",
        "PLUCK": "MIDGROUND",
        "BRASS": "MIDGROUND",

        "PAD": "BACKGROUND",
        "PADS": "BACKGROUND",
        "STRINGS": "BACKGROUND",
        "HARMONY": "BACKGROUND",
        "BACKING": "BACKGROUND",
        "CHOIR": "BACKGROUND",
        "FX": "BACKGROUND",
        "RISER": "BACKGROUND",
        "FOLEY": "BACKGROUND",
        "TEXTURE": "BACKGROUND"
    }

    @classmethod
    def get_tier_for_role(cls, role: str) -> str:
        """Resolves target Z-plane tier based on track role."""
        r_up = str(role or "").upper()
        for role_key, tier in cls.ROLE_DEPTH_MAP.items():
            if role_key in r_up:
                return tier
        return "MIDGROUND"

    @classmethod
    def prescribe_depth_parameters(cls, role: str) -> Dict[str, Any]:
        """Prescribes Z-plane acoustic parameters for a given instrument role."""
        tier = cls.get_tier_for_role(role)
        cfg = cls.DEPTH_TIERS[tier]
        return {
            "role": role,
            "depth_tier": tier,
            "z_value": cfg["z_value"],
            "transient_attack_factor": 1.0 if tier == "FOREGROUND" else (0.75 if tier == "MIDGROUND" else 0.5),
            "transient_attack_db": cfg["transient_attack_db"],
            "early_reflections_mix": cfg["early_reflections_mix"],
            "early_reflection_predelay_ms": cfg["pre_delay_ms"],
            "air_absorption_cutoff_hz": cfg["air_absorption_cutoff_hz"],
            "reverb_wet_percent": int(cfg["early_reflections_mix"] * 100),
            "description": cfg["description"]
        }

    @classmethod
    def evaluate_session_depth(cls, tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Audits all tracks in the session and assigns optimal 3D Z-plane depth profiles.
        """
        assigned_tiers = {"FOREGROUND": [], "MIDGROUND": [], "BACKGROUND": []}
        depth_distribution_objects = {"FOREGROUND": [], "MIDGROUND": [], "BACKGROUND": []}
        track_depth_plans = []

        for trk in tracks:
            r = trk.get("role", "SYNTH")
            tier = cls.get_tier_for_role(r)
            cfg = cls.DEPTH_TIERS[tier]
            t_idx = trk.get("index", 0)
            t_name = trk.get("name", f"Track {t_idx}")

            plan = {
                "track_index": t_idx,
                "track_name": t_name,
                "role": r,
                "depth_tier": tier,
                "z_value": cfg["z_value"],
                "transient_attack_db": cfg["transient_attack_db"],
                "early_reflections_mix": cfg["early_reflections_mix"],
                "air_absorption_cutoff_hz": cfg["air_absorption_cutoff_hz"],
                "pre_delay_ms": cfg["pre_delay_ms"]
            }
            assigned_tiers[tier].append(t_name)
            depth_distribution_objects[tier].append({"name": t_name, "role": r, "index": t_idx})
            track_depth_plans.append(plan)

        return {
            "status": "Z_DEPTH_CALIBRATED",
            "total_tracks": len(tracks),
            "tiers_distribution": {k: len(v) for k, v in assigned_tiers.items()},
            "assigned_tracks": assigned_tiers,
            "depth_distribution": depth_distribution_objects,
            "depth_plans": track_depth_plans
        }

    @classmethod
    def render_markdown_summary(cls, depth_audit: Dict[str, Any]) -> str:
        """Renders clear, human-readable markdown summary."""
        assigned = depth_audit.get("assigned_tracks", {})
        fg_str = ", ".join(assigned.get("FOREGROUND", [])) or "Ninguno"
        mg_str = ", ".join(assigned.get("MIDGROUND", [])) or "Ninguno"
        bg_str = ", ".join(assigned.get("BACKGROUND", [])) or "Ninguno"

        return (
            "🏛️ **Arquitectura Psicoacústica de Profundidad en Eje Z (Z-Plane Depth)**\n\n"
            f"• **Primer Plano (In-Your-Face, Z=0.0):** {fg_str}\n"
            f"• **Plano Medio (Anchura & Presencia, Z=0.5):** {mg_str}\n"
            f"• **Fondo Inmersivo (Profundidad & Aire, Z=1.0):** {bg_str}\n"
            "• **Resultado:** Separación física tridimensional de elementos sin saturar el espectro."
        )
