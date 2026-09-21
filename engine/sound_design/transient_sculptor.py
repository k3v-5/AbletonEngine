# engine/sound_design/transient_sculptor.py
"""
Transient Sculptor (Family 3):
Separates and independently shapes the 4 key envelope stages of an acoustic event:
- Attack     (0 - 15 ms)   : Initial click, beater, pick strike
- Transient  (15 - 40 ms)  : Tonal snap, knock, front harmonic punch
- Body       (40 - 250 ms) : Fundamental weight, core pitch sustain
- Tail       (250 ms+)     : Acoustic room decay, convolution release, resonance
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("TransientSculptor")


class EnvelopeZone(str, Enum):
    ATTACK = "ATTACK"          # 0 to 15 ms
    TRANSIENT = "TRANSIENT"    # 15 to 40 ms
    BODY = "BODY"              # 40 to 250 ms
    TAIL = "TAIL"              # 250 ms and beyond


@dataclass
class ZoneSculptConfig:
    """Processing profile for an isolated envelope zone."""
    zone: EnvelopeZone
    time_window_ms: tuple[float, float]
    drive_db: float = 0.0
    brightness_tilt_db: float = 0.0
    stereo_width_pct: float = 100.0
    character_action: str = "transparent"
    suggested_devices: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone": self.zone.value if isinstance(self.zone, EnvelopeZone) else str(self.zone),
            "time_window_ms": list(self.time_window_ms),
            "drive_db": round(self.drive_db, 1),
            "brightness_tilt_db": round(self.brightness_tilt_db, 1),
            "stereo_width_pct": round(self.stereo_width_pct, 1),
            "character_action": self.character_action,
            "suggested_devices": list(self.suggested_devices),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ZoneSculptConfig:
        zone_str = data.get("zone", "TRANSIENT")
        try:
            zone = EnvelopeZone(zone_str)
        except ValueError:
            zone = EnvelopeZone.TRANSIENT
        win = data.get("time_window_ms", [0.0, 40.0])
        return cls(
            zone=zone,
            time_window_ms=(float(win[0]), float(win[1])),
            drive_db=float(data.get("drive_db", 0.0)),
            brightness_tilt_db=float(data.get("brightness_tilt_db", 0.0)),
            stereo_width_pct=float(data.get("stereo_width_pct", 100.0)),
            character_action=data.get("character_action", "transparent"),
            suggested_devices=data.get("suggested_devices", []),
        )


@dataclass
class TransientSculptProfile:
    """A complete multi-zone sculpting profile for a specific instrument or stem."""
    element_name: str
    zones: Dict[EnvelopeZone, ZoneSculptConfig] = field(default_factory=dict)
    summary_intent: str = ""

    def get_zone(self, zone: EnvelopeZone) -> Optional[ZoneSculptConfig]:
        return self.zones.get(zone)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "element_name": self.element_name,
            "zones": {k.value if isinstance(k, EnvelopeZone) else str(k): v.to_dict() for k, v in self.zones.items()},
            "summary_intent": self.summary_intent,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TransientSculptProfile:
        zones_raw = data.get("zones", {})
        zones = {}
        for k, v in zones_raw.items():
            try:
                zone_key = EnvelopeZone(k)
            except ValueError:
                zone_key = EnvelopeZone.TRANSIENT
            zones[zone_key] = ZoneSculptConfig.from_dict(v)
        return cls(
            element_name=data.get("element_name", "Instrument"),
            zones=zones,
            summary_intent=data.get("summary_intent", ""),
        )


class TransientSculptor:
    """
    Factory creating multi-stage envelope profiles tailored for drums, bass, and harmony.
    """

    @classmethod
    def sculpt_kick(cls, is_aggressive: bool = True) -> TransientSculptProfile:
        """
        Kick:
        - Attack: Sharp click boost (+3.5 dB brightness) for speaker cut.
        - Transient: Aggressive saturation (+4.5 dB drive) for punch.
        - Body: Pure clean sub (mono, 0 dB drive, unclipped 55 Hz).
        - Tail: Controlled gate to keep room clean.
        """
        zones = {
            EnvelopeZone.ATTACK: ZoneSculptConfig(
                zone=EnvelopeZone.ATTACK,
                time_window_ms=(0.0, 12.0),
                drive_db=2.0 if is_aggressive else 0.5,
                brightness_tilt_db=+3.5,
                stereo_width_pct=0.0,  # keep center
                character_action="High-frequency beater click emphasis for mobile speakers",
                suggested_devices=["EQ Eight (Peak @ 3.2 kHz)", "Drum Buss (Transients)"]
            ),
            EnvelopeZone.TRANSIENT: ZoneSculptConfig(
                zone=EnvelopeZone.TRANSIENT,
                time_window_ms=(12.0, 35.0),
                drive_db=4.5 if is_aggressive else 2.0,
                brightness_tilt_db=+1.0,
                stereo_width_pct=0.0,
                character_action="Analog clip saturation for chest-impact knock",
                suggested_devices=["Saturator (Analog Clip)", "Glue Compressor (Fast Attack)"]
            ),
            EnvelopeZone.BODY: ZoneSculptConfig(
                zone=EnvelopeZone.BODY,
                time_window_ms=(35.0, 180.0),
                drive_db=0.0,  # Zero drive to preserve pristine sub dynamics
                brightness_tilt_db=-3.0,
                stereo_width_pct=0.0,
                character_action="Pure unclipped sub-bass sine wave sustain (50-65 Hz)",
                suggested_devices=["Utility (Bass Mono @ 120 Hz)"]
            ),
            EnvelopeZone.TAIL: ZoneSculptConfig(
                zone=EnvelopeZone.TAIL,
                time_window_ms=(180.0, 400.0),
                drive_db=0.0,
                brightness_tilt_db=-6.0,
                stereo_width_pct=0.0,
                character_action="Tight gated decay preventing sub overlap with bass line",
                suggested_devices=["Gate (Fast Release @ 100 ms)"]
            ),
        }
        return TransientSculptProfile(
            element_name="Kick Drum",
            zones=zones,
            summary_intent="Hard-hitting punchy beater combined with clean, unclipped sub fundamental."
        )

    @classmethod
    def sculpt_piano(cls) -> TransientSculptProfile:
        """
        Piano:
        - Attack: Bright percussive hammer strike (+2.0 dB brightness).
        - Transient: Gentle tape glue (+1.5 dB drive).
        - Body: Warm, dark harmonic sustain (-2.5 dB brightness tilt).
        - Tail: Wide spatial diffusion (130% width).
        """
        zones = {
            EnvelopeZone.ATTACK: ZoneSculptConfig(
                zone=EnvelopeZone.ATTACK,
                time_window_ms=(0.0, 15.0),
                drive_db=0.5,
                brightness_tilt_db=+2.0,
                stereo_width_pct=100.0,
                character_action="Percussive felt-hammer bite and tactile articulation",
                suggested_devices=["EQ Eight (High Shelf @ 5 kHz)"]
            ),
            EnvelopeZone.TRANSIENT: ZoneSculptConfig(
                zone=EnvelopeZone.TRANSIENT,
                time_window_ms=(15.0, 50.0),
                drive_db=1.8,
                brightness_tilt_db=0.0,
                stereo_width_pct=110.0,
                character_action="Warm analog tube rounding of sharp peaks",
                suggested_devices=["Saturator (Soft Sine)"]
            ),
            EnvelopeZone.BODY: ZoneSculptConfig(
                zone=EnvelopeZone.BODY,
                time_window_ms=(50.0, 300.0),
                drive_db=0.0,
                brightness_tilt_db=-2.5,
                stereo_width_pct=100.0,
                character_action="Warm, dark Neo-Soul harmonic body with vocal-range notch",
                suggested_devices=["EQ Eight (Notch @ 440 Hz)"]
            ),
            EnvelopeZone.TAIL: ZoneSculptConfig(
                zone=EnvelopeZone.TAIL,
                time_window_ms=(300.0, 1200.0),
                drive_db=0.0,
                brightness_tilt_db=-1.0,
                stereo_width_pct=135.0,
                character_action="Stereo chorus expansion and lush reverbed halo",
                suggested_devices=["Chorus-Ensemble", "ValhallaVintageVerb"]
            ),
        }
        return TransientSculptProfile(
            element_name="Neo-Soul Rhodes",
            zones=zones,
            summary_intent="Clear acoustic finger strike transitioning into warm, dark, stereophonic sustain."
        )
