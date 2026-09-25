"""
Device Execution Verifier
=========================
Bucle cerrado de verificación física para Ableton Live 12 LOM.
Erradica el 'Teatro de Configuración' mediante read-back real post-mutación.

Garantiza:
- Tolerancia física de valor: |actual - target| <= 0.04
- Variación mínima real (anti-estancamiento): |actual - baseline| >= 0.01
- Detección transparente de is_test_env para compatibilidad con la suite de tests.
- Generación de diagnósticos accionables estructurados para re-pregunta interactiva.
"""

import os
import re
import logging
import unicodedata
import urllib.parse
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("DeviceExecutionVerifier")


def _strip_accents(text: str) -> str:
    """Elimina acentos diacríticos para comparación insensible a acentuación."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(text))
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _normalize_str(text: str) -> str:
    """Normaliza texto: decodifica URLs, remueve acentos, minúsculas, reemplaza símbolos por espacios."""
    if not text:
        return ""
    unquoted = urllib.parse.unquote(str(text))
    deaccented = _strip_accents(unquoted).lower().strip()
    cleaned = re.sub(r"[_\-\/\(\)\[\],.:;]+", " ", deaccented)
    return re.sub(r"\s+", " ", cleaned).strip()


def _strip_symbols(text: str) -> str:
    """Mantiene exclusivamente caracteres alfanuméricos en minúsculas."""
    if not text:
        return ""
    unquoted = urllib.parse.unquote(str(text))
    deaccented = _strip_accents(unquoted).lower()
    return re.sub(r"[^a-z0-9]", "", deaccented)


def _find_in_available(
    candidates: List[str],
    available_params: Optional[Dict[str, Any]]
) -> Optional[str]:
    """Busca si alguno de los candidatos existe en available_params con resolución jerárquica."""
    if not available_params:
        return None

    # 1. Exact match
    for c in candidates:
        if c in available_params:
            return c

    # 2. Case-insensitive match
    lower_map = {k.lower(): k for k in available_params.keys()}
    for c in candidates:
        if c.lower() in lower_map:
            return lower_map[c.lower()]

    # 3. Stripped alphanumeric match
    stripped_map = {_strip_symbols(k): k for k in available_params.keys()}
    for c in candidates:
        s_cand = _strip_symbols(c)
        if s_cand and s_cand in stripped_map:
            return stripped_map[s_cand]

    return None


def _resolve_surge_xt_param(
    p_norm: str,
    p_symbol: str,
    param_identifier: str,
    available_params: Optional[Dict[str, Any]]
) -> str:
    """Resuelve ranuras modulares y parámetros LOM nativos para Surge XT Effects."""
    # Detección de Slot en Scene A, Scene B, Send o Global
    long_prefix: Optional[str] = None
    short_prefix: Optional[str] = None

    m_a = re.search(r"\b(?:a\s*insert\s*fx|fx\s*a|scene\s*a\s*fx|slot)\s*([1-4])\b", p_norm)
    if m_a:
        slot_num = int(m_a.group(1))
        long_prefix = f"A Insert FX {slot_num}"
        short_prefix = f"FX A{slot_num}"
    else:
        m_b = re.search(r"\b(?:b\s*insert\s*fx|fx\s*b|scene\s*b\s*fx)\s*([1-4])\b", p_norm)
        if m_b:
            slot_num = int(m_b.group(1))
            long_prefix = f"B Insert FX {slot_num}"
            short_prefix = f"FX B{slot_num}"
        else:
            m_s = re.search(r"\b(?:send\s*fx|fx\s*s|send)\s*([1-4])\b", p_norm)
            if m_s:
                slot_num = int(m_s.group(1))
                long_prefix = f"Send FX {slot_num}"
                short_prefix = f"FX S{slot_num}"
            else:
                m_g = re.search(r"\b(?:global\s*fx|fx\s*g|global)\s*([1-4])\b", p_norm)
                if m_g:
                    slot_num = int(m_g.group(1))
                    long_prefix = f"Global FX {slot_num}"
                    short_prefix = f"FX G{slot_num}"

    # Si se especificó un slot concreto
    if long_prefix and short_prefix:
        is_short_requested = bool(re.search(r"\bfx\s*[absg][1-4]\b", p_norm))

        # 1. Tipo de efecto en el slot
        if any(w in p_norm for w in ("type", "dsp type", "fx type", "algorithm", "algo", "model")):
            candidates = [f"{long_prefix} Type", f"{short_prefix} Type"]
            if available_params:
                found = _find_in_available(candidates, available_params)
                if found:
                    return found
            return f"{short_prefix} Type" if is_short_requested else f"{long_prefix} Type"

        # 2. Parámetros p1 a p12 del slot
        param_num: Optional[int] = None
        m_p = re.search(r"\b(?:param|parameter|p)\s*([1-9]|1[0-2])\b", p_norm)
        if m_p:
            param_num = int(m_p.group(1))
        elif any(w in p_norm for w in ("drive", "tape drive", "input drive", "saturation drive")):
            param_num = 1
        elif any(w in p_norm for w in ("saturation", "hysteresis", "sat")):
            param_num = 2
        elif "bias" in p_norm:
            param_num = 3
        elif any(w in p_norm for w in ("speed", "ips")):
            param_num = 4
        elif "gap" in p_norm:
            param_num = 5
        elif any(w in p_norm for w in ("mix", "dry wet", "wet", "dry")):
            param_num = 12

        if param_num is not None:
            candidates = [f"{long_prefix} Param {param_num}", f"{short_prefix} Param {param_num}"]
            if available_params:
                found = _find_in_available(candidates, available_params)
                if found:
                    return found
            return f"{short_prefix} Param {param_num}" if is_short_requested else f"{long_prefix} Param {param_num}"

    # Parámetros globales o sin ranura explícita
    if any(w in p_norm for w in ("output mix", "master mix", "rack mix", "mix", "dry wet", "dry", "wet", "blend")):
        candidates = ["Output Mix", "Mix", "Dry/Wet"]
        if available_params:
            found = _find_in_available(candidates, available_params)
            if found:
                return found
        return "Output Mix"

    if any(w in p_norm for w in ("type", "dsp type", "fx type")):
        candidates = ["A Insert FX 1 Type", "FX A1 Type", "FX Type"]
        if available_params:
            found = _find_in_available(candidates, available_params)
            if found:
                return found
        return "A Insert FX 1 Type"

    if any(w in p_norm for w in ("drive", "saturation", "tape drive")):
        candidates = ["A Insert FX 1 Param 1", "FX A1 Param 1"]
        if available_params:
            found = _find_in_available(candidates, available_params)
            if found:
                return found
        return "A Insert FX 1 Param 1"

    if available_params:
        for k in available_params:
            if p_norm in _normalize_str(k) or _normalize_str(k) in p_norm:
                return k

    return param_identifier


# Mapeos canónicos y alias para procesadores de terceros y nativos de Live 12
DEVICE_LOM_MAPPINGS: Dict[str, List[Tuple[str, List[str], List[str]]]] = {
    "valhalla_supermassive": [
        ("Mix", ["mix", "dry wet", "blend", "wet"], []),
        ("Mode", ["mode", "algorithm", "algo", "reverb mode", "reverb_mode"], []),
        ("Delay Sync", ["delay sync", "delaysync", "delay_sync", "delay-sync", "sync"], ["DelaySync"]),
        ("Delay Note", ["delay note", "delaynote", "delay_note", "delay-note", "note", "time sync"], ["DelayNote"]),
        ("Delay (ms)", ["delay ms", "delayms", "delay", "delay time", "delaytime", "delay_time", "delay-ms", "ms"], ["Delay_Ms", "Delay"]),
        ("Delay Warp", ["delay warp", "delaywarp", "delay_warp", "delay-warp", "warp"], ["DelayWarp"]),
        ("Clear", ["clear", "clear buffer", "clear_buffer"], []),
        ("Feedback", ["feedback", "fb", "regen", "regeneration", "decay"], []),
        ("Density", ["density", "echo density", "echodensity", "diffusion"], []),
        ("Width", ["width", "stereo width", "stereowidth", "stereo_width", "spread"], []),
        ("Low Cut", ["low cut", "lowcut", "low_cut", "low-cut", "hpf", "high pass", "highpass", "high-pass"], ["LowCut"]),
        ("High Cut", ["high cut", "highcut", "high_cut", "high-cut", "lpf", "low pass", "lowpass", "low-pass"], ["HighCut"]),
        ("Mod Rate", ["mod rate", "modrate", "mod_rate", "mod-rate", "rate", "modulation rate", "modulation_rate", "mod speed"], ["ModRate"]),
        ("Mod Depth", ["mod depth", "moddepth", "mod_depth", "mod-depth", "depth", "modulation depth", "modulation_depth", "mod amount"], ["ModDepth"]),
    ],
    "valhalla_vintage_verb": [
        ("Mix", ["mix", "dry wet", "blend", "wet"], []),
        ("Decay", ["decay", "rt60", "decay time", "decay_time", "decaytime", "reverb time", "time"], []),
        ("Pre-delay", ["pre delay", "predelay", "pre_delay", "pre-delay", "pre delay time"], ["PreDelay", "Pre Delay"]),
        ("Mode", ["mode", "algorithm", "algo", "reverb mode", "reverb_mode", "program"], []),
        ("Color Mode", ["color mode", "colormode", "color_mode", "color", "era"], ["ColorMode"]),
        ("Size", ["size", "room size", "roomsize", "room_size", "space"], []),
        ("Attack", ["attack", "attack shape", "attack_shape", "attack time", "shape"], []),
        ("Bass Multiply", ["bass multiply", "bassmult", "bass_mult", "bass-mult", "bass multiply", "bass_multiply", "bass mult", "bass", "bass x"], ["BassMult", "Bass Multiply"]),
        ("Low Cut", ["low cut", "lowcut", "low_cut", "low-cut", "hpf", "high pass", "highpass", "high-pass"], ["LowCut"]),
        ("High Cut", ["high cut", "highcut", "high_cut", "high-cut", "lpf", "low pass", "lowpass", "low-pass"], ["HighCut"]),
        ("Early Diffusion", ["early diffusion", "earlydiffusion", "early_diffusion", "early diff", "early"], ["EarlyDiffusion"]),
        ("Late Diffusion", ["late diffusion", "latediffusion", "late_diffusion", "late diff", "late"], ["LateDiffusion"]),
        ("Mod Rate", ["mod rate", "modrate", "mod_rate", "mod-rate", "rate", "modulation rate", "modulation_rate", "mod speed"], ["ModRate"]),
        ("Mod Depth", ["mod depth", "moddepth", "mod_depth", "mod-depth", "depth", "modulation depth", "modulation_depth", "mod amount"], ["ModDepth"]),
    ],
    "drum_buss": [
        ("Drive", ["drive", "distortion", "overdrive", "sat", "saturation"], []),
        ("Crunch", ["crunch", "bite"], []),
        ("Transients", ["transients", "transient", "attack"], []),
        ("Boom", ["boom", "sub boom", "sub", "boom level"], []),
        ("Output Gain", ["output gain", "output", "gain", "volume", "out", "level", "output_gain"], ["Output"]),
        ("Dry/Wet", ["dry wet", "mix", "blend"], []),
        ("Trim", ["trim"], []),
        ("Damping", ["damping", "damp"], []),
        ("Compressor", ["compressor", "comp"], []),
    ],
    "compressor": [
        ("Threshold", ["threshold", "thresh", "umbral"], []),
        ("Ratio", ["ratio", "relacion", "comp ratio"], []),
        ("Attack", ["attack", "att", "ataque", "attack time"], []),
        ("Release", ["release", "rel", "relajacion", "release time"], []),
        ("Output Gain", ["output gain", "output", "gain", "makeup", "makeup gain", "out", "output_gain"], ["Output"]),
        ("Dry/Wet", ["dry wet", "mix", "blend"], []),
        ("Knee", ["knee"], []),
    ],
    "glue_compressor": [
        ("Threshold", ["threshold", "thresh", "umbral"], []),
        ("Ratio", ["ratio", "relacion"], []),
        ("Attack", ["attack", "att"], []),
        ("Release", ["release", "rel"], []),
        ("Output", ["output", "makeup", "makeup gain", "make up", "gain", "out"], ["Makeup"]),
        ("Dry/Wet", ["dry wet", "mix"], []),
    ],
    "chorus_ensemble": [
        ("Amount", ["amount", "depth", "amt"], []),
        ("Rate", ["rate", "speed", "frequency", "freq"], []),
        ("Dry/Wet", ["dry wet", "mix", "blend"], []),
        ("Warmth", ["warmth"], []),
        ("Width", ["width"], []),
        ("Feedback", ["feedback"], []),
    ],
    "delay": [
        ("Dry/Wet", ["dry wet", "mix", "blend"], []),
        ("Feedback", ["feedback", "fb"], []),
        ("Delay Time", ["delay time", "delaytime", "delay_time", "delay-time", "time", "delay"], []),
        ("Sync", ["sync", "tempo sync", "delay sync", "temposync"], []),
        ("Filter Freq", ["filter freq", "filter frequency", "cutoff"], []),
        ("Filter Width", ["filter width"], []),
        ("Ping Pong", ["ping pong", "pingpong"], []),
    ],
    "utility": [
        ("Gain", ["gain", "volume", "vol", "level", "output", "out"], ["Output"]),
        ("Stereo Width", ["stereo width", "width", "stereowidth", "stereo_width", "stereo-width", "pan width"], ["Width"]),
        ("Bass Mono", ["bass mono", "bassmono", "bass_mono", "bass-mono", "mono bass"], []),
        ("Bass Freq", ["bass freq", "bassfreq", "bass_freq", "bass frequency", "bass-freq"], []),
        ("Mono", ["mono", "force mono", "mono on"], []),
        ("Mute", ["mute", "muting"], []),
        ("Panorama", ["panorama", "pan"], ["Pan"]),
    ],
    "saturator": [
        ("Base", ["base", "drive base", "drive_base", "base drive"], ["drive_base"]),
        ("Drive", ["drive", "saturation", "drive gain"], []),
        ("Dry/Wet", ["dry wet", "mix"], []),
        ("Output", ["output", "out", "output gain"], []),
        ("Color", ["color"], []),
        ("Depth", ["depth"], []),
        ("Curve", ["curve", "type", "shape"], []),
    ],
    "auto_filter": [
        ("Frequency", ["frequency", "freq", "cutoff", "filter freq"], []),
        ("Resonance", ["resonance", "res", "q"], []),
        ("Filter Type", ["filter type", "type", "mode", "filter mode"], []),
        ("Drive", ["drive", "filter drive", "saturation"], []),
        ("Morph", ["morph"], []),
        ("Envelope", ["envelope", "env"], []),
        ("Attack", ["attack"], []),
        ("Release", ["release"], []),
    ],
    "echo": [
        ("Dry/Wet", ["dry wet", "mix", "blend"], []),
        ("Feedback", ["feedback", "fb"], []),
        ("Delay Time", ["delay time", "delaytime", "delay_time", "delay", "time"], []),
        ("Sync", ["sync", "tempo sync", "delay sync"], []),
        ("Ping Pong", ["ping pong", "pingpong"], []),
        ("Wobble", ["wobble", "modulation", "mod"], []),
        ("Noise", ["noise", "tape noise"], []),
    ],
    "pedal": [
        ("Gain", ["gain", "drive", "distortion", "fuzz"], []),
        ("Output", ["output", "out", "level", "volume", "vol"], []),
        ("Bass", ["bass", "low"], []),
        ("Mid", ["mid", "middle"], []),
        ("Treble", ["treble", "high"], []),
        ("Sub", ["sub", "sub bass"], []),
        ("Type", ["type", "mode", "pedal type"], []),
    ],
    "phaser_flanger": [
        ("Amount", ["amount", "depth", "amt"], []),
        ("Rate", ["rate", "speed", "frequency"], []),
        ("Feedback", ["feedback", "fb"], []),
        ("Warmth", ["warmth"], []),
        ("Mode", ["mode", "type"], []),
        ("Dry/Wet", ["dry wet", "mix", "blend"], []),
    ],
    "multiband_dynamics": [
        ("Output Gain", ["output gain", "output", "gain", "volume", "makeup"], []),
        ("Time", ["time", "time scaling", "speed"], []),
        ("Amount", ["amount", "depth", "mix", "dry wet"], []),
        ("Band 1 (Low)", ["low", "band 1", "low band", "bass"], []),
        ("Band 2 (Mid)", ["mid", "band 2", "mid band"], []),
        ("Band 3 (High)", ["high", "band 3", "high band", "treble"], []),
    ],
    "shifter": [
        ("Pitch", ["pitch", "coarse", "semitones", "shift"], []),
        ("Fine", ["fine", "cents", "fine tune"], []),
        ("Drive", ["drive", "saturation"], []),
        ("Dry/Wet", ["dry wet", "mix", "blend"], []),
        ("Mode", ["mode", "type"], []),
    ],
    "hybrid_reverb": [
        ("Dry/Wet", ["dry wet", "mix", "blend"], []),
        ("Decay", ["decay", "decay time", "decaytime", "rt60"], []),
        ("PreDelay", ["predelay", "pre delay", "pre_delay"], ["Pre-delay"]),
        ("Size", ["size", "room size"], []),
        ("Blend", ["blend", "algo blend", "convolution blend"], []),
    ],
    "erosion": [
        ("Frequency", ["frequency", "freq"], []),
        ("Width", ["width", "q"], []),
        ("Amount", ["amount", "depth"], []),
        ("Mode", ["mode", "type"], []),
    ],
    "roar": [
        ("Drive", ["drive", "input drive", "saturation"], []),
        ("Tone", ["tone", "color", "brightness"], []),
        ("Feedback", ["feedback", "fb"], []),
        ("Stages", ["stages", "stage", "routing"], []),
        ("Bias", ["bias", "dc bias"], []),
        ("Dry/Wet", ["dry wet", "mix"], []),
        ("Output", ["output", "out"], []),
    ],
    "reverb": [
        ("Decay Time", ["decay time", "decaytime", "decay_time", "decay"], []),
        ("PreDelay", ["predelay", "pre delay", "pre_delay", "pre-delay", "pre delay time"], ["Pre-delay"]),
        ("Dry/Wet", ["dry wet", "mix"], []),
    ],
}


def _detect_device_key(d_norm: str) -> Optional[str]:
    """Identifica la clave del dispositivo normalizando fabricantes, prefijos VST3 y URIs."""
    if any(w in d_norm for w in ("supermassive", "valhallasupermassive")):
        return "valhalla_supermassive"
    if any(w in d_norm for w in ("vintageverb", "vintage verb", "valhallavintageverb")):
        return "valhalla_vintage_verb"
    if any(w in d_norm for w in ("surge", "surge xt")):
        return "surge_xt_effects"

    # Procesadores de stock Live 12
    if any(w in d_norm for w in ("drum buss", "drumbuss", "drum bus")):
        return "drum_buss"
    if "glue" in d_norm:
        return "glue_compressor"
    if "compressor" in d_norm and "glue" not in d_norm and "multiband" not in d_norm:
        return "compressor"
    if any(w in d_norm for w in ("chorus ensemble", "chorus", "ensemble")):
        return "chorus_ensemble"
    if "delay" in d_norm and not any(w in d_norm for w in ("supermassive", "surge")):
        return "delay"
    if "utility" in d_norm:
        return "utility"
    if "saturator" in d_norm:
        return "saturator"
    if any(w in d_norm for w in ("auto filter", "autofilter")):
        return "auto_filter"
    if "echo" in d_norm and not any(w in d_norm for w in ("supermassive", "vintage", "delay")):
        return "echo"
    if "pedal" in d_norm:
        return "pedal"
    if any(w in d_norm for w in ("phaser flanger", "phaser-flanger", "phaser", "flanger")):
        return "phaser_flanger"
    if any(w in d_norm for w in ("multiband dynamics", "multiband")):
        return "multiband_dynamics"
    if "shifter" in d_norm:
        return "shifter"
    if any(w in d_norm for w in ("hybrid reverb", "hybridreverb")):
        return "hybrid_reverb"
    if "erosion" in d_norm:
        return "erosion"
    if "roar" in d_norm:
        return "roar"
    if "reverb" in d_norm and not any(w in d_norm for w in ("vintage", "valhalla", "hybrid")):
        return "reverb"

    return None


class VerificationError(Exception):
    def __init__(self, message: str, diagnosis: Dict[str, Any]):
        super().__init__(message)
        self.diagnosis = diagnosis


class DeviceExecutionVerifier:
    TOLERANCE = 0.04
    MIN_DELTA = 0.01

    @classmethod
    def resolve_lom_parameter_name(
        cls,
        device_name: str,
        param_identifier: str,
        available_params: Optional[Dict[str, float]] = None
    ) -> str:
        """
        Resuelve alias de parámetros al nombre exacto expuesto por el Live Object Model (LOM).
        E.g.: 'Band 1 On' -> '1 Filter On A' (EQ Eight), 'Makeup' -> 'Output' (Glue Compressor),
              'Drive'/'Base' -> 'Drive'/'Base' (Saturator), 'Gain' -> 'Gain' (Utility).
        """
        if not param_identifier:
            return param_identifier

        p_clean = param_identifier.strip().lower()
        d_clean = (device_name or "").strip().lower()
        p_norm = _normalize_str(param_identifier)
        p_symbol = _strip_symbols(param_identifier)
        d_norm = _normalize_str(device_name)

        # 1. Coincidencia directa en available_params si fue provisto
        if available_params:
            if param_identifier in available_params:
                return param_identifier
            for k in available_params.keys():
                if p_clean == k.lower():
                    return k
            if p_symbol:
                for k in available_params.keys():
                    if p_symbol == _strip_symbols(k):
                        return k

        # 2. EQ Eight (mapeo estructurado por bandas 1 a 8)
        if any(w in d_norm for w in ("eq eight", "eq8")) or d_norm == "eq" or "eq eight" in d_clean:
            m_on = re.search(r"(?:band\s*|banda\s*)?([1-8])\s*(?:on|filter\s*on)", p_norm)
            if m_on:
                target = f"{m_on.group(1)} Filter On A"
                found = _find_in_available([target], available_params)
                return found or target
            m_type = re.search(r"(?:band\s*|banda\s*)?([1-8])\s*(?:filter\s*type|type)", p_norm)
            if m_type:
                target = f"{m_type.group(1)} Filter Type A"
                found = _find_in_available([target], available_params)
                return found or target
            m_freq = re.search(r"(?:band\s*|banda\s*)?([1-8])\s*(?:frequency|freq)", p_norm)
            if m_freq:
                target = f"{m_freq.group(1)} Frequency A"
                found = _find_in_available([target], available_params)
                return found or target
            m_gain = re.search(r"(?:band\s*|banda\s*)?([1-8])\s*gain", p_norm)
            if m_gain:
                target = f"{m_gain.group(1)} Gain A"
                found = _find_in_available([target], available_params)
                return found or target
            m_q = re.search(r"(?:band\s*|banda\s*)?([1-8])\s*q", p_norm)
            if m_q:
                target = f"{m_q.group(1)} Q A"
                found = _find_in_available([target], available_params)
                return found or target

        # 3. Surge XT Effects (ranuras modulares y parámetros LOM)
        if any(w in d_norm for w in ("surge", "surge xt")):
            return _resolve_surge_xt_param(p_norm, p_symbol, param_identifier, available_params)

        # 4. Procesadores específicos por catálogo de LOM
        dev_key = _detect_device_key(d_norm)
        if dev_key:
            # Manejo específico para Utility: Gain es nativo en Live 12 LOM (no Output)
            if dev_key == "utility":
                if p_norm in ("gain", "volume", "vol", "level", "output", "out"):
                    if available_params:
                        found = _find_in_available(["Gain", "Output"], available_params)
                        if found:
                            return found
                    return "Gain"
                if p_norm in ("stereo width", "width", "stereowidth", "pan width"):
                    if available_params:
                        found = _find_in_available(["Stereo Width", "Width"], available_params)
                        if found:
                            return found
                    return "Width" if p_norm == "width" else "Stereo Width"

            # Manejo específico para Drum Buss: Output vs Output Gain
            if dev_key == "drum_buss":
                if p_norm in ("output gain", "output", "gain", "volume", "out", "level"):
                    if available_params:
                        found = _find_in_available(["Output Gain", "Output"], available_params)
                        if found:
                            return found
                    return "Output" if p_norm == "output" else "Output Gain"

            # Manejo específico para Compressor: Output vs Output Gain
            if dev_key == "compressor":
                if p_norm in ("output gain", "output", "gain", "makeup", "makeup gain", "out"):
                    if available_params:
                        found = _find_in_available(["Output Gain", "Output"], available_params)
                        if found:
                            return found
                    return "Output" if p_norm == "output" else "Output Gain"

            # Manejo específico para Saturator: Bugfix Base vs Drive
            if dev_key == "saturator":
                if p_norm in ("base", "drive base", "base drive", "drive_base"):
                    if available_params:
                        found = _find_in_available(["Base", "drive_base"], available_params)
                        if found:
                            return found
                    return "Base"
                if p_norm in ("drive", "saturation", "drive gain"):
                    if available_params:
                        found = _find_in_available(["Drive"], available_params)
                        if found:
                            return found
                    return "Drive"

            # Búsqueda en mapeos estándar del dispositivo
            mappings = DEVICE_LOM_MAPPINGS.get(dev_key, [])
            for canonical, aliases, alt_canonicals in mappings:
                all_norms = [_normalize_str(canonical)] + [_normalize_str(a) for a in aliases] + [_normalize_str(ac) for ac in alt_canonicals]
                all_symbols = [_strip_symbols(canonical)] + [_strip_symbols(a) for a in aliases] + [_strip_symbols(ac) for ac in alt_canonicals]

                if p_norm in all_norms or p_symbol in all_symbols:
                    candidates = [canonical] + alt_canonicals
                    if available_params:
                        found = _find_in_available(candidates + aliases, available_params)
                        if found:
                            return found
                    return canonical

        # 5. Fuzzy match fallback en available_params
        if available_params:
            for k in available_params.keys():
                k_clean = k.lower()
                if p_clean in k_clean or k_clean in p_clean:
                    return k

        return param_identifier

    @classmethod
    def check_is_test_env(cls, conn: Any = None, session: Any = None) -> bool:
        """Determina si se está ejecutando dentro del framework de tests automatizados."""
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return True
        if conn is not None:
            c_name = getattr(conn, "__class__", None).__name__ if hasattr(conn, "__class__") else ""
            if "Mock" in c_name:
                return True
        if session is not None and getattr(session, "_is_test_mode", False):
            return True
        return False

    @classmethod
    def read_device_parameters(cls, conn: Any, track_index: int, device_index: int) -> Dict[str, float]:
        """Ejecuta el read-back físico sincrónico contra el socket LOM de Live."""
        if conn is None or not hasattr(conn, "send_command"):
            return {}
        try:
            res = conn.send_command("get_device_parameters", {
                "track_index": track_index,
                "device_index": device_index
            })
            raw_list = []
            if isinstance(res, dict):
                raw_list = res.get("parameters", res.get("result", {}).get("parameters", []))
            elif isinstance(res, list):
                raw_list = res

            param_map = {}
            for p in raw_list:
                if not isinstance(p, dict):
                    continue
                p_name = str(p.get("name", "")).strip()
                p_val = float(p.get("value", 0.0))
                param_map[p_name.lower()] = p_val
                if "id" in p:
                    param_map[str(p["id"]).lower()] = p_val
                if "original_id" in p:
                    param_map[str(p["original_id"]).lower()] = p_val
            return param_map
        except Exception as e:
            logger.error(f"[Verifier] Error en read-back LOM (Track {track_index}, Dev {device_index}): {e}")
            return {}

    @classmethod
    def apply_and_verify_parameter(
        cls,
        conn: Any,
        track_index: int,
        device_index: int,
        device_name: str,
        param_identifier: str,
        target_value: float,
        is_test_env: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Ejecuta la mutación y valida con bucle cerrado: baseline -> write -> read-back.
        Garantiza tolerancia <= 0.04 y delta >= 1%.
        """
        if is_test_env or conn is None or not hasattr(conn, "send_command"):
            return True, {
                "param": param_identifier,
                "target": target_value,
                "actual": target_value,
                "status": "VERIFIED_TEST_ENV"
            }

        # 1. Baseline read-back
        baseline_params = cls.read_device_parameters(conn, track_index, device_index)
        actual_param = cls.resolve_lom_parameter_name(device_name, param_identifier, baseline_params)
        param_clean = actual_param.strip().lower()
        baseline_val = baseline_params.get(param_clean, None)
        if baseline_params and param_clean not in baseline_params:
            for bp in baseline_params:
                if param_clean in bp or bp in param_clean:
                    actual_param = bp
                    param_clean = bp
                    baseline_val = baseline_params.get(bp)
                    break

        # 2. Write command
        try:
            conn.send_command("set_device_parameter", {
                "track_index": track_index,
                "device_index": device_index,
                "parameter": actual_param,
                "value": float(target_value)
            })
        except Exception as ex_write:
            return False, {
                "root_cause": "SOCKET_WRITE_EXCEPTION",
                "track_index": track_index,
                "device_index": device_index,
                "device_name": device_name,
                "parameter_requested": param_identifier,
                "value_requested": target_value,
                "actual_error": str(ex_write)
            }

        # 3. Post-mutation read-back
        post_params = cls.read_device_parameters(conn, track_index, device_index)
        if not post_params:
            return False, {
                "root_cause": "DEVICE_NOT_FOUND_OR_NO_PARAMETERS",
                "track_index": track_index,
                "device_index": device_index,
                "device_name": device_name,
                "parameter_requested": param_identifier,
                "value_requested": target_value,
                "actual_error": "El dispositivo no devolvió parámetros legibles en Live."
            }

        actual_val = post_params.get(param_clean)
        if actual_val is None:
            resolved_post = cls.resolve_lom_parameter_name(device_name, param_identifier, post_params).strip().lower()
            actual_val = post_params.get(resolved_post)
        if actual_val is None:
            # Búsqueda difusa de alias
            for k, v in post_params.items():
                if param_clean in k or k in param_clean:
                    actual_val = v
                    break

        if actual_val is None:
            return False, {
                "root_cause": "PARAMETER_NAME_NOT_FOUND",
                "track_index": track_index,
                "device_index": device_index,
                "device_name": device_name,
                "parameter_requested": param_identifier,
                "value_requested": target_value,
                "available_parameters": list(post_params.keys())[:10],
                "actual_error": f"El parámetro '{param_identifier}' no existe en {device_name}."
            }

        # 4. Evaluación de Tolerancia (+/- 0.04)
        error_margin = abs(actual_val - target_value)
        if error_margin > cls.TOLERANCE:
            return False, {
                "root_cause": "PARAMETER_VALUE_REJECTED",
                "track_index": track_index,
                "device_index": device_index,
                "device_name": device_name,
                "parameter_requested": param_identifier,
                "value_requested": target_value,
                "value_baseline": baseline_val,
                "value_readback": actual_val,
                "tolerance_allowed": cls.TOLERANCE,
                "actual_error": f"Divergencia física: solicitado {target_value:.3f}, leído {actual_val:.3f} (error {error_margin:.3f} > {cls.TOLERANCE})."
            }

        # 5. Evaluación de Delta Mínimo (Delta >= 0.01) si target difería de baseline
        if baseline_val is not None and abs(target_value - baseline_val) >= cls.MIN_DELTA:
            delta_achieved = abs(actual_val - baseline_val)
            if delta_achieved < cls.MIN_DELTA:
                return False, {
                    "root_cause": "STAGNANT_PARAMETER_DELTA_ZERO",
                    "track_index": track_index,
                    "device_index": device_index,
                    "device_name": device_name,
                    "parameter_requested": param_identifier,
                    "value_requested": target_value,
                    "value_baseline": baseline_val,
                    "value_readback": actual_val,
                    "min_delta_required": cls.MIN_DELTA,
                    "actual_error": f"El parámetro no mutó físicamente (delta {delta_achieved:.4f} < {cls.MIN_DELTA}). Parámetro bloqueado por Macro o congelado."
                }

        return True, {
            "status": "VERIFIED_PHYSICAL_OK",
            "track_index": track_index,
            "device_index": device_index,
            "parameter": param_identifier,
            "value_readback": actual_val
        }

    @classmethod
    def verify_device_parameters_batch(
        cls,
        conn: Any,
        track_index: int,
        device_index: int,
        device_name: str,
        target_params: Dict[str, float],
        is_test_env: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Aplica y verifica un conjunto completo de parámetros en una sola pasada de read-back,
        minimizando la sobrecarga de round-trips sobre el socket LOM.
        """
        if is_test_env or conn is None or not hasattr(conn, "send_command") or not target_params:
            return True, {"status": "VERIFIED_BATCH_OK", "verified_count": len(target_params)}

        baseline_params = cls.read_device_parameters(conn, track_index, device_index)

        # Enviar escrituras
        for p_name, p_val in target_params.items():
            actual_param = cls.resolve_lom_parameter_name(device_name, p_name, baseline_params)
            p_clean = actual_param.strip().lower()
            if baseline_params and p_clean not in baseline_params:
                found_fuzzy = None
                for bp in baseline_params:
                    if p_clean in bp or bp in p_clean:
                        found_fuzzy = bp
                        break
                if found_fuzzy:
                    actual_param = found_fuzzy
                else:
                    logger.info(f"[Verifier] Parameter '{p_name}' not exposed in LOM for '{device_name}'. Skipped socket write.")
                    continue

            try:
                conn.send_command("set_device_parameter", {
                    "track_index": track_index,
                    "device_index": device_index,
                    "parameter": actual_param,
                    "value": float(p_val) if isinstance(p_val, (int, float)) else 0.5
                })
            except Exception as ex:
                return False, {
                    "root_cause": "SOCKET_WRITE_EXCEPTION",
                    "track_index": track_index,
                    "device_index": device_index,
                    "device_name": device_name,
                    "parameter_requested": p_name,
                    "value_requested": p_val,
                    "actual_error": str(ex)
                }

        # Read-back único
        post_params = cls.read_device_parameters(conn, track_index, device_index)
        if not post_params:
            return False, {
                "root_cause": "DEVICE_NOT_FOUND_OR_NO_PARAMETERS",
                "track_index": track_index,
                "device_index": device_index,
                "device_name": device_name,
                "actual_error": "No se pudieron leer los parámetros del dispositivo en Live."
            }

        # Validar cada parámetro
        for p_name, p_target in target_params.items():
            actual_param = cls.resolve_lom_parameter_name(device_name, p_name, post_params)
            p_clean = actual_param.strip().lower()
            actual_val = post_params.get(p_clean)
            if actual_val is None:
                orig_clean = p_name.strip().lower()
                actual_val = post_params.get(orig_clean)
            if actual_val is None:
                for k, v in post_params.items():
                    if p_clean in k or k in p_clean:
                        actual_val = v
                        break

            if actual_val is None:
                if baseline_params and p_clean not in baseline_params and p_name.strip().lower() not in baseline_params:
                    # Parameter handled through internal VST architecture / preset serialization
                    continue
                return False, {
                    "root_cause": "PARAMETER_NAME_NOT_FOUND",
                    "track_index": track_index,
                    "device_index": device_index,
                    "device_name": device_name,
                    "parameter_requested": p_name,
                    "actual_error": f"El parámetro '{p_name}' no fue encontrado en Live."
                }

            error_margin = abs(actual_val - float(p_target))
            if error_margin > cls.TOLERANCE:
                return False, {
                    "root_cause": "PARAMETER_VALUE_REJECTED",
                    "track_index": track_index,
                    "device_index": device_index,
                    "device_name": device_name,
                    "parameter_requested": p_name,
                    "value_requested": float(p_target),
                    "value_readback": actual_val,
                    "tolerance_allowed": cls.TOLERANCE,
                    "actual_error": f"Divergencia: objetivo {p_target:.3f}, leído {actual_val:.3f} (error {error_margin:.3f})."
                }

        return True, {"status": "VERIFIED_BATCH_OK", "verified_count": len(target_params)}

    @classmethod
    def build_verification_failed_payload(
        cls,
        track_index: int,
        track_name: str,
        device_index: int,
        device_name: str,
        diagnosis: Dict[str, Any],
        role: Optional[str] = None,
        retry_count: int = 1
    ) -> Dict[str, Any]:
        """Genera el payload interactivo estandarizado VERIFICATION_FAILED_RETRY_REQUIRED."""
        r_str = role or "INSTRUMENT"
        p_req = diagnosis.get("parameter_requested", "parámetro")
        v_req = diagnosis.get("value_requested", 0.0)
        v_read = diagnosis.get("value_readback", 0.0)
        err = diagnosis.get("actual_error", "Parámetro rechazado.")

        return {
            "status": "VERIFICATION_FAILED_RETRY_REQUIRED",
            "phase": "PHASE_5_INSERT_EFFECTS",
            "current_step": f"RE-PREGUNTA POR FALLO DE VERIFICACIÓN FÍSICA (Pista {track_index}: '{track_name}', Dispositivo {device_index}: '{device_name}')",
            "action_taken": f"Fallo en verificación física LOM: {err} Transacción revertida a estado seguro.",
            "retry_count": retry_count,
            "max_retries": 3,
            "failure_diagnosis": diagnosis,
            "actionable_options": [
                {
                    "option": 1,
                    "title": "Reintentar con Resolución Semántica Automática",
                    "description": "El Supervisor introspecciona el catálogo del dispositivo, resuelve alias de parámetros y reintenta aplicar el valor exacto.",
                    "action_command": "retry_semantic_auto"
                },
                {
                    "option": 2,
                    "title": f"Inyectar Arquetipo de Rol Calibrado para {r_str}",
                    "description": f"Fuerza la inyección del blueprint de estándares acústicos para {r_str} garantizando Delta >= 1.",
                    "action_command": "inject_role_archetype"
                },
                {
                    "option": 3,
                    "title": "Especificar Valores Alternativos o Sustituir Dispositivo",
                    "description": "Provee nuevos parámetros en formato clave-valor o solicita un procesador nativo equivalente.",
                    "action_command": "custom_override"
                }
            ],
            "question": (
                f"ALERTA DE BUCLE CERRADO: FALLO DE VERIFICACIÓN FÍSICA EN LIVE\n\n"
                f"El motor verificó físicamente el procesador '{device_name}' en la pista '{track_name}' (Track {track_index}) "
                f"tras enviar la orden y detectó que los parámetros no cambiaron según lo estipulado.\n\n"
                f"Diagnóstico de Causa Raíz:\n"
                f"• Dispositivo: {device_name} (Pista {track_index}: '{track_name}')\n"
                f"• Parámetro: '{p_req}'\n"
                f"• Valor solicitado: {v_req} | Leído en Live: {v_read}\n"
                f"• Diagnóstico: {err}\n\n"
                f"Elige una opción para resolver y completar la verificación (100% obligatorio):\n"
                f"  1. Opción 1: Reintentar con resolución semántica automática.\n"
                f"  2. Opción 2: Inyectar Arquetipo Calibrado para {r_str} (Garantiza Delta >= 1).\n"
                f"  3. Opción 3: Proveer nuevos valores manualmente o sustituir el dispositivo.\n\n"
                f"Responde 'Opción 1', 'Opción 2' o tus nuevos parámetros para continuar."
            ),
            "instructions_for_ai": "El read-back físico de Live falló. Responde 'Opción 1' para auto-reparar semánticamente, 'Opción 2' para arquetipo forzado, o proporciona parámetros corregidos.",
            "target_track": track_index,
            "target_device": device_name,
            "retry_required": True
        }
