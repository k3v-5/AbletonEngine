# engine/fx/role_fx_catalog.py
"""
Role-based insert effects catalog and psychoacoustic spectral guide.
"""
from typing import Dict, List, Any

ROLE_INSERT_EFFECTS: Dict[str, List[Dict[str, Any]]] = {
    "KICK": [
        {
            "name": "EQ Eight",
            "uri": "query:AudioFx#EQ%20Eight",
            "params": [
                {"id": "Band 1 On", "name": "Banda 1 High-Pass", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Filtro pasa-altos subsónico (30 Hz) para limpiar rumble inaudible.", "default": 1.0},
                {"id": "1 Frequency A", "name": "Frecuencia de Corte Subsónico", "range": "0.0 a 1.0 (20 Hz a 50 Hz)", "behavior": "Protege el cuerpo del bombo y limpia el rango subgrave inaudible.", "default": 0.14},
                {"id": "Band 2 On", "name": "Banda 2 Bell (Punch)", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Realce paramétrico en el punto de impacto fundamental del bombo.", "default": 1.0},
                {"id": "2 Frequency A", "name": "Frecuencia de Punch", "range": "0.0 a 1.0 (50 Hz a 75 Hz)", "behavior": "Enfatiza la pegada y transiente del bombo.", "default": 0.25}
            ]
        },
        {
            "name": "Glue Compressor",
            "uri": "query:AudioFx#Glue%20Compressor",
            "params": [
                {"id": "Threshold", "name": "Threshold (Umbral)", "range": "-40.0 dB a 0.0 dB", "behavior": "Nivel de control dinámico del transiente del bombo.", "default": -14.0},
                {"id": "Ratio", "name": "Ratio", "range": "1.0 (2:1) o 2.0 (4:1)", "behavior": "Relación de compresión para asentar el golpe.", "default": 1.0},
                {"id": "Attack", "name": "Attack (Tiempo de ataque)", "range": "0.0 a 1.0 (0.1 ms a 30 ms)", "behavior": "Ataque lento (>0.6) para dejar pasar el transitorio inicial intacto.", "default": 0.70},
                {"id": "Release", "name": "Release (Relajación)", "range": "0.0 a 1.0", "behavior": "Relajación rápida para no comerse el decaimiento.", "default": 0.0},
                {"id": "Makeup", "name": "Makeup Gain", "range": "0.0 a 1.0", "behavior": "Compensación de salida.", "default": 0.10}
            ]
        }
    ],
    "DRUMS": [
        {
            "name": "EQ Eight",
            "uri": "query:AudioFx#EQ%20Eight",
            "params": [
                {"id": "Band 1 On", "name": "Banda 1 High-Pass", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Filtro pasa-altos en 30-40 Hz para eliminar subgraves inaudibles y proteger el limitador.", "default": 1.0},
                {"id": "1 Frequency A", "name": "Frecuencia de Corte Subsónico", "range": "0.0 a 1.0 (20 Hz a 60 Hz)", "behavior": "Corte de sub-graves sucios para dejar espacio cristalino al sub del 808.", "default": 0.18},
                {"id": "Band 2 On", "name": "Banda 2 Bell (Caja/Snare Mud)", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Control de resonancias y barro en 300-450 Hz.", "default": 1.0},
                {"id": "2 Frequency A", "name": "Frecuencia de Resonancia Caja", "range": "0.0 a 1.0 (250 Hz a 500 Hz)", "behavior": "Limpieza de resonancia acartonada en la caja.", "default": 0.45},
                {"id": "Band 4 On", "name": "Banda 4 High-Shelf (Brillo Platillos)", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Apertura en 9-12 kHz para brillo y aire en hi-hats y platillos.", "default": 1.0},
                {"id": "4 Frequency A", "name": "Frecuencia de Brillo Platillos", "range": "0.0 a 1.0", "behavior": "Definición y presencia de percusión superior.", "default": 0.82}
            ]
        },
        {
            "name": "Drum Buss",
            "uri": "query:AudioFx#Drum%20Buss",
            "params": [
                {"id": "Drive", "name": "Drive", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Saturación analógica y distorsión armónica no lineal; aporta presencia y grosor en el bus de batería.", "default": 0.28},
                {"id": "Crunch", "name": "Crunch", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Saturación en frecuencias medias-altas; incrementa la mordida en caja, platos y percusión.", "default": 0.35},
                {"id": "Transients", "name": "Transients", "range": "0.0 a 1.0 (-inf a +inf dB)", "behavior": "Modificación de transientes; valores < 0.5 amortiguan el ataque, valores > 0.5 aumentan el snap inicial de tambores.", "default": 0.65},
                {"id": "Boom", "name": "Boom", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Resonancia sintonizada en subgraves; enfatiza la pegada y peso del bombo.", "default": 0.20},
                {"id": "Output", "name": "Output Gain", "range": "0.0 a 1.0 (-inf a +6 dB)", "behavior": "Ajuste de ganancia de salida para compensar el incremento de volumen del procesamiento.", "default": 0.70}
            ]
        },
        {
            "name": "Glue Compressor",
            "uri": "query:AudioFx#Glue%20Compressor",
            "params": [
                {"id": "Threshold", "name": "Threshold (Umbral)", "range": "-40.0 dB a 0.0 dB", "behavior": "Nivel de señal a partir del cual comienza la compresión dinámica.", "default": -12.0},
                {"id": "Ratio", "name": "Ratio (Relación)", "range": "1.0 (2:1), 2.0 (4:1), 3.0 (10:1)", "behavior": "Proporción de atenuación aplicada a la señal que supera el umbral.", "default": 1.0},
                {"id": "Attack", "name": "Attack (Tiempo de ataque)", "range": "0.0 a 1.0 (0.1 ms a 30 ms)", "behavior": "Velocidad de respuesta; ataques lentos (>0.4) dejan pasar la pegada inicial del bombo y caja.", "default": 0.50},
                {"id": "Release", "name": "Release (Relajación)", "range": "0.0 a 1.0 (Auto / 0.1s a 1.2s)", "behavior": "Tiempo de recuperación dinámica; Auto adapta la respuesta al ritmo del material.", "default": 0.0},
                {"id": "Dry/Wet", "name": "Dry/Wet (Mezcla)", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Balance de procesamiento paralelo; permite compresión estilo New York sin perder transientes.", "default": 0.85},
                {"id": "Makeup", "name": "Makeup Gain", "range": "0.0 a 1.0 (0 dB a +40 dB)", "behavior": "Compensación de nivel post-compresión para igualar la ganancia percibida.", "default": 0.15}
            ]
        }
    ],
    "BASS": [
        {
            "name": "EQ Eight",
            "uri": "query:AudioFx#EQ%20Eight",
            "params": [
                {"id": "Band 1 On", "name": "Banda 1 High-Pass", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Filtro pasa-altos subsónico.", "default": 1.0},
                {"id": "1 Frequency A", "name": "Frecuencia de Corte Subsónico", "range": "0.0 a 1.0 (10 Hz a 200 Hz)", "behavior": "Elimina energía inaudible subsónica (< 25-30 Hz) que resta potencia al limitador.", "default": 0.20}
            ]
        },
        {
            "name": "Saturator",
            "uri": "query:AudioFx#Saturator",
            "params": [
                {"id": "Drive", "name": "Drive (Distorsión armónica)", "range": "0.0 a 1.0 (0 dB a +36 dB)", "behavior": "Generación de armónicos superiores para que el bajo sea audible en altavoces pequeños.", "default": 0.22},
                {"id": "Base", "name": "Base (Graves limpios)", "range": "0.0 a 1.0 (-inf a 0 dB)", "behavior": "Aislamiento del subgrave fundamental para evitar distorsión indeseada en < 80 Hz.", "default": 0.0},
                {"id": "Output", "name": "Output Trim", "range": "0.0 a 1.0 (-inf a 0 dB)", "behavior": "Atenuación de salida para conservar el headroom de mezcla.", "default": 0.70}
            ]
        }
    ],
    "KEYS": [
        {
            "name": "EQ Eight",
            "uri": "query:AudioFx#EQ%20Eight",
            "params": [
                {"id": "Band 1 On", "name": "Banda 1 High-Pass", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Filtro pasa-altos en 110-130 Hz para liberar el espacio del 808 y Kick.", "default": 1.0},
                {"id": "1 Frequency A", "name": "Frecuencia de Corte Graves", "range": "0.0 a 1.0 (50 Hz a 250 Hz)", "behavior": "Elimina retumbes graves de teclado para no enturbiar el bajo.", "default": 0.30},
                {"id": "Band 2 On", "name": "Banda 2 Bell (Limpieza de Barro)", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Muesca de atenuación en 300-400 Hz para evitar congestión en medios-bajos.", "default": 1.0},
                {"id": "2 Frequency A", "name": "Frecuencia de Limpieza Barro", "range": "0.0 a 1.0", "behavior": "Despeja el rango medio donde conviven guitarras y voces.", "default": 0.42},
                {"id": "Band 3 On", "name": "Banda 3 Bell (Presencia)", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Realce sutil en 2.5-3.5 kHz para articulación de acordes.", "default": 1.0},
                {"id": "3 Frequency A", "name": "Frecuencia de Presencia", "range": "0.0 a 1.0", "behavior": "Definición armónica en la mezcla.", "default": 0.65}
            ]
        },
        {
            "name": "Chorus-Ensemble",
            "uri": "query:AudioFx#Chorus-Ensemble",
            "params": [
                {"id": "Amount", "name": "Amount (Profundidad)", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Profundidad de modulación de tono; ensancha la imagen estéreo de los acordes.", "default": 0.40},
                {"id": "Rate", "name": "Rate (Velocidad)", "range": "0.0 a 1.0 (0.01 Hz a 10 Hz)", "behavior": "Velocidad del LFO; tasas bajas generan movimiento orgánico lento.", "default": 0.25}
            ]
        },
        {
            "name": "ValhallaVintageVerb",
            "uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb",
            "params": [
                {"id": "Mix", "name": "Mix (Mezcla de Reverb)", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Proporción de señal procesada; valores moderados (15-25%) evitan enturbiar el plano armónico.", "default": 0.18},
                {"id": "Decay", "name": "Decay (Tiempo de reverberación)", "range": "0.0 a 1.0 (0.2 s a 70 s)", "behavior": "Longitud de la cola de reverberación y tamaño del espacio acústico.", "default": 0.25}
            ]
        }
    ],
    "LEAD": [
        {
            "name": "EQ Eight",
            "uri": "query:AudioFx#EQ%20Eight",
            "params": [
                {"id": "Band 1 On", "name": "Banda 1 High-Pass", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Filtro pasa-altos en 140-160 Hz para limpiar peso innecesario.", "default": 1.0},
                {"id": "1 Frequency A", "name": "Frecuencia de Corte Lead", "range": "0.0 a 1.0 (80 Hz a 300 Hz)", "behavior": "Corte de graves para dejar libre el espacio de acordes y bajo.", "default": 0.34},
                {"id": "Band 2 On", "name": "Banda 2 Notch (Anti-Dureza Digital)", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Atenuación quirúrgica en 3.2-4.2 kHz para suprimir asperezas digitales de sintetizador.", "default": 1.0},
                {"id": "2 Frequency A", "name": "Frecuencia Anti-Dureza", "range": "0.0 a 1.0", "behavior": "Suaviza el timbre melódico sin perder protagonismo.", "default": 0.68},
                {"id": "Band 4 On", "name": "Banda 4 High-Shelf (Aire)", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Apertura por encima de 10 kHz para presencia etérea moderna.", "default": 1.0},
                {"id": "4 Frequency A", "name": "Frecuencia de Aire Lead", "range": "0.0 a 1.0", "behavior": "Brillo de alta gama.", "default": 0.85}
            ]
        },
        {
            "name": "Delay",
            "uri": "query:AudioFx#Delay",
            "params": [
                {"id": "Dry/Wet", "name": "Dry/Wet (Mezcla de Delay)", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Balance de eco rítmico frente a la señal directa.", "default": 0.25},
                {"id": "Feedback", "name": "Feedback (Repeticiones)", "range": "0.0 a 1.0 (0% a 95%)", "behavior": "Cantidad de repeticiones en el tiempo; valores altos extienden la cola melódica.", "default": 0.30},
                {"id": "Sync", "name": "Sincronización Rítmica", "range": "0.0 (Tiempo ms) o 1.0 (Sincronizado a compás)", "behavior": "Sincroniza las repeticiones a subdivisiones métricas del tempo.", "default": 1.0}
            ]
        },
        {
            "name": "OTT",
            "uri": "query:Plugins#VST3:Xfer%20Records:OTT",
            "params": [
                {"id": "Depth", "name": "Depth (Profundidad Multibanda)", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Cantidad de compresión ascendente/descendente sobre las tres bandas espectrales.", "default": 0.25},
                {"id": "Time", "name": "Time (Velocidad dinámica)", "range": "0.0 a 1.0 (10% a 1000%)", "behavior": "Escala de constantes de tiempo de ataque y relajación de la compresión.", "default": 0.50}
            ]
        }
    ],
    "STRINGS": [
        {
            "name": "EQ Eight",
            "uri": "query:AudioFx#EQ%20Eight",
            "params": [
                {"id": "Band 1 On", "name": "Banda 1 High-Pass", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Filtro pasa-altos para limpiar graves.", "default": 1.0},
                {"id": "1 Frequency A", "name": "Frecuencia de Corte", "range": "0.0 a 1.0 (20 Hz a 500 Hz)", "behavior": "Despeja el espectro inferior (80-150 Hz) para que el bombo y bajo mantengan claridad.", "default": 0.35}
            ]
        },
        {
            "name": "ValhallaVintageVerb",
            "uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb",
            "params": [
                {"id": "Mix", "name": "Mix (Espacio ambiental)", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Profundidad ambiental para empujar las cuerdas al fondo del plano auditivo.", "default": 0.28},
                {"id": "Decay", "name": "Decay (Cola larga)", "range": "0.0 a 1.0 (0.2 s a 70 s)", "behavior": "Sustain sedoso que une las transiciones de notas.", "default": 0.32}
            ]
        }
    ],
    "VOCALS": [
        {
            "name": "Auto-Tune Artist",
            "uri": "query:Plugins#VST3:Antares:Auto-Tune%20Artist",
            "params": [
                {"id": "Retune Speed", "name": "Retune Speed (Velocidad de Afinación)", "range": "0 ms (Snap Tyler/Travis) a 100 ms (Natural)", "behavior": "Velocidad de corrección tonal hacia la nota objetivo. 0 ms produce el efecto característico in-your-face.", "default": 0.0},
                {"id": "Flex-Tune", "name": "Flex-Tune (Tolerancia Expresiva)", "range": "0.0 (Estricto) a 1.0 (Relajado)", "behavior": "Permite libertad expresiva cuando el vocalista se acerca a la nota.", "default": 0.0},
                {"id": "Humanize", "name": "Humanize (Notas Sostenidas)", "range": "0.0 a 1.0", "behavior": "Aplica una corrección más suave y natural a notas largas.", "default": 0.0},
                {"id": "Key", "name": "Key (Tono Fundamental)", "range": "C, C#, D, D#, E, F, F#, G, G#, A, A#, B", "behavior": "Tonalidad base del tema musical.", "default": "F"},
                {"id": "Scale", "name": "Scale (Escala Musical)", "range": "Major, Minor, Chromatic", "behavior": "Modo de escala armónica de afinación.", "default": "Minor"}
            ]
        },
        {
            "name": "Pro-Q 4",
            "uri": "query:Plugins#VST3:FabFilter:Pro-Q%204",
            "params": [
                {"id": "Band 1 Frequency", "name": "Band 1 HPF (Corte de Graves)", "range": "20 Hz a 200 Hz", "behavior": "Filtro pasa-altos quirúrgico en 110 Hz para eliminar ruidos sub y resonancias.", "default": 0.25},
                {"id": "Band 2 Gain", "name": "Band 2 Notch (Corte de Resonancia)", "range": "-12 dB a 0 dB", "behavior": "Atenuación quirúrgica en ~380-450 Hz para limpiar resonancia de cuarto.", "default": 0.40},
                {"id": "Band 4 Gain", "name": "Band 4 High Shelf (Brillo y Aire)", "range": "0 dB a +6 dB", "behavior": "Realce suave por encima de 10-12 kHz para presencia moderna in-your-face.", "default": 0.55}
            ]
        },
        {
            "name": "Compressor",
            "uri": "query:AudioFx#Compressor",
            "params": [
                {"id": "Threshold", "name": "Threshold (Umbral de Compresión)", "range": "-40.0 dB a 0.0 dB", "behavior": "Nivel de activación donde comienza el control dinámico vocal.", "default": -18.0},
                {"id": "Ratio", "name": "Ratio (Relación de Compresión)", "range": "2:1 a 8:1", "behavior": "Control estricto de picos para mantener la voz al frente de la mezcla.", "default": 4.0},
                {"id": "Attack", "name": "Attack (Tiempo de Ataque)", "range": "1 ms a 50 ms", "behavior": "Tiempo de respuesta; 15 ms preserva las consonantes inteligibles.", "default": 0.35},
                {"id": "Release", "name": "Release (Tiempo de Relajación)", "range": "20 ms a 300 ms", "behavior": "Recuperación dinámica; 80 ms mantiene la respiración musical.", "default": 0.45}
            ]
        },
        {
            "name": "Saturn 2",
            "uri": "query:Plugins#VST3:FabFilter:Saturn%202",
            "params": [
                {"id": "Drive", "name": "Drive (Saturación y Color Armónico)", "range": "0.0 a 1.0 (0 dB a +36 dB)", "behavior": "Genera armónicos de válvulas/cinta cálida para engrosar el cuerpo vocal.", "default": 0.20},
                {"id": "Tone", "name": "Tone (Color Tímbrico)", "range": "0.0 (Cálido) a 1.0 (Brillante)", "behavior": "Ajuste de balance frecuencial de la saturación.", "default": 0.55},
                {"id": "Mix", "name": "Mix (Dry/Wet)", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Balance de saturación paralela para mantener la pureza de la señal.", "default": 0.75}
            ]
        },
        {
            "name": "ValhallaVintageVerb",
            "uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb",
            "params": [
                {"id": "Mix", "name": "Mix (Mezcla de Reverberación)", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Espacio acústico; 15-20% añade profundidad tridimensional sin alejar la voz.", "default": 0.18},
                {"id": "Decay", "name": "Decay (Tiempo de Reverberación)", "range": "0.2 s a 70 s", "behavior": "Longitud de la cola ambiental (1.8s a 2.5s ideal para trap/pop).", "default": 0.25},
                {"id": "PreDelay", "name": "Pre-Delay (Retardo Inicial)", "range": "0 ms a 200 ms", "behavior": "Separa la voz seca del inicio de la reverberación para máxima inteligibilidad.", "default": 0.15}
            ]
        }
    ],
    "PAD": [
        {
            "name": "EQ Eight",
            "uri": "query:AudioFx#EQ%20Eight",
            "params": [
                {"id": "Band 1 On", "name": "Banda 1 High-Pass", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Filtro pasa-altos para evitar colisión con subgraves.", "default": 1.0},
                {"id": "1 Frequency A", "name": "Frecuencia de Corte", "range": "0.0 a 1.0 (20 Hz a 500 Hz)", "behavior": "Corte por encima de 120 Hz.", "default": 0.30}
            ]
        },
        {
            "name": "ValhallaVintageVerb",
            "uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb",
            "params": [
                {"id": "Mix", "name": "Mix (Ambiente estéreo)", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Profundidad ambiental para texturas de fondo.", "default": 0.30},
                {"id": "Decay", "name": "Decay (Sostenimiento largo)", "range": "0.0 a 1.0 (0.2 s a 70 s)", "behavior": "Cola extendida para colchón armónico.", "default": 0.35}
            ]
        }
    ],
    "GUITAR": [
        {
            "name": "EQ Eight",
            "uri": "query:AudioFx#EQ%20Eight",
            "params": [
                {"id": "Band 1 On", "name": "Banda 1 High-Pass", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Filtro pasa-altos en 120 Hz para eliminar retumbes de cuerpo de guitarra.", "default": 1.0},
                {"id": "1 Frequency A", "name": "Frecuencia de Corte", "range": "0.0 a 1.0", "behavior": "Protege el rango del bajo y bombo.", "default": 0.30},
                {"id": "Band 2 On", "name": "Banda 2 Bell (Mud Cut)", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Atenuación en 350-450 Hz para eliminar tono hueco o acartonado.", "default": 1.0},
                {"id": "2 Frequency A", "name": "Frecuencia de Muesca Barro", "range": "0.0 a 1.0", "behavior": "Limpieza de medios acústicos/eléctricos.", "default": 0.44}
            ]
        },
        {
            "name": "Saturator",
            "uri": "query:AudioFx#Saturator",
            "params": [
                {"id": "Drive", "name": "Drive (Amp Emulation)", "range": "0.0 a 1.0 (0 dB a +36 dB)", "behavior": "Distorsión agresiva de amplificador para lead de guitarra.", "default": 0.35}
            ]
        },
        {
            "name": "Delay",
            "uri": "query:AudioFx#Delay",
            "params": [
                {"id": "Dry/Wet", "name": "Dry/Wet (Eco rítmico)", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Repeticiones rítmicas para el motivo pentatónico.", "default": 0.25}
            ]
        }
    ],
    "BRASS": [
        {
            "name": "EQ Eight",
            "uri": "query:AudioFx#EQ%20Eight",
            "params": [
                {"id": "Band 1 On", "name": "Banda 1 High-Pass", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Filtro pasa-altos en 90-110 Hz para limpiar retumbes.", "default": 1.0},
                {"id": "1 Frequency A", "name": "Frecuencia de Corte Subsónico", "range": "0.0 a 1.0 (20 Hz a 500 Hz)", "behavior": "Corte de graves para dejar espacio limpio al bombo y bajo.", "default": 0.28},
                {"id": "Band 3 On", "name": "Banda 3 Bell (Mordida)", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Realce de presencia en 2.8-4 kHz para mordida de trompeta.", "default": 1.0},
                {"id": "3 Frequency A", "name": "Frecuencia de Mordida", "range": "0.0 a 1.0", "behavior": "Brillo y fanfarria en la mezcla.", "default": 0.65}
            ]
        },
        {
            "name": "Glue Compressor",
            "uri": "query:AudioFx#Glue%20Compressor",
            "params": [
                {"id": "Threshold", "name": "Threshold (Umbral)", "range": "-40.0 dB a 0.0 dB", "behavior": "Pegada dinámica para fanfarrias y stabs.", "default": -14.0},
                {"id": "Ratio", "name": "Ratio", "range": "1.0 (2:1) o 2.0 (4:1)", "behavior": "Control de dinámicas de vientos.", "default": 1.0},
                {"id": "Attack", "name": "Attack", "range": "0.0 a 1.0", "behavior": "Ataque medio-lento para preservar el transitorio inicial de boquilla.", "default": 0.50},
                {"id": "Release", "name": "Release", "range": "0.0 a 1.0", "behavior": "Recuperación musical.", "default": 0.0}
            ]
        }
    ],
    "CHOIR": [
        {
            "name": "EQ Eight",
            "uri": "query:AudioFx#EQ%20Eight",
            "params": [
                {"id": "Band 1 On", "name": "Banda 1 High-Pass", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Filtro pasa-altos en 140 Hz para eliminar retumbes graves.", "default": 1.0},
                {"id": "1 Frequency A", "name": "Frecuencia de Corte", "range": "0.0 a 1.0", "behavior": "Despeja el fondo armónico para mantener nitidez coral.", "default": 0.32},
                {"id": "Band 4 On", "name": "Banda 4 High-Shelf (Aire Celestial)", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Realce suave por encima de 8 kHz para brillo etéreo.", "default": 1.0},
                {"id": "4 Frequency A", "name": "Frecuencia de Aire", "range": "0.0 a 1.0", "behavior": "Apertura de armónicos superiores vocales.", "default": 0.80}
            ]
        },
        {
            "name": "ValhallaVintageVerb",
            "uri": "query:Plugins#VST3:Valhalla%20DSP:ValhallaVintageVerb",
            "params": [
                {"id": "Mix", "name": "Mix (Espacio Catedral)", "range": "0.0 a 1.0 (0% a 100%)", "behavior": "Proporción de espacio eclesiástico para el coro.", "default": 0.35},
                {"id": "Decay", "name": "Decay (Cola Litúrgica)", "range": "0.0 a 1.0 (0.2 s a 70 s)", "behavior": "Longitud de resonancia de catedral gótica.", "default": 0.45}
            ]
        }
    ],
    "PERCUSSION": [
        {
            "name": "EQ Eight",
            "uri": "query:AudioFx#EQ%20Eight",
            "params": [
                {"id": "Band 1 On", "name": "Banda 1 High-Pass", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Filtro pasa-altos en 80-120 Hz para percusiones secundarias (shakers, congas, claves).", "default": 1.0},
                {"id": "1 Frequency A", "name": "Frecuencia de Corte", "range": "0.0 a 1.0", "behavior": "Evita ensuciar el subgrave.", "default": 0.28},
                {"id": "Band 3 On", "name": "Banda 3 Bell (Presencia)", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Realce en 3 kHz para articular el ataque.", "default": 1.0},
                {"id": "3 Frequency A", "name": "Frecuencia de Ataque", "range": "0.0 a 1.0", "behavior": "Mordida y claridad.", "default": 0.62}
            ]
        },
        {
            "name": "Glue Compressor",
            "uri": "query:AudioFx#Glue%20Compressor",
            "params": [
                {"id": "Threshold", "name": "Threshold", "range": "-40.0 dB a 0.0 dB", "behavior": "Control de transientes de percusión.", "default": -15.0},
                {"id": "Ratio", "name": "Ratio", "range": "1.0 a 3.0", "behavior": "Compresión suave.", "default": 1.0},
                {"id": "Attack", "name": "Attack", "range": "0.0 a 1.0", "behavior": "Ataque lento para no aplastar el transitorio.", "default": 0.60},
                {"id": "Release", "name": "Release", "range": "0.0 a 1.0", "behavior": "Recuperación rápida.", "default": 0.0}
            ]
        }
    ],
    "FX": [
        {
            "name": "EQ Eight",
            "uri": "query:AudioFx#EQ%20Eight",
            "params": [
                {"id": "Band 1 On", "name": "Banda 1 High-Pass", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Filtro pasa-altos en 60-100 Hz para evitar que el efecto enturbie el subgrave.", "default": 1.0},
                {"id": "1 Frequency A", "name": "Frecuencia de Corte HPF", "range": "0.0 a 1.0", "behavior": "Protección de frecuencias graves en el bus de efectos.", "default": 0.25},
                {"id": "Band 4 On", "name": "Banda 4 Low-Pass", "range": "0.0 (Off) o 1.0 (On)", "behavior": "Filtro pasa-bajos o corte de aire en 12-16 kHz para evitar asperezas.", "default": 1.0},
                {"id": "4 Frequency A", "name": "Frecuencia de Corte LPF", "range": "0.0 a 1.0", "behavior": "Atenuación de sibilancias y resonancias estridentes.", "default": 0.85}
            ]
        },
        {
            "name": "Utility",
            "uri": "query:AudioFx#Utility",
            "params": [
                {"id": "Gain", "name": "Gain (Nivel de Retorno)", "range": "-inf a +35 dB", "behavior": "Ajuste de nivel del efecto en el contexto de mezcla.", "default": 0.0},
                {"id": "Width", "name": "Stereo Width", "range": "0.0 a 1.0 (0% a 400%)", "behavior": "Apertura estéreo espacial del retorno de efecto.", "default": 1.0}
            ]
        }
    ]
}

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
    }
}


