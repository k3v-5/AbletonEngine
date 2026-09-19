# engine/arrangement/collision_guard.py
"""
Arrangement Collision Guard:
Punto 24: Detects and resolves timeline collisions and overlaps on arrangement tracks.
Prevents accidental double-triggering, phase cancellation, or stacked audio/MIDI layers.
Supports clean overwriting, automatic offset shifting, or protective rejection.
"""

from typing import Dict, Any, List, Optional, Tuple


class ArrangementCollisionGuard:
    """Safeguards arrangement timeline tracks against unintended clip collisions."""

    @staticmethod
    def intervals_overlap(
        start_a: float,
        len_a: float,
        start_b: float,
        len_b: float,
        tolerance: float = 0.05
    ) -> bool:
        """Returns True if interval A overlaps interval B (in beats)."""
        end_a = start_a + len_a
        end_b = start_b + len_b
        return (start_a < end_b - tolerance) and (end_a > start_b + tolerance)

    @classmethod
    def audit_track_timeline(
        cls,
        track_clips: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Scans all clips on a track and flags any overlapping boundary collisions.
        """
        sorted_clips = sorted(track_clips, key=lambda c: float(c.get("start_time", c.get("start", 0.0))))
        collisions = []

        for i in range(len(sorted_clips)):
            c_a = sorted_clips[i]
            s_a = float(c_a.get("start_time", c_a.get("start", 0.0)))
            l_a = float(c_a.get("length", 4.0))

            for j in range(i + 1, len(sorted_clips)):
                c_b = sorted_clips[j]
                s_b = float(c_b.get("start_time", c_b.get("start", 0.0)))
                l_b = float(c_b.get("length", 4.0))

                if cls.intervals_overlap(s_a, l_a, s_b, l_b):
                    collisions.append({
                        "clip_a": c_a.get("name", f"Clip {i}"),
                        "clip_b": c_b.get("name", f"Clip {j}"),
                        "start_a": round(s_a, 2),
                        "end_a": round(s_a + l_a, 2),
                        "start_b": round(s_b, 2),
                        "end_b": round(s_b + l_b, 2),
                        "overlap_beats": round(min(s_a + l_a, s_b + l_b) - max(s_a, s_b), 2)
                    })
                elif s_b > s_a + l_a:
                    break  # Sorted order ensures subsequent clips won't overlap

        return {
            "status": "COLLISIONS_DETECTED" if collisions else "TIMELINE_CLEAN",
            "collision_count": len(collisions),
            "collisions": collisions,
            "has_collisions": len(collisions) > 0
        }

    @classmethod
    def resolve_clip_placement(
        cls,
        existing_clips: List[Dict[str, Any]],
        new_start_beat: float,
        new_len_beats: float,
        strategy: str = "OVERWRITE_AND_TRIM"
    ) -> Dict[str, Any]:
        """
        Evaluates proposed clip placement against existing clips on the track.
        Strategies:
        - OVERWRITE_AND_TRIM: Identifies existing clips to delete or trim.
        - SHIFT_OFFSET: Shifts placement to earliest available empty space.
        - REJECT: Aborts if collision occurs.
        """
        strat = strategy.upper()
        colliding_clips = []

        for c in existing_clips:
            c_s = float(c.get("start_time", c.get("start", 0.0)))
            c_l = float(c.get("length", 4.0))
            if cls.intervals_overlap(new_start_beat, new_len_beats, c_s, c_l):
                colliding_clips.append(c)

        if not colliding_clips:
            return {
                "action": "PROCEED",
                "start_beat": new_start_beat,
                "length_beats": new_len_beats,
                "clips_to_delete": [],
                "clips_to_trim": []
            }

        if strat == "REJECT":
            return {
                "action": "REJECTED_COLLISION",
                "start_beat": new_start_beat,
                "length_beats": new_len_beats,
                "colliding_count": len(colliding_clips),
                "colliding_clips": [c.get("name", "unnamed") for c in colliding_clips]
            }

        elif strat == "SHIFT_OFFSET":
            # Search for next available open slot
            sorted_clips = sorted(existing_clips, key=lambda c: float(c.get("start_time", c.get("start", 0.0))))
            candidate_start = new_start_beat
            for c in sorted_clips:
                c_s = float(c.get("start_time", c.get("start", 0.0)))
                c_l = float(c.get("length", 4.0))
                c_e = c_s + c_l
                if cls.intervals_overlap(candidate_start, new_len_beats, c_s, c_l):
                    candidate_start = c_e  # Move past the end of this clip

            return {
                "action": "SHIFTED",
                "original_start": new_start_beat,
                "shifted_start": round(candidate_start, 2),
                "length_beats": new_len_beats,
                "clips_to_delete": [],
                "clips_to_trim": []
            }

        else:  # OVERWRITE_AND_TRIM
            to_delete = []
            to_trim = []
            new_end = new_start_beat + new_len_beats

            for c in colliding_clips:
                c_s = float(c.get("start_time", c.get("start", 0.0)))
                c_l = float(c.get("length", 4.0))
                c_e = c_s + c_l

                # If completely engulfed by new clip, delete it
                if c_s >= new_start_beat and c_e <= new_end:
                    to_delete.append(c)
                # If existing clip starts before and ends inside new clip -> trim its end
                elif c_s < new_start_beat and c_e <= new_end:
                    to_trim.append({
                        "clip": c,
                        "new_length": round(new_start_beat - c_s, 2)
                    })
                # If existing clip starts inside and ends after -> trim its start or delete
                else:
                    to_delete.append(c)

            return {
                "action": "OVERWRITE_AUTHORIZED",
                "start_beat": new_start_beat,
                "length_beats": new_len_beats,
                "clips_to_delete": to_delete,
                "clips_to_trim": to_trim,
                "colliding_count": len(colliding_clips)
            }
