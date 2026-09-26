# engine/sound_design/surge_xt_synth/model.py
"""
Surge XT Synthesizer Model & Patch Representation.

Encapsulates complete patch architecture for Surge XT:
- 3 Oscillators per Scene
- Dual Multi-Mode Filters
- AHDSR Envelopes (Amp & Filter)
- Unison Configuration
- XML Serialization (.surgepatch) and DAW LOM parameter mappings.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
import xml.etree.ElementTree as ET

from .schema import (
    SurgeXTSynthSchema,
    SurgeOscillatorType,
    SurgeFilterType,
    SurgeFilterSubtype,
    SurgeFilterConfig
)


@dataclass
class SurgeSynthOscillatorModel:
    """Represents a single oscillator in a Surge XT scene."""
    slot: int = 1  # 1, 2, or 3
    osc_type: str = SurgeOscillatorType.CLASSIC.value
    octave: int = 0         # -3 to +3
    semitone: int = 0       # -12 to +12
    cent: float = 0.0       # -100.0 to +100.0
    level: float = 0.80     # 0.0 to 1.0
    pan: float = 0.0        # -1.0 to 1.0
    mute: bool = False
    route: str = "Filter 1" # "Filter 1", "Filter 2", "Both", "Direct Out"

    # Specific DSP parameters (p0 .. p6)
    param1: float = 0.50    # e.g., Sub-Osc level / Morph
    param2: float = 0.50    # e.g., Pulse Width / Formant
    param3: float = 0.00    # e.g., Sync / Feedback
    param4: float = 0.00
    param5: float = 0.00
    param6: float = 0.00
    param7: float = 0.00

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slot": self.slot,
            "osc_type": self.osc_type,
            "octave": self.octave,
            "semitone": self.semitone,
            "cent": self.cent,
            "level": round(self.level, 4),
            "pan": round(self.pan, 4),
            "mute": self.mute,
            "route": self.route,
            "param1": round(self.param1, 4),
            "param2": round(self.param2, 4),
            "param3": round(self.param3, 4),
        }


@dataclass
class SurgeSynthFilterModel:
    """Represents a filter unit in Surge XT."""
    unit: int = 1  # 1 or 2
    filter_type: str = SurgeFilterType.LADDER_LP.value
    subtype: str = SurgeFilterSubtype.STANDARD.value
    cutoff: float = 0.70      # 0.0 to 1.0
    resonance: float = 0.25   # 0.0 to 1.0
    drive: float = 0.00       # 0.0 to 1.0
    feedback: float = 0.00    # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unit": self.unit,
            "filter_type": self.filter_type,
            "subtype": self.subtype,
            "cutoff": round(self.cutoff, 4),
            "resonance": round(self.resonance, 4),
            "drive": round(self.drive, 4),
            "feedback": round(self.feedback, 4),
        }


@dataclass
class SurgeSynthEnvelopeModel:
    """Represents an AHDSR envelope in Surge XT."""
    name: str = "Amp"  # "Amp" or "Filter"
    attack: float = 0.01    # seconds or norm
    decay: float = 0.40     # seconds or norm
    sustain: float = 0.70   # amplitude 0.0 to 1.0
    release: float = 0.25   # seconds or norm

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "attack": round(self.attack, 4),
            "decay": round(self.decay, 4),
            "sustain": round(self.sustain, 4),
            "release": round(self.release, 4),
        }


@dataclass
class SurgeSynthPatchModel:
    """Represents a complete, serializable patch for Surge XT Synthesizer."""
    patch_name: str = "Default_Patch"
    category: str = "AbletonEngine"
    author: str = "AbletonEngine Copilot"
    version: str = SurgeXTSynthSchema.DEFAULT_VERSION

    # Scene A Oscillators (3 units)
    oscillators: List[SurgeSynthOscillatorModel] = field(default_factory=lambda: [
        SurgeSynthOscillatorModel(slot=1, osc_type="Classic", level=0.85),
        SurgeSynthOscillatorModel(slot=2, osc_type="Classic", level=0.00, mute=True),
        SurgeSynthOscillatorModel(slot=3, osc_type="Classic", level=0.00, mute=True),
    ])

    # Filters
    filter1: SurgeSynthFilterModel = field(default_factory=lambda: SurgeSynthFilterModel(unit=1))
    filter2: SurgeSynthFilterModel = field(default_factory=lambda: SurgeSynthFilterModel(unit=2, cutoff=1.0, resonance=0.0))
    filter_config: str = SurgeFilterConfig.SERIAL.value

    # Envelopes
    amp_envelope: SurgeSynthEnvelopeModel = field(default_factory=lambda: SurgeSynthEnvelopeModel(name="Amp"))
    filter_envelope: SurgeSynthEnvelopeModel = field(default_factory=lambda: SurgeSynthEnvelopeModel(name="Filter", attack=0.02, decay=0.35, sustain=0.40, release=0.20))

    # Master & Unison
    volume: float = 0.80
    unison_count: int = 1      # 1 to 16 voices
    unison_detune: float = 0.0 # 0.0 to 1.0
    polyphony: int = 16

    def get_oscillator(self, slot: int) -> Optional[SurgeSynthOscillatorModel]:
        for osc in self.oscillators:
            if osc.slot == slot:
                return osc
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patch_name": self.patch_name,
            "category": self.category,
            "author": self.author,
            "version": self.version,
            "volume": round(self.volume, 4),
            "unison_count": self.unison_count,
            "unison_detune": round(self.unison_detune, 4),
            "polyphony": self.polyphony,
            "filter_config": self.filter_config,
            "oscillators": [osc.to_dict() for osc in self.oscillators],
            "filter1": self.filter1.to_dict(),
            "filter2": self.filter2.to_dict(),
            "amp_envelope": self.amp_envelope.to_dict(),
            "filter_envelope": self.filter_envelope.to_dict(),
        }

    def to_xml_string(self) -> str:
        """
        Generates structured XML string for native .surgepatch file.
        """
        root = ET.Element("surge-patch", {
            "name": self.patch_name,
            "category": self.category,
            "author": self.author,
            "version": self.version,
        })

        # Global settings
        ET.SubElement(root, "meta", {
            "volume": str(round(self.volume, 4)),
            "unison_count": str(self.unison_count),
            "unison_detune": str(round(self.unison_detune, 4)),
            "polyphony": str(self.polyphony),
        })

        # Scene A
        scene_a = ET.SubElement(root, "scene", {"id": "A"})

        # Oscillators
        oscs_elem = ET.SubElement(scene_a, "oscillators")
        for osc in self.oscillators:
            ET.SubElement(oscs_elem, "oscillator", {
                "slot": str(osc.slot),
                "type": osc.osc_type,
                "octave": str(osc.octave),
                "semitone": str(osc.semitone),
                "cent": str(round(osc.cent, 2)),
                "level": str(round(osc.level, 4)),
                "pan": str(round(osc.pan, 4)),
                "mute": "1" if osc.mute else "0",
                "route": osc.route,
                "p1": str(round(osc.param1, 4)),
                "p2": str(round(osc.param2, 4)),
                "p3": str(round(osc.param3, 4)),
            })

        # Filters
        filters_elem = ET.SubElement(scene_a, "filters", {"config": self.filter_config})
        for f in [self.filter1, self.filter2]:
            ET.SubElement(filters_elem, "filter", {
                "unit": str(f.unit),
                "type": f.filter_type,
                "subtype": f.subtype,
                "cutoff": str(round(f.cutoff, 4)),
                "resonance": str(round(f.resonance, 4)),
                "drive": str(round(f.drive, 4)),
                "feedback": str(round(f.feedback, 4)),
            })

        # Envelopes
        envs_elem = ET.SubElement(scene_a, "envelopes")
        for env in [self.amp_envelope, self.filter_envelope]:
            ET.SubElement(envs_elem, "envelope", {
                "name": env.name,
                "attack": str(round(env.attack, 4)),
                "decay": str(round(env.decay, 4)),
                "sustain": str(round(env.sustain, 4)),
                "release": str(round(env.release, 4)),
            })

        return ET.tostring(root, encoding="utf-8").decode("utf-8")

    def to_lom_command_list(self) -> List[Tuple[str, float]]:
        """
        Translates the patch state into canonical Live Object Model (LOM)
        parameter commands for direct real-time dispatching.
        """
        cmds = []
        cmds.append(("Volume", float(self.volume)))

        # Oscillators
        for osc in self.oscillators:
            idx = osc.slot
            cmds.append((f"Osc {idx} Level", 0.0 if osc.mute else float(osc.level)))
            cmds.append((f"Osc {idx} Octave", float(osc.octave)))
            cmds.append((f"Osc {idx} Semi", float(osc.semitone)))
            cmds.append((f"Osc {idx} Pan", float(osc.pan)))

        # Filter 1
        cmds.append(("Filter 1 Cutoff", float(self.filter1.cutoff)))
        cmds.append(("Filter 1 Resonance", float(self.filter1.resonance)))
        cmds.append(("Filter 1 Drive", float(self.filter1.drive)))

        # Envelopes
        cmds.append(("Amp Attack", float(self.amp_envelope.attack)))
        cmds.append(("Amp Decay", float(self.amp_envelope.decay)))
        cmds.append(("Amp Sustain", float(self.amp_envelope.sustain)))
        cmds.append(("Amp Release", float(self.amp_envelope.release)))

        # Unison
        cmds.append(("Unison Count", float(self.unison_count)))
        cmds.append(("Unison Detune", float(self.unison_detune)))

        return cmds
