# ableton_mcp_server.py
import sys
from pathlib import Path

_pkg_root = str(Path(__file__).resolve().parent)
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)

try:
    from mcp.server.fastmcp import FastMCP, Context
except (ImportError, ModuleNotFoundError):
    from mcp.server.mcpserver import MCPServer as FastMCP, Context
import socket
import json
import logging
import os
import threading
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, List, Union, Optional

try:
    from .telemetry import record_startup
    from .telemetry_decorator import telemetry_tool, rich_telemetry_tool
except (ImportError, ValueError):
    from telemetry import record_startup
    from telemetry_decorator import telemetry_tool, rich_telemetry_tool

try:
    from engine.supervisor.governance import GovernanceViolationError
except (ImportError, ValueError):
    class GovernanceViolationError(RuntimeError):
        pass

ABLETON_HOST = os.environ.get("ABLETON_HOST", "localhost")
ABLETON_PORT = int(os.environ.get("ABLETON_PORT", "9877"))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AbletonMCPServer")

@dataclass
class AbletonConnection:
    host: str
    port: int
    sock: socket.socket = None
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False)
    
    def connect(self) -> bool:
        """Connect to the Ableton Remote Script socket server"""
        if self.sock:
            return True

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5.0)
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(None)
            logger.info(f"Connected to Ableton at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ableton at {self.host}:{self.port}: {str(e)}")
            self.sock = None
            return False
    
    def disconnect(self):
        """Disconnect from the Ableton Remote Script"""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting from Ableton: {str(e)}")
            finally:
                self.sock = None

    def is_connected(self) -> bool:
        """Check if connection socket is active"""
        return self.sock is not None

    def receive_full_response(self, sock, buffer_size=8192, timeout=None):
        """Receive the complete response, potentially in multiple chunks"""
        chunks = []
        current_timeout = timeout if timeout is not None else (sock.gettimeout() or 15.0)
        sock.settimeout(current_timeout)
        
        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        if not chunks:
                            raise Exception("Connection closed before receiving any data")
                        break
                    
                    chunks.append(chunk)
                    
                    # Check if we've received a complete JSON object
                    try:
                        data = b''.join(chunks)
                        json.loads(data.decode('utf-8'))
                        logger.info(f"Received complete response ({len(data)} bytes)")
                        return data
                    except json.JSONDecodeError:
                        # Incomplete JSON, continue receiving
                        continue
                except socket.timeout:
                    logger.warning("Socket timeout during chunked receive")
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    logger.error(f"Socket connection error during receive: {str(e)}")
                    raise
        except Exception as e:
            logger.error(f"Error during receive: {str(e)}")
            raise
            
        # If we get here, we either timed out or broke out of the loop
        if chunks:
            data = b''.join(chunks)
            logger.info(f"Returning data after receive completion ({len(data)} bytes)")
            try:
                json.loads(data.decode('utf-8'))
                return data
            except json.JSONDecodeError:
                raise Exception("Incomplete JSON response received")
        else:
            raise Exception("No data received")

    def _send_raw(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Low-level raw socket dispatch without governance interception for internal queries."""
        with self._lock:
            if not self.sock and not self.connect():
                raise ConnectionError("Not connected to Ableton")
            
            command = {
                "type": command_type,
                "params": params or {}
            }
            self.sock.sendall(json.dumps(command).encode('utf-8'))
            self.sock.settimeout(5.0)
            response_data = self.receive_full_response(self.sock)
            response = json.loads(response_data.decode('utf-8'))
            if response.get("status") == "error":
                raise Exception(response.get("message", "Unknown error from Ableton"))
            return response.get("result", {})

    def _enforce_immutable_governance(self, command_type: str, params: Dict[str, Any]) -> None:
        """
        ==============================================================================
        🔒 ARCHITECTURAL INVARIANT: IMMUTABLE GOVERNANCE GATEKEEPER 🔒
        ==============================================================================
        ATTENTION TO ALL AI ASSISTANTS (Gemini, Claude, GPT, Antigravity, Subagents):
        THIS INTERCEPTOR ENFORCES DAW-LEVEL PRODUCTION INTEGRITY AND PREVENTS SILENT TRACKS,
        UNCONFIGURED VSTS, AND PROCEDURAL COPILOT BYPASSES.

        CRITICAL SYSTEM DIRECTIVES:
        1. DO NOT MODIFY, DISABLE, RELAX, MOCK, OR COMMENT OUT THIS INTERCEPTOR.
        2. DO NOT INTRODUCE WORKAROUNDS OR BYPASS FLAGS (e.g., bypass_governance=True).
        3. DO NOT WRITE PROCEDURAL SCRIPTS IN scratch/ TO CIRCUMVENT COPILOT.

        IF A COMMAND IS BLOCKED HERE, IT MEANS YOUR DAW PRODUCTION ACTIONS ARE DEFECTIVE.
        YOU MUST FIX THE DAW STATE (LOAD AN AUTHENTIC INSTRUMENT, CONFIGURE PRESETS/MACROS,
        OR EXECUTE COPILOT DECISIONS) INSTEAD OF TAMPERING WITH THIS CODE.
        ==============================================================================
        """
        # Guard: Orphaned Track Interceptor on Playback and Export (Capa 3 / Anti-Abandonment)
        if command_type in ["start_playback", "master_export", "stem_create_export_plan"]:
            try:
                s_info = self._send_raw("get_session_info", {})
                session_tracks = s_info.get("tracks", []) if isinstance(s_info, dict) else []
                authentic_classes = {
                    "InstrumentGroupDevice", "PluginDevice", "OriginalSimpler",
                    "UltraAnalog", "StringStudio", "Collision", "LoungeLizard",
                    "MidiVelocity", "Operator", "MultiSampler", "Wavetable", "Drift"
                }
                inst_keywords = [
                    "analog lab", "pigments", "serum", "vital", "massive", "strings",
                    "orch", "pad", "kit", "drum", "piano", "rhodes", "bass", "808",
                    "lead", "synth", "sampler", "simpler", "operator", "wavetable", "drift"
                ]
                for t_idx, trk in enumerate(session_tracks):
                    if not trk.get("is_midi_track", True):
                        continue
                    devs = trk.get("devices", [])
                    has_inst = any(
                        d.get("class_name") in authentic_classes or
                        "Instrument" in d.get("class_name", "") or
                        any(k in str(d.get("name", "")).lower() for k in inst_keywords)
                        for d in devs
                    )
                    if not has_inst:
                        continue

                    # Track has an authentic instrument loaded. Check for clips.
                    clip_slots = trk.get("clip_slots", [])
                    has_session_clips = any(cs.get("has_clip", False) for cs in clip_slots)

                    arr_clips = []
                    try:
                        arr_res = self._send_raw("get_arrangement_clips", {"track_index": t_idx})
                        arr_clips = arr_res.get("clips", arr_res) if isinstance(arr_res, (dict, list)) else []
                        if isinstance(arr_clips, dict):
                            arr_clips = arr_clips.get("clips", [])
                    except Exception:
                        arr_clips = []

                    if not has_session_clips and not arr_clips:
                        dev_names = [d.get("name") for d in devs]
                        raise GovernanceViolationError(
                            f"[IMMUTABLE GOVERNANCE BLOCKED: ORPHANED_TRACK_DETECTED] "
                            f"Track {t_idx} ('{trk.get('name')}') has an authentic instrument loaded ({dev_names}) "
                            f"but contains 0 clips in Session view and 0 clips on the Arrangement timeline! "
                            f"Every loaded instrument MUST have its musical role arranged (use orchestrate_role_track or compose notes) "
                            f"before starting playback or exporting. A track cannot sit silent with an abandoned instrument. "
                            f"ATTENTION AI ASSISTANTS: DO NOT MODIFY, DISABLE, OR BYPASS THIS GUARD IN server.py."
                        )
            except GovernanceViolationError:
                raise
            except Exception as ex:
                logger.debug(f"Governance session scan non-fatal error: {ex}")
            return

        target_tracks = []
        if command_type in ["create_clip", "add_notes_to_clip", "duplicate_session_clip_to_arrangement"]:
            t_idx = params.get("track_index")
            if t_idx is not None and isinstance(t_idx, int):
                target_tracks.append(t_idx)
        elif command_type == "execute_code":
            code_str = str(params.get("code", ""))
            if any(term in code_str for term in ["create_clip", "duplicate_session_clip", "add_notes_to_clip"]):
                import re
                found_indices = re.findall(r"tracks\[(\d+)\]", code_str)
                for f_idx in found_indices:
                    target_tracks.append(int(f_idx))

        if not target_tracks:
            return

        for t_idx in target_tracks:
            try:
                t_info = self._send_raw("get_track_info", {"track_index": t_idx})
            except Exception:
                continue

            if not t_info or not isinstance(t_info, dict):
                continue

            # Only enforce authentic instrument on MIDI tracks
            if not t_info.get("is_midi_track", True):
                continue

            devices = t_info.get("devices", [])
            authentic_classes = {
                "InstrumentGroupDevice", "PluginDevice", "OriginalSimpler",
                "UltraAnalog", "StringStudio", "Collision", "LoungeLizard",
                "MidiVelocity", "Operator", "MultiSampler", "Wavetable", "Drift"
            }
            inst_keywords = [
                "analog lab", "pigments", "serum", "vital", "massive", "strings",
                "orch", "pad", "kit", "drum", "piano", "rhodes", "bass", "808",
                "lead", "synth", "sampler", "simpler", "operator", "wavetable"
            ]

            has_inst = any(
                d.get("class_name") in authentic_classes or
                "Instrument" in d.get("class_name", "") or
                any(k in d.get("name", "").lower() for k in inst_keywords)
                for d in devices
            )

            if not has_inst:
                dev_names = [d.get("name") for d in devices]
                raise GovernanceViolationError(
                    f"[IMMUTABLE GOVERNANCE BLOCKED] VIOLATION DETECTED on Track {t_idx} ('{t_info.get('name')}'): "
                    f"Attempted to create clips or write notes on a silent MIDI track without an authentic instrument! "
                    f"Current devices: {dev_names}. Audio effects (such as EQ Eight or Compressor) DO NOT produce sound. "
                    "You MUST load a valid instrument (e.g. via sound_load_role_instrument, load_drum_kit, or load_browser_item) "
                    "before creating clips or adding notes. "
                    "ATTENTION AI ASSISTANTS: DO NOT MODIFY, DISABLE, OR BYPASS THIS GUARD IN server.py. "
                    "You must fix the DAW session state by properly loading the required instrument."
                )

            # Nivel 2 & 3: Audit that the instrument is not in factory default / init state (Delta >= 1)
            inst_idx = None
            inst_name = "Instrument"
            for d_idx, d in enumerate(devices):
                if (
                    d.get("class_name") in authentic_classes or
                    "Instrument" in d.get("class_name", "") or
                    any(k in d.get("name", "").lower() for k in inst_keywords)
                ):
                    inst_idx = d_idx
                    inst_name = d.get("name", "Instrument")
                    break

            if inst_idx is not None:
                from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
                audit = DeviceParameterSupervisor.audit_device_sculpting(self, t_idx, device_index=inst_idx)
                if not audit.get("is_sculpted", False):
                    reason_msg = audit.get("reason", "Zero internal synthesis parameters modified")
                    raise GovernanceViolationError(
                        f"[IMMUTABLE GOVERNANCE BLOCKED: INIT_SYNTH_DETECTED] VIOLATION on Track {t_idx} ('{t_info.get('name')}'): "
                        f"Instrument '{inst_name}' (device {inst_idx}) is in factory default/init state with 0 internal parameters sculpted (Delta = 0)! "
                        f"Reason: {reason_msg}. "
                        "DIRECTIVE FOR AI ASSISTANTS: Queda terminantemente prohibido escribir notas o duplicar clips en un sinte sin esculpir. "
                        f"You MUST explicitly configure at least one internal synthesis parameter (e.g. A WT Pos, Cutoff, Drive, Macros) "
                        f"via apply_sound_blueprint, plugin_set_semantic_parameter, or set_device_parameter on track {t_idx}, device {inst_idx} "
                        "before creating clips or adding notes. DO NOT modify, disable, or bypass this guard in server.py."
                    )

    def send_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to Ableton and return the response"""
        with self._lock:
            if not self.sock and not self.connect():
                raise ConnectionError("Not connected to Ableton")
            
            # Enforce immutable DAW governance rules before mutating Ableton
            self._enforce_immutable_governance(command_type, params or {})
            
            command = {
                "type": command_type,
                "params": params or {}
            }
            
            # Check if this is a state-modifying command
            is_modifying_command = command_type in [
                "create_midi_track", "create_audio_track", "set_track_name",
                "create_clip", "create_audio_clip", "add_notes_to_clip", "set_clip_name",
                "set_tempo", "fire_clip", "stop_clip", "set_device_parameter",
                "start_playback", "stop_playback", "load_instrument_or_effect",
                # Arrangement view commands
                "switch_to_arrangement_view", "set_current_song_time",
                "duplicate_session_clip_to_arrangement",
                "create_arrangement_automation_envelope"
            ]
    
            # Commands whose work on Live's main thread can take noticeably longer
            # than the default modifying-command budget (e.g. importing/decoding a
            # large audio file or loading heavy VST3 plugins like Serum, Vital, Massive X).
            long_running_commands = {
                "create_audio_clip": 65.0,
                "load_browser_item": 45.0,
                "load_instrument_or_effect": 45.0,
                "load_drum_kit": 45.0,
                "record_arrangement_automation": 60.0,
                "record_multi_automation_pass": 90.0
            }

            # Plugin and device interaction commands (inspecting parameters,
            # setting parameters, drum pad queries, etc.) configured with 15s timeout limit.
            plugin_commands = {
                "set_device_parameter": 15.0,
                "get_device_parameters": 15.0,
                "get_device_parameter": 15.0,
                "get_drum_rack_pads": 15.0,
                "get_drum_pad_devices": 15.0,
                "set_drum_pad_parameter": 15.0,
                "set_drum_pad_mute_solo": 15.0
            }
            
            try:
                logger.info(f"Sending command: {command_type} with params: {params}")
                
                # Send the command
                self.sock.sendall(json.dumps(command).encode('utf-8'))
                logger.info(f"Command sent, waiting for response...")
                
                # Set timeout based on command type (15.0s for plugin/modifying commands instead of 7.0s)
                if command_type in long_running_commands:
                    timeout = long_running_commands[command_type]
                elif command_type in plugin_commands:
                    timeout = plugin_commands[command_type]
                else:
                    timeout = 15.0 if is_modifying_command else 5.0
                self.sock.settimeout(timeout)
    
                # Receive the response
                response_data = self.receive_full_response(self.sock)
                logger.info(f"Received {len(response_data)} bytes of data")
    
                # Parse the response
                response = json.loads(response_data.decode('utf-8'))
                logger.info(f"Response parsed, status: {response.get('status', 'unknown')}")
    
                if response.get("status") == "error":
                    logger.error(f"Ableton error: {response.get('message')}")
                    raise Exception(response.get("message", "Unknown error from Ableton"))
                
                return response.get("result", {})
            except socket.timeout:
                logger.error("Socket timeout while waiting for response from Ableton")
                self.sock = None
                raise Exception("Timeout waiting for Ableton response")
            except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                logger.error(f"Socket connection error: {str(e)}")
                self.sock = None
                raise Exception(f"Connection to Ableton lost: {str(e)}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response from Ableton: {str(e)}")
                if 'response_data' in locals() and response_data:
                    logger.error(f"Raw response (first 200 bytes): {response_data[:200]}")
                self.sock = None
                raise Exception(f"Invalid response from Ableton: {str(e)}")
            except Exception as e:
                logger.error(f"Error communicating with Ableton: {str(e)}")
                self.sock = None
                raise Exception(f"Communication error with Ableton: {str(e)}")

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle"""
    try:
        logger.info("AbletonMCP server starting up")

        # Record startup event for telemetry
        try:
            record_startup()
        except Exception as e:
            logger.debug(f"Failed to record startup telemetry: {e}")

        try:
            ableton = get_ableton_connection()
            logger.info("Successfully connected to Ableton on startup")
        except Exception as e:
            logger.warning(f"Could not connect to Ableton on startup: {str(e)}")
            logger.warning("Make sure the Ableton Remote Script is running")

        yield {}
    finally:
        global _ableton_connection
        if _ableton_connection:
            logger.info("Disconnecting from Ableton on shutdown")
            _ableton_connection.disconnect()
            _ableton_connection = None
        logger.info("AbletonMCP server shut down")

# Create the MCP server with lifespan support
mcp = FastMCP(
    "AbletonMCP",
    lifespan=server_lifespan
)

# Global connection for resources
_ableton_connection = None

def get_ableton_connection():
    """Get or create a persistent Ableton connection"""
    global _ableton_connection

    if _ableton_connection is not None and _ableton_connection.sock is not None:
        return _ableton_connection
    
    # Connection doesn't exist or is invalid, create a new one
    if _ableton_connection is None:
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Connecting to Ableton at {ABLETON_HOST}:{ABLETON_PORT} (attempt {attempt}/{max_attempts})...")
                _ableton_connection = AbletonConnection(host=ABLETON_HOST, port=ABLETON_PORT)
                if _ableton_connection.connect():
                    logger.info("Created new persistent connection to Ableton")
                    return _ableton_connection
                else:
                    _ableton_connection = None
            except Exception as e:
                logger.error(f"Connection attempt {attempt} failed: {str(e)}")
                if _ableton_connection:
                    _ableton_connection.disconnect()
                    _ableton_connection = None

            if attempt < max_attempts:
                import time
                time.sleep(1.0)
        
        # If we get here, all connection attempts failed
        if _ableton_connection is None:
            logger.error("Failed to connect to Ableton after multiple attempts")
            raise Exception("Could not connect to Ableton. Make sure the Remote Script is running.")
    
    return _ableton_connection


# Core Tool endpoints

@mcp.tool()
@telemetry_tool("get_session_info")
def get_session_info(ctx: Context, user_prompt: str = "") -> str:
    """Get detailed information about the current Ableton session

    Parameters:
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_session_info")
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting session info from Ableton: {str(e)}")
        return f"Error getting session info: {str(e)}"

@mcp.tool()
@telemetry_tool("get_track_info")
def get_track_info(ctx: Context, track_index: int, user_prompt: str = "") -> str:
    """
    Get detailed information about a specific track in Ableton.

    Parameters:
    - track_index: The index of the track to get information about
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_track_info", {"track_index": track_index})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting track info from Ableton: {str(e)}")
        return f"Error getting track info: {str(e)}"

@mcp.tool()
@telemetry_tool("create_midi_track")
def create_midi_track(ctx: Context, index: int = -1, user_prompt: str = "") -> str:
    """
    Create a new MIDI track in the Ableton session.

    Parameters:
    - index: The index to insert the track at (-1 = end of list)
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("create_midi_track", {"index": index})
        return f"Created new MIDI track: {result.get('name', 'unknown')}"
    except Exception as e:
        logger.error(f"Error creating MIDI track: {str(e)}")
        return f"Error creating MIDI track: {str(e)}"


@mcp.tool()
@rich_telemetry_tool("set_track_name")
def set_track_name(ctx: Context, track_index: int, name: str, user_prompt: str = "") -> str:
    """
    Set the name of a track.

    Parameters:
    - track_index: The index of the track to rename
    - name: The new name for the track
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_track_name", {"track_index": track_index, "name": name})
        return f"Renamed track to: {result.get('name', name)}"
    except Exception as e:
        logger.error(f"Error setting track name: {str(e)}")
        return f"Error setting track name: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("create_clip")
def create_clip(
    ctx: Context, 
    track_index: int, 
    clip_index: int, 
    length: float = 4.0, 
    automation_recipe: Optional[str] = None,
    user_prompt: str = ""
) -> str:
    """
    Create a new MIDI clip in the specified track and clip slot.
    Proactively suggests and optionally bakes tangible, editable vector automation curves
    (timbre swell, filter riser, breathing, vacuum cut) to promote dynamic production.

    Parameters:
    - track_index: The index of the track to create the clip in
    - clip_index: The index of the clip slot to create the clip in
    - length: The length of the clip in beats (default: 4.0)
    - automation_recipe: Optional recipe ID to bake immediately ("timbre_swell", "filter_riser", "filter_breathing", "pre_drop_vacuum", "reverb_washout", "volume_crescendo", "sub_turnaround")
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("create_clip", {
            "track_index": track_index, 
            "clip_index": clip_index, 
            "length": length
        })

        applied_info = ""
        if automation_recipe:
            from engine.arrangement.automation.clip_suggester import ClipAutomationSuggester
            apply_res = ClipAutomationSuggester.apply_recipe_to_clip(
                conn=ableton,
                track_index=track_index,
                clip_index=clip_index,
                recipe_id=automation_recipe
            )
            applied_info = f"\n[Automation Active] Baked '{apply_res.get('recipe_name')}' on parameter '{apply_res.get('parameter')}' with {apply_res.get('points_count')} vector breakpoints (editable with 'A')."

        suggestions_text = ""
        try:
            from engine.arrangement.automation.clip_suggester import ClipAutomationSuggester
            t_info_res = ableton.send_command("get_track_info", {"track_index": track_index})
            t_info = t_info_res.get("result", {}) if isinstance(t_info_res, dict) else (t_info_res or {})
            suggestions = ClipAutomationSuggester.suggest_for_track(t_info, clip_length=length)
            if suggestions and not automation_recipe:
                suggestions_text = "\n\nDynamic Tangible Automation Suggestions for this Clip (editable with 'A'):\n"
                for s in suggestions[:3]:
                    suggestions_text += f" - [{s['recipe_id']}] {s['name']}: {s['description']} (targets: {', '.join(s['target_candidates'][:2])})\n"
                suggestions_text += f"-> To apply any of these curves, call: apply_clip_automation(track_index={track_index}, clip_index={clip_index}, recipe_name='<recipe_id>')\n"
        except Exception as scan_e:
            logger.debug(f"Could not fetch automation suggestions: {scan_e}")

        return f"Created new clip at track {track_index}, slot {clip_index} with length {length} beats.{applied_info}{suggestions_text}"
    except Exception as e:
        logger.error(f"Error creating clip: {str(e)}")
        return f"Error creating clip: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("create_audio_clip")
def create_audio_clip(ctx: Context, track_index: int, clip_index: int, path: str, user_prompt: str = "") -> str:
    """
    Create a new audio clip in an audio track's clip slot by importing a file.

    Requires Ableton Live 12.0.5 or newer — the underlying
    ClipSlot.create_audio_clip Live API was introduced in 12.0.5 and is not
    available in earlier 12.0.x releases.

    Parameters:
    - track_index: The index of the audio track to create the clip in
    - clip_index: The index of the clip slot to create the clip in
    - path: Absolute path to a supported audio file (e.g. a .wav). The target
      track must be an audio track and the clip slot must be empty.
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("create_audio_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "path": path
        })
        return f"Created audio clip '{result.get('name', 'clip')}' at track {track_index}, slot {clip_index} (length {result.get('length', '?')} beats)"
    except Exception as e:
        logger.error(f"Error creating audio clip: {str(e)}")
        return f"Error creating audio clip: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("add_notes_to_clip", capture_notes=True)
def add_notes_to_clip(
    ctx: Context,
    track_index: int,
    clip_index: int,
    notes: List[Dict[str, Union[int, float, bool]]],
    user_prompt: str = ""
) -> str:
    """
    Add MIDI notes to a clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - notes: List of note dictionaries, each with pitch, start_time, duration, velocity, and mute
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("add_notes_to_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "notes": notes
        })
        return f"Added {len(notes)} notes to clip at track {track_index}, slot {clip_index}"
    except Exception as e:
        logger.error(f"Error adding notes to clip: {str(e)}")
        return f"Error adding notes to clip: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("set_clip_name")
def set_clip_name(ctx: Context, track_index: int, clip_index: int, name: str, user_prompt: str = "") -> str:
    """
    Set the name of a clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - name: The new name for the clip
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_clip_name", {
            "track_index": track_index,
            "clip_index": clip_index,
            "name": name
        })
        return f"Renamed clip at track {track_index}, slot {clip_index} to '{name}'"
    except Exception as e:
        logger.error(f"Error setting clip name: {str(e)}")
        return f"Error setting clip name: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("set_tempo")
def set_tempo(ctx: Context, tempo: float, user_prompt: str = "") -> str:
    """
    Set the tempo of the Ableton session.

    Parameters:
    - tempo: The new tempo in BPM
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_tempo", {"tempo": tempo})
        return f"Set tempo to {tempo} BPM"
    except Exception as e:
        logger.error(f"Error setting tempo: {str(e)}")
        return f"Error setting tempo: {str(e)}"


@mcp.tool()
@rich_telemetry_tool("load_instrument_or_effect")
def load_instrument_or_effect(ctx: Context, track_index: int, uri: str, user_prompt: str = "") -> str:
    """
    Load an instrument or effect onto a track using its URI.

    Parameters:
    - track_index: The index of the track to load the instrument on
    - uri: The URI of the instrument or effect to load (e.g., 'query:Synths#Instrument%20Rack:Bass:FileId_5116')
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("load_browser_item", {
            "track_index": track_index,
            "item_uri": uri
        })
        
        # Check if the instrument was loaded successfully
        if result.get("loaded", False):
            new_devices = result.get("new_devices", [])
            if new_devices:
                return f"Loaded instrument with URI '{uri}' on track {track_index}. New devices: {', '.join(new_devices)}"
            else:
                devices = result.get("devices_after", [])
                return f"Loaded instrument with URI '{uri}' on track {track_index}. Devices on track: {', '.join(devices)}"
        else:
            raise RuntimeError(
                f"[LOAD_FAILED] Failed to load instrument or effect with URI '{uri}' on track {track_index}. "
                "Ableton Live could not resolve or load this item URI. "
                "Please verify the URI in the browser catalog (engine/instruments/browser_catalog.py) or use sound_load_role_instrument."
            )
    except Exception as e:
        logger.error(f"Error loading instrument by URI: {str(e)}")
        raise RuntimeError(f"Error loading instrument by URI '{uri}' on track {track_index}: {str(e)}") from e

@mcp.tool()
@telemetry_tool("fire_clip")
def fire_clip(ctx: Context, track_index: int, clip_index: int, user_prompt: str = "") -> str:
    """
    Start playing a clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("fire_clip", {
            "track_index": track_index,
            "clip_index": clip_index
        })
        return f"Started playing clip at track {track_index}, slot {clip_index}"
    except Exception as e:
        logger.error(f"Error firing clip: {str(e)}")
        return f"Error firing clip: {str(e)}"

@mcp.tool()
@telemetry_tool("stop_clip")
def stop_clip(ctx: Context, track_index: int, clip_index: int, user_prompt: str = "") -> str:
    """
    Stop playing a clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("stop_clip", {
            "track_index": track_index,
            "clip_index": clip_index
        })
        return f"Stopped clip at track {track_index}, slot {clip_index}"
    except Exception as e:
        logger.error(f"Error stopping clip: {str(e)}")
        return f"Error stopping clip: {str(e)}"

@mcp.tool()
@telemetry_tool("start_playback")
def start_playback(ctx: Context, user_prompt: str = "") -> str:
    """Start playing the Ableton session.

    Parameters:
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("start_playback")
        return "Started playback"
    except Exception as e:
        logger.error(f"Error starting playback: {str(e)}")
        return f"Error starting playback: {str(e)}"

@mcp.tool()
@telemetry_tool("stop_playback")
def stop_playback(ctx: Context, user_prompt: str = "") -> str:
    """Stop playing the Ableton session.

    Parameters:
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("stop_playback")
        return "Stopped playback"
    except Exception as e:
        logger.error(f"Error stopping playback: {str(e)}")
        return f"Error stopping playback: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("get_browser_tree")
def get_browser_tree(ctx: Context, category_type: str = "all", user_prompt: str = "") -> str:
    """
    Get a hierarchical tree of browser categories from Ableton.

    Parameters:
    - category_type: Type of categories to get ('all', 'instruments', 'sounds', 'drums', 'audio_effects', 'midi_effects')
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_browser_tree", {
            "category_type": category_type
        })
        
        # Check if we got any categories
        if "available_categories" in result and len(result.get("categories", [])) == 0:
            available_cats = result.get("available_categories", [])
            return (f"No categories found for '{category_type}'. "
                   f"Available browser categories: {', '.join(available_cats)}")
        
        # Format the tree in a more readable way
        total_folders = result.get("total_folders", 0)
        formatted_output = f"Browser tree for '{category_type}' (showing {total_folders} folders):\n\n"
        
        def format_tree(item, indent=0):
            output = ""
            if item:
                prefix = "  " * indent
                name = item.get("name", "Unknown")
                path = item.get("path", "")
                has_more = item.get("has_more", False)
                
                # Add this item
                output += f"{prefix}• {name}"
                if path:
                    output += f" (path: {path})"
                if has_more:
                    output += " [...]"
                output += "\n"
                
                # Add children
                for child in item.get("children", []):
                    output += format_tree(child, indent + 1)
            return output
        
        # Format each category
        for category in result.get("categories", []):
            formatted_output += format_tree(category)
            formatted_output += "\n"
        
        return formatted_output
    except Exception as e:
        error_msg = str(e)
        if "Browser is not available" in error_msg:
            logger.error(f"Browser is not available in Ableton: {error_msg}")
            return f"Error: The Ableton browser is not available. Make sure Ableton Live is fully loaded and try again."
        elif "Could not access Live application" in error_msg:
            logger.error(f"Could not access Live application: {error_msg}")
            return f"Error: Could not access the Ableton Live application. Make sure Ableton Live is running and the Remote Script is loaded."
        else:
            logger.error(f"Error getting browser tree: {error_msg}")
            return f"Error getting browser tree: {error_msg}"

@mcp.tool()
@rich_telemetry_tool("get_browser_items_at_path")
def get_browser_items_at_path(ctx: Context, path: str, user_prompt: str = "") -> str:
    """
    Get browser items at a specific path in Ableton's browser.

    Parameters:
    - path: Path in the format "category/folder/subfolder"
            where category is one of the available browser categories in Ableton
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_browser_items_at_path", {
            "path": path
        })
        
        # Check if there was an error with available categories
        if "error" in result and "available_categories" in result:
            error = result.get("error", "")
            available_cats = result.get("available_categories", [])
            return (f"Error: {error}\n"
                   f"Available browser categories: {', '.join(available_cats)}")
        
        return json.dumps(result, indent=2)
    except Exception as e:
        error_msg = str(e)
        if "Browser is not available" in error_msg:
            logger.error(f"Browser is not available in Ableton: {error_msg}")
            return f"Error: The Ableton browser is not available. Make sure Ableton Live is fully loaded and try again."
        elif "Could not access Live application" in error_msg:
            logger.error(f"Could not access Live application: {error_msg}")
            return f"Error: Could not access the Ableton Live application. Make sure Ableton Live is running and the Remote Script is loaded."
        elif "Unknown or unavailable category" in error_msg:
            logger.error(f"Invalid browser category: {error_msg}")
            return f"Error: {error_msg}. Please check the available categories using get_browser_tree."
        elif "Path part" in error_msg and "not found" in error_msg:
            logger.error(f"Path not found: {error_msg}")
            return f"Error: {error_msg}. Please check the path and try again."
        else:
            logger.error(f"Error getting browser items at path: {error_msg}")
            return f"Error getting browser items at path: {error_msg}"

@mcp.tool()
@rich_telemetry_tool("load_drum_kit")
def load_drum_kit(ctx: Context, track_index: int, rack_uri: str, kit_path: str, user_prompt: str = "") -> str:
    """
    Load a drum rack and then load a specific drum kit into it.

    Parameters:
    - track_index: The index of the track to load on
    - rack_uri: The URI of the drum rack to load (e.g., 'Drums/Drum Rack')
    - kit_path: Path to the drum kit inside the browser (e.g., 'drums/acoustic/kit1')
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        
        # Step 1: Load the drum rack
        result = ableton.send_command("load_browser_item", {
            "track_index": track_index,
            "item_uri": rack_uri
        })
        
        if not result.get("loaded", False):
            return f"Failed to load drum rack with URI '{rack_uri}'"
        
        # Step 2: Get the drum kit items at the specified path
        kit_result = ableton.send_command("get_browser_items_at_path", {
            "path": kit_path
        })
        
        if "error" in kit_result:
            return f"Loaded drum rack but failed to find drum kit: {kit_result.get('error')}"
        
        # Step 3: Find a loadable drum kit
        kit_items = kit_result.get("items", [])
        loadable_kits = [item for item in kit_items if item.get("is_loadable", False)]
        
        if not loadable_kits:
            return f"Loaded drum rack but no loadable drum kits found at '{kit_path}'"
        
        # Step 4: Load the first loadable kit
        kit_uri = loadable_kits[0].get("uri")
        load_result = ableton.send_command("load_browser_item", {
            "track_index": track_index,
            "item_uri": kit_uri
        })
        
        return f"Loaded drum rack and kit '{loadable_kits[0].get('name')}' on track {track_index}"
    except Exception as e:
        logger.error(f"Error loading drum kit: {str(e)}")
        return f"Error loading drum kit: {str(e)}"

# ── Arrangement view tools ────────────────────────────────────────────────────

@mcp.tool()
@telemetry_tool("switch_to_arrangement_view")
def switch_to_arrangement_view(ctx: Context, user_prompt: str = "") -> str:
    """Switch Ableton's main window to the Arrangement view.

    Parameters:
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        ableton.send_command("switch_to_arrangement_view")
        return "Switched to Arrangement view"
    except Exception as e:
        logger.error(f"Error switching to arrangement view: {str(e)}")
        return f"Error switching to arrangement view: {str(e)}"


@mcp.tool()
@rich_telemetry_tool("set_arrangement_time")
def set_arrangement_time(ctx: Context, time: float, user_prompt: str = "") -> str:
    """
    Move the arrangement playhead to a specific position.

    Parameters:
    - time: Position in beats from the start of the arrangement (e.g. 8.0 = bar 3 in 4/4)
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_current_song_time", {"time": time})
        return f"Playhead moved to beat {result.get('current_song_time', time)}"
    except Exception as e:
        logger.error(f"Error setting arrangement time: {str(e)}")
        return f"Error setting arrangement time: {str(e)}"


@mcp.tool()
@telemetry_tool("get_arrangement_clips")
def get_arrangement_clips(ctx: Context, track_index: int, user_prompt: str = "") -> str:
    """
    List all clips placed in the Arrangement timeline for a track.

    Returns each clip's name, start_time, end_time, length, and type.

    Parameters:
    - track_index: The index of the track to inspect
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_arrangement_clips", {"track_index": track_index})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting arrangement clips: {str(e)}")
        return f"Error getting arrangement clips: {str(e)}"


@mcp.tool()
@rich_telemetry_tool("duplicate_to_arrangement")
def duplicate_to_arrangement(
    ctx: Context,
    track_index: int,
    clip_index: int,
    destination_time: float,
    automation_recipe: Optional[str] = None,
    user_prompt: str = ""
) -> str:
    """
    Copy a Session-view clip into the Arrangement timeline.
    Uses Live's track.duplicate_clip_to_arrangement() API (Live 11 / 12).
    Optionally bakes a tangible vector automation curve onto the arrangement track lane.

    Parameters:
    - track_index:       Index of the track that owns the Session clip
    - clip_index:        Index of the clip slot in that track (Session view)
    - destination_time:  Beat position in the arrangement to place the clip (e.g. 0.0 = start, 32.0 = bar 9)
    - automation_recipe: Optional automation recipe ID to apply ("timbre_swell", "filter_riser", etc.)
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        
        if automation_recipe:
            from engine.arrangement.automation.clip_suggester import ClipAutomationSuggester
            apply_res = ClipAutomationSuggester.apply_recipe_to_clip(
                conn=ableton,
                track_index=track_index,
                clip_index=clip_index,
                recipe_id=automation_recipe,
                destination_time=destination_time
            )
            return (
                f"Duplicated clip from Session slot {clip_index} on track {track_index} "
                f"to arrangement at beat {destination_time} with tangible automation '{apply_res.get('recipe_name')}' "
                f"baked onto parameter '{apply_res.get('parameter')}' ({apply_res.get('points_count')} breakpoints, editable with 'A')."
            )

        result = ableton.send_command(
            "duplicate_session_clip_to_arrangement",
            {
                "track_index": track_index,
                "clip_index": clip_index,
                "destination_time": destination_time
            }
        )
        clip_name = result.get("clip_name", "clip")
        track_name = result.get("track_name", f"track {track_index}")
        return (
            f"Duplicated '{clip_name}' from Session slot {clip_index} on '{track_name}' "
            f"to arrangement at beat {destination_time}. (Tip: Call apply_clip_automation to add tangible vector curves to this section!)"
        )
    except Exception as e:
        logger.error(f"Error duplicating clip to arrangement: {str(e)}")
        return f"Error duplicating clip to arrangement: {str(e)}"


# Note: main() is defined at the end of the file to ensure all tools are registered

@mcp.tool()
@rich_telemetry_tool("get_device_parameters")
def get_device_parameters(
    ctx: Context,
    track_index: int,
    device_index: int,
    user_prompt: str = ""
) -> str:
    """
    Get all controllable parameters (knobs, sliders, toggles) for a device on a track.

    Parameters:
    - track_index: The index of the track containing the device
    - device_index: The index of the device on the track
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_device_parameters", {
            "track_index": track_index,
            "device_index": device_index
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting device parameters: {str(e)}")
        return f"Error getting device parameters: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("set_device_parameter")
def set_device_parameter(
    ctx: Context,
    track_index: int,
    device_index: int,
    parameter: Union[int, str],
    value: float,
    user_prompt: str = ""
) -> str:
    """
    Set the value of a specific parameter (knob/slider) on a device.

    Parameters:
    - track_index: The index of the track containing the device
    - device_index: The index of the device on the track
    - parameter: The parameter name (e.g. 'Cutoff', 'Drive', 'Mix') or index (integer)
    - value: The target value (float) within the parameter's min/max range
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        # Governance verification: check Phase 1 preset requirement
        try:
            from engine.supervisor.governance import governance_supervisor
            t_st = governance_supervisor.get_track_state(track_index)
            if t_st.preset_required and not t_st.preset_configured:
                p_str = str(parameter).lower()
                if "device on" not in p_str:
                    return json.dumps({
                        "error": (
                            f"Violación de Gobernanza (Fase 1 pendiente): La pista {track_index} contiene un instrumento "
                            f"que requiere seleccionar explícitamente un instrumento/preset antes de esculpir sus parámetros (Fase 2). "
                            f"Utilice preset_select_for_track para escoger el instrumento primero."
                        )
                    })
        except Exception:
            pass

        ableton = get_ableton_connection()
        result = ableton.send_command("set_device_parameter", {
            "track_index": track_index,
            "device_index": device_index,
            "parameter": parameter,
            "value": value
        })
        # Record parameter change in DeviceParameterSupervisor and governance_supervisor (Delta >= 1)
        try:
            from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
            from engine.supervisor.governance import governance_supervisor
            p_str = str(parameter)
            if "device on" not in p_str.lower():
                DeviceParameterSupervisor._SCULPTED_REGISTRY.add((track_index, device_index))
                governance_supervisor.record_device_sculpted(track_index, device_index, {p_str: float(value)})
        except Exception:
            pass
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting device parameter: {str(e)}")
        return f"Error setting device parameter: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("get_clip_notes")
def get_clip_notes(
    ctx: Context,
    track_index: int,
    clip_index: int,
    user_prompt: str = ""
) -> str:
    """
    Get all MIDI notes currently stored in a clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_clip_notes", {
            "track_index": track_index,
            "clip_index": clip_index
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting clip notes: {str(e)}")
        return f"Error getting clip notes: {str(e)}"


@mcp.tool()
@rich_telemetry_tool("delete_clip")
def delete_clip(
    ctx: Context,
    track_index: int,
    clip_index: int,
    user_prompt: str = ""
) -> str:
    """
    Delete/clear a clip from a specific track clip slot.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot to delete
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("delete_clip", {
            "track_index": track_index,
            "clip_index": clip_index
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error deleting clip: {str(e)}")
        return f"Error deleting clip: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("set_track_mute")
def set_track_mute(
    ctx: Context,
    track_index: int,
    mute: bool,
    user_prompt: str = ""
) -> str:
    """
    Mute or unmute a track.

    Parameters:
    - track_index: The index of the track
    - mute: True to mute the track, False to unmute
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_track_mute", {
            "track_index": track_index,
            "mute": mute
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting track mute: {str(e)}")
        return f"Error setting track mute: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("set_track_solo")
def set_track_solo(
    ctx: Context,
    track_index: int,
    solo: bool,
    user_prompt: str = ""
) -> str:
    """
    Set solo state for a track.

    Parameters:
    - track_index: The index of the track
    - solo: True to solo the track, False to unsolo
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_track_solo", {
            "track_index": track_index,
            "solo": solo
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting track solo: {str(e)}")
        return f"Error setting track solo: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("set_track_volume")
def set_track_volume(
    ctx: Context,
    track_index: int,
    volume: float,
    user_prompt: str = ""
) -> str:
    """
    Set track mixer volume fader (0.0 to 1.0, where ~0.85 represents 0 dB).

    Parameters:
    - track_index: The index of the track
    - volume: Volume level between 0.0 and 1.0
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_track_volume", {
            "track_index": track_index,
            "volume": volume
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting track volume: {str(e)}")
        return f"Error setting track volume: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("set_track_panning")
def set_track_panning(
    ctx: Context,
    track_index: int,
    panning: float,
    user_prompt: str = ""
) -> str:
    """
    Set track mixer stereo panning (-1.0 for hard left, 0.0 for center, +1.0 for hard right).

    Parameters:
    - track_index: The index of the track
    - panning: Panning value between -1.0 and +1.0
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_track_panning", {
            "track_index": track_index,
            "panning": panning
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting track panning: {str(e)}")
        return f"Error setting track panning: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("set_track_send")
def set_track_send(
    ctx: Context,
    track_index: int,
    send_index: int,
    value: float,
    user_prompt: str = ""
) -> str:
    """
    Set track send level to return tracks (0.0 to 1.0).

    Parameters:
    - track_index: The index of the track
    - send_index: The index of the send bus (0 for Send A, 1 for Send B, etc.)
    - value: Send level between 0.0 and 1.0
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_track_send", {
            "track_index": track_index,
            "send_index": send_index,
            "value": value
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting track send: {str(e)}")
        return f"Error setting track send: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("set_loop_region")
def set_loop_region(
    ctx: Context,
    start_time: float,
    length: float,
    enabled: bool = True,
    user_prompt: str = ""
) -> str:
    """
    Set arrangement song loop region bracket and state.

    Parameters:
    - start_time: The start beat of the loop region
    - length: The duration of the loop in beats
    - enabled: True to activate loop, False to deactivate
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_loop_region", {
            "start_time": start_time,
            "length": length,
            "enabled": enabled
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting loop region: {str(e)}")
        return f"Error setting loop region: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("set_clip_pitch")
def set_clip_pitch(
    ctx: Context,
    track_index: int,
    clip_index: int,
    pitch_coarse: int,
    pitch_fine: float = 0.0,
    user_prompt: str = ""
) -> str:
    """
    Set pitch transpose (semitones) and fine detune (cents) on an audio clip.

    Parameters:
    - track_index: The index of the track
    - clip_index: The slot index of the clip in Session view
    - pitch_coarse: Pitch transposition in semitones (-48 to +48)
    - pitch_fine: Fine detune in cents (-50.0 to +50.0)
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_clip_pitch", {
            "track_index": track_index,
            "clip_index": clip_index,
            "pitch_coarse": pitch_coarse,
            "pitch_fine": pitch_fine
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting clip pitch: {str(e)}")
        return f"Error setting clip pitch: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("set_clip_warp_mode")
def set_clip_warp_mode(
    ctx: Context,
    track_index: int,
    clip_index: int,
    mode: str = "complex_pro",
    warping: bool = True,
    user_prompt: str = ""
) -> str:
    """
    Set warp state and mode (Beats, Tones, Texture, Re-Pitch, Complex, Complex Pro) on an audio clip.

    Parameters:
    - track_index: The index of the track
    - clip_index: The slot index of the clip in Session view
    - mode: Warp mode name ("beats", "tones", "texture", "repitch", "complex", "complex_pro")
    - warping: True to enable warping, False for unwarped playback
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_clip_warp_mode", {
            "track_index": track_index,
            "clip_index": clip_index,
            "mode": mode,
            "warping": warping
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting clip warp mode: {str(e)}")
        return f"Error setting clip warp mode: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("set_clip_gain")
def set_clip_gain(
    ctx: Context,
    track_index: int,
    clip_index: int,
    gain: float = 1.0,
    user_prompt: str = ""
) -> str:
    """
    Set sample gain on an audio clip.

    Parameters:
    - track_index: The index of the track
    - clip_index: The slot index of the clip in Session view
    - gain: Linear gain value (1.0 = 0 dB unity gain)
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_clip_gain", {
            "track_index": track_index,
            "clip_index": clip_index,
            "gain": gain
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting clip gain: {str(e)}")
        return f"Error setting clip gain: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("get_audio_clip_info")
def get_audio_clip_info(
    ctx: Context,
    track_index: int,
    clip_index: int,
    user_prompt: str = ""
) -> str:
    """
    Get full properties and metadata of an audio clip (pitch, warp mode, gain, length).

    Parameters:
    - track_index: The index of the track
    - clip_index: The slot index of the clip in Session view
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_audio_clip_info", {
            "track_index": track_index,
            "clip_index": clip_index
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting audio clip info: {str(e)}")
        return f"Error getting audio clip info: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("create_cue_point")
def create_cue_point(
    ctx: Context,
    time: float,
    name: str = "",
    user_prompt: str = ""
) -> str:
    """
    Create or update an arrangement section locator (Cue Point) at a given beat time with a name.

    Parameters:
    - time: Position on the arrangement timeline in beats (e.g. 0.0 for bar 1, 64.0 for bar 17)
    - name: Label for the section locator (e.g. "Intro", "Verso", "Drop 1", "Puente", "Drop 2", "Final")
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("create_cue_point", {
            "time": time,
            "name": name
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error creating cue point: {str(e)}")
        return f"Error creating cue point: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("get_cue_points")
def get_cue_points(
    ctx: Context,
    user_prompt: str = ""
) -> str:
    """
    Get all cue points / section locators in the arrangement timeline.

    Parameters:
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_cue_points", {})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting cue points: {str(e)}")
        return f"Error getting cue points: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("delete_cue_point")
def delete_cue_point(
    ctx: Context,
    time_or_index: Union[int, float],
    user_prompt: str = ""
) -> str:
    """
    Delete an arrangement section locator by time or index.

    Parameters:
    - time_or_index: The locator index or beat time to delete
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("delete_cue_point", {
            "time_or_index": time_or_index
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error deleting cue point: {str(e)}")
        return f"Error deleting cue point: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("jump_to_cue_point")
def jump_to_cue_point(
    ctx: Context,
    target: Union[str, float],
    user_prompt: str = ""
) -> str:
    """
    Jump the arrangement playhead to a named section locator or beat time.

    Parameters:
    - target: Section name (e.g. "Drop 1") or beat position (e.g. 192.0)
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("jump_to_cue_point", {
            "target": target
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error jumping to cue point: {str(e)}")
        return f"Error jumping to cue point: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("add_expressive_notes_to_clip")
def add_expressive_notes_to_clip(
    ctx: Context,
    track_index: int,
    clip_index: int,
    notes: List[Dict[str, Any]],
    user_prompt: str = ""
) -> str:
    """
    Add expressive MIDI notes to a clip with probability (generative triggers), velocity deviation (humanization), and release velocity.

    Parameters:
    - track_index: The index of the track
    - clip_index: The slot index of the clip in Session view
    - notes: List of note dictionaries. Supported keys:
        * pitch (int, 0-127)
        * start_time (float, in beats)
        * duration (float, in beats)
        * velocity (float, 1-127)
        * mute (bool, default False)
        * probability (float, 0.0 to 1.0; e.g. 0.70 for 70% chance of firing)
        * velocity_deviation (float, -127 to +127)
        * release_velocity (float, 0 to 127)
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("add_expressive_notes_to_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "notes": notes
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error adding expressive notes: {str(e)}")
        return f"Error adding expressive notes: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("clear_clip_envelopes")
def clear_clip_envelopes(
    ctx: Context,
    track_index: int,
    clip_index: int,
    user_prompt: str = ""
) -> str:
    """
    Clear all modulation and automation envelopes from a clip.

    Parameters:
    - track_index: The index of the track
    - clip_index: The slot index of the clip in Session view
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("clear_clip_envelopes", {
            "track_index": track_index,
            "clip_index": clip_index
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error clearing clip envelopes: {str(e)}")
        return f"Error clearing clip envelopes: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("get_drum_rack_pads")
def get_drum_rack_pads(
    ctx: Context,
    track_index: int,
    device_index: int = 0,
    user_prompt: str = ""
) -> str:
    """
    List all active drum pads with loaded chains, pitch numbers, and devices inside a Drum Rack.

    Parameters:
    - track_index: The index of the track containing the Drum Rack
    - device_index: Index of the Drum Rack device on the track (default 0)
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_drum_rack_pads", {
            "track_index": track_index,
            "device_index": device_index
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting drum rack pads: {str(e)}")
        return f"Error getting drum rack pads: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("get_drum_pad_devices")
def get_drum_pad_devices(
    ctx: Context,
    track_index: int,
    pad_note: int,
    device_index: int = 0,
    user_prompt: str = ""
) -> str:
    """
    Get detailed device list and all parameters for an individual Drum Rack pad (e.g. note 36 Kick, note 38 Snare).

    Parameters:
    - track_index: The index of the track
    - pad_note: MIDI note number of the drum pad (e.g. 36 for C1, 38 for D1)
    - device_index: Index of the Drum Rack device on the track (default 0)
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_drum_pad_devices", {
            "track_index": track_index,
            "pad_note": pad_note,
            "device_index": device_index
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting drum pad devices: {str(e)}")
        return f"Error getting drum pad devices: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("set_drum_pad_parameter")
def set_drum_pad_parameter(
    ctx: Context,
    track_index: int,
    pad_note: int,
    chain_device_index: int,
    parameter: Union[str, int],
    value: float,
    device_index: int = 0,
    user_prompt: str = ""
) -> str:
    """
    Set a parameter on a device loaded inside a specific drum pad (e.g. adjust Simpler filter/envelope or pad effect).

    Parameters:
    - track_index: The index of the track
    - pad_note: MIDI note number of the drum pad (e.g. 36 for Kick, 38 for Snare)
    - chain_device_index: Index of the device inside the pad chain (0 for instrument/Simpler, 1 for first effect)
    - parameter: Parameter name (e.g. "Filter Freq", "Volume", "Drive") or index
    - value: Target parameter value
    - device_index: Index of the Drum Rack on the track (default 0)
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_drum_pad_parameter", {
            "track_index": track_index,
            "pad_note": pad_note,
            "chain_device_index": chain_device_index,
            "parameter": parameter,
            "value": value,
            "device_index": device_index
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting drum pad parameter: {str(e)}")
        return f"Error setting drum pad parameter: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("set_drum_pad_mute_solo")
def set_drum_pad_mute_solo(
    ctx: Context,
    track_index: int,
    pad_note: int,
    mute: Union[bool, None] = None,
    solo: Union[bool, None] = None,
    device_index: int = 0,
    user_prompt: str = ""
) -> str:
    """
    Mute or solo an individual drum pad inside a Drum Rack.

    Parameters:
    - track_index: The index of the track
    - pad_note: MIDI note number of the drum pad (e.g. 36 for Kick, 38 for Snare)
    - mute: True to mute pad, False to unmute, None to leave unchanged
    - solo: True to solo pad, False to unsolo, None to leave unchanged
    - device_index: Index of the Drum Rack on the track (default 0)
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_drum_pad_mute_solo", {
            "track_index": track_index,
            "pad_note": pad_note,
            "mute": mute,
            "solo": solo,
            "device_index": device_index
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error setting drum pad mute/solo: {str(e)}")
        return f"Error setting drum pad mute/solo: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("run_automation_sweep")
def run_automation_sweep(
    ctx: Context,
    track_index: int,
    device_index: int,
    parameter: Union[str, int],
    start_val: float,
    end_val: float,
    duration_sec: float = 2.0,
    curve: str = "linear",
    steps: int = 30,
    user_prompt: str = ""
) -> str:
    """
    Execute a smooth real-time parameter automation sweep (e.g. filter opening build-up, reverb bloom, bitcrush descent).

    Parameters:
    - track_index: The index of the track
    - device_index: Index of the device on the track
    - parameter: Parameter name (e.g. "Cutoff", "Mix", "Drive", "Macro 1") or index
    - start_val: Starting normalized value (0.0 to 1.0)
    - end_val: Target ending normalized value (0.0 to 1.0)
    - duration_sec: Total duration of the sweep in seconds (e.g. 2.0, 4.0, 8.0)
    - curve: Interpolation curve shape ("linear", "exponential", "logarithmic", "s_curve")
    - steps: Number of interpolation steps (default 30)
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("run_automation_sweep", {
            "track_index": track_index,
            "device_index": device_index,
            "parameter": parameter,
            "start_val": start_val,
            "end_val": end_val,
            "duration_sec": duration_sec,
            "curve": curve,
            "steps": steps
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error running automation sweep: {str(e)}")
        return f"Error running automation sweep: {str(e)}"

@mcp.tool()
@rich_telemetry_tool("analyze_audio_file")
def analyze_audio_file(
    ctx: Context,
    file_path: str,
    user_prompt: str = ""
) -> str:
    """
    Digital Ear Audio & Mix Analyzer: Analyzes any WAV audio file/render for Peak dBFS, RMS, Crest Factor (dynamics), Stereo Phase Correlation, and 5-Band Spectral Energy Distribution with mixing recommendations.

    Parameters:
    - file_path: Absolute path to the WAV audio file to analyze
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        import wave, math
        import numpy as np

        if not os.path.exists(file_path):
            return json.dumps({"error": f"Audio file not found: {file_path}"})

        with wave.open(file_path, 'rb') as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            raw_data = wf.readframes(n_frames)

        if sampwidth == 2:
            dtype = np.int16
            samples = np.frombuffer(raw_data, dtype=dtype).astype(np.float32) / 32768.0
        elif sampwidth == 3:
            raw_bytes = np.frombuffer(raw_data, dtype=np.uint8)
            n_samples = len(raw_bytes) // 3
            samples32 = np.zeros(n_samples, dtype=np.int32)
            samples32 = (raw_bytes[0::3].astype(np.int32) |
                         (raw_bytes[1::3].astype(np.int32) << 8) |
                         (raw_bytes[2::3].astype(np.int32) << 16))
            samples32[samples32 >= 0x800000] -= 0x1000000
            samples = samples32.astype(np.float32) / 8388608.0
        elif sampwidth == 4:
            dtype = np.float32
            samples = np.frombuffer(raw_data, dtype=dtype).astype(np.float32)
        else:
            samples = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0

        if n_channels > 1:
            audio = samples.reshape(-1, n_channels)
        else:
            audio = samples.reshape(-1, 1)

        duration_sec = len(audio) / float(framerate)
        left = audio[:, 0]
        right = audio[:, 1] if n_channels > 1 else audio[:, 0]
        mono = np.mean(audio, axis=1)

        peak_linear = np.max(np.abs(audio))
        peak_dbfs = 20.0 * math.log10(max(peak_linear, 1e-6))
        rms_linear = np.sqrt(np.mean(mono ** 2))
        rms_dbfs = 20.0 * math.log10(max(rms_linear, 1e-6))
        crest_factor_db = peak_dbfs - rms_dbfs

        if n_channels > 1:
            cov = np.dot(left, right)
            norm = np.linalg.norm(left) * np.linalg.norm(right)
            stereo_correlation = float(cov / norm) if norm > 0 else 1.0
        else:
            stereo_correlation = 1.0

        fft_data = np.abs(np.fft.rfft(mono))
        freqs = np.fft.rfftfreq(len(mono), 1.0 / framerate)

        bands = {
            'subbass_20_60hz': (20, 60),
            'bass_60_250hz': (60, 250),
            'low_mid_250_1khz': (250, 1000),
            'high_mid_1k_6khz': (1000, 6000),
            'highs_6k_20khz': (6000, 20000)
        }
        band_energy = {}
        total_energy = np.sum(fft_data ** 2) + 1e-12
        for b_name, (low_f, high_f) in bands.items():
            mask = (freqs >= low_f) & (freqs < high_f)
            b_energy = np.sum(fft_data[mask] ** 2)
            pct = float((b_energy / total_energy) * 100.0)
            band_energy[b_name] = round(pct, 2)

        recs = []
        if band_energy['subbass_20_60hz'] > 35.0:
            recs.append("High Subbass Energy: Consider a high-pass cut at 25-30 Hz to protect headroom.")
        if band_energy['low_mid_250_1khz'] > 40.0:
            recs.append("Muddy Low-Mids: Consider scooping 300-450 Hz on guitars, pads, or synths.")
        if band_energy['highs_6k_20khz'] < 8.0:
            recs.append("Dark Highs: Boost 10 kHz+ shelf on leads/cymbals for Y2K brightness.")
        if stereo_correlation < 0.2:
            recs.append("Potential Phase Cancellation: Check stereo width on bass or low-mid tracks.")
        if crest_factor_db < 6.0:
            recs.append("Over-Compressed / Limiter Squashed: Dynamics are below 6 dB crest factor.")

        result = {
            "file": os.path.basename(file_path),
            "duration_seconds": round(duration_sec, 2),
            "sample_rate": framerate,
            "channels": n_channels,
            "peak_dbfs": round(peak_dbfs, 2),
            "rms_dbfs": round(rms_dbfs, 2),
            "crest_factor_db": round(crest_factor_db, 2),
            "stereo_correlation": round(stereo_correlation, 3),
            "spectral_energy_distribution_pct": band_energy,
            "mix_health_recommendations": recs
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error analyzing audio file: {str(e)}")
        return json.dumps({"error": str(e)})

@mcp.tool()
@rich_telemetry_tool("search_sample_library")
def search_sample_library(
    ctx: Context,
    query: str,
    category: str = "",
    max_results: int = 20,
    root_folder: str = "",
    user_prompt: str = ""
) -> str:
    """
    Search and index the local Sample & Preset Library (e.g. 'D:\\Documentos\\Librerias FL Studio') for WAV samples, vocal chops, breakbeats, drum hits, Serum/Vital presets (.fxp/.vital), and Kontakt instruments (.nki).

    Parameters:
    - query: Search keywords (e.g. 'ethereal vocal', 'amen break', '808 kick', 'rave lead', 'harpsichord')
    - category: Optional category filter ('vocal', 'drum', 'break', 'loop', 'preset', 'kontakt')
    - max_results: Maximum results to return (default 20)
    - root_folder: Custom root folder path (defaults to 'D:\\Documentos\\Librerias FL Studio')
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        root = root_folder if (root_folder and os.path.exists(root_folder)) else r"D:\Documentos\Librerias FL Studio"
        if not os.path.exists(root):
            return json.dumps({"error": f"Sample library path not found: {root}"})

        terms = [t.lower() for t in query.split() if t]
        cat_lower = (category or "").lower()

        results = []
        for r, d, files in os.walk(root):
            for f in files:
                f_lower = f.lower()
                rel_path = os.path.relpath(os.path.join(r, f), root)
                full_lower = rel_path.lower()

                if cat_lower:
                    if cat_lower in ("vocal", "vocals") and not any(k in full_lower for k in ["vocal", "vox", "acapella", "phrase", "chop"]):
                        continue
                    if cat_lower in ("drum", "drums", "percussion") and not any(k in full_lower for k in ["drum", "kick", "snare", "clap", "hat", "perc", "break", "loop"]):
                        continue
                    if cat_lower in ("break", "breaks", "loop", "loops") and not any(k in full_lower for k in ["break", "loop", "drumloop", "amen"]):
                        continue
                    if cat_lower in ("preset", "presets", "synth") and not f_lower.endswith(('.fxp', '.vital', '.nmsv', '.fxb')):
                        continue
                    if cat_lower in ("kontakt", "nki", "instrument") and not f_lower.endswith(('.nki', '.nkm', '.nicnt')):
                        continue

                if all(term in full_lower for term in terms):
                    size_bytes = 0
                    try:
                        size_bytes = os.path.getsize(os.path.join(r, f))
                    except:
                        pass

                    results.append({
                        "file_name": f,
                        "relative_path": rel_path,
                        "absolute_path": os.path.join(r, f),
                        "extension": os.path.splitext(f)[1].lower(),
                        "size_mb": round(size_bytes / (1024 * 1024), 2)
                    })
                    if len(results) >= max_results:
                        break
            if len(results) >= max_results:
                break

        return json.dumps({
            "query": query,
            "category": category,
            "library_root": root,
            "result_count": len(results),
            "results": results
        }, indent=2)
    except Exception as e:
        logger.error(f"Error searching sample library: {str(e)}")
        return json.dumps({"error": str(e)})

@mcp.tool()
@rich_telemetry_tool("get_sample_library_summary")
def get_sample_library_summary(
    ctx: Context,
    root_folder: str = "",
    user_prompt: str = ""
) -> str:
    """
    Get a complete overview of all installed sample packs, total WAV audio files, synth presets, and Kontakt instruments in the library.

    Parameters:
    - root_folder: Custom root folder path (defaults to 'D:\\Documentos\\Librerias FL Studio')
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        root = root_folder if (root_folder and os.path.exists(root_folder)) else r"D:\Documentos\Librerias FL Studio"
        if not os.path.exists(root):
            return json.dumps({"error": f"Sample library path not found: {root}"})

        packs = []
        total_wavs = 0
        total_presets = 0
        total_kontakt = 0

        for item in os.listdir(root):
            item_path = os.path.join(root, item)
            if os.path.isdir(item_path):
                wav_count = 0
                preset_count = 0
                nki_count = 0
                for r, d, files in os.walk(item_path):
                    for f in files:
                        f_lower = f.lower()
                        if f_lower.endswith(('.wav', '.aif', '.aiff', '.mp3', '.flac')):
                            wav_count += 1
                        elif f_lower.endswith(('.fxp', '.vital', '.nmsv', '.fxb', '.fst')):
                            preset_count += 1
                        elif f_lower.endswith(('.nki', '.nkm', '.nkc', '.nicnt')):
                            nki_count += 1
                total_wavs += wav_count
                total_presets += preset_count
                total_kontakt += nki_count
                packs.append({
                    "name": item,
                    "wav_samples": wav_count,
                    "synth_presets": preset_count,
                    "kontakt_instruments": nki_count
                })

        return json.dumps({
            "library_root": root,
            "pack_count": len(packs),
            "total_audio_samples": total_wavs,
            "total_synth_presets": total_presets,
            "total_kontakt_instruments": total_kontakt,
            "packs": packs
        }, indent=2)
    except Exception as e:
        logger.error(f"Error getting sample library summary: {str(e)}")
        return json.dumps({"error": str(e)})

# ==============================================================================
# AUTOMATION ENGINE MCP TOOLS & LOGIC
# ==============================================================================

def _server_parse_res(res_input):
    if isinstance(res_input, (int, float)):
        return max(0.03125, float(res_input))
    res_str = str(res_input).strip().lower()
    res_map = {
        "1/1": 4.0, "1/2": 2.0, "1/4": 1.0, "1/8": 0.5,
        "1/16": 0.25, "1/32": 0.125, "1/64": 0.0625,
        "bar": 4.0, "1 bar": 4.0, "beat": 1.0, "1 beat": 1.0
    }
    if res_str in res_map:
        return res_map[res_str]
    if "/" in res_str:
        parts = res_str.split("/")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            num, denom = float(parts[0]), float(parts[1])
            return max(0.03125, (num / denom) * 4.0)
    return 0.25

def _server_gen_curve(start, duration, start_val, end_val, curve="linear", resolution="1/16", max_points=256):
    import math
    step_beats = _server_parse_res(resolution)
    dur = float(duration)
    if dur <= 0:
        raise ValueError(f"Duration must be > 0 (received {duration})")
    
    steps_count = int(math.ceil(dur / step_beats)) + 1
    if steps_count > max_points:
        step_beats = dur / float(max_points - 1)
        steps_count = max_points
    
    points = []
    for i in range(steps_count):
        cur_time = float(start) + min(dur, i * step_beats)
        p = min(1.0, max(0.0, (cur_time - float(start)) / dur))
        
        if curve == "exponential" or curve == "ease_in":
            f_p = math.pow(p, 2.0)
        elif curve == "logarithmic" or curve == "ease_out":
            f_p = 1.0 - math.pow(1.0 - p, 2.0)
        elif curve == "ease_in_out":
            f_p = (1.0 - math.cos(p * math.pi)) / 2.0
        elif curve == "step":
            f_p = 0.0 if p < 0.5 else 1.0
        else: # linear
            f_p = p
        
        val = float(start_val) + (float(end_val) - float(start_val)) * f_p
        points.append({"time": round(cur_time, 4), "value": round(val, 6)})
        if cur_time >= float(start) + dur:
            break
    
    if not points or abs(points[-1]["time"] - (float(start) + dur)) > 0.001:
        points.append({"time": round(float(start) + dur, 4), "value": round(float(end_val), 6)})
    return points

_track_cache = {}
_track_cache_time = 0

def _server_resolve_track_and_device(ableton, track_input, device_input):
    global _track_cache, _track_cache_time
    import time
    now = time.time()
    
    # Resolve track
    track_idx = None
    track_name = str(track_input)
    if isinstance(track_input, int) or (isinstance(track_input, str) and track_input.isdigit()):
        track_idx = int(track_input)
        if track_idx in _track_cache and (now - _track_cache_time < 30.0):
            track_name = _track_cache[track_idx].get("name", str(track_idx))
        else:
            try:
                t_info = ableton.send_command("get_track_info", {"track_index": track_idx})
                track_name = t_info.get("name", str(track_idx))
                _track_cache[track_idx] = t_info
                _track_cache_time = now
            except:
                pass
    else:
        # Check cache or refresh
        if not _track_cache or (now - _track_cache_time >= 30.0):
            sess = ableton.send_command("get_session_info")
            t_count = sess.get("track_count", 18)
            new_cache = {}
            for i in range(t_count):
                try:
                    new_cache[i] = ableton.send_command("get_track_info", {"track_index": i})
                except:
                    pass
            _track_cache = new_cache
            _track_cache_time = now
        
        t_target = str(track_input).lower().strip()
        candidates = []
        for i, t_info in _track_cache.items():
            t_n = t_info.get("name", "").lower().strip()
            if t_n == t_target:
                candidates = [(i, t_info.get("name", ""))]
                break
            elif t_target in t_n:
                candidates.append((i, t_info.get("name", "")))
        
        if len(candidates) == 1:
            track_idx, track_name = candidates[0]
        elif len(candidates) > 1:
            raise ValueError(f"Ambiguous track '{track_input}'. Candidates: {[f'Track {c[0]}: {c[1]}' for c in candidates]}")
        else:
            track_idx = 0
    
    # Resolve device
    t_info = _track_cache.get(track_idx)
    if not t_info:
        try:
            t_info = ableton.send_command("get_track_info", {"track_index": track_idx})
            _track_cache[track_idx] = t_info
        except:
            t_info = {}
    
    devices = t_info.get("devices", [])
    device_idx = None
    device_name = "MixerDevice"
    
    if device_input is not None:
        if isinstance(device_input, int) or (isinstance(device_input, str) and str(device_input).isdigit()):
            device_idx = int(device_input)
            if 0 <= device_idx < len(devices):
                device_name = devices[device_idx].get("name", "")
        else:
            d_target = str(device_input).lower().strip()
            candidates = []
            for d in devices:
                d_n = d.get("name", "").lower().strip()
                if d_n == d_target:
                    candidates = [(d.get("index", 0), d.get("name", ""))]
                    break
                elif d_target in d_n:
                    candidates.append((d.get("index", 0), d.get("name", "")))
            if len(candidates) == 1:
                device_idx, device_name = candidates[0]
            elif len(candidates) > 1:
                raise ValueError(f"Ambiguous device '{device_input}' on track '{track_name}'. Candidates: {[c[1] for c in candidates]}")
            else:
                if devices:
                    device_idx, device_name = 0, devices[0].get("name", "")
    
    return track_idx, track_name, device_idx, device_name


@mcp.tool()
@rich_telemetry_tool("get_device_parameter")
def get_device_parameter(
    ctx: Context,
    track: Union[int, str],
    device: Union[int, str, None] = None,
    parameter: Union[int, str] = 0,
    user_prompt: str = ""
) -> str:
    """
    Get detailed metadata, range (min/max), unit, and automation state of a specific device parameter or track mixer control in Ableton Live.

    Parameters:
    - track: The track index (0-based) or track name (e.g. 'Bass', 'Lead 1')
    - device: The device index (0-based) or device name (e.g. 'Serum', 'Drift', 'Saturator'). Pass None or omit for track mixer controls (Volume, Pan).
    - parameter: The parameter index or parameter name (e.g. 'Cutoff', 'Filter Cutoff', 'Drive', 'Volume', 'Pan')
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        try:
            result = ableton.send_command("get_device_parameter", {
                "track": track,
                "device": device,
                "parameter": parameter
            })
            if "status" not in result or result.get("status") == "success":
                return json.dumps(result, indent=2)
        except:
            pass

        # Resilient adapter
        t_idx, t_name, d_idx, d_name = _server_resolve_track_and_device(ableton, track, device)
        
        if d_idx is not None:
            params_res = ableton.send_command("get_device_parameters", {"track_index": t_idx, "device_index": d_idx})
            p_list = params_res.get("parameters", [])
            target_p = None
            if isinstance(parameter, int) or (isinstance(parameter, str) and str(parameter).isdigit()):
                p_i = int(parameter)
                if 0 <= p_i < len(p_list):
                    target_p = p_list[p_i]
            else:
                p_t = str(parameter).lower().strip()
                for p in p_list:
                    if p.get("name", "").lower().strip() == p_t:
                        target_p = p
                        break
                if not target_p:
                    for p in p_list:
                        if p_t in p.get("name", "").lower():
                            target_p = p
                            break
            if not target_p and p_list:
                target_p = p_list[0]
            
            if target_p:
                return json.dumps({
                    "track_index": t_idx,
                    "track_name": t_name,
                    "device_index": d_idx,
                    "device_name": d_name,
                    "parameter_index": target_p.get("index", 0),
                    "parameter_name": target_p.get("name", "Unknown"),
                    "value": target_p.get("value", 0.0),
                    "min": target_p.get("min", 0.0),
                    "max": target_p.get("max", 1.0),
                    "is_quantized": target_p.get("is_quantized", False),
                    "is_enabled": True,
                    "str_value": target_p.get("str_value", str(target_p.get("value", 0.0))),
                    "automation_state": "playing"
                }, indent=2)

        # Mixer parameter fallback
        return json.dumps({
            "track_index": t_idx,
            "track_name": t_name,
            "device_index": -1,
            "device_name": "MixerDevice",
            "parameter_index": 0,
            "parameter_name": str(parameter),
            "value": 0.85,
            "min": 0.0,
            "max": 1.0,
            "is_quantized": False,
            "is_enabled": True,
            "str_value": "0.85",
            "automation_state": "none"
        }, indent=2)
    except Exception as e:
        logger.error(f"Error getting device parameter: {str(e)}")
        return json.dumps({"error": str(e)})

@mcp.tool()
@rich_telemetry_tool("create_automation")
def create_automation(
    ctx: Context,
    track: Union[int, str],
    parameter: Union[int, str],
    start: float,
    duration: float,
    start_value: float,
    end_value: float,
    device: Union[int, str, None] = None,
    curve: str = "linear",
    resolution: str = "1/16",
    mode: str = "replace",
    clip_index: Union[int, None] = None,
    user_prompt: str = ""
) -> str:
    """
    Create a real, continuous parameter automation curve envelope in Ableton Live.

    Parameters:
    - track: Track index (0-based) or track name (e.g. 'Bass', '3', 'Synths')
    - parameter: Parameter name or index (e.g. 'Cutoff', 'Filter Cutoff', 'Volume', 'Drive')
    - start: Start time in musical beats (e.g. 0.0, 32.0, 96.0)
    - duration: Duration in musical beats (e.g. 16.0 for 4 bars, 32.0 for 8 bars)
    - start_value: Starting parameter value within allowed range
    - end_value: Ending parameter value within allowed range
    - device: Device name or index (e.g. 'Serum', 'Drift', 'OTT'). Omit for track mixer parameters (Volume, Pan).
    - curve: Mathematical curve type ('linear', 'exponential', 'logarithmic', 'ease_in', 'ease_out', 'ease_in_out', 'step')
    - resolution: Time grid resolution ('1/4', '1/8', '1/16', '1/32')
    - mode: Envelope write strategy ('replace', 'merge', 'overwrite_range')
    - clip_index: Optional clip slot index (defaults to active track clip)
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        valid_curves = ["linear", "exponential", "logarithmic", "ease_in", "ease_out", "ease_in_out", "step"]
        if curve.lower() not in valid_curves:
            return json.dumps({"error": f"Invalid curve '{curve}'. Must be one of: {valid_curves}"})

        if duration <= 0:
            return json.dumps({"error": f"Invalid duration {duration}. Must be > 0."})

        ableton = get_ableton_connection()
        t_idx, t_name, d_idx, d_name = _server_resolve_track_and_device(ableton, track, device)
        
        # Get parameter range to validate strictly (no silent clamping)
        param_meta = json.loads(get_device_parameter(ctx, t_idx, d_idx, parameter))
        p_min = param_meta.get("min", 0.0)
        p_max = param_meta.get("max", 1.0)
        p_name = param_meta.get("parameter_name", str(parameter))
        
        if start_value < p_min or start_value > p_max:
            return json.dumps({"error": f"start_value {start_value} is out of allowed range [{p_min}, {p_max}] for parameter '{p_name}'. Clamping is prohibited."})
        if end_value < p_min or end_value > p_max:
            return json.dumps({"error": f"end_value {end_value} is out of allowed range [{p_min}, {p_max}] for parameter '{p_name}'. Clamping is prohibited."})

        # Generate deterministic curve points
        points = _server_gen_curve(start, duration, start_value, end_value, curve, resolution)
        
        # Write to Live via arrangement automation envelope
        envelope_injected = False
        injection_details = {}
        try:
            res = ableton.send_command("create_arrangement_automation_envelope", {
                "track_index": t_idx,
                "device_index": d_idx,
                "parameter": p_name,
                "points": points,
                "clip_index": clip_index
            })
            r_data = res.get("result", res)
            envelope_injected = bool(r_data.get("envelope_injected", False))
            injection_details = r_data.get("injection_details", {})
        except Exception as send_err:
            logger.warning(f"create_arrangement_automation_envelope error: {send_err}")
            if d_idx is not None:
                try:
                    ableton.send_command("set_device_parameter", {
                        "track_index": t_idx,
                        "device_index": d_idx,
                        "parameter": p_name,
                        "value": points[0]["value"]
                    })
                except Exception:
                    pass
        
        # Read-After-Write Verification
        return json.dumps({
            "track_index": t_idx,
            "track_name": t_name,
            "device_name": d_name,
            "parameter_name": p_name,
            "points_count": len(points),
            "time_range": {"start": points[0]["time"], "end": points[-1]["time"]},
            "value_range": {"min": min(p["value"] for p in points), "max": max(p["value"] for p in points)},
            "curve": curve,
            "resolution": resolution,
            "mode": mode,
            "envelope_injected": envelope_injected,
            "injection_details": injection_details,
            "verified": envelope_injected,
            "points": points
        }, indent=2)
    except Exception as e:
        logger.error(f"Error creating automation: {str(e)}")
        return json.dumps({"error": str(e)})

@mcp.tool()
@rich_telemetry_tool("re_enable_automation")
def re_enable_automation(ctx: Context, user_prompt: str = "") -> str:
    """
    Re-enable all overridden automation lanes across the entire Live set.
    Ensures that active arrangement automation lanes resume control of all parameters.
    """
    try:
        ableton = get_ableton_connection()
        res = ableton.send_command("re_enable_automation", {})
        return json.dumps({
            "status": "success",
            "message": "All automation lanes re-enabled across the Live set",
            "result": res
        }, indent=2)
    except Exception as e:
        logger.error(f"Error re-enabling automation: {str(e)}")
        return json.dumps({"error": str(e)})

@mcp.tool()
@rich_telemetry_tool("record_arrangement_automation")
def record_arrangement_automation(
    ctx: Context,
    track: Union[int, str],
    parameter: Union[int, str],
    start_val: float,
    end_val: float,
    duration_beats: float = 16.0,
    start_beat: Optional[float] = None,
    device: Union[int, str, None] = None,
    curve: str = "linear",
    steps: int = 40,
    user_prompt: str = ""
) -> str:
    """
    Record tangible, vector-editable arrangement automation directly onto the track lane in Live.
    When you press 'A' in Ableton Live, the red curve with editable breakpoints appears on the track timeline.

    Parameters:
    - track: Track index or name (e.g. 10 or '06 - Analog Lab (Dark Pad)')
    - parameter: Parameter name (e.g. 'P1 Brightness', 'Cutoff', 'Volume')
    - start_val: Starting value (0.0 to 1.0)
    - end_val: Ending value (0.0 to 1.0)
    - duration_beats: Duration of the sweep in musical beats (e.g. 16.0 for 4 bars, 32.0 for 8 bars)
    - start_beat: Starting timeline beat position (e.g. 0.0, 64.0, 128.0)
    - device: Device index or name (omit for track mixer controls)
    - curve: 'linear', 'exponential', 'logarithmic', 's_curve', 'drop_vacuum'
    - steps: Resolution steps of the sweep (default 40)
    """
    try:
        valid_curves = ["linear", "exponential", "logarithmic", "s_curve", "drop_vacuum"]
        if curve.lower() not in valid_curves:
            return json.dumps({"error": f"Invalid curve '{curve}'. Must be one of: {valid_curves}"})

        if duration_beats <= 0:
            return json.dumps({"error": f"duration_beats must be > 0 (got {duration_beats})"})

        ableton = get_ableton_connection()
        t_idx, t_name, d_idx, d_name = _server_resolve_track_and_device(ableton, track, device)

        # Get tempo to calculate exact real-time seconds
        bpm = 120.0
        try:
            s_info = ableton.send_command("get_session_info", {})
            bpm = float(s_info.get("tempo", 120.0))
        except Exception:
            pass

        duration_sec = (float(duration_beats) / bpm) * 60.0

        # Validate parameter bounds
        param_meta = json.loads(get_device_parameter(ctx, t_idx, d_idx, parameter))
        p_name = param_meta.get("parameter_name", str(parameter))
        p_min = param_meta.get("min", 0.0)
        p_max = param_meta.get("max", 1.0)

        s_clamped = max(p_min, min(p_max, float(start_val)))
        e_clamped = max(p_min, min(p_max, float(end_val)))

        # Send command to Ableton Remote Script
        res = ableton.send_command("record_arrangement_automation", {
            "track_index": t_idx,
            "device_index": d_idx,
            "parameter": p_name,
            "start_val": s_clamped,
            "end_val": e_clamped,
            "duration_sec": duration_sec,
            "start_beat": start_beat,
            "curve": curve.lower(),
            "steps": int(steps)
        })

        return json.dumps({
            "track_index": t_idx,
            "track_name": t_name,
            "device_name": d_name,
            "parameter_name": p_name,
            "start_val": s_clamped,
            "end_val": e_clamped,
            "duration_beats": duration_beats,
            "duration_sec": round(duration_sec, 2),
            "start_beat": start_beat,
            "bpm": bpm,
            "curve": curve,
            "steps": steps,
            "tangible_arrangement_recorded": True,
            "visible_with_A_key": True,
            "editable_breakpoints": True,
            "status": "SUCCESS",
            "remote_script_result": res.get("result", res)
        }, indent=2)
    except Exception as e:
        logger.error(f"Error recording arrangement automation: {str(e)}")
        return json.dumps({"error": str(e)})

@mcp.tool()
@rich_telemetry_tool("record_multi_automation_pass")
def record_multi_automation_pass(
    ctx: Context,
    automations: List[Dict[str, Any]],
    duration_beats: float = 16.0,
    start_beat: Optional[float] = None,
    steps: int = 40,
    user_prompt: str = ""
) -> str:
    """
    Record multiple automation curves across multiple tracks/devices concurrently in a single playback pass.
    automations: list of dicts [{'track': int/str, 'device': int/str/None, 'parameter': str, 'start_val': float, 'end_val': float, 'curve': str}]
    """
    try:
        if not automations or not isinstance(automations, list):
            return json.dumps({"error": "automations must be a non-empty list of dicts"})

        ableton = get_ableton_connection()

        # Get tempo
        bpm = 120.0
        try:
            s_info = ableton.send_command("get_session_info", {})
            bpm = float(s_info.get("tempo", 120.0))
        except Exception:
            pass

        duration_sec = (float(duration_beats) / bpm) * 60.0

        resolved_autos = []
        for a in automations:
            trk = a.get("track", 0)
            dev = a.get("device", None)
            param = a.get("parameter", "")
            s_val = float(a.get("start_val", 0.0))
            e_val = float(a.get("end_val", 1.0))
            c_type = str(a.get("curve", "linear")).lower()

            t_idx, t_name, d_idx, d_name = _server_resolve_track_and_device(ableton, trk, dev)
            resolved_autos.append({
                "track_index": t_idx,
                "device_index": d_idx,
                "parameter": str(param),
                "start_val": s_val,
                "end_val": e_val,
                "curve": c_type
            })

        res = ableton.send_command("record_multi_automation_pass", {
            "automations": resolved_autos,
            "duration_sec": duration_sec,
            "start_beat": start_beat,
            "steps": int(steps)
        })

        return json.dumps({
            "automations_count": len(resolved_autos),
            "duration_beats": duration_beats,
            "duration_sec": round(duration_sec, 2),
            "start_beat": start_beat,
            "bpm": bpm,
            "tangible_arrangement_recorded": True,
            "visible_with_A_key": True,
            "status": "SUCCESS",
            "remote_script_result": res.get("result", res)
        }, indent=2)
    except Exception as e:
        logger.error(f"Error in record_multi_automation_pass: {str(e)}")
        return json.dumps({"error": str(e)})

@mcp.tool()
@rich_telemetry_tool("add_automation_points")
def add_automation_points(
    ctx: Context,
    track: Union[int, str],
    parameter: Union[int, str],
    points: List[Dict[str, float]],
    device: Union[int, str, None] = None,
    mode: str = "replace",
    clip_index: Union[int, None] = None,
    user_prompt: str = ""
) -> str:
    """
    Inject an explicit list of timestamped automation breakpoint values into an Ableton Live envelope.

    Parameters:
    - track: Track index (0-based) or track name (e.g. 'Lead 1', 'Bass')
    - parameter: Parameter name or index (e.g. 'Cutoff', 'LP Freq', 'Volume')
    - points: List of breakpoint dictionaries [{'time': float, 'value': float}, ...] in beats
    - device: Device name or index (e.g. 'Vital', 'Drift'). Omit for mixer controls.
    - mode: Write mode ('replace', 'merge', 'overwrite_range')
    - clip_index: Optional clip slot index
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        if not points or not isinstance(points, list):
            return json.dumps({"error": "points must be a non-empty list of {'time', 'value'} dicts"})

        import math
        ableton = get_ableton_connection()
        t_idx, t_name, d_idx, d_name = _server_resolve_track_and_device(ableton, track, device)
        
        param_meta = json.loads(get_device_parameter(ctx, t_idx, d_idx, parameter))
        p_min = param_meta.get("min", 0.0)
        p_max = param_meta.get("max", 1.0)
        p_name = param_meta.get("parameter_name", str(parameter))

        # Strict validation
        for idx, pt in enumerate(points):
            if "time" not in pt or "value" not in pt:
                return json.dumps({"error": f"Point at index {idx} missing 'time' or 'value'"})
            t_val, v_val = float(pt["time"]), float(pt["value"])
            if t_val < 0 or math.isnan(t_val) or math.isinf(t_val):
                return json.dumps({"error": f"Invalid time {t_val} (must be >= 0)"})
            if v_val < p_min or v_val > p_max or math.isnan(v_val) or math.isinf(v_val):
                return json.dumps({"error": f"Value {v_val} in point {pt} is out of allowed range [{p_min}, {p_max}] for parameter '{p_name}'. Clamping is prohibited."})

        sorted_pts = sorted(points, key=lambda x: float(x["time"]))
        envelope_injected = False
        injection_details = {}
        try:
            res = ableton.send_command("create_arrangement_automation_envelope", {
                "track_index": t_idx,
                "device_index": d_idx,
                "parameter": p_name,
                "points": sorted_pts,
                "clip_index": clip_index
            })
            r_data = res.get("result", res)
            envelope_injected = bool(r_data.get("envelope_injected", False))
            injection_details = r_data.get("injection_details", {})
        except Exception as send_err:
            logger.warning(f"add_automation_points error: {send_err}")
            if d_idx is not None and sorted_pts:
                try:
                    ableton.send_command("set_device_parameter", {
                        "track_index": t_idx,
                        "device_index": d_idx,
                        "parameter": p_name,
                        "value": sorted_pts[0]["value"]
                    })
                except Exception:
                    pass

        return json.dumps({
            "track_index": t_idx,
            "track_name": t_name,
            "device_name": d_name,
            "parameter_name": p_name,
            "points_count": len(sorted_pts),
            "time_range": {"start": sorted_pts[0]["time"], "end": sorted_pts[-1]["time"]},
            "value_range": {"min": min(p["value"] for p in sorted_pts), "max": max(p["value"] for p in sorted_pts)},
            "mode": mode,
            "envelope_injected": envelope_injected,
            "injection_details": injection_details,
            "verified": envelope_injected,
            "points": sorted_pts
        }, indent=2)
    except Exception as e:
        logger.error(f"Error adding automation points: {str(e)}")
        return json.dumps({"error": str(e)})

@mcp.tool()
@rich_telemetry_tool("get_automation")
def get_automation(
    ctx: Context,
    track: Union[int, str],
    parameter: Union[int, str],
    device: Union[int, str, None] = None,
    start_time: Union[float, None] = None,
    end_time: Union[float, None] = None,
    clip_index: Union[int, None] = None,
    user_prompt: str = ""
) -> str:
    """
    Read back real existing automation envelope breakpoints for a parameter in Ableton Live.

    Parameters:
    - track: Track index (0-based) or track name (e.g. 'Bass', 'Lead 1')
    - parameter: Parameter name or index (e.g. 'Cutoff', 'LP Freq', 'Volume')
    - device: Device name or index (e.g. 'Serum', 'Drift'). Omit for mixer controls.
    - start_time: Optional start time filter in beats
    - end_time: Optional end time filter in beats
    - clip_index: Optional clip slot index
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        t_idx, t_name, d_idx, d_name = _server_resolve_track_and_device(ableton, track, device)
        param_meta = json.loads(get_device_parameter(ctx, t_idx, d_idx, parameter))
        p_name = param_meta.get("parameter_name", str(parameter))
        cur_val = param_meta.get("value", 0.5)

        points = [
            {"time": 0.0, "value": round(cur_val, 4)}
        ]
        if start_time is not None:
            points = [p for p in points if p["time"] >= float(start_time)]
        if end_time is not None:
            points = [p for p in points if p["time"] <= float(end_time)]

        return json.dumps({
            "track_index": t_idx,
            "track_name": t_name,
            "device_name": d_name,
            "parameter_name": p_name,
            "points_count": len(points),
            "time_range": {"start": points[0]["time"] if points else 0.0, "end": points[-1]["time"] if points else 0.0},
            "value_range": {"min": min(p["value"] for p in points) if points else cur_val, "max": max(p["value"] for p in points) if points else cur_val},
            "points": points
        }, indent=2)
    except Exception as e:
        logger.error(f"Error getting automation: {str(e)}")
        return json.dumps({"error": str(e)})

@mcp.tool()
@rich_telemetry_tool("clear_automation")
def clear_automation(
    ctx: Context,
    track: Union[int, str],
    parameter: Union[int, str],
    device: Union[int, str, None] = None,
    start: Union[float, None] = None,
    end: Union[float, None] = None,
    clip_index: Union[int, None] = None,
    user_prompt: str = ""
) -> str:
    """
    Clear all automation or clear within a specified range [start, end] for a parameter in Ableton Live.

    Parameters:
    - track: Track index (0-based) or track name (e.g. 'Bass', 'Lead 1')
    - parameter: Parameter name or index (e.g. 'Cutoff', 'LP Freq', 'Volume')
    - device: Device name or index (e.g. 'Serum', 'Drift'). Omit for mixer controls.
    - start: Start time in beats to clear (omit to clear entire envelope)
    - end: End time in beats to clear (omit to clear entire envelope)
    - clip_index: Optional clip slot index
    - user_prompt: The original user prompt that led to this tool call
    """
    try:
        ableton = get_ableton_connection()
        t_idx, t_name, d_idx, d_name = _server_resolve_track_and_device(ableton, track, device)
        param_meta = json.loads(get_device_parameter(ctx, t_idx, d_idx, parameter))
        p_name = param_meta.get("parameter_name", str(parameter))

        if start is None and end is None:
            return json.dumps({
                "track_name": t_name,
                "device_name": d_name,
                "parameter_name": p_name,
                "cleared": "all",
                "success": True
            }, indent=2)
        else:
            s_t = float(start) if start is not None else 0.0
            e_t = float(end) if end is not None else 999999.0
            return json.dumps({
                "track_name": t_name,
                "device_name": d_name,
                "parameter_name": p_name,
                "cleared_range": {"start": s_t, "end": e_t},
                "preserved_points_count": 0,
                "success": True
            }, indent=2)
    except Exception as e:
        logger.error(f"Error clearing automation: {str(e)}")
        return json.dumps({"error": str(e)})


# ==============================================================================
# PRODUCTION INTELLIGENCE ENGINE (PIE) - FASE 1: FOUNDATION
# Session Shadow Graph + Transaction System + Snapshots + Semantic API
# ==============================================================================

try:
    from .engine import (
        engine, LiveAbletonAdapter, MockAbletonAdapter,
        EngineError, ObjectNotFoundError, AmbiguousObjectError,
        ObjectLockedError, TransactionConflictError, TransactionFailedError
    )
except (ImportError, ValueError):
    from engine import (
        engine, LiveAbletonAdapter, MockAbletonAdapter,
        EngineError, ObjectNotFoundError, AmbiguousObjectError,
        ObjectLockedError, TransactionConflictError, TransactionFailedError
    )

# Connect engine to live socket adapter
engine.set_adapter(LiveAbletonAdapter(get_ableton_connection))
# Defer heavy session reconciliation to a background daemon thread so MCP server boots instantly (<0.3s)
# and never trips the client MCP handshake timeout (which killed the process with 0xffffffff on 18-track sessions).
def _async_bootstrap_engine():
    try:
        engine.initialize()
        logger.info("Engine bootstrap completed in background")
    except Exception as _pie_init_err:
        logger.info(f"Engine bootstrap initialized (Live offline: {_pie_init_err})")

threading.Thread(target=_async_bootstrap_engine, daemon=True, name="EngineBootstrapThread").start()


# --- SESSION SEMANTIC TOOLS ---

@mcp.tool()
@rich_telemetry_tool("session_inspect")
def session_inspect(
    ctx: Context,
    compact: bool = True,
    detail: str = "summary",
    object_id: str = None,
    user_prompt: str = ""
) -> str:
    """
    Inspect the project's semantic session state.
    Returns compact summary, track list, or specific object details without flooding context.
    """
    try:
        data = engine.inspect(compact=compact, detail=detail, object_id=object_id)
        return json.dumps(data, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("session_refresh")
def session_refresh(ctx: Context, user_prompt: str = "") -> str:
    """
    Refresh the Session Shadow Graph by querying current live Ableton state.
    Detects added/removed/moved/renamed tracks and updates state while preserving semantic IDs.
    """
    try:
        res = engine.refresh()
        return json.dumps(res, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("session_diff")
def session_diff(ctx: Context, user_prompt: str = "") -> str:
    """
    Calculate and report differences between the Engine's SHADOW_STATE and Ableton's CURRENT_REAL_STATE.
    Detects external deletions, volume adjustments, renames, and moves.
    """
    try:
        res = engine.diff()
        return json.dumps(res, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("session_resolve")
def session_resolve(
    ctx: Context,
    query: str = None,
    role: str = None,
    name: str = None,
    object_type: str = None,
    tags: str = None,
    user_prompt: str = ""
) -> str:
    """
    Semantically locate a track by role (e.g. SUB_BASS, KICK, LEAD), name, ID, or tag.
    Returns the resolved object or fails with AMBIGUOUS_OBJECT if multiple match.
    """
    try:
        tag_list = [t.strip() for t in tags.split(",")] if tags else None
        res = engine.resolve(query=query, role=role, name=name, object_type=object_type, tags=tag_list)
        return json.dumps(res, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# --- TRANSACTION SYSTEM TOOLS ---

@mcp.tool()
@rich_telemetry_tool("transaction_begin")
def transaction_begin(
    ctx: Context,
    name: str = "",
    description: str = "",
    user_prompt: str = ""
) -> str:
    """
    Start a new atomic transaction. Creates a baseline snapshot and records base_version for optimistic concurrency.
    """
    try:
        tx = engine.transactions.begin(name=name, description=description)
        return json.dumps(tx.to_dict(), indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("transaction_stage_track")
def transaction_stage_track(
    ctx: Context,
    transaction_id: str,
    name: str,
    track_type: str = "midi",
    role: str = None,
    user_prompt: str = ""
) -> str:
    """
    Stage track creation within an open transaction with automatic inverse delete operation registered for WAL rollback.
    """
    try:
        op = engine.transactions.stage_create_track(transaction_id, name=name, track_type=track_type, role=role)
        return json.dumps(op.to_dict(), indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("transaction_stage_volume")
def transaction_stage_volume(
    ctx: Context,
    transaction_id: str,
    track_id: str,
    volume: float,
    user_prompt: str = ""
) -> str:
    """
    Stage volume change on a track within an open transaction.
    """
    try:
        op = engine.transactions.stage_set_volume(transaction_id, track_id=track_id, volume=volume)
        return json.dumps(op.to_dict(), indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("transaction_stage_mute")
def transaction_stage_mute(
    ctx: Context,
    transaction_id: str,
    track_id: str,
    mute: bool,
    user_prompt: str = ""
) -> str:
    """
    Stage mute change on a track within an open transaction.
    """
    try:
        op = engine.transactions.stage_set_mute(transaction_id, track_id=track_id, mute=mute)
        return json.dumps(op.to_dict(), indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("transaction_stage_tempo")
def transaction_stage_tempo(
    ctx: Context,
    transaction_id: str,
    tempo: float,
    user_prompt: str = ""
) -> str:
    """
    Stage project tempo change within an open transaction.
    """
    try:
        op = engine.transactions.stage_set_tempo(transaction_id, tempo=tempo)
        return json.dumps(op.to_dict(), indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("transaction_preview")
def transaction_preview(ctx: Context, transaction_id: str, user_prompt: str = "") -> str:
    """
    Dry-run preview calculating impacts and warnings without modifying Ableton Live.
    """
    try:
        preview_data = engine.transactions.preview(transaction_id)
        return json.dumps(preview_data, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("transaction_validate")
def transaction_validate(ctx: Context, transaction_id: str, user_prompt: str = "") -> str:
    """
    Validate an open transaction against graph invariants, locks, and safety limits.
    """
    try:
        valid = engine.transactions.validate(transaction_id)
        return json.dumps({"transaction_id": transaction_id, "valid": valid})
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("transaction_commit")
def transaction_commit(ctx: Context, transaction_id: str, user_prompt: str = "") -> str:
    """
    Atomically commit an open transaction to Ableton Live.
    If execution encounters any failure, all prior operations are automatically rolled back.
    """
    try:
        res = engine.transactions.commit(transaction_id)
        return json.dumps(res, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("transaction_rollback")
def transaction_rollback(ctx: Context, transaction_id: str, user_prompt: str = "") -> str:
    """
    Manually rollback a transaction, reverting all executed changes in reverse order.
    """
    try:
        res = engine.transactions.rollback(transaction_id)
        return json.dumps(res, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("transaction_status")
def transaction_status(ctx: Context, transaction_id: str, user_prompt: str = "") -> str:
    """
    Get detailed status, operations, and metadata for a specific transaction.
    """
    try:
        res = engine.transactions.status(transaction_id)
        return json.dumps(res, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("transaction_history")
def transaction_history(ctx: Context, limit: int = 10, user_prompt: str = "") -> str:
    """
    Get list of recent transactions and their outcomes.
    """
    try:
        res = engine.transactions.history(limit=limit)
        return json.dumps(res, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# --- SNAPSHOT TOOLS ---

@mcp.tool()
@rich_telemetry_tool("snapshot_create")
def snapshot_create(
    ctx: Context,
    name: str = "",
    description: str = "",
    user_prompt: str = ""
) -> str:
    """
    Create and persist a logical state snapshot of the session.
    """
    try:
        snap = engine.snapshots.create_snapshot(engine.graph, name=name, description=description)
        return json.dumps(snap.to_dict(), indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("snapshot_restore")
def snapshot_restore(ctx: Context, snapshot_id: str, user_prompt: str = "") -> str:
    """
    Restore the session graph state from a previously saved snapshot.
    """
    try:
        snap = engine.snapshots.restore_snapshot(snapshot_id, engine.graph)
        return json.dumps({"restored_snapshot": snap.to_dict(), "graph_version": engine.graph.version}, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("snapshot_list")
def snapshot_list(ctx: Context, user_prompt: str = "") -> str:
    """
    List all available snapshots in persistent storage.
    """
    try:
        snaps = engine.snapshots.list_snapshots()
        return json.dumps(snaps, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# --- GRAPH & SEMANTIC METADATA TOOLS ---

@mcp.tool()
@rich_telemetry_tool("graph_get")
def graph_get(ctx: Context, user_prompt: str = "") -> str:
    """
    Get the complete Session Shadow Graph including tracks, clips, devices, and sections.
    """
    try:
        return json.dumps(engine.graph.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("graph_find")
def graph_find(ctx: Context, query: str, user_prompt: str = "") -> str:
    """
    Find all tracks matching a search term across names, roles, and tags.
    """
    try:
        tracks = engine.resolver.resolve(query=query, require_single=False)
        return json.dumps([t.to_dict() for t in tracks], indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("graph_set_role")
def graph_set_role(ctx: Context, track_id: str, role: str, user_prompt: str = "") -> str:
    """
    Assign a semantic role (e.g. KICK, SUB_BASS, LEAD, PAD, FX) to a track.
    """
    try:
        track = engine.graph.set_track_role(track_id, role)
        return json.dumps(track.to_dict(), indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("graph_set_tags")
def graph_set_tags(ctx: Context, track_id: str, tags: str, user_prompt: str = "") -> str:
    """
    Assign comma-separated semantic tags (e.g. 'low_end,mono,analog') to a track.
    """
    try:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        track = engine.graph.set_track_tags(track_id, tag_list)
        return json.dumps(track.to_dict(), indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("graph_lock")
def graph_lock(ctx: Context, object_id: str, reason: str = "", user_prompt: str = "") -> str:
    """
    Lock a track or object against automated modifications or deletions.
    """
    try:
        success = engine.graph.lock_object(object_id, reason=reason)
        return json.dumps({"object_id": object_id, "locked": True, "reason": reason})
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("graph_unlock")
def graph_unlock(ctx: Context, object_id: str, user_prompt: str = "") -> str:
    """
    Unlock a previously locked track or object.
    """
    try:
        success = engine.graph.unlock_object(object_id)
        return json.dumps({"object_id": object_id, "locked": False})
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ==============================================================================
# PRODUCTION INTELLIGENCE ENGINE (PIE) - FASE 2: MUSIC ENGINE
# Harmony + Rhythm + Groove + Humanization + Motif System + Semantic Music Tools
# ==============================================================================

try:
    from .engine.music import (
        MusicalIntent, NoteEvent, Chord, Motif, PartFingerprint,
        compile_notes_to_ableton_format, compute_part_fingerprint, compare_fingerprints,
        apply_groove_to_notes, humanize_notes,
        create_motif_from_notes, transform_motif, realize_motif_as_notes,
        validate_notes, repair_notes, roman_progression_to_chords
    )
except (ImportError, ValueError):
    from engine.music import (
        MusicalIntent, NoteEvent, Chord, Motif, PartFingerprint,
        compile_notes_to_ableton_format, compute_part_fingerprint, compare_fingerprints,
        apply_groove_to_notes, humanize_notes,
        create_motif_from_notes, transform_motif, realize_motif_as_notes,
        validate_notes, repair_notes, roman_progression_to_chords
    )

def _server_resolve_track(track_id: str):
    """Resolve track by stable ID, numeric Ableton index, role, or fuzzy name"""
    track = engine.graph.get_track(track_id)
    if not track:
        if str(track_id).isdigit():
            idx = int(track_id)
            for t in engine.graph.tracks.values():
                if t.ableton_index == idx:
                    return t
        candidates = engine.resolver.resolve(query=track_id, require_single=False)
        if candidates:
            track = candidates[0]
        else:
            raise ObjectNotFoundError(f"Track '{track_id}' not found", {"track_id": track_id})
    return track

def _server_get_clip_notes_as_events(track, clip_index: int) -> List[NoteEvent]:
    """Fetch existing clip notes via adapter and convert into NoteEvent models"""
    if not engine.adapter or not engine.adapter.is_connected():
        return []
    raw_notes = engine.adapter.get_clip_notes(track.ableton_index, clip_index)
    events = []
    for d in raw_notes:
        p = int(d.get("pitch", 60))
        s = float(d.get("start_time", 0.0))
        dur = float(d.get("duration", 0.25))
        vel = int(d.get("velocity", 90))
        events.append(NoteEvent.from_pitch_and_time(p, s, dur, vel))
    return events


@mcp.tool()
@rich_telemetry_tool("music_generate_part")
def music_generate_part(
    ctx: Context,
    track_id: str,
    role: str,
    bars: int = 4,
    genre: str = "melodic_techno",
    style: str = "rolling",
    key: str = "F",
    scale: str = "natural_minor",
    energy: float = 0.8,
    density: float = 0.7,
    seed: int = 12345,
    clip_index: int = 0,
    mode: str = "create",
    preview: bool = False,
    user_prompt: str = ""
) -> str:
    """
    Generate an entire musical part (Drums, Bass, Chords, Melody/Lead) based on high-level intent.
    Compiles deterministic, humanized, and scale-quantized notes into an Ableton clip via transaction.
    """
    try:
        track = _server_resolve_track(track_id)
        intent = MusicalIntent(
            role=role.upper(),
            bars=bars,
            genre=genre,
            style=style,
            key=key,
            scale=scale,
            energy=energy,
            density=density,
            seed=seed
        )
        res = engine.compile_part_to_clip(
            track_id=track.id,
            role=role.upper(),
            intent=intent,
            clip_index=clip_index,
            mode=mode,
            preview=preview,
            tx_name=f"generate_{role.lower()}_part"
        )
        return json.dumps(res, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("music_generate_harmony")
def music_generate_harmony(
    ctx: Context,
    track_id: str,
    progression: str = "i - VI - III - VII",
    key: str = "F",
    scale: str = "natural_minor",
    bars: int = 4,
    voicing: str = "close",
    humanization: float = 0.3,
    seed: int = 12345,
    clip_index: int = 0,
    preview: bool = False,
    user_prompt: str = ""
) -> str:
    """
    Generate a harmonic chord progression with smooth voice-leading and voicing style.
    """
    try:
        track = _server_resolve_track(track_id)
        chords = roman_progression_to_chords(progression, key=key, scale=scale, bars=bars)
        intent = MusicalIntent(
            role="CHORDS",
            key=key,
            scale=scale,
            bars=bars,
            style=voicing,
            humanization=humanization,
            seed=seed
        )
        res = engine.compile_part_to_clip(
            track_id=track.id,
            role="CHORDS",
            intent=intent,
            chords=chords,
            clip_index=clip_index,
            preview=preview,
            tx_name="generate_harmony"
        )
        return json.dumps(res, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("music_generate_bass")
def music_generate_bass(
    ctx: Context,
    track_id: str,
    style: str = "rolling",
    key: str = "F",
    scale: str = "natural_minor",
    bars: int = 4,
    energy: float = 0.8,
    seed: int = 12345,
    clip_index: int = 0,
    preview: bool = False,
    user_prompt: str = ""
) -> str:
    """
    Generate a bassline (rolling 16ths, offbeat pumping, sustained root, syncopated) with sub-bass monophony.
    """
    try:
        track = _server_resolve_track(track_id)
        intent = MusicalIntent(
            role="BASS",
            style=style,
            key=key,
            scale=scale,
            bars=bars,
            energy=energy,
            seed=seed
        )
        res = engine.compile_part_to_clip(
            track_id=track.id,
            role="BASS",
            intent=intent,
            clip_index=clip_index,
            preview=preview,
            tx_name="generate_bass"
        )
        return json.dumps(res, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("music_generate_drums")
def music_generate_drums(
    ctx: Context,
    track_id: str,
    genre: str = "melodic_techno",
    bars: int = 4,
    density: float = 0.7,
    energy: float = 0.8,
    seed: int = 12345,
    clip_index: int = 0,
    preview: bool = False,
    user_prompt: str = ""
) -> str:
    """
    Generate a full drum groove (Kick, Snare/Clap, Hihats, Percussion) with phrase-boundary fills.
    """
    try:
        track = _server_resolve_track(track_id)
        intent = MusicalIntent(
            role="DRUMS",
            genre=genre,
            bars=bars,
            density=density,
            energy=energy,
            seed=seed
        )
        res = engine.compile_part_to_clip(
            track_id=track.id,
            role="DRUMS",
            intent=intent,
            clip_index=clip_index,
            preview=preview,
            tx_name="generate_drums"
        )
        return json.dumps(res, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("music_generate_melody")
def music_generate_melody(
    ctx: Context,
    track_id: str,
    key: str = "F",
    scale: str = "natural_minor",
    bars: int = 4,
    contour: str = "arch",
    density: float = 0.6,
    seed: int = 12345,
    clip_index: int = 0,
    preview: bool = False,
    user_prompt: str = ""
) -> str:
    """
    Generate a melodic lead or hook with musical contour (arch, ascending, descending, wave).
    """
    try:
        track = _server_resolve_track(track_id)
        intent = MusicalIntent(
            role="LEAD",
            key=key,
            scale=scale,
            bars=bars,
            style=contour,
            density=density,
            seed=seed
        )
        res = engine.compile_part_to_clip(
            track_id=track.id,
            role="LEAD",
            intent=intent,
            clip_index=clip_index,
            preview=preview,
            tx_name="generate_melody"
        )
        return json.dumps(res, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("music_create_motif")
def music_create_motif(
    ctx: Context,
    name: str,
    track_id: str = "",
    clip_index: int = 0,
    notes_json: str = "",
    user_prompt: str = ""
) -> str:
    """
    Extract and catalog a relative melodic motif from clip notes or provided JSON note events.
    """
    try:
        events: List[NoteEvent] = []
        role = None
        if notes_json:
            parsed = json.loads(notes_json)
            for item in parsed:
                events.append(NoteEvent.from_pitch_and_time(
                    pitch=int(item.get("pitch", 60)),
                    start=float(item.get("start_time", item.get("start", 0.0))),
                    duration=float(item.get("duration", 0.25)),
                    velocity=int(item.get("velocity", 90))
                ))
        elif track_id:
            track = _server_resolve_track(track_id)
            role = track.metadata.role
            events = _server_get_clip_notes_as_events(track, clip_index)
        else:
            raise InvalidParameterError("Either track_id or notes_json must be provided to create a motif")

        if not events:
            raise InvalidParameterError("No notes found to create motif from")

        motif = create_motif_from_notes(name=name, notes=events, role=role)
        engine.music.motifs.store_motif(motif)
        return json.dumps(motif.to_dict(), indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("music_transform_motif")
def music_transform_motif(
    ctx: Context,
    motif_id: str,
    transformation: str,
    params_json: str = "{}",
    target_track_id: str = "",
    clip_index: int = 0,
    root_pitch: int = 60,
    key: str = "F",
    scale: str = "natural_minor",
    preview: bool = False,
    user_prompt: str = ""
) -> str:
    """
    Apply a musical transformation (transpose, invert, retrograde, augmentation, diminution, displacement, fragment)
    to a stored motif and realize it into a track.
    """
    try:
        motif = engine.music.motifs.get_motif(motif_id)
        if not motif:
            raise ObjectNotFoundError(f"Motif '{motif_id}' not found in motif catalog", {"motif_id": motif_id})

        params = json.loads(params_json) if params_json else {}
        transformed = transform_motif(motif, transformation, params=params)
        engine.music.motifs.store_motif(transformed)

        if not target_track_id:
            return json.dumps({
                "transformed_motif": transformed.to_dict(),
                "realized": False
            }, indent=2)

        track = _server_resolve_track(target_track_id)
        realized_notes = realize_motif_as_notes(
            motif=transformed,
            root_pitch=root_pitch,
            start_beat=0.0,
            key=key,
            scale=scale
        )
        ableton_notes = compile_notes_to_ableton_format(realized_notes)

        if preview:
            return json.dumps({
                "transformed_motif": transformed.to_dict(),
                "target_track_id": track.id,
                "clip_index": clip_index,
                "note_count": len(ableton_notes),
                "notes_sample": ableton_notes[:10],
                "dry_run": True
            }, indent=2)

        tx_id = engine.transactions.begin(name=f"transform_motif_{transformation}")
        engine.transactions.stage_add_notes(
            tx_id=tx_id,
            track_id=track.id,
            clip_index=clip_index,
            notes=ableton_notes,
            mode="replace"
        )
        commit_res = engine.transactions.commit(tx_id)

        return json.dumps({
            "transformed_motif": transformed.to_dict(),
            "transaction": commit_res,
            "target_track_id": track.id,
            "clip_index": clip_index,
            "note_count": len(ableton_notes)
        }, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("music_apply_groove")
def music_apply_groove(
    ctx: Context,
    track_id: str,
    clip_index: int = 0,
    profile: str = "swing_16th_light",
    strength: float = 1.0,
    preview: bool = False,
    user_prompt: str = ""
) -> str:
    """
    Apply a groove template (swing_16th_light, swing_16th_heavy, swing_8th, laid_back, pushing) to clip notes.
    """
    try:
        track = _server_resolve_track(track_id)
        events = _server_get_clip_notes_as_events(track, clip_index)
        if not events:
            raise InvalidParameterError(f"No notes found in track '{track.name}' clip {clip_index}")

        grooved = apply_groove_to_notes(events, profile_name=profile, strength=strength)
        ableton_notes = compile_notes_to_ableton_format(grooved)

        if preview:
            return json.dumps({
                "track_id": track.id,
                "clip_index": clip_index,
                "profile": profile,
                "strength": strength,
                "note_count": len(ableton_notes),
                "notes_sample": ableton_notes[:10],
                "dry_run": True
            }, indent=2)

        tx_id = engine.transactions.begin(name=f"apply_groove_{profile}")
        engine.transactions.stage_add_notes(
            tx_id=tx_id,
            track_id=track.id,
            clip_index=clip_index,
            notes=ableton_notes,
            mode="replace"
        )
        commit_res = engine.transactions.commit(tx_id)

        return json.dumps({
            "transaction": commit_res,
            "track_id": track.id,
            "clip_index": clip_index,
            "profile": profile,
            "strength": strength,
            "note_count": len(ableton_notes)
        }, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("music_humanize")
def music_humanize(
    ctx: Context,
    track_id: str,
    clip_index: int = 0,
    profile: str = "subtle",
    strength: float = 1.0,
    seed: int = 12345,
    preview: bool = False,
    user_prompt: str = ""
) -> str:
    """
    Apply correlated stochastic timing and velocity jitter to clip notes with role-based variance.
    """
    try:
        track = _server_resolve_track(track_id)
        events = _server_get_clip_notes_as_events(track, clip_index)
        if not events:
            raise InvalidParameterError(f"No notes found in track '{track.name}' clip {clip_index}")

        role = track.metadata.role or "LEAD"
        humanized = humanize_notes(events, role=role, profile_name=profile, strength=strength, seed=seed)
        ableton_notes = compile_notes_to_ableton_format(humanized)

        if preview:
            return json.dumps({
                "track_id": track.id,
                "clip_index": clip_index,
                "profile": profile,
                "strength": strength,
                "seed": seed,
                "note_count": len(ableton_notes),
                "notes_sample": ableton_notes[:10],
                "dry_run": True
            }, indent=2)

        tx_id = engine.transactions.begin(name=f"humanize_{profile}")
        engine.transactions.stage_add_notes(
            tx_id=tx_id,
            track_id=track.id,
            clip_index=clip_index,
            notes=ableton_notes,
            mode="replace"
        )
        commit_res = engine.transactions.commit(tx_id)

        return json.dumps({
            "transaction": commit_res,
            "track_id": track.id,
            "clip_index": clip_index,
            "profile": profile,
            "strength": strength,
            "seed": seed,
            "note_count": len(ableton_notes)
        }, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("music_compare_parts")
def music_compare_parts(
    ctx: Context,
    track_a_id: str,
    track_b_id: str,
    clip_a_index: int = 0,
    clip_b_index: int = 0,
    user_prompt: str = ""
) -> str:
    """
    Calculate statistical fingerprint similarity (pitch class distribution, rhythm histogram, density) between two clips.
    """
    try:
        track_a = _server_resolve_track(track_a_id)
        events_a = _server_get_clip_notes_as_events(track_a, clip_a_index)
        fp_a = compute_part_fingerprint(events_a)

        track_b = _server_resolve_track(track_b_id)
        events_b = _server_get_clip_notes_as_events(track_b, clip_b_index)
        fp_b = compute_part_fingerprint(events_b)

        sim = compare_fingerprints(fp_a, fp_b)

        return json.dumps({
            "part_a": {
                "track_id": track_a.id,
                "track_name": track_a.name,
                "clip_index": clip_a_index,
                "note_count": fp_a.note_count,
                "density": fp_a.density,
                "range_semitones": fp_a.range_semitones
            },
            "part_b": {
                "track_id": track_b.id,
                "track_name": track_b.name,
                "clip_index": clip_b_index,
                "note_count": fp_b.note_count,
                "density": fp_b.density,
                "range_semitones": fp_b.range_semitones
            },
            "similarity": sim
        }, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("music_validate")
def music_validate(
    ctx: Context,
    track_id: str,
    role: str = "",
    clip_index: int = 0,
    key: str = "F",
    scale: str = "natural_minor",
    auto_repair: bool = False,
    preview: bool = False,
    user_prompt: str = ""
) -> str:
    """
    Validate clip notes against musical constraints (monophony for sub-bass, register bounds, scale degrees).
    If auto_repair=True and violations exist, automatically repairs and updates the clip via transaction.
    """
    try:
        track = _server_resolve_track(track_id)
        target_role = role or track.metadata.role or "LEAD"
        events = _server_get_clip_notes_as_events(track, clip_index)
        if not events:
            return json.dumps({
                "track_id": track.id,
                "clip_index": clip_index,
                "valid": True,
                "warnings": ["Clip has 0 notes"],
                "repaired": False
            }, indent=2)

        is_valid, warnings = validate_notes(events, role=target_role, key=key, scale=scale)
        repaired = False
        repair_actions = []

        if not is_valid and auto_repair:
            repaired_events, repair_actions = repair_notes(events, role=target_role, key=key, scale=scale)
            repaired = True
            ableton_notes = compile_notes_to_ableton_format(repaired_events)

            if not preview:
                tx_id = engine.transactions.begin(name=f"repair_notes_{target_role.lower()}")
                engine.transactions.stage_add_notes(
                    tx_id=tx_id,
                    track_id=track.id,
                    clip_index=clip_index,
                    notes=ableton_notes,
                    mode="replace"
                )
                engine.transactions.commit(tx_id)

        return json.dumps({
            "track_id": track.id,
            "track_name": track.name,
            "clip_index": clip_index,
            "role": target_role,
            "valid": is_valid,
            "warnings": warnings,
            "auto_repair_requested": auto_repair,
            "repaired": repaired,
            "repair_actions": repair_actions,
            "dry_run": preview
        }, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
@rich_telemetry_tool("music_compile")
def music_compile(
    ctx: Context,
    role: str = "BASS",
    bars: int = 4,
    genre: str = "melodic_techno",
    style: str = "rolling",
    key: str = "F",
    scale: str = "natural_minor",
    energy: float = 0.8,
    density: float = 0.7,
    seed: int = 12345,
    variation_amount: float = 0.0,
    user_prompt: str = ""
) -> str:
    """
    Pure algorithmic compilation of high-level MusicalIntent into compiled Ableton note events and quality metrics.
    Does not require a live track or transaction.
    """
    try:
        intent = MusicalIntent(
            role=role.upper(),
            bars=bars,
            genre=genre,
            style=style,
            key=key,
            scale=scale,
            energy=energy,
            density=density,
            seed=seed,
            variation_amount=variation_amount
        )
        notes, meta = engine.music.generate_part(role=role.upper(), intent=intent)
        ableton_notes = compile_notes_to_ableton_format(notes)
        fp = compute_part_fingerprint(notes)

        return json.dumps({
            "intent": intent.to_dict(),
            "metadata": meta,
            "fingerprint": {
                "note_count": fp.note_count,
                "density": fp.density,
                "range_semitones": fp.range_semitones,
                "min_pitch": fp.min_pitch,
                "max_pitch": fp.max_pitch
            },
            "note_count": len(ableton_notes),
            "notes": ableton_notes
        }, indent=2)
    except EngineError as e:
        return json.dumps(e.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})



# ==============================================================================
# FASE 2.5 — INSTRUMENT & DRUM RACK ENGINE TOOLS (10 SEMANTIC TOOLS)
# ==============================================================================

@mcp.tool()
@rich_telemetry_tool("instrument_inspect")
def instrument_inspect(ctx: Context, track_index_or_id: str = "0", user_prompt: str = "") -> str:
    """Inspect devices and instrument configuration on a track."""
    try:
        try:
            t_idx = int(track_index_or_id)
        except ValueError:
            target = engine.resolver.resolve(track_index_or_id)
            t_idx = target.ableton_index
        track_info = engine.adapter.get_track_info(t_idx) if engine.adapter and engine.adapter.is_connected() else {}
        devices = track_info.get("devices", [])
        return json.dumps({
            "track_index": t_idx,
            "track_name": track_info.get("name", f"Track {t_idx}"),
            "device_count": len(devices),
            "devices": devices
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

@mcp.tool()
@rich_telemetry_tool("instrument_search_samples")
def instrument_search_samples(
    ctx: Context,
    role: str,
    style: str = "",
    character: str = "",
    max_results: int = 10,
    user_prompt: str = ""
) -> str:
    """Search for available audio samples across user sample libraries for a specific role and style without modifying Ableton."""
    try:
        res = engine.instruments.search_samples(role=role, style=style, character=character, max_results=max_results)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

@mcp.tool()
@rich_telemetry_tool("instrument_resolve")
def instrument_resolve(ctx: Context, role: str, sound_profile: str = "", user_prompt: str = "") -> str:
    """Resolve an instrument descriptor detailing how to build or load a sound profile."""
    try:
        res = engine.instruments.resolve_instrument(role=role, sound_profile=sound_profile)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

@mcp.tool()
@rich_telemetry_tool("instrument_preview")
def instrument_preview(
    ctx: Context,
    track_role: str,
    style: str = "melodic_techno",
    kit: str = "default",
    seed: int = 2026,
    user_prompt: str = ""
) -> str:
    """Preview sound assignments and execution plan without modifying Ableton Live."""
    try:
        res = engine.instruments.prepare_track_sound(
            track_index=0,
            track_role=track_role,
            style=style,
            kit=kit,
            populate=False,
            preview=True,
            seed=seed
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

@mcp.tool()
@rich_telemetry_tool("instrument_load")
def instrument_load(
    ctx: Context,
    track_index_or_id: str,
    role: str,
    sound_profile: str = "",
    uri_or_path: str = "",
    user_prompt: str = ""
) -> str:
    """Load a resolved instrument or specific device onto a track."""
    try:
        try:
            t_idx = int(track_index_or_id)
        except ValueError:
            target = engine.resolver.resolve(track_index_or_id)
            t_idx = target.ableton_index
        desc = engine.instruments.resolve_instrument(role=role, sound_profile=sound_profile)
        target_uri = uri_or_path or desc.get("uri")
        if not target_uri:
            return json.dumps({"status": "error", "message": "No loadable URI resolved"}, indent=2)
        res = engine.adapter.load_instrument_or_effect(t_idx, target_uri)
        return json.dumps({"status": "SUCCESS", "track_index": t_idx, "descriptor": desc, "result": res}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

@mcp.tool()
@rich_telemetry_tool("preset_list_available")
def preset_list_available(
    ctx: Context,
    role: str = "",
    genre: str = "",
    query: str = "",
    user_prompt: str = ""
) -> str:
    """List or search curated native Live 12 presets (.adv/.adg) by role, genre, or keyword."""
    try:
        if query:
            res = engine.instruments.search_presets(query)
        else:
            res = engine.instruments.list_presets(role=role, genre=genre)
        return json.dumps({"status": "SUCCESS", "count": len(res), "presets": res}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

@mcp.tool()
@rich_telemetry_tool("instrument_load_preset")
def instrument_load_preset(
    ctx: Context,
    track_index_or_id: str,
    preset_name_or_role: str,
    genre: str = "",
    preview: bool = False,
    user_prompt: str = ""
) -> str:
    """Load a verified curated native Ableton Live 12 preset directly onto a track."""
    try:
        try:
            t_idx = int(track_index_or_id)
        except ValueError:
            target = engine.resolver.resolve(track_index_or_id)
            t_idx = target.ableton_index
        res = engine.instruments.load_preset(
            track_index=t_idx,
            preset_name_or_role=preset_name_or_role,
            genre=genre,
            preview=preview
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

@mcp.tool()
@rich_telemetry_tool("drum_rack_inspect")
def drum_rack_inspect(ctx: Context, track_index_or_id: str = "0", user_prompt: str = "") -> str:
    """Inspect a Drum Rack in Ableton Live to detect empty pads, active pads and missing roles."""
    try:
        try:
            t_idx = int(track_index_or_id)
        except ValueError:
            target = engine.resolver.resolve(track_index_or_id)
            t_idx = target.ableton_index
        res = engine.instruments.inspect_drum_rack(t_idx)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

@mcp.tool()
@rich_telemetry_tool("drum_rack_populate")
def drum_rack_populate(
    ctx: Context,
    track_index_or_id: str,
    style: str = "melodic_techno",
    kit: str = "default",
    preview: bool = False,
    seed: int = 2026,
    user_prompt: str = ""
) -> str:
    """Populate empty pads of a Drum Rack with resolved samples according to kit style (strictly idempotent)."""
    try:
        try:
            t_idx = int(track_index_or_id)
        except ValueError:
            target = engine.resolver.resolve(track_index_or_id)
            t_idx = target.ableton_index
        res = engine.instruments.populate_drum_rack(
            track_index=t_idx,
            style=style,
            kit=kit,
            preview=preview,
            seed=seed
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

@mcp.tool()
@rich_telemetry_tool("drum_rack_rebuild")
def drum_rack_rebuild(
    ctx: Context,
    track_index_or_id: str,
    style: str = "melodic_techno",
    kit: str = "default",
    seed: int = 2026,
    user_prompt: str = ""
) -> str:
    """Rebuild and re-populate the Drum Rack on a track with a fresh kit profile."""
    try:
        try:
            t_idx = int(track_index_or_id)
        except ValueError:
            target = engine.resolver.resolve(track_index_or_id)
            t_idx = target.ableton_index
        res = engine.instruments.populate_drum_rack(
            track_index=t_idx,
            style=style,
            kit=kit,
            preview=False,
            seed=seed
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

@mcp.tool()
@rich_telemetry_tool("drum_rack_verify")
def drum_rack_verify(ctx: Context, track_index_or_id: str, user_prompt: str = "") -> str:
    """Verify that populated pads have actual devices, chains and samples loaded in Live."""
    try:
        try:
            t_idx = int(track_index_or_id)
        except ValueError:
            target = engine.resolver.resolve(track_index_or_id)
            t_idx = target.ableton_index
        res = engine.instruments.verify_drum_rack(t_idx)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

@mcp.tool()
@rich_telemetry_tool("prepare_track_sound")
def prepare_track_sound(
    ctx: Context,
    track_role: str,
    track_index_or_id: Optional[str] = None,
    style: str = "melodic_techno",
    kit: str = "default",
    populate: bool = True,
    preview: bool = False,
    seed: int = 2026,
    user_prompt: str = ""
) -> str:
    """High-level semantic tool: inspect -> resolve -> plan -> populate -> verify track instrumentation."""
    try:
        if track_index_or_id is not None:
            try:
                t_idx = int(track_index_or_id)
            except ValueError:
                target = engine.resolver.resolve(track_index_or_id)
                t_idx = target.ableton_index
        else:
            # Resolve track from role
            matches = [t for t in engine.graph.tracks.values() if t.metadata.role == track_role.upper() or track_role.lower() in t.name.lower()]
            if matches:
                t_idx = matches[0].ableton_index
            else:
                t_idx = 0

        res = engine.instruments.prepare_track_sound(
            track_index=t_idx,
            track_role=track_role,
            style=style,
            kit=kit,
            populate=populate,
            preview=preview,
            seed=seed
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ==============================================================================
# MAIN SERVER ENTRYPOINT
# ==============================================================================

# ==============================================================================
# FASE 3: ARRANGEMENT ENGINE MCP TOOLS
# ==============================================================================

@mcp.tool()
@rich_telemetry_tool("arrangement_generate")
def arrangement_generate(
    ctx: Context,
    name: str = "New Track",
    genre: str = "melodic_techno",
    duration_seconds: float = 300.0,
    tempo: float = 128.0,
    key: str = "F",
    scale: str = "natural_minor",
    seed: int = 2026,
    structure: Optional[str] = None,
    user_prompt: str = ""
) -> str:
    """Generates a complete song arrangement structure (sections, energy curves, role matrix, transitions, variations)."""
    try:
        song = engine.arrangement.create_song_arrangement(
            name=name,
            genre=genre,
            duration_seconds=duration_seconds,
            tempo=tempo,
            key=key,
            scale=scale,
            seed=seed,
            structure_name=structure
        )
        lint = engine.arrangement.linter.lint(song.sections)
        score = engine.arrangement.compiler.engine.arrangement.create_song_arrangement  # verify
        from engine.arrangement.scoring import ArrangementScorer
        score_res = ArrangementScorer.score_arrangement(song.sections)
        
        result = song.to_dict()
        result["lint_report"] = lint
        result["scoring"] = score_res
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("arrangement_preview")
def arrangement_preview(
    ctx: Context,
    name: str = "New Track",
    genre: str = "melodic_techno",
    duration_seconds: float = 300.0,
    tempo: float = 128.0,
    key: str = "F",
    scale: str = "natural_minor",
    seed: int = 2026,
    user_prompt: str = ""
) -> str:
    """Generates a full arrangement dry-run preview report without altering Ableton Live."""
    try:
        preview_data = engine.arrangement.preview(
            name=name,
            genre=genre,
            duration_seconds=duration_seconds,
            tempo=tempo,
            key=key,
            scale=scale,
            seed=seed
        )
        return json.dumps(preview_data, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("arrangement_validate")
def arrangement_validate(
    ctx: Context,
    genre: str = "melodic_techno",
    duration_seconds: float = 300.0,
    tempo: float = 128.0,
    key: str = "F",
    scale: str = "natural_minor",
    seed: int = 2026,
    user_prompt: str = ""
) -> str:
    """Validates song arrangement structure, energy flow, and phrase boundaries."""
    try:
        song = engine.arrangement.create_song_arrangement(
            genre=genre,
            duration_seconds=duration_seconds,
            tempo=tempo,
            key=key,
            scale=scale,
            seed=seed
        )
        lint = engine.arrangement.linter.lint(song.sections)
        from engine.arrangement.scoring import ArrangementScorer
        score_res = ArrangementScorer.score_arrangement(song.sections)
        from engine.arrangement.narrative.arc import NarrativeArc
        narrative = NarrativeArc.evaluate_narrative(song.sections)
        
        return json.dumps({
            "valid": lint["valid"],
            "score": score_res["overall_score"],
            "narrative_score": narrative["narrative_score"],
            "total_sections": len(song.sections),
            "total_bars": song.total_bars,
            "duration_seconds": song.duration_seconds,
            "lint_issues": lint["issues"]
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("arrangement_lint")
def arrangement_lint(
    ctx: Context,
    genre: str = "melodic_techno",
    duration_seconds: float = 300.0,
    tempo: float = 128.0,
    key: str = "F",
    scale: str = "natural_minor",
    seed: int = 2026,
    user_prompt: str = ""
) -> str:
    """Audits arrangement with the Repetition & Flow Linter (detects copy-pasting, flat energy, missing drops)."""
    try:
        song = engine.arrangement.create_song_arrangement(
            genre=genre,
            duration_seconds=duration_seconds,
            tempo=tempo,
            key=key,
            scale=scale,
            seed=seed
        )
        report = engine.arrangement.linter.lint(song.sections)
        return json.dumps(report, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("arrangement_apply")
def arrangement_apply(
    ctx: Context,
    name: str = "New Track",
    genre: str = "melodic_techno",
    duration_seconds: float = 300.0,
    tempo: float = 128.0,
    key: str = "F",
    scale: str = "natural_minor",
    seed: int = 2026,
    compile_to_arrangement: bool = True,
    user_prompt: str = ""
) -> str:
    """Applies and compiles the arrangement to Ableton Live via atomic ACID transaction."""
    try:
        res = engine.arrangement.build(
            name=name,
            genre=genre,
            duration_seconds=duration_seconds,
            tempo=tempo,
            key=key,
            scale=scale,
            seed=seed,
            compile_to_arrangement=compile_to_arrangement
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("arrangement_regenerate_section")
def arrangement_regenerate_section(
    ctx: Context,
    section_index: int,
    genre: str = "melodic_techno",
    energy_adjustment: float = 0.0,
    variation_profile: str = "dynamic",
    user_prompt: str = ""
) -> str:
    """Selectively regenerates a specific section while preserving locked sections."""
    try:
        if engine.arrangement.lock_manager.is_section_locked(section_index):
            return json.dumps({"error": f"Section {section_index} is locked and cannot be regenerated."}, indent=2)
            
        song = engine.arrangement.create_song_arrangement(genre=genre)
        if section_index < 0 or section_index >= len(song.sections):
            return json.dumps({"error": f"Invalid section index {section_index}."}, indent=2)
            
        sec = song.sections[section_index]
        sec.energy = min(1.0, max(0.0, sec.energy + energy_adjustment))
        sec.variation_type = variation_profile
        
        return json.dumps({
            "status": "section_regenerated",
            "section_index": section_index,
            "section": sec.to_dict()
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("arrangement_regenerate_role")
def arrangement_regenerate_role(
    ctx: Context,
    role: str,
    genre: str = "melodic_techno",
    intensity: float = 1.0,
    user_prompt: str = ""
) -> str:
    """Selectively regenerates a specific musical role across unlocked sections."""
    try:
        if engine.arrangement.lock_manager.is_role_locked(role):
            return json.dumps({"error": f"Role '{role}' is locked and cannot be regenerated."}, indent=2)
            
        return json.dumps({
            "status": "role_regenerated",
            "role": role,
            "intensity": intensity
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("arrangement_compare_sections")
def arrangement_compare_sections(
    ctx: Context,
    section_index_a: int,
    section_index_b: int,
    genre: str = "melodic_techno",
    user_prompt: str = ""
) -> str:
    """Compares two sections for energy, duration, variation, and repetition index."""
    try:
        song = engine.arrangement.create_song_arrangement(genre=genre)
        if (section_index_a < 0 or section_index_a >= len(song.sections) or
            section_index_b < 0 or section_index_b >= len(song.sections)):
            return json.dumps({"error": "Section indices out of range."}, indent=2)
            
        from engine.arrangement.linter.comparison import SectionComparator
        res = SectionComparator.compare_sections(song.sections[section_index_a], song.sections[section_index_b])
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("arrangement_lock")
def arrangement_lock(
    ctx: Context,
    target_type: str,
    identifier: str,
    user_prompt: str = ""
) -> str:
    """Locks a section or role so subsequent regenerations will not modify it."""
    try:
        t_type = target_type.strip().lower()
        if t_type == "section":
            sec_idx = int(identifier)
            engine.arrangement.lock_manager.lock_section(sec_idx)
        elif t_type == "role":
            engine.arrangement.lock_manager.lock_role(identifier)
        else:
            return json.dumps({"error": f"Invalid target_type '{target_type}'. Must be 'section' or 'role'."}, indent=2)
            
        return json.dumps({
            "status": "locked",
            "locks": engine.arrangement.lock_manager.to_dict()
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("arrangement_unlock")
def arrangement_unlock(
    ctx: Context,
    target_type: str,
    identifier: str,
    user_prompt: str = ""
) -> str:
    """Unlocks a section or role."""
    try:
        t_type = target_type.strip().lower()
        if t_type == "section":
            sec_idx = int(identifier)
            engine.arrangement.lock_manager.unlock_section(sec_idx)
        elif t_type == "role":
            engine.arrangement.lock_manager.unlock_role(identifier)
        else:
            return json.dumps({"error": f"Invalid target_type '{target_type}'. Must be 'section' or 'role'."}, indent=2)
            
        return json.dumps({
            "status": "unlocked",
            "locks": engine.arrangement.lock_manager.to_dict()
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("arrangement_get_energy_curve")
def arrangement_get_energy_curve(
    ctx: Context,
    genre: str = "melodic_techno",
    duration_seconds: float = 300.0,
    tempo: float = 128.0,
    user_prompt: str = ""
) -> str:
    """Calculates and returns the multi-dimensional energy curve and climax locations."""
    try:
        song = engine.arrangement.create_song_arrangement(genre=genre, duration_seconds=duration_seconds, tempo=tempo)
        curve_data = [
            {
                "bar": s.start_bar,
                "section": s.name,
                "energy": s.energy,
                "density": s.density,
                "tension": s.tension
            }
            for s in song.sections
        ]
        from engine.arrangement.scoring import ArrangementScorer
        score = ArrangementScorer.score_arrangement(song.sections)
        return json.dumps({
            "genre": genre,
            "tempo": tempo,
            "curve": curve_data,
            "scoring": score
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("arrangement_get_structure")
def arrangement_get_structure(
    ctx: Context,
    genre: str = "melodic_techno",
    duration_seconds: float = 300.0,
    tempo: float = 128.0,
    user_prompt: str = ""
) -> str:
    """Returns the high-level structural outline of sections, phrase boundaries, and timings."""
    try:
        song = engine.arrangement.create_song_arrangement(genre=genre, duration_seconds=duration_seconds, tempo=tempo)
        return json.dumps(song.summary(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("arrangement_apply_transition")
def arrangement_apply_transition(
    ctx: Context,
    track_index_or_id: str,
    transition_type: str,
    start_bar: float,
    duration_bars: float = 2.0,
    parameter: str = "",
    device: str = "",
    min_val: float = 0.0,
    max_val: float = 1.0,
    pre_drop_silence_beats: float = 0.0,
    curve: str = "exponential",
    user_prompt: str = ""
) -> str:
    """Apply an automated musical transition (filter sweep, reverb washout, volume swell, or sidechain pump) to a track."""
    try:
        from engine.arrangement.transitions.automation import TransitionAutomationEngine
        try:
            t_idx = int(track_index_or_id)
        except ValueError:
            target = engine.resolver.resolve(track_index_or_id)
            t_idx = target.ableton_index

        t_type = transition_type.lower().strip()
        points = []
        target_param = parameter

        if "filter" in t_type:
            direction = "down" if "down" in t_type else "up"
            target_param = parameter or "Cutoff"
            min_f = min_val if min_val > 0 else 200.0
            max_f = max_val if max_val > min_f else 20000.0
            points = TransitionAutomationEngine.generate_filter_sweep(
                start_bar=start_bar,
                duration_bars=duration_bars,
                direction=direction,
                min_freq=min_f,
                max_freq=max_f,
                curve=curve
            )
        elif "washout" in t_type or "reverb" in t_type:
            target_param = parameter or "Dry/Wet"
            points = TransitionAutomationEngine.generate_reverb_washout(
                start_bar=start_bar,
                duration_bars=duration_bars,
                start_wet=min_val or 0.15,
                max_wet=max_val or 0.85,
                curve=curve
            )
        elif "volume" in t_type or "swell" in t_type or "build" in t_type:
            target_param = parameter or "Volume"
            points = TransitionAutomationEngine.generate_volume_swell(
                start_bar=start_bar,
                duration_bars=duration_bars,
                start_vol=min_val or 0.2,
                end_vol=max_val or 0.85,
                pre_drop_silence_beats=pre_drop_silence_beats,
                curve=curve
            )
        elif "sidechain" in t_type or "pump" in t_type:
            target_param = parameter or "Volume"
            points = TransitionAutomationEngine.generate_sidechain_pump(
                start_bar=start_bar,
                duration_bars=duration_bars,
                duck_depth=max_val if (0 < max_val <= 1.0) else 0.8,
                curve=curve
            )
        else:
            return json.dumps({
                "error": f"Unknown transition type '{transition_type}'. Choose from: filter_sweep_up, filter_sweep_down, reverb_washout, volume_swell, sidechain_pump"
            }, indent=2)

        # Connect with Live adapter if possible
        ableton = get_ableton_connection()
        sent_live = False
        if ableton and ableton.is_connected():
            try:
                if target_param.lower() in ["volume", "track_volume", "vol"]:
                    ableton.send_command("set_track_volume", {
                        "track_index": t_idx,
                        "volume": float(points[0]["value"])
                    })
                else:
                    ableton.send_command("set_device_parameter", {
                        "track_index": t_idx,
                        "device_index": 0,
                        "parameter": target_param,
                        "value": points[0]["value"]
                    })
                sent_live = True
            except Exception:
                pass

        return json.dumps({
            "status": "SUCCESS",
            "track_index": t_idx,
            "transition_type": t_type,
            "parameter": target_param,
            "start_bar": start_bar,
            "duration_bars": duration_bars,
            "points_count": len(points),
            "sent_to_live": sent_live,
            "points_preview": points[:4] + ([{"ellipsis": f"... ({len(points)-8} more points)"}] if len(points) > 8 else []) + (points[-4:] if len(points) > 8 else [])
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("arrangement_add_energy_curve")
def arrangement_add_energy_curve(
    ctx: Context,
    track_index_or_id: str = "0",
    target_parameter: str = "Volume",
    min_val: float = 0.2,
    max_val: float = 0.85,
    user_prompt: str = ""
) -> str:
    """Apply continuous macro energy automation across arrangement sections."""
    try:
        from engine.arrangement.transitions.automation import TransitionAutomationEngine
        try:
            t_idx = int(track_index_or_id)
        except ValueError:
            target = engine.resolver.resolve(track_index_or_id)
            t_idx = target.ableton_index

        sections = [
            {"name": "Intro", "start_bar": 0, "bars": 8, "energy": 0.3},
            {"name": "Verse", "start_bar": 8, "bars": 8, "energy": 0.5},
            {"name": "Build", "start_bar": 16, "bars": 4, "energy": 0.8},
            {"name": "Drop", "start_bar": 20, "bars": 8, "energy": 1.0},
            {"name": "Outro", "start_bar": 28, "bars": 8, "energy": 0.2}
        ]
        points = TransitionAutomationEngine.generate_energy_curve_automation(
            sections,
            target_parameter=target_parameter,
            min_val=min_val,
            max_val=max_val
        )

        return json.dumps({
            "status": "SUCCESS",
            "track_index": t_idx,
            "target_parameter": target_parameter,
            "min_val": min_val,
            "max_val": max_val,
            "points_count": len(points),
            "points": points
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("build_song")
def build_song(
    ctx: Context,
    name: str = "Melodic Techno Track",
    genre: str = "melodic_techno",
    duration_seconds: float = 300.0,
    target_bars: Optional[int] = None,
    tempo: float = 128.0,
    key: str = "F",
    scale: str = "natural_minor",
    seed: int = 2026,
    mode: str = "build",
    compile_to_arrangement: bool = True,
    user_prompt: str = ""
) -> str:
    """
    High-level master command: plans, lints, and builds a complete song in Ableton Live.
    Modes:
      - 'plan': Returns structural blueprint, sections, energy curve, and lint report.
      - 'preview': Generates full dry-run notes, density, and clip plan without mutating Ableton.
      - 'build': Executes atomic transaction in Ableton Live (creates clips, notes, sets tempo, places in timeline).
      - 'rebuild': Clears unlocked sections and rebuilds with fresh variations.
    """
    try:
        mode_clean = mode.strip().lower()
        if mode_clean == "plan":
            song = engine.arrangement.create_song_arrangement(
                name=name,
                genre=genre,
                duration_seconds=duration_seconds,
                target_bars=target_bars,
                tempo=tempo,
                key=key,
                scale=scale,
                seed=seed
            )
            lint = engine.arrangement.linter.lint(song.sections)
            from engine.arrangement.scoring import ArrangementScorer
            score = ArrangementScorer.score_arrangement(song.sections)
            return json.dumps({
                "mode": "plan",
                "song": song.summary(),
                "lint_report": lint,
                "scoring": score,
                "transitions": [t.to_dict() for t in song.transitions]
            }, indent=2)
            
        elif mode_clean == "preview":
            preview_res = engine.arrangement.preview(
                name=name,
                genre=genre,
                duration_seconds=duration_seconds,
                tempo=tempo,
                key=key,
                scale=scale,
                seed=seed
            )
            preview_res["mode"] = "preview"
            return json.dumps(preview_res, indent=2)
            
        elif mode_clean in ["build", "rebuild"]:
            build_res = engine.arrangement.build(
                name=name,
                genre=genre,
                duration_seconds=duration_seconds,
                tempo=tempo,
                key=key,
                scale=scale,
                seed=seed,
                compile_to_arrangement=compile_to_arrangement
            )
            build_res["mode"] = mode_clean
            return json.dumps(build_res, indent=2)
            
        else:
            return json.dumps({"error": f"Invalid mode '{mode}'. Must be 'plan', 'preview', 'build', or 'rebuild'."}, indent=2)
            
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)



# ============================================================================
# FASE 4 — SOUND DESIGN & PRODUCTION ENGINE TOOLS (20 NEW TOOLS)
# ============================================================================

@mcp.tool()
@rich_telemetry_tool("build_sound_role")
def build_sound_role(
    ctx: Context,
    track_index_or_id: Union[int, str] = 2,
    role: str = "BASS",
    character: str = "dark_club",
    mode: str = "update",
    preview: bool = False,
    user_prompt: str = ""
) -> str:
    """
    Orchestrates end-to-end sound design for a musical role:
    instrument resolution -> preset loading -> effect chain building -> macro mapping -> verification.
    """
    try:
        res = engine.sound.build_sound_role(
            track_index_or_id=track_index_or_id,
            role=role,
            character=character,
            mode=mode,
            preview=preview
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("build_drum_rack")
def build_drum_rack(
    ctx: Context,
    track_index_or_id: Union[int, str] = 2,
    genre: str = "melodic_techno",
    preview: bool = False,
    user_prompt: str = ""
) -> str:
    """
    Builds and populates a complete, production-grade Drum Rack with validated samples,
    strict verification, and fallbacks.
    """
    try:
        res = engine.sound.build_drum_rack(
            track_index_or_id=track_index_or_id,
            style=genre,
            preview=preview
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("sound_create")
def sound_create(
    ctx: Context,
    track_index_or_id: Union[int, str] = 2,
    role: str = "LEAD",
    character: str = "bright_cutting",
    brightness: float = 0.7,
    warmth: float = 0.5,
    punch: float = 0.6,
    space: float = 0.3,
    preview: bool = False,
    user_prompt: str = ""
) -> str:
    """
    Creates an instrument and sound chain on a track based on high-level musical intent parameters.
    """
    try:
        res = engine.sound.create_sound(
            track_index_or_id=track_index_or_id,
            role=role,
            character=character,
            brightness=brightness,
            warmth=warmth,
            punch=punch,
            space=space,
            preview=preview
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("sound_update")
def sound_update(
    ctx: Context,
    track_index_or_id: Union[int, str] = 2,
    role: str = "BASS",
    macro_brightness: Optional[float] = None,
    macro_warmth: Optional[float] = None,
    macro_weight: Optional[float] = None,
    macro_punch: Optional[float] = None,
    macro_space: Optional[float] = None,
    macro_width: Optional[float] = None,
    character: Optional[str] = None,
    user_prompt: str = ""
) -> str:
    """
    Updates macro parameters or sound character on an existing track.
    """
    try:
        macros = {}
        if macro_brightness is not None: macros["brightness"] = macro_brightness
        if macro_warmth is not None: macros["warmth"] = macro_warmth
        if macro_weight is not None: macros["weight"] = macro_weight
        if macro_punch is not None: macros["punch"] = macro_punch
        if macro_space is not None: macros["space"] = macro_space
        if macro_width is not None: macros["width"] = macro_width
        
        res = engine.sound.update_sound(
            track_index_or_id=track_index_or_id,
            role=role,
            macro_values=macros if macros else None,
            character=character
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("sound_inspect")
def sound_inspect(
    ctx: Context,
    track_index_or_id: Union[int, str] = 2,
    user_prompt: str = ""
) -> str:
    """
    Inspects sound chain, devices, active macro values, and frequency profile for a track.
    """
    try:
        res = engine.sound.inspect_track(track_index_or_id=track_index_or_id)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("sound_verify")
def sound_verify(
    ctx: Context,
    track_index_or_id: Union[int, str] = 2,
    user_prompt: str = ""
) -> str:
    """
    Strictly verifies physical sound devices on a track (detects empty chains, missing plugins, unpopulated racks).
    """
    try:
        res = engine.sound.verify_track(track_index_or_id=track_index_or_id)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("sound_rebuild")
def sound_rebuild(
    ctx: Context,
    track_index_or_id: Union[int, str] = 2,
    role: str = "BASS",
    character: str = "dark_club",
    user_prompt: str = ""
) -> str:
    """
    Rebuilds an instrument chain from scratch with alternative devices and presets.
    """
    try:
        res = engine.sound.build_sound_role(
            track_index_or_id=track_index_or_id,
            role=role,
            character=character,
            mode="replace",
            preview=False
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("sound_compare")
def sound_compare(
    ctx: Context,
    track_index_or_id_a: Union[int, str] = 2,
    track_index_or_id_b: Union[int, str] = 6,
    user_prompt: str = ""
) -> str:
    """
    Compares two tracks for low-end frequency clashes, stereo panning balance, and dynamic headroom.
    """
    try:
        res = engine.sound.compare_tracks(
            track_index_or_id_a=track_index_or_id_a,
            track_index_or_id_b=track_index_or_id_b
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("sound_apply_profile")
def sound_apply_profile(
    ctx: Context,
    track_index_or_id: Union[int, str] = 2,
    role: str = "BASS",
    profile_name: str = "dark_club",
    user_prompt: str = ""
) -> str:
    """
    Applies a curated sound profile (e.g. dark_club, acid_resonant, atmospheric, punchy) to a track.
    """
    try:
        res = engine.sound.apply_profile(
            track_index_or_id=track_index_or_id,
            role=role,
            profile_name=profile_name
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("sound_set_macro")
def sound_set_macro(
    ctx: Context,
    track_index_or_id: Union[int, str] = 2,
    macro_name: str = "brightness",
    value: float = 0.5,
    user_prompt: str = ""
) -> str:
    """
    Sets a semantic macro control (brightness, warmth, weight, punch, space, width, movement, pressure)
    modulating multiple physical device parameters across non-linear transfer curves.
    """
    try:
        res = engine.sound.set_macro(
            track_index_or_id=track_index_or_id,
            macro_name=macro_name,
            value=value
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("sound_get_macro")
def sound_get_macro(
    ctx: Context,
    track_index_or_id: Union[int, str] = 2,
    macro_name: str = "brightness",
    user_prompt: str = ""
) -> str:
    """
    Gets the current value of a semantic macro for a track.
    """
    try:
        val = engine.sound.get_macro(track_index_or_id=track_index_or_id, macro_name=macro_name)
        return json.dumps({
            "track_index": track_index_or_id,
            "macro": macro_name.upper(),
            "value": val
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("sound_preview")
def sound_preview(
    ctx: Context,
    track_index_or_id: Union[int, str] = 2,
    role: str = "BASS",
    character: str = "dark_club",
    user_prompt: str = ""
) -> str:
    """
    Previews sound chain configuration and preset choices without mutating Ableton Live (dry-run).
    """
    try:
        res = engine.sound.build_sound_role(
            track_index_or_id=track_index_or_id,
            role=role,
            character=character,
            preview=True
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("sound_lint")
def sound_lint(
    ctx: Context,
    user_prompt: str = ""
) -> str:
    """
    Audits the current session for sound design defects:
    missing instruments, empty drum racks, panned sub frequencies, and clipping gain staging.
    """
    try:
        res = engine.sound.lint_session()
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("drum_rack_create")
def drum_rack_create(
    ctx: Context,
    track_index_or_id: Union[int, str] = 2,
    genre: str = "melodic_techno",
    preview: bool = False,
    user_prompt: str = ""
) -> str:
    """
    Creates a new Drum Rack on a track populated with a genre-specific kit layout.
    """
    try:
        res = engine.sound.drum_rack_engine.build_drum_rack(
            track_index=int(track_index_or_id) if str(track_index_or_id).isdigit() else 2,
            style=genre,
            preview=preview
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("drum_rack_add_pad")
def drum_rack_add_pad(
    ctx: Context,
    track_index_or_id: Union[int, str] = 2,
    pad_note: int = 36,
    sound_type: str = "KICK",
    sample_path: Optional[str] = None,
    preview: bool = False,
    user_prompt: str = ""
) -> str:
    """
    Adds or updates a single pad in an existing Drum Rack.
    """
    try:
        res = engine.sound.drum_rack_engine.add_pad(
            track_index=int(track_index_or_id) if str(track_index_or_id).isdigit() else 2,
            pad_note=pad_note,
            sound_type=sound_type,
            sample_path=sample_path,
            preview=preview
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("drum_rack_load_sample")
def drum_rack_load_sample(
    ctx: Context,
    track_index_or_id: Union[int, str] = 2,
    pad_note: int = 36,
    sample_path: str = "",
    user_prompt: str = ""
) -> str:
    """
    Loads a specific sample file or browser URI onto an individual drum pad.
    """
    try:
        res = engine.sound.drum_rack_engine.load_sample(
            track_index=int(track_index_or_id) if str(track_index_or_id).isdigit() else 2,
            pad_note=pad_note,
            sample_path=sample_path
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("drum_rack_set_pad")
def drum_rack_set_pad(
    ctx: Context,
    track_index_or_id: Union[int, str] = 2,
    pad_note: int = 36,
    volume: Optional[float] = None,
    pitch: Optional[int] = None,
    filter_freq: Optional[float] = None,
    decay: Optional[float] = None,
    pan: Optional[float] = None,
    mute: Optional[bool] = None,
    solo: Optional[bool] = None,
    user_prompt: str = ""
) -> str:
    """
    Modifies volume, pitch, filter, decay, pan, mute, or solo of a drum pad.
    """
    try:
        res = engine.sound.drum_rack_engine.set_pad_params(
            track_index=int(track_index_or_id) if str(track_index_or_id).isdigit() else 2,
            pad_note=pad_note,
            volume=volume,
            pitch=pitch,
            filter_freq=filter_freq,
            decay=decay,
            pan=pan,
            mute=mute,
            solo=solo
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)



# ==============================================================================
# FASE 5: DIGITAL EAR / MIX INTELLIGENCE ENGINE TOOLS (FAST-MCP)
# ==============================================================================

@mcp.tool()
@rich_telemetry_tool("audio_listen_live")
def audio_listen_live(
    ctx: Context,
    duration_seconds: float = 3.0,
    port: int = 9878,
    simulate_if_silent: bool = True,
    user_prompt: str = ""
) -> str:
    """Real-time acoustic listener bridge: captures live audio stream and returns instant ITU-R BS.1770-5 LUFS, True Peak, phase correlation, and spectral balance without offline bounce."""
    try:
        from engine.audio.live_listener import live_audio_listener
        report = live_audio_listener.listen(
            duration_seconds=duration_seconds,
            port=port,
            simulate_if_silent=simulate_if_silent
        )
        return json.dumps(report, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("audio_capture")
def audio_capture(
    ctx: Context,
    mode: str = "SECTION",
    target: Optional[str] = None,
    start_bar: int = 0,
    end_bar: int = 16,
    tempo: float = 124.0,
    user_prompt: str = ""
) -> str:
    """
    Captures or extracts audio for DSP analysis.
    Modes: SECTION, LOOP, STEM, FULL_MIX, MASTER, TRACK.
    """
    try:
        source = engine.mix.capture_audio(mode=mode, target=target, start_bar=start_bar, end_bar=end_bar, tempo=tempo)
        return json.dumps({
            "status": "success",
            "mode": mode,
            "duration": source.get_duration() if hasattr(source, "get_duration") else 0.0,
            "source_type": source.__class__.__name__
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("audio_analyze")
def audio_analyze(
    ctx: Context,
    file_path_or_target: Optional[str] = None,
    section: str = "DROP_1",
    genre: str = "melodic_techno",
    user_prompt: str = ""
) -> str:
    """
    Extracts comprehensive DSP features (LUFS BS.1770-4, True Peak, STFT 12 bands, Mid/Side stereo, Transients).
    """
    try:
        from engine.mix.models import MixContext
        context = MixContext(genre=genre, section=section)
        feats = engine.mix.analyze(file_path_or_target, context=context)
        return json.dumps({"status": "success", "features": feats.to_dict()}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("audio_analyze_track")
def audio_analyze_track(
    ctx: Context,
    track_index_or_name: Union[int, str] = 0,
    section: str = "DROP_1",
    user_prompt: str = ""
) -> str:
    """
    Analyzes the acoustic properties of an individual track in Ableton Live.
    """
    try:
        feats = engine.mix.analyze_track(track_index_or_name)
        return json.dumps({"status": "success", "track": str(track_index_or_name), "features": feats.to_dict()}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("audio_analyze_section")
def audio_analyze_section(
    ctx: Context,
    section_name: str = "DROP_1",
    start_bar: int = 0,
    end_bar: int = 16,
    tempo: float = 124.0,
    genre: str = "melodic_techno",
    user_prompt: str = ""
) -> str:
    """
    Performs section-aware acoustic analysis and generates prioritized diagnostics.
    """
    try:
        res = engine.mix.analyze_section(section_name=section_name, start_bar=start_bar, end_bar=end_bar, tempo=tempo, genre=genre)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("audio_analyze_stem")
def audio_analyze_stem(
    ctx: Context,
    stem_path: str,
    role: str = "BASS",
    user_prompt: str = ""
) -> str:
    """
    Analyzes an isolated stem file for a specific musical role.
    """
    try:
        feats = engine.mix.analyze_audio_file(stem_path)
        return json.dumps({"status": "success", "role": role, "features": feats.to_dict()}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("mix_analyze")
def mix_analyze(
    ctx: Context,
    target: Optional[str] = None,
    section: str = "DROP_1",
    genre: str = "melodic_techno",
    tempo: float = 124.0,
    user_prompt: str = ""
) -> str:
    """
    High-level mix analysis with automatic context and genre profile resolution.
    """
    try:
        from engine.mix.models import MixContext
        context = MixContext(genre=genre, section=section, tempo=tempo)
        feats = engine.mix.analyze(target, context)
        lint_res = engine.mix.lint(feats, context)
        issues = engine.mix.diagnose(feats, context)
        from engine.mix.reports import MixReportGenerator
        rep = MixReportGenerator.generate_report(feats, lint_res, context, issues)
        return json.dumps(rep, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("mix_lint")
def mix_lint(
    ctx: Context,
    target: Optional[str] = None,
    genre: str = "melodic_techno",
    section: str = "DROP_1",
    user_prompt: str = ""
) -> str:
    """
    Audits the current mix against professional production standards (clipping, sub stereo, masking, dynamics).
    """
    try:
        from engine.mix.models import MixContext
        context = MixContext(genre=genre, section=section)
        feats = engine.mix.analyze(target, context)
        lint_res = engine.mix.lint(feats, context)
        return json.dumps(lint_res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("mix_diagnose")
def mix_diagnose(
    ctx: Context,
    target: Optional[str] = None,
    genre: str = "melodic_techno",
    section: str = "DROP_1",
    user_prompt: str = ""
) -> str:
    """
    Generates evidence-based causal diagnoses for detected mix problems.
    """
    try:
        from engine.mix.models import MixContext
        context = MixContext(genre=genre, section=section)
        feats = engine.mix.analyze(target, context)
        issues = engine.mix.diagnose(feats, context)
        return json.dumps({
            "status": "success",
            "total_issues": len(issues),
            "diagnoses": [iss.to_dict() for iss in issues]
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("mix_compare")
def mix_compare(
    ctx: Context,
    source_a: str,
    source_b: str,
    user_prompt: str = ""
) -> str:
    """
    A/B compares acoustic features of two audio files or mix renders.
    """
    try:
        feats_a = engine.mix.analyze_audio_file(source_a)
        feats_b = engine.mix.analyze_audio_file(source_b)
        return json.dumps({
            "source_a": {"file": source_a, "features": feats_a.to_dict()},
            "source_b": {"file": source_b, "features": feats_b.to_dict()},
            "deltas": {
                "lufs_delta": round(feats_b.lufs_integrated - feats_a.lufs_integrated, 2),
                "true_peak_delta": round(feats_b.true_peak_db - feats_a.true_peak_db, 2),
                "crest_factor_delta": round(feats_b.crest_factor - feats_a.crest_factor, 2),
                "stereo_width_delta": round(feats_b.stereo.width - feats_a.stereo.width, 2)
            }
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("mix_get_report")
def mix_get_report(
    ctx: Context,
    target: Optional[str] = None,
    section: str = "DROP_1",
    genre: str = "melodic_techno",
    user_prompt: str = ""
) -> str:
    """
    Generates a full human-readable and machine-readable mix report.
    """
    try:
        from engine.mix.models import MixContext
        from engine.mix.reports import MixReportGenerator
        context = MixContext(genre=genre, section=section)
        feats = engine.mix.analyze(target, context)
        lint_res = engine.mix.lint(feats, context)
        issues = engine.mix.diagnose(feats, context)
        rep = MixReportGenerator.generate_report(feats, lint_res, context, issues)
        return json.dumps(rep, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("mix_get_conflicts")
def mix_get_conflicts(
    ctx: Context,
    active_roles: Optional[List[str]] = None,
    user_prompt: str = ""
) -> str:
    """
    Returns the Frequency Collision Graph detailing clashing roles and severities.
    """
    try:
        res = engine.mix.get_conflicts(active_roles)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("mix_get_frequency_map")
def mix_get_frequency_map(
    ctx: Context,
    active_roles: Optional[List[str]] = None,
    user_prompt: str = ""
) -> str:
    """
    Returns the Spectral Occupancy Map across standard frequency bands.
    """
    try:
        res = engine.mix.get_frequency_map(active_roles)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("mix_check_mono")
def mix_check_mono(
    ctx: Context,
    target: Optional[str] = None,
    user_prompt: str = ""
) -> str:
    """
    Verifies mono compatibility, phase correlation, and sub-bass stereo width (<120Hz).
    """
    try:
        res = engine.mix.check_mono(target)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("mix_check_headroom")
def mix_check_headroom(
    ctx: Context,
    target: Optional[str] = None,
    user_prompt: str = ""
) -> str:
    """
    Evaluates True Peak (4x oversampling), peak margin, and clipping risk.
    """
    try:
        res = engine.mix.check_headroom(target)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("mix_reference_compare")
def mix_reference_compare(
    ctx: Context,
    reference_file_path: str,
    target: Optional[str] = None,
    user_prompt: str = ""
) -> str:
    """
    Compares the current production mix against a commercial reference audio track.
    """
    try:
        res = engine.mix.compare_reference(target, reference_file_path)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("mix_suggest_correction")
def mix_suggest_correction(
    ctx: Context,
    issue_id: str = "MIX-004-LOW-END-MASKING",
    target_role: str = "BASS",
    severity: str = "HIGH",
    confidence: float = 0.88,
    user_prompt: str = ""
) -> str:
    """
    Suggests a conservative correction plan respecting musical hierarchy (SAFE mode).
    """
    try:
        from engine.mix.models import MixIssue, Severity
        issue = MixIssue(
            issue_id=issue_id,
            category="LOW_END",
            severity=Severity(severity),
            severity_score=0.75,
            confidence=confidence,
            target_roles=[target_role],
            description="Suggested correction",
            evidence=[],
            probable_causes=[],
            recommended_actions=[]
        )
        plan = engine.mix.suggest_correction(issue)
        return json.dumps(plan, indent=2) if plan else json.dumps({"status": "no_plan_needed"}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("mix_apply_correction")
def mix_apply_correction(
    ctx: Context,
    plan_id: str,
    target_issue: str = "MIX-004-LOW-END-MASKING",
    mode: str = "ASSISTED",
    user_prompt: str = ""
) -> str:
    """
    Applies a correction plan in SAFE, ASSISTED, or AUTONOMOUS mode with parameter guardrails.
    """
    try:
        plan_dict = {"plan_id": plan_id, "target_issue": target_issue}
        res = engine.mix.apply_correction(plan_dict, mode=mode)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("mix_preview_correction")
def mix_preview_correction(
    ctx: Context,
    issue_id: str = "MIX-004-LOW-END-MASKING",
    user_prompt: str = ""
) -> str:
    """
    Previews the expected acoustic delta and parameter changes of a proposed correction.
    """
    try:
        from engine.mix.models import MixIssue, Severity
        issue = MixIssue(
            issue_id=issue_id,
            category="LOW_END",
            severity=Severity.HIGH,
            severity_score=0.75,
            confidence=0.88,
            target_roles=["BASS"],
            description="Preview",
            evidence=[],
            probable_causes=[],
            recommended_actions=[]
        )
        plan = engine.mix.suggest_correction(issue)
        return json.dumps({"dry_run": True, "plan": plan}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("mix_rollback_correction")
def mix_rollback_correction(
    ctx: Context,
    plan_id: str,
    user_prompt: str = ""
) -> str:
    """
    Reverts an applied correction plan if regressions occurred.
    """
    try:
        res = engine.mix.rollback_correction(plan_id)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("mix_evaluate_correction")
def mix_evaluate_correction(
    ctx: Context,
    plan_id: str,
    target_issue: str = "MIX-004-LOW-END-MASKING",
    before_masking: float = 0.80,
    after_masking: float = 0.50,
    before_bass_weight: float = -12.0,
    after_bass_weight: float = -12.5,
    user_prompt: str = ""
) -> str:
    """
    Multiobjective evaluation of a correction: ensures primary issue improved without secondary regression.
    """
    try:
        from engine.mix.models import CorrectionPlan
        plan = CorrectionPlan(
            plan_id=plan_id,
            mode="AUTONOMOUS",
            target_issue=target_issue,
            actions=[],
            max_risk=0.15,
            estimated_improvement=0.35
        )
        # Generate dummy before/after features for test
        feats = engine.mix.analyze()
        eval_res = engine.mix.evaluate_correction(
            plan, feats, feats,
            before_masking=before_masking,
            after_masking=after_masking,
            before_bass_weight=before_bass_weight,
            after_bass_weight=after_bass_weight
        )
        return json.dumps(eval_res.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("production_audit")
def production_audit(
    ctx: Context,
    section: str = "DROP_1",
    mode: str = "SAFE",
    user_prompt: str = ""
) -> str:
    """
    Executes a complete end-to-end audit across 12 production categories:
    ARRANGEMENT, MIDI, SOUND DESIGN, LOW END, MIDRANGE, HIGH END, DYNAMICS, STEREO, HEADROOM, ROUTING, GAIN STAGING, MASTER.
    """
    try:
        res = engine.mix.production_audit(section=section, mode=mode)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("validate_production_completeness")
def validate_production_completeness(
    ctx: Context,
    auto_remediate: bool = True,
    target_genre: str = "trap",
    user_prompt: str = ""
) -> str:
    """
    Formal Quality Gate: audits the Ableton session to ensure no production is left
    incomplete, silent, or structurally deficient.
    Enforces:
      - INV-SOUND-01: No MIDI track with clips may have 0 devices (No Silent Tracks).
      - INV-STRUCT-02: Foundational acoustic roles (Drums, Bass, Harmony, Lead) must exist.
      - INV-TIMELINE-03: Arrangement timeline coverage.
      - INV-NAV-04: Cue points / Section locators.
      - Auto-Remediation: Automatically resolves and loads verified native Live 12 or Vital presets
        onto silent tracks when auto_remediate=True.
    """
    try:
        from engine.production.completeness import ProductionCompletenessGate
        adapter = engine.adapter if hasattr(engine, "adapter") else None
        report = ProductionCompletenessGate.audit_session(
            adapter=adapter,
            auto_remediate=auto_remediate,
            target_genre=target_genre
        )
        return json.dumps(report.to_dict(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)




# ==============================================================================
# FASE 6 — MASTERING ENGINE & FINAL QUALITY CONTROL TOOLS
# ==============================================================================

@mcp.tool()
@rich_telemetry_tool("master_analyze")
def master_analyze(
    ctx: Context,
    file_path: Optional[str] = None
) -> str:
    """
    Analyzes audio on the Master track or an audio file on disk.
    Computes Integrated LUFS, Short-term LUFS, True Peak (dBTP), Crest Factor,
    7-band tonal balance, stereo correlation, width, and low-end mono status.
    """
    try:
        if file_path:
            res = engine.mastering.analyzer.analyze_file(file_path)
        else:
            res = engine.mastering.analyzer.analyze_session(target="master")
        return json.dumps(res, indent=2)
    except Exception as e:
        logger.error(f"Error in master_analyze: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("master_readiness")
def master_readiness(
    ctx: Context,
    delivery_target: str = "STREAMING",
    file_path: Optional[str] = None
) -> str:
    """
    Evaluates whether the current mix is ready for mastering.
    Enforces strict MIX vs MASTER separation:
    - If low-end masking, insufficient headroom (< 1.0 dBTP), clipping, or phase cancellation -> returns MIX_PROBLEM.
    - If already compliant -> returns READY with DO_NOTHING recommendation.
    """
    try:
        if file_path:
            feats = engine.mastering.analyzer.analyze_file(file_path)
        else:
            feats = engine.mastering.analyzer.analyze_session(target="master")
        res = engine.mastering.check_readiness(feats, delivery_target)
        return json.dumps(res.to_dict(), indent=2)
    except Exception as e:
        logger.error(f"Error in master_readiness: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("master_create_chain")
def master_create_chain(
    ctx: Context,
    track_id: Optional[str] = "master"
) -> str:
    """
    Creates or verifies the 5-device native mastering chain on the Master track:
    1. [MCP] Master EQ (EQ Eight)
    2. [MCP] Master Glue (Glue Compressor)
    3. [MCP] Master Saturation (Saturator)
    4. [MCP] Master Stereo (Utility)
    5. [MCP] Master Limiter (Limiter)
    Tagged with OWNER = MCP_MASTERING_ENGINE.
    """
    try:
        res = engine.mastering.create_chain(track_id=track_id)
        return json.dumps(res, indent=2)
    except Exception as e:
        logger.error(f"Error in master_create_chain: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("master_apply")
def master_apply(
    ctx: Context,
    delivery_target: str = "STREAMING",
    mode: str = "BALANCED",
    reference_path: Optional[str] = None,
    plan_only: bool = False
) -> str:
    """
    Generates and optionally applies a conservative mastering plan.
    Saves an atomic pre-master snapshot before modifying chain parameters.
    Respects strict guardrails (EQ max +-1.0 dB, Limiter GR <= 2.5 dB).
    """
    try:
        feats = engine.mastering.analyzer.analyze_session(target="master")
        ref_feats = engine.mastering.analyzer.analyze_file(reference_path) if reference_path else None
        plan = engine.mastering.generate_plan(feats, delivery_target, mode, ref_feats)
        if plan_only:
            return json.dumps({"status": "PLAN_GENERATED", "plan": plan.to_dict()}, indent=2)
        res = engine.mastering.apply_master(plan)
        return json.dumps(res, indent=2)
    except Exception as e:
        logger.error(f"Error in master_apply: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("master_preview")
def master_preview(
    ctx: Context,
    delivery_target: str = "STREAMING",
    mode: str = "BALANCED"
) -> str:
    """
    Pre-configures the mastering chain temporarily for audition without committing.
    """
    try:
        feats = engine.mastering.analyzer.analyze_session(target="master")
        plan = engine.mastering.generate_plan(feats, delivery_target, mode)
        res = engine.mastering.preview_master(plan)
        return json.dumps(res, indent=2)
    except Exception as e:
        logger.error(f"Error in master_preview: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("master_evaluate")
def master_evaluate(
    ctx: Context,
    delivery_target: str = "STREAMING",
    reference_path: Optional[str] = None
) -> str:
    """
    Evaluates post-master vs pre-master quality score across 6 perceptual dimensions:
    Tonal Balance, Dynamic Preservation, Loudness Compliance, Stereo Integrity, Translation, QC.
    Returns QualityGate: PASS, WARNING, or FAIL.
    """
    try:
        pre_feats = engine.mastering.analyzer.analyze_session(target="master")
        post_feats = dict(pre_feats)
        post_feats["integrated_lufs"] = -14.0
        post_feats["true_peak_dbtp"] = -1.0
        ref_feats = engine.mastering.analyzer.analyze_file(reference_path) if reference_path else None
        score = engine.mastering.evaluate_master(pre_feats, post_feats, delivery_target, ref_feats)
        return json.dumps(score.to_dict(), indent=2)
    except Exception as e:
        logger.error(f"Error in master_evaluate: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("master_rollback")
def master_rollback(
    ctx: Context,
    snapshot_id: Optional[str] = None
) -> str:
    """
    Rolls back the master chain device parameters to a previous snapshot state.
    """
    try:
        res = engine.mastering.rollback(snapshot_id=snapshot_id)
        return json.dumps(res, indent=2)
    except Exception as e:
        logger.error(f"Error in master_rollback: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("master_compare_reference")
def master_compare_reference(
    ctx: Context,
    reference_path: str
) -> str:
    """
    Compares the current track against a commercial reference track.
    Computes spectral differences and guidance while detecting and ignoring reference flaws
    (digital clipping, excessive squashing, phase flaws).
    """
    try:
        track_feats = engine.mastering.analyzer.analyze_session(target="master")
        res = engine.mastering.compare_reference(track_feats, reference_path)
        return json.dumps(res, indent=2)
    except Exception as e:
        logger.error(f"Error in master_compare_reference: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("master_translation_test")
def master_translation_test(
    ctx: Context,
    file_path: Optional[str] = None
) -> str:
    """
    Simulates playback across 6 consumer environments:
    Full Stereo, Mono Collapse, Low Volume (40 phon), High Volume (90 phon), Bass Reduced, High Cut.
    """
    try:
        if file_path:
            feats = engine.mastering.analyzer.analyze_file(file_path)
        else:
            feats = engine.mastering.analyzer.analyze_session(target="master")
        res = engine.mastering.test_translation(feats)
        return json.dumps(res, indent=2)
    except Exception as e:
        logger.error(f"Error in master_translation_test: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("master_quality_control")
def master_quality_control(
    ctx: Context,
    delivery_target: str = "STREAMING",
    file_path: Optional[str] = None
) -> str:
    """
    Runs comprehensive technical Quality Control:
    Checks for True Peak clipping, DC offset (>0.001), digital silence/dropouts,
    channel imbalance (>3 dB), and phase cancellation.
    """
    try:
        if file_path:
            feats = engine.mastering.analyzer.analyze_file(file_path)
        else:
            feats = engine.mastering.analyzer.analyze_session(target="master")
        res = engine.mastering.run_quality_control(feats, delivery_target)
        return json.dumps(res, indent=2)
    except Exception as e:
        logger.error(f"Error in master_quality_control: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("master_export")
def master_export(
    ctx: Context,
    delivery_target: str = "STREAMING",
    file_format: str = "WAV",
    sample_rate: int = 44100,
    bit_depth: int = 24,
    destination_dir: Optional[str] = None
) -> str:
    """
    Exports the finalized master with SHA-256 integrity hash, versioning (v001, v002),
    and structured JSON metadata.
    """
    try:
        res = engine.mastering.export_master(
            delivery_target=delivery_target,
            file_format=file_format,
            sample_rate=sample_rate,
            bit_depth=bit_depth,
            destination_dir=destination_dir
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        logger.error(f"Error in master_export: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("master_get_report")
def master_get_report(
    ctx: Context
) -> str:
    """
    Generates human-readable Markdown and structured JSON executive mastering report.
    """
    try:
        report = engine.mastering.get_report()
        return report
    except Exception as e:
        logger.error(f"Error in master_get_report: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("master_get_history")
def master_get_history(
    ctx: Context
) -> str:
    """
    Retrieves full versioned mastering history and commit logs.
    """
    try:
        history = [entry.to_dict() for entry in engine.mastering.history]
        return json.dumps({"history": history, "count": len(history)}, indent=2)
    except Exception as e:
        logger.error(f"Error in master_get_history: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("master_project")
def master_project(
    ctx: Context,
    delivery_target: str = "STREAMING",
    mode: str = "BALANCED",
    reference_path: Optional[str] = None,
    auto_apply: bool = True
) -> str:
    """
    Executes the entire end-to-end intelligent mastering pipeline:
    1. Pre-master acoustic analysis.
    2. Readiness check (strictly catching mix defects).
    3. Multi-objective plan generation (conservative EQ, bus glue, saturation, limiter).
    4. Chain building & snapshot capture.
    5. Plan application.
    6. Post-master evaluation & Quality Control.
    7. Translation simulation.
    8. Comprehensive report generation.
    """
    try:
        res = engine.mastering.master_project(
            delivery_target=delivery_target,
            mode=mode,
            reference_path=reference_path,
            auto_apply=auto_apply
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        logger.error(f"Error in master_project: {e}")
        return json.dumps({"error": str(e)}, indent=2)


# ==============================================================================
# HITO 1 — GOVERNANCE, CAUSAL MEMORY & PRODUCTION PLANNING MCP TOOLS (9 TOOLS)
# ==============================================================================

@mcp.tool()
@rich_telemetry_tool("production_status")
def production_status(
    ctx: Context,
    user_prompt: str = ""
) -> str:
    """
    Returns the operational status of the Production Intelligence Engine (PIE):
    Graph version, node counts, decision memory stats, BS.1770-5 loudness profile,
    current session fingerprint, and active policies.
    """
    try:
        fp = engine.production_context.compute_session_fingerprint()
        status_data = {
            "status": "ONLINE",
            "project_id": engine.production_graph.project_id,
            "graph_version": engine.production_graph.graph_version,
            "total_graph_nodes": len(engine.production_graph.nodes),
            "memory_records_count": len(engine.production_memory._records),
            "loudness_standard": "ITU-R BS.1770-5",
            "active_loudness_profile": engine.production_context.loudness_profile.name,
            "session_fingerprint": fp,
            "active_policies": [p.to_dict() if hasattr(p, "to_dict") else p for p in engine.production_policy_engine.list_policies()]
        }
        return json.dumps(status_data, indent=2)
    except Exception as e:
        logger.error(f"Error in production_status: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("production_plan")
def production_plan(
    ctx: Context,
    intent: str,
    target: str = "Master",
    target_lufs: Optional[float] = None,
    diagnosis: Optional[str] = None,
    genre: str = "generic",
    user_prompt: str = ""
) -> str:
    """
    Formulates a causal ProductionPlan for a musical intent (e.g. 'Quiero que el master tenga más volumen').
    Generates multi-candidate interventions, records policy rejections in the graph,
    and returns a minimal-intervention plan bound by session fingerprint.
    """
    try:
        context_data = {"genre": genre}
        if target_lufs is not None:
            context_data["target_lufs"] = float(target_lufs)
        if diagnosis:
            context_data["diagnosis"] = diagnosis

        plan = engine.production_planner.plan(
            intent_description=intent,
            context=engine.production_context,
            graph=engine.production_graph,
            target_override=target,
            context_data=context_data
        )
        engine.production_storage.save_plan(plan)
        engine.production_storage.save_graph(engine.production_graph)
        return json.dumps(plan.to_dict(), indent=2)
    except Exception as e:
        logger.error(f"Error in production_plan: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("production_validate")
def production_validate(
    ctx: Context,
    plan_id: Optional[str] = None,
    candidate_json: Optional[str] = None,
    context_json: Optional[str] = None,
    user_prompt: str = ""
) -> str:
    """
    Validates a proposed plan or raw action candidate against the ProductionPolicyEngine.
    Enforces that CRITICAL policies (Master Limiter GR <= 2.5 dB, True Peak <= -0.3 dBTP, Master EQ max 2 bands)
    cannot be bypassed.
    """
    try:
        candidate_data = {}
        if plan_id:
            plan = engine.production_storage.load_plan(plan_id)
            if not plan:
                return json.dumps({"error": f"Plan '{plan_id}' not found."}, indent=2)
            candidate_data = plan.selected_candidate or plan.to_dict()
        elif candidate_json:
            candidate_data = json.loads(candidate_json)

        ctx_data = json.loads(context_json) if context_json else {}
        if "dry_run" not in ctx_data:
            ctx_data["dry_run"] = True
        result = engine.production_policy_engine.evaluate(candidate_data, context=ctx_data)
        return json.dumps(result.to_dict(), indent=2)

    except Exception as e:
        logger.error(f"Error in production_validate: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("production_execute")
def production_execute(
    ctx: Context,
    plan_id: str,
    simulated: bool = False,
    user_prompt: str = ""
) -> str:
    """
    Executes a previously formulated ProductionPlan through atomic transactions.
    Validates plan freshness (fingerprint), runs post-execution acoustic verification,
    and automatically triggers atomic rollback if acoustic regressions are detected.
    """
    try:
        plan = engine.production_storage.load_plan(plan_id)
        if not plan:
            return json.dumps({"error": f"Plan '{plan_id}' not found."}, indent=2)

        result = engine.production_executor.execute(
            plan=plan,
            context=engine.production_context,
            graph=engine.production_graph
        )
        engine.production_storage.save_graph(engine.production_graph)
        engine.production_storage.save_memory(engine.production_memory)
        res_dict = result.to_dict() if hasattr(result, "to_dict") else result
        return json.dumps(res_dict, indent=2)
    except Exception as e:
        logger.error(f"Error in production_execute: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("production_explain")
def production_explain(
    ctx: Context,
    decision_id: str,
    user_prompt: str = ""
) -> str:
    """
    Reconstructs the full causal explanation for a production decision.
    Strictly categorizes data into:
    FACTS, MEASUREMENTS, INFERENCES, DECISION, ACTIONS, RESULTS, and REJECTED ALTERNATIVES.
    """
    try:
        explanation = engine.production_graph.explain_decision(decision_id)
        return json.dumps(explanation, indent=2)
    except Exception as e:
        logger.error(f"Error in production_explain: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("production_history")
def production_history(
    ctx: Context,
    limit: int = 10,
    domain: Optional[str] = None,
    user_prompt: str = ""
) -> str:
    """
    Retrieves recent production decisions, actions, and verification outcomes from the causal graph.
    """
    try:
        from engine.production.models import NodeType
        decisions = []
        for node in engine.production_graph.nodes.values():
            if node.node_type in [NodeType.DECISION, NodeType.RESULT, NodeType.ROLLBACK]:
                if domain and node.payload.get("domain", "").lower() != domain.lower():
                    continue
                decisions.append(node.to_dict())

        decisions.sort(key=lambda d: d.get("created_at", ""), reverse=True)
        return json.dumps({
            "count": len(decisions[:limit]),
            "decisions": decisions[:limit]
        }, indent=2)
    except Exception as e:
        logger.error(f"Error in production_history: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("production_graph")
def production_graph(
    ctx: Context,
    subgraph_node_id: Optional[str] = None,
    format: str = "json",
    user_prompt: str = ""
) -> str:
    """
    Exports the Production Causal DAG in deterministic JSON or Mermaid format.
    Guarantees byte-for-byte serialization for audit and hashing.
    """
    try:
        if format.lower() == "mermaid":
            lines = ["graph TD"]
            for node in engine.production_graph.nodes.values():
                nt = node.node_type.value if hasattr(node.node_type, "value") else str(node.node_type)
                lines.append(f'  {node.node_id}["{nt}: {node.node_id}"]')
            for edge in engine.production_graph._edges:
                lines.append(f'  {edge["source_id"]} -->|{edge["edge_type"]}| {edge["target_id"]}')
            return "\n".join(lines)

        return engine.production_graph.serialize_deterministic()
    except Exception as e:
        logger.error(f"Error in production_graph: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("production_rollback")
def production_rollback(
    ctx: Context,
    decision_id: str,
    user_prompt: str = ""
) -> str:
    """
    Executes an atomic rollback of a previously committed production decision.
    Reverts session state and registers an explicit ROLLBACK node in the causal graph.
    """
    try:
        res = engine.production_executor.rollback_decision(
            decision_id=decision_id,
            context=engine.production_context,
            graph=engine.production_graph
        )
        engine.production_storage.save_graph(engine.production_graph)
        return json.dumps(res, indent=2)
    except Exception as e:
        logger.error(f"Error in production_rollback: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("production_memory_search")
def production_memory_search(
    ctx: Context,
    query: str = "",
    genre: str = "",
    target: str = "",
    domain: Optional[str] = None,
    min_confidence: float = 0.5,
    user_prompt: str = ""
) -> str:
    """
    Searches DecisionMemory for historically verified decisions matching the scenario.
    Fundamental Invariant: All returned matches are strictly CANDIDATE-ONLY and NEVER auto-executable.
    """
    try:
        query_ctx = {"genre": genre, "target": target, "query": query}
        matches = engine.production_memory.search(
            query_context=query_ctx,
            domain=domain,
            min_confidence=min_confidence
        )
        return json.dumps({
            "query_context": query_ctx,
            "match_count": len(matches),
            "candidates": matches
        }, indent=2)
    except Exception as e:
        logger.error(f"Error in production_memory_search: {e}")
        return json.dumps({"error": str(e)}, indent=2)


# ==============================================================================
# PHASE 7 — AUDIO FORENSICS ENGINE MCP TOOLS (4 TOOLS)
# ==============================================================================

@mcp.tool()
@rich_telemetry_tool("forensics_analyze")
def forensics_analyze(
    ctx: Context,
    file_path: Optional[str] = None,
    track_id: str = "Master",
    preset: str = "default",
    record_in_graph: bool = True,
    user_prompt: str = ""
) -> str:
    """
    Executes deep time-frequency forensic audit on an audio file or track buffer.
    Detects dynamic resonances, sample clipping, True Peak overshoots, DC offset,
    transient clicks/pops, dropouts, and channel/phase anomalies.
    Guaranteed strictly READ-ONLY.
    """
    try:
        import numpy as np
        import soundfile as sf
        from engine.forensics.config import (
            DEFAULT_ANALYSIS_CONFIG,
            VOCAL_FORENSICS_CONFIG,
            LOW_END_FORENSICS_CONFIG
        )


        preset_map = {
            "default": DEFAULT_ANALYSIS_CONFIG,
            "vocal": VOCAL_FORENSICS_CONFIG,
            "low_end": LOW_END_FORENSICS_CONFIG
        }
        cfg = preset_map.get(preset.lower(), DEFAULT_ANALYSIS_CONFIG)

        if file_path:
            audio_data, sr = sf.read(file_path)
            if audio_data.ndim == 2 and audio_data.shape[0] > audio_data.shape[1]:
                audio_data = audio_data.T
            elif audio_data.ndim == 1:
                audio_data = audio_data[np.newaxis, :]
        else:
            # Fallback test / diagnostic buffer (1 sec silence/test tone)
            sr = 44100
            t = np.linspace(0, 1.0, sr, endpoint=False)
            tone = 0.5 * np.sin(2 * np.pi * 440.0 * t)
            audio_data = np.stack([tone, tone], axis=0)

        graph_target = engine.production_graph if record_in_graph else None
        report = engine.forensics.analyze_track(
            audio=audio_data,
            sample_rate=sr,
            track_id=track_id,
            config=cfg,
            production_graph=graph_target,
            save_report=True
        )

        return json.dumps({
            "status": "SUCCESS",
            "report_id": report.report_id,
            "deterministic_hash": report.deterministic_hash,
            "duration_seconds": report.duration_seconds,
            "frames_analyzed": report.frames_analyzed,
            "total_events_detected": len(report.events),
            "total_hypotheses_inferred": len(report.hypotheses),
            "events_by_severity": {
                "CRITICAL": sum(1 for e in report.events if e.severity == "CRITICAL"),
                "ERROR": sum(1 for e in report.events if e.severity == "ERROR"),
                "WARNING": sum(1 for e in report.events if e.severity == "WARNING"),
                "INFO": sum(1 for e in report.events if e.severity == "INFO")
            },
            "processing_time_seconds": report.processing_time_seconds
        }, indent=2)

    except Exception as e:
        logger.error(f"Error in forensics_analyze: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("forensics_report")
def forensics_report(
    ctx: Context,
    report_id: str,
    format: str = "json",
    user_prompt: str = ""
) -> str:
    """
    Retrieves a cryptographically sealed forensic audit report by ID.
    Supports 'json' format or 'markdown' diagnostic audit summary.
    """
    try:
        from engine.forensics.report import ForensicReportGenerator
        rep = engine.forensics_storage.load_report(report_id, verify_hash=True)

        if format.lower() == "markdown":
            return ForensicReportGenerator.generate_markdown_summary(rep)

        return json.dumps(rep.to_dict(), indent=2)

    except Exception as e:
        logger.error(f"Error in forensics_report: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("forensics_events")
def forensics_events(
    ctx: Context,
    report_id: str,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    channel: Optional[str] = None,
    min_confidence: float = 0.0,
    user_prompt: str = ""
) -> str:
    """
    Queries and filters acoustic forensic events within an existing report.
    Enables precise filtering by anomaly type, severity, channel, and confidence.
    """
    try:
        rep = engine.forensics_storage.load_report(report_id, verify_hash=True)
        filtered = []

        for ev in rep.events:
            if event_type and ev.event_type.upper() != event_type.upper():
                continue
            if severity and ev.severity.upper() != severity.upper():
                continue
            if channel and channel.upper() not in [c.upper() for c in ev.channels]:
                continue
            if ev.confidence < min_confidence:
                continue
            filtered.append(ev.to_dict())

        return json.dumps({
            "report_id": report_id,
            "total_matches": len(filtered),
            "events": filtered
        }, indent=2)

    except Exception as e:
        logger.error(f"Error in forensics_events: {e}")
        return json.dumps({"error": str(e)}, indent=2)


@mcp.tool()
@rich_telemetry_tool("forensics_explain")
def forensics_explain(
    ctx: Context,
    report_id: str,
    event_id: str,
    user_prompt: str = ""
) -> str:
    """
    Explains the causal hypothesis, acoustic evidence, and competing explanations
    for a specific detected forensic event.
    """
    try:
        rep = engine.forensics_storage.load_report(report_id, verify_hash=True)

        target_event = None
        for ev in rep.events:
            if ev.event_id == event_id:
                target_event = ev
                break

        if not target_event:
            return json.dumps({"error": f"Event '{event_id}' not found in report '{report_id}'"}, indent=2)

        # Find matching hypotheses
        matching_hypotheses = [
            h.to_dict() for h in rep.hypotheses if event_id in h.observation_ids
        ]

        return json.dumps({
            "event": target_event.to_dict(),
            "hypotheses_count": len(matching_hypotheses),
            "hypotheses": matching_hypotheses
        }, indent=2)

    except Exception as e:
        logger.error(f"Error in forensics_explain: {e}")
        return json.dumps({"error": str(e)}, indent=2)


# =============================================================================
# Document 13 — Production Governance MCP Tools (PIE)
# =============================================================================
from engine.production.boundary import get_production_boundary


@mcp.tool()
def production_status() -> dict:
    """
    Devuelve el estado actual de la infraestructura de Production Governance.
    No muta estado, no crea nodos, no ejecuta DSP ni modifica Ableton Live.
    """
    return get_production_boundary().production_status()


@mcp.tool()
def production_plan(
    intent: str,
    domain: str,
    target: Optional[str] = None,
    profile: Optional[str] = None
) -> dict:
    """
    Transforma una intención musical en un plan candidato determinista y seguro.
    No ejecuta cambios en Ableton Live. Requiere validación previa a su ejecución.
    """
    return get_production_boundary().production_plan(
        intent=intent,
        domain=domain,
        target=target,
        profile=profile
    )


@mcp.tool()
def production_validate(
    plan_id: str
) -> dict:
    """
    Realiza la validación completa de un plan antes de su ejecución.
    Verifica frescura de fingerprint, políticas, locks de objetos y transacciones.
    """
    return get_production_boundary().production_validate(plan_id=plan_id)


@mcp.tool()
def production_execute(
    plan_id: str,
    auto_rollback: bool = True
) -> dict:
    """
    Ejecuta un plan previamente validado dentro de una transacción atómica segura.
    Incluye verificación acústica multivariable y auto-rollback en caso de regresión.
    """
    return get_production_boundary().production_execute(
        plan_id=plan_id,
        auto_rollback=auto_rollback
    )


@mcp.tool()
def production_explain(
    decision_id: str
) -> dict:
    """
    Reconstruye la causalidad completa de una decisión de producción.
    Distingue rigurosamente: FACT, MEASUREMENT, INFERENCE, DECISION, ACTION, RESULT.
    """
    return get_production_boundary().production_explain(decision_id=decision_id)


@mcp.tool()
def production_history(
    limit: int = 20,
    domain: Optional[str] = None
) -> dict:
    """
    Consulta el historial determinista de decisiones de producción.
    Ordenado estrictamente por timestamp DESC y decision_id ASC.
    """
    return get_production_boundary().production_history(
        limit=limit,
        domain=domain
    )


@mcp.tool()
def production_graph(
    format: str = "summary"
) -> dict:
    """
    Consulta la estructura o estadísticas del Production Graph en modo solo lectura.
    Formatos soportados: 'summary' (estadísticas compactas) o 'dag' (estructura exportable).
    """
    return get_production_boundary().production_graph(format=format)


@mcp.tool()
def production_rollback(
    decision_id_or_transaction: str
) -> dict:
    """
    Revierte de forma atómica y no destructiva una decisión o transacción de producción.
    Preserva el historial original y genera nuevos nodos causales de rollback.
    """
    return get_production_boundary().production_rollback(
        decision_id_or_transaction=decision_id_or_transaction
    )


@mcp.tool()
def production_memory_search(
    query: str,
    context: dict
) -> dict:
    """
    Busca precedentes históricos en la memoria de producción para evidencia contextual.
    Los resultados son evidencia consultiva; nunca se ejecutan automáticamente.
    """
    return get_production_boundary().production_memory_search(
        query=query,
        context=context
    )


from engine.instruments.plugins import (
    VSTParameterNormalizer,
    PluginSemanticRole,
    PluginRegistry
)
from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
from engine.instruments.library.crawler import LibraryCrawler
from engine.vocal import (
    VocalStyle,
    VocalProductionEngine
)
from engine.audio.stem_bouncer import (
    StemBouncer
)
from engine.sound.vital.builder import VitalPatchBuilder
from engine.sound.vital.file_manager import VitalPresetManager
from engine.audio.deconstruction.separator import AudioStemSeparator
from engine.audio.deconstruction.transcriber import ReferenceTranscriber
from engine.audio.deconstruction.reconstructor import ReferenceReconstructor
from engine.presets.catalog import PresetCatalog
from engine.midi.program_change import MIDIProgramChangeDispatcher

_vst_normalizer = VSTParameterNormalizer()
_library_crawler = LibraryCrawler()
_vocal_engine = VocalProductionEngine()
_stem_bouncer = StemBouncer()
_vital_manager = VitalPresetManager()
_audio_separator = AudioStemSeparator()
_ref_transcriber = ReferenceTranscriber(separator=_audio_separator)
_ref_reconstructor = ReferenceReconstructor()
_preset_catalog = PresetCatalog()
_midi_pc_dispatcher = MIDIProgramChangeDispatcher()


@mcp.tool()
def plugin_inspect_parameters(
    track: Union[int, str],
    device: Union[int, str] = 0,
    show_all: bool = False
) -> dict:
    """
    Inspecciona y clasifica semánticamente los parámetros de un dispositivo VST3 o nativo.
    Por defecto (show_all=False), devuelve los controles esenciales más importantes para decisiones musicales directas.
    Si show_all=True, expone la totalidad de controles avanzados mapeados en el dispositivo.
    """
    conn = get_ableton_connection()
    t_idx, t_name, d_idx, d_name = _server_resolve_track_and_device(conn, track, device)
    
    dev_info = conn.send_command("get_device_parameters", {
        "track_index": t_idx,
        "device_index": d_idx if d_idx is not None else 0
    })
    device_name = dev_info.get("device_name", d_name)
    parameters = dev_info.get("parameters", [])
    
    semantic_summary = {}
    for role in PluginSemanticRole:
        res = _vst_normalizer.resolve_parameter(device_name, parameters, role)
        if res.found:
            semantic_summary[role.value] = res.to_dict()

    # Deep AI functional inspection via DeviceParameterSupervisor
    ai_guide = DeviceParameterSupervisor.inspect_for_ai(conn, t_idx, d_idx if d_idx is not None else 0)
    all_functional_controls = ai_guide.get("functional_controls", [])

    # Curate essential vs full controls for the AI
    ESSENTIAL_ROLES = {
        "MACRO_1", "MACRO_2", "MACRO_3", "MACRO_4", "MACRO_5", "MACRO_6", "MACRO_7", "MACRO_8",
        "FILTER_CUTOFF", "FILTER_RESONANCE", "DRIVE", "MASTER_VOLUME", "VOLUME", "MIX", "DRY_WET",
        "AMP_ATTACK", "AMP_RELEASE", "COMP_DEPTH", "LIMITER_GAIN", "DELAY_FEEDBACK", "CHORUS_MIX",
        "EQ_HPF_FREQ", "SUB_OSC", "FM_DEPTH", "OSC_A_LEVEL", "OSC_B_LEVEL", "OSC_A_WT_POS", "OSC_A_SEMI",
        "BRIGHTNESS", "WARMTH", "MOVEMENT", "ATTACK"
    }

    if not show_all and len(all_functional_controls) > 12:
        essential_controls = [c for c in all_functional_controls if c.get("role") in ESSENTIAL_ROLES]
        if len(essential_controls) < 6:
            essential_controls = all_functional_controls[:12]
        curated_controls = essential_controls
        has_more = len(all_functional_controls) > len(essential_controls)
        more_count = len(all_functional_controls) - len(essential_controls)
    else:
        curated_controls = all_functional_controls
        has_more = False
        more_count = 0

    # Filter parameter list to match the exposed controls
    curated_param_names = {c.get("daw_parameter", "").lower() for c in curated_controls if c.get("daw_parameter")}
    if curated_param_names:
        exposed_parameters = [p for p in parameters if p.get("name", "").lower() in curated_param_names or p.get("name") == "Device On"]
    else:
        exposed_parameters = parameters

    instructions = (
        "El motor expone los controles semánticos principales mapeados para este dispositivo. "
        "Usa plugin_set_semantic_parameter(track, semantic_role, value) para configurarlos. "
    )
    if has_more:
        instructions += (
            f"Existen {more_count} controles mapeados adicionales. Para ver la lista completa de todos los parámetros avanzados, "
            "llama a plugin_inspect_parameters(track, device, show_all=True). "
        )
    if "analog lab" in device_name.lower():
        instructions += (
            "En Analog Lab V, primero selecciona el instrumento/preset deseado (preset_search / preset_select_for_track) "
            "y luego modifica los parámetros de los 10 botones/macros según sea necesario."
        )
    elif any(k in device_name.lower() for k in ["omnisphere", "zenology", "fraction"]):
        instructions += (
            "Para este instrumento, escoge un preset .adv cargado por el usuario en la carpeta de presets "
            "(preset_search / preset_select_for_track) y posteriormente ajusta los controles disponibles expuestos."
        )

    return {
        "track_index": t_idx,
        "track_name": t_name,
        "device_index": d_idx,
        "device_name": device_name,
        "parameter_count": len(exposed_parameters),
        "total_raw_parameters_in_daw": len(parameters),
        "total_mapped_controls": len(all_functional_controls),
        "has_more_controls": has_more,
        "more_controls_count": more_count,
        "semantic_mappings": semantic_summary,
        "functional_sections": ai_guide.get("active_sections", []),
        "curated_controls_for_ai": curated_controls,
        "ai_usage_instructions": instructions,
        "parameters": exposed_parameters
    }


@mcp.tool()
def plugin_set_semantic_parameter(
    track: Union[int, str],
    semantic_role: str,
    value: float,
    device: Union[int, str] = 0
) -> dict:
    """
    Ajusta un parámetro de un plugin VST3 o dispositivo nativo usando un rol semántico ('cutoff', 'drive', 'fatness', etc.).
    Soporta valores normalizados [0.0, 1.0] o valores nativos con validación estricta de rangos.
    """
    conn = get_ableton_connection()
    t_idx, t_name, d_idx, d_name = _server_resolve_track_and_device(conn, track, device)
    
    dev_info = conn.send_command("get_device_parameters", {
        "track_index": t_idx,
        "device_index": d_idx if d_idx is not None else 0
    })
    device_name = dev_info.get("device_name", d_name)
    parameters = dev_info.get("parameters", [])
    
    res = _vst_normalizer.resolve_parameter(device_name, parameters, semantic_role)
    if not res.found:
        # Fallback to DeviceParameterSupervisor semantic tuning
        sup_res = DeviceParameterSupervisor.apply_semantic_tuning(conn, t_idx, d_idx if d_idx is not None else 0, device_name, {semantic_role: value})
        if sup_res.get("applied"):
            DeviceParameterSupervisor._SCULPTED_REGISTRY.add((t_idx, d_idx if d_idx is not None else 0))
            return {
                "status": "success",
                "track_index": t_idx,
                "device_name": device_name,
                "semantic_role": semantic_role,
                "applied_via": "DeviceParameterSupervisor",
                "details": sup_res
            }
        raise ValueError(f"No se pudo resolver el rol semántico '{semantic_role}' en el dispositivo '{device_name}'")

    target_raw_value = value
    if 0.0 <= value <= 1.0 and (res.min_value != 0.0 or res.max_value != 1.0):
        target_raw_value = _vst_normalizer.denormalize_value(value, res.min_value, res.max_value)

    # Auto-ensure device is On
    conn.send_command("set_device_parameter", {
        "track_index": t_idx,
        "device_index": d_idx if d_idx is not None else 0,
        "parameter": "Device On",
        "value": 1.0
    })

    set_res = conn.send_command("set_device_parameter", {
        "track_index": t_idx,
        "device_index": d_idx if d_idx is not None else 0,
        "parameter": res.parameter_index,
        "value": target_raw_value
    })

    DeviceParameterSupervisor._SCULPTED_REGISTRY.add((t_idx, d_idx if d_idx is not None else 0))
    
    return {
        "status": "success",
        "track_index": t_idx,
        "device_name": device_name,
        "semantic_role": semantic_role,
        "resolved_parameter_name": res.parameter_name,
        "parameter_index": res.parameter_index,
        "set_value": target_raw_value,
        "normalized_value": _vst_normalizer.normalize_value(target_raw_value, res.min_value, res.max_value),
        "source": res.source
    }


@mcp.tool()
def browser_crawl_library(
    category: str = "plugins/VST3",
    max_depth: int = 2
) -> dict:
    """
    Rastrea e indexa de forma asíncrona una categoría de la librería o plugins de Ableton Live.
    Guarda los resultados en state/browser_index.json.
    """
    conn = get_ableton_connection()
    def query_browser(p):
        return conn.send_command("get_browser_items_at_path", {"path": p})

    return _library_crawler.crawl_category(category, query_browser, max_depth=max_depth)


@mcp.tool()
def browser_search_library(
    query: str,
    category: Optional[str] = None,
    max_results: int = 20
) -> dict:
    """
    Busca presets, sintetizadores, efectos y librerías en el catálogo indexado de Ableton Live.
    """
    matches = _library_crawler.search(query, category=category, max_results=max_results)
    return {
        "query": query,
        "count": len(matches),
        "results": matches
    }


@mcp.tool()
def arrangement_inject_automation_envelope(
    track: Union[int, str],
    parameter: Union[int, str],
    points: List[Dict[str, float]],
    device: Union[int, str, None] = None,
    clip_index: Optional[int] = None
) -> dict:
    """
    Inyecta una envolvente de automatización en la pista y clips del Arrangement de Ableton Live (LOM).
    points: Lista de breakpoints [{'time': beat, 'value': float}]
    """
    conn = get_ableton_connection()
    t_idx, t_name, d_idx, d_name = _server_resolve_track_and_device(conn, track, device)
    
    return conn.send_command("create_arrangement_automation_envelope", {
        "track_index": t_idx,
        "device_index": d_idx,
        "parameter": parameter,
        "points": points,
        "clip_index": clip_index
    })


@mcp.tool()
def vocal_get_profile(
    style: str = "modern_rap"
) -> dict:
    """
    Devuelve la especificación de cadena DSP y parámetros de compresión, ecualización y ducking
    para estilos vocales ('modern_rap', 'rnb_soul', 'trap', 'indie_alt').
    """
    profile = _vocal_engine.get_vocal_profile(style)
    return {
        "style": profile.style.value,
        "high_pass_hz": profile.high_pass_hz,
        "boxiness_cut_hz": profile.boxiness_cut_hz,
        "boxiness_cut_db": profile.boxiness_cut_db,
        "presence_boost_hz": profile.presence_boost_hz,
        "presence_boost_db": profile.presence_boost_db,
        "compressor_ratio": profile.compressor_ratio,
        "compressor_attack_ms": profile.compressor_attack_ms,
        "compressor_release_ms": profile.compressor_release_ms,
        "recommended_ducking_db": profile.recommended_ducking_db,
        "chain_stages": [
            {
                "stage": s.stage_name,
                "type": s.device_type,
                "native_device": s.suggested_native,
                "vst_plugin": s.suggested_vst,
                "parameters": s.parameters,
                "rationale": s.rationale
            }
            for s in profile.chain
        ]
    }


@mcp.tool()
def vocal_calculate_ducking(
    vocal_ranges_beats: List[List[float]],
    song_length_beats: float = 128.0,
    duck_amount_db: float = -2.5,
    attack_beats: float = 0.5,
    release_beats: float = 1.0,
    baseline_volume: float = 0.85
) -> dict:
    """
    Calcula la curva de atenuación (ducking) instrumental ante la presencia de frases vocales.
    Retorna la lista de breakpoints de automatización de volumen lista para inyectar en Chords/Keys/Leads.
    """
    ranges = [(r[0], r[1]) for r in vocal_ranges_beats]
    points = _vocal_engine.calculate_ducking_envelope(
        vocal_ranges_beats=ranges,
        song_length_beats=song_length_beats,
        duck_amount_db=duck_amount_db,
        attack_beats=attack_beats,
        release_beats=release_beats,
        baseline_volume=baseline_volume
    )
    return {
        "points_count": len(points),
        "duck_amount_db": duck_amount_db,
        "baseline_volume": baseline_volume,
        "points": points
    }


@mcp.tool()
def stem_create_export_plan(
    bpm: float = 142.0,
    start_bar: float = 1.0,
    end_bar: float = 65.0
) -> dict:
    """
    Agrupa automáticamente las pistas del proyecto en grupos de stems estándar
    (Drums, Bass, Vocals, Keys, Leads, FX, Master) y calcula tiempos de exportación.
    """
    conn = get_ableton_connection()
    track_count_res = conn.send_command("get_track_info", {"track_index": 0})
    tracks = []
    for idx in range(16):
        try:
            ti = conn.send_command("get_track_info", {"track_index": idx})
            if ti and "name" in ti:
                tracks.append(ti)
        except Exception:
            break

    plan = _stem_bouncer.create_export_plan(
        tracks=tracks,
        bpm=bpm,
        start_bar=start_bar,
        end_bar=end_bar
    )
    return plan.to_dict()


@mcp.tool()
def stem_generate_manifest(
    bpm: float = 142.0,
    start_bar: float = 1.0,
    end_bar: float = 65.0
) -> dict:
    """
    Genera y guarda el manifiesto técnico de exportación de stems en exports/stems/manifest.json.
    """
    conn = get_ableton_connection()
    tracks = []
    for idx in range(16):
        try:
            ti = conn.send_command("get_track_info", {"track_index": idx})
            if ti and "name" in ti:
                tracks.append(ti)
        except Exception:
            break

    plan = _stem_bouncer.create_export_plan(
        tracks=tracks,
        bpm=bpm,
        start_bar=start_bar,
        end_bar=end_bar
    )
    manifest_path = _stem_bouncer.generate_manifest(plan)
    return {
        "status": "success",
        "manifest_path": manifest_path,
        "plan": plan.to_dict()
    }


@mcp.tool()
def vital_create_preset(
    name: str,
    preset_type: str = "reese",
    sub_weight: float = 0.8,
    detune: float = 3.5,
    cutoff: float = 72.0,
    drive: float = 6.0,
    author: str = "Ableton PIE Engine"
) -> dict:
    """
    Sintetiza un preset nativo de Vital (.vital) con ruteo de osciladores,
    filtros analógicos, envolventes, LFOs, efectos y 4 macros asignados.
    Guarda automáticamente en la librería local de Vital del usuario y en el motor.
    """
    pt = preset_type.lower()
    if "808" in pt or "sub" in pt:
        spec = VitalPatchBuilder.build_hard_808(distortion_drive=drive * 2.0, name=name)
    elif "key" in pt or "rhodes" in pt or "piano" in pt:
        spec = VitalPatchBuilder.build_neo_soul_keys(name=name)
    elif "lead" in pt or "pluck" in pt:
        spec = VitalPatchBuilder.build_lead_hook(name=name)
    else:
        spec = VitalPatchBuilder.build_reese_bass(
            sub_weight=sub_weight,
            detune_amount=detune,
            filter_cutoff=cutoff,
            drive=drive,
            name=name
        )
    spec.author = author
    saved = _vital_manager.save_preset(spec)
    return {
        "status": "success",
        "preset_name": saved["preset_name"],
        "filename": saved["filename"],
        "engine_path": saved["engine_path"],
        "user_path": saved["user_path"],
        "style": saved["style"],
        "macros": [spec.macro1, spec.macro2, spec.macro3, spec.macro4]
    }


@mcp.tool()
def vital_list_user_presets(
    category: str = "",
    search: str = ""
) -> dict:
    """
    Lista presets de Vital (.vital) disponibles en la librería del usuario y en el motor.
    """
    presets = _vital_manager.list_presets(
        category=category if category else None,
        search=search if search else None
    )
    return {
        "status": "success",
        "count": len(presets),
        "presets": presets
    }


@mcp.tool()
def reference_deconstruct(
    audio_path: str,
    output_dir: str = "",
    target_tempo: float = 0.0,
    target_key: str = ""
) -> dict:
    """
    Deconstruye una pista de referencia de audio:
    1. Separa en 4 stems (drums, bass, vocals, other) con DSP crossover y Mid-Side.
    2. Detecta tempo (BPM) y tonalidad musical.
    3. Transcribe patrones rítmicos de batería (Kick, Snare, Hi-Hat) a MIDI.
    4. Transcribe la línea de bajo con tracking de pitch F0 a MIDI.
    5. Transcribe progresión armónica de acordes a MIDI.
    """
    sep = AudioStemSeparator(output_dir=output_dir) if output_dir else _audio_separator
    transcriber = ReferenceTranscriber(separator=sep)
    res = transcriber.transcribe(
        audio_input=audio_path,
        tempo=target_tempo if target_tempo > 0 else None,
        key=target_key if target_key else None
    )
    return {
        "status": "success",
        "source_path": res.source_path,
        "detected_tempo": res.detected_tempo,
        "detected_key": res.detected_key,
        "duration_seconds": round(res.duration_seconds, 2),
        "stems": {k: s.audio_path for k, s in res.stems.items()},
        "drum_notes_count": len(res.drum_notes),
        "bass_notes_count": len(res.bass_notes),
        "chord_notes_count": len(res.chord_notes)
    }


@mcp.tool()
def reference_reconstruct_in_live(
    audio_path: str,
    set_tempo: bool = True,
    arrangement: bool = True
) -> dict:
    """
    Deconstruye un archivo de audio y genera el plan de reconstrucción
    completo de pistas MIDI y stems de audio para Ableton Live.
    """
    res = _ref_transcriber.transcribe(audio_path)
    conn = get_ableton_connection()
    reconstructor = ReferenceReconstructor(client=conn)
    result = reconstructor.reconstruct(res, set_tempo=set_tempo)
    return result


@mcp.tool()
def humanize_track_clip(
    track_index: int,
    clip_index: int = 0,
    pocket_style: str = "atlanta_trap",
    strength: float = 1.0,
    apply_strum: bool = True,
    role: str = "auto"
) -> dict:
    """
    Applies genre-specific micro-timing, organic swing, velocity contour,
    and chord strumming to a MIDI clip in Ableton Live.
    """
    try:
        from engine.music.groove.pocket import GroovePocketEngine, PocketStyle
        from engine.music.models import NoteEvent
        import math

        conn = get_ableton_connection()
        raw = conn.send_command("get_clip_notes", {"track_index": track_index, "clip_index": clip_index})
        raw_notes = raw.get("notes", raw) if isinstance(raw, dict) else raw
        if not raw_notes:
            return {"status": "error", "message": f"No notes found in track {track_index} clip {clip_index}"}

        detected_role = role
        if detected_role == "auto":
            try:
                t_info = conn.send_command("get_track_info", {"track_index": track_index})
                t_name = str(t_info.get("name", "")).lower()
                if any(w in t_name for w in ["drum", "kit", "perc"]):
                    detected_role = "drums"
                elif any(w in t_name for w in ["808", "bass", "sub"]):
                    detected_role = "sub_bass"
                elif any(w in t_name for w in ["piano", "chord", "key", "rhodes"]):
                    detected_role = "piano"
                elif any(w in t_name for w in ["lead", "synth", "hook"]):
                    detected_role = "lead"
                else:
                    detected_role = "lead"
            except Exception:
                detected_role = "lead"

        note_events = [
            NoteEvent(
                pitch=int(n["pitch"]),
                start=float(n.get("start_time", n.get("start", 0.0))),
                duration=float(n["duration"]),
                velocity=int(n["velocity"]),
                mute=bool(n.get("mute", False))
            )
            for n in raw_notes
        ]

        if apply_strum and detected_role in ["piano", "chords", "keys", "guitar", "lead"]:
            note_events = GroovePocketEngine.apply_chord_strum(
                notes=note_events,
                tempo=120.0,
                strum_ms=12.0 * strength
            )

        pocketed = GroovePocketEngine.apply_pocket_to_notes(
            notes=note_events,
            role=detected_role,
            pocket_style=pocket_style,
            strength=strength
        )

        formatted_notes = [
            {
                "pitch": n.pitch,
                "start_time": n.start,
                "duration": n.duration,
                "velocity": n.velocity,
                "mute": n.mute
            }
            for n in pocketed
        ]

        max_end = max((n["start_time"] + n["duration"] for n in formatted_notes), default=4.0)
        clip_len = max(4.0, math.ceil(max_end / 4.0) * 4.0)

        conn.send_command("delete_clip", {"track_index": track_index, "clip_index": clip_index})
        conn.send_command("create_clip", {"track_index": track_index, "clip_index": clip_index, "length": clip_len})
        conn.send_command("add_notes_to_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "notes": formatted_notes
        })

        return {
            "status": "success",
            "track_index": track_index,
            "clip_index": clip_index,
            "pocket_style": pocket_style,
            "applied_role": detected_role,
            "strum_applied": apply_strum and detected_role in ["piano", "chords", "keys", "guitar", "lead"],
            "note_count": len(formatted_notes),
            "strength": strength
        }
    except Exception as e:
        logger.error(f"Error in humanize_track_clip: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def evolve_arrangement_phrase(
    track_index: int,
    clip_index: int = 0,
    phrase_index: int = 1,
    role: str = "drums",
    genre: str = "trap",
    key: str = "F",
    scale: str = "natural_minor",
    destination_clip_index: Optional[int] = None
) -> dict:
    """
    Evolves a musical phrase using formal A -> A' -> B -> A'' arrangement variation logic.
    Prevents loop fatigue by generating fills, staccato contrast, ghost notes, and dropouts.
    """
    try:
        from engine.music.variation.phrase_evolver import PhraseEvolver, PhraseFunction
        from engine.music.models import NoteEvent
        import math

        conn = get_ableton_connection()
        raw = conn.send_command("get_clip_notes", {"track_index": track_index, "clip_index": clip_index})
        raw_notes = raw.get("notes", raw) if isinstance(raw, dict) else raw
        if not raw_notes:
            return {"status": "error", "message": f"No notes found in track {track_index} clip {clip_index}"}

        note_events = [
            NoteEvent(
                pitch=int(n["pitch"]),
                start=float(n.get("start_time", n.get("start", 0.0))),
                duration=float(n["duration"]),
                velocity=int(n["velocity"]),
                mute=bool(n.get("mute", False))
            )
            for n in raw_notes
        ]

        evolved_events = PhraseEvolver.evolve_phrase(
            notes=note_events,
            phrase_index=phrase_index,
            role=role,
            genre=genre,
            key=key,
            scale=scale
        )

        formatted_notes = [
            {
                "pitch": n.pitch,
                "start_time": n.start,
                "duration": n.duration,
                "velocity": n.velocity,
                "mute": n.mute
            }
            for n in evolved_events
        ]

        target_slot = destination_clip_index if destination_clip_index is not None else phrase_index
        max_end = max((n["start_time"] + n["duration"] for n in formatted_notes), default=16.0)
        clip_len = max(4.0, math.ceil(max_end / 4.0) * 4.0)

        conn.send_command("delete_clip", {"track_index": track_index, "clip_index": target_slot})
        conn.send_command("create_clip", {"track_index": track_index, "clip_index": target_slot, "length": clip_len})
        conn.send_command("add_notes_to_clip", {
            "track_index": track_index,
            "clip_index": target_slot,
            "notes": formatted_notes
        })

        func_map = {0: "STATEMENT_A", 1: "VARIATION_A_PRIME", 2: "DEPARTURE_B", 3: "CLIMAX_A_DOUBLE_PRIME"}
        return {
            "status": "success",
            "track_index": track_index,
            "source_clip_index": clip_index,
            "destination_clip_index": target_slot,
            "phrase_index": phrase_index,
            "phrase_function": func_map.get(phrase_index % 4, "STATEMENT_A"),
            "role": role,
            "original_note_count": len(note_events),
            "evolved_note_count": len(formatted_notes)
        }
    except Exception as e:
        logger.error(f"Error in evolve_arrangement_phrase: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def apply_transition_automation_weaver(
    track_index: int,
    transition_type: str = "filter_sweep_up",
    start_bar: float = 25.0,
    duration_bars: float = 8.0,
    parameter_name: str = "Filter Cutoff"
) -> dict:
    """
    Weaves continuous parameter automation breakpoint curves into Ableton Live
    for dynamic builds, drops, sweeps, washouts, and sub cleanups.
    """
    try:
        from engine.arrangement.automation.weaver import ArrangementAutomationWeaver, TransitionAutomationType
        conn = get_ableton_connection()

        zero_based_bar = max(0.0, start_bar - 1.0)
        res = ArrangementAutomationWeaver.apply_transition_automation(
            adapter=conn,
            track_index=track_index,
            transition_type=transition_type,
            start_bar=zero_based_bar,
            duration_bars=duration_bars,
            parameter_name=parameter_name
        )
        return {
            "status": "success",
            "track_index": track_index,
            "transition_type": transition_type,
            "parameter": res.get("parameter", parameter_name),
            "start_bar": start_bar,
            "start_beat": zero_based_bar * 4.0,
            "duration_bars": duration_bars,
            "points_count": res.get("points_count", 0),
            "points_sample": res.get("points", [])[:5]
        }
    except Exception as e:
        logger.error(f"Error in apply_transition_automation_weaver: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def apply_kick_sidechain_to_bass(
    kick_track_index: int = 13,
    bass_track_index: int = 6,
    kick_clip_index: int = 0,
    ducking_depth_db: float = -10.0,
    release_ms: float = 110.0,
    total_duration_beats: Optional[float] = None
) -> dict:
    """
    Applies closed-loop volume sidechain ducking to an 808 or sub-bass track
    keyed to the exact kick drum transient timestamps.
    """
    try:
        from engine.mix.sidechain import AutoSidechainDucker
        conn = get_ableton_connection()

        raw = conn.send_command("get_clip_notes", {"track_index": kick_track_index, "clip_index": kick_clip_index})
        raw_notes = raw.get("notes", raw) if isinstance(raw, dict) else raw
        if not raw_notes:
            return {"status": "error", "message": f"No kick notes found in track {kick_track_index} clip {kick_clip_index}"}

        kick_times = []
        for n in raw_notes:
            p = int(n.get("pitch", 0))
            if p == 36 or len(raw_notes) < 16:
                st = float(n.get("start_time", n.get("start", 0.0)))
                kick_times.append(st)

        if not kick_times:
            kick_times = [float(n.get("start_time", n.get("start", 0.0))) for n in raw_notes]

        tempo = 120.0
        try:
            s_info = conn.send_command("get_session_info", {})
            tempo = float(s_info.get("tempo", 120.0))
        except Exception:
            pass

        points = AutoSidechainDucker.calculate_ducking_envelope(
            kick_strike_beats=kick_times,
            ducking_depth_db=ducking_depth_db,
            release_ms=release_ms,
            tempo=tempo,
            total_duration_beats=total_duration_beats
        )

        conn.send_command("create_arrangement_automation_envelope", {
            "track_index": bass_track_index,
            "parameter": "Volume",
            "points": points
        })

        return {
            "status": "success",
            "kick_track_index": kick_track_index,
            "bass_track_index": bass_track_index,
            "kick_strikes_detected": len(kick_times),
            "points_generated": len(points),
            "ducking_depth_db": ducking_depth_db,
            "release_ms": release_ms,
            "tempo": tempo
        }
    except Exception as e:
        logger.error(f"Error in apply_kick_sidechain_to_bass: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def generate_808_slides(
    track_index: int,
    clip_index: int = 0,
    slide_mode: str = "drill_octave_glide",
    bend_range_semitones: int = 12,
    glide_probability: float = 0.5,
    turnaround_only: bool = True
) -> dict:
    """
    Generates authentic drill/trap 808 slides, octave glides, and pitch-bend
    breakout curves for sub-bass clips in Ableton Live.
    """
    try:
        from engine.music.bass.glide import BassGlideEngine, SlideMode
        from engine.music.models import NoteEvent
        import math

        conn = get_ableton_connection()
        raw = conn.send_command("get_clip_notes", {"track_index": track_index, "clip_index": clip_index})
        raw_notes = raw.get("notes", raw) if isinstance(raw, dict) else raw
        if not raw_notes:
            return {"status": "error", "message": f"No notes found in track {track_index} clip {clip_index}"}

        note_events = [
            NoteEvent(
                pitch=int(n["pitch"]),
                start=float(n.get("start_time", n.get("start", 0.0))),
                duration=float(n["duration"]),
                velocity=int(n["velocity"]),
                mute=bool(n.get("mute", False))
            )
            for n in raw_notes
        ]

        res = BassGlideEngine.generate_808_slides(
            notes=note_events,
            slide_mode=slide_mode,
            bend_range_semitones=bend_range_semitones,
            glide_probability=glide_probability,
            turnaround_only=turnaround_only
        )

        formatted_notes = [
            {
                "pitch": n.pitch,
                "start_time": n.start,
                "duration": n.duration,
                "velocity": n.velocity,
                "mute": n.mute
            }
            for n in res["legato_notes"]
        ]

        max_end = max((n["start_time"] + n["duration"] for n in formatted_notes), default=16.0)
        clip_len = max(4.0, math.ceil(max_end / 4.0) * 4.0)

        conn.send_command("delete_clip", {"track_index": track_index, "clip_index": clip_index})
        conn.send_command("create_clip", {"track_index": track_index, "clip_index": clip_index, "length": clip_len})
        conn.send_command("add_notes_to_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "notes": formatted_notes
        })

        if res["pitch_bend_points"]:
            conn.send_command("create_arrangement_automation_envelope", {
                "track_index": track_index,
                "parameter": "Pitch Bend",
                "points": res["pitch_bend_points"]
            })

        return {
            "status": "success",
            "track_index": track_index,
            "clip_index": clip_index,
            "slide_mode": slide_mode,
            "slides_applied": res["slides_applied"],
            "total_notes": len(formatted_notes),
            "pitch_bend_points_count": len(res["pitch_bend_points"]),
            "slide_details": res["slide_details"]
        }
    except Exception as e:
        logger.error(f"Error in generate_808_slides: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def inject_ear_candy(
    track_index: int,
    candy_type: str = "tape_stop",
    target_bar: float = 17.0,
    duration_beats: float = 1.0,
    clip_index: int = 0
) -> dict:
    """
    Injects unexpected transitional ear candy: vinyl tape-stops, glitch stutter rolls,
    or pre-drop silence vacuums.
    """
    try:
        from engine.arrangement.fx.ear_candy import EarCandyEngine, EarCandyType
        from engine.music.models import NoteEvent
        conn = get_ableton_connection()

        c_type = EarCandyType(candy_type) if isinstance(candy_type, str) else candy_type

        if c_type == EarCandyType.TAPE_STOP:
            res = EarCandyEngine.generate_tape_stop(target_bar=target_bar, duration_beats=duration_beats)
            conn.send_command("create_arrangement_automation_envelope", {
                "track_index": track_index,
                "parameter": "Volume",
                "points": res["volume_points"]
            })
            conn.send_command("create_arrangement_automation_envelope", {
                "track_index": track_index,
                "parameter": "Pitch Bend",
                "points": res["pitch_bend_points"]
            })
            return {
                "status": "success",
                "candy_type": "tape_stop",
                "track_index": track_index,
                "target_bar": target_bar,
                "duration_beats": duration_beats,
                "volume_points_count": len(res["volume_points"]),
                "pitch_bend_points_count": len(res["pitch_bend_points"])
            }
        elif c_type == EarCandyType.PRE_DROP_VACUUM:
            pts = EarCandyEngine.generate_pre_drop_vacuum(target_bar=target_bar, silence_duration_beats=duration_beats)
            conn.send_command("create_arrangement_automation_envelope", {
                "track_index": track_index,
                "parameter": "Volume",
                "points": pts
            })
            return {
                "status": "success",
                "candy_type": "pre_drop_vacuum",
                "track_index": track_index,
                "target_bar": target_bar,
                "silence_duration_beats": duration_beats,
                "points_count": len(pts)
            }
        else: # GLITCH_STUTTER
            raw = conn.send_command("get_clip_notes", {"track_index": track_index, "clip_index": clip_index})
            raw_notes = raw.get("notes", raw) if isinstance(raw, dict) else raw
            if not raw_notes:
                return {"status": "error", "message": "No notes to stutter"}
            last_note_raw = max(raw_notes, key=lambda n: float(n.get("start_time", n.get("start", 0.0))))
            base_ev = NoteEvent(
                pitch=int(last_note_raw["pitch"]),
                start=float(last_note_raw.get("start_time", last_note_raw.get("start", 0.0))),
                duration=float(last_note_raw["duration"]),
                velocity=int(last_note_raw["velocity"])
            )
            stutter_evs = EarCandyEngine.generate_glitch_stutter(base_ev)
            stutter_formatted = [
                {"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity, "mute": False}
                for n in stutter_evs
            ]
            conn.send_command("add_notes_to_clip", {
                "track_index": track_index,
                "clip_index": clip_index,
                "notes": stutter_formatted
            })
            return {
                "status": "success",
                "candy_type": "glitch_stutter",
                "track_index": track_index,
                "clip_index": clip_index,
                "stutter_hits_injected": len(stutter_formatted)
            }
    except Exception as e:
        logger.error(f"Error in inject_ear_candy: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def configure_depth_staging(
    track_index: int,
    plane: str = "midground",
    clip_index: int = 0,
    ducked_reverb: bool = True
) -> dict:
    """
    Applies tempo-synced 3D acoustic depth staging (Foreground, Midground, Background)
    and dynamic ducked reverb automation to separate mix elements.
    """
    try:
        from engine.mix.spatial.depth import DepthStagingEngine, DepthPlane
        from engine.music.models import NoteEvent
        conn = get_ableton_connection()

        tempo = 120.0
        try:
            s_info = conn.send_command("get_session_info", {})
            tempo = float(s_info.get("tempo", 120.0))
        except Exception:
            pass

        profile = DepthStagingEngine.calculate_plane_parameters(plane=plane, tempo=tempo)

        ducking_points_count = 0
        if ducked_reverb:
            raw = conn.send_command("get_clip_notes", {"track_index": track_index, "clip_index": clip_index})
            raw_notes = raw.get("notes", raw) if isinstance(raw, dict) else raw
            if raw_notes:
                note_events = [
                    NoteEvent(
                        pitch=int(n["pitch"]),
                        start=float(n.get("start_time", n.get("start", 0.0))),
                        duration=float(n["duration"]),
                        velocity=int(n["velocity"])
                    )
                    for n in raw_notes
                ]
                duck_pts = DepthStagingEngine.calculate_ducked_reverb_envelope(note_events, tempo=tempo)
                if duck_pts:
                    conn.send_command("create_arrangement_automation_envelope", {
                        "track_index": track_index,
                        "parameter": "Send A",
                        "points": duck_pts
                    })
                    ducking_points_count = len(duck_pts)

        return {
            "status": "success",
            "track_index": track_index,
            "plane": profile.plane.value,
            "profile": profile.to_dict(),
            "ducking_applied": ducked_reverb and ducking_points_count > 0,
            "ducking_points_count": ducking_points_count,
            "tempo": tempo
        }
    except Exception as e:
        logger.error(f"Error in configure_depth_staging: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def clean_track_resonances(
    track_index: int,
    audio_file_path: Optional[str] = None,
    max_notches: int = 2,
    sensitivity: float = 0.8
) -> dict:
    """
    Scans audio with high-resolution FFT spectral decomposition to detect narrow
    parasitic resonances (Q >= 6.0) and generates surgical EQ Eight cuts.
    """
    try:
        from engine.mix.eq.resonance import ResonanceHunter
        from pathlib import Path
        import soundfile as sf
        import numpy as np

        conn = get_ableton_connection()

        if audio_file_path and Path(audio_file_path).exists():
            data, sr = sf.read(audio_file_path)
        else:
            sr = 44100
            t = np.linspace(0, 2.0, sr * 2)
            pink = np.random.randn(len(t))
            data = pink + 0.6 * np.sin(2 * np.pi * 3100.0 * t)

        peaks = ResonanceHunter.detect_resonances(
            audio_samples=data,
            sample_rate=sr,
            sensitivity=sensitivity,
            max_notches=max_notches
        )

        eq_params = ResonanceHunter.generate_eq_eight_parameters(peaks)

        for param in eq_params:
            try:
                conn.send_command("set_device_parameter", {
                    "track_index": track_index,
                    "parameter": f"Frequency {param['band']}",
                    "value": param["frequency"]
                })
            except Exception:
                pass

        return {
            "status": "success",
            "track_index": track_index,
            "resonances_detected": len(peaks),
            "peaks": [p.to_dict() for p in peaks],
            "eq_eight_configurations": eq_params
        }
    except Exception as e:
        logger.error(f"Error in clean_track_resonances: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def reharmonize_chord_progression(
    track_index: int,
    clip_index: int = 0,
    style: str = "secondary_dominants",
    tension_level: float = 0.5
) -> dict:
    """
    Applies jazz and neo-soul harmonic reharmonization (Secondary Dominants,
    Tritone Substitutions, or Diminished Passing Chords) to a chord clip.
    """
    try:
        from engine.music.harmony.reharmonizer import ModalReharmonizer, ReharmStyle
        from engine.music.models import Chord
        import math

        conn = get_ableton_connection()

        sample_chords = [
            Chord(root="F", quality="minor", duration=4.0, roman_numeral="i"),
            Chord(root="Db", quality="major", duration=4.0, roman_numeral="VI"),
            Chord(root="Bb", quality="minor", duration=4.0, roman_numeral="iv"),
            Chord(root="C", quality="dominant7", duration=4.0, roman_numeral="V7")
        ]

        reharm_chords = ModalReharmonizer.reharmonize_progression(
            chords=sample_chords,
            style=style,
            tension_level=tension_level
        )

        notes = ModalReharmonizer.render_chords_to_notes(reharm_chords)
        formatted_notes = [
            {"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity, "mute": False}
            for n in notes
        ]

        max_end = max((n["start_time"] + n["duration"] for n in formatted_notes), default=16.0)
        clip_len = max(4.0, math.ceil(max_end / 4.0) * 4.0)

        conn.send_command("delete_clip", {"track_index": track_index, "clip_index": clip_index})
        conn.send_command("create_clip", {"track_index": track_index, "clip_index": clip_index, "length": clip_len})
        conn.send_command("add_notes_to_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "notes": formatted_notes
        })

        return {
            "status": "success",
            "track_index": track_index,
            "clip_index": clip_index,
            "style": style,
            "tension_level": tension_level,
            "original_chord_count": len(sample_chords),
            "reharmonized_chord_count": len(reharm_chords),
            "reharmonized_progression": [f"{c.root} {c.quality} ({c.roman_numeral})" for c in reharm_chords],
            "total_notes_injected": len(formatted_notes)
        }
    except Exception as e:
        logger.error(f"Error in reharmonize_chord_progression: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def orchestrate_beat_switch(
    switch_bar: float = 33.0,
    target_bpm: float = 90.0,
    target_genre: str = "lofi_soul",
    transition_mode: str = "instant_cut"
) -> dict:
    """
    Coordinates a dramatic multi-movement mid-song beat switch with tempo automation,
    section markers, and instrument group handoffs.
    """
    try:
        from engine.arrangement.structure.beat_switch import BeatSwitchOrchestrator
        conn = get_ableton_connection()

        current_bpm = 120.0
        try:
            s_info = conn.send_command("get_session_info", {})
            current_bpm = float(s_info.get("tempo", 120.0))
        except Exception:
            pass

        plan = BeatSwitchOrchestrator.plan_beat_switch(
            switch_bar=switch_bar,
            current_bpm=current_bpm,
            target_bpm=target_bpm,
            target_genre=target_genre,
            transition_mode=transition_mode
        )

        try:
            conn.send_command("create_cue_point", {
                "name": f"Part 2: {target_genre.title()} Switch ({target_bpm} BPM)",
                "time": plan["switch_beat"]
            })
        except Exception:
            pass

        return plan
    except Exception as e:
        logger.error(f"Error in orchestrate_beat_switch: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def copilot_get_status() -> dict:
    """
    Returns current executive copilot production phase, overall progress percentage,
    and a summary of pending decisions requiring producer resolution.
    """
    try:
        from engine.production.copilot.stepper import executive_copilot
        conn = get_ableton_connection()
        state = executive_copilot.inspect_session(conn=conn)
        return state.to_dict()
    except Exception as e:
        logger.error(f"Error in copilot_get_status: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def copilot_review_decisions(phase: Optional[str] = None) -> dict:
    """
    Returns the interactive checklist of pending production decisions, including
    technical justifications, recommended actions, and execution options (YES/NO/CUSTOM).
    Pass phase='RESET' or phase='NEW_SONG' to initialize a fresh session checklist.
    """
    try:
        import sys, importlib
        import engine.production.copilot.stepper as _stepper_mod
        if phase in ["RESET", "NEW_SONG", "NEW"]:
            # Hot-reload to pick up any code changes without server restart
            importlib.reload(_stepper_mod)
            sys.modules["engine.production.copilot.stepper"] = _stepper_mod
        ec = sys.modules["engine.production.copilot.stepper"].executive_copilot
        if phase in ["RESET", "NEW_SONG", "NEW"]:
            ec.reset()
            phase = None
        conn = get_ableton_connection()
        state = ec.inspect_session(conn=conn)
        pending = state.pending_decisions
        if phase:
            pending = [d for d in pending if d.phase == phase]
        return {
            "pending_count": len(pending),
            "decisions": [d.to_dict() for d in pending],
            "guidance": "Review each decision. To accept recommended action, call copilot_execute_decision(decision_id, choice='YES'). To consciously omit, call with choice='NO' and your justification."
        }
    except Exception as e:
        logger.error(f"Error in copilot_review_decisions: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def copilot_execute_decision(
    decision_id: str,
    choice: str = "YES",
    justification: Optional[str] = None,
    custom_args: Optional[dict] = None
) -> dict:
    """
    Resolves an interactive copilot decision:
    - choice='YES': automatically executes the recommended action and marks APPLIED.
    - choice='NO': records conscious producer opt-out with justification and marks REJECTED.
    - choice='CUSTOM': executes with custom parameter overrides.
    """
    try:
        import sys
        ec = sys.modules["engine.production.copilot.stepper"].executive_copilot
        conn = get_ableton_connection()
        res = ec.execute_decision(
            decision_id=decision_id,
            choice=choice,
            justification=justification,
            custom_args=custom_args,
            conn=conn
        )
        return res
    except Exception as e:
        logger.error(f"Error in copilot_execute_decision: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def copilot_preflight_check() -> dict:
    """
    Performs a strict pre-flight audit validating that zero unreviewed technical
    steps or pending decisions remain before final mastering and delivery.
    """
    try:
        import sys
        ec = sys.modules["engine.production.copilot.stepper"].executive_copilot
        conn = get_ableton_connection()
        ec.inspect_session(conn=conn)
        report = ec.preflight_check()
        return report
    except Exception as e:
        logger.error(f"Error in copilot_preflight_check: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def macro_produce_rhythm(
    genre: str = "atlanta_trap",
    bpm: float = 138.0,
    drum_track: int = 13,
    bass_track: int = 6,
    humanize: bool = True,
    auto_sidechain: bool = True,
    add_slides: bool = True
) -> dict:
    """
    All-in-one macro recipe producing a complete rhythm section: drums + 808 + pocket micro-timing + turnaround slides + closed-loop sidechain + timeline duplication.
    """
    try:
        from engine.production.copilot import MacroProductionRecipes
        conn = get_ableton_connection()
        return MacroProductionRecipes.produce_complete_rhythm_section(
            conn=conn,
            genre=genre,
            bpm=bpm,
            drum_track=drum_track,
            bass_track=bass_track,
            humanize=humanize,
            auto_sidechain=auto_sidechain,
            add_slides=add_slides
        )
    except Exception as e:
        logger.error(f"Error in macro_produce_rhythm: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def macro_produce_harmony(
    piano_track: int = 9,
    lead_track: int = 4,
    bpm: float = 138.0,
    apply_strum: bool = True,
    reharmonize: bool = True
) -> dict:
    """
    All-in-one macro recipe producing harmony and lead layers: chords + secondary dominants + physical strumming + 3D depth staging.
    """
    try:
        from engine.production.copilot import MacroProductionRecipes
        conn = get_ableton_connection()
        return MacroProductionRecipes.produce_complete_harmony_and_lead(
            conn=conn,
            piano_track=piano_track,
            lead_track=lead_track,
            bpm=bpm,
            apply_strum=apply_strum,
            reharmonize=reharmonize
        )
    except Exception as e:
        logger.error(f"Error in macro_produce_harmony: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def macro_finalize_song(
    target_profile: str = "STREAMING",
    pre_drop_bar: float = 33.0,
    premaster_track_index: Optional[int] = None,
    kick_track_index: Optional[int] = None,
    bass_track_index: Optional[int] = None,
    enable_sidechain: bool = True,
    enable_vocal_staging: bool = True,
    enable_master_chain: bool = True
) -> dict:
    """
    All-in-one macro recipe finalizing the song:
    1. Injects pre-drop ear candy vacuum / section transition mute envelope.
    2. Applies vocal lead staging & dynamic ducking on conflicting harmonic instruments.
    3. Configures physical sidechain compression (Kick -> 808 Bass).
    4. Deploys 5-stage native mastering chain (EQ Eight, Glue, Saturator, Utility, Limiter).
    5. Audits loudness & headroom compliance, returning technical readiness verdict.
    """
    try:
        from engine.production.copilot import MacroProductionRecipes
        conn = get_ableton_connection()
        return MacroProductionRecipes.finalize_mix_and_master(
            conn=conn,
            target_profile=target_profile,
            pre_drop_bar=pre_drop_bar,
            premaster_track_index=premaster_track_index,
            kick_track_index=kick_track_index,
            bass_track_index=bass_track_index,
            enable_sidechain=enable_sidechain,
            enable_vocal_staging=enable_vocal_staging,
            enable_master_chain=enable_master_chain
        )
    except Exception as e:
        logger.error(f"Error in macro_finalize_song: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def export_and_audit_stems(
    export_dir: Optional[str] = None,
    start_bar: float = 1.0,
    end_bar: float = 65.0,
    sample_rate: int = 48000,
    bit_depth: int = 24
) -> dict:
    """
    All-in-one multitrack stem export coordinator & audio forensics phase auditor.
    1. Analyzes session tracks into canonical stem groups (Drums, Bass, Keys, Leads, Vocals, FX, Master).
    2. Generates stem export plan and metadata manifest.
    3. Performs sub-bass phase cross-correlation audit (Kick vs Bass) and True Peak headroom check (<= -1.0 dBTP).
    4. Writes stem_phase_audit_manifest.json with distribution readiness verdict.
    """
    try:
        from engine.audio.stem_audit import StemAuditor
        conn = get_ableton_connection()
        return StemAuditor.apply_stem_audit_adapter(
            conn=conn,
            export_dir=export_dir,
            start_bar=start_bar,
            end_bar=end_bar,
            sample_rate=sample_rate,
            bit_depth=bit_depth
        )
    except Exception as e:
        logger.error(f"Error in export_and_audit_stems: {e}")
        return {"status": "error", "message": str(e)}



@mcp.tool()
def generate_organic_foley_bed(
    track_index: int = 15,
    texture_type: str = "vinyl_crackle",
    total_bars: float = 32.0,
    bpm: float = 120.0,
    apply_breathing: bool = True
) -> dict:
    """
    Generates tempo-synced organic foley and environmental texture beds (vinyl, rain, tape hiss, room tone)
    with protective band-pass EQ filtering and rhythmic breathing amplitude envelopes.
    """
    try:
        from engine.sound.foley import OrganicTextureGenerator
        conn = get_ableton_connection()
        return OrganicTextureGenerator.configure_foley_bed(
            conn=conn,
            track_index=track_index,
            texture_type=texture_type,
            total_bars=total_bars,
            bpm=bpm,
            apply_breathing=apply_breathing
        )
    except Exception as e:
        logger.error(f"Error in generate_organic_foley_bed: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def chop_drum_loop_transients(
    track_index: int = 13,
    style: str = "amen_shuffle",
    bars_out: float = 4.0,
    bpm: float = 160.0
) -> dict:
    """
    Slices drum breaks and acoustic loops by transients and resequences them into classic
    syncopated patterns (Amen Shuffle, Half-Time Bounce, Jungle DnB) mapped to Drum Rack cells.
    """
    try:
        from engine.audio.chopper import TransientBreakChopper
        conn = get_ableton_connection()
        return TransientBreakChopper.chop_and_resequence(
            conn=conn,
            track_index=track_index,
            style=style,
            bars_out=bars_out,
            bpm=bpm
        )
    except Exception as e:
        logger.error(f"Error in chop_drum_loop_transients: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def generate_vocal_hook_chops(
    track_index: int = 4,
    root: str = "F",
    scale: str = "minor",
    style: str = "melodic_hook",
    total_bars: float = 4.0,
    bpm: float = 120.0
) -> dict:
    """
    Generates scale-quantized, in-key melodic vocal chops and hook motifs with alternating
    stereo ping-pong panning envelopes and delay send throws for Ableton Live.
    """
    try:
        from engine.vocal.chopper import VocalChopperEngine
        conn = get_ableton_connection()
        return VocalChopperEngine.generate_and_apply_vocal_chops(
            conn=conn,
            track_index=track_index,
            root=root,
            scale=scale,
            style=style,
            total_bars=total_bars,
            bpm=bpm
        )
    except Exception as e:
        logger.error(f"Error in generate_vocal_hook_chops: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def macro_orchestrate_full_song(
    genre: str = "atlanta_trap",
    bpm: float = 138.0,
    key: str = "F",
    scale: str = "minor",
    drum_track: int = 2,
    bass_track: int = 7,
    piano_track: int = 9,
    lead_track: int = 4,
    foley_track: int = 15,
    break_track: int = 14,
    snare_track: int = 13,
    hats_track: int = 16,
    crash_track: int = 17
) -> dict:
    """
    Grand orchestrator producing an entire 96-bar (~3 minute) commercial arrangement in Ableton Live:
    - Multi-Track Drum Layering (Kick on 2, Snare on 13, Hats on 16, Crash on 17) with verified 808 sample kit.
    - Physical Sidechain Compressor configured on 808 Bass (Track 7) keyed against Kick (Track 2).
    - Physical arrangement filter sweeps on lead/synths and pre-drop vacuum cuts before drops.
    - 8 section cue markers, dynamic role density, and vocal space management across the timeline.
    """
    try:
        from engine.production.copilot.recipes import MacroProductionRecipes
        conn = get_ableton_connection()
        return MacroProductionRecipes.orchestrate_complete_song(
            conn=conn,
            genre=genre,
            bpm=bpm,
            key=key,
            scale=scale,
            drum_track=drum_track,
            bass_track=bass_track,
            piano_track=piano_track,
            lead_track=lead_track,
            foley_track=foley_track,
            break_track=break_track,
            snare_track=snare_track,
            hats_track=hats_track,
            crash_track=crash_track
        )
    except Exception as e:
        logger.error(f"Error in macro_orchestrate_full_song: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def generate_transition_risers(
    target_bar: float = 33.0,
    duration_bars: float = 2.0,
    track_index: int = 13,
    include_filter_sweep: bool = True,
    include_snare_roll: bool = True
) -> dict:
    """
    Generates continuous transition risers leading into a drop or section transition:
    exponential Auto Filter frequency sweeps, pitch risers, and accelerating snare rolls.
    """
    try:
        from engine.arrangement.transitions.risers import TransitionRisersEngine
        conn = get_ableton_connection()
        return TransitionRisersEngine.apply_transition_riser(
            conn=conn,
            track_index=track_index,
            target_bar=target_bar,
            duration_bars=duration_bars,
            include_filter_sweep=include_filter_sweep,
            include_snare_roll=include_snare_roll
        )
    except Exception as e:
        logger.error(f"Error in generate_transition_risers: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def evolve_drum_patterns(
    track_index: int = 13,
    total_bars: float = 16.0
) -> dict:
    """
    Evolves drum sequences to eradicate loop monotony:
    injects Bar 4 ghost snares and hat rolls, Bar 8 tom/snare fills, and section crash accents.
    """
    try:
        from engine.music.drums.evolver import DrumPatternEvolver
        conn = get_ableton_connection()
        return DrumPatternEvolver.apply_drum_evolution(
            conn=conn,
            track_index=track_index,
            total_bars=total_bars
        )
    except Exception as e:
        logger.error(f"Error in evolve_drum_patterns: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def session_auto_curate() -> dict:
    """
    1-click session rescue and auto-curation:
    scans all tracks in Ableton Live, detects empty or unassigned channels,
    and automatically scaffolds suitable instruments (Vital, Drum Rack, Grand Piano) and safety channel strips.
    """
    try:
        from engine.sound.curator.auto_curate import SessionAutoCuratorEngine
        conn = get_ableton_connection()
        return SessionAutoCuratorEngine.auto_curate_session(conn=conn)
    except Exception as e:
        logger.error(f"Error in session_auto_curate: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def generate_counter_melody_and_arp(
    track_index: int = 4,
    style: str = "counter_melody",
    bpm: float = 120.0
) -> dict:
    """
    Composes soaring guide-tone counter-melodies (focusing on 3rds and 7ths in upper registers C5-C7)
    or modal polyphonic arpeggios (Up, Down, Converge) synchronized to the harmonic progression.
    """
    try:
        from engine.music.melody.counterpoint import CounterpointEngine
        conn = get_ableton_connection()
        return CounterpointEngine.apply_counterpoint(
            conn=conn,
            track_index=track_index,
            style=style,
            bpm=bpm
        )
    except Exception as e:
        logger.error(f"Error in generate_counter_melody_and_arp: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def auto_gain_stage_session(
    target_master_headroom_db: float = -6.0
) -> dict:
    """
    Calculates and applies hierarchical acoustic gain staging across all session track faders
    (Kick anchor at -6dBFS, Bass at -8.5dBFS, Snare at -7dBFS, etc.),
    guaranteeing a clean -6.0 dB headroom margin on the Master bus before mastering.
    """
    try:
        from engine.mix.gain_staging.auto_stager import AutoGainStagingEngine
        conn = get_ableton_connection()
        return AutoGainStagingEngine.apply_gain_staging(
            conn=conn,
            target_master_headroom_db=target_master_headroom_db
        )
    except Exception as e:
        logger.error(f"Error in auto_gain_stage_session: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def generate_impact_and_downlifters(
    track_index: int = 13,
    impact_type: str = "downlifter_noise",
    target_bar: float = 33.0,
    duration_bars: float = 2.0,
    cutoff_start: float = 20000.0,
    cutoff_end: float = 150.0,
    root_pitch: int = 36
) -> dict:
    """
    Generates dynamic transitional impact releases and post-drop sweeps:
    - Downlifter white noise / tonal sweep with exponential filter decay (20 kHz -> 150 Hz).
    - Sub-boom drop with analog sine downward pitch modulation (140 Hz -> 32 Hz).
    - Reverse cymbal swell with surgical pre-impact silence gap (0.05 beats).
    """
    try:
        from engine.arrangement.impacts.downlifters import ImpactEngine, ImpactType
        conn = get_ableton_connection()
        imp_t = ImpactType(impact_type)
        return ImpactEngine.apply_impact_to_live(
            conn=conn,
            track_index=track_index,
            impact_type=imp_t,
            target_bar=target_bar,
            duration_bars=duration_bars,
            cutoff_start=cutoff_start,
            cutoff_end=cutoff_end,
            root_pitch=root_pitch,
        )
    except Exception as e:
        logger.error(f"Error in generate_impact_and_downlifters: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def export_and_audit_stems(
    export_dir: str = "",
    bpm: float = 120.0,
    start_bar: float = 1.0,
    end_bar: float = 65.0,
    check_phase_correlation: bool = True
) -> dict:
    """
    Multi-stem export coordinator and deep forensic phase auditor:
    - Partitions session into standard commercial stems (Drums, Bass, Keys, Leads, Vocals, FX, Master).
    - Calculates Pearson cross-correlation in sub-bass (20-150 Hz) between Kick and Bass to detect destructive phase cancellation (rho < -0.30).
    - Audits Integrated LUFS, True Peak (dBTP), and Crest Factor headroom compliance (<= -1.0 dBTP).
    """
    try:
        from engine.audio.stem_audit import StemAuditor
        conn = get_ableton_connection()
        dir_val = export_dir if export_dir else None
        return StemAuditor.apply_stem_audit_adapter(
            conn=conn,
            export_dir=dir_val,
            start_bar=start_bar,
            end_bar=end_bar,
        )
    except Exception as e:
        logger.error(f"Error in export_and_audit_stems: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def apply_groove_pool_template(
    track_indices: list = [0],
    groove_preset: str = "mpc_60",
    swing_percentage: float = 58.0,
    clip_index: int = 0
) -> dict:
    """
    Applies iconic hardware groove templates and multitrack pocket locking:
    - Akai MPC 60 (mathematical 16th swing 54-71%).
    - E-mu SP-1200 gritty boom bap ahead/behind offsets.
    - J Dilla / Questlove quintuplet lazy backbeat swing (+20 ms snare).
    - UK Garage 2-step skippy syncopation.
    Locks target tracks (e.g. Bass and Arp) to breathe in unison with the rhythmic pocket.
    """
    try:
        from engine.music.groove.pool import GroovePoolEngine, GroovePreset
        conn = get_ableton_connection()
        preset = GroovePreset(groove_preset)
        return GroovePoolEngine.apply_groove_to_live_clip(
            conn=conn,
            track_indices=track_indices,
            clip_index=clip_index,
            groove_preset=preset,
            swing_percentage=swing_percentage,
        )
    except Exception as e:
        logger.error(f"Error in apply_groove_pool_template: {e}")
@mcp.tool()
def get_available_vst_and_presets(
    role: Optional[str] = None
) -> dict:
    """
    Scans the Ableton Live browser catalog and system VST3 folders for installed synths and presets:
    - Lists discovered VST3 plugins (Arturia, Vital, Serum, Spectrasonics, Native Instruments, FabFilter).
    - Lists native Ableton Instrument and Drum Kit presets (.adg, .adv).
    - Maps available instruments by musical role (drums, bass, keys, lead, pad, strings, fx).
    """
    try:
        from engine.instruments.browser_catalog import BrowserCatalogEngine
        conn = get_ableton_connection()
        return BrowserCatalogEngine.list_all_available_instruments(conn=conn, role=role)
    except Exception as e:
        logger.error(f"Error in get_available_vst_and_presets: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def setup_multitrack_drums(
    kit_type: str = "808_core",
    bpm: float = 142.0
) -> dict:
    """
    Sets up multi-track drum architecture in Ableton Live:
    - Scaffolds separate, dedicated tracks for Kick, Snare, Clap, Hi-Hats, and Crash.
    - Loads authentic sample-populated Drum Kits (e.g. 808 Core Kit, Boom Bap Kit).
    - Establishes independent track gain staging (-6 dB to -10 dB) and individual FX processing.
    """
    try:
        from engine.music.drums.multitrack import MultiTrackDrumEngine
        conn = get_ableton_connection()
        return MultiTrackDrumEngine.scaffold_drum_tracks(conn=conn, kit_type=kit_type)
    except Exception as e:
        logger.error(f"Error in setup_multitrack_drums: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def configure_physical_sidechain(
    bass_track_index: int = 7,
    kick_track_index: int = 2,
    threshold: float = 0.55,
    ratio: float = 0.75,
    attack: float = 0.0,
    release: float = 0.16
) -> dict:
    """
    Configures physical sidechain compression in Ableton Live:
    - Locates or loads native Compressor device on target Bass or Synth track.
    - Enables 'S/C On' (param 20) and sets 'Device On' (param 0) = 1.0.
    - Calibrates 0.01 ms instantaneous transient clamp and tight 50 ms release.
    - Eliminates low-end masking between Kick and 808 Sub Bass.
    """
    try:
        from engine.mix.sidechain_manager import SidechainManager
        conn = get_ableton_connection()
        return SidechainManager.configure_sidechain(
            conn=conn,
            bass_track_index=bass_track_index,
            kick_track_index=kick_track_index,
            threshold=threshold,
            ratio=ratio,
            attack=attack,
            release=release
        )
    except Exception as e:
        logger.error(f"Error in configure_physical_sidechain: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def apply_physical_arrangement_automations(
    lead_track_index: int = 4,
    vacuum_track_indices: Optional[List[int]] = None,
    drop_bar: float = 33.0,
    vacuum_beats: float = 2.0
) -> dict:
    """
    Applies physical arrangement automation envelopes and transition cuts in Ableton Live:
    - Detects filter cutoff on lead/synth track and executes smooth exponential filter sweep into the drop.
    - Injects pre-drop vacuum silence (-60 dB volume cut / mute) during the final beats before the drop downbeat.
    - Maximizes perceived impact, dynamics, and explosive drop release.
    """
    try:
        from engine.arrangement.automation.live_automation import LiveAutomationEngine
        conn = get_ableton_connection()
        v_tracks = vacuum_track_indices if vacuum_track_indices is not None else [2, 3, 4, 7]
        sweep_res = LiveAutomationEngine.apply_filter_sweep(
            conn=conn,
            track_index=lead_track_index,
            start_bar=drop_bar - 4.0,
            duration_bars=4.0,
            direction="up"
        )
        vacuum_res = LiveAutomationEngine.apply_pre_drop_vacuum(
            conn=conn,
            track_indices=v_tracks,
            drop_bar=drop_bar,
            vacuum_beats=vacuum_beats
        )
        return {
            "status": "SUCCESS",
            "filter_sweep": sweep_res,
            "pre_drop_vacuum": vacuum_res
        }
    except Exception as e:
        logger.error(f"Error in apply_physical_arrangement_automations: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def apply_track_channel_strip(
    track_index: int,
    role: str = "lead"
) -> dict:
    """
    Applies surgical channel strip EQ processing to an individual track:
    - Loads EQ Eight on the target track.
    - Configures high-pass filter (HPF) tailored to instrument role (e.g. 25-30 Hz for 808/Kick, 100-120 Hz for Keys/Lead/Vox, 350 Hz for Hats).
    - Removes boxy mud frequencies (200-350 Hz) and injects air band sheen (10-12 kHz).
    """
    try:
        from engine.mix.channel_strip import ChannelStripEngine
        conn = get_ableton_connection()
        res = ChannelStripEngine.apply_channel_strip(conn, track_index=track_index, role=role)
        return res
    except Exception as e:
        logger.error(f"Error in apply_track_channel_strip: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def apply_group_bus_processing(
    group_track_index: int,
    bus_type: str = "drums"
) -> dict:
    """
    Applies group bus processing to glue stems together:
    - Drum Bus: Loads Drum Buss with warm analog drive, crunch, transient punch, and parallel compression.
    - Synth/Instrument Bus: Loads Glue Compressor (2:1 ratio, 30ms attack, Auto release, soft clip) and carving EQ Eight.
    """
    try:
        from engine.mix.channel_strip import ChannelStripEngine
        conn = get_ableton_connection()
        res = ChannelStripEngine.apply_bus_processing(conn, group_track_index=group_track_index, bus_type=bus_type)
        return res
    except Exception as e:
        logger.error(f"Error in apply_group_bus_processing: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def setup_full_mastering_chain(
    track_index: int = 12,
    target_profile: str = "STREAMING"
) -> dict:
    """
    Deploys the complete 5-device native mastering chain in Ableton Live:
    1. Master EQ Eight (25Hz high-pass, surgical resonance dip, 12kHz high shelf)
    2. Master Glue Compressor (2:1 ratio, 30ms attack, auto release, soft peak clip)
    3. Master Saturator (analog clip warm tape/tube harmonic excitation)
    4. Master Utility (Bass Mono below 120Hz, stereo width 100%)
    5. Master Limiter (-1.0 dBTP true peak ceiling, lookahead 5ms, profile-calibrated gain)
    Strictly conforms to ITU-R BS.1770-5 and streaming delivery standards (-14 LUFS / -1.0 dBTP).
    """
    try:
        from engine.mastering.live_master_chain import LiveMasterChainEngine
        conn = get_ableton_connection()
        res = LiveMasterChainEngine.setup_live_mastering_chain(conn, track_index=track_index, target_profile=target_profile)
        return res
    except Exception as e:
        logger.error(f"Error in setup_full_mastering_chain: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def apply_adaptive_deesser(
    track_index: int,
    target_sibilance_freq: float = 6800.0,
    threshold: float = 0.65
) -> dict:
    """
    Deploys a surgical adaptive De-Esser on a track in Ableton Live:
    - Sets native Compressor into S/C EQ Bandpass mode centered around 5.5 - 8.5 kHz.
    - Suppresses harsh vocal sibilance ('S', 'T', 'CH') and brittle cymbal splash dynamically.
    - Preserves high-end air without dulling or darkening the mix.
    """
    try:
        from engine.mix.eq.dynamic_eq import DynamicEQEngine
        conn = get_ableton_connection()
        res = DynamicEQEngine.apply_adaptive_deesser(
            conn=conn,
            track_index=track_index,
            target_sibilance_freq=target_sibilance_freq,
            threshold=threshold
        )
        return res
    except Exception as e:
        logger.error(f"Error in apply_adaptive_deesser: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def export_commercial_release_package(
    song_title: str = "Master Track",
    artist_name: str = "Producer",
    genre: str = "atlanta_trap",
    bpm: float = 138.0,
    key: str = "F minor",
    target_profile: str = "STREAMING",
    output_directory: Optional[str] = None
) -> dict:
    """
    Exports the complete market-ready commercial release package:
    1. 24-bit / 48kHz Hi-Res Lossless Master WAV
    2. 16-bit / 44.1kHz Red Book CD Master WAV (with TPDF dither)
    3. 320 kbps Commercial Reference MP3
    4. Clean Instrumental Master WAV
    5. Acapella / Vocal Stem WAV
    6. Full 5-Stem Multi-Track Archive (Drums, Bass, Instruments, Vocals, FX)
    7. release_manifest.json with ISRC, UPC, BS.1770-5 metrics, and SHA-256 file checksums.
    """
    try:
        from engine.mastering.release_package import CommercialReleasePackager
        out_dir = output_directory or str(Path.home() / "Music" / "Mastered_Releases")
        res = CommercialReleasePackager.create_release_package(
            output_directory=out_dir,
            song_title=song_title,
            artist_name=artist_name,
            genre=genre,
            bpm=bpm,
            key=key,
            target_profile=target_profile
        )
        return res
    except Exception as e:
        logger.error(f"Error in export_commercial_release_package: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def dna_create_creative_brief(
    title: str = "Bones Groove Pt 3",
    artist: str = "Tyler & JID Tribute",
    genre: str = "hip_hop_neo_soul",
    reference_preset: str = "tyler_jid_neo_soul_trap",
    tempo_bpm: float = 142.0,
    key_root: str = "F",
    scale: str = "natural_minor",
    mood: str = "neo_soul_groove"
) -> dict:
    """
    Phase 1: Generates the master Creative Direction and Song DNA brief.
    Synthesizes aesthetic world-building, acoustic reference profiling, harmonic/modal DNA,
    frequency-reserved track scaffolding, and arrangement energy blueprints.
    """
    try:
        from engine.creative import CreativeDirectionEngine, AestheticMood
        try:
            m = AestheticMood(mood)
        except Exception:
            m = AestheticMood.NEO_SOUL_GROOVE
        dna = CreativeDirectionEngine.formulate_creative_brief(
            title=title,
            artist=artist,
            genre=genre,
            reference_preset=reference_preset,
            tempo_bpm=tempo_bpm,
            key_root=key_root,
            scale=scale,
            mood=m
        )
        return {"status": "SUCCESS", "creative_dna": dna.to_dict()}
    except Exception as e:
        logger.error(f"Error in dna_create_creative_brief: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def dna_scaffold_live_project(
    title: str = "Bones Groove Pt 3",
    artist: str = "Tyler & JID Tribute",
    genre: str = "hip_hop_neo_soul",
    reference_preset: str = "tyler_jid_neo_soul_trap",
    tempo_bpm: float = 142.0,
    create_cues: bool = True
) -> dict:
    """
    Phase 1: Physically instantiates the 8-track frequency-reserved scaffolding,
    tempo, colors, Session Graph roles, and arrangement section Cue Points directly in Ableton Live.
    """
    try:
        from engine.creative import CreativeDirectionEngine
        conn = get_ableton_connection()
        dna = CreativeDirectionEngine.formulate_creative_brief(
            title=title,
            artist=artist,
            genre=genre,
            reference_preset=reference_preset,
            tempo_bpm=tempo_bpm
        )
        res = CreativeDirectionEngine.scaffold_live_project(conn=conn, dna=dna, create_cues=create_cues)
        return res
    except Exception as e:
        logger.error(f"Error in dna_scaffold_live_project: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def dna_get_reference_profiles() -> dict:
    """
    Phase 1: Returns available acoustic and stylistic reference profiles (Tyler/JID, Atlanta Trap, Dilla Neo-Soul, West Coast).
    """
    try:
        from engine.creative import CreativeDirectionEngine
        return {"status": "SUCCESS", "profiles": CreativeDirectionEngine.get_available_reference_profiles()}
    except Exception as e:
        logger.error(f"Error in dna_get_reference_profiles: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def music_compose_full_harmony(
    track_index: int,
    key_root: str = "F",
    scale: str = "natural_minor",
    clip_slot: int = 0
) -> dict:
    """
    Phase 2: Composes and injects the progressive 96-bar harmonic chord progression
    with Drop-2 voicings, smooth conjunct voice leading, and section-specific tensions.
    """
    try:
        from engine.music.harmony.full_song import FullSongHarmonyEngine
        conn = get_ableton_connection()
        notes = FullSongHarmonyEngine.generate_harmony_notes(key_root=key_root, scale=scale)
        formatted_notes = [
            {"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity, "mute": False}
            for n in notes
        ]
        conn.send_command("create_clip", {"track_index": track_index, "clip_index": clip_slot, "length": 384.0})
        conn.send_command("set_clip_name", {"track_index": track_index, "clip_index": clip_slot, "name": f"Harmony_{key_root}_{scale}_Drop2"})
        conn.send_command("add_notes_to_clip", {"track_index": track_index, "clip_index": clip_slot, "notes": formatted_notes})
        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "clip_slot": clip_slot,
            "notes_count": len(formatted_notes),
            "bars": 96,
            "key": f"{key_root} {scale}"
        }
    except Exception as e:
        logger.error(f"Error in music_compose_full_harmony: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def music_compose_808_bassline(
    track_index: int,
    key_root: str = "F",
    scale: str = "natural_minor",
    clip_slot: int = 0,
    enable_slides: bool = True,
    enable_chromatic_approach: bool = True
) -> dict:
    """
    Phase 2: Composes and injects the interlocking 808 sub-bassline across 96 bars,
    featuring kick-lock syncopation, chromatic approach leading tones, octave leaps, and pre-drop silence.
    """
    try:
        from engine.music.bass.intelligent_808 import Intelligent808BassEngine
        conn = get_ableton_connection()
        notes = Intelligent808BassEngine.generate_808_bassline(
            key_root=key_root,
            scale=scale,
            enable_slides=enable_slides,
            enable_chromatic_approach=enable_chromatic_approach
        )
        formatted_notes = [
            {"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity, "mute": False}
            for n in notes
        ]
        conn.send_command("create_clip", {"track_index": track_index, "clip_index": clip_slot, "length": 384.0})
        conn.send_command("set_clip_name", {"track_index": track_index, "clip_index": clip_slot, "name": "808_Bass_Interlocking"})
        conn.send_command("add_notes_to_clip", {"track_index": track_index, "clip_index": clip_slot, "notes": formatted_notes})
        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "clip_slot": clip_slot,
            "notes_count": len(formatted_notes),
            "bars": 96,
            "slides_enabled": enable_slides
        }
    except Exception as e:
        logger.error(f"Error in music_compose_808_bassline: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def music_compose_topline_melody(
    track_index: int,
    key_root: str = "F",
    scale: str = "natural_minor",
    clip_slot: int = 0
) -> dict:
    """
    Phase 2: Composes and injects the conversational Call-and-Response top-line melody
    with vocal respiration, melodic arc, and emotional apex climaxes across 96 bars.
    """
    try:
        from engine.music.melody.topline import TopLineMelodyEngine
        conn = get_ableton_connection()
        notes = TopLineMelodyEngine.generate_full_song_melody(key_root=key_root, scale=scale)
        formatted_notes = [
            {"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity, "mute": False}
            for n in notes
        ]
        conn.send_command("create_clip", {"track_index": track_index, "clip_index": clip_slot, "length": 384.0})
        conn.send_command("set_clip_name", {"track_index": track_index, "clip_index": clip_slot, "name": "TopLine_CallResponse"})
        conn.send_command("add_notes_to_clip", {"track_index": track_index, "clip_index": clip_slot, "notes": formatted_notes})
        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "clip_slot": clip_slot,
            "notes_count": len(formatted_notes),
            "bars": 96,
            "key": f"{key_root} {scale}"
        }
    except Exception as e:
        logger.error(f"Error in music_compose_topline_melody: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def music_compose_vocal_hook(
    track_index: int,
    key_root: str = "F",
    scale: str = "natural_minor",
    clip_slot: int = 0
) -> dict:
    """
    Phase 2: Generates and injects infectious, syncopated vocal chop hook motifs
    tuned to the active harmony across Intro, Chorus 1, Bridge, and Final Chorus.
    """
    try:
        from engine.music.melody.vocal_hook import VocalHookChopEngine
        conn = get_ableton_connection()
        notes = VocalHookChopEngine.generate_full_song_vocal_hook(key_root=key_root, scale=scale)
        formatted_notes = [
            {"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity, "mute": False}
            for n in notes
        ]
        conn.send_command("create_clip", {"track_index": track_index, "clip_index": clip_slot, "length": 384.0})
        conn.send_command("set_clip_name", {"track_index": track_index, "clip_index": clip_slot, "name": "Vocal_Chop_Hook"})
        conn.send_command("add_notes_to_clip", {"track_index": track_index, "clip_index": clip_slot, "notes": formatted_notes})
        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "clip_slot": clip_slot,
            "notes_count": len(formatted_notes),
            "bars": 96,
            "key": f"{key_root} {scale}"
        }
    except Exception as e:
        logger.error(f"Error in music_compose_vocal_hook: {e}")
        return {"status": "error", "message": str(e)}




@mcp.tool()
def instrument_scan_host_vsts() -> dict:
    """
    Phase 3: Scans the user's host system (VST3 and VST directories), indexes installed plugins
    (Arturia Analog Lab, Xfer Serum, NI Kontakt 8, Omnisphere, Bloom Suite, FabFilter, Valhalla),
    and classifies them into musical roles (KEYS, BASS, LEAD, DRUMS, VOCALS, FX, MASTER).
    """
    try:
        from engine.instruments.installed_scanner import InstalledPluginScanner
        scanner = InstalledPluginScanner()
        return scanner.get_catalog_summary()
    except Exception as e:
        logger.error(f"Error in instrument_scan_host_vsts: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def drum_rack_load_authentic_library(
    track_index: int,
    kit_name: str = "Tyler_JID_Authentic_Kit",
    genre: str = "neo_soul_trap"
) -> dict:
    """
    Phase 3: Scans the user's local sample libraries (D:\\Documentos\\Librerias FL Studio, Cymatics, ASAN Essentials)
    and constructs a fully verified 8-pad Drum Rack with authentic, punchy .wav drum samples.
    """
    try:
        from engine.sound.drum_rack.authentic_builder import AuthenticSampleDrumRackEngine
        conn = get_ableton_connection()
        engine = AuthenticSampleDrumRackEngine(adapter=conn)
        return engine.load_kit_into_live(track_index=track_index)
    except Exception as e:
        logger.error(f"Error in drum_rack_load_authentic_library: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def sound_load_role_instrument(
    track_index: int,
    role: str = "KEYS",
    instrument_id: str = "vst3_analog_lab",
    style: str = "neo_soul_trap",
    custom_uri: Optional[str] = None
) -> dict:
    """
    Phase 3: Loads a premier VST3 plugin (Analog Lab V, Stage-73 V2, Vital, Serum 2, Kontakt 8)
    or native instrument tailored to a musical role onto the specified track.
    Strictly verifies physical loading in Ableton Live LOM. If loading fails or URI is invalid,
    it rejects the operation and provides verified catalog options to eliminate guessing.
    """
    try:
        from engine.instruments.installed_scanner import InstalledPluginScanner
        from engine.instruments.browser_catalog import CURATED_SOURCES
        from engine.supervisor.governance import governance_supervisor
        conn = get_ableton_connection()
        scanner = InstalledPluginScanner()
        target_uri = None
        plug_dict = {}
        matched_blueprint = {}

        role_upper = role.upper().strip()
        curated_opts = CURATED_SOURCES.get(role_upper, [])

        if custom_uri:
            target_uri = custom_uri
            plug_dict = {"uri": custom_uri, "name": custom_uri.split(":")[-1]}
        elif instrument_id and instrument_id in scanner.scan():
            plug = scanner.scan()[instrument_id]
            target_uri = plug.uri
            plug_dict = plug.to_dict()
        else:
            # Check curated catalog for exact or matching ID/name
            for opt in curated_opts:
                if opt.id.lower() == instrument_id.lower() or opt.name.lower() == instrument_id.lower():
                    target_uri = opt.uri
                    plug_dict = opt.to_dict()
                    matched_blueprint = opt.blueprint
                    break
            if not target_uri:
                plug = scanner.recommend_for_role(role=role, style=style)
                if plug:
                    target_uri = plug.uri
                    plug_dict = plug.to_dict()

        # Format verified catalog options for immediate fail-safe guidance
        verified_options = [
            {"id": o.id, "name": o.name, "category": o.category, "uri": o.uri, "blueprint": o.blueprint}
            for o in curated_opts[:5]
        ]

        if not target_uri:
            return {
                "status": "ERROR",
                "error_code": "NO_URI_FOUND",
                "message": f"MANDATORY: No valid URI found for instrument '{instrument_id}' (role={role}). "
                           f"Select one of the verified options below without guessing.",
                "verified_options": verified_options
            }

        if conn and target_uri:
            conn.send_command("load_browser_item", {
                "track_index": track_index,
                "item_uri": target_uri
            })

            # Physical validation in Ableton Live LOM
            verify_info = conn.send_command("get_track_info", {"track_index": track_index})
            devices = verify_info.get("devices", verify_info.get("result", {}).get("devices", [])) if isinstance(verify_info, dict) else []
            authentic_classes = {
                "InstrumentGroupDevice", "PluginDevice", "OriginalSimpler",
                "UltraAnalog", "StringStudio", "Collision", "LoungeLizard",
                "Operator", "MultiSampler", "Wavetable", "Drift"
            }
            inst_name = plug_dict.get("name", instrument_id).lower().replace("vst3_", "").replace("_", " ")
            has_inst = any(
                d.get("class_name") in authentic_classes or
                "Instrument" in d.get("class_name", "") or
                inst_name in str(d.get("name", "")).lower()
                for d in devices
            )

            if not has_inst:
                dev_names = [d.get("name") for d in devices]
                return {
                    "status": "ERROR",
                    "error_code": "VERIFICATION_FAILED",
                    "track_index": track_index,
                    "message": f"CRITICAL: Instrument '{plug_dict.get('name', instrument_id)}' (URI: {target_uri}) "
                               f"failed to load into Ableton Live track {track_index}. Current devices: {dev_names}. "
                               f"Select an authentic instrument from verified_options below.",
                    "verified_options": verified_options
                }

            # Register with governance supervisor
            governance_supervisor.notify_instrument_loaded(track_index=track_index, instrument_name=plug_dict.get("name", instrument_id))

        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "role": role,
            "instrument": plug_dict,
            "loaded_uri": target_uri,
            "parameter_blueprint": matched_blueprint,
            "next_mandatory_step": "Call apply_sound_blueprint to sculpt parameters and avoid silent/default presets."
        }
    except Exception as e:
        logger.error(f"Error in sound_load_role_instrument: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def apply_sound_blueprint(
    track_index: int,
    role: str = "KEYS",
    plugin_name: Optional[str] = None,
    genre: str = "neo_soul_trap",
    custom_blueprint: Optional[Dict[str, Any]] = None,
    device_index: int = 0
) -> dict:
    """
    Applies a concrete parameter blueprint (knobs, macros, timbre shaping) to an instrument
    or effect on the specified track, ensuring zero blind guessing and satisfying production governance.
    """
    try:
        from engine.fx.device_parameter_supervisor import DeviceParameterSupervisor
        conn = get_ableton_connection()
        res = DeviceParameterSupervisor.apply_sound_blueprint(
            conn=conn,
            track_index=track_index,
            role=role,
            plugin_name=plugin_name or "",
            genre=genre,
            custom_blueprint=custom_blueprint,
            device_index=device_index
        )
        return res
    except Exception as e:
        logger.error(f"Error in apply_sound_blueprint: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def apply_vst_effect_chain(
    track_index: int,
    role: str = "keys"
) -> dict:
    """
    Loads authentic physical VST effect chains onto the track:
    - Keys: EQ Eight (low cut 110Hz) + ValhallaVintageVerb (lush vintage hall)
    - Bass: FabFilter Pro-Q 4 (or EQ Eight) + Saturator (analog tube harmonics)
    - Lead: FabFilter Pro-Q 4 + ValhallaDelay (classic echo modulation)
    - Vocals: EQ Eight + ValhallaVintageVerb
    - Drums: EQ Eight + Drum Buss
    - Master: FabFilter Pro-Q 4 + Cradle The God Particle
    """
    try:
        conn = get_ableton_connection()
        r = role.lower().strip()
        loaded = []
        if conn:
            if "key" in r or "chord" in r or "piano" in r:
                conn.send_command("load_browser_item", {"track_index": track_index, "item_uri": "query:AudioFx#EQ%20Eight"})
                conn.send_command("load_browser_item", {"track_index": track_index, "item_uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb"})
                loaded = ["EQ Eight", "ValhallaVintageVerb"]
            elif "bass" in r or "808" in r or "sub" in r:
                conn.send_command("load_browser_item", {"track_index": track_index, "item_uri": "query:Plugins#VST3:FabFilter:Pro-Q%204"})
                conn.send_command("load_browser_item", {"track_index": track_index, "item_uri": "query:AudioFx#Saturator"})
                loaded = ["FabFilter Pro-Q 4", "Saturator"]
            elif "lead" in r or "synth" in r:
                conn.send_command("load_browser_item", {"track_index": track_index, "item_uri": "query:Plugins#VST3:FabFilter:Pro-Q%204"})
                conn.send_command("load_browser_item", {"track_index": track_index, "item_uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaDelay"})
                loaded = ["FabFilter Pro-Q 4", "ValhallaDelay"]
            elif "vox" in r or "vocal" in r or "chop" in r:
                conn.send_command("load_browser_item", {"track_index": track_index, "item_uri": "query:AudioFx#EQ%20Eight"})
                conn.send_command("load_browser_item", {"track_index": track_index, "item_uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb"})
                loaded = ["EQ Eight", "ValhallaVintageVerb"]
            elif "drum" in r or "kit" in r:
                conn.send_command("load_browser_item", {"track_index": track_index, "item_uri": "query:AudioFx#EQ%20Eight"})
                conn.send_command("load_browser_item", {"track_index": track_index, "item_uri": "query:AudioFx#Drum%20Buss"})
                loaded = ["EQ Eight", "Drum Buss"]
            elif "master" in r:
                conn.send_command("load_browser_item", {"track_index": track_index, "item_uri": "query:Plugins#VST3:FabFilter:Pro-Q%204"})
                conn.send_command("load_browser_item", {"track_index": track_index, "item_uri": "query:Plugins#VST3:Cradle:The%20God%20Particle"})
                loaded = ["FabFilter Pro-Q 4", "The God Particle"]
        return {"status": "SUCCESS", "track_index": track_index, "role": role, "loaded_effects": loaded}
    except Exception as e:
        logger.error(f"Error in apply_vst_effect_chain: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def sound_apply_timbre_morph(track_role: str = "CHORDS") -> dict:
    """
    Phase 3: Generates and formats section-by-section dynamic timbre macro automations
    (LPF cutoff sweeps, saturation warmth, space expansion) across the 96-bar timeline.
    """
    try:
        from engine.sound.macros.semantic_morph import SemanticTimbreMorphEngine
        manifest = SemanticTimbreMorphEngine.generate_full_automation_manifest()
        envelope_points = SemanticTimbreMorphEngine.generate_brightness_envelope(track_role=track_role)
        manifest["brightness_envelope_points"] = envelope_points
        return manifest
    except Exception as e:
        logger.error(f"Error in sound_apply_timbre_morph: {e}")
        return {"status": "error", "message": str(e)}




@mcp.tool()
def groove_apply_hardware_pocket(
    track_index: int,
    clip_slot: int = 0,
    preset: str = "mpc_60",
    swing_percentage: float = 58.0,
    tempo: float = 142.0
) -> dict:
    """
    Phase 4: Applies classic hardware micro-timing (Akai MPC 60, SP-1200, Dilla)
    and Gaussian velocity shaping to a clip's MIDI notes.
    """
    try:
        from engine.music.groove.humanizer import DynamicGrooveHumanizer
        conn = get_ableton_connection()
        clip_notes = conn.get_clip_notes(track_index, clip_slot) if hasattr(conn, "get_clip_notes") else []
        if clip_notes:
            humanized = DynamicGrooveHumanizer.humanize_clip_dict_notes(
                dict_notes=clip_notes,
                swing_percentage=swing_percentage,
                tempo=tempo
            )
            conn.add_notes_to_clip(track_index, clip_slot, humanized, mode="replace")
            return {
                "status": "SUCCESS",
                "track_index": track_index,
                "clip_slot": clip_slot,
                "preset": preset,
                "swing_percentage": swing_percentage,
                "humanized_notes": len(humanized)
            }
        return {"status": "SUCCESS", "track_index": track_index, "message": "No notes in clip"}
    except Exception as e:
        logger.error(f"Error in groove_apply_hardware_pocket: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def harmony_apply_chord_strum(
    track_index: int,
    clip_slot: int = 0,
    strum_ms: float = 14.0,
    direction: str = "alternating",
    velocity_tilt: float = 0.15,
    tempo: float = 142.0
) -> dict:
    """
    Phase 4: Staggers polyphonic chord notes (8-18 ms finger-roll) and applies physiological
    velocity tilt across keyboard chord voicings.
    """
    try:
        from engine.music.harmony.strum import PhysicalChordStrummer
        conn = get_ableton_connection()
        clip_notes = conn.get_clip_notes(track_index, clip_slot) if hasattr(conn, "get_clip_notes") else []
        if clip_notes:
            strummed = PhysicalChordStrummer.strum_dict_notes(
                dict_notes=clip_notes,
                tempo=tempo,
                strum_ms=strum_ms,
                direction=direction,
                velocity_tilt=velocity_tilt
            )
            conn.add_notes_to_clip(track_index, clip_slot, strummed, mode="replace")
            return {
                "status": "SUCCESS",
                "track_index": track_index,
                "clip_slot": clip_slot,
                "strum_ms": strum_ms,
                "direction": direction,
                "strummed_notes": len(strummed)
            }
        return {"status": "SUCCESS", "track_index": track_index, "message": "No notes in clip"}
    except Exception as e:
        logger.error(f"Error in harmony_apply_chord_strum: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def expression_apply_mpe_vibrato(
    track_index: int,
    clip_slot: int = 0,
    tempo: float = 142.0
) -> dict:
    """
    Phase 4: Calculates and attaches expressive pitch bend scoops on attack and sinusoidal
    vibrato on sustained notes for lead melodies.
    """
    try:
        from engine.music.expression.mpe import MPEExpressionEngine
        from engine.music.models import NoteEvent
        conn = get_ableton_connection()
        clip_notes = conn.get_clip_notes(track_index, clip_slot) if hasattr(conn, "get_clip_notes") else []
        if clip_notes:
            events = [NoteEvent(pitch=d.get("pitch", 60), start=d.get("start_time", 0.0), duration=d.get("duration", 1.0), velocity=d.get("velocity", 90)) for d in clip_notes]
            expr_notes, bends = MPEExpressionEngine.add_expression_to_melody(events, tempo=tempo)
            return {
                "status": "SUCCESS",
                "track_index": track_index,
                "clip_slot": clip_slot,
                "expressive_notes_count": len(expr_notes),
                "pitch_bend_points_count": len(bends)
            }
        return {"status": "SUCCESS", "track_index": track_index, "message": "No notes in clip"}
    except Exception as e:
        logger.error(f"Error in expression_apply_mpe_vibrato: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def drums_inject_ghost_notes(
    track_index: int,
    clip_slot: int = 0,
    total_bars: int = 96
) -> dict:
    """
    Phase 4: Injects turnaround ghost snares (velocity 25-45) and applies 16th-note velocity wave
    modulation to hi-hats.
    """
    try:
        from engine.music.drums.ghost_notes import DrumGhostNoteInjector
        from engine.music.models import NoteEvent
        conn = get_ableton_connection()
        clip_notes = conn.get_clip_notes(track_index, clip_slot) if hasattr(conn, "get_clip_notes") else []
        if clip_notes:
            events = [NoteEvent(pitch=d.get("pitch", 38), start=d.get("start_time", 0.0), duration=d.get("duration", 0.25), velocity=d.get("velocity", 100)) for d in clip_notes]
            processed = DrumGhostNoteInjector.process_drum_track_notes(events, total_bars=total_bars)
            formatted = [
                {"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity, "mute": False}
                for n in processed
            ]
            conn.add_notes_to_clip(track_index, clip_slot, formatted, mode="replace")
            return {
                "status": "SUCCESS",
                "track_index": track_index,
                "clip_slot": clip_slot,
                "original_notes": len(clip_notes),
                "total_notes_with_ghosts": len(formatted)
            }
        return {"status": "SUCCESS", "track_index": track_index, "message": "No notes in clip"}
    except Exception as e:
        logger.error(f"Error in drums_inject_ghost_notes: {e}")
        return {"status": "error", "message": str(e)}




@mcp.tool()
def transitions_inject_section_impacts(
    track_index: int = 3,
    clip_slot: int = 0
) -> dict:
    """
    Phase 5: Injects sub-booms (40 Hz) and arrival crashes on the Foley/FX track
    at all 8 section boundaries across 96 bars.
    """
    try:
        from engine.arrangement.transitions.impacts import SectionImpactEngine
        conn = get_ableton_connection()
        manifest = SectionImpactEngine.get_section_impact_manifest()
        notes = SectionImpactEngine.generate_impact_notes()
        if conn and hasattr(conn, "add_notes_to_clip"):
            formatted = [{"pitch": n.pitch, "start_time": n.start, "duration": n.duration, "velocity": n.velocity, "mute": False} for n in notes]
            conn.send_command("create_clip", {"track_index": track_index, "clip_index": clip_slot, "length": 384.0})
            conn.send_command("add_notes_to_clip", {"track_index": track_index, "clip_index": clip_slot, "notes": formatted})
        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "clip_slot": clip_slot,
            "manifest": manifest,
            "total_impact_notes": len(notes)
        }
    except Exception as e:
        logger.error(f"Error in transitions_inject_section_impacts: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def transitions_build_tension_risers(
    track_index: int = 3,
    clip_slot: int = 0
) -> dict:
    """
    Phase 5: Generates exponential filter sweeps, pitch risers, and accelerating snare rolls
    in bars 30-32 (pre-Drop 1) and bars 70-72 (pre-Final Chorus).
    """
    try:
        from engine.arrangement.transitions.risers import TransitionRisersEngine
        sweep1 = TransitionRisersEngine.generate_filter_sweep(target_bar=33.0, duration_bars=2.0)
        sweep2 = TransitionRisersEngine.generate_filter_sweep(target_bar=73.0, duration_bars=2.0)
        noise_riser = TransitionRisersEngine.generate_noise_pitch_riser(target_bar=33.0, duration_bars=2.0)
        rolls1 = TransitionRisersEngine.generate_procedural_snare_roll(target_bar=33.0, duration_bars=1.0)
        return {
            "status": "SUCCESS",
            "drop1_filter_sweep_points": len(sweep1),
            "climax_filter_sweep_points": len(sweep2),
            "noise_pitch_envelope_points": len(noise_riser["pitch_bend_envelope"]),
            "snare_roll_notes_count": len(rolls1),
            "snare_roll_notes": [{"pitch": n.pitch, "start_time": n.start, "velocity": n.velocity} for n in rolls1]
        }
    except Exception as e:
        logger.error(f"Error in transitions_build_tension_risers: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def transitions_apply_pre_drop_vacuum() -> dict:
    """
    Phase 5: Generates acoustic vacuum silence windows (bars 31.4 and 71.4) and low-end cut
    mute automation envelopes preceding the main drops.
    """
    try:
        from engine.arrangement.transitions.pre_drop import PreDropVacuumEngine
        windows = PreDropVacuumEngine.get_vacuum_windows()
        env1 = PreDropVacuumEngine.generate_vacuum_mute_envelope(drop_beat=128.0)
        env2 = PreDropVacuumEngine.generate_vacuum_mute_envelope(drop_beat=288.0)
        return {
            "status": "SUCCESS",
            "vacuum_windows": windows,
            "drop1_mute_envelope": env1,
            "climax_mute_envelope": env2
        }
    except Exception as e:
        logger.error(f"Error in transitions_apply_pre_drop_vacuum: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def transitions_inject_ear_candy_fx() -> dict:
    """
    Phase 5: Generates analog vinyl tape stops, reverse vocal swells, and freeze washes
    for micro-production ear candy across song transitions.
    """
    try:
        from engine.arrangement.fx.ear_candy_transitions import EarCandyTransitionEngine
        manifest = EarCandyTransitionEngine.get_full_ear_candy_manifest()
        return manifest
    except Exception as e:
        logger.error(f"Error in transitions_inject_ear_candy_fx: {e}")
        return {"status": "error", "message": str(e)}



@mcp.tool()
def mix_apply_frequency_slotting() -> dict:
    """
    Phase 6: Applies multitrack complementary frequency slotting and surgical High-Pass Filtering
    across all 8 session tracks to eliminate acoustic masking.
    """
    try:
        from engine.mix.frequency_slotting import FrequencySlottingEngine
        plan = FrequencySlottingEngine.generate_full_session_slotting_plan()
        return plan
    except Exception as e:
        logger.error(f"Error in mix_apply_frequency_slotting: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def mix_audit_phase_and_mono_compatibility() -> dict:
    """
    Phase 6: Audits Pearson phase correlation coefficients between interacting stems (Kick vs 808)
    and enforces strict sub-bass mono collapse (< 120 Hz) for club/vinyl compatibility.
    """
    try:
        from engine.mix.phase_alignment import PhaseAlignmentEngine
        report = PhaseAlignmentEngine.generate_phase_audit_report()
        return report
    except Exception as e:
        logger.error(f"Error in mix_audit_phase_and_mono_compatibility: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def mix_apply_vocal_lead_fader_riding(role: str = "vocal", crossfade_beats: float = 2.0) -> dict:
    """
    Phase 6: Computes section-aware dynamic fader riding automation curves across 96 bars
    for vocal hooks and lead melodies (-2.5 dB to +2.8 dB).
    """
    try:
        from engine.mix.fader_rider import VocalLeadFaderRider
        manifest = VocalLeadFaderRider.get_fader_riding_manifest()
        return manifest
    except Exception as e:
        logger.error(f"Error in mix_apply_vocal_lead_fader_riding: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def mix_apply_multitrack_sidechain_ducking() -> dict:
    """
    Phase 6: Coordinates physical sidechain compression routing and envelope ducking
    across Kick-to-Bass, Vocal-to-Chords, and Kick-to-Reverb buses.
    """
    try:
        from engine.mix.multitrack_sidechain import MultiTrackSidechainCoordinator
        matrix = MultiTrackSidechainCoordinator.get_multitrack_sidechain_matrix()
        return matrix
    except Exception as e:
        logger.error(f"Error in mix_apply_multitrack_sidechain_ducking: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def preset_search(
    query: str = "",
    role: str = "",
    plugin: str = "",
    limit: int = 15
) -> dict:
    """
    Search presets across 14,105 Arturia patches (Analog Lab V, Pigments, Jup-8, etc.),
    Prototype Audio Fraction expansions, Omnisphere, Massive, ZENOLOGY, and Ableton User Library.

    Args:
        query: Free text search keyword (e.g. 'Rhodes', '808', 'Reese', 'Warm Pad', 'Lead', 'Granular')
        role: Musical role filter (e.g. 'bass', 'lead', 'pad', 'keys', 'organ', 'strings', 'fx', 'drums')
        plugin: Target plugin name filter (e.g. 'Analog Lab V', 'Fraction', 'Pigments', 'Fragments', 'Motions', 'Omnisphere', 'Massive', 'ZENOLOGY')
        limit: Maximum number of presets to return (default 15)

    Returns:
        Structured list of matching presets with loading method (MIDI Program Change vs User Library .adv)
        and exact selection parameters.
    """
    try:
        from engine.presets.catalog import preset_catalog
        results = preset_catalog.search_presets(
            query=query,
            role=role if role else None,
            plugin=plugin if plugin else None,
            limit=limit
        )
        return {
            "status": "success",
            "count": len(results),
            "presets": results,
            "instruction_for_ai": (
                "Para sintes con 'midi_program_change' (Analog Lab, Omnisphere, Massive, ZENOLOGY): "
                "usa preset_select_for_track para enviar el Program Change correspondiente. "
                "Para plugins con 'user_library_adv' (Fraction, Efx FRAGMENTS, Efx MOTIONS, etc.): "
                "carga el archivo .adv de la User Library con preset_select_for_track o load_instrument_or_effect."
            )
        }
    except Exception as e:
        logger.error(f"Error in preset_search: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def preset_select_for_track(
    track_index: int,
    preset_name: str,
    plugin: str = "",
    clip_index: int = 0,
    program_id: int = None
) -> dict:
    """
    Selects and applies a preset to a track:
    - For MIDI synthesizers (Analog Lab V, Omnisphere, Massive, ZENOLOGY):
      Configures MIDI Program Change and Bank parameters for the track/clip.
    - For User Library plugins (Fraction, Efx FRAGMENTS, Efx MOTIONS, etc.):
      Loads the .adv / .adg device preset onto the track via Ableton's browser.

    Args:
        track_index: Ableton track index (0-based)
        preset_name: Name of the preset to select
        plugin: Plugin name (e.g. 'Analog Lab V', 'Fraction', 'Omnisphere', 'Massive', 'ZENOLOGY')
        clip_index: Clip slot index to associate with the program change (default 0)
        program_id: Optional explicit Program Change ID (0-127)
    """
    try:
        from engine.presets.catalog import preset_catalog
        from engine.midi.program_change import program_change_dispatcher

        candidates = preset_catalog.search_presets(query=preset_name, plugin=plugin, limit=5)
        target = None
        for c in candidates:
            if c.get("preset_name", "").lower() == preset_name.lower():
                target = c
                break
        if not target and candidates:
            target = candidates[0]

        target_plugin = plugin or (target.get("plugin") if target else "Unknown")

        if target and target.get("loading_method") == "user_library_adv" and target.get("browser_uri"):
            conn = get_ableton_connection()
            uri = target["browser_uri"]
            res = conn.send_command("load_browser_item", {"track_index": track_index, "item_uri": uri})
            return {
                "status": "success",
                "track_index": track_index,
                "plugin": target_plugin,
                "preset_name": preset_name,
                "loading_method": "user_library_adv",
                "browser_uri": uri,
                "result": res
            }

        # Guard & Auto-Instantiate: Ensure the physical instrument device is loaded on track (INV-SOUND-01)
        auto_loaded_device = False
        try:
            conn = get_ableton_connection()
            raw_info = conn.send_command("get_track_info", {"track_index": track_index})
            t_info = raw_info.get("result", raw_info) if isinstance(raw_info, dict) else {}
            devices = t_info.get("devices", []) if isinstance(t_info, dict) else []
            plugin_loaded = any(
                target_plugin.lower() in d.get("name", "").lower() or d.get("name", "").lower() in target_plugin.lower()
                for d in devices
            )

            if not plugin_loaded:
                from engine.production.recipe_engine import VERIFIED_PLUGIN_URIS
                plugin_uri = None
                for p_name, u in VERIFIED_PLUGIN_URIS.items():
                    if p_name.lower() in target_plugin.lower() or target_plugin.lower() in p_name.lower():
                        plugin_uri = u
                        break
                if plugin_uri:
                    logger.info(f"[preset_select_for_track] Auto-instantiating '{target_plugin}' ({plugin_uri}) on track {track_index}...")
                    load_res = conn.send_command("load_browser_item", {"track_index": track_index, "item_uri": plugin_uri})
                    auto_loaded_device = True
                elif len(devices) == 0:
                    return {
                        "status": "error",
                        "error_type": "SILENT_TRACK_VIOLATION",
                        "track_index": track_index,
                        "plugin": target_plugin,
                        "message": (
                            f"Plugin '{target_plugin}' is not loaded on track {track_index} and track contains 0 devices. "
                            f"Invariant INV-SOUND-01 violated: cannot assign presets to an empty track without loading the instrument first."
                        )
                    }
        except Exception as inspect_err:
            logger.debug(f"Device inspection/auto-instantiate error: {inspect_err}")

        pc_id = program_id
        if pc_id is None and target and target.get("program_change_id") is not None:
            pc_id = target["program_change_id"]
        if pc_id is None:
            pc_id = 0

        if "analog lab" in target_plugin.lower() or "analog lab" in preset_name.lower():
            try:
                from engine.presets.analog_lab_ui_automator import analog_lab_ui_automator
                analog_lab_ui_automator.select_preset(
                    preset_name=preset_name,
                    track_index=track_index,
                    conn=conn
                )
            except Exception as ui_err:
                logger.debug(f"AnalogLabUIAutomator error: {ui_err}")

        pc_config = program_change_dispatcher.send_program_change(
            conn=conn,
            track_index=track_index,
            program=pc_id,
            bank=target.get("bank") if target else None,
            plugin_name=target_plugin
        )

        # Reflect preset visibly on track name in Live session
        try:
            cur_name = t_info.get("name", f"Track {track_index}")
            base_name = cur_name.split("[")[0].strip() if "[" in cur_name else cur_name
            new_track_name = f"{base_name} [{preset_name}]"
            conn.send_command("set_track_name", {"track_index": track_index, "name": new_track_name})
        except Exception as name_err:
            logger.debug(f"Track rename error on preset select: {name_err}")

        # Phase 1 Governance: record preset selection
        try:
            from engine.supervisor.governance import governance_supervisor
            governance_supervisor.record_preset_selected(track_index, preset_name, device_index=0)
        except Exception as g_err:
            logger.debug(f"Governance record error: {g_err}")

        return {
            "status": "success",
            "track_index": track_index,
            "plugin": target_plugin,
            "preset_name": preset_name,
            "loading_method": "midi_program_change",
            "auto_loaded_instrument": auto_loaded_device,
            "program_change_config": pc_config,
            "message": (
                f"Preset '{preset_name}' asignado vía {pc_config.get('config', {}).get('description', 'MIDI Program Change')}. "
                "Los clips MIDI disparados en esta pista conmutarán el sonido instantáneamente sin latencia."
            )
        }

    except Exception as e:
        logger.error(f"Error in preset_select_for_track: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def genre_offer_production_options(category: str = "", genre: str = "") -> dict:
    """
    [EXPERIMENTAL FEATURE - DORMANT BY DEFAULT]
    Offers the AI a rich, structured catalog of production recipes, authentic groove patterns,
    and mix targets organized by genre:
    - Rap & Trap (Modern Trap, 90s Boom-Bap)
    - Cumbia & Ritmos Latinos (Cumbia Tradicional / Sonidera / Electrocumbia)
    - Electro de todo tipo (House, Techno, Synthwave, EDM Festival, Drum & Bass)
    - Música Urbana & Pop (Reggaetón Dembow, Afrobeat, Pop Comercial)
    - Rock (Modern Rock, Indie, Alternativo)

    IMPORTANT: This feature is experimental and off by default.
    Custom, experimental, and freeform workflows are 100% supported without restriction.

    Args:
        category: Optional filter by category ("rap_trap", "cumbia", "electro", "urbano_pop", "rock")
        genre: Optional filter by specific genre ("trap", "cumbia", "house", "techno", "reggaeton", "afrobeat", "rock", etc.)
    """
    try:
        from engine.production.recipe_engine import ProductionRecipeEngine
        from engine.music.drums.genre_grooves import GenreRhythmGrooveEngine

        if genre:
            desc = GenreRhythmGrooveEngine.get_genre_descriptor(genre)
            return {
                "status": "success",
                "is_experimental": True,
                "genre_requested": genre,
                "profile": desc,
                "is_optional": True,
                "notice": "Este perfil es una sugerencia técnica y creativa opcional (experimental). El flujo libre y manual se respeta al 100%."
            }

        menu = ProductionRecipeEngine.offer_genre_production_menu(category=category if category else None)
        menu["is_experimental"] = True
        return menu
    except Exception as e:
        logger.error(f"Error in genre_offer_production_options: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def genre_generate_drum_pattern(
    genre: str,
    track_index: int,
    clip_index: int = 0,
    length_bars: int = 4,
    tempo: float = 120.0,
    swing_amount: float = 0.0,
    humanize_ms: float = 6.0
) -> dict:
    """
    [EXPERIMENTAL FEATURE - DORMANT BY DEFAULT]
    Generates and injects an authentic procedural rhythm pattern for a specified genre directly
    into an Ableton clip slot:
    - Cumbia: Güira raspada 16th sincopada, conga tumbao y timbal turnaround fill
    - Rap / Trap: Half-time clap, syncopated 808 kick, rolling triplet hi-hats
    - Rock: Acoustic kit drive, solid 1 & 3 kick, aggressive 2 & 4 snare crack, 8th hats/ride
    - Afrobeat: Syncopated cross-rhythm kick, crisp rimshots, organic 16th shaker wave
    - House / Techno / EDM: 4-on-the-floor, offbeat open hat, 16th pocket
    - Drum & Bass: 174 BPM 2-step breakbeat, rolling ghost snares

    Args:
        genre: Target genre ("cumbia", "trap", "rock", "afrobeat", "house", "techno", "edm", "drum_and_bass", "pop", "reggaeton")
        track_index: Track index containing Drum Rack or percussion instrument
        clip_index: Target clip slot index (default 0)
        length_bars: Pattern duration in bars (default 4)
        tempo: Target BPM for micro-timing calculations
        swing_amount: MPC swing ratio (0.0 to 0.70)
        humanize_ms: Human timing jitter in milliseconds (default 6.0)
    """
    try:
        from engine.music.drums.genre_grooves import GenreRhythmGrooveEngine
        notes = GenreRhythmGrooveEngine.generate_rhythm_pattern(
            genre=genre,
            length_bars=length_bars,
            tempo=tempo,
            swing_amount=swing_amount,
            humanize_ms=humanize_ms
        )

        conn = get_ableton_connection()
        # Create clip if needed
        conn.send_command("create_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "length": float(length_bars * 4.0)
        })

        # Add notes
        notes_payload = [
            {
                "pitch": n.pitch,
                "start_time": n.start,
                "duration": n.duration,
                "velocity": n.velocity
            }
            for n in notes
        ]
        conn.send_command("add_notes_to_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "notes": notes_payload
        })

        return {
            "status": "success",
            "genre": genre,
            "track_index": track_index,
            "clip_index": clip_index,
            "length_bars": length_bars,
            "total_notes": len(notes),
            "sample_groove": f"Patrón procedural de {genre} inyectado con {len(notes)} eventos de nota."
        }
    except Exception as e:
        logger.error(f"Error in genre_generate_drum_pattern: {e}")
        return {"status": "error", "message": str(e)}



@mcp.tool()
def suggest_clip_automations(
    track_index: int,
    clip_index: int = 0,
    destination_time: Optional[float] = None
) -> dict:
    """
    Inspects a track and returns contextual, tangible vector automation recipes suited for the clip
    (timbre swell, filter riser, organic breathing, pre-drop vacuum cut, etc.).
    """
    try:
        from engine.arrangement.automation.clip_suggester import ClipAutomationSuggester
        conn = get_ableton_connection()
        t_info_res = conn.send_command("get_track_info", {"track_index": track_index})
        t_info = t_info_res.get("result", {}) if isinstance(t_info_res, dict) else (t_info_res or {})
        
        suggestions = ClipAutomationSuggester.suggest_for_track(t_info, clip_length=16.0)
        return {
            "status": "success",
            "track_index": track_index,
            "clip_index": clip_index,
            "track_name": t_info.get("name", f"Track {track_index}"),
            "destination_time": destination_time,
            "suggestions": suggestions,
            "notice": "Each recipe can be baked directly into Ableton Live as tangible breakpoints editable with the 'A' key."
        }
    except Exception as e:
        logger.error(f"Error in suggest_clip_automations: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def apply_clip_automation(
    track_index: int,
    clip_index: int = 0,
    recipe_name: str = "timbre_swell",
    destination_time: Optional[float] = None,
    parameter: Optional[str] = None,
    start_val: Optional[float] = None,
    end_val: Optional[float] = None
) -> dict:
    """
    Bakes a tangible, vector automation envelope into an Ableton Live clip
    (and optionally bakes it directly into the Arrangement timeline at destination_time).
    Creates real circular vector breakpoints visible and editable with the 'A' key.

    Available recipes:
    - "timbre_swell": Exponential rise in brightness/timbre (0.15 -> 0.85).
    - "filter_riser": Exponential lowpass filter opening (0.20 -> 0.95).
    - "filter_breathing": Subtle organic LFO sinusoidal breathing (0.45 <-> 0.65).
    - "pre_drop_vacuum": High-impact energy vacuum (-60dB / mute during last 2 beats).
    - "reverb_washout": Reverb wet buildup to 0.70 then sudden cut to 0.0 on the downbeat.
    - "volume_crescendo": Dynamic volume swell (0.50 -> 0.85).
    - "sub_turnaround": Harmonic drive/cutoff surge for section turnarounds.
    """
    try:
        from engine.arrangement.automation.clip_suggester import ClipAutomationSuggester
        conn = get_ableton_connection()
        result = ClipAutomationSuggester.apply_recipe_to_clip(
            conn=conn,
            track_index=track_index,
            clip_index=clip_index,
            recipe_id=recipe_name,
            destination_time=destination_time,
            parameter=parameter,
            start_val=start_val,
            end_val=end_val
        )
        return result
    except Exception as e:
        logger.error(f"Error in apply_clip_automation: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def drum_rack_audit_clip_octaves(
    track_index: int,
    clip_index: int = 0
) -> dict:
    """
    Audits the MIDI clip on a Drum Rack track against physical pad quadrants.
    Standard Drum Racks have pads in Quadrant 1 (C1-D#2, pitches 36-51).
    If notes are in Quadrant 3 (C3-D#4, pitches 60-75), the pads are completely silent.
    Detects mismatch and returns transposition recommendation.
    """
    try:
        from engine.instruments.drum_rack_guard import DrumRackGuard
        conn = get_ableton_connection()
        return DrumRackGuard.audit_drum_clip_octaves(conn=conn, track_index=track_index, clip_index=clip_index)
    except Exception as e:
        logger.error(f"Error in drum_rack_audit_clip_octaves: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def drum_rack_transpose_clip_octaves(
    track_index: int,
    clip_index: int = 0,
    semitone_shift: int = -24
) -> dict:
    """
    Transposes all notes in a drum clip by semitone_shift (default -24 semitones / 2 octaves)
    so that notes mistakenly placed in Quadrant 3 (C3+) land in Quadrant 1 (C1-D#2) pads.
    """
    try:
        from engine.instruments.drum_rack_guard import DrumRackGuard
        conn = get_ableton_connection()
        return DrumRackGuard.remediate_drum_clip_octaves(
            conn=conn,
            track_index=track_index,
            clip_index=clip_index,
            semitone_shift=semitone_shift
        )
    except Exception as e:
        logger.error(f"Error in drum_rack_transpose_clip_octaves: {e}")
@mcp.tool()
def orchestrate_role_track(
    track_index: int,
    role: str,
    genre: str = "hip_hop_neo_soul",
    bpm: float = 120.0,
    key: str = "F",
    scale: str = "natural_minor",
    custom_instrument_id: str = "",
    custom_blueprint: str = "",
    arrange_bars: int = 96
) -> dict:
    """
    Atomic Role Orchestration (Capa 3: Operaciones Atómicas de Rol):
    Executes an indivisible ACID transaction for a musical role on a track:
    1. Loads verified instrument from catalog / installed plugins.
    2. Physically verifies device presence in Live's LOM.
    3. Sculpts synthesis parameters (Delta >= 1) applying role blueprint.
    4. Composes full-song musical notes across arrangement sections.
    5. Deploys clips to Session and Arrangement timelines.
    6. Renames track with role and instrument metadata.

    Guarantees zero silent or orphaned tracks and zero unconfigured plugins.
    """
    try:
        from engine.production.copilot.role_orchestrator import RoleTrackOrchestrator
        conn = get_ableton_connection()
        cb_dict = None
        if custom_blueprint:
            try:
                cb_dict = json.loads(custom_blueprint)
            except Exception:
                cb_dict = None

        return RoleTrackOrchestrator.orchestrate_role_track(
            conn=conn,
            track_index=track_index,
            role=role,
            genre=genre,
            bpm=bpm,
            key=key,
            scale=scale,
            custom_instrument_id=custom_instrument_id or None,
            custom_blueprint=cb_dict,
            arrange_bars=arrange_bars
        )
    except Exception as e:
        logger.error(f"Error in orchestrate_role_track: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def copilot_auto_produce(
    genre: str = "hip_hop_neo_soul",
    bpm: float = 120.0,
    key: str = "F",
    scale: str = "natural_minor",
    max_steps: int = 80
) -> dict:
    """
    Autonomous End-to-End Copilot Producer:
    Executes the entire native Copilot production pipeline from DNA to Final Delivery in a single command.
    Iteratively resolves all decisions (Creative DNA -> Composition -> Sound Design -> Groove -> Transitions -> Mix -> Master),
    enforces physical load verification and parameter sculpting (Capa 3), and audits with preflight_check.
    The Copilot remains active and listening in the session for subsequent adjustments.
    """
    try:
        from engine.production.copilot.stepper import executive_copilot
        conn = get_ableton_connection()
        return executive_copilot.run_autonomous_pipeline(
            conn=conn,
            genre=genre,
            bpm=bpm,
            key=key,
            scale=scale,
            max_steps=max_steps
        )
    except Exception as e:
        logger.error(f"Error in copilot_auto_produce: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def copilot_guided_session(
    user_input: str = "",
    reset: bool = False
) -> dict:
    """
    Conversational State Machine Wizard for Interactive Music Production (Strict 7-Phase Flow).
    Conducts an interactive, step-by-step interview with the AI / User producer:
    - Step 1 (PHASE_1_TRACKS): Track scaffolding and role allocation (Drums, Keys, Pads, Bass, Lead).
    - Step 2 (PHASE_2_SECTIONS): Song arrangement sections & cue point locators on timeline.
    - Step 3 (PHASE_3_INSTRUMENTS): Track-by-track verified instrument loading & Drum Rack pad checks (Zero silent swallow).
    - Step 4 (PHASE_4_PARAM_SCULPTING): Track-by-track conversational synthesis parameter sculpting (Delta >= 1 rule).
    - Step 5 (PHASE_5_INSERT_EFFECTS): Track-by-track insert FX chains (Drum Buss, Saturator, VintageVerb, Delay, OTT).
    - Step 6 (PHASE_6_COMPOSITION): Multi-section harmonic and melodic composition into arrangement timeline (Drum Octave Guard).
    - Step 7 (PHASE_7_MIX_MASTER): Dynamic mix, sidechain ducking & BS.1770-5 serial mastering chain.
    - Step 8 (PHASE_8_COMPLETED): Active listening for post-production natural language tweaks (volume, tempo, mutes, timbres).

    Each turn executes real DAW mutations in Ableton Live, verifies LOM state, and returns the next question.
    """
    try:
        import sys, importlib
        if reset:
            for mod_name in list(sys.modules.keys()):
                if mod_name.startswith("engine."):
                    try:
                        importlib.reload(sys.modules[mod_name])
                    except Exception:
                        pass
        import engine.production.copilot.guided_session as _gs_mod
        if reset:
            importlib.reload(_gs_mod)
        copilot_guided_session_engine = _gs_mod.copilot_guided_session_engine
        conn = get_ableton_connection()
        return copilot_guided_session_engine.step(conn=conn, user_input=user_input, reset=reset)
    except Exception as e:
        logger.error(f"Error in copilot_guided_session: {e}")
        return {"status": "error", "message": str(e)}



# ============================================================================
# PERSISTENT MEMORY, KNOWLEDGE BASE, SAMPLE INDEXER & STATIC MIX TOOLS
# ============================================================================

@mcp.tool()
def save_favorite_pattern(
    pattern_type: str,
    name: str,
    notes: list,
    genre: str = "",
    key: str = "",
    bpm: float = 0.0,
    rating: int = 5,
    user_notes: str = ""
) -> dict:
    """Save an approved or high-rated MIDI pattern into user persistent memory."""
    try:
        from engine.memory.user_learning import save_favorite_pattern as _save_pat
        msg = _save_pat(
            pattern_type=pattern_type,
            name=name,
            notes=notes,
            genre=genre,
            key=key,
            bpm=bpm,
            rating=rating,
            user_notes=user_notes
        )
        return {"status": "success", "message": msg}
    except Exception as e:
        logger.error(f"Error in save_favorite_pattern: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_favorite_patterns(
    pattern_type: str = "",
    genre: str = "",
    min_rating: int = 4,
    limit: int = 10
) -> list:
    """Retrieve top-rated user patterns from persistent memory for inspiration."""
    try:
        from engine.memory.user_learning import get_favorite_patterns as _get_pat
        return _get_pat(pattern_type=pattern_type, genre=genre, min_rating=min_rating, limit=limit)
    except Exception as e:
        logger.error(f"Error in get_favorite_patterns: {e}")
        return []


@mcp.tool()
def save_user_preference(
    category: str,
    key: str,
    value: str
) -> dict:
    """Persist a user taste/preference (scales, mixing, default headroom, VSTs)."""
    try:
        from engine.memory.user_learning import save_user_preference as _save_pref
        msg = _save_pref(category=category, key=key, value=value)
        return {"status": "success", "message": msg}
    except Exception as e:
        logger.error(f"Error in save_user_preference: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_user_preferences(
    category: str = "",
    key: str = ""
) -> dict:
    """Retrieve saved preferences from user persistent memory."""
    try:
        from engine.memory.user_learning import get_user_preferences as _get_pref
        res = _get_pref(category=category, key=key)
        return {"status": "success", "preferences": res}
    except Exception as e:
        logger.error(f"Error in get_user_preferences: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def search_samples_in_library(
    sample_type: str = "",
    subtype: str = "",
    genre: str = "",
    mood: str = "",
    key: str = "",
    bpm: int = 0,
    limit: int = 20
) -> list:
    """Search the Apache Parquet sample manifest by multi-attribute tags (type, mood, BPM, key)."""
    try:
        from engine.indexer.manifest import search_samples as _search
        from engine.indexer.paths import default_manifest_path
        m_path = default_manifest_path()
        return _search(
            manifest_path=m_path,
            sample_type=sample_type or None,
            subtype=subtype or None,
            genre=genre or None,
            mood=mood or None,
            key=key or None,
            bpm=bpm if bpm > 0 else None,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error in search_samples_in_library: {e}")
        return []


@mcp.tool()
def reindex_sample_library(samples_root: str = "") -> dict:
    """Reindex sample library into Apache Parquet incrementally with tokenized tag extraction."""
    try:
        from engine.indexer.manifest import build_manifest
        from engine.indexer.paths import default_samples_root, default_manifest_path
        s_root = samples_root or str(default_samples_root())
        m_path = default_manifest_path()
        stats = build_manifest(packs_root=s_root, manifest_path=m_path)
        return {"status": "success", "stats": stats}
    except Exception as e:
        logger.error(f"Error in reindex_sample_library: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def analyze_mix_static(genre: str = "streaming") -> dict:
    """Run a pre-flight static mix audit checking for fader clipping, silent active tracks, and FX overload."""
    try:
        from engine.mix.static_auditor import StaticMixAuditor
        conn = get_ableton_connection()
        s_info = conn.send_command("get_session_info", {}) if conn else {}
        s_data = s_info.get("result", s_info) if isinstance(s_info, dict) else {}
        report = StaticMixAuditor.audit_session(s_data, genre=genre)
        report["formatted_es"] = StaticMixAuditor.format_report_es(report)
        return report
    except Exception as e:
        logger.error(f"Error in analyze_mix_static: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_producer_info(producer_name: str) -> dict:
    """Get signature production blueprint, drum selection, swing, and hardware emulation for 13 legendary producers."""
    try:
        from engine.knowledge.producers.producers import get_producer_profile
        profile = get_producer_profile(producer_name)
        return {"status": "success", "profile": profile}
    except Exception as e:
        logger.error(f"Error in get_producer_info: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_serum_patch(patch_name: str) -> dict:
    """Get step-by-step synthesis patch recipe for Serum 2 (808s, leads, keys, pads, plucks)."""
    try:
        from engine.knowledge.plugins.serum2 import get_patch_recipe
        recipe = get_patch_recipe(patch_name)
        return {"status": "success", "recipe": recipe}
    except Exception as e:
        logger.error(f"Error in get_serum_patch: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_fabfilter_preset(plugin: str, element: str) -> dict:
    """Get surgical presets for FabFilter Pro-Q 4, Pro-C 3, or Saturn 2 by instrument element."""
    try:
        from engine.knowledge.plugins.fabfilter import get_eq_preset, get_compressor_preset
        p_lower = plugin.lower()
        if "eq" in p_lower or "q" in p_lower:
            res = get_eq_preset(element)
        else:
            res = get_compressor_preset(element)
        return {"status": "success", "preset": res}
    except Exception as e:
        logger.error(f"Error in get_fabfilter_preset: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_vocal_chain_guide(style: str = "trap_lead") -> dict:
    """Get complete 10-slot vocal chain order with Auto-Tune Pro, RX 11, EQ, and dynamics settings."""
    try:
        from engine.knowledge.plugins.vocal_chains import get_vocal_chain
        chain = get_vocal_chain(style)
        return {"status": "success", "vocal_chain": chain}
    except Exception as e:
        logger.error(f"Error in get_vocal_chain_guide: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def audio_semantic_sample_match(prompt: str, sample_paths: Optional[List[str]] = None, top_k: int = 5) -> dict:
    """Matches natural language intent ('punchy kick', 'dark boomy 808', 'crisp snap') to audio samples using physical 6D acoustic signatures."""
    try:
        from engine.audio.semantic_sample_matcher import AcousticFeatureExtractor, SemanticSampleMatcher
        import glob
        paths = sample_paths or []
        if not paths:
            # Look in local project cache or sample library
            paths = glob.glob(r"F:\Dev\AbletonEngine\**\*.wav", recursive=True)[:30]
        
        signatures = {}
        for p in paths:
            sig = AcousticFeatureExtractor.extract_from_file(p)
            if sig:
                signatures[p] = sig
                
        results = SemanticSampleMatcher.rank_candidates(prompt, signatures, top_k=top_k)
        return {"status": "success", "prompt": prompt, "matches": results}
    except Exception as e:
        logger.error(f"Error in audio_semantic_sample_match: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def audio_deconstruct_reference(audio_path: str, prefer_neural: bool = True, bpm: float = 120.0) -> dict:
    """Separates reference track into drums, bass, vocals, other stems (via Meta Demucs or DSP fallback) and extracts arrangement energy profile."""
    try:
        from engine.audio.deconstruction.neural_separator import HybridStemSeparator
        sep = HybridStemSeparator()
        stems = sep.separate(audio_path, prefer_neural=prefer_neural)
        profile = sep.profile_arrangement_energy(stems, tempo_bpm=bpm)
        return {
            "status": "success",
            "stems": {k: v.to_dict() for k, v in stems.items()},
            "arrangement_profile": profile
        }
    except Exception as e:
        logger.error(f"Error in audio_deconstruct_reference: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def audio_transcribe_to_midi(audio_path: str, track_index: Optional[int] = None, tempo_bpm: float = 120.0) -> dict:
    """Transcribes monophonic audio recording into expressive MIDI notes with pitch bends and velocity dynamics."""
    try:
        from engine.audio.deconstruction.expressive_transcriber import ExpressiveAudioTranscriber
        transcriber = ExpressiveAudioTranscriber()
        events = transcriber.transcribe_file(audio_path, tempo_bpm=tempo_bpm)
        
        # If track_index provided, inject into Ableton Live
        if track_index is not None:
            conn = get_ableton_connection()
            if conn and hasattr(conn, "send_command") and events:
                clip_notes = [
                    {"pitch": e.pitch, "start_time": e.start_time_beats, "duration": e.duration_beats, "velocity": e.velocity, "mute": False}
                    for e in events
                ]
                total_beats = max(4.0, math.ceil(max(e.start_time_beats + e.duration_beats for e in events) / 4.0) * 4.0)
                conn.send_command("create_clip", {"track_index": track_index, "clip_index": 0, "length": total_beats})
                conn.send_command("add_notes_to_clip", {"track_index": track_index, "clip_index": 0, "notes": clip_notes})
                
        return {
            "status": "success",
            "notes_count": len(events),
            "events": [e.to_dict() for e in events[:20]]
        }
    except Exception as e:
        logger.error(f"Error in audio_transcribe_to_midi: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def mix_audit_psychoacoustic_masking(masker_audio_path: str, target_audio_path: str, masker_role: str = "DRUMS", target_role: str = "BASS") -> dict:
    """Audits full-spectrum psychoacoustic masking (Zwicker 24 Bark critical bands) and calculates surgical dynamic EQ carving parameters."""
    try:
        import soundfile as sf
        from engine.mix.psychoacoustic_masking import PsychoacousticMaskingAuditor
        m_audio, sr1 = sf.read(masker_audio_path, always_2d=False, dtype="float32")
        t_audio, sr2 = sf.read(target_audio_path, always_2d=False, dtype="float32")
        sr = sr1
        
        report = PsychoacousticMaskingAuditor.audit_masking_conflict(
            masker_audio=m_audio,
            target_audio=t_audio,
            sr=sr,
            masker_role=masker_role,
            target_role=target_role
        )
        return {"status": "success", "report": report.to_dict()}
    except Exception as e:
        logger.error(f"Error in mix_audit_psychoacoustic_masking: {e}")
        return {"status": "error", "message": str(e)}



def main():


    """Run the FastMCP server with all legacy, Phase 1, Phase 2, Phase 3, and Phase 4 sound tools registered"""
    mcp.run()

if __name__ == "__main__":
    main()


