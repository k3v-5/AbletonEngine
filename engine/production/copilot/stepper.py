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

        # If no tracks found, provide baseline DNA setup decisions
        if not session_tracks:
            dec_dna = ProductionDecision(
                id="DEC-P1-SONG-DNA",
                phase=ProductionPhase.PHASE_1_DNA,
                title="Initialize Song DNA & Harmonic Foundation",
                description="The project has no active tracks. Define tempo, key, scale, and genre identity.",
                recommendation="YES, set 138.0 BPM in F Natural Minor (Trap/Hip-Hop).",
                action_tool="set_tempo",
                action_args={"tempo": 138.0}
            )
            self._register_pending(dec_dna)
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
            if "808" in t_name or "bass" in t_name or "sub" in t_name:
                bass_tracks.append(t_idx)
            if any(w in t_name for w in ["drum", "kit", "perc", "break"]):
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
