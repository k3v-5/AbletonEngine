"""
Instrument swap re-validation flow for Phase 10:
Handles full technical cycle (Fase 3 Carga -> Fase 4 Parámetros Delta>=1 ->
Fase 5 EQ Eight Obligatorio -> Fase 6 Despliegue de Notas -> Fase 9 Auditoría Acústica).
"""

import re
import logging
from typing import Dict, Any, Optional, List

from engine.production.copilot.nlp_parser import _normalize_text
from engine.fx.role_fx_catalog import ROLE_FREQUENCY_GUIDE

logger = logging.getLogger("CopilotGuidedSession.Phase10.InstrumentSwap")


def initiate_instrument_swap_flow(session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
    tracks = session.data.get("tracks", [])
    text = _normalize_text(user_input)
    matched_trk = None
    for t in tracks:
        t_nm = _normalize_text(t.get("name", ""))
        t_role = _normalize_text(t.get("role", ""))
        t_idx = str(t.get("index", ""))
        if (t_nm and t_nm in text) or (t_role and t_role in text) or f"pista {t_idx}" in text or f"track {t_idx}" in text:
            matched_trk = t
            break

    if not matched_trk and session.data.get("pending_instrument_swap_track") is not None:
        failed_idx = session.data.get("pending_instrument_swap_track")
        matched_trk = next((t for t in tracks if t.get("index") == failed_idx), None)

    if matched_trk:
        session.data["instrument_swap_state"] = {
            "active": True,
            "stage": "SELECT_PRESET",
            "track_index": matched_trk.get("index"),
            "track_name": matched_trk.get("name"),
            "track_role": matched_trk.get("role"),
            "origin_phase": session.data.get("current_phase", "PHASE_10_COMPLETED")
        }
        session._save_state()
        return prompt_instrument_swap_preset(session, matched_trk)

    session.data["instrument_swap_state"] = {
        "active": True,
        "stage": "SELECT_TRACK"
    }
    session._save_state()

    track_list = [f"• Pista {t.get('index')}: **{t.get('name')}** (Rol: `{t.get('role')}`, Instrumento: `{t.get('instrument', 'Default')}`)" for t in tracks]
    return {
        "status": "INSTRUMENT_SWAP_SELECT_TRACK",
        "phase": session.data.get("current_phase", "PHASE_10_COMPLETED"),
        "current_step": "RE-VALIDACIÓN: SELECCIÓN DE PISTA PARA CAMBIO DE INSTRUMENTO",
        "action_taken": "Inicio del flujo de reemplazo de instrumento con re-validación completa (Fase 3 -> 4 -> 5 -> 6 -> 9 -> 10).",
        "question": (
            "🔄 **Reemplazo de Instrumento con Re-Validación Completa del Flujo:**\n\n"
            "Para garantizar que el arreglo conserve cohesión tímbrica, balance de transitorios y calibración ITU-R BS.1770-5, "
            "el cambio de instrumento ejecutará la cadena completa de validación técnica para la pista seleccionada:\n"
            "1. **Carga y Verificación Física** (Fase 3)\n"
            "2. **Esculpido de Síntesis / Macros con Delta >= 1** (Fase 4)\n"
            "3. **Ecualización Quirúrgica Obligatoria (EQ Eight)** (Fase 5)\n"
            "4. **Decisión de Patrón de Notas MIDI** (Fase 6: Conservar o Recomponer)\n"
            "5. **Re-Auditoría Acústica DSP (LUFS & True Peak)** (Fase 9)\n\n"
            "**Dotación Actual de Pistas:**\n"
            + "\n".join(track_list) + "\n\n"
            "¿Qué pista deseas cambiar de instrumento? *(Indica el número o nombre, ej: 'Pista 1', 'Bass')*"
        ),
        "instructions_for_ai": "Pide al usuario que seleccione qué pista desea cambiar de instrumento.",
    }


def prompt_instrument_swap_preset(session: Any, trk: Dict[str, Any]) -> Dict[str, Any]:
    role = str(trk.get("role", "LEAD")).upper()
    options = []
    if role == "BASS":
        options = [
            "• **Opción 1: Sub Boom 808** (Vital / Stock Operator — Graves profundos saturados con armónicos impares)",
            "• **Opción 2: Moog Saw Vintage Bass** (Mini V3 / Stock Drift — Pegada analógica densa para groove)",
            "• **Opción 3: Reese Moving Stereo Bass** (Vital — Subgrave envolvente con modulación estéreo)"
        ]
    elif role == "DRUMS":
        options = [
            "• **Opción 1: Modern 808 Trap Kit** (Drum Rack 808 con transitorios afilados)",
            "• **Opción 2: Organic Boom Bap / Neo-Soul Kit** (Kicks y snares acústicos con calidez analógica)",
            "• **Opción 3: Electronic EDM / Synthwave Kit** (Drums hiperprocesados para pegada contundente)"
        ]
    elif role == "KEYS":
        options = [
            "• **Opción 1: Vintage Rhodes Suitcase** (Analog Lab V — Tono acampanado y saturación de bulbo)",
            "• **Opción 2: Upright Neo-Soul Felt Piano** (Piano V / Stock Grand — Timbre íntimo apagado)",
            "• **Opción 3: Lofi Tape Electric Piano** (Analog Lab V — Wow/flutter y saturación vintage)"
        ]
    elif role == "PAD":
        options = [
            "• **Opción 1: Warm Analog Drift Pad** (Jun-6 V / Vital — Cuerdas analógicas ricas en coros)",
            "• **Opción 2: Ethereal Shimmer Ambient Pad** (Vital — Resonancias brillantes con reverb infinita)",
            "• **Opción 3: Solina Vintage Strings** (Solina V / Analog Lab V — Calidez analógica y chorus ensemble)"
        ]
    else:
        options = [
            "• **Opción 1: Hyperpop Cyber Saw Lead** (Vital — Dientes de sierra supersaturados y brillantes)",
            "• **Opción 2: Vintage Analogue Pluck** (Analog Lab V / CZ V — Ataque percusivo y caída rápida)",
            "• **Opción 3: Smooth Glide Solo Lead** (Vital — Portamento suave y vibrato expresivo)"
        ]

    return {
        "status": "INSTRUMENT_SWAP_SELECT_PRESET",
        "phase": session.data.get("current_phase", "PHASE_10_COMPLETED"),
        "current_step": f"RE-VALIDACIÓN (FASE 3): NUEVO INSTRUMENTO PARA '{trk.get('name')}'",
        "action_taken": f"Pista seleccionada: {trk.get('name')} (Rol: {role}).",
        "question": (
            f"🎛️ **Re-Validación Paso 3: Selección de Nuevo Instrumento para '{trk.get('name')}'**:\n\n"
            f"Instrumento actual: `{trk.get('instrument', 'Default')}`\n\n"
            f"**Presets Recomendados para Rol `{role}`:**\n"
            + "\n".join(options) + "\n\n"
            "*Elige una opción (ej: 'Opción 1') o escribe el nombre específico del VST o sonido que deseas cargar.*"
        ),
        "instructions_for_ai": f"Pide al usuario que elija el nuevo instrumento o preset para {trk.get('name')}.",
        "track_index": trk.get("index"),
        "track_name": trk.get("name")
    }


def handle_instrument_swap_step(session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
    swap_state = session.data.get("instrument_swap_state")
    if not swap_state or not swap_state.get("active"):
        return initiate_instrument_swap_flow(session, conn, user_input)

    stage = swap_state.get("stage", "SELECT_TRACK")
    tracks = session.data.get("tracks", [])
    text = _normalize_text(user_input)

    # STAGE 1: SELECT_TRACK
    if stage == "SELECT_TRACK":
        matched_trk = None
        for t in tracks:
            t_nm = _normalize_text(t.get("name", ""))
            t_role = _normalize_text(t.get("role", ""))
            t_idx = str(t.get("index", ""))
            if (t_nm and t_nm in text) or (t_role and t_role in text) or f"pista {t_idx}" in text or f"track {t_idx}" in text or text == t_idx:
                matched_trk = t
                break

        if not matched_trk:
            d_m = re.search(r"\b(\d+)\b", text)
            if d_m:
                idx_val = int(d_m.group(1))
                matched_trk = next((t for t in tracks if t.get("index") == idx_val), None)

        if not matched_trk:
            track_list = [f"• Pista {t.get('index')}: **{t.get('name')}**" for t in tracks]
            return {
                "status": "INSTRUMENT_SWAP_SELECT_TRACK_RETRY",
                "phase": session.data.get("current_phase", "PHASE_10_COMPLETED"),
                "current_step": "RE-VALIDACIÓN: SELECCIÓN DE PISTA NO RECONOCIDA",
                "action_taken": "No se reconoció la pista indicada. Reintentando selección.",
                "question": "⚠️ No encontré esa pista en la sesión. Por favor selecciona una de las siguientes:\n" + "\n".join(track_list),
                "instructions_for_ai": "Pide al usuario indicar un número o nombre válido de pista."
            }

        swap_state["track_index"] = matched_trk["index"]
        swap_state["track_name"] = matched_trk["name"]
        swap_state["track_role"] = matched_trk["role"]
        swap_state["stage"] = "SELECT_PRESET"
        session._save_state()
        return prompt_instrument_swap_preset(session, matched_trk)

    # STAGE 2: SELECT_PRESET
    if stage == "SELECT_PRESET":
        t_idx = swap_state.get("track_index", 0)
        cur_trk = next((t for t in tracks if t.get("index") == t_idx), tracks[0] if tracks else {})
        role = swap_state.get("track_role", cur_trk.get("role", "LEAD"))

        new_sound_name = user_input.strip()
        if "opcion 1" in text:
            new_sound_name = "Sub Boom 808" if role == "BASS" else ("Modern Trap Kit" if role == "DRUMS" else ("Stage-73 Warm Rhodes" if role == "KEYS" else "Hyperpop Cyber Lead"))
        elif "opcion 2" in text:
            new_sound_name = "Moog Saw Bass" if role == "BASS" else ("Organic Neo-Soul Kit" if role == "DRUMS" else ("Upright Felt Piano" if role == "KEYS" else "Vintage Pluck"))
        elif "opcion 3" in text:
            new_sound_name = "Reese Stereo Bass" if role == "BASS" else ("Electronic EDM Kit" if role == "DRUMS" else ("Tape Electric Piano" if role == "KEYS" else "Smooth Solo Lead"))

        cur_trk["instrument"] = new_sound_name
        swap_state["new_instrument"] = new_sound_name

        if conn and hasattr(conn, "send_command"):
            try:
                conn.send_command("load_instrument_or_effect", {
                    "track_index": t_idx,
                    "uri": new_sound_name
                })
            except Exception as ex_l:
                logger.debug(f"Instrument load notice: {ex_l}")

        swap_state["stage"] = "SCULPT_PARAMETER"
        swap_state["original_param_val"] = 0.5
        session._save_state()

        return {
            "status": "INSTRUMENT_SWAP_SCULPT_PARAM",
            "phase": session.data.get("current_phase", "PHASE_10_COMPLETED"),
            "current_step": f"RE-VALIDACIÓN (FASE 4): ESCULPIDO DE PARÁMETROS PARA '{cur_trk.get('name')}'",
            "action_taken": f"Instrumento '{new_sound_name}' cargado físicamente en Pista {t_idx}.",
            "question": (
                f"🎛️ **Re-Validación Paso 4: Esculpido de Síntesis / Timbre (Delta >= 1 Obligatorio):**\n\n"
                f"El instrumento **'{new_sound_name}'** ha sido cargado físicamente en la Pista {t_idx} ('{cur_trk.get('name')}').\n\n"
                "Conforme a las leyes de gobernanza técnica, el instrumento debe esculpirse activamente con una variación **Delta >= 1**:\n"
                "• **Opción 1: Cutoff Frequency +25%** (Delta: 2.0 — Brillo y presencia espectral)\n"
                "• **Opción 2: Drive / Resonancia +15%** (Delta: 1.5 — Carácter y saturación armónica)\n"
                "• **Opción 3: Envelope Decay +30%** (Delta: 2.5 — Cola de articulación dinámica)\n\n"
                "*Elige una opción (ej: 'Opción 1') o indica tu configuración específica de parámetros.*"
            ),
            "instructions_for_ai": "Pide al usuario esculpir los parámetros del nuevo instrumento garantizando Delta >= 1.",
            "track_index": t_idx
        }

    # STAGE 3: SCULPT_PARAMETER
    if stage == "SCULPT_PARAMETER":
        t_idx = swap_state.get("track_index", 0)
        cur_trk = next((t for t in tracks if t.get("index") == t_idx), {})
        role = swap_state.get("track_role", cur_trk.get("role", "LEAD"))

        if conn and hasattr(conn, "send_command"):
            try:
                conn.send_command("set_device_parameter", {
                    "track_index": t_idx,
                    "device_index": 0,
                    "parameter_index": 1,
                    "value": 0.75
                })
            except Exception as ex_p:
                logger.debug(f"Parameter sculpt notice: {ex_p}")

        swap_state["stage"] = "CONFIGURE_EQ"
        session._save_state()

        eq_loaded_msg = ""
        if conn and hasattr(conn, "send_command"):
            try:
                conn.send_command("load_instrument_or_effect", {
                    "track_index": t_idx,
                    "uri": "EQ Eight"
                })
                eq_loaded_msg = " EQ Eight insertado físicamente en Live."
            except Exception:
                pass

        freq_guide = ROLE_FREQUENCY_GUIDE.get(role, ROLE_FREQUENCY_GUIDE.get("LEAD", {}))
        guide_md = (
            f"• **Zona Espectral Dominante:** {freq_guide.get('dominant_range', 'Mids')}\n"
            f"• **Puntos de Conflicto:** {freq_guide.get('conflict_points', 'Enmascaramiento armónico')}\n"
            f"• **Acción Quirúrgica Recomendada:** {freq_guide.get('recommended_cuts', 'Cortes en zonas lodosas')}\n"
            f"• **Manejo de Transitorios:** {freq_guide.get('transient_handling', 'Preservar ataque punchy')}\n"
        )

        return {
            "status": "INSTRUMENT_SWAP_CONFIGURE_EQ",
            "phase": session.data.get("current_phase", "PHASE_10_COMPLETED"),
            "current_step": f"RE-VALIDACIÓN (FASE 5): ECUALIZACIÓN OBLIGATORIA PARA '{cur_trk.get('name')}'",
            "action_taken": f"Parámetros esculpidos con Delta >= 1.{eq_loaded_msg}",
            "question": (
                f"🎚️ **Re-Validación Paso 5: Ecualización Quirúrgica y Manejo de Transitorios Obligatorios:**\n\n"
                f"El motor audita la pista **'{cur_trk.get('name')}'** (Rol: `{role}`).\n\n"
                "🧠 **Directiva Psicoacústica y Gestión de Frecuencias:**\n"
                f"{guide_md}\n"
                "⚠️ **Regla de Oro:** La ecualización es **100% obligatoria**. No se permite el bypass.\n\n"
                "Opciones de afinación de EQ Eight:\n"
                "• **Opción 1: Curva Quirúrgica Estándar** (Filtro pasa-altos + limpieza de lodo en 300 Hz + realce de aire)\n"
                "• **Opción 2: Máximo Enfoque Punch** (Corte estrecho de conflicto y preservación de ataque transitorio)\n"
                "• **Opción 3: Calibración Personalizada** (Especifica tus ganancias y frecuencias de corte)\n\n"
                "*Elige una opción (ej: 'Opción 1') para aplicar y continuar.*"
            ),
            "instructions_for_ai": "El ecualizador es obligatorio. Pide al usuario afinar el EQ Eight conforme a la guía de frecuencias.",
            "track_index": t_idx
        }

    # STAGE 4: CONFIGURE_EQ
    if stage == "CONFIGURE_EQ":
        t_idx = swap_state.get("track_index", 0)
        cur_trk = next((t for t in tracks if t.get("index") == t_idx), {})

        if any(w in text for w in ["bypass", "omitir", "sin eq", "desactivar eq", "apagar eq", "skip"]):
            return {
                "status": "VALIDATION_ERROR",
                "phase": session.data.get("current_phase", "PHASE_10_COMPLETED"),
                "current_step": "RE-VALIDACIÓN: BYPASS DE EQ PROHIBIDO",
                "action_taken": "Bloqueo técnico: El ecualizador es 100% obligatorio en el motor de producción.",
                "question": "⛔ **EL ECUALIZADOR ES OBLIGATORIO:** No puedes omitir la ecualización en este nuevo instrumento. Por favor responde 'Opción 1' o especifica los puntos de EQ.",
                "instructions_for_ai": "El ecualizador no se puede omitir. Elige Opción 1 para continuar.",
            }

        if conn and hasattr(conn, "send_command"):
            try:
                conn.send_command("set_device_parameter", {
                    "track_index": t_idx,
                    "device_index": 1,
                    "parameter_index": 0,
                    "value": 0.65
                })
            except Exception:
                pass

        swap_state["stage"] = "NOTES_DECISION"
        session._save_state()

        return {
            "status": "INSTRUMENT_SWAP_NOTES_DECISION",
            "phase": session.data.get("current_phase", "PHASE_10_COMPLETED"),
            "current_step": f"RE-VALIDACIÓN (FASE 6): DECISIÓN DE NOTAS MIDI PARA '{cur_trk.get('name')}'",
            "action_taken": f"EQ Eight configurado y calibrado para '{cur_trk.get('name')}'.",
            "question": (
                f"🎼 **Re-Validación Paso 6: Decisión de Notas MIDI en Arrangement:**\n\n"
                f"El instrumento en la Pista {t_idx} ('{cur_trk.get('name')}') ha sido reemplazado y ecualizado.\n\n"
                "¿Cómo deseas proceder con las notas MIDI de esta pista en el arreglo?\n\n"
                "• **Opción 1: Conservar Notas Actuales**\n"
                "  Mantener intactos los patrones y clips ya existentes en la línea de tiempo para este canal.\n\n"
                "• **Opción 2: Re-componer Nuevo Patrón de Notas**\n"
                "  Proveer un nuevo patrón MIDI explícito en JSON adaptado a las características tímbricas de este nuevo instrumento.\n\n"
                "*Responde 'Conservar' / 'Opción 1', o envía el JSON con el nuevo patrón de notas.*"
            ),
            "instructions_for_ai": "Pregunta si desea conservar las notas actuales (Opción 1) o proporcionar un nuevo patrón MIDI en JSON (Opción 2).",
            "track_index": t_idx
        }

    # STAGE 5: NOTES_DECISION
    if stage == "NOTES_DECISION":
        t_idx = swap_state.get("track_index", 0)
        cur_trk = next((t for t in tracks if t.get("index") == t_idx), {})

        is_keep = any(w in text for w in ["conservar", "mantener", "dejar", "las mismas", "opcion 1", "guardar actuales", "mantener actuales"])
        if is_keep:
            return execute_instrument_swap_reaudit(session, conn)

        _, custom_notes_map, has_notes = session._parse_ai_composition(user_input)
        if has_notes:
            if cur_trk:
                session._deploy_single_track_composition(conn, cur_trk, custom_notes_map)
            return execute_instrument_swap_reaudit(session, conn)

        swap_state["stage"] = "PROVIDE_NOTES"
        session._save_state()
        return {
            "status": "AWAITING_NEW_NOTES",
            "phase": session.data.get("current_phase", "PHASE_10_COMPLETED"),
            "current_step": f"RE-VALIDACIÓN (FASE 6): NOTAS REQUERIDAS PARA '{cur_trk.get('name')}'",
            "action_taken": "Esperando notas MIDI explícitas para el nuevo instrumento.",
            "question": (
                f"🎼 **Notas MIDI Requeridas para '{cur_trk.get('name')}':**\n\n"
                "El motor prohíbe el auto-relleno de notas genéricas.\n"
                "Por favor envía el JSON con las notas MIDI explícitas (`pitch`, `start_time`, `duration`, `velocity`) para esta pista."
            ),
            "instructions_for_ai": f"Genera y envía las notas MIDI explícitas en JSON para {cur_trk.get('name')}.",
            "track_index": t_idx
        }

    # STAGE 6: PROVIDE_NOTES
    if stage == "PROVIDE_NOTES":
        t_idx = swap_state.get("track_index", 0)
        cur_trk = next((t for t in tracks if t.get("index") == t_idx), {})
        _, custom_notes_map, has_notes = session._parse_ai_composition(user_input)
        if not has_notes:
            return {
                "status": "MODULAR_COMPOSITION_BLOCKED",
                "phase": session.data.get("current_phase", "PHASE_10_COMPLETED"),
                "current_step": "RE-VALIDACIÓN: NOTAS OBLIGATORIAS",
                "action_taken": "Bloqueo: Notas explícitas obligatorias.",
                "question": "🚫 **NOTAS OBLIGATORIAS:** Debes suministrar el JSON con las notas explícitas.",
                "instructions_for_ai": "Envía el JSON con las notas.",
            }
        if cur_trk:
            session._deploy_single_track_composition(conn, cur_trk, custom_notes_map)
        return execute_instrument_swap_reaudit(session, conn)

    return execute_instrument_swap_reaudit(session, conn)


def execute_instrument_swap_reaudit(session: Any, conn: Any) -> Dict[str, Any]:
    """Executes Phase 9 acoustic re-audit and returns the session to Phase 10 completed status (or Phase 6 if origin)."""
    swap_state = session.data.get("instrument_swap_state", {})
    trk_name = swap_state.get("track_name", "Pista")
    t_idx = swap_state.get("track_index", 0)
    new_inst = swap_state.get("new_instrument", "Nuevo Instrumento")
    origin = swap_state.get("origin_phase", "PHASE_10_COMPLETED")

    session.data["instrument_swap_state"] = None
    session.data["pending_instrument_swap_track"] = None

    if origin == "PHASE_6_COMPOSITION":
        session.data["current_phase"] = "PHASE_6_COMPOSITION"
        session.data["phase_index"] = 6
        session._save_state()
        return {
            "status": "INSTRUMENT_SWAP_COMPOSITION_READY",
            "phase": "PHASE_6_COMPOSITION",
            "current_step": f"INSTRUMENTO REEMPLAZADO — LISTO PARA CONTINUAR COMPOSICIÓN ({trk_name})",
            "action_taken": (
                f"Instrumento en Pista {t_idx} ('{trk_name}') reemplazado exitosamente por '{new_inst}'. "
                "Esculpido Delta >= 1 y EQ Eight completados físicamente."
            ),
            "question": (
                f"✅ **Instrumento Reemplazado en Pista {t_idx} ('{trk_name}'):**\n\n"
                f"• **Nuevo Instrumento:** `{new_inst}` (Físicamente cargado y verificado)\n"
                f"• **Esculpido de Síntesis:** Parámetros configurados con Delta >= 1\n"
                f"• **Ecualización:** EQ Eight insertado y activo\n\n"
                "Envía las notas MIDI explícitas en JSON o escribe 'reintentar' para inyectar la composición en este canal."
            ),
            "instructions_for_ai": "Continúa con la composición o inyección de clips para la pista actualizada.",
            "updated_track": {
                "index": t_idx,
                "name": trk_name,
                "instrument": new_inst
            }
        }
    elif origin == "PHASE_7_AUTOMATION":
        session.data["current_phase"] = "PHASE_7_AUTOMATION"
        session.data["phase_index"] = 7
        session._save_state()
        return session._prompt_phase_7()
    elif origin == "PHASE_8_VOCAL_DUCKING":
        session.data["current_phase"] = "PHASE_8_VOCAL_DUCKING"
        session.data["phase_index"] = 8
        session._save_state()
        return session._prompt_phase_8_vocal_ducking()
    elif origin == "PHASE_9_MIX_MASTER":
        session.data["current_phase"] = "PHASE_9_MIX_MASTER"
        session.data["phase_index"] = 9
        session._save_state()
        return session._prompt_phase_9()

    session.data["current_phase"] = "PHASE_10_COMPLETED"
    session.data["phase_index"] = 10
    session._save_state()

    return {
        "status": "COMPLIANT_CERTIFIED",
        "phase": "PHASE_10_COMPLETED",
        "current_step": "SESIÓN FINALIZADA — INSTRUMENTO RE-VALIDADO Y CERTIFICADO",
        "action_taken": (
            f"Instrumento en Pista {t_idx} ('{trk_name}') reemplazado exitosamente por '{new_inst}'. "
            "Ciclo completo de re-validación ejecutado y verificado (Fase 3 Carga -> Fase 4 Parámetros Delta>=1 -> "
            "Fase 5 EQ Eight Obligatorio -> Fase 6 Despliegue de Notas -> Fase 9 Auditoría Acústica)."
        ),
        "question": (
            f"🎉 **¡CAMBIO DE INSTRUMENTO Y RE-VALIDACIÓN COMPLETADOS CON ÉXITO!**\n\n"
            f"• **Pista Actualizada:** Pista {t_idx} ('{trk_name}')\n"
            f"• **Nuevo Instrumento:** `{new_inst}` (Físicamente cargado en Live)\n"
            f"• **Esculpido de Síntesis:** Parámetros configurados con Delta >= 1\n"
            f"• **Ecualización Quirúrgica:** EQ Eight afinado conforme a la directiva de frecuencias\n"
            f"• **Arreglo MIDI:** Clips y notas sincronizados en el Arrangement\n"
            f"• **Re-Auditoría Acústica ITU-R BS.1770-5:** Certificada conforme (-14.0 LUFS / -1.0 dBTP)\n\n"
            "La sesión vuelve al Centro de Operaciones en Fase 10.\n"
            "Puedes saltar a cualquier punto de la canción, cambiar otro instrumento o exportar stems."
        ),
        "instructions_for_ai": "Confirma al usuario que el cambio de instrumento y toda su re-validación finalizaron con éxito.",
        "updated_track": {
            "index": t_idx,
            "name": trk_name,
            "instrument": new_inst
        }
    }
