# engine/mix/headroom_budget_engine.py
"""
Headroom Budget Engine & Summing Bus Guardian:
Punto 18: Prevents digital summing bus distortion and clipping.
Calculates coherent vs incoherent stem summing accumulation and dynamically allocates
fader headroom budgets to guarantee an unclipped, pristine >= 6.0 dBFS headroom margin
before feeding into the mastering chain.
"""

from typing import Dict, Any, List, Optional
import math
import numpy as np


class HeadroomBudgetEngine:
    """Calculates mix summing acoustics and allocates track headroom budgets."""

    DEFAULT_TARGET_HEADROOM_DBFS = -6.0

    @classmethod
    def calculate_incoherent_sum(cls, track_levels_db: List[float]) -> float:
        """
        Calculates uncorrelated (incoherent) power summing:
        L_sum = 10 * log10( sum( 10^(L_i / 10) ) )
        """
        if not track_levels_db:
            return -96.0
        # Filter out silence
        active = [l for l in track_levels_db if l > -90.0]
        if not active:
            return -96.0
        lin_power = sum(10.0 ** (l / 10.0) for l in active)
        return round(10.0 * math.log10(max(1e-12, lin_power)), 2)

    @classmethod
    def calculate_coherent_sum(cls, track_levels_db: List[float]) -> float:
        """
        Calculates worst-case in-phase (coherent) amplitude summing:
        L_sum = 20 * log10( sum( 10^(L_i / 20) ) )
        """
        if not track_levels_db:
            return -96.0
        active = [l for l in track_levels_db if l > -90.0]
        if not active:
            return -96.0
        lin_amp = sum(10.0 ** (l / 20.0) for l in active)
        return round(20.0 * math.log10(max(1e-12, lin_amp)), 2)

    @classmethod
    def predict_master_sum_level(
        cls,
        track_peaks_db: List[float],
        correlation_factor: float = 0.35
    ) -> float:
        """
        Calculates realistic music summing level:
        Blends incoherent power sum (65%) with coherent peak sum (35%).
        """
        if not track_peaks_db:
            return -96.0
        incoh = cls.calculate_incoherent_sum(track_peaks_db)
        coh = cls.calculate_coherent_sum(track_peaks_db)
        pred = (correlation_factor * coh) + ((1.0 - correlation_factor) * incoh)
        return round(pred, 2)

    @classmethod
    def audit_and_budget_headroom(
        cls,
        tracks: List[Dict[str, Any]],
        target_headroom_db: float = DEFAULT_TARGET_HEADROOM_DBFS
    ) -> Dict[str, Any]:
        """
        Audits full session track peaks and computes exact trim offsets
        to ensure predicted master bus peak stays below target_headroom_db.
        """
        peaks = []
        track_entries = []

        for t in tracks:
            pk = float(t.get("peak_db", t.get("peak", -12.0)))
            peaks.append(pk)
            track_entries.append({
                "track_index": t.get("index", t.get("track_index", 0)),
                "name": t.get("name", f"Track {len(track_entries)+1}"),
                "role": t.get("role", "general"),
                "current_peak_db": round(pk, 2)
            })

        predicted_master_peak = cls.predict_master_sum_level(peaks)
        headroom_available = -predicted_master_peak
        target_headroom_positive = abs(target_headroom_db)

        # Deficit exists if predicted peak is hotter than target (e.g. -2 dBFS vs target -6 dBFS -> 4 dB deficit)
        deficit_db = max(0.0, round(predicted_master_peak - target_headroom_db, 2))
        compliance = deficit_db <= 0.0

        trims = []
        if not compliance:
            # Need to trim tracks to carve out deficit
            # Protect kick and lead vocal by trimming secondary tracks slightly more
            for entry in track_entries:
                role = str(entry["role"]).lower()
                name = str(entry["name"]).lower()
                # Priority tracks: kick and lead vocal take smaller trims
                if "kick" in role or "kick" in name or "lead" in role or "vox" in role:
                    trim = -round(deficit_db * 0.70, 2)
                elif "foley" in role or "fx" in role or "pad" in role:
                    trim = -round(deficit_db * 1.30, 2)
                else:
                    trim = -round(deficit_db, 2)

                trims.append({
                    "track_index": entry["track_index"],
                    "name": entry["name"],
                    "current_peak_db": entry["current_peak_db"],
                    "recommended_trim_db": trim,
                    "target_peak_db": round(entry["current_peak_db"] + trim, 2)
                })
        else:
            for entry in track_entries:
                trims.append({
                    "track_index": entry["track_index"],
                    "name": entry["name"],
                    "current_peak_db": entry["current_peak_db"],
                    "recommended_trim_db": 0.0,
                    "target_peak_db": entry["current_peak_db"]
                })

        return {
            "status": "COMPLIANT" if compliance else "HEADROOM_DEFICIT_DETECTED",
            "predicted_master_peak_dbfs": predicted_master_peak,
            "target_headroom_dbfs": target_headroom_db,
            "deficit_db": deficit_db,
            "is_headroom_safe": compliance,
            "total_tracks": len(tracks),
            "trims": trims,
            "action": "PASS" if compliance else "APPLY_SUMMING_BUS_TRIMS"
        }
