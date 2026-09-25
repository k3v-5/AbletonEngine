# engine/production/copilot/phases/phase_6/parser.py
"""
Phase 6 AI Composition Parser:
Parses raw user input, files, and markdown fenced JSON blocks into normalized
note maps with bidirectional role and section matching.
"""
import os
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from engine.production.copilot.role_orchestrator import RoleTrackOrchestrator

logger = logging.getLogger("Phase6Parser")


def _norm_notes(raw_list: List[Any]) -> List[Dict[str, Any]]:
    normed = []
    for n in raw_list:
        if isinstance(n, dict) and "pitch" in n:
            normed.append({
                "pitch": int(n["pitch"]),
                "start_time": round(float(n.get("start_time", n.get("start", 0.0))), 4),
                "duration": round(float(n.get("duration", 1.0)), 4),
                "velocity": int(n.get("velocity", 100)),
                "mute": bool(n.get("mute", False))
            })
    return normed


class Phase6Parser:
    """Parser and query engine for custom AI composition notes."""

    @staticmethod
    def parse_ai_composition(
        session: Any,
        user_input: str
    ) -> Tuple[Dict[str, Any], Dict[Tuple[Any, Any], List[Dict[str, Any]]], bool]:
        """
        Parses structured AI composition notes from markdown code fences, JSON objects,
        or file paths.
        Supports format variations:
        - {"composition": {track_key: {section_key: [notes]}}}
        - {"composition": [{"track_name": ..., "section": ..., "notes": [...]}]}
        - {"tracks": {track_key: {section_key: [notes]}}}
        - {"roles": {role_key: {section_key: [notes]}}}
        - {"clips": [{"track": ..., "section": ..., "notes": [...]}]}
        - Direct file path (.json) containing full score
        """
        meta: Dict[str, Any] = {}
        custom_map: Dict[Tuple[Any, Any], List[Dict[str, Any]]] = {}
        data = None

        clean_path = str(user_input).strip().strip('"').strip("'")
        if not (os.path.exists(clean_path) and clean_path.endswith(".json")):
            path_m = re.search(r'([A-Za-z]:\\[^"\'\r\n]+\.json|/[^"\'\r\n]+\.json)', user_input)
            if path_m and os.path.exists(path_m.group(1)):
                clean_path = path_m.group(1)

        if os.path.exists(clean_path) and clean_path.endswith(".json"):
            try:
                with open(clean_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = None

        if not data:
            json_str = None
            fence_m = re.search(r"```(?:json)?\s*([\{\[][\s\S]*?[\}\]])\s*```", user_input, re.DOTALL)
            if fence_m:
                json_str = fence_m.group(1)
            else:
                brace_m = re.search(r"([\{\[][\s\S]*[\}\]])", user_input, re.DOTALL)
                if brace_m:
                    json_str = brace_m.group(1)

            if not json_str:
                return meta, custom_map, False

            try:
                data = json.loads(json_str)
            except Exception:
                return meta, custom_map, False

        if isinstance(data, list):
            custom_map[("current", "all")] = _norm_notes(data)
            return meta, custom_map, len(custom_map) > 0

        if not isinstance(data, dict):
            return meta, custom_map, False

        for k in ["bpm", "key", "scale", "genre"]:
            if k in data:
                meta[k] = data[k]

        # Single track 'notes' list or 'sections' dict
        if "notes" in data and isinstance(data["notes"], list):
            custom_map[("current", "all")] = _norm_notes(data["notes"])
        if "sections" in data and isinstance(data["sections"], dict):
            for s_k, n_list in data["sections"].items():
                if isinstance(n_list, list):
                    try:
                        s_idx = int(s_k)
                    except ValueError:
                        s_idx = str(s_k).lower()
                    custom_map[("current", s_idx)] = _norm_notes(n_list)

        # Direct section keys at root level (e.g. {"Intro": [...], "Verse 1": [...]})
        for s_k, n_list in data.items():
            if str(s_k).lower() in ("intro", "verse", "verse 1", "verse 2", "buildup", "build", "drop", "drop 1", "drop 2", "puente", "breakdown", "outro", "all") and isinstance(n_list, list):
                custom_map[("current", str(s_k).lower())] = _norm_notes(n_list)

        # 1. 'composition' dict or list: {track_key: {section_key: [notes]}} or list of track items
        comp = data.get("composition")
        if isinstance(comp, dict):
            for t_k, sec_val in comp.items():
                if isinstance(sec_val, dict):
                    for s_k, n_list in sec_val.items():
                        try:
                            s_idx = int(s_k)
                        except ValueError:
                            s_idx = str(s_k).lower()
                        if isinstance(n_list, list):
                            custom_map[(t_k, s_idx)] = _norm_notes(n_list)
                elif isinstance(sec_val, list):
                    custom_map[(t_k, "all")] = _norm_notes(sec_val)
        elif isinstance(comp, list):
            for item in comp:
                if isinstance(item, dict):
                    t_ident = item.get("track", item.get("track_name", item.get("track_index", item.get("role", item.get("name")))))
                    s_idx = item.get("section", item.get("section_index", 0))
                    try:
                        s_idx = int(s_idx)
                    except ValueError:
                        s_idx = str(s_idx).lower()
                    normed = _norm_notes(item.get("notes", []))
                    custom_map[(t_ident, s_idx)] = normed
                    if isinstance(t_ident, str):
                        custom_map[(t_ident.lower(), s_idx)] = normed
                        if not t_ident.isdigit():
                            norm_r = RoleTrackOrchestrator.normalize_role(t_ident)
                            if norm_r:
                                custom_map[(norm_r, s_idx)] = normed
                                custom_map[(norm_r.lower(), s_idx)] = normed

        # 2. 'tracks' list or dict
        trks = data.get("tracks")
        if isinstance(trks, dict):
            for t_k, sec_val in trks.items():
                if isinstance(sec_val, dict):
                    for s_k, n_list in sec_val.items():
                        try:
                            s_idx = int(s_k)
                        except ValueError:
                            s_idx = str(s_k).lower()
                        if isinstance(n_list, list):
                            custom_map[(t_k, s_idx)] = _norm_notes(n_list)
                elif isinstance(sec_val, list):
                    custom_map[(t_k, "all")] = _norm_notes(sec_val)
        elif isinstance(trks, list):
            for trk_item in trks:
                if not isinstance(trk_item, dict):
                    continue
                t_ident = trk_item.get("index", trk_item.get("track_index", trk_item.get("name", trk_item.get("role"))))
                if "clips" in trk_item and isinstance(trk_item["clips"], list):
                    for c_idx, clip in enumerate(trk_item["clips"]):
                        if isinstance(clip, dict):
                            s_idx = clip.get("section_index", clip.get("section", c_idx))
                            try:
                                s_idx = int(s_idx)
                            except ValueError:
                                s_idx = str(s_idx).lower()
                            custom_map[(t_ident, s_idx)] = _norm_notes(clip.get("notes", []))
                elif "notes" in trk_item and isinstance(trk_item["notes"], list):
                    custom_map[(t_ident, "all")] = _norm_notes(trk_item["notes"])

        # 3. 'roles' dict
        roles = data.get("roles")
        if isinstance(roles, dict):
            for r_k, r_val in roles.items():
                r_upper = str(r_k).upper()
                if isinstance(r_val, dict):
                    for s_k, n_list in r_val.items():
                        try:
                            s_idx = int(s_k)
                        except ValueError:
                            s_idx = str(s_k).lower()
                        if isinstance(n_list, list):
                            custom_map[(r_upper, s_idx)] = _norm_notes(n_list)
                elif isinstance(r_val, list):
                    custom_map[(r_upper, "all")] = _norm_notes(r_val)

        # 4. 'clips' list
        clips = data.get("clips")
        if isinstance(clips, list):
            for clip in clips:
                if isinstance(clip, dict):
                    t_ident = clip.get("track", clip.get("track_index", clip.get("role", clip.get("name"))))
                    s_idx = clip.get("section", clip.get("section_index", 0))
                    try:
                        s_idx = int(s_idx)
                    except ValueError:
                        s_idx = str(s_idx).lower()
                    normed = _norm_notes(clip.get("notes", []))
                    custom_map[(t_ident, s_idx)] = normed
                    if isinstance(t_ident, str) and not t_ident.isdigit():
                        norm_r = RoleTrackOrchestrator.normalize_role(t_ident)
                        if norm_r:
                            custom_map[(norm_r, s_idx)] = normed
                            custom_map[(norm_r.lower(), s_idx)] = normed

        return meta, custom_map, len(custom_map) > 0

    @staticmethod
    def find_custom_notes_for_track_section(
        session: Any,
        custom_map: Dict[Tuple[Any, Any], List[Dict[str, Any]]],
        trk: Dict[str, Any],
        s_idx: int,
        s_name: str,
        s_beats: float
    ) -> Optional[List[Dict[str, Any]]]:
        """Resolves custom AI notes matching track and section by ID, alias, or case-insensitive name."""
        t_idx = trk.get("index")
        t_name = str(trk.get("name", "")).lower()
        t_role = str(trk.get("role", "")).upper()
        s_name_lower = str(s_name).lower()

        # Bidirectional role aliases resolution
        role_aliases = RoleTrackOrchestrator.get_role_aliases(t_role)
        norm_name_role = RoleTrackOrchestrator.normalize_role(trk.get("name", ""))
        for r_extra in RoleTrackOrchestrator.get_role_aliases(norm_name_role):
            if r_extra not in role_aliases:
                role_aliases.append(r_extra)

        keys_to_check = [
            ("current", s_idx),
            ("current", str(s_idx)),
            ("current", s_name_lower),
            (t_idx, s_idx),
            (str(t_idx), s_idx),
            (str(t_idx), str(s_idx)),
            (t_name, s_idx),
            (t_name, str(s_idx)),
            (t_idx, s_name_lower),
            (str(t_idx), s_name_lower),
            (t_name, s_name_lower),
        ]
        for alias in role_aliases:
            keys_to_check.extend([
                (alias, s_idx),
                (alias, str(s_idx)),
                (alias, s_name_lower),
                (alias.lower(), s_idx),
                (alias.lower(), str(s_idx)),
                (alias.lower(), s_name_lower),
            ])

        for k in keys_to_check:
            if k in custom_map:
                return list(custom_map[k])

        # Cross-map lookup across custom_map keys for matching section
        for (map_ident, map_sec), notes_val in custom_map.items():
            if str(map_sec).lower() in [str(s_idx), str(s_name_lower)]:
                map_ident_str = str(map_ident).strip().upper()
                if map_ident_str in role_aliases or map_ident_str.lower() in t_name or t_name in map_ident_str.lower():
                    return list(notes_val)

        # Check fallback to "all"
        all_keys = [
            ("current", "all"),
            (t_idx, "all"),
            (str(t_idx), "all"),
            (t_name, "all"),
        ]
        for alias in role_aliases:
            all_keys.extend([
                (alias, "all"),
                (alias.lower(), "all"),
            ])
        for k in all_keys:
            if k in custom_map:
                base_notes = custom_map[k]
                if not base_notes:
                    return []
                max_reach = max(n["start_time"] + n["duration"] for n in base_notes)
                if max_reach > 0 and s_beats > max_reach:
                    pattern_len = 16.0 if max_reach <= 16.0 else max_reach
                    tiled = []
                    offset = 0.0
                    while offset < s_beats:
                        for n in base_notes:
                            n_st = n["start_time"] + offset
                            if n_st < s_beats:
                                n_copy = dict(n)
                                n_copy["start_time"] = round(n_st, 4)
                                n_dur = min(n["duration"], s_beats - n_st)
                                n_copy["duration"] = round(n_dur, 4)
                                tiled.append(n_copy)
                        offset += pattern_len
                    return tiled
                else:
                    return list(base_notes)

        # Cross-map fallback for "all"
        for (map_ident, map_sec), notes_val in custom_map.items():
            if str(map_sec).lower() == "all":
                map_ident_str = str(map_ident).strip().upper()
                if map_ident_str in role_aliases or map_ident_str.lower() in t_name or t_name in map_ident_str.lower():
                    base_notes = notes_val
                    if not base_notes:
                        return []
                    max_reach = max(n["start_time"] + n["duration"] for n in base_notes)
                    if max_reach > 0 and s_beats > max_reach:
                        pattern_len = 16.0 if max_reach <= 16.0 else max_reach
                        tiled = []
                        offset = 0.0
                        while offset < s_beats:
                            for n in base_notes:
                                n_st = n["start_time"] + offset
                                if n_st < s_beats:
                                    n_copy = dict(n)
                                    n_copy["start_time"] = round(n_st, 4)
                                    n_dur = min(n["duration"], s_beats - n_st)
                                    n_copy["duration"] = round(n_dur, 4)
                                    tiled.append(n_copy)
                            offset += pattern_len
                        return tiled
                    else:
                        return list(base_notes)

        return None
