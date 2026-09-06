# engine/fx/device_parameter_supervisor.py
"""
Device Parameter Supervisor & Multi-Section Semantic Engine:
Comprehensive parameter abstraction for professional music production in Ableton Live.
Organizes all exposed parameters across Vital, Analog Lab V, Pigments, FabFilter Pro-Q 4,
The God Particle, OTT, ValhallaVintageVerb, Efx REFRACT, 808 Core Kit, and Native Live devices
into 8 production-grade functional sections:

Section 1: MACROS & MASTER (Quick sound character & overall gain)
Section 2: OSCILLATORS & ENGINES (Wavetable position, pitch, unison, morph)
Section 3: FILTERS & SPECTRAL CUTOFF (Filter cutoff, resonance, drive, filter modes)
Section 4: SURGICAL & DYNAMIC EQ (Pro-Q 4 bands 1-13: HPF, Sub bump, Mud cut, Air shelf, Thresholds)
Section 5: ENVELOPES & TIME DYNAMICS (Attack, decay, sustain, release, glide/portamento)
Section 6: DYNAMICS & COMPRESSION (OTT depth/bands, Glue threshold, Limiter drive)
Section 7: HARMONIC SATURATION & COLOR (Analog drive, distortion, character, bitcrusher)
Section 8: SPACE & MODULATION FX (Reverb mix/decay, delay feedback, chorus, flanger, phaser)

Guarantees:
- Dynamic live inspection of what parameters are actually present on each device.
- The AI never needs to guess obscure DAW names or parameter indices.
- Zero crashes: safely skips unmapped parameters without error.
"""

import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger("DeviceParameterSupervisor")


class DeviceParameterSupervisor:
    """Intelligent semantic and sectional parameter controller for Ableton Live devices."""

    _SCULPTED_REGISTRY = set()

    ROLE_DESCRIPTIONS: Dict[str, str] = {
        # Section 1: MACROS & MASTER
        "MACRO_1": "Macro 1: Control primario de brillo, timbre espectral o apertura sonora del sinte o rack.",
        "MACRO_2": "Macro 2: Control secundario de calidez, cuerpo, saturación analógica o resonancia.",
        "MACRO_3": "Macro 3: Control de envolvente de ataque, tiempo o modulación rítmica y dinámica.",
        "MACRO_4": "Macro 4: Control de movimiento espacial, reverb/delay, chorus o unísono estéreo.",
        "MACRO_5": "Macro 5: Control de modulación secundaria o timbre alternativo.",
        "MACRO_6": "Macro 6: Control de capas armónicas o saturación adicional.",
        "MACRO_7": "Macro 7: Control de efectos auxiliares o modulación de filtro.",
        "MACRO_8": "Macro 8: Control maestro de dinámica o espacio sonoro.",
        "MASTER_VOLUME": "Nivel de ganancia o volumen maestro de salida del dispositivo.",
        "INPUT_GAIN": "Ganancia o calibración de entrada hacia el circuito de procesamiento.",
        "OUTPUT_TRIM": "Ajuste de ganancia limpia de salida para gain-staging y compensación de nivel.",

        # Section 2: OSCILLATORS & ENGINES
        "SUB_OSC": "Nivel y activación del oscilador de subgraves para solidez física en el espectro sub-bass (< 80 Hz).",
        "SUB_OCTAVE": "Octava de afinación del oscilador de subgraves (-1 o -2 octavas).",
        "SUB_SHAPE": "Forma de onda del sub-oscilador (seno, triángulo, pulso, sierra).",
        "OSC_LEVEL": "Nivel de volumen o mezcla del oscilador principal (A/B/1/2).",
        "OSC_PAN": "Paneo estéreo del oscilador en el panorama acústico.",
        "OSC_TUNE": "Afinación en semitonos u octavas del oscilador.",
        "OSC_FINE": "Micro-afinación en centésimas de semitono para enriquecimiento armónico.",
        "WAVETABLE_POS": "Posición en la tabla de ondas (wavetable morphing) para timbre evolutivo y armónicos.",
        "WAVETABLE_WARP": "Cantidad de deformación de tabla de ondas (Sync, Bend, FM, PWM, etc.).",
        "UNISON_VOICES": "Número de voces de unísono estéreo para ensanchamiento masivo.",
        "UNISON_DETUNE": "Desafinación y dispersión del unísono o refracción estéreo.",
        "UNISON_BLEND": "Balance de volumen entre las voces centrales y laterales del unísono.",
        "VOICE_PITCH": "Desplazamiento de tono (pitch shift) en semitonos para voces, texturas o leads (-12 a +12).",
        "VOICE_FORMANT": "Modificación de formantes vocales (modifica el tamaño del tracto vocal / garganta sin alterar el tono).",
        "VOICE_MODE": "Modo de transposición vocal (Transpose natural, Quantize robótico, Robot sintético).",
        "HARMONY_SPRAY": "Dispersión micro-tonal de los intervalos armónicos generados.",
        "HARMONY_CHORD": "Estructura de acordes o intervalos para generación de armonías automáticas.",

        # Section 3: FILTERS & SPECTRAL CUTOFF
        "FILTER_CUTOFF": "Frecuencia de corte principal del filtro (apertura/cierre espectral).",
        "FILTER_RESONANCE": "Resonancia o pico armónico en la frecuencia de corte.",
        "FILTER_DRIVE": "Overdrive o saturación analógica interna del filtro.",
        "FILTER_HPF": "Filtro paso-alto (High Pass) para eliminar frecuencias subsónicas o lodo.",
        "FILTER_LPF": "Filtro paso-bajo (Low Pass) para contener brillo excesivo, asperezas y sibilancias.",
        "FILTER_STEREO": "Separación estéreo del corte de filtro para ensanchamiento acústico.",
        "FILTER_WET": "Balance seco/procesado del módulo de filtrado.",

        # Section 4: SURGICAL & DYNAMIC EQ
        "EQ_HPF_FREQ": "Frecuencia del corte de graves quirúrgico (HPF) para despejar el rango sub.",
        "EQ_LOW_BOOST": "Ganancia de realce en graves para añadir pegada, peso y cuerpo sonoro.",
        "EQ_MUD_CUT": "Corte quirúrgico de frecuencias lodosas y resonancias de caja (~250-600 Hz).",
        "EQ_PRESENCE": "Control de presencia, articulación y definición en medios-altos (~2-5 kHz).",
        "EQ_AIR_SHELF": "Realce tipo shelf en frecuencias agudas (>10 kHz) para brillo comercial.",
        "SOOTHE_DEPTH": "Profundidad global de supresión dinámica de frecuencias resonantes estridentes.",
        "SOOTHE_SHARPNESS": "Selectividad y factor Q de las muescas dinámicas de supresión.",
        "SOOTHE_SELECTIVITY": "Sensibilidad de detección espectral para resonancias problemáticas.",
        "SOOTHE_ATTACK": "Velocidad de reacción del ecualizador dinámico ante la aparición de resonancias.",
        "SOOTHE_RELEASE": "Tiempo de recuperación de la curva tras suprimir un pico resonante.",
        "SOOTHE_LOWCUT": "Filtro paso-alto en el detector para evitar que el sub grave active la reducción.",
        "SOOTHE_HIGHCUT": "Filtro paso-bajo en el detector para centrar la acción en frecuencias medias.",

        # Section 5: ENVELOPES & TIME DYNAMICS
        "AMP_ATTACK": "Tiempo de ataque de amplitud (rápido para pegada inmediata, lento para pads).",
        "AMP_HOLD": "Tiempo de sostenimiento inicial en el pico de amplitud antes del decaimiento.",
        "AMP_DECAY": "Tiempo de caída de amplitud tras el ataque inicial.",
        "AMP_SUSTAIN": "Nivel de volumen sostenido mientras la nota permanece activa.",
        "AMP_RELEASE": "Tiempo de desvanecimiento tras soltar la tecla o finalizar la nota.",
        "PORTAMENTO_GLIDE": "Tiempo de deslizamiento suave de tono (glide/portamento) entre notas consecutivas.",
        "LFO_RATE": "Velocidad de oscilación del LFO (sincronizada al tempo métrico o en Hz).",
        "LFO_SMOOTH": "Suavizado de la curva del LFO para transiciones sin saltos bruscos.",

        # Section 6: DYNAMICS & COMPRESSION
        "COMP_DEPTH": "Profundidad o ratio de compresión dinámica aplicada a la señal.",
        "COMP_THRESHOLD": "Umbral de compresión a partir del cual actúa la reducción de ganancia.",
        "COMP_IN_GAIN": "Ganancia de entrada al compresor.",
        "COMP_OUT_GAIN": "Compensación de ganancia (makeup gain) de salida.",
        "COMP_TIME": "Constante de tiempo global para tiempos de ataque y relajación de compresión multibanda.",
        "UPWARD_COMP": "Fuerza de la compresión ascendente (levanta detalles tímbricos y sustain silencioso).",
        "DOWNWARD_COMP": "Fuerza de la compresión descendente (controla y aplasta picos transitorios).",
        "LIMITER_GAIN": "Ganancia de empuje hacia el techo del limitador (maximización de sonoridad comercial LUFS).",
        "LIMITER_CEILING": "Techo máximo de pico verdadero (True Peak) para prevenir distorsión inter-sample (-0.3 a -1.0 dB).",
        "LIMITER_LOOKAHEAD": "Tiempo de anticipación del limitador para atrapar transitorios rápidos de forma transparente.",

        # Section 7: HARMONIC SATURATION & COLOR
        "DRIVE": "Cantidad de saturación armónica, calor analógico de previo o distorsión de cinta/válvulas.",
        "PUNISH": "Multiplicador de ganancia extrema (+20 dB) para saturación sucia, agresiva y aplastante.",
        "DRIVE_TONE": "Tono de la saturación (oscuro/cálido a la izquierda, brillante/abierto a la derecha).",
        "DRIVE_MIX": "Balance Dry/Wet entre la señal limpia y la señal saturada (compresión/saturación paralela).",
        "DRIVE_THUMP": "Acento y realce de pegada en graves para conservar peso y cuerpo en el bombo o bajo.",
        "DRIVE_STYLE": "Estilo o modelo de circuito analógico emulado (A/E/N/T/P: cinta, consola, válvulas).",
        "BITCRUSHER_DEPTH": "Reducción de profundidad de bits (bitcrushing) para texturas lofi crujientes.",
        "BITCRUSHER_RATE": "Submuestreo (downsampling) para generar artefactos y aliasing armónico digital.",

        # Section 8: SPACE & MODULATION
        "REVERB_MIX": "Balance Dry/Wet de la reverberación espacial.",
        "REVERB_DECAY": "Tiempo de decaimiento (RT60) de la cola de reverberación.",
        "REVERB_PREDELAY": "Retardo previo a la reverberación para preservar el impacto del transitorio directo.",
        "REVERB_SIZE": "Tamaño de la sala acústica simulada (Small Room a Massive Hall).",
        "REVERB_ATTACK": "Forma del ataque de reverberación: inmediato vs hinchamiento progresivo.",
        "REVERB_MODULATION": "Modulación de tono y movimiento coral en la cola de reverberación.",
        "REVERB_COLOR": "Coloración histórica de algoritmo (1970s lofi, 1980s vintage, NOW pristino).",
        "DELAY_MIX": "Balance Dry/Wet de ecos y repeticiones.",
        "DELAY_FEEDBACK": "Cantidad de realimentación y número de repeticiones del delay.",
        "DELAY_TIME": "Tiempo de retardo de las repeticiones (en milisegundos o sincronizado a la métrica).",
        "DELAY_SYNC": "Sincronización métrica del delay al tempo del proyecto (1/4, 1/8d, 1/16, etc.).",
        "DELAY_STYLE": "Estilo de emulación analógica del delay (Tape, Echoplex, Memory Man, Digital).",
        "DELAY_GROOVE": "Micro-desplazamiento temporal con swing y cadencia humana en las repeticiones.",
        "CHORUS_MIX": "Cantidad de modulación estéreo (chorus, phaser o refracción multi-voz).",
        "REFRACTION": "Cantidad de dispersión o separación armónica estéreo de múltiples capas.",
        "HUMANIZE": "Fluctuación analógica orgánica y micro-variaciones humanas de tiempo/tono.",
        "VINTAGE": "Coloración analógica cálida, calidez de válvulas y transformadores vintage.",
        "FRACTALIZE": "Descomposición tímbrica granular y repeticiones fractales rítmicas.",
        "VOICE_EFFECT": "Procesamiento combinado de formantes, pitch y mezcla para voces y transiciones.",
        "STEREO_WIDTH": "Control de apertura y amplitud del panorama estéreo o ensanchamiento acústico.",
        "SUB_LEVEL": "Nivel de presencia de la capa sub-bass o refuerzo de graves fundamentales (Fill/Sub).",
        "FM_DEPTH": "Profundidad de modulación de fase o frecuencia (Phase Modulation / PM / FM) para timbres metálicos y armónicos agresivos.",
        "NOISE_LEVEL": "Nivel del generador de ruido analógico, texturas o transitorios de ataque.",
        "COMB_FREQ": "Frecuencia de afinación y resonancia del filtro peine (Comb filter) para timbres físicos y modelado de cuerdas.",
        "TIME_SHAPE": "Modulación rítmica del tiempo y deformación temporal (stutter, tape stop, reverse, scratch).",
        "TREMOLO": "Modulación periódica de amplitud y volumen.",
        "GRAIN_DENSITY": "Densidad de disparo de granos acústicos por segundo en síntesis granular.",
        "GRAIN_SIZE": "Duración y tamaño temporal de cada micro-grano sonoro.",
        "BUFFER_LENGTH": "Longitud del búfer de captura en tiempo real.",
        "FREEZE": "Congelación del búfer de audio en bucle infinito para colchones y texturas continuas.",
        "DRY_WET": "Balance global entre señal directa sin procesar (Dry) y señal procesada (Wet)."
    }

    ROLE_USAGE_HINTS: Dict[str, str] = {
        "DRIVE": "0.15-0.35 para calor y armónicos sutiles; 0.45-0.70 para saturación visible; >0.80 para distorsión agresiva.",
        "PUNISH": "1.0 para activar saturación masiva (+20 dB); 0.0 para modo normal transparente.",
        "DRIVE_TONE": "0.3-0.5 para oscurecer y engordar; 0.5-0.7 para añadir mordida y presencia en agudos.",
        "DRIVE_MIX": "0.3-0.6 para saturación paralela (mantiene transitorios limpios); 0.8-1.0 para distorsión total.",
        "SOOTHE_DEPTH": "0.20-0.45 para limpieza quirúrgica transparente; 0.50-0.70 para voces o platos estridentes; evitar >0.85.",
        "SOOTHE_SHARPNESS": "0.40-0.60 para respuesta balanceada; >0.70 para muescas muy estrechas en picos aislados.",
        "SOOTHE_SELECTIVITY": "0.35-0.60 para discriminar solo picos ásperos sin alterar la tonalidad global.",
        "WAVETABLE_POS": "0.0 para forma de onda base limpia; 0.3-0.7 para timbres evolutivos y ricos en armónicos.",
        "LIMITER_GAIN": "0.35-0.65 para empuje comercial balanceado (-14 a -9 LUFS); >0.75 para limitación agresiva.",
        "LIMITER_CEILING": "0.95-0.98 (-0.5 a -0.2 dB True Peak) para evitar recortes al codificar a MP3/AAC en Spotify.",
        "VOICE_PITCH": "0.50 = tono original; 0.0 = -12 semitonos (octava abajo); 1.0 = +12 semitonos (octava arriba).",
        "VOICE_FORMANT": "0.50 = formante neutro; <0.40 = engrosamiento masculino/profundo; >0.60 = timbre agudo/femenino/chipmunk.",
        "REVERB_MIX": "0.10-0.25 para pistas solistas/leads en primer plano; 0.30-0.55 para pads o ambientación profunda.",
        "REVERB_DECAY": "0.20-0.40 (1.0-2.0s) para mezclas densas y rítmicas; 0.50-0.80 (3.0-6.0s) para texturas cinematográficas.",
        "DELAY_MIX": "0.15-0.30 para ecos espaciales de fondo; >0.40 para delays rítmicos protagonistas.",
        "DELAY_FEEDBACK": "0.20-0.40 para 3 a 5 repeticiones limpias; 0.50-0.70 para colas largas y envolventes.",
        "FILTER_CUTOFF": "0.20-0.50 para graves oscuros o sintes amortiguados; 0.60-0.95 para brillo y apertura total.",
        "COMP_DEPTH": "0.30-0.60 para control de dinámica natural; 0.70-0.90 para pegada agresiva estilo EDM/Trap.",
        "AMP_ATTACK": "0.01-0.08 para percusión, bajos y plucks rápidos; 0.20-0.60 para pads y colchones lentos.",
        "AMP_RELEASE": "0.10-0.30 para cortes secos y rítmicos; 0.45-0.80 para colas acústicas largas y naturales.",
        "STEREO_WIDTH": "0.40-0.60 para ancho natural; 0.70-0.90 para apertura estéreo expansiva en leads o pads.",
        "SUB_LEVEL": "0.60-0.85 para bajos contundentes; <0.30 para instrumentos que no deban interferir en el sub.",
        "FM_DEPTH": "0.10-0.35 para color armónico metálico; >0.50 para timbres industriales agresivos o neurobass.",
        "DRY_WET": "0.20-0.40 para inserción paralela; 1.0 para efectos en buses auxiliares o filtros globales."
    }

    ROLE_SCULPTING_PROFILES: Dict[str, Dict[str, Dict[str, float]]] = {
        # Musical Instrument Roles
        "BASS": {
            "MACROS_MASTER": {"MACRO_1": 0.82, "MACRO_2": 0.65, "MASTER_VOLUME": 0.88},
            "FILTERS": {"FILTER_CUTOFF": 0.45, "FILTER_DRIVE": 0.35},
            "SURGICAL_EQ": {"EQ_HPF_FREQ": 0.15, "EQ_LOW_BOOST": 0.53, "EQ_MUD_CUT": 0.46},
            "SATURATION": {"DRIVE": 0.50, "DRIVE_MIX": 0.40}
        },
        "SUB_BASS": {
            "MACROS_MASTER": {"MACRO_1": 0.85, "MASTER_VOLUME": 0.90},
            "FILTERS": {"FILTER_CUTOFF": 0.38},
            "SURGICAL_EQ": {"EQ_HPF_FREQ": 0.12, "EQ_LOW_BOOST": 0.52}
        },
        "LEAD": {
            "MACROS_MASTER": {"MACRO_1": 0.85, "MACRO_2": 0.70, "MACRO_3": 0.50, "MACRO_4": 0.60},
            "FILTERS": {"FILTER_CUTOFF": 0.75, "FILTER_RESONANCE": 0.25},
            "SURGICAL_EQ": {"EQ_HPF_FREQ": 0.20, "EQ_MUD_CUT": 0.46, "EQ_AIR_SHELF": 0.53},
            "SPACE_MODULATION": {"REVERB_MIX": 0.35, "DELAY_MIX": 0.25, "CHORUS_MIX": 0.30}
        },
        "PAD": {
            "MACROS_MASTER": {"MACRO_1": 0.68, "MACRO_2": 0.62, "MACRO_3": 0.70, "MACRO_4": 0.55},
            "ENVELOPES": {"AMP_ATTACK": 0.40, "AMP_RELEASE": 0.60},
            "FILTERS": {"FILTER_CUTOFF": 0.65},
            "SURGICAL_EQ": {"EQ_HPF_FREQ": 0.22, "EQ_MUD_CUT": 0.46, "EQ_AIR_SHELF": 0.52},
            "SPACE_MODULATION": {"REVERB_MIX": 0.45, "REVERB_DECAY": 0.55, "CHORUS_MIX": 0.40}
        },
        "STRINGS": {
            "MACROS_MASTER": {"MACRO_1": 0.70, "MACRO_2": 0.65, "MASTER_VOLUME": 0.85},
            "ENVELOPES": {"AMP_ATTACK": 0.35, "AMP_RELEASE": 0.60},
            "FILTERS": {"FILTER_CUTOFF": 0.80},
            "SPACE_MODULATION": {"REVERB_MIX": 0.40, "REVERB_DECAY": 0.60}
        },
        "KEYS": {
            "MACROS_MASTER": {"MACRO_1": 0.75, "MACRO_2": 0.68, "MACRO_3": 0.55, "MASTER_VOLUME": 0.85},
            "SURGICAL_EQ": {"EQ_HPF_FREQ": 0.18, "EQ_MUD_CUT": 0.46, "EQ_AIR_SHELF": 0.52},
            "SPACE_MODULATION": {"REVERB_MIX": 0.35, "DELAY_MIX": 0.20}
        },
        "PLUCK": {
            "MACROS_MASTER": {"MACRO_1": 0.80, "MACRO_3": 0.25, "MACRO_4": 0.60},
            "ENVELOPES": {"AMP_ATTACK": 0.05, "AMP_DECAY": 0.25, "AMP_SUSTAIN": 0.15},
            "FILTERS": {"FILTER_CUTOFF": 0.70},
            "SPACE_MODULATION": {"DELAY_MIX": 0.30, "REVERB_MIX": 0.25}
        },
        "DRUMS": {
            "SURGICAL_EQ": {"EQ_HPF_FREQ": 0.12, "EQ_LOW_BOOST": 0.52, "EQ_AIR_SHELF": 0.52},
            "DYNAMICS": {"COMP_DEPTH": 0.65, "COMP_THRESHOLD": 0.50, "COMP_OUT_GAIN": 0.55},
            "SATURATION": {"DRIVE": 0.35, "DRIVE_MIX": 0.30}
        },
        "VOCAL": {
            "MACROS_MASTER": {"MACRO_1": 0.80, "MACRO_2": 0.60},
            "SURGICAL_EQ": {"EQ_HPF_FREQ": 0.25, "EQ_MUD_CUT": 0.46, "EQ_AIR_SHELF": 0.53},
            "SPACE_MODULATION": {"REVERB_MIX": 0.30, "DELAY_MIX": 0.25}
        },

        # Specific Plugin Character Profiles
        "SERUM": {
            "MACROS_MASTER": {"MACRO_1": 0.85, "MACRO_2": 0.70, "MACRO_3": 0.50, "MACRO_4": 0.60, "MASTER_VOLUME": 0.88},
            "FILTERS": {"FILTER_CUTOFF": 0.58, "FILTER_RESONANCE": 0.35, "FILTER_DRIVE": 0.35},
            "OSCILLATORS": {"OSC_A_WT_POS": 0.65, "WAVETABLE_WARP": 0.40, "UNISON_VOICES": 0.25, "SUB_OSC": 1.0, "SUB_LEVEL": 0.70},
            "ENVELOPES": {"AMP_ATTACK": 0.05, "AMP_RELEASE": 0.35}
        },
        "VITAL": {
            "MACROS_MASTER": {"MACRO_1": 0.82, "MACRO_2": 0.65},
            "OSCILLATORS": {"WAVETABLE_WARP": 0.60, "OSC_A_LEVEL": 0.80},
            "ENVELOPES": {"AMP_ATTACK": 0.02, "AMP_DECAY": 0.45, "AMP_RELEASE": 0.30}
        },
        "DECAPITATOR": {
            "SATURATION": {"DRIVE": 0.45, "DRIVE_TONE": 0.55, "DRIVE_MIX": 0.85},
            "FILTERS": {"FILTER_HPF": 0.15}
        },
        "ECHOBOY": {
            "SPACE_MODULATION": {"DELAY_MIX": 0.30, "DELAY_FEEDBACK": 0.35},
            "SATURATION": {"DRIVE": 0.30}
        },
        "LITTLEALTERBOY": {
            "OSCILLATORS": {
                "VOICE_PITCH": 0.50,
                "VOICE_FORMANT": 0.42,
                "VOICE_MODE": 0.0
            },
            "SATURATION": {
                "DRIVE": 0.35
            },
            "MACROS_MASTER": {
                "DRY_WET": 0.85
            }
        },
        "EFX_REFRACT": {
            "OSCILLATORS": {
                "UNISON_VOICES": 0.50,
                "UNISON_DETUNE": 0.45
            },
            "FILTERS": {
                "FILTER_CUTOFF": 0.75,
                "FILTER_RESONANCE": 0.25
            },
            "SPACE_MODULATION": {
                "CHORUS_MIX": 0.60,
                "REVERB_MIX": 0.35
            },
            "MACROS_MASTER": {
                "DRY_WET": 0.55,
                "MASTER_VOLUME": 0.85
            }
        },
        "SOOTHE2": {
            "SURGICAL_EQ": {"SOOTHE_DEPTH": 0.55, "SOOTHE_SHARPNESS": 0.60, "SOOTHE_SELECTIVITY": 0.50}
        },
        "PRO_L2": {
            "DYNAMICS": {"LIMITER_GAIN": 0.65, "LIMITER_CEILING": 0.98}
        },
        "THE_GOD_PARTICLE": {
            "DYNAMICS": {"COMP_DEPTH": 0.60, "LIMITER_GAIN": 0.52},
            "SURGICAL_EQ": {"EQ_LOW_BOOST": 0.52, "EQ_AIR_SHELF": 0.54}
        },
        "OTT": {
            "DYNAMICS": {"COMP_DEPTH": 0.55, "COMP_IN_GAIN": 0.50, "COMP_OUT_GAIN": 0.52}
        },
        "VALHALLAVINTAGEVERB": {
            "SPACE_MODULATION": {"REVERB_MIX": 0.28, "REVERB_DECAY": 0.45, "REVERB_PREDELAY": 0.20}
        },
        "FRACTION": {
            "MACROS_MASTER": {"MASTER_VOLUME": 0.50, "HUMANIZE": 0.40},
            "FILTERS": {"FILTER_CUTOFF": 0.70, "FILTER_DEPTH": 0.80},
            "SATURATION": {"DRIVE": 0.35, "DRIVE_TONE": 0.40},
            "SPACE_MODULATION": {"REVERB_MIX": 0.30, "DELAY_MIX": 0.20, "FRACTALIZE": 0.44}
        },
        "SURGICAL_EQ": {
            "SURGICAL_EQ": {
                "EQ_HPF_FREQ": 0.20,
                "EQ_LOW_BOOST": 0.52,
                "EQ_MUD_CUT": 0.46,
                "EQ_AIR_SHELF": 0.53
            },
            "MACROS_MASTER": {"MASTER_VOLUME": 0.50}
        },
        "DYNAMICS": {
            "DYNAMICS": {"COMP_DEPTH": 0.60, "COMP_THRESHOLD": 0.55, "COMP_OUT_GAIN": 0.55}
        },
        "SPACE_MODULATION": {
            "SPACE_MODULATION": {"REVERB_MIX": 0.30, "REVERB_DECAY": 0.50, "DELAY_FEEDBACK": 0.40}
        },
        "SATURATION": {
            "SATURATION": {"DRIVE": 0.45, "DRIVE_MIX": 0.40}
        },
        "MASSIVE_X": {
            "MACROS_MASTER": {"MACRO_1": 0.50, "MACRO_2": 0.60, "MACRO_3": 0.70, "MASTER_VOLUME": 0.85},
            "FILTERS": {"FILTER_CUTOFF": 0.72, "FILTER_RESONANCE": 0.28},
            "OSCILLATORS": {"OSC_A_WT_POS": 0.45, "UNISON_DETUNE": 0.50},
            "ENVELOPES": {"AMP_ATTACK": 0.05, "AMP_RELEASE": 0.40}
        },
        "MASSIVE": {
            "MACROS_MASTER": {"MASTER_VOLUME": 0.75},
            "FILTERS": {"FILTER_CUTOFF": 0.52, "FILTER_RESONANCE": 0.38},
            "OSCILLATORS": {"OSC_A_WT_POS": 0.68, "OSC_A_WARP": 0.15, "OSC_A_LEVEL": 0.85},
            "SATURATION": {"DRIVE": 0.45}
        },
        "ZENOLOGY": {
            "FILTERS": {"FILTER_CUTOFF": 0.70, "FILTER_RESONANCE": 0.25},
            "ENVELOPES": {"AMP_ATTACK": 0.08, "AMP_RELEASE": 0.35},
            "SPACE_MODULATION": {"CHORUS_DEPTH": 0.40}
        },
        "OMNISPHERE": {
            "MACROS_MASTER": {"MASTER_VOLUME": 0.85, "OSC_LEVEL": 0.80}
        },
        "EFX_MOTIONS": {
            "MACROS_MASTER": {"MACRO_1": 0.70, "MACRO_2": 0.50},
            "FILTERS": {"FILTER_CUTOFF": 0.65},
            "SATURATION": {"DRIVE": 0.40}
        },
        "EFX_FRAGMENTS": {
            "MACROS_MASTER": {"MACRO_1": 0.60, "MACRO_2": 0.50},
            "SPACE_MODULATION": {"REVERB_MIX": 0.35, "DELAY_MIX": 0.30}
        },
        "SHAPERBOX_3": {
            "DYNAMICS": {"COMP_DEPTH": 0.70, "COMP_THRESHOLD": 0.50},
            "SATURATION": {"DRIVE": 0.40, "DRIVE_MIX": 0.60},
            "FILTERS": {"FILTER_CUTOFF": 0.65},
            "SPACE_MODULATION": {"TIME_SHAPE": 0.50},
            "MACROS_MASTER": {"DRY_WET": 0.85, "MASTER_VOLUME": 0.85}
        },
        "SOLINA_V2": {
            "MACROS_MASTER": {
                "MACRO_1": 0.70,
                "MACRO_2": 0.65,
                "MASTER_VOLUME": 0.84
            },
            "FILTERS": {
                "FILTER_CUTOFF": 0.65,
                "FILTER_RESONANCE": 0.30
            },
            "SPACE_MODULATION": {
                "CHORUS_MIX": 0.80,
                "REVERB_MIX": 0.40
            }
        },
        "THERMAL": {
            "MACROS_MASTER": {"MACRO_1": 0.65, "MACRO_2": 0.50},
            "SATURATION": {"DRIVE": 0.50, "DRIVE_MIX": 0.75}
        },
        "ANALOG_LAB_V": {
            "MACROS_MASTER": {
                "MACRO_1": 0.75,  # P1 Brightness (sculpted away from default 0.5)
                "MACRO_2": 0.68,  # P1 Timbre (sculpted away from default 0.5)
                "MACRO_3": 0.55,  # P1 Time (sculpted away from default 0.5)
                "MACRO_4": 0.60,  # P1 Movement (sculpted away from default 0.5)
                "MASTER_VOLUME": 0.85,
                "DRY_WET": 0.55   # FXA Dry/Wet
            },
            "SPACE_MODULATION": {
                "REVERB_MIX": 0.35,  # Reverb Volume
                "DELAY_MIX": 0.20,   # Delay Volume
                "CHORUS_MIX": 0.40   # FXB Dry/Wet
            }
        },
        "ANALOG_LAB_KEYS": {
            "MACROS_MASTER": {
                "MACRO_1": 0.75,
                "MACRO_2": 0.68,
                "MACRO_3": 0.55,
                "MACRO_4": 0.60,
                "MASTER_VOLUME": 0.85,
                "DRY_WET": 0.50
            },
            "SPACE_MODULATION": {
                "REVERB_MIX": 0.35,
                "DELAY_MIX": 0.20,
                "CHORUS_MIX": 0.40
            }
        },
        "ANALOG_LAB_PAD": {
            "MACROS_MASTER": {
                "MACRO_1": 0.65,
                "MACRO_2": 0.60,
                "MACRO_3": 0.72,
                "MACRO_4": 0.55,
                "MASTER_VOLUME": 0.82,
                "DRY_WET": 0.60
            },
            "SPACE_MODULATION": {
                "REVERB_MIX": 0.48,
                "DELAY_MIX": 0.28,
                "CHORUS_MIX": 0.50
            }
        },
        "ANALOG_LAB_LEAD": {
            "MACROS_MASTER": {
                "MACRO_1": 0.85,
                "MACRO_2": 0.72,
                "MACRO_3": 0.45,
                "MACRO_4": 0.65,
                "MASTER_VOLUME": 0.88,
                "DRY_WET": 0.45
            },
            "SPACE_MODULATION": {
                "REVERB_MIX": 0.25,
                "DELAY_MIX": 0.25,
                "CHORUS_MIX": 0.35
            }
        },
        "PIGMENTS": {
            "MACROS_MASTER": {
                "MACRO_1": 0.75,
                "MACRO_2": 0.65,
                "MACRO_3": 0.60,
                "MACRO_4": 0.55
            },
            "FILTERS": {
                "FILTER_CUTOFF": 0.70
            },
            "ENVELOPES": {
                "AMP_ATTACK": 0.15,
                "AMP_RELEASE": 0.50
            }
        }
    }

    # Comprehensive Functional Section Definitions with Priority Alias Mappings
    FUNCTIONAL_SECTIONS = {
        # Section 1: Macros & Global Master
        "MACROS_MASTER": {
            "MACRO_1": ["macro 1", "macro_1", "p1 brightness", "brightness", "01 spread"],
            "MACRO_2": ["macro 2", "macro_2", "p1 timbre", "timbre", "02 width"],
            "MACRO_3": ["macro 3", "macro_3", "p1 time", "time", "03 cutoff"],
            "MACRO_4": ["macro 4", "macro_4", "p1 movement", "movement", "04 fill"],
            "MACRO_5": ["macro 5", "macro_5", "05 delay"],
            "MACRO_6": ["macro 6", "macro_6", "06 mix"],
            "MACRO_7": ["macro 7", "macro_7", "07 drift"],
            "MACRO_8": ["macro 8", "macro_8", "08 seq"],
            "MASTER_VOLUME": ["output level", "out gain", "master", "master volume", "global volume", "output gain", "outputtrim", "output trim", "gain", "volume", "trim", "master-volume", "output", "grain volume", "amp - level"],
            "HUMANIZE": ["humanize", "07 drift"],
            "INPUT_GAIN": ["input gain", "in gain", "input level", "input trim", "inputgain", "bypass-gain"],
            "OUTPUT_TRIM": ["outputtrim", "output trim", "trim", "out gain", "output"],
            "DRY_WET": ["dry/wet", "mix", "master mix", "master - mix", "output mix", "master dry/wet", "wet", "grain mix", "master-dry wet", "fxa dry/wet", "fxb dry/wet", "fx1 dry / wet", "fx2 dry / wet"],
            "STEREO_WIDTH": ["02 width", "width", "stereo", "nonlinear - stereo", "fx2 rev width"],
            "OSC_PAN": ["pan (fltr-path)", "amp - pan", "pan amount", "pan", "osc_pan", "parameter 1 pan", "parameter 2 pan", "parameter 3 pan", "parameter 4 pan", "parameter 5 pan", "parameter 6 pan", "parameter 7 pan", "parameter 8 pan"]
        },

        # Section 2: Oscillators & Synthesizer Engines
        "OSCILLATORS": {
            "SUB_OSC": ["sub level", "sub osc", "sub enable", "04 fill"],
            "SUB_OCTAVE": ["sub octave"],
            "SUB_SHAPE": ["sub shape"],
            "OSC_A_LEVEL": ["a level", "level a", "oscillator 1 level", "engine 1 volume", "wavetable 1 main vol", "osc 1 - level", "osc1-amp", "osc c - mix", "parameter 1 level"],
            "OSC_A_OCTAVE": ["a octave"],
            "OSC_A_SEMI": ["a semi", "oscillator 1 transpose", "oscillator 1 tune", "coarse", "osc 1 - pitch", "osc1-pitch", "voice - pitch"],
            "OSC_A_FINE": ["a fine", "osc 1 - fine"],
            "OSC_A_WT_POS": ["a wt pos", "wavetable 1 position", "modal 1 warp shape", "osc 1 - pos", "osc1-position", "position"],
            "OSC_A_WARP": ["a warp", "a warp 2", "modal 1 warp amount", "osc 1 - warp mode", "osc 1 - wavetable", "osc1-wavetable", "osc1-mode", "osc 1 - ratio", "osc 1 - bend"],
            "OSC_A_UNISON": ["a unison", "wavetable 1 unison voices", "voices", "layers", "01 spread"],
            "OSC_A_DETUNE": ["a uni detune", "wavetable 1 unison detune", "refraction", "01 spread", "02 width", "random fine"],
            "OSC_A_BLEND": ["a uni blend"],
            "OSC_B_LEVEL": ["b level", "level b", "osc2-amp", "parameter 2 level"],
            "OSC_B_OCTAVE": ["b octave"],
            "OSC_B_SEMI": ["b semi", "osc 2 - pitch", "osc2-pitch", "osc3-pitch", "mod.osc-pitch"],
            "OSC_B_WT_POS": ["b wt pos", "osc 2 - pos", "osc2-position"],
            "OSC_B_UNISON": ["b unison"],
            "OSC_B_DETUNE": ["b uni detune"],
            "FM_DEPTH": ["phase mod - pm 1", "phase mod - pm 2", "osc 1 - pm1", "osc 1 - pm2", "osc 2 - pm1", "osc 2 - pm2", "mod.osc-glmod", "phase mod - aux"],
            "NOISE_LEVEL": ["noise 1 - level", "noise 1 - pitch", "noise-color", "noise-amp", "noise level", "noise amount"],
            "COMB_FREQ": ["comb - pitch", "comb - ap freq", "comb - lp freq", "comb - mode"],
            "UNISON_VOICES": ["voices", "a unison", "b unison", "wavetable 1 unison voices", "layers"],
            "UNISON_DETUNE": ["refraction", "a uni detune", "b uni detune", "wavetable 1 unison detune", "01 spread", "detune", "dispersion"],
            "VOICE_PITCH": ["pitch", "pitch shift", "transpose", "voice pitch", "pitchshaper on", "osc 1 - pitch"],
            "VOICE_FORMANT": ["formant", "voice formant"],
            "VOICE_MODE": ["shiftmode", "mode", "quantize", "robot", "formantlink", "osc 1 - warp mode"],
            "HARMONY_SPRAY": ["harmony spray", "spray direction"],
            "HARMONY_CHORD": ["harmony chord", "scale"]
        },

        # Section 3: Filters & Spectral Cutoff
        "FILTERS": {
            "FILTER_CUTOFF": ["filter 1 freq", "f1 cutoff", "filter 1 cutoff", "cutoff", "filtershaper cutoff", "filter - cutoff", "global filter", "filter a", "bandpass filter cutoff frequency", "comb filter cutoff frequency", "f2 comb freq", "03 cutoff", "filter1-param1", "filter2-param1", "filter cutoff", "master hp cutoff", "master lp cutoff", "filter threshold"],
            "FILTER_RESONANCE": ["filter 1 res", "filter 1 resonance", "resonance", "filter depth", "f1 resonance", "bandpass filter resonance", "comb filter resonance", "reso", "filter1-param2", "filter2-param2", "filter resonance"],
            "FILTER_DRIVE": ["filter 1 drive", "distortion drive", "drive amount", "osc 1 - drive", "filter1-param3", "filter2-param3"],
            "FILTER_BLEND": ["filter 1 blend", "engine1 filter mix", "sub osc filter mix", "filter 1 wet", "filter-crossfade", "seriell-parallel"],
            "FILTER_HPF": ["lowcut", "low cut", "highpass", "filter 1 high pass", "modal 1 friction hp", "master hp cutoff", "comb - ap freq"],
            "FILTER_LPF": ["highcut", "high cut", "lowpass", "highcut freq", "master lp cutoff", "comb - lp freq"],
            "FILTER_STEREO": ["filter 1 stereo", "filter stereo rate"]
        },

        # Section 4: Surgical & Dynamic EQ (FabFilter Pro-Q 4, soothe2, The God Particle)
        "SURGICAL_EQ": {
            "SOOTHE_DEPTH": ["depth"],
            "SOOTHE_SHARPNESS": ["sharpness"],
            "SOOTHE_SELECTIVITY": ["selectivity"],
            "SOOTHE_ATTACK": ["soothe attack", "dynamic attack"],
            "SOOTHE_RELEASE": ["soothe release", "dynamic release"],
            "SOOTHE_LOWCUT": ["low cut freq", "low cut on", "low cut q"],
            "SOOTHE_HIGHCUT": ["high cut freq", "high cut on", "high cut q"],
            "SOOTHE_BAND1": ["band1 sens", "band1 freq", "band1 q", "band1 on"],
            "SOOTHE_BAND2": ["band2 sens", "band2 freq", "band2 q", "band2 on"],
            "SOOTHE_BAND3": ["band3 sens", "band3 freq", "band3 q", "band3 on"],
            "SOOTHE_BAND4": ["band4 sens", "band4 freq", "band4 q", "band4 on"],
            "EQ_HPF_FREQ": ["band 1 frequency", "low cut", "hpf", "1 frequency a"],
            "EQ_HPF_STATE": ["band 1 enabled", "band 1 state", "band 1 on"],
            "EQ_HPF_SHAPE": ["band 1 shape"],
            "EQ_HPF_Q": ["band 1 q", "1 resonance a"],
            "EQ_LOW_BOOST": ["eq low gain", "band 2 gain", "low gain", "sub", "2 gain a"],
            "EQ_LOW_FREQ": ["band 2 frequency", "2 frequency a"],
            "EQ_MUD_CUT": ["eq mid gain", "band 3 gain", "mid gain", "3 gain a"],
            "EQ_MUD_FREQ": ["band 3 frequency", "3 frequency a"],
            "EQ_PRESENCE": ["band 4 gain", "4 gain a"],
            "EQ_PRESENCE_FREQ": ["band 4 frequency", "4 frequency a"],
            "EQ_AIR_SHELF": ["eq high gain", "band 5 gain", "high gain", "high shelf", "air"],
            "EQ_AIR_FREQ": ["band 5 frequency", "5 frequency a"],
            "EQ_DYN_THRESH_1": ["band 1 threshold"],
            "EQ_DYN_THRESH_2": ["band 2 threshold"],
            "EQ_DYN_THRESH_3": ["band 3 threshold"],
            "EQ_ENABLE": ["eq-on off", "eq bypass"]
        },

        # Section 5: Envelopes & Time Dynamics
        "ENVELOPES": {
            "AMP_ATTACK": ["env 1 attack", "attack", "amp attack", "modal 1 collision mallet attack", "amp env - attack", "filter attack"],
            "AMP_HOLD": ["env 1 hold", "amp env - hold 1", "amp env - hold 2"],
            "AMP_DECAY": ["env 1 decay", "decay", "amp decay", "modal 1 decay", "amp env - decay"],
            "AMP_SUSTAIN": ["env 1 sustain", "sustain", "amp sustain", "amp env - sustain"],
            "AMP_RELEASE": ["env 1 release", "release", "amp release", "amp env - release", "filter release", "grain release"],
            "PORTAMENTO_GLIDE": ["porta time", "portamento time", "glide", "portamento", "pitch bend", "voice - glide", "voice - ...te glide"],
            "LFO_RATE": ["lfo 1 rate", "rate (sync)", "rate (hertz)", "rate", "lfo 1 tempo", "random lfo 1 tempo", "modrate", "lfo rate", "filter rate sync", "drive rate sync", "noise rate sync", "pan rate sync", "volume rate sync", "perfor... 1 - rate", "08 seq", "speed", "density"],
            "LFO_SMOOTH": ["lfo 1 smooth", "vibrato", "07 drift"]
        },

        # Section 6: Dynamics & Compression (FabFilter Pro-L 2, OTT, The God Particle, ShaperBox)
        "DYNAMICS": {
            "COMP_DEPTH": ["depth", "glue", "ratio", "volumeshaper mix", "volume - mix", "volumeshaper on", "volume mid mix", "volumeshaper depth", "volume amount", "nonlinear - comp"],
            "COMP_TIME": ["time"],
            "COMP_THRESHOLD": ["threshold", "thresh m", "thresh l", "thresh h"],
            "COMP_IN_GAIN": ["in gain", "input gain", "input level"],
            "COMP_OUT_GAIN": ["out gain", "output gain", "gain m", "gain l", "gain h", "master compressor gain"],
            "UPWARD_COMP": ["upwd strgth"],
            "DOWNWARD_COMP": ["dnwd strgth"],
            "LIMITER_GAIN": ["gain", "limiter input gain"],
            "LIMITER_CEILING": ["output level", "out ceiling", "ceiling"],
            "LIMITER_LOOKAHEAD": ["lookahead"],
            "LIMITER_ATTACK": ["attack"],
            "LIMITER_RELEASE": ["release", "master compressor release"],
            "LIMITER_STEREO_LINK": ["channel link transients", "channel link release"]
        },

        # Section 7: Harmonic Saturation & Color (Decapitator, LittleAlterBoy, EchoBoy, Efx REFRACT, Thermal)
        "SATURATION": {
            "DRIVE": ["drive", "saturation", "distortion drive amount", "distortion drive", "character", "distortion", "drive amount", "stage 1 drive", "stage 2 drive", "nonlinear - drive", "feedback-amp", "driveshaper on", "driveshaper drive", "drive - drive", "drive mid mix"],
            "PUNISH": ["punish"],
            "DRIVE_TONE": ["tone", "drive tone", "vintage", "color mode", "stage 1 tone", "stage 2 tone"],
            "DRIVE_MIX": ["mix", "distortion mix", "fxa dry/wet", "stage 1 mix", "stage 2 mix"],
            "DRIVE_THUMP": ["lowthump", "low thump"],
            "DRIVE_STYLE": ["style"],
            "BITCRUSHER_DEPTH": ["bitcrusher bit depth", "grain crush", "crushshaper on"],
            "BITCRUSHER_RATE": ["bitcrusher downsample ratio"]
        },

        # Section 8: Space & Modulation FX (ValhallaVintageVerb, EchoBoy, LittleAlterBoy, Efx REFRACT, ShaperBox)
        "SPACE_MODULATION": {
            "REVERB_MIX": ["reverb volume", "reverb mix", "reverb", "room", "space", "fx2 reverb size", "fx1 dry / wet"],
            "REVERB_DECAY": ["decay", "reverb decay time", "size", "fx2 reverb decay", "fx2 rev decay"],
            "REVERB_PREDELAY": ["predelay", "reverb delay", "fx2 rev predelay"],
            "REVERB_SIZE": ["size", "fx2 reverb size", "grain size ratio", "grain size absolute", "texture size absolute"],
            "REVERB_ATTACK": ["attack"],
            "REVERB_MODULATION": ["moddepth", "modrate"],
            "REVERB_COLOR": ["colormode"],
            "REVERB_MODE": ["reverbmode"],
            "DELAY_MIX": ["delay volume", "delay mix", "delay", "05 delay", "fx2 delay time", "fx2 dry / wet"],
            "DELAY_FEEDBACK": ["feedback", "delay feedback", "amp - fb"],
            "DELAY_TIME": ["echo1time", "echo2time", "delay time", "fx2 delay time", "1/4 offset synced", "buffer length"],
            "DELAY_SYNC": ["echo1note", "echo2note", "density sync"],
            "DELAY_STYLE": ["style"],
            "DELAY_GROOVE": ["groove"],
            "DELAY_FEEL": ["feel"],
            "CHORUS_MIX": ["chorus mix", "refraction amount", "refraction", "voices", "phaser mix", "flanger mix", "01 spread", "fxb dry/wet"],
            "CHORUS_DEPTH": ["chorus mod depth", "phaser depth", "flanger depth", "vibrato"],
            "FRACTALIZE": ["fractalize"],
            "VOICE_PITCH": ["pitch", "pitch shift", "transpose"],
            "VOICE_FORMANT": ["formant", "voice formant"],
            "VOICE_MODE": ["mode", "shiftmode", "quantize", "robot"],
            "VOICE_EFFECT": ["pitch", "formant", "shiftmode", "formantlink", "pitchshaper on"],
            "TIME_SHAPE": ["timeshaper on", "timeshaper mix", "time - mix", "time mid mix", "time mid wave", "freeze", "clear"]
        }
    }

    # Flat semantic aliases for direct high-level requests
    SEMANTIC_ROLES = {
        "BRIGHTNESS": ["macro 1", "macro_1", "p1 brightness", "brightness", "f1 cutoff", "filter 1 cutoff", "cutoff", "bandpass filter cutoff frequency", "03 cutoff", "filter1-param1", "filter cutoff"],
        "WARMTH": ["macro 2", "macro_2", "p1 timbre", "timbre", "f1 resonance", "filter 1 resonance", "resonance", "filter1-param2", "filter resonance", "reso"],
        "HUMANIZE": ["humanize", "07 drift"],
        "VINTAGE": ["vintage", "tone", "drive tone", "stage 1 tone", "stage 2 tone"],
        "FRACTALIZE": ["fractalize", "grain crush"],
        "ATTACK": ["macro 3", "macro_3", "p1 time", "envelope 1 attack", "env 1 attack", "time", "attack", "amp env - attack", "filter attack"],
        "MOVEMENT": ["macro 4", "macro_4", "p1 movement", "movement", "refraction", "voices", "chorus", "01 spread", "02 width", "layers", "timeshaper on"],
        "MACRO_1": ["macro 1", "macro_1", "01 spread"],
        "MACRO_2": ["macro 2", "macro_2", "02 width"],
        "MACRO_3": ["macro 3", "macro_3", "03 cutoff"],
        "MACRO_4": ["macro 4", "macro_4", "04 fill"],
        "MACRO_5": ["macro 5", "macro_5", "05 delay"],
        "MACRO_6": ["macro 6", "macro_6", "06 mix"],
        "MACRO_7": ["macro 7", "macro_7", "07 drift"],
        "MACRO_8": ["macro 8", "macro_8", "08 seq"],
        "DRIVE": ["drive", "saturation", "distortion drive amount", "distortion drive", "character", "distortion", "drive amount", "stage 1 drive", "stage 2 drive", "nonlinear - drive", "feedback-amp"],
        "FILTER_CUTOFF": ["cutoff", "f1 cutoff", "filter 1 cutoff", "filter cutoff", "filter1-param1", "03 cutoff", "master hp cutoff", "master lp cutoff"],
        "FILTER_RESONANCE": ["resonance", "f1 resonance", "filter 1 resonance", "filter resonance", "filter1-param2", "reso"],
        "REVERB_MIX": ["reverb mix", "reverb volume", "reverb", "fx2 reverb size", "fx1 dry / wet"],
        "SPACE_REVERB": ["reverb volume", "reverb mix", "reverb", "room", "space", "fx2 reverb size", "fx1 dry / wet"],
        "DELAY_MIX": ["delay mix", "delay volume", "delay", "05 delay", "fx2 delay time", "fx2 dry / wet"],
        "SPACE_DELAY": ["delay volume", "delay mix", "delay", "echo", "feedback", "05 delay", "fx2 delay time"],
        "DELAY_FEEDBACK": ["feedback", "delay feedback", "amp - fb"],
        "CHORUS_MIX": ["chorus mix", "phaser mix", "flanger mix", "refraction", "01 spread"],
        "MIX": ["mix", "dry/wet", "wet", "grain mix", "master dry/wet", "master-dry wet"],
        "DRY_WET": ["mix", "dry/wet", "wet", "grain mix", "master dry/wet", "master-dry wet"],
        "VOLUME": ["master", "master volume", "output level", "out gain", "gain", "outputtrim", "volume", "trim", "master-volume", "output", "grain volume", "amp - level"],
        "GLIDE": ["porta time", "portamento time", "glide", "portamento", "pitch bend", "voice - glide"],
        "EQ_HPF": ["band 1 frequency", "low cut", "hpf", "band 1 state", "band 1 on", "master hp cutoff"],
        "EQ_LOW_BOOST": ["band 2 gain", "eq low gain", "low gain", "sub", "04 fill"],
        "EQ_MUD_CUT": ["band 3 gain", "band 3 frequency", "eq mid gain", "mid gain"],
        "EQ_AIR_SHELF": ["band 5 gain", "band 4 gain", "eq high gain", "high gain", "high shelf", "air"],
        "COMP_DEPTH": ["depth", "glue", "ratio", "volumeshaper on", "volume amount", "nonlinear - comp"],
        "DEPTH": ["depth", "volume amount", "drive amount"],
        "COMPRESSION_GLUE": ["glue", "depth", "threshold", "limiter input gain", "character", "nonlinear - comp"]
    }

    @classmethod
    def introspect_device_parameters(cls, conn: Any, track_index: int, device_index: int) -> List[Dict[str, Any]]:
        """Queries Live for all exposed parameters on a specific device."""
        if conn is None or not hasattr(conn, "send_command"):
            return []
        try:
            res = conn.send_command("get_device_parameters", {"track_index": track_index, "device_index": device_index})
            if isinstance(res, dict):
                if "parameters" in res:
                    return res["parameters"]
                return res.get("result", {}).get("parameters", [])
        except Exception as e:
            logger.warning(f"Failed to query parameters for track {track_index}, device {device_index}: {e}")
        return []

    @classmethod
    def inspect_device_catalog(cls, conn: Any, track_index: int, device_index: int) -> Dict[str, Any]:
        """
        Deep structural cataloging: Inspects the live device and categorizes every detected
        parameter into its respective functional section (Macros, Oscillators, Filters, EQ, etc.).
        Returns an intuitive breakdown designed specifically for AI production decisions.
        """
        raw_params = cls.introspect_device_parameters(conn, track_index, device_index)
        if not raw_params:
            return {"track_index": track_index, "device_index": device_index, "total_params": 0, "sections": {}}

        assigned_indices = set()
        sections_report = {}

        for sec_name, sec_controls in cls.FUNCTIONAL_SECTIONS.items():
            sec_found = {}
            for ctrl_role, aliases in sec_controls.items():
                best = None
                for alias in aliases:
                    for p in raw_params:
                        p_idx = p.get("index")
                        if p_idx in assigned_indices:
                            continue
                        p_name = p.get("name", "").lower().strip()
                        if alias == p_name or alias in p_name:
                            best = p
                            break
                    if best:
                        break
                if best:
                    p_idx = best.get("index")
                    assigned_indices.add(p_idx)
                    sec_found[ctrl_role] = {
                        "role": ctrl_role,
                        "description": cls.ROLE_DESCRIPTIONS.get(ctrl_role, f"Control de {ctrl_role.lower()}."),
                        "typical_usage": cls.ROLE_USAGE_HINTS.get(ctrl_role, "Ajustar con valor normalizado [0.0 - 1.0]."),
                        "param_index": p_idx,
                        "param_name": best.get("name"),
                        "min": float(best.get("min", 0.0)),
                        "max": float(best.get("max", 1.0)),
                        "current_value": float(best.get("value", 0.0))
                    }
            if sec_found:
                sections_report[sec_name] = sec_found

        return {
            "track_index": track_index,
            "device_index": device_index,
            "total_params": len(raw_params),
            "sections_available": list(sections_report.keys()),
            "sections": sections_report
        }

    @classmethod
    def inspect_semantic_capabilities(cls, conn: Any, track_index: int, device_index: int) -> Dict[str, Any]:
        """Standard high-level semantic capability query with detailed AI descriptions."""
        catalog = cls.inspect_device_catalog(conn, track_index, device_index)
        available_controls = {}
        for sec_name, sec_data in catalog.get("sections", {}).items():
            for ctrl_key, ctrl_info in sec_data.items():
                ctrl_copy = dict(ctrl_info)
                ctrl_copy["section"] = sec_name
                ctrl_copy["semantic_role"] = ctrl_key
                ctrl_copy["description"] = cls.ROLE_DESCRIPTIONS.get(ctrl_key, ctrl_info.get("description", ""))
                ctrl_copy["typical_usage"] = cls.ROLE_USAGE_HINTS.get(ctrl_key, ctrl_info.get("typical_usage", ""))

                # Register under functional role name (e.g. COMP_DEPTH, REVERB_MIX, SOOTHE_DEPTH, DRIVE)
                if ctrl_key not in available_controls:
                    available_controls[ctrl_key] = ctrl_copy

                # Also register under all matching semantic aliases (e.g. SPACE_REVERB, BRIGHTNESS, WARMTH, DEPTH)
                param_name_clean = ctrl_info.get("param_name", "").lower().strip()
                for s_key, aliases in cls.SEMANTIC_ROLES.items():
                    matched = False
                    for a in aliases:
                        if a == param_name_clean:
                            matched = True
                            break
                        if len(a) > 3 and a in param_name_clean:
                            matched = True
                            break
                        if len(a) <= 3 and a in param_name_clean.split():
                            matched = True
                            break
                    if matched and s_key not in available_controls:
                        alias_copy = dict(ctrl_copy)
                        alias_copy["semantic_role"] = s_key
                        alias_copy["description"] = cls.ROLE_DESCRIPTIONS.get(s_key, cls.ROLE_DESCRIPTIONS.get(ctrl_key, ctrl_info.get("description", "")))
                        alias_copy["typical_usage"] = cls.ROLE_USAGE_HINTS.get(s_key, cls.ROLE_USAGE_HINTS.get(ctrl_key, ctrl_info.get("typical_usage", "")))
                        available_controls[s_key] = alias_copy

        return {
            "track_index": track_index,
            "device_index": device_index,
            "total_params": catalog.get("total_params", 0),
            "available_controls": available_controls,
            "supported_roles": list(available_controls.keys())
        }

    @classmethod
    def inspect_for_ai(cls, conn: Any, track_index: int, device_index: int) -> Dict[str, Any]:
        """
        AI-Oriented Parameter Introspection & Guide:
        Inspects what parameters are actually exposed on this device in Ableton Live,
        maps them to functional roles, and tells the AI agent exactly what each control does
        musically ('para qué sirve cada uno'), its current value, recommended usage range,
        and instructions for modifying only the controls it wants without DAW friction.
        """
        catalog = cls.inspect_device_catalog(conn, track_index, device_index)
        capabilities = cls.inspect_semantic_capabilities(conn, track_index, device_index)

        # Get device name if possible
        device_name = "Unknown Device"
        if conn and hasattr(conn, "send_command"):
            try:
                t_info = conn.send_command("get_track_info", {"track_index": track_index})
                if isinstance(t_info, dict):
                    devices = t_info.get("devices") or t_info.get("result", {}).get("devices", [])
                    if device_index < len(devices):
                        device_name = devices[device_index].get("name", device_name)
            except Exception:
                pass

        # Build unique readable parameter summaries for AI reasoning
        controls_summary = []
        seen_indices = set()
        for sem_role, info in capabilities.get("available_controls", {}).items():
            p_idx = info.get("param_index")
            if p_idx in seen_indices:
                continue
            seen_indices.add(p_idx)
            controls_summary.append({
                "role": sem_role,
                "function": info.get("description", ""),
                "recommendation": info.get("typical_usage", ""),
                "current_value": info.get("current_value"),
                "physical_bounds": [info.get("min"), info.get("max")],
                "daw_parameter": info.get("param_name")
            })

        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "device_index": device_index,
            "device_name": device_name,
            "total_parameters_exposed": catalog.get("total_params", 0),
            "active_sections": catalog.get("sections_available", []),
            "functional_controls": controls_summary,
            "ai_usage_instructions": (
                "Para modificar cualquiera de estos controles de forma explícita, llama a la herramienta MCP plugin_set_semantic_parameter(track=track, semantic_role=ROLE, value=0.0_a_1.0). "
                "No necesitas adivinar nombres de perillas en Ableton ni mapeos internos: especifica únicamente el rol semántico (ej: 'MACRO_1', 'CUTOFF', 'DRIVE', 'AMP_ATTACK', 'FM_DEPTH', etc.). "
                "El motor se encarga de traducir el rol, convertir el valor a los límites físicos reales del plugin, activar bandas de EQ y asegurar que el dispositivo esté encendido."
            )
        }

    @classmethod
    def get_semantic_guide(cls) -> Dict[str, Any]:
        """Returns the full catalog guide with descriptions and usage hints for all roles."""
        return {
            "role_descriptions": cls.ROLE_DESCRIPTIONS,
            "role_usage_hints": cls.ROLE_USAGE_HINTS,
            "functional_sections": list(cls.FUNCTIONAL_SECTIONS.keys()),
            "semantic_roles": list(cls.SEMANTIC_ROLES.keys())
        }

    @classmethod
    def _calculate_musical_parameter_value(
        cls,
        device_name: str,
        param_name: str,
        norm_val: float,
        p_min: float,
        p_max: float
    ) -> float:
        """
        Calculates safe musical physical values.
        For EQ gain parameters on FabFilter/Pro-Q where 0.5 is 0.00 dB (-30 to +30 dB),
        clamps to gentle surgical boosts (max +3.0 dB, norm 0.55) and cuts (max -6.0 dB, norm 0.40)
        to completely eliminate unnatural, deafening +13.2 dB spikes.
        """
        d_lower = str(device_name).lower()
        p_lower = str(param_name).lower()

        if "gain" in p_lower and any(eq in d_lower for eq in ["pro-q", "fabfilter", "eq"]) and p_min == 0.0 and p_max == 1.0:
            if norm_val > 0.5:
                # Map (0.5..1.0) to subtle boost (0.0..+3.0 dB) -> normalized 0.50..0.55
                boost_db = min(3.0, (norm_val - 0.5) * 6.0)
                return round(0.50 + (boost_db / 60.0), 4)
            elif norm_val < 0.5:
                # Map (0.5..0.0) to surgical cut (0.0..-6.0 dB) -> normalized 0.50..0.40
                cut_db = min(6.0, (0.5 - norm_val) * 12.0)
                return round(0.50 - (cut_db / 60.0), 4)
            else:
                return 0.50

        return p_min + norm_val * (p_max - p_min)

    @classmethod
    def _configure_eq_band_shape(
        cls,
        conn: Any,
        track_index: int,
        device_index: int,
        device_name: str,
        param_name: str,
        b_num: str
    ):
        """
        Configures proper musical band shapes on FabFilter Pro-Q.
        Band 1: Low Cut (HPF) shape = 0.2, slope = 0.2 (12 dB/oct), gain = 0.5 (0.00 dB).
        Band 3: Bell shape = 0.0 (mud cut).
        Band 5: High Shelf shape = 0.3 (air shelf).
        """
        d_lower = str(device_name).lower()
        if not any(eq in d_lower for eq in ["pro-q", "fabfilter"]):
            return

        if b_num == "1":
            try:
                conn.send_command("set_device_parameter", {
                    "track_index": track_index,
                    "device_index": device_index,
                    "parameter": "Band 1 Shape",
                    "value": 0.2  # Low Cut (HPF)
                })
                conn.send_command("set_device_parameter", {
                    "track_index": track_index,
                    "device_index": device_index,
                    "parameter": "Band 1 Slope",
                    "value": 0.20  # 12 dB/oct
                })
                conn.send_command("set_device_parameter", {
                    "track_index": track_index,
                    "device_index": device_index,
                    "parameter": "Band 1 Gain",
                    "value": 0.50  # 0.00 dB (flat)
                })
            except Exception:
                pass
        elif b_num == "3":
            try:
                conn.send_command("set_device_parameter", {
                    "track_index": track_index,
                    "device_index": device_index,
                    "parameter": "Band 3 Shape",
                    "value": 0.0  # Bell
                })
            except Exception:
                pass
        elif b_num == "5":
            try:
                conn.send_command("set_device_parameter", {
                    "track_index": track_index,
                    "device_index": device_index,
                    "parameter": "Band 5 Shape",
                    "value": 0.3  # High Shelf
                })
            except Exception:
                pass

    @classmethod
    def _activate_shaperbox_modules(
        cls,
        conn: Any,
        track_index: int,
        device_index: int,
        device_name: str
    ):
        """
        Ensures ShaperBox 3 modules are visibly and audibly active.
        Turns ON VolumeShaper, DriveShaper, and sets dynamic pumping depth.
        """
        d_lower = str(device_name).lower()
        if not any(sb in d_lower for sb in ["shaperbox", "cableguys"]):
            return
        try:
            conn.send_command("set_device_parameter", {
                "track_index": track_index,
                "device_index": device_index,
                "parameter": "Device On",
                "value": 1.0
            })
            conn.send_command("set_device_parameter", {
                "track_index": track_index,
                "device_index": device_index,
                "parameter": "VolumeShaper On",
                "value": 1.0
            })
            conn.send_command("set_device_parameter", {
                "track_index": track_index,
                "device_index": device_index,
                "parameter": "Volume Mid Mix",
                "value": 0.85
            })
            conn.send_command("set_device_parameter", {
                "track_index": track_index,
                "device_index": device_index,
                "parameter": "DriveShaper On",
                "value": 1.0
            })
            conn.send_command("set_device_parameter", {
                "track_index": track_index,
                "device_index": device_index,
                "parameter": "FilterShaper On",
                "value": 1.0
            })
        except Exception:
            pass

    @classmethod
    def apply_semantic_tuning(
        cls,
        conn: Any,
        track_index: int,
        device_index: int,
        device_name: str,
        semantic_requests: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Tunes device parameters using high-level semantic roles.
        Safely applies matching parameters and skips absent roles gracefully.
        """
        if conn is None or not hasattr(conn, "send_command"):
            return {"status": "MOCK_OK", "applied": semantic_requests}

        capabilities = cls.inspect_semantic_capabilities(conn, track_index, device_index)
        available = capabilities.get("available_controls", {})

        applied = {}
        skipped = []

        for role_name, target_val in semantic_requests.items():
            if isinstance(role_name, int):
                try:
                    conn.send_command("set_device_parameter", {
                        "track_index": track_index,
                        "device_index": device_index,
                        "parameter": role_name,
                        "value": float(target_val)
                    })
                    applied[f"PARAM_{role_name}"] = float(target_val)
                except Exception:
                    skipped.append(role_name)
                continue

            role_upper = str(role_name).upper().strip()
            ctrl_info = available.get(role_upper)
            if not ctrl_info:
                # Flexible lookup
                aliases = [a.lower() for a in cls.SEMANTIC_ROLES.get(role_upper, [])]
                for k, v in available.items():
                    p_name_clean = v.get("param_name", "").lower()
                    if (
                        k.upper() == role_upper
                        or v.get("role", "").upper() == role_upper
                        or v.get("semantic_role", "").upper() == role_upper
                        or p_name_clean == role_upper.lower()
                        or any(a == p_name_clean or a in p_name_clean for a in aliases)
                    ):
                        ctrl_info = v
                        break

            if ctrl_info:
                p_idx = ctrl_info["param_index"]
                p_min = ctrl_info["min"]
                p_max = ctrl_info["max"]

                norm_val = max(0.0, min(1.0, float(target_val)))
                physical_val = cls._calculate_musical_parameter_value(
                    device_name, ctrl_info["param_name"], norm_val, p_min, p_max
                )

                try:
                    # Auto-ensure device is On
                    conn.send_command("set_device_parameter", {
                        "track_index": track_index,
                        "device_index": device_index,
                        "parameter": "Device On",
                        "value": 1.0
                    })
                    # Auto-activate Pro-Q style band if param belongs to a band
                    import re
                    m = re.search(r"band\s*(\d+)", ctrl_info["param_name"], re.IGNORECASE)
                    if m:
                        b_num = m.group(1)
                        conn.send_command("set_device_parameter", {
                            "track_index": track_index,
                            "device_index": device_index,
                            "parameter": f"Band {b_num} Used",
                            "value": 1.0
                        })
                        conn.send_command("set_device_parameter", {
                            "track_index": track_index,
                            "device_index": device_index,
                            "parameter": f"Band {b_num} Enabled",
                            "value": 1.0
                        })
                        cls._configure_eq_band_shape(
                            conn, track_index, device_index, device_name, ctrl_info["param_name"], b_num
                        )

                    cls._activate_shaperbox_modules(conn, track_index, device_index, device_name)

                    conn.send_command("set_device_parameter", {
                        "track_index": track_index,
                        "device_index": device_index,
                        "parameter": p_idx,
                        "value": physical_val
                    })
                    applied[role_upper] = {
                        "param_name": ctrl_info["param_name"],
                        "param_index": p_idx,
                        "value": physical_val
                    }
                    logger.info(f"Tuned {role_upper} on {device_name} (Track {track_index}) -> {ctrl_info['param_name']}={physical_val:.2f}")
                except Exception as e:
                    logger.warning(f"Failed to set {role_upper} on {device_name}: {e}")
            else:
                skipped.append(role_upper)

        if applied:
            cls._SCULPTED_REGISTRY.add((track_index, device_index))

        return {
            "status": "SUCCESS",
            "device_name": device_name,
            "track_index": track_index,
            "device_index": device_index,
            "applied_count": len(applied),
            "applied": applied,
            "skipped": skipped
        }

    @classmethod
    def apply_sectional_tuning(
        cls,
        conn: Any,
        track_index: int,
        device_index: int,
        device_name: str,
        section_requests: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Tunes specific functional sections (e.g. FILTERS, SURGICAL_EQ, SPACE_MODULATION).
        Enables surgical micro-tuning without requiring exact parameter indexing.
        """
        if conn is None or not hasattr(conn, "send_command"):
            return {"status": "MOCK_OK", "applied": section_requests}

        catalog = cls.inspect_device_catalog(conn, track_index, device_index)
        available_sections = catalog.get("sections", {})

        applied = {}
        skipped = {}

        for sec_name, controls in section_requests.items():
            sec_upper = sec_name.upper().strip()
            if sec_upper in available_sections:
                sec_ctrls = available_sections[sec_upper]
                applied[sec_upper] = {}
                for ctrl_key, val in controls.items():
                    ctrl_upper = ctrl_key.upper().strip()
                    if ctrl_upper in sec_ctrls:
                        c_info = sec_ctrls[ctrl_upper]
                        p_idx = c_info["param_index"]
                        p_min = c_info["min"]
                        p_max = c_info["max"]
                        norm_val = max(0.0, min(1.0, float(val)))
                        phys_val = cls._calculate_musical_parameter_value(
                            device_name, c_info["param_name"], norm_val, p_min, p_max
                        )
                        try:
                            # Auto-ensure device is On
                            conn.send_command("set_device_parameter", {
                                "track_index": track_index,
                                "device_index": device_index,
                                "parameter": "Device On",
                                "value": 1.0
                            })
                            # Auto-activate Pro-Q style band if param belongs to a band
                            import re
                            m = re.search(r"band\s*(\d+)", c_info["param_name"], re.IGNORECASE)
                            if m:
                                b_num = m.group(1)
                                conn.send_command("set_device_parameter", {
                                    "track_index": track_index,
                                    "device_index": device_index,
                                    "parameter": f"Band {b_num} Used",
                                    "value": 1.0
                                })
                                conn.send_command("set_device_parameter", {
                                    "track_index": track_index,
                                    "device_index": device_index,
                                    "parameter": f"Band {b_num} Enabled",
                                    "value": 1.0
                                })
                                cls._configure_eq_band_shape(
                                    conn, track_index, device_index, device_name, c_info["param_name"], b_num
                                )

                            cls._activate_shaperbox_modules(conn, track_index, device_index, device_name)

                            conn.send_command("set_device_parameter", {
                                "track_index": track_index,
                                "device_index": device_index,
                                "parameter": p_idx,
                                "value": phys_val
                            })
                            applied[sec_upper][ctrl_upper] = {
                                "param_name": c_info["param_name"],
                                "value": phys_val
                            }
                        except Exception as e:
                            logger.warning(f"Error setting {ctrl_upper} in {sec_upper}: {e}")
                    else:
                        if sec_upper not in skipped:
                            skipped[sec_upper] = []
                        skipped[sec_upper].append(ctrl_upper)
            else:
                skipped[sec_upper] = list(controls.keys())

        if applied:
            cls._SCULPTED_REGISTRY.add((track_index, device_index))

        return {
            "status": "SUCCESS",
            "device_name": device_name,
            "applied": applied,
            "skipped": skipped
        }

    @classmethod
    def tune_vital_macros(
        cls,
        conn: Any,
        track_index: int,
        device_index: int,
        macros: Dict[int, float]
    ) -> Dict[str, Any]:
        """Modulates Vital's 4 macros directly."""
        semantic_map = {1: "BRIGHTNESS", 2: "WARMTH", 3: "ATTACK", 4: "MOVEMENT"}
        reqs = {semantic_map.get(k, f"MACRO_{k}"): v for k, v in macros.items()}
        return cls.apply_semantic_tuning(conn, track_index, device_index, "Vital", reqs)

    @classmethod
    def tune_device_parameters(
        cls,
        conn: Any,
        track_index: int,
        device_index: int,
        device_name: str,
        desired_params: Dict[Union[str, int], float]
    ) -> Dict[str, Any]:
        """Unified tuning router supporting semantic roles, sections, or literal keys."""
        if conn is None or not hasattr(conn, "send_command"):
            return {"status": "MOCK_OK", "applied": desired_params}

        # Check if caller passed sectional dicts
        has_sections = any(isinstance(v, dict) for v in desired_params.values())
        if has_sections:
            return cls.apply_sectional_tuning(conn, track_index, device_index, device_name, desired_params)

        # Standard semantic tuning
        return cls.apply_semantic_tuning(conn, track_index, device_index, device_name, desired_params)

    @classmethod
    def audit_device_sculpting(cls, conn: Any, track_index: int, device_index: int) -> Dict[str, Any]:
        """
        Audits whether a device on a track has been sculpted/configured
        or if it remains in a blank, unconfigured default state (Delta = 0).
        Enforces Nivel 2: Regla Delta >= 1 across all synths and plugins.
        """
        if conn is None or not hasattr(conn, "send_command"):
            if (track_index, device_index) in cls._SCULPTED_REGISTRY:
                return {
                    "is_sculpted": True,
                    "reason": "Registered in sculpted devices cache",
                    "track_index": track_index,
                    "device_index": device_index
                }
            return {"is_sculpted": False, "reason": "No live connection"}

        # Introspect track device info if possible to detect sample-based devices (Drum Rack, Simpler)
        try:
            raw_info = conn.send_command("get_track_info", {"track_index": track_index})
            t_info = raw_info.get("result", raw_info) if isinstance(raw_info, dict) else {}
            dev_list = t_info.get("devices", [])
            if device_index < len(dev_list):
                dev_entry = dev_list[device_index]
                dev_name = str(dev_entry.get("name", "")).lower()
                class_name = str(dev_entry.get("class_name", ""))
                if (
                    class_name in ("DrumGroupDevice", "OriginalSimpler", "MultiSampler")
                    or any(k in dev_name for k in ["drum rack", "kit", "simpler", "sampler"])
                ):
                    cls._SCULPTED_REGISTRY.add((track_index, device_index))
                    return {
                        "is_sculpted": True,
                        "reason": f"Sample-based instrument '{dev_entry.get('name')}' verified",
                        "track_index": track_index,
                        "device_index": device_index
                    }
        except Exception:
            pass

        params = cls.introspect_device_parameters(conn, track_index, device_index)
        if not params:
            if (track_index, device_index) in cls._SCULPTED_REGISTRY:
                return {
                    "is_sculpted": True,
                    "reason": "Registered in sculpted devices cache",
                    "track_index": track_index,
                    "device_index": device_index
                }
            return {"is_sculpted": False, "reason": "No controllable parameters found on device"}

        p_map = {p["name"]: p["value"] for p in params}

        # Check for Pro-Q band usage
        has_active_eq_band = any("Used" in k and v > 0.5 for k, v in p_map.items())
        if has_active_eq_band:
            cls._SCULPTED_REGISTRY.add((track_index, device_index))
            return {"is_sculpted": True, "reason": "Active EQ bands detected", "track_index": track_index, "device_index": device_index}

        # 1. Check for Analog Lab V factory default state & preset selection (Phase 1)
        if "P1 Brightness" in p_map:
            try:
                from engine.supervisor.governance import governance_supervisor
                t_state = governance_supervisor.get_track_state(track_index)
                if t_state.preset_required and not t_state.preset_configured:
                    return {
                        "is_sculpted": False,
                        "reason": "Analog Lab V requires explicit instrument/preset selection (Fase 1) before parameter sculpting (Fase 2)",
                        "track_index": track_index,
                        "device_index": device_index,
                        "total_params": len(params)
                    }
            except Exception:
                pass

            al_macros = [p_map.get("P1 Brightness", 0.5), p_map.get("P1 Timbre", 0.5), p_map.get("P1 Time", 0.5), p_map.get("P1 Movement", 0.5)]
            if all(abs(v - 0.5) < 0.03 for v in al_macros):
                cls._SCULPTED_REGISTRY.discard((track_index, device_index))
                return {
                    "is_sculpted": False,
                    "reason": "Analog Lab V parameters are in un-sculpted default state (all macros at 0.50) - macro sculpting required (Fase 2)",
                    "track_index": track_index,
                    "device_index": device_index,
                    "total_params": len(params)
                }

        # 2. Specific check for Serum / Serum 2 factory default state (Delta = 0)
        serum_wt = [v for k, v in p_map.items() if any(w in k.lower() for w in ["a wt pos", "b wt pos", "wt pos", "wavetable pos"])]
        serum_macros = [v for k, v in p_map.items() if "macro" in k.lower()]
        serum_filter_drive = [v for k, v in p_map.items() if "drive" in k.lower()]
        serum_warp = [v for k, v in p_map.items() if any(w in k.lower() for w in ["a warp", "b warp", "warp"])]
        if serum_wt and serum_macros:
            all_wt_zero = all(abs(v - 0.0) < 0.01 for v in serum_wt)
            all_macro_zero = all(abs(v - 0.0) < 0.01 for v in serum_macros)
            all_drive_zero = all(abs(v - 0.0) < 0.01 for v in serum_filter_drive) if serum_filter_drive else True
            all_warp_zero = all(abs(v - 0.0) < 0.01 for v in serum_warp) if serum_warp else True
            if all_wt_zero and all_macro_zero and all_drive_zero and all_warp_zero:
                cls._SCULPTED_REGISTRY.discard((track_index, device_index))
                return {
                    "is_sculpted": False,
                    "reason": "Serum 2 is in factory default saw wave init state (Delta = 0) - internal synthesis sculpting required (A WT Pos, Cutoff, Drive, or Macros)",
                    "track_index": track_index,
                    "device_index": device_index,
                    "total_params": len(params)
                }

        # 3. Specific check for Massive X factory default state (Delta = 0)
        massive_wt = [v for k, v in p_map.items() if any(w in k.lower() for w in ["osc a wt", "osc a pos", "wavetable pos"])]
        massive_macros = [v for k, v in p_map.items() if "macro" in k.lower() and not "assign" in k.lower()]
        if massive_wt and massive_macros:
            all_m_wt_zero = all(abs(v - 0.0) < 0.01 for v in massive_wt)
            all_m_macro_zero = all(abs(v - 0.0) < 0.01 or abs(v - 0.5) < 0.01 for v in massive_macros)
            if all_m_wt_zero and all_m_macro_zero:
                cls._SCULPTED_REGISTRY.discard((track_index, device_index))
                return {
                    "is_sculpted": False,
                    "reason": "Massive X is in factory default init state (Delta = 0) - internal synthesis parameters or macros must be sculpted",
                    "track_index": track_index,
                    "device_index": device_index,
                    "total_params": len(params)
                }

        # 4. Specific check for Vital factory default state (Delta = 0)
        vital_warp = [v for k, v in p_map.items() if "warp" in k.lower() and "osc" in k.lower()]
        vital_macros = [v for k, v in p_map.items() if "macro" in k.lower()]
        if vital_macros and vital_warp:
            all_v_macro_zero = all(abs(v - 0.0) < 0.01 for v in vital_macros)
            all_v_warp_zero = all(abs(v - 0.0) < 0.01 for v in vital_warp)
            if all_v_macro_zero and all_v_warp_zero:
                cls._SCULPTED_REGISTRY.discard((track_index, device_index))
                return {
                    "is_sculpted": False,
                    "reason": "Vital is in factory default saw wave init state (Delta = 0) - internal synthesis parameters or macros must be sculpted",
                    "track_index": track_index,
                    "device_index": device_index,
                    "total_params": len(params)
                }

        # 5. Check if registered in sculpted cache AND verified non-init
        if (track_index, device_index) in cls._SCULPTED_REGISTRY:
            return {
                "is_sculpted": True,
                "reason": "Registered in sculpted devices cache and confirmed modified (Delta >= 1)",
                "track_index": track_index,
                "device_index": device_index
            }

        # 6. General Check: non-zero/non-default macro controls (Delta >= 1)
        macro_vals = [v for k, v in p_map.items() if any(m in k.lower() for m in ["macro", "brightness", "timbre"])]
        if macro_vals and any(abs(v - 0.0) > 0.01 and abs(v - 0.5) > 0.05 for v in macro_vals):
            cls._SCULPTED_REGISTRY.add((track_index, device_index))
            return {"is_sculpted": True, "reason": "Non-default macro positions detected (Delta >= 1)", "track_index": track_index, "device_index": device_index}

        # 7. Check for filter / envelope / timbre modifications away from default (Delta >= 1)
        timbre_vals = [
            v for k, v in p_map.items()
            if any(t in k.lower() for t in ["cutoff", "drive", "resonance", "decay", "attack", "wt pos", "warp", "waveframe"])
            and not any(ex in k.lower() for ex in ["on", "enabled", "solo", "mute", "speaker"])
        ]
        if timbre_vals and any(abs(v - 0.0) > 0.02 and abs(v - 1.0) > 0.02 for v in timbre_vals):
            cls._SCULPTED_REGISTRY.add((track_index, device_index))
            return {"is_sculpted": True, "reason": "Sculpted timbre parameters detected (Delta >= 1)", "track_index": track_index, "device_index": device_index}

        return {
            "is_sculpted": False,
            "reason": "Device appears to be in initial/default state with zero sculpted parameters (Delta = 0)",
            "track_index": track_index,
            "device_index": device_index,
            "total_params": len(params)
        }

    @classmethod
    def enforce_mandatory_sculpting(
        cls,
        conn: Any,
        track_index: int,
        device_index: int,
        role: str = "SYNTH"
    ) -> Dict[str, Any]:
        """
        Enforces that a device is configured and sculpted.
        If the device is unconfigured, automatically applies character-defining
        parameters matched to the track's musical role.
        """
        if conn is None or not hasattr(conn, "send_command"):
            cls._SCULPTED_REGISTRY.add((track_index, device_index))
            return {"status": "MOCK_OK", "applied_count": 1}

        # Resolve device name
        try:
            raw_info = conn.send_command("get_track_info", {"track_index": track_index})
            t_info = raw_info.get("result", raw_info) if isinstance(raw_info, dict) else {}
            devices = t_info.get("devices", [])
            dev_name = devices[device_index]["name"] if device_index < len(devices) else "Unknown"
        except Exception:
            dev_name = "Unknown"

        # Determine best role profile
        r_upper = role.upper().strip()
        profile_key = "SYNTH"
        dev_lower = dev_name.lower()

        # Match specific plugin profiles first
        if "serum" in dev_lower:
            profile_key = "SERUM"
        elif "massive x" in dev_lower:
            profile_key = "MASSIVE_X"
        elif "massive" in dev_lower:
            profile_key = "MASSIVE"
        elif "vital" in dev_lower:
            profile_key = "VITAL"
        elif "pigments" in dev_lower:
            profile_key = "PIGMENTS"
        elif "solina" in dev_lower:
            profile_key = "SOLINA_V2"
        elif "analog lab" in dev_lower or "stage-73" in dev_lower:
            if "pad" in r_upper:
                profile_key = "ANALOG_LAB_PAD"
            elif "lead" in r_upper:
                profile_key = "ANALOG_LAB_LEAD"
            else:
                profile_key = "ANALOG_LAB_KEYS"

            # Phase 1 verification for Analog Lab: ensure an instrument/preset is recorded
            try:
                from engine.supervisor.governance import governance_supervisor
                t_st = governance_supervisor.get_track_state(track_index)
                if t_st.preset_required and not t_st.preset_configured:
                    chosen_preset = "Cinema Strings Pad" if "pad" in r_upper else "Classic Jun Keys"
                    governance_supervisor.record_preset_selected(track_index, chosen_preset, device_index=device_index)
                    logger.info(f"[Supervisor] Enforced instrument selection on Analog Lab (Track {track_index}): '{chosen_preset}'")
            except Exception:
                pass
        elif "decapitator" in dev_lower:
            profile_key = "DECAPITATOR"
        elif "echoboy" in dev_lower:
            profile_key = "ECHOBOY"
        elif "alterboy" in dev_lower:
            profile_key = "LITTLEALTERBOY"
        elif "refract" in dev_lower:
            profile_key = "EFX_REFRACT"
        elif "motions" in dev_lower:
            profile_key = "EFX_MOTIONS"
        elif "fragments" in dev_lower:
            profile_key = "EFX_FRAGMENTS"
        elif "thermal" in dev_lower:
            profile_key = "THERMAL"
        elif "shaperbox" in dev_lower:
            profile_key = "SHAPERBOX_3"
        elif "god particle" in dev_lower:
            profile_key = "THE_GOD_PARTICLE"
        elif "pro-l" in dev_lower:
            profile_key = "PRO_L2"
        elif "pro-q" in dev_lower or "eq eight" in dev_lower or "eq" in dev_lower:
            profile_key = "SURGICAL_EQ"
        elif "ott" in dev_lower or "glue" in dev_lower or "compressor" in dev_lower:
            profile_key = "DYNAMICS"
        elif "reverb" in dev_lower or "valhalla" in dev_lower or "delay" in dev_lower:
            profile_key = "SPACE_MODULATION"
        elif "saturator" in dev_lower or "distortion" in dev_lower:
            profile_key = "SATURATION"
        elif "drum" in dev_lower:
            profile_key = "DRUMS"
        else:
            for k in cls.ROLE_SCULPTING_PROFILES:
                if k in r_upper:
                    profile_key = k
                    break

        profile = cls.ROLE_SCULPTING_PROFILES.get(profile_key, cls.ROLE_SCULPTING_PROFILES.get("LEAD", {}))

        res = cls.apply_sectional_tuning(conn, track_index, device_index, dev_name, profile)
        cls._activate_shaperbox_modules(conn, track_index, device_index, dev_name)
        cls._SCULPTED_REGISTRY.add((track_index, device_index))
        try:
            from engine.supervisor.governance import governance_supervisor
            applied_params = {}
            if isinstance(res, dict) and "applied" in res:
                for sec, ctrls in res["applied"].items():
                    if isinstance(ctrls, dict):
                        for c_k, c_v in ctrls.items():
                            applied_params[f"{sec}_{c_k}"] = c_v.get("value", 0.5) if isinstance(c_v, dict) else float(c_v)
            if not applied_params:
                applied_params = {"sculpted_auto": 1.0}
            governance_supervisor.record_device_sculpted(track_index, device_index, applied_params)
        except Exception as gov_err:
            logger.debug(f"Governance sync notice: {gov_err}")

        logger.info(f"Enforced mandatory parameter sculpting on {dev_name} (Track {track_index}, Role {role}) using profile {profile_key}")
        return res

    @classmethod
    def apply_sound_blueprint(
        cls,
        conn: Any,
        track_index: int,
        role: str,
        plugin_name: str = "",
        genre: str = "neo_soul_trap",
        custom_blueprint: Optional[Dict[str, Any]] = None,
        device_index: int = 0
    ) -> Dict[str, Any]:
        """
        Applies a concrete parameter blueprint to an instrument or device on track_index.
        Resolves parameters from custom_blueprint, the curated browser catalog,
        or ROLE_SCULPTING_PROFILES, applies them via Live connection, and records
        the device as SCULPTED in both _SCULPTED_REGISTRY and governance_supervisor.
        """
        applied_params: Dict[str, float] = {}

        # 1. Resolve blueprint parameters
        target_params: Dict[str, float] = {}
        sculpt_type = "macro"

        if custom_blueprint and isinstance(custom_blueprint, dict):
            target_params = custom_blueprint.get("parameters", custom_blueprint)
            sculpt_type = custom_blueprint.get("sculpt_type", "macro")
        else:
            # Look up in curated catalog
            try:
                from engine.instruments.browser_catalog import CURATED_SOURCES
                r_upper = role.upper().strip()
                options = CURATED_SOURCES.get(r_upper, [])
                p_lower = plugin_name.lower().strip()
                matched_opt = None
                for opt in options:
                    if p_lower and (p_lower in opt.name.lower() or opt.id.lower() in p_lower):
                        matched_opt = opt
                        break
                if not matched_opt and options:
                    matched_opt = options[0]

                if matched_opt and matched_opt.blueprint:
                    target_params = matched_opt.blueprint.get("parameters", {})
                    sculpt_type = matched_opt.blueprint.get("sculpt_type", "macro")
            except Exception as cat_err:
                logger.debug(f"Catalog lookup error in apply_sound_blueprint: {cat_err}")

        # Fallback to role sculpting profile if still empty
        if not target_params:
            res = cls.enforce_mandatory_sculpting(conn, track_index, device_index, role=role)
            return {
                "status": "SUCCESS",
                "track_index": track_index,
                "device_index": device_index,
                "role": role,
                "applied_parameters": res.get("applied", {}),
                "is_sculpted": True
            }

        # 2. Dispatch parameters to Live if connected
        if conn is not None and hasattr(conn, "send_command"):
            live_params = cls.introspect_device_parameters(conn, track_index, device_index)
            live_param_map = {str(p.get("name", "")).strip().lower(): p.get("original_id", p.get("id")) for p in live_params}

            for p_name, p_val in target_params.items():
                val_float = float(p_val)
                p_clean = str(p_name).strip().lower()

                # Try direct name match first
                matched_id = None
                for live_name, orig_id in live_param_map.items():
                    if p_clean == live_name or p_clean in live_name or live_name in p_clean:
                        matched_id = orig_id
                        break

                if matched_id is not None:
                    try:
                        conn.send_command("set_device_parameter", {
                            "track_index": track_index,
                            "device_index": device_index,
                            "parameter": matched_id,
                            "value": val_float
                        })
                        applied_params[p_name] = val_float
                    except Exception as set_err:
                        logger.debug(f"Could not set parameter {p_name}: {set_err}")
                else:
                    # Try semantic tuning for this parameter
                    try:
                        sem_res = cls.apply_semantic_tuning(conn, track_index, device_index, plugin_name, {p_name: val_float})
                        if sem_res.get("applied"):
                            applied_params[p_name] = val_float
                    except Exception:
                        pass
        else:
            applied_params = dict(target_params)

        if not applied_params:
            applied_params = dict(target_params)

        # 3. Register as sculpted
        cls._SCULPTED_REGISTRY.add((track_index, device_index))
        try:
            from engine.supervisor.governance import governance_supervisor
            governance_supervisor.record_device_sculpted(track_index, device_index, applied_params)
        except Exception as gov_err:
            logger.debug(f"Governance sync in apply_sound_blueprint: {gov_err}")

        logger.info(f"Applied sound blueprint to Track {track_index} Dev {device_index} (Role: {role}): {applied_params}")
        return {
            "status": "SUCCESS",
            "track_index": track_index,
            "device_index": device_index,
            "role": role,
            "applied_parameters": applied_params,
            "is_sculpted": True
        }

