# engine/mix/frequency_slotting.py
"""
Frequency Slotting & Complementary EQ Carving Engine:
Calculates surgical notch, bell, and shelf cuts to interlock conflicting stems,
carves out acoustic pockets, and enforces strict High-Pass Filtering across all 8 session tracks.
"""

import math
from typing import Dict, Any, List, Optional, Tuple


class FrequencySlottingEngine:
    """Calculates complementary EQ curves to eliminate frequency collisions between stems."""

    F_MIN = 10.0
    F_MAX = 22000.0
    LOG_RANGE = math.log10(F_MAX / F_MIN)

    @classmethod
    def freq_to_normalized(cls, freq_hz: float) -> float:
        """Converts frequency in Hz (10 to 22000) to EQ Eight's normalized float [0.0..1.0]."""
        clamped = max(cls.F_MIN, min(cls.F_MAX, freq_hz))
        return round(math.log10(clamped / cls.F_MIN) / cls.LOG_RANGE, 6)

    @classmethod
    def get_multitrack_hpf_scaffold(cls) -> Dict[str, Dict[str, Any]]:
        """
        Returns surgical High-Pass Filter cutoff frequencies and Q values
        tailored for each instrument role across the 8 standard session tracks.
        """
        return {
            "sub_808": {
                "hpf_freq_hz": 28.0,
                "normalized": cls.freq_to_normalized(28.0),
                "q": 0.40,
                "description": "Cuts inaudible sub-rumble below 28Hz, preserving massive headroom."
            },
            "kick": {
                "hpf_freq_hz": 35.0,
                "normalized": cls.freq_to_normalized(35.0),
                "q": 0.40,
                "description": "Removes DC offset and mud while anchoring sub punch."
            },
            "snare": {
                "hpf_freq_hz": 85.0,
                "normalized": cls.freq_to_normalized(85.0),
                "q": 0.38,
                "description": "Tightens snare fundamental around 200Hz, removing hollow boxiness."
            },
            "hihats_perc": {
                "hpf_freq_hz": 320.0,
                "normalized": cls.freq_to_normalized(320.0),
                "q": 0.38,
                "description": "Completely clears low and low-mid spectrum for maximum drum air."
            },
            "chords_keys": {
                "hpf_freq_hz": 110.0,
                "normalized": cls.freq_to_normalized(110.0),
                "q": 0.38,
                "description": "Pans low end out of bass lane, letting 808 dominate cleanly."
            },
            "lead_synth": {
                "hpf_freq_hz": 140.0,
                "normalized": cls.freq_to_normalized(140.0),
                "q": 0.38,
                "description": "Cleans bottom end so synth cuts through top of the mix."
            },
            "vocals_chops": {
                "hpf_freq_hz": 120.0,
                "normalized": cls.freq_to_normalized(120.0),
                "q": 0.42,
                "description": "Eliminates mic proximity effect and plosive rumble."
            },
            "foley_fx": {
                "hpf_freq_hz": 180.0,
                "normalized": cls.freq_to_normalized(180.0),
                "q": 0.38,
                "description": "Constrains textures and downlifters away from rhythmic punch."
            }
        }

    @classmethod
    def calculate_complementary_carving(
        cls,
        role_primary: str,
        role_secondary: str,
        primary_fundamental_hz: float = 52.0,
        secondary_fundamental_hz: float = 38.0
    ) -> Dict[str, Any]:
        """
        Calculates interlocking EQ Eight curves between two competing elements:
        - Creates a surgical notch on secondary track at primary fundamental.
        - Creates a complementary notch on primary track at secondary fundamental.
        """
        r1 = role_primary.lower()
        r2 = role_secondary.lower()

        carving_plan: Dict[str, Any] = {
            "pair": f"{r1}_vs_{r2}",
            "primary": {"role": r1, "cuts": []},
            "secondary": {"role": r2, "cuts": []}
        }

        if ("kick" in r1 and "bass" in r2) or ("bass" in r1 and "kick" in r2):
            # Kick (punch @ primary_fundamental) vs 808 (sub @ secondary_fundamental)
            kick_fund = primary_fundamental_hz if "kick" in r1 else secondary_fundamental_hz
            bass_fund = secondary_fundamental_hz if "kick" in r1 else primary_fundamental_hz

            carving_plan["primary"]["cuts"].append({
                "filter_band": 3,
                "filter_type": 3.0,  # Bell
                "freq_hz": round(bass_fund, 1),
                "freq_normalized": cls.freq_to_normalized(bass_fund),
                "gain_db": -4.0,
                "q": 3.2,
                "purpose": f"Notch kick at {bass_fund}Hz to give 808 sub clean fundamental space"
            })
            carving_plan["secondary"]["cuts"].append({
                "filter_band": 3,
                "filter_type": 3.0,  # Bell
                "freq_hz": round(kick_fund, 1),
                "freq_normalized": cls.freq_to_normalized(kick_fund),
                "gain_db": -3.5,
                "q": 3.0,
                "purpose": f"Notch 808 at {kick_fund}Hz to let kick transient punch through"
            })

        elif ("vocal" in r1 or "lead" in r1) and ("chord" in r2 or "key" in r2 or "pad" in r2):
            # Vocal/Lead presence (2.8 kHz) vs Chords mid pocket
            presence_freq = 2800.0
            carving_plan["secondary"]["cuts"].append({
                "filter_band": 3,
                "filter_type": 3.0,  # Bell
                "freq_hz": presence_freq,
                "freq_normalized": cls.freq_to_normalized(presence_freq),
                "gain_db": -3.0,
                "q": 1.4,
                "purpose": "Wide mid pocket dip on chords to let vocal/lead melody pierce through"
            })

        elif "snare" in r1 and ("key" in r2 or "chord" in r2):
            # Snare snap (200 Hz body) vs Keys
            carving_plan["secondary"]["cuts"].append({
                "filter_band": 2,
                "filter_type": 3.0,
                "freq_hz": 200.0,
                "freq_normalized": cls.freq_to_normalized(200.0),
                "gain_db": -2.0,
                "q": 2.0,
                "purpose": "Carve 200Hz out of keys to prevent snare body masking"
            })

        return carving_plan

    @classmethod
    def generate_full_session_slotting_plan(
        cls,
        session_tracks: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generates the master surgical frequency slotting blueprint for the entire 8-track session.
        """
        hpf_scaffold = cls.get_multitrack_hpf_scaffold()
        kick_bass_slot = cls.calculate_complementary_carving("kick", "bass", 52.0, 38.0)
        vocal_chord_slot = cls.calculate_complementary_carving("vocal", "chords")
        snare_keys_slot = cls.calculate_complementary_carving("snare", "keys")

        return {
            "status": "SUCCESS",
            "phase": "PHASE_6_MIX_SURGICAL",
            "hpf_enforcement": hpf_scaffold,
            "complementary_carvings": [
                kick_bass_slot,
                vocal_chord_slot,
                snare_keys_slot
            ],
            "total_conflicts_resolved": 3
        }
