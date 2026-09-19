# engine/mix/spectral_carver.py
"""
Spectral Carver & Acoustic Space Architect:
- Spectral Sidechain (<80 Hz sub-bass ducking with transient preservation) [Punto 16]
- Dynamic Frequency Carving (Complementary surgical EQ between competing stems) [Punto 17]
- Mid/Side Slotting & Spatial Separation (Mono bass integrity <120 Hz, Mid lead, Side spread) [Punto 19]
"""

from typing import Dict, Any, List, Optional, Tuple
import math
import numpy as np


class SpectralCarver:
    """Manages frequency carving, low-end spectral sidechaining, and mid/side placement."""

    F_MIN = 10.0
    F_MAX = 22000.0
    LOG_RANGE = math.log10(F_MAX / F_MIN)

    @classmethod
    def freq_to_normalized(cls, freq_hz: float) -> float:
        """Converts frequency in Hz to Ableton EQ Eight normalized value [0.0..1.0]."""
        clamped = max(cls.F_MIN, min(cls.F_MAX, freq_hz))
        return round(math.log10(clamped / cls.F_MIN) / cls.LOG_RANGE, 6)

    @classmethod
    def calculate_spectral_sidechain(
        cls,
        kick_track_idx: int = 0,
        bass_track_idx: int = 1,
        crossover_hz: float = 80.0,
        ducking_depth_db: float = -6.0,
        bpm: float = 120.0
    ) -> Dict[str, Any]:
        """
        Punto 16: Spectral Sidechain (<80 Hz ducking).
        Instead of broadband sidechain pumping that dulls upper bass harmonics,
        ducks ONLY the frequency zone below crossover_hz (<80 Hz) on the bass track,
        preserving transient punch and mid-range bass texture intact.
        """
        beat_duration_ms = (60.0 / bpm) * 1000.0
        # Optimal fast attack 2-4 ms, release ~1/8 note sub-tail decay
        attack_ms = 3.0
        release_ms = min(120.0, max(45.0, beat_duration_ms * 0.18))

        return {
            "status": "SPECTRAL_SIDECHAIN_CALCULATED",
            "kick_track_idx": kick_track_idx,
            "bass_track_idx": bass_track_idx,
            "crossover_hz": crossover_hz,
            "ducking_depth_db": ducking_depth_db,
            "attack_ms": round(attack_ms, 1),
            "release_ms": round(release_ms, 1),
            "multiband_configuration": {
                "low_band_cutoff_hz": crossover_hz,
                "low_band_ducking_db": ducking_depth_db,
                "mid_high_band_ducking_db": 0.0,
                "transient_preservation_active": True
            },
            "recommendation": f"Sidechain bass below {crossover_hz}Hz with {attack_ms}ms attack, {release_ms:.0f}ms release to eliminate sub collisions."
        }

    @classmethod
    def calculate_complementary_carving(
        cls,
        masker_role: str,
        target_role: str,
        masker_center_hz: float = 0.0,
        carve_depth_db: float = -3.5,
        q: float = 2.8
    ) -> Dict[str, Any]:
        """
        Punto 17: Dynamic Frequency Carving.
        Calculates complementary inverse notch/dip on the masking track
        centered around the target track's prominent fundamental frequency.
        """
        m_role = masker_role.lower()
        t_role = target_role.lower()

        # Preset standard acoustic conflicts if default
        freq = masker_center_hz
        if freq <= 0:
            if "vocal" in t_role and ("synth" in m_role or "key" in m_role or "guitar" in m_role or "chord" in m_role):
                freq = 2800.0  # Vocal presence pocket
            elif "snare" in t_role and ("key" in m_role or "chord" in m_role):
                freq = 220.0   # Snare body pocket
            elif "kick" in t_role and "bass" in m_role:
                freq = 55.0    # Kick click/sub punch
            else:
                freq = 1000.0

        eq_params = {
            "masker_role": m_role,
            "target_role": t_role,
            "target_fundamental_hz": round(freq, 1),
            "filter_band": 3,
            "filter_type": "bell",
            "freq_normalized": cls.freq_to_normalized(freq),
            "gain_db": carve_depth_db,
            "q": q,
            "description": f"Carve {carve_depth_db}dB at {freq}Hz (Q={q}) in {m_role} to open transparent acoustic pocket for {t_role}."
        }
        return eq_params

    @classmethod
    def calculate_mid_side_slotting(
        cls,
        track_roles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Punto 19: Mid/Side Slotting & Spatial Separation.
        - Sub & Kick (<120 Hz): 100% Mono / Mid. Side HPF at 120-140 Hz.
        - Lead Vocals / Snare: Anchored in Mid (+0.5 dB Mid gain, Side width 100%).
        - Synths, Pads, Reverbs, Ear Candy: Pushed to Side (Side gain +1.5 dB, stereo width 120-140%).
        """
        slotting_directives = []

        for trk in track_roles:
            role = str(trk.get("role", "")).lower()
            name = str(trk.get("name", "")).lower()
            idx = trk.get("track_index", 0)

            if "sub" in role or "bass" in role or "808" in role or "sub" in name or "808" in name:
                slotting_directives.append({
                    "track_index": idx,
                    "role": "sub_bass",
                    "mode": "MONO_MID_ONLY",
                    "side_hpf_hz": 130.0,
                    "side_hpf_normalized": cls.freq_to_normalized(130.0),
                    "stereo_width_pct": 0.0,
                    "mid_gain_db": 0.0,
                    "side_gain_db": -96.0,
                    "rationale": "Enforce strict mono sub-bass below 130Hz to prevent low-end phase cancellations."
                })
            elif "kick" in role or "kick" in name:
                slotting_directives.append({
                    "track_index": idx,
                    "role": "kick",
                    "mode": "MONO_MID_ANCHOR",
                    "side_hpf_hz": 110.0,
                    "side_hpf_normalized": cls.freq_to_normalized(110.0),
                    "stereo_width_pct": 0.0,
                    "mid_gain_db": 0.0,
                    "side_gain_db": -96.0,
                    "rationale": "Keep kick centered in Mid for direct transient energy."
                })
            elif "vocal" in role or "vox" in role or "lead" in role or "vocal" in name:
                slotting_directives.append({
                    "track_index": idx,
                    "role": "lead_vocal",
                    "mode": "MID_DOMINANT",
                    "side_hpf_hz": 150.0,
                    "side_hpf_normalized": cls.freq_to_normalized(150.0),
                    "stereo_width_pct": 105.0,
                    "mid_gain_db": 0.6,
                    "side_gain_db": -1.0,
                    "rationale": "Focus vocal intonation in phantom center, slight air on side."
                })
            elif ("pad" in role or "chord" in role or "foley" in role or "fx" in role or "reverb" in role or "candy" in role or
                  "pad" in name or "chord" in name or "synth" in name or "ambient" in name):
                slotting_directives.append({
                    "track_index": idx,
                    "role": "ambient_harmonic",
                    "mode": "SIDE_EXPANDED",
                    "side_hpf_hz": 160.0,
                    "side_hpf_normalized": cls.freq_to_normalized(160.0),
                    "stereo_width_pct": 130.0,
                    "mid_gain_db": -1.5,
                    "side_gain_db": 1.5,
                    "rationale": "Spread lush pads and effects to sides, clearing center for lead elements."
                })
            else:
                slotting_directives.append({
                    "track_index": idx,
                    "role": "standard",
                    "mode": "BALANCED_STEREO",
                    "side_hpf_hz": 120.0,
                    "side_hpf_normalized": cls.freq_to_normalized(120.0),
                    "stereo_width_pct": 100.0,
                    "mid_gain_db": 0.0,
                    "side_gain_db": 0.0,
                    "rationale": "Standard balanced stereo configuration."
                })

        return slotting_directives
