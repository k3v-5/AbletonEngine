# engine/production/copilot/cognitive_evaluator.py
r"""
Cognitive Phase Evaluator & Conscious Decision Engine:
Evaluates real available options, parameters, and sound archetypes at each phase of production.
Replaces blind 'Option 1' loops with artist-informed, genre-calibrated technical decisions.

Adheres strictly to the Multi-Platinum Principle:
'La IA decide y el motor solo valida, expone lo que la IA necesite en su momento y coloca lo que la IA pide,
el motor es un harness para que la IA siempre se acuerde de hacer cada paso.'
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("CognitivePhaseEvaluator")


class CognitivePhaseEvaluator:
    """
    Analyzes live options exposed by the engine harness at each phase,
    matches them against the artist's authentic sonic identity, and selects
    the optimal technical parameters.
    """

# Official supported musical roles exposed by the engine harness
SUPPORTED_TRACK_ROLES = [
    "DRUMS",          # Main drum kit (Kick, Snare, Hi-Hats, Claps)
    "PERCUSSION",     # Auxiliary percussion, foley, organic snaps, shakers
    "BASS",           # Acoustic/Electric Bass, Synth Bass
    "808_BASS",       # Trap/Urban Sub Bass with pitch glide and saturation
    "SUB_BASS",       # Pure sine/subliminal fundamental sub
    "LEAD",           # Main melodic lead instrument / synthesizer
    "COUNTER_LEAD",   # Melodic counterpoint lead / secondary harmony motif
    "GUITAR",         # Electric/Acoustic guitars (riff, fingerpicking, strum)
    "KEYS",           # General synthesizers, polyphonic comping, organs
    "PIANO",          # Grand Piano, Upright Acoustic Felt Piano
    "RHODES",         # Electric Piano (Rhodes, Wurlitzer, Clavinet)
    "PAD",            # Atmospheric lush sustained pads, shimmer, ambient
    "STRINGS",        # Orchestral strings, ensemble, solo cello, violin
    "BRASS",          # Brass section, horns, trumpets, stabs
    "CHOIR",          # Vocal textures, backing choir, whispered vocals
    "VOCAL_CHOP",     # Rhythmic chopped/pitched vocal samples
    "ARP",            # Arpeggiated sequence, synth arpeggios
    "EAR_CANDY",      # Micro-transitions, glitch accents, transitional textures
    "FX"              # Risers, impacts, downlifters, sweeps
]


class CognitivePhaseEvaluator:
    """
    Analyzes live options exposed by the engine harness at each phase,
    matches them against the artist's authentic sonic identity, and selects
    the optimal technical parameters.
    """

    SUPPORTED_TRACK_ROLES = SUPPORTED_TRACK_ROLES

    @classmethod
    def evaluate_step(
        cls,
        phase: str,
        step_response: Dict[str, Any],
        proposal: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Evaluates the step response, inspects all available choices, and returns:
        (chosen_input_string, rationale_explanation)
        """
        artist = proposal.get("artist", "Artista")
        genre = proposal.get("genre", "Pop")
        subgenre = proposal.get("subgenre", "")
        bpm = float(proposal.get("bpm", 120.0))
        target_lufs = float(proposal.get("target_lufs", -9.0))
        climax_bar = proposal.get("climax_bar") or proposal.get("drop_bar") or 32

        step_response = step_response or {}
        question = step_response.get("question", "")
        options = step_response.get("options", [])
        status = step_response.get("status", "")

        # ---------------------------------------------------------------------
        # 1. PHASE 0: DESIGN SPECIFICATION & ARTIST CONFIRMATION
        # ---------------------------------------------------------------------
        if phase == "PHASE_0_DESIGN":
            if status == "VITAL_MODELING_REQUIRED" or "MODELADO DE SINTETIZADOR VITAL" in question.upper():
                import copy
                target_track = step_response.get("target_track", {})
                t_role = str(target_track.get("role", "LEAD")).upper()
                base_preset_data = step_response.get("base_preset_data", {})
                base_name = step_response.get("base_preset_name", "Archetype_Base")

                modeled_preset = copy.deepcopy(base_preset_data) if base_preset_data else {}
                settings = modeled_preset.setdefault("settings", {})

                # Ensure volume is strictly audible and within professional domain
                settings["volume"] = 5400.0

                mod_desc = []
                if any(k in t_role for k in ("BASS", "808", "SUB")):
                    settings["filter_1_cutoff"] = 48.0
                    settings["filter_1_resonance"] = 0.22
                    settings["filter_1_drive"] = 4.5
                    settings["distortion_on"] = 1.0
                    settings["distortion_drive"] = 7.0
                    settings["env_1_decay"] = 1.8
                    settings["env_1_sustain"] = 0.65
                    settings["osc_1_unison_detune"] = 0.02
                    mod_desc.extend(["filter_1_cutoff=48.0", "distortion_drive=7.0dB", "filter_1_drive=4.5dB"])
                elif any(k in t_role for k in ("LEAD", "COUNTER")):
                    settings["filter_1_cutoff"] = 94.0
                    settings["filter_1_resonance"] = 0.28
                    settings["osc_1_unison_voices"] = 4.0
                    settings["osc_1_unison_detune"] = 0.16
                    settings["reverb_on"] = 1.0
                    settings["reverb_dry_wet"] = 0.22
                    settings["delay_on"] = 1.0
                    settings["delay_dry_wet"] = 0.18
                    settings["distortion_on"] = 1.0
                    settings["distortion_drive"] = 5.5
                    mod_desc.extend(["filter_1_cutoff=94.0", "unison=4v_detune_0.16", "reverb_wet=0.22"])
                elif any(k in t_role for k in ("PAD", "STRINGS", "CHOIR", "TEXTURE")):
                    settings["env_1_attack"] = 0.42
                    settings["env_1_decay"] = 2.5
                    settings["env_1_sustain"] = 0.85
                    settings["env_1_release"] = 1.4
                    settings["filter_1_cutoff"] = 76.0
                    settings["reverb_on"] = 1.0
                    settings["reverb_dry_wet"] = 0.40
                    settings["reverb_decay_time"] = 4.0
                    mod_desc.extend(["attack=0.42s", "release=1.4s", "reverb_wet=0.40", "reverb_decay=4.0s"])
                elif any(k in t_role for k in ("KEYS", "RHODES", "PIANO", "PLUCK")):
                    settings["env_1_attack"] = 0.008
                    settings["env_1_decay"] = 1.25
                    settings["env_1_sustain"] = 0.45
                    settings["filter_1_cutoff"] = 82.0
                    settings["filter_1_drive"] = 2.0
                    settings["reverb_on"] = 1.0
                    settings["reverb_dry_wet"] = 0.16
                    mod_desc.extend(["decay=1.25s", "filter_1_cutoff=82.0", "drive=2.0dB"])
                else:
                    curr_cut = float(settings.get("filter_1_cutoff", 80.0))
                    settings["filter_1_cutoff"] = round(curr_cut + 6.0, 2)
                    settings["osc_1_unison_detune"] = 0.12
                    settings["reverb_dry_wet"] = 0.20
                    mod_desc.extend([f"filter_1_cutoff={settings['filter_1_cutoff']}", "detune=0.12"])

                clean_artist = re.sub(r'[^a-zA-Z0-9_]', '_', artist)
                modeled_preset["preset_name"] = f"{base_name}_{clean_artist}_Custom"
                modeled_preset["author"] = f"Cognitive AI ({artist})"
                modeled_preset["comments"] = f"Consciously sculpted Vital preset for {target_track.get('name')} ({t_role}) emulating {artist}."

                rationale = (
                    f"Modelado consciente de sintetizador Vital para pista '{target_track.get('name')}' ({t_role}) "
                    f"adaptado a {artist}. Parámetros modificados: {', '.join(mod_desc)}."
                )
                return json.dumps(modeled_preset, indent=2), rationale

            if status in ("AWAITING_ARTIST_CONFIRMATION", "CONFIRMATION") or "CONFIRMACIÓN" in question.upper():
                rationale = f"Confirmación consciente del ADN musical para {artist} ({genre} @ {bpm} BPM, Clímax en compás {climax_bar}, Target {target_lufs} LUFS)."
                return "Sí, confirmo el diseño para el artista.", rationale

            # Initial design spec: AI defines tracks with explicit roles (no engine guessing)
            designed_tracks = proposal.get("tracks", [])
            if not designed_tracks and proposal.get("track_names"):
                # Convert track names if needed
                raw_names = proposal["track_names"].split(",") if isinstance(proposal["track_names"], str) else proposal["track_names"]
                raw_insts = proposal.get("instruments", [])
                for i, tn in enumerate(raw_names):
                    name_clean = tn.strip()
                    inst_clean = raw_insts[i] if i < len(raw_insts) else "Native Device"
                    # Default role from explicit proposal or mapping
                    role = proposal.get(f"track_{i}_role") or ("DRUMS" if i == 0 else "808_BASS" if i == 1 else "LEAD" if i == 2 else "KEYS" if i == 3 else "PAD")
                    designed_tracks.append({"name": name_clean, "role": role, "instrument": inst_clean})

            density = len(designed_tracks) or proposal.get("channel_density", 6)
            spec_payload = {
                "artist": artist,
                "genre": genre,
                "subgenre": subgenre,
                "bpm": bpm,
                "key": proposal.get("key", "C"),
                "scale": proposal.get("scale", "natural_minor"),
                "time_signature": proposal.get("time_signature", "4/4"),
                "channel_density": density,
                "drop_bar": climax_bar,
                "sections": proposal.get("sections", []),
                "tracks": designed_tracks,
                "instruments": [t.get("instrument", "") for t in designed_tracks] if designed_tracks else proposal.get("instruments", []),
                "target_lufs": target_lufs,
                "groove_style": proposal.get("groove_style") or proposal.get("pocket_style", "straight_precise"),
                "swing_percentage": float(proposal.get("swing_percentage", proposal.get("hihat_swing_pct", 58.0))),
                "snare_drag_ms": float(proposal.get("snare_drag_ms", proposal.get("snare_dragging_ms", 12.0))),
                "sub_drag_ms": float(proposal.get("sub_drag_ms", proposal.get("sub_dragging_ms", 4.0))),
                "advanced_production": proposal.get("advanced_production", {})
            }
            rationale = f"Diseño de arquitectura musical personalizado para {artist} con {density} canales, roles explícitos y groove consciente ({spec_payload['groove_style']}, swing {spec_payload['swing_percentage']}%) definidos por la IA."
            return json.dumps(spec_payload), rationale

        # ---------------------------------------------------------------------
        # 2. PHASE 1: TRACKS SCAFFOLDING
        # ---------------------------------------------------------------------
        # ---------------------------------------------------------------------
        # 2. PHASE 1: TRACKS SCAFFOLDING
        # ---------------------------------------------------------------------
        if phase == "PHASE_1_TRACKS":
            designed_tracks = proposal.get("tracks", [])
            if designed_tracks:
                # Send structured JSON with explicit roles so the engine NEVER guesses dynamically!
                payload = json.dumps([
                    {
                        "name": t.get("name", "Track"),
                        "role": t.get("role", "KEYS"),
                        "type": t.get("type", "MIDI")
                    }
                    for t in designed_tracks
                ])
                rationale = f"Creación consciente de {len(designed_tracks)} pistas con roles explícitos definidos en diseño para {artist}."
                return payload, rationale
            else:
                t_names = proposal.get("track_names", "")
                if isinstance(t_names, list):
                    t_names = ", ".join(t_names)
                return t_names, f"Creación de pistas para {artist}: {t_names}"

        # ---------------------------------------------------------------------
        # 3. PHASE 2: STRUCTURE & SECTIONS
        # ---------------------------------------------------------------------
        if phase == "PHASE_2_STRUCTURE":
            sections = proposal.get("sections", [])
            payload = json.dumps({
                "sections": sections,
                "key": proposal.get("key", "C"),
                "scale": proposal.get("scale", "natural_minor"),
                "bpm": bpm
            })
            rationale = f"Definición de estructura formal ({len(sections)} secciones auténticas) para {artist} en {proposal.get('key')} {proposal.get('scale')}."
            return payload, rationale

        # ---------------------------------------------------------------------
        # 4. PHASE 3: INSTRUMENT SELECTION (CONSCIENTIOUS CHOICE)
        # ---------------------------------------------------------------------
        if phase == "PHASE_3_INSTRUMENTS":
            ptr = step_response.get("track_ptr")
            if ptr is None:
                m_step = re.search(r"PISTA\s+(\d+)\s+DE", step_response.get("current_step", ""), re.IGNORECASE)
                if m_step:
                    ptr = int(m_step.group(1)) - 1
                else:
                    ptr = step_response.get("target_track", 0)

            role = str(step_response.get("role", "")).upper()
            proposal_tracks = proposal.get("tracks", [])
            proposal_insts = proposal.get("instruments", [])

            # Planned instrument from Phase 0 Design for this specific track
            planned_inst = step_response.get("planned_instrument")
            if not planned_inst:
                if ptr is not None and isinstance(ptr, int) and ptr < len(proposal_tracks):
                    planned_inst = proposal_tracks[ptr].get("instrument")
                    if not role:
                        role = str(proposal_tracks[ptr].get("role", "")).upper()
                elif ptr is not None and isinstance(ptr, int) and ptr < len(proposal_insts):
                    planned_inst = proposal_insts[ptr]
                elif role and ptr is not None and isinstance(ptr, int):
                    # Match by role only for the specific track index if possible
                    matching_tracks = [t for i, t in enumerate(proposal_tracks) if str(t.get("role", "")).upper() == role and i == ptr]
                    if matching_tracks:
                        planned_inst = matching_tracks[0].get("instrument")

            available_options = step_response.get("options", []) or cls._extract_options(question, options)

            # If planned instrument exists in Phase 0 design, respect the AI's Phase 0 decision!
            if planned_inst:
                if "kit-core 909" in str(planned_inst).lower() or planned_inst == "Kit-Core 909":
                    planned_inst = "909 Core Kit (.adg)"
                rationale = f"Instrumento consciente según diseño de Fase 0 para {artist} (Pista {ptr+1 if ptr is not None else ''} [{role}]): {planned_inst}."
                return planned_inst, rationale

            # If options are exposed, select the best instrument for this specific role and artist
            if available_options:
                chosen, rat = cls._select_best_instrument_option(available_options, proposal, role=role, ptr=ptr)
                return chosen, rat

            # Conscientious role fallback (never load a drum kit on a bass or pad track!)
            role_fallbacks = {
                "DRUMS": "808 Core Kit (.adg)",
                "PERCUSSION": "Percussion Core Kit (.adg)",
                "BASS": "Vital Audio 808 Sub",
                "808_BASS": "Vital Audio 808 Sub",
                "SUB_BASS": "Basic Sub Sine (.adg)",
                "KEYS": "Ac Piano Upright (.adg)",
                "PIANO": "Ac Piano Upright (.adg)",
                "RHODES": "Drift Neo-Soul Rhodes",
                "LEAD": "Vital Spectral Lead",
                "COUNTER_LEAD": "Agenda Lead (.adv)",
                "PAD": "Warm Analog Pad (.adg)",
                "STRINGS": "Ac Strings Orch (.adg)",
                "CHOIR": "Choir Pad Avalon (.adg)",
                "GUITAR": "Nylon Flamenco Guitar (.adv)",
                "BRASS": "Transilvania Brass (.adg)"
            }
            fb = role_fallbacks.get(role, "Vital Audio 808 Sub" if "BASS" in role else "Warm Analog Pad (.adg)")
            return fb, f"Instrumentación consciente según rol {role} para {artist}: {fb}"

        # ---------------------------------------------------------------------
        # 5. PHASE 4: SOUND DESIGN & PARAMETER SCULPTING
        # ---------------------------------------------------------------------
        if phase == "PHASE_4_PARAM_SCULPTING":
            role = str(step_response.get("role", "")).upper()
            available_options = cls._extract_options(question, options)
            if available_options:
                chosen, rat = cls._select_best_sculpt_option(available_options, proposal, role=role)
                return chosen, rat

            if "BASS" in role or "808" in role or "SUB" in role:
                b_sculpt = proposal.get("bass_sculpt", "Opción 1: Sub Grave Monofónico Limpio")
                return b_sculpt, f"Escultura tímbrica de bajo adaptada a {artist}: {b_sculpt}"
            if "LEAD" in role or "SOLO" in role or "COUNTER" in role:
                l_sculpt = proposal.get("lead_sculpt", "Opción 4: Vintage Pluck Lead")
                return l_sculpt, f"Escultura de lead adaptada a {artist}: {l_sculpt}"
            if "KEYS" in role or "PIANO" in role or "RHODES" in role:
                k_sculpt = proposal.get("keys_sculpt", "Opción 1: Neo-Soul Warmth Rhodes")
                return k_sculpt, f"Escultura armónica adaptada a {artist}: {k_sculpt}"
            if "PAD" in role or "STRINGS" in role:
                p_sculpt = proposal.get("pad_sculpt", "Opción 1: Ethereal Ambient Shimmer Pad")
                return p_sculpt, f"Escultura atmosférica adaptada a {artist}: {p_sculpt}"
            if any(k in role for k in ("DRUM", "PERC", "KICK", "SNARE")):
                d_sculpt = "Opción 3: Acoustic Natural Wood & Brass" if "billie" in artist.lower() else "Opción 1: Tight Transient Snap"
                return d_sculpt, f"Escultura rítmica adaptada a {artist}: {d_sculpt}"

            return f"Opción 1: Arquetipo Tímbrico Consciente para {role}", f"Parámetro adaptado a {artist} ({role})"

        # ---------------------------------------------------------------------
        # 6. PHASE 5: INSERT EFFECTS CHAINS
        # ---------------------------------------------------------------------
        if phase == "PHASE_5_INSERT_EFFECTS":
            if status == "AESTHETIC_PROFILE_REQUIRED":
                schema = step_response.get("schema_expected", {})
                return json.dumps(schema), "Perfil estético de inserciones enviado."

            available_options = cls._extract_options(question, options)
            if available_options:
                chosen, rat = cls._select_best_fx_option(available_options, proposal)
                return chosen, rat
            return "Cadena express: EQ Eight quirúrgico y Glue Compressor calibrado", f"Cadena de inserción consciente para {artist}"

        # ---------------------------------------------------------------------
        # 7. PHASE 7: DYNAMIC ARRANGEMENT MIXING & PANNING
        # ---------------------------------------------------------------------
        if phase in ("PHASE_7_AUTOMATION", "PHASE_7_MIXING"):
            available_options = cls._extract_options(question, options)
            for opt in available_options:
                opt_low = opt.lower()
                if "complementario" in opt_low or "dinámico" in opt_low or "estéreo" in opt_low or "opción a" in opt_low:
                    return opt, f"Paneo estéreo complementario seleccionado conscientemente para {artist}."
            return "Opción A: Balance Estéreo Dinámico Complementario (-30L / +30R)", f"Paneo balanceado para {artist}"

        # ---------------------------------------------------------------------
        # 8. PHASE 8: SPACE & VOCAL DUCKING (KICK -> BASS SIDECHAIN)
        # ---------------------------------------------------------------------
        if phase == "PHASE_8_VOCAL_DUCKING":
            available_options = cls._extract_options(question, options)
            for opt in available_options:
                opt_low = opt.lower()
                if "sidechain" in opt_low or "kick" in opt_low or "ducking" in opt_low or "4:1" in opt_low or "opción 1" in opt_low:
                    return opt, f"Compresión sidechain física Kick -> Bajo (4:1, Post FX, S/C On=1.0) activada para {artist}."
            return "Opción 1: Ruteo Físico Kick -> Bass Ducking (4:1, Post FX)", f"Sidechain kick->bass para {artist}"

        # ---------------------------------------------------------------------
        # 9. PHASE 9: PHYSICAL MASTERING & LUFS CALIBRATION
        # ---------------------------------------------------------------------
        if phase in ("PHASE_9_MIX_MASTER", "PHASE_9_MASTERING"):
            target_str = f"Mastering a {target_lufs} LUFS para {genre} con calibración de limitador y True Peak"
            rationale = f"Calibración consciente de masterización al estándar de {genre}: {target_lufs} LUFS (Evitando -14.7 LUFS genérico)."
            return target_str, rationale

        return "Opción 1", f"Aceptación guiada de fase {phase} para {artist}"

    @classmethod
    def _extract_options(cls, question: str, options_list: List[Any]) -> List[str]:
        """Extracts available options from the engine response."""
        extracted = []
        if options_list and isinstance(options_list, list):
            for o in options_list:
                if isinstance(o, str) and o.strip():
                    extracted.append(o.strip())
                elif isinstance(o, dict) and "label" in o:
                    extracted.append(o["label"])

        if not extracted and question:
            matches = re.findall(r"((?:Opción\s*\d+|Option\s*\d+|Arquetipo\s*\d+|Preset\s*\d+|\b[A-E]\))\s*[:\-\)]?\s*[^\n\r]+)", question, re.IGNORECASE)
            for m in matches:
                clean_m = m.strip(" *`")
                if clean_m:
                    extracted.append(clean_m)

        return extracted

    @classmethod
    def _select_best_sculpt_option(
        cls,
        options: List[str],
        p: Dict[str, Any],
        role: str = ""
    ) -> Tuple[str, str]:
        """Selects sound design archetype based on artist sonic DNA and track role."""
        artist_low = p.get("artist", "").lower()
        genre_low = p.get("genre", "").lower()
        role_upper = role.upper() if role else ""

        if any(k in role_upper for k in ("DRUM", "PERC", "KICK", "SNARE")):
            if "billie" in artist_low or "minimal" in genre_low or "acoustic" in genre_low:
                for opt in options:
                    if any(w in opt.lower() for w in ["acoustic", "natural", "wood", "brass"]):
                        return opt, f"Percusión acústica/orgánica para {p.get('artist')}: {opt}"
            if "trap" in genre_low or "drill" in genre_low or "travis" in artist_low or "metro" in artist_low:
                for opt in options:
                    if any(w in opt.lower() for w in ["heavy saturated", "boom", "trap", "808"]):
                        return opt, f"Batería pesada saturada para {p.get('artist')}: {opt}"
            if "lofi" in genre_low or "lo-fi" in genre_low or "boom bap" in genre_low:
                for opt in options:
                    if any(w in opt.lower() for w in ["lo-fi", "12-bit", "sp-1200", "vintage"]):
                        return opt, f"Batería Lo-Fi con carácter vintage para {p.get('artist')}: {opt}"
            for opt in options:
                if any(w in opt.lower() for w in ["tight", "transient", "punch", "snap", "natural"]):
                    return opt, f"Escultura rítmica seleccionada: {opt}"

        elif "BASS" in role_upper or "SUB" in role_upper or "808" in role_upper:
            if "billie" in artist_low:
                for opt in options:
                    if any(w in opt.lower() for w in ["sub grave", "monofónico", "limpio", "sub", "senoidal"]):
                        return opt, "Seleccionado subgrave monofónico limpio característico de Finneas/Billie."
            if "travis" in artist_low or "trap" in genre_low:
                for opt in options:
                    if any(w in opt.lower() for w in ["808 saturado", "808", "distorsión", "saturado"]):
                        return opt, "Seleccionado bajo 808 saturado con pegada para Trap."
            for opt in options:
                if any(w in opt.lower() for w in ["sub grave", "808", "bass", "bajo"]):
                    return opt, f"Escultura óptima de bajo: {opt}"

        elif "LEAD" in role_upper or "SYNTH" in role_upper or "SOLO" in role_upper:
            if "billie" in artist_low:
                for opt in options:
                    if any(w in opt.lower() for w in ["vintage pluck", "pluck", "warm analog"]):
                        return opt, "Seleccionado lead pluck íntimo/vintage para Billie Eilish."
            for opt in options:
                if any(w in opt.lower() for w in ["lead", "pluck", "solo", "piercing", "supersaw"]):
                    return opt, f"Escultura óptima de lead: {opt}"

        elif "PAD" in role_upper or "STRINGS" in role_upper or "CHOIR" in role_upper:
            for opt in options:
                if any(w in opt.lower() for w in ["ethereal", "ambient", "shimmer", "warm vintage", "choir"]):
                    return opt, f"Escultura atmosférica seleccionada: {opt}"

        elif "KEYS" in role_upper or "PIANO" in role_upper:
            for opt in options:
                if any(w in opt.lower() for w in ["vintage", "warm", "cálido", "natural", "equilibrado"]):
                    return opt, f"Escultura armónica de teclas: {opt}"

        for opt in options:
            if role_upper and any(w in opt.upper() for w in role_upper.split("_")):
                return opt, f"Selección óptima de catálogo según rol {role_upper}: {opt}"
        return options[0], f"Selección de catálogo: {options[0]}"

    @classmethod
    def _select_best_instrument_option(
        cls,
        options: List[str],
        p: Dict[str, Any],
        role: str = "",
        ptr: Optional[int] = None
    ) -> Tuple[str, str]:
        """Selects sound source instrument matching artist instrumentation and track role."""
        artist_low = p.get("artist", "").lower()
        role_upper = role.upper() if role else ""

        # Collect instruments already used in earlier tracks of this song to avoid duplicate timbre
        used_insts = set()
        if ptr is not None and ptr > 0:
            for t_idx in range(ptr):
                if t_idx < len(p.get("tracks", [])):
                    inst_name = str(p["tracks"][t_idx].get("instrument", "")).lower()
                    if inst_name:
                        used_insts.add(inst_name)
                        for part in inst_name.replace("(", "").replace(")", "").split():
                            if len(part) > 3:
                                used_insts.add(part)

        def is_already_used(cand_opt: str) -> bool:
            cand_l = cand_opt.lower()
            return any(u in cand_l for u in used_insts)

        # Filter options suitable for role if possible
        def pick_first_unused_or_any(matching_cands: List[str]) -> Optional[str]:
            if not matching_cands:
                return None
            unused = [c for c in matching_cands if not is_already_used(c)]
            return unused[0] if unused else matching_cands[0]

        if role_upper in ("DRUMS", "PERCUSSION"):
            cands = [opt for opt in options if any(w in opt.lower() for w in ["kit", "drum", "perc", "808 core", "tamuz", "session", "garage"])]
            chosen = pick_first_unused_or_any(cands)
            if chosen:
                return chosen, f"Kit rítmico seleccionado para {p.get('artist')}: {chosen}"
        elif role_upper in ("BASS", "SUB_BASS", "808_BASS", "SUB"):
            cands = [opt for opt in options if any(w in opt.lower() for w in ["sublab", "vital", "808", "sub", "drift", "sine", "bass", "serum", "massive"])]
            chosen = pick_first_unused_or_any(cands)
            if chosen:
                return chosen, f"Bajo/sub seleccionado para {p.get('artist')}: {chosen}"
        elif role_upper in ("KEYS", "PIANO", "RHODES"):
            cands = [opt for opt in options if any(w in opt.lower() for w in ["piano", "keyscape", "rhodes", "wurli", "analog lab", "keys"])]
            chosen = pick_first_unused_or_any(cands)
            if chosen:
                return chosen, f"Teclado armónico para {p.get('artist')}: {chosen}"
        elif role_upper in ("PAD", "STRINGS"):
            cands = [opt for opt in options if any(w in opt.lower() for w in ["pad", "warm", "strings", "pigments", "omnisphere", "shimmer"])]
            chosen = pick_first_unused_or_any(cands)
            if chosen:
                return chosen, f"Colchón/cuerdas atmosféricas para {p.get('artist')}: {chosen}"
        elif role_upper == "CHOIR":
            cands = [opt for opt in options if any(w in opt.lower() for w in ["choir", "voices", "ghost", "avalon", "bloom"])]
            chosen = pick_first_unused_or_any(cands)
            if chosen:
                return chosen, f"Textura coral sacra para {p.get('artist')}: {chosen}"
        elif role_upper in ("LEAD", "COUNTER_LEAD", "ARP", "EAR_CANDY"):
            cands = [opt for opt in options if any(w in opt.lower() for w in ["lead", "spectral", "agenda", "solo", "drift", "vital"])]
            chosen = pick_first_unused_or_any(cands)
            if chosen:
                return chosen, f"Topline/Lead solista para {p.get('artist')}: {chosen}"
        elif role_upper in ("GUITAR", "RHYTHM_GUITAR", "LEAD_GUITAR"):
            cands = [opt for opt in options if any(w in opt.lower() for w in ["guitar", "flamenco", "nylon", "steel"])]
            chosen = pick_first_unused_or_any(cands)
            if chosen:
                return chosen, f"Guitarra orgánica para {p.get('artist')}: {chosen}"
        elif role_upper in ("BRASS", "HORNS"):
            cands = [opt for opt in options if any(w in opt.lower() for w in ["brass", "horn", "trumpet", "transilvania"])]
            chosen = pick_first_unused_or_any(cands)
            if chosen:
                return chosen, f"Sección de metales para {p.get('artist')}: {chosen}"

        unused_all = [opt for opt in options if not is_already_used(opt)]
        final_pick = unused_all[0] if unused_all else options[0]
        return final_pick, f"Instrumento seleccionado: {final_pick}"

    @classmethod
    def _select_best_fx_option(cls, options: List[str], p: Dict[str, Any]) -> Tuple[str, str]:
        """Selects insert effects profile matching genre aesthetic."""
        genre_low = p.get("genre", "").lower()
        for opt in options:
            if "rock" in genre_low and any(w in opt.lower() for w in ["saturador", "drive", "compressor"]):
                return opt, "Cadena con saturación armónica para Rock."
            if "pop" in genre_low and any(w in opt.lower() for w in ["claridad", "quirúrgica", "glue"]):
                return opt, "Cadena quirúrgica transparente para Pop."
        return options[0], f"Efectos seleccionados: {options[0]}"
