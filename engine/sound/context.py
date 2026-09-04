"""
Mix Context, Frequency Role Mapping & Adaptive Sound Advisor.
Prevents frequency collision between Kick, Sub-bass, Bass, Leads, and Pads.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class FrequencyBand:
    name: str
    min_hz: float
    max_hz: float
    dominant_roles: List[str]

class FrequencyRoleMap:
    """Defines acoustic spectrum frequency domains."""
    BANDS = [
        FrequencyBand("Sub", 20.0, 60.0, ["SUB_BASS", "KICK_SUB"]),
        FrequencyBand("Low", 60.0, 120.0, ["KICK", "BASS"]),
        FrequencyBand("Low-Mid", 120.0, 300.0, ["BASS", "SNARE_BODY", "WARM_PAD"]),
        FrequencyBand("Mid", 300.0, 800.0, ["CHORDS", "VOCAL_BODY", "LEAD_BODY"]),
        FrequencyBand("High-Mid", 800.0, 2500.0, ["LEAD", "VOCAL", "PERCUSSION"]),
        FrequencyBand("Presence", 2500.0, 6000.0, ["SNARE_CRACK", "LEAD_BITE", "HIHAT_CLOSED"]),
        FrequencyBand("Brilliance", 6000.0, 12000.0, ["HIHAT_OPEN", "CYMBALS", "AIR"]),
        FrequencyBand("Air", 12000.0, 20000.0, ["SHAKER", "FX_RISER"])
    ]

    ROLE_FREQUENCY_PROFILES: Dict[str, Dict[str, Any]] = {
        "SUB_BASS": {"fundamental_hz": [20.0, 60.0], "body_hz": [60.0, 100.0], "stereo": False},
        "BASS": {"fundamental_hz": [40.0, 150.0], "harmonics_hz": [150.0, 800.0], "stereo": False},
        "KICK": {"fundamental_hz": [45.0, 65.0], "click_hz": [2000.0, 5000.0], "stereo": False},
        "LEAD": {"fundamental_hz": [300.0, 2000.0], "air_hz": [6000.0, 12000.0], "stereo": True},
        "PAD": {"warmth_hz": [200.0, 800.0], "space_hz": [800.0, 6000.0], "stereo": True},
        "CHORDS": {"body_hz": [250.0, 1200.0], "presence_hz": [2000.0, 6000.0], "stereo": True},
        "DRUMS": {"spectrum_hz": [20.0, 20000.0], "stereo": True}
    }

@dataclass
class MixContext:
    """Current musical context across active session tracks."""
    kick_frequency_hz: float = 55.0
    bass_frequency_hz: float = 50.0
    arrangement_density: float = 0.7
    tempo: float = 128.0
    key: str = "F"
    section_name: str = "Drop 1"
    section_energy: float = 0.90
    headroom_db: float = -6.0
    active_roles: List[str] = field(default_factory=list)

class AdaptiveAdvisor:
    """Analyzes MixContext to diagnose frequency clashes and produce sound design recommendations."""

    @staticmethod
    def evaluate_clashes(context: MixContext) -> List[Dict[str, Any]]:
        recommendations = []
        
        # 1. Low-end collision between Kick & Bass
        if abs(context.kick_frequency_hz - context.bass_frequency_hz) < 15.0:
            recommendations.append({
                "issue": "LOW_END_MASKING",
                "severity": "WARNING",
                "description": f"Kick fundamental ({context.kick_frequency_hz}Hz) and Bass fundamental ({context.bass_frequency_hz}Hz) collide within 15Hz.",
                "action": "SIDECHAIN_OR_PITCH_OFFSET",
                "suggested_actions": [
                    "Engage sidechain ducking on BASS triggered by KICK (amount >= 0.6)",
                    "Shorten bass release/decay time",
                    "Carve 3dB dip at 55Hz on BASS EQ Eight"
                ]
            })

        # 2. Excessive arrangement density during high-energy sections
        if context.section_energy > 0.85 and context.arrangement_density > 0.8:
            recommendations.append({
                "issue": "HIGH_ENERGY_CLUTTER",
                "severity": "INFO",
                "description": "High arrangement density with full role activation.",
                "action": "NARROW_STEREO_MID_ROLES",
                "suggested_actions": [
                    "High-pass Pads and Chords above 250Hz",
                    "Keep Sub-bass and Kick strictly Mono"
                ]
            })

        return recommendations

    @staticmethod
    def check_low_end_phase(role: str, panning: float = 0.0) -> Dict[str, Any]:
        """Validates that low-end roles (SUB_BASS, KICK) are strictly mono/centered."""
        clean_role = role.upper().strip()
        if clean_role in ["SUB_BASS", "SUB", "KICK"]:
            if abs(panning) > 0.05:
                return {
                    "valid": False,
                    "role": clean_role,
                    "panning": panning,
                    "issue": "STEREO_LOW_END",
                    "recommendation": f"{clean_role} must be centered/mono (panning=0.0) to prevent acoustic phase cancellation."
                }
        return {"valid": True, "role": clean_role, "panning": panning}
