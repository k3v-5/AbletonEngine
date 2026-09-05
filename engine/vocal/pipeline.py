# engine/vocal/pipeline.py
import math
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum

class VocalStyle(str, Enum):
    MODERN_RAP = "modern_rap"   # JID, Tyler, Kendrick: Upfront, crisp presence, punchy opto-compression
    RNB_SOUL = "rnb_soul"       # Smooth, warm, velvety opto, rich reverb
    TRAP = "trap"               # Auto-tune ready, bright top-end air, 1/8d delay throws
    INDIE_ALT = "indie_alt"     # Tape saturation, analog color, natural dynamics

@dataclass
class VocalChainStage:
    stage_name: str
    device_type: str             # "eq", "compressor", "saturation", "deesser", "delay", "reverb"
    suggested_native: str        # Native Live 12 Suite device
    suggested_vst: Optional[str] # 3rd party VST3 alternative if available
    parameters: Dict[str, Any] = field(default_factory=dict)
    rationale: str = ""

@dataclass
class VocalProductionProfile:
    style: VocalStyle
    high_pass_hz: float
    boxiness_cut_hz: float
    boxiness_cut_db: float
    presence_boost_hz: float
    presence_boost_db: float
    compressor_ratio: float
    compressor_attack_ms: float
    compressor_release_ms: float
    compression_gr_target_db: float
    saturation_drive_db: float
    recommended_ducking_db: float
    chain: List[VocalChainStage] = field(default_factory=list)

class VocalProductionEngine:
    """
    Intelligent vocal production engine for track scaffolding, DSP chain design,
    and automatic instrumental ducking matrix around vocal phrasing.
    """

    STYLE_PROFILES: Dict[VocalStyle, VocalProductionProfile] = {
        VocalStyle.MODERN_RAP: VocalProductionProfile(
            style=VocalStyle.MODERN_RAP,
            high_pass_hz=100.0,
            boxiness_cut_hz=340.0,
            boxiness_cut_db=-2.5,
            presence_boost_hz=4200.0,
            presence_boost_db=2.0,
            compressor_ratio=4.0,
            compressor_attack_ms=15.0,
            compressor_release_ms=60.0,
            compression_gr_target_db=4.0,
            saturation_drive_db=2.0,
            recommended_ducking_db=-2.5,
            chain=[
                VocalChainStage("Sub Cut & Clarity", "eq", "EQ Eight", "FabFilter Pro-Q 3",
                                {"hp_freq": 100.0, "notch_freq": 340.0, "notch_gain": -2.5},
                                "Removes mic rumble and removes boxy room resonance"),
                VocalChainStage("Dynamic Leveling", "compressor", "Glue Compressor", "The God Particle",
                                {"threshold": -18.0, "ratio": 4.0, "attack": 15.0, "release": 60.0},
                                "Controls fast vocal transients while preserving articulate consonants"),
                VocalChainStage("Harmonic Warmth", "saturation", "Saturator", "Output Thermal",
                                {"drive": 2.0, "curve": "Analog Clip"},
                                "Adds harmonic saturation to cut through dense 808s and synth beds"),
                VocalChainStage("Spatial Throw", "delay", "Echo", "Arturia Efx REFRACT",
                                {"dry_wet": 0.15, "sync": "1/8d", "feedback": 30.0},
                                "Creates rhythmic depth without muddying center vocal lane")
            ]
        ),
        VocalStyle.RNB_SOUL: VocalProductionProfile(
            style=VocalStyle.RNB_SOUL,
            high_pass_hz=90.0,
            boxiness_cut_hz=400.0,
            boxiness_cut_db=-2.0,
            presence_boost_hz=5000.0,
            presence_boost_db=1.5,
            compressor_ratio=2.5,
            compressor_attack_ms=30.0,
            compressor_release_ms=120.0,
            compression_gr_target_db=3.0,
            saturation_drive_db=1.0,
            recommended_ducking_db=-2.0,
            chain=[
                VocalChainStage("Gentle High-Pass", "eq", "EQ Eight", "FabFilter Pro-Q 3",
                                {"hp_freq": 90.0}, "Cleans low end while retaining chest warmth"),
                VocalChainStage("Optical Leveler", "compressor", "Compressor", "FabFilter Pro-C 2",
                                {"ratio": 2.5, "attack": 30.0, "release": 120.0}, "Velvety leveling with slow release"),
                VocalChainStage("Silk Air", "eq", "EQ Eight", "FabFilter Pro-Q 3",
                                {"shelf_freq": 10000.0, "shelf_gain": 2.0}, "Silky airy sheen"),
                VocalChainStage("Lush Atmosphere", "reverb", "Hybrid Reverb", "Valhalla VintageVerb",
                                {"decay": 2.2, "dry_wet": 0.22}, "Expansive stereo space")
            ]
        ),
        VocalStyle.TRAP: VocalProductionProfile(
            style=VocalStyle.TRAP,
            high_pass_hz=120.0,
            boxiness_cut_hz=500.0,
            boxiness_cut_db=-3.0,
            presence_boost_hz=3500.0,
            presence_boost_db=3.0,
            compressor_ratio=5.0,
            compressor_attack_ms=5.0,
            compressor_release_ms=45.0,
            compression_gr_target_db=6.0,
            saturation_drive_db=3.5,
            recommended_ducking_db=-3.0,
            chain=[
                VocalChainStage("Aggressive Sub Cut", "eq", "EQ Eight", "FabFilter Pro-Q 3",
                                {"hp_freq": 120.0}, "Maximum isolation from booming 808 sub bass"),
                VocalChainStage("Pitch Correction", "pitch", "Live Auto-Pitch", "Antares Auto-Tune",
                                {"speed": 0.0, "scale": "minor"}, "Hard robotic pitch snapping"),
                VocalChainStage("Fast Limiting", "compressor", "Glue Compressor", "Sausage Fattener",
                                {"threshold": -22.0, "ratio": 5.0}, "Sits vocal strictly in your face"),
                VocalChainStage("Bright Saturation", "saturation", "Saturator", "Output Thermal",
                                {"drive": 3.5}, "Gives vocals metallic sparkle")
            ]
        ),
        VocalStyle.INDIE_ALT: VocalProductionProfile(
            style=VocalStyle.INDIE_ALT,
            high_pass_hz=85.0,
            boxiness_cut_hz=280.0,
            boxiness_cut_db=-1.5,
            presence_boost_hz=2500.0,
            presence_boost_db=1.0,
            compressor_ratio=3.0,
            compressor_attack_ms=25.0,
            compressor_release_ms=90.0,
            compression_gr_target_db=3.0,
            saturation_drive_db=2.5,
            recommended_ducking_db=-2.0,
            chain=[
                VocalChainStage("Warm Low-Cut", "eq", "EQ Eight", "FabFilter Pro-Q 3",
                                {"hp_freq": 85.0}, "Organic bottom end"),
                VocalChainStage("Tape Mojo", "saturation", "Saturator", "Arturia Efx MOTIONS",
                                {"drive": 2.5, "curve": "Warm Tube"}, "Analog cassette character"),
                VocalChainStage("Spring Depth", "reverb", "Hybrid Reverb", "Valhalla VintageVerb",
                                {"decay": 1.4, "dry_wet": 0.18}, "Vintage indie aesthetic")
            ]
        )
    }

    @classmethod
    def get_vocal_profile(cls, style: Union[VocalStyle, str]) -> VocalProductionProfile:
        if isinstance(style, str):
            style_enum = VocalStyle(style.lower()) if style.lower() in [s.value for s in VocalStyle] else VocalStyle.MODERN_RAP
        else:
            style_enum = style
        return cls.STYLE_PROFILES[style_enum]

    @staticmethod
    def calculate_ducking_envelope(
        vocal_ranges_beats: List[Tuple[float, float]],
        song_length_beats: float,
        duck_amount_db: float = -2.5,
        attack_beats: float = 0.5,
        release_beats: float = 1.0,
        baseline_volume: float = 0.85
    ) -> List[Dict[str, float]]:
        """
        Calculates a continuous volume automation envelope that transparently ducks
        instrumental accompaniment when vocals are present.
        duck_amount_db: Gain reduction in decibels (e.g. -2.5 dB)
        """
        if duck_amount_db > 0:
            raise ValueError(f"duck_amount_db must be <= 0, got {duck_amount_db}")

        # Linear amplitude factor: 10^(dB / 20)
        duck_factor = 10.0 ** (duck_amount_db / 20.0)
        ducked_volume = baseline_volume * duck_factor

        # Sort and merge overlapping vocal intervals
        sorted_ranges = sorted(vocal_ranges_beats, key=lambda x: x[0])
        merged_ranges = []
        for start, end in sorted_ranges:
            if not merged_ranges:
                merged_ranges.append((start, end))
            else:
                prev_start, prev_end = merged_ranges[-1]
                if start <= prev_end:
                    merged_ranges[-1] = (prev_start, max(prev_end, end))
                else:
                    merged_ranges.append((start, end))

        points = []
        # Add initial baseline if first range doesn't start at 0
        current_time = 0.0
        if not merged_ranges or merged_ranges[0][0] > 0.0:
            points.append({"time": 0.0, "value": round(baseline_volume, 4)})

        for start, end in merged_ranges:
            # Point right before attack starts
            pre_attack = max(0.0, start - attack_beats)
            if not points or abs(points[-1]["time"] - pre_attack) > 0.01:
                points.append({"time": round(pre_attack, 4), "value": round(baseline_volume, 4)})
            
            # Point when fully ducked at start of vocal
            points.append({"time": round(start, 4), "value": round(ducked_volume, 4)})

            # Point maintaining ducked level until end of vocal
            points.append({"time": round(end, 4), "value": round(ducked_volume, 4)})

            # Point recovering after release
            post_release = min(song_length_beats, end + release_beats)
            points.append({"time": round(post_release, 4), "value": round(baseline_volume, 4)})

        # Ensure trailing baseline point at song end
        if points and points[-1]["time"] < song_length_beats:
            points.append({"time": round(song_length_beats, 4), "value": round(baseline_volume, 4)})

        # Remove duplicate adjacent points with same time
        deduped = []
        for p in points:
            if not deduped or abs(deduped[-1]["time"] - p["time"]) > 0.001:
                deduped.append(p)

        return deduped

    @staticmethod
    def identify_ducking_targets(all_track_names: List[str]) -> List[int]:
        """
        Scans track names to find high-priority musical elements to duck (Keys, Chords, Leads, Pads, Guitars, Synths)
        while strictly protecting rhythm anchors (Drums, Kick, Snare, 808, Sub Bass).
        """
        duck_keywords = ["keys", "chord", "lead", "synth", "pad", "piano", "rhodes", "guitar", "pluck"]
        protect_keywords = ["drum", "kick", "snare", "hat", "perc", "808", "bass", "sub", "vocal", "vox", "master"]

        targets = []
        for idx, name in enumerate(all_track_names):
            clean_name = name.lower()
            if any(prot in clean_name for prot in protect_keywords):
                continue
            if any(duck in clean_name for duck in duck_keywords):
                targets.append(idx)

        return targets
