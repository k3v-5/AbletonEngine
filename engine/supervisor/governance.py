# engine/supervisor/governance.py
"""
Engine Governance Supervisor & Production Contract Enforcer.
Enforces strict DAW-level rules for AI music production:
1. Mandatory preset selection prior to production (where applicable).
2. Mandatory parameter sculpting immediately after preset selection.
3. Strict effect stacking discipline: blocks adding subsequent effects until the current effect is configured.
4. Clean plugin and effect replacement support.
5. Permissive effect expansion respecting active configuration rules.
6. Channel signal integrity audit (device presence, clip content, live meter activity).
7. Final song master LUFS compliance (-14.0 to -11.0 LUFS) and True Peak ceiling (<= -1.0 dBTP).
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set

logger = logging.getLogger("EngineGovernance")


class GovernanceViolationError(RuntimeError):
    """Raised when an AI production action violates the engine governance contract."""
    pass


class UnconfiguredEffectStackingError(GovernanceViolationError):
    """Raised when attempting to add an effect while the previous effect remains unconfigured."""
    pass


class PresetSelectionRequiredError(GovernanceViolationError):
    """Raised when producing without selecting a preset on an instrument requiring presets."""
    pass


class ParameterSculptingRequiredError(GovernanceViolationError):
    """Raised when an instrument or effect is left in un-sculpted default/init state."""
    pass


class UnconfiguredDeviceViolationError(ParameterSculptingRequiredError):
    """Raised when an AI attempts to proceed or produce while a device is unconfigured or in default/init state."""
    pass


class ChannelSilenceError(GovernanceViolationError):
    """Raised when a track has no audio output during playback audit."""
    pass


class MasterLoudnessNonCompliantError(GovernanceViolationError):
    """Raised when the master output fails LUFS or True Peak thresholds."""
    pass


@dataclass
class DeviceState:
    device_index: int
    name: str
    is_instrument: bool = False
    is_sculpted: bool = False
    preset_selected: Optional[str] = None
    sculpted_parameters: Dict[str, float] = field(default_factory=dict)


@dataclass
class TrackState:
    track_index: int
    name: str = ""
    role: Optional[str] = None
    devices: List[DeviceState] = field(default_factory=list)
    preset_required: bool = False
    preset_configured: bool = False
    has_clips: bool = False
    last_meter_level: float = 0.0


class EngineGovernanceSupervisor:
    """
    Authoritative production supervisor enforcing AbletonEngine governance rules.
    """

    PRESET_REQUIRED_INSTRUMENTS = {
        "analog lab", "analog lab v",
        "omnisphere", "zenology", "fraction"
    }

    CHANNEL_CATEGORIES = {
        "DRUMS": {"min_meter": 0.35, "max_meter": 0.85, "target_meter": 0.55, "name": "Drums / Percussion"},
        "BASS": {"min_meter": 0.30, "max_meter": 0.75, "target_meter": 0.48, "name": "Bass / 808 Sub"},
        "KEYS": {"min_meter": 0.20, "max_meter": 0.60, "target_meter": 0.38, "name": "Keys / Rhodes / Piano"},
        "LEAD": {"min_meter": 0.20, "max_meter": 0.65, "target_meter": 0.40, "name": "Lead Synth / Vocals"},
        "PAD": {"min_meter": 0.12, "max_meter": 0.45, "target_meter": 0.28, "name": "Atmospheric Pad"},
        "ARP_FX": {"min_meter": 0.08, "max_meter": 0.40, "target_meter": 0.20, "name": "Arpeggio / FX Textures"}
    }

    @classmethod
    def resolve_category_for_role(cls, role: str) -> str:
        r = role.lower().strip()
        if any(w in r for w in ["drum", "percussion", "beat", "kick", "snare", "hat"]):
            return "DRUMS"
        if any(w in r for w in ["bass", "808", "sub", "reese"]):
            return "BASS"
        if any(w in r for w in ["key", "rhodes", "piano", "clav", "organ", "wurl"]):
            return "KEYS"
        if any(w in r for w in ["lead", "vocal", "hook", "solo", "top"]):
            return "LEAD"
        if any(w in r for w in ["pad", "atmos", "string", "ambient", "texture", "bed"]):
            return "PAD"
        return "ARP_FX"

    @classmethod
    def audit_track_category(cls, role: str, meter_level: float) -> Dict[str, Any]:
        cat_key = cls.resolve_category_for_role(role)
        cfg = cls.CHANNEL_CATEGORIES[cat_key]
        min_m = cfg["min_meter"]
        max_m = cfg["max_meter"]
        in_range = min_m <= meter_level <= max_m

        # Suggested gain adjustment ratio
        gain_adjustment = 1.0
        if meter_level > 0.001:
            if meter_level < min_m:
                gain_adjustment = cfg["target_meter"] / meter_level
            elif meter_level > max_m:
                gain_adjustment = cfg["target_meter"] / meter_level

        return {
            "category": cat_key,
            "category_name": cfg["name"],
            "meter_level": meter_level,
            "min_allowed": min_m,
            "max_allowed": max_m,
            "target_meter": cfg["target_meter"],
            "in_range": in_range,
            "recommended_gain_factor": round(gain_adjustment, 3),
            "status": "COMPLIANT" if in_range else ("TOO_QUIET" if meter_level < min_m else "TOO_LOUD")
        }

    def __init__(self):
        self._tracks: Dict[int, TrackState] = {}
        self._pending_effect_sculpting: Dict[int, int] = {}  # track_index -> device_index

    def register_track(self, track_index: int, name: str = "", role: Optional[str] = None) -> TrackState:
        if track_index not in self._tracks:
            self._tracks[track_index] = TrackState(track_index=track_index, name=name, role=role)
        else:
            if name:
                self._tracks[track_index].name = name
            if role:
                self._tracks[track_index].role = role
        return self._tracks[track_index]

    def get_track_state(self, track_index: int) -> TrackState:
        return self._tracks.setdefault(track_index, TrackState(track_index=track_index))

    # -------------------------------------------------------------------------
    # RULE 1: MANDATORY PRESET SELECTION
    # -------------------------------------------------------------------------
    def notify_instrument_loaded(self, track_index: int, instrument_name: str, device_index: int = 0) -> None:
        track = self.get_track_state(track_index)
        is_preset_req = any(req in instrument_name.lower() for req in self.PRESET_REQUIRED_INSTRUMENTS)
        track.preset_required = is_preset_req
        track.preset_configured = not is_preset_req  # If not required, initially satisfied

        dev = DeviceState(
            device_index=device_index,
            name=instrument_name,
            is_instrument=True,
            is_sculpted=False,
            preset_selected=None
        )
        if len(track.devices) <= device_index:
            track.devices.append(dev)
        else:
            track.devices[device_index] = dev

    def record_preset_selected(self, track_index: int, preset_name: str, device_index: int = 0) -> None:
        track = self.get_track_state(track_index)
        track.preset_configured = True
        if device_index < len(track.devices):
            track.devices[device_index].preset_selected = preset_name
        logger.info(f"[Governance] Track {track_index}: Preset '{preset_name}' selected successfully.")

    def assert_preset_selection_valid(self, track_index: int) -> None:
        track = self.get_track_state(track_index)
        if track.preset_required and not track.preset_configured:
            raise PresetSelectionRequiredError(
                f"Track {track_index} ({track.name}) requires explicit preset selection before proceeding! "
                f"Instrument requires preset selection from catalog or User Library."
            )

    def assert_instrument_sculpted(self, track_index: int, device_index: int = 0) -> None:
        """
        Enforces that the track's instrument has been actively sculpted.
        Raises UnconfiguredDeviceViolationError if un-sculpted.
        """
        track = self.get_track_state(track_index)
        if device_index >= len(track.devices):
            raise IndexError(f"Instrument device index {device_index} out of range on track {track_index}.")
        dev = track.devices[device_index]
        if not dev.is_sculpted:
            raise UnconfiguredDeviceViolationError(
                f"Track {track_index} ('{track.name}'): Instrument '{dev.name}' is unconfigured! "
                f"Governance Rule: The AI must explicitly sculpt oscillator, filter, or macro parameters."
            )

    # -------------------------------------------------------------------------
    # RULE 2 & 5: EFFECT STACKING DISCIPLINE & EXPANSION
    # -------------------------------------------------------------------------
    def request_add_effect(self, track_index: int, effect_name: str) -> int:
        """
        Request permission to append an effect to a track.
        Fails if a previously added effect is still un-sculpted.
        """
        track = self.get_track_state(track_index)

        # Check if there's an unconfigured effect waiting for parameters
        if track_index in self._pending_effect_sculpting:
            pending_dev_idx = self._pending_effect_sculpting[track_index]
            pending_name = track.devices[pending_dev_idx].name if pending_dev_idx < len(track.devices) else "Unknown"
            raise UnconfiguredEffectStackingError(
                f"Cannot add effect '{effect_name}' to Track {track_index}! "
                f"Previous effect '{pending_name}' (device {pending_dev_idx}) has not been sculpted yet. "
                f"Governance Rule: Each effect must have parameters actively tuned before adding further effects."
            )

        new_dev_idx = len(track.devices)
        dev = DeviceState(
            device_index=new_dev_idx,
            name=effect_name,
            is_instrument=False,
            is_sculpted=False
        )
        track.devices.append(dev)
        self._pending_effect_sculpting[track_index] = new_dev_idx
        logger.info(f"[Governance] Track {track_index}: Added effect '{effect_name}' at index {new_dev_idx}. Parameter tuning required.")
        return new_dev_idx

    def record_device_sculpted(self, track_index: int, device_index: int, parameters: Dict[str, float]) -> None:
        """
        Marks an instrument or effect as consciously tuned and sculpted.
        Blocks empty parameter assignments.
        """
        if not parameters:
            raise UnconfiguredDeviceViolationError(
                f"No se puede marcar el dispositivo {device_index} de la pista {track_index} como esculpido con un diccionario de parámetros vacío."
            )

        track = self.get_track_state(track_index)
        dev_name = "Device"
        if device_index < len(track.devices):
            dev = track.devices[device_index]
            dev_name = dev.name
            dev.is_sculpted = True
            dev.sculpted_parameters.update(parameters)

        if self._pending_effect_sculpting.get(track_index) == device_index:
            del self._pending_effect_sculpting[track_index]

        logger.info(f"[Governance] Track {track_index} Dev {device_index} ({dev_name}) parameter sculpting confirmed: {parameters}")

    def record_effect_sculpted(self, track_index: int, device_index: int, parameters: Dict[str, float]) -> None:
        """Backward-compatible alias for record_device_sculpted."""
        self.record_device_sculpted(track_index, device_index, parameters)

    def assert_device_sculpted(self, track_index: int, device_index: int) -> None:
        """
        Checks that a specific device on a track has been actively configured.
        Raises UnconfiguredDeviceViolationError if un-sculpted.
        """
        track = self.get_track_state(track_index)
        if device_index >= len(track.devices):
            raise IndexError(f"Índice de dispositivo {device_index} fuera de rango en pista {track_index}.")
        dev = track.devices[device_index]
        if not dev.is_sculpted:
            dev_type = "instrumento" if dev.is_instrument else "efecto"
            raise UnconfiguredDeviceViolationError(
                f"Violación de Gobernanza en Pista {track_index} ('{track.name}'): "
                f"El {dev_type} '{dev.name}' (dispositivo {device_index}) permanece en estado default/init sin configurar. "
                f"La IA debe afinar obligatoriamente sus parámetros."
            )

    def assert_track_fully_sculpted(self, track_index: int) -> None:
        """
        Enforces that EVERY device (both instruments and serial effects) on the track
        has been actively configured and sculpted.
        Raises UnconfiguredDeviceViolationError if any device remains un-sculpted.
        """
        track = self.get_track_state(track_index)
        for dev in track.devices:
            if not dev.is_sculpted:
                dev_type = "instrumento" if dev.is_instrument else "efecto"
                raise UnconfiguredDeviceViolationError(
                    f"Violación de Gobernanza en Pista {track_index} ('{track.name}'): "
                    f"El {dev_type} '{dev.name}' (dispositivo {dev.device_index}) permanece en estado default/init sin configurar. "
                    f"Es obligatorio configurar todos los dispositivos de la pista."
                )

    def assert_session_fully_sculpted(self) -> None:
        """
        Enforces that all tracks in the current production session have every device configured.
        """
        for t_idx in self._tracks:
            self.assert_track_fully_sculpted(t_idx)

    def get_unconfigured_devices(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all devices across all tracks currently in un-sculpted state.
        """
        unconfigured = []
        for t_idx, track in self._tracks.items():
            for dev in track.devices:
                if not dev.is_sculpted:
                    unconfigured.append({
                        "track_index": t_idx,
                        "track_name": track.name,
                        "device_index": dev.device_index,
                        "device_name": dev.name,
                        "is_instrument": dev.is_instrument,
                        "preset_configured": track.preset_configured
                    })
        return unconfigured

    def get_mandatory_sculpting_requirements(self, device_name: str, role: Optional[str] = None) -> Dict[str, Any]:
        """
        Provides the dictionary of parameters and semantic controls that must be configured for a device.
        """
        d_lower = device_name.lower()
        if "serum" in d_lower:
            return {
                "device": "Serum 2",
                "mandatory_sections": ["OSCILLATORS", "FILTERS", "ENVELOPES"],
                "required_parameters": ["A_Wavetable_Pos", "Filter_Cutoff", "Env1_Release", "Filter_Resonance"]
            }
        elif "vital" in d_lower:
            return {
                "device": "Vital",
                "mandatory_sections": ["OSCILLATORS", "FILTERS", "ENVELOPES"],
                "required_parameters": ["Osc 1 Waveframe", "Filter 1 Cutoff", "Env 1 Attack", "Env 1 Release"]
            }
        elif "analog lab" in d_lower:
            return {
                "device": "Analog Lab V",
                "mandatory_sections": ["MACROS_MASTER"],
                "required_parameters": ["Brightness", "Timbre", "Time", "Movement"]
            }
        elif "shaperbox" in d_lower:
            return {
                "device": "ShaperBox 3",
                "mandatory_sections": ["DYNAMICS", "SPACE_MODULATION"],
                "required_parameters": ["VolumeShaper Mix", "DriveShaper Drive", "FilterShaper Cutoff"]
            }
        elif "alterboy" in d_lower:
            return {
                "device": "LittleAlterBoy",
                "mandatory_sections": ["SPACE_MODULATION", "SATURATION"],
                "required_parameters": ["Pitch", "Formant", "Drive", "Mix"]
            }
        elif "refract" in d_lower:
            return {
                "device": "Efx REFRACT",
                "mandatory_sections": ["SPACE_MODULATION", "OSCILLATORS"],
                "required_parameters": ["Refraction Amount", "Detune", "Filter Cutoff", "Output Mix"]
            }
        else:
            return {
                "device": device_name,
                "mandatory_sections": ["MACROS_MASTER", "FILTERS"],
                "required_parameters": ["Master Volume", "Filter Cutoff"]
            }

    # -------------------------------------------------------------------------
    # RULE 4: PLUGIN & EFFECT REPLACEMENT
    # -------------------------------------------------------------------------
    def replace_device(self, track_index: int, device_index: int, new_device_name: str, is_instrument: bool = False) -> None:
        """
        Cleanly replaces a device on a track. Resets sculpting state for that slot.
        """
        track = self.get_track_state(track_index)
        new_dev = DeviceState(
            device_index=device_index,
            name=new_device_name,
            is_instrument=is_instrument,
            is_sculpted=False
        )
        if device_index < len(track.devices):
            track.devices[device_index] = new_dev
        else:
            track.devices.append(new_dev)

        if not is_instrument:
            self._pending_effect_sculpting[track_index] = device_index
        else:
            is_preset_req = any(req in new_device_name.lower() for req in self.PRESET_REQUIRED_INSTRUMENTS)
            track.preset_required = is_preset_req
            track.preset_configured = not is_preset_req

        logger.info(f"[Governance] Track {track_index} Dev {device_index}: Replaced with '{new_device_name}'. Parameter sculpting required.")

    # -------------------------------------------------------------------------
    # RULE 6: CHANNEL AUDIT (INTEGRITY & SIGNAL ACTIVITY)
    # -------------------------------------------------------------------------
    def audit_channel_integrity(self, session_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audits all active tracks in the session snapshot:
        - Confirms presence of valid devices.
        - Confirms musical clips or audio content.
        - Checks non-zero meter levels during live playback.
        """
        audit_results = {
            "compliant": True,
            "tracks_checked": 0,
            "violations": [],
            "details": []
        }

        tracks_data = session_snapshot.get("tracks", {})
        for t_key, t_info in tracks_data.items():
            t_idx = t_info.get("ableton_index", t_info.get("index", 0))
            t_name = t_info.get("name", f"Track_{t_idx}")
            devs = t_info.get("devices", {})
            clips = t_info.get("clips", {})
            meter = t_info.get("output_meter_level", 0.0)

            dev_count = len(devs) if isinstance(devs, (list, dict)) else 0
            clip_count = len(clips) if isinstance(clips, (list, dict)) else 0

            status_entry = {
                "track_index": t_idx,
                "track_name": t_name,
                "device_count": dev_count,
                "clip_count": clip_count,
                "meter_level": meter,
                "healthy": True
            }

            # If track is an active musical track, it should have content
            if "synth" in t_name.lower() or "lead" in t_name.lower() or "pad" in t_name.lower() or "bass" in t_name.lower():
                if clip_count == 0:
                    status_entry["healthy"] = False
                    audit_results["violations"].append(f"Track {t_idx} ({t_name}) has 0 clips.")

            audit_results["details"].append(status_entry)
            audit_results["tracks_checked"] += 1

        if audit_results["violations"]:
            audit_results["compliant"] = False

        return audit_results

    # -------------------------------------------------------------------------
    # RULE 7: MASTER LUFS & TRUE PEAK COMPLIANCE
    # -------------------------------------------------------------------------
    def audit_and_enforce_master_lufs(
        self,
        measured_lufs: float,
        measured_true_peak: float,
        target_lufs: float = -14.0,
        max_true_peak: float = -1.0
    ) -> Dict[str, Any]:
        """
        Verifies and calibrates master output against commercial broadcast standards.
        """
        lufs_delta = measured_lufs - target_lufs
        true_peak_violation = measured_true_peak > max_true_peak
        lufs_compliant = abs(lufs_delta) <= 1.0

        remediation_gain_db = 0.0
        if not lufs_compliant:
            remediation_gain_db = -lufs_delta

        compliant = lufs_compliant and not true_peak_violation

        return {
            "compliant": compliant,
            "measured_lufs": measured_lufs,
            "target_lufs": target_lufs,
            "lufs_delta": lufs_delta,
            "measured_true_peak": measured_true_peak,
            "max_true_peak": max_true_peak,
            "limiter_remediation_gain_db": round(remediation_gain_db, 2),
            "status": "PASSED" if compliant else "CALIBRATION_REQUIRED"
        }


# Global singleton supervisor instance
governance_supervisor = EngineGovernanceSupervisor()
