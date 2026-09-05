# Ableton Production Intelligence Engine (PIE)

> **Autonomous AI-Assisted Music Production, Mixing, and Mastering Middleware for Ableton Live 12 Suite.**
> Powered by Model Context Protocol (FastMCP) with 183 specialized tools and 366 automated unit/acceptance/chaos tests (100% pass rate).

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
                                          │ FastMCP (174 Tools)
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
