# engine/arrangement/automation/clip_envelopes.py
"""
Live 12 Clip Envelope Engine:
Manages automation envelopes directly inside Ableton Live 12 clips
(both Session View and Arrangement View clips).

LOM Clip Envelope Architecture:
- `clip.has_envelopes`: boolean indicating if any envelope is defined.
- `clip.create_automation_envelope(parameter_object)`: returns an AutomationEnvelope.
- `clip.clear_envelope(parameter_object)`: clears envelope for specific parameter.
- `clip.clear_all_envelopes()`: clears all envelopes inside the clip.
- `envelope.insert_step(start_time, length, value)`: inserts discreet parameter steps.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Union
import logging

logger = logging.getLogger("ClipEnvelopeEngine")


@dataclass
class EnvelopeBreakpoint:
    """A discrete time-value point for clip envelope generation."""
    time: float          # Time in beats relative to clip start (0.0 = clip start)
    length: float        # Duration in beats of the step
    value: float         # Parameter value (typically normalized 0.0 to 1.0 or target scale)

    def to_dict(self) -> Dict[str, float]:
        return {
            "time": round(self.time, 4),
            "length": round(self.length, 4),
            "value": round(self.value, 4)
        }


class ClipEnvelopeEngine:
    """
    Orchestrates clip envelope creation, clearing, and step insertion
    in Ableton Live 12 via the Live Object Model (LOM).
    """

    @classmethod
    def apply_clip_envelope(
        cls,
        conn: Any,
        track_index: int,
        clip_index: int,
        is_arrangement: bool = True,
        parameter_type: str = "volume",  # "volume", "panning", "send", "device_parameter"
        device_index: int = 0,
        parameter_name: Optional[str] = None,
        parameter_index: Optional[int] = None,
        send_index: int = 0,
        breakpoints: Optional[List[Union[EnvelopeBreakpoint, Dict[str, float]]]] = None,
        clear_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Injects an automation envelope into a Live 12 clip.

        Args:
            conn: Ableton connection adapter.
            track_index: Track index (0-based).
            clip_index: Index of clip in track.arrangement_clips (if arrangement) or clip_slots.
            is_arrangement: True for Arrangement View clips, False for Session clip slots.
            parameter_type: "volume", "panning", "send", or "device_parameter".
            device_index: Device index when parameter_type == "device_parameter".
            parameter_name: Name of device parameter to match.
            parameter_index: Direct index of device parameter (if known).
            send_index: Send index when parameter_type == "send".
            breakpoints: List of EnvelopeBreakpoint instances or dicts with {time, length, value}.
            clear_existing: Whether to clear existing envelopes on the parameter first.
        """
        points = breakpoints or []
        normalized_points: List[Dict[str, float]] = []
        for bp in points:
            if isinstance(bp, EnvelopeBreakpoint):
                normalized_points.append(bp.to_dict())
            elif isinstance(bp, dict):
                normalized_points.append({
                    "time": float(bp.get("time", bp.get("start", 0.0))),
                    "length": float(bp.get("length", bp.get("duration", 1.0))),
                    "value": float(bp.get("value", 0.5))
                })

        if conn is None or not hasattr(conn, "send_command"):
            return {
                "status": "MOCK_OK",
                "track_index": track_index,
                "clip_index": clip_index,
                "is_arrangement": is_arrangement,
                "parameter_type": parameter_type,
                "breakpoints_count": len(normalized_points),
                "has_envelopes": len(normalized_points) > 0
            }

        # Build LOM execution code to resolve clip and target parameter
        code = cls._build_envelope_injection_script(
            track_index=track_index,
            clip_index=clip_index,
            is_arrangement=is_arrangement,
            parameter_type=parameter_type,
            device_index=device_index,
            parameter_name=parameter_name,
            parameter_index=parameter_index,
            send_index=send_index,
            points=normalized_points,
            clear_existing=clear_existing
        )

        try:
            res = conn.send_command("execute_code", params={"code": code})
            result_data = res.get("result", res) if isinstance(res, dict) else res
            return {
                "status": "SUCCESS",
                "track_index": track_index,
                "clip_index": clip_index,
                "is_arrangement": is_arrangement,
                "parameter_type": parameter_type,
                "breakpoints_injected": len(normalized_points),
                "lom_result": result_data
            }
        except Exception as e:
            logger.error(f"Error applying clip envelope: {e}")
            return {
                "status": "ERROR",
                "track_index": track_index,
                "clip_index": clip_index,
                "error": str(e)
            }

    @classmethod
    def clear_clip_envelopes(
        cls,
        conn: Any,
        track_index: int,
        clip_index: int,
        is_arrangement: bool = True,
        parameter_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clears clip envelopes. If parameter_type is None, clears all envelopes via clip.clear_all_envelopes().
        """
        if conn is None or not hasattr(conn, "send_command"):
            return {"status": "MOCK_OK", "cleared": True}

        clip_locator = (
            f"song.tracks[{track_index}].arrangement_clips[{clip_index}]"
            if is_arrangement
            else f"song.tracks[{track_index}].clip_slots[{clip_index}].clip"
        )

        if parameter_type is None:
            code = f"""
clip = {clip_locator}
if hasattr(clip, 'clear_all_envelopes'):
    clip.clear_all_envelopes()
result = {{"cleared_all": True, "has_envelopes": getattr(clip, 'has_envelopes', False)}}
"""
        else:
            param_ref = cls._build_param_reference(track_index, parameter_type)
            code = f"""
clip = {clip_locator}
param = {param_ref}
if hasattr(clip, 'clear_envelope') and param is not None:
    clip.clear_envelope(param)
result = {{"cleared_param": "{parameter_type}", "has_envelopes": getattr(clip, 'has_envelopes', False)}}
"""

        try:
            res = conn.send_command("execute_code", params={"code": code})
            return {"status": "SUCCESS", "result": res.get("result", res)}
        except Exception as e:
            logger.error(f"Error clearing clip envelopes: {e}")
            return {"status": "ERROR", "error": str(e)}

    @classmethod
    def generate_filter_sweep_breakpoints(
        cls,
        clip_length: float,
        start_val: float = 0.1,
        end_val: float = 0.9,
        steps: int = 16,
        curve: str = "exponential"  # "linear", "exponential", "logarithmic"
    ) -> List[EnvelopeBreakpoint]:
        """Generates envelope breakpoints for an expressive filter sweep."""
        step_len = clip_length / max(1, steps)
        points: List[EnvelopeBreakpoint] = []
        for i in range(steps):
            t = i * step_len
            progress = i / max(1, steps - 1)
            if curve == "exponential":
                val = start_val + (end_val - start_val) * (progress ** 2)
            elif curve == "logarithmic":
                val = start_val + (end_val - start_val) * (progress ** 0.5)
            else:
                val = start_val + (end_val - start_val) * progress
            points.append(EnvelopeBreakpoint(time=t, length=step_len, value=val))
        return points

    @classmethod
    def generate_sidechain_duck_breakpoints(
        cls,
        bars: int = 4,
        duck_depth: float = 0.2,
        release_len: float = 0.75
    ) -> List[EnvelopeBreakpoint]:
        """Generates envelope breakpoints replicating 4-on-the-floor sidechain volume pump."""
        points: List[EnvelopeBreakpoint] = []
        total_beats = bars * 4
        for beat in range(total_beats):
            # Instant dip on downbeat
            points.append(EnvelopeBreakpoint(time=float(beat), length=0.25, value=duck_depth))
            # Smooth recovery over remainder of the beat
            points.append(EnvelopeBreakpoint(time=float(beat) + 0.25, length=release_len, value=1.0))
        return points

    @classmethod
    def _build_param_reference(cls, track_index: int, parameter_type: str) -> str:
        """Helper to generate Python snippet resolving track parameter."""
        t_ref = f"song.tracks[{track_index}]"
        if parameter_type == "volume":
            return f"{t_ref}.mixer_device.volume"
        elif parameter_type == "panning":
            return f"{t_ref}.mixer_device.panning"
        return f"{t_ref}.mixer_device.volume"

    @classmethod
    def _build_envelope_injection_script(
        cls,
        track_index: int,
        clip_index: int,
        is_arrangement: bool,
        parameter_type: str,
        device_index: int,
        parameter_name: Optional[str],
        parameter_index: Optional[int],
        send_index: int,
        points: List[Dict[str, float]],
        clear_existing: bool
    ) -> str:
        """Constructs safe Python code executed inside Live 12 to build clip envelopes."""
        clip_locator = (
            f"song.tracks[{track_index}].arrangement_clips[{clip_index}]"
            if is_arrangement
            else f"song.tracks[{track_index}].clip_slots[{clip_index}].clip"
        )

        param_resolution = ""
        if parameter_type == "volume":
            param_resolution = f"param = song.tracks[{track_index}].mixer_device.volume"
        elif parameter_type == "panning":
            param_resolution = f"param = song.tracks[{track_index}].mixer_device.panning"
        elif parameter_type == "send":
            param_resolution = f"""
sends = list(song.tracks[{track_index}].mixer_device.sends)
param = sends[{send_index}] if {send_index} < len(sends) else song.tracks[{track_index}].mixer_device.volume
"""
        elif parameter_type == "device_parameter":
            if parameter_name:
                param_resolution = f"""
param = None
t = song.tracks[{track_index}]
if {device_index} < len(t.devices):
    dev = t.devices[{device_index}]
    for p in dev.parameters:
        if p.name.lower() == "{parameter_name.lower()}":
            param = p
            break
if param is None:
    param = t.mixer_device.volume
"""
            elif parameter_index is not None:
                param_resolution = f"""
t = song.tracks[{track_index}]
param = t.devices[{device_index}].parameters[{parameter_index}] if {device_index} < len(t.devices) else t.mixer_device.volume
"""
            else:
                param_resolution = f"param = song.tracks[{track_index}].mixer_device.volume"

        # Serialize points into code
        points_repr = str(points)

        script = f"""
clip = {clip_locator}
{param_resolution}

if hasattr(clip, 'create_automation_envelope') and param is not None:
    if {clear_existing} and hasattr(clip, 'clear_envelope'):
        try:
            clip.clear_envelope(param)
        except Exception:
            pass
    env = clip.create_automation_envelope(param)
    points_to_inject = {points_repr}
    for pt in points_to_inject:
        t_start = float(pt.get("time", 0.0))
        t_len = float(pt.get("length", 1.0))
        val = float(pt.get("value", 0.5))
        env.insert_step(t_start, t_len, val)

result = {{
    "clip_name": getattr(clip, 'name', ''),
    "has_envelopes": getattr(clip, 'has_envelopes', False),
    "steps_inserted": len({points_repr})
}}
"""
        return script
