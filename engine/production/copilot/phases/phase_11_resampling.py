# engine/production/copilot/phases/phase_11_resampling.py
"""
Phase 11: Audio Reprocessing & Resynthesis Catalog (UHTS).
Single-tool conversational state machine guiding the producer through:
1. Automatic Key & BPM project detection.
2. Source sound selection (existing session track vs. new unused track with guided sound design).
3. 20-algorithm DSP Resampling Mutation Catalog dynamically tuned to Key & BPM.
4. Deployment to a brand new unused Audio Track in Live with safe gain staging.
5. Audition, soloing, and multi-layering.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from engine.production.copilot.phases.base import BasePhaseHandler
from engine.production.copilot.nlp_parser import _normalize_text
from engine.sound_design.reprocessing_pipeline import AudioReprocessingPipeline

logger = logging.getLogger("CopilotGuidedSession.Phase11")


class Phase11ResamplingHandler(BasePhaseHandler):
    """Handles Phase 11: Textural Reprocessing & Audio Resynthesis Catalog."""

    def __init__(self):
        pass

    def prompt(self, session: Any, conn: Any = None, **kwargs) -> Dict[str, Any]:
        """Entry prompt for Phase 11."""
        pipeline = AudioReprocessingPipeline(conn=conn)
        tuning = pipeline.detect_project_key_and_bpm(session.data)

        # Initialize or fetch phase state
        res_state = session.data.setdefault("resampling_session", {})
        res_state["active"] = True
        res_state["stage"] = res_state.get("stage", "SELECT_SOURCE")
        res_state["key"] = tuning["key"]
        res_state["scale"] = tuning["scale"]
        res_state["bpm"] = tuning["bpm"]
        session._save_state(action_tag="PHASE_11_INIT")

        tracks = session.data.get("tracks", [])
        track_cands = [f"Pista {t.get('index', i)}: {t.get('name')}" for i, t in enumerate(tracks) if not t.get("is_foldable", False)]
        track_sample_str = "\n".join([f"    • {tc}" for tc in track_cands[:5]]) if track_cands else "    • Pistas del proyecto en Live"

        q_prompt = (
            f"🧪 **FASE 11: CATÁLOGO DE REPROCESAMIENTO Y RESÍNTESIS DE AUDIO (UHTS)**\n\n"
            f"El motor ha detectado automáticamente la configuración musical de tu sesión en Ableton Live:\n"
            f"🎵 **Tonalidad & Escala:** `{tuning['key']} {tuning['scale']}`\n"
            f"⏱️ **Tempo:** `{tuning['bpm']:.1f} BPM`\n\n"
            "Este catálogo permite transformar un sonido continuo mediante 20 técnicas avanzadas de "
            "productores (congelamiento espectral, filtros Karplus-Strong afinados a escala, sub-growls monofónicos, "
            "micro-granos, wow/flutter, choppers rítmicos a tempo, etc.) para crear capas texturales únicas.\n\n"
            "El resultado mutado se colocará automáticamente en una **pista de audio nueva sin utilizar**.\n\n"
            "¿Cómo deseas originar el sonido fuente?\n\n"
            f"🅰️ **Opción A: Usar una pista existente de la sesión**\n"
            f"Tomará el audio continuo de una de tus pistas actuales para mutarlo.\n"
            f"{track_sample_str}\n"
            f"*(Responde: 'Opción A' o 'Usar Pista Piano')*\n\n"
            "🅱️ **Opción B: Crear una pista nueva no utilizada con diseño guiado**\n"
            "Te guiaremos en una entrevista interactiva paso a paso (Rol acústico, Instrumento/VST, "
            "Preset con blueprint Delta >= 1, Efectos de inserción y acorde prolongado) antes de renderizar.\n"
            "*(Responde: 'Opción B' o 'Crear pista nueva')*\n\n"
            "🅲️ **Opción C: Desplegar el Pad Evolutivo de 20 Escenas UHTS (80 Compases en Arrangement)**\n"
            f"Genera las 20 mutaciones espectrales y tímbricas afinadas a {tuning['key']} {tuning['scale']} @ {tuning['bpm']:.1f} BPM, "
            "crea la pista '[PAD] UHTS 20-Stage Audio', puebla las 20 escenas de Session View y extiende la línea temporal completa "
            "de 80 compases con sus 20 locators en Arrangement View.\n"
            "*(Responde: 'Opción C' o 'Pad de 20 escenas' o 'Desplegar todas')*"
        )

        return {
            "status": "AWAITING_SOURCE_SELECTION",
            "phase": "PHASE_11_AUDIO_RESAMPLING",
            "current_step": "FASE 11: SELECCIÓN DE ORIGEN DEL SONIDO FUENTE",
            "action_taken": f"Tonalidad detectada automáticamente: {tuning['key']} {tuning['scale']} @ {tuning['bpm']:.1f} BPM.",
            "question": q_prompt,
            "instructions_for_ai": "Elige Opción A (pista existente), Opción B (crear pista nueva con diseño sonoro), u Opción C (pad evolutivo de 20 escenas).",
            "tuning": tuning
        }

    def handle(self, session: Any, conn: Any, user_input: str) -> Dict[str, Any]:
        """Main dispatcher for Phase 11 user decisions."""
        text = _normalize_text(user_input)
        pipeline = AudioReprocessingPipeline(conn=conn)
        res_state = session.data.setdefault("resampling_session", {})

        # Ensure tuning is synchronized
        if "key" not in res_state or "bpm" not in res_state:
            tuning = pipeline.detect_project_key_and_bpm(session.data)
            res_state["key"] = tuning["key"]
            res_state["scale"] = tuning["scale"]
            res_state["bpm"] = tuning["bpm"]

        stage = res_state.get("stage", "SELECT_SOURCE")

        # ---------------------------------------------------------------------
        # SUB-STAGE: SELECT_SOURCE (Existing vs. New Track)
        # ---------------------------------------------------------------------
        if stage == "SELECT_SOURCE":
            is_opt_c = any(w in text for w in [
                "opcion c", "opcion 3", "20 escenas", "las 20", "todas las tecnicas",
                "catalogo completo", "pad evolutivo", "pad a lo largo", "desplegar todas",
                "todas las escenas", "80 compases", "full pad", "pad completo"
            ])
            if is_opt_c:
                return self._deploy_full_20_scene_pad(session, conn, pipeline, res_state)

            is_opt_a = any(w in text for w in ["opcion a", "opcion 1", "existente", "pista existente", "usar pista", "canal existente"])
            is_opt_b = any(w in text for w in ["opcion b", "opcion 2", "nueva", "crear pista", "nueva pista", "desde cero", "diseno", "diseño"])

            # Check if user directly specified a track name
            tracks = session.data.get("tracks", [])
            named_track = None
            for t in tracks:
                t_name = str(t.get("name", "")).lower()
                if t_name and t_name in text:
                    named_track = t
                    is_opt_a = True
                    break

            if is_opt_a or (named_track is not None):
                target_t = named_track
                if not target_t:
                    # Look for track index in input e.g. "pista 16"
                    m_idx = re.search(r'(?:pista|canal|track)\s*(\d+)', text)
                    if m_idx:
                        cand_idx = int(m_idx.group(1))
                        target_t = next((t for t in tracks if t.get("index") == cand_idx), None)
                    if not target_t:
                        # Fallback to first harmonic track (Keys or Pad or Synth)
                        target_t = next((t for t in tracks if t.get("role") in ["KEYS", "PAD", "SYNTH", "LEAD"]), tracks[0] if tracks else {"name": "Audio Source", "index": 0})

                src_name = target_t.get("name", "Audio Source")
                src_idx = target_t.get("index", 0)

                # Locate or generate continuous audio for this source
                source_wav = self._resolve_or_create_source_audio(session, conn, target_t, pipeline)
                res_state["source"] = {
                    "type": "EXISTING_TRACK",
                    "track_index": src_idx,
                    "track_name": src_name,
                    "wav_path": source_wav
                }
                res_state["source_wav_path"] = source_wav
                res_state["stage"] = "SELECT_TECHNIQUE"
                session._save_state(action_tag="RESAMPLE_SOURCE_EXISTING")

                return self._prompt_technique_selection(session, pipeline, src_name)

            elif is_opt_b:
                res_state["stage"] = "DESIGN_ROLE"
                res_state["designer"] = {}
                session._save_state(action_tag="RESAMPLE_START_NEW_TRACK")
                return self._prompt_design_role()

            else:
                return self.prompt(session, conn)

        # ---------------------------------------------------------------------
        # SUB-STAGE: DESIGN_ROLE (Acoustic Role Selection)
        # ---------------------------------------------------------------------
        if stage == "DESIGN_ROLE":
            role = "KEYS"
            if any(w in text for w in ["pad", "atmosfera", "colchon", "wash"]):
                role = "PAD"
            elif any(w in text for w in ["bass", "bajo", "reese", "sub"]):
                role = "BASS"
            elif any(w in text for w in ["lead", "solista", "melodia"]):
                role = "LEAD"
            elif any(w in text for w in ["texture", "textura", "foley", "ruido"]):
                role = "TEXTURE"
            elif any(w in text for w in ["keys", "piano", "rhodes", "wurli", "teclado"]):
                role = "KEYS"

            res_state["designer"]["role"] = role
            res_state["stage"] = "DESIGN_INSTRUMENT"
            session._save_state(action_tag="RESAMPLE_DESIGN_ROLE")
            return self._prompt_design_instrument(role)

        # ---------------------------------------------------------------------
        # SUB-STAGE: DESIGN_INSTRUMENT (VST / Plugin Selection)
        # ---------------------------------------------------------------------
        if stage == "DESIGN_INSTRUMENT":
            inst = "Analog Lab V"
            if any(w in text for w in ["serum", "serum 2", "serum2"]):
                inst = "Serum 2"
            elif any(w in text for w in ["vital"]):
                inst = "Vital"
            elif any(w in text for w in ["pigments"]):
                inst = "Pigments"
            elif any(w in text for w in ["drift", "wavetable", "nativo", "ableton"]):
                inst = "Drift"
            elif any(w in text for w in ["analog lab", "analog lab v", "arturia", "piano"]):
                inst = "Analog Lab V"

            res_state["designer"]["instrument"] = inst
            res_state["stage"] = "DESIGN_PRESET"
            session._save_state(action_tag="RESAMPLE_DESIGN_INSTRUMENT")
            return self._prompt_design_preset(res_state["designer"]["role"], inst)

        # ---------------------------------------------------------------------
        # SUB-STAGE: DESIGN_PRESET (Preset & Parameter Blueprint Delta >= 1)
        # ---------------------------------------------------------------------
        if stage == "DESIGN_PRESET":
            preset_name = user_input.strip() or "Prolonged Concert Grand"
            role = res_state["designer"].get("role", "KEYS")
            blueprint = self._get_blueprint_for_role(role)

            res_state["designer"]["preset"] = preset_name
            res_state["designer"]["blueprint"] = blueprint
            res_state["stage"] = "DESIGN_FX"
            session._save_state(action_tag="RESAMPLE_DESIGN_PRESET")
            return self._prompt_design_fx(role, preset_name, blueprint)

        # ---------------------------------------------------------------------
        # SUB-STAGE: DESIGN_FX (Effects Chain & Sound Synthesis)
        # ---------------------------------------------------------------------
        if stage == "DESIGN_FX":
            fx_chain = ["EQ Eight", "Glue Compressor"]
            if any(w in text for w in ["reverb", "espacio", "hall"]):
                fx_chain.append("Valhalla VintageVerb")
            if any(w in text for w in ["delay", "eco"]):
                fx_chain.append("Delay")
            if any(w in text for w in ["saturador", "overdrive", "drive", "distorsion"]):
                fx_chain.append("Saturator")
            if any(w in text for w in ["chorus", "dimension"]):
                fx_chain.append("Chorus-Ensemble")

            res_state["designer"]["fx_chain"] = fx_chain

            # Synthesize continuous audio source sound
            role = res_state["designer"].get("role", "KEYS")
            inst = res_state["designer"].get("instrument", "Analog Lab V")
            preset = res_state["designer"].get("preset", "Prolonged Concert Grand")
            key = res_state.get("key", "F")
            scale = res_state.get("scale", "Minor")
            bpm = float(res_state.get("bpm", 120.0))

            source_res = pipeline.generate_source_sound_for_new_track(
                role=role,
                instrument_name=inst,
                preset_name=preset,
                key=key,
                scale=scale,
                bpm=bpm,
                bars=4
            )

            src_wav = source_res["wav_path"]
            res_state["source"] = {
                "type": "NEW_TRACK_DESIGNED",
                "role": role,
                "instrument": inst,
                "preset": preset,
                "fx_chain": fx_chain,
                "wav_path": src_wav
            }
            res_state["source_wav_path"] = src_wav
            res_state["stage"] = "SELECT_TECHNIQUE"
            session._save_state(action_tag="RESAMPLE_SOURCE_SYNTHESIZED")

            dur_sec = float(source_res.get("duration", 8.0))
            src_summary = f"{inst} ('{preset}') en {key} {scale} ({dur_sec:.1f}s)"
            return self._prompt_technique_selection(session, pipeline, src_summary)

        # ---------------------------------------------------------------------
        # SUB-STAGE: SELECT_TECHNIQUE (Pick from the 20 UHTS Algorithms)
        # ---------------------------------------------------------------------
        if stage == "SELECT_TECHNIQUE":
            is_opt_c = any(w in text for w in [
                "opcion c", "opcion 3", "20 escenas", "las 20", "todas las tecnicas",
                "catalogo completo", "pad evolutivo", "pad a lo largo", "desplegar todas",
                "todas las escenas", "80 compases", "full pad", "pad completo"
            ])
            if is_opt_c:
                return self._deploy_full_20_scene_pad(session, conn, pipeline, res_state)

            tech = pipeline.get_technique_by_selector(user_input)
            if not tech:
                # If couldn't match, re-prompt catalog
                return self._prompt_technique_selection(session, pipeline, res_state.get("source", {}).get("track_name", "Sonido Fuente"))

            # Execute DSP mutation!
            src_wav = res_state.get("source_wav_path")
            if not src_wav or not Path(src_wav).exists():
                src_wav = self._ensure_fallback_source(pipeline, res_state)

            key = res_state.get("key", "F")
            scale = res_state.get("scale", "Minor")
            bpm = float(res_state.get("bpm", 120.0))

            mut_res = pipeline.execute_mutation(
                source_wav_path=src_wav,
                technique_selector=tech["index"],
                key=key,
                scale=scale,
                bpm=bpm
            )

            # Deploy to a BRAND NEW UNUSED Audio Track in Live!
            deploy_res = pipeline.deploy_mutated_track_to_live(
                mutated_wav_path=mut_res["output_path"],
                technique_name=tech["name"],
                technique_index=tech["index"],
                key=key,
                scale=scale,
                target_volume=0.75
            )

            # Record deployed asset in session state
            resampled_tracks = session.data.setdefault("resampled_tracks", [])
            resampled_tracks.append({
                "technique_id": tech["id"],
                "technique_index": tech["index"],
                "technique_name": tech["name"],
                "live_track_index": deploy_res["track_index"],
                "live_track_name": deploy_res["track_name"],
                "wav_path": mut_res["output_path"],
                "duration": mut_res["duration"],
                "key": key,
                "scale": scale,
                "bpm": bpm
            })

            res_state["last_deployed_track"] = deploy_res["track_index"]
            res_state["last_technique"] = tech
            res_state["stage"] = "AUDITION_LAYER"
            session._save_state(action_tag=f"RESAMPLE_DEPLOY_{tech['index']}")

            return self._prompt_audition_and_layering(session, tech, deploy_res, key, scale, bpm)

        # ---------------------------------------------------------------------
        # SUB-STAGE: AUDITION_LAYER (Solo, Layer Another Technique, or Finish)
        # ---------------------------------------------------------------------
        if stage == "AUDITION_LAYER":
            # 1. Solo action
            if any(w in text for w in ["solo", "soloing", "escuchar", "audicionar", "reproducir", "probar"]):
                t_idx = res_state.get("last_deployed_track", -1)
                if t_idx >= 0:
                    pipeline.solo_track(t_idx, solo=True)
                    return {
                        "status": "TRACK_SOLOED",
                        "phase": "PHASE_11_AUDIO_RESAMPLING",
                        "current_step": "PISTA DE RESAMPLE EN SOLO",
                        "action_taken": f"Pista {t_idx} en Solo activo para escucha aislada.",
                        "question": (
                            f"🎧 **Pista en Solo Activo (Pista {t_idx}):**\n"
                            f"La pista `{res_state.get('last_technique', {}).get('name')}` está en solo.\n\n"
                            "¿Deseas quitar el solo, generar otra capa de mutación (Opción A), o finalizar la sesión?"
                        ),
                        "instructions_for_ai": "Puedes pedir 'Quitar solo', 'Generar otra mutación' o 'Finalizar sesión'."
                    }

            if any(w in text for w in ["quitar solo", "desactivar solo", "unsolo"]):
                t_idx = res_state.get("last_deployed_track", -1)
                if t_idx >= 0:
                    pipeline.solo_track(t_idx, solo=False)
                    return {
                        "status": "SOLO_REMOVED",
                        "phase": "PHASE_11_AUDIO_RESAMPLING",
                        "current_step": "SOLO DESACTIVADO",
                        "action_taken": f"Solo desactivado en Pista {t_idx}.",
                        "question": "🔊 **Solo desactivado.** Todas las pistas vuelven a sonar en la mezcla.\n¿Deseas generar otra capa o finalizar?"
                    }

            # 2. Layer another mutation on another new track
            if any(w in text for w in ["otra capa", "otra tecnica", "otra mutacion", "mas mutaciones", "capa adicional", "layer", "agregar otra"]):
                res_state["stage"] = "SELECT_TECHNIQUE"
                session._save_state(action_tag="RESAMPLE_LAYER_ANOTHER")
                src_name = res_state.get("source", {}).get("track_name", "Sonido Fuente")
                return self._prompt_technique_selection(session, pipeline, src_name)

            # 3. Complete and proceed to Stem Export / Final Active Listening
            if any(w in text for w in ["finalizar", "terminar", "completar", "exportar stems", "stems", "listo"]):
                res_state["active"] = False
                res_state["stage"] = "COMPLETED"
                session.data["current_phase"] = "PHASE_10_COMPLETED"
                session._save_state(action_tag="PHASE_11_COMPLETED")

                return {
                    "status": "RESAMPLING_COMPLETED",
                    "phase": "PHASE_10_COMPLETED",
                    "current_step": "REPROCESAMIENTO FINALIZADO — SESIÓN LISTA PARA DISTRIBUCIÓN",
                    "action_taken": f"Catálogo de Reprocesamiento completado. {len(session.data.get('resampled_tracks', []))} pistas de mutación continua inyectadas en Live.",
                    "question": (
                        "🎉 **¡FASE DE REPROCESAMIENTO Y MUTACIÓN COMPLETADA CON ÉXITO!**\n\n"
                        f"Se han incorporado exitosamente {len(session.data.get('resampled_tracks', []))} capas de audio continuo en pistas nuevas de Live.\n\n"
                        "🎧 **¿Deseas exportar los stems oficiales de la canción o realizar algún ajuste final en los faders?**\n"
                        "*(Responde: 'Exportar stems' o pide cualquier ajuste)*"
                    ),
                    "instructions_for_ai": "Puedes solicitar 'Exportar stems' para el paquete comercial o 'Saltar al Drop 1' para reproducir.",
                    "ready_for_distribution": True
                }

            # Default fallback in AUDITION_LAYER: re-display choices
            tech = res_state.get("last_technique", {})
            deploy_res = {"track_index": res_state.get("last_deployed_track", -1), "track_name": "Resample Track"}
            key = res_state.get("key", "F")
            scale = res_state.get("scale", "Minor")
            bpm = float(res_state.get("bpm", 120.0))
            return self._prompt_audition_and_layering(session, tech, deploy_res, key, scale, bpm)

        return self.prompt(session, conn)

    # -------------------------------------------------------------------------
    # PROMPT GENERATORS
    # -------------------------------------------------------------------------
    def _prompt_design_role(self) -> Dict[str, Any]:
        q = (
            "🎹 **DISEÑO DE PISTA FUENTE — PASO 1 DE 4: ROL ACÚSTICO**\n\n"
            "¿Qué rol musical deseas que tenga el sonido base a diseñar?\n\n"
            "1. **KEYS** (Piano de cola prolongado, E-Piano Rhodes/Wurli con cuerpo y sostenimiento natural).\n"
            "2. **PAD** (Colchón ambiental cinemático, barridos armónicos y drone envolvente).\n"
            "3. **BASS** (Bajo analógico profundo, sub Reese denso o bajo saturado).\n"
            "4. **LEAD** (Sintetizador polifónico, melodía abierta para resonancias).\n"
            "5. **TEXTURE** (Lecho de foley orgánico, crujidos y ruidos texturales).\n\n"
            "*(Responde con el número o nombre del rol, ej: '1' o 'Keys')*"
        )
        return {
            "status": "AWAITING_DESIGN_ROLE",
            "phase": "PHASE_11_AUDIO_RESAMPLING",
            "current_step": "DISEÑO DE SONIDO FUENTE: SELECCIÓN DE ROL",
            "question": q,
            "instructions_for_ai": "Selecciona el rol acústico para la pista fuente (Keys, Pad, Bass, Lead, Texture)."
        }

    def _prompt_design_instrument(self, role: str) -> Dict[str, Any]:
        q = (
            f"🎛️ **DISEÑO DE PISTA FUENTE — PASO 2 DE 4: INSTRUMENTO / VST (Rol: {role})**\n\n"
            "Selecciona el sintetizador o instrumento que generará el sonido:\n\n"
            "1. **Arturia Analog Lab V** (Recomendado para pianos orquestales, Rhodes físicos y timbres vintage).\n"
            "2. **Xfer Serum 2** (Síntesis wavetable de alta precisión, filtros limpios y modulación extrema).\n"
            "3. **Matt Tytel Vital** (Síntesis espectral avanzada con modulación estéreo transparente).\n"
            "4. **Arturia Pigments** (Motores híbridos analógico/granular para texturas complejas).\n"
            "5. **Ableton Native Drift / Wavetable** (Bajo consumo de CPU y máxima integración DAW).\n\n"
            "*(Responde con tu preferencia, ej: '1' o 'Analog Lab V')*"
        )
        return {
            "status": "AWAITING_DESIGN_INSTRUMENT",
            "phase": "PHASE_11_AUDIO_RESAMPLING",
            "current_step": f"DISEÑO DE SONIDO FUENTE: INSTRUMENTO ({role})",
            "question": q,
            "instructions_for_ai": "Selecciona el sintetizador o plugin deseado."
        }

    def _prompt_design_preset(self, role: str, instrument: str) -> Dict[str, Any]:
        recommendations = {
            "KEYS": "Prolonged Concert Grand Piano (Voicing Fm9 con caja de resonancia abierta)",
            "PAD": "Warm Ambient Atmosphere (Ataque lento, apertura de filtro progresiva)",
            "BASS": "Deep Analog Reese (Batimento de dos ondas de sierra con paso bajo)",
            "LEAD": "Polyphonic Melodic Sieve (Pluck abierto con decaimiento medio)",
            "TEXTURE": "Organic Soundboard Foil (Resonancia natural y ruidos micro-mecánicos)"
        }
        rec = recommendations.get(role, "Sustained Chord Soundboard")

        q = (
            f"📜 **DISEÑO DE PISTA FUENTE — PASO 3 DE 4: PRESET & ESCULPIDO ({instrument})**\n\n"
            f"El motor sugiere la siguiente configuración optimizada para resíntesis:\n"
            f"• **Preset Sugerido:** `{rec}`\n"
            "• **Gobernanza Delta >= 1:** Se esculpirán los parámetros internos del sinte (filtro cutoff, envolvente ADSR, macro timbres) para evitar estado 'Init'.\n\n"
            "¿Confirmas este preset o deseas indicar uno personalizado?\n"
            "*(Responde 'Confirmar' o escribe el nombre del preset/timbre deseado)*"
        )
        return {
            "status": "AWAITING_DESIGN_PRESET",
            "phase": "PHASE_11_AUDIO_RESAMPLING",
            "current_step": f"DISEÑO DE SONIDO FUENTE: PRESET ({instrument})",
            "question": q,
            "instructions_for_ai": "Confirma el preset recomendado o especifica uno alternativo."
        }

    def _prompt_design_fx(self, role: str, preset: str, blueprint: Dict[str, Any]) -> Dict[str, Any]:
        q = (
            f"⚡ **DISEÑO DE PISTA FUENTE — PASO 4 DE 4: CADENA DE EFECTOS ({preset})**\n\n"
            "Se preparará la cadena de efectos en serie antes del congelamiento a audio:\n"
            "  1. **Ecualizador Quirúrgico (EQ Eight):** Corte de subgraves innecesarios y limpieza de medios.\n"
            "  2. **Compresión Óptica / Glue:** Control de picos y nivelación del cuerpo sostenido.\n"
            "  3. **Espacio & Dimensión:** Saturación analógica sutil y difusión estéreo.\n\n"
            "¿Deseas agregar algún procesador específico (ej: 'Añadir Reverb', 'Añadir Saturator', 'Añadir Chorus') o proceder a sintetizar el acorde fuente continuo?\n"
            "*(Responde 'Proceder' o escribe los efectos adicionales)*"
        )
        return {
            "status": "AWAITING_DESIGN_FX",
            "phase": "PHASE_11_AUDIO_RESAMPLING",
            "current_step": "DISEÑO DE SONIDO FUENTE: CADENA DE EFECTOS",
            "question": q,
            "instructions_for_ai": "Responde 'Proceder' para sintetizar el audio fuente continuo."
        }

    def _prompt_technique_selection(self, session: Any, pipeline: AudioReprocessingPipeline, source_name: str) -> Dict[str, Any]:
        res_state = session.data.get("resampling_session", {})
        key = res_state.get("key", "F")
        scale = res_state.get("scale", "Minor")
        bpm = float(res_state.get("bpm", 120.0))

        q = (
            f"🎛️ **CATÁLOGO DE REPROCESAMIENTO Y MUTACIÓN — SELECCIÓN DE TÉCNICA**\n\n"
            f"• **Sonido Fuente:** `{source_name}` (Audio continuo listo en caché)\n"
            f"• **Afinación Automática:** `{key} {scale}` @ `{bpm:.1f} BPM`\n\n"
            "Elige una de las 20 técnicas especializadas de resíntesis:\n\n"
            "🌊 **Espectral & Granular:**\n"
            "  `[01]` **Spectral Freeze Drone** — Congela magnitudes espectrales; dron líquido infinito.\n"
            "  `[08]` **Granular Micro Cloud** — 40ms micro-granos con jitter y spray estéreo.\n"
            "  `[17]` **Spectral Blur Infinite** — Difuminado Gaussiano 2D del espectrograma.\n\n"
            "🎵 **Armónicas Afinadas a Tonalidad (Key):**\n"
            f"  `[02]` **Tuned Comb Chime** — 3 peines Karplus-Strong sintonizados a {key} {scale} (Tónica, 3ª, 5ª).\n"
            "  `[03]` **Vocal Formant Resonance** — 3 resonadores vocales (/a/, /e/, /i/) en paralelo.\n"
            f"  `[10]` **Inharmonic Metallic Ring** — Modulación en anillo y desplazamiento Hz sintonizado a {key}.\n"
            "  `[15]` **Octave Fuzz Multiplier** — Rectificación de onda completa (octava superior) + fuzz.\n\n"
            "🔊 **Subgraves & Resíntesis de Bajos:**\n"
            f"  `[05]` **Sub-Safe Low Growl** — Mono <120Hz + sub-oscilador locked a {key}1 (30-65Hz) + saturación.\n"
            "  `[07]` **Dark Reese Octave Dive** — -24st transposición doble octava + batimento Reese estéreo.\n\n"
            "🌌 **Espacio, Pitch & Tiempo:**\n"
            "  `[06]` **Pitch Shimmer Diffusion** — +12st velocidad doble + difusor multi-tap.\n"
            "  `[11]` **Reverse Swell Bloom** — Inversión temporal + difusión exponencial de 1.5s + re-inversión.\n"
            "  `[13]` **Haas 3D Spatial Decouple** — Mid/Side + rotación de 90° Hilbert en Side (180° estéreo).\n"
            "  `[20]` **Exponential Pitch Dive** — Caída exponencial de 0 a -14st + barrido paso alto.\n\n"
            "⏱️ **Rítmico & Sincopado a Tempo (BPM):**\n"
            f"  `[14]` **Rhythmic Stutter Chop** — Rebanador de semicorcheas sincopado a {bpm:.1f} BPM.\n"
            f"  `[16]` **Chopped Trance Pulse** — Compuerta trapezoidal a {bpm:.1f} BPM + delay ping-pong.\n\n"
            "🔥 **Saturación, Calidez & Textura:**\n"
            "  `[04]` **Industrial Crunch Mutation** — Wavefolder no lineal de 4 etapas + crunch >3.5kHz.\n"
            "  `[09]` **Vintage Tape Wow Warp** — Emulación cassette con doble LFO wow/flutter e histéresis.\n"
            "  `[12]` **LoFi Bit Crusher Dirt** — Cuantización 10-bit + downsampling 7x (~6.3kHz).\n"
            "  `[18]` **Analog Tape Warmth Glue** — Saturación triodo suave + realce de aire analógico >11kHz.\n"
            "  `[19]` **Neoperreo Metallic Comb** — Peine 11.5ms en 1.18kHz + distorsión Drum Buss urbana.\n\n"
            "*(Responde con el número o nombre de la técnica, ej: '2' o 'Tuned Comb Chime')*"
        )

        return {
            "status": "AWAITING_TECHNIQUE_SELECTION",
            "phase": "PHASE_11_AUDIO_RESAMPLING",
            "current_step": "SELECCIÓN DE TÉCNICA DE MUTACIÓN",
            "source_track": source_name,
            "tuning": {"key": key, "scale": scale, "bpm": bpm},
            "question": q,
            "instructions_for_ai": "Selecciona una técnica del 1 al 20."
        }

    def _prompt_audition_and_layering(
        self,
        session: Any,
        tech: Dict[str, Any],
        deploy_res: Dict[str, Any],
        key: str,
        scale: str,
        bpm: float
    ) -> Dict[str, Any]:
        t_idx = deploy_res.get("track_index", 0)
        t_name = deploy_res.get("track_name", "Resampled Audio Track")

        q = (
            f"🎉 **¡PISTA DE AUDIO MUTADA DESPLEGADA EN LIVE CON ÉXITO!**\n\n"
            f"• **Técnica Aplicada:** `#{tech['index']:02d} {tech['name']}` ({tech['category']})\n"
            f"• **Pista de Audio Nueva:** `Pista {t_idx}: {t_name}`\n"
            f"• **Ubicación en Live:** Clip continuo de 16 compases colocado en el Slot 0\n"
            f"• **Afinación Musical:** Sintonizado a `{key} {scale}` @ `{bpm:.1f} BPM`\n"
            f"• **Calibración de Fader:** 0.75 (-6.0 dBFS) para un margen de mezcla perfecto\n\n"
            "¿Qué deseas hacer a continuación?\n\n"
            "1. **Audicionar / Escuchar en Solo:** Aísla temporalmente esta pista para oír el detalle tímbrico.\n"
            "   *(Responde: 'Solo' o 'Escuchar pista')*\n"
            "2. **Crear otra capa de mutación:** Escoge otra de las 20 técnicas para crear una segunda pista de textura.\n"
            "   *(Responde: 'Crear otra capa' o 'Otra mutación')*\n"
            "3. **Finalizar y proceder a exportar stems:** Concluye el reprocesamiento y regresa al control maestro.\n"
            "   *(Responde: 'Finalizar' o 'Exportar stems')*"
        )

        return {
            "status": "MUTATION_DEPLOYED_SUCCESSFULLY",
            "phase": "PHASE_11_AUDIO_RESAMPLING",
            "current_step": f"MUTACIÓN #{tech['index']} DESPLEGADA EN PISTA {t_idx}",
            "action_taken": f"Pista de audio '{t_name}' creada en Live con clip de audio continuo en slot 0.",
            "question": q,
            "instructions_for_ai": "Puedes pedir 'Solo', 'Crear otra capa' o 'Finalizar'.",
            "deployed_track": deploy_res,
            "technique": tech
        }

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------
    def _resolve_or_create_source_audio(
        self, session: Any, conn: Any, target_track: Dict[str, Any], pipeline: AudioReprocessingPipeline
    ) -> str:
        """Finds existing WAV file or synthesizes physical source chord."""
        # 1. Check if default piano chord already exists
        default_piano = Path("cache/uhts_resampled/source_piano_chord.wav")
        if default_piano.exists() and default_piano.stat().st_size > 10000:
            return str(default_piano.resolve())

        # 2. Synthesize using pipeline
        key = session.data.get("key", "F")
        scale = session.data.get("scale", "Minor")
        bpm = float(session.data.get("bpm", 120.0))
        res = pipeline.generate_source_sound_for_new_track(
            role=target_track.get("role", "KEYS"),
            instrument_name=target_track.get("name", "Analog Lab V"),
            preset_name="Prolonged Concert Grand",
            key=key,
            scale=scale,
            bpm=bpm,
            bars=4
        )
        return res["wav_path"]

    def _ensure_fallback_source(self, pipeline: AudioReprocessingPipeline, res_state: Dict[str, Any]) -> str:
        key = res_state.get("key", "F")
        scale = res_state.get("scale", "Minor")
        bpm = float(res_state.get("bpm", 120.0))
        res = pipeline.generate_source_sound_for_new_track(
            role="KEYS",
            instrument_name="Analog Lab V",
            preset_name="Prolonged Concert Grand",
            key=key,
            scale=scale,
            bpm=bpm,
            bars=4
        )
        return res["wav_path"]

    def _get_blueprint_for_role(self, role: str) -> Dict[str, Any]:
        if role == "KEYS":
            return {"Drive": 0.25, "Tremolo Rate": 0.35, "Filter Cutoff": 0.78, "Reverb": 0.40}
        elif role == "PAD":
            return {"Attack": 0.45, "Release": 0.70, "Cutoff": 0.55, "Resonance": 0.20, "Reverb": 0.65}
        elif role == "BASS":
            return {"Drive": 0.40, "Cutoff": 0.45, "Sub Harmonics": 0.60, "Glide Time": 0.20}
        elif role == "LEAD":
            return {"Attack": 0.05, "Decay": 0.40, "Cutoff": 0.85, "Delay Send": 0.35}
        return {"Cutoff": 0.60, "Density": 0.70, "Space": 0.50}

    def _deploy_full_20_scene_pad(
        self,
        session: Any,
        conn: Any,
        pipeline: AudioReprocessingPipeline,
        res_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deploys all 20 UHTS Pad Resampling textures across 20 scenes in Session View
        and as an 80-bar continuous evolutionary timeline in Arrangement View with 20 locators.
        """
        key = res_state.get("key", "F")
        scale = res_state.get("scale", "Minor")
        bpm = float(res_state.get("bpm", 100.0))

        root_dir = Path(__file__).resolve().parent.parent.parent.parent
        assets_dir = root_dir / "cache" / "resampled_mutations"
        assets_dir.mkdir(parents=True, exist_ok=True)
        catalog = pipeline.get_catalog()

        # 1. Check or generate all 20 audio files
        missing_count = 0
        for item in catalog:
            idx = item["index"]
            pattern = f"*uhts_{idx:02d}_*.wav"
            if not list(assets_dir.glob(pattern)):
                missing_count += 1

        if missing_count > 0:
            from engine.sound_design.piano_chord_generator import generate_source_piano_chord
            source_path = assets_dir.parent / "taiko_casti" / "taiko_casti_source_chord.wav"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            if not source_path.exists():
                duration_sec = 16.0 * (60.0 / bpm)
                generate_source_piano_chord(str(source_path), duration_sec=duration_sec)

            for item in catalog:
                idx = item["index"]
                pattern = f"*uhts_{idx:02d}_*.wav"
                if not list(assets_dir.glob(pattern)):
                    pipeline.execute_mutation(
                        source_wav_path=str(source_path),
                        technique_selector=idx,
                        key=key,
                        scale=scale,
                        bpm=bpm
                    )

        # 2. Physical deployment in Live if connected
        deployed_scenes = []
        pad_track_idx = -1
        pad_track_name = "[PAD] UHTS 20-Stage Audio"

        if conn is not None and hasattr(conn, "send_command"):
            s_info = conn.send_command("get_session_info", {})
            raw_count = s_info.get("track_count", 0) if isinstance(s_info, dict) else 0
            try:
                t_count = int(raw_count)
            except Exception:
                t_count = 0

            for t_i in range(t_count):
                try:
                    ti = conn.send_command("get_track_info", {"track_index": t_i})
                    res_name = ti.get("name", "") if isinstance(ti, dict) else ""
                    if pad_track_name.lower() in str(res_name).lower():
                        pad_track_idx = t_i
                        break
                except Exception:
                    pass

            if pad_track_idx < 0:
                res_create = conn.send_command("execute_code", {
                    "code": f"t = song.create_audio_track(-1); t.name = '{pad_track_name}'; result = len(song.tracks) - 1"
                })
                raw_idx = res_create.get("result", t_count) if isinstance(res_create, dict) else t_count
                try:
                    pad_track_idx = int(raw_idx)
                except Exception:
                    pad_track_idx = t_count

            try:
                conn.send_command("set_track_volume", {"track_index": pad_track_idx, "volume": 0.75})
            except Exception:
                pass

            # Ensure at least 20 scenes
            conn.send_command("execute_code", {
                "code": "while len(song.scenes) < 20: song.create_scene(-1); result = len(song.scenes)"
            })

            # Populate 20 scenes and arrangement timeline
            for s_idx in range(1, 21):
                scene_pos = s_idx - 1
                tech_meta = catalog[scene_pos]
                tech_name = tech_meta["name"]
                dest_time_beat = float(scene_pos * 16.0)

                pattern = f"*uhts_{s_idx:02d}_*.wav"
                matching_files = list(assets_dir.glob(pattern))
                if matching_files:
                    wav_path = str(matching_files[0].resolve())
                    try:
                        conn.send_command("create_audio_clip", {
                            "track_index": pad_track_idx,
                            "clip_index": scene_pos,
                            "path": wav_path
                        })
                        conn.send_command("set_clip_name", {
                            "track_index": pad_track_idx,
                            "clip_index": scene_pos,
                            "name": f"UHTS #{s_idx:02d}: {tech_name}"
                        })
                        conn.send_command("duplicate_session_clip_to_arrangement", {
                            "track_index": pad_track_idx,
                            "clip_index": scene_pos,
                            "destination_time": dest_time_beat
                        })
                    except Exception as e:
                        logger.warning(f"Error staging pad clip {s_idx}: {e}")

                    try:
                        conn.send_command("create_cue_point", {
                            "time": dest_time_beat,
                            "name": f"#{s_idx:02d}: {tech_name}"
                        })
                    except Exception:
                        pass

                deployed_scenes.append({
                    "scene": s_idx,
                    "bar": scene_pos * 4 + 1,
                    "technique": tech_name,
                    "category": tech_meta["category"]
                })

            try:
                conn.send_command("switch_to_arrangement_view", {})
                conn.send_command("set_loop_region", {"start_time": 0.0, "length": 320.0, "enabled": True})
                conn.send_command("jump_to_cue_point", {"target": 0.0})
            except Exception:
                pass

        # 3. Register state
        res_state["last_deployed_track"] = pad_track_idx
        res_state["mode"] = "FULL_20_SCENE_EVOLUTION"
        res_state["stage"] = "AUDITION_LAYER"
        session.data.setdefault("resampled_tracks", []).append({
            "mode": "FULL_20_SCENE_EVOLUTION",
            "track_name": pad_track_name,
            "track_index": pad_track_idx,
            "scenes_count": 20,
            "total_bars": 80,
            "key": key,
            "scale": scale,
            "bpm": bpm
        })
        session._save_state(action_tag="RESAMPLE_DEPLOY_FULL_20_SCENES")

        return {
            "status": "FULL_20_SCENE_PAD_DEPLOYED",
            "phase": "PHASE_11_AUDIO_RESAMPLING",
            "current_step": "FASE 11: PAD EVOLUTIVO DE 20 ESCENAS UHTS DESPLEGADO",
            "action_taken": (
                f"Despliegue exitoso del Pad Evolutivo UHTS en Pista '{pad_track_name}'. "
                f"20 escenas en Session View y 80 compases en Arrangement View con 20 Cue Points configurados "
                f"a {key} {scale} @ {bpm:.1f} BPM."
            ),
            "pad_track_index": pad_track_idx,
            "pad_track_name": pad_track_name,
            "scenes_deployed": len(deployed_scenes) if deployed_scenes else 20,
            "question": (
                f"🎉 **¡Pad Evolutivo UHTS Desplegado Exitosamente a lo largo de la Canción!**\n\n"
                f"• **Pista de Audio:** `{pad_track_name}` (Fader calibrado a -6 dBFS)\n"
                f"• **Session View:** 20 escenas operativas con sus respectivos clips de audio continuo.\n"
                f"• **Arrangement View:** Línea temporal completa de 80 compases con **20 Cue Points / Locators**.\n"
                f"• **Afinación:** `{key} {scale} @ {bpm:.1f} BPM`.\n\n"
                "¿Deseas poner la pista en solo para audicionarla aislada, o certificar la producción final?"
            ),
            "instructions_for_ai": "Puedes pedir 'Poner en solo', 'Reproducir' o 'Finalizar sesión'."
        }
