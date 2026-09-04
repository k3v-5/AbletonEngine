# engine/session/diff.py
from typing import Dict, Any, List
from ..models import DiffReport, TrackNode

class SessionDiff:
    """Calculates granular differences between the Engine's SHADOW_STATE and Live's REAL_STATE"""
    @staticmethod
    def compute_diff(shadow_tracks: Dict[str, TrackNode], real_tracks_info: List[Dict[str, Any]]) -> DiffReport:
        report = DiffReport()

        # Build lookup maps for shadow state
        shadow_by_id = dict(shadow_tracks)
        shadow_by_index = {t.ableton_index: t for t in shadow_tracks.values()}
        shadow_by_name = {}
        for t in shadow_tracks.values():
            shadow_by_name.setdefault(t.name, []).append(t)

        matched_shadow_ids = set()
        matched_real_indices = set()

        # Step 1: Match by index and name (exact match)
        for real_track in real_tracks_info:
            r_idx = real_track["index"]
            r_name = real_track["name"]
            if r_idx in shadow_by_index and shadow_by_index[r_idx].name == r_name:
                sh_track = shadow_by_index[r_idx]
                matched_shadow_ids.add(sh_track.id)
                matched_real_indices.add(r_idx)
                # Check property modifications
                SessionDiff._check_properties(sh_track, real_track, report)

        # Step 2: Match remaining by name (tracks that may have moved index)
        for real_track in real_tracks_info:
            r_idx = real_track["index"]
            if r_idx in matched_real_indices:
                continue
            r_name = real_track["name"]
            candidates = [t for t in shadow_by_name.get(r_name, []) if t.id not in matched_shadow_ids]
            if len(candidates) == 1:
                sh_track = candidates[0]
                matched_shadow_ids.add(sh_track.id)
                matched_real_indices.add(r_idx)
                # Track moved!
                report.moved.append({
                    "id": sh_track.id,
                    "name": sh_track.name,
                    "from_index": sh_track.ableton_index,
                    "to_index": r_idx
                })
                SessionDiff._check_properties(sh_track, real_track, report)

        # Step 3: Match remaining by index (tracks that were renamed in-place)
        for real_track in real_tracks_info:
            r_idx = real_track["index"]
            if r_idx in matched_real_indices:
                continue
            if r_idx in shadow_by_index and shadow_by_index[r_idx].id not in matched_shadow_ids:
                sh_track = shadow_by_index[r_idx]
                matched_shadow_ids.add(sh_track.id)
                matched_real_indices.add(r_idx)
                # Track renamed!
                report.renamed.append({
                    "id": sh_track.id,
                    "before": sh_track.name,
                    "after": real_track["name"],
                    "index": r_idx
                })
                SessionDiff._check_properties(sh_track, real_track, report)

        # Step 4: Unmatched real tracks are ADDED
        for real_track in real_tracks_info:
            if real_track["index"] not in matched_real_indices:
                report.added.append({
                    "type": "track",
                    "name": real_track["name"],
                    "index": real_track["index"],
                    "is_midi": real_track.get("is_midi_track", True),
                    "is_audio": real_track.get("is_audio_track", False)
                })

        # Step 5: Unmatched shadow tracks are REMOVED
        for sh_id, sh_track in shadow_tracks.items():
            if sh_id not in matched_shadow_ids:
                report.removed.append({
                    "type": "track",
                    "id": sh_id,
                    "name": sh_track.name,
                    "last_index": sh_track.ableton_index,
                    "role": sh_track.metadata.role
                })

        return report

    @staticmethod
    def _check_properties(sh_track: TrackNode, real_track: Dict[str, Any], report: DiffReport):
        # Compare volume (threshold for floating point delta)
        r_vol = float(real_track.get("volume", 0.85))
        if abs(sh_track.volume - r_vol) > 0.005:
            report.modified.append({
                "id": sh_track.id,
                "name": sh_track.name,
                "property": "volume",
                "before": round(sh_track.volume, 3),
                "after": round(r_vol, 3)
            })

        # Compare panning
        r_pan = float(real_track.get("panning", 0.0))
        if abs(sh_track.panning - r_pan) > 0.005:
            report.modified.append({
                "id": sh_track.id,
                "name": sh_track.name,
                "property": "panning",
                "before": round(sh_track.panning, 3),
                "after": round(r_pan, 3)
            })

        # Compare mute
        r_mute = bool(real_track.get("mute", False))
        if sh_track.mute != r_mute:
            report.modified.append({
                "id": sh_track.id,
                "name": sh_track.name,
                "property": "mute",
                "before": sh_track.mute,
                "after": r_mute
            })

        # Compare solo
        r_solo = bool(real_track.get("solo", False))
        if sh_track.solo != r_solo:
            report.modified.append({
                "id": sh_track.id,
                "name": sh_track.name,
                "property": "solo",
                "before": sh_track.solo,
                "after": r_solo
            })

        # Compare type
        real_type = "audio" if (real_track.get("is_audio_track") or not real_track.get("is_midi_track")) else "midi"
        if sh_track.type != real_type:
            report.modified.append({
                "id": sh_track.id,
                "name": sh_track.name,
                "property": "type",
                "before": sh_track.type,
                "after": real_type
            })

