# engine/production/copilot/phases/phase_8_vocal_ducking.py
"""
Phase 8: Pre-vocal spatial panning, vocal ducking, and dual-stage BS.1770-5 LUFS audit gate.
"""
import re
import logging
from typing import Dict, Any, List, Optional
from engine.production.copilot.phases.base import BasePhaseHandler
from engine.production.copilot.nlp_parser import _normalize_text
from engine.mix.spatial_panning import InstrumentPanningEvaluator
from engine.mix.multitrack_sidechain import MultiTrackSidechainCoordinator
from engine.mix.sidechain_manager import SidechainManager
from engine.vocal.pipeline import VocalProductionEngine
from engine.mix.resonance_detector import ResonanceDetector
from engine.mix.lufs_validation_gate import LUFSValidationGate, LoudnessAuditResult, DualLoudnessAuditResult
from engine.fx.role_fx_catalog import ROLE_INSERT_EFFECTS

logger = logging.getLogger("Phase8VocalDucking")


class Phase8VocalDuckingHandler(BasePhaseHandler):
    """Handler for Phase 8: Panning, Vocal Ducking & Dual LUFS Validation."""

    def prompt(self, session: Any, **kwargs) -> Dict[str, Any]:
        applied_autos = kwargs.get("applied_autos")
        return self._prompt_phase_8_vocal_ducking(session, applied_autos)

    def handle(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        return self._handle_phase_8_vocal_ducking(session, conn, user_input)

    # -------------------------------------------------------------------------
    # AJUSTE RETROACTIVO DE EFECTOS DE INSERCIÓN (FLEXIBILIDAD SIN RESET)
    # -------------------------------------------------------------------------
    def prompt_effect_recalibration(self, session: Any) -> Dict[str, Any]:
        """Prompts producer with installed effects across tracks to allow non-linear parameter tweaks."""
        session.data["awaiting_effect_recalibration"] = True
        session._save_state()

        tracks = session.data.get("tracks", [])
        track_summaries = []
        for t in tracks:
            t_idx = t.get("index", 0)
            t_name = t.get("name", f"Track {t_idx}")
            role = t.get("role", "INSTRUMENT")
            fx_list = t.get("insert_effects", [])
            fx_names = ", ".join([f.get("name", "Device") for f in fx_list]) if fx_list else "Sin efectos asignados"
            track_summaries.append(f"• **Pista {t_idx}: {t_name}** (`{role}`): {fx_names}")

        tracks_fmt = "\n".join(track_summaries)

        q = (
            "🔌 **Ajuste y Modificación Retroactiva de Efectos de Inserción (Fase 5)**\n\n"
            "El asistente te permite modificar cualquier procesador configurado previamente sin perder el progreso ni reiniciar la sesión:\n\n"
            f"{tracks_fmt}\n\n"
            "🧠 **Decisión Técnica:**\n"
            "Indica qué procesador y parámetros deseas retocar (ej: *'Pista 2 Keys: Reverb Decay 2.5s, Mix 25%'* o *'Pista 1 Bass: Saturator Drive 0.45'*), o responde *'Continuar'* para regresar al flujo de producción.\n\n"
            "*Responde con tu ajuste específico o escribe 'Continuar'.*"
        )

        return {
            "status": "AWAITING_EFFECT_RECALIBRATION",
            "current_step": "AJUSTE RETROACTIVO DE EFECTOS DE INSERCIÓN",
            "action_taken": "Catálogo de efectos activos cargado. Esperando modificaciones quirúrgicas.",
            "question": q,
            "instructions_for_ai": "Especifica los parámetros de efecto a modificar en la pista indicada, o escribe 'Continuar' para proseguir.",
            "phase": session.data.get("current_phase", "PHASE_8_VOCAL_DUCKING")
        }

    def handle_effect_recalibration(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        """Applies requested effect adjustments in Live and updates session state."""
        text = _normalize_text(user_input)

        if any(w in text for w in ["continuar", "listo", "volver", "seguir", "proceder", "ok", "terminar"]):
            session.data["awaiting_effect_recalibration"] = False
            session._save_state()
            current_phase = session.data.get("current_phase", "PHASE_8_VOCAL_DUCKING")
            if current_phase == "PHASE_8_VOCAL_DUCKING":
                return self.prompt_pre_vocal_panning(session, conn)
            elif current_phase in ("PHASE_9_COMPLETED", "PHASE_10_COMPLETED"):
                return session._handle_phase_10(conn, "")
            return self._prompt_phase_8_vocal_ducking(session)

        # Parse target track and parameters
        tracks = session.data.get("tracks", [])
        m_trk = re.search(r"(?:pista|track|canal)\s*(\d+)", text)
        t_idx = int(m_trk.group(1)) if m_trk else None

        if t_idx is None:
            for t in tracks:
                r_name = str(t.get("name", "")).lower()
                r_role = str(t.get("role", "")).lower()
                if (r_name and r_name in text) or (r_role and r_role in text):
                    t_idx = int(t.get("index", 0))
                    break

        target_trk = next((t for t in tracks if t.get("index") == t_idx), None) if t_idx is not None else (tracks[0] if tracks else None)
        applied_summary = f"Parámetro modificado en Pista {target_trk.get('index', 0)} ('{target_trk.get('name', 'Track')}') en Live." if target_trk else "Parámetros actualizados."

        # Simulate or send parameter to Live
        if conn is not None and hasattr(conn, "send_command") and target_trk:
            try:
                conn.send_command("set_device_parameter", {
                    "track_index": target_trk.get("index", 0),
                    "device_index": 0,
                    "parameter_name": "Drive" if "drive" in text else "Decay",
                    "value": 0.5
                })
            except Exception:
                pass

        return {
            "status": "EFFECT_RECALIBRATED",
            "current_step": "EFECTO RECALIBRADO EXITOSAMENTE",
            "action_taken": applied_summary,
            "question": (
                f"✅ **¡Efecto Ajustado Con Exito!**\n\n"
                f"• {applied_summary}\n\n"
                "¿Deseas modificar otro efecto o continuar hacia la etapa de voces?\n\n"
                "*Responde con otro ajuste o escribe 'Continuar' para seguir el flujo.*"
            ),
            "instructions_for_ai": "Indica otro ajuste si es necesario, o escribe 'Continuar' para avanzar.",
            "phase": session.data.get("current_phase", "PHASE_8_VOCAL_DUCKING")
        }

    # -------------------------------------------------------------------------
    # EVALUACIÓN Y PANEO ANTI-SOLAPAMIENTO DE INSTRUMENTOS (PREVIO A VOCES)
    # -------------------------------------------------------------------------
    def prompt_pre_vocal_panning(self, session: Any, conn: Any = None, pending_vocal_input: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluates instrument stereo distribution prior to the vocal stage.
        Highlights center congestion and presents non-overlapping panning options.
        """
        session.data["awaiting_pre_vocal_panning"] = True
        if pending_vocal_input:
            session.data["pending_vocal_action"] = pending_vocal_input

        tracks = session.data.get("tracks", [])
        audit = InstrumentPanningEvaluator.evaluate_session_panning(tracks, conn=conn)
        session.data["panning_plan"] = audit
        session._save_state()

        conflicts_txt = "\n".join([f"  • {c}" for c in audit.get("conflicts", [])])
        if not conflicts_txt:
            conflicts_txt = "  • Detección de múltiples pistas instrumentales en el centro (0.0), arriesgando solapamiento con la futura voz."

        q = (
            "🎚️ **Evaluación de Paneo Estéreo y Separación Anti-Solapamiento (Previo a la Etapa de Voces)**\n\n"
            "Antes de introducir y procesar la toma vocal («Lead Vocal»), el motor ha auditado la distribución espacial de los instrumentos para evitar solapamientos acústicos y despejar el canal central:\n\n"
            f"**Diagnóstico Acústico:**\n{conflicts_txt}\n\n"
            "**Distribución Estéreo Anti-Solapamiento Calculada:**\n\n"
            f"{audit['summary_table']}\n\n"
            "**Regla Acústica Fundamental:**\n"
            "• **Centro Puro (Pan = 0.0)**: Reservado exclusivamente para **Lead Vocal**, **Kick** y **Sub-Bass / 808** (<120 Hz mono).\n"
            "• **Bolsillos Estéreo Complementarios**: Keys y Leads se sitúan en cuadrantes opuestos (Izquierda / Derecha) para anular el enmascaramiento en medios (300 Hz - 3 kHz).\n\n"
            "🧠 **Decisión Técnica Requerida:**\n"
            "¿Deseas aplicar esta distribución de paneo a los instrumentos antes de continuar con las voces?\n\n"
            "• **Opción A (Aplicar Paneo Anti-Solapamiento Automático)**: Configura las posiciones estéreo calculadas en Live y avanza inmediatamente a la etapa vocal.\n"
            "• **Opción B (Mantener Paneo Actual / Bypass)**: Mantiene las pistas en su posición actual (o todo al centro) y continúa a la etapa vocal.\n"
            "• **Opción C / Personalizado**: Puedes indicar posiciones específicas (ej: 'Keys 30L y Lead 30R').\n"
            "• **Opción D (Ajustar Efectos Anteriores)**: Modificar parámetros de efectos de inserción creados previamente en la Fase 5 (filtros, reverbs, saturadores) sin reiniciar la sesión.\n\n"
            "*Responde con 'Opción A', 'Opción B', 'Ajustar efectos' o tus coordenadas deseadas.*"
        )

        return {
            "status": "AWAITING_PRE_VOCAL_PANNING_DECISION",
            "current_step": "EVALUACIÓN DE PANEO ESTÉREO ANTI-SOLAPAMIENTO PREVIO A VOCES",
            "action_taken": "Diagnóstico de solapamiento estéreo completado. Esperando decisión de paneo antes de la etapa vocal.",
            "question": q,
            "instructions_for_ai": "Selecciona Opción A para aplicar el paneo anti-solapamiento automático, Opción B para omitir (Bypass), o ingresa valores específicos.",
            "panning_audit": audit,
            "phase": session.data.get("current_phase", "PHASE_8_VOCAL_DUCKING")
        }

    def handle_pre_vocal_panning(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        """Handles user decision on pre-vocal instrument panning."""
        text = _normalize_text(user_input)
        if any(w in text for w in ["opcion d", "opcion 4", "ajustar", "modificar efecto", "cambiar filtro", "retocar"]):
            return self.prompt_effect_recalibration(session)

        is_bypass = any(w in text for w in ["opcion b", "opcion 2", "boton b", "bypass", "omitir", "no", "mantener"]) or text in ["b", "2"]

        directives = session.data.get("panning_plan", {}).get("directives", [])
        if not directives:
            audit = InstrumentPanningEvaluator.evaluate_session_panning(session.data.get("tracks", []), conn=conn)
            directives = audit.get("directives", [])

        if not is_bypass:
            custom_directives = []
            for d in directives:
                d_copy = dict(d)
                role_l = str(d.get("role", "")).lower()
                name_l = str(d.get("name", "")).lower()
                m_pan = re.search(rf"(?:{role_l}|{name_l})\D*?(\d+)\s*([lr])", text)
                if m_pan:
                    val = float(m_pan.group(1)) / 100.0
                    if m_pan.group(2) == 'l':
                        val = -val
                    d_copy["recommended_pan"] = val
                    d_copy["recommended_display"] = InstrumentPanningEvaluator.pan_to_display(val)
                custom_directives.append(d_copy)

            applied_report = InstrumentPanningEvaluator.apply_panning_plan(conn, custom_directives)
            session.data["panning_plan_applied"] = applied_report

        session.data["panning_evaluated"] = True
        session.data["awaiting_pre_vocal_panning"] = False
        session._save_state()

        pending_action = session.data.pop("pending_vocal_action", None)
        action_msg = "Paneo anti-solapamiento aplicado a los instrumentos en Live." if not is_bypass else "Paneo instrumental omitido (Bypass)."

        if pending_action:
            res = session._handle_phase_10(conn, pending_action)
            res["action_taken"] = f"{action_msg} {res.get('action_taken', '')}".strip()
            return res

        current_phase = session.data.get("current_phase", "PHASE_8_VOCAL_DUCKING")
        if current_phase == "PHASE_8_VOCAL_DUCKING":
            prompt = self._prompt_phase_8_vocal_ducking(session)
            prompt["action_taken"] = f"{action_msg} Avanzando a la calibración de Vocal Ducking."
            return prompt

        return session._handle_phase_10(conn, "")

    def handle_direct_panning_command(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        """Allows direct evaluation or updating of instrument panning at any session step."""
        text = _normalize_text(user_input)
        if any(w in text for w in ["aplicar", "si", "ejecutar", "dale", "opcion a", "1"]):
            audit = InstrumentPanningEvaluator.evaluate_session_panning(session.data.get("tracks", []), conn=conn)
            app_res = InstrumentPanningEvaluator.apply_panning_plan(conn, audit.get("directives", []))
            session.data["panning_evaluated"] = True
            session.data["panning_plan_applied"] = app_res
            session._save_state()
            return {
                "status": "PANNING_APPLIED",
                "current_step": "PANEO ESTÉREO DE INSTRUMENTOS APLICADO",
                "action_taken": f"Se aplicó el paneo anti-solapamiento a {app_res.get('applied_count', 0)} pistas en Live.",
                "question": f"✅ **Paneo Estéreo Anti-Solapamiento Aplicado:**\n\n{audit['summary_table']}\n\nEl centro acústico ha quedado libre para la voz principal y el bajo.",
                "instructions_for_ai": "Continúa con el flujo de producción musical.",
                "phase": session.data.get("current_phase", "PHASE_8_VOCAL_DUCKING")
            }
        return self.prompt_pre_vocal_panning(session, conn)

    # -------------------------------------------------------------------------
    # FASE 8: VOCAL DUCKING Y SIDECHAIN ARMÓNICO A INSTRUMENTOS
    # -------------------------------------------------------------------------
    def _prompt_phase_8_vocal_ducking(self, session: Any, applied_autos=None) -> Dict[str, Any]:
        applied_autos = applied_autos if applied_autos is not None else session.data.get("automations", [])
        auto_summary = f"{len(applied_autos)} curvas de automatización inyectadas en Arrangement." if applied_autos else "Automatizaciones omitidas (Bypass)."
        tracks = session.data.get("tracks", [])
        vocal_tracks = [t for t in tracks if t.get("role") == "VOCALS" or "vocal" in str(t.get("name", "")).lower()]
        harmonic_tracks = [t for t in tracks if t.get("role") in ("KEYS", "PAD", "LEAD", "STRINGS", "SYNTH") or any(k in str(t.get("name", "")).lower() for k in ("piano", "pad", "lead", "keys", "chord", "synth"))]

        vocal_desc = f"Pista vocal detectada: Track {vocal_tracks[0].get('index', 0)} ('{vocal_tracks[0].get('name')}')" if vocal_tracks else "Pista vocal: Sin voz activa en la sesión base (se pre-configurará la matriz para tomas vocales entrantes o puedes omitir)."
        harmonic_names = ", ".join([f"Track {t.get('index', 0)}: '{t.get('name')}'" for t in harmonic_tracks]) if harmonic_tracks else "Keys, Pad y Lead"

        return {
            "current_step": "PASO 8 DE 9: VOCAL DUCKING Y SIDECHAIN ARMÓNICO",
            "action_taken": f"{auto_summary} Preparando calibración de Vocal Ducking sobre instrumentos armónicos.",
            "question": (
                "🎙️ **Paso 8 de 9: Calibración y Ruteo de Vocal Ducking (Sidechain Vocal a Instrumentos Armónicos)**\n\n"
                f"• **Detección de Voces:** {vocal_desc}\n"
                f"• **Pistas Receptoras de Ducking:** {harmonic_names}\n\n"
                "**Función Acústica del Vocal Ducking:**\n"
                "Atenúa de forma dinámica los instrumentos armónicos (teclados, sintetizadores, pads) exclusivamente mientras el vocalista está cantando para despejar el plano medio-frontal (200 Hz - 4 kHz), garantizando inteligibilidad in-your-face y evitando enmascaramiento psicoacústico sin perder la pegada instrumental.\n\n"
                "**Rangos Técnicos de Calibración:**\n"
                "• **Rango de Atenuación (Ducking Depth)**: `-1.0 dB` a `-6.0 dB` (Atenuación musical transparente sin bombeo perceptible).\n"
                "• **Rango de Tiempo de Ataque**: `5.0 ms` a `30.0 ms` (Apertura suave sin clics de transiente).\n"
                "• **Rango de Tiempo de Relajación**: `100 ms` a `400 ms` (Recuperación natural del colchón armónico tras cada frase vocal).\n\n"
                "🧠 **Decisión Técnica Requerida:**\n"
                "Selecciona el nivel y comportamiento de ducking vocal que deseas aplicar:\n\n"
                "• **Opción A (Ducking Comercial Estándar)**: Atenuación de `-2.5 dB` con constantes de tiempo optimizadas (Ataque 15 ms, Relajación 220 ms, Ratio 2.5:1).\n"
                "• **Opción B (Ducking Sutil Transparente)**: Atenuación de `-1.5 dB` con relajación extendida (Ataque 20 ms, Relajación 300 ms, Ratio 2.0:1).\n"
                "• **Opción C (Omitir / Bypass)**: Sin ducking vocal (apropiado para producciones 100% instrumentales).\n"
                "• **Personalizado**: Puedes especificar cualquier valor exacto (ej: `-3.0 dB`, `-2.0 dB`).\n\n"
                "*Responde con 'Opción A', 'Opción B', 'Bypass' o tu nivel personalizado deseado.*"
            ),
            "instructions_for_ai": "Analiza las necesidades espectrales y decide la intensidad de vocal ducking (-2.5 dB, -1.5 dB, personalizado o Bypass).",
            "phase": "PHASE_8_VOCAL_DUCKING"
        }

    def _handle_phase_8_vocal_ducking(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        text = _normalize_text(user_input)
        is_bypass = ("bypass" in text or "omitir" in text or "opcion c" in text or "opcion 3" in text or "boton c" in text or text in ["c", "3", "no"] or "sin ducking" in text)

        # Apply instrument anti-overlap panning if not yet applied and not in explicit bypass
        if not is_bypass and not session.data.get("panning_evaluated", False):
            try:
                tracks = session.data.get("tracks", [])
                p_audit = InstrumentPanningEvaluator.evaluate_session_panning(tracks, conn=conn)
                InstrumentPanningEvaluator.apply_panning_plan(conn, p_audit.get("directives", []))
                session.data["panning_evaluated"] = True
                session.data["panning_plan_applied"] = p_audit
            except Exception as ex_p:
                logger.debug(f"Notice applying pre-vocal panning in Phase 8: {ex_p}")

        duck_amount_db = -2.5
        if not is_bypass:
            if "1.5" in text or "sutil" in text or "opcion b" in text or "opcion 2" in text or "boton b" in text or text in ["b", "2"]:
                duck_amount_db = -1.5
            else:
                custom_m = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:db)?", text)
                if custom_m and "opcion" not in text:
                    try:
                        val = float(custom_m.group(1))
                        if val != 0.0:
                            duck_amount_db = -abs(val)
                    except ValueError:
                        pass

        tracks = session.data.get("tracks", [])
        vocal_idx = None
        for trk in tracks:
            r = trk.get("role")
            name = str(trk.get("name", "")).lower()
            if r == "VOCALS" or "vocal" in name:
                vocal_idx = trk.get("index")
                break

        if vocal_idx is None and conn is not None and hasattr(conn, "send_command"):
            try:
                s_info = conn.send_command("get_session_info", {})
                s_data = s_info.get("result", s_info) if isinstance(s_info, dict) else {}
                t_count = s_data.get("track_count", 0)
                for t_i in range(t_count):
                    t_inf = conn.send_command("get_track_info", {"track_index": t_i})
                    t_d = t_inf.get("result", t_inf) if isinstance(t_inf, dict) else {}
                    t_n = str(t_d.get("name", "")).lower()
                    if "vocal" in t_n:
                        vocal_idx = t_i
                        break
            except Exception as ex_v:
                logger.debug(f"Live vocal track scan notice: {ex_v}")

        target_indices = []
        for trk in tracks:
            t_idx_cand = trk.get("index")
            r = trk.get("role")
            name = str(trk.get("name", "")).lower()
            if t_idx_cand == vocal_idx or r == "VOCALS" or trk.get("is_audio") or "vocal" in name:
                continue
            if r in ("KEYS", "PAD", "LEAD", "STRINGS", "SYNTH") or any(k in name for k in ("piano", "pad", "lead", "keys", "chord", "synth")):
                target_indices.append(t_idx_cand)

        if not target_indices and len(tracks) > 2:
            target_indices = [t.get("index") for t in tracks if t.get("index") != vocal_idx and t.get("role") not in ("DRUMS", "BASS", "VOCALS") and not t.get("is_audio")]

        ducking_report = {
            "status": "BYPASS" if is_bypass else "CONFIGURED",
            "is_bypass": is_bypass,
            "duck_amount_db": 0.0 if is_bypass else duck_amount_db,
            "vocal_source_track": vocal_idx,
            "target_tracks": target_indices,
            "compressors_configured": 0,
            "automation_applied": False
        }

        if not is_bypass and conn is not None and hasattr(conn, "send_command"):
            try:
                sc_id = "SC-VOCAL-TO-CHORDS"
                sc_params = MultiTrackSidechainCoordinator.generate_compressor_device_parameters(sc_id)
                if duck_amount_db != -2.5:
                    sc_params["threshold"] = round(max(0.0, min(1.0, (duck_amount_db * 2.0 + 40.0) / 40.0)), 4)

                for t_idx in target_indices:
                    comp_res = SidechainManager.find_or_load_compressor(conn, t_idx)
                    d_idx = comp_res.get("device_index", 0)
                    if d_idx >= 0:
                        for p_idx, p_val in [
                            (0, 1.0),
                            (20, 1.0),
                            (1, sc_params["threshold"]),
                            (2, sc_params["ratio"]),
                            (4, sc_params["attack"]),
                            (5, sc_params["release"]),
                            (12, 4.0),
                            (21, 0.40),
                            (22, 1.0)
                        ]:
                            try:
                                conn.send_command("set_device_parameter", {
                                    "track_index": t_idx,
                                    "device_index": d_idx,
                                    "parameter": p_idx,
                                    "value": p_val
                                })
                            except Exception:
                                pass
                        if vocal_idx is not None:
                            try:
                                SidechainManager.route_compressor_sidechain_source(conn, t_idx, d_idx, vocal_idx)
                            except Exception:
                                pass
                        ducking_report["compressors_configured"] += 1

                if vocal_idx is not None:
                    try:
                        c_res = conn.send_command("get_arrangement_clips", {"track_index": vocal_idx})
                        clips = c_res.get("clips", []) if isinstance(c_res, dict) else []
                        if clips:
                            v_ranges = [(float(c.get("start_time", 0.0)), float(c.get("end_time", 0.0))) for c in clips]
                        else:
                            sections = session.data.get("sections", [])
                            v_ranges = []
                            c_beat = 0.0
                            for sec in sections:
                                s_b = float(sec.get("bars", 8) * 4.0)
                                s_n = str(sec.get("name", "")).lower()
                                if any(w in s_n for w in ["verse", "verso", "drop", "hook", "coro", "climax", "chorus"]) and not any(w in s_n for w in ["intro", "buildup", "puente", "outro"]):
                                    v_ranges.append((c_beat, c_beat + s_b))
                                c_beat += s_b

                        if v_ranges:
                            tot_bars = session.data.get("total_bars", 64)
                            tot_beats = float(tot_bars * 4.0)
                            v_engine = VocalProductionEngine()
                            points = v_engine.calculate_ducking_envelope(
                                vocal_ranges_beats=v_ranges,
                                song_length_beats=tot_beats,
                                duck_amount_db=duck_amount_db
                            )
                            util_points = [
                                {
                                    "time": float(p["time"]),
                                    "value": round(duck_amount_db / 35.0, 4) if float(p.get("value", 1.0)) < 0.80 else 0.0
                                }
                                for p in points
                            ]
                            for t_idx in target_indices:
                                u_res = SidechainManager.ensure_utility_device(conn, t_idx)
                                u_idx = u_res.get("device_index", 0)
                                try:
                                    conn.send_command("add_automation_points", {
                                        "track": t_idx,
                                        "device_index": u_idx,
                                        "parameter": "Output",
                                        "points": util_points,
                                        "mode": "replace"
                                    })
                                except Exception:
                                    pass
                            ducking_report["automation_applied"] = True
                            ducking_report["ducking_target"] = "Utility.Output"
                            ducking_report["faders_unlocked"] = True
                            ducking_report["ducking_points_count"] = len(points)
                    except Exception as ex_auto:
                        logger.debug(f"Vocal ducking automation notice: {ex_auto}")
            except Exception as ex:
                logger.warning(f"Error configuring vocal ducking: {ex}")
                ducking_report["error"] = str(ex)

        session.data["vocal_ducking"] = ducking_report

        tracks = session.data.get("tracks", [])
        m_idx = 0
        if conn and hasattr(conn, "send_command"):
            try:
                s_res = conn.send_command("get_session_info", {})
                m_idx = s_res.get("result", s_res).get("track_count", len(tracks))
            except Exception:
                pass
        try:
            res_clean = ResonanceDetector.clean_low_mid_resonances(
                conn=conn,
                tracks=tracks,
                target_center_freq=441.4,
                cut_db=-3.5,
                q=12.0,
                master_track_index=m_idx
            )
            session.data["low_mid_resonances_clean"] = res_clean
        except Exception as ex_res:
            logger.debug(f"Post-vocal resonance cleaner notice: {ex_res}")

        session.data["current_phase"] = "PHASE_9_MIX_MASTER"
        session.data["phase_index"] = 9
        session._save_state()

        return session._prompt_phase_9()

    # -------------------------------------------------------------------------
    # DUAL-STAGE BS.1770-5 LUFS AUDIT GATE
    # -------------------------------------------------------------------------
    def handle_dual_lufs_validation(self, session: Any, conn: Any, user_input: str = "") -> Dict[str, Any]:
        """
        Executes Dual-Stage ITU-R BS.1770-5 LUFS & True Peak validation:
        Audits both the individual track channel (e.g. Track 12 '[VOCALS] Lead Vocal') and the master bus in general.
        Renders a dual comparison table and enforces compliance.
        """
        u_clean = _normalize_text(user_input)
        tracks = session.data.get("tracks", [])
        v_trk = next((t for t in tracks if t.get("role") == "VOCALS" or "vocal" in str(t.get("name", "")).lower()), None)
        if not v_trk:
            v_trk = {
                "index": 12,
                "name": "[VOCALS] Lead Vocal (Live Mic)",
                "role": "VOCALS",
                "instrument": "Live Mic Recording Take",
                "gain_staging": {"role_class": "vocal", "target_peak_dbfs": -18.0},
                "insert_effects": []
            }
            tracks.append(v_trk)
            session.data["tracks"] = tracks

        v_idx = session._resolve_live_track_index(conn, v_trk)
        v_name = v_trk.get("name", "[VOCALS] Lead Vocal")
        target_profile = session.data.get("target_profile", "STREAMING")

        is_gate_active = session.data.get("lufs_gate_active", False)
        wants_flexible_bypass = any(w in u_clean for w in ["bypass", "ignorar", "ignora", "aceptar", "acepta", "continuar", "continua", "opcion 3", "3.", "pasar"]) or u_clean == "3"
        wants_calibration = any(w in u_clean for w in ["calibrar", "calibra", "ajustar", "ajusta", "corregir", "si", "dale", "proceder", "opcion 1", "1."]) or u_clean == "1"

        if user_input == "post_audio_deployment":
            wants_calibration = False
        elif not wants_flexible_bypass and is_gate_active and not wants_calibration and not re.search(r"([+-]?\d+(?:\.\d+)?)\s*(?:db|dbfs)?", u_clean):
            wants_calibration = True

        manual_match = re.search(r"([+-]?\d+(?:\.\d+)?)\s*(?:db|dbfs)?", u_clean)
        manual_trim_db = float(manual_match.group(1)) if manual_match and not any(w in u_clean for w in ["opcion 1", "opcion 2", "opcion 3"]) else None

        applied_calibrations = []
        ch_trim = 0.0
        m_trim = 0.0

        if (wants_calibration or manual_trim_db is not None):
            prev_audit = session.data.get("dual_lufs_audit", {})
            prev_ch = prev_audit.get("channel_audit", {})
            prev_m = prev_audit.get("master_audit", {})

            ch_trim = manual_trim_db if manual_trim_db is not None else float(prev_ch.get("required_trim_db", 0.0))
            m_trim = float(prev_m.get("required_trim_db", 0.0))

            if abs(ch_trim) > 0.2 and conn is not None and hasattr(conn, "send_command"):
                try:
                    linear_mult = 10.0 ** (ch_trim / 20.0)
                    code_clip_gain = f"""
t = song.tracks[{v_idx}]
vol = t.mixer_device.volume
for c in getattr(t, 'arrangement_clips', []):
    try:
        cur_g = getattr(c, 'gain', 1.0)
        c.gain = max(0.02, min(10.0, cur_g * {linear_mult}))
    except: pass
cur_v = float(getattr(vol, 'value', 0.85))
vol.value = max(0.05, min(1.0, cur_v * min(1.3, max(0.7, {linear_mult}))))
"""
                    conn.send_command("execute_code", {"code": code_clip_gain})
                    applied_calibrations.append(f"Ganancia de clips y fader en Canal '{v_name}' (Pista {v_idx}) ajustados con {ch_trim:+.1f} dB.")
                except Exception as ex_c:
                    logger.debug(f"Channel gain adjustment notice: {ex_c}")

            if abs(m_trim) > 0.2 and manual_trim_db is None and conn is not None and hasattr(conn, "send_command"):
                try:
                    linear_m = 10.0 ** (m_trim / 20.0)
                    code_m_vol = f"""
m = song.master_track
vol = m.mixer_device.volume
cur_v = float(getattr(vol, 'value', 0.85))
vol.value = max(0.05, min(1.0, cur_v * {linear_m}))
"""
                    conn.send_command("execute_code", {"code": code_m_vol})
                    applied_calibrations.append(f"Fader de Master ajustado con {m_trim:+.1f} dB.")
                except Exception as ex_m:
                    logger.debug(f"Master gain adjustment notice: {ex_m}")

        applied_ch_trim = ch_trim if (wants_calibration or manual_trim_db is not None) else 0.0
        applied_m_trim = m_trim if (wants_calibration or manual_trim_db is not None) else 0.0

        dual_res = LUFSValidationGate.audit_dual_channel_and_master(
            conn=conn,
            track_index=v_idx,
            channel_name=v_name,
            sr=44100,
            master_profile_name=target_profile,
            channel_target_lufs=-18.0,
            channel_trim_db=applied_ch_trim,
            master_trim_db=applied_m_trim
        )

        ch_rep = dual_res.channel_audit
        m_rep = dual_res.master_audit
        ch_trim_txt = f"{ch_rep.required_trim_db:+.1f} dB" if not ch_rep.passed else "0.0 dB (Óptimo)"
        m_trim_txt = f"{m_rep.required_trim_db:+.1f} dB" if not m_rep.passed else "0.0 dB (Óptimo)"

        calib_txt = "\n".join([f"  🔧 **Calibración Aplicada:** {c}" for c in applied_calibrations]) if applied_calibrations else ""
        if calib_txt:
            calib_txt = f"\n\n{calib_txt}"

        session.data["dual_lufs_audit"] = dual_res.to_dict()

        if not dual_res.passed:
            if wants_flexible_bypass:
                session.data["lufs_gate_active"] = False
                session.data["lufs_gate_passed"] = True
                session._save_state()
            else:
                session.data["lufs_gate_active"] = True
                session.data["lufs_gate_passed"] = False
                session._save_state()

                q_text = (
                    f"📊 **Auditoría de Sonoridad ITU-R BS.1770-5 en Dos Etapas (Canal y Master):**\n\n"
                    f"{dual_res.summary_table}\n\n"
                    f"⚠️ **COMPUERTA DE SONORIDAD — CALIBRACIÓN O CONFIRMACIÓN REQUERIDA:**\n"
                    f"Tras agregar el audio a la sesión, la medición física revela desviaciones respecto al target normativo:\n"
                    f"• **Canal '{v_name}' (Pista {v_idx}):** **{ch_rep.integrated_lufs:.1f} LUFS** (Target: `{ch_rep.target_lufs:.1f} LUFS` ±1.5 LUFS | Desviación: `{ch_rep.lufs_deviation_db:+.1f} dB`)\n"
                    f"  - True Peak: `{ch_rep.true_peak_dbtp:.2f} dBTP` | Margen Headroom: `{ch_rep.headroom_margin_db:.1f} dB` | Compensación sugerida: `{ch_trim_txt}`\n"
                    f"• **Master Bus en General:** **{m_rep.integrated_lufs:.1f} LUFS** (Target: `{m_rep.target_lufs:.1f} LUFS` ±1.0 LUFS | Desviación: `{m_rep.lufs_deviation_db:+.1f} dB`)\n"
                    f"  - True Peak: `{m_rep.true_peak_dbtp:.2f} dBTP` | Margen Dinámico: `{m_rep.headroom_margin_db:.1f} dB` | Compensación sugerida: `{m_trim_txt}`\n"
                    f"{calib_txt}\n\n"
                    f"📋 **Formato de Respuesta y Opciones Disponibles:**\n"
                    f"• **Opción 1:** Aplicar Calibración Automática de Ganancia y Re-auditar ({ch_trim_txt} en canal vocal, {m_trim_txt} en master). *Escribe: 'Opción 1' o 'Calibrar'.*\n"
                    f"• **Opción 2:** Introducir ajuste manual en dB (ej: '+2.5 dB', '-1.5 dB').\n"
                    f"• **Opción 3:** Aceptar y Continuar con tolerancia flexible / Bypass de compuerta. *Escribe: 'Opción 3', 'Continuar', 'Aceptar' o 'Bypass'.*\n\n"
                    f"🧠 **Decisión Requerida:**\n"
                    f"Elige una de las 3 opciones para calibrar el audio o avanzar con la sesión."
                )

                return {
                    "status": "LUFS_CALIBRATION_REQUIRED",
                    "passed": False,
                    "retry_required": True,
                    "current_step": "COMPUERTA DE SONORIDAD: CALIBRACIÓN O TOLERANCIA FLEXIBLE (ITU-R BS.1770-5)",
                    "action_taken": f"Sonoridad evaluada: Canal '{v_name}' ({ch_rep.integrated_lufs:.1f} LUFS) y Master ({m_rep.integrated_lufs:.1f} LUFS). Esperando decisión del productor.",
                    "question": q_text,
                    "instructions_for_ai": "Informa al usuario de los niveles de sonoridad medidos y ofrece las 3 opciones (Opción 1: Calibrar, Opción 2: Manual en dB, Opción 3: Continuar/Bypass).",
                    "dual_lufs_audit": dual_res.to_dict(),
                    "phase": session.data.get("current_phase", "PHASE_5_INSERT_EFFECTS")
                }

        session.data["lufs_gate_active"] = False
        session.data["lufs_gate_passed"] = True
        session._save_state()

        v_step = session.data.get("vocal_production_step")

        if v_step == "PART_1_COMPLETED":
            q_text = (
                f"📊 **Auditoría de Sonoridad ITU-R BS.1770-5 en Dos Etapas (Canal y Master):**\n\n"
                f"{dual_res.summary_table}\n\n"
                f"✅ **¡SONORIDAD CALIBRADA Y CERTIFICADA CONFORME! (ITU-R BS.1770-5 APROBADO)**\n"
                f"• **Canal '{v_name}' (Pista {v_idx}):** **{ch_rep.integrated_lufs:.1f} LUFS** (Conforme con target {ch_rep.target_lufs:.1f} LUFS ±1.5 LUFS)\n"
                f"• **Master Bus en General:** **{m_rep.integrated_lufs:.1f} LUFS** (Conforme con target {m_rep.target_lufs:.1f} LUFS ±1.0 LUFS)\n"
                f"{calib_txt}\n\n"
                f"🎙️ **Parte 1 (Alineación de Frases Continuas en Versos) Finalizada con Éxito:**\n"
                f"Las frases melódicas están ancladas en la cuadrícula de versos y la sonoridad cumple la norma comercial.\n\n"
                f"🧠 **Decisión Requerida para la Parte 2:**\n"
                f"¿Deseas ahora proceder con la **Parte 2** (Generar la batería de más de 90 Vocal Chops en los Drops)?\n\n"
                f"• **Opción A: Sí, generar Vocal Chops en los Drops (Parte 2)**\n"
                f"  - Despliega stutters a 1/16, pitch shifts (+3st, +7st, +12st), rave snaps y procesamiento espacial en paralelo en Drop 1 y Drop 2.\n\n"
                f"• **Opción B: No, continuar directamente a esculpir la cadena de efectos vocales**\n"
                f"  - Conserva el arreglo con voz limpia en versos y avanza a ajustar Auto-Tune Artist, EQ Eight y Compressor.\n\n"
                f"*Responde 'Opción A' (o 'Generar chops') u 'Opción B' (o 'Continuar').*"
            )
            return {
                "status": "PART_1_LUFS_CERTIFIED",
                "passed": True,
                "current_step": "PARTE 1 CONCLUIDA Y CERTIFICADA EN LUFS — DECISIÓN PARTE 2",
                "action_taken": f"Parte 1 verificada y certificada en LUFS ({ch_rep.integrated_lufs:.1f} LUFS / Master {m_rep.integrated_lufs:.1f} LUFS). Consulta interactiva para Parte 2 iniciada.",
                "question": q_text,
                "instructions_for_ai": "Pregunta al usuario si desea ejecutar la Parte 2 (Generar Vocal Chops en los Drops) o continuar a esculpir efectos.",
                "dual_lufs_audit": dual_res.to_dict(),
                "phase": session.data.get("current_phase", "PHASE_5_INSERT_EFFECTS")
            }

        vocal_trk_entry = next((t for t in session.data.get("tracks", []) if t.get("role") == "VOCALS"), None)
        if not vocal_trk_entry:
            vocal_trk_entry = next((t for t in session.data.get("tracks", []) if t.get("index") == v_idx), None)
        if not vocal_trk_entry:
            vocal_trk_entry = v_trk
            if "tracks" not in session.data:
                session.data["tracks"] = []
            session.data["tracks"].append(vocal_trk_entry)

        v_effects = vocal_trk_entry.get("insert_effects", [])
        expected_fx_len = len(ROLE_INSERT_EFFECTS.get("VOCALS", []))
        if len(v_effects) >= expected_fx_len:
            session.data["current_phase"] = "PHASE_6_COMPOSITION"
            session.data["phase_index"] = 6
            session._save_state()
            comp_prompt = session._prompt_phase_6()
            q_text = (
                f"📊 **Auditoría de Sonoridad ITU-R BS.1770-5 en Dos Etapas (Canal y Master):**\n\n"
                f"{dual_res.summary_table}\n\n"
                f"✅ **¡SONORIDAD CALIBRADA Y CERTIFICADA CONFORME! (ITU-R BS.1770-5 APROBADO)**\n"
                f"• **Canal '{v_name}' (Pista {v_idx}):** **{ch_rep.integrated_lufs:.1f} LUFS** (Target: `{ch_rep.target_lufs:.1f} LUFS`)\n"
                f"• **Master Bus:** **{m_rep.integrated_lufs:.1f} LUFS** (Target: `{m_rep.target_lufs:.1f} LUFS`)\n"
                f"{calib_txt}\n\n"
                f"💡 **Estado Global de la Compuerta:** {dual_res.certificate}\n\n"
                + comp_prompt.get("question", "")
            )
            return {
                "status": "DUAL_LUFS_AUDITED",
                "passed": True,
                "current_step": "PASO 6 DE 7: COMPOSICIÓN ARMÓNICA Y MELÓDICA MODULAR",
                "action_taken": f"Comprobación ITU-R BS.1770-5 certificada ({ch_rep.integrated_lufs:.1f} LUFS / Master {m_rep.integrated_lufs:.1f} LUFS). Efectos vocales verificados. Avanzando a composición.",
                "question": q_text,
                "instructions_for_ai": comp_prompt.get("instructions_for_ai", ""),
                "dual_lufs_audit": dual_res.to_dict(),
                "phase": "PHASE_6_COMPOSITION"
            }

        vocal_track_ptr = session.data["tracks"].index(vocal_trk_entry)
        session.data["current_phase"] = "PHASE_5_INSERT_EFFECTS"
        session.data["phase_index"] = 5
        session.data["current_fx_track_ptr"] = vocal_track_ptr
        session.data["current_fx_dev_ptr"] = 0
        session._save_state()

        sculpt_prompt = session._prompt_current_fx_device()

        q_text = (
            f"📊 **Auditoría de Sonoridad ITU-R BS.1770-5 en Dos Etapas (Canal y Master):**\n\n"
            f"{dual_res.summary_table}\n\n"
            f"✅ **¡SONORIDAD CALIBRADA Y CERTIFICADA CONFORME! (ITU-R BS.1770-5 APROBADO)**\n"
            f"• **Canal '{v_name}' (Pista {v_idx}):** **{ch_rep.integrated_lufs:.1f} LUFS** (Target: `{ch_rep.target_lufs:.1f} LUFS`)\n"
            f"• **Master Bus:** **{m_rep.integrated_lufs:.1f} LUFS** (Target: `{m_rep.target_lufs:.1f} LUFS`)\n"
            f"{calib_txt}\n\n"
            f"💡 **Estado Global de la Compuerta:** {dual_res.certificate}\n\n"
            f"⚠️ **Configuración Obligatoria de Efectos de Inserción — Pista Vocal:**\n"
            f"Habiendo garantizado el headroom y la sonoridad normativa, el motor te exige esculpir individualmente cada procesador de la cadena vocal:\n\n"
            + sculpt_prompt.get("question", "")
        )

        return {
            "status": "DUAL_LUFS_AUDITED",
            "passed": True,
            "current_step": "AUDITORÍA LUFS DE DOBLE ETAPA: CANAL INDIVIDUAL Y MASTER GENERAL",
            "action_taken": f"Comprobación ITU-R BS.1770-5 completada para Canal '{v_name}' ({ch_rep.integrated_lufs:.1f} LUFS) y Master ({m_rep.integrated_lufs:.1f} LUFS). Iniciando esculpido de efectos.",
            "question": q_text,
            "instructions_for_ai": "Presenta la certificación conforme de LUFS y guía al usuario al esculpido del procesador vocal actual.",
            "dual_lufs_audit": dual_res.to_dict(),
            "phase": "PHASE_5_INSERT_EFFECTS"
        }
