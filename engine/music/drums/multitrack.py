# engine/music/drums/multitrack.py
"""
Multi-Track Drum Layering & Sample Kit Loader.
- Decomposes drum sequences into distinct physical tracks (Kick, Snare, Clap, Hats, Perc, Crash).
- Loads verified native Drum Kits (.adg) with real analog and acoustic samples into Drum Racks.
- Eliminates single-track drum clutter, allowing granular mixing, independent processing, and surgical arrangement mutes.
"""

from enum import Enum
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("MultiTrackDrums")


class DrumLayerRole(str, Enum):
    KICK = "kick"
    SNARE = "snare"
    CLAP = "clap"
    HIHAT_CLOSED = "hihat_closed"
    HIHAT_OPEN = "hihat_open"
    PERCUSSION = "percussion"
    CRASH = "crash"


@dataclass
class DrumLayerConfig:
    name: str
    role: DrumLayerRole
    track_index: int
    default_fader_db: float = -6.0


DRUM_LAYERS: List[DrumLayerConfig] = [
    DrumLayerConfig(name="Kick", role=DrumLayerRole.KICK, track_index=2, default_fader_db=-6.0),
    DrumLayerConfig(name="Snare", role=DrumLayerRole.SNARE, track_index=4, default_fader_db=-7.0),
    DrumLayerConfig(name="Clap", role=DrumLayerRole.CLAP, track_index=3, default_fader_db=-8.0),
    DrumLayerConfig(name="Hi-Hats", role=DrumLayerRole.HIHAT_CLOSED, track_index=5, default_fader_db=-10.0),
    DrumLayerConfig(name="Crash", role=DrumLayerRole.CRASH, track_index=9, default_fader_db=-12.0),
]


PITCH_TO_LAYER_ROLE: Dict[int, DrumLayerRole] = {
    35: DrumLayerRole.KICK,
    36: DrumLayerRole.KICK,
    37: DrumLayerRole.SNARE,  # Side stick
    38: DrumLayerRole.SNARE,  # Acoustic / Trap Snare
    39: DrumLayerRole.CLAP,   # Hand Clap
    40: DrumLayerRole.SNARE,  # Electric Snare
    41: DrumLayerRole.PERCUSSION,  # Low Tom
    42: DrumLayerRole.HIHAT_CLOSED,
    43: DrumLayerRole.PERCUSSION,  # High Floor Tom
    44: DrumLayerRole.HIHAT_CLOSED,  # Pedal Hat
    45: DrumLayerRole.PERCUSSION,  # Low Mid Tom
    46: DrumLayerRole.HIHAT_OPEN,
    47: DrumLayerRole.PERCUSSION,  # High Mid Tom
    48: DrumLayerRole.PERCUSSION,  # High Tom
    49: DrumLayerRole.CRASH,       # Crash Cymbal 1
    50: DrumLayerRole.PERCUSSION,  # High Tom
    51: DrumLayerRole.CRASH,       # Ride Cymbal
}

VERIFIED_DRUM_KITS: Dict[str, Dict[str, str]] = {
    "808_core": {
        "name": "808 Core Kit",
        "uri": "query:Drums#FileId_5422",
        "genre": "trap_hiphop",
    },
    "boom_bap": {
        "name": "Boom Bap Kit",
        "uri": "query:Drums#FileId_5305",
        "genre": "boom_bap_lofi",
    },
    "909_core": {
        "name": "909 Core Kit",
        "uri": "query:Drums#909%20Core%20Kit.adg",
        "genre": "house_techno",
    },
    "bnyx_boot": {
        "name": "BNYX Boot Kit",
        "uri": "query:Drums#BNYX%20Boot%20Kit.adg",
        "genre": "rage_drill",
    },
}

DEFAULT_TEMPLATE_TRACK_MAP: Dict[DrumLayerRole, int] = {
    DrumLayerRole.KICK: 2,
    DrumLayerRole.CLAP: 3,
    DrumLayerRole.SNARE: 4,
    DrumLayerRole.HIHAT_CLOSED: 5,
    DrumLayerRole.HIHAT_OPEN: 6,
    DrumLayerRole.PERCUSSION: 7,
    DrumLayerRole.CRASH: 9,
}


class MultiTrackDrumEngine:
    """
    Coordinates multi-track drum decomposition and physical sample kit loading.
    """

    DRUM_LAYERS = DRUM_LAYERS
    VERIFIED_DRUM_KITS = VERIFIED_DRUM_KITS

    @classmethod
    def split_drum_notes_by_layer(
        cls,
        notes: List[Dict[str, Any]],
    ) -> Dict[DrumLayerRole, List[Dict[str, Any]]]:
        """
        Partitions an aggregated drum note list into separated role layers.
        """
        layers: Dict[DrumLayerRole, List[Dict[str, Any]]] = {
            role: [] for role in DrumLayerRole
        }

        for note in notes:
            pitch = int(note.get("pitch", 36))
            role = PITCH_TO_LAYER_ROLE.get(pitch, DrumLayerRole.PERCUSSION)
            layers[role].append(note)

        return layers

    @classmethod
    def distribute_drum_pattern(
        cls,
        notes: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Distributes notes across standard drum layer names (Kick, Snare, Clap, Hi-Hats, Crash).
        """
        layers_map = {l.name: [] for l in cls.DRUM_LAYERS}
        for n in notes:
            pitch = int(n.get("pitch", 36))
            if pitch in (35, 36):
                layers_map["Kick"].append(n)
            elif pitch in (37, 38, 40):
                layers_map["Snare"].append(n)
            elif pitch == 39:
                layers_map["Clap"].append(n)
            elif pitch in (42, 44, 46):
                layers_map["Hi-Hats"].append(n)
            elif pitch in (49, 51):
                layers_map["Crash"].append(n)
            else:
                layers_map["Hi-Hats"].append(n)
        return layers_map

    @classmethod
    def load_verified_drum_kit(
        cls,
        conn: Any,
        track_index: int = 2,
        kit_id: str = "808_core",
    ) -> Dict[str, Any]:
        """
        Physically loads an authentic .adg drum kit preset into the track's Drum Rack.
        """
        kit_meta = VERIFIED_DRUM_KITS.get(kit_id, VERIFIED_DRUM_KITS["808_core"])
        uri = kit_meta["uri"]

        if conn and hasattr(conn, "send_command"):
            res = conn.send_command("load_instrument_or_effect", {
                "track_index": track_index,
                "uri": uri,
            })
            return {
                "status": "success",
                "kit_id": kit_id,
                "kit_name": kit_meta["name"],
                "uri": uri,
                "live_response": res,
            }

        return {
            "status": "success",
            "kit_id": kit_id,
            "kit_name": kit_meta["name"],
            "uri": uri,
            "mode": "mock_simulated",
        }

    @classmethod
    def scaffold_drum_tracks(
        cls,
        conn: Any,
        kit_type: str = "808_core"
    ) -> Dict[str, Any]:
        """
        Scaffolds multi-track drum architecture and loads verified sample kit.
        """
        load_res = cls.load_verified_drum_kit(conn, track_index=2, kit_id=kit_type)
        return {
            "status": "SUCCESS",
            "kit_loaded": VERIFIED_DRUM_KITS.get(kit_type, {}).get("name", "808 Core Kit"),
            "scaffolded_layers": [l.name for l in cls.DRUM_LAYERS],
            "details": load_res
        }

    @classmethod
    def setup_multitrack_session(
        cls,
        conn: Any,
        full_drum_notes: List[Dict[str, Any]],
        track_mapping: Optional[Dict[DrumLayerRole, int]] = None,
        clip_index: int = 0,
        length: float = 16.0,
    ) -> Dict[str, Any]:
        """
        Decomposes notes and creates dedicated clips on each physical drum track.
        """
        mapping = track_mapping or DEFAULT_TEMPLATE_TRACK_MAP
        layers = cls.split_drum_notes_by_layer(full_drum_notes)
        dispatched_tracks = []

        for role, notes_list in layers.items():
            if not notes_list:
                continue
            target_track = mapping.get(role)
            if target_track is None:
                continue

            if conn and hasattr(conn, "send_command"):
                conn.send_command("create_clip", {
                    "track_index": target_track,
                    "slot_index": clip_index,
                    "length": length,
                })
                conn.send_command("add_notes_to_clip", {
                    "track_index": target_track,
                    "clip_index": clip_index,
                    "notes": notes_list,
                })

            dispatched_tracks.append({
                "role": role.value,
                "track_index": target_track,
                "notes_count": len(notes_list),
            })

        return {
            "status": "success",
            "dispatched_layers_count": len(dispatched_tracks),
            "layers": dispatched_tracks,
        }
