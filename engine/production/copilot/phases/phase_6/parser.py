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

            def _extract_freetext_meta(txt: str, target_meta: Dict[str, Any]):
                groove_m = re.search(r'(?:groove|pocket|estilo_groove|estilo)\s*[:=]\s*([a-zA-Z0-9_\-]+)', txt, re.IGNORECASE)
                if groove_m and "groove" not in target_meta and "pocket_style" not in target_meta:
                    target_meta["pocket_style"] = groove_m.group(1).lower()

                if "pocket_style" not in target_meta and "groove" not in target_meta:
                    u_lower = txt.lower()
                    if any(w in u_lower for w in ["ukg_2step", "uk garage", "ukg", "2step", "2-step", "garage londinense"]):
                        target_meta["pocket_style"] = "ukg_2step"
                    elif any(w in u_lower for w in ["dilla_drunk", "dilla", "drunken"]):
                        target_meta["pocket_style"] = "dilla_drunk"
                    elif any(w in u_lower for w in ["lofi_sp1200", "sp1200", "sp-1200"]):
                        target_meta["pocket_style"] = "lofi_sp1200"
                    elif any(w in u_lower for w in ["reggaeton_dembow", "dembow"]):
                        target_meta["pocket_style"] = "reggaeton_dembow"
                    elif any(w in u_lower for w in ["mpc_60", "mpc60", "roger linn"]):
                        target_meta["pocket_style"] = "mpc_60"
                    elif any(w in u_lower for w in ["straight_precise", "straight", "cuantizado", "rigido", "grid", "sin swing"]):
                        target_meta["pocket_style"] = "straight_precise"

                swing_m = re.search(r'(?:swing|swing_pct|swing_percentage)\s*[:=]?\s*(\d{2}(?:\.\d+)?)\s*%?', txt, re.IGNORECASE)
                if not swing_m:
                    swing_m = re.search(r'(\d{2}(?:\.\d+)?)\s*%\s*(?:de\s+)?swing', txt, re.IGNORECASE)
                if swing_m and "swing" not in target_meta and "swing_percentage" not in target_meta:
                    try:
                        target_meta["swing_percentage"] = float(swing_m.group(1))
                    except ValueError:
                        pass

                hum_m = re.search(r'(?:humanizaci[oó]n|humanization|hum_level|nivel_humanizaci[oó]n)\s*[:=]?\s*([0-5])', txt, re.IGNORECASE)
                if hum_m and "humanization_level" not in target_meta:
                    try:
                        target_meta["humanization_level"] = int(hum_m.group(1))
                    except ValueError:
                        pass

            _extract_freetext_meta(user_input, meta)

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

        for k in [
            "bpm", "key", "scale", "genre",
            "groove", "pocket", "pocket_style",
            "swing", "swing_percentage", "humanization", "humanization_level"
        ]:
            if k in data:
                meta[k] = data[k]

        # Single track 'notes' list or 'sections' dict
        if "notes" in data and isinstance(data["notes"], list):
            custom_map[("current", "all")] = _norm_notes(data["notes"])
        if "sections" in data:
            if isinstance(data["sections"], dict):
                for s_k, sec_val in data["sections"].items():
                    try:
                        s_idx = int(s_k)
                    except ValueError:
                        s_idx = str(s_k).lower()
                    if isinstance(sec_val, list):
                        custom_map[("current", s_idx)] = _norm_notes(sec_val)
                    elif isinstance(sec_val, dict):
                        trk_dict = sec_val.get("tracks", sec_val) if isinstance(sec_val.get("tracks"), dict) else sec_val
                        for t_k, t_val in trk_dict.items():
                            n_list = t_val.get("notes", []) if isinstance(t_val, dict) else t_val
                            if isinstance(n_list, list):
                                normed_n = _norm_notes(n_list)
                                custom_map[(t_k, s_idx)] = normed_n
                                if isinstance(t_k, str):
                                    custom_map[(t_k.lower(), s_idx)] = normed_n
            elif isinstance(data["sections"], list):
                for s_pos, sec_item in enumerate(data["sections"]):
                    if not isinstance(sec_item, dict):
                        continue
                    s_raw = sec_item.get("name", sec_item.get("section", sec_item.get("index", s_pos)))
                    try:
                        s_idx = int(s_raw)
                    except ValueError:
                        s_idx = str(s_raw).lower()
                    trk_dict = sec_item.get("tracks", {})
                    if isinstance(trk_dict, dict):
                        for t_k, t_val in trk_dict.items():
                            n_list = t_val.get("notes", []) if isinstance(t_val, dict) else t_val
                            if isinstance(n_list, list):
                                normed_n = _norm_notes(n_list)
                                custom_map[(t_k, s_idx)] = normed_n
                                if isinstance(t_k, str):
                                    custom_map[(t_k.lower(), s_idx)] = normed_n

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
                    s_idx = item.get("section", item.get("section_index", 0))
                    try:
                        s_idx = int(s_idx)
                    except ValueError:
                        s_idx = str(s_idx).lower()

                    # Support nested "tracks" dict inside section item: {"tracks": {"0": {"notes": [...]}}}
                    if "tracks" in item and isinstance(item["tracks"], dict):
                        for sub_t_k, sub_t_val in item["tracks"].items():
                            sub_notes = sub_t_val.get("notes", []) if isinstance(sub_t_val, dict) else sub_t_val
                            if isinstance(sub_notes, list):
                                sub_normed = _norm_notes(sub_notes)
                                try:
                                    sub_t_idx = int(sub_t_k)
                                    custom_map[(sub_t_idx, s_idx)] = sub_normed
                                    custom_map[(str(sub_t_idx), s_idx)] = sub_normed
                                except ValueError:
                                    custom_map[(sub_t_k, s_idx)] = sub_normed
                                    custom_map[(sub_t_k.lower(), s_idx)] = sub_normed
                                    norm_sub_r = RoleTrackOrchestrator.normalize_role(sub_t_k)
                                    if norm_sub_r:
                                        custom_map[(norm_sub_r, s_idx)] = sub_normed
                                        custom_map[(norm_sub_r.lower(), s_idx)] = sub_normed

                    t_ident = item.get("track", item.get("track_name", item.get("track_index", item.get("role", item.get("name")))))
                    if t_ident is not None:
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
                    if "notes" in sec_val and isinstance(sec_val["notes"], list):
                        normed_notes = _norm_notes(sec_val["notes"])
                        custom_map[(t_k, "all")] = normed_notes
                        t_role = sec_val.get("role")
                        if t_role:
                            custom_map[(str(t_role).upper(), "all")] = normed_notes
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
                t_name_explicit = trk_item.get("name")
                if "sections" in trk_item and isinstance(trk_item["sections"], dict):
                    for s_k, n_list in trk_item["sections"].items():
                        if isinstance(n_list, list):
                            try:
                                s_idx = int(s_k)
                            except ValueError:
                                s_idx = str(s_k).lower()
                            normed_n = _norm_notes(n_list)
                            custom_map[(t_ident, s_idx)] = normed_n
                            if t_name_explicit:
                                custom_map[(str(t_name_explicit).lower(), s_idx)] = normed_n
                if "clips" in trk_item and isinstance(trk_item["clips"], list):
                    for c_idx, clip in enumerate(trk_item["clips"]):
                        if isinstance(clip, dict):
                            s_idx = clip.get("section_index", clip.get("section", c_idx))
                            try:
                                s_idx = int(s_idx)
                            except ValueError:
                                s_idx = str(s_idx).lower()
                            normed_n = _norm_notes(clip.get("notes", []))
                            custom_map[(t_ident, s_idx)] = normed_n
                            if t_name_explicit:
                                custom_map[(str(t_name_explicit).lower(), s_idx)] = normed_n
                elif "notes" in trk_item and isinstance(trk_item["notes"], list):
                    normed_n = _norm_notes(trk_item["notes"])
                    custom_map[(t_ident, "all")] = normed_n
                    if t_name_explicit:
                        custom_map[(str(t_name_explicit).lower(), "all")] = normed_n

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
    def _clean_track_ident(raw: Any) -> str:
        s = str(raw or "").strip()
        s = re.sub(r"^\[[^\]]+\]\s*", "", s)
        s = re.sub(r"^\d+[\s_\-\.]*", "", s)
        s = re.sub(r"\.(adg|adv|als|vst3|vst|wav|aif)$", "", s, flags=re.IGNORECASE)
        s = re.sub(r"[\s_\-]+", " ", s).strip().lower()
        return s

    @staticmethod
    def _tile_notes_to_beats(base_notes: List[Dict[str, Any]], s_beats: float) -> List[Dict[str, Any]]:
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
        return list(base_notes)

    @staticmethod
    def find_custom_notes_for_track_section(
        session: Any,
        custom_map: Dict[Tuple[Any, Any], List[Dict[str, Any]]],
        trk: Dict[str, Any],
        s_idx: int,
        s_name: str,
        s_beats: float
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Resolves custom AI notes matching track and section.
        Strictly prioritizes exact track index, original_name, and normalized track name
        BEFORE falling back to generic role aliases so multiple tracks sharing a role family
        never collide or overwrite each other's notes.
        """
        t_idx = trk.get("index")
        t_name = str(trk.get("name", "")).lower().strip()
        t_orig = str(trk.get("original_name", "")).lower().strip()
        t_clean = Phase6Parser._clean_track_ident(t_name)
        t_orig_clean = Phase6Parser._clean_track_ident(t_orig)
        t_role = str(trk.get("role", "")).upper()
        s_name_lower = str(s_name).lower().strip()
        s_name_clean = Phase6Parser._clean_track_ident(s_name)

        # Candidate track identifiers (specific to this track)
        specific_idents = []
        for cand in [t_idx, str(t_idx), t_orig, t_orig_clean, t_name, t_clean]:
            if cand is not None and cand != "" and cand not in specific_idents:
                specific_idents.append(cand)

        sec_targets = [s_idx, str(s_idx), s_name_lower, s_name_clean]

        # PASS 1A: Exact key match on specific track identifiers + section
        for ident in specific_idents:
            for st in sec_targets:
                if (ident, st) in custom_map:
                    return list(custom_map[(ident, st)])

        # PASS 1B: Normalized cross-map match on specific track identifiers + section
        for (map_ident, map_sec), notes_val in custom_map.items():
            map_sec_str = str(map_sec).lower().strip()
            map_sec_clean = Phase6Parser._clean_track_ident(map_sec)
            if map_sec_str in [str(s_idx), s_name_lower] or (map_sec_clean and map_sec_clean == s_name_clean):
                # Check if map_ident is integer track index
                if str(map_ident).strip().isdigit() and int(str(map_ident).strip()) == t_idx:
                    return list(notes_val)
                map_ident_clean = Phase6Parser._clean_track_ident(map_ident)
                if map_ident_clean and len(map_ident_clean) >= 3:
                    for cand_clean in [t_orig_clean, t_clean]:
                        if cand_clean and (map_ident_clean == cand_clean or map_ident_clean in cand_clean or cand_clean in map_ident_clean):
                            return list(notes_val)

        # PASS 2: Bidirectional role aliases resolution (only if no track-specific match found)
        role_aliases = RoleTrackOrchestrator.get_role_aliases(t_role)
        norm_name_role = RoleTrackOrchestrator.normalize_role(trk.get("original_name") or trk.get("name", ""))
        for r_extra in RoleTrackOrchestrator.get_role_aliases(norm_name_role):
            if r_extra not in role_aliases:
                role_aliases.append(r_extra)

        role_keys = []
        for alias in role_aliases:
            for st in sec_targets:
                role_keys.append((alias, st))
                role_keys.append((alias.lower(), st))
        for k in role_keys:
            if k in custom_map:
                return list(custom_map[k])

        for (map_ident, map_sec), notes_val in custom_map.items():
            map_sec_str = str(map_sec).lower().strip()
            if map_sec_str in [str(s_idx), s_name_lower]:
                map_ident_str = str(map_ident).strip().upper()
                if map_ident_str in role_aliases:
                    return list(notes_val)

        # PASS 3A: Specific track fallback to "all"
        for ident in specific_idents:
            if (ident, "all") in custom_map:
                return Phase6Parser._tile_notes_to_beats(custom_map[(ident, "all")], s_beats)

        for (map_ident, map_sec), notes_val in custom_map.items():
            if str(map_sec).lower() == "all":
                if str(map_ident).strip().isdigit() and int(str(map_ident).strip()) == t_idx:
                    return Phase6Parser._tile_notes_to_beats(notes_val, s_beats)
                map_ident_clean = Phase6Parser._clean_track_ident(map_ident)
                if map_ident_clean and len(map_ident_clean) >= 3:
                    for cand_clean in [t_orig_clean, t_clean]:
                        if cand_clean and (map_ident_clean == cand_clean or map_ident_clean in cand_clean or cand_clean in map_ident_clean):
                            return Phase6Parser._tile_notes_to_beats(notes_val, s_beats)

        # PASS 3B: Role alias fallback to "all"
        for alias in role_aliases:
            for k in [(alias, "all"), (alias.lower(), "all")]:
                if k in custom_map:
                    return Phase6Parser._tile_notes_to_beats(custom_map[k], s_beats)

        for (map_ident, map_sec), notes_val in custom_map.items():
            if str(map_sec).lower() == "all":
                map_ident_str = str(map_ident).strip().upper()
                if map_ident_str in role_aliases:
                    return Phase6Parser._tile_notes_to_beats(notes_val, s_beats)

        return None

