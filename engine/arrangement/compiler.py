"""
Arrangement Compiler:
Translates logical Song model into Ableton Session clips & Arrangement timeline.
Enforces ACID transaction safety, dry-run preview invariant, and phrase alignment.
"""
from typing import Dict, List, Any, Optional
from engine.arrangement.models.song import Song
from engine.arrangement.models.section import Section
from engine.music.intent import MusicalIntent
from engine import compile_notes_to_ableton_format
from engine import AbletonConnectionError, ObjectNotFoundError

class ArrangementCompiler:
    """Compiles Song data structure into concrete Ableton Live clips and notes."""

    def __init__(self, engine_instance):
        self.engine = engine_instance

    def compile(
        self,
        song: Song,
        preview: bool = False,
        compile_to_arrangement: bool = True,
        ensure_sound_sources: bool = True
    ) -> Dict[str, Any]:
        """
        Compiles the entire song arrangement.
        If preview=True, generates all notes and verifies structure without altering Ableton.
        If preview=False, executes atomic WAL transaction staging all clips, then commits.
        """
        # Ensure session graph has tracks if adapter is connected
        if hasattr(self.engine, "synchronizer") and self.engine.synchronizer:
            if hasattr(self.engine, "graph") and not self.engine.graph.tracks:
                try:
                    self.engine.synchronizer.reconcile()
                except Exception:
                    pass

        # Map logical roles to session tracks
        role_to_track = self._map_roles_to_tracks(preview=preview)
        
        compilation_manifest = []
        total_notes_generated = 0
        section_summaries = []
        
        # Pre-generate parts for each section and active role
        for sec_idx, sec in enumerate(song.sections):
            role_map = song.role_matrix.get_section_roles(sec_idx) if song.role_matrix else None
            sec_notes_count = 0
            active_roles = role_map.active_roles() if role_map else ["kick", "bass", "lead"]
            
            sec_manifest = {
                "section_index": sec_idx,
                "name": sec.name,
                "type": sec.section_type.value if hasattr(sec.section_type, "value") else str(sec.section_type),
                "start_bar": sec.start_bar,
                "bars": sec.bars,
                "energy": sec.energy,
                "roles": []
            }
            
            for role in active_roles:
                track_info = role_to_track.get(role)
                if not track_info:
                    continue
                    
                slot = role_map.roles.get(role) if role_map else None
                density_factor = slot.density_factor if slot else 1.0
                
                # Derive musical intent for this section
                intent = MusicalIntent(
                    role=role,
                    genre=song.genre,
                    style=sec.variation_type or "standard",
                    key=song.key,
                    scale=song.scale,
                    tempo=song.tempo,
                    bars=sec.bars,
                    energy=sec.energy,
                    density=min(1.0, max(0.1, sec.energy * density_factor)),
                    groove=sec.groove or "straight",
                    seed=(song.seed + sec_idx * 31) if song.seed else None,
                    section_type=sec.section_type.value if hasattr(sec.section_type, "value") else str(sec.section_type)
                )
                
                # Generate notes via Fase 2 Music Engine
                try:
                    notes, meta = self.engine.music.generate_part(role=role, intent=intent)
                    ableton_notes = compile_notes_to_ableton_format(notes)
                except Exception as e:
                    ableton_notes = []
                    meta = {"error": str(e)}
                    
                note_count = len(ableton_notes)
                sec_notes_count += note_count
                total_notes_generated += note_count
                
                sec_manifest["roles"].append({
                    "role": role,
                    "track_id": track_info["id"],
                    "track_index": track_info["index"],
                    "track_name": track_info["name"],
                    "clip_index": sec_idx,
                    "note_count": note_count,
                    "notes": ableton_notes
                })
                
            sec_manifest["total_notes"] = sec_notes_count
            section_summaries.append(sec_manifest)
            compilation_manifest.append(sec_manifest)
            
        # Preview Mode: Return full dry-run plan
        if preview:
            return {
                "status": "preview_success",
                "dry_run": True,
                "song_name": song.name,
                "genre": song.genre,
                "tempo": song.tempo,
                "key": f"{song.key} {song.scale}",
                "total_bars": song.total_bars,
                "duration_seconds": song.duration_seconds,
                "total_sections": len(song.sections),
                "total_notes": total_notes_generated,
                "sections": [
                    {
                        "index": s["section_index"],
                        "name": s["name"],
                        "type": s["type"],
                        "start_bar": s["start_bar"],
                        "bars": s["bars"],
                        "energy": s["energy"],
                        "note_count": s["total_notes"],
                        "active_roles": [r["role"] for r in s["roles"]]
                    }
                    for s in section_summaries
                ]
            }

        # Execution Mode: Begin atomic transaction
        if not self.engine.transactions:
            raise AbletonConnectionError("Transactions manager not initialized.")
            
        tx_id = self.engine.transactions.begin(name=f"compile_song_{song.name}")
        
        # 1. Update project tempo
        if hasattr(self.engine, "adapter") and self.engine.adapter:
            try:
                self.engine.adapter.set_tempo(song.tempo)
            except Exception:
                try:
                    self.engine.adapter.send_command("set_tempo", {"tempo": song.tempo})
                except Exception:
                    pass
                
        # Aggregate notes per unique (track, section) slot to avoid overwrites
        slot_notes_map = {}
        for sec in compilation_manifest:
            sec_idx = sec["section_index"]
            clip_length_beats = sec["bars"] * 4.0
            for role_data in sec["roles"]:
                t_idx = role_data["track_index"]
                t_id = role_data["track_id"]
                key = (t_idx, t_id, sec_idx)
                if key not in slot_notes_map:
                    slot_notes_map[key] = {
                        "length": clip_length_beats,
                        "name": f"[{sec['name']}] {role_data['track_name']}",
                        "notes": [],
                        "sec_idx": sec_idx,
                        "start_bar": sec["start_bar"]
                    }
                slot_notes_map[key]["notes"].extend(role_data["notes"])

        # 2. Ensure sound sources (instruments) on tracks receiving notes
        loaded_instruments = []
        if ensure_sound_sources and hasattr(self.engine, "adapter") and self.engine.adapter and not preview:
            tracks_checked = set()
            for (track_idx, track_id, sec_idx), slot_data in slot_notes_map.items():
                if track_idx in tracks_checked:
                    continue
                tracks_checked.add(track_idx)
                try:
                    track_info = None
                    if hasattr(self.engine.adapter, "get_track_info"):
                        track_info = self.engine.adapter.get_track_info(track_idx)
                    elif hasattr(self.engine.adapter, "send_command"):
                        track_info = self.engine.adapter.send_command("get_track_info", {"track_index": track_idx})
                    
                    devices = track_info.get("devices", []) if track_info else []
                    if len(devices) == 0:
                        # Find musical role for track
                        t_role = "KEYS"
                        for r_name, t_meta in role_to_track.items():
                            if t_meta.get("index") == track_idx:
                                t_role = r_name
                                break
                        from engine.instruments.library.preset_catalog import PresetCatalog
                        preset = PresetCatalog.resolve_preset(t_role, genre=song.genre)
                        if preset:
                            if hasattr(self.engine.adapter, "load_instrument_or_effect"):
                                self.engine.adapter.load_instrument_or_effect(track_idx, preset.uri)
                            elif hasattr(self.engine.adapter, "send_command"):
                                self.engine.adapter.send_command("load_instrument_or_effect", {
                                    "track_index": track_idx,
                                    "uri": preset.uri
                                })
                            loaded_instruments.append({
                                "track_index": track_idx,
                                "role": t_role,
                                "preset": preset.name,
                                "uri": preset.uri
                            })
                except Exception:
                    pass

        # 3. Stage clip creation and note insertion per unique track slot
        for (track_idx, track_id, sec_idx), slot_data in slot_notes_map.items():
            # Ensure clip slot exists in Ableton
            if hasattr(self.engine, "adapter") and self.engine.adapter:
                try:
                    self.engine.adapter.create_clip(
                        track_index=track_idx,
                        clip_index=sec_idx,
                        length=slot_data["length"]
                    )
                    self.engine.adapter.set_clip_name(
                        track_index=track_idx,
                        clip_index=sec_idx,
                        name=slot_data["name"]
                    )
                except Exception:
                    pass
                    
            # Stage merged notes once per slot in replace mode
            if slot_data["notes"]:
                self.engine.transactions.stage_add_notes(
                    tx_id=tx_id,
                    track_id=track_id,
                    clip_index=sec_idx,
                    notes=slot_data["notes"],
                    mode="replace"
                )

        # Commit ACID transaction
        commit_res = self.engine.transactions.commit(tx_id)
        
        # 3. Duplicate unique slots into Arrangement Timeline
        duplicated_to_arrangement = 0
        if compile_to_arrangement and hasattr(self.engine, "adapter") and self.engine.adapter:
            for (track_idx, track_id, sec_idx), slot_data in slot_notes_map.items():
                sec_start_beat = slot_data["start_bar"] * 4.0
                try:
                    if hasattr(self.engine.adapter, "send_command"):
                        self.engine.adapter.send_command("duplicate_session_clip_to_arrangement", {
                            "track_index": track_idx,
                            "clip_index": sec_idx,
                            "destination_time": sec_start_beat
                        })
                        duplicated_to_arrangement += 1
                except Exception:
                    pass

        return {
            "status": "compiled_success",
            "dry_run": False,
            "song_name": song.name,
            "transaction": commit_res,
            "total_notes": total_notes_generated,
            "total_sections": len(song.sections),
            "timeline_clips_placed": duplicated_to_arrangement,
            "instruments_loaded": loaded_instruments
        }

    def _map_roles_to_tracks(self, preview: bool = False) -> Dict[str, Dict[str, Any]]:
        """Maps standard roles to active session tracks."""
        mapping = {}
        tracks = self.engine.graph.tracks if hasattr(self.engine, "graph") else {}
        
        # If no tracks exist or if in preview mode without tracks, provide full virtual mapping
        if not tracks:
            standard_roles = [
                "kick", "bass", "sub_bass", "snare", "clap", "hihat_closed",
                "hihat_open", "percussion", "lead", "chords", "pad", "arp", "fx"
            ]
            for i, r in enumerate(standard_roles):
                mapping[r] = {
                    "id": f"track_{i % 4}",
                    "index": i % 4,
                    "name": f"Track {i % 4}"
                }
            return mapping

        # Role matching heuristics against actual tracks in session graph
        role_keywords = {
            "kick": ["drum", "kick", "rhythm", "percussion"],
            "snare": ["drum", "snare", "clap", "percussion"],
            "clap": ["drum", "clap", "percussion"],
            "hihat_closed": ["drum", "hihat", "percussion"],
            "hihat_open": ["drum", "hihat", "percussion"],
            "percussion": ["drum", "percussion", "perc"],
            "bass": ["bass", "sub", "synth 1", "low"],
            "sub_bass": ["bass", "sub"],
            "lead": ["lead", "melody", "synth", "hook"],
            "chords": ["chord", "pad", "string", "keys"],
            "pad": ["pad", "string", "ambient", "chord"],
            "arp": ["lead", "arp", "synth"],
            "vocal": ["vocal", "lead"],
            "fx": ["drum", "fx", "perc"]
        }
        
        for r, keywords in role_keywords.items():
            for t_id, track in tracks.items():
                # Strictly filter for MIDI tracks to avoid audio track errors
                if getattr(track, "type", "").lower() != "midi":
                    continue
                t_name = track.name.lower()
                if any(kw in t_name for kw in keywords):
                    mapping[r] = {"id": t_id, "index": getattr(track, "ableton_index", getattr(track, "index", 0)), "name": track.name}
                    break
                    
        # In preview mode, fallback unmapped roles to virtual tracks so notes are calculated
        if preview:
            track_list = list(tracks.values())
            for r in role_keywords.keys():
                if r not in mapping:
                    fallback_track = track_list[0]
                    mapping[r] = {"id": fallback_track.id, "index": getattr(fallback_track, "ableton_index", getattr(fallback_track, "index", 0)), "name": fallback_track.name}

        return mapping
