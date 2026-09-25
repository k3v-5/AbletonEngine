"""
Psychoacoustic Heuristics Advisor (Tier 3 Authority).
Evaluates mix health, phase correlation, mud box accumulation, and dynamic range.
Provides educational warnings that guide the AI/producer without blocking execution.
"""

from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger("HeuristicsAdvisor")


class HeuristicsAdvisor:
    """
    Tier 3 Advisor: Psychoacoustic Heuristics.
    Produces non-blocking advisory warnings (PASS_WITH_WARNING) to improve mix quality.
    """

    @classmethod
    def audit_psychoacoustics(
        cls,
        session_data: Dict[str, Any],
        tracks: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """
        Audits the current session structure for psychoacoustic clashing risks.
        Returns a list of advisory warning messages.
        """
        warnings: List[str] = []
        track_list = tracks if tracks is not None else session_data.get("tracks", [])

        # 1. Mud Box 200-500 Hz Accumulation (P15)
        low_mid_roles = {"KEYS", "PAD", "GUITAR", "RHYTHM_GUITAR", "STRINGS", "BRASS", "CHOIR"}
        clutter_count = 0
        for trk in track_list:
            role = str(trk.get("role", "")).upper()
            if role in low_mid_roles:
                # Check if this track lacks a mud-box cut
                sculpted = trk.get("sculpted_parameters", {})
                insert_effects = trk.get("insert_effects", [])
                has_cut = any(
                    "300" in str(p) or "400" in str(p) or "mud" in str(p).lower()
                    for p in sculpted.keys()
                )
                for eff in insert_effects:
                    params = eff.get("parameters", {})
                    if any("mud" in str(k).lower() or "300" in str(k) for k in params.keys()):
                        has_cut = True
                if not has_cut:
                    clutter_count += 1

        if clutter_count >= 3:
            warnings.append(
                f"[Heuristic P15] Acumulación de energía en Mud Box (200-500 Hz): {clutter_count} instrumentos "
                f"armónicos compiten en medios bajos sin ecualización quirúrgica de limpieza."
            )

        # 2. Sub-Bass Phase Correlation & Unison Risk (P14)
        for trk in track_list:
            role = str(trk.get("role", "")).upper()
            if role in {"SUB", "808_BASS", "BASS"}:
                params = trk.get("sculpted_parameters", {})
                unison = float(params.get("UNISON_DETUNE", params.get("unison_detune", 0.0)))
                if unison > 0.35:
                    warnings.append(
                        f"[Heuristic P14] Riesgo de cancelación de fase en graves: '{trk.get('name')}' tiene "
                        f"unison_detune={unison:.2f} (> 0.35). Se recomienda mantener subgraves completamente en fase."
                    )

        # 3. Dynamic Squashing / Crest Factor Warning (P44)
        for trk in track_list:
            for eff in trk.get("insert_effects", []):
                name = str(eff.get("name", "")).lower()
                if "compressor" in name or "glue" in name:
                    params = eff.get("parameters", {})
                    ratio = params.get("Ratio", params.get("ratio", 2.0))
                    thresh = params.get("Threshold", params.get("threshold", -12.0))
                    try:
                        if float(ratio) >= 8.0 and float(thresh) < -20.0:
                            warnings.append(
                                f"[Heuristic P44] Compresión severa en '{trk.get('name')}' ({eff.get('name')}): "
                                f"Ratio {ratio}:1 con Umbral {thresh} dBFS puede reducir el factor de cresta por debajo de 8 dB."
                            )
                    except (ValueError, TypeError):
                        pass

        # 4. Abbey Road Reverb Send Filters (P18)
        for trk in track_list:
            for eff in trk.get("insert_effects", []):
                name = str(eff.get("name", "")).lower()
                if ("reverb" in name or "verb" in name) and not eff.get("bypass", False):
                    params = eff.get("parameters", {})
                    has_low_cut = any("lowcut" in str(k).lower() or "hpf" in str(k).lower() for k in params.keys())
                    if not has_low_cut:
                        warnings.append(
                            f"[Heuristic P18] Filtro Abbey Road recomendado para Reverb en '{trk.get('name')}': "
                            f"aplicar HPF en 500 Hz y LPF en 8 kHz para preservar claridad en la mezcla."
                        )

        # 5. Drop 2 Arrangement Mutation (P24)
        sections = session_data.get("sections", [])
        drop_sections = [s for s in sections if "drop" in str(s.get("name", "")).lower()]
        if len(drop_sections) >= 2:
            second_drop_contracts = session_data.get("structural_contracts", {})
            has_variation_contract = any(
                "drop_2" in str(k).lower() or "drop" in str(k).lower()
                for k in second_drop_contracts.keys()
            )
            if not has_variation_contract and not session_data.get("drop_2_mutated", False):
                warnings.append(
                    "[Heuristic P24] Variación en segundo Drop recomendada: Se detectaron múltiples drops en el arreglo. "
                    "Inyectar mutación rítmica, cambio de octava o pre-drop vacuum para maximizar impacto emocional."
                )

        return warnings
