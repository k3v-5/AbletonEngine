# Decent Sampler Instrument Compiler & Engine Manual

Este documento detalla la arquitectura, el modelo intermedio (IR), el validador en 3 niveles, las políticas de seguridad acústica y el compilador procedural de instrumentos para **Decent Sampler** (`.dspreset`).

---

## 1. Misión Arquitectónica

Decent Sampler actúa como el **Pilar de Instrumentos Multi-Muestreados** dentro de nuestro motor de producción musical, complementando a **Vital Synth** (enfocado en síntesis sustractiva/wavetable/FM digital):

```
                                  Motor de Diseño Sonoro
                                             │
                     ┌───────────────────────┴───────────────────────┐
                     ▼                                               ▼
         [ Vital Sound Engine ]                         [ Decent Sampler Engine ]
     Síntesis Digital Pura (DSP)                     Instrumentos Acústicos & Muestras
  • Leads, Plucks, 808s sintéticos                • Pianos de cola, Cuerdas orquestales
  • Modulación LFO, Chebyshev, FM                 • Baterías multicapa con choke & RR
  • JSON binario zlib (.vital)                    • Árbol XML determinista (.dspreset)
```

---

## 2. El Pipeline del Compilador de Instrumentos

En lugar de concatenar XML empíricamente, el sistema opera como un **compilador de instrumentos**:

```
  Archivos de Audio (.wav / .flac)
                 │
                 ▼
     [ SampleAnalyzer ] (Metadata, Onset, Pitch, Peak/RMS)
                 │
                 ▼
     [ SampleMapPlanner ] (Algoritmo de cobertura de zonas de notas y velocidad)
                 │
                 ▼
      [ InstrumentModel ] (Modelo Intermedio de Dominio en Python puro)
                 │
        ┌────────┴────────┐
        ▼                 ▼
   [ Validator ]    [ DSPresetSerializer ]
 (Nivel 1, 2 y 3)         │
                          ▼
                  Archivo .dspreset
```

### Ventajas del desacoplamiento:
1. **Modelado Puro**: Se puede planear, testear y manipular el mapeo de teclas y velocidades sin tocar XML.
2. **Round-Trip Fidelity**: El serializador y deserializador garantizan que `Model -> XML -> Model` conserva el 100% de la información.
3. **Validación Formal**: Errores sintácticos, de consistencia y de heurística acústica se reportan por separado.

---

## 3. Jerarquía de Validación en 3 Niveles

| Nivel | Ámbito | Responsabilidad | Ejemplo |
| :--- | :--- | :--- | :--- |
| **Tier 1** | **Formato & Especificación** | Valida sintaxis XML, etiquetas reconocidas, atributos válidos, tipos y nombres canónicos de efectos. | El tipo de efecto debe ser canónico en minúsculas (`lowpass`, `reverb`). |
| **Tier 2** | **Consistencia Estructural** | Valida relaciones matemáticas internas y portabilidad de archivos. | `loNote <= rootNote <= hiNote`, `loVel <= hiVel`, rutas relativas con `/`. |
| **Tier 3** | **Políticas de Audio y Recursos** | Heurísticas no bloqueantes de seguridad acústica y consumo de CPU. | Prevención de clics DC (`attack >= 0.001s`), efectos de cola a nivel global. |

---

## 4. Módulos del Sistema (`engine/sound_design/decent_sampler/`)

### `schema.py` (Tier 1: Especificación Oficial)
* Define los 19 procesadores de efectos canónicos en minúsculas:
  * **Filtros**: `lowpass`, `lowpass_1pl`, `highpass`, `bandpass`, `notch`, `peak`.
  * **Espaciales y Dinámica**: `reverb`, `delay`, `chorus`, `phaser`, `convolution`, `pitch_shift`, `wave_folder`, `wave_shaper`, `stereo_simulator`, `bit_crusher`, `compressor`, `stutter`, `gain`.
* Define los tokens válidos de bindings: `AMP_VOLUME`, `PAN`, `GLOBAL_TUNING`, `ENV_ATTACK`, `FX_FILTER_FREQUENCY`, `FX_REVERB_WET_LEVEL`, etc.
* Límites físicos de MIDI: notas (0–127), velocidades (0–127), frecuencias (20.0–22000.0 Hz).

### `model.py` (Representación Intermedia - IR)
* Clases de datos fuertemente tipadas:
  * `InstrumentModel`: Raíz del instrumento (volumen, afinación, UI, grupos, efectos, moduladores).
  * `GroupModel`: Colección de muestras que comparten envolvente ADSR, dinámicas de velocidad y voice choke.
  * `SampleZoneModel`: Zona individual de audio con puntos de loop, afinación y round-robin.
  * `EffectModel`: Definición de un efecto y sus parámetros DSP.
  * `ControlModel` y `BindingModel`: Perillas UI macro vinculadas a parámetros del motor.

### `policies.py` (Tier 3: Políticas Acústicas y de UX)
* **`AudioSafetyPolicy`**:
  * Suelo de ataque recomendado: `0.001s` (1 ms) para mitigar saltos DC si la muestra no inicia en cruce por cero.
  * Suelo de relajación recomendado: `0.005s` (5 ms) para evitar cortes abruptos al soltar la tecla.
* **`ResourcePolicy`**:
  * Recomienda que `reverb` y `delay` operen a nivel de instrumento (global) y no por grupo para proteger la CPU.
* **`UXPolicy`**:
  * Calcula coordenadas `(x, y)` automáticas con espaciado de 100px para perillas macro.

### `sample_analyzer.py`
* Infiere tono fundamental, capa de velocidad y round-robin desde el nombre del archivo (ej. `piano_c4_soft_rr2.wav` -> root=60, layer="soft", rr=2).
* Convierte nombres de notas a números MIDI (`C4` -> 60, `A#3` -> 58).

### `sample_mapper.py` (`SampleMapPlanner`)
* **Mapeo gapless**: Calcula automáticamente los puntos medios entre notas fundamentales para que no existan teclas mudas ni solapamientos accidentales.
* **Capas de velocidad**: Ordena las capas según jerarquía dinámica musical (`pp` < `p` < `soft` < `medium` < `hard` < `f` < `ff`) y divide el rango 0–127 uniformemente.

### `sanitizer.py` (`DecentSamplerSanitizer`)
* Modo de auto-corrección resiliente:
  * Convierte mayúsculas en tipos de efecto a minúsculas canónicas.
  * Convierte barras invertidas de Windows `\` en plecas `/` y remueve letras de disco (`C:\`).
  * Corrige rangos invertidos (`loNote > hiNote`) y ajusta `rootNote` al rango válido.
  * Migra efectos de tiempo (reverb/delay) colocados en grupos al canal global.

### `serializer.py` (`DSPresetSerializer`)
* Genera XML UTF-8 formateado y determinista.
* Parsea XML `.dspreset` de vuelta a `InstrumentModel` para pruebas de round-trip.

### `builder.py` (`DecentSamplerBuilder`)
* Fachada fluida de alto nivel para diseñar instrumentos por código:
  ```python
  from engine.sound_design.decent_sampler import DecentSamplerBuilder

  builder = DecentSamplerBuilder(name="Warm Upright Piano")
  builder.add_sample("Samples/piano_c3.wav", root_note=48, lo_note=36, hi_note=59)
  builder.add_sample("Samples/piano_c4.wav", root_note=60, lo_note=60, hi_note=84)
  builder.set_envelope(attack=0.002, decay=8.0, sustain=0.0, release=0.5)
  builder.add_effect("lowpass", frequency=14000.0, resonance=0.7)
  builder.add_macro_knob(label="Tone", parameter="FX_FILTER_FREQUENCY", target_index=0, min_value=500.0, max_value=20000.0)

  xml_preset = builder.compile(strict=True)
  builder.save("Presets/WarmPiano.dspreset")
  ```

---

## 5. Arquetipos Incorporados (`engine/sound_design/decent_sampler/templates/`)

1. **`create_acoustic_piano()`**:
   * Zonas multicapa, disparadores de liberación (*release triggers*), reverberación de sala de conciertos y perillas de *Tone*, *Space* y *Release*.
2. **`create_orchestral_strings()`**:
   * Ataque expresivo lento, ensemble chorus, reverberación amplia y perillas de *Expression*, *Ensemble*, *Reverb* y *Attack*.
3. **`create_drum_kit()`**:
   * Disparo *one-shot* (`ampEnvEnabled=False`), 3x Round-Robin en la caja para evitar efecto ametralladora, y asfixia de hi-hat (*choke groups*) donde el hi-hat cerrado silencia al abierto mediante `silencedByTags="hh_closed"`.
4. **`create_808_sub_bass()`**:
   * Sub-bajo sintonizado con seguimiento de tono completo (`pitchKeyTrack=1.0`), portamento legato (`glideTime=0.08`), wave folding y saturación con perillas de *Drive*, *Cutoff*, *Glide* y *Release*.

---

## 6. Cobertura de Pruebas Automatizadas

La suite en `tests/decent_sampler/` cuenta con **24 pruebas unitarias** pasando al 100%:
* `test_schema.py`: Verificación de tokens, límites y tipos de efectos.
* `test_model.py`: Composición e inmutabilidad por clonación profunda del IR.
* `test_sample_mapper.py`: Cobertura de teclas sin huecos y división de capas dinámicas.
* `test_validator.py`: Detección en los 3 niveles de validación y modo estricto.
* `test_sanitizer.py`: Auto-corrección de notas invertidas, normalización de rutas y clics.
* `test_roundtrip.py`: Fidelidad absoluta `Model -> XML -> Model`.
* `test_golden_presets.py`: Comparación determinista contra snapshots de referencia y validación de los 4 arquetipos.
