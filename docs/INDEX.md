# Ableton Production Intelligence Engine (PIE) — Índice Maestro y Sitemap

> **Directorio de Referencia y Mapa Arquitectónico Integral del Proyecto**  
> Última actualización: Hito 1 (Pasos 01 a 15) + Fase 7 (Audio Forensics) | 331 Tests (100% Verde) | 174 MCP Tools

---

## 1. Mapa Estructural de Directorios

```
AbletonEngine/
├── docs/                                    # Documentación consolidada del sistema
│   ├── audit/                               # Reportes de auditoría y líneas base (Pasos 01-03)
│   │   ├── HITO_1_AUDIT_REPORT.md           # Auditoría técnica inicial y análisis de dependencias
│   │   ├── HITO_1_BASELINE.md               # Congelación de baseline criptográfica SHA-256
│   │   ├── HITO_1_DSP_CONTRACT.md           # Contrato formal de medición y compliance DSP
│   │   └── baseline_manifest.json           # Manifiesto JSON de hashes y entorno
│   ├── production_rollback.md               # Especificación formal de Rollback Engine (Paso 12)
│   ├── production_mcp.md                    # Superficie FastMCP de gobernanza (Paso 13)
│   ├── production_integration.md            # Arquitectura E2E Golden Pipeline (Paso 14)
│   ├── production_failure_injection.md      # Resiliencia caótica y casos de fallo (Paso 15)
│   ├── USER_GUIDE.md                        # Manual operativo para el usuario y agentes
│   ├── NEXT_STEPS.md                        # Hoja de ruta y especificación de pasos siguientes
│   └── INDEX.md                             # El presente índice maestro
├── documentation/                           # Copia simétrica de especificaciones operativas
├── engine/                                  # Núcleo del motor de producción
│   ├── adapters/                            # Abstracción de conexión con Live (Socket y Mock)
│   │   ├── base.py                          # Interfaz abstracta BaseAbletonAdapter
│   │   ├── ableton_adapter.py               # Adaptador socket TCP real (localhost:9877)
│   │   └── mock_adapter.py                  # Adaptador determinista en memoria para tests
│   ├── session/                             # Estado fenoménico ("Qué existe")
│   │   ├── graph.py                         # SessionShadowGraph y locking de objetos
│   │   ├── diff.py                          # Detección de drift con Ableton Live
│   │   ├── resolver.py                      # Resolución difusa de pistas por rol y tags
│   │   └── synchronizer.py                  # Sincronización bidireccional
│   ├── transactions/                        # Capa transaccional atómica y WAL
│   │   ├── manager.py                       # TransactionManager y concurrencia optimista
│   │   ├── rollback.py                      # Reversión de operaciones con snapshots
│   │   └── validator.py                     # Validador de invariantes pre-commit
│   ├── snapshots/                           # Puntos de restauración de sesión
│   │   ├── manager.py                       # SnapshotManager
│   │   └── serializer.py                    # Serializador de snapshots a disco
│   ├── persistence/                         # Persistencia tradicional de sesión
│   │   └── storage.py                       # StorageManager
│   ├── events/                              # Auditoría de eventos
│   │   └── event_logger.py                  # EventLogger estructurado en JSONL
│   ├── music/                               # Fase 2: Teoría musical, armonía y ritmo
│   │   ├── harmony/                         # Análisis de grados tonales y funciones
│   │   ├── voicing/                         # Conducción de voces (voice leading estricto)
│   │   ├── groove/                          # Plantillas de swing y micro-tiempos
│   │   ├── humanizer/                       # Variación sutil de timing y velocidad
│   │   ├── motifs/                          # Generación y transformación motívica
│   │   └── rhythm/                          # Rejillas y densidad rítmica
│   ├── instruments/                         # Fase 2.5: Instrumentos y racks
│   │   ├── profiles/                        # Perfiles tímbricos canónicos
│   │   ├── rack/                            # Ensamblador de Drum Racks nativos
│   │   └── execution/                       # Carga de presets y kits
│   ├── arrangement/                         # Fase 3: Arreglo y macro-estructura
│   │   ├── models/                          # Secciones canónicas (Intro, Drop, Outro)
│   │   ├── energy/                          # Curvas y gradientes de energía musical
│   │   ├── transitions/                     # FX de transición, sweeps y risers
│   │   ├── drops/                           # Diferenciación y diseño de drops
│   │   └── linter/                          # Linter estructural de arreglos
│   ├── sound/                               # Fase 4: Diseño sonoro y presets
│   │   ├── macros/                          # Mapeo de perillas Macro de racks
│   │   ├── chains/                          # Plantillas de cadenas de efectos
│   │   ├── presets/                         # Scoring y recomendación de presets
│   │   └── profiles/                        # Normalización de perfiles tímbricos
│   ├── mix/                                 # Fase 5: Motor de mezcla y Digital Ear
│   │   ├── loudness_analyzer.py             # DSP normativo ITU-R BS.1770-5 (K-Weighting, Gating)
│   │   ├── loudness_standards.py            # Perfiles de entrega (EBU R 128, STREAMING, CLUB)
│   │   ├── masking_detector.py              # Detección de colisiones kick/bass
│   │   ├── conflict_graph.py                # Grafo de conflictos espectrales
│   │   ├── balance_analyzer.py              # Balance de frecuencias en 8 bandas
│   │   ├── stereo_analyzer.py               # Correlación de fase y campo estéreo
│   │   ├── correction_engine.py             # Correcciones automáticas en mezcla
│   │   └── mix_linter.py                    # Linter de mezcla
│   ├── mastering/                           # Fase 6: Masterización
│   │   ├── mastering_engine.py              # Orquestador del flujo de mastering
│   │   ├── mastering_chain.py               # Cadena canónica de 5 procesadores
│   │   ├── limiter.py                       # Limitador True Peak
│   │   ├── true_peak.py                     # DSP sobremuestreo sinc FIR 4x
│   │   ├── loudness_target.py               # Especificaciones de entrega
│   │   ├── reference_match.py               # Comparación contra pistas de referencia
│   │   ├── translation_test.py              # Simulación en 6 sistemas de escucha
│   │   └── quality_control.py               # Reportes QC de pre-exportación
│   ├── forensics/                           # Fase 7: Audio Forensics Engine
│   │   ├── stft.py                          # Transformada STFT multi-resolución
│   │   ├── temporal.py                      # Análisis temporal (RMS, picos, cresta)
│   │   ├── spectral.py                      # Métricas espectrales (centroide, flux, 14 bandas)
│   │   ├── baseline.py                      # Percentiles dinámicos (p10, p50, p90)
│   │   ├── clipping.py                      # Detección de clipping inter-sample
│   │   ├── anomalies.py                     # DC offset, clicks, pops, dropouts
│   │   ├── masking.py                       # Enmascaramiento stem-a-stem
│   │   ├── correlation.py                   # Correlación cruzada y alineación de fase
│   │   ├── causality.py                     # Separación de observaciones e hipótesis
│   │   ├── report.py                        # Generador de reportes criptográficos
│   │   └── serializer.py                    # Persistencia atómica de reportes
│   └── production/                          # Hito 1: Capa de Gobernanza Causal
│       ├── models.py                        # ProductionNode, ProductionDecision, ProductionPlan
│       ├── graph.py                         # ProductionGraph (DAG causal: Por qué existe)
│       ├── memory.py                        # DecisionMemory (Memoria contextual, Candidate-Only)
│       ├── policies.py                      # ProductionPolicyEngine (Guardrails acústicos)
│       ├── planner.py                       # ProductionPlanner (Mínima intervención)
│       ├── context.py                       # ProductionContext y fingerprints de alcance
│       ├── executor.py                      # ProductionExecutor (Verificación y rollback)
│       ├── verification.py                  # VerificationMatrix (Matriz multi-criterio)
│       ├── serializer.py                    # ProductionStorage (Escritura atómica ACID)
│       ├── exceptions.py                    # Jerarquía tipada de excepciones de gobernanza
│       └── boundary.py                      # ProductionAPIBoundary (Adaptador MCP)
├── state/                                   # Estado persistido en tiempo de ejecución
│   ├── session_graph.json                   # Snapshot fenoménico de la sesión
│   ├── production/                          # Base de datos de gobernanza
│   │   ├── graph.json                       # Grafo causal serializado
│   │   ├── memory.json                      # Memoria de decisiones
│   │   ├── plans/                           # Planes de producción versionados
│   │   └── executions/                      # Registros de ejecución y verificación
│   ├── snapshots/                           # Snapshots de la sesión
│   ├── transactions/                        # Write-Ahead Log transaccional
│   └── events/                              # Auditoría de eventos diarios
├── tests/                                   # Suite oficial de 331 pruebas automatizadas
│   ├── fixtures/                            # Fixtures reutilizables para integración
│   └── run_all_tests.py                     # Runner maestro de pruebas
├── server.py                                # Servidor FastMCP con 174 herramientas
└── README.md                                # Documentación de presentación
```

---

## 2. Índice del Catálogo FastMCP (174 Herramientas)

### 2.1 Gobernanza de Producción (Hito 1 — 9 Herramientas)
1. `production_status`: Retorna estado del motor de gobernanza, total de nodos, decisiones y salud del DAG.
2. `production_plan`: Genera un plan formal de producción bajo el Principio de Mínima Intervención (no muta la sesión).
3. `production_validate`: Valida un plan comprobando frescura del fingerprint (`STALE`), ausencia de bloqueos y políticas activas.
4. `production_execute`: Ejecuta atómicamente un plan con verificación multi-criterio y auto-rollback ante regresiones.
5. `production_explain`: Genera informe causal exhaustivo de una decisión (FACT, MEASUREMENT, INFERENCE, DECISION, ACTION, RESULT).
6. `production_history`: Paginación cronológica inversa de decisiones adoptadas.
7. `production_graph`: Inspección estructural y visualización del subgrafo causal de producción.
8. `production_rollback`: Reversión atómica y no destructiva de una decisión previa.
9. `production_memory_search`: Búsqueda de precedentes en la memoria contextual (invariante: jamás auto-ejecutables).

### 2.2 Núcleo de Sesión y Control de Live (Fase 1 — 78 Herramientas)
- **Inspección de Sesión:** `get_session_info`, `get_track_info`, `get_master_info`, `get_track_names`, `get_return_tracks`, `get_browser_tree`.
- **Pistas y Canales:** `create_midi_track`, `create_audio_track`, `delete_track`, `set_track_name`, `set_track_color`, `set_track_volume`, `set_track_pan`, `set_track_mute`, `set_track_solo`, `set_track_arm`, `set_track_role`.
- **Clips y Notas:** `create_clip`, `delete_clip`, `fire_clip`, `stop_clip`, `get_clip_notes`, `add_notes_to_clip`, `clear_clip_notes`, `set_clip_looping`, `set_clip_length`, `quantize_clip`.
- **Dispositivos y Parámetros:** `get_track_devices`, `get_device_parameters`, `set_device_parameter`, `get_device_parameter_by_name`, `set_device_parameter_by_name`, `bypass_device`.
- **Línea Temporal:** `get_arrangement_clips`, `set_arrangement_locator`, `jump_to_locator`, `start_playback`, `stop_playback`.

### 2.3 Shadow Graph, Locking y Transacciones (Fase 1 — 9 Herramientas)
- `graph_get`: Obtiene el grafo semántico actual en memoria.
- `graph_sync`: Sincroniza el grafo semántico con Live.
- `graph_diff`: Detecta desviaciones entre el ShadowGraph y Ableton Live.
- `lock_object`: Bloquea una pista o clip contra mutaciones automáticas.
- `unlock_object`: Desbloquea una pista o clip.
- `reconcile_state`: Reconcilia divergencias externas de estado.
- `tx_begin`: Abre una unidad de trabajo transaccional con snapshot previo.
- `tx_commit`: Confirma una transacción validando concurrencia optimista.
- `snapshot_create`: Genera un punto de restauración inmutable de la sesión.

### 2.4 Instrumentos y Racks (Fase 2.5 — 5 Herramientas)
- `load_drum_kit`: Carga kits nativos según género y perfil de sonido.
- `rack_build_drum_kit`: Ensambla Drum Racks asignando pads canónicos (Kick C1, Snare D1, Hat F#1, etc.).
- `rack_map_macro`: Mapea parámetros profundos a las perillas Macro del rack.
- `instrument_inspect`: Inspecciona la arquitectura interna de un instrumento cargado.
- `instrument_verify`: Verifica la correcta asignación tímbrica de un instrumento.

### 2.5 Diseño Sonoro y Presets (Fase 3 — 19 Herramientas)
- `sound_design_chain`: Construye cadenas de efectos basadas en intención tímbrica.
- `preset_score`: Califica la adecuación acústica de un preset para un rol específico.
- `macro_modulate`: Configura modulaciones de parámetros macro.
- `sound_linter`: Audita posibles saturaciones, problemas de ganancia o filtros redundantes en cadenas de efectos.
- `sound_preview`: Dry-run acústico de un diseño sonoro antes de aplicarlo.

### 2.6 Teoría Musical, Armonía y Arreglo (Fase 2 y 4 — 24 Herramientas)
- `music_generate_progression`: Genera progresiones de acordes tonales y modales.
- `music_apply_voice_leading`: Conducción estricta de voces minimizando saltos interválicos.
- `music_apply_groove`: Aplica plantillas de swing, micro-tiempos y acentuaciones.
- `music_humanize`: Humaniza interpretación en velocidad y timing.
- `sub_bass_repair`: Limpia y alinea fases en la región de sub-graves.
- `arrangement_generate`: Genera la estructura macro (Intro, Build, Drop, Outro).
- `arrangement_curve`: Diseña la curva de energía a lo largo del tiempo.
- `drop_design`: Aplica contraste espectral y dinámico en los drops.
- `narrative_plan`: Modula la tensión y relajación del arreglo.

### 2.7 Digital Ear y Mezcla (Fase 5 — 16 Herramientas)
- `mix_analyze`: Análisis acústico de pistas y subgrupos.
- `mix_lint`: Diagnóstico de reglas de mezcla y problemas de fase.
- `mix_diagnose`: Identificación de enmascaramiento kick/bass y acumulación de frecuencias.
- `mix_conflict_graph`: Grafo de colisiones espectrales inter-pista.
- `mix_suggest_correction`: Sugerencias de ecualización y compresión lateral.
- `mix_apply_correction`: Aplicación gobernada de correcciones de mezcla.
- `production_audit`: Auditoría completa de niveles, sonoridad y balance tímbrico.

### 2.8 Masterización y Control de Calidad (Fase 6 — 14 Herramientas)
- `master_analyze`: Medición BS.1770-5 del canal master.
- `master_readiness`: Auditoría de preparación de la mezcla para mastering.
- `master_create_chain`: Configuración de la cadena canónica de 5 dispositivos.
- `master_apply`: Aplicación de la cadena de masterización.
- `master_preview`: Vista previa determinista del resultado acústico.
- `master_evaluate`: Evaluación contra perfiles de entrega.
- `master_translation_test`: Simulación acústica en 6 entornos de escucha.
- `master_export`: Exportación versionada con verificación True Peak.
- `master_rollback`: Reversión de la cadena de masterización.

---

## 3. Índice de la Suite de Pruebas (331 Tests)

| Módulo de Pruebas | Dominio de Verificación | Cantidad | Estado |
| :--- | :--- | :---: | :---: |
| [`tests/test_arrangement_engine.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_arrangement_engine.py) | Estructura macro, curvas de energía y diseño de drops | 10 | 100% PASS |
| [`tests/test_bs1770_5_loudness.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_bs1770_5_loudness.py) | Filtrado K, dual-gating y True Peak $4\times$ sinc FIR | 6 | 100% PASS |
| [`tests/test_concurrency.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_concurrency.py) | Bloqueo concurrente y exclusión mutua de grafos | 1 | 100% PASS |
| [`tests/test_decision_memory.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_decision_memory.py) | Memoria contextual e invariante Candidate-Only | 4 | 100% PASS |
| [`tests/test_failure_injection.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_failure_injection.py) | Inyección de fallos, caos, caídas de socket y persistencia | 22 | 100% PASS |
| [`tests/test_forensics_anomalies.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_forensics_anomalies.py) | DC offset, clics, pops, dropouts e inversión de fase | 4 | 100% PASS |
| [`tests/test_forensics_baseline.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_forensics_baseline.py) | Percentiles dinámicos espectrales ($p_{10}$, $p_{50}$, $p_{90}$) | 3 | 100% PASS |
| [`tests/test_forensics_causality.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_forensics_causality.py) | Separación entre observación e hipótesis causal | 3 | 100% PASS |
| [`tests/test_forensics_clipping.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_forensics_clipping.py) | Detección de picos inter-sample y clipping digital | 4 | 100% PASS |
| [`tests/test_forensics_correlation.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_forensics_correlation.py) | Correlación cruzada, alineación y retardo en ms | 3 | 100% PASS |
| [`tests/test_forensics_failure_injection.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_forensics_failure_injection.py) | Intoxicación por NaN/Inf, corrupción JSON y hashes | 6 | 100% PASS |
| [`tests/test_forensics_integration.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_forensics_integration.py) | Integración forense multi-pista y reportes | 4 | 100% PASS |
| [`tests/test_forensics_masking.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_forensics_masking.py) | Enmascaramiento espectral por pares en 14 bandas | 4 | 100% PASS |
| [`tests/test_forensics_models.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_forensics_models.py) | Modelos inmutables forenses y serialización | 5 | 100% PASS |
| [`tests/test_forensics_spectral.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_forensics_spectral.py) | Centroide espectral, flux, dispersión y resonancias | 4 | 100% PASS |
| [`tests/test_forensics_stft.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_forensics_stft.py) | STFT en números reales y reconstrucción de ventanas | 4 | 100% PASS |
| [`tests/test_forensics_temporal.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_forensics_temporal.py) | Potencia RMS, pico de muestra y factor de cresta | 4 | 100% PASS |
| [`tests/test_instrument_engine.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_instrument_engine.py) | Cadenas de instrumentos y asignación de roles tímbricos | 7 | 100% PASS |
| [`tests/test_mastering_engine.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_mastering_engine.py) | Cadena de 5 dispositivos, limitación y preview | 10 | 100% PASS |
| [`tests/test_mix_engine.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_mix_engine.py) | Enmascaramiento, balance tímbrico y fase estéreo | 10 | 100% PASS |
| [`tests/test_music_engine.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_music_engine.py) | Armonía tonal, conducción de voces y humanización | 17 | 100% PASS |
| [`tests/test_production_context.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_production_context.py) | Fingerprints de ámbito y contexto de producción | 2 | 100% PASS |
| [`tests/test_production_executor.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_production_executor.py) | Ejecución gobernada, auto-rollback y commit atómico | 4 | 100% PASS |
| [`tests/test_production_graph.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_production_graph.py) | Acyclicidad, ordenamiento topológico y linaje causal | 8 | 100% PASS |
| [`tests/test_production_integration.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_production_integration.py) | Escenarios de integración y pipeline Golden E2E | 21 | 100% PASS |
| [`tests/test_production_mcp.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_production_mcp.py) | Superficie MCP de gobernanza de producción | 20 | 100% PASS |
| [`tests/test_production_models.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_production_models.py) | Validación tipada de nodos, decisiones y planes | 7 | 100% PASS |
| [`tests/test_production_planner.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_production_planner.py) | Generación de planes, Do Nothing y barrera mix/master | 4 | 100% PASS |
| [`tests/test_production_policy.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_production_policy.py) | Guardrails acústicos inviolables y precedencia | 13 | 100% PASS |
| [`tests/test_production_rollback.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_production_rollback.py) | Rollback de primera clase no destructivo | 23 | 100% PASS |
| [`tests/test_production_storage.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_production_storage.py) | Persistencia atómica ACID (`fsync` + `replace`) | 1 | 100% PASS |
| [`tests/test_production_verification.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_production_verification.py) | Matriz multi-criterio de no regresión acústica | 16 | 100% PASS |
| [`tests/test_reconciliation.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_reconciliation.py) | Detección de drift externo y reconciliación | 3 | 100% PASS |
| [`tests/test_resolver.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_resolver.py) | Resolución de pistas por rol, tags y ambigüedad | 3 | 100% PASS |
| [`tests/test_session_fingerprint.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_session_fingerprint.py) | Determinismo y estabilidad de huellas SHA-256 | 5 | 100% PASS |
| [`tests/test_session_graph.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_session_graph.py) | Protección de objetos bloqueados e identidades | 2 | 100% PASS |
| [`tests/test_snapshots.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_snapshots.py) | Creación, listado y restauración de snapshots | 2 | 100% PASS |
| [`tests/test_sound_engine.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_sound_engine.py) | Drum racks, macros, perfiles tímbricos y scoring | 12 | 100% PASS |
| [`tests/test_transactions.py`](file:///d:/Proyectos/TEST/AbletonEngine/tests/test_transactions.py) | Previews dry-run, commit y rollback transaccional | 3 | 100% PASS |
| **TOTAL** | **Suite Oficial Maestro de PIE** | **331** | **100% PASS** |

---

## 4. Taxonomía de Nodos y Aristas del Grafo Causal (`ProductionGraph`)

### 4.1 Tipos de Nodo (`NodeType`)
1. `INTENT`: Intención musical o técnica de alto nivel recibida del usuario o LLM.
2. `OBSERVATION`: Medición acústica objetiva previa a la intervención.
3. `ANALYSIS`: Diagnóstico de headroom, balance espectral y detección de problemas.
4. `HYPOTHESIS`: Hipótesis causal que justifica por qué una acción logrará el objetivo.
5. `CANDIDATE`: Estrategia de producción candidata en competencia.
6. `POLICY_CHECK`: Evaluación de guardrails inviolables del `ProductionPolicyEngine`.
7. `PLAN`: Plan inmutable, versionado y asociado a la huella digital de sesión.
8. `VALIDATION`: Comprobación previa de frescura (`STALE`) y ausencia de bloqueos.
9. `SIMULATION`: Dry-run acústico predictivo sin efectos secundarios en Live.
10. `TRANSACTION`: Unidad atómica de trabajo con snapshot de seguridad previo.
11. `ACTION`: Operación física en dispositivo o parámetro de Ableton Live.
12. `MEASUREMENT`: Medición acústica posterior a la ejecución.
13. `VERIFICATION`: Evaluación de la `VerificationMatrix` (delta real vs esperado y regresiones).
14. `RESULT`: Resultado final exitoso (`COMMITTED`).
15. `ROLLBACK`: Reversión atómica de la acción; conserva evidencia y causalidad.
16. `REJECTION`: Registro inmutable de un candidato descartado por violación de políticas.
17. `NO_OP`: Decisión formal de no intervenir bajo el Principio de Mínima Intervención.

### 4.2 Tipos de Arista (`EdgeType`)
1. `CAUSED_BY`: Causalidad directa entre un nodo fuente y su efecto.
2. `DERIVED_FROM`: Derivación analítica a partir de una observación o medición.
3. `PARENT_OF`: Relación jerárquica padre-hijo.
4. `ALTERNATIVE_TO`: Relación entre candidatos en competencia para el mismo objetivo.
5. `VALIDATED_BY`: Vinculación entre un plan y su resultado de validación.
6. `REJECTED_BY`: Causalidad que explica por qué un candidato fue rechazado.
7. `EXECUTED_BY`: Vinculación entre una decisión y las acciones físicas ejecutadas.
8. `MEASURED_BY`: Vinculación entre una acción y la medición resultante.
9. `VERIFIED_BY`: Vinculación entre una medición y la evaluación de verificación.
10. `ROLLED_BACK_BY`: Vinculación causal entre un fallo de verificación y su nodo de rollback.

---

## 5. Especificaciones de Entrega Acústica (Loudness & True Peak)

| Perfil | Tipo de Autoridad | Target LUFS | Tolerancia | Techo True Peak | Max Limiter GR | Dinámica (LRA) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`EBU_R128`** | `STANDARD` | $-23.0\text{ LUFS}$ | $\pm 0.5\text{ LU}$ | $-1.00\text{ dBTP}$ | $2.0\text{ dB}$ | $\le 14.0\text{ LU}$ |
| **`STREAMING`** | `RECOMMENDATION` | $-14.0\text{ LUFS}$ | $\pm 1.0\text{ LU}$ | $-1.00\text{ dBTP}$ | $2.5\text{ dB}$ | $\ge 4.0\text{ LU}$ |
| **`CLUB`** | `PIE_POLICY` | $-7.5\text{ LUFS}$ | $\pm 1.0\text{ LU}$ | $-0.30\text{ dBTP}$ | $3.0\text{ dB}$ | $\ge 3.0\text{ LU}$ |
| **`DIGITAL_DOWNLOAD`** | `RECOMMENDATION` | $-9.0\text{ LUFS}$ | $\pm 1.0\text{ LU}$ | $-0.50\text{ dBTP}$ | $2.5\text{ dB}$ | $\ge 4.0\text{ LU}$ |
| **`VIDEO`** | `RECOMMENDATION` | $-15.0\text{ LUFS}$ | $\pm 1.0\text{ LU}$ | $-1.00\text{ dBTP}$ | $2.0\text{ dB}$ | N/A |
| **`PREMASTER`** | `PIE_POLICY` | $-18.0\text{ LUFS}$ | $\pm 2.0\text{ LU}$ | $-3.00\text{ dBTP}$ | $0.0\text{ dB}$ | N/A |
