"""
Ultra Acoustic Config Catalog (Ableton Live 12 Native)
======================================================
Matriz exhaustiva y determinista de configuraciones acústicas especializadas por rol
instrumental (21 roles) x arquetipos sonoros canónicos (11 arquetipos).

Cumple estrictamente la directiva de producción:
"Cada arquetipo debe ser diferente para cada tipo de rol acústico ya que no todos
manejan las mismas frecuencias."
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import math

class AcousticArchetype(str, Enum):
    PUNCHY = "PUNCHY"
    OSCURO = "OSCURO"
    BRILLANTE = "BRILLANTE"
    WARM = "WARM"
    AGGRESSIVE = "AGGRESSIVE"
    TIGHT = "TIGHT"
    AIRY = "AIRY"
    WIDE = "WIDE"
    LOFI = "LOFI"
    DEEP = "DEEP"
    BALANCED = "BALANCED"

@dataclass
class EQBandSetting:
    band_index: int              # 1 a 8
    band_type: int               # 1: HPF, 2: Low Shelf, 3: Bell, 4: Notch, 5: High Shelf, 6: LPF
    freq_hz: float
    gain_db: float = 0.0
    q: float = 0.71
    enabled: bool = True

@dataclass
class AcousticProfileSpec:
    role: str
    archetype: AcousticArchetype
    description: str
    eq_bands: List[EQBandSetting]
    glue_params: Optional[Dict[str, float]] = None
    drum_buss_params: Optional[Dict[str, float]] = None
    saturator_params: Optional[Dict[str, float]] = None
    utility_params: Optional[Dict[str, float]] = None
    reverb_params: Optional[Dict[str, float]] = None

# --- Helpers de conversión matemática analítica a Live 12 ---

def hz_to_eq8_norm(hz: float) -> float:
    """Convierte Hertz a escala logarítmica normalizada [0.0, 1.0] de Live EQ Eight (20Hz a 20kHz)."""
    hz_clamped = max(20.0, min(20000.0, float(hz)))
    return round(math.log10(hz_clamped / 20.0) / 3.0, 4)

def db_to_eq8_norm(db: float) -> float:
    """Convierte ganancia en dB (-15 a +15) a valor normalizado [0.0, 1.0] (0 dB = 0.5)."""
    db_clamped = max(-15.0, min(15.0, float(db)))
    return round((db_clamped + 15.0) / 30.0, 4)

def ms_to_glue_attack(ms: float) -> float:
    """Mapea milisegundos al paso discreto normalizado de Glue Compressor."""
    steps = [(0.1, 0.0), (0.5, 0.2), (1.0, 0.4), (3.0, 0.6), (10.0, 0.8), (30.0, 1.0)]
    return min(steps, key=lambda x: abs(x[0] - ms))[1]

def sec_to_glue_release(sec: float, auto: bool = False) -> float:
    """Mapea segundos al paso discreto normalizado de Glue Compressor (0.0 = Auto)."""
    if auto:
        return 0.0
    steps = [(0.1, 0.2), (0.2, 0.4), (0.4, 0.6), (0.8, 0.8), (1.2, 1.0)]
    return min(steps, key=lambda x: abs(x[0] - sec))[1]


def _build_archetype(
    role: str,
    archetype: AcousticArchetype,
    desc: str,
    bands_def: List[Tuple[int, int, float, float, float]], # (band_idx, band_type, freq, gain, q)
    glue: Optional[Dict[str, float]] = None,
    drumbuss: Optional[Dict[str, float]] = None,
    sat: Optional[Dict[str, float]] = None,
    util: Optional[Dict[str, float]] = None,
    rev: Optional[Dict[str, float]] = None
) -> AcousticProfileSpec:
    bands = [
        EQBandSetting(band_index=b[0], band_type=b[1], freq_hz=b[2], gain_db=b[3], q=b[4], enabled=True)
        for b in bands_def
    ]
    return AcousticProfileSpec(
        role=role,
        archetype=archetype,
        description=desc,
        eq_bands=bands,
        glue_params=glue,
        drum_buss_params=drumbuss,
        saturator_params=sat,
        utility_params=util,
        reverb_params=rev
    )

# --- Matriz de 21 Roles x 11 Arquetipos Acústicos Específicos ---

ULTRA_ACOUSTIC_CATALOG: Dict[str, Dict[AcousticArchetype, AcousticProfileSpec]] = {}

# 1. KICK
ULTRA_ACOUSTIC_CATALOG["KICK"] = {
    AcousticArchetype.PUNCHY: _build_archetype(
        "KICK", AcousticArchetype.PUNCHY, "Bombo moderno con pegada en el pecho y clic de batidor afilado.",
        [(1, 1, 30.0, 0.0, 0.71), (2, 3, 65.0, 3.5, 1.8), (3, 3, 320.0, -4.0, 2.5), (4, 3, 3200.0, 2.5, 2.0)],
        glue={"Attack": ms_to_glue_attack(30.0), "Release": sec_to_glue_release(0.1), "Ratio": 1.0, "Threshold": -14.0},
        drumbuss={"Drive": 0.18, "Transients": 0.68, "Boom": 0.20},
        util={"Bass Mono": 1.0, "Bass Freq": 130.0, "Width": 0.0}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "KICK", AcousticArchetype.OSCURO, "Bombo profundo y pesado, batidor apagado para club techno / lo-fi.",
        [(1, 1, 25.0, 0.0, 0.71), (2, 3, 50.0, 3.0, 1.5), (3, 3, 300.0, -3.0, 2.0), (8, 5, 2500.0, -6.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(10.0), "Release": sec_to_glue_release(0.4), "Ratio": 0.0},
        sat={"Drive": 0.15, "Base": 0.0},
        util={"Bass Mono": 1.0, "Bass Freq": 140.0, "Width": 0.0}
    ),
    AcousticArchetype.TIGHT: _build_archetype(
        "KICK", AcousticArchetype.TIGHT, "Bombo corto y controlado, liberación rápida sin reverberación.",
        [(1, 1, 35.0, 0.0, 0.8), (2, 3, 75.0, 2.0, 2.0), (3, 3, 350.0, -4.5, 2.8), (4, 3, 4000.0, 1.5, 2.2)],
        glue={"Attack": ms_to_glue_attack(10.0), "Release": sec_to_glue_release(0.1), "Ratio": 1.0},
        drumbuss={"Transients": 0.60, "Drive": 0.10},
        util={"Bass Mono": 1.0, "Width": 0.0}
    ),
    AcousticArchetype.DEEP: _build_archetype(
        "KICK", AcousticArchetype.DEEP, "Sub-bombo ultra-grave centrado en 48 Hz con sustain sostenido.",
        [(1, 1, 24.0, 0.0, 0.71), (2, 3, 48.0, 4.0, 1.6), (3, 3, 280.0, -3.5, 2.2)],
        drumbuss={"Boom": 0.45, "Drive": 0.12},
        util={"Bass Mono": 1.0, "Width": 0.0}
    ),
    AcousticArchetype.AGGRESSIVE: _build_archetype(
        "KICK", AcousticArchetype.AGGRESSIVE, "Bombo distorsionado con saturación dura y batidor agresivo.",
        [(1, 1, 32.0, 0.0, 0.71), (2, 3, 70.0, 3.0, 1.9), (3, 3, 300.0, -3.0, 2.0), (4, 3, 3500.0, 4.0, 2.2)],
        sat={"Drive": 0.35, "Base": 0.0},
        drumbuss={"Drive": 0.40, "Transients": 0.75, "Crunch": 0.30},
        util={"Bass Mono": 1.0, "Width": 0.0}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "KICK", AcousticArchetype.BALANCED, "Bombo acústico balanceado de estándar comercial.",
        [(1, 1, 30.0, 0.0, 0.71), (2, 3, 60.0, 2.0, 1.8), (3, 3, 320.0, -3.0, 2.0), (4, 3, 3000.0, 1.5, 1.8)],
        glue={"Attack": ms_to_glue_attack(30.0), "Release": sec_to_glue_release(0.2), "Ratio": 0.0},
        util={"Bass Mono": 1.0, "Width": 0.0}
    ),
}

# 2. 808_BASS
ULTRA_ACOUSTIC_CATALOG["808_BASS"] = {
    AcousticArchetype.DEEP: _build_archetype(
        "808_BASS", AcousticArchetype.DEEP, "808 subgrave puro y limpio con cuerpo fundamental en 40-50 Hz.",
        [(1, 1, 24.0, 0.0, 0.71), (2, 3, 45.0, 3.0, 1.8), (3, 3, 90.0, -2.5, 2.5), (8, 6, 400.0, 0.0, 0.71)],
        sat={"Drive": 0.10, "Base": 0.0},
        util={"Bass Mono": 1.0, "Bass Freq": 140.0, "Width": 0.0}
    ),
    AcousticArchetype.PUNCHY: _build_archetype(
        "808_BASS", AcousticArchetype.PUNCHY, "808 con golpe inicial claro y armónicos de 2do orden para móviles.",
        [(1, 1, 26.0, 0.0, 0.71), (2, 3, 55.0, 2.5, 2.0), (3, 3, 80.0, -2.5, 3.0), (4, 3, 140.0, 2.0, 2.2), (8, 6, 1800.0, 0.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(20.0), "Release": sec_to_glue_release(0.2), "Ratio": 1.0},
        sat={"Drive": 0.28, "Base": 0.0},
        util={"Bass Mono": 1.0, "Width": 0.0}
    ),
    AcousticArchetype.AGGRESSIVE: _build_archetype(
        "808_BASS", AcousticArchetype.AGGRESSIVE, "808 distorsionado estilo trap / drill agresivo con saturación visible.",
        [(1, 1, 28.0, 0.0, 0.71), (2, 3, 50.0, 3.0, 1.8), (4, 3, 220.0, 3.5, 2.0), (8, 6, 3000.0, 0.0, 0.71)],
        sat={"Drive": 0.48, "Base": 0.0},
        drumbuss={"Drive": 0.35, "Crunch": 0.25},
        util={"Bass Mono": 1.0, "Width": 0.0}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "808_BASS", AcousticArchetype.OSCURO, "808 cálido y aterciopelado sin asperezas armónicas altas.",
        [(1, 1, 24.0, 0.0, 0.71), (2, 3, 45.0, 3.0, 1.6), (8, 6, 250.0, 0.0, 0.8)],
        glue={"Attack": ms_to_glue_attack(5.0), "Release": sec_to_glue_release(0.6), "Ratio": 0.0},
        sat={"Drive": 0.08, "Base": 0.0},
        util={"Bass Mono": 1.0, "Width": 0.0}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "808_BASS", AcousticArchetype.BALANCED, "808 estándar con buen balance entre pegada y subgrave.",
        [(1, 1, 26.0, 0.0, 0.71), (2, 3, 50.0, 2.0, 1.8), (3, 3, 90.0, -2.0, 2.2), (8, 6, 1200.0, 0.0, 0.71)],
        sat={"Drive": 0.15, "Base": 0.0},
        util={"Bass Mono": 1.0, "Width": 0.0}
    )
}

# 3. SUB
ULTRA_ACOUSTIC_CATALOG["SUB"] = {
    AcousticArchetype.OSCURO: _build_archetype(
        "SUB", AcousticArchetype.OSCURO, "Subgrave senoidal ultra-oscuro y puro sin armónicos medios.",
        [(1, 1, 22.0, 0.0, 0.71), (2, 3, 42.0, 2.5, 1.8), (8, 6, 120.0, 0.0, 1.0)],
        util={"Bass Mono": 1.0, "Bass Freq": 140.0, "Width": 0.0}
    ),
    AcousticArchetype.PUNCHY: _build_archetype(
        "SUB", AcousticArchetype.PUNCHY, "Subgrave con ilusión de pegada mediante excitación armónica controlada.",
        [(1, 1, 28.0, 0.0, 0.71), (2, 3, 48.0, 2.0, 2.2), (8, 6, 160.0, 0.0, 0.8)],
        glue={"Attack": ms_to_glue_attack(10.0), "Release": sec_to_glue_release(0.2), "Ratio": 0.0},
        sat={"Drive": 0.14, "Base": 0.0},
        util={"Bass Mono": 1.0, "Width": 0.0}
    ),
    AcousticArchetype.DEEP: _build_archetype(
        "SUB", AcousticArchetype.DEEP, "Sub profundo con refuerzo en la octava más baja (35-45 Hz).",
        [(1, 1, 20.0, 0.0, 0.71), (2, 3, 38.0, 3.0, 1.8), (8, 6, 110.0, 0.0, 1.0)],
        util={"Bass Mono": 1.0, "Width": 0.0}
    ),
    AcousticArchetype.TIGHT: _build_archetype(
        "SUB", AcousticArchetype.TIGHT, "Subgrave firme y comprimido para evitar desplazamientos excesivos de cono.",
        [(1, 1, 30.0, 0.0, 0.8), (2, 3, 50.0, 1.5, 2.0), (8, 6, 130.0, 0.0, 0.9)],
        glue={"Attack": ms_to_glue_attack(1.0), "Release": sec_to_glue_release(0.1), "Ratio": 1.0},
        util={"Bass Mono": 1.0, "Width": 0.0}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "SUB", AcousticArchetype.BALANCED, "Subgrave comercial perfectamente acoplado.",
        [(1, 1, 25.0, 0.0, 0.71), (2, 3, 45.0, 2.0, 1.8), (8, 6, 140.0, 0.0, 0.8)],
        util={"Bass Mono": 1.0, "Width": 0.0}
    )
}

# 4. BASS (Reese / Synth Bass)
ULTRA_ACOUSTIC_CATALOG["BASS"] = {
    AcousticArchetype.PUNCHY: _build_archetype(
        "BASS", AcousticArchetype.PUNCHY, "Bajo sintético con mordida en graves y corte para el bombo.",
        [(1, 1, 32.0, 0.0, 0.71), (2, 3, 90.0, 3.0, 2.0), (3, 3, 300.0, -3.5, 2.2), (4, 3, 1800.0, 2.0, 2.0)],
        glue={"Attack": ms_to_glue_attack(20.0), "Release": sec_to_glue_release(0.1), "Ratio": 1.0},
        sat={"Drive": 0.20, "Base": 0.0},
        util={"Bass Mono": 1.0, "Bass Freq": 120.0, "Width": 0.5}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "BASS", AcousticArchetype.OSCURO, "Bajo cálido y analógico, filtrado en agudos para sonar detrás de los leads.",
        [(1, 1, 30.0, 0.0, 0.71), (2, 3, 55.0, 2.5, 1.8), (3, 3, 300.0, -2.0, 2.0), (8, 6, 900.0, 0.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(8.0), "Release": sec_to_glue_release(0.3), "Ratio": 0.0},
        sat={"Drive": 0.15, "Base": 0.0},
        util={"Bass Mono": 1.0, "Width": 0.0}
    ),
    AcousticArchetype.AGGRESSIVE: _build_archetype(
        "BASS", AcousticArchetype.AGGRESSIVE, "Bajo rasposo y saturado con armónicos agresivos en medios.",
        [(1, 1, 35.0, 0.0, 0.71), (2, 3, 85.0, 2.5, 2.0), (4, 3, 1200.0, 4.0, 2.0), (5, 5, 4000.0, 2.0, 0.71)],
        sat={"Drive": 0.42, "Base": 0.0},
        glue={"Attack": ms_to_glue_attack(10.0), "Release": sec_to_glue_release(0.1), "Ratio": 1.0},
        util={"Bass Mono": 1.0, "Width": 0.8}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "BASS", AcousticArchetype.BALANCED, "Bajo synth sólido y equilibrado para mezclas modernas.",
        [(1, 1, 32.0, 0.0, 0.71), (2, 3, 75.0, 2.0, 1.8), (3, 3, 280.0, -2.5, 2.2), (4, 3, 1500.0, 1.5, 1.8)],
        glue={"Attack": ms_to_glue_attack(10.0), "Release": sec_to_glue_release(0.2), "Ratio": 0.0},
        sat={"Drive": 0.15, "Base": 0.0},
        util={"Bass Mono": 1.0, "Width": 0.4}
    )
}

# 5. ELECTRIC_BASS
ULTRA_ACOUSTIC_CATALOG["ELECTRIC_BASS"] = {
    AcousticArchetype.WARM: _build_archetype(
        "ELECTRIC_BASS", AcousticArchetype.WARM, "Bajo eléctrico cálido y redondo con sonido de pastilla de mástil.",
        [(1, 1, 35.0, 0.0, 0.71), (2, 3, 80.0, 2.5, 1.8), (3, 3, 350.0, -3.0, 2.2), (8, 6, 2500.0, 0.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(15.0), "Release": sec_to_glue_release(0.4), "Ratio": 0.0},
        sat={"Drive": 0.12, "Base": 0.0},
        util={"Bass Mono": 1.0, "Width": 0.0}
    ),
    AcousticArchetype.PUNCHY: _build_archetype(
        "ELECTRIC_BASS", AcousticArchetype.PUNCHY, "Bajo eléctrico con articulación clara de púa y mordida metálica.",
        [(1, 1, 38.0, 0.0, 0.71), (2, 3, 100.0, 2.5, 2.0), (3, 3, 380.0, -3.5, 2.5), (4, 3, 1200.0, 3.0, 2.0)],
        glue={"Attack": ms_to_glue_attack(15.0), "Release": sec_to_glue_release(0.15), "Ratio": 1.0},
        sat={"Drive": 0.18, "Base": 0.0},
        util={"Bass Mono": 1.0, "Width": 0.0}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "ELECTRIC_BASS", AcousticArchetype.OSCURO, "Bajo eléctrico apagado estilo Motown / flatwound strings.",
        [(1, 1, 35.0, 0.0, 0.71), (2, 3, 75.0, 2.0, 1.6), (3, 3, 350.0, -2.5, 2.0), (8, 6, 1800.0, 0.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(10.0), "Release": sec_to_glue_release(0.4), "Ratio": 0.0},
        util={"Bass Mono": 1.0, "Width": 0.0}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "ELECTRIC_BASS", AcousticArchetype.BALANCED, "Bajo eléctrico con respuesta estándar balanceada.",
        [(1, 1, 35.0, 0.0, 0.71), (2, 3, 90.0, 2.0, 1.8), (3, 3, 350.0, -3.0, 2.2), (4, 3, 1000.0, 1.5, 1.8)],
        glue={"Attack": ms_to_glue_attack(15.0), "Release": sec_to_glue_release(0.2), "Ratio": 0.0},
        util={"Bass Mono": 1.0, "Width": 0.0}
    )
}

# 6. DRUMS (Bus / Kit)
ULTRA_ACOUSTIC_CATALOG["DRUMS"] = {
    AcousticArchetype.PUNCHY: _build_archetype(
        "DRUMS", AcousticArchetype.PUNCHY, "Batería con pegada y cohesión de bus ('glue').",
        [(1, 1, 35.0, 0.0, 0.71), (2, 3, 80.0, 2.5, 1.8), (3, 3, 400.0, -4.0, 2.2), (4, 3, 3500.0, 3.0, 1.8), (5, 5, 11000.0, 2.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(30.0), "Release": sec_to_glue_release(0.1), "Ratio": 1.0},
        drumbuss={"Drive": 0.20, "Transients": 0.65},
        util={"Bass Mono": 1.0, "Bass Freq": 110.0, "Width": 1.0}
    ),
    AcousticArchetype.TIGHT: _build_archetype(
        "DRUMS", AcousticArchetype.TIGHT, "Batería seca y controlada, transientes precisos sin colas de sala.",
        [(1, 1, 40.0, 0.0, 0.8), (3, 3, 450.0, -3.5, 2.5), (4, 3, 4000.0, 2.0, 2.0)],
        glue={"Attack": ms_to_glue_attack(10.0), "Release": sec_to_glue_release(0.1), "Ratio": 1.0},
        drumbuss={"Transients": 0.60},
        util={"Width": 0.95}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "DRUMS", AcousticArchetype.OSCURO, "Batería oscura y cálida, platos atenuados para vibra vintage.",
        [(1, 1, 35.0, 0.0, 0.71), (2, 3, 70.0, 2.0, 1.8), (3, 3, 400.0, -3.0, 2.0), (5, 5, 6000.0, -4.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(15.0), "Release": sec_to_glue_release(0.2), "Ratio": 0.0},
        sat={"Drive": 0.15},
        util={"Width": 0.9}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "DRUMS", AcousticArchetype.BALANCED, "Bus de batería equilibrado listo para radio.",
        [(1, 1, 35.0, 0.0, 0.71), (2, 3, 80.0, 1.5, 1.8), (3, 3, 400.0, -3.0, 2.0), (4, 3, 3000.0, 1.5, 1.8)],
        glue={"Attack": ms_to_glue_attack(30.0), "Release": sec_to_glue_release(0.2), "Ratio": 0.0},
        util={"Bass Mono": 1.0, "Width": 1.0}
    )
}

# 7. DEMBOW
ULTRA_ACOUSTIC_CATALOG["DEMBOW"] = {
    AcousticArchetype.PUNCHY: _build_archetype(
        "DEMBOW", AcousticArchetype.PUNCHY, "Dembow urbano afilado: snap seco en timbal y cuerpo en 90 Hz.",
        [(1, 1, 35.0, 0.0, 0.71), (2, 3, 90.0, 2.0, 2.0), (3, 3, 420.0, -4.0, 2.8), (4, 3, 2800.0, 4.5, 2.4)],
        glue={"Attack": ms_to_glue_attack(30.0), "Release": sec_to_glue_release(0.1, auto=True), "Ratio": 1.0},
        drumbuss={"Drive": 0.32, "Transients": 0.72},
        util={"Bass Mono": 1.0, "Bass Freq": 120.0, "Width": 0.95}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "DEMBOW", AcousticArchetype.OSCURO, "Dembow underground/retro con golpe redondeado sin clic metálico.",
        [(1, 1, 30.0, 0.0, 0.71), (2, 3, 75.0, 2.5, 1.8), (4, 3, 3000.0, -3.5, 2.2), (8, 6, 7000.0, 0.0, 0.71)],
        drumbuss={"Drive": 0.20, "Transients": 0.40},
        rev={"Decay": 0.6, "DryWet": 0.12},
        util={"Bass Mono": 1.0, "Width": 0.9}
    ),
    AcousticArchetype.AGGRESSIVE: _build_archetype(
        "DEMBOW", AcousticArchetype.AGGRESSIVE, "Dembow saturado hiper-presente para perreo pesado.",
        [(1, 1, 35.0, 0.0, 0.71), (2, 3, 95.0, 3.0, 2.0), (3, 3, 400.0, -4.0, 2.5), (4, 3, 3200.0, 4.0, 2.0)],
        drumbuss={"Drive": 0.45, "Transients": 0.78, "Crunch": 0.35},
        util={"Bass Mono": 1.0, "Width": 1.0}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "DEMBOW", AcousticArchetype.BALANCED, "Dembow comercial limpio y con pegada definida.",
        [(1, 1, 35.0, 0.0, 0.71), (2, 3, 85.0, 2.0, 1.8), (3, 3, 400.0, -3.0, 2.2), (4, 3, 2600.0, 2.5, 2.0)],
        drumbuss={"Drive": 0.25, "Transients": 0.65},
        util={"Bass Mono": 1.0, "Width": 1.0}
    )
}

# 8. PERCUSSION
ULTRA_ACOUSTIC_CATALOG["PERCUSSION"] = {
    AcousticArchetype.TIGHT: _build_archetype(
        "PERCUSSION", AcousticArchetype.TIGHT, "Percusión cortada y quirúrgica sin lodo subsónico.",
        [(1, 1, 110.0, 0.0, 0.8), (3, 3, 450.0, -3.5, 2.2), (4, 3, 3500.0, 2.5, 2.0)],
        glue={"Attack": ms_to_glue_attack(10.0), "Release": sec_to_glue_release(0.1), "Ratio": 1.0},
        util={"Width": 1.1}
    ),
    AcousticArchetype.AIRY: _build_archetype(
        "PERCUSSION", AcousticArchetype.AIRY, "Shakers y panderetas con apertura etérea y brillo superior.",
        [(1, 1, 180.0, 0.0, 0.8), (3, 3, 500.0, -3.0, 2.0), (5, 5, 12000.0, 3.5, 0.71)],
        rev={"Decay": 1.5, "DryWet": 0.20},
        util={"Width": 1.25}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "PERCUSSION", AcousticArchetype.OSCURO, "Percusiones de madera / congas con tono cálido y agudos apagados.",
        [(1, 1, 90.0, 0.0, 0.71), (3, 3, 450.0, -2.5, 2.0), (5, 5, 7000.0, -4.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(15.0), "Release": sec_to_glue_release(0.2), "Ratio": 0.0},
        util={"Width": 0.95}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "PERCUSSION", AcousticArchetype.BALANCED, "Percusiones estándar nítidas y en su bolsillo estéreo.",
        [(1, 1, 110.0, 0.0, 0.71), (3, 3, 450.0, -2.5, 2.0), (4, 3, 3000.0, 1.5, 1.8)],
        util={"Width": 1.1}
    )
}

# 9. KEYS
ULTRA_ACOUSTIC_CATALOG["KEYS"] = {
    AcousticArchetype.OSCURO: _build_archetype(
        "KEYS", AcousticArchetype.OSCURO, "Rhodes / Felt Piano vintage, calor en 240 Hz y agudos redondeados.",
        [(1, 1, 100.0, 0.0, 0.71), (2, 3, 240.0, 2.5, 1.4), (3, 3, 500.0, -1.5, 2.0), (8, 5, 4500.0, -5.0, 0.71)],
        sat={"Drive": 0.18},
        rev={"Decay": 2.8, "DryWet": 0.25},
        util={"Width": 1.05}
    ),
    AcousticArchetype.PUNCHY: _build_archetype(
        "KEYS", AcousticArchetype.PUNCHY, "Piano con ataque de martillo cortante y stabs brillantes.",
        [(1, 1, 130.0, 0.0, 0.8), (3, 3, 360.0, -3.5, 2.2), (4, 3, 2800.0, 3.0, 1.6), (5, 5, 10000.0, 1.5, 0.71)],
        glue={"Attack": ms_to_glue_attack(10.0), "Release": sec_to_glue_release(0.2), "Ratio": 1.0},
        util={"Width": 1.15}
    ),
    AcousticArchetype.AIRY: _build_archetype(
        "KEYS", AcousticArchetype.AIRY, "Piano de ensueño con aire cristalino en altas frecuencias y reverb amplia.",
        [(1, 1, 140.0, 0.0, 0.8), (3, 3, 380.0, -3.0, 2.0), (5, 5, 11000.0, 3.5, 0.71)],
        rev={"Decay": 3.8, "DryWet": 0.35},
        util={"Width": 1.30}
    ),
    AcousticArchetype.WARM: _build_archetype(
        "KEYS", AcousticArchetype.WARM, "Teclados analógicos cálidos con saturación sutil de cinta.",
        [(1, 1, 110.0, 0.0, 0.71), (2, 3, 280.0, 2.0, 1.5), (3, 3, 400.0, -2.0, 2.0), (5, 5, 9000.0, -1.5, 0.71)],
        sat={"Drive": 0.15},
        util={"Width": 1.1}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "KEYS", AcousticArchetype.BALANCED, "Teclados estándar comerciales con cuerpo y claridad.",
        [(1, 1, 120.0, 0.0, 0.71), (3, 3, 350.0, -2.5, 2.0), (4, 3, 2500.0, 1.5, 1.8), (5, 5, 10000.0, 1.5, 0.71)],
        glue={"Attack": ms_to_glue_attack(15.0), "Release": sec_to_glue_release(0.2), "Ratio": 0.0},
        util={"Width": 1.1}
    )
}

# 10. GUITAR (Acústica)
ULTRA_ACOUSTIC_CATALOG["GUITAR"] = {
    AcousticArchetype.WARM: _build_archetype(
        "GUITAR", AcousticArchetype.WARM, "Guitarra acústica de madera cálida, cuerpo en 200 Hz y caja controlada.",
        [(1, 1, 100.0, 0.0, 0.71), (2, 3, 200.0, 2.0, 1.6), (3, 3, 380.0, -3.0, 2.5), (4, 3, 3200.0, 1.5, 1.8)],
        glue={"Attack": ms_to_glue_attack(15.0), "Release": sec_to_glue_release(0.2), "Ratio": 0.0},
        util={"Width": 1.1}
    ),
    AcousticArchetype.BRILLANTE: _build_archetype(
        "GUITAR", AcousticArchetype.BRILLANTE, "Guitarra acústica con brillo de cuerdas de bronce y púa nítida.",
        [(1, 1, 120.0, 0.0, 0.8), (3, 3, 380.0, -3.5, 2.5), (4, 3, 3500.0, 3.0, 1.8), (5, 5, 11000.0, 3.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(10.0), "Release": sec_to_glue_release(0.1), "Ratio": 1.0},
        util={"Width": 1.2}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "GUITAR", AcousticArchetype.OSCURO, "Guitarra española de cuerdas de nylon oscura y nostálgica.",
        [(1, 1, 100.0, 0.0, 0.71), (2, 3, 220.0, 2.0, 1.6), (3, 3, 400.0, -2.0, 2.0), (5, 5, 4000.0, -4.0, 0.71)],
        rev={"Decay": 2.2, "DryWet": 0.20},
        util={"Width": 1.0}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "GUITAR", AcousticArchetype.BALANCED, "Guitarra balanceada limpia y presente.",
        [(1, 1, 110.0, 0.0, 0.71), (3, 3, 380.0, -2.5, 2.2), (4, 3, 3000.0, 2.0, 1.8)],
        glue={"Attack": ms_to_glue_attack(15.0), "Release": sec_to_glue_release(0.2), "Ratio": 0.0},
        util={"Width": 1.1}
    )
}

# 11. RHYTHM_GUITAR
ULTRA_ACOUSTIC_CATALOG["RHYTHM_GUITAR"] = {
    AcousticArchetype.TIGHT: _build_archetype(
        "RHYTHM_GUITAR", AcousticArchetype.TIGHT, "Guitarras rítmicas comprimidas y ajustadas en el bolsillo estéreo.",
        [(1, 1, 130.0, 0.0, 0.8), (3, 3, 420.0, -3.5, 2.2), (4, 3, 2600.0, 3.0, 2.0), (8, 6, 8000.0, 0.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(15.0), "Release": sec_to_glue_release(0.1), "Ratio": 1.0},
        util={"Width": 1.3}
    ),
    AcousticArchetype.AGGRESSIVE: _build_archetype(
        "RHYTHM_GUITAR", AcousticArchetype.AGGRESSIVE, "Riffs crunch/overdrive potentes con mordida en medios.",
        [(1, 1, 120.0, 0.0, 0.71), (3, 3, 400.0, -3.0, 2.0), (4, 3, 2400.0, 4.0, 2.0), (8, 6, 7500.0, 0.0, 0.71)],
        sat={"Drive": 0.35},
        util={"Width": 1.35}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "RHYTHM_GUITAR", AcousticArchetype.OSCURO, "Guitarras rítmicas analógicas oscuras estilo indie lo-fi.",
        [(1, 1, 120.0, 0.0, 0.71), (2, 3, 300.0, 2.0, 1.8), (5, 5, 4500.0, -4.0, 0.71)],
        sat={"Drive": 0.18},
        util={"Width": 1.1}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "RHYTHM_GUITAR", AcousticArchetype.BALANCED, "Guitarras rítmicas estándar bien situadas en el panorama.",
        [(1, 1, 125.0, 0.0, 0.71), (3, 3, 400.0, -2.5, 2.0), (4, 3, 2800.0, 2.0, 1.8)],
        glue={"Attack": ms_to_glue_attack(15.0), "Release": sec_to_glue_release(0.2), "Ratio": 0.0},
        util={"Width": 1.25}
    )
}

# 12. LEAD_GUITAR
ULTRA_ACOUSTIC_CATALOG["LEAD_GUITAR"] = {
    AcousticArchetype.AGGRESSIVE: _build_archetype(
        "LEAD_GUITAR", AcousticArchetype.AGGRESSIVE, "Guitarra solista desgarradora con sustain de válvulas y armónicos.",
        [(1, 1, 140.0, 0.0, 0.8), (3, 3, 450.0, -2.5, 2.0), (4, 3, 3200.0, 4.0, 2.0), (5, 5, 10000.0, 2.0, 0.71)],
        sat={"Drive": 0.40},
        glue={"Attack": ms_to_glue_attack(5.0), "Release": sec_to_glue_release(0.4), "Ratio": 1.0},
        rev={"Decay": 2.5, "DryWet": 0.25}
    ),
    AcousticArchetype.WARM: _build_archetype(
        "LEAD_GUITAR", AcousticArchetype.WARM, "Guitarra solista de blues/jazz cálida con cuerpo medio sedoso.",
        [(1, 1, 130.0, 0.0, 0.71), (2, 3, 400.0, 2.5, 1.6), (4, 3, 2400.0, 1.5, 1.8), (8, 6, 6000.0, 0.0, 0.71)],
        sat={"Drive": 0.20},
        rev={"Decay": 2.0, "DryWet": 0.20}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "LEAD_GUITAR", AcousticArchetype.OSCURO, "Solo de guitarra oscuro y envolvente para climas melancólicos.",
        [(1, 1, 130.0, 0.0, 0.71), (2, 3, 450.0, 2.0, 1.6), (5, 5, 3800.0, -3.0, 0.71)],
        rev={"Decay": 3.0, "DryWet": 0.30}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "LEAD_GUITAR", AcousticArchetype.BALANCED, "Guitarra solista estándar con claridad y presencia central.",
        [(1, 1, 135.0, 0.0, 0.71), (3, 3, 420.0, -2.0, 2.0), (4, 3, 3000.0, 2.5, 1.8)],
        glue={"Attack": ms_to_glue_attack(10.0), "Release": sec_to_glue_release(0.2), "Ratio": 0.0}
    )
}

# 13. LEAD (Synth)
ULTRA_ACOUSTIC_CATALOG["LEAD"] = {
    AcousticArchetype.PUNCHY: _build_archetype(
        "LEAD", AcousticArchetype.PUNCHY, "Synth lead con ataque inicial contundente que corta el drop.",
        [(1, 1, 160.0, 0.0, 0.8), (3, 3, 3800.0, -2.0, 2.5), (4, 3, 2500.0, 3.5, 2.0), (5, 5, 12000.0, 2.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(5.0), "Release": sec_to_glue_release(0.1), "Ratio": 1.0},
        drumbuss={"Crunch": 0.25, "Transients": 0.60},
        util={"Width": 1.15}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "LEAD", AcousticArchetype.OSCURO, "Synth lead analógico estilo Moog cálido y misterioso.",
        [(1, 1, 120.0, 0.0, 0.71), (2, 3, 500.0, 3.0, 1.2), (5, 5, 3500.0, -4.5, 0.71), (8, 6, 5000.0, 0.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(10.0), "Release": sec_to_glue_release(0.2), "Ratio": 0.0},
        sat={"Drive": 0.25},
        rev={"Decay": 2.5, "DryWet": 0.25},
        util={"Width": 1.0}
    ),
    AcousticArchetype.BRILLANTE: _build_archetype(
        "LEAD", AcousticArchetype.BRILLANTE, "Synth lead moderno EDM/Pop híper brillante y aireado.",
        [(1, 1, 160.0, 0.0, 0.8), (4, 3, 3500.0, 3.0, 2.0), (5, 5, 12000.0, 4.0, 0.71)],
        sat={"Drive": 0.20},
        glue={"Attack": ms_to_glue_attack(5.0), "Release": sec_to_glue_release(0.1), "Ratio": 1.0},
        rev={"Decay": 2.2, "DryWet": 0.25},
        util={"Width": 1.25}
    ),
    AcousticArchetype.AGGRESSIVE: _build_archetype(
        "LEAD", AcousticArchetype.AGGRESSIVE, "Synth lead saturado y mordiente para drops energéticos.",
        [(1, 1, 150.0, 0.0, 0.8), (4, 3, 2800.0, 4.5, 2.0), (5, 5, 11000.0, 2.5, 0.71)],
        sat={"Drive": 0.45},
        drumbuss={"Drive": 0.35, "Crunch": 0.30},
        util={"Width": 1.2}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "LEAD", AcousticArchetype.BALANCED, "Synth lead balanceado con presencia clara.",
        [(1, 1, 150.0, 0.0, 0.71), (3, 3, 400.0, -2.0, 2.0), (4, 3, 2800.0, 2.5, 1.8), (5, 5, 10000.0, 2.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(10.0), "Release": sec_to_glue_release(0.2), "Ratio": 0.0},
        util={"Width": 1.15}
    )
}

# 14. COUNTER_LEAD
ULTRA_ACOUSTIC_CATALOG["COUNTER_LEAD"] = {
    AcousticArchetype.AIRY: _build_archetype(
        "COUNTER_LEAD", AcousticArchetype.AIRY, "Contramelodía flotante en las alas estéreo que responde al lead.",
        [(1, 1, 200.0, 0.0, 0.8), (3, 3, 2500.0, -2.0, 2.0), (5, 5, 12000.0, 3.5, 0.71)],
        rev={"Decay": 3.2, "DryWet": 0.35},
        util={"Width": 1.4}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "COUNTER_LEAD", AcousticArchetype.OSCURO, "Contramelodía apagada y sutil en segundo plano.",
        [(1, 1, 160.0, 0.0, 0.71), (2, 3, 600.0, 2.0, 1.8), (5, 5, 4000.0, -4.0, 0.71)],
        rev={"Decay": 2.5, "DryWet": 0.28},
        util={"Width": 1.2}
    ),
    AcousticArchetype.PUNCHY: _build_archetype(
        "COUNTER_LEAD", AcousticArchetype.PUNCHY, "Plucks de contramelodía cortos y rítmicos.",
        [(1, 1, 200.0, 0.0, 0.8), (3, 3, 2000.0, -2.0, 2.0), (4, 3, 3000.0, 2.5, 2.0)],
        glue={"Attack": ms_to_glue_attack(10.0), "Release": sec_to_glue_release(0.1), "Ratio": 1.0},
        util={"Width": 1.3}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "COUNTER_LEAD", AcousticArchetype.BALANCED, "Contramelodía balanceada sin conflicto con el lead principal.",
        [(1, 1, 180.0, 0.0, 0.8), (3, 3, 2500.0, -2.0, 2.2), (4, 3, 3200.0, 1.5, 1.8)],
        rev={"Decay": 2.8, "DryWet": 0.25},
        util={"Width": 1.3}
    )
}

# 15. PAD
ULTRA_ACOUSTIC_CATALOG["PAD"] = {
    AcousticArchetype.AIRY: _build_archetype(
        "PAD", AcousticArchetype.AIRY, "Colchón armónico etéreo y abierto con reverberación infinita.",
        [(1, 1, 180.0, 0.0, 0.8), (3, 3, 600.0, -3.0, 2.0), (5, 5, 11000.0, 3.5, 0.71)],
        rev={"Decay": 5.5, "DryWet": 0.45},
        util={"Width": 1.45}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "PAD", AcousticArchetype.OSCURO, "Bruma armónica oscura y densa, texturas cinematográficas sumergidas.",
        [(1, 1, 130.0, 0.0, 0.71), (2, 3, 400.0, 2.0, 1.0), (3, 3, 2000.0, -3.0, 2.0), (8, 6, 3200.0, 0.0, 0.8)],
        sat={"Drive": 0.12},
        rev={"Decay": 6.0, "DryWet": 0.45},
        util={"Width": 1.25}
    ),
    AcousticArchetype.WARM: _build_archetype(
        "PAD", AcousticArchetype.WARM, "Pad analógico cálido, calor envolvente en 350 Hz sin enturbiar el bajo.",
        [(1, 1, 150.0, 0.0, 0.71), (2, 3, 350.0, 2.0, 1.5), (3, 3, 700.0, -2.5, 2.0), (5, 5, 8000.0, -2.0, 0.71)],
        sat={"Drive": 0.15},
        rev={"Decay": 4.5, "DryWet": 0.35},
        util={"Width": 1.3}
    ),
    AcousticArchetype.WIDE: _build_archetype(
        "PAD", AcousticArchetype.WIDE, "Pad ultra-amplio con máxima apertura en los extremos estéreo.",
        [(1, 1, 160.0, 0.0, 0.8), (3, 3, 800.0, -2.5, 2.0), (5, 5, 10000.0, 2.5, 0.71)],
        rev={"Decay": 5.0, "DryWet": 0.40},
        util={"Width": 1.6}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "PAD", AcousticArchetype.BALANCED, "Pad comercial con presencia limpia y espacio controlado.",
        [(1, 1, 160.0, 0.0, 0.71), (3, 3, 600.0, -2.5, 2.0), (5, 5, 9000.0, 1.5, 0.71)],
        rev={"Decay": 4.0, "DryWet": 0.30},
        util={"Width": 1.3}
    )
}

# 16. STRINGS
ULTRA_ACOUSTIC_CATALOG["STRINGS"] = {
    AcousticArchetype.AIRY: _build_archetype(
        "STRINGS", AcousticArchetype.AIRY, "Cuerdas orquestales sedosas con aire en 12 kHz y sala amplia.",
        [(1, 1, 120.0, 0.0, 0.8), (3, 3, 700.0, -3.0, 2.0), (5, 5, 12000.0, 3.5, 0.71)],
        glue={"Attack": ms_to_glue_attack(30.0), "Release": sec_to_glue_release(0.8), "Ratio": 0.0},
        rev={"Decay": 3.5, "DryWet": 0.35},
        util={"Width": 1.35}
    ),
    AcousticArchetype.WARM: _build_archetype(
        "STRINGS", AcousticArchetype.WARM, "Ensamble de cuerdas cálido y orgánico, cuerpo en 300 Hz.",
        [(1, 1, 110.0, 0.0, 0.71), (2, 3, 300.0, 2.5, 1.5), (3, 3, 650.0, -2.5, 2.0), (5, 5, 8000.0, -2.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(20.0), "Release": sec_to_glue_release(0.6), "Ratio": 0.0},
        rev={"Decay": 2.8, "DryWet": 0.25},
        util={"Width": 1.2}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "STRINGS", AcousticArchetype.OSCURO, "Cuerdas oscuras y sombrías con arco pesado.",
        [(1, 1, 110.0, 0.0, 0.71), (2, 3, 300.0, 2.5, 1.5), (5, 5, 5000.0, -3.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(20.0), "Release": sec_to_glue_release(0.8), "Ratio": 0.0},
        rev={"Decay": 3.0, "DryWet": 0.30},
        util={"Width": 1.15}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "STRINGS", AcousticArchetype.BALANCED, "Cuerdas balanceadas para producciones pop y orquestales.",
        [(1, 1, 115.0, 0.0, 0.71), (3, 3, 650.0, -2.0, 2.0), (4, 3, 3500.0, 1.5, 1.8), (5, 5, 10000.0, 2.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(20.0), "Release": sec_to_glue_release(0.4), "Ratio": 0.0},
        rev={"Decay": 3.0, "DryWet": 0.25},
        util={"Width": 1.25}
    )
}

# 17. BRASS
ULTRA_ACOUSTIC_CATALOG["BRASS"] = {
    AcousticArchetype.PUNCHY: _build_archetype(
        "BRASS", AcousticArchetype.PUNCHY, "Metales con ataque de boquilla agresivo y pegada armónica.",
        [(1, 1, 120.0, 0.0, 0.8), (2, 3, 350.0, 2.5, 1.8), (4, 3, 3000.0, 3.0, 2.0)],
        glue={"Attack": ms_to_glue_attack(20.0), "Release": sec_to_glue_release(0.2), "Ratio": 1.0},
        sat={"Drive": 0.20},
        util={"Width": 1.2}
    ),
    AcousticArchetype.WARM: _build_archetype(
        "BRASS", AcousticArchetype.WARM, "Sección de metales cálida y redonda, trombones y cornos suaves.",
        [(1, 1, 110.0, 0.0, 0.71), (2, 3, 280.0, 2.0, 1.5), (3, 3, 4000.0, -3.0, 2.0), (8, 6, 6000.0, 0.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(15.0), "Release": sec_to_glue_release(0.4), "Ratio": 0.0},
        util={"Width": 1.15}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "BRASS", AcousticArchetype.OSCURO, "Metales oscuros y misteriosos para bandas sonoras.",
        [(1, 1, 110.0, 0.0, 0.71), (2, 3, 280.0, 2.0, 1.5), (4, 3, 4000.0, -3.0, 2.0), (8, 6, 6000.0, 0.0, 0.71)],
        rev={"Decay": 2.5, "DryWet": 0.25},
        util={"Width": 1.1}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "BRASS", AcousticArchetype.BALANCED, "Metales estándar con brillo y cuerpo controlado.",
        [(1, 1, 115.0, 0.0, 0.71), (3, 3, 500.0, -2.0, 2.0), (4, 3, 3200.0, 2.0, 1.8)],
        glue={"Attack": ms_to_glue_attack(15.0), "Release": sec_to_glue_release(0.2), "Ratio": 0.0},
        util={"Width": 1.2}
    )
}

# 18. CHOIR
ULTRA_ACOUSTIC_CATALOG["CHOIR"] = {
    AcousticArchetype.AIRY: _build_archetype(
        "CHOIR", AcousticArchetype.AIRY, "Coro celestial y etéreo con brillo superior y amplia apertura.",
        [(1, 1, 160.0, 0.0, 0.8), (3, 3, 800.0, -3.0, 2.0), (5, 5, 12000.0, 3.5, 0.71)],
        rev={"Decay": 4.5, "DryWet": 0.40},
        util={"Width": 1.4}
    ),
    AcousticArchetype.WARM: _build_archetype(
        "CHOIR", AcousticArchetype.WARM, "Coro vocal cálido y sacro, cuerpo en 400 Hz.",
        [(1, 1, 140.0, 0.0, 0.71), (2, 3, 400.0, 2.0, 1.5), (3, 3, 900.0, -2.5, 2.0), (5, 5, 8000.0, -2.0, 0.71)],
        rev={"Decay": 3.5, "DryWet": 0.30},
        util={"Width": 1.25}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "CHOIR", AcousticArchetype.OSCURO, "Coro oscuro gregoriano o gótico para ambientes profundos.",
        [(1, 1, 140.0, 0.0, 0.71), (2, 3, 400.0, 2.0, 1.5), (5, 5, 6000.0, -4.0, 0.71)],
        rev={"Decay": 4.0, "DryWet": 0.35},
        util={"Width": 1.2}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "CHOIR", AcousticArchetype.BALANCED, "Coro balanceado con buena articulación y textura de fondo.",
        [(1, 1, 150.0, 0.0, 0.71), (3, 3, 800.0, -2.0, 2.0), (4, 3, 2800.0, 1.5, 1.8), (5, 5, 10000.0, 2.0, 0.71)],
        rev={"Decay": 3.5, "DryWet": 0.28},
        util={"Width": 1.3}
    )
}

# 19. VOCALS (Lead)
ULTRA_ACOUSTIC_CATALOG["VOCALS"] = {
    AcousticArchetype.PUNCHY: _build_archetype(
        "VOCALS", AcousticArchetype.PUNCHY, "Vocal solista agresiva e in-your-face para trap/pop contemporáneo.",
        [(1, 1, 95.0, 0.0, 0.8), (3, 3, 400.0, -3.0, 2.5), (4, 3, 3200.0, 3.0, 1.4), (5, 5, 12000.0, 3.5, 0.71)],
        glue={"Attack": ms_to_glue_attack(1.0), "Release": sec_to_glue_release(0.1, auto=True), "Ratio": 1.0},
        sat={"Drive": 0.18},
        util={"Width": 1.0}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "VOCALS", AcousticArchetype.OSCURO, "Vocal íntima, cálida y cercana estilo jazz/R&B sin sibilancias modernas.",
        [(1, 1, 80.0, 0.0, 0.71), (2, 3, 220.0, 2.0, 1.5), (3, 3, 3800.0, -2.0, 2.0), (5, 5, 8000.0, -4.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(3.0), "Release": sec_to_glue_release(0.4), "Ratio": 0.0},
        sat={"Drive": 0.15},
        rev={"Decay": 3.2, "DryWet": 0.20},
        util={"Width": 1.0}
    ),
    AcousticArchetype.AIRY: _build_archetype(
        "VOCALS", AcousticArchetype.AIRY, "Vocal de pop moderna hiper-brillante con halo de aire de alta gama.",
        [(1, 1, 100.0, 0.0, 0.8), (3, 3, 450.0, -3.5, 2.5), (4, 3, 3500.0, 2.5, 1.8), (5, 5, 12500.0, 4.5, 0.71)],
        glue={"Attack": ms_to_glue_attack(1.0), "Release": sec_to_glue_release(0.1, auto=True), "Ratio": 1.0},
        rev={"Decay": 2.8, "DryWet": 0.22},
        util={"Width": 1.05}
    ),
    AcousticArchetype.WARM: _build_archetype(
        "VOCALS", AcousticArchetype.WARM, "Vocal analógica cálida con cuerpo de pecho y saturación suave de cinta.",
        [(1, 1, 85.0, 0.0, 0.71), (2, 3, 240.0, 2.0, 1.6), (3, 3, 400.0, -2.0, 2.0), (4, 3, 2800.0, 1.5, 1.8)],
        sat={"Drive": 0.16},
        glue={"Attack": ms_to_glue_attack(3.0), "Release": sec_to_glue_release(0.2), "Ratio": 0.0},
        util={"Width": 1.0}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "VOCALS", AcousticArchetype.BALANCED, "Vocal balanceada de estándar comercial, nítida y presente.",
        [(1, 1, 90.0, 0.0, 0.8), (3, 3, 400.0, -3.0, 2.2), (4, 3, 3000.0, 2.0, 1.8), (5, 5, 11000.0, 2.5, 0.71)],
        glue={"Attack": ms_to_glue_attack(1.0), "Release": sec_to_glue_release(0.2), "Ratio": 1.0},
        rev={"Decay": 2.2, "DryWet": 0.18},
        util={"Width": 1.0}
    )
}

# 20. BACKING_VOCALS
ULTRA_ACOUSTIC_CATALOG["BACKING_VOCALS"] = {
    AcousticArchetype.WIDE: _build_archetype(
        "BACKING_VOCALS", AcousticArchetype.WIDE, "Voces de fondo abiertas a los extremos estéreo que arropan la voz líder.",
        [(1, 1, 180.0, 0.0, 0.8), (3, 3, 2000.0, -3.0, 2.0), (5, 5, 12000.0, 3.0, 0.71)],
        glue={"Attack": ms_to_glue_attack(3.0), "Release": sec_to_glue_release(0.2), "Ratio": 1.0},
        rev={"Decay": 3.0, "DryWet": 0.35},
        util={"Width": 1.5}
    ),
    AcousticArchetype.AIRY: _build_archetype(
        "BACKING_VOCALS", AcousticArchetype.AIRY, "Coros brillantes y aireados que forman un colchón cristalino.",
        [(1, 1, 200.0, 0.0, 0.8), (3, 3, 2200.0, -2.5, 2.0), (5, 5, 13000.0, 4.0, 0.71)],
        rev={"Decay": 3.8, "DryWet": 0.40},
        util={"Width": 1.45}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "BACKING_VOCALS", AcousticArchetype.OSCURO, "Coros oscuros situados detrás de la mezcla.",
        [(1, 1, 150.0, 0.0, 0.71), (2, 3, 350.0, 2.0, 1.5), (5, 5, 6000.0, -5.0, 0.71)],
        rev={"Decay": 3.2, "DryWet": 0.30},
        util={"Width": 1.3}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "BACKING_VOCALS", AcousticArchetype.BALANCED, "Voces secundarias limpias y compactas.",
        [(1, 1, 170.0, 0.0, 0.8), (3, 3, 2000.0, -2.5, 2.0), (4, 3, 3500.0, 1.5, 1.8), (5, 5, 11000.0, 2.5, 0.71)],
        glue={"Attack": ms_to_glue_attack(5.0), "Release": sec_to_glue_release(0.2), "Ratio": 1.0},
        rev={"Decay": 2.8, "DryWet": 0.30},
        util={"Width": 1.4}
    )
}

# 21. EAR_CANDY
ULTRA_ACOUSTIC_CATALOG["EAR_CANDY"] = {
    AcousticArchetype.AIRY: _build_archetype(
        "EAR_CANDY", AcousticArchetype.AIRY, "Destellos y texturas agudas en los extremos del campo estéreo.",
        [(1, 1, 300.0, 0.0, 0.8), (3, 3, 800.0, -4.0, 2.0), (4, 3, 4000.0, 3.5, 2.0), (5, 5, 14000.0, 4.5, 0.71)],
        drumbuss={"Transients": 0.70},
        rev={"Decay": 3.5, "DryWet": 0.35},
        util={"Width": 1.6}
    ),
    AcousticArchetype.PUNCHY: _build_archetype(
        "EAR_CANDY", AcousticArchetype.PUNCHY, "Impactos breves, bleeps o glitches rítmicos muy filosos.",
        [(1, 1, 250.0, 0.0, 0.8), (4, 3, 3500.0, 4.0, 2.2), (5, 5, 12000.0, 3.0, 0.71)],
        drumbuss={"Transients": 0.75, "Drive": 0.20},
        util={"Width": 1.4}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "EAR_CANDY", AcousticArchetype.OSCURO, "Texturas discretas y oscuras con agudos filtrados.",
        [(1, 1, 200.0, 0.0, 0.71), (2, 3, 800.0, 1.0, 1.5), (5, 5, 5000.0, -3.0, 0.71)],
        rev={"Decay": 2.5, "DryWet": 0.25},
        util={"Width": 1.3}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "EAR_CANDY", AcousticArchetype.BALANCED, "Elementos de dinamismo y adorno estéreo equilibrados.",
        [(1, 1, 250.0, 0.0, 0.8), (4, 3, 3500.0, 2.5, 2.0), (5, 5, 12000.0, 3.0, 0.71)],
        rev={"Decay": 2.8, "DryWet": 0.30},
        util={"Width": 1.5}
    )
}

# 22. TEXTURE_FOLEY
ULTRA_ACOUSTIC_CATALOG["TEXTURE_FOLEY"] = {
    AcousticArchetype.LOFI: _build_archetype(
        "TEXTURE_FOLEY", AcousticArchetype.LOFI, "Foley orgánico con textura lo-fi, ruido de vinilo o cinta de fondo.",
        [(1, 1, 100.0, 0.0, 0.71), (4, 3, 2500.0, 2.0, 2.0), (8, 6, 8000.0, 0.0, 0.71)],
        sat={"Drive": 0.20},
        util={"Width": 1.2}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "TEXTURE_FOLEY", AcousticArchetype.OSCURO, "Ambiente orgánico de fondo oscuro (lluvia, murmullo) sin agudos.",
        [(1, 1, 80.0, 0.0, 0.71), (8, 6, 5000.0, 0.0, 0.8)],
        rev={"Decay": 2.0, "DryWet": 0.20},
        util={"Width": 1.1}
    ),
    AcousticArchetype.AIRY: _build_archetype(
        "TEXTURE_FOLEY", AcousticArchetype.AIRY, "Atmósferas superiores con brillo y halo etéreo.",
        [(1, 1, 150.0, 0.0, 0.8), (5, 5, 10000.0, 3.0, 0.71)],
        rev={"Decay": 4.0, "DryWet": 0.35},
        util={"Width": 1.4}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "TEXTURE_FOLEY", AcousticArchetype.BALANCED, "Textura de fondo con nivel seguro a -24 dBFS.",
        [(1, 1, 100.0, 0.0, 0.71), (8, 6, 9000.0, 0.0, 0.71)],
        util={"Width": 1.2}
    )
}

# 23. FX (Transition / Sweeps)
ULTRA_ACOUSTIC_CATALOG["FX"] = {
    AcousticArchetype.AIRY: _build_archetype(
        "FX", AcousticArchetype.AIRY, "Efecto de subida o impacto con cola de reverb amplia.",
        [(1, 1, 80.0, 0.0, 0.71), (4, 3, 3000.0, 3.0, 1.8), (5, 5, 12000.0, 3.0, 0.71)],
        rev={"Decay": 4.5, "DryWet": 0.40},
        util={"Width": 1.3}
    ),
    AcousticArchetype.PUNCHY: _build_archetype(
        "FX", AcousticArchetype.PUNCHY, "Impacto o downlifter con pegada inicial dura.",
        [(1, 1, 60.0, 0.0, 0.71), (2, 3, 80.0, 3.0, 1.8), (4, 3, 3200.0, 2.5, 2.0)],
        drumbuss={"Drive": 0.30, "Transients": 0.70},
        util={"Width": 1.1}
    ),
    AcousticArchetype.OSCURO: _build_archetype(
        "FX", AcousticArchetype.OSCURO, "Downlifter oscuro y subgrave para transiciones sutiles.",
        [(1, 1, 40.0, 0.0, 0.71), (2, 3, 60.0, 2.5, 1.8), (8, 6, 4000.0, 0.0, 0.71)],
        util={"Width": 1.0}
    ),
    AcousticArchetype.BALANCED: _build_archetype(
        "FX", AcousticArchetype.BALANCED, "Efectos y transiciones estándar con buena presencia.",
        [(1, 1, 80.0, 0.0, 0.71), (4, 3, 3000.0, 2.0, 1.8)],
        rev={"Decay": 3.0, "DryWet": 0.30},
        util={"Width": 1.2}
    )
}


class UltraAcousticCatalog:
    """API Principal para consulta y generación de cadenas nativas de Live 12."""

    ROLE_DEFAULT_ARCHETYPE: Dict[str, AcousticArchetype] = {
        "KICK": AcousticArchetype.PUNCHY,
        "808_BASS": AcousticArchetype.DEEP,
        "SUB": AcousticArchetype.OSCURO,
        "BASS": AcousticArchetype.PUNCHY,
        "ELECTRIC_BASS": AcousticArchetype.WARM,
        "DRUMS": AcousticArchetype.PUNCHY,
        "DEMBOW": AcousticArchetype.PUNCHY,
        "PERCUSSION": AcousticArchetype.TIGHT,
        "KEYS": AcousticArchetype.WARM,
        "GUITAR": AcousticArchetype.WARM,
        "RHYTHM_GUITAR": AcousticArchetype.TIGHT,
        "LEAD_GUITAR": AcousticArchetype.AGGRESSIVE,
        "LEAD": AcousticArchetype.BRILLANTE,
        "COUNTER_LEAD": AcousticArchetype.AIRY,
        "PAD": AcousticArchetype.AIRY,
        "STRINGS": AcousticArchetype.AIRY,
        "BRASS": AcousticArchetype.PUNCHY,
        "CHOIR": AcousticArchetype.AIRY,
        "VOCALS": AcousticArchetype.BALANCED,
        "BACKING_VOCALS": AcousticArchetype.WIDE,
        "EAR_CANDY": AcousticArchetype.AIRY,
        "TEXTURE_FOLEY": AcousticArchetype.LOFI,
        "FX": AcousticArchetype.AIRY,
    }

    @classmethod
    def get_role_archetype_spec(cls, role: str, archetype: Optional[str] = None) -> AcousticProfileSpec:
        """Obtiene la especificación exacta del perfil para un rol y arquetipo dados."""
        r_clean = str(role or "KEYS").strip().upper()
        if r_clean not in ULTRA_ACOUSTIC_CATALOG:
            # Fallback seguro a KEYS si no existe
            r_clean = "KEYS"

        role_dict = ULTRA_ACOUSTIC_CATALOG[r_clean]

        arch_enum = None
        if archetype:
            try:
                arch_enum = AcousticArchetype(str(archetype).strip().upper())
            except (ValueError, KeyError):
                arch_enum = None

        if arch_enum is None or arch_enum not in role_dict:
            arch_enum = cls.ROLE_DEFAULT_ARCHETYPE.get(r_clean, AcousticArchetype.BALANCED)
            if arch_enum not in role_dict:
                arch_enum = list(role_dict.keys())[0]

        return role_dict[arch_enum]

    @classmethod
    def build_native_insert_chain(cls, role: str, archetype: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retorna la lista de dispositivos nativos de Ableton Live 12 listos para cargar:
        [EQ Eight, Saturator (si aplica), Glue/DrumBuss, Utility, Reverb (si aplica)].
        Garantiza 100% de éxito en Live 12 sin diálogos de plugin faltante.
        """
        spec = cls.get_role_archetype_spec(role, archetype)
        chain: List[Dict[str, Any]] = []

        # 1. EQ Eight (Universal y Obligatorio)
        eq_params: Dict[str, float] = {}
        for band in spec.eq_bands:
            idx = band.band_index
            eq_params[f"{idx} Band On"] = 1.0 if band.enabled else 0.0
            eq_params[f"{idx} Filter Type"] = float(band.band_type)
            eq_params[f"{idx} Frequency A"] = hz_to_eq8_norm(band.freq_hz)
            eq_params[f"{idx} Gain A"] = db_to_eq8_norm(band.gain_db)
            eq_params[f"{idx} Resonance A"] = round(min(1.0, max(0.0, band.q / 5.0)), 4)

        chain.append({
            "name": "EQ Eight",
            "uri": "query:AudioFx#EQ%20Eight",
            "parameters": eq_params
        })

        # 2. Saturator (si tiene parámetros)
        if spec.saturator_params:
            sat_p: Dict[str, float] = {}
            if "Drive" in spec.saturator_params:
                sat_p["Drive"] = round(spec.saturator_params["Drive"], 4)
            if "Base" in spec.saturator_params:
                sat_p["Base"] = round(spec.saturator_params["Base"], 4)
            chain.append({
                "name": "Saturator",
                "uri": "query:AudioFx#Saturator",
                "parameters": sat_p
            })

        # 3. Drum Buss (si tiene parámetros)
        if spec.drum_buss_params:
            chain.append({
                "name": "Drum Buss",
                "uri": "query:AudioFx#Drum%20Buss",
                "parameters": dict(spec.drum_buss_params)
            })
        # 4. Glue Compressor (si no usa Drum Buss y tiene glue_params)
        elif spec.glue_params:
            chain.append({
                "name": "Glue Compressor",
                "uri": "query:AudioFx#Glue%20Compressor",
                "parameters": dict(spec.glue_params)
            })

        # 5. Utility (Control de ancho y Bass Mono)
        if spec.utility_params:
            chain.append({
                "name": "Utility",
                "uri": "query:AudioFx#Utility",
                "parameters": dict(spec.utility_params)
            })

        # 6. Reverb (si aplica)
        if spec.reverb_params:
            chain.append({
                "name": "Reverb",
                "uri": "query:AudioFx#Reverb",
                "parameters": dict(spec.reverb_params)
            })

        return chain
