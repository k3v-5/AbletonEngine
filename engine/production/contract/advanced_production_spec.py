# engine/production/contract/advanced_production_spec.py
"""
Modular Advanced Production Specification & Validation System:
Exposes granular, decoupled production parameters to the AI (Crossover Stacking,
Turnarounds & Silences, Groove Pocket, Spatial Narrative, Ear Candy, Master Dynamics).
Ensures genre agnosticism, strict LOM safety, and acoustic pedagogical guidance
without silent overrides.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("AdvancedProductionSpec")


@dataclass
class CrossoverStackingConfig:
    enabled: bool = False
    target_roles: List[str] = field(default_factory=lambda: ["BASS"])
    sub_crossover_hz: float = 90.0
    air_crossover_hz: float = 1200.0
    sub_mono_strict: bool = True
    mid_saturation_drive: float = 0.35
    top_stereo_width: float = 1.25

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "target_roles": self.target_roles,
            "sub_crossover_hz": round(self.sub_crossover_hz, 1),
            "air_crossover_hz": round(self.air_crossover_hz, 1),
            "sub_mono_strict": self.sub_mono_strict,
            "mid_saturation_drive": round(self.mid_saturation_drive, 2),
            "top_stereo_width": round(self.top_stereo_width, 2),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CrossoverStackingConfig:
        return cls(
            enabled=bool(data.get("enabled", False)),
            target_roles=list(data.get("target_roles", ["BASS"])),
            sub_crossover_hz=float(data.get("sub_crossover_hz", 90.0)),
            air_crossover_hz=float(data.get("air_crossover_hz", 1200.0)),
            sub_mono_strict=bool(data.get("sub_mono_strict", True)),
            mid_saturation_drive=float(data.get("mid_saturation_drive", 0.35)),
            top_stereo_width=float(data.get("top_stereo_width", 1.25)),
        )


@dataclass
class TurnaroundsAndSilencesConfig:
    enabled: bool = True
    vacuum_stops: bool = True
    vacuum_duration_beats: float = 1.0
    preserve_solo_element: str = "REVERB_TAIL"  # NONE, VOCAL_WHISPER, REVERB_TAIL, SNARE_SNAP
    drum_fills: bool = True
    fill_velocity_crescendo: bool = True
    kick_dropout_in_fill: bool = True
    analog_tape_stop: bool = False
    tape_stop_semitones: float = -12.0
    tape_stop_scope: str = "MUSIC_BUS_ONLY"  # MUSIC_BUS_ONLY, MASTER_BUS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "vacuum_stops": self.vacuum_stops,
            "vacuum_duration_beats": round(self.vacuum_duration_beats, 2),
            "preserve_solo_element": self.preserve_solo_element,
            "drum_fills": self.drum_fills,
            "fill_velocity_crescendo": self.fill_velocity_crescendo,
            "kick_dropout_in_fill": self.kick_dropout_in_fill,
            "analog_tape_stop": self.analog_tape_stop,
            "tape_stop_semitones": round(self.tape_stop_semitones, 1),
            "tape_stop_scope": self.tape_stop_scope,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TurnaroundsAndSilencesConfig:
        return cls(
            enabled=bool(data.get("enabled", True)),
            vacuum_stops=bool(data.get("vacuum_stops", True)),
            vacuum_duration_beats=float(data.get("vacuum_duration_beats", 1.0)),
            preserve_solo_element=str(data.get("preserve_solo_element", "REVERB_TAIL")),
            drum_fills=bool(data.get("drum_fills", True)),
            fill_velocity_crescendo=bool(data.get("fill_velocity_crescendo", True)),
            kick_dropout_in_fill=bool(data.get("kick_dropout_in_fill", True)),
            analog_tape_stop=bool(data.get("analog_tape_stop", False)),
            tape_stop_semitones=float(data.get("tape_stop_semitones", -12.0)),
            tape_stop_scope=str(data.get("tape_stop_scope", "MUSIC_BUS_ONLY")),
        )


@dataclass
class GrooveAndPocketConfig:
    pocket_style: str = "straight_precise"  # neo_soul_dilla, atlanta_trap, boom_bap, french_pump, dark_rage, organic_human, straight_precise
    snare_dragging_ms: float = 0.0          # +12.0 to +18.0 for Kevin Parker / Dilla
    sub_dragging_ms: float = 0.0            # +4.0 to +6.0 for pocket bass
    hihat_swing_pct: float = 50.0           # 50.0 to 68.0%
    chord_strum_spread_ms: float = 12.0     # 0.0 to 30.0 ms
    humanize_velocity_jitter: int = 6       # Gaussian velocity jitter std dev

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pocket_style": self.pocket_style,
            "snare_dragging_ms": round(self.snare_dragging_ms, 1),
            "sub_dragging_ms": round(self.sub_dragging_ms, 1),
            "hihat_swing_pct": round(self.hihat_swing_pct, 1),
            "chord_strum_spread_ms": round(self.chord_strum_spread_ms, 1),
            "humanize_velocity_jitter": int(self.humanize_velocity_jitter),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GrooveAndPocketConfig:
        return cls(
            pocket_style=str(data.get("pocket_style", "straight_precise")),
            snare_dragging_ms=float(data.get("snare_dragging_ms", 0.0)),
            sub_dragging_ms=float(data.get("sub_dragging_ms", 0.0)),
            hihat_swing_pct=float(data.get("hihat_swing_pct", 50.0)),
            chord_strum_spread_ms=float(data.get("chord_strum_spread_ms", 12.0)),
            humanize_velocity_jitter=int(data.get("humanize_velocity_jitter", 6)),
        )


@dataclass
class SpatialNarrativeConfig:
    enabled: bool = True
    verse_width_pct: float = 75.0           # Narrow intimate verses
    chorus_width_pct: float = 140.0         # Ultra-wide mammoth chorus
    bridge_width_pct: float = 95.0
    bass_mono_cutoff_hz: float = 110.0      # Monofy everything below this
    abbey_road_reverb_filter: bool = True   # HP 350Hz, LP 7kHz on returns
    reverb_sidechain_ducking: bool = True   # Reverb ducks while lead is active

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "verse_width_pct": round(self.verse_width_pct, 1),
            "chorus_width_pct": round(self.chorus_width_pct, 1),
            "bridge_width_pct": round(self.bridge_width_pct, 1),
            "bass_mono_cutoff_hz": round(self.bass_mono_cutoff_hz, 1),
            "abbey_road_reverb_filter": self.abbey_road_reverb_filter,
            "reverb_sidechain_ducking": self.reverb_sidechain_ducking,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SpatialNarrativeConfig:
        return cls(
            enabled=bool(data.get("enabled", True)),
            verse_width_pct=float(data.get("verse_width_pct", 75.0)),
            chorus_width_pct=float(data.get("chorus_width_pct", 140.0)),
            bridge_width_pct=float(data.get("bridge_width_pct", 95.0)),
            bass_mono_cutoff_hz=float(data.get("bass_mono_cutoff_hz", 110.0)),
            abbey_road_reverb_filter=bool(data.get("abbey_road_reverb_filter", True)),
            reverb_sidechain_ducking=bool(data.get("reverb_sidechain_ducking", True)),
        )


@dataclass
class EarCandyConfig:
    enabled: bool = True
    max_events_per_song: int = 2
    allowed_types: List[str] = field(default_factory=lambda: ["DELAY_THROW", "NOISE_SWEEP_VACUUM"])
    delay_throw_spike: bool = True
    dynamic_auto_pan: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "max_events_per_song": self.max_events_per_song,
            "allowed_types": self.allowed_types,
            "delay_throw_spike": self.delay_throw_spike,
            "dynamic_auto_pan": self.dynamic_auto_pan,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EarCandyConfig:
        return cls(
            enabled=bool(data.get("enabled", True)),
            max_events_per_song=int(data.get("max_events_per_song", 2)),
            allowed_types=list(data.get("allowed_types", ["DELAY_THROW", "NOISE_SWEEP_VACUUM"])),
            delay_throw_spike=bool(data.get("delay_throw_spike", True)),
            dynamic_auto_pan=bool(data.get("dynamic_auto_pan", True)),
        )


@dataclass
class MasterDynamicsConfig:
    soft_clipper_pre_limiter: bool = True
    clipper_drive_db: float = 1.5
    nyc_parallel_drums: bool = False
    nyc_mix_blend_pct: float = 15.0
    target_lufs: float = -9.0
    true_peak_ceiling_dbtp: float = -0.8

    def to_dict(self) -> Dict[str, Any]:
        return {
            "soft_clipper_pre_limiter": self.soft_clipper_pre_limiter,
            "clipper_drive_db": round(self.clipper_drive_db, 1),
            "nyc_parallel_drums": self.nyc_parallel_drums,
            "nyc_mix_blend_pct": round(self.nyc_mix_blend_pct, 1),
            "target_lufs": round(self.target_lufs, 1),
            "true_peak_ceiling_dbtp": round(self.true_peak_ceiling_dbtp, 2),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MasterDynamicsConfig:
        return cls(
            soft_clipper_pre_limiter=bool(data.get("soft_clipper_pre_limiter", True)),
            clipper_drive_db=float(data.get("clipper_drive_db", 1.5)),
            nyc_parallel_drums=bool(data.get("nyc_parallel_drums", False)),
            nyc_mix_blend_pct=float(data.get("nyc_mix_blend_pct", 15.0)),
            target_lufs=float(data.get("target_lufs", -9.0)),
            true_peak_ceiling_dbtp=float(data.get("true_peak_ceiling_dbtp", -0.8)),
        )


@dataclass
class AdvancedProductionSpec:
    """Master aggregated specification of all 6 advanced production modules."""
    crossover_stacking: CrossoverStackingConfig = field(default_factory=CrossoverStackingConfig)
    turnarounds_and_silences: TurnaroundsAndSilencesConfig = field(default_factory=TurnaroundsAndSilencesConfig)
    groove_and_pocket: GrooveAndPocketConfig = field(default_factory=GrooveAndPocketConfig)
    spatial_narrative: SpatialNarrativeConfig = field(default_factory=SpatialNarrativeConfig)
    ear_candy: EarCandyConfig = field(default_factory=EarCandyConfig)
    master_dynamics: MasterDynamicsConfig = field(default_factory=MasterDynamicsConfig)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crossover_stacking": self.crossover_stacking.to_dict(),
            "turnarounds_and_silences": self.turnarounds_and_silences.to_dict(),
            "groove_and_pocket": self.groove_and_pocket.to_dict(),
            "spatial_narrative": self.spatial_narrative.to_dict(),
            "ear_candy": self.ear_candy.to_dict(),
            "master_dynamics": self.master_dynamics.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]] = None) -> AdvancedProductionSpec:
        if not data or not isinstance(data, dict):
            return cls()
        return cls(
            crossover_stacking=CrossoverStackingConfig.from_dict(data.get("crossover_stacking", {})),
            turnarounds_and_silences=TurnaroundsAndSilencesConfig.from_dict(data.get("turnarounds_and_silences", {})),
            groove_and_pocket=GrooveAndPocketConfig.from_dict(data.get("groove_and_pocket", {})),
            spatial_narrative=SpatialNarrativeConfig.from_dict(data.get("spatial_narrative", {})),
            ear_candy=EarCandyConfig.from_dict(data.get("ear_candy", {})),
            master_dynamics=MasterDynamicsConfig.from_dict(data.get("master_dynamics", {})),
        )


def validate_advanced_production_spec(
    spec: AdvancedProductionSpec,
    genre: str = "",
    bpm: float = 120.0
) -> List[str]:
    """
    Executes pedagogical acoustic validation against physical limits and genre aesthetics.
    Returns a list of explanatory warnings without silently modifying any parameter.
    """
    warnings: List[str] = []
    g_lower = str(genre or "").lower()

    # 1. Physical safety limits (Ableton LOM safety)
    gp = spec.groove_and_pocket
    if gp.snare_dragging_ms < -25.0 or gp.snare_dragging_ms > 40.0:
        warnings.append(
            f"⚠️ LÍMITE FÍSICO: 'snare_dragging_ms' ({gp.snare_dragging_ms} ms) excede el bolsillo rítmico audible. "
            "Valores entre -15.0 ms y +25.0 ms preservan coherencia perceptual."
        )

    if gp.hihat_swing_pct < 45.0 or gp.hihat_swing_pct > 75.0:
        warnings.append(
            f"⚠️ RANGO DE SWING: 'hihat_swing_pct' ({gp.hihat_swing_pct}%) está fuera del rango estándar (50% a 70%). "
            "Valores superiores a 70% pueden desfasar semicorcheas."
        )

    # 2. Genre-specific acoustic checks
    is_four_on_floor = any(k in g_lower for k in ["techno", "house", "trance", "hardstyle", "edm", "disco"])
    if is_four_on_floor and gp.snare_dragging_ms > 8.0:
        warnings.append(
            f"⚠️ ADVERTENCIA ACÚSTICA: El género '{genre}' depende de una rejilla 4-on-the-floor locked. "
            f"Un snare dragging de {gp.snare_dragging_ms} ms puede hacer que la caja pelee con la pegada del bombo. "
            "¿Deseas mantener este desfase deliberadamente o ajustar a 0.0 - 3.0 ms?"
        )

    is_ambient_drone = any(k in g_lower for k in ["ambient", "drone", "meditation", "cinematic_soundscape"])
    ts = spec.turnarounds_and_silences
    if is_ambient_drone and (ts.drum_fills or ts.analog_tape_stop):
        warnings.append(
            f"⚠️ ESTILO INUSUAL: El género '{genre}' es de naturaleza etérea continua. "
            "La activación de 'drum_fills' o 'analog_tape_stop' romperá la inmersión meditativa. Confirma si es intencional."
        )

    # 3. Spatial contrast checks
    sp = spec.spatial_narrative
    if sp.enabled and sp.verse_width_pct > sp.chorus_width_pct:
        warnings.append(
            f"⚠️ CONTRASTE ESPACIAL INVERTIDO: El ancho del verso ({sp.verse_width_pct}%) es mayor que el del coro ({sp.chorus_width_pct}%). "
            "El estándar psicoacústico es mantener el verso más estrecho e íntimo para que el coro explote físicamente."
        )

    # 4. Low-end crossover safety
    cs = spec.crossover_stacking
    if cs.enabled and cs.sub_crossover_hz > 140.0:
        warnings.append(
            f"⚠️ FRECUENCIA DE CORTE: 'sub_crossover_hz' ({cs.sub_crossover_hz} Hz) invade frecuencias medias del bajo. "
            "Recomendado: mantener entre 70 Hz y 110 Hz para evitar phase smearing en medios."
        )

    return warnings


def get_advanced_production_schema() -> Dict[str, Any]:
    """Returns the full JSON schema and documentation for Phase 0 prompting."""
    return {
        "title": "AdvancedProductionSpec",
        "description": "Especificación modular de 6 componentes de producción multiplatino de élite.",
        "type": "object",
        "properties": {
            "crossover_stacking": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean", "default": False},
                    "target_roles": {"type": "array", "items": {"type": "string"}, "default": ["BASS"]},
                    "sub_crossover_hz": {"type": "number", "minimum": 60.0, "maximum": 120.0, "default": 90.0},
                    "air_crossover_hz": {"type": "number", "minimum": 1000.0, "maximum": 3500.0, "default": 1200.0},
                    "sub_mono_strict": {"type": "boolean", "default": True},
                    "mid_saturation_drive": {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.35},
                    "top_stereo_width": {"type": "number", "minimum": 1.0, "maximum": 1.8, "default": 1.25}
                }
            },
            "turnarounds_and_silences": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean", "default": True},
                    "vacuum_stops": {"type": "boolean", "default": True},
                    "vacuum_duration_beats": {"type": "number", "minimum": 0.5, "maximum": 2.0, "default": 1.0},
                    "preserve_solo_element": {"type": "string", "enum": ["NONE", "VOCAL_WHISPER", "REVERB_TAIL", "SNARE_SNAP"], "default": "REVERB_TAIL"},
                    "drum_fills": {"type": "boolean", "default": True},
                    "fill_velocity_crescendo": {"type": "boolean", "default": True},
                    "kick_dropout_in_fill": {"type": "boolean", "default": True},
                    "analog_tape_stop": {"type": "boolean", "default": False},
                    "tape_stop_semitones": {"type": "number", "minimum": -24.0, "maximum": -6.0, "default": -12.0},
                    "tape_stop_scope": {"type": "string", "enum": ["MUSIC_BUS_ONLY", "MASTER_BUS"], "default": "MUSIC_BUS_ONLY"}
                }
            },
            "groove_and_pocket": {
                "type": "object",
                "properties": {
                    "pocket_style": {"type": "string", "enum": ["neo_soul_dilla", "atlanta_trap", "boom_bap", "french_pump", "dark_rage", "organic_human", "straight_precise"], "default": "straight_precise"},
                    "snare_dragging_ms": {"type": "number", "minimum": -15.0, "maximum": 25.0, "default": 0.0},
                    "sub_dragging_ms": {"type": "number", "minimum": 0.0, "maximum": 10.0, "default": 0.0},
                    "hihat_swing_pct": {"type": "number", "minimum": 50.0, "maximum": 72.0, "default": 50.0},
                    "chord_strum_spread_ms": {"type": "number", "minimum": 0.0, "maximum": 30.0, "default": 12.0},
                    "humanize_velocity_jitter": {"type": "integer", "minimum": 0, "maximum": 16, "default": 6}
                }
            },
            "spatial_narrative": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean", "default": True},
                    "verse_width_pct": {"type": "number", "minimum": 50.0, "maximum": 90.0, "default": 75.0},
                    "chorus_width_pct": {"type": "number", "minimum": 110.0, "maximum": 160.0, "default": 140.0},
                    "bridge_width_pct": {"type": "number", "minimum": 70.0, "maximum": 120.0, "default": 95.0},
                    "bass_mono_cutoff_hz": {"type": "number", "minimum": 80.0, "maximum": 140.0, "default": 110.0},
                    "abbey_road_reverb_filter": {"type": "boolean", "default": True},
                    "reverb_sidechain_ducking": {"type": "boolean", "default": True}
                }
            },
            "ear_candy": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean", "default": True},
                    "max_events_per_song": {"type": "integer", "minimum": 1, "maximum": 3, "default": 2},
                    "allowed_types": {"type": "array", "items": {"type": "string"}, "default": ["DELAY_THROW", "NOISE_SWEEP_VACUUM"]},
                    "delay_throw_spike": {"type": "boolean", "default": True},
                    "dynamic_auto_pan": {"type": "boolean", "default": True}
                }
            },
            "master_dynamics": {
                "type": "object",
                "properties": {
                    "soft_clipper_pre_limiter": {"type": "boolean", "default": True},
                    "clipper_drive_db": {"type": "number", "minimum": 0.0, "maximum": 4.0, "default": 1.5},
                    "nyc_parallel_drums": {"type": "boolean", "default": False},
                    "nyc_mix_blend_pct": {"type": "number", "minimum": 10.0, "maximum": 30.0, "default": 15.0},
                    "target_lufs": {"type": "number", "minimum": -15.0, "maximum": -6.5, "default": -9.0},
                    "true_peak_ceiling_dbtp": {"type": "number", "minimum": -1.5, "maximum": -0.1, "default": -0.8}
                }
            }
        }
    }
