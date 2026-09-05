# Ableton Production Intelligence Engine (PIE)

> **Autonomous AI-Assisted Music Production, Mixing, and Mastering Middleware for Ableton Live 12 Suite.**
> Powered by Model Context Protocol (FastMCP) with 204 specialized tools and 423 automated unit/acceptance/chaos tests (100% pass rate).

📚 **Documentación Principal:**
- 📖 [**Guía de Usuario y Manual Operativo (USER_GUIDE.md)**](docs/USER_GUIDE.md)
- 🗺️ [**Índice Maestro de Módulos, Herramientas y Sitemap (INDEX.md)**](docs/INDEX.md)
- 🎛️ [**Playbook de Prompting y Recetas de Producción (PROMPTING_PLAYBOOK.md)**](docs/PROMPTING_PLAYBOOK.md)
- 🔌 [**Catálogo del Navegador y URIs de Plugins VST3 (ABLETON_BROWSER_CATALOG.md)**](docs/ABLETON_BROWSER_CATALOG.md)
- 📋 [**Matriz Integral de Capacidades y Herramientas API (API_CAPABILITIES_MATRIX.md)**](docs/API_CAPABILITIES_MATRIX.md)
- 🚀 [**Hoja de Ruta y Pasos Siguientes (NEXT_STEPS.md)**](docs/NEXT_STEPS.md)
- 🛡️ [**Documento 15: Failure Injection & Chaos Resilience**](docs/production_failure_injection.md)
- 🔬 [**Documento 14: Integration Tests & Golden Pipeline**](docs/production_integration.md)
- 🔌 [**Documento 13: Superficie FastMCP de Gobernanza**](docs/production_mcp.md)
- ⏪ [**Documento 12: Rollback de Primera Clase**](docs/production_rollback.md)

---

## Core Philosophy & Design Axioms

- **"The LLM decides musical intent; the Engine decides how to execute it; Ableton Live executes."**
- **"Separation of Mix vs. Master: Low-end mud, kick/bass masking, and headroom defects must be resolved in the mix, NEVER patched in mastering."**
- **"Principle of Minimum Intervention: DO NOTHING is a valid and preferred outcome if the session already meets target acoustic standards."**
- **"Causal Governance & Verifiability: Every production action must be traceably linked to concrete measurements, musical intent, and post-execution verification in an acyclic causal DAG."**
- **"Memory as Evidence, Not Blind Autopilot: Historical decisions serve as candidate evidence; they NEVER auto-execute without passing current session policies and verification."**
- **"Inviolable Guardrails: CRITICAL policies (limiter gain reduction <= 2.5 dB, true peak <= -0.3 dBTP, master EQ <= 2 bands) CANNOT be bypassed by LLM overrides."**
- **"No Fake DSP and No Fake Success: All spectral and perceptual measurements use real DSP algorithms (ITU-R BS.1770-5 LUFS, True Peak 4x sinc FIR oversampling, FFT energy integration). Never invent metrics or report successful device creation when slots are empty."**

---

## Architecture Overview (Phases 1 to 6 + Hito 1 Governance)

```
                       ┌─────────────────────────────────────┐
                       │        LLM Cognitive Client         │
                       │    (Antigravity / Claude Desktop)   │
                       └──────────────────┬──────────────────┘
                                          │ FastMCP (204 Tools)
                                          ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                 Production Intelligence Engine (PIE)                  │
  ├───────────────────┬───────────────────┬────────────────────────────────┤
  │ Fase 1: Foundation│ Fase 2: Music     │ Fase 2.5: Instruments          │
  │ • Shadow Graph    │ • Roman Numerals  │ • Sound Profiles               │
  │ • ACID Transact.  │ • Voice Leading   │ • Drum Rack Pad Populator      │
  │ • State Snapshots │ • Grooves/Motifs  │ • Native Browser Resolution    │
  ├───────────────────┼───────────────────┼────────────────────────────────┤
  │ Fase 3: Arrange   │ Fase 4: Sound     │ Fase 5: Digital Ear / Mix      │
  │ • Energy Curves   │ • Macro Controls  │ • LUFS / True Peak / Masking   │
  │ • Transitions     │ • Chain Templates │ • Frequency Conflict Graph     │
  │ • Drop Differ.    │ • Native Racks    │ • Closed-Loop Corrections      │
  ├───────────────────┼───────────────────┼────────────────────────────────┤
  │ Fase 6: Mastering │ HITO 1: Governance, Causal Memory & Compliance     │
  │ • 5-Device Chain  │ • ProductionGraph (Acyclic Causal DAG, BFS check)  │
  │ • Reference Match │ • DecisionMemory (Contextual, Candidate-Only)      │
  │ • Translation (6x)│ • PolicyEngine (7 Inviolable Acoustic Guardrails)  │
  │ • Versioned WAV   │ • ProductionPlanner (Minimum Intervention Ranking) │
  │ • master_project()│ • ProductionExecutor (SHA-256 Scoped Fingerprints) │
  │                   │ • VerificationMatrix (Delta vs Expected Regression)│
  │                   │ • ITU-R BS.1770-5 (Normative Standard / Profiles)  │
  └───────────────────┴───────────────────┴────────────────────────────────┘
                                     │ TCP Socket (Port 9877)
                                     ▼
                       ┌─────────────────────────────────────┐
                       │     Ableton Live 12 Suite Engine    │
                       │     (MIDI Remote Script: AbletonMCP)│
                       └─────────────────────────────────────┘
```

---

## ITU-R BS.1770-5 Compliance & Delivery Profiles

PIE implements a strict mathematical and conceptual separation between **Measurement**, **Profile**, and **Compliance**:

$$\text{Measurement} \neq \text{Profile} \neq \text{Compliance}$$

1. **Measurement (`LoudnessMeasurement`):** Strictly descriptive of objective acoustics (`integrated_lufs`, `true_peak_dbtp`, `loudness_range_lra`). `LoudnessAnalyzer` only measures and never takes mastering decisions or applies profiles.
2. **Profile (`LoudnessProfile`):** Target specification and guardrails. Immutable contract (`EBU_R128`, `STREAMING`, `CLUB`).
3. **Compliance (`LoudnessComplianceResult`):** Pure, deterministic evaluation of whether a measurement satisfies profile tolerances.

### Key Conceptual Guardrails
- **`-14 LUFS` is NOT a universal streaming law:** It is an internal operational target used by PIE. Platforms dynamically adjust replay volume using diverse metadata targets.
- **`CLUB` profile is NOT a universal industry standard:** It is an internal PIE high-energy acoustic target (-7.5 LUFS) designed for DJ play and sound system punch.
- **`Gain Reduction` is NOT a loudness measurement:** Limiter gain reduction is a processing metric that belongs to mastering devices, never to `LoudnessMeasurement`.
- **`True Peak` is NOT Sample Peak:** Discrete sample peak (`sample_peak_dbfs`) measures sample values; True Peak (`true_peak_dbtp`) utilizes 4x sinc FIR oversampling (Annex 2) to detect inter-sample peaks that breach $0.0\text{ dBTP}$ even when sample peaks are $< 0.0\text{ dBFS}$.

| Category | Type | Profile Name | Target LUFS | Tolerance | Max True Peak | Max Limiter GR | Description |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Normative Standard** | `STANDARD` | `EBU_R128` | -23.0 LUFS | ±0.5 LU | -1.0 dBTP | 2.0 dB | International broadcast standard (ITU-R BS.1770-5 / EBU R 128) |
| **Delivery Guidance** | `RECOMMENDATION`| `STREAMING` | -14.0 LUFS | ±1.0 LU | -1.0 dBTP | 2.5 dB | PIE target for commercial streaming (AES TD1004 guidance) |
| **Delivery Guidance** | `RECOMMENDATION`| `DIGITAL_DOWNLOAD`| -9.0 LUFS | ±1.0 LU | -0.5 dBTP | 2.5 dB | Direct master download target (Bandcamp / Beatport) |
| **Delivery Guidance** | `RECOMMENDATION`| `VIDEO` | -15.0 LUFS | ±1.0 LU | -1.0 dBTP | 2.0 dB | Web video & film sync delivery |
| **Engine Policy** | `PIE_POLICY` | `CLUB` | -7.5 LUFS | ±1.0 LU | -0.3 dBTP | 3.0 dB | PIE high-energy sound system / DJ club target |
| **Engine Policy** | `PIE_POLICY` | `PREMASTER` | -18.0 LUFS | ±2.0 LU | -3.0 dBTP | 0.0 dB | Pre-master delivery for external mastering engineer |

### DSP Implementation Details
- **K-Weighting:** Stage 1 high shelf ($f_0 \approx 1682\text{ Hz}$, $+4\text{ dB}$) + Stage 2 RLB high-pass ($f_0 \approx 38\text{ Hz}$).
- **True Peak (Annex 2):** 4x zero-stuffed upsampling combined with a windowed sinc FIR reconstruction filter detecting inter-sample peaks $> 0\text{ dBTP}$ even when discrete sample peaks are $< 0\text{ dBFS}$.
- **Loudness Range (LRA):** EBU Tech 3342 dual-gating (-70 LKFS absolute, -20 LU relative gating across 3-second short-term windows).

---

## Hito 1 Governance Layer

### 1. ProductionGraph (Causal DAG)
Separates **WHAT EXISTS** (`SessionShadowGraph`) from **WHY IT EXISTS** (`ProductionGraph`):
- **15 Canonical Node Types:** `INTENT`, `OBSERVATION`, `ANALYSIS`, `HYPOTHESIS`, `CANDIDATE`, `DECISION`, `POLICY_CHECK`, `SIMULATION`, `ACTION`, `MEASUREMENT`, `VERIFICATION`, `RESULT`, `ROLLBACK`, `REJECTION`, `NO_OP`.
- **10 Canonical Edge Types:** `DERIVED_FROM`, `CAUSED_BY`, `PARENT_OF`, `ALTERNATIVE_TO`, `VALIDATED_BY`, `REJECTED_BY`, `EXECUTED_BY`, `MEASURED_BY`, `VERIFIED_BY`, `ROLLED_BACK_BY`.
- **Cycle Prevention:** Enforces DAG acyclicity at edge insertion time using reachability search; raises `GraphIntegrityError` if a cycle is attempted.
- **Explainability:** `explain_decision()` categorizes full lineage into `facts`, `measurements`, `inferences`, `decision`, `actions`, `results`, and `rejected_alternatives`.

### 2. DecisionMemory
Contextually indexes verified production decisions (`genre`, `tempo`, `key`, `target`, `domain`):
- **Fundamental Invariant:** All search results return strictly marked as `is_candidate_only = True` and `auto_executable = False`.
- Supports invalidation, superseding, and causal linking between decisions.

### 3. ProductionPolicyEngine
Enforces inviolable guardrails before any mutation occurs:
- `MASTER_LIMIT`: Rejects Limiter Gain Reduction $> 2.5\text{ dB}$ or True Peak $> -0.3\text{ dBTP}$.
- `MASTER_EQ`: Rejects master EQ modifying $> 2$ bands or boosts/cuts $> \pm 1.0\text{ dB}$.
- `MIX_MASTER_BOUNDARY`: Rejects patching diagnosed `MIX_PROBLEM` issues in mastering; redirects to mix domain.
- `LOCKED_OBJECT`: Prevents mutation of user-locked or engine-locked tracks/clips.
- `TRANSACTION_REQUIRED`: Requires active transactional unit of work for state mutations.
- `STALE_PLAN`: Rejects plans whose relevant session fingerprint has drifted.
- `REGRESSION`: Flags post-execution secondary metric regressions and mandates rollback.

### 4. ProductionPlanner & Executor
- **Minimum Intervention:** Multi-candidate generation evaluates alternatives and chooses the least intrusive valid action.
- **Scoped Fingerprinting:** Deterministic SHA-256 session hash scoped strictly to relevant entities (e.g., changes to an unrelated vocal track do not invalidate a master limiter plan).
- **Atomic Verification & Rollback:** Post-execution verification evaluates expected vs actual deltas. If an acoustic regression occurs (True Peak clipping, phase collapse, LRA squashing), transaction is automatically rolled back and recorded as `ROLLBACK` in the causal DAG.

---

## Tool Catalog Summary (174 FastMCP Tools)

| Category | Tool Count | Core Capabilities |
| :--- | :---: | :--- |
| **Governance & Planning (Hito 1)** | **9** | `production_status`, `production_plan`, `production_validate`, `production_execute`, `production_explain`, `production_history`, `production_graph`, `production_rollback`, `production_memory_search` |
| **Foundation (Fase 1)** | 29 | Session graph, inspect, resolve, diff, transactions, WAL commit/rollback, snapshots |
| **Music Engine (Fase 2)** | 12 | Harmony, roman numeral parsing, voice leading, rhythm grids, swing, humanize, motifs |
| **Instrument Engine (Fase 2.5)**| 10 | Instrument inspect, resolve, sound profile mapping, drum rack populate, verify |
| **Arrangement (Fase 3)** | 13 | Energy curves, section structures, transitions, risers, drop differentiation, linter |
| **Sound Design (Fase 4)** | 17 | Tonal sound intent, device chain presets, macro mapping, drum bus, sound profiles |
| **Digital Ear / Mix (Fase 5)** | 21 | Audio capture, ITU-R LUFS, True Peak, masking detector, conflict graph, linter, corrections |
| **Mastering & QC (Fase 6)** | 14 | Master readiness, chain builder, preview, apply, evaluate, rollback, reference match, translation test, QC, export, report |
| **Ableton Native / Legacy** | 49 | Clips, tracks, notes, devices, mixer faders, arrangement timeline, browser navigation |
| **TOTAL** | **174** | **Autonomous, verifiable, causal-governed production operating system** |

---

## Verification & Test Suite

All 331 comprehensive unit, acceptance, integration, forensics, and failure injection tests execute offline with **100% pass rate**:

```bash
python tests/run_all_tests.py
# ============================ 331 passed in 45.57s =============================
```

### Verified Test Categories (See [INDEX.md](file:///d:/Proyectos/TEST/AbletonEngine/documentation/INDEX.md) for full breakdown)
- **Hito 1 — Failure Injection & Chaos (22 tests):** `tests/test_failure_injection.py` (Dropped socket, corrupted persistence, double commits, crash recovery, stale plans).
- **Hito 1 — Integration & Golden Pipeline (21 tests):** `tests/test_production_integration.py` (Full E2E governed workflow with zero internal mocking).
- **Hito 1 — Rollback Engine (23 tests):** `tests/test_production_rollback.py` (Atomic, non-destructive rollbacks, verified restorations).
- **Hito 1 — FastMCP Surface (20 tests):** `tests/test_production_mcp.py` (High-level tool boundary validation).
- **Fase 7 — Audio Forensics Engine (31 tests):** `tests/test_forensics_*.py` (STFT, DC offset, anomalies, clipping, spectral percentiles).
- **Phases 1 to 6 Baseline Suites (80+ tests):** Music theory, sound design, arrangement, mix conflict graph, and transaction management preserved with zero regressions.

---

## Quickstart & Example Workflow

### 1. Formulate a Production Plan
```json
{
  "tool": "production_plan",
  "args": {
    "intent": "Quiero que el master tenga más volumen",
    "target": "Master",
    "target_lufs": -14.0
  }
}
```

### 2. Validate Against Inviolable Policies
```json
{
  "tool": "production_validate",
  "args": {
    "plan_id": "plan_95689104"
  }
}
```

### 3. Execute Transactionally with Acoustic Verification
```json
{
  "tool": "production_execute",
  "args": {
    "plan_id": "plan_95689104"
  }
}
```

### 4. Explain Causal Lineage
```json
{
  "tool": "production_explain",
  "args": {
    "decision_id": "dec_3439b16e"
  }
}
```
Outputs categorized causal provenance:
- **Facts:** Session target and baseline state.
- **Measurements:** Pre-execution ITU-R BS.1770-5 integrated LUFS and True Peak.
- **Inferences:** Headroom analysis and candidate simulations.
- **Decision:** Chosen minimal-intervention limiter adjustment.
- **Actions:** Discrete Ableton device parameter writes staged within the transaction.
- **Results:** Post-execution verification confirming target LUFS reached without True Peak clipping.
- **Rejected Alternatives:** Aggressive EQ boost rejected by `MASTER_EQ`; over-compression rejected by `MASTER_LIMIT`.

---

## Evolución Avanzada PIE v3.5 (Fases A, B y C)

El motor integra una capa integral de normalización de instrumentos de terceros, inyección física de automatización y producción vocal:

```
                      ARQUITECTURA DE INTEGRACIÓN PIE v3.5
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          ▼                             ▼                             ▼
     [FASE A]                       [FASE B]                      [FASE C]
Suite VST3 & Presets         Automatización Gráfica        Vocal Pipeline &
(Vital, Omni, Kontakt,       en Línea de Tiempo LOM         Stem Resampler
 Analog Lab, Thermal...)     (Envolventes Físicas)          (Ducking & Bouncer)
```

### 1. Fase A: Suite VST3 & Parameter Normalizer (`engine/instruments/plugins/`)
- **Plugins Mapeados:** `Vital`, `Spectrasonics Omnisphere`, `Arturia Analog Lab V`, `Native Instruments Kontakt 8`, `Output Thermal`, `Dada Life Sausage Fattener`, `The God Particle`, `Arturia Efx REFRACT/MOTIONS` + nativos de Ableton.
- **Fuzzy Fallback Universal:** Identifica automáticamente parámetros de cualquier plugin de terceros no catalogado mediante tokenización difusa.
- **Auto-Crawler:** `LibraryCrawler` indexa de forma recursiva la librería y plugins de Live en `state/browser_index.json`.

### 2. Fase B: Automatización Física en Arrangement LOM (`AbletonMCP/__init__.py`)
- Inyección directa de curvas matemáticas (`insert_step`) en envolventes de clips y parámetros de pista mediante el comando `create_arrangement_automation_envelope`.
- Soporta barridos de filtro, washouts de reverb con snap reset y crescendos con silencios pre-drop.

### 3. Fase C: Vocal Production Pipeline & Stem Resampler (`engine/vocal/`, `engine/audio/`)
- **Cadena Vocal Óptima:** High-Pass en 100 Hz, Dynamic Notch en 340 Hz (limpieza de resonancias), Glue Compressor 4:1 y saturación cálida (+2 dB drive).
- **Smart Ducking Matrix:** Atenuación matemática continua ($10^{dB/20}$) en instrumentos de medios (Keys, Synths, Leads) ante la presencia de voces, protegiendo bajo y batería.
- **Stem Resampler Autónomo:** Agrupa la sesión en stems (`01_Drums`, `02_Bass`, `05_Vocals`, `03_Keys`, `04_Lead`, `06_FX`, `00_Master`) y genera `exports/stems/manifest.json`.

---

## Verificación de Tests (100% Pass Rate)

```bash
python -m pytest
# ============================ 366 passed in 59.78s =============================
```

---

## 🚀 Fronteras de Producción Inteligente: Horizontes 1 y 2

### 🎛️ Horizonte 1: Deconstructor de Referencias (Audio-to-MIDI & Stem Separation)
Transforma cualquier archivo de audio de referencia comercial en material de producción editable dentro de Ableton Live:
- **Separación de 4 Stems vía DSP Crossover & Mid-Side:** Aísla `drums` (transient dynamics & high-crest factor), `bass` (20-220 Hz sub fundamental centrado en mono), `vocals` (aislamiento mid-channel en formantes 300-3800 Hz) y `other` (residuos armónicos y reverberación estéreo).
- **Detección Acústica de Tempo y Tonalidad:** Autocorrelación de energía de transientes para BPM exacto y correlación cromagrama Krumhansl-Schmuckler para tonalidad mayor/menor.
- **Transcripción de Baterías a MIDI:** Clasificación multi-banda en Kick (MIDI 36), Snare/Clap (MIDI 38) y Closed Hat (MIDI 42) cuantizados a la grilla rítmica.
- **Pitch Tracking F0 de Bajo:** Detección frame-a-frame de fundamentales entre 35 Hz y 260 Hz mediante autocorrelación segmentada en notas continuas con duración y velocidad dinámicas.
- **Transcripción Armónica:** Análisis de cromagramas de 12 semitonos por bloques de compás para acordes.
- **Reconstrucción en Ableton Live:** Herramientas `reference_deconstruct` y `reference_reconstruct_in_live`.

### 🎹 Horizonte 2: Generador Procedural de Patches para Vital (.vital Synthesis)
Generador nativo de sintetizadores que produce directamente archivos `.vital` en formato JSON auto-contenidos, listos para reproducirse en Vital VST3:
- **Recetas Procedurales:**
  - `PIE Heavy Reese Bass`: Osciladores duales con detune unison estéreo (5 y 7 voces), sub oscilador puro directo en mono, filtro analógico 24dB con drive y modulación LFO.
  - `PIE Carnage 808`: Oscilador sub a -24 semitonos con envolvente de pitch ultra-rápida para pegada transient, distorsión Hard Clip y portamento glide.
  - `PIE Warm Rhodes Keys`: Envolvente suave, filtro analógico cálido, LFO de trémolo senoidal, chorus exuberante y delay ping-pong.
  - `PIE Euphoric Lead`: 7 voces supersaw, filtro Ladder 24dB, portamento y reverb con delay estéreo.
- **Asignación de Macros y Modulación:** Todos los patches configuran los 4 macros estándar (ej. CUTOFF, DRIVE, DETUNE, SUB LVL) con enrutamiento automático a los parámetros de síntesis.
- **Despliegue Directo:** Los presets se guardan automáticamente en la librería local de Vital del usuario (`D:\Documentos\Vital\User\Presets\PIE_Presets\`) para que aparezcan de inmediato en el navegador del sintetizador, y se sincronizan en `presets/vital/`.
- **Herramientas FastMCP:** `vital_create_preset` y `vital_list_user_presets`.

---

## 💎 Producción de Élite: Opciones A y B (Anti-Loop & Acoustic Physics)

### 🥁 Opción A.1: Groove Pocket Engine & Humanización de Pistas (`engine/music/groove/pocket.py`)
Reemplaza la cuantización robótica al 100% por micro-tiempos basados en la física y hábitos interpretativos de cada género:
- **Estilos de Pocket Disponibles:** `atlanta_trap` (kicks con timing cerrado, 808s arrastrados, snares laid-back con snap retrasado), `neo_soul_dilla` (kicks empujando hacia adelante, bajo borracho y swing desfasado), `boom_bap`, `dark_rage` y `organic_human`.
- **Jitter Correlacionado con Velocidad:** Notas con velocidades altas (acentos fuertes) se tocan con precisión milimétrica, mientras que notas débiles (ghost notes, rellenos) tienen mayor varianza temporal y dinámica.
- **Chord Strumming Físico:** Dispersa acordes polifónicos con arpegio manual natural ($\Delta t$ escalonado por voz) y curvatura dinámica (*velocity tilt*) para teclados, pianos y guitarras.
- **Herramienta FastMCP:** `humanize_track_clip(track_index, clip_index, pocket_style, strength, apply_strum, role)`.

### 🔄 Opción A.2: Phrase Evolver Anti-Loop (`engine/music/variation/phrase_evolver.py`)
Erradica la fatiga auditiva de bucles estáticos de 4 compases implementando la estructura formal clásica y moderna de evolución temática:
- **Arquetipo $A \to A' \to B \to A''$:**
  - $A$ (Compases 1-4): Establecimiento del tema principal con máxima nitidez.
  - $A'$ (Compases 5-8): Variación sutil, adornos, rolls de hi-hats 1/32 y ghost notes en redoblante.
  - $B$ (Compases 9-12): Contraste rítmico, silencios intencionales de bombo (*kick dropouts*) para respiración y bajo en staccato.
  - $A''$ (Compases 13-16): Clímax de energía, redobles de transición de 4 golpes (*turnaround roll*) y corte de silencio pre-drop.
- **Herramienta FastMCP:** `evolve_arrangement_phrase(track_index, clip_index, phrase_index, role, genre, key, scale)`.

### 📈 Opción B.1: Arrangement Automation Weaver (`engine/arrangement/automation/weaver.py`)
Traduce curvas de energía abstractas en envolventes continuas de parámetros en Ableton Live:
- **Barridos de Filtro Paramétricos:** Curvas exponenciales/logarítmicas de apertura y cierre de filtro calculadas paso a paso.
- **Reverb Washouts Dramáticos:** Subida exponencial del *Dry/Wet* durante el build con restablecimiento instantáneo a cero (*snap reset*) en el downbeat exacto del drop.
- **Sub-Bass Cleanup Pre-Drop:** Atenuación progresiva de graves antes del impacto para maximizar la sorpresa y pegada del drop.
- **Herramienta FastMCP:** `apply_transition_automation_weaver(track_index, transition_type, start_bar, duration_bars, parameter_name)`.

### 🦆 Opción B.2: Auto-Sidechain Kick-to-Bass Ducker (`engine/mix/sidechain.py`)
Resuelve quirúrgicamente el enmascaramiento y colisión de fase en frecuencias sub-graves (20-90 Hz):
- **Modelado Closed-Loop:** Sincroniza la curva de atenuación de volumen del 808/sub-bass con los timestamps exactos de los golpes de bombo (*kick strikes*).
- **Geometría de Respuesta Quirúrgica:** Ataque inmediato (0 ms) para liberar el impacto del transiente del bombo, retención (*hold*) configurable (20-30 ms) y relajación (*exponential release*) que devuelve el 100% del sustain del bajo sin distorsión ni clics.
- **Herramienta FastMCP:** `apply_kick_sidechain_to_bass(kick_track_index, bass_track_index, kick_clip_index, ducking_depth_db, release_ms)`.

---

## 🏆 Producción de Élite: Las 5 Dimensiones Avanzadas (Opciones 1 a 5)

### 🛝 Opción 1: 808 Slide & Pitch-Bend Glide Engine (`engine/music/bass/glide.py`)
Genera articulaciones de bajo y 808s dinámicos para trap, drill y rage:
- **Modos:** `drill_octave_glide` (+12 semitonos con resolución rápida en notas de remate), `pitch_drop` (-12 a -24 semitonos al final de transiciones), `chord_fifth_glide` (+7 semitonos) y `vibrato_tail`.
- **Doble Capa de Articulación:** Puntos de Pitch Bend precisos en rango $[-8192, 8191]$ y notas legato superpuestas ($\Delta t = 0.04$ pulsos) para sintetizadores monofónicos con portamento activo.
- **Herramienta FastMCP:** `generate_808_slides(track_index, clip_index, slide_mode, bend_range_semitones, glide_probability, turnaround_only)`.

### 🍬 Opción 2: "Ear Candy" & Micro-FX Engine (`engine/arrangement/fx/ear_candy.py`)
Inyecta micro-eventos impredecibles en transiciones:
- **Tape-Stop / Vinyl Slowdown:** Desaceleración exponencial de pitch ($0 \to -8192$) y volumen ($0.85 \to 0.0$) en el último tiempo del compás previo al drop.
- **Glitch Stutter:** Subdivisión rítmica geométrica acelerada ($1/8 \to 1/16 \to 1/32 \to 1/64$) con rampa de velocidad dinámica de acento.
- **Pre-Drop Vacuum:** Silencio quirúrgico de 0.5 a 1.0 pulsos en todas las pistas rítmicas para maximizar la sorpresa e impacto del drop.
- **Herramienta FastMCP:** `inject_ear_candy(track_index, candy_type, target_bar, duration_beats, clip_index)`.

### 🌌 Opción 3: 3D Depth & Ducked Reverb/Delay Staging (`engine/mix/spatial/depth.py`)
Crea separación tridimensional y profundidad acústica profesional:
- **Planos de Profundidad Acústica:**
  - *Foreground:* Pre-delay a 0 ms, reverberación ultracorta ($T_{60} \le 0.75\text{ s}$), Dry/Wet 8%, agudos transparentes (16 kHz).
  - *Midground:* Pre-delay a 1/32 sincronizado a BPM, Dry/Wet 22%, corte en 9.5 kHz.
  - *Background:* Pre-delay a 1/16, Dry/Wet 45%, simulación de absorción de aire con filtro paso-bajos en 5.2 kHz y apertura estéreo ultra-ancha (140%).
- **Ducked Reverb Automático ("Breathing Space"):** Atenúa los envíos de reverb a $-8.0\text{ dB}$ durante la presencia de notas y los devuelve suavemente a $0.0\text{ dB}$ en las pausas vocales/leads.
- **Herramienta FastMCP:** `configure_depth_staging(track_index, plane, clip_index, ducked_reverb)`.

### 🎯 Opción 4: Resonance Hunter & Surgical Dynamic EQ (`engine/mix/eq/resonance.py`)
Detector automático de resonancias parásitas mediante descomposición espectral FFT:
- **Detección Quirúrgica:** Identifica frecuencias con prominencia $\ge 5.0\text{ dB}$ por encima del declive natural $1/f$ con factor $Q \ge 6.0$.
- **Prioridad de Bandas:** 2.2 kHz – 4.8 kHz (aspereza metálica), 250 Hz – 500 Hz (sonido hueco/caja) y 80 Hz – 180 Hz (retumbo de graves).
- **Inyección de EQ Eight:** Configura filtros Notch estrechos ($Q = 6.0 \text{ a } 9.0$, $-2.5 \text{ a } -4.5\text{ dB}$) con guardarraíl estricto de máximo 2 muescas por pista.
- **Herramienta FastMCP:** `clean_track_resonances(track_index, audio_file_path, max_notches, sensitivity)`.

### 🔀 Opción 5: Beat-Switch & Modal Reharmonization Engine
Composición armónica avanzada y estructuras multi-movimiento:
- **Modal Reharmonizer (`engine/music/harmony/reharmonizer.py`):**
  - *Dominantes Secundarias ($V^7/X$):* Inyecta acordes dominantes en el pulso 4 antes del acorde destino.
  - *Sustituciones Tritónicas ($\text{Sub}V^7$):* Resolución cromática descendente a medio tono de la tónica.
  - *Acordes de Paso Disminuidos ($vii^{\circ 7}$) y Préstamo Modal.*
  - **Herramienta FastMCP:** `reharmonize_chord_progression(track_index, clip_index, style, tension_level)`.
- **Beat-Switch Orchestrator (`engine/arrangement/structure/beat_switch.py`):**
  - Planifica cambios radicales de tempo y género en compases de quiebre (ej. compás 33: de 138 BPM a 90 BPM), automatizaciones de tempo escalonadas (*instant cut* o *ritardando*) y marcadores de sección en Ableton Live.
  - **Herramienta FastMCP:** `orchestrate_beat_switch(switch_bar, target_bpm, target_genre, transition_mode)`.


