"""
Phase 10: Active Listening, Transport Navigation, Clip Micro-Surgery,
Vocal Production / Chops, Instrument Swap Re-validation, and Forensic Stem Export.
Facade handler delegating to specialized modular domain engines.
"""

import logging
from typing import Dict, Any, Optional, List

from engine.production.copilot.phases.base import BasePhaseHandler
from engine.production.copilot.nlp_parser import _normalize_text

from .instrument_swap import (
    initiate_instrument_swap_flow,
    prompt_instrument_swap_preset,
    handle_instrument_swap_step,
    execute_instrument_swap_reaudit,
)
from .stem_coordinator import audit_and_prepare_stems
from .vocal_pipeline import handle_vocal_pipeline
from .drop_mutator import handle_drop_mutator
from .surgery_and_navigation import (
    handle_clip_surgery,
    handle_master_gain_boost,
    handle_low_mid_resonance_clean,
    handle_top_and_tail_guard,
    handle_transport_navigation,
    handle_session_tweaks,
    handle_track_freeze,
    handle_texture_and_foley_injection,
)

logger = logging.getLogger("CopilotGuidedSession.Phase10")


class Phase10ListenersHandler(BasePhaseHandler):
    """
    Handles Phase 10: Active session management, transport controls, vocal production,
    instrument swap re-validation flow, and stem export quality gate.
    """

    def prompt(self, session: Any, conn: Any = None, **kwargs) -> Dict[str, Any]:
        return self.handle(session, conn, "")

    def initiate_instrument_swap_flow(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        return initiate_instrument_swap_flow(session, conn, user_input)

    def prompt_instrument_swap_preset(self, session: Any, trk: Dict[str, Any]) -> Dict[str, Any]:
        return prompt_instrument_swap_preset(session, trk)

    def handle_instrument_swap_step(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        return handle_instrument_swap_step(session, conn, user_input)

    def execute_instrument_swap_reaudit(self, session: Any, conn: Any) -> Dict[str, Any]:
        return execute_instrument_swap_reaudit(session, conn)

    def audit_and_prepare_stems(self, session: Any, conn: Any) -> Dict[str, Any]:
        return audit_and_prepare_stems(session, conn)

    def handle(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        text = _normalize_text(user_input)
        tracks = session.data.get("tracks", [])
        completed_phase = session.data.get("current_phase", "PHASE_10_COMPLETED")

        # 0. Instrument Swap Re-validation Flow (Fases 3 -> 4 -> 5 -> 6 -> 9 -> 10)
        is_swap_trigger = any(w in text for w in [
            "cambiar instrumento", "cambio de instrumento", "reemplazar instrumento",
            "modificar instrumento", "nuevo instrumento", "cambiar preset"
        ])
        if is_swap_trigger or session.data.get("instrument_swap_state", {}).get("active", False):
            return self.handle_instrument_swap_step(session, conn, user_input)

        # 0. Clip Micro-Surgery Gatekeeper (Compás puntual, velocidades, alturas)
        is_surgery_choice = any(w in text for w in ["microcirugia", "microedicion", "micro-cirugia", "micro-edicion", "mover nota", "mover notas", "cambiar velocidad", "ajustar clip", "editar clip", "compas 47", "compás 47"]) or (("opcion 2" in text or "opcion b" in text) and any(w in text for w in ["clip", "nota", "notas", "quirurgic", "velocidad", "compas"]))
        if is_surgery_choice:
            return handle_clip_surgery(conn, user_input, tracks, completed_phase)

        # 0. Retroactive Effect Recalibration in Phase 10
        is_effect_choice = any(w in text for w in ["corregir efecto", "corregir efectos", "ajustar efecto", "ajustar efectos", "modificar efecto", "modificar efectos"]) or (("opcion 3" in text or "opcion c" in text) and any(w in text for w in ["efecto", "efectos", "filtro", "reverb", "plugin", "dsp", "insert"]))
        if is_effect_choice:
            return session._prompt_effect_recalibration()

        # 0. Stem Export & Forensic Quality Audit Gatekeeper
        if any(w in text for w in ["stem", "stems", "exportar", "paquete", "manifiesto"]):
            stem_result = self.audit_and_prepare_stems(session, conn)
            return {
                "current_step": "AUDITORÍA Y EXPORTACIÓN DE STEMS COMPLETADA",
                "action_taken": stem_result["summary"],
                "question": stem_result["report_text"],
                "instructions_for_ai": stem_result["instructions_for_ai"],
                "phase": completed_phase,
                "ready_for_distribution": stem_result["ready_for_distribution"],
                "stems_export": stem_result
            }

        # 0. Master Gain Boost Gatekeeper (Limitador / Glue Makeup +2.5 a +3.5 dB)
        if any(w in text for w in ["impulsar ganancia", "ganancia de entrada", "ganancia del limitador", "subir limitador", "makeup gain", "glue compressor", "+2.5", "+3", "+3.5", "ganancia master"]):
            return handle_master_gain_boost(session, conn, text, tracks, completed_phase)

        # 0. Limpieza Quirúrgica de Resonancias en Medios Bajos (Mud Box)
        if any(w in text for w in ["limpieza de resonancia", "limpiar resonancia", "resonancias en medios bajos", "medios bajos", "mud box", "441 hz", "441.4 hz", "limpiar medios"]):
            return handle_low_mid_resonance_clean(session, conn, tracks, completed_phase)

        # 0. Top & Tail Acoustic Guard
        if any(w in text for w in ["top and tail", "top & tail", "ruidos residuales", "compas 0", "segundo 0", "desvanecer reverb", "cola de reverb", "reverberacion a -inf", "fade out outro"]):
            return handle_top_and_tail_guard(session, conn, tracks, completed_phase)

        # 0. Track Freezing / Unfreezing in Live 12
        if any(w in text for w in ["congelar pista", "descongelar pista", "congelar track", "descongelar track", "freeze track", "unfreeze track", "congelar", "descongelar"]):
            return handle_track_freeze(conn, text, tracks, completed_phase)

        # 0. Organic Foley Bed, Textures & Resampling Injection
        if any(w in text for w in ["inyectar foley", "lecho de vinilo", "textura foley", "crear textura", "inyectar textura", "textura granular", "resamplear pista", "self-sampling"]):
            return handle_texture_and_foley_injection(session, conn, text, tracks, completed_phase)

        # 0.01 Vocal Production Co-Creation & Continuous Take / Room Echo / Mix Audit / Vocal Chops / Gain Staging
        if any(w in text for w in ["vocal", "voz", "voces", "cantar", "letra", "grabar voz", "toma continua", "toma larga", "eco", "habitacion", "cortar y alinear", "balance", "chop", "chops", "vocal chop", "vocal chops", "partir", "distribuir", "distribuyelo", "rebanar", "trocear", "grabe", "grabo", "grabar", "procesar", "audio", "corta", "cortalo", "chopp", "choppealo", "bajo", "muy bajo", "controlar", "ganancia", "volumen", "nivel", "avisar", "2 partes", "dos partes", "ambos en 2 partes", "opcion 1", "opcion 2", "opcion 3"]):
            return handle_vocal_pipeline(session, conn, text, user_input, completed_phase)

        # 0.02 / 0.03 Drop Multi-Verse Mutations A/B/C and Arrangement Stamping
        drop_res = handle_drop_mutator(session, conn, text, user_input, completed_phase)
        if drop_res is not None:
            return drop_res

        # 0.1 Navigation / Transport Jump to section, compás, or beat
        nav_res = handle_transport_navigation(session, conn, text, completed_phase)
        if nav_res is not None:
            return nav_res

        # Default fallback: session tweaks (learning, preferences, disarm, automation, tempo, volume)
        return handle_session_tweaks(session, conn, text, tracks, completed_phase)
