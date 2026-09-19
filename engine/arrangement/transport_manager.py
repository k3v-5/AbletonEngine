# engine/arrangement/transport_manager.py
"""
Smart Transport & Cue Point Manager:
Automates Arrangement timeline navigation, section cue point markers,
and transport scrubbing directly inside Ableton Live 12.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
import logging
import re

logger = logging.getLogger("TransportManager")


class TransportManager:
    """Orchestrates arrangement cue points and conversational transport navigation."""

    @classmethod
    def get_timeline_map(cls, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculates exact bar and beat intervals for every section in the arrangement.
        """
        timeline: List[Dict[str, Any]] = []
        current_bar = 0.0

        for idx, sec in enumerate(sections):
            name = str(sec.get("name", f"Section_{idx + 1}"))
            bars = float(sec.get("bars", 16.0))
            start_beat = current_bar * 4.0
            end_bar = current_bar + bars
            end_beat = end_bar * 4.0

            timeline.append({
                "index": idx,
                "name": name,
                "start_bar": current_bar,
                "end_bar": end_bar,
                "bars": bars,
                "start_beat": start_beat,
                "end_beat": end_beat
            })
            current_bar = end_bar

        return timeline

    @classmethod
    def sync_section_cue_points(cls, conn: Any, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Creates named cue points on Live's Arrangement timeline for all project sections.
        """
        if not conn or not hasattr(conn, "send_command"):
            return {"status": "SKIPPED", "message": "No Live connection available."}

        timeline = cls.get_timeline_map(sections)
        created_cues = []

        try:
            # Delete existing cue points if supported
            existing_cues = conn.send_command("get_cue_points", {})
            c_list = existing_cues.get("cue_points", existing_cues) if isinstance(existing_cues, dict) else []
            if isinstance(c_list, list):
                for cp in c_list:
                    cp_id = cp.get("id", cp.get("time"))
                    if cp_id is not None:
                        try:
                            conn.send_command("delete_cue_point", {"cue_point_id": cp_id})
                        except Exception:
                            pass
        except Exception as e:
            logger.debug(f"Cue cleanup notice: {e}")

        for item in timeline:
            b_time = item["start_beat"]
            c_name = item["name"]
            try:
                conn.send_command("create_cue_point", {
                    "time": b_time,
                    "name": c_name
                })
                created_cues.append({"name": c_name, "time": b_time})
            except Exception as e:
                logger.debug(f"Notice creating cue point '{c_name}' at beat {b_time}: {e}")

        return {
            "status": "SUCCESS",
            "cue_points_created": len(created_cues),
            "cue_points": created_cues,
            "total_bars": timeline[-1]["end_bar"] if timeline else 0.0
        }

    @classmethod
    def jump_to_section(
        cls,
        conn: Any,
        sections: List[Dict[str, Any]],
        target: Union[str, int, float],
        start_playback: bool = True
    ) -> Dict[str, Any]:
        """
        Resolves a target section or bar and jumps playback head to that exact point.
        """
        timeline = cls.get_timeline_map(sections)
        target_beat: Optional[float] = None
        matched_section_name: str = "Custom Position"

        target_str = str(target).strip().lower()

        # 1. Bar number pattern match (e.g. "compas 24", "bar 16", "c32", or pure number)
        bar_m = re.search(r"(?:comp[aá]s|bar|c)?\s*(\d+(?:\.\d+)?)", target_str)
        if bar_m and any(kw in target_str for kw in ["compas", "compás", "bar", "c"]):
            bar_num = float(bar_m.group(1))
            target_beat = bar_num * 4.0
            matched_section_name = f"Compás {bar_num}"
        elif target_str.isdigit():
            bar_num = float(target_str)
            target_beat = bar_num * 4.0
            matched_section_name = f"Compás {bar_num}"

        # 2. Section name match
        if target_beat is None:
            for item in timeline:
                s_name = item["name"].lower()
                if target_str in s_name or s_name in target_str:
                    target_beat = item["start_beat"]
                    matched_section_name = item["name"]
                    break

        # Fallback to start
        if target_beat is None:
            target_beat = 0.0
            matched_section_name = timeline[0]["name"] if timeline else "Inicio"

        if conn and hasattr(conn, "send_command"):
            try:
                conn.send_command("jump_to_cue_point", {"target": target_beat})
            except Exception:
                try:
                    conn.send_command("set_current_song_time", {"time": target_beat})
                except Exception as ex:
                    logger.warning(f"Error jumping to beat {target_beat}: {ex}")

            if start_playback:
                try:
                    conn.send_command("start_playback", {})
                except Exception as ex:
                    logger.debug(f"Playback trigger notice: {ex}")

        return {
            "status": "NAVIGATED",
            "section": matched_section_name,
            "target_beat": target_beat,
            "target_bar": target_beat / 4.0,
            "playback_started": start_playback
        }
