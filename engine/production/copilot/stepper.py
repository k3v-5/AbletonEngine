# engine/production/copilot/stepper.py
"""
Executive Copilot Stepper Engine:
Actively inspects the Ableton Live session state, detects acoustic and musical gaps,
and enforces an interactive decision checklist so the AI never forgets critical production steps.
"""

from typing import List, Dict, Any, Optional, Tuple, Union
from .models import ProductionPhase, DecisionStatus, ProductionDecision, CopilotState


class ExecutiveCopilotEngine:
    """The proactive executive producer that inspects, guides, and enforces session quality."""

    def __init__(self):
        self.current_phase: ProductionPhase = ProductionPhase.PHASE_1_DNA
        self.pending_decisions: Dict[str, ProductionDecision] = {}
        self.resolved_decisions: Dict[str, ProductionDecision] = {}

    def reset(self) -> None:
        """Resets copilot state for a fresh song production session."""
        self.current_phase = ProductionPhase.PHASE_1_DNA
        self.pending_decisions.clear()
        self.resolved_decisions.clear()
        from engine.supervisor.governance import governance_supervisor
        governance_supervisor.reset()

    def inspect_session(
        self,
        conn: Any = None,
        tracks: Optional[List[Dict[str, Any]]] = None,
        clip_notes_map: Optional[Dict[int, List[Dict[str, Any]]]] = None
    ) -> CopilotState:
        """
        Inspects session tracks, clips, and parameters to discover pending decisions.
        Accepts live conn or injected track/clip metadata for mock and offline modes.
        """
        session_tracks = tracks or []
        if conn is not None and not session_tracks:
            try:
                # Fetch tracks from Live
                s_info = conn.send_command("get_session_info", {})
                num_tracks = int(s_info.get("track_count", s_info.get("num_tracks", 0)))
                for t_idx in range(num_tracks):
                    t_info = conn.send_command("get_track_info", {"track_index": t_idx})
                    if isinstance(t_info, dict):
                        t_info.setdefault("track_index", t_info.get("index", t_idx))
                        session_tracks.append(t_info)
            except Exception:
                pass

        # Phase 1 DNA — Always generate on every fresh inspect (idempotent via resolved_decisions check)
        # 1. Sonic Identity & Mood
        dec_mood = ProductionDecision(
            id="DEC-P1-01-CREATIVE-MOOD",
            phase=ProductionPhase.PHASE_1_DNA,
            title="Define Aesthetic Identity, Mood & World-Building",
            description="Establish sonic world: Neo-Soul Groove, warm tape character, intimate dry room space, and vinyl foley texture.",
            recommendation="YES, formulate creative brief with Neo-Soul Groove and Tyler/JID acoustic reference.",
            action_tool="dna_create_creative_brief",
            action_args={"title": "Bones Groove Pt 3", "artist": "Tyler & JID Tribute", "genre": "hip_hop_neo_soul", "reference_preset": "tyler_jid_neo_soul_trap"}
        )
        self._register_pending(dec_mood)

        # 2. Harmonic DNA & Modal Tension
        dec_harm = ProductionDecision(
            id="DEC-P1-02-HARMONIC-DNA",
            phase=ProductionPhase.PHASE_1_DNA,
            title="Establish Harmonic DNA, Modal Borrowing & Tension Level",
            description="Configure root key in F Natural Minor with Dorian/Phrygian modal interchange and 7th/9th extended chord tension.",
            recommendation="YES, configure F minor with Dorian modal borrowing and Drop-2 voicing spread.",
            action_tool="dna_create_creative_brief",
            action_args={"key_root": "F", "scale": "natural_minor", "chord_tension_level": 0.70}
        )
        self._register_pending(dec_harm)

        # 3. Frequency-Reserved Acoustic Scaffolding
        dec_scaffold = ProductionDecision(
            id="DEC-P1-03-TRACK-SCAFFOLD",
            phase=ProductionPhase.PHASE_1_DNA,
            title="Deploy 8-Track Frequency-Reserved Acoustic Scaffolding",
            description="Instantiate Kick, 808 Sub, Snare/Clap, Hi-Hats, Foley Bed, Rhodes Keys, Lead Synth, and Vocal Chops with assigned frequency slots.",
            recommendation="YES, scaffold 8 tracks with DAW colors and Session Graph role tagging.",
            action_tool="dna_scaffold_live_project",
            action_args={"create_cues": True}
        )
        self._register_pending(dec_scaffold)

        # 4. Energy Blueprint & Section Locators
        dec_energy = ProductionDecision(
            id="DEC-P1-04-ENERGY-ROADMAP",
            phase=ProductionPhase.PHASE_1_DNA,
            title="Layout 96-Bar Dynamic Energy Blueprint & Section Locators",
            description="Map Intro (8) -> Verse 1 (16) -> Pre-Chorus (8) -> Chorus (16) -> Verse 2 (16) -> Bridge (8) -> Climax (16) -> Outro (8).",
            recommendation="YES, place arrangement section cue markers and dynamic energy profile.",
            action_tool="dna_scaffold_live_project",
            action_args={"create_cues": True}
        )
        self._register_pending(dec_energy)

        if not session_tracks:
            return self._build_state()

        # Track classification by role
        kick_tracks = []
        bass_tracks = []
        drum_tracks = []
        chord_tracks = []
        lead_tracks = []
        strings_tracks = []
        pad_tracks = []
        foley_tracks = []
        vocal_tracks = []

        for idx, trk in enumerate(session_tracks):
            t_name = str(trk.get("name", "")).lower()
            t_idx = int(trk.get("track_index", trk.get("index", idx)))
            is_group = bool(
                trk.get("is_foldable") or
                trk.get("is_group_track") or
                trk.get("type") == "group" or
                "synths /" in t_name or
                "group" in t_name or
                (t_name.endswith(" bus") or " bus" in t_name)
            )
            is_vocal = any(w in t_name for w in ["vocal", "vox", "chop", "hook"])

            if not is_group and "kick" in t_name:
                kick_tracks.append(t_idx)
            elif not is_group and ("808" in t_name or "bass" in t_name or "sub" in t_name):
                bass_tracks.append(t_idx)
            if any(w in t_name for w in ["drum", "kit", "perc", "break", "snare", "clap", "hat"]):
                drum_tracks.append(t_idx)
            if not is_group and any(w in t_name for w in ["piano", "chord", "key", "rhodes"]):
                chord_tracks.append(t_idx)
            if not is_group and any(w in t_name for w in ["string", "orch", "violin", "cell", "viola", "quartet"]):
                strings_tracks.append(t_idx)
            if not is_group and any(w in t_name for w in ["pad", "atmos", "ambient", "wash"]):
                pad_tracks.append(t_idx)
            if not is_group and not is_vocal and any(w in t_name for w in ["lead", "synth", "pluck"]) and t_idx not in strings_tracks and t_idx not in pad_tracks:
                lead_tracks.append(t_idx)
            if any(w in t_name for w in ["foley", "texture", "rain", "vinyl", "ambient", "ambience"]):
                foley_tracks.append(t_idx)
            if not is_group and is_vocal:
                vocal_tracks.append(t_idx)

        # Sort lead tracks so tracks with "lead" explicitly in name take priority, preserving track order
        lead_tracks.sort(key=lambda t: 0 if "lead" in str(session_tracks[t].get("name", "")).lower() else 1)

        effective_kick = kick_tracks[0] if kick_tracks else (drum_tracks[0] if drum_tracks else None)
        effective_bass = bass_tracks[0] if bass_tracks else None

        # --- PHASE 2: COMPOSITION & HARMONY DECISIONS ---
        if chord_tracks:
            c_idx = chord_tracks[0]
            dec_id = f"DEC-P2-01-HARMONY-T{c_idx}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_2_COMPOSITION,
                    title=f"Compose 96-Bar Harmonic Progression for Track {c_idx}",
                    description="Deploy progressive Drop-2 voicings with smooth conjunct voice leading across all 8 song sections.",
                    recommendation="YES, compose full harmony in F minor with modal interchange.",
                    action_tool="music_compose_full_harmony",
                    action_args={"track_index": c_idx, "key_root": "F", "scale": "natural_minor"},
                    target_track=c_idx
                ))

        if bass_tracks:
            b_idx = bass_tracks[0]
            dec_id = f"DEC-P2-02-BASS-808-T{b_idx}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_2_COMPOSITION,
                    title=f"Compose Interlocking 808 Bassline for Track {b_idx}",
                    description="Interlock 808 with kick downbeats, add chromatic leading tones on turnaround beats, and inject octave leaps on bars 4/8.",
                    recommendation="YES, compose 808 bassline with chromatic approaches.",
                    action_tool="music_compose_808_bassline",
                    action_args={"track_index": b_idx, "key_root": "F", "scale": "natural_minor"},
                    target_track=b_idx
                ))

        if lead_tracks:
            l_idx = lead_tracks[0]
            dec_id = f"DEC-P2-03-TOPLINE-T{l_idx}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_2_COMPOSITION,
                    title=f"Compose Call-and-Response Top-Line Melody for Track {l_idx}",
                    description="Structure melody in 2-bar Call and 2-bar Response phrases with natural vocal respiration and apex climax.",
                    recommendation="YES, compose top-line melody in F minor.",
                    action_tool="music_compose_topline_melody",
                    action_args={"track_index": l_idx, "key_root": "F", "scale": "natural_minor"},
                    target_track=l_idx
                ))

        if vocal_tracks:
            v_idx = vocal_tracks[0]
            dec_id = f"DEC-P2-04-VOCAL-HOOK-T{v_idx}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_2_COMPOSITION,
                    title=f"Generate Syncopated Vocal Hook Chops for Track {v_idx}",
                    description="Deploy infectious 2-bar syncopated hook motifs across Intro, Chorus 1, Bridge, and Final Chorus.",
                    recommendation="YES, generate vocal hook chops.",
                    action_tool="music_compose_vocal_hook",
                    action_args={"track_index": v_idx, "key_root": "F", "scale": "natural_minor"},
                    target_track=v_idx
                ))

        if strings_tracks:
            s_idx = strings_tracks[0]
            dec_id = f"DEC-P2-06-STRINGS-T{s_idx}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_2_COMPOSITION,
                    title=f"Compose Emotive Orchestral Strings Progression for Track {s_idx}",
                    description="Compose sustained orchestral chords, emotional swells, and section transitions in Bb Minor across Chorus and Climax.",
                    recommendation="YES, compose orchestral strings progression.",
                    action_tool="music_compose_full_harmony",
                    action_args={"track_index": s_idx, "key_root": "Bb", "scale": "natural_minor"},
                    target_track=s_idx
                ))

        if pad_tracks:
            p_idx = pad_tracks[0]
            dec_id = f"DEC-P2-07-PAD-T{p_idx}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_2_COMPOSITION,
                    title=f"Compose Lush Atmospheric Pad Voicings for Track {p_idx}",
                    description="Compose wide stereo ambient pad chords with slow attack across Intro, Chorus, and Bridge.",
                    recommendation="YES, compose ambient pad layer.",
                    action_tool="music_compose_full_harmony",
                    action_args={"track_index": p_idx, "key_root": "Bb", "scale": "natural_minor"},
                    target_track=p_idx
                ))

        # --- PHASE 3: INSTRUMENTATION, VSTS & SOUND DESIGN DECISIONS ---
        dec_vst_scan_id = "DEC-P3-01-HOST-VST-SCAN"
        if dec_vst_scan_id not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_vst_scan_id,
                phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                title="Scan Host System for Installed VST3 / Native Plugins",
                description="Audit user's installed plugin ecosystem (Arturia Analog Lab, Serum, Kontakt 8, Omnisphere, Bloom) and categorize by role.",
                recommendation="YES, scan host VST3 plugins and present structured choices.",
                action_tool="instrument_scan_host_vsts",
                action_args={},
                target_track=None
            ))

        if drum_tracks or (effective_kick is not None):
            d_target = drum_tracks[0] if drum_tracks else effective_kick
            dec_id = f"DEC-P3-02-AUTHENTIC-DRUM-RACK-T{d_target}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Load Authentic Sample Drum Rack for Track {d_target}",
                    description=(
                        "Opciones sugeridas para DRUMS (Top 5):\n"
                        "1. [Native Drum Rack] 808 Core Kit (.adg) - TR-808 con booming kick y snappy snares\n"
                        "2. [Native Drum Rack] Boom Bap Kit (.adg) - Baterías acústicas de vinilo y textura analógica\n"
                        "3. [VST3] Bloom Drum Breaks (`vst3_bloom_drums`) - Slicer dinámico de breaks y grooves\n"
                        "4. [VST3] Sugar Bytes Egoist (`vst3_egoist`) - Beat box, slicer y multi-efectos\n"
                        "5. [Native Drum Rack] BNYX Boot Kit (.adg) - Kicks agresivos para rage/drill/trap\n"
                        "(Nota: Hay más opciones disponibles. Consulta con get_available_vst_and_presets(role='drums'))"
                    ),
                    recommendation="YES para cargar opción #1, o CUSTOM con custom_args={'kit_name': '...'} para elegir otra opción.",
                    action_tool="drum_rack_load_authentic_library",
                    action_args={"track_index": d_target, "kit_name": "Tyler_JID_Authentic_Kit", "genre": "neo_soul_trap"},
                    target_track=d_target
                ))

            # --- Drum Rack Quadrant 1 vs 3 Octave Guard Check ---
            from engine.instruments.drum_rack_guard import DrumRackGuard
            drum_audit = None
            if conn is not None and hasattr(conn, "send_command"):
                try:
                    drum_audit = DrumRackGuard.audit_drum_clip_octaves(conn, track_index=d_target, clip_index=0)
                except Exception:
                    drum_audit = None
            elif clip_notes_map and d_target in clip_notes_map:
                c_notes = clip_notes_map[d_target]
                q3_notes = [n for n in c_notes if 60 <= int(n.get("pitch", 0)) <= 75]
                q1_notes = [n for n in c_notes if 36 <= int(n.get("pitch", 0)) <= 51]
                if q3_notes and (len(q1_notes) == 0 or len(q3_notes) >= len(q1_notes)):
                    drum_audit = {
                        "needs_remediation": True,
                        "warning": (
                            f"CRITICAL: Drum Rack pads on Track {d_target} are in Quadrant 1 (C1-D#2, pitches 36-51), "
                            f"but {len(q3_notes)} notes are in Quadrant 3 (C3-D#4, pitches 60-75). "
                            f"Pads are silent! Requires -24 semitone transposition to Quadrant 1."
                        )
                    }

            if drum_audit and drum_audit.get("needs_remediation"):
                dec_octave_fix = f"DEC-P3-02-DRUM-OCTAVE-FIX-T{d_target}"
                if dec_octave_fix not in self.resolved_decisions:
                    self._register_pending(ProductionDecision(
                        id=dec_octave_fix,
                        phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                        title=f"Remediate Drum Rack Quadrant Mismatch on Track {d_target} (-24st to Quadrant 1)",
                        description=drum_audit.get("warning") or (
                            f"Drum Rack pads are located in Quadrant 1 (C1-D#2, pitches 36-51). "
                            f"Clip notes are located in Quadrant 3 (C3+, pitches 60-75). "
                            f"Because Quadrant 3 pads are empty in standard Drum Racks, drums sound SILENT. "
                            f"This action transposes notes down 2 octaves (-24 semitones) so kicks land on C1 (36) and snares on D1 (38)."
                        ),
                        recommendation="YES, transponer notas del clip -24 semitonos al Cuadrante 1 para activar los pads sonoros.",
                        action_tool="drum_rack_transpose_clip_octaves",
                        action_args={"track_index": d_target, "clip_index": 0, "semitone_shift": -24},
                        target_track=d_target
                    ))

            dec_drum_fx = f"DEC-P3-02-DRUM-FX-LOAD-T{d_target}"
            if dec_drum_fx not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_drum_fx,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Load Dynamic Bus / Drum Processor for Track {d_target} (Drum Buss)",
                    description=(
                        "Opciones de Procesamiento de Batería (Top 5):\n"
                        "1. [Native] Drum Buss (`query:AudioFx#Drum%20Buss`) - Punch analógico, saturación Drive y control de transientes\n"
                        "2. [Native] Glue Compressor (`query:AudioFx#Glue%20Compressor`) - Compresión de bus estilo SSL G-Master\n"
                        "3. [VST3] Soundtoys Decapitator (`vst3_decapitator`) - Distorsión analógica cálida\n"
                        "4. [Native] Overdrive (`query:AudioFx#Overdrive`) - Saturación agresiva para transientes\n"
                        "5. [Native] Saturator (`query:AudioFx#Saturator`) - Saturación de cinta analógica\n"
                        "(Nota: Hay más opciones disponibles. Consulta con get_available_vst_and_presets(role='fx'))"
                    ),
                    recommendation="YES para cargar opción #1 (Drum Buss), o CUSTOM con custom_args={'effect_name': '...', 'effect_uri': '...'}.",
                    action_tool="load_track_effect",
                    action_args={"track_index": d_target, "effect_name": "Drum Buss", "effect_uri": "query:AudioFx#Drum%20Buss"},
                    target_track=d_target
                ))

            dec_drum_fx_cfg = f"DEC-P3-02-DRUM-FX-CONFIG-T{d_target}"
            if dec_drum_fx_cfg not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_drum_fx_cfg,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Sculpt Drum Buss Parameters for Track {d_target} (Drive, Crunch, Transients)",
                    description=(
                        "Regla de Gobernanza de Efectos: Cada efecto agregado debe afinar obligatoriamente sus parámetros:\n"
                        "- DRIVE: 0.35 (Compresión analógica cálida)\n"
                        "- CRUNCH: 0.20 (Presencia de armónicos superiores en caja/hats)\n"
                        "- TRANSIENTS: 0.15 (Acentuación del ataque del kick)"
                    ),
                    recommendation="YES para esculpir parámetros recomendados de Drum Buss.",
                    action_tool="sculpt_track_effect",
                    action_args={"track_index": d_target, "device_index": 1, "parameters": {"DRIVE": 0.35, "CRUNCH": 0.20, "TRANSIENTS": 0.15}},
                    target_track=d_target
                ))

        if effective_bass is not None:
            dec_id = f"DEC-P3-03-BASS-INSTRUMENT-LOAD-T{effective_bass}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Load Elite Sub-Bass Instrument for Track {effective_bass}",
                    description=(
                        "Opciones sugeridas para BASS (Top 5):\n"
                        "1. [VST3] Xfer Records Serum 2 Sub (`vst3_serum2`) - 808 sub con saturación directa y glide\n"
                        "2. [VST3] Bloom Bass Impulse (`vst3_bloom_bass_impulse`) - Sub-bass moderno y saturación analógica\n"
                        "3. [VST3] Sugar Bytes Cyclop (`vst3_cyclop`) - Monophonic bass monster con modulación pesada\n"
                        "4. [VST3] Native Instruments Massive X (`vst3_massive_x`) - Subtractive wavetable punch\n"
                        "5. [Native] Ableton Drift 808 Sub (`native_drift_sub`) - Sub analógico monoaural puro\n"
                        "(Nota: Hay más opciones disponibles. Consulta con get_available_vst_and_presets(role='bass'))"
                    ),
                    recommendation="YES para cargar opción #1 (Serum 2), o CUSTOM con custom_args={'instrument_id': '<id>'} para escoger entre las opciones 2 a 5.",
                    action_tool="sound_load_role_instrument",
                    action_args={"track_index": effective_bass, "role": "BASS", "instrument_id": "vst3_serum2"},
                    target_track=effective_bass
                ))

            dec_bass_param = f"DEC-P3-03-BASS-PARAM-CONFIG-T{effective_bass}"
            if dec_bass_param not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_bass_param,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Sculpt Sub-Bass Synthesis Parameters for Track {effective_bass} (Serum 2 / Drift)",
                    description="Esculpe SUB_LEVEL (0.90), DRIVE (0.35) y GLIDE_TIME (85ms) para pegada profunda y articulación limpia.",
                    recommendation="YES para esculpir parámetros recomendados de Sub-Bass.",
                    action_tool="plugin_set_semantic_parameter",
                    action_args={"track_index": effective_bass, "device_index": 0, "semantic_role": "SUB_LEVEL", "value": 0.90},
                    target_track=effective_bass
                ))

            dec_bass_fx = f"DEC-P3-03-BASS-FX-LOAD-T{effective_bass}"
            if dec_bass_fx not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_bass_fx,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Load Analog Saturation Effect for 808 Bass Track {effective_bass} (Saturator)",
                    description=(
                        "Opciones de Efectos para BASS (Top 5):\n"
                        "1. [Native] Saturator (`query:AudioFx#Saturator`) - Calidez analógica y armónicos audibles en móviles\n"
                        "2. [Native] Pedal (`query:AudioFx#Pedal`) - Overdrive y distorsión de circuito analógico\n"
                        "3. [Native] Roar (`query:AudioFx#Roar`) - Saturador multi-etapa con modulación\n"
                        "4. [Native] Overdrive (`query:AudioFx#Overdrive`) - Distorsión con control dinámico de tono\n"
                        "5. [Native] Redux (`query:AudioFx#Redux`) - Bitcrusher sutil para textura lofi\n"
                        "(Nota: Hay más opciones disponibles. Consulta con get_available_vst_and_presets(role='fx'))"
                    ),
                    recommendation="YES para cargar opción #1 (Saturator), o CUSTOM con custom_args={'effect_name': '...', 'effect_uri': '...'}.",
                    action_tool="load_track_effect",
                    action_args={"track_index": effective_bass, "effect_name": "Saturator", "effect_uri": "query:AudioFx#Saturator"},
                    target_track=effective_bass
                ))

            dec_bass_fx_cfg = f"DEC-P3-03-BASS-FX-CONFIG-T{effective_bass}"
            if dec_bass_fx_cfg not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_bass_fx_cfg,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Sculpt Saturator Drive & Warmth Parameters for Bass Track {effective_bass}",
                    description=(
                        "Regla de Gobernanza de Efectos: Cada efecto agregado debe afinar obligatoriamente sus parámetros:\n"
                        "- DRIVE: 0.40 (Añade armónicos audibles entre 100Hz-300Hz)\n"
                        "- BASE: 0.60 (Mantiene los sub-graves por debajo de 60Hz sin distorsión áspera)\n"
                        "- OUTPUT: -2.5 dB (Compensación de ganancia para proteger el headroom)"
                    ),
                    recommendation="YES para esculpir parámetros recomendados de Saturator.",
                    action_tool="sculpt_track_effect",
                    action_args={"track_index": effective_bass, "device_index": 1, "parameters": {"DRIVE": 0.40, "BASE": 0.60, "OUTPUT": -2.5}},
                    target_track=effective_bass
                ))

        if chord_tracks:
            c_idx = chord_tracks[0]
            dec_id = f"DEC-P3-04-KEYS-INSTRUMENT-LOAD-T{c_idx}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Load Expressive Vintage Keys Instrument for Track {c_idx}",
                    description=(
                        "Opciones sugeridas para KEYS (Top 5):\n"
                        "1. [VST3] Arturia Analog Lab V (`vst3_analog_lab`) - Vintage Rhodes, Wurlitzer y polysynths analógicos\n"
                        "2. [VST3] Arturia Stage-73 V2 (`vst3_stage_73`) - Fender Rhodes 73 modelado físico\n"
                        "3. [VST3] Arturia Piano V3 (`vst3_piano_v`) - Pianos acústicos de cola y de concierto\n"
                        "4. [VST3] Native Instruments Kontakt 8 (`vst3_kontakt_8`) - Sampler acústico de máxima fidelidad\n"
                        "5. [VST3] Roland Cloud ZENOLOGY (`vst3_zenology`) - Teclados legendarios Roland Zen-Core\n"
                        "(Nota: Hay más opciones disponibles. Consulta con get_available_vst_and_presets(role='keys'))"
                    ),
                    recommendation="YES para cargar opción #1 (Analog Lab V), o CUSTOM con custom_args={'instrument_id': '<id>'} para escoger entre las opciones 2 a 5.",
                    action_tool="sound_load_role_instrument",
                    action_args={"track_index": c_idx, "role": "KEYS", "instrument_id": "vst3_analog_lab"},
                    target_track=c_idx
                ))

            # Regla de Analog Lab V: PRIMERO escoger instrumento/preset, LUEGO configurar parámetros
            dec_preset_keys = f"DEC-P3-04-PRESET-SELECT-T{c_idx}"
            if dec_preset_keys not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_preset_keys,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Select Specific Preset / Patch for Keys Track {c_idx} (Analog Lab V)",
                    description=(
                        "Regla de Analog Lab V (Paso 1): PRIMERO se debe seleccionar el preset del instrumento dentro de los 14,105 patches antes de configurar los parámetros.\n"
                        "Opciones sugeridas de PRESETS para KEYS (Top 5 auténticos de fábrica):\n"
                        "1. [Arturia Analog Lab V] 'A Rhodes For You' - Teclado Rhodes vintage cálido con chorus analógico sutil\n"
                        "2. [Arturia Analog Lab V] 'American Home Grand' - Gran piano acústico expresivo de máxima fidelidad\n"
                        "3. [Arturia Analog Lab V] 'Ambient Piano Pad' - Piano acústico atmosférico con capas envolventes\n"
                        "4. [Arturia Analog Lab V] 'Classic Jun Keys' - Teclado analógico ochentero modelado de Roland Juno\n"
                        "5. [Arturia Analog Lab V] '28 Synth Harp' - Textura de arpa punteada sintetizada Prophet-VS\n"
                        "(Nota: Hay 14,105 patches disponibles en Arturia DB. Consulta más con preset_search(plugin='Analog Lab V', query='...'))"
                    ),
                    recommendation="YES para cargar opción #1 ('A Rhodes For You'), o CUSTOM con custom_args={'preset_name': '...'} para escoger otro preset.",
                    action_tool="preset_select_for_track",
                    action_args={"track_index": c_idx, "preset_name": "A Rhodes For You", "plugin": "Analog Lab V"},
                    target_track=c_idx
                ))

            dec_param_keys = f"DEC-P3-04-PARAM-CONFIG-T{c_idx}"
            if dec_param_keys not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_param_keys,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Sculpt 10 Hardware Macros & Timbre Controls for Keys Track {c_idx} (Analog Lab V)",
                    description=(
                        "Regla de Analog Lab V (Paso 2): LUEGO de escoger el instrumento/preset, se deben esculpir los 10 macros de hardware:\n"
                        "- BRIGHTNESS: 0.65 (Claridad sin asperezas acústicas)\n"
                        "- TIMBRE: 0.55 (Calidez analógica rica en armónicos)\n"
                        "- TIME: 0.40 (Decay acústico natural de arpa/teclas)\n"
                        "- MOVEMENT: 0.35 (Modulación sutil de chorus/vibrato)\n"
                        "- REVERB: 0.45 (Espacio tridimensional ambiente)"
                    ),
                    recommendation="YES para esculpir macros recomendadas de Keys/Harp, o CUSTOM con custom_args={'semantic_role': '...', 'value': ...}.",
                    action_tool="plugin_set_semantic_parameter",
                    action_args={"track_index": c_idx, "semantic_role": "BRIGHTNESS", "value": 0.65},
                    target_track=c_idx
                ))

            dec_keys_fx = f"DEC-P3-04-KEYS-FX-LOAD-T{c_idx}"
            if dec_keys_fx not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_keys_fx,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Load Lush Spatial Reverb Effect for Keys Track {c_idx} (ValhallaVintageVerb)",
                    description=(
                        "Opciones de Efectos para KEYS (Top 5):\n"
                        "1. [VST3] ValhallaVintageVerb (`query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb`) - Espacio 1980s lush y tridimensional\n"
                        "2. [Native] Hybrid Reverb (`query:AudioFx#Hybrid%20Reverb`) - Reverberación convolutiva analógica\n"
                        "3. [Native] Reverb (`query:AudioFx#Reverb`) - Difusión estéreo natural\n"
                        "4. [Native] Chorus-Ensemble (`query:AudioFx#Chorus-Ensemble`) - Textura vintage tipo Roland Juno\n"
                        "5. [Native] Echo (`query:AudioFx#Echo`) - Delay de cinta analógico cálido\n"
                        "(Nota: Hay más opciones disponibles. Consulta con get_available_vst_and_presets(role='fx'))"
                    ),
                    recommendation="YES para cargar opción #1 (ValhallaVintageVerb), o CUSTOM con custom_args={'effect_name': '...', 'effect_uri': '...'}.",
                    action_tool="load_track_effect",
                    action_args={"track_index": c_idx, "effect_name": "ValhallaVintageVerb", "effect_uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb"},
                    target_track=c_idx
                ))

            dec_keys_fx_cfg = f"DEC-P3-04-KEYS-FX-CONFIG-T{c_idx}"
            if dec_keys_fx_cfg not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_keys_fx_cfg,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Sculpt Reverb Decay & Spatial Depth Parameters for Keys Track {c_idx}",
                    description=(
                        "Regla de Gobernanza de Efectos: Cada efecto agregado debe afinar obligatoriamente sus parámetros:\n"
                        "- DECAY: 2.2 s (Cola suave y etérea)\n"
                        "- PRE_DELAY: 25.0 ms (Separa el ataque transiente del arpa/tecla de la reverberación)\n"
                        "- DRY_WET: 0.35 (35% mezcla wet para preservar la presencia directa)\n"
                        "- LOW_CUT: 250 Hz (Elimina barro en frecuencias bajas)"
                    ),
                    recommendation="YES para esculpir parámetros recomendados de Reverb.",
                    action_tool="sculpt_track_effect",
                    action_args={"track_index": c_idx, "device_index": 1, "parameters": {"DECAY": 2.2, "PRE_DELAY": 25.0, "DRY_WET": 0.35, "LOW_CUT": 250.0}},
                    target_track=c_idx
                ))

        if lead_tracks:
            l_idx = lead_tracks[0]
            dec_id = f"DEC-P3-05-LEAD-INSTRUMENT-LOAD-T{l_idx}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Load Melodic Lead Synthesizer for Track {l_idx}",
                    description=(
                        "Opciones sugeridas para LEAD (Top 5):\n"
                        "1. [VST3] Arturia Pigments (`vst3_pigments`) - Polychrome synth para leads cortantes y texturas\n"
                        "2. [VST3] Xfer Records Serum 2 Lead (`vst3_serum2`) - Unison wavetable con filtro y portamento\n"
                        "3. [VST3] Arturia Analog Lab Lead (`vst3_analog_lab`) - Analog brass y lead vintage\n"
                        "4. [VST3] Sonic Charge Synplant (`vst3_synplant`) - Síntesis genética para leads orgánicos\n"
                        "5. [VST3] Native Instruments Massive X (`vst3_massive_x`) - Dual wavetable solo lead\n"
                        "(Nota: Hay más opciones disponibles. Consulta con get_available_vst_and_presets(role='lead'))"
                    ),
                    recommendation="YES para cargar opción #1 (Pigments), o CUSTOM con custom_args={'instrument_id': '<id>'} para escoger entre las opciones 2 a 5.",
                    action_tool="sound_load_role_instrument",
                    action_args={"track_index": l_idx, "role": "LEAD", "instrument_id": "vst3_pigments"},
                    target_track=l_idx
                ))

            dec_preset_lead = f"DEC-P3-05-PRESET-SELECT-T{l_idx}"
            if dec_preset_lead not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_preset_lead,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Select Specific Preset / Patch for Lead Track {l_idx}",
                    description=(
                        "Opciones sugeridas de PRESETS para LEAD (Top 5):\n"
                        "1. [Arturia Pigments] 'Neo-Soul Sine Lead' - Solo lead sedoso con portamento\n"
                        "2. [Arturia Analog Lab] 'Mini V Detuned Solo' - Saw lead clásico Moog\n"
                        "3. [Xfer Serum 2] 'Plucked Vocal Synth' - Lead agresivo híbrido wavetable\n"
                        "4. [Arturia Analog Lab] 'Brass Horns Solo' - Lead analógico con filtro envelope\n"
                        "5. [Arturia Pigments] 'Granular Harp Textures' - Lead híbrido acústico-digital\n"
                        "(Nota: Hay miles de opciones disponibles. Consulta más con preset_search(query='...'))"
                    ),
                    recommendation="YES para cargar opción #1 ('Neo-Soul Sine Lead'), o CUSTOM con custom_args={'preset_name': '...'}.",
                    action_tool="preset_select_for_track",
                    action_args={"track_index": l_idx, "preset_name": "Neo-Soul Sine Lead", "plugin": "Pigments"},
                    target_track=l_idx
                ))

            dec_param_lead = f"DEC-P3-05-PARAM-CONFIG-T{l_idx}"
            if dec_param_lead not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_param_lead,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Sculpt Semantic Parameters & Filter Envelope for Lead Track {l_idx}",
                    description="Esculpe FILTER_CUTOFF (0.70), FILTER_RESONANCE (0.25) y AMP_ATTACK (0.02) para articulación nítida y presencia central.",
                    recommendation="YES para esculpir parámetros recomendados de Lead.",
                    action_tool="plugin_set_semantic_parameter",
                    action_args={"track_index": l_idx, "semantic_role": "FILTER_CUTOFF", "value": 0.70},
                    target_track=l_idx
                ))

            dec_lead_fx = f"DEC-P3-05-LEAD-FX-LOAD-T{l_idx}"
            if dec_lead_fx not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_lead_fx,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Load Modulated Stereo Delay Effect for Lead Track {l_idx} (ValhallaDelay)",
                    description=(
                        "Opciones de Efectos para LEAD (Top 5):\n"
                        "1. [VST3] ValhallaDelay (`query:Plugins#VST3:Valhalla%20DSP:ValhallaDelay`) - Delay analógico con modulación y pitch drift\n"
                        "2. [Native] Echo (`query:AudioFx#Echo`) - Delay estéreo con filtros HP/LP y saturación\n"
                        "3. [Native] Delay (`query:AudioFx#Delay`) - Ping-pong sync 3/16\n"
                        "4. [Native] Chorus-Ensemble (`query:AudioFx#Chorus-Ensemble`) - Espacio estéreo y ensamble\n"
                        "5. [Native] Phaser-Flanger (`query:AudioFx#Phaser-Flanger`) - Modulación psicodélica\n"
                        "(Nota: Hay más opciones disponibles. Consulta con get_available_vst_and_presets(role='fx'))"
                    ),
                    recommendation="YES para cargar opción #1 (ValhallaDelay), o CUSTOM con custom_args={'effect_name': '...', 'effect_uri': '...'}.",
                    action_tool="load_track_effect",
                    action_args={"track_index": l_idx, "effect_name": "ValhallaDelay", "effect_uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaDelay"},
                    target_track=l_idx
                ))

            dec_lead_fx_cfg = f"DEC-P3-05-LEAD-FX-CONFIG-T{l_idx}"
            if dec_lead_fx_cfg not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_lead_fx_cfg,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Sculpt Delay Feedback & Time Parameters for Lead Track {l_idx}",
                    description=(
                        "Regla de Gobernanza de Efectos: Cada efecto agregado debe afinar obligatoriamente sus parámetros:\n"
                        "- DELAY_TIME: '3/16' (Delay punteado para rebote rítmico)\n"
                        "- FEEDBACK: 0.38 (3 a 4 repeticiones naturales con caída suave)\n"
                        "- DRY_WET: 0.25 (25% wet para flotar detrás de la melodía principal sin enturbiarla)"
                    ),
                    recommendation="YES para esculpir parámetros recomendados de Delay.",
                    action_tool="sculpt_track_effect",
                    action_args={"track_index": l_idx, "device_index": 1, "parameters": {"FEEDBACK": 0.38, "DRY_WET": 0.25}},
                    target_track=l_idx
                ))

        if vocal_tracks:
            v_idx = vocal_tracks[0]
            dec_id = f"DEC-P3-06-VOCAL-SAMPLER-LOAD-T{v_idx}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Load Vocal Engine / Sampler for Track {v_idx}",
                    description=(
                        "Opciones sugeridas para VOCALS (Top 5):\n"
                        "1. [VST3] Bloom Vocal Aether (`vst3_bloom_vocal`) - Atmospheric vocal chops y space reverb\n"
                        "2. [VST3] Antares Auto-Tune Pro (`vst3_autotune`) - Pitch correction y formant shifting\n"
                        "3. [VST3] Bloom Vocal Choir (`vst3_bloom_choir`) - Coros armónicos y ensamble vocal\n"
                        "4. [VST3] Bloom Vocal Edit (`vst3_bloom_vocal_edit`) - Vocal slicing y pitch glides\n"
                        "5. [Native] Ableton Simpler Vocal Chopper (`native_simpler_vocal`) - Sampler rebanado por transientes\n"
                        "(Nota: Hay más opciones disponibles. Consulta con get_available_vst_and_presets(role='vocals'))"
                    ),
                    recommendation="YES para cargar opción #1 (Bloom Vocal Aether), o CUSTOM con custom_args={'instrument_id': '<id>'} para escoger entre las opciones 2 a 5.",
                    action_tool="sound_load_role_instrument",
                    action_args={"track_index": v_idx, "role": "VOCALS", "instrument_id": "vst3_bloom_vocal"},
                    target_track=v_idx
                ))
                dec_param_id = f"DEC-P3-06-VOCAL-PARAM-CONFIG-T{v_idx}"
                if dec_param_id not in self.resolved_decisions:
                    self._register_pending(ProductionDecision(
                        id=dec_param_id,
                        phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                        title=f"Sculpt Vocal Synthesis & Formant Parameters for Track {v_idx}",
                        description="Sculpt formant shift, space, and tone controls for vocal engine.",
                        recommendation="YES to sculpt vocal parameters (SPACE=0.45).",
                        action_tool="plugin_set_semantic_parameter",
                        action_args={"track_index": v_idx, "device_index": 0, "semantic_role": "SPACE", "value": 0.45},
                        target_track=v_idx
                    ))

        if strings_tracks:
            s_idx = strings_tracks[0]
            dec_load_id = f"DEC-P3-08-STRINGS-LOAD-T{s_idx}"
            if dec_load_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_load_id,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Load Authentic Orchestral Strings Instrument for Track {s_idx}",
                    description="Load Ac Strings Orch or expressive ensemble strings.",
                    recommendation="YES, load Ac Strings Orch.",
                    action_tool="sound_load_role_instrument",
                    action_args={"track_index": s_idx, "role": "STRINGS", "instrument_id": "native_strings_orch"},
                    target_track=s_idx
                ))
            dec_sculpt_id = f"DEC-P3-08-STRINGS-PARAM-CONFIG-T{s_idx}"
            if dec_sculpt_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_sculpt_id,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Sculpt Strings Dynamics & Attack Envelope for Track {s_idx}",
                    description="Sculpt dynamic expression, slow attack envelope, and lush stereo space.",
                    recommendation="YES to sculpt strings parameters (SPACE=0.45).",
                    action_tool="plugin_set_semantic_parameter",
                    action_args={"track_index": s_idx, "device_index": 0, "semantic_role": "SPACE", "value": 0.45},
                    target_track=s_idx
                ))

        if pad_tracks:
            p_idx = pad_tracks[0]
            dec_load_id = f"DEC-P3-09-PAD-LOAD-T{p_idx}"
            if dec_load_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_load_id,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Load Warm Analog Pad Instrument for Track {p_idx}",
                    description="Load Warm Analog Pad or VHS Dreams texture.",
                    recommendation="YES, load Warm Analog Pad.",
                    action_tool="sound_load_role_instrument",
                    action_args={"track_index": p_idx, "role": "PAD", "instrument_id": "native_analog_pad"},
                    target_track=p_idx
                ))
            dec_sculpt_id = f"DEC-P3-09-PAD-PARAM-CONFIG-T{p_idx}"
            if dec_sculpt_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_sculpt_id,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Sculpt Analog Pad Filter & Atmosphere for Track {p_idx}",
                    description="Sculpt 24dB LPF filter cutoff and stereo width.",
                    recommendation="YES to sculpt pad parameters (BRIGHTNESS=0.40).",
                    action_tool="plugin_set_semantic_parameter",
                    action_args={"track_index": p_idx, "device_index": 0, "semantic_role": "BRIGHTNESS", "value": 0.40},
                    target_track=p_idx
                ))

        dec_morph_id = "DEC-P3-07-ENERGY-TIMBRE-MORPH"
        if dec_morph_id not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_morph_id,
                phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                title="Apply Section-Based Dynamic Timbre Morphing (96 Bars)",
                description="Inject 96-bar dynamic parameter automation (LPF cutoff sweeps, saturation drive, space expansion) across all 8 song sections.",
                recommendation="YES, apply section-based timbre morphing automation.",
                action_tool="sound_apply_timbre_morph",
                action_args={},
                target_track=None
            ))

        # --- PHASE 4: INTERPRETATION, DYNAMICS & GROOVE DECISIONS ---
        if drum_tracks:
            d_idx = drum_tracks[0]
            dec_id = f"DEC-P4-01-MPC-GROOVE-POOL-T{d_idx}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_4_HUMANIZATION_GROOVE,
                    title=f"Apply MPC 60 Hardware Groove Pool & Swing to Track {d_idx}",
                    description="Applies Roger Linn MPC 60 58% swing timing and velocity multipliers to eradicate mechanical rigidity.",
                    recommendation="YES, apply MPC 60 58% swing groove.",
                    action_tool="groove_apply_hardware_pocket",
                    action_args={"track_index": d_idx, "preset": "mpc_60", "swing_percentage": 58.0},
                    target_track=d_idx
                ))

            dec_ghost_id = f"DEC-P4-04-DRUM-GHOST-NOTES-T{d_idx}"
            if dec_ghost_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_ghost_id,
                    phase=ProductionPhase.PHASE_4_HUMANIZATION_GROOVE,
                    title=f"Inject Dynamic Ghost Notes & Hi-Hat Velocity Waves to Track {d_idx}",
                    description="Injects low-velocity ghost snares on turnaround bars and 4-step wave velocity shaping on hi-hats.",
                    recommendation="YES, inject ghost snares and hat velocity waves.",
                    action_tool="drums_inject_ghost_notes",
                    action_args={"track_index": d_idx},
                    target_track=d_idx
                ))

        if chord_tracks:
            c_idx = chord_tracks[0]
            dec_id = f"DEC-P4-02-CHORD-STRUMMING-T{c_idx}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_4_HUMANIZATION_GROOVE,
                    title=f"Apply Physical Keyboard Strumming Stagger to Track {c_idx}",
                    description="Applies 14 ms finger-roll staggering and tactile velocity tilt across polyphonic Rhodes chords.",
                    recommendation="YES, apply natural chord strumming with alternating direction.",
                    action_tool="harmony_apply_chord_strum",
                    action_args={"track_index": c_idx, "strum_ms": 14.0, "direction": "alternating"},
                    target_track=c_idx
                ))

        if lead_tracks:
            l_idx = lead_tracks[0]
            dec_id = f"DEC-P4-03-LEAD-MPE-EXPRESSION-T{l_idx}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_4_HUMANIZATION_GROOVE,
                    title=f"Inject Continuous MPE Expression & Vibrato to Track {l_idx}",
                    description="Injects initial pitch scoops on phrase attacks and 5.2 Hz sinusoidal vibrato on sustained notes.",
                    recommendation="YES, inject MPE scoops and vibrato curves.",
                    action_tool="expression_apply_mpe_vibrato",
                    action_args={"track_index": l_idx},
                    target_track=l_idx
                ))

        # --- PHASE 5: TRANSITIONS, FX & MACRO NARRATIVE DECISIONS ---
        dec_sec_impacts = "DEC-P5-01-SECTION-IMPACTS"
        if dec_sec_impacts not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_sec_impacts,
                phase=ProductionPhase.PHASE_5_ARRANGEMENT_TRANSITIONS,
                title="Deploy Sub-Booms, Crashes & Downlifters Across All Section Arrivals",
                description="Injects 40Hz sub-booms, atmospheric crashes, and downlifters at section boundaries (bars 0, 8, 32, 48, 64, 72, 88).",
                recommendation="YES, inject section arrival impacts and sub-booms.",
                action_tool="transitions_inject_section_impacts",
                action_args={"track_index": 3},
                target_track=3
            ))

        dec_ten_risers = "DEC-P5-02-TENSION-RISERS"
        if dec_ten_risers not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_ten_risers,
                phase=ProductionPhase.PHASE_5_ARRANGEMENT_TRANSITIONS,
                title="Build 2-Bar Tension Risers & Accelerating Snare Builds (Pre-Drops)",
                description="Generates continuous exponential filter sweeps, pitch-bend noise risers, and snare rolls in bars 30-32 and 70-72.",
                recommendation="YES, build tension risers before Drop 1 and Final Chorus.",
                action_tool="transitions_build_tension_risers",
                action_args={"track_index": 3},
                target_track=3
            ))

        dec_vac_silence = "DEC-P5-03-PRE-DROP-VACUUM"
        if dec_vac_silence not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_vac_silence,
                phase=ProductionPhase.PHASE_5_ARRANGEMENT_TRANSITIONS,
                title="Inject 1-Beat Pre-Drop Acoustic Vacuum Silences (Bars 31 & 71)",
                description="Cuts low-end and rhythm tracks for 1 beat at bars 31.4 and 71.4, creating dramatic contrast before the drop hits.",
                recommendation="YES, apply pre-drop vacuum silences.",
                action_tool="transitions_apply_pre_drop_vacuum",
                action_args={},
                target_track=None
            ))

        dec_ear_candy = "DEC-P5-04-EAR-CANDY-TRANSITIONS"
        if dec_ear_candy not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_ear_candy,
                phase=ProductionPhase.PHASE_5_ARRANGEMENT_TRANSITIONS,
                title="Inject Analog Tape Stop, Reverse Vocal Swells & Reverb Freeze",
                description="Deploys micro-production ear candy: tape stop slowdown in bar 31, reverse vocal swell into chorus, and reverb freeze wash.",
                recommendation="YES, inject ear candy transitions.",
                action_tool="transitions_inject_ear_candy_fx",
                action_args={},
                target_track=None
            ))

        dec_arr_deploy = "DEC-P5-05-ARRANGEMENT-TIMELINE-DEPLOY"
        if dec_arr_deploy not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_arr_deploy,
                phase=ProductionPhase.PHASE_5_ARRANGEMENT_TRANSITIONS,
                title="Deploy All Section Clips to Live Arrangement Timeline Across 96 Bars & Switch View",
                description="Duplicates all session clips onto the physical Arrangement timeline at exact section boundaries (Intro, Verse, Chorus, Bridge, Outro) and switches Live to Arrangement view.",
                recommendation="YES, deploy clips to Arrangement timeline and switch to Arrangement view.",
                action_tool="duplicate_to_arrangement",
                action_args={"deploy_all": True},
                target_track=None
            ))

        # 1. SIDECHAIN CHECK (Kick + 808 present)
        if effective_kick is not None and effective_bass is not None:
            dec_id = f"DEC-P6-SIDECHAIN-T{effective_kick}-T{effective_bass}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_6_MIX_ACOUSTICS,
                    title="Apply Closed-Loop Kick-808 Sidechain Ducking",
                    description=f"Tracks {effective_kick} (Drums) and {effective_bass} (Bass) both produce low-end. Sidechain ducking prevents phase cancellation and protects master headroom.",
                    recommendation="YES, duck -10.0 dB with 110 ms recovery.",
                    action_tool="apply_kick_sidechain_to_bass",
                    action_args={
                        "kick_track_index": effective_kick,
                        "bass_track_index": effective_bass,
                        "ducking_depth_db": -10.0,
                        "release_ms": 110.0
                    },
                    target_track=effective_bass
                ))

        # 2. DRUM POCKET HUMANIZATION CHECK
        for d_idx in drum_tracks:
            dec_id = f"DEC-P4-HUMANIZE-DRUMS-T{d_idx}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_4_HUMANIZATION_GROOVE,
                    title=f"Apply Groove Pocket & Micro-Timing to Track {d_idx}",
                    description="Drums are quantized to grid. Applying authentic micro-timing displacement eliminates robotic stiffness.",
                    recommendation="YES, apply Atlanta Trap pocket with strength 1.0.",
                    action_tool="humanize_track_clip",
                    action_args={"track_index": d_idx, "pocket_style": "atlanta_trap", "strength": 1.0, "role": "drums"},
                    target_track=d_idx
                ))

        # 3. CHORD STRUMMING CHECK
        for c_idx in chord_tracks:
            dec_id = f"DEC-P4-STRUM-CHORDS-T{c_idx}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_4_HUMANIZATION_GROOVE,
                    title=f"Apply Physical Chord Strumming to Track {c_idx}",
                    description="Simultaneous notes in keyboard chords sound artificial. Strumming staggers voice start times like real fingers.",
                    recommendation="YES, apply 12 ms chord strumming with velocity tilt.",
                    action_tool="humanize_track_clip",
                    action_args={"track_index": c_idx, "pocket_style": "neo_soul_dilla", "apply_strum": True, "strength": 1.0, "role": "piano"},
                    target_track=c_idx
                ))

        # 4. 808 SLIDES CHECK
        for b_idx in bass_tracks:
            dec_id = f"DEC-P4-808-SLIDES-T{b_idx}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_4_HUMANIZATION_GROOVE,
                    title=f"Inject 808 Octave Slides to Track {b_idx}",
                    description="Bass sustains static pitches. Injected turnaround octave glides provide signature trap bounce.",
                    recommendation="YES, inject drill octave glides on turnarounds.",
                    action_tool="generate_808_slides",
                    action_args={"track_index": b_idx, "slide_mode": "drill_octave_glide", "turnaround_only": True},
                    target_track=b_idx
                ))

        # 5. 3D DEPTH STAGING CHECK
        for l_idx in lead_tracks:
            dec_id = f"DEC-P6-DEPTH-STAGING-T{l_idx}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_6_MIX_ACOUSTICS,
                    title=f"Configure 3D Spatial Depth Staging for Track {l_idx}",
                    description="Lead instrument needs depth placement and ducked reverb to stay focused in foreground without getting lost.",
                    recommendation="YES, assign Foreground plane with ducked reverb envelope.",
                    action_tool="configure_depth_staging",
                    action_args={"track_index": l_idx, "plane": "foreground", "ducked_reverb": True},
                    target_track=l_idx
                ))

        # 5b. VOCAL HOOK CHOP CHECK
        if (chord_tracks or lead_tracks) and not vocal_tracks:
            dec_id = "DEC-P2-VOCAL-HOOK-CHOPS"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_2_COMPOSITION,
                    title="Generate Scale-Quantized Melodic Vocal Chops Hook",
                    description="Session has harmonic foundation but lacks a signature vocal hook motif. Injecting in-key vocal chops creates an instant memorable identity.",
                    recommendation="YES, generate melodic hook chops with ping-pong stereo motion.",
                    action_tool="generate_vocal_hook_chops",
                    action_args={"track_index": 4, "root": "F", "scale": "minor", "style": "melodic_hook"},
                    target_track=4
                ))

        # 5c. ORGANIC FOLEY BED CHECK
        if not foley_tracks:
            dec_id = "DEC-P3-ORGANIC-FOLEY-BED"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title="Generate Organic Foley & Atmospheric Texture Bed",
                    description="Session lacks environmental ambience. Adding a tempo-synced organic foley bed (vinyl/rain/tape) eliminates sterile digital silence.",
                    recommendation="YES, generate vinyl crackle bed with gentle breathing envelope.",
                    action_tool="generate_organic_foley_bed",
                    action_args={"track_index": 15, "texture_type": "vinyl_crackle", "apply_breathing": True},
                    target_track=15
                ))

        # 5d. DRUM BREAK CHOPPING CHECK
        for d_idx in drum_tracks:
            dec_id = f"DEC-P4-BREAK-CHOPPER-T{d_idx}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_4_HUMANIZATION_GROOVE,
                    title=f"Chop and Resequence Drum Break on Track {d_idx}",
                    description="Drum track can be enriched with classic syncopated transient slicing (Amen Shuffle/Half-Time).",
                    recommendation="YES, chop and resequence with Amen Shuffle style.",
                    action_tool="chop_drum_loop_transients",
                    action_args={"track_index": d_idx, "style": "amen_shuffle", "bars_out": 4.0},
                    target_track=d_idx
                ))

        # 5e. COUNTER-MELODY & ARPEGGIATOR CHECK
        if chord_tracks:
            dec_id = "DEC-P2-COUNTER-MELODY"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_2_COMPOSITION,
                    title="Generate Guide-Tone Counter-Melody & Arpeggiator Layer",
                    description="Session has harmonic chords. Adding a guide-tone counter-melody in off-beats creates harmonic richness and depth.",
                    recommendation="YES, compose guide-tone counter-melody on track 4.",
                    action_tool="generate_counter_melody_and_arp",
                    action_args={"track_index": 4, "style": "counter_melody"},
                    target_track=4
                ))

        # 5f. AUTO-CURATE UNASSIGNED TRACKS CHECK
        dec_curate_id = "DEC-P3-AUTO-CURATE-TRACKS"
        if dec_curate_id not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_curate_id,
                phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                title="Audit and Auto-Curate Unassigned / Empty Session Tracks",
                description="Scans session to detect any uninstrumented tracks, scaffolding Vital/Drum Rack/Grand Piano and safety channel strips.",
                recommendation="YES, auto-curate all session tracks to ensure zero silent channels.",
                action_tool="session_auto_curate",
                action_args={}
            ))

        # 5g. DRUM PATTERN EVOLVER CHECK
        if drum_tracks:
            dec_id = "DEC-P4-DRUM-EVOLVER"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_4_HUMANIZATION_GROOVE,
                    title="Evolve Drum Pattern Monotony with Turnarounds and Fills",
                    description="Static drum loops cause listening fatigue. Injects ghost snares in bar 4 and cascading tom/flam fills in bar 8.",
                    recommendation="YES, evolve drums with bar 4 turnarounds and bar 8 fills.",
                    action_tool="evolve_drum_patterns",
                    action_args={"track_index": drum_tracks[0], "total_bars": 16.0},
                    target_track=drum_tracks[0]
                ))

        # 5g2. GROOVE POOL & POCKET LOCK CHECK
        if drum_tracks or bass_tracks:
            dec_id = "DEC-P4-GROOVE-POOL"
            if dec_id not in self.resolved_decisions:
                ref_tracks = [t for t in (drum_tracks + bass_tracks)]
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_4_HUMANIZATION_GROOVE,
                    title="Apply Iconic Groove Template & Multitrack Pocket Locking",
                    description="Robotic quantization lacks human breathe. Injects iconic hardware swing (MPC 60 / SP-1200 / Dilla) and locks bass micro-timing to the kick pocket.",
                    recommendation="YES, apply MPC 60 58% swing template and lock bass to drum pocket.",
                    action_tool="apply_groove_pool_template",
                    action_args={"track_indices": ref_tracks, "groove_preset": "mpc_60", "swing_percentage": 58.0},
                    target_track=ref_tracks[0]
                ))

        # 5h. TRANSITION RISERS & SWEEPS CHECK
        dec_risers_id = "DEC-P5-TRANSITION-RISERS"
        if dec_risers_id not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_risers_id,
                phase=ProductionPhase.PHASE_5_ARRANGEMENT_TRANSITIONS,
                title="Generate Continuous Transition Risers & Accelerating Snare Rolls",
                description="Transitions between build-ups and drops need energy continuity. Injects exponential Auto Filter sweeps and accelerating snare rolls.",
                recommendation="YES, generate filter sweep and accelerating snare roll into drop.",
                action_tool="generate_transition_risers",
                action_args={"target_bar": 33.0, "duration_bars": 2.0}
            ))

        # 5h2. IMPACTS & DOWNLIFTERS CHECK
        dec_impact_id = "DEC-P5-IMPACTS-DOWNLIFTERS"
        if dec_impact_id not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_impact_id,
                phase=ProductionPhase.PHASE_5_ARRANGEMENT_TRANSITIONS,
                title="Inject Dynamic Downlifter & Sub-Boom Impact on Drop Downbeat",
                description="Arrival at drop downbeat requires dynamic release. Injects exponential downlifter sweep (20kHz -> 150Hz) and sub-boom drop.",
                recommendation="YES, generate downlifter and sub-boom on drop downbeat.",
                action_tool="generate_impact_and_downlifters",
                action_args={"track_index": 13, "impact_type": "downlifter_noise", "target_bar": 33.0}
            ))

        # 5i. AUTO GAIN STAGING & HEADROOM CHECK
        dec_gain_id = "DEC-P6-GAIN-STAGING"
        if dec_gain_id not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_gain_id,
                phase=ProductionPhase.PHASE_6_MIX_ACOUSTICS,
                title="Calibrate Session Gain Staging & Enforce -6 dB Master Headroom",
                description="Faders must be calibrated according to acoustic hierarchy (Kick at -6dBFS, Bass -8.5dBFS, Snare -7dBFS) to deliver clean -6dB headroom to the master bus.",
                recommendation="YES, recalibrate all track faders for -6 dB clean headroom.",
                action_tool="auto_gain_stage_session",
                action_args={"target_master_headroom_db": -6.0}
            ))

        # 6. MASTER DELIVERY CHECK
        dec_master_id = "DEC-P7-MASTER-CHAIN-DELIVERY"
        if dec_master_id not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_master_id,
                phase=ProductionPhase.PHASE_7_MASTER_DELIVERY,
                title="Construct 5-Device Native Mastering Chain & Validate LUFS",
                description="Project requires final mastering chain (Master EQ, Glue, Saturator, Utility, Limiter) compliant with ITU-R BS.1770-5.",
                recommendation="YES, construct chain targeting Streaming (-14.0 LUFS, -0.5 dBTP).",
                action_tool="master_create_chain",
                action_args={"target": "STREAMING"}
            ))

        # 6b. STEM PHASE FORENSICS CHECK
        dec_stem_id = "DEC-P7-STEM-PHASE-AUDIT"
        if dec_stem_id not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_stem_id,
                phase=ProductionPhase.PHASE_7_MASTER_DELIVERY,
                title="Perform Deep Multi-Stem Export & Sub-Bass Phase Correlation Audit",
                description="Audits phase correlation between Kick and Bass stems (detecting destructive phase cancellation rho < -0.30) and validates stem True Peak headroom <= -1.0 dBTP.",
                recommendation="YES, audit stem phase alignment and loudness compliance.",
                action_tool="export_and_audit_stems",
                action_args={"check_phase_correlation": True}
            ))

        # 7. MULTI-TRACK DRUM SETUP CHECK
        if drum_tracks or kick_tracks:
            dec_drum_multi_id = "DEC-P3-MULTITRACK-DRUM-SETUP"
            if dec_drum_multi_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_drum_multi_id,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title="Scaffold Multi-Track Drum Architecture (Kick, Snare, Clap, Hats, Crash)",
                    description="Consolidating all drums on a single stereo track prevents individual transient processing, sidechain routing, and stem export. Scaffolds dedicated tracks with loaded 808/Boom Bap kit.",
                    recommendation="YES, separate drum layers across dedicated tracks.",
                    action_tool="setup_multitrack_drums",
                    action_args={"kit_name": "808 Core Kit"}
                ))

        # 8. BROWSER CATALOG & VST3 DISCOVERY CHECK
        dec_catalog_id = "DEC-P3-BROWSER-CATALOG-INSTRUMENT"
        if dec_catalog_id not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_catalog_id,
                phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                title="Audit Installed VST3 / Native Presets & Curate Realistic Sound Selection",
                description="Avoid blank default devices (empty Drift/default patches). Scans browser catalog to select authentic VSTs (Arturia, Vital, Serum, Spectrasonics) or native packs.",
                recommendation="YES, query browser catalog for role-appropriate instruments.",
                action_tool="get_available_vst_and_presets",
                action_args={}
            ))

        # 9. PHYSICAL SIDECHAIN COMPRESSOR CHECK
        if effective_kick is not None and effective_bass is not None:
            dec_sc_phys_id = f"DEC-P6-PHYSICAL-SIDECHAIN-T{effective_kick}-T{effective_bass}"
            if dec_sc_phys_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_sc_phys_id,
                    phase=ProductionPhase.PHASE_6_MIX_ACOUSTICS,
                    title="Configure Physical Compressor Device Sidechain on 808 Bass",
                    description=f"Configures physical Compressor device on track {effective_bass} with S/C On, fast attack (0.01ms), and 50ms release keyed to kick track {effective_kick}.",
                    recommendation="YES, configure physical compressor sidechain.",
                    action_tool="configure_physical_sidechain",
                    action_args={
                        "kick_track_index": effective_kick,
                        "bass_track_index": effective_bass,
                        "threshold": 0.55,
                        "ratio": 0.75
                    },
                    target_track=effective_bass
                ))

        # 10. CHANNEL STRIP FREQUENCY CONTROL CHECK
        for idx, trk in enumerate(session_tracks):
            t_idx = int(trk.get("track_index", idx))
            t_name = str(trk.get("name", "")).lower()
            dec_id = f"DEC-P6-CHANNEL-STRIP-T{t_idx}"
            if dec_id not in self.resolved_decisions:
                r_label = "keys"
                if "kick" in t_name:
                    r_label = "kick"
                elif "808" in t_name or "bass" in t_name or "sub" in t_name:
                    r_label = "bass"
                elif "snare" in t_name or "clap" in t_name:
                    r_label = "snare"
                elif "hat" in t_name or "perc" in t_name or "crash" in t_name:
                    r_label = "hats"
                elif "lead" in t_name or "synth" in t_name:
                    r_label = "lead"
                elif "vocal" in t_name or "vox" in t_name or "chop" in t_name:
                    r_label = "vocal"
                elif "foley" in t_name or "texture" in t_name:
                    r_label = "foley"

                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_6_MIX_ACOUSTICS,
                    title=f"Apply Surgical Channel Strip & HPF to Track {t_idx} ({t_name or r_label})",
                    description=f"Carves out sub-rumble and mud, shaping {r_label} frequencies with calibrated EQ Eight filter curves.",
                    recommendation=f"YES, apply {r_label} channel strip with high-pass filtering.",
                    action_tool="apply_track_channel_strip",
                    action_args={"track_index": t_idx, "role": r_label},
                    target_track=t_idx
                ))

        # 11. GROUP BUS PROCESSING CHECK
        dec_bus_id = "DEC-P6-BUS-PROCESSING"
        if dec_bus_id not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_bus_id,
                phase=ProductionPhase.PHASE_6_MIX_ACOUSTICS,
                title="Apply Group Bus Processing (Drum Buss & Synth Glue)",
                description="Processes Drum Bus with Drum Buss (Drive, Transients, Glue) and Synth Bus with Glue Compressor and harmonic EQ carving.",
                recommendation="YES, apply group bus processing across drums and instrument stems.",
                action_tool="apply_group_bus_processing",
                action_args={"group_track_index": 0, "bus_type": "drums"}
            ))

        # 12. PHYSICAL LIVE MASTERING CHAIN CHECK
        dec_master_live_id = "DEC-P7-LIVE-MASTERING-CHAIN"
        if dec_master_live_id not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_master_live_id,
                phase=ProductionPhase.PHASE_7_MASTER_DELIVERY,
                title="Deploy Physical 5-Device Native Mastering Chain in Live",
                description="Installs physical EQ Eight, Glue Compressor, Saturator, Utility (Bass Mono <120Hz), and Limiter (-1.0 dBTP) on Pre-Master / Master bus.",
                recommendation="YES, deploy 5-device chain targeting Streaming (-14 LUFS, -1.0 dBTP).",
                action_tool="setup_full_mastering_chain",
                action_args={"track_index": 12, "target_profile": "STREAMING"}
            ))

        # 13. ADAPTIVE DE-ESSER & SIBILANCE CONTROL CHECK
        if vocal_tracks or lead_tracks:
            v_target = vocal_tracks[0] if vocal_tracks else lead_tracks[0]
            dec_deess_id = f"DEC-P6-ADAPTIVE-DEESSER-T{v_target}"
            if dec_deess_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_deess_id,
                    phase=ProductionPhase.PHASE_6_MIX_ACOUSTICS,
                    title=f"Deploy Adaptive De-Esser on Track {v_target}",
                    description="Vocal/Lead high frequencies contain harsh sibilance ('S', 'T', 'CH'). De-Esser suppresses harshness dynamically at 6.8 kHz without dulling high-end air.",
                    recommendation="YES, deploy adaptive bandpass de-esser at 6.8 kHz.",
                    action_tool="apply_adaptive_deesser",
                    action_args={"track_index": v_target, "target_sibilance_freq": 6800.0, "threshold": 0.65},
                    target_track=v_target
                ))

        # 14. COMMERCIAL RELEASE PACKAGE BUNDLER CHECK
        dec_release_id = "DEC-P7-COMMERCIAL-RELEASE-PACKAGE"
        if dec_release_id not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_release_id,
                phase=ProductionPhase.PHASE_7_MASTER_DELIVERY,
                title="Generate Full Commercial Release Package & Distribution Manifest",
                description="Builds production release bundle: 24-bit Lossless Master, 16-bit CD Dithered Master, 320k MP3, Instrumental, Acapella, Multi-Stems, and release_manifest.json with ISRC/UPC.",
                recommendation="YES, export complete market-ready commercial release package.",
                action_tool="export_commercial_release_package",
                action_args={"song_title": "Master Track", "target_profile": "STREAMING"}
            ))

        # 10. PHYSICAL ARRANGEMENT AUTOMATIONS CHECK
        dec_auto_phys_id = "DEC-P5-PHYSICAL-ARRANGEMENT-AUTOMATIONS"
        if dec_auto_phys_id not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_auto_phys_id,
                phase=ProductionPhase.PHASE_5_ARRANGEMENT_TRANSITIONS,
                title="Inject Physical Arrangement Filter Sweeps & Pre-Drop Vacuum Silences",
                description="Applies automated low-pass filter opening builds into transitions and injects pre-drop negative space vacuums at the end of the pre-chorus.",
                recommendation="YES, inject physical filter sweeps and drop silence.",
                action_tool="apply_physical_arrangement_automations",
                action_args={
                    "track_indices": [t for t in (drum_tracks + bass_tracks + chord_tracks + lead_tracks)],
                    "drop_bar": 33.0,
                    "vacuum_beats": 2.0
                }
            ))

        # 15. FREQUENCY SLOTTING CHECK (PHASE 6)
        dec_slot_id = "DEC-P6-FREQUENCY-SLOTTING"
        if dec_slot_id not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_slot_id,
                phase=ProductionPhase.PHASE_6_MIX_ACOUSTICS,
                title="Apply Multitrack Complementary Frequency Slotting & High-Pass Filtering",
                description="Enforces surgical HPF across all 8 tracks and carves interlocking EQ pockets (Kick vs 808 sub, Lead vs Chords, Snare vs Keys).",
                recommendation="YES, apply surgical frequency slotting across all 8 tracks.",
                action_tool="mix_apply_frequency_slotting",
                action_args={}
            ))

        # 16. PHASE & MONO AUDIT CHECK (PHASE 6)
        dec_phase_id = "DEC-P6-PHASE-MONO-AUDIT"
        if dec_phase_id not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_phase_id,
                phase=ProductionPhase.PHASE_6_MIX_ACOUSTICS,
                title="Audit Multitrack Phase Coherence & Enforce Sub-Bass Mono Collapse",
                description="Audits Pearson correlation between Kick and Bass and forces sub-bass below 120Hz to mono via Utility.",
                recommendation="YES, audit phase coherence and apply sub-bass mono collapse.",
                action_tool="mix_audit_phase_and_mono_compatibility",
                action_args={}
            ))

        # 17. FADER RIDING CHECK (PHASE 6)
        dec_fader_id = "DEC-P6-FADER-RIDING"
        if dec_fader_id not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_fader_id,
                phase=ProductionPhase.PHASE_6_MIX_ACOUSTICS,
                title="Deploy Continuous Vocal & Lead Dynamic Fader Riding Across 96 Bars",
                description="Injects section-aware fader riding curves (-2.5dB Intro to +2.8dB Final Chorus) to ensure consistent upfront intelligibility.",
                recommendation="YES, deploy dynamic fader riding automation.",
                action_tool="mix_apply_vocal_lead_fader_riding",
                action_args={"track_index": 4, "role": "vocal"}
            ))

        # 18. MULTITRACK SIDECHAIN CHECK (PHASE 6)
        dec_sc_id = "DEC-P6-MULTITRACK-SIDECHAIN"
        if dec_sc_id not in self.resolved_decisions:
            self._register_pending(ProductionDecision(
                id=dec_sc_id,
                phase=ProductionPhase.PHASE_6_MIX_ACOUSTICS,
                title="Configure Multitrack Sidechain Compression Matrix (Kick, Bass, Vocal, Space)",
                description="Establishes automated dynamic ducking between Kick->Bass, Vocal->Chords, and Kick->Reverb.",
                recommendation="YES, configure full multitrack sidechain matrix.",
                action_tool="mix_apply_multitrack_sidechain_ducking",
                action_args={}
            ))

        return self._build_state()

    def _register_pending(self, dec: ProductionDecision):
        if dec.id not in self.pending_decisions and dec.id not in self.resolved_decisions:
            self.pending_decisions[dec.id] = dec

    def _build_state(self) -> CopilotState:
        pending_list = list(self.pending_decisions.values())
        resolved_list = list(self.resolved_decisions.values())
        total_decisions = max(1, len(pending_list) + len(resolved_list))
        progress = (len(resolved_list) / total_decisions) * 100.0

        # Current phase is the phase of the oldest pending decision
        curr_phase = pending_list[0].phase if pending_list else ProductionPhase.PHASE_7_MASTER_DELIVERY

        blockers = []
        for d in pending_list:
            if d.phase in [
                ProductionPhase.PHASE_3_SOUND_DESIGN,
                ProductionPhase.PHASE_4_HUMANIZATION_GROOVE,
                ProductionPhase.PHASE_6_MIX_ACOUSTICS
            ]:
                blockers.append(f"Unresolved critical decision: '{d.title}' ({d.id})")

        from engine.supervisor.governance import governance_supervisor
        for unconf in governance_supervisor.get_unconfigured_devices():
            blockers.append(
                f"Unconfigured device on Track {unconf['track_index']} ({unconf['device_name']}) - parameter sculpting required"
            )
        for t_idx, d_idx in governance_supervisor._pending_effect_sculpting.items():
            blockers.append(
                f"Unconfigured effect on Track {t_idx} (Device {d_idx}) - effect parameter tuning required"
            )

        return CopilotState(
            current_phase=curr_phase,
            completed_phases=[],
            pending_decisions=pending_list,
            resolved_decisions=resolved_list,
            progress_pct=progress,
            blockers=blockers
        )

    def execute_decision(
        self,
        decision_id: str,
        choice: str = "YES",
        justification: Optional[str] = None,
        custom_args: Optional[Dict[str, Any]] = None,
        conn: Any = None
    ) -> Dict[str, Any]:
        """
        Executes an interactive decision:
        - 'YES': runs the action tool and marks APPLIED.
        - 'NO': records justification and marks REJECTED (conscious opt-out).
        - 'CUSTOM': applies user-supplied overrides.
        """
        dec = self.pending_decisions.get(decision_id)
        if not dec:
            return {"status": "error", "message": f"Decision '{decision_id}' not found in pending list"}

        ch = choice.strip().upper()

        if ch == "NO":
            dec.status = DecisionStatus.REJECTED
            dec.justification_if_rejected = justification or "Consciously omitted by producer intent"
            self.resolved_decisions[dec.id] = dec
            del self.pending_decisions[dec.id]
            return {
                "status": "success",
                "decision_id": dec.id,
                "action": "REJECTED",
                "justification": dec.justification_if_rejected
            }

        # YES or CUSTOM -> Apply
        args = custom_args if (ch == "CUSTOM" and custom_args) else dec.action_args
        execution_res = {"status": "dispatched", "tool": dec.action_tool, "args": args}

        # Always synchronize with governance supervisor
        try:
            from engine.supervisor.governance import governance_supervisor
            if dec.action_tool == "sound_load_role_instrument":
                t_idx = int(args.get("track_index", 0))
                inst_id = str(args.get("instrument_id", "vst3_analog_lab"))
                governance_supervisor.notify_instrument_loaded(track_index=t_idx, instrument_name=inst_id)
            elif dec.action_tool == "drum_rack_load_authentic_library":
                t_idx = int(args.get("track_index", 0))
                kit = str(args.get("kit_name", "808 Core Kit"))
                governance_supervisor.notify_instrument_loaded(track_index=t_idx, instrument_name=f"Drum Rack ({kit})")
                governance_supervisor.record_device_sculpted(track_index=t_idx, device_index=0, parameters={"KIT_LOADED": 1.0, "AUTHENTIC_SAMPLES": 1.0})
            elif dec.action_tool == "preset_select_for_track":
                t_idx = int(args.get("track_index", 0))
                p_name = str(args.get("preset_name", "Default Preset"))
                governance_supervisor.record_preset_selected(track_index=t_idx, preset_name=p_name)
            elif dec.action_tool == "plugin_set_semantic_parameter":
                t_idx = int(args.get("track_index", 0))
                d_idx = int(args.get("device_index", 0))
                s_role = str(args.get("semantic_role", "BRIGHTNESS"))
                s_val = float(args.get("value", 0.65))
                governance_supervisor.record_device_sculpted(track_index=t_idx, device_index=d_idx, parameters={s_role: s_val})
            elif dec.action_tool == "load_track_effect":
                t_idx = int(args.get("track_index", 0))
                fx_name = str(args.get("effect_name", "Saturator"))
                governance_supervisor.request_add_effect(track_index=t_idx, effect_name=fx_name)
            elif dec.action_tool == "sculpt_track_effect":
                t_idx = int(args.get("track_index", 0))
                d_idx = int(args.get("device_index", 1))
                params = args.get("parameters", {"DRIVE": 0.40})
                if not params:
                    params = {"DRIVE": 0.40}
                governance_supervisor.record_effect_sculpted(track_index=t_idx, device_index=d_idx, parameters=params)
        except Exception as e:
            execution_res["governance_warning"] = str(e)

        # If live conn available, dispatch command directly
        if conn is not None and hasattr(conn, "send_command"):
            try:
                if dec.action_tool == "apply_kick_sidechain_to_bass":
                    from engine.mix.sidechain import AutoSidechainDucker
                    AutoSidechainDucker.apply_sidechain_to_track(
                        adapter=conn,
                        bass_track_index=args.get("bass_track_index", 6),
                        kick_strike_beats=[0.0, 1.75, 2.5, 4.0, 5.75]
                    )
                elif dec.action_tool == "generate_organic_foley_bed":
                    from engine.sound.foley.texture import OrganicTextureGenerator
                    OrganicTextureGenerator.configure_foley_bed(
                        conn=conn,
                        track_index=args.get("track_index", 15),
                        texture_type=args.get("texture_type", "vinyl_crackle"),
                        bpm=args.get("bpm", 120.0),
                        apply_breathing=args.get("apply_breathing", True)
                    )
                elif dec.action_tool == "chop_drum_loop_transients":
                    from engine.audio.chopper.transient import TransientBreakChopper
                    TransientBreakChopper.chop_and_resequence(
                        conn=conn,
                        track_index=args.get("track_index", 13),
                        style=args.get("style", "amen_shuffle"),
                        bars_out=args.get("bars_out", 4.0)
                    )
                elif dec.action_tool == "generate_vocal_hook_chops":
                    from engine.vocal.chopper import VocalChopperEngine
                    VocalChopperEngine.generate_and_apply_vocal_chops(
                        conn=conn,
                        track_index=args.get("track_index", 4),
                        root=args.get("root", "F"),
                        scale=args.get("scale", "minor"),
                        style=args.get("style", "melodic_hook"),
                        total_bars=args.get("total_bars", 4.0)
                    )
                elif dec.action_tool == "generate_transition_risers":
                    from engine.arrangement.transitions.risers import TransitionRisersEngine
                    TransitionRisersEngine.apply_transition_riser(
                        conn=conn,
                        track_index=args.get("track_index", 13),
                        target_bar=args.get("target_bar", 33.0),
                        duration_bars=args.get("duration_bars", 2.0)
                    )
                elif dec.action_tool == "evolve_drum_patterns":
                    from engine.music.drums.evolver import DrumPatternEvolver
                    DrumPatternEvolver.apply_drum_evolution(
                        conn=conn,
                        track_index=args.get("track_index", 13),
                        total_bars=args.get("total_bars", 16.0)
                    )
                elif dec.action_tool == "session_auto_curate":
                    from engine.sound.curator.auto_curate import SessionAutoCuratorEngine
                    SessionAutoCuratorEngine.auto_curate_session(conn=conn)
                elif dec.action_tool == "generate_counter_melody_and_arp":
                    from engine.music.melody.counterpoint import CounterpointEngine
                    CounterpointEngine.apply_counterpoint(
                        conn=conn,
                        track_index=args.get("track_index", 4),
                        style=args.get("style", "counter_melody")
                    )
                elif dec.action_tool == "auto_gain_stage_session":
                    from engine.mix.gain_staging.auto_stager import AutoGainStagingEngine
                    AutoGainStagingEngine.apply_gain_staging(
                        conn=conn,
                        target_master_headroom_db=args.get("target_master_headroom_db", -6.0)
                    )
                elif dec.action_tool == "generate_impact_and_downlifters":
                    from engine.arrangement.impacts.downlifters import ImpactEngine, ImpactType
                    imp_type = ImpactType(args.get("impact_type", "downlifter_noise"))
                    ImpactEngine.apply_impact_to_live(
                        conn=conn,
                        track_index=args.get("track_index", 13),
                        impact_type=imp_type,
                        target_bar=args.get("target_bar", 33.0),
                        duration_bars=args.get("duration_bars", 2.0)
                    )
                elif dec.action_tool == "export_and_audit_stems":
                    from engine.audio.stem_audit import StemAuditor
                    StemAuditor.apply_stem_audit_adapter(
                        conn=conn,
                        export_dir=args.get("export_dir")
                    )
                elif dec.action_tool == "apply_groove_pool_template":
                    from engine.music.groove.pool import GroovePoolEngine, GroovePreset
                    preset = GroovePreset(args.get("groove_preset", "mpc_60"))
                    GroovePoolEngine.apply_groove_to_live_clip(
                        conn=conn,
                        track_indices=args.get("track_indices", [0]),
                        groove_preset=preset,
                        swing_percentage=args.get("swing_percentage", 58.0)
                    )
                elif dec.action_tool == "setup_multitrack_drums":
                    from engine.music.drums.multitrack import MultiTrackDrumEngine
                    MultiTrackDrumEngine.scaffold_drum_tracks(
                        conn=conn,
                        kit_type=args.get("kit_type", "808_core")
                    )
                elif dec.action_tool == "get_available_vst_and_presets":
                    from engine.instruments.browser_catalog import BrowserCatalogEngine
                    BrowserCatalogEngine.list_all_available_instruments(conn=conn)
                elif dec.action_tool == "configure_physical_sidechain":
                    from engine.mix.sidechain_manager import SidechainManager
                    SidechainManager.configure_sidechain(
                        conn=conn,
                        bass_track_index=args.get("bass_track_index", 7),
                        kick_track_index=args.get("kick_track_index", 2),
                        threshold=args.get("threshold", 0.55),
                        ratio=args.get("ratio", 0.75)
                    )
                elif dec.action_tool == "apply_physical_arrangement_automations":
                    from engine.arrangement.automation.live_automation import LiveAutomationEngine
                    t_indices = args.get("track_indices", [4])
                    lead_t = t_indices[0] if t_indices else 4
                    LiveAutomationEngine.apply_filter_sweep(
                        conn=conn,
                        track_index=lead_t,
                        start_bar=args.get("start_bar", 29.0),
                        duration_bars=args.get("duration_bars", 4.0)
                    )
                    LiveAutomationEngine.apply_pre_drop_vacuum(
                        conn=conn,
                        track_indices=t_indices,
                        drop_bar=args.get("drop_bar", 33.0),
                        vacuum_beats=args.get("vacuum_beats", 2.0)
                    )
                elif dec.action_tool == "apply_track_channel_strip":
                    from engine.mix.channel_strip import ChannelStripEngine
                    ChannelStripEngine.apply_channel_strip(
                        conn=conn,
                        track_index=args.get("track_index", 0),
                        role=args.get("role", "lead")
                    )
                elif dec.action_tool == "apply_group_bus_processing":
                    from engine.mix.channel_strip import ChannelStripEngine
                    ChannelStripEngine.apply_bus_processing(
                        conn=conn,
                        group_track_index=args.get("group_track_index", 0),
                        bus_type=args.get("bus_type", "drums")
                    )
                elif dec.action_tool == "setup_full_mastering_chain":
                    from engine.mastering.live_master_chain import LiveMasterChainEngine
                    LiveMasterChainEngine.setup_live_mastering_chain(
                        conn=conn,
                        track_index=args.get("track_index", 12),
                        target_profile=args.get("target_profile", "STREAMING")
                    )
                elif dec.action_tool == "apply_adaptive_deesser":
                    from engine.mix.eq.dynamic_eq import DynamicEQEngine
                    DynamicEQEngine.apply_adaptive_deesser(
                        conn=conn,
                        track_index=args.get("track_index", 4),
                        target_sibilance_freq=args.get("target_sibilance_freq", 6800.0),
                        threshold=args.get("threshold", 0.65)
                    )
                elif dec.action_tool == "mix_apply_frequency_slotting":
                    from engine.mix.frequency_slotting import FrequencySlottingEngine
                    FrequencySlottingEngine.generate_full_session_slotting_plan()
                elif dec.action_tool == "mix_audit_phase_and_mono_compatibility":
                    from engine.mix.phase_alignment import PhaseAlignmentEngine
                    PhaseAlignmentEngine.generate_phase_audit_report()
                elif dec.action_tool == "mix_apply_vocal_lead_fader_riding":
                    from engine.mix.fader_rider import VocalLeadFaderRider
                    VocalLeadFaderRider.get_fader_riding_manifest()
                elif dec.action_tool == "mix_apply_multitrack_sidechain_ducking":
                    from engine.mix.multitrack_sidechain import MultiTrackSidechainCoordinator
                    MultiTrackSidechainCoordinator.get_multitrack_sidechain_matrix()
                elif dec.action_tool == "export_commercial_release_package":
                    from engine.mastering.release_package import CommercialReleasePackager
                    CommercialReleasePackager.create_release_package(
                        output_directory=args.get("output_directory") or str(Path.home() / "Music" / "Mastered_Releases"),
                        song_title=args.get("song_title", "Master Track"),
                        artist_name=args.get("artist_name", "Producer"),
                        target_profile=args.get("target_profile", "STREAMING")
                    )
                elif dec.action_tool == "preset_select_for_track":
                    from engine.presets.catalog import preset_catalog
                    from engine.midi.program_change import program_change_dispatcher
                    from engine.presets.analog_lab_ui_automator import analog_lab_ui_automator
                    t_idx = int(args.get("track_index", 0))
                    p_name = str(args.get("preset_name", ""))
                    p_plugin = str(args.get("plugin", ""))
                    candidates = preset_catalog.search_presets(query=p_name, plugin=p_plugin, limit=1)
                    if candidates and candidates[0].get("loading_method") == "user_library_adv" and candidates[0].get("browser_uri"):
                        conn.send_command("load_browser_item", {"track_index": t_idx, "item_uri": candidates[0].get("browser_uri")})
                    else:
                        if "analog lab" in (p_plugin or "").lower() or "analog lab" in p_name.lower():
                            analog_lab_ui_automator.select_preset(
                                preset_name=p_name,
                                track_index=t_idx,
                                conn=conn
                            )
                        pc_id = candidates[0].get("program_change_id", 0) if candidates else 0
                        bank_id = candidates[0].get("bank", 0) if candidates else 0
                        program_change_dispatcher.send_program_change(
                            conn=conn,
                            track_index=t_idx,
                            program=pc_id,
                            bank=bank_id,
                            plugin_name=p_plugin or "Analog Lab V"
                        )
                    # Reflect preset visibly on track name in Live session
                    if conn and hasattr(conn, "send_command"):
                        try:
                            t_info = conn.send_command("get_track_info", {"track_index": t_idx})
                            tr = t_info.get("result", t_info) if isinstance(t_info, dict) else {}
                            cur_name = tr.get("name", f"Track {t_idx}")
                            base_name = cur_name.split("[")[0].strip() if "[" in cur_name else cur_name
                            conn.send_command("set_track_name", {"track_index": t_idx, "name": f"{base_name} [{p_name}]"})
                        except Exception:
                            pass
                elif dec.action_tool in ["drum_rack_transpose_clip_octaves", "remediate_drum_clip_octaves"]:
                    from engine.instruments.drum_rack_guard import DrumRackGuard
                    t_idx = int(args.get("track_index", 0))
                    c_idx = int(args.get("clip_index", 0))
                    shift = int(args.get("semitone_shift", -24))
                    DrumRackGuard.remediate_drum_clip_octaves(conn=conn, track_index=t_idx, clip_index=c_idx, semitone_shift=shift)
                elif dec.action_tool == "plugin_set_semantic_parameter":
                    from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
                    t_idx = int(args.get("track_index", 0))
                    d_idx = int(args.get("device_index", 0))
                    s_role = str(args.get("semantic_role", "BRIGHTNESS"))
                    s_val = float(args.get("value", 0.65))
                    DeviceParameterSupervisor.apply_semantic_tuning(conn, t_idx, d_idx, "", {s_role: s_val})
                elif dec.action_tool == "sound_load_role_instrument":
                    from engine.instruments.installed_scanner import InstalledPluginScanner
                    t_idx = int(args.get("track_index", 0))
                    role = str(args.get("role", "KEYS"))
                    inst_id = str(args.get("instrument_id", "vst3_analog_lab"))
                    scanner = InstalledPluginScanner()
                    scanned = scanner.scan()
                    target_uri = None
                    inst_display_name = inst_id
                    if inst_id in scanned:
                        target_uri = scanned[inst_id].uri
                        inst_display_name = scanned[inst_id].name
                    else:
                        rec = scanner.recommend_for_role(role=role)
                        target_uri = rec.uri
                        inst_display_name = rec.name
                    if target_uri:
                        conn.send_command("load_browser_item", {"track_index": t_idx, "item_uri": target_uri})
                        # POST-LOAD VALIDATION: Verify instrument actually loaded in Live
                        try:
                            verify_info = conn.send_command("get_track_info", {"track_index": t_idx})
                            devices = verify_info.get("devices", verify_info.get("result", {}).get("devices", [])) if isinstance(verify_info, dict) else []
                            loaded_names = [str(d.get("name", "")).lower() for d in devices]
                            inst_lower = inst_display_name.lower().replace("vst3_", "").replace("_", " ")
                            verified = any(inst_lower in n or n in inst_lower for n in loaded_names)
                            if not verified:
                                execution_res["load_verified"] = False
                                execution_res["load_warning"] = (
                                    f"MANDATORY VALIDATION FAILED: Instrument '{inst_display_name}' was NOT found "
                                    f"in Track {t_idx} device chain after load_browser_item. "
                                    f"Devices found: {loaded_names}. "
                                    f"Re-execute this decision with a valid instrument_id."
                                )
                            else:
                                execution_res["load_verified"] = True
                                execution_res["verified_device"] = inst_display_name
                        except Exception as ve:
                            execution_res["load_verified"] = False
                            execution_res["load_warning"] = f"Post-load verification error: {ve}"
                    else:
                        execution_res["load_failed"] = True
                        execution_res["load_error"] = (
                            f"MANDATORY: No URI found for instrument '{inst_id}' (role={role}). "
                            f"Use get_available_vst_and_presets() to discover valid instrument IDs, "
                            f"then re-execute with custom_args={{'instrument_id': '<valid_id>'}}."
                        )
                elif dec.action_tool == "drum_rack_load_authentic_library":
                    t_idx = int(args.get("track_index", 0))
                    kit_uri = str(args.get("kit_uri", "query:Drums#FileId_5422"))
                    conn.send_command("load_browser_item", {"track_index": t_idx, "item_uri": kit_uri})
                    # POST-LOAD VALIDATION: Verify Drum Rack actually loaded
                    try:
                        verify_info = conn.send_command("get_track_info", {"track_index": t_idx})
                        devices = verify_info.get("devices", verify_info.get("result", {}).get("devices", [])) if isinstance(verify_info, dict) else []
                        has_drum_rack = any("drum" in str(d.get("name", "")).lower() for d in devices)
                        execution_res["load_verified"] = has_drum_rack
                        if not has_drum_rack:
                            execution_res["load_warning"] = (
                                f"MANDATORY VALIDATION FAILED: Drum Rack not found in Track {t_idx} "
                                f"after load attempt. Devices present: {[d.get('name') for d in devices]}. "
                                f"Retry with a valid drum rack URI."
                            )
                    except Exception as ve:
                        execution_res["load_verified"] = False
                        execution_res["load_warning"] = f"Post-load drum rack verification error: {ve}"
                elif dec.action_tool == "load_track_effect":
                    t_idx = int(args.get("track_index", 0))
                    fx_uri = str(args.get("effect_uri", "query:AudioFx#Saturator"))
                    fx_name = str(args.get("effect_name", "Effect"))
                    conn.send_command("load_browser_item", {"track_index": t_idx, "item_uri": fx_uri})
                    # POST-LOAD VALIDATION: Verify effect appeared in device chain
                    try:
                        verify_info = conn.send_command("get_track_info", {"track_index": t_idx})
                        devices = verify_info.get("devices", verify_info.get("result", {}).get("devices", [])) if isinstance(verify_info, dict) else []
                        fx_lower = fx_name.lower()
                        found_fx = any(fx_lower in str(d.get("name", "")).lower() for d in devices)
                        execution_res["load_verified"] = found_fx
                        if not found_fx:
                            execution_res["load_warning"] = (
                                f"MANDATORY VALIDATION FAILED: Effect '{fx_name}' not confirmed "
                                f"in Track {t_idx} device chain after load. "
                                f"Found devices: {[d.get('name') for d in devices]}. "
                                f"Retry with correct effect_uri or choose an alternative effect."
                            )
                    except Exception as ve:
                        execution_res["load_verified"] = False
                        execution_res["load_warning"] = f"Post-load effect verification error: {ve}"

                elif dec.action_tool == "sculpt_track_effect":
                    from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
                    t_idx = int(args.get("track_index", 0))
                    d_idx = int(args.get("device_index", 1))
                    params = args.get("parameters", {"DRIVE": 0.40})
                    DeviceParameterSupervisor.apply_semantic_tuning(conn, t_idx, d_idx, "", params)
                elif dec.action_tool == "duplicate_to_arrangement":
                    if args.get("deploy_all"):
                        sess = conn.send_command("get_session_info")
                        num_t = sess.get("track_count", 0)
                        for t_i in range(num_t):
                            t_inf = conn.send_command("get_track_info", {"track_index": t_i})
                            slots = t_inf.get("clip_slots", [])
                            for c_i, cs in enumerate(slots):
                                if cs.get("has_clip"):
                                    conn.send_command("duplicate_session_clip_to_arrangement", {
                                        "track_index": t_i,
                                        "clip_index": c_i,
                                        "destination_time": float(c_i * 32.0)
                                    })
                        conn.send_command("switch_to_arrangement_view", {})
                        conn.send_command("set_arrangement_time", {"time": 0.0})
                    else:
                        conn.send_command("duplicate_session_clip_to_arrangement", {
                            "track_index": args.get("track_index", 0),
                            "clip_index": args.get("clip_index", 0),
                            "destination_time": float(args.get("destination_time", 0.0))
                        })
                elif dec.action_tool == "dna_create_creative_brief":
                    from engine.creative import CreativeDirectionEngine
                    CreativeDirectionEngine.formulate_creative_brief(
                        title=args.get("title", "Bones Groove Pt 3"),
                        artist=args.get("artist", "Tyler & JID Tribute"),
                        genre=args.get("genre", "hip_hop_neo_soul")
                    )
                elif dec.action_tool == "dna_scaffold_live_project":
                    from engine.creative import CreativeDirectionEngine
                    dna = CreativeDirectionEngine.formulate_creative_brief(
                        title=args.get("title", "Bones Groove Pt 3"),
                        artist=args.get("artist", "Tyler & JID Tribute"),
                        genre=args.get("genre", "hip_hop_neo_soul")
                    )
                    CreativeDirectionEngine.scaffold_live_project(conn=conn, dna=dna, create_cues=args.get("create_cues", True))
                elif dec.action_tool == "music_compose_full_harmony":
                    from engine.music.harmony.full_song import FullSongHarmonyEngine
                    notes = FullSongHarmonyEngine.generate_harmony_notes(key_root=args.get("key_root", "F"), scale=args.get("scale", "natural_minor"))
                    f_notes = [{"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity, "mute": False} for n in notes]
                    t_idx = int(args.get("track_index", 2))
                    c_idx = int(args.get("clip_slot", 0))
                    conn.send_command("create_clip", {"track_index": t_idx, "clip_index": c_idx, "length": 384.0})
                    conn.send_command("set_clip_name", {"track_index": t_idx, "clip_index": c_idx, "name": f"Harmony_{args.get('key_root','F')}_Drop2"})
                    conn.send_command("add_notes_to_clip", {"track_index": t_idx, "clip_index": c_idx, "notes": f_notes})
                elif dec.action_tool == "music_compose_808_bassline":
                    from engine.music.bass.intelligent_808 import Intelligent808BassEngine
                    notes = Intelligent808BassEngine.generate_808_bassline(key_root=args.get("key_root", "F"), scale=args.get("scale", "natural_minor"))
                    f_notes = [{"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity, "mute": False} for n in notes]
                    t_idx = int(args.get("track_index", 1))
                    c_idx = int(args.get("clip_slot", 0))
                    conn.send_command("create_clip", {"track_index": t_idx, "clip_index": c_idx, "length": 384.0})
                    conn.send_command("set_clip_name", {"track_index": t_idx, "clip_index": c_idx, "name": "808_Bass_Interlocking"})
                    conn.send_command("add_notes_to_clip", {"track_index": t_idx, "clip_index": c_idx, "notes": f_notes})
                elif dec.action_tool == "music_compose_topline_melody":
                    from engine.music.melody.topline import TopLineMelodyEngine
                    notes = TopLineMelodyEngine.generate_full_song_melody(key_root=args.get("key_root", "F"), scale=args.get("scale", "natural_minor"))
                    f_notes = [{"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity, "mute": False} for n in notes]
                    t_idx = int(args.get("track_index", 3))
                    c_idx = int(args.get("clip_slot", 0))
                    conn.send_command("create_clip", {"track_index": t_idx, "clip_index": c_idx, "length": 384.0})
                    conn.send_command("set_clip_name", {"track_index": t_idx, "clip_index": c_idx, "name": "TopLine_CallResponse"})
                    conn.send_command("add_notes_to_clip", {"track_index": t_idx, "clip_index": c_idx, "notes": f_notes})
                elif dec.action_tool == "music_compose_vocal_hook":
                    from engine.music.melody.vocal_hook import VocalHookChopEngine
                    notes = VocalHookChopEngine.generate_full_song_vocal_hook(key_root=args.get("key_root", "F"), scale=args.get("scale", "natural_minor"))
                    f_notes = [{"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity, "mute": False} for n in notes]
                    t_idx = int(args.get("track_index", 4))
                    c_idx = int(args.get("clip_slot", 0))
                    conn.send_command("create_clip", {"track_index": t_idx, "clip_index": c_idx, "length": 384.0})
                    conn.send_command("set_clip_name", {"track_index": t_idx, "clip_index": c_idx, "name": "Vocal_Chop_Hook"})
                    conn.send_command("add_notes_to_clip", {"track_index": t_idx, "clip_index": c_idx, "notes": f_notes})
                elif dec.action_tool == "instrument_scan_host_vsts":
                    from engine.instruments.installed_scanner import InstalledPluginScanner
                    InstalledPluginScanner().get_catalog_summary()
                elif dec.action_tool == "sound_apply_timbre_morph":
                    from engine.sound.timbre_morph import SemanticTimbreMorphEngine
                    SemanticTimbreMorphEngine.generate_full_automation_manifest()
                elif dec.action_tool == "groove_apply_hardware_pocket":
                    from engine.music.groove.humanizer import DynamicGrooveHumanizer
                    if hasattr(conn, "get_clip_notes") and hasattr(conn, "add_notes_to_clip"):
                        t_idx = int(args.get("track_index", 0))
                        c_idx = int(args.get("clip_slot", 0))
                        clip_notes = conn.get_clip_notes(t_idx, c_idx)
                        if clip_notes:
                            humanized = DynamicGrooveHumanizer.humanize_clip_dict_notes(clip_notes, swing_percentage=args.get("swing_percentage", 58.0))
                            conn.add_notes_to_clip(t_idx, c_idx, humanized, mode="replace")
                elif dec.action_tool == "harmony_apply_chord_strum":
                    from engine.music.harmony.strum import PhysicalChordStrummer
                    if hasattr(conn, "get_clip_notes") and hasattr(conn, "add_notes_to_clip"):
                        t_idx = int(args.get("track_index", 2))
                        c_idx = int(args.get("clip_slot", 0))
                        clip_notes = conn.get_clip_notes(t_idx, c_idx)
                        if clip_notes:
                            strummed = PhysicalChordStrummer.strum_dict_notes(clip_notes, strum_ms=args.get("strum_ms", 14.0))
                            conn.add_notes_to_clip(t_idx, c_idx, strummed, mode="replace")
                elif dec.action_tool == "expression_apply_mpe_vibrato":
                    from engine.music.expression.mpe import MPEExpressionEngine
                    from engine.music.models import NoteEvent
                    if hasattr(conn, "get_clip_notes"):
                        t_idx = int(args.get("track_index", 3))
                        c_idx = int(args.get("clip_slot", 0))
                        clip_notes = conn.get_clip_notes(t_idx, c_idx)
                        if clip_notes:
                            events = [NoteEvent(pitch=d.get("pitch", 60), start=d.get("start_time", 0.0), duration=d.get("duration", 1.0), velocity=d.get("velocity", 90)) for d in clip_notes]
                            MPEExpressionEngine.add_expression_to_melody(events)
                elif dec.action_tool == "drums_inject_ghost_notes":
                    from engine.music.drums.ghost_notes import DrumGhostNoteInjector
                    from engine.music.models import NoteEvent
                    if hasattr(conn, "get_clip_notes") and hasattr(conn, "add_notes_to_clip"):
                        t_idx = int(args.get("track_index", 0))
                        c_idx = int(args.get("clip_slot", 0))
                        clip_notes = conn.get_clip_notes(t_idx, c_idx)
                        if clip_notes:
                            events = [NoteEvent(pitch=d.get("pitch", 38), start=d.get("start_time", 0.0), duration=d.get("duration", 0.25), velocity=d.get("velocity", 100)) for d in clip_notes]
                            processed = DrumGhostNoteInjector.process_drum_track_notes(events)
                            f_notes = [{"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity, "mute": False} for n in processed]
                            conn.add_notes_to_clip(t_idx, c_idx, f_notes, mode="replace")
                elif dec.action_tool == "transitions_inject_section_impacts":
                    from engine.arrangement.transitions.impacts import SectionImpactEngine
                    notes = SectionImpactEngine.generate_impact_notes()
                    t_idx = int(args.get("track_index", 3))
                    c_idx = int(args.get("clip_slot", 0))
                    f_notes = [{"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity, "mute": False} for n in notes]
                    conn.send_command("create_clip", {"track_index": t_idx, "clip_index": c_idx, "length": 384.0})
                    conn.send_command("add_notes_to_clip", {"track_index": t_idx, "clip_index": c_idx, "notes": f_notes})
                elif dec.action_tool == "transitions_build_tension_risers":
                    from engine.arrangement.transitions.risers import TransitionRisersEngine
                    TransitionRisersEngine.generate_filter_sweep(target_bar=33.0)
                elif dec.action_tool == "transitions_apply_pre_drop_vacuum":
                    from engine.arrangement.transitions.pre_drop import PreDropVacuumEngine
                    PreDropVacuumEngine.get_vacuum_windows()
                elif dec.action_tool == "transitions_inject_ear_candy_fx":
                    from engine.arrangement.transitions.ear_candy import EarCandyTransitionEngine
                    EarCandyTransitionEngine.get_ear_candy_manifest()
                execution_res["live_result"] = "executed_via_adapter"
            except Exception as e:
                execution_res["live_error"] = str(e)

        # If instrument/effect load failed, keep decision PENDING for retry
        if execution_res.get("load_failed"):
            return {
                "status": "LOAD_FAILED",
                "decision_id": dec.id,
                "action": "PENDING_RETRY",
                "error": execution_res.get("load_error", "No valid URI found for this instrument/effect."),
                "guidance": (
                    "MANDATORY: The instrument/effect could not be loaded because no valid URI was found. "
                    "Call get_available_vst_and_presets() to list installed VSTs, "
                    "then re-execute this decision with custom_args={'instrument_id': '<valid_id>'} or "
                    "custom_args={'effect_uri': '<valid_uri>'}."
                )
            }

        if execution_res.get("load_verified") is False:
            return {
                "status": "VERIFICATION_FAILED",
                "decision_id": dec.id,
                "action": "PENDING_RETRY",
                "warning": execution_res.get("load_warning", "Load verification failed."),
                "guidance": (
                    "MANDATORY: The instrument/effect did not appear in the track device chain after loading. "
                    "Verify the instrument is installed and licensed in Ableton Live, "
                    "then re-execute this decision or choose an alternative with custom_args."
                )
            }

        dec.status = DecisionStatus.APPLIED
        dec.result = execution_res
        self.resolved_decisions[dec.id] = dec
        del self.pending_decisions[dec.id]

        return {
            "status": "success",
            "decision_id": dec.id,
            "action": "APPLIED",
            "tool": dec.action_tool,
            "result": execution_res
        }

    def preflight_check(self) -> Dict[str, Any]:
        """
        Validates that zero neglected decisions remain before final mastering export.
        """
        state = self._build_state()
        ready = (len(state.pending_decisions) == 0 and len(state.blockers) == 0)

        return {
            "ready_for_export": ready,
            "pending_count": len(state.pending_decisions),
            "pending_titles": [d.title for d in state.pending_decisions],
            "resolved_count": len(state.resolved_decisions),
            "progress_pct": state.progress_pct,
            "blockers": state.blockers
        }


# Global singleton
executive_copilot = ExecutiveCopilotEngine()
