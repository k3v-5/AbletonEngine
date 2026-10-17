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
    def infer_bus_for_track(cls, trk: Dict[str, Any]) -> str:
        """Infers the appropriate submix bus name for a track based on role or name."""
        if trk.get("output_bus"):
            return str(trk["output_bus"]).replace("[BUS] ", "").strip()

        role = str(trk.get("role", "")).upper()
        name = str(trk.get("name", "")).upper()

        # 1. Drums / Percussion
        if any(w in role or w in name for w in ("DRUM", "PERC", "BEAT", "KIT", "KICK", "SNARE", "HIHAT", "DEMBOW")):
            return "DRUMS BUS"
        # 2. Bass / Sub / 808
        if any(w in role or w in name for w in ("BASS", "808", "SUB", "REESE")):
            return "BASS BUS"
        # 3. Vocals / Chops
        if any(w in role or w in name for w in ("VOCAL", "VOX", "VOICE", "CHOP")):
            return "VOCALS BUS"
        # 4. Pads / Strings / Choir / Atmosphere
        if any(w in role or w in name for w in ("PAD", "STRINGS", "CHOIR", "VIOLIN", "CELLO", "ATMOSPHERE")):
            return "PADS BUS"
        # 5. Synths / Leads / Keys / Guitar / Brass
        return "SYNTHS BUS"

    @classmethod
    def analyze_bus_topology(cls, tracks: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Maps current tracks into their prospective submix buses.
        Infers the bus automatically from role and name if output_bus is not explicitly defined.
        """
        bus_map: Dict[str, List[Dict[str, Any]]] = {}

        for trk in tracks:
            t_name = str(trk.get("name", ""))
            if t_name.startswith("[BUS]") or t_name.startswith("[RETURN]"):
                continue

            bus_name = trk.get("output_bus") or cls.infer_bus_for_track(trk)
            clean_bus_name = bus_name.replace("[BUS] ", "").strip()
            if clean_bus_name not in bus_map:
                bus_map[clean_bus_name] = []
            bus_map[clean_bus_name].append(trk)

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
        effective_tracks = list(tracks) if tracks is not None else []

        # Auto-query tracks from Live if not supplied
        if not effective_tracks and conn is not None and hasattr(conn, "send_command"):
            try:
                code_get_trks = """
t_list = []
for i, t in enumerate(song.tracks):
    if not t.name.startswith("[BUS]") and not t.name.startswith("[RETURN]") and not getattr(t, 'is_foldable', False):
        t_list.append({'index': i, 'name': t.name, 'role': t.name})
return_val = t_list
result = t_list
"""
                res_get = conn.send_command("execute_code", {"code": code_get_trks})
                inner = res_get.get("result", {}) if isinstance(res_get, dict) else {}
                if isinstance(inner, dict):
                    live_trks = inner.get("return_val", inner.get("result", []))
                elif isinstance(inner, list):
                    live_trks = inner
                else:
                    live_trks = []
                if isinstance(live_trks, list) and live_trks:
                    effective_tracks = live_trks
            except Exception as ex_gt:
                logger.debug(f"Error querying live tracks: {ex_gt}")

        # Ensure output_bus is assigned on every track spec
        for trk in effective_tracks:
            if not trk.get("output_bus"):
                trk["output_bus"] = cls.infer_bus_for_track(trk)

        topology = cls.analyze_bus_topology(effective_tracks)
        configured_buses: List[Dict[str, Any]] = []

        if conn is not None and hasattr(conn, "send_command"):
            # 1. Create missing submix buses
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
existing_bus.mixer_device.volume.value = 0.85
"""
                try:
                    conn.send_command("execute_code", {"code": code_bus})
                except Exception as ex_bus:
                    logger.debug(f"Submix bus creation notice for {bus_label}: {ex_bus}")

                configured_buses.append({
                    "bus_name": bus_name,
                    "bus_label": bus_label,
                    "tracks_count": len(member_tracks),
                    "member_tracks": member_names,
                    "glue_recipe": recipe
                })

            # 2. Route tracks based on output_bus by physical track index and sovereign name
            code_route = f"""
tracks_spec = {repr(effective_tracks)}
routed_results = []

# Pass A: Group-level Submix Routing (Foldable Parent Groups -> Corresponding Submix Buses)
for g in song.tracks:
    if getattr(g, 'is_foldable', False) and not g.name.startswith("[BUS]"):
        g_name = g.name.lower()
        target_g_bus = None
        if any(w in g_name for w in ("drum", "perc", "beat", "kit")):
            target_g_bus = "[BUS] DRUMS BUS"
        elif any(w in g_name for w in ("synth", "inst", "lead", "key", "chord", "guitar", "brass", "string")):
            target_g_bus = "[BUS] SYNTHS BUS"
        elif any(w in g_name for w in ("vocal", "vox", "voice", "chop")):
            target_g_bus = "[BUS] VOCALS BUS"
        elif any(w in g_name for w in ("fx", "effect", "foley", "riser")):
            target_g_bus = "[BUS] FX BUS"
        elif any(w in g_name for w in ("bass", "808", "sub")):
            target_g_bus = "[BUS] BASS BUS"

        if target_g_bus:
            for out_type in getattr(g, 'available_output_routing_types', []):
                if target_g_bus.lower() in getattr(out_type, 'display_name', '').lower():
                    try:
                        g.output_routing_type = out_type
                        routed_results.append({{'group': g.name, 'target_bus': target_g_bus, 'type': 'group_bus'}})
                    except Exception:
                        pass
                    break

# Pass B: Track-level Submix Routing (Individual Audio/Instrument Tracks -> Target Submix Bus)
for idx, spec in enumerate(tracks_spec):
    bus_name = spec.get('output_bus')
    if not bus_name:
        continue
    target_bus = f"[BUS] {{bus_name}}" if not bus_name.startswith("[BUS]") else bus_name
    
    # Target track in Live by explicit spec['index'] and sovereign name (accounting for [ROLE] prefix)
    trk = None
    target_name = str(spec.get('name', '')).strip()
    target_role = str(spec.get('role', '')).strip()
    spec_idx = spec.get('index')

    if spec_idx is not None and 0 <= int(spec_idx) < len(song.tracks):
        cand = song.tracks[int(spec_idx)]
        if not cand.name.startswith("[BUS]") and not getattr(cand, 'is_foldable', False):
            if (not target_name) or (target_name.lower() in cand.name.lower()) or (target_role and f"[{{target_role.lower()}}]" in cand.name.lower()):
                trk = cand

    if not trk and target_name:
        for t in song.tracks:
            if t.name.startswith("[BUS]") or getattr(t, 'is_foldable', False):
                continue
            if t.name.lower() == target_name.lower() or t.name.lower() == f"[{{target_role.lower()}}] {{target_name.lower()}}" or target_name.lower() in t.name.lower():
                trk = t
                break

    if not trk:
        fallback_i = int(spec_idx) if spec_idx is not None else idx
        if 0 <= fallback_i < len(song.tracks):
            cand = song.tracks[fallback_i]
            if not cand.name.startswith("[BUS]") and not getattr(cand, 'is_foldable', False):
                trk = cand

    if trk and not trk.name.startswith("[BUS]"):
        target_assigned = False
        for out_type in getattr(trk, 'available_output_routing_types', []):
            if target_bus.lower() in getattr(out_type, 'display_name', '').lower():
                try:
                    trk.output_routing_type = out_type
                    routed_results.append({{'track': trk.name, 'target_bus': target_bus, 'type': 'direct'}})
                    target_assigned = True
                except Exception:
                    pass
                break

        # If direct track routing is restricted (e.g. grouped MIDI track before instrument load),
        # ensure parent group track routes to target_bus
        if not target_assigned and getattr(trk, 'is_grouped', False):
            p_group = getattr(trk, 'group_track', None)
            if p_group:
                for out_type in getattr(p_group, 'available_output_routing_types', []):
                    if target_bus.lower() in getattr(out_type, 'display_name', '').lower():
                        try:
                            p_group.output_routing_type = out_type
                            routed_results.append({{'track': trk.name, 'parent_group': p_group.name, 'target_bus': target_bus, 'type': 'parent_group_bus'}})
                        except Exception:
                            pass
                        break

bus_indices = {{t.name: i for i, t in enumerate(song.tracks) if t.name.startswith("[BUS]")}}
return_val = {{'routed': routed_results, 'buses': bus_indices}}
result = return_val
"""
            try:
                res_route = conn.send_command("execute_code", {"code": code_route})
                inner_r = res_route.get("result", res_route) if isinstance(res_route, dict) else {}
                r_val = inner_r.get("return_val", inner_r.get("result", {})) if isinstance(inner_r, dict) else {}
                bus_indices = r_val.get("buses", {}) if isinstance(r_val, dict) else {}
            except Exception as ex_route:
                logger.debug(f"Submix bus audio routing notice: {ex_route}")
                bus_indices = {}

            # 3. Physically load devices (Glue Compressor + EQ Eight) using track_index
            for b_info in configured_buses:
                b_lbl = b_info["bus_label"]
                b_idx = bus_indices.get(b_lbl)
                if b_idx is not None and b_info.get("glue_recipe"):
                    try:
                        code_check = f"""
b = song.tracks[{b_idx}] if {b_idx} < len(song.tracks) else None
return_val = len(b.devices) > 0 if b else False
result = return_val
"""
                        chk = conn.send_command("execute_code", {"code": code_check})
                        c_inner = chk.get("result", chk) if isinstance(chk, dict) else {}
                        has_devs = c_inner.get("return_val", c_inner.get("result", False)) if isinstance(c_inner, dict) else False
                        if not has_devs:
                            conn.send_command("load_browser_item", {"track_index": b_idx, "item_uri": "query:AudioFx#Glue%20Compressor"})
                            conn.send_command("load_browser_item", {"track_index": b_idx, "item_uri": "query:AudioFx#EQ%20Eight"})
                    except Exception as ex_dev:
                        logger.debug(f"Failed to load devices on {b_lbl} at index {b_idx}: {ex_dev}")

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
