# engine/arrangement/batch_composer.py
"""
Batch Multi-Track Composer:
Injects clips and notes across all tracks and sections in a single compound operation,
eliminating repetitive sequential network calls and ensuring atomic synchronization
between Session view clips and the Arrangement timeline.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import logging

logger = logging.getLogger("BatchComposer")


class BatchComposer:
    """Atomic multi-track composition and arrangement injection engine."""

    @classmethod
    def compose_batch(
        cls,
        conn: Any,
        session_data: Dict[str, Any],
        composition_data: Union[Dict[str, Any], List[Dict[str, Any]]],
        duplicate_to_arrangement: bool = True
    ) -> Dict[str, Any]:
        """
        Processes a full multi-track composition payload and injects all clips and notes.

        Args:
            conn: Ableton Live adapter or connection.
            session_data: The session state containing 'tracks' and 'sections'.
            composition_data: Map of track_name/role/index -> {section_name/idx: [notes]}
                             or list of clip items.
            duplicate_to_arrangement: If True, replicates clips on the Arrangement timeline.

        Returns:
            Dict summarizing clips created, notes injected, and tracks touched.
        """
        tracks = session_data.get("tracks", [])
        sections = session_data.get("sections", [])

        if not tracks or not sections:
            return {
                "status": "SKIPPED",
                "message": "Session contains no tracks or sections to compose onto.",
                "clips_created": 0,
                "notes_injected": 0
            }

        # Normalize composition data into a standardized lookup map: (track_key, section_key) -> [notes]
        comp_map: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}

        if isinstance(composition_data, dict):
            # Check for top-level keys like 'composition' or 'tracks'
            inner = composition_data.get("composition", composition_data.get("tracks", composition_data))
            if isinstance(inner, dict):
                for t_key, s_dict in inner.items():
                    if isinstance(s_dict, dict):
                        for s_key, n_list in s_dict.items():
                            if isinstance(n_list, list):
                                comp_map[(str(t_key).lower(), str(s_key).lower())] = n_list
                    elif isinstance(s_dict, list):
                        comp_map[(str(t_key).lower(), "all")] = s_dict
            elif isinstance(inner, list):
                for item in inner:
                    if isinstance(item, dict):
                        t_k = str(item.get("track", item.get("track_name", item.get("track_index", item.get("role", ""))))).lower()
                        s_k = str(item.get("section", item.get("section_index", "all"))).lower()
                        notes = item.get("notes", [])
                        if t_k and isinstance(notes, list):
                            comp_map[(t_k, s_k)] = notes

        elif isinstance(composition_data, list):
            for item in composition_data:
                if isinstance(item, dict):
                    t_k = str(item.get("track", item.get("track_name", item.get("track_index", item.get("role", ""))))).lower()
                    s_k = str(item.get("section", item.get("section_index", "all"))).lower()
                    notes = item.get("notes", [])
                    if t_k and isinstance(notes, list):
                        comp_map[(t_k, s_k)] = notes

        clips_created = 0
        notes_injected = 0
        tracks_touched = set()

        # Iterate over all tracks and sections to inject
        for trk in tracks:
            t_idx = trk.get("index", 0)
            t_name = str(trk.get("name", "")).lower()
            t_role = str(trk.get("role", "")).lower()

            current_beat = 0.0

            for s_idx, sec in enumerate(sections):
                s_name = str(sec.get("name", "")).lower()
                s_bars = float(sec.get("bars", 16))
                s_beats = s_bars * 4.0

                # Find matching notes from comp_map
                matched_notes = None
                lookup_keys = [
                    (str(t_idx), str(s_idx)),
                    (str(t_idx), s_name),
                    (t_name, str(s_idx)),
                    (t_name, s_name),
                    (t_role, str(s_idx)),
                    (t_role, s_name),
                    # Fallbacks for 'all'
                    (str(t_idx), "all"),
                    (t_name, "all"),
                    (t_role, "all")
                ]

                for lk in lookup_keys:
                    if lk in comp_map:
                        matched_notes = comp_map[lk]
                        break

                if matched_notes is None:
                    # Substring match on track name or role
                    for (mk_t, mk_s), n_val in comp_map.items():
                        if mk_s in (str(s_idx), s_name, "all"):
                            if mk_t in t_name or mk_t in t_role or t_role in mk_t:
                                matched_notes = n_val
                                break

                # Auto-clamp notes if track is a Chopping / Slicing track
                if matched_notes and (trk.get("chopping_mode") or "chop" in t_name or trk.get("slice_mode") == "Slicing"):
                    slices_cnt = int(trk.get("slices_count", 64))
                    if slices_cnt <= 0:
                        slices_cnt = 64
                    clamped_notes = []
                    for n in matched_notes:
                        n_c = dict(n)
                        p = int(n_c.get("pitch", 36))
                        if p < 36 or p >= (36 + slices_cnt):
                            n_c["pitch"] = 36 + ((p - 36) % slices_cnt)
                        clamped_notes.append(n_c)
                    matched_notes = clamped_notes

                # Inject into Live via connection
                if conn is not None and hasattr(conn, "send_command"):
                    try:
                        # 1. Reset/Delete existing session clip
                        conn.send_command("delete_clip", {"track_index": t_idx, "clip_index": s_idx})

                        if matched_notes:
                            # 2. Create Session clip
                            conn.send_command("create_clip", {
                                "track_index": t_idx,
                                "clip_index": s_idx,
                                "length": s_beats
                            })
                            conn.send_command("set_clip_name", {
                                "track_index": t_idx,
                                "clip_index": s_idx,
                                "name": f"{sec.get('name', f'Sec_{s_idx}')}"
                            })
                            conn.send_command("add_notes_to_clip", {
                                "track_index": t_idx,
                                "clip_index": s_idx,
                                "notes": [
                                    {
                                        "pitch": int(d["pitch"]),
                                        "start_time": round(float(d.get("start_time", d.get("start", 0.0))), 3),
                                        "duration": round(float(d.get("duration", 1.0)), 3),
                                        "velocity": int(d.get("velocity", 100)),
                                        "mute": bool(d.get("mute", False))
                                    }
                                    for d in matched_notes
                                ]
                            })
                            clips_created += 1
                            notes_injected += len(matched_notes)
                            tracks_touched.add(t_idx)

                            # 3. Duplicate to Arrangement timeline at exact current_beat
                            if duplicate_to_arrangement:
                                try:
                                    conn.send_command("duplicate_to_arrangement", {
                                        "track_index": t_idx,
                                        "clip_index": s_idx,
                                        "destination_time": current_beat
                                    })
                                except Exception as d_ex:
                                    logger.debug(f"Arrangement duplication notice: {d_ex}")
                    except Exception as e:
                        logger.warning(f"Batch compose error on track {t_idx} section {s_idx}: {e}")

                current_beat += s_beats

        return {
            "status": "SUCCESS",
            "clips_created": clips_created,
            "notes_injected": notes_injected,
            "tracks_touched": sorted(list(tracks_touched)),
            "sections_count": len(sections)
        }
