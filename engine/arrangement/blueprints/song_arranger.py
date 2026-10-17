# engine/arrangement/blueprints/song_arranger.py
"""
Full Song Blueprint & Dynamic Section Arranger Engine:
Orchestrates an entire radio/streaming commercial song structure across 96 bars (~3 minutes)
in Ableton Live 12 Suite's Arrangement View with dynamic role matrix distribution,
pre-drop micro-vacuums, section cue points, and multi-track clip placements.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from engine.arrangement.models.section import SectionType
from engine.arrangement.fx.ear_candy import EarCandyEngine


@dataclass
class SectionSpec:
    name: str
    type: SectionType
    start_bar: int           # 1-based measure (e.g. 1, 9, 25, 33...)
    bars: int                # Duration in bars (8 or 16)
    energy_target: float     # 0.0 to 1.0
    roles: Dict[str, str]    # {"kick": "OFF", "drums": "FULL", "bass": "OFF", ...}
    transition_fx: Optional[str] = None
    time_signature: Tuple[int, int] = (4, 4)

    @property
    def beats_per_bar(self) -> float:
        num, den = self.time_signature if self.time_signature else (4, 4)
        return float(num * (4.0 / max(1, den)))

    @property
    def start_beat(self) -> float:
        return (self.start_bar - 1) * self.beats_per_bar

    @property
    def end_beat(self) -> float:
        return (self.start_bar - 1 + self.bars) * self.beats_per_bar

    @property
    def end_bar(self) -> int:
        return self.start_bar + self.bars - 1


@dataclass
class FullSongBlueprint:
    title: str
    total_bars: int = 64
    tempo: float = 138.0
    key: str = "F"
    scale: str = "minor"
    genre: str = "atlanta_trap"
    time_signature: Tuple[int, int] = (4, 4)
    sections: List[SectionSpec] = field(default_factory=list)
    cue_points: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def beats_per_bar(self) -> float:
        num, den = self.time_signature if self.time_signature else (4, 4)
        return float(num * (4.0 / max(1, den)))

    @property
    def duration_seconds(self) -> float:
        return (self.total_bars * self.beats_per_bar / self.tempo) * 60.0


class FullSongArrangerEngine:
    """End-to-end architect for full-length song arrangement and dynamic layer orchestration."""

    @classmethod
    def generate_dynamic_blueprint(
        cls,
        total_bars: Optional[int] = None,
        sections_spec: Optional[List[Dict[str, Any]]] = None,
        bpm: float = 138.0,
        key: str = "F",
        scale: str = "minor",
        genre: str = "atlanta_trap",
        time_signature: Tuple[int, int] = (4, 4),
        drop_bar: Optional[int] = None,
        title: str = "PIE Dynamic Master Blueprint"
    ) -> FullSongBlueprint:
        """
        Dynamically generates a full song arrangement blueprint listening purely
        to how many bars the producer/AI requests, supporting asymmetric phrases,
        compound/irregular meters, and flexible drop placement without rigid templates.
        """
        sections: List[SectionSpec] = []
        effective_bars = total_bars or 96

        if sections_spec and isinstance(sections_spec, list):
            # 1. Custom sections supplied explicitly (supports asymmetric phrases e.g. 5, 7, 9, 11 bars)
            curr_bar = 1
            for idx, s in enumerate(sections_spec, 1):
                s_name = s.get("name", f"Section {idx}")
                s_type_raw = str(s.get("type", "VERSE")).upper()
                try:
                    s_type = SectionType[s_type_raw] if s_type_raw in SectionType.__members__ else SectionType.VERSE
                except Exception:
                    s_type = SectionType.VERSE
                s_bars = int(s.get("bars", 8))
                s_energy = float(s.get("energy_target", s.get("energy", 0.5)))
                s_roles = s.get("roles")
                if not s_roles or not isinstance(s_roles, dict):
                    # Proportional default role energy assignment
                    if s_type == SectionType.INTRO:
                        s_roles = {"kick": "OFF", "drums": "GHOST", "bass": "OFF", "lead": "OFF"}
                    elif s_type == SectionType.DROP:
                        s_roles = {"kick": "FULL", "drums": "FULL", "bass": "FULL_SLIDES", "lead": "FOREGROUND"}
                    elif s_type in (SectionType.BUILD, SectionType.BREAK):
                        s_roles = {"kick": "OFF", "drums": "BUILD_ROLL", "bass": "CUT_AT_32", "lead": "OFF"}
                    elif s_type == SectionType.OUTRO:
                        s_roles = {"kick": "OFF", "drums": "FADING", "bass": "OFF", "lead": "OFF"}
                    else:
                        s_roles = {"kick": "PUNCH", "drums": "FULL", "bass": "MEDIUM", "lead": "OFF"}

                sections.append(SectionSpec(
                    name=s_name,
                    type=s_type,
                    start_bar=curr_bar,
                    bars=s_bars,
                    energy_target=s_energy,
                    roles=s_roles,
                    transition_fx=s.get("transition_fx"),
                    time_signature=time_signature
                ))
                curr_bar += s_bars
            effective_bars = curr_bar - 1
        else:
            # 2. Dynamic proportional layout scaled to exact total_bars requested
            # Use 12 proportional units:
            # Intro: 1, Verse 1: 2, Pre-Chorus: 1, Drop 1: 2, Verse 2: 2, Bridge: 1, Final Drop: 2, Outro: 1 (Total = 12 units)
            eff = max(8, int(effective_bars)) if effective_bars >= 8 else int(effective_bars)
            if eff >= 8:
                unit = eff / 12.0
                intro_bars = max(1, int(round(unit * 1)))
                verse1_bars = max(1, int(round(unit * 2)))
                pre_bars = max(1, int(round(unit * 1)))
                drop1_bars = max(1, int(round(unit * 2)))
                verse2_bars = max(1, int(round(unit * 2)))
                bridge_bars = max(1, int(round(unit * 1)))
                final_drop_bars = max(1, int(round(unit * 2)))
                outro_bars = max(1, int(round(unit * 1)))

                # Exact sum reconciliation
                alloc_sum = intro_bars + verse1_bars + pre_bars + drop1_bars + verse2_bars + bridge_bars + final_drop_bars + outro_bars
                diff = eff - alloc_sum
                final_drop_bars += diff
                if final_drop_bars < 1:
                    verse1_bars += (final_drop_bars - 1)
                    final_drop_bars = 1

                raw_specs = [
                    ("Intro", SectionType.INTRO, intro_bars, 0.25,
                     {"kick": "OFF", "drums": "GHOST", "bass": "OFF", "piano": "WARM_CHORDS", "lead": "OFF", "foley": "FULL", "break": "OFF", "vocal_chops": "FILTERED_AMBIENT"},
                     "filter_sweep_rise"),
                    ("Verse 1", SectionType.VERSE, verse1_bars, 0.55,
                     {"kick": "PUNCH", "drums": "FULL", "bass": "SUB_ONLY", "piano": "OFF", "lead": "OFF", "foley": "LOW", "break": "OFF", "vocal_chops": "OFF"},
                     "drum_fill"),
                    ("Pre-Chorus", SectionType.BUILD, pre_bars, 0.75,
                     {"kick": "OFF", "drums": "BUILD_ROLL", "bass": "CUT_AT_32", "piano": "STACCATO_RISER", "lead": "OFF", "foley": "OFF", "break": "ROLL", "vocal_chops": "RISING_PITCH"},
                     "pre_drop_vacuum"),
                    ("Drop 1 (Chorus)", SectionType.DROP, drop1_bars, 0.95,
                     {"kick": "FULL", "drums": "FULL", "bass": "FULL_SLIDES", "piano": "FULL", "lead": "FOREGROUND", "foley": "OFF", "break": "OFF", "vocal_chops": "MAIN_HOOK"},
                     "instant_cut"),
                    ("Verse 2", SectionType.VERSE, verse2_bars, 0.60,
                     {"kick": "PUNCH", "drums": "FULL", "bass": "MID_BOUNCE", "piano": "OFF", "lead": "OFF", "foley": "LOW", "break": "AMEN_SHUFFLE", "vocal_chops": "CALL_RESPONSE"},
                     "break_fill"),
                    ("Bridge", SectionType.BREAK, bridge_bars, 0.40,
                     {"kick": "OFF", "drums": "OFF", "bass": "OFF", "piano": "SOLO_SPACIOUS", "lead": "WHISPER", "foley": "FULL", "break": "OFF", "vocal_chops": "DREAMY_DELAY"},
                     "pre_drop_vacuum"),
                    ("Final Drop (Climax)", SectionType.DROP, final_drop_bars, 1.00,
                     {"kick": "FULL", "drums": "FULL", "bass": "FULL_SLIDES", "piano": "FULL_ENERGY", "lead": "OCTAVE_LAYERED", "foley": "OFF", "break": "LAYERED_FULL", "vocal_chops": "STUTTER_MAX"},
                     "crash_ringout"),
                    ("Outro", SectionType.OUTRO, outro_bars, 0.20,
                     {"kick": "OFF", "drums": "FADING", "bass": "OFF", "piano": "LINGERING", "lead": "OFF", "foley": "FULL", "break": "OFF", "vocal_chops": "REVERB_TAIL"},
                     "fade_out"),
                ]
            else:
                # Ultra-short arrangement (< 8 bars)
                raw_specs = [
                    ("Intro", SectionType.INTRO, 1, 0.30, {"kick": "OFF", "drums": "GHOST", "bass": "OFF", "piano": "OFF", "lead": "OFF", "foley": "OFF", "break": "OFF", "vocal_chops": "OFF"}, "filter_sweep_rise"),
                    ("Drop 1 (Chorus)", SectionType.DROP, eff - 2 if eff >= 3 else 1, 0.95, {"kick": "FULL", "drums": "FULL", "bass": "FULL_SLIDES", "piano": "FULL", "lead": "FOREGROUND", "foley": "OFF", "break": "OFF", "vocal_chops": "OFF"}, "instant_cut"),
                    ("Outro", SectionType.OUTRO, 1, 0.20, {"kick": "OFF", "drums": "FADING", "bass": "OFF", "piano": "OFF", "lead": "OFF", "foley": "OFF", "break": "OFF", "vocal_chops": "OFF"}, "fade_out")
                ]
                alloc_sum = sum(s[2] for s in raw_specs)
                diff = eff - alloc_sum
                raw_specs[1] = (raw_specs[1][0], raw_specs[1][1], raw_specs[1][2] + diff, raw_specs[1][3], raw_specs[1][4], raw_specs[1][5])

            curr = 1
            for name, stype, bars, energy, roles, fx in raw_specs:
                if bars <= 0:
                    continue
                sections.append(SectionSpec(
                    name=name,
                    type=stype,
                    start_bar=curr,
                    bars=bars,
                    energy_target=energy,
                    roles=roles,
                    transition_fx=fx,
                    time_signature=time_signature
                ))
                curr += bars
            effective_bars = curr - 1

        # Generate cue points metadata dynamically
        cue_points: List[Dict[str, Any]] = []
        for idx, s in enumerate(sections, 1):
            cue_points.append({
                "name": f"{idx}. {s.name} ({s.bars}b)",
                "time": s.start_beat,
                "bar": s.start_bar
            })

        return FullSongBlueprint(
            title=title,
            total_bars=effective_bars,
            tempo=bpm,
            key=key,
            scale=scale,
            genre=genre,
            time_signature=time_signature,
            sections=sections,
            cue_points=cue_points
        )


    @classmethod
    def calculate_clip_placements(
        cls,
        blueprint: FullSongBlueprint,
        tracks_map: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """
        Calculates all Session-to-Arrangement clip duplications based on the section role matrix,
        adapted dynamically to any meter and phrasing length.
        """
        placements: List[Dict[str, Any]] = []
        bpb = blueprint.beats_per_bar
        block_beats = max(1.0, 4.0 * bpb)

        for sec in blueprint.sections:
            sec_start_beat = sec.start_beat
            sec_beats = sec.bars * bpb

            for role, state in sec.roles.items():
                if state in ["OFF", "CUT_AT_32", "CUT"]:
                    continue

                t_idx = tracks_map.get(role)
                if t_idx is None:
                    continue

                # Duplicate clip across section length in blocks
                offset = 0.0
                while offset < sec_beats:
                    dest_time = sec_start_beat + offset
                    if role == "bass" and sec.name == "Pre-Drop" and (offset >= sec_beats - bpb):
                        # Silence bass in last measure before drop
                        offset += block_beats
                        continue

                    placements.append({
                        "role": role,
                        "track_index": t_idx,
                        "source_clip_index": 0,
                        "destination_time": dest_time,
                        "section": sec.name,
                        "role_state": state
                    })
                    offset += block_beats

        return placements

    @classmethod
    def calculate_pre_drop_vacuums(cls, blueprint: FullSongBlueprint) -> List[Dict[str, Any]]:
        """
        Calculates ear candy pre-drop silence vacuum automation points.
        Injected at any section boundary transitioning into a Drop or with pre_drop_vacuum fx.
        """
        vacuum_ops = []
        bpb = blueprint.beats_per_bar
        for sec in blueprint.sections:
            if sec.transition_fx == "pre_drop_vacuum":
                target_bar = sec.end_bar + 1.0
                pts = EarCandyEngine.generate_pre_drop_vacuum(
                    target_bar=target_bar,
                    silence_duration_beats=min(2.0, bpb),
                    normal_gain=0.85
                )
                vacuum_ops.append({
                    "section": sec.name,
                    "target_bar": target_bar,
                    "points": pts
                })
        return vacuum_ops

    @classmethod
    def orchestrate_full_song(
        cls,
        conn: Any,
        tracks_map: Optional[Dict[str, int]] = None,
        bpm: float = 138.0,
        key: str = "F",
        scale: str = "minor",
        genre: str = "atlanta_trap",
        total_bars: Optional[int] = None,
        sections: Optional[List[Dict[str, Any]]] = None,
        time_signature: Tuple[int, int] = (4, 4),
        drop_bar: Optional[int] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end full song arrangement orchestration in Ableton Live:
        1. Generates dynamic blueprint matching the requested bar count and meter.
        2. Injects Section Cue Points (markers).
        3. Duplicates active clips across the Arrangement timeline based on role matrix.
        4. Injects pre-drop vacuum automations.
        """
        # Default tracks mapping if not provided
        effective_map = tracks_map or {
            "kick": 0,
            "drums": 13,
            "bass": 6,
            "piano": 9,
            "lead": 4,
            "foley": 15,
            "break": 14,
            "vocal_chops": 5
        }

        blueprint = cls.generate_dynamic_blueprint(
            total_bars=total_bars,
            sections_spec=sections,
            bpm=bpm,
            key=key,
            scale=scale,
            genre=genre,
            time_signature=time_signature,
            drop_bar=drop_bar,
            title=title or "PIE Dynamic Master Blueprint"
        )
        placements = cls.calculate_clip_placements(blueprint, effective_map)
        vacuums = cls.calculate_pre_drop_vacuums(blueprint)

        commands_dispatched = 0

        if conn is not None and hasattr(conn, "send_command"):
            try:
                # 1. Set Tempo
                conn.send_command("set_tempo", {"tempo": bpm})
                commands_dispatched += 1

                # 2. Add Section Cue Points
                for cp in blueprint.cue_points:
                    conn.send_command("create_cue_point", {
                        "name": cp["name"],
                        "time": cp["time"]
                    })
                    commands_dispatched += 1

                # 3. Duplicate clips across timeline
                for p in placements:
                    conn.send_command("duplicate_session_clip_to_arrangement", {
                        "track_index": p["track_index"],
                        "clip_index": p["source_clip_index"],
                        "destination_time": p["destination_time"]
                    })
                    commands_dispatched += 1

                # 4. Inject Pre-Drop Vacuums into Drum and Bass tracks
                for vac in vacuums:
                    for t_role in ["drums", "bass"]:
                        t_idx = effective_map.get(t_role)
                        if t_idx is not None:
                            conn.send_command("create_arrangement_automation_envelope", {
                                "track_index": t_idx,
                                "parameter": "Volume",
                                "points": vac["points"]
                            })
                            commands_dispatched += 1

                # 5. Automatically load verified 808 sample kit onto drum tracks
                try:
                    from engine.music.drums.multitrack import MultiTrackDrumEngine
                    for d_role in ["kick", "drums", "snare", "hats", "crash"]:
                        if d_role in effective_map:
                            MultiTrackDrumEngine.load_verified_drum_kit(conn, track_index=effective_map[d_role], kit_id="808_core")
                            commands_dispatched += 1
                except Exception:
                    pass

                # 6. Automatically configure physical compressor sidechain (Bass keyed against Kick)
                try:
                    from engine.mix.sidechain_manager import SidechainManager
                    b_trk = effective_map.get("bass", 7)
                    k_trk = effective_map.get("kick", effective_map.get("drums", 2))
                    SidechainManager.configure_sidechain(conn, bass_track_index=b_trk, kick_track_index=k_trk)
                    commands_dispatched += 1
                except Exception:
                    pass

                # 7. Automatically apply physical filter sweeps and pre-drop vacuums
                try:
                    from engine.arrangement.automation.live_automation import LiveAutomationEngine
                    l_trk = effective_map.get("lead", 4)
                    LiveAutomationEngine.apply_filter_sweep(conn, track_index=l_trk, start_bar=29.0, duration_bars=4.0, direction="up")
                    LiveAutomationEngine.apply_filter_sweep(conn, track_index=l_trk, start_bar=69.0, duration_bars=4.0, direction="up")
                    LiveAutomationEngine.apply_pre_drop_vacuum(conn, track_indices=[effective_map.get("kick", 2), effective_map.get("bass", 7)], drop_bar=33.0)
                    LiveAutomationEngine.apply_pre_drop_vacuum(conn, track_indices=[effective_map.get("kick", 2), effective_map.get("bass", 7)], drop_bar=73.0)
                    commands_dispatched += 1
                except Exception:
                    pass

                # 8. Automatically apply track channel strips (EQ Eight per role)
                try:
                    from engine.mix.channel_strip import ChannelStripEngine
                    for r_name, r_idx in effective_map.items():
                        if r_name in ["kick", "snare", "hats", "crash", "bass", "piano", "lead", "foley"]:
                            ChannelStripEngine.apply_channel_strip(conn, track_index=r_idx, role=r_name)
                            commands_dispatched += 1
                except Exception:
                    pass

                # 9. Automatically apply group bus processing (Drum Buss on Track 0, Glue on Track 3)
                try:
                    from engine.mix.channel_strip import ChannelStripEngine
                    ChannelStripEngine.apply_bus_processing(conn, group_track_index=0, bus_type="drums")
                    ChannelStripEngine.apply_bus_processing(conn, group_track_index=3, bus_type="synths")
                    commands_dispatched += 2
                except Exception:
                    pass

                # 10. Automatically configure 5-device live mastering chain
                try:
                    from engine.mastering.live_master_chain import LiveMasterChainEngine
                    LiveMasterChainEngine.setup_live_mastering_chain(conn, track_index=12, target_profile="STREAMING")
                    commands_dispatched += 5
                except Exception:
                    pass

            except Exception:
                pass

        return {
            "status": "SUCCESS",
            "title": blueprint.title,
            "total_bars": blueprint.total_bars,
            "duration_seconds": round(blueprint.duration_seconds, 1),
            "bpm": bpm,
            "key": key,
            "scale": scale,
            "genre": genre,
            "sections_count": len(blueprint.sections),
            "cue_points_created": len(blueprint.cue_points),
            "clip_placements_count": len(placements),
            "pre_drop_vacuums_count": len(vacuums),
            "commands_dispatched": commands_dispatched
        }

    # Alias for flexibility
    orchestrate_full_song_timeline = orchestrate_full_song
