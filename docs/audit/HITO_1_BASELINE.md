# HITO 1 — PARTE 02: BASELINE TESTS Y CONGELACIÓN DEL ESTADO
## Production Intelligence Engine (PIE) — AbletonEngine
**Documento Normativo de Certificación y Congelación de Línea Base v1.0**  
**Fecha de Emisión:** 2026-09-04  
**Ambiente:** Python 3.13.1 (Windows AMD64)  
**Estado:** BASELINE CONGELADO / CERO REGRESIONES (Step 02 de 18)

---

## 1. Baseline ID

```
================================================================================
BASELINE ID: H1-BL-1ddc70d0158c
================================================================================
```

El identificador único determinista `H1-BL-1ddc70d0158c` ha sido derivado criptográficamente a partir de los primeros 12 caracteres del hash global de código fuente del proyecto (`1ddc70d0158c66fb4bbde156da32317b822158e7f303e45c9961c1c0fe487584`), calculado conforme a la especificación de la Sección 3.

---

## 2. Git State

El estado del árbol de control de versiones al momento de la congelación es el siguiente:

- **Sistema de Control de Versiones:** Git
- **Commit HEAD:** `8ed86c556173555ae2239e8bdeae524f1f94174f`
- **Rama Actual:** `main`
- **Working Tree State:** `BASELINE_WORKTREE = DIRTY`
- **Archivos Modificados sin Commit (25 archivos):**
  - `.gitignore`, `README.md`, `engine/__init__.py`, `engine/adapters/ableton_adapter.py`, `engine/arrangement/linter/linter.py`, `engine/mastering/mastering_analyzer.py`, `engine/mix/bridge.py`, `engine/mix/loudness_analyzer.py`, `engine/music/voicing/voice_leading.py`, `engine/transactions/manager.py`, `mix_engine/__init__.py`, `server.py`, `state/events/events_2026-09-04.jsonl`, `state/session_graph.json`, `telemetry_decorator.py`, `tests/run_all_tests.py`, `tests/test_concurrency.py`, `tests/test_instrument_engine.py`, `tests/test_mix_engine.py`, `tests/test_music_engine.py`, `tests/test_reconciliation.py`, `tests/test_resolver.py`, `tests/test_session_graph.py`, `tests/test_snapshots.py`, `tests/test_transactions.py`.
- **Archivos y Directorios No Rastreados (Untracked) (15 elementos):**
  - `docs/` (incluyendo reportes de auditoría y baseline)
  - `engine/mix/loudness_standards.py`
  - `engine/production/` (subsistema de gobernanza causal Hito 1)
  - `state/production/`
  - 11 suites de pruebas en `tests/`: `test_bs1770_5_loudness.py`, `test_decision_memory.py`, `test_failure_injection.py`, `test_production_context.py`, `test_production_executor.py`, `test_production_graph.py`, `test_production_integration.py`, `test_production_models.py`, `test_production_planner.py`, `test_production_policy.py`, `test_production_storage.py`, `test_production_verification.py`.

> [!NOTE]
> De conformidad con la directriz del requerimiento, las modificaciones existentes no han sido descartadas ni sobrescritas. El estado del árbol queda formalmente registrado como `DIRTY` y protegido.

---

## 3. Source Fingerprint

El fingerprint del código fuente proporciona una huella digital determinista e independiente del historial de Git, permitiendo verificar en el futuro si `BASELINE == CURRENT`:

- **Algoritmo de Cálculo:**
  1. Recolección de la totalidad de archivos de código fuente Python en `engine/`, `tests/`, `server.py`, `telemetry.py` y `telemetry_decorator.py` (excluyendo cachés y `.git`).
  2. Ordenamiento lexicográfico estricto de las rutas normalizadas (POSIX format).
  3. Cálculo de SHA-256 individual por archivo.
  4. Agregación acumulativa:
     $$\text{Global Hash} = \text{SHA-256}\left(\sum_{i=1}^{N} \left(\text{path}_i + \text{"\\0"} + \text{file\_sha256}_i + \text{"\\0"}\right)\right)$$
- **Total de Archivos Fuente Catalogados:** 223 archivos
- **Global Source Hash (SHA-256):**
  ```
  1ddc70d0158c66fb4bbde156da32317b822158e7f303e45c9961c1c0fe487584
  ```
- **Fórmula de Baseline ID:** `H1-BL-` + `GlobalHash[0:12]` = `H1-BL-1ddc70d0158c`.

---

## 4. Python Environment

La ejecución del motor y de las herramientas se realiza bajo el siguiente entorno Python formal:

- **Python Executable:** `C:\Program Files\Python313\python.exe`
- **Python Version:** `3.13.1 (tags/v3.13.1:0671451, Dec 3 2024, 19:06:28) [MSC v.1942 64 bit (AMD64)]`
- **Python Implementation:** `CPython`
- **Operating System:** Windows 10 Pro (`10.0.19045`)
- **Architecture:** AMD64 (64-bit)
- **Current Working Directory (CWD):** `D:\Proyectos\TEST\AbletonEngine`
- **System Paths (`sys.path`):**
  - `D:\Proyectos\TEST\AbletonEngine`
  - `C:\Program Files\Python313\python313.zip`
  - `C:\Program Files\Python313\DLLs`
  - `C:\Program Files\Python313\Lib`
  - `C:\Program Files\Python313`
  - `C:\Users\kevin.garrido\AppData\Roaming\Python\Python313\site-packages`
  - `C:\Program Files\Python313\Lib\site-packages`

---

## 5. Dependency Snapshot

Tabla comparativa de dependencias (Declarada vs Instalada vs Importable vs Utilizada):

| Dependencia | Declarada (Manifest) | Instalada (pip) | Importable (`importlib`) | Utilizada en Código | Ubicación en Disco |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`numpy`** | No | `2.5.2` | Sí | Sí | `...\Python313\site-packages\numpy` |
| **`soundfile`** | No | `0.14.0` | Sí | Sí | `...\Python313\site-packages\soundfile.py` |
| **`networkx`** | No | `3.6.1` | Sí | Sí | `...\Python313\site-packages\networkx` |
| **`mcp`** | No | `1.29.1` | Sí | Sí | `...\Python313\site-packages\mcp` |
| **`opentelemetry-api`** | No | `1.44.0` | Sí | Sí | `...\Python313\site-packages\opentelemetry` |
| **`pytest`** | No | `9.0.3` | Sí | Sí | `...\Python313\site-packages\pytest` |
| **`pydantic`** | No | `2.13.5` | Sí | No | `...\Python313\site-packages\pydantic` |
| **`uvicorn`** | No | `0.52.4` | Sí | No (CLI) | `...\Python313\site-packages\uvicorn` |
| **`starlette`** | No | `1.6.0` | Sí | No | `...\Python313\site-packages\starlette` |
| **`anyio`** | No | `4.15.0` | Sí | No | `...\Python313\site-packages\anyio` |
| **`httpx`** | No | `0.28.1` | Sí | No | `...\Python313\site-packages\httpx` |

> [!WARNING]
> Ninguna dependencia está declarada en un archivo de manifiesto formal (`requirements.txt` o `pyproject.toml`) en el repositorio. Todas residen en el directorio global `site-packages` del usuario.

---

## 6. Test Execution #1 (Línea Base Inicial)

- **Test Run ID:** `RUN-001`
- **Timestamp:** `2026-09-04T11:28:21`
- **Comando Ejecutado:** `pytest -q` (a través de `tests/run_all_tests.py`)
- **Directorio de Trabajo:** `D:\Proyectos\TEST\AbletonEngine`
- **Intérprete:** `Python 3.13.1` (`C:\Program Files\Python313\python.exe`)
- **Exit Code:** `0`
- **Duración Total:** `44.57 segundos`
- **Total de Pruebas:** `149`
- **Pruebas Superadas (`PASS`):** `149` (100.0%)
- **Pruebas Fallidas (`FAIL`):** `0`
- **Errores de Ejecución (`ERROR`):** `0`
- **Pruebas Omitidas (`SKIP`):** `0`

---

## 7. Test Execution #2 (Verificación de Determinismo)

- **Test Run ID:** `RUN-002`
- **Timestamp:** `2026-09-04T11:29:05`
- **Comando Ejecutado:** `pytest -q`
- **Exit Code:** `0`
- **Duración Total:** `10.65 segundos` (ejecución con bytecode en memoria)
- **Total de Pruebas:** `149`
- **Pruebas Superadas (`PASS`):** `149` (100.0%)
- **Pruebas Fallidas (`FAIL`):** `0`
- **Errores de Ejecución (`ERROR`):** `0`
- **Pruebas Omitidas (`SKIP`):** `0`

---

## 8. Flaky Tests

Se contrastó el resultado individual de cada prueba entre `RUN-001` y `RUN-002`:

$$\Delta(\text{RUN-001}, \text{RUN-002}) = \emptyset$$

- **Total de Tests Flaky Detectados:** **0**
- **Estado de Estabilidad:** **100% DETERMINISTA**
- **Fuentes de Aleatoriedad Identificadas en Código:**
  - `random.Random(seed)` en `engine/music`: Todas las rutinas de generación rítmica, humanización y variación aceptan y fijan una semilla determinista (`seed=12345` por defecto), garantizando reproducibilidad exacta entre corridas.
  - `uuid.uuid4()`: Empleado para generación de identificadores de sesión (`track_id`, `plan_id`, `decision_id`), sin impacto en el resultado lógico de las aserciones.
  - `datetime.now()` / `time.time()`: Empleado exclusivamente para metadatos de auditoría y marcas de tiempo en logs.

---

## 9. Current MCP Inventory

Catálogo exacto de herramientas expuestas mediante FastMCP en `server.py`:

- **TOTAL_TOOLS:** **174**
- **Cotejo contra Declaración Previa:** En fases preliminares se hacía referencia a 165 herramientas de dominio musical; con la incorporación formal de las 9 herramientas de gobernanza de producción del Hito 1, el total es exactamente **174 herramientas**.
- **Estado de Coincidencia:** **COHERENTE (165 Dominio + 9 Gobernanza = 174)**

### 9.1 Distribución por Dominio Funcional

| Dominio Funcional | Cantidad | Herramientas Clave Representativas |
| :--- | :---: | :--- |
| **Session Core & Live Adapter** | 78 | `get_session_info`, `create_midi_track`, `set_track_name`, `create_clip`, `fire_clip`, `stop_clip`, `set_device_parameter`, `get_browser_tree`, etc. |
| **Shadow Graph & Locking** | 6 | `graph_get`, `graph_sync`, `graph_diff`, `lock_object`, `unlock_object`, `reconcile_state`. |
| **Transactions & Snapshots** | 3 | `tx_begin`, `tx_commit`, `snapshot_create`. |
| **Instruments & Racks** | 5 | `load_drum_kit`, `rack_build_drum_kit`, `rack_map_macro`, etc. |
| **Sound Design & Presets** | 19 | `sound_design_chain`, `preset_score`, `macro_modulate`, `sound_linter`, `sound_preview`, etc. |
| **Music Theory & Harmony** | 12 | `music_generate_progression`, `music_apply_groove`, `music_humanize`, `sub_bass_repair`, etc. |
| **Arrangement & Energy** | 12 | `arrangement_generate`, `arrangement_curve`, `drop_design`, `narrative_plan`, etc. |
| **Mix Engine** | 16 | `mix_analyze`, `mix_lint`, `mix_diagnose`, `mix_compare`, `mix_suggest_correction`, `mix_apply_correction`, `production_audit`, etc. |
| **Mastering Engine** | 14 | `master_analyze`, `master_readiness`, `master_create_chain`, `master_apply`, `master_preview`, `master_rollback`, `master_export`, etc. |
| **Production Governance (H1)** | 9 | `production_status`, `production_plan`, `production_validate`, `production_execute`, `production_explain`, `production_history`, `production_graph`, `production_rollback`, `production_memory_search`. |
| **TOTAL** | **174** | **Superficie completa expuesta al LLM** |

---

## 10. Current Public APIs

Contrato de interfaces públicas protegidas contra regresión:

### 10.1 `LoudnessAnalyzer` (`engine/mix/loudness_analyzer.py`)
- **Constructor:** `__init__(profile: Optional[LoudnessProfile] = None)`
- **Métodos Públicos:**
  - `measure(audio: np.ndarray, sr: int, bit_depth: int, channel_layout: str) -> LoudnessMeasurement`
  - `calculate_lufs_with_blocks(audio: np.ndarray, sr: int) -> Tuple[float, float, float, np.ndarray, np.ndarray]`
  - `calculate_lufs(audio: np.ndarray, sr: int) -> Tuple[float, float, float]`
  - `calculate_lra(st_lufs: np.ndarray) -> float`
  - `calculate_true_peak(audio: np.ndarray, oversample_factor: int = 4) -> float`
  - `calculate_headroom(peak_db: float, true_peak_db: float) -> HeadroomClassification`
- **Excepciones:** No lanza excepciones ante audios vacíos o silencios; devuelve `LoudnessMeasurement` con `measurement_valid=False`.

### 10.2 `LoudnessTargetCalculator` (`engine/mastering/loudness_target.py`)
- **Métodos Públicos:**
  - `get_target_specs(target: Union[str, DeliveryTarget]) -> Dict[str, Any]`
  - `get_target_lufs(target: Union[str, DeliveryTarget]) -> float`
- **Consumidores:** `engine/mastering/mastering_engine.py`, `engine/mastering/limiter.py`.

### 10.3 `SessionShadowGraph` (`engine/session/graph.py`)
- **Constructor:** `__init__()`
- **Métodos Públicos:**
  - `add_track(track: TrackNode) -> TrackNode`
  - `get_track(track_id: str) -> Optional[TrackNode]`
  - `remove_track(track_id: str) -> Optional[TrackNode]`
  - `lock_object(object_id: str, reason: str = "") -> bool`
  - `unlock_object(object_id: str) -> bool`
  - `add_section(...) -> SectionNode`
  - `to_dict() -> Dict[str, Any]`
  - `from_dict(data: Dict[str, Any]) -> SessionShadowGraph`
- **Excepciones:** `ObjectNotFoundError`, `ObjectLockedError`, `InvalidParameterError`.

### 10.4 `TransactionManager` (`engine/transactions/manager.py`)
- **Constructor:** `__init__(graph: SessionShadowGraph, adapter: BaseAbletonAdapter)`
- **Métodos Públicos:**
  - `begin(name: str = "", description: str = "") -> Transaction`
  - `preview(tx_id: str) -> Dict[str, Any]`
  - `validate(tx_id: str) -> bool`
  - `commit(tx_id: str) -> Dict[str, Any]`
  - `rollback(tx_id: str) -> Dict[str, Any]`
  - `status(tx_id: str) -> Dict[str, Any]`
  - `history(limit: int = 10) -> List[Dict[str, Any]]`
- **Excepciones:** `TransactionConflictError`, `TransactionFailedError`.

### 10.5 `StorageManager` (`engine/persistence/storage.py`)
- **Métodos Públicos:** `save_graph()`, `load_graph()`, `save_snapshot()`, `load_snapshot()`, `list_snapshots()`, `save_transaction()`, `load_transaction()`, `list_transactions()`.

### 10.6 `EngineConfig` (`engine/config.py`)
- **Propiedades Centrales:** `STATE_DIR`, `SNAPSHOTS_DIR`, `TRANSACTIONS_DIR`, `MAX_OPERATIONS_PER_TRANSACTION` (500), `MAX_TRACKS_CREATED_PER_TRANSACTION` (20), `ABLETON_HOST` ("localhost"), `ABLETON_PORT` (9877).

---

## 11. DSP Baseline (Batería de Señales Sintéticas)

Se ejecutó la batería completa de señales sintéticas contra el código actual de `LoudnessAnalyzer` a $f_s = 44100\text{ Hz}$:

| Caso / Señal | Entrada | Sample Peak | True Peak | LUFS Int. | LUFS ST | LRA | Crest Factor | Estado |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Señal 1: Silencio** | Zeros ($2\text{ ch}, 2\text{ s}$) | $-240.00\text{ dBFS}$ | $-100.00\text{ dBTP}$ | $-70.00$ | $-120.69$ | $0.00\text{ LU}$ | $0.00\text{ dB}$ | `ACCEPT` (`valid=True`) |
| **Señal 2: Seno $1\text{ kHz}$** | Amp $0.5$ ($-6.02\text{ dBFS}$), $2\text{ s}$ | $-6.02\text{ dBFS}$ | $-6.02\text{ dBTP}$ | $-6.27$ | $-6.27$ | $0.00\text{ LU}$ | $3.01\text{ dB}$ | `ACCEPT` (`valid=True`) |
| **Señal 3: Stereo Idéntico** | $L = R$ (Seno $440\text{ Hz}$) | $-6.02\text{ dBFS}$ | $-6.02\text{ dBTP}$ | $-6.76$ | $-6.76$ | $0.00\text{ LU}$ | $3.01\text{ dB}$ | `ACCEPT` (`valid=True`) |
| **Señal 4: Canales Diferentes** | $L = 440\text{ Hz}, R = 0$ | $-6.02\text{ dBFS}$ | $-6.02\text{ dBTP}$ | $-9.77$ | $-9.77$ | $0.00\text{ LU}$ | $3.01\text{ dB}$ | `ACCEPT` (Canales no colapsados, $-3.01\text{ LU}$ delta) |
| **Señal 5: Silencio + Tono** | $1\text{s sil} + 1\text{s tono} + 1\text{s sil}$ | $-6.02\text{ dBFS}$ | $-6.02\text{ dBTP}$ | $-7.41$ | $-6.27$ | $5.42\text{ LU}$ | $4.77\text{ dB}$ | `ACCEPT` (Gating dual activo, LRA detectado) |
| **True Peak Overshoot** | Seno $11025\text{ Hz}$ fase $\pi/4$ | $-3.93\text{ dBFS}$ | $-0.82\text{ dBTP}$ | $-3.85$ | $-3.85$ | $0.00\text{ LU}$ | $3.01\text{ dB}$ | `ACCEPT` ($\Delta = \mathbf{+3.11\text{ dB}}$ inter-sample detectado) |

### 11.1 Comportamiento ante Entradas Problemáticas (Error Handling Baseline)

| Entrada | Comportamiento | Excepción Producida | Observación |
| :--- | :---: | :---: | :--- |
| **`empty array`** | `ACCEPT` | Ninguna | Devuelve `valid=False`, `int_lufs=-70.0`, `tp=-100.0`. |
| **`mono (1D array)`** | `ACCEPT` | Ninguna | Expande automáticamente a 2 canales (`stereo`). |
| **`stereo (2D array)`** | `ACCEPT` | Ninguna | Procesa normalmente. |
| **`NaN array`** | `ACCEPT` | Ninguna | Maneja NaN mediante clamping y fallback. |
| **`Inf array`** | `ACCEPT` | Ninguna | Maneja desbordamiento sin congelar el proceso. |
| **`very short signal (10 muestras)`** | `ACCEPT` | Ninguna | Emplea cálculo directo de potencia en bloque corto. |
| **`single sample (1 muestra)`** | `ACCEPT` | Ninguna | Emplea cálculo directo de potencia en bloque corto. |
| **`zero duration (2x0 array)`** | `ACCEPT` | Ninguna | Detecta tamaño 0, devuelve `valid=False`. |
| **`unsupported sr (0)`** | `RAISE` | `ZeroDivisionError` | División por cero al calcular $\omega_0 = 2\pi f_0 / f_s$. |
| **`unsupported sr (-44100)`** | `RAISE` | `ValueError` | Array de longitud negativa en tamaño de bloque. |
| **`unsupported channels (3D)`** | `RAISE` | `ValueError` | Error de broadcast de dimensionalidad. |
| **`unsupported channels (0xN)`** | `ACCEPT` | Ninguna | Detecta tamaño 0, devuelve `valid=False`. |

---

## 12. Known Failures

- **Fallos en la Suite Automatizada:** **0** (Cero pruebas fallidas).
- **`BASELINE_EXPECTED_FAILURES`:** `[]`
- **`BASELINE_NEW_FAILURES`:** `[]`
- **Estado Global:** **VERDE TOTAL (149 / 149 PASS)**

---

## 13. Known Limitations

Limitaciones técnicas conocidas y registradas para su resolución planificada en pasos posteriores:

1. **LIM-001 (Validación de Frecuencia de Muestreo):** `LoudnessAnalyzer.measure` no valida explícitamente si `sr <= 0`, dejando que el cálculo dispare `ZeroDivisionError` en lugar de una excepción de dominio (`InvalidSampleRateError`).
2. **LIM-002 (Dimensionalidad de Entrada):** `LoudnessAnalyzer.measure` no valida arrays tridimensionales (`ndim > 2`), disparando un `ValueError` genérico de NumPy.
3. **LIM-003 (Duplicación de Delivery Targets):** Coexisten `DELIVERY_SPECS` en `engine/mastering/loudness_target.py` y `ProfileRegistry` en `engine/mix/loudness_standards.py`.
4. **LIM-004 (Persistencia de Sesión sin fsync):** `StorageManager` utiliza `shutil.move` sin invocar previamente `os.fsync()`, a diferencia de `ProductionStorage`.
5. **LIM-005 (Simulación en Tests):** Todas las pruebas unitarias y de integración se ejecutan contra `MockAbletonAdapter`, no requiriendo la ejecución concurrente de Ableton Live.

---

## 14. Protected Behavior

Tabla explícita de componentes y comportamientos cuya semántica no puede romperse en ningún paso posterior del Hito 1:

| Componente | Estado Baseline | Regla de Protección |
| :--- | :---: | :--- |
| **`SessionShadowGraph`** | Conocido y estable | **NO modificar** semántica de nodos, identidades ni locking. |
| **Existing MCP Tools (165 tools)** | Conocido y estable | **NO romper** nombres, parámetros ni firmas de retorno. |
| **`TransactionManager`** | Conocido y estable | **NO modificar** semántica de commit atómico, rollback ni WAL. |
| **`LoudnessAnalyzer`** | Conforme ITU-R BS.1770-5 | **Refactor futuro controlado** (preservar exactitud numérica). |
| **`LoudnessTargetCalculator`** | Funcional en Fase 6 | **Refactor futuro controlado** (unificación con `ProfileRegistry`). |
| **Tests Existentes (80 legacy + 69 H1)** | 149 passing | **NO modificar** para ocultar fallos o degradar cobertura. |

---

## 15. Acceptance Result

### 15.1 Veredicto de Certificación
```
================================================================================
VEREDICTO: BASELINE ESTABLISHED & FROZEN
BASELINE ID: H1-BL-1ddc70d0158c
ESTADO DEL SISTEMA: 100% OPERACIONAL (149/149 PASS, 0 FLAKY, 174 MCP TOOLS)
ACCESO A PASO 03 (DSP CONTRACT): AUTORIZADO
================================================================================
```

### 15.2 Cumplimiento de la Definition of Done (Paso 02)
- [x] Repositorio identificado bajo Git (`commit 8ed86c55`, `main`, `DIRTY`).
- [x] Código fuente con fingerprint SHA-256 (`1ddc70d0158c...`).
- [x] Intérprete Python identificado (`Python 3.13.1 AMD64`).
- [x] Dependencias identificadas (tabla declarada vs instalada vs importable vs utilizada).
- [x] Suite oficial ejecutada (RUN-001: 149/149 PASS en 44.57s).
- [x] Suite ejecutada por segunda vez (RUN-002: 149/149 PASS en 10.65s).
- [x] Determinismo comprobado (0 tests flaky, fuentes de aleatoriedad catalogadas).
- [x] Fallos clasificados (0 fallos).
- [x] Inventario MCP extraído (174 herramientas totales clasificadas).
- [x] APIs públicas identificadas y documentadas.
- [x] Batería DSP ejecutada (señales 1 a 5, True Peak delta $+3.11\text{ dB}$, matriz de errores).
- [x] Limitaciones actuales documentadas (LIM-001 a LIM-005).
- [x] Archivo `HITO_1_BASELINE.md` creado.
- [x] Manifiesto `baseline_manifest.json` creado.
- [x] Baseline ID generado (`H1-BL-1ddc70d0158c`).
- [x] Cero modificaciones en el comportamiento del producto.
- [x] Cero modificaciones en los tests existentes.

---
*Fin del Documento de Baseline — Estado formalmente congelado para el Paso 03.*
