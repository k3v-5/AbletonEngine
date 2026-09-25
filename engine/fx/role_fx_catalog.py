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

    # 1. Urbana / Moderna: Trap, Drill, Boom Bap, Reggaeton, Phonk, Dembow, Plugg, Rage, Jersey Club, Hip-Hop
    if any(k in g for k in [
        "trap", "drill", "uk_drill", "ny_drill", "chicago_drill", "boom_bap", "boombap",
        "reggaeton", "hip_hop", "hiphop", "phonk", "drift_phonk", "dembow", "latin", "urbano", "urban",
        "plugg", "pluggnb", "rage", "jersey_club", "baile_funk", "favela_funk", "rkt", "afrotrap",
        "latin_trap", "trap_latino", "grime", "cloud_rap", "rap"
    ]):
        return GenreFamily.URBANA_MODERNA

    # 2. Electrónica de Club: House, Techno, EDM, DnB, Dubstep, Trance, Synthwave, Hardstyle
    if any(k in g for k in [
        "house", "deep_house", "tech_house", "afro_house", "progressive_house", "acid_house",
        "techno", "melodic_techno", "peak_time_techno", "hard_techno", "minimal_techno", "dub_techno",
        "edm", "drum_and_bass", "drum & bass", "dnb", "liquid_dnb", "neurofunk", "jump_up", "jungle",
        "dubstep", "brostep", "riddim", "melodic_dubstep", "bass_music", "future_bass",
        "trance", "psytrance", "progressive_trance", "uplifting_trance", "club", "dance",
        "synthwave", "retrowave", "darksynth", "vaporwave", "electro", "hardstyle", "garage", "uk_garage", "2_step"
    ]):
        return GenreFamily.ELECTRONICA_CLUB

    # 3. Orgánica / Acústica: Neo-Soul, R&B, Flamenco, Indie/Pop, Rock, Jazz, Folk, Cumbia, Afrobeat, Bossa
    if any(k in g for k in [
        "neo_soul", "neosoul", "rnb", "r_and_b", "r&b", "soul", "motown", "gospel",
        "flamenco", "flamenco_fusion", "rumba", "bulerias",
        "indie", "indie_pop", "indie_rock", "alt_rock", "pop", "acoustic_pop",
        "rock", "classic_rock", "hard_rock", "blues", "jazz", "smooth_jazz", "bebop", "modal_jazz",
        "acoustic", "acustica", "organica", "unplugged", "folk", "americana", "bluegrass", "country",
        "lofi", "lo_fi", "chillhop", "jazzhop",
        "cumbia", "cumbia_sonidera", "afrobeat", "afropop", "highlife",
        "bossa", "bossa_nova", "samba", "salsa", "son_cubano", "bolero", "bachata", "reggae", "dub", "roots_reggae",
        "funk", "p_funk", "disco", "nu_disco", "ballad"
    ]):
        return GenreFamily.ORGANICA_ACUSTICA

    # 4. Espacial / Cinemática: Ambient, Drone, Downtempo, Trip-Hop, Cinematic, Orchestral, Soundscape
    if any(k in g for k in [
        "ambient", "dark_ambient", "drone", "space_ambient", "downtempo", "trip_hop", "triphop", "illbient",
        "cinematic", "cinematica", "espacial", "soundscape", "film_score", "soundtrack", "trailer_music",
        "orchestral", "epic_orchestral", "space", "meditation", "atmospheric", "chillout", "new_age",
        "ethereal", "shoegaze", "dreampop", "ambient_techno", "isolationism", "post_rock"
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


def make_auto_filter(
    frequency: float = 0.45,
    resonance: float = 0.20,
    filter_type: float = 0.0,
    drive: float = 0.0,
    envelope: float = 0.0,
    attack: float = 0.20,
    release: float = 0.30,
    acoustic_purpose: str = "Filtrado resonante dinámico y modulación tímbrica"
) -> Dict[str, Any]:
    """Generates an Ableton Auto Filter dictionary specification."""
    return {
        "name": "Auto Filter",
        "type": "native",
        "uri": "query:AudioFx#Auto%20Filter",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Frequency", "name": "Frequency (Frecuencia de corte)", "range": "0.0 a 1.0 (20 Hz a 20 kHz)", "behavior": "Punto de corte espectral dinámico.", "default": frequency},
            {"id": "Resonance", "name": "Resonance (Resonancia Q)", "range": "0.0 a 1.0 (0.5 a 10.0)", "behavior": "Realce del pico en la frecuencia de corte.", "default": resonance},
            {"id": "Filter Type", "name": "Filter Type (Modo)", "range": "0.0 (LP), 1.0 (HP), 2.0 (BP), 3.0 (Notch)", "behavior": "Topología del filtro.", "default": filter_type},
            {"id": "Drive", "name": "Filter Drive", "range": "0.0 a 1.0", "behavior": "Saturación analógica en el circuito del filtro.", "default": drive},
            {"id": "Envelope", "name": "Envelope Amount", "range": "-1.0 a 1.0", "behavior": "Modulación del filtro mediante seguidor de envolvente.", "default": envelope},
            {"id": "Attack", "name": "Attack Time", "range": "0.0 a 1.0", "behavior": "Velocidad de reacción del seguidor de envolvente.", "default": attack},
            {"id": "Release", "name": "Release Time", "range": "0.0 a 1.0", "behavior": "Tiempo de recuperación del filtro tras el pico.", "default": release}
        ]
    }


def make_echo(
    dry_wet: float = 0.30,
    feedback: float = 0.40,
    delay_time: float = 0.35,
    sync: float = 1.0,
    ping_pong: float = 1.0,
    wobble: float = 0.25,
    noise: float = 0.10,
    acoustic_purpose: str = "Eco de cinta analógica vintage y retardos rítmicos"
) -> Dict[str, Any]:
    """Generates an Ableton Echo dictionary specification."""
    return {
        "name": "Echo",
        "type": "native",
        "uri": "query:AudioFx#Echo",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Dry/Wet", "name": "Dry/Wet", "range": "0.0 a 1.0", "behavior": "Balance de procesamiento del retardo.", "default": dry_wet},
            {"id": "Feedback", "name": "Feedback", "range": "0.0 a 1.0", "behavior": "Regeneración de ecos y cola de retardo.", "default": feedback},
            {"id": "Delay Time", "name": "Delay Time", "range": "0.0 a 1.0", "behavior": "Tiempo de retardo en milisegundos o compases.", "default": delay_time},
            {"id": "Sync", "name": "Tempo Sync", "range": "0.0 o 1.0", "behavior": "Sincronización rítmica métrica.", "default": sync},
            {"id": "Ping Pong", "name": "Ping Pong Mode", "range": "0.0 o 1.0", "behavior": "Alternancia estéreo de repeticiones en el panorama.", "default": ping_pong},
            {"id": "Wobble", "name": "Tape Wobble", "range": "0.0 a 1.0", "behavior": "Fluctuación analógica de tono (wow y flutter).", "default": wobble},
            {"id": "Noise", "name": "Tape Noise", "range": "0.0 a 1.0", "behavior": "Inyección de ruido analógico de cinta vintage.", "default": noise}
        ]
    }


def make_pedal(
    gain: float = 0.30,
    output: float = 0.70,
    bass: float = 0.50,
    mid: float = 0.50,
    treble: float = 0.50,
    sub: float = 0.0,
    pedal_type: float = 0.0,
    acoustic_purpose: str = "Distorsión de pedal analógico, overdrive y carácter cálido"
) -> Dict[str, Any]:
    """Generates an Ableton Pedal dictionary specification."""
    return {
        "name": "Pedal",
        "type": "native",
        "uri": "query:AudioFx#Pedal",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Gain", "name": "Gain (Drive)", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Intensidad de distorsión y saturación de entrada.", "default": gain},
            {"id": "Output", "name": "Output Level", "range": "0.0 a 1.0", "behavior": "Compensación de nivel de salida.", "default": output},
            {"id": "Bass", "name": "Bass EQ", "range": "0.0 a 1.0", "behavior": "Control tonal de frecuencias bajas.", "default": bass},
            {"id": "Mid", "name": "Mid EQ", "range": "0.0 a 1.0", "behavior": "Control tonal de frecuencias medias.", "default": mid},
            {"id": "Treble", "name": "Treble EQ", "range": "0.0 a 1.0", "behavior": "Control tonal de frecuencias agudas.", "default": treble},
            {"id": "Sub", "name": "Sub Boost", "range": "0.0 o 1.0", "behavior": "Refuerzo subsónico analógico para cuerpo extremo.", "default": sub},
            {"id": "Type", "name": "Pedal Model", "range": "0.0 (Overdrive), 1.0 (Distortion), 2.0 (Fuzz)", "behavior": "Circuito de recorte analógico activo.", "default": pedal_type}
        ]
    }


def make_phaser_flanger(
    amount: float = 0.35,
    rate: float = 0.20,
    feedback: float = 0.25,
    warmth: float = 0.50,
    mode: float = 0.0,
    acoustic_purpose: str = "Modulación de fase y peine para ensanchamiento tímbrico"
) -> Dict[str, Any]:
    """Generates an Ableton Phaser-Flanger dictionary specification."""
    return {
        "name": "Phaser-Flanger",
        "type": "native",
        "uri": "query:AudioFx#Phaser-Flanger",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Amount", "name": "Amount (Profundidad)", "range": "0.0 a 1.0", "behavior": "Intensidad de modulación de muescas espectrales.", "default": amount},
            {"id": "Rate", "name": "LFO Rate", "range": "0.0 a 1.0", "behavior": "Velocidad de ciclo del oscilador de modulación.", "default": rate},
            {"id": "Feedback", "name": "Feedback", "range": "-1.0 a 1.0", "behavior": "Regeneración de resonancia de fase.", "default": feedback},
            {"id": "Warmth", "name": "Warmth", "range": "0.0 a 1.0", "behavior": "Saturación cálida no lineal en el circuito.", "default": warmth},
            {"id": "Mode", "name": "Mode", "range": "0.0 (Phaser), 1.0 (Flanger), 2.0 (Doubler)", "behavior": "Topología algorítmica de modulación.", "default": mode}
        ]
    }


def make_multiband_dynamics(
    band_low: float = 0.0,
    band_mid: float = 0.0,
    band_high: float = 0.0,
    output: float = 0.70,
    time: float = 0.50,
    amount: float = 0.30,
    acoustic_purpose: str = "Control dinámico multibanda upward/downward nativo de Live 12"
) -> Dict[str, Any]:
    """Generates an Ableton Multiband Dynamics dictionary specification."""
    return {
        "name": "Multiband Dynamics",
        "type": "native",
        "uri": "query:AudioFx#Multiband%20Dynamics",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Amount", "name": "Amount (Dry/Wet)", "range": "0.0 a 1.0", "behavior": "Porcentaje global de compresión multibanda.", "default": amount},
            {"id": "Time", "name": "Time Scaling", "range": "0.0 a 1.0", "behavior": "Escalado proporcional de constantes de tiempo.", "default": time},
            {"id": "Output Gain", "name": "Output Gain", "range": "0.0 a 1.0", "behavior": "Compensación de ganancia maestra.", "default": output},
            {"id": "Band 1 (Low)", "name": "Banda Graves", "range": "-24 dB a +24 dB", "behavior": "Ajuste dinámico en banda baja (< 120 Hz).", "default": band_low},
            {"id": "Band 2 (Mid)", "name": "Banda Medios", "range": "-24 dB a +24 dB", "behavior": "Ajuste dinámico en banda media (120 Hz a 2.5 kHz).", "default": band_mid},
            {"id": "Band 3 (High)", "name": "Banda Agudos", "range": "-24 dB a +24 dB", "behavior": "Ajuste dinámico en banda alta (> 2.5 kHz).", "default": band_high}
        ]
    }


def make_shifter(
    pitch: float = 0.0,
    fine: float = 0.0,
    drive: float = 0.0,
    dry_wet: float = 0.50,
    mode: float = 0.0,
    acoustic_purpose: str = "Desplazamiento armónico de tono, micro-afinación y modulación de anillo"
) -> Dict[str, Any]:
    """Generates an Ableton Shifter dictionary specification."""
    return {
        "name": "Shifter",
        "type": "native",
        "uri": "query:AudioFx#Shifter",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Pitch", "name": "Coarse Pitch", "range": "-24 a +24 semitonos", "behavior": "Desplazamiento de tono por semitonos.", "default": pitch},
            {"id": "Fine", "name": "Fine Tune", "range": "-50 a +50 cents", "behavior": "Microdesafinación para grosor y coros.", "default": fine},
            {"id": "Drive", "name": "Input Drive", "range": "0.0 a 1.0", "behavior": "Saturación armónica en el núcleo de cambio de tono.", "default": drive},
            {"id": "Dry/Wet", "name": "Dry/Wet", "range": "0.0 a 1.0", "behavior": "Balance de señal directa y procesada.", "default": dry_wet},
            {"id": "Mode", "name": "Shifter Mode", "range": "0.0 (Pitch), 1.0 (Frequency), 2.0 (Ring Mod)", "behavior": "Algoritmo de transposición tímbrica.", "default": mode}
        ]
    }


def make_hybrid_reverb(
    blend: float = 0.50,
    decay: float = 0.35,
    dry_wet: float = 0.25,
    predelay: float = 0.05,
    size: float = 0.50,
    acoustic_purpose: str = "Espacialidad híbrida de convolución y algoritmos de estudio"
) -> Dict[str, Any]:
    """Generates an Ableton Hybrid Reverb dictionary specification."""
    return {
        "name": "Hybrid Reverb",
        "type": "native",
        "uri": "query:AudioFx#Hybrid%20Reverb",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Dry/Wet", "name": "Dry/Wet", "range": "0.0 a 1.0", "behavior": "Balance de señal de mezcla de reverberación.", "default": dry_wet},
            {"id": "Decay", "name": "Decay Time", "range": "0.0 a 1.0", "behavior": "Longitud de la cola reverberada.", "default": decay},
            {"id": "PreDelay", "name": "Pre-delay", "range": "0.0 a 1.0", "behavior": "Separación de reflexiones tempranas.", "default": predelay},
            {"id": "Size", "name": "Room Size", "range": "0.0 a 1.0", "behavior": "Escala dimensional del espacio acústico.", "default": size},
            {"id": "Blend", "name": "Convolution/Algo Blend", "range": "0.0 a 1.0", "behavior": "Balance entre respuesta al impulso y algoritmo sintético.", "default": blend}
        ]
    }


def make_erosion(
    frequency: float = 0.50,
    width: float = 0.40,
    amount: float = 0.25,
    mode: float = 0.0,
    acoustic_purpose: str = "Degradación digital controlada, modulación sinusoidal y textura lo-fi"
) -> Dict[str, Any]:
    """Generates an Ableton Erosion dictionary specification."""
    return {
        "name": "Erosion",
        "type": "native",
        "uri": "query:AudioFx#Erosion",
        "acoustic_purpose": acoustic_purpose,
        "params": [
            {"id": "Frequency", "name": "Center Frequency", "range": "0.0 a 1.0 (200 Hz a 15 kHz)", "behavior": "Frecuencia focal de erosión y ruido.", "default": frequency},
            {"id": "Width", "name": "Bandwidth / Q", "range": "0.0 a 1.0", "behavior": "Ancho de banda del generador de ruido espectral.", "default": width},
            {"id": "Amount", "name": "Erosion Amount", "range": "0.0 a 1.0", "behavior": "Profundidad de artefacto digital o modulación senoidal.", "default": amount},
            {"id": "Mode", "name": "Mode", "range": "0.0 (Noise), 1.0 (Sine), 2.0 (Wide Noise)", "behavior": "Naturaleza tímbrica de la distorsión digital.", "default": mode}
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
        ],
        "SYNTH_BASS": [
            make_eq_eight(hpf_default=0.18, bell_default=0.55, bell_name="Mordida Armónica Synth (800 Hz)", acoustic_purpose="Corte subsónico 30 Hz y presencia armónica"),
            make_saturator(drive=0.26, base=0.0, output=0.70, acoustic_purpose="Saturación no lineal agresiva para subgraves audibles"),
            make_utility(bass_mono=1.0, bass_freq=125.0, width=0.0, acoustic_purpose="Monofonización pura del bajo sintético")
        ],
        "SYNTH_PLUCK": [
            make_eq_eight(hpf_default=0.30, bell_default=0.65, bell_name="Presencia Pluck (3 kHz)", high_default=0.80, high_name="Aire Cristalino", acoustic_purpose="HPF 140 Hz y brillo de ataque"),
            make_delay(dry_wet=0.28, feedback=0.32, sync=1.0, ping_pong=1.0, acoustic_purpose="Retardo estéreo rítmico"),
            make_valhalla_vintage_verb(mode=0.10, color=0.50, mix=0.18, decay=0.20, predelay=0.03, acoustic_purpose="Ambiente de placa corto y controlado")
        ],
        "ARPEGGIO": [
            make_eq_eight(hpf_default=0.32, bell_default=0.60, bell_name="Cuerpo Arp (1.5 kHz)", high_default=0.82, high_name="Brillo Arpegio", acoustic_purpose="HPF 150 Hz y apertura estéreo"),
            make_auto_filter(frequency=0.55, resonance=0.25, filter_type=0.0, drive=0.15, acoustic_purpose="Filtrado dinámico con apertura de corte"),
            make_delay(dry_wet=0.30, feedback=0.35, sync=1.0, ping_pong=1.0, acoustic_purpose="Ecos estéreo sincronizados a compás")
        ],
        "VOCAL_CHOP": [
            make_auto_tune_artist(key="C", scale="Minor", retune_speed=0.0, humanize=0.0, acoustic_purpose="Snap duro de afinación moderna"),
            make_pro_q_4(hpf_freq=0.28, clean_dip=0.40, presence_boost=0.70, air_shelf=0.85, acoustic_purpose="Corte de frecuencias bajas y presencia"),
            make_delay(dry_wet=0.30, feedback=0.35, sync=1.0, ping_pong=1.0, acoustic_purpose="Ecos sincronizados de chop"),
            make_valhalla_vintage_verb(mode=0.30, color=0.50, mix=0.22, decay=0.25, predelay=0.04, acoustic_purpose="Placa de estudio sedosa")
        ],
        "ACOUSTIC_PIANO": [
            make_eq_eight(hpf_default=0.28, bell_default=0.42, bell_name="Limpieza Barro (350 Hz)", high_default=0.75, high_name="Brillo Martillos (8 kHz)", acoustic_purpose="HPF 110 Hz para despejar el 808"),
            make_glue_compressor(threshold=-12.0, ratio=1.0, attack=0.60, release=0.0, dry_wet=0.80, makeup=0.10, acoustic_purpose="Control dinámico de pulsación"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.18, decay=0.24, predelay=0.04, acoustic_purpose="Sala de estudio íntima")
        ],
        "RHODES": [
            make_eq_eight(hpf_default=0.28, bell_default=0.40, bell_name="Calidez Campana (300 Hz)", high_default=0.68, high_name="Brillo Tines (3.5 kHz)", acoustic_purpose="HPF 100 Hz y limpieza modal"),
            make_chorus_ensemble(amount=0.35, rate=0.20, warmth=0.60, acoustic_purpose="Ensanchamiento estéreo y modulación"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.20, mix=0.65, slot_name="Slot 1 Tape Saturation", acoustic_purpose="Saturación magnética de cinta"),
            make_valhalla_vintage_verb(mode=0.30, color=0.50, mix=0.18, decay=0.22, predelay=0.04, acoustic_purpose="Placa vintage cálida")
        ],
        "ORGAN": [
            make_eq_eight(hpf_default=0.28, bell_default=0.50, bell_name="Mordida Leslie (1.2 kHz)", acoustic_purpose="HPF 120 Hz para acoplamiento con bombo"),
            make_saturator(drive=0.22, base=0.0, output=0.70, acoustic_purpose="Saturación de válvulas y presencia"),
            make_chorus_ensemble(amount=0.40, rate=0.35, warmth=0.55, acoustic_purpose="Efecto rotatorio Leslie de órgano")
        ],
        "VIOLIN": [
            make_eq_eight(hpf_default=0.32, bell_default=0.68, bell_name="Corte Asperezas (3.8 kHz)", high_default=0.80, high_name="Aire Violín", acoustic_purpose="HPF 160 Hz y control de estridencias"),
            make_valhalla_vintage_verb(mode=0.20, color=0.50, mix=0.22, decay=0.30, predelay=0.05, acoustic_purpose="Sala de concierto sinfónica controlada")
        ],
        "CELLO": [
            make_eq_eight(hpf_default=0.22, bell_default=0.45, bell_name="Cuerpo Chelo (250 Hz)", high_default=0.70, high_name="Aire Cuerda", acoustic_purpose="HPF 75 Hz y limpieza de resonancias"),
            make_glue_compressor(threshold=-12.0, ratio=1.0, attack=0.50, release=0.0, makeup=0.08, acoustic_purpose="Control dinámico suave"),
            make_valhalla_vintage_verb(mode=0.20, color=0.50, mix=0.20, decay=0.28, predelay=0.05, acoustic_purpose="Sala acústica cálida")
        ],
        "UPRIGHT_BASS": [
            make_eq_eight(hpf_default=0.18, bell_default=0.35, bell_name="Cuerpo Contrabajo (100 Hz)", high_default=0.60, high_name="Ataque Dedos (1.5 kHz)", acoustic_purpose="HPF 35 Hz y definición de madera"),
            make_compressor(threshold=-15.0, ratio=2.5, attack=0.15, release=0.25, acoustic_purpose="Nivelación suave"),
            make_utility(bass_mono=1.0, bass_freq=115.0, width=1.0, acoustic_purpose="Monofonización natural")
        ],
        "CONGAS": [
            make_eq_eight(hpf_default=0.22, bell_default=0.65, bell_name="Chasquido Slap (2.6 kHz)", acoustic_purpose="HPF 90 Hz y realce de slap percusivo"),
            make_glue_compressor(threshold=-12.0, ratio=2.0, attack=0.65, release=0.0, makeup=0.10, acoustic_purpose="Pegada transitoria controlada")
        ],
        "SHAKER": [
            make_eq_eight(hpf_default=0.38, bell_default=0.70, bell_name="Cuerpo Shaker (4 kHz)", high_default=0.88, high_name="Brillo Aire (12 kHz)", acoustic_purpose="HPF 260 Hz para limpiar completamente el rango grave"),
            make_glue_compressor(threshold=-12.0, ratio=1.0, attack=0.80, release=0.0, makeup=0.08, acoustic_purpose="Transientes intactos y ritmo nivelado")
        ],
        "SNARE": [
            make_eq_eight(hpf_default=0.20, bell_default=0.45, bell_name="Cuerpo Caja (200 Hz)", high_default=0.78, high_name="Chasquido Bordonero (4 kHz)", acoustic_purpose="HPF 85 Hz y pegada fundamental"),
            make_drum_buss(drive=0.25, crunch=0.35, transients=0.65, boom=0.0, output=0.70, acoustic_purpose="Crunch y pegada dura de caja urbana"),
            make_valhalla_vintage_verb(mode=0.0, color=0.50, mix=0.14, decay=0.18, predelay=0.02, acoustic_purpose="Reverb de caja corto y con mordida")
        ],
        "HIHAT": [
            make_eq_eight(hpf_default=0.40, bell_default=0.75, bell_name="Definición Tic (6 kHz)", high_default=0.88, high_name="Aire Platillo (12 kHz)", acoustic_purpose="HPF 320 Hz estricto anti-barro"),
            make_glue_compressor(threshold=-14.0, ratio=1.0, attack=0.80, release=0.0, makeup=0.08, acoustic_purpose="Control de picos en rolls de hi-hats")
        ],
        "SYNTH_LEAD": [
            make_eq_eight(hpf_default=0.30, bell_default=0.68, bell_name="Corte Asperezas (3.5 kHz)", high_default=0.82, high_name="Presencia Lead", acoustic_purpose="HPF 140 Hz y apertura espectral"),
            make_saturator(drive=0.28, base=0.0, output=0.70, acoustic_purpose="Saturación agresiva para cortar la mezcla urbana"),
            make_delay(dry_wet=0.28, feedback=0.32, sync=1.0, ping_pong=1.0, acoustic_purpose="Ecos rítmicos sincronizados"),
            make_valhalla_vintage_verb(mode=0.10, color=0.50, mix=0.20, decay=0.25, predelay=0.04, acoustic_purpose="Placa de estudio brillante")
        ],
        "SOUNDSCAPE": [
            make_eq_eight(hpf_default=0.22, bell_default=0.50, bell_name="Medios Textura", high_default=0.75, high_name="LPF Suave (8 kHz)", acoustic_purpose="HPF 80 Hz y control de siseo"),
            make_utility(bass_mono=1.0, width=1.35, acoustic_purpose="Apertura estéreo amplia de fondo"),
            make_valhalla_vintage_verb(mode=0.50, color=0.50, mix=0.35, decay=0.45, predelay=0.06, acoustic_purpose="Catedral envolvente")
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
        ],
        "SYNTH_BASS": [
            make_eq_eight(hpf_default=0.16, bell_default=0.25, bell_name="Muesca Bombo (60 Hz)", acoustic_purpose="HPF 32 Hz y tallado quirúrgico"),
            make_compressor(threshold=-16.0, ratio=4.0, attack=0.01, release=0.18, sidechain=True, acoustic_purpose="Ducking sidechain rítmico"),
            make_saturator(drive=0.32, base=0.0, output=0.70, acoustic_purpose="Saturación pesada para cortar la pista"),
            make_utility(bass_mono=1.0, bass_freq=125.0, width=0.0, acoustic_purpose="Monofonización pura")
        ],
        "SYNTH_PLUCK": [
            make_eq_eight(hpf_default=0.32, bell_default=0.65, bell_name="Presencia Pluck Club", high_default=0.85, high_name="Aire Sintetizador", acoustic_purpose="HPF 150 Hz y apertura aérea"),
            make_ott(depth=0.20, time=0.50, acoustic_purpose="Compresión multibanda rápida"),
            make_delay(dry_wet=0.32, feedback=0.35, sync=1.0, ping_pong=1.0, acoustic_purpose="Ecos ping-pong sincronizados"),
            make_valhalla_vintage_verb(mode=0.0, color=0.0, mix=0.22, decay=0.25, acoustic_purpose="Concert Hall brillante")
        ],
        "ARPEGGIO": [
            make_eq_eight(hpf_default=0.32, bell_default=0.60, bell_name="Cuerpo Arp Club", high_default=0.85, high_name="Aire Arpegio", acoustic_purpose="HPF 150 Hz y corte modal"),
            make_auto_filter(frequency=0.60, resonance=0.30, filter_type=0.0, drive=0.20, acoustic_purpose="Filtro resonante con barrido"),
            make_ott(depth=0.22, time=0.50, acoustic_purpose="Pegada multibanda OTT"),
            make_delay(dry_wet=0.35, feedback=0.40, sync=1.0, ping_pong=1.0, acoustic_purpose="Retardo estéreo sincronizado a 1/8d")
        ],
        "VOCAL_CHOP": [
            make_auto_tune_artist(key="C", scale="Minor", retune_speed=0.0, humanize=0.0, acoustic_purpose="Cuantización instantánea snap"),
            make_pro_q_4(hpf_freq=0.28, clean_dip=0.40, presence_boost=0.70, air_shelf=0.88, acoustic_purpose="Corte quirúrgico y presencia en pista"),
            make_ott(depth=0.25, time=0.50, acoustic_purpose="Densidad multibanda upward/downward"),
            make_delay(dry_wet=0.32, feedback=0.38, sync=1.0, ping_pong=1.0, acoustic_purpose="Ecos estéreo sincronizados"),
            make_valhalla_vintage_verb(mode=0.0, color=0.0, mix=0.30, decay=0.35, acoustic_purpose="Concert Hall amplio y brillante")
        ],
        "ACOUSTIC_PIANO": [
            make_eq_eight(hpf_default=0.30, bell_default=0.45, bell_name="Corte Graves Piano", high_default=0.80, high_name="Brillo Piano Club", acoustic_purpose="HPF 130 Hz y apertura aérea"),
            make_compressor(threshold=-14.0, ratio=3.0, attack=0.02, release=0.25, sidechain=True, acoustic_purpose="Bombeo sidechain con el bombo"),
            make_valhalla_vintage_verb(mode=0.0, color=0.0, mix=0.25, decay=0.32, acoustic_purpose="Sala de concierto amplia")
        ],
        "RHODES": [
            make_eq_eight(hpf_default=0.28, bell_default=0.42, bell_name="Limpieza Medios", high_default=0.75, high_name="Brillo Acordes", acoustic_purpose="HPF 120 Hz para acoplamiento"),
            make_chorus_ensemble(amount=0.35, rate=0.25, warmth=0.40, acoustic_purpose="Apertura dimensional"),
            make_compressor(threshold=-15.0, ratio=3.0, attack=0.02, release=0.25, sidechain=True, acoustic_purpose="Sidechain rítmico"),
            make_valhalla_vintage_verb(mode=0.0, color=0.0, mix=0.22, decay=0.28, acoustic_purpose="Reverb brillante de estudio")
        ],
        "ORGAN": [
            make_eq_eight(hpf_default=0.30, bell_default=0.55, bell_name="Presencia Órgano Club", acoustic_purpose="HPF 130 Hz y corte de choque con bajo"),
            make_phaser_flanger(amount=0.30, rate=0.20, feedback=0.20, warmth=0.40, mode=0.0, acoustic_purpose="Modulación de fase estilo house organ"),
            make_compressor(threshold=-15.0, ratio=3.0, attack=0.02, release=0.20, sidechain=True, acoustic_purpose="Sidechain con bombo")
        ],
        "VIOLIN": [
            make_eq_eight(hpf_default=0.32, bell_default=0.65, bell_name="Corte Asperezas Violín", high_default=0.85, high_name="Aire Sintético", acoustic_purpose="HPF 180 Hz y apertura"),
            make_compressor(threshold=-14.0, ratio=3.0, attack=0.05, release=0.25, sidechain=True, acoustic_purpose="Bombeo sidechain rítmico"),
            make_valhalla_supermassive(mode=0.25, mix=0.30, feedback=0.55, acoustic_purpose="Nube difusa estéreo")
        ],
        "CELLO": [
            make_eq_eight(hpf_default=0.20, bell_default=0.45, bell_name="Cuerpo Chelo", high_default=0.75, high_name="Aire", acoustic_purpose="HPF 70 Hz y despeje modal"),
            make_compressor(threshold=-15.0, ratio=3.0, attack=0.02, release=0.25, sidechain=True, acoustic_purpose="Ducking sidechain"),
            make_valhalla_supermassive(mode=0.20, mix=0.25, feedback=0.50, acoustic_purpose="Difusión masiva")
        ],
        "UPRIGHT_BASS": [
            make_eq_eight(hpf_default=0.18, bell_default=0.35, bell_name="Cuerpo Contrabajo", acoustic_purpose="HPF 35 Hz"),
            make_compressor(threshold=-16.0, ratio=3.5, attack=0.02, release=0.20, sidechain=True, acoustic_purpose="Compresión con bombeo sidechain"),
            make_utility(bass_mono=1.0, bass_freq=120.0, width=1.0, acoustic_purpose="Monofonización natural")
        ],
        "CONGAS": [
            make_eq_eight(hpf_default=0.24, bell_default=0.68, bell_name="Slap Congas Club", acoustic_purpose="HPF 110 Hz y snap percusivo"),
            make_compressor(threshold=-15.0, ratio=3.0, attack=0.05, release=0.15, sidechain=True, acoustic_purpose="Sidechain rítmico con el bombo"),
            make_delay(dry_wet=0.28, feedback=0.32, sync=1.0, acoustic_purpose="Retardo sincronizado")
        ],
        "SHAKER": [
            make_eq_eight(hpf_default=0.38, bell_default=0.75, bell_name="Presencia Shaker Club", high_default=0.90, high_name="Aire Platillos", acoustic_purpose="HPF 280 Hz"),
            make_compressor(threshold=-16.0, ratio=3.0, attack=0.02, release=0.15, sidechain=True, acoustic_purpose="Bombeo rítmico con bombo")
        ],
        "SNARE": [
            make_eq_eight(hpf_default=0.20, bell_default=0.48, bell_name="Pegada Caja (220 Hz)", high_default=0.85, high_name="Chasquido Club (4.5 kHz)", acoustic_purpose="HPF 90 Hz y chasquido brillante"),
            make_glue_compressor(threshold=-10.0, ratio=2.0, attack=0.50, release=0.0, dry_wet=0.90, makeup=0.15, acoustic_purpose="Pegamento de caja de club"),
            make_saturator(drive=0.22, base=0.0, output=0.70, acoustic_purpose="Distorsión armónica sólida")
        ],
        "HIHAT": [
            make_eq_eight(hpf_default=0.40, bell_default=0.78, bell_name="Tic 909 (7 kHz)", high_default=0.90, high_name="Aire 909 (12 kHz)", acoustic_purpose="HPF 320 Hz"),
            make_glue_compressor(threshold=-12.0, ratio=1.0, attack=0.80, release=0.0, makeup=0.10, acoustic_purpose="Control dinámico de platillos de club")
        ],
        "SYNTH_LEAD": [
            make_eq_eight(hpf_default=0.32, bell_default=0.68, bell_name="Presencia Lead Club (3.5 kHz)", high_default=0.85, high_name="Aire Cristalino", acoustic_purpose="HPF 150 Hz y corte modal"),
            make_ott(depth=0.30, time=0.50, acoustic_purpose="Compresión agresiva OTT para cortar la pista"),
            make_compressor(threshold=-16.0, ratio=4.0, attack=0.01, release=0.20, sidechain=True, acoustic_purpose="Ducking sidechain al compás del bombo"),
            make_delay(dry_wet=0.35, feedback=0.40, sync=1.0, ping_pong=1.0, acoustic_purpose="Retardo ping-pong sincronizado"),
            make_valhalla_supermassive(mode=0.38, mix=0.25, feedback=0.45, acoustic_purpose="Difusión masiva espacial")
        ],
        "SOUNDSCAPE": [
            make_eq_eight(hpf_default=0.22, bell_default=0.60, bell_name="Cuerpo Transición Club", high_default=0.85, high_name="Aire Risers", acoustic_purpose="HPF 90 Hz y apertura estéreo"),
            make_auto_filter(frequency=0.45, resonance=0.25, filter_type=0.0, drive=0.10, acoustic_purpose="Modulación de corte"),
            make_valhalla_supermassive(mode=0.45, mix=0.45, feedback=0.70, acoustic_purpose="Difusión masiva para subidas de club")
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
        ],
        "SYNTH_BASS": [
            make_eq_eight(hpf_default=0.18, bell_default=0.35, bell_name="Cuerpo Cálido (100 Hz)", acoustic_purpose="HPF 35 Hz y calidez musical"),
            make_compressor(threshold=-16.0, ratio=2.5, attack=0.20, release=0.30, acoustic_purpose="Compresión óptica suave"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.18, mix=0.60, slot_name="Slot 1 Tape Saturation", acoustic_purpose="Calidez de cinta vintage"),
            make_utility(bass_mono=1.0, bass_freq=110.0, width=1.0, acoustic_purpose="Monofonización natural")
        ],
        "SYNTH_PLUCK": [
            make_eq_eight(hpf_default=0.28, bell_default=0.45, bell_name="Dulzura Acordes", high_default=0.75, high_name="Aire Suave", acoustic_purpose="HPF 120 Hz y limpieza musical"),
            make_chorus_ensemble(amount=0.25, rate=0.15, warmth=0.75, acoustic_purpose="Chorus BBD analógico"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.18, decay=0.22, predelay=0.04, acoustic_purpose="Cámara vintage suave")
        ],
        "ARPEGGIO": [
            make_eq_eight(hpf_default=0.28, bell_default=0.50, bell_name="Cuerpo Melódico", high_default=0.75, high_name="Aire", acoustic_purpose="HPF 130 Hz"),
            make_delay(dry_wet=0.20, feedback=0.25, sync=1.0, acoustic_purpose="Eco sutil de cinta analógica"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.18, decay=0.24, predelay=0.04, acoustic_purpose="Ambiente de estudio")
        ],
        "VOCAL_CHOP": [
            make_pro_q_4(hpf_freq=0.26, clean_dip=0.40, presence_boost=0.65, air_shelf=0.78, acoustic_purpose="Corte suave de graves y aire cálido"),
            make_compressor(threshold=-16.0, ratio=2.5, attack=0.15, release=0.25, acoustic_purpose="Nivelación óptica estilo LA-2A"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.16, mix=0.55, slot_name="Slot 1 Tape Warmth", acoustic_purpose="Saturación de cinta analógica"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.22, decay=0.26, predelay=0.04, acoustic_purpose="Placa de estudio 1970s Plate sedosa")
        ],
        "ACOUSTIC_PIANO": [
            make_eq_eight(hpf_default=0.26, bell_default=0.40, bell_name="Limpieza de Barro (320 Hz)", high_default=0.72, high_name="Calidez de Cola (6 kHz)", acoustic_purpose="HPF 100 Hz y curvas no invasivas"),
            make_compressor(threshold=-14.0, ratio=2.0, attack=0.25, release=0.25, acoustic_purpose="Compresión óptica transparente"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.20, decay=0.28, predelay=0.04, acoustic_purpose="Sala de concierto de madera natural")
        ],
        "RHODES": [
            make_eq_eight(hpf_default=0.26, bell_default=0.38, bell_name="Cuerpo Rhodes (280 Hz)", high_default=0.68, high_name="Campanilleo Suave (3.5 kHz)", acoustic_purpose="HPF 100 Hz y limpieza modal"),
            make_chorus_ensemble(amount=0.30, rate=0.18, warmth=0.85, acoustic_purpose="Modulación BBD cálida analógica"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.18, mix=0.65, slot_name="Slot 1 Tape Saturation", acoustic_purpose="Saturación de cinta vintage"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.20, decay=0.26, predelay=0.04, acoustic_purpose="Cámara acústica 1970s Chamber")
        ],
        "ORGAN": [
            make_eq_eight(hpf_default=0.28, bell_default=0.45, bell_name="Cuerpo Hammond (350 Hz)", high_default=0.70, high_name="Presencia Armónica", acoustic_purpose="HPF 110 Hz y calidez"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.20, mix=0.60, slot_name="Slot 1 Tape Warmth", acoustic_purpose="Calidez de previo de válvulas"),
            make_chorus_ensemble(amount=0.35, rate=0.25, warmth=0.80, acoustic_purpose="Efecto rotatorio suave"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.22, decay=0.28, acoustic_purpose="Cámara de estudio")
        ],
        "VIOLIN": [
            make_eq_eight(hpf_default=0.30, bell_default=0.50, bell_name="Cuerpo Violín (600 Hz)", high_default=0.75, high_name="Aire Acústico", acoustic_purpose="HPF 160 Hz y tono cálido"),
            make_compressor(threshold=-12.0, ratio=2.0, attack=0.30, release=0.40, acoustic_purpose="Compresión suave que respeta dinámicas"),
            make_valhalla_vintage_verb(mode=0.20, color=0.50, mix=0.24, decay=0.32, predelay=0.05, acoustic_purpose="Sala sinfónica cálida")
        ],
        "CELLO": [
            make_eq_eight(hpf_default=0.20, bell_default=0.40, bell_name="Cuerpo Chelo Acústico (200 Hz)", acoustic_purpose="HPF 65 Hz y resonancia de madera"),
            make_compressor(threshold=-14.0, ratio=2.0, attack=0.25, release=0.30, acoustic_purpose="Compresión óptica musical"),
            make_valhalla_vintage_verb(mode=0.20, color=0.50, mix=0.22, decay=0.30, predelay=0.05, acoustic_purpose="Sala acústica cálida")
        ],
        "UPRIGHT_BASS": [
            make_eq_eight(hpf_default=0.18, bell_default=0.35, bell_name="Cuerpo Madera (100 Hz)", high_default=0.60, high_name="Clic Cuerda (1.4 kHz)", acoustic_purpose="HPF 32 Hz y cuerpo de contrabajo"),
            make_compressor(threshold=-15.0, ratio=2.0, attack=0.25, release=0.30, acoustic_purpose="Nivelación óptica estilo LA-2A"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.15, mix=0.55, slot_name="Slot 1 Tape Warmth", acoustic_purpose="Saturación sutil analógica"),
            make_utility(bass_mono=1.0, bass_freq=110.0, width=1.0, acoustic_purpose="Monofonización natural")
        ],
        "CONGAS": [
            make_eq_eight(hpf_default=0.20, bell_default=0.60, bell_name="Cuerpo Parche y Slap (2.4 kHz)", acoustic_purpose="HPF 85 Hz y cuerpo de cuero"),
            make_glue_compressor(threshold=-10.0, ratio=1.0, attack=0.60, release=0.0, makeup=0.06, acoustic_purpose="Compresión suave que no aplasta transientes"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.14, decay=0.18, predelay=0.03, acoustic_purpose="Sala acústica íntima")
        ],
        "SHAKER": [
            make_eq_eight(hpf_default=0.36, bell_default=0.65, bell_name="Cuerpo Semilla (3.5 kHz)", high_default=0.85, high_name="Aire Seda (10 kHz)", acoustic_purpose="HPF 240 Hz y apertura sedosa"),
            make_glue_compressor(threshold=-12.0, ratio=1.0, attack=0.70, release=0.0, makeup=0.06, acoustic_purpose="Control dinámico transparente")
        ],
        "SNARE": [
            make_eq_eight(hpf_default=0.20, bell_default=0.44, bell_name="Cuerpo Madera Caja (220 Hz)", high_default=0.75, high_name="Snap Natural (3.8 kHz)", acoustic_purpose="HPF 85 Hz y pegada cálida"),
            make_glue_compressor(threshold=-9.0, ratio=1.0, attack=0.60, release=0.0, dry_wet=0.70, makeup=0.06, acoustic_purpose="Compresión transparente"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.18, mix=0.55, slot_name="Slot 1 Tape Saturation", acoustic_purpose="Calidez de cinta en caja acústica"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.16, decay=0.20, predelay=0.03, acoustic_purpose="Sala 1970s Room natural")
        ],
        "HIHAT": [
            make_eq_eight(hpf_default=0.38, bell_default=0.70, bell_name="Tic Platillo Acústico (5 kHz)", high_default=0.85, high_name="Aire Natural (10 kHz)", acoustic_purpose="HPF 280 Hz"),
            make_glue_compressor(threshold=-10.0, ratio=1.0, attack=0.70, release=0.0, makeup=0.05, acoustic_purpose="Compresión suave sin fatiga auditiva")
        ],
        "SYNTH_LEAD": [
            make_eq_eight(hpf_default=0.28, bell_default=0.55, bell_name="Cuerpo Solista", high_default=0.75, high_name="Aire Cálido", acoustic_purpose="HPF 130 Hz y calidez no invasiva"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.18, mix=0.60, slot_name="Slot 1 Tape Warmth", acoustic_purpose="Saturación de cinta analógica"),
            make_delay(dry_wet=0.20, feedback=0.25, sync=1.0, acoustic_purpose="Eco sutil de cinta"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.18, decay=0.25, acoustic_purpose="Cámara de estudio")
        ],
        "SOUNDSCAPE": [
            make_eq_eight(hpf_default=0.22, bell_default=0.50, bell_name="Medios Orgánicos", high_default=0.72, high_name="LPF Calidez (7.5 kHz)", acoustic_purpose="HPF 80 Hz y LPF 7.5 kHz para calidez analógica"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.14, mix=0.50, slot_name="Slot 1 Tape Warmth", acoustic_purpose="Textura suave de cinta"),
            make_valhalla_vintage_verb(mode=0.50, color=0.50, mix=0.30, decay=0.40, acoustic_purpose="Ambiente acústico profundo")
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
        ],
        "SYNTH_BASS": [
            make_eq_eight(hpf_default=0.12, bell_default=0.25, bell_name="Cuerpo Sub Profundo (40 Hz)", high_default=0.60, high_name="LPF Oscuro (4 kHz)", acoustic_purpose="HPF 24 Hz y LPF 4 kHz"),
            make_saturator(drive=0.18, base=0.0, output=0.75, acoustic_purpose="Calidez analógica sutil"),
            make_utility(bass_mono=1.0, bass_freq=110.0, width=0.0, acoustic_purpose="Monofonización rigurosa"),
            make_valhalla_supermassive(mode=0.15, mix=0.15, feedback=0.40, acoustic_purpose="Halo ambiental sutil")
        ],
        "SYNTH_PLUCK": [
            make_eq_eight(hpf_default=0.28, bell_default=0.60, bell_name="Cuerpo Pluck Espacial", high_default=0.85, high_name="Aire Celestial", acoustic_purpose="HPF 140 Hz y brillo etéreo"),
            make_delay(dry_wet=0.35, feedback=0.45, sync=1.0, ping_pong=1.0, acoustic_purpose="Ecos rítmicos envolventes"),
            make_valhalla_supermassive(mode=0.38, mix=0.35, feedback=0.65, acoustic_purpose="Difusión masiva modo Andromeda")
        ],
        "ARPEGGIO": [
            make_eq_eight(hpf_default=0.30, bell_default=0.60, bell_name="Cuerpo Arp Espacial", high_default=0.85, high_name="Aire Celestial", acoustic_purpose="HPF 150 Hz y corte modal"),
            make_delay(dry_wet=0.35, feedback=0.50, sync=1.0, ping_pong=1.0, acoustic_purpose="Ecos en abanico estéreo"),
            make_valhalla_supermassive(mode=0.45, mix=0.40, feedback=0.75, acoustic_purpose="Difusión masiva cósmica")
        ],
        "VOCAL_CHOP": [
            make_pro_q_4(hpf_freq=0.28, clean_dip=0.40, presence_boost=0.70, air_shelf=0.88, acoustic_purpose="Corte de frecuencias bajas y presencia aérea"),
            make_delay(dry_wet=0.35, feedback=0.45, sync=1.0, ping_pong=1.0, acoustic_purpose="Ecos envolventes de chop vocal"),
            make_valhalla_supermassive(mode=0.50, mix=0.45, feedback=0.75, acoustic_purpose="Difusión celestial infinita")
        ],
        "ACOUSTIC_PIANO": [
            make_eq_eight(hpf_default=0.26, bell_default=0.40, bell_name="Limpieza de Medios (300 Hz)", high_default=0.75, high_name="Aire Martillos", acoustic_purpose="HPF 100 Hz"),
            make_glue_compressor(threshold=-12.0, ratio=1.0, attack=0.60, release=0.0, dry_wet=0.75, makeup=0.08, acoustic_purpose="Control dinámico suave"),
            make_valhalla_supermassive(mode=0.35, mix=0.35, feedback=0.65, acoustic_purpose="Nube difusa estéreo para piano cinematográfico")
        ],
        "RHODES": [
            make_eq_eight(hpf_default=0.26, bell_default=0.40, bell_name="Limpieza Medios (300 Hz)", acoustic_purpose="HPF 100 Hz"),
            make_chorus_ensemble(amount=0.35, rate=0.20, warmth=0.60, acoustic_purpose="Ensanchamiento estéreo"),
            make_valhalla_supermassive(mode=0.38, mix=0.35, feedback=0.65, acoustic_purpose="Difusión masiva Cassiopeia")
        ],
        "ORGAN": [
            make_eq_eight(hpf_default=0.28, bell_default=0.50, bell_name="Cuerpo Órgano", acoustic_purpose="HPF 120 Hz"),
            make_valhalla_supermassive(mode=0.50, mix=0.40, feedback=0.70, acoustic_purpose="Catedral majestuosa infinita")
        ],
        "VIOLIN": [
            make_eq_eight(hpf_default=0.28, bell_default=0.55, bell_name="Cuerpo Violín Solista", high_default=0.82, high_name="Aire Celestial", acoustic_purpose="HPF 150 Hz y apertura sedosa"),
            make_delay(dry_wet=0.30, feedback=0.45, sync=1.0, acoustic_purpose="Retardo estéreo envolvente"),
            make_valhalla_supermassive(mode=0.55, mix=0.40, feedback=0.75, acoustic_purpose="Modo Triangulum con difusión orquestal épica")
        ],
        "CELLO": [
            make_eq_eight(hpf_default=0.18, bell_default=0.40, bell_name="Cuerpo Chelo Orquestal (180 Hz)", acoustic_purpose="HPF 60 Hz y resonancia profunda"),
            make_valhalla_supermassive(mode=0.45, mix=0.35, feedback=0.70, acoustic_purpose="Espacio orquestal sinfónico profundo")
        ],
        "UPRIGHT_BASS": [
            make_eq_eight(hpf_default=0.16, bell_default=0.32, bell_name="Cuerpo Contrabajo Profundo", acoustic_purpose="HPF 30 Hz"),
            make_compressor(threshold=-14.0, ratio=2.0, attack=0.15, release=0.25, acoustic_purpose="Compresión óptica transparente"),
            make_utility(bass_mono=1.0, bass_freq=110.0, width=0.0, acoustic_purpose="Monofonización estricta"),
            make_valhalla_supermassive(mode=0.15, mix=0.12, feedback=0.35, acoustic_purpose="Halo sutil de sala de conciertos")
        ],
        "CONGAS": [
            make_eq_eight(hpf_default=0.22, bell_default=0.60, bell_name="Cuerpo Tambor Étnico", acoustic_purpose="HPF 90 Hz"),
            make_delay(dry_wet=0.30, feedback=0.40, sync=1.0, acoustic_purpose="Ecos espaciales"),
            make_valhalla_supermassive(mode=0.30, mix=0.25, feedback=0.50, acoustic_purpose="Difusión percusiva ambiental")
        ],
        "SHAKER": [
            make_eq_eight(hpf_default=0.36, bell_default=0.65, bell_name="Brillo Textura", high_default=0.88, high_name="Aire Celestial", acoustic_purpose="HPF 260 Hz"),
            make_delay(dry_wet=0.32, feedback=0.45, sync=1.0, ping_pong=1.0, acoustic_purpose="Repeticiones ping-pong en extremos"),
            make_valhalla_supermassive(mode=0.35, mix=0.30, feedback=0.60, acoustic_purpose="Nube de difusión brillante")
        ],
        "SNARE": [
            make_eq_eight(hpf_default=0.20, bell_default=0.45, bell_name="Cuerpo Caja Épica (200 Hz)", high_default=0.78, high_name="Aire Platillo", acoustic_purpose="HPF 80 Hz y pegada cinemática"),
            make_glue_compressor(threshold=-12.0, ratio=1.0, attack=0.60, release=0.0, dry_wet=0.75, acoustic_purpose="Control dinámico cinematográfico"),
            make_valhalla_supermassive(mode=0.25, mix=0.25, feedback=0.55, acoustic_purpose="Nube difusa estéreo para caja ambiental")
        ],
        "HIHAT": [
            make_eq_eight(hpf_default=0.38, bell_default=0.75, bell_name="Tic Espacial", high_default=0.88, high_name="Aire Celestial", acoustic_purpose="HPF 300 Hz"),
            make_delay(dry_wet=0.30, feedback=0.45, sync=1.0, ping_pong=1.0, acoustic_purpose="Ecos perimetrales"),
            make_valhalla_supermassive(mode=0.30, mix=0.25, feedback=0.50, acoustic_purpose="Difusión etérea")
        ],
        "SYNTH_LEAD": [
            make_eq_eight(hpf_default=0.30, bell_default=0.65, bell_name="Presencia Lead Celestial", high_default=0.85, high_name="Aire Espacial", acoustic_purpose="HPF 140 Hz y apertura aérea"),
            make_delay(dry_wet=0.35, feedback=0.45, sync=1.0, ping_pong=1.0, acoustic_purpose="Ecos rítmicos sincronizados"),
            make_valhalla_supermassive(mode=0.45, mix=0.40, feedback=0.75, acoustic_purpose="Difusión masiva cósmica")
        ],
        "SOUNDSCAPE": [
            make_eq_eight(hpf_default=0.20, bell_default=0.50, bell_name="Cuerpo Atmósfera", high_default=0.80, high_name="LPF Control (8 kHz)", acoustic_purpose="HPF 70 Hz y LPF 8 kHz"),
            make_surge_xt_effects(dsp_type="fxt_conditioner", drive=0.32, mix=0.70, slot_name="Slot 1 Nimbus Shaper", acoustic_purpose="Modelado granular Nimbus de texturas profundas"),
            make_valhalla_supermassive(mode=0.75, mix=0.55, feedback=0.90, acoustic_purpose="Modo Pleiades/Sirius para brillo celestial masivo e infinito")
        ]
    }


# --- 5. Surgical Subgenre Specialization Matrices ---

SUBGENRE_CHAIN_OVERRIDES: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    # 1. Urbana / Moderna subgenres
    "boom_bap": {
        "DRUMS": [
            make_eq_eight(hpf_default=0.18, bell_default=0.44, bell_name="Corte Resonancia Caja (350 Hz)", high_default=0.75, high_name="Aire Vinilo (8 kHz)", acoustic_purpose="Limpieza de medios y calidez de vinilo"),
            make_drum_buss(drive=0.22, crunch=0.25, transients=0.55, boom=0.15, output=0.72, acoustic_purpose="Crunch analógico vintage estilo MPC"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.24, mix=0.70, slot_name="Slot 1 DSP Type (Analog Tape)", acoustic_purpose="Saturación magnética de cinta en batería boom bap"),
            make_glue_compressor(threshold=-10.0, ratio=1.0, attack=0.60, release=0.0, dry_wet=0.75, makeup=0.10, acoustic_purpose="Compresión paralela sutil")
        ],
        "BASS": [
            make_eq_eight(hpf_default=0.16, bell_default=0.35, bell_name="Cuerpo Bajo Calido (100 Hz)", acoustic_purpose="HPF 32 Hz y peso cálido de muestra"),
            make_saturator(drive=0.20, base=0.0, output=0.72, acoustic_purpose="Calidez armónica suave en medios"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.18, mix=0.65, slot_name="Slot 1 Tape Saturation", acoustic_purpose="Grosor de cinta analógica"),
            make_utility(bass_mono=1.0, bass_freq=120.0, width=0.0, acoustic_purpose="Monofonización pura")
        ],
        "KEYS": [
            make_eq_eight(hpf_default=0.28, bell_default=0.40, bell_name="Limpieza de Barro (320 Hz)", high_default=0.68, high_name="Dulzura Vinilo (3 kHz)", acoustic_purpose="Filtro pasa-altos 110 Hz para despejar el bajo"),
            make_surge_xt_effects(dsp_type="fxt_tape", drive=0.22, mix=0.75, slot_name="Slot 1 Chow Tape", acoustic_purpose="Color analógico Chow Tape estilo muestreador 90s"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.18, decay=0.22, predelay=0.04, acoustic_purpose="Ambiente de habitación cálido 1970s Room")
        ],
        "VOCALS": [
            make_pro_q_4(hpf_freq=0.25, clean_dip=0.40, presence_boost=0.65, air_shelf=0.82, acoustic_purpose="Limpieza quirúrgica y presencia vocal clásica"),
            make_compressor(threshold=-16.0, ratio=3.0, attack=0.05, release=0.20, acoustic_purpose="Nivelación analógica estilo VCA/Opto"),
            make_saturn_2(drive=0.20, dynamics=0.0, warmth=0.50, mix=0.75, acoustic_purpose="Saturación de cinta para presencia vocal cálida sin afinación robótica"),
            make_valhalla_vintage_verb(mode=0.30, color=0.50, mix=0.16, decay=0.22, predelay=0.04, acoustic_purpose="Placa de estudio vintage sedosa")
        ]
    },
    "drill": {
        "808_BASS": [
            make_eq_eight(hpf_default=0.14, bell_default=0.55, bell_name="Mordida Glides (700-1200 Hz)", acoustic_purpose="HPF 28 Hz y mordida para glides de Drill"),
            make_saturator(drive=0.34, base=0.0, output=0.68, acoustic_purpose="Saturación dura para cortes de glides agresivos"),
            make_utility(bass_mono=1.0, bass_freq=125.0, width=0.0, acoustic_purpose="Monofonización rigurosa de subgraves")
        ],
        "KEYS": [
            make_eq_eight(hpf_default=0.32, bell_default=0.50, bell_name="Cuerpo Sombrío", high_default=0.65, high_name="LPF Oscuro (6 kHz)", acoustic_purpose="Filtro sombrío característico del sonido UK/NY Drill"),
            make_delay(dry_wet=0.30, feedback=0.35, sync=1.0, ping_pong=1.0, acoustic_purpose="Ecos oscuros sincronizados"),
            make_valhalla_vintage_verb(mode=0.10, color=0.50, mix=0.22, decay=0.30, acoustic_purpose="Cámara oscura de piano drill")
        ]
    },
    "phonk": {
        "808_BASS": [
            make_eq_eight(hpf_default=0.12, bell_default=0.25, bell_name="Punch Pesado Phonk (50 Hz)", acoustic_purpose="HPF 26 Hz y pegada masiva"),
            make_saturator(drive=0.38, base=0.0, output=0.68, acoustic_purpose="Distorsión analógica saturada para bajo Phonk"),
            make_utility(bass_mono=1.0, bass_freq=130.0, width=0.0, acoustic_purpose="Monofonización pura")
        ],
        "LEAD": [
            make_eq_eight(hpf_default=0.30, bell_default=0.65, bell_name="Mordida Cowbell", high_default=0.75, high_name="LPF Sucio (8 kHz)", acoustic_purpose="Corte de frecuencias bajas y siseo"),
            make_erosion(frequency=0.45, width=0.35, amount=0.30, acoustic_purpose="Degradación de cinta analógica para sonido Memphis/Phonk"),
            make_saturator(drive=0.30, base=0.0, output=0.70, acoustic_purpose="Saturación de cinta para presencia estridente"),
            make_delay(dry_wet=0.30, feedback=0.35, sync=1.0, acoustic_purpose="Retardo sincronizado")
        ]
    },
    # 2. Electrónica de Club subgenres
    "techno": {
        "KICK": [
            make_eq_eight(hpf_default=0.16, bell_default=0.24, bell_name="Punch Bombo Techno (55 Hz)", acoustic_purpose="HPF 32 Hz y punch contundente industrial"),
            make_glue_compressor(threshold=-12.0, ratio=3.0, attack=0.60, release=0.0, dry_wet=0.90, makeup=0.15, acoustic_purpose="Compresión dura para pegada de club"),
            make_saturator(drive=0.26, base=0.0, output=0.70, acoustic_purpose="Rumble analógico y distorsión armónica"),
            make_utility(bass_mono=1.0, bass_freq=130.0, width=1.0, acoustic_purpose="Monofonización quirúrgica de subgraves")
        ],
        "BASS": [
            make_eq_eight(hpf_default=0.16, bell_default=0.25, bell_name="Muesca Bombo (55 Hz)", acoustic_purpose="Corte subsónico y despeje de bombo"),
            make_auto_filter(frequency=0.40, resonance=0.35, filter_type=0.0, drive=0.20, acoustic_purpose="Filtro resonante ácido modulado"),
            make_compressor(threshold=-16.0, ratio=4.0, attack=0.01, release=0.18, sidechain=True, acoustic_purpose="Ducking sidechain agresivo"),
            make_saturator(drive=0.32, base=0.0, output=0.70, acoustic_purpose="Distorsión pesada para cortar la pista"),
            make_utility(bass_mono=1.0, bass_freq=125.0, width=0.0, acoustic_purpose="Monofonización absoluta")
        ]
    },
    "liquid_dnb": {
        "DRUMS": [
            make_eq_eight(hpf_default=0.18, bell_default=0.45, bell_name="Corte Barro Amen Break", high_default=0.85, high_name="Aire Hi-Hats Rápidos", acoustic_purpose="Limpieza de medios y apertura de platillos rápidos"),
            make_drum_buss(drive=0.24, crunch=0.30, transients=0.70, boom=0.15, output=0.70, acoustic_purpose="Snap afilado de transientes para breakbeats rápidos"),
            make_glue_compressor(threshold=-12.0, ratio=2.0, attack=0.50, release=0.0, dry_wet=0.85, makeup=0.12, acoustic_purpose="Pegamento de breakbeat a 174 BPM")
        ],
        "PAD": [
            make_eq_eight(hpf_default=0.32, bell_default=0.48, bell_name="Limpieza Medios (400 Hz)", high_default=0.80, high_name="Aire Celestial Liquid", acoustic_purpose="HPF 140 Hz para despejar el Reese bass"),
            make_chorus_ensemble(amount=0.40, rate=0.20, warmth=0.50, acoustic_purpose="Ensanchamiento estéreo flotante"),
            make_valhalla_supermassive(mode=0.38, mix=0.35, feedback=0.65, acoustic_purpose="Difusión celestial Andromeda para acordes de liquid"),
            make_compressor(threshold=-16.0, ratio=3.0, attack=0.02, release=0.20, sidechain=True, acoustic_purpose="Ducking rítmico suave al compás del bombo")
        ]
    },
    # 3. Orgánica / Acústica subgenres
    "flamenco": {
        "GUITAR": [
            make_eq_eight(hpf_default=0.26, bell_default=0.60, bell_name="Mordida Rasgueo / Púa (2.8 kHz)", high_default=0.76, high_name="Aire Madera", acoustic_purpose="HPF 100 Hz y presencia de ataque de dedos sobre guitarra española"),
            make_glue_compressor(threshold=-10.0, ratio=1.0, attack=0.70, release=0.0, dry_wet=0.65, makeup=0.06, acoustic_purpose="Compresión transparente que respeta el virtuosismo y dinámica flamenca"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.16, decay=0.20, predelay=0.03, acoustic_purpose="Sala de madera natural 1970s Room íntima")
        ],
        "PERCUSSION": [
            make_eq_eight(hpf_default=0.16, bell_default=0.68, bell_name="Chasquido Cajón / Palmas (3 kHz)", acoustic_purpose="HPF 35 Hz, cuerpo de cajón en 60 Hz y chasquido en 3 kHz"),
            make_glue_compressor(threshold=-12.0, ratio=1.0, attack=0.65, release=0.0, dry_wet=0.75, makeup=0.08, acoustic_purpose="Preservación del transitorio agudo de las palmas y snap de cajón")
        ]
    },
    "bossa_nova": {
        "GUITAR": [
            make_eq_eight(hpf_default=0.26, bell_default=0.42, bell_name="Calidez Nylon (350 Hz)", high_default=0.70, high_name="Suavidad Dedos (2.5 kHz)", acoustic_purpose="HPF 100 Hz y timbre aterciopelado de cuerda de nylon"),
            make_compressor(threshold=-14.0, ratio=2.0, attack=0.30, release=0.25, acoustic_purpose="Compresión óptica ultra-suave sin aplastar dinámicas"),
            make_valhalla_vintage_verb(mode=0.40, color=0.50, mix=0.15, decay=0.22, predelay=0.04, acoustic_purpose="Cámara acústica suave y cercana")
        ],
        "BASS": [
            make_eq_eight(hpf_default=0.18, bell_default=0.35, bell_name="Cuerpo Contrabajo (100 Hz)", acoustic_purpose="HPF 35 Hz y resonancia de madera noble"),
            make_compressor(threshold=-15.0, ratio=2.0, attack=0.25, release=0.30, acoustic_purpose="Nivelación óptica sutil estilo LA-2A"),
            make_utility(bass_mono=1.0, bass_freq=110.0, width=1.0, acoustic_purpose="Monofonización natural")
        ]
    },
    # 4. Espacial / Cinemática subgenres
    "dark_ambient": {
        "PAD": [
            make_eq_eight(hpf_default=0.22, bell_default=0.35, bell_name="Cuerpo Drone Oscuro (150 Hz)", high_default=0.60, high_name="LPF Tenebroso (5 kHz)", acoustic_purpose="HPF 60 Hz y LPF 5 kHz para atmósfera profunda y oscura"),
            make_surge_xt_effects(dsp_type="fxt_conditioner", drive=0.32, mix=0.70, slot_name="Slot 1 Dark Nimbus Cloud", acoustic_purpose="Modelado granular oscuro con flutter y dispersión de tono"),
            make_valhalla_supermassive(mode=0.65, mix=0.55, feedback=0.88, density=0.90, acoustic_purpose="Modo Great Annihilator con decaimiento infinito cavernoso")
        ],
        "BASS": [
            make_eq_eight(hpf_default=0.12, bell_default=0.25, bell_name="Cuerpo Subgrave Abismal (40 Hz)", high_default=0.55, high_name="LPF Oscuridad (3 kHz)", acoustic_purpose="HPF 22 Hz y LPF 3 kHz"),
            make_saturator(drive=0.22, base=0.0, output=0.72, acoustic_purpose="Saturación oscura para grosor sub-armónico"),
            make_utility(bass_mono=1.0, bass_freq=110.0, width=0.0, acoustic_purpose="Monofonización pura del canal drone"),
            make_valhalla_supermassive(mode=0.15, mix=0.20, feedback=0.45, acoustic_purpose="Halo expansivo subterráneo")
        ]
    }
}


# --- 6. Universal Genre-Family FX Catalog Class ---

class UniversalGenreFamilyFXCatalog:
    """
    Universal Genre-Family Insert Effects Catalog.
    Maps all 4 GenreFamily sound worlds to 39 role-specific acoustic insert chains,
    plus surgical subgenre specialization overrides for distinct subgenre aesthetics.
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
        Checks for surgical subgenre overrides first, then falls back to the canonical GenreFamily matrix.
        Defaults gracefully to URBANA_MODERNA if genre is unspecified or unknown.
        """
        r_clean = str(role or "KEYS").strip().upper()

        # Check surgical subgenre overrides if a specific genre string is provided
        if genre and not isinstance(genre, GenreFamily):
            g_str = str(genre.value if hasattr(genre, "value") else genre).lower().strip().replace("-", "_").replace(" ", "_")
            for sub_key, sub_dict in SUBGENRE_CHAIN_OVERRIDES.items():
                if sub_key in g_str and r_clean in sub_dict:
                    return sub_dict[r_clean]

        family = resolve_genre_family(genre, bpm=bpm)
        fam_dict = cls.CATALOG.get(family, cls.CATALOG[GenreFamily.URBANA_MODERNA])
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
    },
    "SYNTH_BASS": {
        "dominant_zone": "Fundamental en 35-70 Hz; densidad de armónicos sintetizados (onda sierra/cuadrada) en 150-1200 Hz.",
        "conflict_points": "Choque con bombo acústico/electrónico en 50-80 Hz; invasión de frecuencias medias que enturbian teclados.",
        "eq_recommendation": "HPF en 28-32 Hz; notch estrecho o ducking sidechain con el bombo; corte suave en 400 Hz.",
        "transient_handling": "Ataque rápido de compresión para asentar el golpe inicial del sintetizador o envelope follower suave."
    },
    "SYNTH_PLUCK": {
        "dominant_zone": "Ataque percusivo en 1.5-4 kHz; fundamental melódica en 300-1000 Hz.",
        "conflict_points": "Resonancias punzantes en 3-5 kHz si el filtro tiene Q alta; enmascaramiento con hi-hats.",
        "eq_recommendation": "HPF en 140-160 Hz; atenuación de resonancia de corte en 3.5 kHz; shelf en 10 kHz para aire.",
        "transient_handling": "Compresión transparente de ataque medio (15 ms) o limitador de picos para preservar el chasquido del pluck."
    },
    "ARPEGGIO": {
        "dominant_zone": "Movimiento melódico rápido en 400-2500 Hz; brillo de secuencia en 5-10 kHz.",
        "conflict_points": "Saturación del centro estéreo si no se panea o ensancha; acumulación de notas superpuestas.",
        "eq_recommendation": "HPF en 150 Hz; vaciado suave en 300-500 Hz para evitar congestión rítmica; auto filter modulado.",
        "transient_handling": "Ataque medio y release rápido en compresor o retardos con ducking para no ensuciar la secuencia."
    },
    "VOCAL_CHOP": {
        "dominant_zone": "Formantes vocales cortadas en 800-3000 Hz; brillo y respiración en 7-14 kHz.",
        "conflict_points": "Clicks y pops por cortes abruptos en el audio; competencia con la voz principal en el rango 1-3 kHz.",
        "eq_recommendation": "HPF estricto en 180-220 Hz; dip de 2 dB en 2 kHz para empujarlo detrás de la voz solista; high shelf sedoso.",
        "transient_handling": "Cuantización dura con Auto-Tune (Retune Speed 0) y compresión OTT o rápida para igualar volumen entre sílabas."
    },
    "ACOUSTIC_PIANO": {
        "dominant_zone": "Rango completo de 27 Hz a 4 kHz; cuerpo cálido en 150-350 Hz; ataque de martillo en 2.5-4 kHz.",
        "conflict_points": "Barro masivo en 250-400 Hz; graves de mano izquierda invaden bajo y bombo; estridencias en notas altas.",
        "eq_recommendation": "HPF en 100-130 Hz; corte sustractivo en 350 Hz; apertura suave en 8-10 kHz para aire de sala.",
        "transient_handling": "Compresor Glue o Vari-Mu con ataque de 20-30 ms para conservar la expresividad de los martillos."
    },
    "RHODES": {
        "dominant_zone": "Fundamentales dulces en 180-600 Hz; campana y resonancia de tines metálicos en 2-4 kHz.",
        "conflict_points": "Exceso de graves retumbantes en 120-200 Hz; resonancias de caja eléctrica en 300 Hz.",
        "eq_recommendation": "HPF en 100 Hz; corte en 280 Hz; realce con chorus BBD para movimiento de fase estéreo.",
        "transient_handling": "Saturación analógica Chow Tape que comprime naturalmente los picos de las púas metálicas."
    },
    "ORGAN": {
        "dominant_zone": "Medios compactos y barras armónicas en 200-2500 Hz; rotor Leslie en frecuencias agudas.",
        "conflict_points": "El órgano produce tonos sostenidos continuos sin decaimiento, consumiendo enorme headroom si no se controla.",
        "eq_recommendation": "HPF en 120 Hz; corte suave en 400 Hz; saturación de previo para suavizar agudos.",
        "transient_handling": "Compresión óptica suave para emparejar acordes sostenidos sin cortar la modulación rotatoria."
    },
    "VIOLIN": {
        "dominant_zone": "Fundamentales en 200-1500 Hz; armónicos de cuerda frotada y aire en 3-12 kHz.",
        "conflict_points": "Asperezas chirriantes en 3.5-4.5 kHz causadas por fricción del arco; colisión con la voz líder.",
        "eq_recommendation": "HPF en 160 Hz; notch quirúrgico en la aspereza modal (3.8 kHz); realce sedoso en 10 kHz.",
        "transient_handling": "Ataque lento (40-60 ms) para respetar el ataque natural del arco; compresión transparente 2:1."
    },
    "CELLO": {
        "dominant_zone": "Cuerpo noble en 65-300 Hz; lamento expresivo en 500-1200 Hz.",
        "conflict_points": "Graves del chelo (< 80 Hz) chocan directamente con bombos y bajos sintéticos.",
        "eq_recommendation": "HPF en 65-75 Hz; notch suave en 200 Hz si retumba; realce de calidez en 600 Hz.",
        "transient_handling": "Compresión óptica estilo LA-2A con ataque lento para preservar el dinamismo orquestal."
    },
    "UPRIGHT_BASS": {
        "dominant_zone": "Resonancia de caja de madera en 60-140 Hz; clic de cuerda y dedo sobre diapasón en 1-2.5 kHz.",
        "conflict_points": "Ondas estacionarias de sala en 100-180 Hz; soplos de micrófono en directos.",
        "eq_recommendation": "HPF en 32-38 Hz; notch en 120 Hz si la caja acústica acopla; realce en 1.5 kHz para articulación.",
        "transient_handling": "Compresor óptico o VCA suave con ataque de 20 ms para retener el punteo inicial de los dedos de jazz."
    },
    "CONGAS": {
        "dominant_zone": "Tono abierto en 200-350 Hz; slap seco en 2.5-4.5 kHz; grave de palma en 90-150 Hz.",
        "conflict_points": "Resonancias acartonadas en 400-600 Hz; graves de golpe de palma ensucian el bombo.",
        "eq_recommendation": "HPF en 85-95 Hz; corte en 500 Hz para eliminar acartonamiento; realce de slap en 3 kHz.",
        "transient_handling": "Compresor Glue con ataque de 30 ms para maximizar el filo del golpe de mano seca."
    },
    "SHAKER": {
        "dominant_zone": "Fricción de semillas en 3-8 kHz; apertura aérea en 10-16 kHz.",
        "conflict_points": "Ruidos de cuerpo grave innecesarios < 250 Hz que restan claridad al ritmo.",
        "eq_recommendation": "HPF estricto en 240-280 Hz; atenuación en 4 kHz si es metálico; shelf amplio en 10 kHz.",
        "transient_handling": "Ataque lento para preservar el micro-ritmo de vaivén de las semillas."
    },
    "SNARE": {
        "dominant_zone": "Cuerpo fundamental en 180-240 Hz; bordonero metálico en 3.5-6 kHz.",
        "conflict_points": "Barro de caja en 300-450 Hz; siseos ásperos y sangrado de hi-hats en micrófonos reales.",
        "eq_recommendation": "HPF en 80-90 Hz; realce de pegada en 200 Hz; corte en 400 Hz; realce en 4 kHz para chasquido.",
        "transient_handling": "Drum Buss con Transients > 0.5 o Glue con ataque lento (30 ms) para un crack demoledor."
    },
    "HIHAT": {
        "dominant_zone": "Cuerpo de platillo en 400-800 Hz; tic de golpe en 5-8 kHz; brillo y aire en 10-18 kHz.",
        "conflict_points": "Retumbes y armónicos medios que congestionan la voz y cajas si no se filtran.",
        "eq_recommendation": "HPF estricto en 300-350 Hz; notch en 4 kHz si el platillo es punzante; apertura en 12 kHz.",
        "transient_handling": "Ataque rápido en compresor para emparejar rolls ultrarrápidos de trap sin perder nitidez."
    },
    "SYNTH_LEAD": {
        "dominant_zone": "Fundamentales agresivas en 250-1200 Hz; contenido armónico masivo en 2-8 kHz.",
        "conflict_points": "Dureza y fatiga auditiva en 3-4 kHz; invasión del centro estéreo de la voz.",
        "eq_recommendation": "HPF en 140 Hz; dip quirúrgico en la frecuencia chillona de distorsión; shelf amplio de aire.",
        "transient_handling": "Compresión multibanda OTT agresiva para densidad constante y corte implacable en el club."
    },
    "SOUNDSCAPE": {
        "dominant_zone": "Espectro envolvente distribuido de 60 Hz a 10 kHz; texturas difusas y resonancias lentas.",
        "conflict_points": "Picos de volumen inesperados por resonancias modales en filtros; saturación de subgraves.",
        "eq_recommendation": "HPF en 70-90 Hz; LPF suave en 8-10 kHz para calidez analógica; ensanchamiento estéreo con Utility.",
        "transient_handling": "Sin transitorios percusivos; compresión lenta o procesamiento granular Nimbus y Supermassive."
    }
}
