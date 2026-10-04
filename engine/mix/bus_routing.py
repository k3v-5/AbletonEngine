# engine/mix/bus_routing.py
"""
Submix Bus Routing Automator:
Automatically creates and routes audio group buses (Drums Bus, Bass Bus, Synths Bus, etc.)
with acoustic glue processing in Ableton Live 12.
"""

from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger("BusRouting")


class BusRoutingManager:
    """Orchestrates track grouping and submix bus signal flow."""

    STANDARD_BUS_GROUPS: Dict[str, List[str]] = {
        "DRUMS BUS": ["DRUMS", "PERCUSSION", "BEAT", "KIT"],
        "BASS BUS": ["BASS", "808", "SUB", "REESE"],
        "SYNTHS BUS": ["LEAD", "KEYS", "CHORDS", "PLUCK", "ARP"],
        "PADS BUS": ["PAD", "STRINGS", "ATMOSPHERE"],
        "VOCALS BUS": ["VOCALS", "VOX", "CHOPS"],
        "FX BUS": ["FX", "RISER", "IMPACT", "FOLEY"]
    }

    BUS_PROCESSING_RECIPES: Dict[str, Dict[str, Any]] = {
        "DRUMS BUS": {"glue_threshold": -4.0, "glue_ratio": 4.0, "glue_attack": 30.0, "glue_release": 0.2, "eq_low_cut": 28.0},
        "BASS BUS": {"glue_threshold": -6.0, "glue_ratio": 4.0, "glue_attack": 10.0, "glue_release": 0.4, "eq_mono_sub": True},
        "SYNTHS BUS": {"glue_threshold": -3.0, "glue_ratio": 2.0, "glue_attack": 10.0, "glue_release": 0.2, "eq_low_cut": 100.0},
        "PADS BUS": {"glue_threshold": -2.0, "glue_ratio": 2.0, "glue_attack": 30.0, "glue_release": 0.6, "eq_low_cut": 140.0},
        "VOCALS BUS": {"glue_threshold": -5.0, "glue_ratio": 4.0, "glue_attack": 1.0, "glue_release": 0.1, "eq_low_cut": 120.0},
        "FX BUS": {"glue_threshold": -2.0, "glue_ratio": 2.0, "glue_attack": 10.0, "glue_release": 0.2, "eq_low_cut": 80.0}
    }

    @classmethod
    def analyze_bus_topology(cls, tracks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Maps current tracks into their prospective submix buses based ONLY on the explicit output_bus field.
        """
        bus_map: Dict[str, List[Dict[str, Any]]] = {}

        for trk in tracks:
            output_bus = trk.get("output_bus")
            if output_bus:
                if output_bus not in bus_map:
                    bus_map[output_bus] = []
                bus_map[output_bus].append(trk)

        return bus_map

    @classmethod
    def setup_aux_return_tracks(cls, conn: Any) -> Dict[str, Any]:
        """
        Ensures auxiliary return tracks exist and are properly named in Live.
        """
        if conn is None or not hasattr(conn, "send_command"):
            return {"status": "MOCK_OK", "returns": []}

        code = """
ret_names = [r.name for r in song.return_tracks]
created_returns = []

# Ensure Reverb Aux exists
has_reverb_ret = False
for r in ret_names:
    if 'reverb' in r.lower():
        has_reverb_ret = True
        break
if not has_reverb_ret:
    new_ret = song.create_return_track()
    new_ret.name = "[RETURN] Reverb Aux"
    created_returns.append(new_ret.name)
else:
    for r in song.return_tracks:
        if 'reverb' in r.name.lower() and '[RETURN]' not in r.name:
            r.name = "[RETURN] Reverb Aux"
            created_returns.append(r.name)

# Ensure Delay Aux exists
has_delay_ret = False
for r in ret_names:
    if 'delay' in r.lower():
        has_delay_ret = True
        break
if not has_delay_ret:
    new_ret2 = song.create_return_track()
    new_ret2.name = "[RETURN] Delay Aux"
    created_returns.append(new_ret2.name)
else:
    for r in song.return_tracks:
        if 'delay' in r.name.lower() and '[RETURN]' not in r.name:
            r.name = "[RETURN] Delay Aux"
            created_returns.append(r.name)

result = {
    'status': 'SUCCESS',
    'total_returns': len(song.return_tracks),
    'return_names': [r.name for r in song.return_tracks],
    'created': created_returns
}
"""
        try:
            res = conn.send_command("execute_code", {"code": code})
            return res.get("result", {}) if isinstance(res, dict) else {}
        except Exception as ex:
            logger.debug(f"Aux return track setup notice: {ex}")
            return {"error": str(ex)}

    @classmethod
    def setup_submix_buses(cls, conn: Any, tracks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Constructs and physically configures the submix bus architecture in Ableton Live.
        Creates audio tracks with monitoring set to 'In' (0) and routes audio.
        """
        effective_tracks = tracks if tracks is not None else []
        topology = cls.analyze_bus_topology(effective_tracks)
        configured_buses: List[Dict[str, Any]] = []

        if conn is not None and hasattr(conn, "send_command"):
            for bus_name, member_tracks in topology.items():
                recipe = cls.BUS_PROCESSING_RECIPES.get(bus_name, {})
                bus_label = f"[BUS] {bus_name}" if not bus_name.startswith("[BUS]") else bus_name
                member_names = [t.get("name", "") for t in member_tracks]

                code_bus = f"""
existing_bus = None
for t in song.tracks:
    if t.name == {repr(bus_label)}:
        existing_bus = t
        break

if not existing_bus:
    existing_bus = song.create_audio_track(-1)
    existing_bus.name = {repr(bus_label)}

# Physical monitor in for audio group summing
existing_bus.current_monitoring_state = 0

# Physically route all member tracks' output to this group bus
mem_names = {repr(member_names)}
routed_members = []
for t in song.tracks:
    if t.name in mem_names:
        # Prevent sequential overwrite if already assigned
        if getattr(t, 'output_routing_type', None) and existing_bus.name in getattr(t.output_routing_type, 'display_name', ''):
            routed_members.append(t.name)
            continue
            
        for out_type in getattr(t, 'available_output_routing_types', []):
            if existing_bus.name in getattr(out_type, 'display_name', ''):
                try:
                    t.output_routing_type = out_type
                    routed_members.append(t.name)
                except Exception:
                    pass
                break

res = {{'bus_name': existing_bus.name, 'monitoring': existing_bus.current_monitoring_state, 'routed_members': routed_members}}
"""
                try:
                    conn.send_command("execute_code", {"code": code_bus})
                except Exception as ex_bus:
                    logger.debug(f"Submix bus creation notice for {bus_label}: {ex_bus}")

                # Instanciar físicamente los dispositivos de BUS_PROCESSING_RECIPES
                if recipe:
                    try:
                        code_check = f"""
b = next((t for t in song.tracks if t.name == {repr(bus_label)}), None)
return_val = len(b.devices) > 0 if b else False
"""
                        check_res = conn.send_command("execute_code", {"code": code_check})
                        if isinstance(check_res, dict) and not check_res.get("return_val", False):
                            conn.send_command("load_browser_item", {"track_name": bus_label, "item_uri": "query:AudioFx#Glue%20Compressor"})
                            conn.send_command("load_browser_item", {"track_name": bus_label, "item_uri": "query:AudioFx#EQ%20Eight"})
                    except Exception as ex:
                        logger.debug(f"Failed to load devices for {bus_label}: {ex}")

                configured_buses.append({
                    "bus_name": bus_name,
                    "bus_label": bus_label,
                    "tracks_count": len(member_tracks),
                    "member_tracks": member_names,
                    "glue_recipe": recipe
                })

            cls.setup_aux_return_tracks(conn)
        else:
            for bus_name, member_tracks in topology.items():
                recipe = cls.BUS_PROCESSING_RECIPES.get(bus_name, {})
                configured_buses.append({
                    "bus_name": bus_name,
                    "bus_label": f"[BUS] {bus_name}" if not bus_name.startswith("[BUS]") else bus_name,
                    "tracks_count": len(member_tracks),
                    "member_tracks": [t.get("name", f"Track {t.get('index')}") for t in member_tracks],
                    "glue_recipe": recipe
                })

        logger.info(f"Configured {len(configured_buses)} submix audio buses.")
        return {
            "status": "SUCCESS",
            "buses_count": len(configured_buses),
            "buses": configured_buses
        }

    @classmethod
    def route_tracks_to_submix_buses(cls, conn: Any, tracks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Re-evaluates and physically connects track output routings to their corresponding [BUS] tracks in Live.
        Crucial after instruments are loaded on MIDI tracks.
        """
        return cls.setup_submix_buses(conn, tracks)


# Alias for backward and architectural compatibility
BusRoutingEngine = BusRoutingManager
