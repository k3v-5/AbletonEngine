# Audio Genesis Engine & Audio Provenance Engine

## 1. Principio Fundamental y Filosofía

> **"El motor nunca debe tomar un sample arbitrario de otra pista o del disco como materia prima creativa salvo que exista una instrucción explícita de reutilización. Todo audio debe tener PROVENIENCIA."**

Tradicionalmente, muchos sistemas generativos o herramientas de sampler recurren a buscar archivos de audio preexistentes y cargarlos en `Simpler`:

```
MIDI / instrumento ──► "¿necesito un sample?" ──► buscar audio arbitrario ──► Simpler
```

Este enfoque destruye la identidad compositiva y genera dependencia de librerías externas o accidentes tímbricos inconexos.

El **Audio Genesis Engine** impone el flujo opuesto: **la canción se convierte en un ecosistema cerrado que se alimenta de sí misma**:

```
                  IDEA MUSICAL ORIGINAL (DNA de la Canción)
                                      │
                                      ▼
                                MIDI ORIGINAL
                                      │
                                      ▼
                           INSTRUMENTO / SÍNTESIS
                                      │
                                      ▼
                            PROCESAMIENTO SONORO
                                      │
                                      ▼
                             RENDER AUDIO (WAV)
                                      │
                                      ▼
                            SELECCIONAR FRAGMENTO
                                      │
                                      ▼
                             TRANSFORMAR / MUTAR
                                      │
                                      ▼
                 DESTINO MUSICAL SEGÚN FUNCIÓN (No solo Simpler)
                                      │
                                      ▼
                              NUEVO INSTRUMENTO
```

---

## 2. Regla 1 — Política de Fuentes (`AudioProvenanceEngine`)
**Ubicación:** [`engine/audio_genesis/provenance.py`](file:///F:/Dev/AbletonEngine/engine/audio_genesis/provenance.py)

Cada archivo de audio que entra al pipeline creativo posee una clasificación estricta:

```python
class SampleOrigin(str, Enum):
    ORIGINAL_GENERATED = "original_generated"  # Renderizado directo de MIDI + instrumento de la canción
    DERIVED_FROM_SONG = "derived_from_song"    # Mutado o re-resampleado de un render previo verificado
    USER_IMPORTED = "user_imported"            # Importado explícitamente por el usuario humano
    CATALOG_SAMPLE = "catalog_sample"          # Sample de catálogo autorizado con metadatos
    UNKNOWN = "unknown"                        # Audio sin linaje / arbitrario
```

### Prohibición Inviolable de Audio `UNKNOWN`
El origen `UNKNOWN` tiene `creative_usage = FORBIDDEN`. Si un componente del motor intenta utilizar un sample sin proveniencia como fuente creativa, se detiene deterministamente la ejecución:

```python
if sample.origin == SampleOrigin.UNKNOWN and not allow_external_override:
    raise CreativeGovernanceError(
        "Cannot use unprovenanced audio as creative source. "
        "The engine never takes arbitrary audio without explicit provenance."
    )
```

### Dossier Genealógico (`SampleProvenanceRecord`)
Cada muestra generada responde inequívocamente a la pregunta: *"¿De dónde salió este audio?"*:

* **`sample_id`:** Identificador único (ej. `genesis_0042`).
* **`origin`:** `ORIGINAL_GENERATED` o `DERIVED_FROM_SONG`.
* **`source`:** Pista origen, clip origen, compases `[start_bar, end_bar]`, si proviene de MIDI, hash de notas.
* **`instrument`:** Dispositivo origen (ej. `Analog Lab V`, `Stage-73 V2`, `SubLab XL`), preset y categoría.
* **`processing`:** Lista encadenada de transformaciones (`saturator`, `transient_slice`, `reverse`, `stretch: 137%`, `pitch_shift: -7st`).
* **`render`:** Metadatos acústicos físicos (formato WAV 44.1kHz 16-bit, duración, canales, pico dBFS, RMS dBFS, content hash).
* **`destination`:** Dispositivo o vehículo objetivo.
* **`parent_sample_id`:** Enlace al ancestro directo.
* **`generation_depth`:** Grado generacional ($0$ para el render raíz, $1+$ para mutaciones sucesivas).

### Árbol Genealógico (`AudioGenealogyTree`)
Permite visualizar e inspeccionar en tiempo real la ascendencia de cualquier sonido del proyecto:

```text
ORIGINAL SONG GENESIS
├── render_piano_a1b2c3d4 [original_generated] (Emotional Piano) -> RenderCache
│   └── mut_a_reverse_e5f6 [derived_from_song] (Emotional Piano) -> Simpler | FX: [analog_saturation, transient_slice, slice_reverse, pitch_shift]
│       └── mut_b_pad_99aa [derived_from_song] (Emotional Piano) -> AudioClip | FX: [granular_freeze, time_stretch, shimmer_diffusion]
└── render_bass_1234 [original_generated] (SubLab XL) -> RenderCache
    └── mut_c_pluck_5678 [derived_from_song] (SubLab XL) -> TransientLayer | FX: [micro_window_isolate, fast_adsr_envelope, harmonic_tuning]
```

---

## 3. Regla 2 — Render Before Sample (`RenderToAudioEngine`)
**Ubicación:** [`engine/audio_genesis/render_engine.py`](file:///F:/Dev/AbletonEngine/engine/audio_genesis/render_engine.py)

Cuando el motor creativo determina que necesita un sample:
1. Comprueba si existe material relevante ya renderizado en la sesión o en caché.
2. Si no existe material, **no busca en el disco**: compone primero un fragmento musical coherente con la tonalidad, escala y motivos de [`CompositionalDNA`](file:///F:/Dev/AbletonEngine/engine/composition/compositional_dna.py).
3. Renderiza físicamente el audio en formato PCM WAV (a través de Ableton Live LOM si está conectado, o mediante síntesis de alta fidelidad determinista en modo modular/test).
4. Registra el certificado de nacimiento como `ORIGINAL_GENERATED` en el `AudioProvenanceEngine`.

---

## 4. Los 4 Pipelines Canónicos de Génesis (`SampleMutationEngine`)
**Ubicación:** [`engine/audio_genesis/mutation_engine.py`](file:///F:/Dev/AbletonEngine/engine/audio_genesis/mutation_engine.py)

El motor implementa 4 caminos canónicos de mutación sonora:

### Génesis A — Resample Melódico
Transforma una frase melódica existente en una nueva textura tímbrica:
$$\text{Melodía MIDI} \to \text{Instrumento} \to \text{Saturación Analógica} \to \text{Render} \to \text{Slice Transientes} \to \text{Reverse Alterno} \to \text{Pitch Shift (-7st)} \to \text{Textura}$$

### Génesis B — Freeze / Ambient Pad
Convierte un bloque de acordes en un pad ambiental envolvente y difuso:
$$\text{Acordes} \to \text{Render} \to \text{Granular Freeze} \to \text{Time-Stretch 400\%} \to \text{Filtro Espectral (HPF/LPF)} \to \text{Reverb Shimmer} \to \text{Pad}$$

### Génesis C — Micro-Sample
Extrae y esculpe un micro-fragmento (80 a 250 ms) de una frase para forjar un instrumento percusivo o melódico nuevo:
$$\text{Frase Original} \to \text{Render} \to \text{Ventana 80–250 ms} \to \text{Envolvente ADSR de Ataque Rápido} \to \text{Afinación a Tónica} \to \text{Pluck / One-Shot}$$

### Génesis D — Audio $\to$ MIDI $\to$ Audio (Ciclo Evolutivo Recurrente)
Crea un descendiente evolutivo lejano pero genéticamente emparentado con la obra:
$$\text{MIDI Original} \to \text{Render} \to \text{Deformación Extrema} \to \text{Análisis Onsets/Pitch} \to \text{Nuevo MIDI} \to \text{Nuevo Instrumento} \to \text{Nuevo Render}$$

---

## 5. Diversificación de Destinos (`SampleInstrumentBuilder`)
**Ubicación:** [`engine/audio_genesis/instrument_builder.py`](file:///F:/Dev/AbletonEngine/engine/audio_genesis/instrument_builder.py)

El sample resultante no se envía ciegamente a `Simpler`. Se enruta según su rol musical exacto:

| Destino | Vehículo en Live 12 | Función Musical |
| :--- | :--- | :--- |
| **`SIMPLER_MELODIC`** | `Simpler (Modo Classic / 1-Shot)` | Interpretación monofónica o polifónica (leads, bajos, melodías con afinación root y loop). |
| **`SIMPLER_SLICED`** | `Simpler (Modo Slicing)` | Resecuenciación rítmica y disparo de cortes por transientes. |
| **`AUDIO_CLIP`** | `Audio Track en Arrangement` | Lecho continuo de textura, foley orgánico o swell sobre la línea de tiempo. |
| **`GRANULAR_STRETCH`** | `Cadena Grain Delay / Auto Filter` | Texturas flotantes y pads evolutivos con modulación temporal. |
| **`TRANSIENT_LAYER`** | `Instrument Rack en paralelo con EQ High Pass` | Refuerzo de pegada transiente (punch/bite) sobre bombo o caja (Frankenstein 2.0). |
| **`ATMOSPHERE_BED`** | `Canal de Retorno 100% Wet` | Cola difusa de reverberación infinita y apertura estéreo para transiciones. |
| **`DRUM_RACK_PAD`** | `Pad de Drum Rack (C1..B2)` | Integración directa en un kit de percusión autógeno. |

---

## 6. Orquestador Maestro (`AudioGenesisEngine`)
**Ubicación:** [`engine/audio_genesis/audio_genesis_engine.py`](file:///F:/Dev/AbletonEngine/engine/audio_genesis/audio_genesis_engine.py)

Unifica los 4 componentes en una sola llamada:
```python
genesis = AudioGenesisEngine()
result = genesis.create_provenanced_sound(
    song_dna=my_dna,
    musical_need="ambient_pad",
    target_destination=TargetInstrumentDestination.AUDIO_CLIP
)
```

Devuelve un objeto [`GenesisSoundResult`](file:///F:/Dev/AbletonEngine/engine/audio_genesis/audio_genesis_engine.py) con el render raíz, la mutación aplicada, el plan de instrumentación, el certificado de proveniencia y el árbol genealógico en formato ASCII.

---

## 7. Integración en el Ecosistema del Motor

1. **[`SonicMutationLab`](file:///F:/Dev/AbletonEngine/engine/sound_design/sonic_mutation_lab.py):** Todo candidato a mutación ahora incluye un `SampleProvenanceRecord` verificado con `is_autogenous=True`.
2. **[`CompositionalDNA`](file:///F:/Dev/AbletonEngine/engine/composition/compositional_dna.py):** Mantiene en `provenance_records` y `sonic_families` el registro acumulativo de todos los sonidos y linajes nacidos de la propia composición.
3. **[`CatalogMemory`](file:///F:/Dev/AbletonEngine/engine/memory/catalog_memory.py):** Incorpora `audit_audio_provenance()` para certificar que ninguna canción del catálogo contenga audio pirata o `UNKNOWN`.
4. **[`SimplerSlicer`](file:///F:/Dev/AbletonEngine/engine/instruments/simpler_slicer.py):** Incorpora `load_provenanced_sample_and_slice()`, verificando la proveniencia antes de cargar o cortar cualquier archivo en Ableton Live.

---

## 8. Sonic Recursion & Self-Sampling Engine: Creatividad Recursiva

**Ubicaciones:**  
- [`engine/audio_genesis/sonic_recursion.py`](file:///F:/Dev/AbletonEngine/engine/audio_genesis/sonic_recursion.py)  
- [`engine/audio_genesis/self_sampling_engine.py`](file:///F:/Dev/AbletonEngine/engine/audio_genesis/self_sampling_engine.py)

Una vez resuelta la proveniencia estricta, el sistema escala hacia la **creatividad recursiva**: el motor se auto-retroalimenta preguntándose:
> *"¿Qué elemento de esta canción puedo convertir en materia prima para crear otro elemento que todavía no existe?"*

### Creación de Sonidos ANTES de Conocer su Ubicación Exacta
En lugar de buscar un sample pasivamente cuando falta un instrumento en el arrangement, el motor opera de forma proactiva:
$$\text{Necesidad estética (ej. textura oscura)} \longrightarrow \text{Semilla de alto valor} \longrightarrow \text{Render} \longrightarrow \text{Mutación} \longrightarrow \text{5 Candidatos} \longrightarrow \text{Taste Engine} \longrightarrow \text{Contexto}$$

```
                               CANCIÓN / COMPOSITIONAL DNA
                                            │
                                            ▼
                       ┌─────────────────────────────────────────┐
                       │       SELF-SAMPLING ENGINE (FACHADA)    │
                       │   "¿Qué elemento transformo para crear  │
                       │    el elemento que aún no existe?"      │
                       └────────────────────┬────────────────────┘
                                            │
           ┌────────────────────────────────┼────────────────────────────────┐
           │                                │                                │
           ▼                                ▼                                ▼
┌─────────────────────┐          ┌─────────────────────┐          ┌─────────────────────┐
│  SIGNIFICANCE SCAN  │          │ ROLE-DEPENDENT MUT. │          │  SONIC RECURSION &  │
│  (Regla 2: Semilla) │          │  (Regla 3: Ramas)   │          │  DISTANCE AUDITOR   │
│                     │          │                     │          │  (Reglas 1 y 4)     │
│ • Motivos Clave     │          │ • BASS Sub-isolate  │          │ • 0.25 <= Dist <=.88│
│ • Progresión Chords │          │ • PAD Stretch 600%  │          │ • Gen Depth <= 3    │
│ • Signature Gestures│          │ • PERC Micro-sample │          │ • Veto Degeneración │
│ • Drum Transients   │          │ • RISER Swell       │          │ • Veto Copy/Paste   │
└──────────┬──────────┘          └──────────┬──────────┘          └──────────┬──────────┘
           │                                │                                │
           └────────────────────────────────┼────────────────────────────────┘
                                            │
                                            ▼
                       ┌─────────────────────────────────────────┐
                       │       GENERATIVE TASTE EVALUATION       │
                       │   10 Ejes Perceptuales + Risk Bonus     │
                       │   Selección de los mejores candidatos   │
                       └────────────────────┬────────────────────┘
                                            │
                                            ▼
                       ┌─────────────────────────────────────────┐
                       │          SONIC FAMILY REGISTRY          │
                       │            (Regla 5: Memoria)           │
                       │  Registro de Familias Sonoras Autógenas │
                       │  Reutilización de linajes tímbricos     │
                       └─────────────────────────────────────────┘
```

### Las 5 Reglas Fundamentales de la Recursión Sónica:

1. **Regla 1 (Anti-reciclaje literal vs Anti-caos degenerado):**  
   Audita la distancia acústico-espectral ($\Delta$) entre el hijo y el padre:
   * $\Delta < 0.25$: **VETO** por reciclaje literal / copy-paste perezoso.
   * $\Delta > 0.88$: **VETO** por degeneración acústica / pérdida de parentesco con la obra.
   * $0.25 \le \Delta \le 0.88$: **APROBADO** (Sweet spot de parentesco genético audible).
2. **Regla 2 (Prioridad de material musicalmente significativo):**  
   Escanea y puntúa las semillas según su valor compositivo: Motivo Principal ($1.0$), Acordes Clave ($0.90$), Gestos Firma ($0.85$), Transientes de Batería ($0.80$), en contraste con capas secundarias o ruido plano ($0.40$).
3. **Regla 3 (Mutación dependiente del rol):**  
   Un mismo render original se bifurca en 5 roles musicales con cadenas DSP especializadas:
   * `BASS`: Aislamiento paso-bajos a 110 Hz, saturación armónica par y compresión VCA.
   * `PAD_TEXTURE`: Time-stretch al 600%, difusión granular y shimmer infinito.
   * `PERCUSSION`: Micro-sample (40–120 ms), ataque transitorio y afinación tonal.
   * `TRANSITION_RISER`: Reverso, sweep exponencial de pitch (+24 semitonos) y barrido HPF.
   * `EAR_CANDY`: Modulación estéreo, micro-chopping en cuadrícula de fusa (1/32) y bitcrush de 12 bits.
4. **Regla 4 (Profundidad genética limitada):**  
   Límite estricto de generaciones: $\text{Gen } 0 \to 1 \to 2 \to 3$. Se prohíbe re-mutar material con $\text{generation\_depth} \ge 3$, forzando a la IA a fertilizarse nuevamente de las semillas raíz de la obra.
5. **Regla 5 (Memoria de identidad y Familias Sonoras Autógenas):**  
   Registra en [`SonicFamilyRegistry`](file:///F:/Dev/AbletonEngine/engine/audio_genesis/sonic_recursion.py) toda mutación exitosa como una **Familia Sonora**, permitiendo la **polinización cruzada** entre secciones (ej. el Rhodes del Verso 1 fertiliza la textura del Puente o el transitorio del Hook 2).

