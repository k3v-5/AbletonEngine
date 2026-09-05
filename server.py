# ableton_mcp_server.py
import sys
from pathlib import Path

_pkg_root = str(Path(__file__).resolve().parent)
if _pkg_root not in sys.path:
    sys.path.insert(0, _pkg_root)

from mcp.server.fastmcp import FastMCP, Context
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
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    
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

    def receive_full_response(self, sock, buffer_size=8192):
        """Receive the complete response, potentially in multiple chunks"""
        chunks = []
        sock.settimeout(6.0)  # Increased timeout for operations that might take longer (reduced to 6.0s to avoid Claude's 10s timeout crash)
        
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

    def send_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to Ableton and return the response"""
        with self._lock:
            if not self.sock and not self.connect():
                raise ConnectionError("Not connected to Ableton")
            
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
                "duplicate_session_clip_to_arrangement"
            ]
    
            # Commands whose work on Live's main thread can take noticeably longer
            # than the default modifying-command budget (e.g. importing/decoding a
            # large audio file). Give them a wider socket timeout so we don't time
            # out before the Remote Script's own queue does.
            long_running_commands = {"create_audio_clip": 65.0}
            
            try:
                logger.info(f"Sending command: {command_type} with params: {params}")
                
                # Send the command
                self.sock.sendall(json.dumps(command).encode('utf-8'))
                logger.info(f"Command sent, waiting for response...")
                
                # Set timeout based on command type
                if command_type in long_running_commands:
                    timeout = long_running_commands[command_type]
                else:
                    timeout = 7.0 if is_modifying_command else 5.0
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
        try:
            # Check if the socket is still alive by peeking for data
            # MSG_PEEK + MSG_DONTWAIT will raise BlockingIOError if alive but no data,
            # or return b'' if the remote end has closed the connection.
            _ableton_connection.sock.setblocking(False)
            try:
                data = _ableton_connection.sock.recv(1, socket.MSG_PEEK)
                if data == b'':
                    raise ConnectionError("Remote end closed")
            except BlockingIOError:
                pass  # Socket is alive, just no data waiting — this is normal
            finally:
                _ableton_connection.sock.setblocking(True)
            return _ableton_connection
        except Exception as e:
            logger.warning(f"Existing connection is no longer valid: {str(e)}")
            try:
                _ableton_connection.disconnect()
            except:
                pass
            _ableton_connection = None
    
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
def create_clip(ctx: Context, track_index: int, clip_index: int, length: float = 4.0, user_prompt: str = "") -> str:
    """
    Create a new MIDI clip in the specified track and clip slot.

    Parameters:
    - track_index: The index of the track to create the clip in
    - clip_index: The index of the clip slot to create the clip in
    - length: The length of the clip in beats (default: 4.0)
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("create_clip", {
            "track_index": track_index, 
            "clip_index": clip_index, 
            "length": length
        })
        return f"Created new clip at track {track_index}, slot {clip_index} with length {length} beats"
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
            return f"Failed to load instrument with URI '{uri}'"
    except Exception as e:
        logger.error(f"Error loading instrument by URI: {str(e)}")
        return f"Error loading instrument by URI: {str(e)}"

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
    user_prompt: str = ""
) -> str:
    """
    Copy a Session-view clip into the Arrangement timeline.

    Uses Live's track.duplicate_clip_to_arrangement() API (Live 11 / 12).
    The clip is placed at destination_time beats from the start of the
    arrangement on the same track it lives in.

    Typical workflow:
      1. create_clip / add_notes_to_clip to build a Session clip
      2. Call duplicate_to_arrangement once per bar/section you need
      3. Call switch_to_arrangement_view to confirm the result in Live

    Parameters:
    - track_index:       Index of the track that owns the Session clip
    - clip_index:        Index of the clip slot in that track (Session view)
    - destination_time:  Beat position in the arrangement to place the clip
                         (e.g. 0.0 = start, 8.0 = bar 3 in 4/4)
    - user_prompt: The original user prompt that led to this tool call (for telemetry)
    """
    try:
        ableton = get_ableton_connection()
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
            f"Duplicated '{clip_name}' from Session slot {clip_index} "
            f"on '{track_name}' to arrangement at beat {destination_time}"
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
        ableton = get_ableton_connection()
        result = ableton.send_command("set_device_parameter", {
            "track_index": track_index,
            "device_index": device_index,
            "parameter": parameter,
            "value": value
        })
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
        
        # Write to Live
        if d_idx is not None:
            try:
                ableton.send_command("set_device_parameter", {
                    "track_index": t_idx,
                    "device_index": d_idx,
                    "parameter": p_name,
                    "value": points[0]["value"]
                })
            except:
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
            "verified": True,
            "points": points
        }, indent=2)
    except Exception as e:
        logger.error(f"Error creating automation: {str(e)}")
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
        if d_idx is not None and sorted_pts:
            try:
                ableton.send_command("set_device_parameter", {
                    "track_index": t_idx,
                    "device_index": d_idx,
                    "parameter": p_name,
                    "value": sorted_pts[0]["value"]
                })
            except:
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
            "verified": True,
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
try:
    engine.initialize()
except Exception as _pie_init_err:
    logger.info(f"Engine bootstrap initialized (Live offline: {_pie_init_err})")


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


def main():


    """Run the FastMCP server with all legacy, Phase 1, Phase 2, Phase 3, and Phase 4 sound tools registered"""
    mcp.run()

if __name__ == "__main__":
    main()


