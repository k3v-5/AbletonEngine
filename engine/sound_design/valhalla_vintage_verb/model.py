# engine/sound_design/valhalla_vintage_verb/model.py
"""
Valhalla VintageVerb Model & Preset Representation.

Encapsulates complete parameter states for Valhalla VintageVerb,
providing serialization to XML clipboard/presets and LOM parameter mapping.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import xml.etree.ElementTree as ET

from .schema import ValhallaVintageVerbSchema, VintageVerbColor


@dataclass
class VintageVerbModel:
    """Represents a validated, serializable state for Valhalla VintageVerb."""

    preset_name: str = "Default"
    plugin_version: str = ValhallaVintageVerbSchema.DEFAULT_VERSION

    # 16 Canonical Parameters (Normalized [0.0, 1.0])
    mix: float = 0.20
    predelay: float = 0.0
    decay: float = 0.25
    size: float = 0.50
    attack: float = 0.0
    bass_mult: float = 0.50
    bass_xover: float = 0.50
    high_shelf: float = 0.0
    high_cut: float = 0.65
    low_cut: float = 0.20
    early_diffusion: float = 1.0
    late_diffusion: float = 1.0
    mod_rate: float = 0.25
    mod_depth: float = 0.50
    mode: float = 0.0  # Concert Hall
    color_mode: float = 0.50  # 1980s

    @property
    def mode_name(self) -> str:
        """Returns the algorithmic mode name for the current normalized mode index."""
        return ValhallaVintageVerbSchema.float_to_mode(self.mode)

    @mode_name.setter
    def mode_name(self, name: str) -> None:
        """Sets the normalized mode index from mode name."""
        self.mode = ValhallaVintageVerbSchema.mode_to_float(name)

    @property
    def color_name(self) -> str:
        """Returns the human-readable color era name (1970s, 1980s, Now)."""
        return ValhallaVintageVerbSchema.float_to_color(self.color_mode)

    @color_name.setter
    def color_name(self, name: str) -> None:
        """Sets the normalized color mode from era name."""
        self.color_mode = ValhallaVintageVerbSchema.color_to_float(name)

    @property
    def decay_seconds(self) -> float:
        """Returns physical decay time in seconds."""
        return ValhallaVintageVerbSchema.decay_to_seconds(self.decay)

    @property
    def predelay_ms(self) -> float:
        """Returns physical pre-delay in milliseconds."""
        return ValhallaVintageVerbSchema.predelay_to_ms(self.predelay)

    def to_dict(self) -> Dict[str, Any]:
        """Returns a dictionary of all parameter values."""
        return {
            "preset_name": self.preset_name,
            "plugin_version": self.plugin_version,
            "Mix": round(self.mix, 4),
            "PreDelay": round(self.predelay, 4),
            "Decay": round(self.decay, 4),
            "Size": round(self.size, 4),
            "Attack": round(self.attack, 4),
            "BassMult": round(self.bass_mult, 4),
            "BassXover": round(self.bass_xover, 4),
            "HighShelf": round(self.high_shelf, 4),
            "HighCut": round(self.high_cut, 4),
            "LowCut": round(self.low_cut, 4),
            "EarlyDiffusion": round(self.early_diffusion, 4),
            "LateDiffusion": round(self.late_diffusion, 4),
            "ModRate": round(self.mod_rate, 4),
            "ModDepth": round(self.mod_depth, 4),
            "Mode": round(self.mode, 6),
            "ColorMode": round(self.color_mode, 2),
            "mode_name": self.mode_name,
            "color_name": self.color_name,
            "decay_seconds": self.decay_seconds,
            "predelay_ms": self.predelay_ms,
        }

    def to_xml_string(self) -> str:
        """
        Generates canonical XML preset string matching Valhalla VintageVerb's
        native clipboard and .vpreset format.
        """
        elem = ET.Element(
            ValhallaVintageVerbSchema.PLUGIN_NAME,
            {
                "pluginVersion": self.plugin_version,
                "presetName": self.preset_name,
                "Mix": str(round(self.mix, 6)),
                "PreDelay": str(round(self.predelay, 6)),
                "Decay": str(round(self.decay, 6)),
                "Size": str(round(self.size, 6)),
                "Attack": str(round(self.attack, 6)),
                "BassMult": str(round(self.bass_mult, 6)),
                "BassXover": str(round(self.bass_xover, 6)),
                "HighShelf": str(round(self.high_shelf, 6)),
                "HighCut": str(round(self.high_cut, 6)),
                "LowCut": str(round(self.low_cut, 6)),
                "EarlyDiffusion": str(round(self.early_diffusion, 6)),
                "LateDiffusion": str(round(self.late_diffusion, 6)),
                "ModRate": str(round(self.mod_rate, 6)),
                "ModDepth": str(round(self.mod_depth, 6)),
                "Mode": str(round(self.mode, 6)),
                "ColorMode": str(round(self.color_mode, 6)),
            }
        )
        return ET.tostring(elem, encoding="utf-8").decode("utf-8")

    def to_lom_dict(self) -> Dict[str, float]:
        """Returns parameter mappings for Ableton Live LOM parameter dispatch."""
        return {
            "Mix": float(self.mix),
            "PreDelay": float(self.predelay),
            "Decay": float(self.decay),
            "Size": float(self.size),
            "Attack": float(self.attack),
            "BassMult": float(self.bass_mult),
            "BassXover": float(self.bass_xover),
            "HighShelf": float(self.high_shelf),
            "HighCut": float(self.high_cut),
            "LowCut": float(self.low_cut),
            "EarlyDiffusion": float(self.early_diffusion),
            "LateDiffusion": float(self.late_diffusion),
            "ModRate": float(self.mod_rate),
            "ModDepth": float(self.mod_depth),
            "Mode": float(self.mode),
            "Color": float(self.color_mode),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VintageVerbModel":
        """Instantiates a VintageVerbModel from a dictionary of parameters."""
        model = cls()
        if "preset_name" in data:
            model.preset_name = str(data["preset_name"])
        if "plugin_version" in data:
            model.plugin_version = str(data["plugin_version"])

        # Map case-insensitive keys
        key_map = {
            "mix": "mix",
            "predelay": "predelay",
            "decay": "decay",
            "size": "size",
            "attack": "attack",
            "bassmult": "bass_mult",
            "bass_mult": "bass_mult",
            "bassxover": "bass_xover",
            "bass_xover": "bass_xover",
            "highshelf": "high_shelf",
            "high_shelf": "high_shelf",
            "highcut": "high_cut",
            "high_cut": "high_cut",
            "lowcut": "low_cut",
            "low_cut": "low_cut",
            "earlydiffusion": "early_diffusion",
            "early_diffusion": "early_diffusion",
            "latediffusion": "late_diffusion",
            "late_diffusion": "late_diffusion",
            "modrate": "mod_rate",
            "mod_rate": "mod_rate",
            "moddepth": "mod_depth",
            "mod_depth": "mod_depth",
            "mode": "mode",
            "colormode": "color_mode",
            "color_mode": "color_mode",
            "color": "color_mode",
        }

        for k, v in data.items():
            k_lower = k.lower().replace(" ", "").replace("-", "")
            target_attr = key_map.get(k_lower)
            if target_attr:
                if target_attr == "mode" and isinstance(v, str):
                    setattr(model, "mode_name", v)
                elif target_attr == "color_mode" and isinstance(v, str):
                    setattr(model, "color_name", v)
                else:
                    try:
                        setattr(model, target_attr, float(v))
                    except (ValueError, TypeError):
                        pass

        return model
