"""
Drum Rack Models:
Declarative specifications for Drum Racks and Pad configurations.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class SampleMetadata:
    filename: str
    path: str
    duration_sec: float = 0.5
    sample_rate: int = 44100
    channels: int = 2
    peak_db: float = -0.5
    rms_db: float = -12.0
    valid: bool = True

@dataclass
class DrumPadSpec:
    note: int  # 36 = C1 (Kick), 38 = D1 (Snare), etc.
    role: str  # KICK, SNARE, CLAP, CLOSED_HAT, etc.
    name: str = ""
    sample_path: Optional[str] = None
    volume_db: float = 0.0
    mute: bool = False
    solo: bool = False

@dataclass
class DrumRackSpec:
    name: str = "DRUMS_MAIN"
    style: str = "melodic_techno"
    pads: Dict[int, DrumPadSpec] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "style": self.style,
            "pad_count": len(self.pads),
            "pads": {
                str(note): {
                    "role": pad.role,
                    "name": pad.name,
                    "sample": pad.sample_path,
                    "volume_db": pad.volume_db
                }
                for note, pad in self.pads.items()
            }
        }
