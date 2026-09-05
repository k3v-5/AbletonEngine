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
                num_tracks = int(s_info.get("num_tracks", 0))
                for t_idx in range(num_tracks):
                    t_info = conn.send_command("get_track_info", {"track_index": t_idx})
                    session_tracks.append(t_info)
            except Exception:
                pass

        # If no tracks found or session uninitialized, provide full Phase 1 DNA decisions
        if not session_tracks or len(session_tracks) < 4:
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
        foley_tracks = []
        vocal_tracks = []

        for idx, trk in enumerate(session_tracks):
            t_name = str(trk.get("name", "")).lower()
            t_idx = int(trk.get("track_index", idx))

            if "kick" in t_name:
                kick_tracks.append(t_idx)
            elif "808" in t_name or "bass" in t_name or "sub" in t_name:
                bass_tracks.append(t_idx)
            if any(w in t_name for w in ["drum", "kit", "perc", "break", "snare", "clap", "hat"]):
                drum_tracks.append(t_idx)
            if any(w in t_name for w in ["piano", "chord", "key", "rhodes"]):
                chord_tracks.append(t_idx)
            if any(w in t_name for w in ["lead", "synth"]):
                lead_tracks.append(t_idx)
            if any(w in t_name for w in ["foley", "texture", "rain", "vinyl", "ambient", "ambience"]):
                foley_tracks.append(t_idx)
            if any(w in t_name for w in ["vocal", "vox", "chop", "hook"]):
                vocal_tracks.append(t_idx)

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
                    description="Populate Drum Rack with verified local .wav samples from FL Studio / Cymatics / ASAN Essentials library (Kick, Snare, Clap, Hats, Foley).",
                    recommendation="YES, load verified local samples into Drum Rack pads.",
                    action_tool="drum_rack_load_authentic_library",
                    action_args={"track_index": d_target, "kit_name": "Tyler_JID_Authentic_Kit", "genre": "neo_soul_trap"},
                    target_track=d_target
                ))

        if effective_bass is not None:
            dec_id = f"DEC-P3-03-BASS-INSTRUMENT-LOAD-T{effective_bass}"
            if dec_id not in self.resolved_decisions:
                self._register_pending(ProductionDecision(
                    id=dec_id,
                    phase=ProductionPhase.PHASE_3_SOUND_DESIGN,
                    title=f"Load Elite Sub-Bass Instrument for Track {effective_bass}",
                    description="Instantiate high-definition bass engine (Serum 808 sub / Bloom Bass / Drift 808) with sub-bass acoustic profile.",
                    recommendation="YES, load Serum/Drift sub-bass instrument.",
                    action_tool="sound_load_role_instrument",
                    action_args={"track_index": effective_bass, "role": "BASS", "instrument_id": "vst3_serum2"},
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
                    description="Instantiate premier keyboard engine (Arturia Analog Lab V Rhodes / Keyscape / Drift) with warm harmonic profile.",
                    recommendation="YES, load Analog Lab V / Drift warm keys.",
                    action_tool="sound_load_role_instrument",
                    action_args={"track_index": c_idx, "role": "KEYS", "instrument_id": "vst3_analog_lab"},
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
                    description="Instantiate expressive lead synth (Serum Glide Lead / Drift Lead) with resonant filter and glide.",
                    recommendation="YES, load Serum/Drift lead synth.",
                    action_tool="sound_load_role_instrument",
                    action_args={"track_index": l_idx, "role": "LEAD", "instrument_id": "vst3_serum2"},
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
                    description="Instantiate Bloom Vocal Aether or Sampler with formant shift and space reverb.",
                    recommendation="YES, load Bloom Vocal / Simpler vocal engine.",
                    action_tool="sound_load_role_instrument",
                    action_args={"track_index": v_idx, "role": "VOCALS", "instrument_id": "vst3_bloom_vocal"},
                    target_track=v_idx
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
            if d.phase in [ProductionPhase.PHASE_4_HUMANIZATION_GROOVE, ProductionPhase.PHASE_6_MIX_ACOUSTICS]:
                blockers.append(f"Unresolved critical decision: '{d.title}' ({d.id})")

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
                elif dec.action_tool == "export_commercial_release_package":
                    from engine.mastering.release_package import CommercialReleasePackager
                    CommercialReleasePackager.create_release_package(
                        output_directory=args.get("output_directory") or str(Path.home() / "Music" / "Mastered_Releases"),
                        song_title=args.get("song_title", "Master Track"),
                        artist_name=args.get("artist_name", "Producer"),
                        target_profile=args.get("target_profile", "STREAMING")
                    )
                execution_res["live_result"] = "executed_via_adapter"
            except Exception as e:
                execution_res["live_error"] = str(e)

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
        ready = len(state.pending_decisions) == 0

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
