# Motor Autónomo de Síntesis y Diseño Sonoro de Vital (`VitalSoundEngine`)

> **Documento Técnico y Manual Operativo Integral**  
> **Ubicación en el Núcleo:** [`engine/sound_design/`](file:///d:/Proyectos/TEST/AbletonEngine-main/AbletonEngine-main/engine/sound_design/)  
> **Estado:** 33/33 Tests Aprobados (100% Verde) | 61 Presets Indexados | Soporte Granular y Macro  

---

## 1. Visión General y Propósito

El **Vital Sound Engine** es un subsistema autónomo de síntesis y diseño de sonido de calibre comercial para el sintetizador **Vital** (`.vital`). Está completamente desacoplado del flujo de sesión de Live y de interfaces gráficas, permitiendo a agentes de IA, productores algorítmicos o scripts crear, esculpir, auditar y mutar parches con calidad de estudio.

### Principio Rector: Seguridad Permisiva ("Safety Without Censorship")
El motor implementa una filosofía de **libertad creativa total con red de seguridad acústica y física**:
- **Garantía Anti-Silencio:** Impide que cualquier combinación errática o alucinada de parámetros resulte en un archivo inaudible (volumen en cero, filtros cerrados por debajo de frecuencias audibles, envolventes sin duración o ausencia de osciladores).
- **Garantía Anti-Daño:** Clampea resonancias excesivas ($>0.75$) que causan aullidos de retroalimentación infinita perjudiciales para monitores y oídos.
- **Sin Camisa de Fuerza Creativa:** Permite cualquier sonido concebible siempre que sea físicamente audible y estructurado válidamente:
  - Sub-graves profundos ($20-35\text{ Hz}$) sin cortes artificiales.
  - Clics percusivos y transitorios de batería ultrarrápidos ($25-45\text{ ms}$).
  - Paisajes sonoros y pads ambientales con ataques de hasta $15\text{ segundos}$.
  - Filtros High-Pass, Band-Pass, Comb y Formant en sus rangos completos.
  - Capas de ruido, vinilo y texturas generadas proceduralmente en el sampler interno.

---

## 2. Mapa Arquitectónico de Componentes

```
engine/sound_design/
├── vital_parameter_schema.py   # Esquema de 772 parámetros, límites físicos e invariantes
├── vital_wavetable_synth.py    # Generador matemático de wavetables Base64 y búferes PCM
├── vital_archetype_catalog.py  # Indexador y selector inteligente de 61 presets base
├── vital_sound_sculptor.py     # Escultor semántico macro (7 Principios de KSHMR)
├── vital_design_validator.py   # Validador y auditor de especificaciones granulares
├── vital_modular_designer.py   # Diseñador modular (síntesis de ondas, filtros, S&H, FX)
└── vital_sound_engine.py       # Fachada y orquestador maestro E2E
```

### 2.1 [`vital_sound_engine.py`](file:///d:/Proyectos/TEST/AbletonEngine-main/AbletonEngine-main/engine/sound_design/vital_sound_engine.py) — Orquestador Maestro
Punto de entrada unificado que expone:
- `create_preset(name, role, directives, output_dir)`: Clona un arquetipo óptimo del catálogo y lo transforma según directivas macro.
- `design_granular_preset(name, spec, role_archetype, output_dir, strict)`: Síntesis quirúrgica a partir de especificaciones JSON a bajo nivel.
- `mutate_preset(source_path, directives, new_name, output_dir)`: Mutación no destructiva de parches existentes.
- `audit_preset_file(file_path)`: Auditoría forense en disco de volumen, generadores activos, filtros y duración.

### 2.2 [`vital_modular_designer.py`](file:///d:/Proyectos/TEST/AbletonEngine-main/AbletonEngine-main/engine/sound_design/vital_modular_designer.py) — Diseñador Modular Granular
Materializa componentes aislados en parámetros reales de Vital:
- **Formas de Onda:** Genera tablas de onda sintetizadas según la demanda (`SINE`, `SAW`, `TRIANGLE`, `PULSE`, `FM`, `VOCAL`, `ANALOG_WARM`, `CHEBYSHEV`, `METALLIC`, `WHITE_NOISE`, `DIRTY_SAW`).
- **Modelos de Filtro:** Asigna modelos internos de Vital:
  - `ANALOG_12` / `ANALOG_24` (`0.0`)
  - `DIRTY` (`1.0`)
  - `LADDER` (`2.0`)
  - `DIGITAL` (`3.0`)
  - `DIODE_303` (`4.0`)
  - `FORMANT` (`5.0`)
  - `COMB` (`6.0`)
- **Modos de Filtro:** Low-Pass (`0.0`), Band-Pass (`1.0`), High-Pass (`2.0`), Notch (`1.0`).
- **LFOs Personalizados:** Dibuja geometrías complejas punto a punto: Sample & Hold de 16 coordenadas aleatorias/estocásticas, rampas ascendentes/descendentes y cuadradas.
- **Efectos Integrados:** Configura distorsión, reverb, delay, chorus, compresor multibanda OTT y EQ paramétrica de 3 bandas.
- **Variación Estocástica:** Inyecta micro-derivas de afinación ($\pm 2\text{ cents}$) y tolerancia analógica en el corte de filtro basadas en una semilla (`seed`), garantizando tomas infinitas e irrepetibles.

### 2.3 [`vital_design_validator.py`](file:///d:/Proyectos/TEST/AbletonEngine-main/AbletonEngine-main/engine/sound_design/vital_design_validator.py) — Auditor y Diagnóstico de Entradas
Verifica las intenciones del productor o de la IA antes de la síntesis:
- **Modo Resiliente (`strict=False`):** Corrige automáticamente entradas erradas (p. ej., nombres de onda mal escritos mediante distancia Levenshtein difusa) y emite un `ValidationReport` con lista de advertencias y correcciones aplicadas.
- **Modo Estricto (`strict=True`):** Lanza una excepción formal `VitalValidationError` detallando los errores cuando se requiere validación crítica en pipelines de CI/CD.

### 2.4 [`vital_wavetable_synth.py`](file:///d:/Proyectos/TEST/AbletonEngine-main/AbletonEngine-main/engine/sound_design/vital_wavetable_synth.py) — Sintetizador Matemático de Wavetables
Generador algorítmico sin dependencias externas:
- Produce ciclos individuales de **2,048 puntos flotantes IEEE-754 little-endian (`float32`)**, empaquetados en cadenas Base64 nativas de Vital (8,192 bytes por cuadro).
- Sintetiza tablas morfables de hasta 256 posiciones continuas con interpolación espectral.
- Módulo `generate_sampler_buffer()`: Genera búferes de audio PCM de 16 bits para el Sampler interno de Vital (`WHITE_NOISE`, `PINK`, `VINYL`, `CLICK`, `TRANSIENT`).

### 2.5 [`vital_sound_sculptor.py`](file:///d:/Proyectos/TEST/AbletonEngine-main/AbletonEngine-main/engine/sound_design/vital_sound_sculptor.py) — Escultor Acústico y Principios KSHMR
Aplica las 7 leyes de producción comercial descubiertas por ingeniería inversa:
1. **Roland JP-8000 7-Voice Sweet Spot:** Unísono de 7 voces con detune en $\sim 1.95$, manteniendo un centro mono sólido y apertura lateral estéreo sin cancelaciones de fase.
2. **Regla del Delay Cero (Anti-Clutter):** Delay apagado en el preset para delegar repeticiones a envíos auxiliares del DAW. Reverb con corte pasa-altos en $25-45\text{ Hz}$ para proteger sub-graves.
3. **Distorsión Focalizada en Medios:** Soft Clip con `distortion_filter_cutoff = 80.0` ($\sim 830\text{ Hz}$), saturando el cuerpo sin generar aspereza digital en agudos.
4. **Transient Laser Pitch-Punch:** Modulación de `env_2` ($35\text{ ms}$, decay power $-2.0$) sobre la transposición de los 3 osciladores asignada a Macro 1 (`PUNCH DROP`).
5. **Capa Sutil de Aire:** Inyección en el sampler de ruido blanco al $14-18\%$ de volumen en bucle.
6. **Curvatura Logarítmica Universal:** `env_1_decay_power = -2.0` con sustain al $100\%$ en leads para permitir sidechain agresivo en mezcla.
7. **Compresor OTT Calibrado:** Mix al $25-35\%$, ganancias de banda de $13.5\text{ dB}$ y agudos a $16.9\text{ dB}$.

### 2.6 [`vital_parameter_schema.py`](file:///d:/Proyectos/TEST/AbletonEngine-main/AbletonEngine-main/engine/sound_design/vital_parameter_schema.py) — Esquema de Parámetros e Invariantes
- Mapea los 772 parámetros del archivo `.vital`.
- Maneja la escala no lineal de volumen de Vital: nominal en $5400.0$, rango admisible $[3000.0 .. 12000.0]$.
- Define umbrales de corte seguros adaptados al modo de filtro:
  - Low-Pass: no permite corte $< 18.0$ ($\sim 23\text{ Hz}$).
  - High-Pass: no permite corte $> 118.0$ ($\sim 7\text{ kHz}$) para evitar eliminar todo el espectro musical.

### 2.7 [`vital_archetype_catalog.py`](file:///d:/Proyectos/TEST/AbletonEngine-main/AbletonEngine-main/engine/sound_design/vital_archetype_catalog.py) — Catálogo de Arquetipos
Indexa automáticamente presets disponibles en el sistema y los clasifica en 10 categorías acústicas.

---

## 3. Catálogo e Índice de Presets (61 Presets Indexados)

| Categoría | Total | Presets Clave Indexados | Características Tímbricas |
|---|:---:|---|---|
| **`BASS_808`** | 6 | `PIE_Carnage_808`, `PIE_Chroma_808`, `PIE_Test_808`, `Procedural_808_Csharp_Glide` | Graves profundos, saturación en medios, glide mono estricto |
| **`BASS_REECE`** | 4 | `PIE_Heavy_Reese`, `PIE_Test_Reese` | Movimiento de desafinación múltiple, filtrado paso banda |
| **`BASS_SUB`** | 2 | `KSHMR Sub Bass 1.vital` | Senos puros con segundo armónico sutil, pre-filtro limpio |
| **`BASS_PUNCH`** | 8 | `KSHMR Bass 1`, `KSHMR Bass 2`, `KSHMR Bass 3`, `KSHMR Bass 4` | Transitorio agresivo en el ataque, corte en medios |
| **`LEAD_SAW`** | 24 | `KSHMR Lead 1` a `KSHMR Lead 11`, `PIE_Bones_Lead`, `PIE_Euphoric_Lead` | 7 voces JP-8000, OTT calibrado, pitch drop de 35ms |
| **`LEAD_PLUCK`** | 2 | `KSHMR Lead 6` | Decaimiento rápido ($150-300\text{ ms}$), sustain cero |
| **`CHORD_SUPERAW`**| 6 | `KSHMR Chord 1` a `KSHMR Chord 6` | Capas apiladas de octavas, apertura estéreo amplia |
| **`PAD_LUSH`** | 5 | `KSHMR Pad 1`, `KSHMR Pad 2`, `KSHMR Stab Pad` | Ataques lentos, modulación de wavetable, colas de reverb |
| **`KEYS_RHODES`** | 3 | `PIE_Tyler_Rhodes`, `PIE_Warm_Rhodes` | Curvaturas Chebyshev cálidas, modulación de trémolo |
| **`TEMPLATE`** | 1 | `engine/sound/vital/template.vital` | Inicialización limpia para diseño desde cero |

---

## 4. Guía de Uso del Motor

### 4.1 Generación Macro (Vía Directivas Semánticas)

```python
from engine.sound_design import VitalSoundEngine

engine = VitalSoundEngine()

# Crear un Lead estilo festival con las 7 leyes de KSHMR
preset_path = engine.create_preset(
    preset_name="Mainstage_Anthem_Lead",
    role="LEAD_SAW",
    directives={
        "brightness": 0.85,        # Filtro abierto + capa de aire White Noise
        "warmth_drive": 0.60,      # Distorsión Soft Clip centrada en 80.0
        "punch": 0.90,             # Pitch drop de 35ms en Macro 1
        "decay_sustain": 1.0,      # 100% sustain para sidechain en DAW
        "stereo_width": 0.75,      # 7 voces JP-8000 + apilamiento de octavas
        "space_dimension": 0.45,   # Reverb exuberante sin delay interno
        "custom_wavetable": "VOCAL" # Tabla morfable de formantes vocales
    }
)
```

### 4.2 Diseño Granular Modular (Especificación a Bajo Nivel)

```python
# Crear un bajo ácido con filtro Diode 303 y modulación Sample & Hold
preset_path, report = engine.design_granular_preset(
    preset_name="Acid_Diode_Modular",
    spec={
        "oscillators": {
            "osc_1": {"waveform": "SAW", "octave": -1, "unison": 1, "level": 0.85},
            "osc_2": {"waveform": "PULSE", "pulse_width": 0.35, "octave": 0, "level": 0.40}
        },
        "filter": {
            "model": "DIODE_303",
            "mode": "LOW_PASS",
            "cutoff_hz": 1200.0,
            "resonance": 0.55,
            "drive": 0.30
        },
        "modulations": [
            {
                "source": "LFO_1",
                "destination": "FILTER_CUTOFF",
                "shape": "STEPPED_RANDOM",
                "rate": "1/16",
                "amount": 0.60
            }
        ],
        "sampler": {
            "on": True,
            "sample_type": "VINYL",
            "level": 0.15,
            "loop": True
        },
        "effects": {
            "distortion": {"on": True, "drive_db": 12.0},
            "reverb": {"on": True, "mix": 0.20}
        },
        "variation": 0.35, # 35% de variación analógica estocástica
        "seed": 42
    },
    role_archetype="BASS_PUNCH"
)

print(f"Preset generado: {preset_path}")
print(f"Reporte de validación: Errores={report['error_count']}, Advertencias={report['warning_count']}")
```

### 4.3 Auditoría Forense de un Parche en Disco

```python
audit = engine.audit_preset_file(preset_path)
if audit["valid"] and audit["audible"]:
    print(f"Parche auditado exitosamente: {audit['preset_name']}")
    print(f"Volumen: {audit['volume']} | Corte: {audit['filter_cutoff']} | Generadores activos: True")
```

---

## 5. Resumen de Pruebas Automatizadas

El motor cuenta con una suite integral de 33 pruebas en `tests/test_vital_modular_designer.py` y `tests/test_vital_sound_engine.py`:

```powershell
python -m pytest tests/test_vital_modular_designer.py tests/test_vital_sound_engine.py -v
```

- **Sintetizador de Wavetables (7 pruebas):** Generación de seno, sierra, triángulo, FM, formantes vocales, Chebyshev y PCM para sampler.
- **Esquema e Invariantes (3 pruebas):** Clampeo de volumen, clampeo de filtro y ejecución de invariantes anti-silencio.
- **Catálogo de Arquetipos (3 pruebas):** Indexación automática y selección de arquetipos por roles.
- **Escultor Semántico (2 pruebas):** Modulación de brillo y blindaje mono de bajas frecuencias.
- **Validador Granular (5 pruebas):** Validación correcta, corrección difusa, protección subsónica, protección de resonancia y modo estricto.
- **Diseñador Modular (3 pruebas):** Materialización de modelos de filtro (Diode, Comb, Dirty), modulación S&H y apilamiento de ondas.
- **Variación Estocástica (1 prueba):** Diversidad tímbrica entre tomas con idéntico prompt.
- **Libertad Creativa y Seguridad Permisiva (5 pruebas):** Sub-graves de 32 Hz, clics percusivos de 35 ms, pads ambientales con sampler, filtros High-Pass permisivos y campanas metálicas FM.
- **Flujos End-to-End (4 pruebas):** Generación de 808, Leads vocales, mutación no destructiva y pads orquestales.
