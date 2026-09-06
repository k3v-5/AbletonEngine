"""
engine/midi/program_change.py - MIDI Program Change & Bank Dispatcher.

Handles MIDI Program Change (0-127) and Bank Select (CC0 MSB / CC32 LSB) configuration for:
- Arturia Analog Lab V (Playlists & Stage Mode)
- Spectrasonics Omnisphere (Live Mode slots)
- Native Instruments Massive (Program List)
- Roland Cloud ZENOLOGY (Roland Tone Banks)
"""

from typing import Dict, Any, Optional, Tuple


class MIDIProgramChangeDispatcher:
    """Manages Program Change and Bank parameters for VST synthesizers."""

    @staticmethod
    def resolve_program_change(
        plugin_name: str,
        preset_name_or_id: Any,
        playlist_or_bank: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Translates a preset request into standard MIDI Program Change and Bank parameters.

        Args:
            plugin_name: Name of the plugin (e.g. 'Analog Lab V', 'Omnisphere', 'Massive', 'ZENOLOGY')
            preset_name_or_id: Integer index (0-127) or string preset name
            playlist_or_bank: Optional playlist index (for Analog Lab) or bank (for Zenology)

        Returns:
            Dict containing:
                - program: int (0-127)
                - bank_msb: Optional[int] (CC0)
                - bank_lsb: Optional[int] (CC32)
                - description: str
        """
        p_lower = plugin_name.lower()

        # Extract numeric ID if provided, default to 0
        if isinstance(preset_name_or_id, int):
            pc_id = max(0, min(127, preset_name_or_id))
        else:
            # Hash or default to 0
            pc_id = 0

        if "analog lab" in p_lower:
            # Analog Lab Playlists:
            # Bank MSB = Playlist Index (0..127)
            # Bank LSB = Song Index (0..127)
            # Program = Preset Index (0..127)
            b_msb = playlist_or_bank if playlist_or_bank is not None else 0
            b_lsb = 0
            return {
                "plugin": "Analog Lab V",
                "method": "midi_program_change",
                "program": pc_id,
                "bank_msb": b_msb,
                "bank_lsb": b_lsb,
                "description": f"Analog Lab Playlist #{b_msb+1}, Song #{b_lsb+1}, Preset #{pc_id+1}"
            }

        elif "omnisphere" in p_lower:
            # Omnisphere Live Mode:
            # Program Change selects Part 1-8 or Multi slot
            # Host Automation ID 0-7 = Parameter 1-8 Level
            # CC 7 Channel 1-8 = Parameter 1-8 Level
            # CC 10 Channel 1-8 = Parameter 1-8 Pan
            slot = pc_id % 8
            return {
                "plugin": "Omnisphere",
                "method": "midi_program_change",
                "program": slot,
                "bank_msb": None,
                "bank_lsb": None,
                "host_automation_id": slot,
                "midi_cc_level": {"cc": 7, "channel": slot + 1},
                "midi_cc_pan": {"cc": 10, "channel": slot + 1},
                "description": f"Omnisphere Live Mode Part/Slot #{slot+1} (Program Change {slot}, Host Automation ID {slot}, Level CC7 Ch{slot+1}, Pan CC10 Ch{slot+1})"
            }

        elif "massive" in p_lower:
            # Massive Program List:
            # Program Change 0-127
            return {
                "plugin": "Massive",
                "method": "midi_program_change",
                "program": pc_id,
                "bank_msb": None,
                "bank_lsb": None,
                "description": f"Massive Program List #{pc_id+1} (Program Change {pc_id})"
            }

        elif "zenology" in p_lower or "roland" in p_lower:
            # Roland ZEN-Core Tones:
            # Bank MSB + LSB + Program Change
            bank = playlist_or_bank if playlist_or_bank is not None else 0
            return {
                "plugin": "ZENOLOGY",
                "method": "midi_program_change",
                "program": pc_id,
                "bank_msb": bank,
                "bank_lsb": 0,
                "description": f"Roland ZENOLOGY Tone #{pc_id+1} (Bank {bank}, PC {pc_id})"
            }

        else:
            # Generic VST Program Change
            return {
                "plugin": plugin_name,
                "method": "midi_program_change",
                "program": pc_id,
                "bank_msb": playlist_or_bank,
                "bank_lsb": 0 if playlist_or_bank is not None else None,
                "description": f"Standard MIDI Program Change #{pc_id} on {plugin_name}"
            }

    @classmethod
    def send_program_change(
        cls,
        conn: Any = None,
        track_index: int = 0,
        program: int = 0,
        bank: Optional[int] = None,
        plugin_name: str = "Analog Lab V"
    ) -> Dict[str, Any]:
        """
        Dispatches MIDI Program Change and Bank parameters to Ableton Live.
        Executes MIDI dispatch via Remote Script if connected.
        """
        pc_config = cls.resolve_program_change(
            plugin_name=plugin_name,
            preset_name_or_id=program,
            playlist_or_bank=bank
        )

        results = {
            "status": "success",
            "track_index": track_index,
            "program": program,
            "bank": bank,
            "plugin": plugin_name,
            "config": pc_config,
            "midi_dispatched": False
        }

        if conn is not None and hasattr(conn, "send_command"):
            try:
                prog_val = max(0, min(127, int(program)))
                bank_val = max(0, min(127, int(bank))) if bank is not None else 0
                midi_code = f"""
try:
    c_inst = self._c_instance if hasattr(self, '_c_instance') else None
    if c_inst and hasattr(c_inst, 'send_midi'):
        c_inst.send_midi((0xB0, 0, {bank_val}))
        c_inst.send_midi((0xC0, {prog_val}))
except Exception:
    pass
"""
                conn.send_command("execute_code", {"code": midi_code})
                results["midi_dispatched"] = True
            except Exception as e:
                results["midi_error"] = str(e)

        return results


program_change_dispatcher = MIDIProgramChangeDispatcher()

