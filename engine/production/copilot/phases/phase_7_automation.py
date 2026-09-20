# engine/production/copilot/phases/phase_7_automation.py
"""
Phase 7: Dynamic track automations and transitions in arrangement timeline.
Supports express batch injection and interactive surgical clip-by-clip mode.
"""
import re
import logging
from typing import Dict, Any, List, Optional
from engine.production.copilot.phases.base import BasePhaseHandler
from engine.production.copilot.nlp_parser import _normalize_text
from engine.production.recipe_engine import ProductionRecipeEngine, ProductionRecipe
from engine.arrangement.automation.weaver import ArrangementAutomationWeaver
from engine.memory.user_learning import get_user_preferences

logger = logging.getLogger("Phase7Automation")


class Phase7AutomationHandler(BasePhaseHandler):
    """Handler for Phase 7: Dynamic Automations and Transitions."""

    def prompt(self, session: Any, **kwargs) -> Dict[str, Any]:
        return self._prompt_phase_7(session)

    def handle(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        return self._handle_phase_7(session, conn, user_input)

    def handle_surgical_step(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        return self._handle_surgical_automation_step(session, conn, user_input)

    def init_surgical_automation(self, session: Any, conn: Any, preselected_indices: Optional[List[int]] = None) -> Dict[str, Any]:
        return self._init_surgical_automation(session, conn, preselected_indices)

    def _prompt_phase_7(self, session: Any) -> Dict[str, Any]:
        # Check user preference for automation mode:
        pref_auto_mode = "prompt"
        try:
            prefs = get_user_preferences()
            pref_auto_mode = prefs.get("automation", {}).get("mode", "prompt")
        except Exception:
            pass

        if pref_auto_mode in ("clip_by_clip", "surgical"):
            return self._init_surgical_automation(session, conn=None)

        recipe = session._build_recipe_from_session()
        menu = ProductionRecipeEngine.get_section_automation_menu(recipe)
        cands = menu.get("available_automations", [])

        cand_lines = []
        for c in cands[:6]:
            cand_lines.append(f"  • **{c['track_name']}** ({c['parameter_name']}): {c['musical_purpose']}")
        cand_preview = "\n".join(cand_lines)

        # Punto 22: Anti-Climax Energy Guard
        sections = session.data.get("sections", [])
        anti_climax_warning = ""
        buildup_idx = -1
        drop_idx = -1
        for i, s in enumerate(sections):
            name_low = str(s.get("name", "")).lower()
            if "build" in name_low or "pre" in name_low:
                buildup_idx = i
            elif ("drop" in name_low or "climax" in name_low or "chorus" in name_low) and buildup_idx != -1 and drop_idx == -1:
                drop_idx = i

        tracks = session.data.get("tracks", [])
        if buildup_idx != -1 and drop_idx != -1:
            bu_sec = sections[buildup_idx]
            drop_sec = sections[drop_idx]
            has_drums_in_drop = any(t.get("role") == "DRUMS" for t in tracks)
            has_bass_in_drop = any("BASS" in str(t.get("role", "")) for t in tracks)
            if not (has_drums_in_drop and has_bass_in_drop) or len(tracks) < 3:
                anti_climax_warning = (
                    f"\n\n⚠️ **ALERTA DE ANTI-CLÍMAX DETECTADA (Punto 22):**\n"
                    f"La sección '{drop_sec.get('name')}' corre riesgo de sonar más débil o vacía que el '{bu_sec.get('name')}'.\n"
                    f"Se recomienda seleccionar **Opción C** para volver al Paso 6 (Composición) y reforzar los clips antes de continuar.\n"
                )

        return {
            "current_step": "PASO 7 DE 8: AUTOMATIZACIONES DINÁMICAS DE PISTAS Y TRANSICIONES",
            "action_taken": f"Clips modulares desplegados en Arrangement. Se identificaron {len(cands)} curvas de transición y movimiento.",
            "question": (
                "🎚️ **Paso 7 de 8: Automatizaciones Dinámicas de Pistas y Transiciones en Arrangement**\n\n"
                f"El motor calculó **{len(cands)} curvas de automatización vectorial** en las transiciones de compás:\n"
                f"{cand_preview}\n\n"
                "**Rangos y Funciones de Automatización Calculados:**\n"
                "• `FILTER_SWEEP_UP`: Apertura de filtro de `200 Hz -> 18,000 Hz` en build-ups (crecimiento progresivo de energía espectral).\n"
                "• `REVERB_WASHOUT`: Rango de mezcla `0% -> 75% -> 0%` en pre-drop (difuminación espacial con corte súbito en el downbeat).\n"
                "• `PRE_DROP_VACUUM`: Rango de ganancia `0 dB -> -inf dB` en los últimos 2 beats previos al drop (corte absoluto de señal para máximo impacto).\n"
                "• `OUTRO_FADE`: Rango `0 dB -> -inf dB` sobre los últimos compases del arreglo.\n\n"
                f"{anti_climax_warning}"
                "\n⚡ **Técnicas de Transición de la Enciclopedia:**\n"
                "  • `pre_drop_vacuum`: Silencio absoluto 2 beats antes del drop para impacto sísmico.\n"
                "  • `snare_roll`: Aceleración rítmica (1/4 -> 1/8 -> 1/16 -> 1/32) con pitch bend ascendente.\n"
                "  • `white_noise_riser`: Riser de ruido blanco con apertura progresiva de filtro HP y reverb.\n\n"
                "🧠 **Decisión Técnica Requerida:**\n"
                "Decide cómo deseas estructurar e inyectar estas curvas de automatización en Arrangement:\n\n"
                "• **Opción A (Modo Express / Paquete Completo)**: Inyectar todo el lote de automatizaciones calculadas de una sola vez.\n"
                "• **Opción B (Modo Quirúrgico Clip por Clip)**: Seleccionar qué elementos automatizar y definir interactivamente los puntos (2, 3, 4 o N) clip por clip.\n"
                "• **Opción C (Regresar a Composición / Punto 22)**: Volver a Paso 6 (Composición) para reajustar clips y capas antes de continuar.\n"
                "• **Opción D (Omitir / Bypass)**: Continuar directamente en seco hacia la mezcla y masterización.\n\n"
                "*Responde con 'Opción A' para inyectar en lote, 'Opción B' para quirúrgico por clip, 'Opción C' para regresar a composición, o 'Opción D' para omitir.*"
            ),
            "instructions_for_ai": "Decide si inyectar en lote (Opción A), quirúrgico por clip (Opción B), regresar (Opción C), u omitir (Opción D).",
            "phase": "PHASE_7_AUTOMATION",
            "automation_candidates_count": len(cands)
        }

    def _init_surgical_automation(self, session: Any, conn: Any, preselected_indices: Optional[List[int]] = None) -> Dict[str, Any]:
        """Initializes the surgical clip-by-clip automation wizard."""
        recipe = session._build_recipe_from_session()
        menu = ProductionRecipeEngine.get_section_automation_menu(recipe)
        cands = menu.get("available_automations", [])

        if not cands:
            session.data["automations"] = []
            session.data["current_phase"] = "PHASE_8_VOCAL_DUCKING"
            session.data["phase_index"] = 8
            session._save_state()
            return session._prompt_phase_8_vocal_ducking([])

        valid_indices = []
        if preselected_indices:
            for idx in preselected_indices:
                if 0 <= idx < len(cands) and idx not in valid_indices:
                    valid_indices.append(idx)

        if valid_indices:
            session.data["automation_session"] = {
                "active": True,
                "mode": "SURGICAL",
                "stage": "POINT_CONFIG",
                "candidates": cands,
                "selected_indices": valid_indices,
                "current_index": 0,
                "applied_automations": []
            }
            session._save_state()
            first_cand = cands[valid_indices[0]]
            return self._prompt_clip_automation_point_step(session, first_cand, 1, len(valid_indices))

        session.data["automation_session"] = {
            "active": True,
            "mode": "SURGICAL",
            "stage": "SELECTION",
            "candidates": cands,
            "selected_indices": [],
            "current_index": 0,
            "applied_automations": []
        }
        session._save_state()
        return self._prompt_automation_selection(session, cands)

    def _prompt_automation_selection(self, session: Any, cands: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Displays the full catalog of available arrangement automations for producer selection."""
        cand_items = []
        for idx, c in enumerate(cands):
            t_name = c.get("track_name", "Track")
            param = c.get("parameter_name", "Param")
            s_from = c.get("section_from", "")
            s_to = c.get("section_to", "")
            start = c.get("start_bar", 0)
            dur = c.get("duration_bars", 0)
            purpose = c.get("musical_purpose", "")
            cand_items.append(
                f"{idx + 1}. **[{t_name}]** `{param}` | {s_from} ➔ {s_to} (Compás {start}, {dur} c.)\n"
                f"   • *Propósito:* {purpose}"
            )

        items_text = "\n".join(cand_items)

        return {
            "status": "AWAITING_AUTOMATION_SELECTION",
            "phase": "PHASE_7_AUTOMATION",
            "current_step": "PASO 7: SELECCIÓN DE ELEMENTOS PARA AUTOMATIZACIÓN QUIRÚRGICA",
            "action_taken": f"Catálogo de {len(cands)} curvas generado en Arrangement. Esperando selección de elementos.",
            "question": (
                f"🎚️ **Paso 7 de 8: Automatizaciones Quirúrgicas — Selección de Elementos**\n\n"
                f"El motor detectó **{len(cands)} curvas de automatización disponibles** en el arreglo:\n\n"
                f"{items_text}\n\n"
                "🧠 **Decisión Técnica Requerida:**\n"
                "Indica cuáles de estos elementos deseas automatizar:\n"
                "• **Números seleccionados**: Escribe los números separados por comas (ejemplo: `1, 3` o `1, 2, 4`).\n"
                "• **Todas**: Escribe `todas` para configurar cada una de las curvas clip por clip.\n"
                "• **Modo Express**: Escribe `express` para inyectar todas las curvas en lote de 1 solo clic.\n"
                "• **Omitir**: Escribe `bypass` para avanzar en seco sin automatizaciones.\n"
                "• **Regresar**: Escribe `regresar` para volver al Paso 6 (Composición).\n\n"
                "*Responde con los números de elementos que deseas (ej. '1, 2') o 'todas'.*"
            ),
            "instructions_for_ai": "Indica los números de los elementos que deseas automatizar (ej. '1, 3'), 'todas' para todas clip por clip, o 'express' para inyección directa.",
            "candidates_count": len(cands)
        }

    def _prompt_clip_automation_point_step(self, session: Any, cand: Dict[str, Any], step_num: int, total_steps: int) -> Dict[str, Any]:
        """Prompts producer for the number of automation points for a specific clip/section."""
        t_name = cand.get("track_name", "Track")
        t_idx = cand.get("track_index", 0)
        param = cand.get("parameter_name", "Param")
        s_from = cand.get("section_from", "")
        s_to = cand.get("section_to", "")
        start_bar = cand.get("start_bar", 0)
        dur_bars = cand.get("duration_bars", 0)
        curve_type = cand.get("type", "AUTOMATION")
        musical_purpose = cand.get("musical_purpose", "")

        return {
            "status": "AWAITING_CLIP_POINTS",
            "phase": "PHASE_7_AUTOMATION",
            "current_step": f"PASO 7: CONFIGURACIÓN DE PUNTOS ({step_num}/{total_steps}) — {t_name}",
            "action_taken": f"Configurando curva de '{param}' para '{t_name}' ({s_from} ➔ {s_to}).",
            "question": (
                f"🎚️ **Paso 7: Configuración de Curva por Clip ({step_num}/{total_steps})**\n\n"
                f"• **Pista:** Pista {t_idx}: **{t_name}**\n"
                f"• **Parámetro:** `{param}`\n"
                f"• **Transición:** `{s_from}` ➔ `{s_to}`\n"
                f"• **Ubicación en Arrangement:** Compás {start_bar} (duración: {dur_bars} compases / {dur_bars * 4.0} beats)\n"
                f"• **Tipo de Envolvente:** `{curve_type}`\n"
                f"• **Propósito Musical:** {musical_purpose}\n\n"
                "🧠 **¿Cuántos puntos de automatización deseas para este clip?**\n"
                "• **2 puntos** (Rampa Lineal / Directa): Interpolación continua inicio ➔ fin (ej. apertura básica de filtro).\n"
                "• **3 puntos** (Campana / Pico / Pre-Drop): Inicio ➔ Pico de tensión / lavado ➔ Resolución o corte seco en downbeat.\n"
                "• **4 puntos** (Escalón / Meseta / Modulación): Inicio ➔ Subida rápida ➔ Sostenimiento en meseta ➔ Retorno.\n"
                "• **Personalizado (N puntos)**: Especifica cualquier número de puntos (ej. `5`, `8`, `16`, `32` para micro-puntos Bézier ultra-suaves).\n"
                "• **Opciones de navegación**: Escribe `saltar` para omitir este clip, `express` para inyectar este y todos los clips restantes automáticamente, o `regresar` para volver a la selección.\n\n"
                "*Responde con el número de puntos (ej. '2', '3', '4' o '8 puntos'), o 'saltar'.*"
            ),
            "instructions_for_ai": "Indica cuántos puntos deseas para este clip (2, 3, 4, o N puntos), o 'saltar'/'express'.",
            "track_index": t_idx,
            "parameter_name": param,
            "step_index": step_num,
            "total_steps": total_steps
        }

    @classmethod
    def generate_custom_points(cls, cand: Dict[str, Any], num_points: int) -> List[Dict[str, float]]:
        """Generates precisely calculated envelope breakpoints for Ableton Live based on user-requested point count."""
        num_points = max(2, int(num_points))
        start_bar = float(cand.get("start_bar", 0.0))
        dur_bars = float(cand.get("duration_bars", 4.0))
        start_beat = start_bar * 4.0
        dur_beats = dur_bars * 4.0
        end_beat = start_beat + dur_beats
        curve = str(cand.get("curve", "exponential"))
        auto_type = str(cand.get("type", "FILTER_SWEEP_UP")).upper()

        # Extract or default base values
        orig_points = cand.get("points", [])
        if orig_points and len(orig_points) >= 2:
            orig_s = float(orig_points[0].get("value", 0.20))
            orig_e = float(orig_points[-1].get("value", 0.92))
        else:
            if "DOWN" in auto_type:
                orig_s, orig_e = 0.88, 0.18
            elif "WASHOUT" in auto_type:
                orig_s, orig_e = 0.15, 0.75
            elif "CLEANUP" in auto_type or "VACUUM" in auto_type:
                orig_s, orig_e = 0.85, 0.0
            else:
                orig_s, orig_e = 0.20, 0.92

        # 1. Reverb Washout
        if "WASHOUT" in auto_type:
            peak_val = max(orig_s, orig_e)
            if num_points == 2:
                return [
                    {"time": round(start_beat, 3), "value": round(orig_s, 4)},
                    {"time": round(end_beat, 3), "value": round(peak_val, 4)}
                ]
            elif num_points == 3:
                return [
                    {"time": round(start_beat, 3), "value": round(orig_s, 4)},
                    {"time": round(max(start_beat, end_beat - 0.25), 3), "value": round(peak_val, 4)},
                    {"time": round(end_beat, 3), "value": 0.0}
                ]
            elif num_points == 4:
                return [
                    {"time": round(start_beat, 3), "value": round(orig_s, 4)},
                    {"time": round(start_beat + dur_beats * 0.5, 3), "value": round(orig_s + (peak_val - orig_s) * 0.4, 4)},
                    {"time": round(max(start_beat, end_beat - 0.25), 3), "value": round(peak_val, 4)},
                    {"time": round(end_beat, 3), "value": 0.0}
                ]
            else:
                pts = []
                ramp_steps = num_points - 1
                ramp_end_beat = max(start_beat, end_beat - 0.25)
                for i in range(ramp_steps):
                    t = i / float(ramp_steps - 1) if ramp_steps > 1 else 0.0
                    b_time = start_beat + t * (ramp_end_beat - start_beat)
                    v = ArrangementAutomationWeaver._interpolate(t, orig_s, peak_val, curve)
                    pts.append({"time": round(b_time, 3), "value": round(v, 4)})
                pts.append({"time": round(end_beat, 3), "value": 0.0})
                return pts

        # 2. Sub Cleanup / Vacuum
        if "CLEANUP" in auto_type or "VACUUM" in auto_type:
            cut_offset = min(2.0, dur_beats * 0.5)
            cut_time = max(start_beat, end_beat - cut_offset)
            if num_points == 2:
                return [
                    {"time": round(start_beat, 3), "value": round(orig_s, 4)},
                    {"time": round(cut_time, 3), "value": 0.0}
                ]
            elif num_points == 3:
                return [
                    {"time": round(start_beat, 3), "value": round(orig_s, 4)},
                    {"time": round(cut_time, 3), "value": round(orig_s, 4)},
                    {"time": round(min(end_beat, cut_time + 0.05), 3), "value": 0.0}
                ]
            else:
                return [
                    {"time": round(start_beat, 3), "value": round(orig_s, 4)},
                    {"time": round(cut_time, 3), "value": round(orig_s, 4)},
                    {"time": round(min(end_beat, cut_time + 0.05), 3), "value": 0.0},
                    {"time": round(end_beat, 3), "value": 0.0}
                ]

        # 3. Standard Filter Sweeps & Parametric Curves
        if num_points == 2:
            return [
                {"time": round(start_beat, 3), "value": round(orig_s, 4)},
                {"time": round(end_beat, 3), "value": round(orig_e, 4)}
            ]
        elif num_points == 3:
            mid_beat = start_beat + dur_beats * 0.5
            mid_val = ArrangementAutomationWeaver._interpolate(0.5, orig_s, orig_e, curve)
            return [
                {"time": round(start_beat, 3), "value": round(orig_s, 4)},
                {"time": round(mid_beat, 3), "value": round(mid_val, 4)},
                {"time": round(end_beat, 3), "value": round(orig_e, 4)}
            ]
        elif num_points == 4:
            t1 = start_beat + dur_beats * 0.33
            t2 = start_beat + dur_beats * 0.66
            v1 = ArrangementAutomationWeaver._interpolate(0.33, orig_s, orig_e, curve)
            v2 = ArrangementAutomationWeaver._interpolate(0.66, orig_s, orig_e, curve)
            return [
                {"time": round(start_beat, 3), "value": round(orig_s, 4)},
                {"time": round(t1, 3), "value": round(v1, 4)},
                {"time": round(t2, 3), "value": round(v2, 4)},
                {"time": round(end_beat, 3), "value": round(orig_e, 4)}
            ]
        else:
            pts = []
            for i in range(num_points):
                t = i / float(num_points - 1)
                b_time = start_beat + t * dur_beats
                v = ArrangementAutomationWeaver._interpolate(t, orig_s, orig_e, curve)
                pts.append({"time": round(b_time, 3), "value": round(v, 4)})
            return pts

    _generate_custom_points = generate_custom_points

    def _handle_surgical_automation_step(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        """Handles stepping through the surgical clip-by-clip automation workflow."""
        auto_session = session.data.get("automation_session", {})
        stage = auto_session.get("stage", "SELECTION")
        cands = auto_session.get("candidates", [])
        text = _normalize_text(user_input)

        # -----------------------------------------------------------------
        # ETAPA 1: SELECCIÓN DE ELEMENTOS
        # -----------------------------------------------------------------
        if stage == "SELECTION":
            # Reversal (Opción C / Regresar)
            if any(w in text for w in ["regresar", "volver", "revers", "paso 6", "opcion c", "boton c"]) or text in ["c", "3"]:
                session.data["automation_session"] = {"active": False}
                session.data["current_phase"] = "PHASE_6_COMPOSITION"
                session.data["phase_index"] = 6
                session._save_state()
                return session._prompt_phase_6()

            # Bypass (Opción D / Omitir)
            if any(w in text for w in ["bypass", "omitir", "opcion d", "boton d"]) or text in ["d", "4"]:
                session.data["automation_session"] = {"active": False}
                session.data["automations"] = []
                session.data["current_phase"] = "PHASE_8_VOCAL_DUCKING"
                session.data["phase_index"] = 8
                session._save_state()
                return session._prompt_phase_8_vocal_ducking([])

            # Express batch
            if any(w in text for w in ["express", "lote", "todo el tema", "opcion a"]) or text in ["a", "1"]:
                session.data["automation_session"] = {"active": False}
                applied_autos = []
                if conn is not None and hasattr(conn, "send_command"):
                    try:
                        apply_res = ProductionRecipeEngine.apply_section_automations(conn, cands)
                        applied_autos = cands if apply_res.get("status") in ("SUCCESS", "PARTIAL_SUCCESS") else apply_res.get("applied", cands)
                    except Exception as ex:
                        logger.warning(f"Error applying recipe automations: {ex}")
                        applied_autos = cands
                else:
                    applied_autos = cands

                # Execute Micro-Automations pass (delay throws, dynamic auto-pan, 808 bends)
                from engine.production.copilot.phases.phase_7.micro_automations import MicroAutomationsPass
                from engine.arrangement.energy_curve import EnergyCurveEngine
                try:
                    micro_res = MicroAutomationsPass.execute_micro_automation_pass(session, conn)
                    session.data["micro_automations"] = micro_res
                    session.data["energy_curve"] = [p.to_dict() for p in EnergyCurveEngine.build_song_energy_curve(session.data.get("sections", []))]
                except Exception as ex_micro:
                    logger.warning(f"Notice on micro-automations pass: {ex_micro}")

                session.data["automations"] = applied_autos
                session.data["current_phase"] = "PHASE_8_VOCAL_DUCKING"
                session.data["phase_index"] = 8
                session._save_state()
                return session._prompt_phase_8_vocal_ducking(applied_autos)

            # All candidates
            if any(w in text for w in ["todas", "todos", "all", "completo"]):
                selected = list(range(len(cands)))
                auto_session["stage"] = "POINT_CONFIG"
                auto_session["selected_indices"] = selected
                auto_session["current_index"] = 0
                session._save_state()
                first_cand = cands[selected[0]]
                return self._prompt_clip_automation_point_step(session, first_cand, 1, len(selected))

            # Selected candidate indices (e.g. "1, 3", "1 y 2", "1-3")
            num_matches = [int(x) for x in re.findall(r'\b\d+\b', text) if 0 < int(x) <= len(cands)]
            if num_matches:
                seen = set()
                selected = []
                for n in num_matches:
                    idx = n - 1
                    if idx not in seen and 0 <= idx < len(cands):
                        seen.add(idx)
                        selected.append(idx)

                auto_session["stage"] = "POINT_CONFIG"
                auto_session["selected_indices"] = selected
                auto_session["current_index"] = 0
                session._save_state()
                first_cand = cands[selected[0]]
                return self._prompt_clip_automation_point_step(session, first_cand, 1, len(selected))

            # If input not recognized, reprompt selection
            prompt = self._prompt_automation_selection(session, cands)
            prompt["action_taken"] = f"Selección '{user_input}' no reconocida. Indica los números (ej. '1, 3') o 'todas'."
            return prompt

        # -----------------------------------------------------------------
        # ETAPA 2: CONFIGURACIÓN DE PUNTOS POR CLIP
        # -----------------------------------------------------------------
        selected = auto_session.get("selected_indices", [])
        cur_idx = auto_session.get("current_index", 0)

        if cur_idx >= len(selected):
            applied_total = auto_session.get("applied_automations", [])
            session.data["automations"] = applied_total
            session.data["automation_session"] = {"active": False}
            session.data["current_phase"] = "PHASE_8_VOCAL_DUCKING"
            session.data["phase_index"] = 8
            session._save_state()
            return session._prompt_phase_8_vocal_ducking(applied_total)

        cur_cand = cands[selected[cur_idx]]

        # Return to selection
        if any(w in text for w in ["regresar", "volver", "revers", "seleccion"]):
            auto_session["stage"] = "SELECTION"
            session._save_state()
            return self._prompt_automation_selection(session, cands)

        # Bypass remaining
        if any(w in text for w in ["bypass", "omitir todo", "cancelar"]):
            applied_total = auto_session.get("applied_automations", [])
            session.data["automations"] = applied_total
            session.data["automation_session"] = {"active": False}
            session.data["current_phase"] = "PHASE_8_VOCAL_DUCKING"
            session.data["phase_index"] = 8
            session._save_state()
            return session._prompt_phase_8_vocal_ducking(applied_total)

        # Express remaining
        if any(w in text for w in ["express", "inyectar restantes", "todas restantes", "lote"]):
            remaining_cands = [cands[idx] for idx in selected[cur_idx:]]
            if conn is not None and hasattr(conn, "send_command"):
                try:
                    ProductionRecipeEngine.apply_section_automations(conn, remaining_cands)
                except Exception as ex:
                    logger.warning(f"Error applying remaining automations: {ex}")
            auto_session["applied_automations"].extend(remaining_cands)
            applied_total = auto_session.get("applied_automations", [])
            session.data["automations"] = applied_total
            session.data["automation_session"] = {"active": False}
            session.data["current_phase"] = "PHASE_8_VOCAL_DUCKING"
            session.data["phase_index"] = 8
            session._save_state()
            return session._prompt_phase_8_vocal_ducking(applied_total)

        # Skip this clip
        if any(w in text for w in ["saltar", "skip", "omitir este", "siguiente"]):
            cur_idx += 1
            auto_session["current_index"] = cur_idx
            session._save_state()
            if cur_idx >= len(selected):
                applied_total = auto_session.get("applied_automations", [])
                session.data["automations"] = applied_total
                session.data["automation_session"] = {"active": False}
                session.data["current_phase"] = "PHASE_8_VOCAL_DUCKING"
                session.data["phase_index"] = 8
                session._save_state()
                return session._prompt_phase_8_vocal_ducking(applied_total)
            next_cand = cands[selected[cur_idx]]
            prompt = self._prompt_clip_automation_point_step(session, next_cand, cur_idx + 1, len(selected))
            prompt["action_taken"] = f"Curva para '{cur_cand.get('track_name')}' omitida. Pasando al siguiente clip."
            return prompt

        # Determine points count
        num_points = 2
        word_to_num = {
            "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6,
            "siete": 7, "ocho": 8, "diez": 10, "dieciseis": 16, "treinta y dos": 32
        }
        for word, val in word_to_num.items():
            if word in text:
                num_points = val
                break
        else:
            digits = re.findall(r'\b\d+\b', text)
            if digits:
                num_points = int(digits[0])
            elif "campana" in text or "pico" in text or "wash" in text:
                num_points = 3
            elif "escalon" in text or "meseta" in text:
                num_points = 4
            else:
                num_points = 2

        num_points = max(2, min(8, num_points))

        # Generate custom points optimized in 2 to 8 key strategic points
        raw_custom_points = self.generate_custom_points(cur_cand, num_points=num_points)
        custom_points = ProductionRecipeEngine.optimize_points_for_clip(raw_custom_points, min_points=2, max_points=8)
        cand_to_inject = dict(cur_cand)
        cand_to_inject["points"] = custom_points

        # Inject physically into Live
        if conn is not None and hasattr(conn, "send_command"):
            try:
                ProductionRecipeEngine.apply_section_automations(conn, [cand_to_inject])
            except Exception as ex:
                logger.warning(f"Error applying surgical automation to Live: {ex}")

        auto_session["applied_automations"].append(cand_to_inject)
        cur_idx += 1
        auto_session["current_index"] = cur_idx
        session._save_state()

        if cur_idx >= len(selected):
            applied_total = auto_session.get("applied_automations", [])
            session.data["automations"] = applied_total
            session.data["automation_session"] = {"active": False}
            session.data["current_phase"] = "PHASE_8_VOCAL_DUCKING"
            session.data["phase_index"] = 8
            session._save_state()
            return session._prompt_phase_8_vocal_ducking(applied_total)

        next_cand = cands[selected[cur_idx]]
        prompt = self._prompt_clip_automation_point_step(session, next_cand, cur_idx + 1, len(selected))
        prompt["action_taken"] = (
            f"✅ Curva de '{cur_cand.get('parameter_name')}' inyectada exitosamente con {len(custom_points)} puntos "
            f"en Pista {cur_cand.get('track_index')} ({cur_cand.get('track_name')})."
        )
        return prompt

    def _handle_phase_7(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        text = _normalize_text(user_input)

        # 1. Punto 22: Allow backward step-reversal to Phase 6
        if any(w in text for w in ["opcion c", "boton c", "regresar", "volver", "revers", "ajustar clip"]) or text in ["c", "3"]:
            if "bypass" not in text and "omitir" not in text and "en seco" not in text:
                session.data["current_phase"] = "PHASE_6_COMPOSITION"
                session.data["phase_index"] = 6
                session._save_state()
                return session._prompt_phase_6()

        # 2. Bypass
        is_bypass = (
            "bypass" in text
            or "omitir" in text
            or "en seco" in text
            or "sin auto" in text
            or text in ["d", "4"]
            or "opcion d" in text
            or "boton d" in text
        )

        # 3. Surgical Mode
        is_surgical = (
            any(w in text for w in [
                "quirurgic", "por clip", "clip por clip", "paso a paso",
                "personaliz", "seleccionar", "selecciona", "detalle",
                "opcion b", "boton b", "opcion 2"
            ])
            and not is_bypass
        )

        # Direct candidate numbers (e.g. "1, 2" or "1 y 3" or "solo 1 y 4")
        if not any(w in text for w in ["opcion", "boton", "paso", "fase"]):
            num_matches = [int(x) for x in re.findall(r'\b\d+\b', text) if 0 < int(x) < 50]
            if num_matches:
                return self._init_surgical_automation(session, conn, preselected_indices=[n - 1 for n in num_matches])

        if is_surgical:
            return self._init_surgical_automation(session, conn)

        if is_bypass:
            session.data["automations"] = []
            session.data["current_phase"] = "PHASE_8_VOCAL_DUCKING"
            session.data["phase_index"] = 8
            session._save_state()
            return session._prompt_phase_8_vocal_ducking([])

        # 4. Option A / Express: Batch inject all calculated candidates
        recipe = session._build_recipe_from_session()
        menu = ProductionRecipeEngine.get_section_automation_menu(recipe)
        cands = menu.get("available_automations", [])
        applied_autos = []
        if conn is not None and hasattr(conn, "send_command"):
            try:
                apply_res = ProductionRecipeEngine.apply_section_automations(conn, cands)
                applied_autos = cands if apply_res.get("status") in ("SUCCESS", "PARTIAL_SUCCESS") else apply_res.get("applied", cands)
            except Exception as ex:
                logger.warning(f"Error applying recipe automations: {ex}")
                applied_autos = cands
        else:
            applied_autos = cands

        session.data["automations"] = applied_autos
        session.data["current_phase"] = "PHASE_8_VOCAL_DUCKING"
        session.data["phase_index"] = 8
        session._save_state()

        return session._prompt_phase_8_vocal_ducking(applied_autos)
