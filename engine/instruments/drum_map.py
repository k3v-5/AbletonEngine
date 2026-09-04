# engine/instruments/drum_map.py
from typing import Dict, Optional
from .roles import InstrumentRole

class DrumMap:
    """Canonical single source of truth mapping between MIDI note pitches and drum roles.
    
    Ensures absolute mathematical consistency:
    Music Engine DrumMap == Ableton Drum Rack DrumMap
    """
    KICK: int = 36          # C1
    KICK_ALT: int = 37      # C#1
    SNARE: int = 38         # D1
    CLAP: int = 39          # D#1
    CLOSED_HAT: int = 40    # E1
    OPEN_HAT: int = 41      # F1
    PERC_1: int = 42        # F#1
    PERC_2: int = 43        # G1
    SHAKER: int = 44        # G#1
    TOM: int = 45           # A1
    FX: int = 46            # A#1
    IMPACT: int = 47        # B1

    # Canonical note to role map
    NOTE_TO_ROLE: Dict[int, InstrumentRole] = {
        36: InstrumentRole.KICK,
        37: InstrumentRole.KICK_ALT,
        38: InstrumentRole.SNARE,
        39: InstrumentRole.CLAP,
        40: InstrumentRole.CLOSED_HAT,
        41: InstrumentRole.OPEN_HAT,
        42: InstrumentRole.PERC_1,
        43: InstrumentRole.PERC_2,
        44: InstrumentRole.SHAKER,
        45: InstrumentRole.TOM,
        46: InstrumentRole.FX,
        47: InstrumentRole.IMPACT,
    }

    # Role to primary note map
    ROLE_TO_NOTE: Dict[str, int] = {
        "KICK": 36,
        "KICK_ALT": 37,
        "SNARE": 38,
        "CLAP": 39,
        "CLOSED_HAT": 40,
        "OPEN_HAT": 41,
        "PERCUSSION": 42,
        "PERC_1": 42,
        "PERC_2": 43,
        "SHAKER": 44,
        "TOM": 45,
        "FX": 46,
        "IMPACT": 47,
        "VOCAL_CHOP": 46,
    }

    # Standard visible pad display names
    PAD_DISPLAY_NAMES: Dict[int, str] = {
        36: "C1 KICK",
        37: "C#1 KICK ALT",
        38: "D1 SNARE",
        39: "D#1 CLAP",
        40: "E1 CLOSED HAT",
        41: "F1 OPEN HAT",
        42: "F#1 PERC 1",
        43: "G1 PERC 2",
        44: "G#1 SHAKER",
        45: "A1 TOM",
        46: "A#1 FX",
        47: "B1 IMPACT",
    }

    @classmethod
    def get_note_for_role(cls, role: str) -> int:
        role_clean = role.strip().upper()
        if role_clean in cls.ROLE_TO_NOTE:
            return cls.ROLE_TO_NOTE[role_clean]
        # General aliases
        if "KICK" in role_clean: return cls.KICK
        if "SNARE" in role_clean: return cls.SNARE
        if "CLAP" in role_clean: return cls.CLAP
        if "CLOSED" in role_clean or "CH" in role_clean: return cls.CLOSED_HAT
        if "OPEN" in role_clean or "OH" in role_clean: return cls.OPEN_HAT
        if "SHAKER" in role_clean: return cls.SHAKER
        if "TOM" in role_clean: return cls.TOM
        return cls.PERC_1

    @classmethod
    def get_role_for_note(cls, pitch: int) -> Optional[InstrumentRole]:
        return cls.NOTE_TO_ROLE.get(pitch)

    @classmethod
    def get_display_name_for_note(cls, pitch: int) -> str:
        return cls.PAD_DISPLAY_NAMES.get(pitch, f"Pad {pitch}")

    @classmethod
    def get_display_name(cls, pitch: int) -> str:
        return cls.get_display_name_for_note(pitch)
