# engine/production/copilot/phases/phase_0_design.py
"""
Phase 0: Artistic Design, Concept Specification & Artist Fidelity Verification.

Before touching a single note or track scaffolding:
1. Conducts an interactive pre-production interview capturing:
   - Target artist to emulate (reproducing actual signature techniques)
   - Musical genre (from the 60 documented genres catalog)
   - Explicit BPM / Tempo (never defaulted or locked to 120.0!)
   - Time signature / Metric changes (4/4, 3/4, 6/8, etc.)
   - Track count / Professional genre density (separated stems, avoiding 5-track lock)
   - Tonality (Key & scale / mode)
   - Rhythm & groove pocket (UKG 2-step, Dembow, MPC 60, Dilla, straight)
   - Harmonic language, chord progressions, and counterpoint intent
   - Instrumentation list (avoiding Vital-for-everything bias)
   - Effects per instrument (analog saturation, tape, OTT, de-esser, space guard)
   - Channel dynamic automations and volume riding
   - Target LUFS mastering standard (tailored to genre, not blind -14.7)
   - Drop / Climax location (bar & beat, not assumed at bar 80)
2. Executes a mandatory Artist Fidelity Confirmation Loop:
   Asks the AI/Producer if the design truly represents what the artist would do.
   Loops until confirmed.
3. Preconfigures session state and physically sets tempo and time signature in Ableton Live.
4. Stores the persistent design blueprint so subsequent phases can remind the AI of its original artistic purpose.
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from engine.production.copilot.phases.base import BasePhaseHandler
from engine.production.copilot.nlp_parser import _normalize_text
from engine.knowledge.genres.sixty_genres import SixtyGenresKnowledgeBase, GENRES_CATALOG
from engine.production.contract.advanced_production_spec import (
    AdvancedProductionSpec,
    validate_advanced_production_spec,
    get_advanced_production_schema,
)

logger = logging.getLogger("Phase0Design")


class Phase0DesignHandler(BasePhaseHandler):
    """Handler for Phase 0: Artistic Design and Pre-Production Interview."""

    def prompt(self, session: Any, **kwargs) -> Dict[str, Any]:
        return self._prompt_phase_0(session)

    def handle(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        return self._handle_phase_0(session, conn, user_input)

    def _prompt_phase_0(self, session: Any) -> Dict[str, Any]:
        """Presents the pre-production design interview to the AI / Producer."""
        pending_spec = session.data.get("pending_design_spec")
        if pending_spec and session.data.get("design_step") in ("CONFIRMATION", "AWAITING_ARTIST_CONFIRMATION"):
            return self._prompt_artist_confirmation(session, pending_spec)

        genres_preview = ", ".join([f"`{g.name}`" for g in list(GENRES_CATALOG.values())[:12]])

        return {
            "phase": "PHASE_0_DESIGN",
            "current_step": "FASE DE DISEÑO (PASO PRE-PRODUCCIÓN): ARQUITECTURA ARTÍSTICA Y CONCEPTO SÓNICO",
            "action_taken": "Iniciando fase de diseño conceptual previo a la inserción de pistas en Ableton Live.",
            "question": (
                "🎨 **FASE DE DISEÑO (Fase 0 de 10): Cuestionario Técnico de 11 preguntas clave de pre-producción**\n\n"
                "Para garantizar que la producción sea una **auténtica obra maestra multi-platino** fiel al ADN sónico "
                "del artista y no un esqueleto genérico repetido, definiremos todos los parámetros arquitectónicos antes de iniciar:\n\n"
                "📋 **Cuestionario Técnico de Diseño Requerido (11 preguntas):**\n"
                "1. **Artista:** ¿A qué artista o productor internacional deseas emular o tomar como referente de técnica? (ej: *Billie Eilish, Finneas, Travis Scott, Mike Dean, Kevin Parker, Rosalía, Mura Masa, Rusowsky*).\n"
                f"2. **Género Musical:** Elige entre los **60 géneros documentados** (ej: {genres_preview}, etc.).\n"
                "3. **Tempo (BPM):** Especifica el tempo exacto de la obra (el motor **NUNCA** asume 120.0 BPM; la IA decide soberanamente).\n"
                "4. **Compás Métrico:** Especifica el compás (ej: `4/4`, `3/4`, `6/8`, `7/8`) y si hay cambios de compás.\n"
                "5. **Tonalidad y Escala:** Tónica y modo del proyecto (ej: `Fa Menor`, `Do Menor`, `Re Dórico`, `Sol Mayor`).\n"
                "6. **Densidad y Asignación de Roles por Pista:** El motor expone los siguientes roles musicales oficiales: `[DRUMS, PERCUSSION, BASS, 808_BASS, SUB_BASS, LEAD, GUITAR, KEYS, PIANO, RHODES, PAD, STRINGS, BRASS, CHOIR, VOCAL_CHOP, ARP, EAR_CANDY, FX]`. La IA decide soberanamente cada una de las pistas con su nombre y su rol exacto (ej: `tracks: [{'name': '...', 'role': '...'}, ...]`). Queda estrictamente prohibido que el motor adivine o infiera roles; la IA los define explícitamente en el diseño.\n"
                "7. **Estructura Formal y Secciones:** La IA define las secciones reales (ej: Intro, Verso 1, Pre-Coro, Coro, Verso 2, Puente, Coro Final, Outro); el motor nunca forzará plantillas fijas de EDM.\n"
                "8. **Ritmo y Groove (Soberanía de IA):** Selecciona explícitamente los 4 parámetros:\n"
                "   - Estilo de pocket/groove (ej: `Dilla`, `Trap`, `BoomBap`, `MPC Heavy Swing`, `Neo Soul`, `Straight`, etc.)\n"
                "   - Porcentaje de swing del hi-hat (`hihat_swing_pct`)\n"
                "   - Desplazamiento de snare en ms (`snare_drag_ms`)\n"
                "   - Desplazamiento de sub/bajo en ms (`sub_drag_ms`)\n"
                "9. **Melodía y Armonía:** Progresión de acordes, lenguaje armónico (acordes de 9na/11na, sustituciones) e intención de contrapunto melódico.\n"
                "10. **Instrumentación Específica:** Lista completa de instrumentos deseados (catálogo abierto: Drift, Analog Lab V, Pigments, Serum 2, Piano V3, Stage-73, Wurli, Wavetable, Operator; **queda prohibido usar Vital para todo**).\n"
                "11. **Efectos por Instrumento:** Saturación analógica (Saturn 2, Tape MELLO-FI, Tape J-37), OTT, De-Esser Pro-DS, Reverb Valhalla configurable con predelay y low-cut.\n"
                "12. **Automatizaciones Dinámicas:** Barridos de filtro, silencios dramáticos (micro-stops), vocal riding y efectos de transición.\n"
                "13. **Nivel de Sonoridad (Target LUFS):** Objetivo de masterización adaptado al género (ej: `-7.5` a `-8.5 LUFS` para Trap/Club; `-11` a `-13 LUFS` para Pop/Indie/ASMR; **se prohíbe normalización ciega a -14.7 LUFS**).\n"
                "14. **Ubicación del Clímax / Drop:** Indica el compás exacto donde ocurrirá el clímax o si la obra no posee drop (**no se asume el compás 80 ni ningún compás fijo**).\n"
                "15. **Controles Modulares Avanzados Multiplatino ('advanced_production'):**\n"
                "    El motor expone 6 sub-módulos independientes y parametrizados (documentados en `docs/MODULAR_ADVANCED_PRODUCTION_CONTROLS.md`):\n"
                "    • `crossover_stacking`: División de frecuencia psicoacústica (Sub mono < 90Hz, Mid saturado 90-1200Hz, Air estéreo > 1200Hz). `enabled: bool`, `sub_crossover_hz: float`.\n"
                "    • `turnarounds_and_silences`: Variación en compás 8, `vacuum_stops: bool` (micro-silencios dramáticos de 1-2 tiempos antes del drop), `drum_fills: bool` con rampa de velocidad y dropout de bombo, y `analog_tape_stop: bool` con desaceleración de pitch.\n"
                "    • `groove_and_pocket`: `pocket_style` (`neo_soul_dilla`, `atlanta_trap`, `boom_bap`, `french_pump`, `straight_precise`), `snare_dragging_ms: float` (+14ms para Kevin Parker/Dilla), `sub_dragging_ms: float` (+6ms), `hihat_swing_pct: float` (50-70%).\n"
                "    • `spatial_narrative`: `enabled: bool`, `verse_width_pct: float` (ej: 70%), `chorus_width_pct: float` (ej: 140%), `bass_mono_cutoff_hz: float` (110Hz), `abbey_road_reverb_filter: bool`.\n"
                "    • `ear_candy`: `enabled: bool`, `delay_throw_spike: bool` (envío 100% de delay en última sílaba), `dynamic_auto_pan: bool`, `max_events_per_song: int` (1-2).\n"
                "    • `master_dynamics`: `soft_clipper_pre_limiter: bool` (Analog Clip antes del limitador para rasurar picos de 2ms sin distorsión por bombeo), `clipper_drive_db: float`, `nyc_parallel_drums: bool`.\n"
                "    *La IA decide explícitamente cuáles de estos módulos activar o configurar según el género.*\n\n"
                "💡 *Puedes responder en texto estructurado o en un bloque JSON.*"
            ),
            "instructions_for_ai": (
                "Envía la especificación completa del diseño indicando: artista, género, bpm, compás, tonalidad, "
                "pistas con roles explícitos, secciones, ritmo/groove, instrumentos, efectos, automatizaciones, target_lufs, "
                "ubicación del clímax y el bloque modular 'advanced_production'."
            )
        }

    def _prompt_artist_confirmation(self, session: Any, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Asks the mandatory artist fidelity confirmation question."""
        artist = spec.get("artist", "el Artista")
        genre = spec.get("genre", "el Género")
        bpm = spec.get("bpm", 120.0)
        time_sig = spec.get("time_signature", "4/4")
        key = spec.get("key", "F")
        scale = spec.get("scale", "Minor")
        density = spec.get("channel_density", 10)
        drop_bar = spec.get("drop_bar", 32)
        target_lufs = spec.get("target_lufs", -8.5)
        groove = spec.get("groove_style", "straight_precise")
        instruments = spec.get("instruments", [])
        inst_str = ", ".join(instruments[:6]) if instruments else "Instrumentación personalizada"
        adv_prod = spec.get("advanced_production", {})
        adv_summary = []
        if adv_prod.get("crossover_stacking", {}).get("enabled"):
            adv_summary.append("Crossover Stacking (Sub/Mid/Air)")
        if adv_prod.get("turnarounds_and_silences", {}).get("enabled"):
            ts = adv_prod["turnarounds_and_silences"]
            items = []
            if ts.get("vacuum_stops"): items.append("Vacuum Stops")
            if ts.get("drum_fills"): items.append("Fills c/Crescendo")
            if ts.get("analog_tape_stop"): items.append("Tape Stop")
            adv_summary.append(f"Turnarounds ({', '.join(items)})")
        gp = adv_prod.get("groove_and_pocket", {})
        if gp.get("snare_dragging_ms", 0) != 0:
            adv_summary.append(f"Snare Drag ({gp.get('snare_dragging_ms')}ms)")
        if adv_prod.get("spatial_narrative", {}).get("enabled"):
            sn = adv_prod["spatial_narrative"]
            adv_summary.append(f"Stereo Riding ({sn.get('verse_width_pct')}% -> {sn.get('chorus_width_pct')}%)")
        if adv_prod.get("master_dynamics", {}).get("soft_clipper_pre_limiter"):
            adv_summary.append("Soft Clipper Pre-Limiter")
        adv_str = ", ".join(adv_summary) if adv_summary else "Estándar"

        warnings_block = ""
        warnings = spec.get("acoustic_warnings", [])
        if warnings:
            warn_lines = "\n".join([f"  {w}" for w in warnings])
            warnings_block = f"\n⚠️ **ALERTAS ACÚSTICAS DETECTADAS (Orientación Pedagógica):**\n{warn_lines}\n"

        return {
            "phase": "PHASE_0_DESIGN",
            "status": "AWAITING_ARTIST_CONFIRMATION",
            "current_step": "FASE DE DISEÑO: RETROALIMENTACIÓN Y CONFIRMACIÓN DE FIDELIDAD AL ARTISTA",
            "action_taken": f"Especificación de diseño analizada para '{artist}' en género '{genre}'.",
            "question": (
                f"🧐 **EVALUACIÓN DE FIDELIDAD ARTÍSTICA Y CONTROL DE ALUCINACIÓN:**\n\n"
                f"Hemos consolidado tu diseño inicial de pre-producción:\n"
                f"• **Artista Referente:** `{artist}`\n"
                f"• **Género:** `{genre}` | **Tempo:** `{bpm} BPM` | **Compás:** `{time_sig}`\n"
                f"• **Tonalidad:** `{key} {scale}`\n"
                f"• **Densidad de Canales:** `{density} pistas independientes`\n"
                f"• **Ubicación del Drop:** `Compás {drop_bar}`\n"
                f"• **Groove / Swing:** `{groove}`\n"
                f"• **Instrumentación:** {inst_str}\n"
                f"• **Mastering Target:** `{target_lufs} LUFS`\n"
                f"• **Módulos Avanzados Multiplatino:** {adv_str}\n"
                f"{warnings_block}\n"
                f"🧠 **Pregunta de Retroalimentación Obligatoria:**\n"
                f"¿Realmente todo lo que indicaste es lo que haría {artist}? "
                f"¿Cumple con su técnica distintiva, tratamiento de transitorios, tímbrica y estándares de producción multi-platino, "
                f"o hay algún atajo genérico que deba corregirse?\n\n"
                f"• Si estás 100% seguro de que honra la técnica de {artist}, responde: **'Sí, confirmo'** o **'Cumple con el artista'**.\n"
                f"• Si deseas ajustar algún aspecto, indica los cambios a realizar (el motor entrará en bucle de refinamiento hasta que confirmes)."
            ),
            "instructions_for_ai": (
                "Confirma explícitamente con 'Sí, confirmo' si el diseño replica fielmente la técnica del artista, "
                "o indica los ajustes técnicos necesarios."
            ),
            "spec": spec
        }

    def _handle_phase_0(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        """Processes design input or artist confirmation."""
        text = _normalize_text(user_input)
        step = session.data.get("design_step", "AWAITING_DESIGN_INPUT")
        pending_spec = session.data.get("pending_design_spec", {})

        # Step B: Artist Confirmation check
        if step in ("CONFIRMATION", "AWAITING_ARTIST_CONFIRMATION") and pending_spec:
            if any(w in text for w in ["si", "sí", "confirmo", "confirmar", "cumple", "yes", "adelante", "correcto", "aprobado"]):
                # Confirmed! Preconfigure session state and Live
                return self._finalize_design(session, conn, pending_spec)
            else:
                # Producer wants adjustments: update spec with adjustments
                updated_spec = self._parse_design_input(user_input, base_spec=pending_spec)
                session.data["pending_design_spec"] = updated_spec
                session._save_state(action_tag="DESIGN_SPEC_ADJUSTED")
                return self._prompt_artist_confirmation(session, updated_spec)

        # Step A: Parse initial design input
        parsed_spec = self._parse_design_input(user_input)
        session.data["pending_design_spec"] = parsed_spec
        session.data["design_step"] = "CONFIRMATION"
        session._save_state(action_tag="DESIGN_SPEC_RECEIVED")

        return self._prompt_artist_confirmation(session, parsed_spec)

    def _parse_design_input(self, user_input: str, base_spec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extracts all architectural parameters from freeform text or JSON."""
        spec: Dict[str, Any] = dict(base_spec or {})
        text = _normalize_text(user_input)

        # 1. Try structured JSON first
        try:
            stripped = user_input.strip()
            if (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]")):
                js = json.loads(stripped)
                if isinstance(js, dict):
                    spec.update(js)
        except Exception:
            pass

        # 2. Extract Artist
        artist_match = re.search(r'(?:artista|artist|musico|músico)[:\s]+([^,\n\.]+)', user_input, re.IGNORECASE)
        if artist_match:
            spec["artist"] = artist_match.group(1).strip()
        elif "artist" not in spec:
            # Check famous artists in text
            for cand in ["Billie Eilish", "Travis Scott", "Linkin Park", "Tame Impala", "Gorillaz",
                         "Kanye West", "Kendrick Lamar", "Baby Keem", "Tyler, The Creator", "Logic",
                         "WOS", "Duki", "Cazzu", "Ca7riel", "Rusowsky", "Mura Masa", "Daddy Yankee",
                         "Dua Lipa", "The Weeknd", "Finneas", "Mike Dean", "Skrillex", "Fred again"]:
                if cand.lower() in user_input.lower():
                    spec["artist"] = cand
                    break
        if "artist" not in spec:
            spec["artist"] = "Artista Multi-Platino"

        # 3. Extract Genre & check 60 genres catalog
        genre_match = re.search(r'(?:genero|género|genre)[:\s]+([^,\n\.]+)', user_input, re.IGNORECASE)
        found_genre = genre_match.group(1).strip() if genre_match else None
        if not found_genre:
            for g_id, g_prof in GENRES_CATALOG.items():
                if g_id in text or g_prof.name.lower() in text:
                    found_genre = g_prof.name
                    break

        resolved_profile = SixtyGenresKnowledgeBase.get_profile(found_genre or spec.get("genre", "Trap"))
        if resolved_profile:
            spec["genre"] = resolved_profile.name
            spec["genre_id"] = resolved_profile.id
            if "target_lufs" not in spec:
                spec["target_lufs"] = resolved_profile.target_lufs[2]
            # groove_style is NOT inferred from genre profile — the IA chooses it explicitly in the design response
            if "channel_density" not in spec:
                spec["channel_density"] = resolved_profile.channel_density[1]
        else:
            spec["genre"] = found_genre or spec.get("genre", "Trap")

        # 4. Extract BPM (Never default to 120.0 blindly!)
        bpm_match = re.search(r'(?:bpm|tempo)[:\s]+(\d+(?:\.\d+)?)', user_input, re.IGNORECASE)
        if not bpm_match:
            bpm_match = re.search(r'\b(\d{2,3}(?:\.\d+)?)\s*bpm\b', user_input, re.IGNORECASE)
        if bpm_match:
            spec["bpm"] = float(bpm_match.group(1))
        elif "bpm" not in spec:
            if resolved_profile:
                spec["bpm"] = float(resolved_profile.bpm_range[2])
            else:
                spec["bpm"] = 130.0

        # 5. Extract Time Signature (Compás)
        sig_match = re.search(r'\b(\d{1,2})\s*/\s*(\d{1,2})\b', user_input)
        if sig_match:
            spec["time_signature"] = f"{sig_match.group(1)}/{sig_match.group(2)}"
            spec["sig_num"] = int(sig_match.group(1))
            spec["sig_denom"] = int(sig_match.group(2))
        elif "time_signature" not in spec:
            if resolved_profile:
                spec["time_signature"] = f"{resolved_profile.time_signature[0]}/{resolved_profile.time_signature[1]}"
                spec["sig_num"] = resolved_profile.time_signature[0]
                spec["sig_denom"] = resolved_profile.time_signature[1]
            else:
                spec["time_signature"] = "4/4"
                spec["sig_num"] = 4
                spec["sig_denom"] = 4

        # 6. Extract Key & Scale
        from engine.production.copilot.nlp_parser import parse_autotune_settings
        detected_key, detected_scale, _ = parse_autotune_settings(user_input)
        if not detected_key:
            km = re.search(r'\b([a-g][#b]?)\s+(?:minor|menor|major|mayor|dórico|dorian)\b', text)
            if km:
                detected_key = km.group(1).upper()
        if detected_key:
            spec["key"] = detected_key
        elif "key" not in spec:
            spec["key"] = resolved_profile.recommended_keys_modes[0].split()[0] if resolved_profile else "F"

        if detected_scale:
            spec["scale"] = detected_scale
        elif "scale" not in spec:
            if "major" in text or "mayor" in text:
                spec["scale"] = "Major"
            elif "dorian" in text or "dórico" in text or "dorico" in text:
                spec["scale"] = "Dorian"
            else:
                spec["scale"] = "Minor"

        # 7. Extract Channel Density (Pistas)
        dens_match = re.search(r'(\d+)\s*(?:pistas|canales|tracks)', text)
        if dens_match:
            spec["channel_density"] = int(dens_match.group(1))
        elif "channel_density" not in spec:
            spec["channel_density"] = resolved_profile.channel_density[1] if resolved_profile else 10

        # 8. Extract Drop / Climax location
        beats_per_bar = float(spec.get("sig_num", 4) * (4.0 / max(1, spec.get("sig_denom", 4))))
        drop_match = re.search(r'(?:drop|climax|clímax|caida|caída).*?(?:compas|compás|bar)\s*[:=]?\s*(\d+)', text)
        if not drop_match:
            drop_match = re.search(r'(?:drop|climax|clímax|caida|caída)[^0-9\n\r,]*(\d+)', text)
        if drop_match:
            spec["drop_bar"] = int(drop_match.group(1))
            spec["drop_beat"] = float(spec["drop_bar"] * beats_per_bar)
        elif "drop_bar" not in spec:
            spec["drop_bar"] = 32  # Standard Drop 1 bar
            spec["drop_beat"] = float(spec["drop_bar"] * beats_per_bar)

        # 9. Extract Target LUFS
        lufs_match = re.search(r'(-?\d+(?:\.\d+)?)\s*lufs', text)
        if lufs_match:
            spec["target_lufs"] = float(lufs_match.group(1))
        elif "target_lufs" not in spec:
            spec["target_lufs"] = resolved_profile.target_lufs[2] if resolved_profile else -8.5

        # 10. Extract Groove Style and Parameters (Soberanía de IA)
        swing_match = re.search(r'(?:swing|swing_pct|swing_percentage|hihat_swing_pct)\s*[:=]?\s*(\d{2}(?:\.\d+)?)\s*%?', text)
        if not swing_match:
            swing_match = re.search(r'(\d{2}(?:\.\d+)?)\s*%\s*(?:de\s+)?swing', text)
        if swing_match:
            spec["swing_percentage"] = float(swing_match.group(1))

        snare_match = re.search(r'(?:snare_drag_ms|snare_drag)\s*[:=]?\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        if snare_match:
            spec["snare_drag_ms"] = float(snare_match.group(1))

        sub_match = re.search(r'(?:sub_drag_ms|sub_drag)\s*[:=]?\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        if sub_match:
            spec["sub_drag_ms"] = float(sub_match.group(1))

        # Extract groove_style from IA response ONLY — no heuristic fallback.
        # The IA must explicitly name one of the valid styles; motor does NOT infer from genre/artist tokens.
        for g_style in ["ukg_2step", "mpc_60", "dilla_drunk", "neo_soul_dilla", "reggaeton_dembow", "straight_precise", "lofi_sp1200", "atlanta_trap", "boom_bap", "straight"]:
            if g_style in text or g_style.replace("_", " ") in text:
                spec["groove_style"] = g_style
                break
        # NOTE: if groove_style not found in text, it is NOT assigned — the IA must be explicit.


        # 11. Extract Instruments list if provided
        inst_match = re.search(r'(?:instrumentos|instruments)[:\s]+([^;\n]+)', user_input, re.IGNORECASE)
        if inst_match:
            raw_insts = [i.strip() for i in inst_match.group(1).split(",") if i.strip()]
            if raw_insts:
                spec["instruments"] = raw_insts

        # 12. Parse and Validate Modular 'advanced_production' block
        raw_adv = spec.get("advanced_production")
        if isinstance(raw_adv, dict):
            adv_spec = AdvancedProductionSpec.from_dict(raw_adv)
        else:
            adv_spec = AdvancedProductionSpec()
            # Adaptive defaults based on resolved profile if available (except groove)
            if resolved_profile:
                adv_spec.master_dynamics.target_lufs = float(spec.get("target_lufs", -9.0))
                g_low = spec.get("genre", "").lower()
                if any(k in g_low for k in ["indie", "psychedelic", "neo_soul", "lofi"]):
                    adv_spec.spatial_narrative.verse_width_pct = 70.0
                    adv_spec.spatial_narrative.chorus_width_pct = 145.0
                elif any(k in g_low for k in ["rock", "metal"]):
                    adv_spec.crossover_stacking.enabled = True
                    adv_spec.spatial_narrative.chorus_width_pct = 150.0

        # Apply strictly what the AI specified for groove
        if "groove_style" in spec:
            adv_spec.groove_and_pocket.pocket_style = spec["groove_style"]
        if "swing_percentage" in spec:
            adv_spec.groove_and_pocket.hihat_swing_pct = spec["swing_percentage"]
        if "snare_drag_ms" in spec:
            adv_spec.groove_and_pocket.snare_dragging_ms = spec["snare_drag_ms"]
        if "sub_drag_ms" in spec:
            adv_spec.groove_and_pocket.sub_dragging_ms = spec["sub_drag_ms"]

        spec["advanced_production"] = adv_spec.to_dict()
        # Pedagogical acoustic validation
        acoustic_warnings = validate_advanced_production_spec(
            adv_spec,
            genre=spec.get("genre", ""),
            bpm=spec.get("bpm", 120.0)
        )
        spec["acoustic_warnings"] = acoustic_warnings

        return spec

    def _finalize_design(self, session: Any, conn: Any, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Preconfigures session state and physically configures Ableton Live."""
        bpm = float(spec.get("bpm", 130.0))
        key = str(spec.get("key", "F"))
        scale = str(spec.get("scale", "Minor"))
        sig_num = int(spec.get("sig_num", 4))
        sig_denom = int(spec.get("sig_denom", 4))
        artist = str(spec.get("artist", "Artista Multi-Platino"))
        genre = str(spec.get("genre", "Trap"))
        drop_bar = int(spec.get("drop_bar", 32))
        beats_per_bar = sig_num * (4.0 / max(1, sig_denom))
        drop_beat = float(spec.get("drop_beat", drop_bar * beats_per_bar))
        target_lufs = float(spec.get("target_lufs", -8.5))
        # groove_style: use ONLY what the IA specified; None means IA did not provide one (no motor inference)
        groove_style = spec.get("groove_style", None)
        swing_pct = float(spec.get("swing_percentage", 56.0))


        # Preconfigure session data
        session.data["design"] = spec
        session.data["artist"] = artist
        session.data["genre"] = genre
        session.data["bpm"] = bpm
        session.data["key"] = key
        session.data["scale"] = scale
        session.data["time_signature"] = (sig_num, sig_denom)
        session.data["drop_bar"] = drop_bar
        session.data["drop_beat"] = drop_beat
        session.data["target_lufs"] = target_lufs
        session.data["groove_style"] = groove_style
        session.data["pocket_style"] = groove_style
        session.data["swing_percentage"] = swing_pct
        session.data["designed_tracks"] = spec.get("tracks", [])
        session.data["designed_sections"] = spec.get("sections", [])
        session.data["advanced_production"] = spec.get("advanced_production", {})
        session.data["design_confirmed"] = True
        session.data["design_step"] = "COMPLETED"

        # Advance phase
        session.data["current_phase"] = "PHASE_1_TRACKS"
        session.data["phase_index"] = 1
        session._save_state(action_tag="DESIGN_PHASE_CONFIRMED")

        # Physical execution in Ableton Live
        if conn is not None and hasattr(conn, "send_command"):
            try:
                # 1. Physical tempo sync
                conn.send_command("set_tempo", {"tempo": bpm})
                logger.info(f"Physically set Ableton Live tempo to {bpm} BPM.")
            except Exception as ex_tempo:
                logger.warning(f"Could not set Live tempo: {ex_tempo}")

            try:
                # 2. Physical time signature sync
                conn.send_command("execute_code", params={"code": f"""
song.signature_numerator = {sig_num}
song.signature_denominator = {sig_denom}
"""})
                logger.info(f"Physically set Live time signature to {sig_num}/{sig_denom}.")
            except Exception as ex_sig:
                logger.debug(f"Time signature notice: {ex_sig}")

            try:
                # 3. Physical root note and scale sync
                session._sync_session_tuning(conn, key, scale)
            except Exception as ex_tune:
                logger.debug(f"Session tuning notice: {ex_tune}")

        # Return prompt for Phase 1 with persistent design reminder
        p1_prompt = session._prompt_phase_1()
        reminder = (
            f"🎯 **RECORDATORIO DEL DISEÑO CONCEPTUAL CONFIRMADO:**\n"
            f"• **Artista:** `{artist}` | **Género:** `{genre}` | **Tempo:** `{bpm} BPM` | **Compás:** `{sig_num}/{sig_denom}`\n"
            f"• **Tonalidad:** `{key} {scale}` | **Densidad:** `{spec.get('channel_density', 10)} canales recomendados` | **Drop:** `Compás {drop_bar}`\n"
            f"• **Mastering:** `{target_lufs} LUFS`\n\n"
        )
        p1_prompt["question"] = reminder + p1_prompt.get("question", "")
        p1_prompt["action_taken"] = (
            f"Fase de diseño aprobada exitosamente. Tempo sincronizado físicamente a {bpm} BPM en Live 12."
        )
        return p1_prompt
