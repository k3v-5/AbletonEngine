# engine/production/copilot/phases/phase_6/gatekeepers.py
"""
Phase 6 Gatekeepers:
Enforces mandatory explicit composition, unpopulated MIDI track barriers,
synthesizer outro non-silencing laws, and physical pre-drop vacuum.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("Phase6Gatekeepers")


class Phase6Gatekeepers:
    """Acoustic and workflow safety checks for Phase 6."""

    @staticmethod
    def enforce_pre_drop_vacuum(session: Any, conn: Any) -> None:
        """Enforces physical pre-drop vacuum across all arrangement clips in Live."""
        if conn is not None and hasattr(conn, "send_command"):
            try:
                code_phys_vac = """
for t in song.tracks:
    try:
        clips = list(t.arrangement_clips)
    except Exception:
        continue
    for c in clips:
        if getattr(c, 'is_midi_clip', False):
            for cp in getattr(song, 'cue_points', []):
                cp_nm = str(getattr(cp, 'name', '')).lower()
                cp_t = float(getattr(cp, 'time', 0.0))
                is_drop = False
                for w in ['drop', 'switch', 'climax', 'caida', 'corte']:
                    if w in cp_nm:
                        is_drop = True
                        break
                if is_drop:
                    v_start = max(0.0, cp_t - 2.0)
                    if c.start_time < cp_t and c.end_time > v_start:
                        c.remove_notes_extended(from_time=max(0.0, v_start - c.start_time), from_pitch=0, time_span=max(0.1, cp_t - max(v_start, c.start_time)), pitch_span=128)
"""
                conn.send_command("execute_code", {"code": code_phys_vac})
            except Exception as ex_vac:
                logger.debug(f"Physical vacuum sweep notice: {ex_vac}")

    @staticmethod
    def check_explicit_composition_required(
        session: Any,
        user_input: str,
        has_custom_notes: bool,
        is_explicit_key_directive: bool
    ) -> Optional[Dict[str, Any]]:
        """Blocks advancement if no custom notes or explicit key directive was supplied."""
        if not has_custom_notes and not is_explicit_key_directive:
            return {
                "status": "AWAITING_EXPLICIT_AI_COMPOSITION",
                "phase": "PHASE_6_COMPOSITION",
                "current_step": "FASE 6: COMPOSICIÓN (NOTAS EXPLÍCITAS REQUERIDAS)",
                "action_taken": "Bloqueo estricto del motor: Se prohíbe terminantemente el autocompletado y relleno procedural de notas.",
                "question": (
                    "🚫 **COMPOSICIÓN REQUERIDA (PROHIBIDO AUTO-RELLENO PROCEDURAL):**\n\n"
                    "El motor prohíbe el autocompletado y relleno de notas genéricas procedimentales.\n"
                    "La IA debe definir y suministrar obligatoriamente las notas MIDI explícitas (`pitch`, `start_time`, `duration`, `velocity`) para cada instrumento y sección.\n\n"
                    "Por favor, envía la composición en formato JSON con la clave `composition` o `tracks` detallando las notas para cada pista en el arreglo."
                ),
                "instructions_for_ai": "Genera y envía las notas MIDI explícitas para cada pista y sección activa. El motor no autocompletará notas.",
            }
        return None

    @staticmethod
    def check_unpopulated_midi_tracks(
        session: Any,
        tracks: List[Dict[str, Any]],
        is_explicit_key_directive: bool
    ) -> Optional[Dict[str, Any]]:
        """Blocks transition if an active instrumental MIDI track has zero notes."""
        unpopulated_midi_tracks = []
        for trk in tracks:
            r = str(trk.get("role", "")).upper()
            is_aud = bool(trk.get("is_audio", False) or r == "VOCALS")
            is_live_rec = bool(trk.get("live_recording_mode", False))
            if is_aud or is_live_rec:
                continue
            notes_cnt = trk.get("notes_count", 0)
            if notes_cnt == 0:
                # Check for explicit StructuralDecisionContract declaring intentional silence / tacet
                s_contracts = session.data.get("structural_contracts", {}) if (session and hasattr(session, "data")) else {}
                is_authorized_silence = False
                for c_id, c_data in s_contracts.items():
                    if isinstance(c_data, dict):
                        target = str(c_data.get("target", "")).lower()
                        decision = str(c_data.get("decision", "")).upper()
                        exc_type = str(c_data.get("exception_type", "")).lower()
                        if (target == trk["name"].lower() or target == str(trk.get("index", ""))) and (exc_type == "intentional_silence" or decision in ("REJECT", "TACET")):
                            is_authorized_silence = True
                            logger.info(f"Phase 6 Gatekeeper: Track '{trk['name']}' has 0 notes authorized by structural contract '{c_id}'.")
                            break
                if not is_authorized_silence:
                    logger.warning(f"Phase 6 Gatekeeper: Track '{trk['name']}' has 0 notes across the arrangement.")
                    unpopulated_midi_tracks.append(trk["name"])

        if unpopulated_midi_tracks and not is_explicit_key_directive:
            session._save_state()
            return {
                "status": "PHASE_6_GATEKEEPER_BLOCKED",
                "phase": "PHASE_6_COMPOSITION",
                "current_step": "FASE 6: COMPOSICIÓN (BLOQUEADA POR GATEKEEPER)",
                "action_taken": f"Gatekeeper de Completitud activado: {len(unpopulated_midi_tracks)} pista(s) sin notas ({', '.join(unpopulated_midi_tracks)}).",
                "question": (
                    f"⚠️ **Gatekeeper de Completitud Activado:**\n\n"
                    f"Las siguientes pistas de instrumento carecen de notas MIDI: **{', '.join(unpopulated_midi_tracks)}**.\n"
                    f"El motor prohíbe el autocompletado y relleno procedural. Bloquea la transición a Fase 7 hasta que la IA defina explícitamente las notas MIDI para estas pistas.\n\n"
                    f"Por favor, provee las notas MIDI (`pitch`, `start_time`, `duration`, `velocity`) para las pistas vacías para continuar."
                ),
                "instructions_for_ai": "Genera y envía las notas MIDI explícitas para las pistas vacías indicadas antes de continuar a Fase 7. El motor no autocompletará notas.",
                "unpopulated_tracks": unpopulated_midi_tracks
            }
        return None

    @staticmethod
    def check_silenced_synths_in_outro(
        session: Any,
        tracks: List[Dict[str, Any]],
        sections: List[Dict[str, Any]],
        has_custom_notes: bool,
        custom_notes_map: Dict[Tuple[Any, Any], List[Dict[str, Any]]],
        parser_fn: Any
    ) -> Optional[Dict[str, Any]]:
        """Enforces that synthesizer tracks sustain notes into the Outro section."""
        outro_sec_idx = next((i for i, s in enumerate(sections) if "outro" in str(s.get("name", "")).lower()), None)
        silenced_synths_in_outro = []
        if outro_sec_idx is not None:
            o_sec = sections[outro_sec_idx]
            o_name = o_sec.get("name", "Outro")
            o_bars = int(o_sec.get("bars", 8))
            o_beats = float(o_bars * 4.0)
            for trk in tracks:
                r = str(trk.get("role", "")).upper()
                nm = str(trk.get("name", "")).lower()
                is_aud = bool(trk.get("is_audio", False) or r == "VOCALS" or "vocal" in nm or trk.get("live_recording_mode", False))
                if is_aud:
                    continue
                is_synth = (r in ("LEAD", "SYNTH") or any(k in nm for k in ["synth", "vital", "serum", "saw", "lead"]))
                if is_synth and has_custom_notes:
                    o_notes = parser_fn(
                        session,
                        custom_map=custom_notes_map,
                        trk=trk,
                        s_idx=outro_sec_idx,
                        s_name=o_name,
                        s_beats=o_beats
                    )
                    if not o_notes:
                        silenced_synths_in_outro.append(trk.get("name", f"Pista {trk.get('index')}"))

        if silenced_synths_in_outro:
            session._save_state()
            return {
                "status": "PHASE_6_GATEKEEPER_BLOCKED",
                "phase": "PHASE_6_COMPOSITION",
                "current_step": "FASE 6: COMPOSICIÓN (BLOQUEADA POR GATEKEEPER - SINTETIZADOR EN OUTRO)",
                "action_taken": f"Gatekeeper de Outro activado: el sintetizador no se debe silenciar en el outro ({', '.join(silenced_synths_in_outro)}).",
                "question": (
                    f"⚠️ **Gatekeeper de Outro Activado (Sintetizador no debe silenciarse):**\n\n"
                    f"Las siguientes pistas de sintetizador carecen de notas en la sección Outro: **{', '.join(silenced_synths_in_outro)}**.\n"
                    f"La regla de producción exige terminantemente que el sintetizador no se silencie en el Outro para mantener drones armónicos sostenidos que alimenten el colapso y la saturación final.\n\n"
                    f"Por favor, provee las notas MIDI para el sintetizador en la sección Outro para continuar a Fase 7."
                ),
                "instructions_for_ai": "Genera y envía las notas MIDI explícitas (drones armónicos sostenidos) para el sintetizador en el Outro. El motor prohíbe silenciar el sintetizador en el outro.",
                "silenced_synth_tracks": silenced_synths_in_outro
            }
        return None

    @staticmethod
    def check_section_contrast(
        session: Any,
        sections: List[Dict[str, Any]],
        custom_notes_map: Optional[Dict[Tuple[Any, Any], List[Dict[str, Any]]]] = None,
        is_test_env: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Audita el contraste dinámico y de densidad entre secciones contiguas (ej: Verse -> Chorus).
        Si el contraste es inferior a 0.20 y se trata de secciones contrastantes, bloquea el avance
        para evitar loops estáticos planos.
        """
        if is_test_env or not custom_notes_map or len(sections) < 2:
            return None

        # Comparar pares de secciones contiguas
        for i in range(len(sections) - 1):
            s1 = sections[i]
            s2 = sections[i + 1]
            n1 = str(s1.get("name", "")).lower()
            n2 = str(s2.get("name", "")).lower()

            # Contrastar solo transiciones dinámicas (ej: verse -> chorus / build -> drop)
            should_contrast = (
                ("verse" in n1 and "chorus" in n2) or
                ("build" in n1 and "drop" in n2) or
                ("intro" in n1 and "drop" in n2) or
                ("break" in n1 and "drop" in n2)
            )
            if not should_contrast:
                continue

            # Contar notas por sección
            notes_s1 = sum(len(notes) for (t_idx, s_idx), notes in custom_notes_map.items() if s_idx == i)
            notes_s2 = sum(len(notes) for (t_idx, s_idx), notes in custom_notes_map.items() if s_idx == (i + 1))

            tot = max(1, notes_s1 + notes_s2)
            contrast_metric = abs(notes_s2 - notes_s1) / tot

            if contrast_metric < 0.20 and notes_s1 > 0 and notes_s2 > 0:
                logger.warning(f"Phase 6 Creative Gatekeeper: Low contrast ({contrast_metric:.2f} < 0.20) between '{s1['name']}' and '{s2['name']}'.")
                return {
                    "status": "CREATIVE_DEVELOPMENT_BLOCKED",
                    "phase": "PHASE_6_COMPOSITION",
                    "current_step": f"FASE 6: GOBERNANZA CREATIVA (CONTRASTE INSUFICIENTE ENTRE '{s1['name']}' Y '{s2['name']}')",
                    "action_taken": f"Bloqueo de desarrollo creativo: El contraste de notas ({contrast_metric:.2f}) es menor al estándar mínimo (0.20). Se detectó un loop plano sin dinamismo de arreglo.",
                    "question": (
                        f"⚠️ **ALERTA DE GOBERNANZA CREATIVA: ARREGLO PLANO DETECTADO**\n\n"
                        f"La transición entre **{s1['name']}** ({notes_s1} notas) y **{s2['name']}** ({notes_s2} notas) presenta un contraste de densidad de solo `{contrast_metric:.2f}` (mínimo exigido: `0.20`).\n\n"
                        f"Un arreglo comercial requiere diferenciación dinámica entre secciones de preparación y secciones de clímax.\n\n"
                        f"🛠️ **Intervenciones Creativas Recomendadas:**\n"
                        f"  1. **Vaciar elementos rítmicos en {s1['name']}** (eliminar hi-hats o bajos para que el impacto de {s2['name']} sea masivo).\n"
                        f"  2. **Duplicar densidad o salto de octava en {s2['name']}** (añadir arpegios, contramelodías o capas de sintetizador).\n"
                        f"  3. **Inyectar silencio / pre-drop vacuum** en los últimos 2 compases de {s1['name']}.\n\n"
                        f"*Envía una composición revisada con mayor contraste para continuar.*"
                    ),
                    "instructions_for_ai": "Incrementa el contraste de notas y densidad entre las secciones indicadas para superar la compuerta de desarrollo creativo.",
                    "contrast_metric": round(contrast_metric, 3)
                }
        return None

    @staticmethod
    def check_second_drop_transformation(
        session: Any,
        sections: List[Dict[str, Any]],
        custom_notes_map: Optional[Dict[Tuple[Any, Any], List[Dict[str, Any]]]] = None,
        is_test_env: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Audita que el segundo drop (Drop 2 / Chorus 2) presente mutación o evolución respecto al primero.
        Si ambos drops son 100% idénticos en notas y densidad, exige variación.
        """
        if is_test_env or not custom_notes_map:
            return None

        drop_indices = [
            i for i, s in enumerate(sections)
            if any(w in str(s.get("name", "")).lower() for w in ["drop", "chorus", "estribillo", "climax"])
        ]
        if len(drop_indices) < 2:
            return None

        d1_idx = drop_indices[0]
        d2_idx = drop_indices[1]

        notes_d1 = sum(len(notes) for (t_idx, s_idx), notes in custom_notes_map.items() if s_idx == d1_idx)
        notes_d2 = sum(len(notes) for (t_idx, s_idx), notes in custom_notes_map.items() if s_idx == d2_idx)

        # Si tienen exactamente el mismo número de notas y distribución
        if notes_d1 > 0 and notes_d1 == notes_d2:
            # Check if artist explicitly contracted to preserve identical drop (e.g., hypnotic techno / minimalism)
            s_contracts = session.data.get("structural_contracts", {}) if (session and hasattr(session, "data")) else {}
            for c_id, c_data in s_contracts.items():
                if isinstance(c_data, dict):
                    target = str(c_data.get("target", "")).lower()
                    decision = str(c_data.get("decision", "")).upper()
                    if ("drop" in target or target in ("drop_2", "second_drop")) and (decision in ("REJECT", "REJECTED_BY_ARTIST", "MAINTAIN")):
                        logger.info(f"Phase 6 Gatekeeper: Drop 2 identical repetition authorized by structural contract '{c_id}'.")
                        return None

            # Comprobar si las notas son idénticas
            d1_pitches = [n.get("pitch") for (t, s), nl in custom_notes_map.items() if s == d1_idx for n in nl]
            d2_pitches = [n.get("pitch") for (t, s), nl in custom_notes_map.items() if s == d2_idx for n in nl]
            if d1_pitches == d2_pitches:
                logger.warning(f"Phase 6 Creative Gatekeeper: Drop 2 (Sec {d2_idx}) is an exact copy-paste of Drop 1 (Sec {d1_idx}).")
                return {
                    "status": "CREATIVE_DEVELOPMENT_BLOCKED",
                    "phase": "PHASE_6_COMPOSITION",
                    "current_step": "FASE 6: GOBERNANZA CREATIVA (DROP 2 IDÉNTICO A DROP 1)",
                    "action_taken": "Bloqueo de desarrollo creativo: El segundo drop es una copia idéntica del primero. La producción profesional exige mutación.",
                    "question": (
                        f"⚠️ **ALERTA DE GOBERNANZA CREATIVA: MUTACIÓN REQUERIDA EN SEGUNDO DROP**\n\n"
                        f"El segundo Drop (**{sections[d2_idx]['name']}**) es idéntico nota por nota al primer Drop (**{sections[d1_idx]['name']}**).\n"
                        f"En la música comercial contemporánea, el segundo clímax debe elevar la energía o introducir un giro rítmico/melódico (Drop Mutation Engine).\n\n"
                        f"🛠️ **Aplica una de las siguientes mutaciones al segundo drop:**\n"
                        f"  • Variación rítmica del bajo / 808 (sincopa o ritmo doble tiempo).\n"
                        f"  • Variación melódica del lead (añadir adornos, arpegios o salto de octava).\n"
                        f"  • Agregar contramelodía o percusión sincopada adicional.\n\n"
                        f"*Envía notas con variación para el segundo drop para continuar.*"
                    ),
                    "instructions_for_ai": "Modifica las notas del segundo drop para incorporar mutación rítmica, melódica o tímbrica respecto al primer drop.",
                    "drop_indices": [d1_idx, d2_idx]
                }
        return None

    @staticmethod
    def check_every_track_has_sound(
        session: Any,
        tracks: List[Dict[str, Any]],
        sections: List[Dict[str, Any]],
        custom_notes_map: Optional[Dict[Tuple[Any, Any], List[Dict[str, Any]]]] = None,
        is_test_env: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Enforces that EVERY registered track (MIDI and Audio) must have sound / notes
        in AT LEAST ONE section across the entire arrangement.
        
        Permits Tacet / silence in individual sections (e.g. verse or intro),
        but blocks progression if a track is 100% silent across the entire song.
        """
        if is_test_env:
            return None

        totally_silent_tracks = []
        for trk in tracks:
            t_idx = trk.get("index", 0)
            t_name = trk.get("name", f"Track {t_idx}")
            r = str(trk.get("role", "")).upper()
            is_aud = bool(trk.get("is_audio", False) or r == "VOCALS")
            is_fx_aud = trk.get("is_fx_audio", False) or r == "FX"
            is_live_rec = bool(trk.get("live_recording_mode", False))

            if is_fx_aud:
                continue

            has_sound = False

            if trk.get("notes_count", 0) > 0:
                has_sound = True

            if not has_sound and custom_notes_map:
                for (t_key, s_key), notes_list in custom_notes_map.items():
                    if (t_key == t_idx or str(t_key) == str(t_idx) or str(t_key).lower() == t_name.lower()) and len(notes_list) > 0:
                        has_sound = True
                        break

            if not has_sound:
                c_notes = session.data.get("custom_notes", {})
                for k, v in c_notes.items():
                    if (str(t_idx) in str(k) or t_name.lower() in str(k).lower()) and (isinstance(v, list) and len(v) > 0):
                        has_sound = True
                        break

            if not has_sound and is_aud:
                if is_live_rec or trk.get("sample_path") or trk.get("sample_loaded") or trk.get("chopping_mode"):
                    has_sound = True

            if not has_sound:
                # Check for explicit StructuralDecisionContract declaring intentional silence / tacet
                s_contracts = session.data.get("structural_contracts", {}) if (session and hasattr(session, "data")) else {}
                for c_id, c_data in s_contracts.items():
                    if isinstance(c_data, dict):
                        target = str(c_data.get("target", "")).lower()
                        decision = str(c_data.get("decision", "")).upper()
                        exc_type = str(c_data.get("exception_type", "")).lower()
                        if (target == t_name.lower() or target == str(t_idx)) and (exc_type == "intentional_silence" or decision in ("REJECT", "TACET")):
                            has_sound = True
                            logger.info(f"Phase 6 Gatekeeper: Track '{t_name}' total silence authorized by structural contract '{c_id}'.")
                            break

            if not has_sound:
                totally_silent_tracks.append((t_name, r, t_idx))

        if totally_silent_tracks:
            silent_names = [f"'{n}' ({r})" for n, r, _ in totally_silent_tracks]
            session._save_state()
            return {
                "status": "TRACK_COMPLETELY_SILENT_ERROR",
                "phase": "PHASE_6_COMPOSITION",
                "current_step": "FASE 6: COMPOSICIÓN (PISTAS SIN SONIDO DETECTADAS)",
                "action_taken": f"Bloqueo de orquestación: {len(totally_silent_tracks)} pista(s) no tienen sonido en ninguna sección ({', '.join(silent_names)}).",
                "question": (
                    f"⚠️ **Gatekeeper de Orquestación: Pistas Completamente Mudas**\n\n"
                    f"Las siguientes pistas carecen de sonido o notas MIDI durante **el 100% de la canción**:\n"
                    f"• {', '.join(silent_names)}\n\n"
                    f"El motor permite y respeta que un instrumento descanse en ciertas secciones (*Tacet* orquestal), "
                    f"pero **cada pista registrada debe sonar al menos en una sección** del arreglo para evitar pistas huérfanas o abandono por ahorro de tokens.\n\n"
                    f"🧠 **Acción Requerida:**\n"
                    f"1. Define notas o eventos de sonido para al menos una sección en las pistas mudas.\n"
                    f"2. O indica 'eliminar pista [nombre]' si decides prescindir de ella en este arreglo."
                ),
                "instructions_for_ai": "Genera notas para al menos una sección en las pistas mudas indicadas o solicita removerlas.",
                "totally_silent_tracks": [n for n, _, _ in totally_silent_tracks]
            }

        return None

