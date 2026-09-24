# engine/production/copilot/phases/phase_6/prompts.py
"""
Phase 6 Prompt Builder:
Generates interactive user prompts for Phase 6 (Monolithic, Track-by-Track, and Clip-by-Clip modes).
"""
from typing import Dict, Any, Callable


class Phase6Prompts:
    """Builder for Phase 6 interactive prompts."""

    @staticmethod
    def prompt_by_track_step(session: Any, trk_idx: int) -> Dict[str, Any]:
        tracks = session.data.get("tracks", [])
        sections = session.data.get("sections", [])
        if trk_idx >= len(tracks):
            return session._prompt_phase_7()

        cur_trk = tracks[trk_idx]
        cur_trk_is_aud = bool(
            cur_trk.get("is_audio", False)
            or str(cur_trk.get("role", "")).upper() == "VOCALS"
            or cur_trk.get("live_recording_mode", False)
        )
        sec_names = [s.get("name", f"Sección {i+1}") for i, s in enumerate(sections)]
        sec_str = ", ".join(sec_names) if sec_names else "Todas las secciones"

        if cur_trk_is_aud:
            return {
                "status": "AWAITING_AUDIO_TRACK_CONFIRMATION",
                "current_step": f"PASO 6 (POR PISTA {trk_idx + 1}/{len(tracks)}): PREPARACIÓN DE CANAL AUDIO '{cur_trk.get('name')}'",
                "action_taken": f"Modo interactivo pista por pista activo. Pista de Audio/Grabación/FX: {cur_trk.get('name')} (Rol: {cur_trk.get('role')}).",
                "question": (
                    f"🎙️ **Canal de Audio / Grabación / Ruteo FX {trk_idx + 1} de {len(tracks)}: '{cur_trk.get('name')}' (Rol: `{cur_trk.get('role')}`):**\n\n"
                    f"• **Instrumento / Ruteo:** {cur_trk.get('instrument', cur_trk.get('name'))}\n"
                    f"• **Tipo de Pista:** Canal de Audio (Sin notas MIDI requeridas).\n\n"
                    f"Envía 'confirmar' o 'siguiente' para validar el ruteo y armar el canal en el Arrangement."
                ),
                "instructions_for_ai": f"Envía 'confirmar' para preparar el canal de audio '{cur_trk.get('name')}'.",
                "phase": "PHASE_6_COMPOSITION",
                "track_index": trk_idx,
                "track_name": cur_trk.get("name"),
                "track_role": cur_trk.get("role")
            }

        drum_spec_block = ""
        role_upper = str(cur_trk.get("role", "")).upper()
        inst_lower = str(cur_trk.get("instrument", "")).lower()
        trk_name_lower = str(cur_trk.get("name", "")).lower()
        if role_upper in ("DRUMS", "KICK") or any(w in inst_lower for w in ["drum", "bater", "kit", "rack"]) or any(w in trk_name_lower for w in ["drum", "bater", "perc"]):
            drum_spec_block = (
                "\n\n🥁 **Especificación Física de Drum Rack (Ableton Live):**\n"
                "• **Octava Inicial Obligatoria:** C1 (MIDI pitch 36).\n"
                "• **Mapa de Pads Estándar:**\n"
                "  - 36 (C1): Bombo / Kick\n"
                "  - 37 (C#1): Aro / Rimshot / Sidestick\n"
                "  - 38 (D1): Caja / Snare acústico\n"
                "  - 39 (D#1): Aplauso / Hand Clap\n"
                "  - 42 (F#1): Hi-Hat cerrado / Shaker\n"
                "  - 46 (A#1): Hi-Hat abierto\n"
                "  - 49 (C#2): Platillo Crash\n"
                "  - 51 (D#2): Platillo Ride\n"
                "⚠️ *Para evitar pads silenciosos en Ableton Live, mapea tus notas a partir de C1 (pitch 36 a 51).*"
            )

        key = session.data.get("key", "F")
        scale = session.data.get("scale", "Minor")
        harmonic_guide = (
            f"\n\n💡 **Asistencia Armónica y Teórica (Tonalidad: {key} {scale}):**\n"
            f"• **Rol actual:** `{cur_trk.get('role')}`\n"
            f"• El motor te asiste con la teoría, pero **nunca escribe notas por su cuenta**.\n"
            f"• Puedes:\n"
            f"  1. Dictar acordes o notas explícitas (ej: `'Acordes: {key}m - Db - Eb'` o enviar JSON con `notes`).\n"
            f"  2. Grabar o dibujar las notas directamente en Ableton Live.\n"
            f"  3. Escribir `'vacio'` o `'siguiente'` para dejar los clips preparados en el Arrangement listos para tu interpretación."
        )

        return {
            "status": "AWAITING_TRACK_COMPOSITION",
            "current_step": f"PASO 6 (POR PISTA {trk_idx + 1}/{len(tracks)}): COMPOSICIÓN PARA '{cur_trk.get('name')}'",
            "action_taken": f"Modo interactivo pista por pista activo. Pista actual: {cur_trk.get('name')} (Rol: {cur_trk.get('role')}).",
            "question": (
                f"🎼 **Paso 6: Componiendo Pista {trk_idx + 1} de {len(tracks)}: '{cur_trk.get('name')}' (Rol: `{cur_trk.get('role')}`):**\n\n"
                f"• **Secciones del Arreglo:** {sec_str}\n"
                f"• **Rol Musical:** `{cur_trk.get('role')}`\n"
                f"• **Instrumento:** {cur_trk.get('instrument', cur_trk.get('name'))}\n\n"
                f"⚠️ **Regla Estricta (Cero Relleno Procedural):**\n"
                f"El motor asiste pero **jamás escribe notas o acordes sin tu autorización explícita**.\n"
                f"Define las notas MIDI explícitas únicamente para esta pista, o indica 'vacio' para preparar el clip en blanco en el Arrangement."
                f"{drum_spec_block}"
                f"{harmonic_guide}"
            ),
            "instructions_for_ai": f"Define y envía las notas MIDI explícitas para '{cur_trk.get('name')}' o escribe 'vacio' para dejar el clip preparado en blanco. El motor no autocompletará notas.",
            "phase": "PHASE_6_COMPOSITION",
            "track_index": trk_idx,
            "track_name": cur_trk.get("name"),
            "track_role": cur_trk.get("role")
        }

    @staticmethod
    def prompt_by_clip_step(session: Any, trk_idx: int, sec_idx: int) -> Dict[str, Any]:
        tracks = session.data.get("tracks", [])
        sections = session.data.get("sections", [])
        if trk_idx >= len(tracks):
            return session._prompt_phase_7()

        cur_trk = tracks[trk_idx]
        cur_trk_is_aud = bool(
            cur_trk.get("is_audio", False)
            or str(cur_trk.get("role", "")).upper() == "VOCALS"
            or cur_trk.get("live_recording_mode", False)
        )

        if cur_trk_is_aud:
            return {
                "status": "AWAITING_AUDIO_TRACK_CONFIRMATION",
                "current_step": f"PASO 6 (PISTA {trk_idx + 1}/{len(tracks)}): CANAL AUDIO '{cur_trk.get('name')}'",
                "action_taken": f"Modo Clip por Clip. Canal de Audio/Grabación/FX: {cur_trk.get('name')} (Rol: {cur_trk.get('role')}).",
                "question": (
                    f"🎙️ **Canal de Audio / Grabación / Ruteo FX {trk_idx + 1} de {len(tracks)}: '{cur_trk.get('name')}' (Rol: `{cur_trk.get('role')}`):**\n\n"
                    f"• **Instrumento / Ruteo:** {cur_trk.get('instrument', cur_trk.get('name'))}\n"
                    f"• **Tipo de Pista:** Canal de Audio (Sin clips MIDI requeridos).\n\n"
                    f"Envía 'confirmar' o 'siguiente' para validar el ruteo y avanzar a la siguiente pista."
                ),
                "instructions_for_ai": f"Envía 'confirmar' para validar el canal de audio '{cur_trk.get('name')}'.",
                "phase": "PHASE_6_COMPOSITION",
                "track_index": trk_idx,
                "section_index": sec_idx,
                "track_name": cur_trk.get("name"),
                "track_role": cur_trk.get("role")
            }

        cur_sec = sections[sec_idx] if sec_idx < len(sections) else sections[0]
        s_bars = int(cur_sec.get("bars", 8))
        s_beats = float(s_bars * 4.0)

        drum_spec_block = ""
        role_upper = str(cur_trk.get("role", "")).upper()
        inst_lower = str(cur_trk.get("instrument", "")).lower()
        trk_name_lower = str(cur_trk.get("name", "")).lower()
        if role_upper in ("DRUMS", "KICK") or any(w in inst_lower for w in ["drum", "bater", "kit", "rack"]) or any(w in trk_name_lower for w in ["drum", "bater", "perc"]):
            drum_spec_block = (
                "\n\n🥁 **Especificación Física de Drum Rack (Ableton Live):**\n"
                "• **Octava Inicial Obligatoria:** C1 (MIDI pitch 36).\n"
                "• **Mapa de Pads Estándar:**\n"
                "  - 36 (C1): Bombo / Kick\n"
                "  - 37 (C#1): Aro / Rimshot / Sidestick\n"
                "  - 38 (D1): Caja / Snare acústico\n"
                "  - 39 (D#1): Aplauso / Hand Clap\n"
                "  - 42 (F#1): Hi-Hat cerrado / Shaker\n"
                "  - 46 (A#1): Hi-Hat abierto\n"
                "  - 49 (C#2): Platillo Crash\n"
                "  - 51 (D#2): Platillo Ride\n"
                "⚠️ *Para evitar pads silenciosos en Ableton Live, mapea tus notas a partir de C1 (pitch 36 a 51).*"
            )

        from engine.music.groove.humanizer import DynamicGrooveHumanizer
        key = session.data.get("key", "F")
        scale = session.data.get("scale", "Minor")
        bpm = session.data.get("bpm", 120.0)
        hum_level = session.data.get("humanization_level", 2)
        hum_cfg = DynamicGrooveHumanizer.get_level_config(hum_level)

        # Accumulated clips context across all tracks so far
        accumulated_lines = []
        for i, t in enumerate(tracks):
            t_name = t.get("name", f"Pista {i}")
            t_role = t.get("role", "OTHER")
            secs_done = t.get("sections_completed", [])
            if secs_done:
                done_desc = [f"{s['section_name']} ({'silencio' if s.get('is_silence') else f'{s.get('notes_count', 0)} notas'})" for s in secs_done]
                accumulated_lines.append(f"  • **{t_name}** [{t_role}]: {', '.join(done_desc)}")
            elif i < trk_idx:
                cnt = t.get("notes_count", 0)
                accumulated_lines.append(f"  • **{t_name}** [{t_role}]: {cnt} notas desplegadas")
            elif i == trk_idx:
                accumulated_lines.append(f"  • **{t_name}** [{t_role}]: ⏳ En proceso (Clip {sec_idx + 1}/{len(sections)})")
            else:
                accumulated_lines.append(f"  • **{t_name}** [{t_role}]: Pendiente")
        accumulated_block = "\n".join(accumulated_lines) if accumulated_lines else "  • Ningún clip agregado aún."

        return {
            "status": "AWAITING_CLIP_COMPOSITION",
            "current_step": f"PASO 6 (CLIP {sec_idx + 1}/{len(sections)} - PISTA {trk_idx + 1}/{len(tracks)}): '{cur_trk.get('name')}' EN '{cur_sec.get('name')}'",
            "action_taken": f"Modo Clip por Clip activo. Solicitando notas para Clip #{sec_idx + 1} ({cur_sec.get('name')}, {s_bars} compases).",
            "question": (
                f"🎼 **Componiendo Clip #{sec_idx + 1} de {len(sections)} — Pista {trk_idx + 1}/{len(tracks)}: '{cur_trk.get('name')}' (Rol: `{cur_trk.get('role')}`):**\n\n"
                f"• **Instrumento / Pista:** `{cur_trk.get('name')}` [{cur_trk.get('role')}] ({cur_trk.get('instrument', cur_trk.get('name'))})\n"
                f"• **Sección Perteneciente:** **'{cur_sec.get('name')}'** ({s_bars} compases / {s_beats} tiempos métricos, inicio en compás {cur_sec.get('start_bar', sec_idx * 8)})\n"
                f"• **Tonalidad y Escala del Proyecto:** `{key} {scale}` | Tempo: `{bpm} BPM`\n"
                f"• **Humanización de Groove Activa:** `{hum_cfg['name']}` ({hum_cfg['description']})\n"
                f"  *(Para cambiar nivel de humanización responde 'Humanización: [1-5]')*\n\n"
                f"📋 **Progreso del Arreglo (Clips Agregados Actualmente):**\n"
                f"{accumulated_block}\n\n"
                f"• **Ventana Temporal del Clip:** `start_time` relativo de `0.0` a `{s_beats}` (o motivo de 16 tiempos con auto-tiling)\n\n"
                f"⚠️ **Regla de Oro (Cero Relleno Procedural):**\n"
                f"Define las notas MIDI explícitas (`pitch`, `start_time`, `duration`, `velocity`) **únicamente para este bloque de {s_bars} compases en {key} {scale}**.\n\n"
                "Puedes enviar una lista JSON `[{\"pitch\": X, \"start_time\": Y, ...}]` o un objeto `{\"notes\": [...]}`.\n"
                "Si este canal debe permanecer en silencio durante esta sección, envía `[]` o escribe 'Silencio'.\n"
                "*(Escribe 'Modo: Por Pista' si deseas alternar a composición pista completa).* "
                f"{drum_spec_block}"
            ),
            "instructions_for_ai": f"Define y envía las notas MIDI explícitas para el clip '{cur_sec.get('name')}' ({s_bars} compases) de '{cur_trk.get('name')}' en {key} {scale}.",
            "phase": "PHASE_6_COMPOSITION",
            "track_index": trk_idx,
            "section_index": sec_idx,
            "clip_index": sec_idx + 1,
            "track_name": cur_trk.get("name"),
            "track_role": cur_trk.get("role"),
            "section_name": cur_sec.get("name"),
            "clip_bars": s_bars,
            "clip_beats": s_beats,
            "key": key,
            "scale": scale,
            "humanization_level": hum_level
        }

    @classmethod
    def prompt_phase_6(
        cls,
        session: Any,
        prompt_by_clip_fn: Callable,
        prompt_by_track_fn: Callable
    ) -> Dict[str, Any]:
        tracks = session.data.get("tracks", [])
        sections = session.data.get("sections", [])
        total_bars = session.data.get("total_bars", 96)

        pref_mode = "monolithic"
        try:
            from engine.memory.user_learning import get_user_preferences
            prefs = get_user_preferences()
            pref_mode = prefs.get("composition", {}).get("mode", "by_clip")
        except Exception:
            pass

        if pref_mode in ("by_clip", "clip_by_clip", "clip"):
            session.data["composition_session"] = {
                "active": True,
                "mode": "BY_CLIP",
                "track_index": 0,
                "section_index": 0
            }
            session._save_state()
            return prompt_by_clip_fn(session, 0, 0)

        if pref_mode == "track_by_track":
            session.data["composition_session"] = {
                "active": True,
                "mode": "BY_TRACK",
                "interactive": True,
                "track_index": 0,
                "section_index": 0
            }
            session._save_state()
            return prompt_by_track_fn(session, 0)

        track_lines = [f"• Pista {t.get('index')}: **{t.get('name')}** (Rol: `{t.get('role')}`)" for t in tracks]
        sec_lines = [f"• Sección {i}: **{s.get('name')}** ({s.get('bars')} compases, inicio: c.{s.get('start_bar', i*8)})" for i, s in enumerate(sections)]

        return {
            "current_step": "PASO 6 DE 7: COMPOSICIÓN MODULAR DE NOTAS Y DESPLIEGUE EN ARRANGEMENT",
            "action_taken": "Todos los instrumentos y efectos de inserción fueron configurados y afinados físicamente en Live.",
            "question": (
                "🎼 **Paso 6 de 7: Composición de Notas MIDI y Despliegue en Arrangement**\n\n"
                "**Dotación Instrumental en Live:**\n"
                + "\n".join(track_lines) + "\n\n"
                f"**Estructura del Arreglo ({total_bars} compases totales):**\n"
                + "\n".join(sec_lines) + "\n\n"
                "🧠 **Decisión Técnica Requerida:**\n"
                "⚠️ **Regla de Oro del Motor (Cero Auto-Relleno Procedural):**\n"
                "El motor prohíbe terminantemente autocompletar con notas genéricas o sugerir 'Siguiente' para inventar patrones.\n"
                "La IA debe definir explícitamente las notas MIDI (`pitch`, `start_time`, `duration`, `velocity`) para cada instrumento y sección.\n\n"
                "🧠 **Modalidades de Envío de Notas:**\n"
                "• **Inyección Estructurada Completa (Recomendada)**: Envía un payload JSON con la clave `composition` o `tracks` detallando notas por pista y sección.\n"
                "• **Composición Modular Por Sección**: Escribe 'Por Sección' para definir notas bloque a bloque.\n"
                "• **Composición Modular Por Pista**: Escribe 'Por Pista' para definir notas pista por pista.\n"
                "• **Composición Combinada**: Escribe 'Combinado' para pista y sección específica.\n\n"
                "*Envía el JSON con la tonalidad, escala y notas de tu composición o indica tu modalidad modular para comenzar.*"
            ),
            "instructions_for_ai": "Genera y envía las notas MIDI explícitas para cada pista y sección activa. El motor no autocompletará notas.",
            "phase": "PHASE_6_COMPOSITION"
        }
