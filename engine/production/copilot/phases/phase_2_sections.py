# engine/production/copilot/phases/phase_2_sections.py
"""
Phase 2: Song structure, section locators, arrangement cues, and scale tuning.
"""
import re
import logging
from typing import Dict, Any, List, Optional
from engine.production.copilot.phases.base import BasePhaseHandler
from engine.production.copilot.nlp_parser import _normalize_text, parse_autotune_settings
from engine.arrangement.transport_manager import TransportManager

logger = logging.getLogger("Phase2Sections")

class Phase2SectionsHandler(BasePhaseHandler):
    def prompt(self, session: Any, **kwargs) -> Dict[str, Any]:
        tracks = kwargs.get('tracks') or session.data.get('tracks', [])
        return self._prompt_phase_2(session, tracks)

    def handle(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        return self._handle_phase_2(session, conn, user_input)

    def _prompt_phase_2(self, session: Any, tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        t_lines = []
        for t in tracks:
            recs = t.get("top_recommendations", [])
            rec_str = f" ➔ Plugins recomendados: {', '.join(recs)}" if recs else ""
            t_lines.append(f"• Pista {t.get('index')}: **{t['name']}** [{t['role']}]{rec_str}")
        t_summary = "\n".join(t_lines)
        return {
            "current_step": "PASO 2 DE 7: ESTRUCTURA FORMAL, MARCADORES Y TONALIDAD/ESCALA",
            "action_taken": f"Se crearon {len(tracks)} canales en Live y se seleccionaron los mejores plugins para cada rol.",
            "question": (
                f"📐 **Paso 2 de 7: Estructura Formal, Marcadores de Arrangement y Tonalidad/Escala**\n\n"
                f"**Canales y Plugins Recomendados en Live:**\n{t_summary}\n\n"
                f"**Rangos y Dinámica Estructural del Arreglo:**\n"
                f"• **Duración total estándar**: Rango de 64 a 128 compases (típicamente 2:00 a 4:00 minutos según el tempo en BPM).\n"
                f"• **Duración por sección**: 8 compases para secciones de transición y preparación (Intro, Buildup, Puente, Outro); 16 compases para desarrollo temático y liberación energética (Verso, Drop, Coro).\n"
                f"• **Arco de energía dinámico**: Es necesario alternar secciones de acumulación de tensión, liberación rítmica y valles de descanso armónico.\n\n"
                f"Estructuras canónicas configuradas:\n"
                f"• **Opción A (Formato Estándar - 96 Compases)**: Intro (8), Verso 1 (16), Buildup (8), Drop 1 (16), Puente (8), Drop 2 (16), Outro (8).\n"
                f"• **Opción B (Formato Compacto - 64 Compases)**: Intro (8), Verso (16), Coro/Drop (16), Puente (8), Coro Final (16).\n"
                f"• **Opción C (EDM / Club - 128 Compases)**: Intro (16), Build (8), Drop 1 (16), Breakdown (16), Build (8), Drop 2 (16), Outro (16).\n"
                f"• **Opción D (Hip-Hop / Boom-Bap - 88 Compases)**: Intro (4), Verse 1 (16), Hook 1 (8), Verse 2 (16), Hook 2 (8), Bridge (8), Hook 3 (8), Outro (4).\n\n"
                f"🎹 **Afinación Armónica (Escala y Tonalidad del Proyecto):**\n"
                f"El motor afinará automáticamente Ableton Live 12 (`song.root_note`, `song.scale_name`) y los plugins de afinación (Auto-Tune Artist/Pro).\n"
                f"• *Recomendaciones por género:* Dubstep/Bass Music: **Fa Menor (F Minor)** o **Re Menor (D Minor)**; Trap: **Do Menor (C Minor)**; Pop/House: **La Menor (A Minor)** / **Do Mayor (C Major)**.\n\n"
                f"🧠 **Decisión Técnica Requerida:**\n"
                f"Elige la estructura y la tonalidad deseada.\n\n"
                f"*Ejemplo de respuesta: 'Opción A en Fa Menor', 'Opción B, tonalidad Re Menor', o simplemente 'Opción A' (se usará Fa Menor por defecto para Dubstep/Trap).* "
            ),
            "instructions_for_ai": "Selecciona la estructura (Opción A, B, C o D) y la tonalidad/escala deseada (ej. 'Opción A en Fa Menor').",
            "phase": "PHASE_2_SECTIONS"
        }
    
    def _handle_phase_2(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        text = _normalize_text(user_input)
    
        # 1. Parse Key & Scale and synchronize session tuning immediately
        detected_key, detected_scale, _ = parse_autotune_settings(user_input)
        if not detected_key:
            km = re.search(r'\b([a-g][#b]?)\b', text)
            if km:
                detected_key = km.group(1).upper()
    
        final_key = detected_key or session.data.get("key") or "F"
        final_scale = detected_scale or session.data.get("scale") or "Minor"
        session.data["key"] = final_key
        session.data["scale"] = final_scale
    
        # Physical tuning sync in Live 12
        session._sync_session_tuning(conn, final_key, final_scale)
    
        parsed_custom = None
        if isinstance(user_input, dict) and "sections" in user_input:
            parsed_custom = user_input["sections"]
        elif isinstance(user_input, list):
            parsed_custom = user_input
        elif isinstance(user_input, str):
            try:
                js = json.loads(user_input)
                if isinstance(js, dict) and "sections" in js:
                    parsed_custom = js["sections"]
                elif isinstance(js, list):
                    parsed_custom = js
            except Exception:
                pass
    
        if parsed_custom and isinstance(parsed_custom, list):
            sections = []
            curr_bar = 0
            for s in parsed_custom:
                bars = int(s.get("bars", 8))
                sections.append({
                    "name": s.get("name", "Section"),
                    "bars": bars,
                    "start_bar": curr_bar
                })
                curr_bar += bars
            total_bars = curr_bar
        elif "drumstep" in text or "175" in text or "intro: 16" in text or "intro 16" in text:
            total_bars = 96
            sections = [
                {"name": "Intro", "bars": 16, "start_bar": 0},
                {"name": "Buildup 1", "bars": 8, "start_bar": 16},
                {"name": "Drop 1", "bars": 16, "start_bar": 24},
                {"name": "Breakdown", "bars": 16, "start_bar": 40},
                {"name": "Buildup 2", "bars": 8, "start_bar": 56},
                {"name": "Drop 2", "bars": 16, "start_bar": 64},
                {"name": "Outro", "bars": 16, "start_bar": 80}
            ]
        elif "opcion b" in text or "64" in text or "compact" in text:
            total_bars = 64
            sections = [
                {"name": "Intro", "bars": 8, "start_bar": 0},
                {"name": "Verse", "bars": 16, "start_bar": 8},
                {"name": "Chorus / Drop", "bars": 16, "start_bar": 24},
                {"name": "Bridge", "bars": 8, "start_bar": 40},
                {"name": "Final Chorus", "bars": 16, "start_bar": 48}
            ]
        elif "opcion c" in text or "128" in text or "club" in text or "edm" in text:
            total_bars = 128
            sections = [
                {"name": "Intro", "bars": 16, "start_bar": 0},
                {"name": "Verse 1", "bars": 16, "start_bar": 16},
                {"name": "Buildup", "bars": 8, "start_bar": 32},
                {"name": "Drop 1", "bars": 24, "start_bar": 40},
                {"name": "Puente (Breakdown)", "bars": 16, "start_bar": 64},
                {"name": "Buildup 2", "bars": 8, "start_bar": 80},
                {"name": "Drop 2 (Climax)", "bars": 24, "start_bar": 88},
                {"name": "Outro", "bars": 16, "start_bar": 112}
            ]
        elif "opcion d" in text or "88" in text or "boom" in text:
            total_bars = 88
            sections = [
                {"name": "Intro", "bars": 4, "start_bar": 0},
                {"name": "Verse 1", "bars": 16, "start_bar": 4},
                {"name": "Hook 1", "bars": 8, "start_bar": 20},
                {"name": "Verse 2", "bars": 16, "start_bar": 28},
                {"name": "Hook 2", "bars": 8, "start_bar": 44},
                {"name": "Puente (Bridge)", "bars": 8, "start_bar": 52},
                {"name": "Hook 3", "bars": 8, "start_bar": 60},
                {"name": "Outro", "bars": 4, "start_bar": 68}
            ]
        else:
            total_bars = 96
            sections = [
                {"name": "Intro", "bars": 8, "start_bar": 0},
                {"name": "Verse 1", "bars": 16, "start_bar": 8},
                {"name": "Buildup", "bars": 8, "start_bar": 24},
                {"name": "Drop 1", "bars": 16, "start_bar": 32},
                {"name": "Puente (Calma)", "bars": 8, "start_bar": 48},
                {"name": "Drop 2 (Climax)", "bars": 16, "start_bar": 56},
                {"name": "Outro", "bars": 8, "start_bar": 72}
            ]
    
        session.data["sections"] = sections
        session.data["total_bars"] = total_bars
    
        if conn is not None and hasattr(conn, "send_command"):
            try:
                TransportManager.sync_section_cue_points(conn, sections)
            except Exception as ex_cue:
                logger.debug(f"TransportManager cue sync notice: {ex_cue}")
    
        session.data["current_phase"] = "PHASE_3_INSTRUMENTS"
        session.data["phase_index"] = 3
        session.data["current_track_ptr"] = 0
        session._save_state()
    
        return session._prompt_current_track_instrument()
    
    # -------------------------------------------------------------------------
    # FASE 3: CARGA VERIFICADA DE INSTRUMENTOS (PISTA POR PISTA)
    # -------------------------------------------------------------------------
