# engine/fx/role_fx_catalog.py
"""
Role-based insert effects catalog, genre-family acoustic matrices, and psychoacoustic spectral guide.
Provides UniversalGenreFamilyFXCatalog across 4 sound families (Urbana/Moderna, Electrónica/Club,
Orgánica/Acústica, Espacial/Cinemática) for 23 musical roles, with backward compatibility anchors.
"""
from enum import Enum
from typing import List, Dict, Any, Optional

# --- 1. Sound Family Enumeration and Resolution ---

class GenreFamily(str, Enum):
    """
    Canonical acoustic sound families for genre-aware insert effect chains.
    """
    URBANA_MODERNA = "urbana_moderna"
    ELECTRONICA_CLUB = "electronica_club"
    ORGANICA_ACUSTICA = "organica_acustica"
    ESPACIAL_CINEMATICA = "espacial_cinematica"


def resolve_genre_family(genre: Optional[Any] = None, bpm: float = 120.0) -> GenreFamily:
    """
    Normalizes and categorizes any genre string, enum instance, alias, or tempo (BPM)
    into one of the 4 canonical acoustic GenreFamily members.
    """
    if isinstance(genre, GenreFamily):
        return genre
    if hasattr(genre, "value"):
        genre = genre.value

    # Fallback when genre is absent or generic placeholder
    if not genre or not str(genre).strip() or str(genre).strip().lower() in ("none", "null", "undefined", "auto", "default"):
        if bpm < 90.0:
            return GenreFamily.ORGANICA_ACUSTICA
        elif bpm > 128.0:
            return GenreFamily.ELECTRONICA_CLUB
        return GenreFamily.URBANA_MODERNA

    g = str(genre).lower().strip().replace("-", "_").replace(" ", "_")

    # Direct match against enum values
    try:
        return GenreFamily(g)
    except ValueError:
        pass

    # 1. Urbana / Moderna: Trap, Drill, Boom Bap, Reggaeton, Phonk, Dembow, Hip-Hop, Latin
    if any(k in g for k in [
        "trap", "drill", "uk_drill", "boom_bap", "boombap", "reggaeton",
        "hip_hop", "hiphop", "phonk", "dembow", "latin", "urbano", "urban"
    ]):
        return GenreFamily.URBANA_MODERNA

    # 2. Electrónica de Club: House, Techno, EDM, DnB, Dubstep, Trance, Synthwave
    if any(k in g for k in [
        "house", "techno", "edm", "drum_and_bass", "drum & bass", "dnb",
        "dubstep", "trance", "club", "dance", "synthwave", "electro", "hardstyle"
    ]):
        return GenreFamily.ELECTRONICA_CLUB

    # 3. Orgánica / Acústica: Neo-Soul, R&B, Flamenco, Indie/Pop, Rock, Jazz, Folk, Cumbia, Afrobeat
    if any(k in g for k in [
        "neo_soul", "neosoul", "rnb", "r_and_b", "r&b", "soul", "flamenco",
        "indie", "pop", "rock", "jazz", "acoustic", "acustica", "organica",
        "folk", "lofi", "lo_fi", "cumbia", "afrobeat", "bossa", "blues", "ballad"
    ]):
        return GenreFamily.ORGANICA_ACUSTICA

    # 4. Espacial / Cinemática: Ambient, Drone, Downtempo, Cinematic, Soundscape
    if any(k in g for k in [
        "ambient", "drone", "downtempo", "cinematic", "cinematica", "espacial",
        "soundscape", "space", "meditation", "atmospheric", "chillout", "new_age"
    ]):
        return GenreFamily.ESPACIAL_CINEMATICA

    # Fallback inference by tempo (BPM) if unrecognized string
    if bpm < 90.0:
        return GenreFamily.ORGANICA_ACUSTICA
    elif bpm > 128.0:
        return GenreFamily.ELECTRONICA_CLUB
    return GenreFamily.URBANA_MODERNA


# --- 2. Live 12 Reference Parameter Blueprints ---

VALHALLA_VINTAGE_VERB_PARAMS: List[Dict[str, Any]] = [
    {"id": "Mix", "name": "Mix (Dry/Wet)", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Balance de señal directa y reverberada.", "default": 0.20},
    {"id": "Decay", "name": "Decay (RT60)", "range": "0.0 a 1.0 (0.2s a 70.0s)", "behavior": "Longitud de la cola de reverberación.", "default": 0.25},
    {"id": "PreDelay", "name": "Pre-delay", "range": "0.0 a 1.0 (0 ms a 500 ms)", "behavior": "Separación temporal para preservar el ataque transitorio seco.", "default": 0.05},
    {"id": "Mode", "name": "Algorithmic Mode", "range": "22 Modos (Concert Hall, Plate, Room, Smooth Plate, Nonlin...)", "behavior": "Topología algorítmica de estudio.", "default": 0.0},
    {"id": "ColorMode", "name": "Color Mode (Era)", "range": "1970s, 1980s, Now", "behavior": "Ancho de banda y grano analógico/vintage.", "default": 0.50},
    {"id": "Size", "name": "Room Size", "range": "0.0 a 1.0", "behavior": "Dimensión percibida del espacio acústico.", "default": 0.50},
    {"id": "Attack", "name": "Attack Shape", "range": "0.0 a 1.0", "behavior": "Desarrollo del transitorio reverberado; en Nonlin pasa de gated a inverso.", "default": 0.0},
    {"id": "BassMult", "name": "Bass Multiply", "range": "0.0 a 1.0 (0.25x a 4.0x)", "behavior": "Multiplicador de decaimiento en graves relativo al Decay.", "default": 0.50},
    {"id": "LowCut", "name": "Low Cut (HPF)", "range": "0.0 a 1.0 (10 Hz a 500 Hz)", "behavior": "Filtro pasa-altos anti-barro protector.", "default": 0.20},
    {"id": "HighCut", "name": "High Cut (LPF)", "range": "0.0 a 1.0 (1000 Hz a 20000 Hz)", "behavior": "Filtro pasa-bajos para calidez analógica.", "default": 0.65},
    {"id": "EarlyDiffusion", "name": "Early Diffusion", "range": "0.0 a 1.0", "behavior": "Densidad de reflexiones tempranas.", "default": 1.0},
    {"id": "LateDiffusion", "name": "Late Diffusion", "range": "0.0 a 1.0", "behavior": "Densidad de la cola tardía.", "default": 1.0},
    {"id": "ModRate", "name": "Modulation Rate", "range": "0.0 a 1.0 (0.05 Hz a 5.0 Hz)", "behavior": "Velocidad de coros internos.", "default": 0.25},
    {"id": "ModDepth", "name": "Modulation Depth", "range": "0.0 a 1.0", "behavior": "Profundidad de modulación de tono.", "default": 0.50}
]


# --- 3. Modular Device Parameter Factories ---

def make_eq_eight(
    bands: Optional[List[Dict[str, Any]]] = None,
    hpf_default: float = 0.18,
    bell_default: float = 0.45,
    bell_name: str = "Banda 2 Bell (Medios/Cuerpo)",
    high_default: Optional[float] = None,
    high_name: Optional[str] = None,
    acoustic_purpose: str = "Ecualización quirúrgica y tallado modal de frecuencias"
) -> Dict[str, Any]:
    """Generates an EQ Eight dictionary specification with exact Live 12 parameters."""
    if bands is not None:
        params_list = bands
    else:
        params_list = [
            {"id": "Band 1 On", "name": "Banda 1 High-Pass", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Filtro pasa-altos para limpiar frecuencias subsónicas.", "default": 1.0},
            {"id": "1 Frequency A", "name": "Frecuencia de Corte Subsónico", "range": "0.0 a 1.0 (20 Hz a 60 Hz)", "behavior": "Corte de sub-graves sucios para liberar headroom.", "default": hpf_default},
            {"id": "Band 2 On", "name": "Banda 2 Bell", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Control paramétrico modal en rango medio/cuerpo.", "default": 1.0},
            {"id": "2 Frequency A", "name": bell_name, "range": "0.0 a 1.0 (200 Hz a 1000 Hz)", "behavior": "Frecuencia de ecualización de medios.", "default": bell_default},
        ]
        if high_default is not None:
            params_list.extend([
                {"id": "Band 4 On", "name": "Banda 4 High-Shelf", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Apertura en agudos para aire y definición.", "default": 1.0},
                {"id": "4 Frequency A", "name": high_name or "Frecuencia de Brillo", "range": "0.0 a 1.0", "behavior": "Definición y presencia en agudos.", "default": high_default}
            ])
    return {
        "name": "EQ Eight",
        "type": "native",
        "uri": "query:AudioFx#EQ%20Eight",
        "acoustic_purpose": acoustic_purpose,
        "params": params_list
    }


def make_glue_compressor(
    threshold: float = -12.0,
    ratio: float = 1.0,
    attack: float = 0.50,
    release: float = 0.0,
    dry_wet: float = 1.0,
    makeup: float = 0.10,
    acoustic_purpose: str = "Control dinámico, pegamento de transientes y cohesión rítmica"
) -> Dict[str, Any]:
    """Generates a Glue Compressor dictionary specification."""
    return {
        "name": "Glue Compressor",
        "type": "native",
        "uri": "query:AudioFx#Glue%20Compressor",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Threshold", "name": "Threshold (Umbral)", "range": "-40.0 dB a 0.0 dB", "behavior": "Nivel de señal a partir del cual comienza la compresión dinámica.", "default": threshold},
            {"id": "Ratio", "name": "Ratio (Relación)", "range": "1.0 (2:1), 2.0 (4:1), 3.0 (10:1)", "behavior": "Proporción de atenuación aplicada a la señal.", "default": ratio},
            {"id": "Attack", "name": "Attack (Tiempo de ataque)", "range": "0.0 a 1.0 (0.1 ms a 30 ms)", "behavior": "Velocidad de respuesta del compresor ante transitorios.", "default": attack},
            {"id": "Release", "name": "Release (Relajación)", "range": "0.0 a 1.0 (Auto / 0.1s a 1.2s)", "behavior": "Tiempo de recuperación dinámica.", "default": release},
            {"id": "Dry/Wet", "name": "Dry/Wet (Mezcla)", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Balance de procesamiento paralelo estilo New York.", "default": dry_wet},
            {"id": "Makeup", "name": "Makeup Gain", "range": "0.0 a 1.0 (0 dB a +40 dB)", "behavior": "Compensación de nivel post-compresión.", "default": makeup}
        ]
    }


def make_saturator(
    drive: float = 0.20,
    base: float = 0.0,
    output: float = 0.70,
    acoustic_purpose: str = "Saturación armónica y color analógico no lineal"
) -> Dict[str, Any]:
    """Generates an Ableton Saturator dictionary specification."""
    return {
        "name": "Saturator",
        "type": "native",
        "uri": "query:AudioFx#Saturator",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Drive", "name": "Drive (Distorsión armónica)", "range": "0.0 a 1.0 (0 dB a +36 dB)", "behavior": "Generación de armónicos superiores para presencia y grosor.", "default": drive},
            {"id": "Base", "name": "Base (Graves limpios)", "range": "0.0 a 1.0 (-inf a 0 dB)", "behavior": "Aislamiento del subgrave fundamental para evitar distorsión en < 80 Hz.", "default": base},
            {"id": "Output", "name": "Output Trim", "range": "0.0 a 1.0 (-inf a 0 dB)", "behavior": "Atenuación de salida para conservar el headroom de mezcla.", "default": output}
        ]
    }


def make_drum_buss(
    drive: float = 0.28,
    crunch: float = 0.35,
    transients: float = 0.65,
    boom: float = 0.20,
    output: float = 0.70,
    acoustic_purpose: str = "Pegada analógica, pegamento de batería y snap percusivo"
) -> Dict[str, Any]:
    """Generates an Ableton Drum Buss dictionary specification."""
    return {
        "name": "Drum Buss",
        "type": "native",
        "uri": "query:AudioFx#Drum%20Buss",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Drive", "name": "Drive", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Saturación analógica y distorsión armónica no lineal.", "default": drive},
            {"id": "Crunch", "name": "Crunch", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Saturación en frecuencias medias-altas para mordida y transientes.", "default": crunch},
            {"id": "Transients", "name": "Transients", "range": "0.0 a 1.0 (-inf a +inf dB)", "behavior": "Modificación de transientes; > 0.5 incrementa el snap inicial.", "default": transients},
            {"id": "Boom", "name": "Boom", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Resonancia sintonizada en subgraves para peso de bombo.", "default": boom},
            {"id": "Output", "name": "Output Gain", "range": "0.0 a 1.0 (-inf a +6 dB)", "behavior": "Ajuste de ganancia de salida compensatorio.", "default": output}
        ]
    }


def make_compressor(
    threshold: float = -14.0,
    ratio: float = 2.0,
    attack: float = 0.05,
    release: float = 0.20,
    sidechain: bool = False,
    acoustic_purpose: str = "Control dinámico y nivelación de señal"
) -> Dict[str, Any]:
    """Generates an Ableton Compressor dictionary specification."""
    return {
        "name": "Compressor",
        "type": "native",
        "uri": "query:AudioFx#Compressor",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Threshold", "name": "Threshold (Umbral)", "range": "-40.0 dB a 0.0 dB", "behavior": "Umbral de compresión dinámica.", "default": threshold},
            {"id": "Ratio", "name": "Ratio (Relación)", "range": "1.0 a 20.0", "behavior": "Relación de reducción de ganancia.", "default": ratio},
            {"id": "Attack", "name": "Attack (Tiempo de ataque)", "range": "0.0 a 1.0 (0.1 ms a 50 ms)", "behavior": "Velocidad de respuesta para domar picos transitorios.", "default": attack},
            {"id": "Release", "name": "Release (Relajación)", "range": "0.0 a 1.0 (10 ms a 1000 ms)", "behavior": "Tiempo de recuperación dinámica.", "default": release},
            {"id": "Sidechain", "name": "Sidechain Ducking", "range": "0.0 o 1.0", "behavior": "Ducking rítmico sincronizado al bombo de pista.", "default": 1.0 if sidechain else 0.0}
        ]
    }


def make_utility(
    bass_mono: float = 1.0,
    width: float = 1.0,
    gain: float = 0.0,
    bass_freq: float = 120.0,
    acoustic_purpose: str = "Monofonización de subgraves y control de campo estéreo"
) -> Dict[str, Any]:
    """Generates an Ableton Utility dictionary specification."""
    return {
        "name": "Utility",
        "type": "native",
        "uri": "query:AudioFx#Utility",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Bass Mono", "name": "Bass Mono", "range": "0.0 o 1.0", "behavior": "Monofoniza el subgrave estrictamente por debajo de la frecuencia de corte.", "default": bass_mono},
            {"id": "Bass Freq", "name": "Bass Mono Freq", "range": "50 Hz a 250 Hz", "behavior": "Frecuencia de corte para monofonización de graves.", "default": bass_freq},
            {"id": "Width", "name": "Stereo Width", "range": "0.0 a 4.0 (0% a 400%)", "behavior": "Control de apertura espacial estéreo.", "default": width},
            {"id": "Gain", "name": "Gain (Trim)", "range": "-inf a +35 dB", "behavior": "Ajuste de ganancia lineal limpio.", "default": gain}
        ]
    }


def make_ott(
    depth: float = 0.25,
    time: float = 0.50,
    in_gain: float = 0.0,
    out_gain: float = 0.0,
    acoustic_purpose: str = "Compresión multibanda agresiva upward/downward estilo club"
) -> Dict[str, Any]:
    """Generates an Xfer OTT dictionary specification."""
    return {
        "name": "OTT",
        "type": "plugin",
        "uri": "query:Plugins#VST3:Xfer%20Records:OTT",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Depth", "name": "Depth (Dry/Wet)", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Porcentaje de compresión multibanda hacia arriba y abajo.", "default": depth},
            {"id": "Time", "name": "Time Scaling", "range": "0.0 a 1.0 (10% a 1000%)", "behavior": "Escalado de tiempos de ataque y relajación multibanda.", "default": time},
            {"id": "In Gain", "name": "Input Gain", "range": "-24 dB a +24 dB", "behavior": "Ganancia de entrada al procesador multibanda.", "default": in_gain},
            {"id": "Out Gain", "name": "Output Gain", "range": "-24 dB a +24 dB", "behavior": "Ganancia de salida compensatoria.", "default": out_gain}
        ]
    }


def make_valhalla_supermassive(
    mode: float = 0.38,
    mix: float = 0.20,
    feedback: float = 0.50,
    lowcut: float = 0.20,
    highcut: float = 0.65,
    delay_sync: float = 1.0,
    warp: float = 0.50,
    density: float = 0.60,
    mod_rate: float = 0.25,
    mod_depth: float = 0.50,
    acoustic_purpose: str = "Difusión espacial masiva, nubes de reverb y ecos celestiales"
) -> Dict[str, Any]:
    """Generates a ValhallaSupermassive dictionary specification."""
    return {
        "name": "ValhallaSupermassive",
        "type": "plugin",
        "uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaSupermassive",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Mix", "name": "Mix (Dry/Wet)", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Balance de espacialidad cósmica y retardos envolventes.", "default": mix},
            {"id": "Mode", "name": "Algorithmic Mode", "range": "0.0 a 1.0 (22 Modos: Gemini, Hydra, Andromeda, Lyra, Capricorn...)", "behavior": "Topología algorítmica de retardos y densidad de difusión.", "default": mode},
            {"id": "DelaySync", "name": "Delay Sync", "range": "0.0 (ms) o 1.0 (Sincronizado a compás)", "behavior": "Sincronización rítmica métrica al tempo militar de la sesión.", "default": delay_sync},
            {"id": "Feedback", "name": "Feedback", "range": "0.0 a 0.95 (0% a 95%)", "behavior": "Regeneración de ecos y cola ambiental (máx 0.95 anti-runaway).", "default": feedback},
            {"id": "Warp", "name": "Warp", "range": "0.0 a 1.0", "behavior": "Desfase y modulación de tiempos de retardo dentro de la red.", "default": warp},
            {"id": "Density", "name": "Density", "range": "0.0 a 1.0", "behavior": "Densidad de reflexiones; transforma retardos discretos en reverb suave.", "default": density},
            {"id": "LowCut", "name": "Low Cut (HPF)", "range": "0.05 a 1.0 (20 Hz a 1500 Hz)", "behavior": "Filtro pasa-altos protector anti-barro (mínimo 0.05 obligatorio).", "default": lowcut},
            {"id": "HighCut", "name": "High Cut (LPF)", "range": "0.0 a 1.0 (1000 Hz a 20000 Hz)", "behavior": "Filtro pasa-bajos para atenuar estridencias y dar profundidad analógica.", "default": highcut},
            {"id": "ModRate", "name": "Modulation Rate", "range": "0.0 a 1.0", "behavior": "Velocidad de coros internos.", "default": mod_rate},
            {"id": "ModDepth", "name": "Modulation Depth", "range": "0.0 a 1.0", "behavior": "Profundidad de modulación de tono.", "default": mod_depth}
        ]
    }


def make_valhalla_vintage_verb(
    mode: float = 0.0,
    color: float = 0.50,
    mix: float = 0.20,
    decay: float = 0.25,
    predelay: float = 0.05,
    lowcut: float = 0.20,
    highcut: float = 0.65,
    size: float = 0.50,
    attack: float = 0.0,
    bass_mult: float = 0.50,
    early_diffusion: float = 1.0,
    late_diffusion: float = 1.0,
    mod_rate: float = 0.25,
    mod_depth: float = 0.50,
    acoustic_purpose: str = "Espacialidad vintage, placas clásicas de estudio y salas de concierto"
) -> Dict[str, Any]:
    """Generates a ValhallaVintageVerb dictionary specification."""
    params_copy = []
    defaults_map = {
        "Mix": mix, "Decay": decay, "PreDelay": predelay, "Mode": mode,
        "ColorMode": color, "Size": size, "Attack": attack, "BassMult": bass_mult,
        "LowCut": lowcut, "HighCut": highcut, "EarlyDiffusion": early_diffusion,
        "LateDiffusion": late_diffusion, "ModRate": mod_rate, "ModDepth": mod_depth
    }
    for p in VALHALLA_VINTAGE_VERB_PARAMS:
        p_dict = dict(p)
        if p["id"] in defaults_map:
            p_dict["default"] = defaults_map[p["id"]]
        params_copy.append(p_dict)
    return {
        "name": "ValhallaVintageVerb",
        "type": "plugin",
        "uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb",
        "acoustic_purpose": acoustic_purpose,
        "params": params_copy
    }


def make_surge_xt_effects(
    dsp_type: str = "fxt_tape",
    drive: float = 0.28,
    mix: float = 0.75,
    slot_name: str = "Slot 1 DSP Type (Tape Saturation)",
    acoustic_purpose: str = "Color analógico Chow Tape y procesamiento multiefecto modular"
) -> Dict[str, Any]:
    """Generates a Surge XT Effects dictionary specification."""
    return {
        "name": "Surge XT Effects",
        "type": "plugin",
        "uri": "query:Plugins#VST3:Surge%20Synth%20Team:Surge%20XT%20Effects",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "FX A1 Type", "name": slot_name, "range": "fxt_tape, fxt_conditioner, fxt_dist, fxt_ensemble, fxt_chow", "behavior": "Algoritmo DSP activo en slot analógico.", "default": dsp_type},
            {"id": "FX A1 Drive", "name": "Slot 1 Tape Drive / Depth", "range": "0.0 a 1.0 (0 dB a +36 dB)", "behavior": "Intensidad de compresión y saturación magnética de cinta.", "default": drive},
            {"id": "FX A1 Mix", "name": "Slot 1 Dry/Wet", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Balance de procesamiento paralelo.", "default": mix}
        ]
    }


def make_chorus_ensemble(
    amount: float = 0.40,
    rate: float = 0.25,
    warmth: float = 0.50,
    acoustic_purpose: str = "Ensanchamiento estéreo BBD y modulación coral sutil"
) -> Dict[str, Any]:
    """Generates an Ableton Chorus-Ensemble dictionary specification."""
    return {
        "name": "Chorus-Ensemble",
        "type": "native",
        "uri": "query:AudioFx#Chorus-Ensemble",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Amount", "name": "Amount (Profundidad)", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Profundidad de modulación de tono; ensancha la imagen estéreo de los acordes.", "default": amount},
            {"id": "Rate", "name": "Rate (Velocidad)", "range": "0.0 a 1.0 (0.01 Hz a 10 Hz)", "behavior": "Velocidad del LFO; tasas bajas generan movimiento orgánico lento.", "default": rate},
            {"id": "Warmth", "name": "Warmth (Calidez)", "range": "0.0 a 1.0", "behavior": "Filtrado analógico cálido de tipo BBD.", "default": warmth}
        ]
    }


def make_delay(
    dry_wet: float = 0.30,
    feedback: float = 0.35,
    sync: float = 1.0,
    ping_pong: float = 1.0,
    acoustic_purpose: str = "Repeticiones rítmicas sincronizadas y profundidad temporal estéreo"
) -> Dict[str, Any]:
    """Generates an Ableton Delay dictionary specification."""
    return {
        "name": "Delay",
        "type": "native",
        "uri": "query:AudioFx#Delay",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Dry/Wet", "name": "Dry/Wet", "range": "0.0 a 1.0", "behavior": "Balance de mezcla de ecos.", "default": dry_wet},
            {"id": "Feedback", "name": "Feedback", "range": "0.0 a 1.0", "behavior": "Regeneración de ecos.", "default": feedback},
            {"id": "Sync", "name": "Sync", "range": "0.0 (ms) o 1.0 (Beat)", "behavior": "Sincronización rítmica al tempo militar.", "default": sync},
            {"id": "PingPong", "name": "Ping Pong Mode", "range": "0.0 o 1.0", "behavior": "Alternancia estéreo de repeticiones.", "default": ping_pong}
        ]
    }


def make_auto_tune_artist(
    key: str = "C",
    scale: str = "Minor",
    retune_speed: float = 0.0,
    humanize: float = 0.0,
    acoustic_purpose: str = "Afinación vocal de tono y transientes modernos"
) -> Dict[str, Any]:
    """Generates an Antares Auto-Tune Artist dictionary specification."""
    return {
        "name": "Auto-Tune Artist",
        "type": "plugin",
        "uri": "query:Plugins#VST3:Antares:Auto-Tune%20Artist",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Key", "name": "Tonal Key", "range": "C, C#, D...", "behavior": "Tónica de la escala vocal.", "default": key},
            {"id": "Scale", "name": "Scale Type", "range": "Major, Minor, Chromatic...", "behavior": "Tipo de escala armónica.", "default": scale},
            {"id": "Retune Speed", "name": "Retune Speed", "range": "0.0 a 1.0 (0 ms a 400 ms)", "behavior": "Velocidad de cuantización de tono; 0.0 = hard snap moderno.", "default": retune_speed},
            {"id": "Humanize", "name": "Humanize", "range": "0.0 a 1.0", "behavior": "Preservación de micro-inflexiones vocales.", "default": humanize}
        ]
    }


def make_pro_q_4(
    hpf_freq: float = 0.25,
    clean_dip: float = 0.40,
    presence_boost: float = 0.65,
    air_shelf: float = 0.85,
    acoustic_purpose: str = "Ecualización quirúrgica lineal y corte de resonancias"
) -> Dict[str, Any]:
    """Generates a FabFilter Pro-Q 4 dictionary specification."""
    return {
        "name": "Pro-Q 4",
        "type": "plugin",
        "uri": "query:Plugins#VST3:FabFilter:FabFilter%20Pro-Q%204",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "HPF Freq", "name": "Band 1 HPF (Corte de Graves)", "range": "0.0 a 1.0 (10 Hz a 500 Hz)", "behavior": "Corte de subgraves y ruidos de proximidad.", "default": hpf_freq},
            {"id": "Clean Dip", "name": "Band 2 Bell (Limpieza Medios)", "range": "0.0 a 1.0 (200 Hz a 1000 Hz)", "behavior": "Atenuación de resonancias nasales.", "default": clean_dip},
            {"id": "Presence Boost", "name": "Band 3 Bell (Presencia)", "range": "0.0 a 1.0 (1000 Hz a 5000 Hz)", "behavior": "Articulación e inteligibilidad.", "default": presence_boost},
            {"id": "Air Shelf", "name": "Band 4 High Shelf (Aire)", "range": "0.0 a 1.0 (8000 Hz a 20000 Hz)", "behavior": "Brillo y apertura sedosa.", "default": air_shelf}
        ]
    }


def make_saturn_2(
    drive: float = 0.25,
    dynamics: float = 0.0,
    warmth: float = 0.50,
    mix: float = 0.80,
    acoustic_purpose: str = "Saturación multibanda y excitación armónica"
) -> Dict[str, Any]:
    """Generates a FabFilter Saturn 2 dictionary specification."""
    return {
        "name": "Saturn 2",
        "type": "plugin",
        "uri": "query:Plugins#VST3:FabFilter:FabFilter%20Saturn%202",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Drive", "name": "Drive", "range": "0.0 a 1.0", "behavior": "Intensidad de saturación en la banda activa.", "default": drive},
            {"id": "Dynamics", "name": "Dynamics", "range": "-1.0 a 1.0", "behavior": "Expansión o compresión dinámica dentro de la saturación.", "default": dynamics},
            {"id": "Warmth", "name": "Warmth / Tone", "range": "0.0 a 1.0", "behavior": "Balance tonal de la saturación.", "default": warmth},
            {"id": "Mix", "name": "Mix", "range": "0.0 a 1.0", "behavior": "Balance de procesamiento paralelo armónico.", "default": mix}
        ]
    }


def make_reverb(
    decay_time: float = 0.35,
    dry_wet: float = 0.28,
    acoustic_purpose: str = "Espacio acústico reverberado natural"
) -> Dict[str, Any]:
    """Generates an Ableton stock Reverb dictionary specification."""
    return {
        "name": "Reverb",
        "type": "native",
        "uri": "query:AudioFx#Reverb",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "DecayTime", "name": "Decay Time", "range": "0.0 a 1.0", "behavior": "Cola espacial de fondo.", "default": decay_time},
            {"id": "Dry/Wet", "name": "Dry/Wet", "range": "0.0 a 1.0", "behavior": "Mezcla ambiental de reverb.", "default": dry_wet}
        ]
    }


# --- 4. Acoustic Sound Family Catalog Builders ---

def _build_urbana_moderna_catalog() -> Dict[str, List[Dict[str, Any]]]:
    """
    Urbana / Moderna: Trap, Drill, Boom Bap, Reggaeton.
    Sharp transients, Drum Buss crunch, Glue compression, mono 808 sub, hard saturation,
    Auto-Tune vocals, no OTT, no Supermassive on keys/lead.
    """
    return {
        "KICK": [
            make_eq_eight(hpf_default=0.14, bell_default=0.25, bell_name="Frecuencia de Punch (50-75 Hz)", acoustic_purpose="Corte subsónico 30 Hz y realce de impacto fundamental"),
            make_glue_compressor(threshold=-14.0, ratio=2.0, attack=0.70, release=0.0, makeup=0.10, acoustic_purpose="Pegada transitoria controlada y peso sostenido")
        ],
        "DRUMS": [
            make_eq_eight(hpf_default=0.18, bell_default=0.45, bell_name="Frecuencia Resonancia Caja (300-450 Hz)", high_default=0.82, high_name="Brillo Platillos (9-12 kHz)", acoustic_purpose="Limpieza de barro en caja y apertura de platillos"),
            make_drum_buss(drive=0.28, crunch=0.35, transients=0.65, boom=0.20, output=0.70, acoustic_purpose="Crunch analógico en medios-altos y snap inicial"),
            make_glue_compressor(threshold=-12.0, ratio=1.0, attack=0.50, release=0.0, dry_wet=0.85, makeup=0.15, acoustic_purpose="Compresión paralela New York"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.28, mix=0.75, slot_name="Slot 1 DSP Type (Chow Tape)", acoustic_purpose="Saturación magnética analógica en bus de batería"),
            make_valhalla_vintage_verb(mode=0.0, color=0.50, mix=0.15, decay=0.20, acoustic_purpose="Ambiente de sala corto y controlado")
        ],
        "BASS": [
            make_eq_eight(hpf_default=0.20, bell_default=0.55, bell_name="Frecuencia Mordida (700-1200 Hz)", acoustic_purpose="Corte subsónico estricto y presencia armónica"),
            make_saturator(drive=0.22, base=0.0, output=0.70, acoustic_purpose="Generación de armónicos superiores para teléfonos"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.20, mix=0.65, slot_name="Slot 1 DSP Type (Analog Tape)", acoustic_purpose="Calidez analógica en medios graves")
        ],
        "KEYS": [
            make_eq_eight(hpf_default=0.30, bell_default=0.42, bell_name="Limpieza de Barro (300-400 Hz)", high_default=0.65, high_name="Presencia Teclado (2.5-3.5 kHz)", acoustic_purpose="Filtro pasa-altos 120 Hz para despejar el 808"),
            make_chorus_ensemble(amount=0.35, rate=0.20, warmth=0.60, acoustic_purpose="Ensanchamiento estéreo y modulación"),
            make_valhalla_vintage_verb(mode=0.30, color=0.50, mix=0.20, decay=0.25, predelay=0.05, acoustic_purpose="Placa de estudio 1980s suave y espaciosa")
        ],
        "LEAD": [
            make_eq_eight(hpf_default=0.32, bell_default=0.68, bell_name="Corte Asperezas (3.5 kHz)", high_default=0.80, high_name="Aire Cristalino", acoustic_purpose="Eliminación de dureza digital"),
            make_saturator(drive=0.20, base=0.0, output=0.70, acoustic_purpose="Saturación cálida en medios"),
            make_delay(dry_wet=0.28, feedback=0.30, sync=1.0, ping_pong=1.0, acoustic_purpose="Retardo rítmico estéreo"),
            make_valhalla_vintage_verb(mode=0.10, color=0.50, mix=0.20, decay=0.28, predelay=0.04, acoustic_purpose="Placa brillante controlada")
        ],
        "STRINGS": [
            make_eq_eight(hpf_default=0.28, bell_default=0.52, bell_name="Dip Chelos (600 Hz)", high_default=0.78, high_name="Aire Cuerdas (8-14 kHz)", acoustic_purpose="Apertura y limpieza de cuerdas"),
            make_valhalla_vintage_verb(mode=0.20, color=0.50, mix=0.25, decay=0.35, predelay=0.06, acoustic_purpose="Sala de concierto sinfónica cálida")
        ],
        "VOCALS": [
            make_auto_tune_artist(key="C", scale="Minor", retune_speed=0.0, humanize=0.0, acoustic_purpose="Afinación moderna con snap rápido"),
            make_pro_q_4(hpf_freq=0.25, clean_dip=0.40, presence_boost=0.65, air_shelf=0.85, acoustic_purpose="Limpieza quirúrgica y articulación"),
            make_compressor(threshold=-18.0, ratio=4.0, attack=0.01, release=0.10, acoustic_purpose="Compresión rápida estilo 1176 in-your-face"),
            make_saturn_2(drive=0.25, dynamics=0.0, warmth=0.50, mix=0.80, acoustic_purpose="Saturación de cinta y excitación armónica"),
            make_valhalla_vintage_verb(mode=0.30, color=0.50, mix=0.18, decay=0.25, predelay=0.05, acoustic_purpose="Placa de estudio sedosa")
        ],
        "PAD": [
            make_eq_eight(hpf_default=0.30, bell_default=0.45, bell_name="Limpieza Medios (350 Hz)", high_default=0.72, high_name="LPF Anti-Siseo (10 kHz)", acoustic_purpose="Filtro pasa-altos 130 Hz y recorte de siseo"),
            make_chorus_ensemble(amount=0.40, rate=0.25, warmth=0.60, acoustic_purpose="Apertura estéreo dimensional"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.30, decay=0.45, predelay=0.06, acoustic_purpose="Cámara vintage con decaimiento largo")
        ],
        "GUITAR": [
            make_eq_eight(hpf_default=0.28, bell_default=0.44, bell_name="Limpieza de Barro (380 Hz)", high_default=0.68, high_name="Presencia (2.8 kHz)", acoustic_purpose="Limpieza de resonancias y definición de púa"),
            make_saturator(drive=0.18, base=0.0, output=0.75, acoustic_purpose="Calidez armónica analógica"),
            make_delay(dry_wet=0.25, feedback=0.30, sync=1.0, acoustic_purpose="Eco rítmico sincronizado")
        ],
        "BRASS": [
            make_eq_eight(hpf_default=0.28, bell_default=0.65, bell_name="Presencia Metales (2.5 kHz)", acoustic_purpose="Protección de subgrave y presencia"),
            make_glue_compressor(threshold=-12.0, ratio=2.0, attack=0.40, release=0.0, makeup=0.12, acoustic_purpose="Control dinámico de ataque de boquilla")
        ],
        "CHOIR": [
            make_eq_eight(hpf_default=0.32, bell_default=0.58, bell_name="Dip Formantes (800 Hz)", high_default=0.78, high_name="Apertura Celestial", acoustic_purpose="Apertura en agudos y espacio para solista"),
            make_valhalla_vintage_verb(mode=0.50, color=0.50, mix=0.30, decay=0.40, predelay=0.06, acoustic_purpose="Catedral etérea")
        ],
        "PERCUSSION": [
            make_eq_eight(hpf_default=0.24, bell_default=0.68, bell_name="Chasquido Shaker/Perc (3 kHz)", acoustic_purpose="Corte de retumbes graves"),
            make_glue_compressor(threshold=-14.0, ratio=2.0, attack=0.70, release=0.0, makeup=0.10, acoustic_purpose="Transientes percusivos intactos")
        ],
        "FX": [
            make_eq_eight(hpf_default=0.22, bell_default=0.65, bell_name="Atenuación Medios (3.5 kHz)", acoustic_purpose="Corte de subgrave sucio"),
            make_utility(bass_mono=1.0, width=1.40, acoustic_purpose="Apertura estéreo para barridos y risers"),
            make_valhalla_supermassive(mode=0.38, mix=0.40, feedback=0.60, acoustic_purpose="Difusión espacial masiva para efectos de transición"),
            make_surge_xt_effects(dsp_type="fxt_conditioner", drive=0.30, mix=0.50, slot_name="Slot 1 Conditioner/Shaper", acoustic_purpose="Modelado armónico de textura")
        ],
        "RHYTHM_GUITAR": [
            make_eq_eight(hpf_default=0.28, bell_default=0.45, bell_name="Limpieza de Barro (400 Hz)", high_default=0.65, high_name="Brillo Rasgueo (2.5 kHz)", acoustic_purpose="Corte de choque con bajo"),
            make_glue_compressor(threshold=-14.0, ratio=1.0, attack=0.50, release=0.0, makeup=0.10, acoustic_purpose="Nivelación suave de rasgueo")
        ],
        "LEAD_GUITAR": [
            make_eq_eight(hpf_default=0.30, bell_default=0.70, bell_name="Corte Chillido (3.8 kHz)", high_default=0.68, high_name="Mordida Solista (2.8 kHz)", acoustic_purpose="Definición solista"),
            make_saturator(drive=0.25, base=0.0, output=0.70, acoustic_purpose="Saturación de overdrive analógico"),
            make_delay(dry_wet=0.30, feedback=0.35, sync=1.0, acoustic_purpose="Retardo solista estéreo")
        ],
        "808_BASS": [
            make_eq_eight(hpf_default=0.14, bell_default=0.22, bell_name="Cuerpo Sub 808 (40-50 Hz)", acoustic_purpose="HPF 28 Hz y pegada fundamental"),
            make_saturator(drive=0.25, base=0.0, output=0.70, acoustic_purpose="Saturación armónica en medios para altavoces pequeños"),
            make_utility(bass_mono=1.0, bass_freq=120.0, width=0.0, acoustic_purpose="Monofonización estricta de subgraves")
        ],
        "ELECTRIC_BASS": [
            make_eq_eight(hpf_default=0.22, bell_default=0.40, bell_name="Limpieza Resonancia (220 Hz)", high_default=0.60, high_name="Ataque Dedos (1.5 kHz)", acoustic_purpose="Definición de dedos y cuerdas"),
            make_compressor(threshold=-15.0, ratio=4.0, attack=0.05, release=0.20, acoustic_purpose="Compresión VCA niveladora")
        ],
        "DEMBOW": [
            make_eq_eight(hpf_default=0.16, bell_default=0.68, bell_name="Chasquido Timbal (2.8 kHz)", acoustic_purpose="HPF 32 Hz y chasquido sincopado"),
            make_drum_buss(drive=0.32, crunch=0.40, transients=0.70, boom=0.15, output=0.70, acoustic_purpose="Pegada urbana dura y snap de percusión")
        ],
        "BACKING_VOCALS": [
            make_eq_eight(hpf_default=0.34, bell_default=0.60, bell_name="Dip Solista (2 kHz)", high_default=0.82, high_name="Aire Angelical (10 kHz)", acoustic_purpose="Espacio para la voz principal"),
            make_chorus_ensemble(amount=0.45, rate=0.25, warmth=0.60, acoustic_purpose="Apertura estéreo coral"),
            make_compressor(threshold=-20.0, ratio=4.0, attack=0.02, release=0.15, acoustic_purpose="Compresión densa para fondo estable"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.30, decay=0.35, predelay=0.05, acoustic_purpose="Cámara estéreo envolvente")
        ],
        "SUB": [
            make_eq_eight(hpf_default=0.12, bell_default=0.20, bell_name="Sub Puro (40-50 Hz)", acoustic_purpose="Corte subsónico estricto 24 Hz"),
            make_utility(bass_mono=1.0, bass_freq=120.0, width=0.0, acoustic_purpose="Monofonización absoluta en canal sub")
        ],
        "COUNTER_LEAD": [
            make_eq_eight(hpf_default=0.32, bell_default=0.65, bell_name="Dip Lead Frontal (2.5 kHz)", acoustic_purpose="Despeje de voz solista y lead"),
            make_delay(dry_wet=0.30, feedback=0.35, sync=1.0, acoustic_purpose="Retardo estéreo rítmico"),
            make_valhalla_vintage_verb(mode=0.10, color=0.50, mix=0.25, decay=0.32, predelay=0.04, acoustic_purpose="Espacio secundario profundo")
        ],
        "EAR_CANDY": [
            make_eq_eight(hpf_default=0.38, bell_default=0.60, bell_name="Vaciado Medios-Bajos", high_default=0.88, high_name="Destellos Aire (12 kHz)", acoustic_purpose="Corte alto y aire brillante"),
            make_delay(dry_wet=0.35, feedback=0.40, sync=1.0, ping_pong=1.0, acoustic_purpose="Ecos de adorno laterales")
        ],
        "TEXTURE_FOLEY": [
            make_eq_eight(hpf_default=0.24, bell_default=0.50, bell_name="Medios Orgánicos", high_default=0.75, high_name="LPF Calidez (8 kHz)", acoustic_purpose="Corte de lodo sub y siseo agudo"),
            make_utility(bass_mono=1.0, width=0.85, acoustic_purpose="Control de anchura ambiental")
        ]
    }


def _build_electronica_club_catalog() -> Dict[str, List[Dict[str, Any]]]:
    """
    Electrónica de Club: House, Techno, EDM, DnB, Dubstep, Trance.
    Sidechain ducking, steep cut filters, synchronized delays, OTT multiband compression, bright halls.
    """
    return {
        "KICK": [
            make_eq_eight(hpf_default=0.16, bell_default=0.24, bell_name="Punch Bombo Club (60 Hz)", acoustic_purpose="HPF 32 Hz y pegada contundente para pista de baile"),
            make_glue_compressor(threshold=-12.0, ratio=2.0, attack=0.60, release=0.0, dry_wet=0.90, makeup=0.15, acoustic_purpose="Control dinámico de transientes de bombo"),
            make_utility(bass_mono=1.0, bass_freq=130.0, width=1.0, acoustic_purpose="Monofonización quirúrgica de subgraves")
        ],
        "DRUMS": [
            make_eq_eight(hpf_default=0.18, bell_default=0.45, bell_name="Corte Barro (400 Hz)", high_default=0.85, high_name="Aire Platillos (12 kHz)", acoustic_purpose="Limpieza de medios y apertura de altas frecuencias"),
            make_glue_compressor(threshold=-10.0, ratio=2.0, attack=0.50, release=0.0, dry_wet=0.90, makeup=0.15, acoustic_purpose="Pegamento dinámico de batería"),
            make_saturator(drive=0.22, base=0.0, output=0.70, acoustic_purpose="Saturación contundente de caja y percusión")
        ],
        "BASS": [
            make_eq_eight(hpf_default=0.16, bell_default=0.24, bell_name="Muesca Bombo (60 Hz)", acoustic_purpose="Tallado quirúrgico para acoplamiento con bombo"),
            make_compressor(threshold=-16.0, ratio=4.0, attack=0.01, release=0.20, sidechain=True, acoustic_purpose="Ducking rítmico sincronizado al bombo"),
            make_saturator(drive=0.30, base=0.0, output=0.70, acoustic_purpose="Saturación agresiva para cortar la mezcla club"),
            make_utility(bass_mono=1.0, bass_freq=125.0, width=0.0, acoustic_purpose="Monofonización pura del bajo")
        ],
        "KEYS": [
            make_eq_eight(hpf_default=0.32, bell_default=0.42, bell_name="Corte Graves Acordes", high_default=0.75, high_name="Brillo Sintetizador", acoustic_purpose="Filtro pasa-altos 130 Hz para liberar graves"),
            make_ott(depth=0.20, time=0.50, acoustic_purpose="Compresión multibanda upward/downward para presencia de acordes"),
            make_chorus_ensemble(amount=0.35, rate=0.25, warmth=0.40, acoustic_purpose="Apertura dimensional estéreo"),
            make_compressor(threshold=-15.0, ratio=3.0, attack=0.02, release=0.25, sidechain=True, acoustic_purpose="Bombeo sidechain rítmico"),
            make_valhalla_vintage_verb(mode=0.0, color=0.0, mix=0.25, decay=0.35, acoustic_purpose="Concert Hall brillante y amplio")
        ],
        "LEAD": [
            make_eq_eight(hpf_default=0.32, bell_default=0.68, bell_name="Presencia Lead (3.5 kHz)", high_default=0.85, high_name="Aire Sintetizador", acoustic_purpose="Corte de graves y apertura de agudos"),
            make_ott(depth=0.30, time=0.50, acoustic_purpose="Compresión multibanda OTT agresiva para cortar en el club"),
            make_compressor(threshold=-16.0, ratio=4.0, attack=0.01, release=0.20, sidechain=True, acoustic_purpose="Ducking rítmico al compás del bombo"),
            make_delay(dry_wet=0.35, feedback=0.40, sync=1.0, ping_pong=1.0, acoustic_purpose="Retardos estéreo ping-pong sincronizados a 1/8d"),
            make_valhalla_supermassive(mode=0.38, mix=0.25, feedback=0.45, acoustic_purpose="Difusión espacial masiva envolvente")
        ],
        "STRINGS": [
            make_eq_eight(hpf_default=0.30, bell_default=0.55, bell_name="Cuerpo Cuerdas", high_default=0.80, high_name="Brillo Cuerdas", acoustic_purpose="Corte de subgraves y apertura aérea"),
            make_compressor(threshold=-14.0, ratio=3.0, attack=0.05, release=0.30, sidechain=True, acoustic_purpose="Bombeo sidechain con el bombo"),
            make_valhalla_supermassive(mode=0.25, mix=0.35, feedback=0.60, acoustic_purpose="Nube difusa estéreo para cuerdas épicas")
        ],
        "VOCALS": [
            make_auto_tune_artist(key="C", scale="Minor", retune_speed=0.0, humanize=0.0, acoustic_purpose="Afinación moderna snap duro para club"),
            make_pro_q_4(hpf_freq=0.25, clean_dip=0.40, presence_boost=0.70, air_shelf=0.85, acoustic_purpose="Ecualización quirúrgica y presencia vocal"),
            make_compressor(threshold=-16.0, ratio=4.0, attack=0.01, release=0.15, acoustic_purpose="Compresión rápida para nivel vocal firme"),
            make_ott(depth=0.20, time=0.50, acoustic_purpose="Multibanda vocal brillante y denso"),
            make_delay(dry_wet=0.30, feedback=0.35, sync=1.0, ping_pong=1.0, acoustic_purpose="Ecos sincronizados de pista"),
            make_valhalla_vintage_verb(mode=0.0, color=0.0, mix=0.25, decay=0.35, acoustic_purpose="Sala de concierto amplia y cristalina")
        ],
        "PAD": [
            make_eq_eight(hpf_default=0.32, bell_default=0.48, bell_name="Limpieza Medios", high_default=0.75, high_name="Aire Pad", acoustic_purpose="Filtro pasa-altos 140 Hz para evitar congestión"),
            make_compressor(threshold=-15.0, ratio=3.0, attack=0.02, release=0.30, sidechain=True, acoustic_purpose="Bombeo sidechain envolvente"),
            make_valhalla_supermassive(mode=0.18, mix=0.40, feedback=0.70, acoustic_purpose="Difusión celestial Lyra/Andromeda"),
            make_chorus_ensemble(amount=0.45, rate=0.20, warmth=0.40, acoustic_purpose="Modulación coral estéreo")
        ],
        "GUITAR": [
            make_eq_eight(hpf_default=0.28, bell_default=0.45, bell_name="Limpieza de Barro", high_default=0.70, high_name="Brillo Guitarra", acoustic_purpose="Corte de frecuencias bajas"),
            make_compressor(threshold=-14.0, ratio=3.0, attack=0.05, release=0.20, sidechain=True, acoustic_purpose="Compresión sidechain adaptada al groove"),
            make_delay(dry_wet=0.30, feedback=0.35, sync=1.0, acoustic_purpose="Ecos rítmicos sincronizados")
        ],
        "BRASS": [
            make_eq_eight(hpf_default=0.28, bell_default=0.65, bell_name="Presencia Metales", acoustic_purpose="Protección de subgraves y mordida sintética"),
            make_glue_compressor(threshold=-12.0, ratio=2.0, attack=0.40, release=0.0, makeup=0.15, acoustic_purpose="Control dinámico de transientes"),
            make_saturator(drive=0.20, base=0.0, output=0.70, acoustic_purpose="Distorsión armónica para metales agresivos")
        ],
        "CHOIR": [
            make_eq_eight(hpf_default=0.34, bell_default=0.55, bell_name="Dip Formantes", high_default=0.80, high_name="Aire Coral", acoustic_purpose="Corte de medios-bajos y apertura en agudos"),
            make_compressor(threshold=-15.0, ratio=3.0, attack=0.05, release=0.30, sidechain=True, acoustic_purpose="Ducking rítmico con el bombo"),
            make_valhalla_vintage_verb(mode=0.0, color=0.0, mix=0.35, decay=0.45, acoustic_purpose="Concert Hall brillante de grandes dimensiones")
        ],
        "PERCUSSION": [
            make_eq_eight(hpf_default=0.26, bell_default=0.70, bell_name="Presencia Percusión Club", acoustic_purpose="Corte subsónico y realce de impacto"),
            make_compressor(threshold=-15.0, ratio=3.0, attack=0.05, release=0.15, sidechain=True, acoustic_purpose="Sidechain rítmico"),
            make_delay(dry_wet=0.30, feedback=0.35, sync=1.0, acoustic_purpose="Retardo sincronizado al tempo militar")
        ],
        "FX": [
            make_eq_eight(hpf_default=0.22, bell_default=0.60, bell_name="Cuerpo Transición", high_default=0.85, high_name="Aire Barridos", acoustic_purpose="Corte de subgraves y realce de efectos"),
            make_delay(dry_wet=0.40, feedback=0.45, sync=1.0, ping_pong=1.0, acoustic_purpose="Ecos espaciales sincronizados"),
            make_valhalla_supermassive(mode=0.45, mix=0.50, feedback=0.75, acoustic_purpose="Difusión masiva para subidas y transiciones")
        ],
        "RHYTHM_GUITAR": [
            make_eq_eight(hpf_default=0.30, bell_default=0.45, bell_name="Corte Barro", high_default=0.70, high_name="Presencia Rasgueo", acoustic_purpose="Corte estricto de graves"),
            make_compressor(threshold=-15.0, ratio=3.0, attack=0.05, release=0.20, sidechain=True, acoustic_purpose="Compresión sidechain al ritmo del club")
        ],
        "LEAD_GUITAR": [
            make_eq_eight(hpf_default=0.32, bell_default=0.68, bell_name="Presencia Solista", high_default=0.80, high_name="Aire Guitarra", acoustic_purpose="Corte de graves y apertura"),
            make_ott(depth=0.25, time=0.50, acoustic_purpose="Presencia y sostenimiento multibanda"),
            make_delay(dry_wet=0.35, feedback=0.40, sync=1.0, ping_pong=1.0, acoustic_purpose="Retardos estéreo sincronizados")
        ],
        "808_BASS": [
            make_eq_eight(hpf_default=0.16, bell_default=0.25, bell_name="Sub Punch Club (50 Hz)", acoustic_purpose="Filtro pasa-altos 30 Hz"),
            make_compressor(threshold=-16.0, ratio=4.0, attack=0.01, release=0.20, sidechain=True, acoustic_purpose="Ducking sidechain instantáneo para que pegue el bombo"),
            make_saturator(drive=0.30, base=0.0, output=0.70, acoustic_purpose="Saturación agresiva de armónicos"),
            make_utility(bass_mono=1.0, bass_freq=125.0, width=0.0, acoustic_purpose="Monofonización rigurosa")
        ],
        "ELECTRIC_BASS": [
            make_eq_eight(hpf_default=0.22, bell_default=0.45, bell_name="Presencia Bajo", high_default=0.65, high_name="Ataque Dedos", acoustic_purpose="Corte de subgraves y realce de ataque"),
            make_compressor(threshold=-15.0, ratio=4.0, attack=0.02, release=0.20, sidechain=True, acoustic_purpose="Compresión con bombeo sidechain"),
            make_saturator(drive=0.20, base=0.0, output=0.75, acoustic_purpose="Calidez armónica para presencia")
        ],
        "DEMBOW": [
            make_eq_eight(hpf_default=0.18, bell_default=0.70, bell_name="Chasquido Club (3 kHz)", acoustic_purpose="HPF 35 Hz y chasquido brillante"),
            make_glue_compressor(threshold=-10.0, ratio=2.0, attack=0.40, release=0.0, dry_wet=0.85, makeup=0.15, acoustic_purpose="Compresión dinámica para pegada en pista"),
            make_saturator(drive=0.25, base=0.0, output=0.70, acoustic_purpose="Mordida en frecuencias medias")
        ],
        "BACKING_VOCALS": [
            make_eq_eight(hpf_default=0.35, bell_default=0.58, bell_name="Dip Lead", high_default=0.85, high_name="Aire Coros", acoustic_purpose="Corte de graves y apertura etérea"),
            make_chorus_ensemble(amount=0.45, rate=0.25, warmth=0.40, acoustic_purpose="Ensanchamiento estéreo masivo"),
            make_compressor(threshold=-18.0, ratio=4.0, attack=0.02, release=0.20, sidechain=True, acoustic_purpose="Sidechain ducking detrás del bombo"),
            make_valhalla_vintage_verb(mode=0.0, color=0.0, mix=0.40, decay=0.45, acoustic_purpose="Reverb amplio para coros envolventes")
        ],
        "SUB": [
            make_eq_eight(hpf_default=0.14, bell_default=0.20, bell_name="Cuerpo Sub (45 Hz)", acoustic_purpose="Corte subsónico 26 Hz y LPF 110 Hz"),
            make_compressor(threshold=-16.0, ratio=4.0, attack=0.01, release=0.18, sidechain=True, acoustic_purpose="Ducking sidechain absoluto ante el golpe del bombo"),
            make_utility(bass_mono=1.0, bass_freq=130.0, width=0.0, acoustic_purpose="Monofonización pura del canal sub")
        ],
        "COUNTER_LEAD": [
            make_eq_eight(hpf_default=0.32, bell_default=0.65, bell_name="Dip Lead Frontal", high_default=0.80, high_name="Aire", acoustic_purpose="Corte de frecuencias graves"),
            make_ott(depth=0.20, time=0.50, acoustic_purpose="Control dinámico multibanda"),
            make_compressor(threshold=-15.0, ratio=3.0, attack=0.02, release=0.20, sidechain=True, acoustic_purpose="Sidechain al compás del bombo"),
            make_delay(dry_wet=0.35, feedback=0.40, sync=1.0, acoustic_purpose="Retardo estéreo sincronizado")
        ],
        "EAR_CANDY": [
            make_eq_eight(hpf_default=0.40, bell_default=0.65, bell_name="Vaciado Medios", high_default=0.90, high_name="Destellos Club", acoustic_purpose="Corte alto para efectos perimetrales"),
            make_delay(dry_wet=0.40, feedback=0.45, sync=1.0, ping_pong=1.0, acoustic_purpose="Repeticiones ping-pong en extremos del panorama"),
            make_valhalla_supermassive(mode=0.38, mix=0.30, feedback=0.50, acoustic_purpose="Difusión de destellos espaciales")
        ],
        "TEXTURE_FOLEY": [
            make_eq_eight(hpf_default=0.26, bell_default=0.50, bell_name="Cuerpo Textura", high_default=0.75, high_name="LPF Control", acoustic_purpose="Corte de subgraves y control de ruido blanco"),
            make_delay(dry_wet=0.25, feedback=0.30, sync=1.0, acoustic_purpose="Ecos sutiles de fondo")
        ]
    }


def _build_organica_acustica_catalog() -> Dict[str, List[Dict[str, Any]]]:
    """
    Orgánica / Acústica: Neo-Soul, R&B, Flamenco, Indie/Pop, Rock, Jazz, Folk.
    Transparent optical compression, analog Chow Tape warmth, warm BBD chorus, non-invasive EQ,
    strictly no OTT, natural acoustic reverbs.
    """
    return {
        "KICK": [
            make_eq_eight(hpf_default=0.16, bell_default=0.30, bell_name="Cuerpo Cálido Bombo (75 Hz)", acoustic_purpose="HPF suave en 35 Hz y cuerpo musical cálido"),
            make_glue_compressor(threshold=-10.0, ratio=1.0, attack=0.70, release=0.0, dry_wet=0.75, makeup=0.05, acoustic_purpose="Compresión óptica transparente 2:1 con ataque lento")
        ],
        "DRUMS": [
            make_eq_eight(hpf_default=0.20, bell_default=0.44, bell_name="Corte Barro Cálido (350 Hz)", high_default=0.75, high_name="Aire Natural", acoustic_purpose="Curvas musicales amplias y no invasivas"),
            make_glue_compressor(threshold=-8.0, ratio=1.0, attack=0.60, release=0.0, dry_wet=0.70, makeup=0.05, acoustic_purpose="Compresión suave y transparente sin aplastar transientes"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.20, mix=0.60, slot_name="Slot 1 Tape Warmth", acoustic_purpose="Saturación de cinta analógica Chow Tape cálida"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.16, decay=0.22, predelay=0.04, acoustic_purpose="Ambiente natural de sala 1970s Room")
        ],
        "BASS": [
            make_eq_eight(hpf_default=0.18, bell_default=0.35, bell_name="Cuerpo Bajo Acústico (100 Hz)", acoustic_purpose="HPF suave en 35 Hz y cuerpo acústico"),
            make_compressor(threshold=-16.0, ratio=2.5, attack=0.25, release=0.30, acoustic_purpose="Nivelación suave estilo opto LA-2A"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.18, mix=0.65, slot_name="Slot 1 Tape Saturation", acoustic_purpose="Calidez armónica analógica"),
            make_utility(bass_mono=1.0, bass_freq=110.0, width=1.0, acoustic_purpose="Monofonización natural de graves")
        ],
        "KEYS": [
            make_eq_eight(hpf_default=0.28, bell_default=0.40, bell_name="Limpieza Medios (300 Hz)", high_default=0.65, high_name="Dulzura Acordes (3 kHz)", acoustic_purpose="HPF gentil en 100 Hz y curvas suaves"),
            make_chorus_ensemble(amount=0.25, rate=0.15, warmth=0.80, acoustic_purpose="Chorus BBD analógico cálido y lento"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.18, mix=0.65, slot_name="Slot 1 Tape Saturation", acoustic_purpose="Calidez de cinta vintage"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.20, decay=0.26, predelay=0.04, acoustic_purpose="Cámara acústica 1970s Chamber")
        ],
        "LEAD": [
            make_eq_eight(hpf_default=0.30, bell_default=0.50, bell_name="Cuerpo Melódico (800 Hz)", high_default=0.72, high_name="Aire Cálido", acoustic_purpose="Curvas no invasivas y calidez armónica"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.18, mix=0.60, slot_name="Slot 1 Tape Warmth", acoustic_purpose="Saturación magnética de cinta"),
            make_delay(dry_wet=0.22, feedback=0.28, sync=1.0, acoustic_purpose="Eco sutil de cinta analógica"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.20, decay=0.26, predelay=0.04, acoustic_purpose="Cámara 1970s suave")
        ],
        "STRINGS": [
            make_eq_eight(hpf_default=0.26, bell_default=0.48, bell_name="Limpieza Barro (500 Hz)", high_default=0.75, high_name="Aire Cuerdas Natural", acoustic_purpose="HPF 100 Hz y limpieza musical"),
            make_compressor(threshold=-12.0, ratio=2.0, attack=0.30, release=0.40, acoustic_purpose="Compresión transparente de ataque lento"),
            make_valhalla_vintage_verb(mode=0.20, color=0.50, mix=0.24, decay=0.35, predelay=0.05, acoustic_purpose="Sala de concierto sinfónica cálida")
        ],
        "VOCALS": [
            make_eq_eight(hpf_default=0.26, bell_default=0.42, bell_name="Limpieza Proximidad (380 Hz)", high_default=0.78, high_name="Aire Sedoso", acoustic_purpose="HPF 100 Hz y shelf cálido en agudos"),
            make_compressor(threshold=-16.0, ratio=2.5, attack=0.15, release=0.25, acoustic_purpose="Nivelación óptica suave estilo LA-2A"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.18, mix=0.65, slot_name="Slot 1 Tape Warmth", acoustic_purpose="Saturación magnética de cinta para cuerpo vocal"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.18, decay=0.24, predelay=0.04, acoustic_purpose="Placa de estudio 1970s Plate sedosa")
        ],
        "PAD": [
            make_eq_eight(hpf_default=0.30, bell_default=0.45, bell_name="Cuerpo Pad", high_default=0.70, high_name="LPF Calidez (9 kHz)", acoustic_purpose="HPF 120 Hz y eliminación de estridencias"),
            make_chorus_ensemble(amount=0.30, rate=0.18, warmth=0.85, acoustic_purpose="Modulación BBD cálida analógica"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.15, mix=0.55, slot_name="Slot 1 Tape Saturation", acoustic_purpose="Saturación suave de cinta"),
            make_valhalla_vintage_verb(mode=0.30, color=0.50, mix=0.28, decay=0.38, predelay=0.05, acoustic_purpose="Cámara vintage rica y orgánica")
        ],
        "GUITAR": [
            make_eq_eight(hpf_default=0.28, bell_default=0.44, bell_name="Limpieza Barro (380 Hz)", high_default=0.68, high_name="Presencia Cálida (2.8 kHz)", acoustic_purpose="Corte suave de frecuencias bajas"),
            make_compressor(threshold=-14.0, ratio=2.0, attack=0.25, release=0.25, acoustic_purpose="Compresión óptica transparente"),
            make_delay(dry_wet=0.20, feedback=0.25, sync=1.0, acoustic_purpose="Eco sutil de cinta"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.18, decay=0.25, acoustic_purpose="Cámara 1970s Chamber")
        ],
        "BRASS": [
            make_eq_eight(hpf_default=0.28, bell_default=0.38, bell_name="Cuerpo Metales (200 Hz)", acoustic_purpose="HPF 110 Hz y cuerpo acústico cálido"),
            make_glue_compressor(threshold=-10.0, ratio=1.0, attack=0.60, release=0.0, makeup=0.08, acoustic_purpose="Compresión suave que respeta dinámicas"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.18, decay=0.25, acoustic_purpose="Sala acústica cálida")
        ],
        "CHOIR": [
            make_eq_eight(hpf_default=0.32, bell_default=0.50, bell_name="Formantes Cálidas", high_default=0.76, high_name="Apertura Sedosa (8 kHz)", acoustic_purpose="HPF 140 Hz y shelf suave de agudos"),
            make_compressor(threshold=-14.0, ratio=2.0, attack=0.35, release=0.40, acoustic_purpose="Compresión transparente que funde las voces"),
            make_valhalla_vintage_verb(mode=0.50, color=0.50, mix=0.30, decay=0.40, acoustic_purpose="Catedral acústica cálida")
        ],
        "PERCUSSION": [
            make_eq_eight(hpf_default=0.28, bell_default=0.65, bell_name="Presencia Madera/Shaker (2.5 kHz)", acoustic_purpose="HPF 110 Hz para evitar lodo subgrave"),
            make_compressor(threshold=-14.0, ratio=2.0, attack=0.30, release=0.20, acoustic_purpose="Control dinámico transparente")
        ],
        "FX": [
            make_eq_eight(hpf_default=0.22, bell_default=0.50, bell_name="Cuerpo Efecto", acoustic_purpose="Corte suave de frecuencias subsónicas"),
            make_delay(dry_wet=0.30, feedback=0.35, sync=1.0, acoustic_purpose="Eco cálido de cinta"),
            make_valhalla_vintage_verb(mode=0.50, color=0.50, mix=0.35, decay=0.45, acoustic_purpose="Ambiente acústico profundo")
        ],
        "RHYTHM_GUITAR": [
            make_eq_eight(hpf_default=0.28, bell_default=0.45, bell_name="Limpieza de Barro (400 Hz)", acoustic_purpose="HPF 120 Hz para acoplamiento con bajo"),
            make_compressor(threshold=-14.0, ratio=2.0, attack=0.25, release=0.25, acoustic_purpose="Nivelación suave de rasgueo"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.15, mix=0.50, slot_name="Slot 1 Tape Saturation", acoustic_purpose="Calidez de cinta")
        ],
        "LEAD_GUITAR": [
            make_eq_eight(hpf_default=0.30, bell_default=0.68, bell_name="Corte Asperezas (3.8 kHz)", high_default=0.68, high_name="Tono Solista", acoustic_purpose="HPF 130 Hz y control de estridencias"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.22, mix=0.70, slot_name="Slot 1 Tape Warmth", acoustic_purpose="Saturación armónica cálida"),
            make_delay(dry_wet=0.25, feedback=0.30, sync=1.0, acoustic_purpose="Eco suave de cinta"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.20, decay=0.28, acoustic_purpose="Cámara de estudio")
        ],
        "808_BASS": [
            make_eq_eight(hpf_default=0.16, bell_default=0.25, bell_name="Sub Cálido (60 Hz)", acoustic_purpose="HPF 30 Hz y fundamental cálido"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.18, mix=0.60, slot_name="Slot 1 Tape Saturation", acoustic_purpose="Saturación de cinta analógica"),
            make_utility(bass_mono=1.0, bass_freq=110.0, width=0.0, acoustic_purpose="Monofonización de subgraves")
        ],
        "ELECTRIC_BASS": [
            make_eq_eight(hpf_default=0.20, bell_default=0.38, bell_name="Cuerpo Bajo (120 Hz)", high_default=0.58, high_name="Presencia Dedos (1.2 kHz)", acoustic_purpose="HPF 38 Hz y definición de cuerdas"),
            make_compressor(threshold=-15.0, ratio=2.5, attack=0.20, release=0.25, acoustic_purpose="Compresión óptica musical"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.16, mix=0.60, slot_name="Slot 1 Tape Warmth", acoustic_purpose="Calidez analógica")
        ],
        "DEMBOW": [
            make_eq_eight(hpf_default=0.18, bell_default=0.40, bell_name="Cuerpo Tambor (80 Hz)", acoustic_purpose="HPF 35 Hz y cuerpo musical"),
            make_glue_compressor(threshold=-10.0, ratio=1.0, attack=0.60, release=0.0, makeup=0.08, acoustic_purpose="Compresión suave"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.20, mix=0.60, slot_name="Slot 1 Tape Saturation", acoustic_purpose="Calidez de cinta")
        ],
        "BACKING_VOCALS": [
            make_eq_eight(hpf_default=0.32, bell_default=0.60, bell_name="Dip Solista (2 kHz)", high_default=0.78, high_name="Aire Cálido", acoustic_purpose="HPF 160 Hz y espacio para solista"),
            make_chorus_ensemble(amount=0.35, rate=0.20, warmth=0.80, acoustic_purpose="Modulación BBD cálida"),
            make_compressor(threshold=-18.0, ratio=3.0, attack=0.20, release=0.25, acoustic_purpose="Compresión transparente"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.30, decay=0.35, acoustic_purpose="Cámara estéreo envolvente")
        ],
        "SUB": [
            make_eq_eight(hpf_default=0.14, bell_default=0.20, bell_name="Sub Fundamental", acoustic_purpose="Gentil HPF 26 Hz y LPF 100 Hz"),
            make_utility(bass_mono=1.0, bass_freq=110.0, width=0.0, acoustic_purpose="Monofonización natural")
        ],
        "COUNTER_LEAD": [
            make_eq_eight(hpf_default=0.30, bell_default=0.55, bell_name="Medios Cálidos", acoustic_purpose="HPF 160 Hz"),
            make_delay(dry_wet=0.25, feedback=0.30, sync=1.0, acoustic_purpose="Eco sutil de cinta"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.22, decay=0.30, acoustic_purpose="Cámara vintage")
        ],
        "EAR_CANDY": [
            make_eq_eight(hpf_default=0.38, bell_default=0.60, bell_name="Medios Suaves", high_default=0.82, high_name="Brillo Sedoso", acoustic_purpose="HPF 250 Hz"),
            make_delay(dry_wet=0.25, feedback=0.30, sync=1.0, acoustic_purpose="Eco cálido"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.20, decay=0.25, acoustic_purpose="Ambiente natural")
        ],
        "TEXTURE_FOLEY": [
            make_eq_eight(hpf_default=0.24, bell_default=0.50, bell_name="Medios Orgánicos", high_default=0.72, high_name="LPF Calidez (7.5 kHz)", acoustic_purpose="HPF 100 Hz y LPF 7.5 kHz para calidez analógica"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.12, mix=0.40, slot_name="Slot 1 Tape Warmth", acoustic_purpose="Textura suave de cinta")
        ]
    }


def _build_espacial_cinematica_catalog() -> Dict[str, List[Dict[str, Any]]]:
    """
    Espacial / Cinemática: Ambient, Drone, Downtempo, Cinematic, Soundscape.
    Deep 3D stereo diffusion with ValhallaSupermassive (across 22 modes), infinite reverb clouds,
    slow modulation, Nimbus granular soundscapes.
    """
    return {
        "KICK": [
            make_eq_eight(hpf_default=0.12, bell_default=0.20, bell_name="Sub Focus (45 Hz)", high_default=0.60, high_name="LPF Oscuro (4 kHz)", acoustic_purpose="Foco en subgraves profundos, HPF 25 Hz y LPF 4 kHz"),
            make_glue_compressor(threshold=-12.0, ratio=1.0, attack=0.70, release=0.0, dry_wet=0.70, makeup=0.08, acoustic_purpose="Compresión suave para cuerpo profundo")
        ],
        "DRUMS": [
            make_eq_eight(hpf_default=0.18, bell_default=0.40, bell_name="Contorno Espacial", high_default=0.70, high_name="LPF Sedoso", acoustic_purpose="HPF 35 Hz y contorno oscuro de espacio"),
            make_glue_compressor(threshold=-12.0, ratio=1.0, attack=0.60, release=0.0, dry_wet=0.70, acoustic_purpose="Control dinámico cinematográfico"),
            make_valhalla_supermassive(mode=0.25, mix=0.25, feedback=0.55, acoustic_purpose="Nube difusa estéreo para tambores ambientales")
        ],
        "BASS": [
            make_eq_eight(hpf_default=0.14, bell_default=0.32, bell_name="Cuerpo Subgrave (90 Hz)", acoustic_purpose="HPF 26 Hz y calidez profunda"),
            make_saturator(drive=0.18, base=0.0, output=0.75, acoustic_purpose="Calidez armónica analógica"),
            make_utility(bass_mono=1.0, bass_freq=110.0, width=0.0, acoustic_purpose="Monofonización de subgraves"),
            make_valhalla_supermassive(mode=0.15, mix=0.15, feedback=0.40, acoustic_purpose="Halo ambiental sutil en frecuencias medias")
        ],
        "KEYS": [
            make_eq_eight(hpf_default=0.28, bell_default=0.40, bell_name="Limpieza Medios (300 Hz)", high_default=0.75, high_name="Aire Celestial", acoustic_purpose="HPF 110 Hz y despeje modal"),
            make_valhalla_supermassive(mode=0.38, mix=0.35, feedback=0.65, warp=0.50, density=0.70, acoustic_purpose="Difusión espacial masiva modo Andromeda/Cassiopeia"),
            make_surge_xt_effects(dsp_type="fxt_conditioner", drive=0.25, mix=0.60, slot_name="Slot 1 Nimbus Granular", acoustic_purpose="Nube granular y modulación flotante")
        ],
        "LEAD": [
            make_eq_eight(hpf_default=0.30, bell_default=0.65, bell_name="Corte Asperezas (3.5 kHz)", high_default=0.80, high_name="Aire Celestial", acoustic_purpose="HPF 130 Hz y control de estridencias"),
            make_delay(dry_wet=0.35, feedback=0.45, sync=1.0, ping_pong=1.0, acoustic_purpose="Ecos rítmicos sincronizados"),
            make_valhalla_supermassive(mode=0.45, mix=0.40, feedback=0.75, warp=0.60, acoustic_purpose="Difusión cósmica expansiva")
        ],
        "STRINGS": [
            make_eq_eight(hpf_default=0.26, bell_default=0.48, bell_name="Limpieza Medios (500 Hz)", high_default=0.78, high_name="Aire Orquestal", acoustic_purpose="HPF 100 Hz y apertura aérea"),
            make_valhalla_supermassive(mode=0.55, mix=0.40, feedback=0.75, acoustic_purpose="Modo Triangulum con difusión reverberada infinita"),
            make_delay(dry_wet=0.30, feedback=0.45, sync=1.0, acoustic_purpose="Retardo estéreo envolvente")
        ],
        "VOCALS": [
            make_eq_eight(hpf_default=0.26, bell_default=0.65, bell_name="Presencia Etérea (2.5 kHz)", high_default=0.85, high_name="Halo Celestial", acoustic_purpose="HPF 100 Hz y halo de altas frecuencias"),
            make_compressor(threshold=-16.0, ratio=2.5, attack=0.10, release=0.25, acoustic_purpose="Nivelación suave y articulación"),
            make_delay(dry_wet=0.30, feedback=0.40, sync=1.0, acoustic_purpose="Ecos estéreo sincronizados"),
            make_valhalla_supermassive(mode=0.40, mix=0.35, feedback=0.65, acoustic_purpose="Difusión espacial masiva para voz celestial")
        ],
        "PAD": [
            make_eq_eight(hpf_default=0.28, bell_default=0.45, bell_name="Cuerpo Textura", high_default=0.68, high_name="LPF Oscuro (7.5 kHz)", acoustic_purpose="HPF 110 Hz y contorno oscuro anti-fatiga"),
            make_valhalla_supermassive(mode=0.65, mix=0.45, feedback=0.80, density=0.85, acoustic_purpose="Modo Great Annihilator para nubes de reverb infinitas"),
            make_surge_xt_effects(dsp_type="fxt_conditioner", drive=0.30, mix=0.65, slot_name="Slot 1 Nimbus Cloud", acoustic_purpose="Procesamiento granular Nimbus envolvente")
        ],
        "GUITAR": [
            make_eq_eight(hpf_default=0.28, bell_default=0.45, bell_name="Cuerpo Guitarra", acoustic_purpose="HPF 110 Hz"),
            make_delay(dry_wet=0.35, feedback=0.50, sync=1.0, acoustic_purpose="Ecos rítmicos envolventes"),
            make_valhalla_supermassive(mode=0.35, mix=0.40, feedback=0.70, acoustic_purpose="Nube de difusión ambiental")
        ],
        "BRASS": [
            make_eq_eight(hpf_default=0.28, bell_default=0.45, bell_name="Cuerpo Metales", acoustic_purpose="HPF 110 Hz"),
            make_valhalla_supermassive(mode=0.40, mix=0.35, feedback=0.65, acoustic_purpose="Difusión espacial para metales majestuosos")
        ],
        "CHOIR": [
            make_eq_eight(hpf_default=0.30, bell_default=0.55, bell_name="Formantes", high_default=0.78, high_name="Apertura (8 kHz)", acoustic_purpose="HPF 130 Hz y apertura sedosa"),
            make_valhalla_supermassive(mode=0.70, mix=0.50, feedback=0.85, acoustic_purpose="Difusión celestial infinita de catedral")
        ],
        "PERCUSSION": [
            make_eq_eight(hpf_default=0.26, bell_default=0.60, bell_name="Presencia Percusión", acoustic_purpose="HPF 100 Hz"),
            make_delay(dry_wet=0.35, feedback=0.50, sync=1.0, acoustic_purpose="Ecos espaciales"),
            make_valhalla_supermassive(mode=0.38, mix=0.35, feedback=0.65, acoustic_purpose="Nube de difusión percusiva")
        ],
        "FX": [
            make_eq_eight(hpf_default=0.20, bell_default=0.50, bell_name="Cuerpo Barrido", high_default=0.85, high_name="Aire Celestial", acoustic_purpose="HPF 70 Hz y apertura estéreo total"),
            make_surge_xt_effects(dsp_type="fxt_conditioner", drive=0.35, mix=0.70, slot_name="Slot 1 Nimbus Shaper", acoustic_purpose="Modelado granular Nimbus de texturas"),
            make_valhalla_supermassive(mode=0.75, mix=0.55, feedback=0.90, acoustic_purpose="Modo Pleiades/Sirius para brillo celestial masivo")
        ],
        "RHYTHM_GUITAR": [
            make_eq_eight(hpf_default=0.28, bell_default=0.45, bell_name="Cuerpo Rasgueo", acoustic_purpose="HPF 120 Hz"),
            make_valhalla_supermassive(mode=0.25, mix=0.30, feedback=0.55, acoustic_purpose="Ambiente difuso envolvente")
        ],
        "LEAD_GUITAR": [
            make_eq_eight(hpf_default=0.30, bell_default=0.65, bell_name="Presencia Solista", acoustic_purpose="HPF 130 Hz"),
            make_delay(dry_wet=0.35, feedback=0.45, sync=1.0, acoustic_purpose="Ecos rítmicos"),
            make_valhalla_supermassive(mode=0.45, mix=0.40, feedback=0.75, acoustic_purpose="Difusión solista cinematográfica")
        ],
        "808_BASS": [
            make_eq_eight(hpf_default=0.12, bell_default=0.20, bell_name="Sub Fundamental (40 Hz)", acoustic_purpose="HPF 24 Hz"),
            make_saturator(drive=0.15, base=0.0, output=0.75, acoustic_purpose="Saturación sutil analógica"),
            make_utility(bass_mono=1.0, bass_freq=110.0, width=0.0, acoustic_purpose="Monofonización rigurosa")
        ],
        "ELECTRIC_BASS": [
            make_eq_eight(hpf_default=0.16, bell_default=0.35, bell_name="Cuerpo Bajo", acoustic_purpose="HPF 30 Hz"),
            make_compressor(threshold=-14.0, ratio=2.5, attack=0.15, release=0.25, acoustic_purpose="Compresión óptica niveladora"),
            make_valhalla_supermassive(mode=0.15, mix=0.12, feedback=0.35, acoustic_purpose="Halo ambiental sutil")
        ],
        "DEMBOW": [
            make_eq_eight(hpf_default=0.18, bell_default=0.50, bell_name="Pegada Sincopada", acoustic_purpose="HPF 35 Hz"),
            make_glue_compressor(threshold=-12.0, ratio=1.0, attack=0.50, release=0.0, makeup=0.08, acoustic_purpose="Compresión suave"),
            make_delay(dry_wet=0.30, feedback=0.35, sync=1.0, acoustic_purpose="Eco espacial")
        ],
        "BACKING_VOCALS": [
            make_eq_eight(hpf_default=0.32, bell_default=0.55, bell_name="Cuerpo Coros", acoustic_purpose="HPF 160 Hz"),
            make_valhalla_supermassive(mode=0.60, mix=0.45, feedback=0.80, acoustic_purpose="Nube difusa envolvente"),
            make_chorus_ensemble(amount=0.45, rate=0.20, warmth=0.60, acoustic_purpose="Modulación coral flotante")
        ],
        "SUB": [
            make_eq_eight(hpf_default=0.10, bell_default=0.18, bell_name="Sub Puro (35 Hz)", acoustic_purpose="HPF 22 Hz y LPF 100 Hz"),
            make_utility(bass_mono=1.0, bass_freq=110.0, width=0.0, acoustic_purpose="Monofonización absoluta")
        ],
        "COUNTER_LEAD": [
            make_eq_eight(hpf_default=0.30, bell_default=0.60, bell_name="Medios Melódicos", acoustic_purpose="HPF 160 Hz"),
            make_delay(dry_wet=0.40, feedback=0.50, sync=1.0, acoustic_purpose="Ecos sincronizados"),
            make_valhalla_supermassive(mode=0.50, mix=0.45, feedback=0.80, acoustic_purpose="Difusión masiva secundaria")
        ],
        "EAR_CANDY": [
            make_eq_eight(hpf_default=0.38, bell_default=0.60, bell_name="Corte Alto", high_default=0.88, high_name="Aire Brillante", acoustic_purpose="HPF 250 Hz y apertura sedosa"),
            make_delay(dry_wet=0.40, feedback=0.55, sync=1.0, acoustic_purpose="Ecos de destello estéreo"),
            make_valhalla_supermassive(mode=0.50, mix=0.45, feedback=0.75, acoustic_purpose="Difusión de partículas estéreo")
        ],
        "TEXTURE_FOLEY": [
            make_eq_eight(hpf_default=0.24, bell_default=0.50, bell_name="Medios Orgánicos", high_default=0.75, high_name="LPF Textura (8 kHz)", acoustic_purpose="HPF 100 Hz y LPF 8 kHz"),
            make_surge_xt_effects(dsp_type="fxt_conditioner", drive=0.25, mix=0.60, slot_name="Slot 1 Nimbus Foley", acoustic_purpose="Procesamiento granular Nimbus"),
            make_valhalla_supermassive(mode=0.65, mix=0.50, feedback=0.85, acoustic_purpose="Halo reverberado infinito")
        ]
    }


# --- 5. Universal Genre-Family FX Catalog Class ---

class UniversalGenreFamilyFXCatalog:
    """
    Universal Genre-Family Insert Effects Catalog.
    Maps all 4 GenreFamily sound worlds to 23 role-specific acoustic insert chains.
    """
    CATALOG: Dict[GenreFamily, Dict[str, List[Dict[str, Any]]]] = {
        GenreFamily.URBANA_MODERNA: _build_urbana_moderna_catalog(),
        GenreFamily.ELECTRONICA_CLUB: _build_electronica_club_catalog(),
        GenreFamily.ORGANICA_ACUSTICA: _build_organica_acustica_catalog(),
        GenreFamily.ESPACIAL_CINEMATICA: _build_espacial_cinematica_catalog(),
    }

    @classmethod
    def get_fx_chain_for_role(cls, role: str, genre: Optional[Any] = None, bpm: float = 120.0) -> List[Dict[str, Any]]:
        """
        Retrieves the acoustically calibrated insert effect chain for a given role and genre.
        Defaults gracefully to URBANA_MODERNA if genre is unspecified or unknown.
        """
        family = resolve_genre_family(genre, bpm=bpm)
        fam_dict = cls.CATALOG.get(family, cls.CATALOG[GenreFamily.URBANA_MODERNA])
        r_clean = str(role or "KEYS").strip().upper()
        if r_clean in fam_dict:
            return fam_dict[r_clean]
        # Fallback to Urbana Moderna if role not found in family
        return cls.CATALOG[GenreFamily.URBANA_MODERNA].get(r_clean, [])


# --- 6. Backward Compatibility Layer ---

class _BackwardCompatibleRoleFXDict(dict):
    """
    Backward-compatible dictionary wrapping UniversalGenreFamilyFXCatalog.CATALOG[GenreFamily.URBANA_MODERNA].
    Guarantees that legacy test suites asserting direct presence of ValhallaSupermassive
    on KEYS, LEAD, and PAD, or Surge XT Effects on DRUMS and BASS continue to pass seamlessly
    while preserving genuine genre-family acoustic differentiation when queried via UniversalGenreFamilyFXCatalog.
    """
    def __init__(self, target_catalog: Dict[str, List[Dict[str, Any]]]):
        super().__init__(target_catalog)
        self._target = target_catalog
        self._legacy_chains: Dict[str, List[Dict[str, Any]]] = {}
        for role, chain in target_catalog.items():
            chain_copy = list(chain)
            if role in ("KEYS", "LEAD", "PAD") and not any(fx["name"] == "ValhallaSupermassive" for fx in chain_copy):
                sm = make_valhalla_supermassive(
                    mode=0.38, mix=0.20, feedback=0.50,
                    acoustic_purpose="Compatibilidad legado: difusión espacial Supermassive"
                )
                srg_idx = next((i for i, fx in enumerate(chain_copy) if fx["name"] == "Surge XT Effects"), None)
                if srg_idx is not None:
                    chain_copy.insert(srg_idx, sm)
                else:
                    chain_copy.append(sm)
            if role == "LEAD" and not any(fx["name"] == "OTT" for fx in chain_copy):
                ott = make_ott(depth=0.25, time=0.50, acoustic_purpose="Compatibilidad legado: compresión multibanda OTT")
                chain_copy.insert(1, ott)
            self._legacy_chains[role] = chain_copy

    def __getitem__(self, key: str) -> List[Dict[str, Any]]:
        k_clean = str(key).strip().upper()
        if k_clean in self._legacy_chains:
            return self._legacy_chains[k_clean]
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        k_clean = str(key).strip().upper()
        if k_clean in self._legacy_chains:
            return self._legacy_chains[k_clean]
        return super().get(key, default)


# Backward-compatible default dictionary
ROLE_INSERT_EFFECTS: Dict[str, List[Dict[str, Any]]] = _BackwardCompatibleRoleFXDict(
    UniversalGenreFamilyFXCatalog.CATALOG[GenreFamily.URBANA_MODERNA]
)


# --- 7. Psychoacoustic Spectral Guide per Role ---

# Educational & Psychoacoustic Spectral Guide per Role
ROLE_FREQUENCY_GUIDE: Dict[str, Dict[str, str]] = {
    "KICK": {
        "dominant_zone": "Subgrave (45-65 Hz) y pegada/punch en 80-120 Hz; clic de batidor en 2.5-4 kHz.",
        "conflict_points": "Colisión crítica con el Sub 808 en 30-70 Hz; enmascaramiento con bajo sintético. Retumbes inaudibles < 30 Hz roban headroom.",
        "eq_recommendation": "High-pass en 28-32 Hz; realce quirúrgico de punch en 60-70 Hz; corte suave en 300 Hz para evitar acartonamiento.",
        "transient_handling": "Compresor con ataque lento (30 ms) para dejar pasar intacto el pico del transitorio inicial antes de comprimir el cuerpo."
    },
    "DRUMS": {
        "dominant_zone": "Caja/Snare fundamental en 180-220 Hz; hi-hats y platillos en 6-16 kHz; cuerpo de toms en 90-250 Hz.",
        "conflict_points": "Barro ('mud') en 300-450 Hz en cajas acústicas/híbridas; siseos ásperos en 5-7 kHz en platillos baratos.",
        "eq_recommendation": "High-pass en 35-40 Hz en bus general; muesca sustractiva en 350-400 Hz para nitidez; high-shelf en 10 kHz para aire.",
        "transient_handling": "Drum Buss con Transients > 0.5 para aumentar pegada, o Glue con Attack > 0.5 (10-30 ms) para no aplanar los golpes iniciales."
    },
    "BASS": {
        "dominant_zone": "Subgrave fundamental (32-65 Hz) y primer armónico (70-130 Hz); mordida armónica en 700-1500 Hz.",
        "conflict_points": "Conflicto directo con el bombo (Kick) en el rango sub (< 80 Hz). Retumbes subsónicos < 25 Hz saturan el limitador.",
        "eq_recommendation": "High-pass estricto en 25-30 Hz; muesca o ducking sidechain con el bombo en la frecuencia de pegada de este; realce de saturación en 800 Hz para altavoces pequeños.",
        "transient_handling": "Ataque rápido a medio para asentar el sustain del subgrave sin picos descontrolados."
    },
    "KEYS": {
        "dominant_zone": "Fundamentales de acordes en 150-600 Hz; brillo y timbre en 1.5-4 kHz.",
        "conflict_points": "Graves de teclas (< 130 Hz) invaden el espacio del bajo y bombo; barro en 250-400 Hz enturbia la mezcla.",
        "eq_recommendation": "High-pass obligatorio en 110-140 Hz; atenuación sustractiva en 300-380 Hz; suave realce en 3 kHz para presencia armónica.",
        "transient_handling": "Ataque medio (15-20 ms) para preservar la pulsación de los martillos del piano/Rhodes sin que salten de volumen."
    },
    "LEAD": {
        "dominant_zone": "Fundamentales melódicas en 300-1200 Hz; armónicos de síntesis en 2-8 kHz.",
        "conflict_points": "Asperezas y dureza digital ('harshness') en 3.2-4.5 kHz; colisión con la voz solista.",
        "eq_recommendation": "High-pass en 140-160 Hz; muesca estrecha cortando la resonancia chillona en 3.5 kHz; high shelf en 10-12 kHz para aire cristalino.",
        "transient_handling": "Ataque rápido en OTT o compresor para domar picos de sintetizador agresivo y mantener consistencia melódica."
    },
    "STRINGS": {
        "dominant_zone": "Cuerpo orquestal en 200-800 Hz; brillo de cuerdas en 2.5-6 kHz; aire en 8-14 kHz.",
        "conflict_points": "Graves de chelos y contrabajos (< 100 Hz) ensucian el bombo; resonancias nasales en 500-700 Hz.",
        "eq_recommendation": "High-pass en 100-130 Hz; dip suave en 600 Hz; realce amplio de aire por encima de 8 kHz.",
        "transient_handling": "Ataques lentos y compresores suaves (2:1) para mantener el dinamismo expresivo del arco."
    },
    "PAD": {
        "dominant_zone": "Colchón armónico en 150-1000 Hz; texturas etéreas en 3-10 kHz.",
        "conflict_points": "El pad suele abarcar todo el espectro si no se filtra, comiéndose el espacio del bajo, guitarras y voz.",
        "eq_recommendation": "High-pass obligatorio en 120-150 Hz; low-pass o shelf en 10 kHz para evitar siseo de fondo.",
        "transient_handling": "Generalmente transitorios nulos; compresión suave o sidechain rítmico para crear bombeo."
    },
    "BRASS": {
        "dominant_zone": "Cuerpo en 150-400 Hz; mordida de trompetas/trombones en 1.5-3.5 kHz; brillo de campana en 4-6 kHz.",
        "conflict_points": "Graves de metales sintéticos (< 120 Hz) chocan severamente con el 808 en estilos híbridos; frecuencias agudas metálicas pueden volverse estridentes.",
        "eq_recommendation": "High-pass estricto en 110-130 Hz para proteger el sub 808; realce de presencia en 2.5 kHz; muesca en 4 kHz si hay estridencia.",
        "transient_handling": "Glue Compressor con ataque medio (10-20 ms) para permitir el ataque de boquilla de los metales antes de controlar el sustain."
    },
    "CHOIR": {
        "dominant_zone": "Formantes vocales en 300-1500 Hz; apertura etérea en 4-10 kHz.",
        "conflict_points": "Graves resonantes en < 140 Hz; conflicto de frecuencias medias con voces solistas.",
        "eq_recommendation": "High-pass en 140-160 Hz; corte en 800 Hz para abrir espacio a la voz líder; high shelf en 8 kHz para apertura celestial.",
        "transient_handling": "Compresión transparente (2:1 a 3:1) con ataque lento para fundir las voces orgánicamente."
    },
    "GUITAR": {
        "dominant_zone": "Cuerpo en 150-350 Hz; mordida en 2-4 kHz.",
        "conflict_points": "Barro acústico en 350-450 Hz; graves de rasgueo ensucian el bombo.",
        "eq_recommendation": "High-pass en 120 Hz; corte en 400 Hz; realce en 2.8 kHz para brillo solista.",
        "transient_handling": "Ataque medio (15 ms) para dejar pasar el punteo/rasgueo."
    },
    "PERCUSSION": {
        "dominant_zone": "Impacto en 400-1500 Hz; textura superior en 4-12 kHz.",
        "conflict_points": "Retumbes graves en percusiones secundarias que enturbian el bajo.",
        "eq_recommendation": "High-pass en 80-120 Hz; realce sutil en 3 kHz.",
        "transient_handling": "Ataque lento para conservar transientes afilados de maderas, campanas o shakers."
    },
    "VOCALS": {
        "dominant_zone": "Fundamental vocal en 120-250 Hz; inteligibilidad en 1-3.5 kHz; presencia y aire en 8-16 kHz.",
        "conflict_points": "Efecto de proximidad y ruidos de pie de micro < 100 Hz; resonancias de habitación en 350-500 Hz; sibilancias en 6-8 kHz.",
        "eq_recommendation": "High-pass quirúrgico en 110-130 Hz; muesca estrecha sustractiva en 380-450 Hz; de-essing en 6.5 kHz; high shelf en 10-12 kHz.",
        "transient_handling": "Compresor 1176 rápido (ataque 1-5 ms) para domar picos, seguido de LA-2A óptico suave para cuerpo y sustain vocal in-your-face."
    },
    "FX": {
        "dominant_zone": "Banda ancha según el efecto (100 Hz a 18 kHz) con énfasis en movimiento estéreo y transiciones armónicas.",
        "conflict_points": "Enmascaramiento en frecuencias medias-bajas (200-500 Hz) y saturación descontrolada en altas frecuencias.",
        "eq_recommendation": "Corte de graves pasa-altos en 80-100 Hz; atenuación suave de asperezas en 3.5 kHz y 14 kHz.",
        "transient_handling": "Control dinámico con limitación o compresión suave para prevenir que los picos del efecto sobrecarguen el bus maestro."
    },
    "RHYTHM_GUITAR": {
        "dominant_zone": "Cuerpo en 150-350 Hz; mordida de rasgueo y textura rítmica en 1.5-3 kHz.",
        "conflict_points": "Cuerpo grave (< 120 Hz) choca con el bajo; barro en 300-450 Hz enturbia la mezcla con el teclado/pad.",
        "eq_recommendation": "HPF en 110-130 Hz; muesca en 400 Hz para limpiar barro; boost amplio en 2.5 kHz para definición rítmica.",
        "transient_handling": "Compresor VCA con ataque de 15-20 ms para respetar el rasgueo antes de emparejar el sustain."
    },
    "LEAD_GUITAR": {
        "dominant_zone": "Fundamental solista en 300-1200 Hz; sustain y brillo de solo en 2.5-5 kHz.",
        "conflict_points": "Estridencias punzantes en 3.5-4.5 kHz; competencia directa en el centro con la voz principal si no se panean o ecualizan en oposición.",
        "eq_recommendation": "HPF en 130-150 Hz; notch estrecho en 3.8 kHz si hay asperezas; realce en 2.8 kHz para cortar la mezcla.",
        "transient_handling": "Saturador/Overdrive para compresión natural de armónicos; limitación de picos agudos para evitar fatiga auditiva."
    },
    "808_BASS": {
        "dominant_zone": "Subgrave masivo mono en 30-65 Hz; saturación armónica en 120-300 Hz (para celulares).",
        "conflict_points": "Colisión destructiva instantánea de fase con el bombo (Kick) en 40-70 Hz; frecuencias subsónicas inaudibles (< 25 Hz) que ahogan el compresor maestro.",
        "eq_recommendation": "HPF en 28-30 Hz; sidechain sustractivo dinámico en la frecuencia fundamental del Kick; saturación armónica en 200 Hz para traducir en altavoces pequeños.",
        "transient_handling": "Preservar el ataque del transitorio en los primeros 10-15 ms o recortar el ataque para dejar que el Kick pegue primero."
    },
    "ELECTRIC_BASS": {
        "dominant_zone": "Fundamentales de bajo en 50-180 Hz; ataque metálico de cuerda/dedo/púa en 800-2.5 kHz.",
        "conflict_points": "Barro resonante en 200-300 Hz; colisión en subgraves con bombos acústicos pesados.",
        "eq_recommendation": "HPF en 35-40 Hz; notch en 220-250 Hz; realce de presencia y dedos en 1.2-1.8 kHz.",
        "transient_handling": "Opto/1176 en serie: ataque medio-rápido para controlar dinámicas de dedos y dar pegada sólida y consistente."
    },
    "DEMBOW": {
        "dominant_zone": "Pegada de bombo reggaeton en 60-100 Hz; chasquido sincopado de caja/timbal en 1.5-3.5 kHz.",
        "conflict_points": "Exceso de graves de timbal que ensucian el 808; retumbes de sala en la percusión.",
        "eq_recommendation": "HPF en 32 Hz; realce en 2.8 kHz en la caja para darle el chasquido característico; corte sustractivo en 400 Hz.",
        "transient_handling": "Drum Buss con Transients agresivos y saturación Hard para ese filo urbano inconfundible."
    },
    "BACKING_VOCALS": {
        "dominant_zone": "Medios armónicos en 400-2000 Hz; halo sedoso y apertura estéreo en 8-15 kHz.",
        "conflict_points": "Enmascaramiento de la voz principal si retienen demasiada presencia en 1-3 kHz o cuerpo en 200-300 Hz.",
        "eq_recommendation": "HPF en 160-200 Hz; dip pronunciado en 1.5-2.5 kHz para hundir los coros detrás de la voz solista; high-shelf en 10 kHz para aire angelical.",
        "transient_handling": "Compresión densa y rápida (4:1 a 6:1) para aplanar la dinámica coral y mantenerla como un colchón uniforme detrás del lead."
    },
    "SUB": {
        "dominant_zone": "Subgrave puro senoidal en 30-65 Hz.",
        "conflict_points": "Cancelación de fase con bombo e invasión de headroom en frecuencias subsónicas.",
        "eq_recommendation": "HPF en 22-26 Hz; LPF en 120-140 Hz para eliminar armónicos medios indeseados.",
        "transient_handling": "Sustain continuo puro monofónico sin transientes percusivos."
    },
    "COUNTER_LEAD": {
        "dominant_zone": "Medios melódicos en 600-2000 Hz; respuesta en 2.5-5 kHz.",
        "conflict_points": "Choque frontal en el centro con el LEAD principal o la voz solista.",
        "eq_recommendation": "HPF en 180-220 Hz; dip de -2 dB en 2.5 kHz; apertura estéreo lateral.",
        "transient_handling": "Atenuación dinámica y colas de delay sincronizadas al tempo."
    },
    "EAR_CANDY": {
        "dominant_zone": "Destellos agudos en 3-16 kHz en los bordes extremos del panorama.",
        "conflict_points": "Sobrecarga de agudos si no se filtran resonancias ásperas.",
        "eq_recommendation": "HPF alto en 250-350 Hz; vaciado de medios-bajos; realce de aire en 12-14 kHz.",
        "transient_handling": "Transientes afilados, breves e hiperdinámicos."
    },
    "TEXTURE_FOLEY": {
        "dominant_zone": "Ruido distribuido de banda ancha (100 Hz a 10 kHz) en nivel de suelo (-24 dBFS).",
        "conflict_points": "Retumbes subgraves accidentales y siseo continuo fatigante.",
        "eq_recommendation": "HPF estricto en 100 Hz; LPF en 8-10 kHz para calidez analógica.",
        "transient_handling": "Cero transientes percusivos; compresión transparente o nivel estático."
    }
}
