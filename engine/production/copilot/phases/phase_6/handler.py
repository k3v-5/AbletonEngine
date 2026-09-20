# engine/production/copilot/phases/phase_6/handler.py
"""
Phase 6 Composition Handler:
Orchestrates multi-section harmonic, rhythmic, and melodic composition in arrangement timeline.
Coordinates parser, gatekeepers, arranger, and prompt builders.
"""
import os
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from engine.production.copilot.phases.base import BasePhaseHandler
from engine.production.copilot.nlp_parser import _normalize_text
from engine.music.modular_generator import resolve_genre_style
from engine.production.recipe_engine import ProductionRecipe
from engine.vocal.vocal_chain_processor import VocalChainProcessor
from .parser import Phase6Parser
from .gatekeepers import Phase6Gatekeepers
from .arranger import Phase6Arranger
from .prompts import Phase6Prompts
from .recipes import Phase6RecipeBuilder

logger = logging.getLogger("Phase6Composition")


class Phase6CompositionHandler(BasePhaseHandler):
    """Facade and orchestrator for Phase 6 composition workflows."""

    def __init__(self):
        super().__init__()
        self._last_custom_notes_map: Optional[Dict[Tuple[Any, Any], List[Dict[str, Any]]]] = None

    def prompt(self, session: Any, **kwargs) -> Dict[str, Any]:
        return self._prompt_phase_6(session)

    def handle(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        return self._handle_phase_6(session, conn, user_input)

    def enforce_pre_drop_vacuum(self, session: Any, conn: Any) -> None:
        Phase6Gatekeepers.enforce_pre_drop_vacuum(session, conn)

    def deploy_clip_with_governance_retry(
        self,
        session_or_conn: Any,
        conn: Any = None,
        t_idx: int = 0,
        s_idx: int = 0,
        s_beats: float = 32.0,
        s_notes_dicts: Optional[List[Dict[str, Any]]] = None,
        current_beat: float = 0.0,
        trk: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> bool:
        return Phase6Arranger.deploy_clip_with_governance_retry(
            session_or_conn=session_or_conn,
            conn=conn,
            t_idx=t_idx,
            s_idx=s_idx,
            s_beats=s_beats,
            s_notes_dicts=s_notes_dicts,
            current_beat=current_beat,
            trk=trk,
            **kwargs
        )

    _deploy_clip_with_governance_retry = deploy_clip_with_governance_retry

    def deploy_single_track_composition(
        self,
        session: Any,
        conn: Any,
        trk: Dict[str, Any],
        custom_notes_map: Dict[Tuple[Any, Any], List[Dict[str, Any]]],
        sections: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        return Phase6Arranger.deploy_single_track_composition(
            session=session,
            conn=conn,
            trk=trk,
            custom_notes_map=custom_notes_map,
            sections=sections,
            find_notes_fn=self.find_custom_notes_for_track_section
        )

    _deploy_single_track_composition = deploy_single_track_composition

    def prompt_by_track_step(self, session: Any, trk_idx: int) -> Dict[str, Any]:
        return Phase6Prompts.prompt_by_track_step(session, trk_idx)

    def prompt_by_clip_step(self, session: Any, trk_idx: int, sec_idx: int) -> Dict[str, Any]:
        return Phase6Prompts.prompt_by_clip_step(session, trk_idx, sec_idx)

    def _prompt_phase_6(self, session: Any) -> Dict[str, Any]:
        return Phase6Prompts.prompt_phase_6(
            session,
            prompt_by_clip_fn=self.prompt_by_clip_step,
            prompt_by_track_fn=self.prompt_by_track_step
        )

    def parse_ai_composition(
        self,
        session: Any,
        user_input: str
    ) -> Tuple[Dict[str, Any], Dict[Tuple[Any, Any], List[Dict[str, Any]]], bool]:
        return Phase6Parser.parse_ai_composition(session, user_input)

    def find_custom_notes_for_track_section(
        self,
        session: Any,
        custom_map: Dict[Tuple[Any, Any], List[Dict[str, Any]]],
        trk: Dict[str, Any],
        s_idx: int,
        s_name: str,
        s_beats: float
    ) -> Optional[List[Dict[str, Any]]]:
        return Phase6Parser.find_custom_notes_for_track_section(
            session=session,
            custom_map=custom_map,
            trk=trk,
            s_idx=s_idx,
            s_name=s_name,
            s_beats=s_beats
        )

    _find_custom_notes_for_track_section = find_custom_notes_for_track_section

    def build_recipe_from_session(self, session: Any) -> ProductionRecipe:
        return Phase6RecipeBuilder.build_recipe_from_session(session)

    def handle_modular_composition_step(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        """Handles stepping through modular composition (by section, by track, or combined)."""
        session_state = session.data.get("composition_session", {})
        mode = session_state.get("mode", "BY_SECTION")
        sections = session.data.get("sections", [])
        tracks = session.data.get("tracks", [])

        sec_idx = session_state.get("section_index", 0)
        trk_idx = session_state.get("track_index", 0)

        text_norm = _normalize_text(user_input)
        ai_meta, custom_notes_map, has_notes = self.parse_ai_composition(session, user_input)

        is_explicit_key_directive = bool(re.search(r'\bKEY\s+[A-G][#b]?\b', user_input, re.IGNORECASE))
        if is_explicit_key_directive or any(w in text_norm for w in ["key ", "tonalidad", "dorian", "bpm", "natural_minor", "phrygian"]):
            session.data["composition_session"] = {"active": False}
            return self._handle_phase_6(session, conn, user_input)

        if mode == "BY_SECTION":
            if has_notes and sec_idx < len(sections):
                for trk in tracks:
                    self.deploy_single_track_composition(session, conn, trk, custom_notes_map, [sections[sec_idx]])
                    if trk.get("deployment_failed"):
                        session.data["pending_instrument_swap_track"] = trk.get("index")
                        session._save_state()
                        return {
                            "status": "PHASE_6_INSTRUMENT_CHANGE_REQUIRED",
                            "phase": "PHASE_6_COMPOSITION",
                            "current_step": f"FASE 6: COMPOSICIÓN (INSTRUMENTO BLOQUEADO: '{trk.get('name')}')",
                            "action_taken": f"Error de gobernanza al desplegar clips en '{trk.get('name')}': {trk.get('deployment_error')}. Reintento de auto-esculpido fallido.",
                            "question": (
                                f"⚠️ **Error de Gobernanza en Pista '{trk.get('name')}' (Rol: `{trk.get('role')}`):**\n\n"
                                f"El instrumento `{trk.get('instrument')}` está en estado init sin esculpir (`INIT_SYNTH_DETECTED`) y el socket bloqueó la creación del clip.\n\n"
                                f"El motor prohíbe ignorar este fallo como un simple aviso.\n\n"
                                f"**Opciones:**\n"
                                f"1. 🔄 **Cambiar de Instrumento:** Escribe 'cambiar instrumento' o el nombre del preset para elegir otro de tu librería.\n"
                                f"2. 🎛️ **Esculpir Parámetros Manualmente:** Envía valores de macros (ej: 'Macro 1: 0.8, Macro 2: 0.6').\n"
                                f"3. 🔁 **Reintentar:** Envía 'reintentar' tras ajustar el instrumento en Live."
                            ),
                            "instructions_for_ai": "Pide al usuario seleccionar otro instrumento o envía parámetros de esculpido.",
                            "track_name": trk.get("name"),
                            "track_index": trk.get("index")
                        }
            sec_idx += 1
            session_state["section_index"] = sec_idx
            if sec_idx >= len(sections):
                session.data["composition_session"] = {"active": False}
                session.data["current_phase"] = "PHASE_7_AUTOMATION"
                session.data["phase_index"] = 7
                session._save_state()
                return session._prompt_phase_7()

            cur_sec = sections[sec_idx]
            session._save_state()
            return {
                "status": "MODULAR_COMPOSITION_STEP",
                "current_step": f"COMPOSICIÓN POR SECCIÓN ({sec_idx + 1}/{len(sections)}): {cur_sec.get('name')}",
                "action_taken": f"Sección {sec_idx} completada e inyectada en Live.",
                "question": f"🎼 **Componiendo Sección {sec_idx + 1} de {len(sections)}: '{cur_sec.get('name')}' ({cur_sec.get('bars')} compases):**\n\nDefine las notas MIDI (`pitch`, `start_time`, `duration`, `velocity`) para los instrumentos de esta sección.",
                "instructions_for_ai": f"Envía las notas explícitas para la sección {cur_sec.get('name')}. El motor no autocompleta notas.",
                "phase": "PHASE_6_COMPOSITION"
            }

        elif mode == "BY_TRACK":
            trk_idx = session_state.get("track_index", 0)
            is_stepping = any(w in text_norm for w in ["siguiente", "next", "skip", "continuar", "avanzar"])
            is_interactive = session_state.get("interactive", False)
            if is_interactive:
                cur_trk = tracks[trk_idx] if trk_idx < len(tracks) else {}
                if is_stepping and not has_notes:
                    return {
                        "status": "MODULAR_COMPOSITION_BLOCKED",
                        "phase": "PHASE_6_COMPOSITION",
                        "current_step": f"COMPOSICIÓN POR PISTA BLOQUEADA ({trk_idx + 1}/{len(tracks)}): {cur_trk.get('name')}",
                        "action_taken": "Bloqueo: Se requieren notas explícitas para esta pista en modo interactivo.",
                        "question": f"⚠️ **Composición Bloqueada para '{cur_trk.get('name')}':**\n\nEl modo interactivo requiere notas MIDI explícitas (`pitch`, `start_time`, `duration`, `velocity`) antes de continuar.",
                        "instructions_for_ai": f"Genera y envía notas MIDI explícitas en JSON para {cur_trk.get('name')}.",
                        "track_index": trk_idx
                    }

                if has_notes and trk_idx < len(tracks):
                    self.deploy_single_track_composition(session, conn, cur_trk, custom_notes_map)
                    cur_trk["notes_count"] = len(custom_notes_map) or sum(len(v) for v in custom_notes_map.values())
                    if cur_trk.get("deployment_failed"):
                        session.data["pending_instrument_swap_track"] = cur_trk.get("index")
                        session._save_state()
                        return {
                            "status": "PHASE_6_INSTRUMENT_CHANGE_REQUIRED",
                            "phase": "PHASE_6_COMPOSITION",
                            "current_step": f"FASE 6: COMPOSICIÓN (INSTRUMENTO BLOQUEADO: '{cur_trk.get('name')}')",
                            "action_taken": f"Error de gobernanza al desplegar clips en '{cur_trk.get('name')}': {cur_trk.get('deployment_error')}. Reintento de auto-esculpido fallido.",
                            "question": (
                                f"⚠️ **Error de Gobernanza en Pista '{cur_trk.get('name')}' (Rol: `{cur_trk.get('role')}`):**\n\n"
                                f"El instrumento `{cur_trk.get('instrument')}` está en estado init sin esculpir (`INIT_SYNTH_DETECTED`) y el socket bloqueó la creación del clip.\n\n"
                                f"El motor prohíbe ignorar este fallo como un simple aviso.\n\n"
                                f"**Opciones:**\n"
                                f"1. 🔄 **Cambiar de Instrumento:** Escribe 'cambiar instrumento' o el nombre del preset para elegir otro de tu librería.\n"
                                f"2. 🎛️ **Esculpir Parámetros Manualmente:** Envía valores de macros (ej: 'Macro 1: 0.8, Macro 2: 0.6').\n"
                                f"3. 🔁 **Reintentar:** Envía 'reintentar' tras ajustar el instrumento en Live."
                            ),
                            "instructions_for_ai": "Pide al usuario seleccionar otro instrumento o envía parámetros de esculpido.",
                            "track_name": cur_trk.get("name"),
                            "track_index": cur_trk.get("index")
                        }

                trk_idx += 1
                session_state["track_index"] = trk_idx
                session._save_state()

                if trk_idx < len(tracks):
                    return self.prompt_by_track_step(session, trk_idx)
                else:
                    self.enforce_pre_drop_vacuum(session, conn)
                    session.data["composition_session"] = {"active": False}
                    session.data["current_phase"] = "PHASE_7_AUTOMATION"
                    session.data["phase_index"] = 7
                    session._save_state()
                    return session._prompt_phase_7()

            if is_stepping or has_notes:
                if has_notes and trk_idx < len(tracks):
                    cur_trk = tracks[trk_idx]
                    self.deploy_single_track_composition(session, conn, cur_trk, custom_notes_map)
                    if cur_trk.get("deployment_failed"):
                        session.data["pending_instrument_swap_track"] = cur_trk.get("index")
                        session._save_state()
                        return {
                            "status": "PHASE_6_INSTRUMENT_CHANGE_REQUIRED",
                            "phase": "PHASE_6_COMPOSITION",
                            "current_step": f"FASE 6: COMPOSICIÓN (INSTRUMENTO BLOQUEADO: '{cur_trk.get('name')}')",
                            "action_taken": f"Error de gobernanza al desplegar clips en '{cur_trk.get('name')}': {cur_trk.get('deployment_error')}. Reintento de auto-esculpido fallido.",
                            "question": (
                                f"⚠️ **Error de Gobernanza en Pista '{cur_trk.get('name')}' (Rol: `{cur_trk.get('role')}`):**\n\n"
                                f"El instrumento `{cur_trk.get('instrument')}` está en estado init sin esculpir (`INIT_SYNTH_DETECTED`) y el socket bloqueó la creación del clip.\n\n"
                                f"El motor prohíbe ignorar este fallo como un simple aviso.\n\n"
                                f"**Opciones:**\n"
                                f"1. 🔄 **Cambiar de Instrumento:** Escribe 'cambiar instrumento' o el nombre del preset para elegir otro de tu librería.\n"
                                f"2. 🎛️ **Esculpir Parámetros Manualmente:** Envía valores de macros (ej: 'Macro 1: 0.8, Macro 2: 0.6').\n"
                                f"3. 🔁 **Reintentar:** Envía 'reintentar' tras ajustar el instrumento en Live."
                            ),
                            "instructions_for_ai": "Pide al usuario seleccionar otro instrumento o envía parámetros de esculpido.",
                            "track_name": cur_trk.get("name"),
                            "track_index": cur_trk.get("index")
                        }
                trk_idx += 1
                session_state["track_index"] = trk_idx
                if trk_idx >= len(tracks):
                    session.data["composition_session"] = {"active": False}
                    session.data["current_phase"] = "PHASE_7_AUTOMATION"
                    session.data["phase_index"] = 7
                    session._save_state()
                    return session._prompt_phase_7()

                next_trk = tracks[trk_idx]
                session._save_state()
                return {
                    "status": "MODULAR_COMPOSITION_STEP",
                    "current_step": f"COMPOSICIÓN POR PISTA ({trk_idx + 1}/{len(tracks)}): {next_trk.get('name')}",
                    "action_taken": f"Pista {trk_idx} completada.",
                    "question": f"🎼 **Componiendo Pista {trk_idx + 1} de {len(tracks)}: '{next_trk.get('name')}' (Rol: `{next_trk.get('role')}`):**\n\nDefine las notas MIDI (`pitch`, `start_time`, `duration`, `velocity`) para esta pista.",
                    "instructions_for_ai": f"Envía las notas explícitas para {next_trk.get('name')}.",
                    "phase": "PHASE_6_COMPOSITION"
                }

            # All tracks completed
            unpopulated = []
            for t in tracks:
                r = str(t.get("role", "")).upper()
                is_aud = bool(t.get("is_audio", False) or r == "VOCALS" or t.get("live_recording_mode", False))
                if not is_aud and t.get("notes_count", 0) == 0:
                    unpopulated.append(t["name"])

            if unpopulated:
                return {
                    "status": "PHASE_6_GATEKEEPER_BLOCKED",
                    "phase": "PHASE_6_COMPOSITION",
                    "current_step": "FASE 6: COMPOSICIÓN (BLOQUEADA POR GATEKEEPER)",
                    "action_taken": f"Gatekeeper de Completitud activado: {len(unpopulated)} pista(s) sin notas ({', '.join(unpopulated)}).",
                    "question": f"⚠️ Las siguientes pistas de instrumento carecen de notas MIDI: **{', '.join(unpopulated)}**.\nPor favor provee las notas MIDI para continuar.",
                    "instructions_for_ai": "Genera y envía las notas explícitas para las pistas vacías.",
                    "unpopulated_tracks": unpopulated
                }

            self.enforce_pre_drop_vacuum(session, conn)
            session.data["composition_session"] = {"active": False}
            session.data["current_phase"] = "PHASE_7_AUTOMATION"
            session.data["phase_index"] = 7
            session._save_state()
            return session._prompt_phase_7()

        elif mode in ("BY_CLIP", "COMBINED"):
            trk_idx = session_state.get("track_index", 0)
            sec_idx = session_state.get("section_index", 0)
            if trk_idx >= len(tracks):
                session.data["composition_session"] = {"active": False}
                session.data["current_phase"] = "PHASE_7_AUTOMATION"
                session.data["phase_index"] = 7
                session._save_state()
                return session._prompt_phase_7()

            cur_trk = tracks[trk_idx]
            cur_sec = sections[sec_idx] if sec_idx < len(sections) else sections[0]
            cur_trk_is_aud = bool(cur_trk.get("is_audio", False) or str(cur_trk.get("role", "")).upper() == "VOCALS" or cur_trk.get("live_recording_mode", False))

            if cur_trk_is_aud:
                trk_idx += 1
                sec_idx = 0
                session_state["track_index"] = trk_idx
                session_state["section_index"] = sec_idx
                session._save_state()
                if trk_idx < len(tracks):
                    return self.prompt_by_clip_step(session, trk_idx, sec_idx)
                else:
                    self.enforce_pre_drop_vacuum(session, conn)
                    session.data["composition_session"] = {"active": False}
                    session.data["current_phase"] = "PHASE_7_AUTOMATION"
                    session.data["phase_index"] = 7
                    session._save_state()
                    return session._prompt_phase_7()

            s_bars = int(cur_sec.get("bars", 8))
            s_beats = float(s_bars * 4.0)
            is_silence = any(w in text_norm for w in ["silencio", "silence", "mutear", "mute", "vacio", "vacío"]) or user_input.strip() in ("[]", "{}")

            clip_notes = []
            if not is_silence:
                for k, v in custom_notes_map.items():
                    if v:
                        clip_notes = list(v)
                        break
                if not clip_notes and not has_notes and not is_silence:
                    return {
                        "status": "AWAITING_CLIP_NOTES",
                        "phase": "PHASE_6_COMPOSITION",
                        "current_step": f"NOTAS REQUERIDAS: '{cur_trk.get('name')}' EN '{cur_sec.get('name')}'",
                        "action_taken": "Bloqueo: Notas requeridas para este clip.",
                        "question": f"⚠️ Por favor envía las notas MIDI explícitas para el clip de '{cur_trk.get('name')}' en '{cur_sec.get('name')}' ({s_bars} compases), o indica 'Silencio'.",
                        "instructions_for_ai": "Envía el JSON con las notas del clip o escribe 'Silencio'."
                    }

            t_idx = session._resolve_live_track_index(conn, cur_trk)
            current_beat = sum(float(sections[i].get("bars", 8)) * 4.0 for i in range(sec_idx))

            if clip_notes:
                max_reach = max(n.get("start_time", 0.0) + n.get("duration", 1.0) for n in clip_notes)
                if 0 < max_reach < s_beats and max_reach <= 16.0:
                    pattern_len = 16.0
                    tiled = []
                    offset = 0.0
                    while offset < s_beats:
                        for n in clip_notes:
                            n_st = n.get("start_time", 0.0) + offset
                            if n_st < s_beats:
                                n_c = dict(n)
                                n_c["start_time"] = round(n_st, 4)
                                n_c["duration"] = round(min(n.get("duration", 1.0), s_beats - n_st), 4)
                                tiled.append(n_c)
                        offset += pattern_len
                    clip_notes = tiled

            role_upper = str(cur_trk.get("role", "")).upper()
            if role_upper == "DRUMS" and clip_notes:
                q3_notes = [d for d in clip_notes if 60 <= d.get("pitch", 0) <= 75]
                q1_notes = [d for d in clip_notes if 36 <= d.get("pitch", 0) <= 51]
                q2_notes = [d for d in clip_notes if 52 <= d.get("pitch", 0) <= 59]
                if len(q3_notes) == len(clip_notes) and len(q1_notes) == 0 and len(q2_notes) == 0:
                    for d in clip_notes:
                        d["pitch"] = max(36, d["pitch"] - 24)

            if conn and hasattr(conn, "send_command"):
                try:
                    self.deploy_clip_with_governance_retry(
                        session_or_conn=session,
                        conn=conn,
                        t_idx=t_idx,
                        s_idx=sec_idx,
                        s_beats=s_beats,
                        s_notes_dicts=clip_notes,
                        current_beat=current_beat,
                        trk=cur_trk
                    )
                    cur_trk["notes_count"] = cur_trk.get("notes_count", 0) + len(clip_notes)
                except Exception as ex_clip:
                    cur_trk["deployment_failed"] = True
                    cur_trk["deployment_error"] = str(ex_clip)
                    logger.error(f"Clip deployment failed on track {t_idx} section {sec_idx}: {ex_clip}")
                    session.data["pending_instrument_swap_track"] = cur_trk.get("index")
                    session._save_state()
                    return {
                        "status": "PHASE_6_INSTRUMENT_CHANGE_REQUIRED",
                        "phase": "PHASE_6_COMPOSITION",
                        "current_step": f"FASE 6: COMPOSICIÓN (INSTRUMENTO BLOQUEADO: '{cur_trk.get('name')}')",
                        "action_taken": f"Error de gobernanza en '{cur_trk.get('name')}': {ex_clip}. Reintento de auto-esculpido fallido.",
                        "question": (
                            f"⚠️ **Error de Gobernanza en Pista '{cur_trk.get('name')}' (Rol: `{cur_trk.get('role')}`):**\n\n"
                            f"El instrumento `{cur_trk.get('instrument')}` está en estado init sin esculpir (`INIT_SYNTH_DETECTED`) y el socket bloqueó la creación del clip.\n\n"
                            f"El motor prohíbe ignorar este fallo como un simple aviso.\n\n"
                            f"**Opciones:**\n"
                            f"1. 🔄 **Cambiar de Instrumento:** Escribe 'cambiar instrumento' o el nombre del preset para elegir otro de tu librería.\n"
                            f"2. 🎛️ **Esculpir Parámetros Manualmente:** Envía valores de macros (ej: 'Macro 1: 0.8, Macro 2: 0.6').\n"
                            f"3. 🔁 **Reintentar:** Envía 'reintentar' tras ajustar el instrumento en Live."
                        ),
                        "instructions_for_ai": "Pide al usuario seleccionar otro instrumento o envía parámetros de esculpido.",
                        "track_name": cur_trk.get("name"),
                        "track_index": t_idx
                    }
            else:
                cur_trk["notes_count"] = cur_trk.get("notes_count", 0) + len(clip_notes)

            sec_idx += 1
            if sec_idx >= len(sections):
                sec_idx = 0
                trk_idx += 1

            session_state["track_index"] = trk_idx
            session_state["section_index"] = sec_idx
            session._save_state()

            if trk_idx < len(tracks):
                return self.prompt_by_clip_step(session, trk_idx, sec_idx)

            self.enforce_pre_drop_vacuum(session, conn)
            session.data["composition_session"] = {"active": False}
            session.data["current_phase"] = "PHASE_7_AUTOMATION"
            session.data["phase_index"] = 7
            session._save_state()
            return session._prompt_phase_7()

        session.data["current_phase"] = "PHASE_7_AUTOMATION"
        session.data["phase_index"] = 7
        session._save_state()
        return session._prompt_phase_7()

    def _handle_phase_6(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        text_norm = _normalize_text(user_input)

        if any(w in text_norm for w in ["por seccion", "seccion por seccion"]) or ("opcion 1" in text_norm and "seccion" in text_norm):
            mode = "BY_SECTION"
        elif any(w in text_norm for w in ["por pista", "pista por pista"]) or ("opcion 2" in text_norm and "pista" in text_norm):
            mode = "BY_TRACK"
        elif any(w in text_norm for w in ["combinado", "seccion y pista", "opcion 3"]):
            mode = "COMBINED"
        elif any(w in text_norm for w in ["por clip", "clip por clip", "clip", "de 16 en 16", "de 8 en 8", "16 en 16", "8 en 8", "opcion 1"]):
            mode = "BY_CLIP"
        elif "opcion 2" in text_norm:
            mode = "BY_TRACK"
        else:
            mode = None

        if mode is not None and not any(w in text_norm for w in ["tonalidad", "bpm", "menor", "mayor", "opcion 4"]):
            session.data["composition_session"] = {
                "active": True,
                "mode": mode,
                "section_index": 0,
                "track_index": 0
            }
            session._save_state()
            sections = session.data.get("sections", [])
            tracks = session.data.get("tracks", [])
            first_sec = sections[0] if sections else {"name": "Intro", "bars": 8}
            first_trk = tracks[0] if tracks else {"name": "Drums", "role": "DRUMS"}
            step_desc = f"Sección 1/{len(sections)}: '{first_sec.get('name')}'" if mode == "BY_SECTION" else (f"Pista 1/{len(tracks)}: '{first_trk.get('name')}'" if mode == "BY_TRACK" else f"Pista '{first_trk.get('name')}' en '{first_sec.get('name')}'")
            return {
                "status": "MODULAR_COMPOSITION_INITIALIZED",
                "mode": mode,
                "current_step": f"COMPOSICIÓN MODULAR INICIADA: {step_desc}",
                "action_taken": f"Modo de composición '{mode}' activado. Esperando notas del primer bloque.",
                "question": f"🎼 **Composición Modular Activada ({step_desc}):**\n\nDefine las notas MIDI (`pitch`, `start_time`, `duration`, `velocity`) para este bloque.",
                "instructions_for_ai": f"Envía las notas MIDI explícitas para {step_desc}.",
                "phase": "PHASE_6_COMPOSITION"
            }

        u_clean = _normalize_text(user_input)

        is_swap_trigger = any(w in u_clean for w in [
            "cambiar instrumento", "cambiar sonido", "cambio de instrumento", "cambio de sonido",
            "reemplazar instrumento", "reemplazar sonido", "otro instrumento", "swap instrument",
            "modificar instrumento", "nuevo instrumento", "cambiar preset"
        ])
        if is_swap_trigger:
            failed_t_idx = session.data.get("pending_instrument_swap_track")
            if failed_t_idx is not None:
                tracks = session.data.get("tracks", [])
                target_t = next((t for t in tracks if t.get("index") == failed_t_idx), None)
                if target_t:
                    session.data["instrument_swap_state"] = {
                        "active": True,
                        "stage": "SELECT_PRESET",
                        "track_index": target_t.get("index"),
                        "track_name": target_t.get("name"),
                        "track_role": target_t.get("role"),
                        "origin_phase": "PHASE_6_COMPOSITION"
                    }
                    session._save_state()
                    return self._prompt_instrument_swap_preset(target_t)
            return self._initiate_instrument_swap_flow(conn, user_input)

        is_retry = any(w in u_clean for w in ["reintentar", "intentar de nuevo", "reintenta", "retry"])
        cached_notes_map = getattr(self, "_last_custom_notes_map", None)
        if is_retry and cached_notes_map:
            tracks = session.data.get("tracks", [])
            for t in tracks:
                t["deployment_failed"] = False
                t["deployment_error"] = None
            sections = session.data.get("sections", [])
            composed_summary = []
            for trk in tracks:
                total_notes_trk = self.deploy_single_track_composition(session, conn, trk, cached_notes_map, sections)
                composed_summary.append(f"{trk['name']} ({total_notes_trk} notas en {len(sections)} secciones)")

            failed_governance_tracks = [t for t in tracks if t.get("deployment_failed")]
            if failed_governance_tracks:
                first_failed = failed_governance_tracks[0]
                session.data["pending_instrument_swap_track"] = first_failed.get("index")
                session._save_state()
                return {
                    "status": "PHASE_6_INSTRUMENT_CHANGE_REQUIRED",
                    "phase": "PHASE_6_COMPOSITION",
                    "current_step": "FASE 6: COMPOSICIÓN (INSTRUMENTO BLOQUEADO POR GOBERNANZA)",
                    "action_taken": f"Reintento fallido en {len(failed_governance_tracks)} pista(s). El instrumento '{first_failed.get('instrument')}' continúa rechazado por gobernanza ({first_failed.get('deployment_error')}).",
                    "question": (
                        f"⚠️ **Error Persistente de Gobernanza en Pista '{first_failed.get('name')}':**\n\n"
                        f"El instrumento `{first_failed.get('instrument')}` sigue sin estar esculpido (`INIT_SYNTH_DETECTED`).\n\n"
                        f"Por favor escribe 'cambiar instrumento' para elegir otro instrumento o provee parámetros manuales para esculpirlo."
                    ),
                    "instructions_for_ai": "Pide al usuario seleccionar otro instrumento o envía parámetros de esculpido.",
                    "failed_tracks": [t["name"] for t in failed_governance_tracks],
                    "target_track": first_failed.get("index")
                }
            session.data["pending_instrument_swap_track"] = None
            self.enforce_pre_drop_vacuum(session, conn)
            session.data["current_phase"] = "PHASE_7_AUTOMATION"
            session.data["phase_index"] = 7
            session._save_state()
            return session._prompt_phase_7()

        ai_meta, custom_notes_map, has_custom_notes = self.parse_ai_composition(session, user_input)
        if has_custom_notes:
            self._last_custom_notes_map = custom_notes_map

        is_explicit_key_directive = bool(re.search(r'\bKEY\s+[A-G][#b]?\b', user_input, re.IGNORECASE))

        # Gatekeeper 1: Explicit composition required
        blk = Phase6Gatekeepers.check_explicit_composition_required(
            session=session,
            user_input=user_input,
            has_custom_notes=has_custom_notes,
            is_explicit_key_directive=is_explicit_key_directive
        )
        if blk:
            return blk

        text = user_input.upper()

        key = ai_meta.get("key")
        if not key:
            key = "F"
            for k_candidate in ["C#", "DB", "D#", "EB", "F#", "GB", "G#", "AB", "A#", "BB", "C", "D", "E", "F", "G", "A", "B"]:
                if f" {k_candidate} " in f" {text} " or f"KEY {k_candidate}" in text or f"TONALIDAD {k_candidate}" in text:
                    key = k_candidate.title()
                    break

        scale = ai_meta.get("scale")
        if not scale:
            scale = "natural_minor"
            if "ROYAL" in text or "JPOP" in text or "J-POP" in text or "ROYAL_ROAD" in text:
                scale = "royal_road"
            elif "DORIAN" in text or "DORICA" in text:
                scale = "dorian"
            elif "ARMONICA" in text or "HARMONIC" in text:
                scale = "harmonic_minor"
            elif "MAYOR" in text or "MAJOR" in text:
                scale = "major"
            elif "CLASSIC_DARK" in text or "OSCURA" in text or "CLASSIC DARK" in text:
                scale = "classic_dark"
            elif "JAZZ_HIPHOP" in text or "JAZZ HIPHOP" in text or "JAZZ" in text:
                scale = "jazz_hiphop"
            elif "SOUL_FEEL" in text or "SOUL FEEL" in text or "SOUL" in text:
                scale = "soul_feel"
            elif "MELANCHOLIC" in text or "MELANCOLICA" in text:
                scale = "melancholic"
            elif "MINIMAL_JAZZ" in text or "MINIMAL" in text:
                scale = "minimal_jazz"
            elif "PHRYGIAN" in text or "FRIGIA" in text:
                scale = "phrygian_dark"
            elif "NEO_SOUL" in text or "NEOSOUL" in text:
                scale = "neo_soul"

        bpm = 120.0
        if "bpm" in ai_meta:
            try:
                bpm = float(ai_meta["bpm"])
            except (ValueError, TypeError):
                bpm = 120.0
        else:
            bpm_match = re.search(r"(\d{2,3}(?:\.\d+)?)\s*BPM", user_input, re.IGNORECASE)
            if bpm_match:
                bpm = float(bpm_match.group(1))

        detected_genre = ai_meta.get("genre")
        if not detected_genre:
            for g_candidate in ["trap", "house", "neo_soul", "reggaeton", "synthwave", "boom_bap", "techno", "cumbia", "afrobeat", "edm", "drum_and_bass", "pop", "rock", "lofi", "hip_hop", "hip hop", "dnb"]:
                if g_candidate.upper() in text:
                    detected_genre = g_candidate.replace(" ", "_").replace("hip_hop", "trap").replace("lofi", "boom_bap").replace("dnb", "drum_and_bass")
                    break
        if detected_genre:
            session.data["genre"] = detected_genre
        elif "genre" not in session.data:
            session.data["genre"] = resolve_genre_style(None, bpm=bpm).value

        session.data["key"] = key
        session.data["scale"] = scale
        session.data["bpm"] = bpm
        session.data["ai_composed"] = bool(has_custom_notes)

        if conn is not None and hasattr(conn, "send_command"):
            try:
                conn.send_command("set_tempo", {"tempo": bpm})
            except Exception:
                pass
            try:
                k_upper = str(key).upper()
                s_upper = "MINOR" if any(w in str(scale).upper() for w in ["MINOR", "MENOR", "DORIAN", "PHRYGIAN", "DARK", "MELANCHOLIC", "SOUL"]) else ("CHROMATIC" if "CHROM" in str(scale).upper() else "MAJOR")
                k_val = VocalChainProcessor.AUTOTUNE_KEY_VALUES.get(k_upper, 0.48)
                s_val = VocalChainProcessor.AUTOTUNE_SCALE_VALUES.get(s_upper, 0.05)
                sync_at_code = f"""
for trk in song.tracks:
    for d in trk.devices:
        d_name = d.name.lower()
        if 'auto-tune' in d_name or 'autotune' in d_name:
            for p in d.parameters:
                p_l = p.name.lower()
                if 'key' in p_l:
                    p.value = {k_val}
                elif 'scale' in p_l:
                    p.value = {s_val}
"""
                conn.send_command("execute_code", {"code": sync_at_code})
            except Exception as ex_sync:
                logger.debug(f"Notice auto-tuning sync in Phase 6: {ex_sync}")

        tracks = session.data.get("tracks", [])
        sections = session.data.get("sections", [])
        if not sections:
            sections = [
                {"name": "Intro", "bars": 8, "start_bar": 0},
                {"name": "Verse 1", "bars": 16, "start_bar": 8},
                {"name": "Buildup", "bars": 8, "start_bar": 24},
                {"name": "Drop 1", "bars": 16, "start_bar": 32},
                {"name": "Puente (Calma)", "bars": 8, "start_bar": 48},
                {"name": "Drop 2 (Climax)", "bars": 16, "start_bar": 56},
                {"name": "Outro", "bars": 8, "start_bar": 72}
            ]

        composed_summary = []
        for trk in tracks:
            total_notes_trk = self.deploy_single_track_composition(session, conn, trk, custom_notes_map, sections)
            composed_summary.append(f"{trk['name']} ({total_notes_trk} notas en {len(sections)} secciones)")

        failed_governance_tracks = [t for t in tracks if t.get("deployment_failed")]
        if failed_governance_tracks:
            first_failed = failed_governance_tracks[0]
            session.data["pending_instrument_swap_track"] = first_failed.get("index")
            session._save_state()
            failed_desc = ", ".join([f"'{t['name']}' ({t.get('instrument', 'Sin instrumento')})" for t in failed_governance_tracks])
            return {
                "status": "PHASE_6_INSTRUMENT_CHANGE_REQUIRED",
                "phase": "PHASE_6_COMPOSITION",
                "current_step": "FASE 6: COMPOSICIÓN (INSTRUMENTO BLOQUEADO POR GOBERNANZA)",
                "action_taken": f"Bloqueo de gobernanza: {len(failed_governance_tracks)} pista(s) no pudieron recibir clips ({failed_desc}). Se intentó auto-esculpido pero el instrumento falló.",
                "question": (
                    f"⚠️ **Error Crítico de Gobernanza en Pista '{first_failed.get('name')}' (Rol: `{first_failed.get('role')}`):**\n\n"
                    f"El instrumento `{first_failed.get('instrument')}` fue bloqueado por el gatekeeper (`INIT_SYNTH_DETECTED`) y el reintento automático no pudo resolverlo.\n"
                    f"Detalle: `{first_failed.get('deployment_error')}`.\n\n"
                    f"El motor prohíbe avanzar con pistas vacías o silenciar errores como advertencias.\n\n"
                    f"**Acciones Disponibles:**\n"
                    f"1. 🔄 **Cambiar de Instrumento:** Escribe 'cambiar instrumento' o 'cargar [preset]' para seleccionar un generador de sonido compatible de la librería.\n"
                    f"2. 🎛️ **Esculpir Parámetros:** Provee valores de macros o síntesis para esculpir este sintetizador (ej: 'Macro 1: 0.8, Macro 2: 0.6').\n"
                    f"3. 🔁 **Reintentar:** Envía 'reintentar' tras inicializar o ajustar el instrumento manualmente en Live."
                ),
                "instructions_for_ai": "Pide al usuario seleccionar un nuevo instrumento o envía parámetros de esculpido explícitos.",
                "failed_tracks": [t["name"] for t in failed_governance_tracks],
                "target_track": first_failed.get("index")
            }

        # Gatekeeper 2: Pre-Drop Vacuum
        self.enforce_pre_drop_vacuum(session, conn)

        # Gatekeeper 3: Completeness (zero unpopulated MIDI tracks)
        blk_unpop = Phase6Gatekeepers.check_unpopulated_midi_tracks(
            session=session,
            tracks=tracks,
            is_explicit_key_directive=is_explicit_key_directive
        )
        if blk_unpop:
            return blk_unpop

        # Gatekeeper 4: Synthesizer Outro Non-Silencing Law
        blk_outro = Phase6Gatekeepers.check_silenced_synths_in_outro(
            session=session,
            tracks=tracks,
            sections=sections,
            has_custom_notes=has_custom_notes,
            custom_notes_map=custom_notes_map,
            parser_fn=self.find_custom_notes_for_track_section
        )
        if blk_outro:
            return blk_outro

        session.data["current_phase"] = "PHASE_7_AUTOMATION"
        session.data["phase_index"] = 7
        session.data["composed_summary"] = composed_summary
        session._save_state()

        return session._prompt_phase_7()
