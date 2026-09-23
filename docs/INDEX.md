# Ableton Production Intelligence Engine (PIE) — Índice Maestro y Sitemap

> **Directorio de Referencia y Mapa Arquitectónico Integral del Proyecto**  
> Última actualización: Fases 1 a 16 + Studio Doctor & Forensic Delivery Package | 956 Tests (100% Verde) | 301 MCP Tools

---

## 1. Mapa Estructural de Directorios

```
AbletonEngine/
├── docs/                                    # Documentación técnica y operativa consolidada
│   ├── INDEX.md                             # El presente índice maestro y sitemap integral
│   ├── VITAL_SOUND_SYNTHESIS_ENGINE.md      # Motor Autónomo de Síntesis y Diseño Sonoro de Vital (Wavetables, Modular, 7 Leyes KSHMR, Seguridad Permisiva)
│   ├── INTENTIONAL_PERFORMANCE_AND_HUMANIZATION.md # Nivel T: Intentional Musical Performance & Humanization (Core, Groove, Breathing, Identity, Closed-Loop)
│   ├── CLOSED_LOOP_CREATIVE_EVOLUTION.md    # Nivel S: Orquestador de retroalimentación activa (Comp ↔ Sound ↔ Arrg ↔ Mix), Planner, Budget y Rollback
│   ├── CONTEXTUAL_SONIC_CRITIC.md           # Nivel R: Contextual Sonic Critic, evaluación in-situ (10D) y flexibilización de distancia
│   ├── AUDIO_GENESIS_AND_PROVENANCE.md      # Audio Genesis Engine, proveniencia, Render-Before-Sample y destinos
│   ├── ARTISTIC_CRITIC_AND_INTENT.md        # Dirección artística generativa, tribunal de 7 críticos y selection loop
│   ├── GENERATIVE_COMPOSITION_AND_TASTE_ENGINE.md # Composición generativa, 4 memorias y taste engine
│   ├── USER_GUIDE.md                        # Manual de usuario: Flujos guiados, Doctor y producción
│   ├── COPILOT_GUIDED_SESSION.md            # Manual maestro de 10 fases de copilot_guided_session y doctor
│   ├── ABLETON_BROWSER_CATALOG.md           # Catálogo del navegador Live 12 y plugins VST3
│   ├── API_CAPABILITIES_MATRIX.md           # Matriz exhaustiva de capacidades FastMCP
│   ├── ENGINE_GOVERNANCE.md                 # Arquitectura del DAG causal y políticas
│   ├── NEXT_STEPS.md                        # Hoja de ruta y evolución continua
│   ├── PROMPTING_PLAYBOOK.md                # Recetas y prompts canónicos para LLMs
│   ├── production_failure_injection.md      # Resiliencia caótica y tolerancia a fallos
│   ├── production_integration.md            # Arquitectura E2E Golden Pipeline
│   ├── production_mcp.md                    # Superficie FastMCP y contratos de gobernanza
│   ├── production_rollback.md               # Especificación del motor de rollback transaccional
│   └── audit/                               # Reportes de auditoría y líneas base
│       ├── HITO_1_AUDIT_REPORT.md           # Auditoría técnica inicial
│       ├── HITO_1_BASELINE.md               # Baseline criptográfico SHA-256
│       ├── HITO_1_DSP_CONTRACT.md           # Contrato formal DSP ITU-R BS.1770-5
│       └── baseline_manifest.json           # Manifiesto JSON de hashes y entorno
├── engine/                                  # Núcleo algorítmico y de procesamiento
│   ├── adapters/                            # Abstracción de conexión con Live
│   │   ├── base.py                          # Interfaz abstracta BaseAbletonAdapter
│   │   ├── ableton_adapter.py               # Adaptador socket TCP real (localhost:9877)
│   │   └── mock_adapter.py                  # Adaptador determinista en memoria para tests
│   ├── copilot/                             # Orquestación guiada y copiloto ejecutivo
│   │   ├── guided_session.py                # Pipeline interactivo de 10 fases (copilot_guided_session)
│   │   ├── copilot_stepper.py               # Máquina de estados para decisiones guiadas
│   │   └── auto_producer.py                 # Pipeline autónomo sin intervención
│   ├── production/                          # Capa de Gobernanza Causal y Auditoría
│   │   ├── doctor/                          # EL DOCTOR DE SESIÓN (Diagnóstico y cirugía clínica)
│   │   │   ├── session_doctor.py            # Motor clínico multi-dominio y auto-reparación
│   │   │   └── __init__.py
│   │   ├── models.py                        # ProductionNode, ProductionDecision, ProductionPlan
│   │   ├── graph.py                         # ProductionGraph (DAG causal acíclico)
│   │   ├── memory.py                        # DecisionMemory (Candidate-Only, contextual)
│   │   ├── policies.py                      # ProductionPolicyEngine (Guardrails acústicos)
│   │   ├── planner.py                       # ProductionPlanner (Mínima intervención)
│   │   ├── context.py                       # ProductionContext y fingerprints SHA-256
│   │   ├── executor.py                      # ProductionExecutor (Verificación y rollback)
│   │   ├── verification.py                  # VerificationMatrix (No regresión acústica)
│   │   ├── serializer.py                    # ProductionStorage (Escritura atómica ACID)
│   │   └── boundary.py                      # ProductionAPIBoundary (Adaptador MCP)
│   ├── session/                             # Estado fenoménico ("Qué existe")
│   │   ├── graph.py                         # SessionShadowGraph y locking de objetos
│   │   ├── diff.py                          # Detección de drift con Live
│   │   ├── resolver.py                      # Resolución difusa por rol y tags
│   │   └── synchronizer.py                  # Sincronización bidireccional
│   ├── transactions/                        # Capa transaccional atómica y WAL
│   │   ├── manager.py                       # TransactionManager y concurrencia optimista
│   │   ├── rollback.py                      # Reversión de operaciones con snapshots
│   │   └── validator.py                     # Validador de invariantes pre-commit
│   ├── snapshots/                           # Puntos de restauración de sesión
│   │   ├── manager.py                       # SnapshotManager
│   │   └── serializer.py                    # Serializador de snapshots a disco
│   ├── music/                               # Teoría musical, armonía y ritmo
│   │   ├── harmony/                         # Progresiones tonales, modales y dominantes secundarias
│   │   ├── voicing/                         # Voice leading estricto y conducción de voces
│   │   ├── groove/                          # Plantillas de swing, MPC micro-timing y pocket
│   │   ├── humanizer/                       # Variación sutil de timing y velocidad
│   │   ├── motifs/                          # Generación y transformación motívica
│   │   └── rhythm/                          # Rejillas y densidad rítmica
│   ├── instruments/                         # Instrumentos, racks y síntesis
│   │   ├── browser_catalog.py               # Catálogo inteligente de VST3 y dispositivos
│   │   ├── profiles/                        # Perfiles tímbricos canónicos (13 roles acústicos)
│   │   ├── rack/                            # Ensamblador de Drum Racks nativos
│   │   ├── vst_normalizer.py                # Mapeo semántico de parámetros VST (Vital, Serum, etc.)
│   │   └── execution/                       # Carga de presets y kits
│   ├── arrangement/                         # Arreglo macro y micro-estructural
│   │   ├── top_tail_guard.py                # Top & Tail Acoustic Guards (0.0s Gate & 63-64 Fadeout)
│   │   ├── models/                          # Secciones canónicas (Intro, Verse, Chorus, Drop, Outro)
│   │   ├── energy/                          # Curvas y gradientes de energía musical
│   │   ├── transitions/                     # FX de transición, sweeps, risers y vacuums
│   │   └── linter/                          # Linter estructural de arreglos
│   ├── sound/                               # Diseño sonoro y presets
│   │   ├── macros/                          # Mapeo de perillas Macro de racks
│   │   ├── chains/                          # Cadenas de inserción y channel strips
│   │   └── presets/                         # Scoring y recomendación de presets
│   ├── sound_design/                        # MOTOR AUTÓNOMO DE SÍNTESIS VITAL (.vital)
│   │   ├── vital_sound_engine.py            # Orquestador maestro (create_preset, design_granular, audit)
│   │   ├── vital_modular_designer.py        # Diseñador modular (síntesis de ondas, Diode/Comb/Dirty, LFO S&H, FX)
│   │   ├── vital_design_validator.py        # Validador y auditor de especificaciones granulares
│   │   ├── vital_sound_sculptor.py          # Escultor semántico macro (7 Principios de KSHMR)
│   │   ├── vital_wavetable_synth.py         # Sintetizador matemático Base64 (2048 float32) y Sampler PCM
│   │   ├── vital_archetype_catalog.py       # Catálogo indexador de 61 presets en 10 categorías
│   │   └── vital_parameter_schema.py        # Esquema de 772 parámetros, límites e invariantes anti-silencio
│   ├── mix/                                 # Motor de mezcla y Digital Ear
│   │   ├── loudness_analyzer.py             # DSP normativo ITU-R BS.1770-5
│   │   ├── loudness_standards.py            # Perfiles de entrega (EBU R 128, STREAMING, CLUB)
│   │   ├── masking_detector.py              # Detección de colisiones kick/bass
│   │   ├── resonance_detector.py            # Detección y corrección de resonancias acústicas
│   │   ├── balance_analyzer.py              # Balance de frecuencias en 8 bandas
│   │   ├── stereo_analyzer.py               # Correlación de fase y campo estéreo
│   │   └── correction_engine.py             # Correcciones automáticas de mezcla
│   ├── mastering/                           # Masterización y ganancia comercial
│   │   ├── gain_staging.py                  # Escalado de ganancia (+3.0 dB nominal / norm 0.635)
│   │   ├── mastering_engine.py              # Orquestador del flujo de mastering
│   │   ├── mastering_chain.py               # Cadena canónica de 5 procesadores
│   │   ├── limiter.py                       # Limitador True Peak
│   │   └── true_peak.py                     # Sobremuestreo sinc FIR 4x
│   ├── audio/                               # Render y Stems de entrega
│   │   ├── stem_bouncer.py                  # Renderizado de 5 grupos de stems + Master en Broadcast WAV
│   │   ├── stem_audit.py                    # Auditoría espectral y correlación cruzada (rho >= 0.35)
│   │   └── listener.py                      # Captura y análisis de audio en vivo
│   ├── composition/                         # Identidad Compositiva y Restricciones Negativas (Fase P)
│   │   └── compositional_dna.py             # CompositionalDNA, PrimaryMotif, NegativeConstraint
│   ├── creative/                            # Dirección Creativa y Taste Engine (Fase P+)
│   │   └── generative_taste_engine.py       # Filtro en 10 dimensiones, candidatos A/B/C, audición A/B
│   ├── memory/                              # Las 4 Memorias y Aprendizaje
│   │   ├── catalog_memory.py                # Memoria de catálogo cross-song y detector de clichés (Fase O)
│   │   ├── production_learning.py           # Bucle de aprendizaje: Audio ➔ Analysis ➔ Learning
│   │   └── production_memory_hub.py         # Hub unificado de las 4 memorias de producción
│   └── forensics/                           # Audio Forensics Engine
│       ├── stft.py                          # Transformada STFT multi-resolución
│       ├── temporal.py                      # Análisis temporal (RMS, picos, cresta)
│       ├── spectral.py                      # Métricas espectrales (centroide, flux, 14 bandas)
│       ├── clipping.py                      # Detección de clipping inter-sample
│       └── report.py                        # Generador de reportes forenses criptográficos
├── exports/                                 # Exportaciones comerciales
│   └── stems/                               # Stems WAV 24-bit / 44.1 kHz con stems_manifest.json
├── state/                                   # Estado persistido en tiempo de ejecución
│   ├── catalog/                             # Registro histórico y diversidad de catálogo
│   │   └── catalog_index.json               # Huellas acústicas e instrumentales de canciones previas
│   ├── learned/                             # Sabiduría duradera aprendida de intervenciones
│   │   ├── production_wisdom.json           # Reglas empíricas indexadas tras análisis acústico
│   │   ├── user_patterns.json               # Patrones favoritos aprendidos
│   │   └── user_preferences.json            # Preferencias acústicas del productor
│   ├── production/
│   │   ├── doctor_session.json              # Estado clínico aislado del Session Doctor
│   │   ├── guided_session.json              # Estado de las 10 fases de producción guiada
│   │   ├── graph.json                       # Grafo causal serializado
│   │   ├── memory.json                      # Memoria de decisiones
│   │   └── snapshots/                       # Snapshots físicos pre-cirugía
│   └── session_graph.json                   # Snapshot fenoménico de la sesión
├── tests/                                   # Suite oficial de 108 pruebas core (100% PASS)
├── server.py                                # Servidor FastMCP (301 herramientas registradas)
└── README.md                                # Presentación y visión general

```

---

## 2. El Doctor de Sesión (`copilot_session_doctor`) — Auditoría Clínica y Cirugía Acústica

El **Doctor de Sesión** ([`session_doctor.py`](file:///F:/Dev/AbletonEngine/engine/production/doctor/session_doctor.py)) es la herramienta clínica de PIE diseñada para auditar, diagnosticar y reparar quirurgicamente proyectos de Ableton Live existentes (tanto mezclas propias como sesiones externas que requieran saneamiento).

### 2.1 Filosofía de Seguridad y Aislamiento de Estado
- **Estado Clínico Aislado:** Opera sobre su propio archivo `state/production/doctor_session.json`. No interfiere con `guided_session.json` ni reinicia proyectos en curso.
- **Política Estrictamente No Destructiva:** JAMÁS ejecuta limpiezas destructivas (`preflight_clean_session`), NO borra pistas con clips o dispositivos del usuario, y NO añade notas musicales arbitrarias.
- **Snapshots Físicos y Rollback Atómico:** Antes de realizar cualquier intervención física, captura un snapshot completo de la sesión. Si el resultado no es el deseado, el comando `"Deshacer"` o `"Rollback"` restaura inmediatamente el estado previo.

### 2.2 Los 8 Dominios Clínicos de Auditoría y Cirugía
1. **Faders de Pistas & Headroom:** Detecta faders ajustados a volumen peligroso (> 0.85 / 0 dBFS digital). Aplica re-trimming proporcional conservando el balance relativo hacia niveles nominales controlados (-14 a -12 dBFS).
2. **Clips Vacíos & Zombies:** Localiza clips con longitud cero o con cero notas MIDI que consumen recursos de procesamiento o generan desorden visual.
3. **Pistas Huérfanas / Muertas:** Detecta canales sin clips, sin ruteo y sin dispositivos para sugerir su limpieza u optimización.
4. **Pistas Silenciadas con Contenido Activo:** Alerta sobre pistas que tienen clips con audio o notas pero se encuentran en estado Mute persistente.
5. **Duplicación / Apilamiento Redundante de Efectos:** Detecta procesadores idénticos consecutivos (ej. doble EQ Eight o doble limitador) que causan corrimiento de fase o sobrecarga.
6. **Campo Estéreo & Compatibilidad Mono:** Audita correlación de fase, garantizando que el sub-grave (< 120 Hz) sea mono estricto y advierte sobre aglomeraciones en el centro acústico.
7. **Colisión Psicoacústica Low-End (Kick vs 808/Bass):** Examina la interacción espectral en la ventana 40-90 Hz y comprueba la presencia de compresión lateral (sidechain) o ecualización dinámica.
8. **Headroom en Master Bus & True Peak:** Mide picos inter-sample y margen dinámico en el canal principal para prevenir saturación inter-sample antes del master final.

### 2.3 Comandos Operativos del Doctor
- `"Diagnóstico Completo"`: Escaneo pasivo de la sesión en los 8 dominios. Genera un reporte detallado con clasificaciones `CRITICAL`, `WARNING` e `INFO` sin alterar la sesión.
- `"Reparación Quirúrgica No Destructiva"`: Toma un snapshot previo y ejecuta las correcciones clínicas necesarias en faders, clips, cadenas duplicadas y ecualización.
- `"Deshacer"` / `"Rollback"`: Revierte instantáneamente la sesión al snapshot capturado antes de la cirugía.

---

## 3. Pipeline de Producción Guiada (`copilot_guided_session` — 10 Fases)

El orquestador guiado ([`guided_session.py`](file:///F:/Dev/AbletonEngine/engine/copilot/guided_session.py)) dirige la creación, arreglo, mezcla y masterización completa de una producción comercial desde cero (0 a 100) en 10 fases ordenadas:

| Fase | Dominio | Acción Principal | Guardrail Acústico Inviolable |
| :---: | :--- | :--- | :--- |
| **1** | Inicialización & ADN | Definición de estilo, BPM, tonalidad y modo vocal | Detección de toma continua o soporte de micro en vivo (`Live Mic Mode`) |
| **2** | Armonía & Progresión | Progresión modal/tonal y voice leading estricto | Conducción sin saltos interválicos superiores a 5ta justa |
| **3** | Scaffolding de Pistas | Creación de canales según los **13 Roles Acústicos** | **Cero plantillas fijas**: Asignación tímbrica adaptada al género |
| **4** | Composición Musical | Patrones rítmicos, bajo/808, acordes y contramelodías | Humanización orgánica con micro-timing y variaciones de velocity (15-25%) |
| **5** | Síntesis & Sound Design | Carga de VSTs, channel strips y macro controles | **Esculpido Obligatorio de Síntesis ($\\Delta \\ge 1$)**: Prohibido preset default |
| **6** | Arreglo Macro | Estructura de 64 compases con secciones y Cue Points | Mínimo 5 secciones canónicas con contraste tímbrico |
| **7** | Transiciones & Risers | Diseños de tensión, sweeps, caídas y automatizaciones | Mínimo 16 curvas de automatización dinámicas activas |
| **8** | Mezcla & Sidechain Físico | Gain staging, ruteo Kick->808 y Malla Anti-Barro | **Notch Quirúrgico a 441.4 Hz** ($Q=12.0$, -3.5 dB) en armónicos y Master |
| **9** | Top & Tail & Gate Pre-Master | Limpieza temporal y compuerta acústica | **Top & Tail Guards** (0.0s < -70 dBFS; compás 63-64 fade a $-\\infty$) |
| **10**| Masterización & Stems | Cadena de 5 etapas y exportación de 6 stems | **Master Gain Boost** (+3.0 dB / norm 0.635) + Stems WAV 24-bit/44.1 kHz |\n
### 3.1 Los 13 Roles Acústicos y Variabilidad Tímbrica
PIE descarta el uso de plantillas estáticas. El motor compone y mezcla dinámicamente seleccionando entre 13 roles acústicos:
1. `kick`: Bombo procesado con curva de pegada y transiente controlado.
2. `drums`: Caja, hi-hats, percusiones foley orgánicas y shakers.
3. `bass` / `808`: Línea de bajo sintetizado, bajo eléctrico o 808 con glide.
4. `keys`: Teclas eléctricas (Rhodes, Wurlitzer, Neo-Soul EP) o piano acústico.
5. `brass`: Sección de metales, flugelhorn, saxofón o sintetizador brass.
6. `pad`: Colchón armónico atmosférico y envolvente textural.
7. `lead`: Topline melódica solista y fraseos sintéticos.
8. `arp`: Arpegios rítmicos y secuenciación melódica de fondo.
9. `guitars`: Guitarras eléctricas limpias, acústicas o crunch con rasgueo.
10. `organ`: Órgano Hammond B3 o emulaciones de barras armónicas.
11. `pluck`: Cuerdas punteadas o sintetizador percusivo.
12. `vocal_chops`: Micro-cortes vocales procesados con pitch-shift, delay y paneo.
13. `fx`: Texturas de foley orgánico, barridos, risers e impactos.
*(Al completar la Fase 10, el comando `"Cambiar instrumento"` permite hot-swapping inmediato de cualquier pista).*\n
---

## 4. Catálogo FastMCP de Herramientas (301 Registros en `server.py`)

La superficie de control FastMCP se estructura en 11 dominios funcionales:

### 4.1 Copilot Ejecutivo & Doctor Clínico (7 Herramientas)
- `copilot_session_doctor`: Auditoría de 8 dominios, cirugía no destructiva y rollback de sesión.
- `copilot_guided_session`: Orquestador interactivo de las 10 fases de producción de 0 a 100.
- `copilot_auto_produce`: Modo autónomo de producción musical sin intervención humana continua.
- `copilot_preflight_check`: Verificación de salud de socket TCP, Live 12 y scripts de control.
- `copilot_get_status`: Consulta el estado y fase activa del motor guiado.
- `copilot_review_decisions`: Inspección de decisiones técnicas y musicales adoptadas.
- `copilot_execute_decision`: Ejecución manual de decisiones pendientes en el pipeline.\n
### 4.2 Gobernanza Causal y Grafo (`ProductionGraph`) (9 Herramientas)
- `production_status`: Estado global del DAG causal y total de decisiones registradas.
- `production_plan`: Formulación de planes formales bajo Mínima Intervención.
- `production_validate`: Validación de frescura del fingerprint SHA-256 de sesión.
- `production_execute`: Ejecución atómica con verificación multi-criterio y auto-rollback.
- `production_explain`: Generación de informe causal detallado (FACT, OBSERVATION, HYPOTHESIS, DECISION, ACTION, RESULT).
- `production_history`: Historial cronológico paginado de decisiones.
- `production_graph`: Inspección y exportación del subgrafo causal.
- `production_rollback`: Reversión atómica y no destructiva de decisiones.
- `production_memory_search`: Búsqueda de precedentes en la memoria contextual (*Candidate-Only*).\n
### 4.3 Núcleo de Sesión, Pistas y Clips
- `get_session_info`, `get_track_info`, `create_midi_track`, `create_audio_track`, `set_track_name`, `set_track_volume`, `set_track_panning`, `set_track_mute`, `set_track_solo`, `set_track_send`, `create_clip`, `create_audio_clip`, `add_notes_to_clip`, `add_expressive_notes_to_clip`, `get_clip_notes`, `delete_clip`, `fire_clip`, `stop_clip`, `start_playback`, `stop_playback`, `set_tempo`, `switch_to_arrangement_view`, `set_arrangement_time`, `get_arrangement_clips`, `duplicate_to_arrangement`.\n
### 4.4 Instrumentos, Navegador y Esculpido VST
- `get_browser_tree`, `get_browser_items_at_path`, `browser_crawl_library`, `browser_search_library`, `load_instrument_or_effect`, `load_drum_kit`, `preset_list_available`, `instrument_load_preset`, `preset_search`, `preset_select_for_track`, `plugin_inspect_parameters`, `plugin_set_semantic_parameter`, `vital_create_preset`, `vital_list_user_presets`, `drum_rack_inspect`, `drum_rack_populate`, `drum_rack_rebuild`, `drum_rack_verify`, `drum_rack_create`, `drum_rack_add_pad`, `drum_rack_load_sample`, `drum_rack_set_pad`, `get_drum_rack_pads`, `get_drum_pad_devices`, `set_drum_pad_parameter`, `set_drum_pad_mute_solo`, `drum_rack_audit_clip_octaves`, `drum_rack_transpose_clip_octaves`, `drum_rack_load_authentic_library`, `sound_load_role_instrument`, `apply_sound_blueprint`, `instrument_scan_host_vsts`.\n
### 4.5 Teoría Musical, Armonía y Ritmo
- `music_generate_part`, `music_generate_harmony`, `music_generate_bass`, `music_generate_drums`, `music_generate_melody`, `music_create_motif`, `music_transform_motif`, `music_apply_groove`, `music_humanize`, `music_compare_parts`, `music_validate`, `music_compile`, `music_compose_full_harmony`, `music_compose_808_bassline`, `music_compose_topline_melody`, `music_compose_vocal_hook`, `reharmonize_chord_progression`, `generate_808_slides`, `generate_counter_melody_and_arp`, `genre_generate_drum_pattern`, `save_favorite_pattern`, `get_favorite_patterns`, `harmony_apply_chord_strum`, `expression_apply_mpe_vibrato`, `drums_inject_ghost_notes`, `groove_apply_hardware_pocket`.\n
### 4.6 Arreglo, Transiciones y Cue Points
- `arrangement_generate`, `arrangement_preview`, `arrangement_validate`, `arrangement_lint`, `arrangement_apply`, `arrangement_regenerate_section`, `arrangement_regenerate_role`, `arrangement_compare_sections`, `arrangement_lock`, `arrangement_unlock`, `arrangement_get_energy_curve`, `arrangement_get_structure`, `arrangement_apply_transition`, `arrangement_add_energy_curve`, `arrangement_inject_automation_envelope`, `record_arrangement_automation`, `record_multi_automation_pass`, `apply_physical_arrangement_automations`, `create_cue_point`, `get_cue_points`, `delete_cue_point`, `jump_to_cue_point`, `generate_transition_risers`, `transitions_inject_section_impacts`, `transitions_build_tension_risers`, `transitions_apply_pre_drop_vacuum`, `transitions_inject_ear_candy_fx`, `evolve_arrangement_phrase`, `apply_transition_automation_weaver`, `orchestrate_beat_switch`.\n
### 4.7 Mezcla, Digital Ear, Sidechain y Anti-Resonancias
- `mix_analyze`, `mix_lint`, `mix_diagnose`, `mix_compare`, `mix_get_report`, `mix_get_conflicts`, `mix_get_frequency_map`, `mix_check_mono`, `mix_check_headroom`, `mix_reference_compare`, `mix_suggest_correction`, `mix_apply_correction`, `mix_preview_correction`, `mix_rollback_correction`, `mix_evaluate_correction`, `production_audit`, `validate_production_completeness`, `clean_track_resonances`, `configure_physical_sidechain`, `apply_kick_sidechain_to_bass`, `configure_depth_staging`, `auto_gain_stage_session`, `apply_track_channel_strip`, `apply_group_bus_processing`, `mix_apply_frequency_slotting`, `mix_audit_phase_and_mono_compatibility`, `mix_apply_vocal_lead_fader_riding`, `mix_apply_multitrack_sidechain_ducking`, `mix_audit_psychoacoustic_masking`, `analyze_mix_static`.\n
### 4.8 Masterización, Loudness y Control de Calidad
- `master_analyze`, `master_readiness`, `master_create_chain`, `master_apply`, `master_preview`, `master_evaluate`, `master_rollback`, `master_compare_reference`, `master_translation_test`, `master_quality_control`, `master_export`, `master_get_report`, `master_get_history`, `master_project`, `setup_full_mastering_chain`.\n
### 4.9 Audio Forensics y Procesamiento de Señal
- `forensics_analyze`, `forensics_report`, `forensics_events`, `forensics_explain`, `audio_listen_live`, `audio_capture`, `audio_analyze`, `audio_analyze_track`, `audio_analyze_section`, `audio_analyze_stem`, `audio_semantic_sample_match`, `audio_deconstruct_reference`, `audio_transcribe_to_midi`, `reference_deconstruct`, `reference_reconstruct_in_live`.\n
### 4.10 Stems y Entrega Comercial
- `stem_create_export_plan`, `stem_generate_manifest`, `export_and_audit_stems`, `export_commercial_release_package`, `macro_finalize_song`.\n
### 4.11 Tratamiento Vocal Avanzado
- `vocal_get_profile`, `vocal_calculate_ducking`, `apply_adaptive_deesser`, `generate_vocal_hook_chops`, `chop_drum_loop_transients`, `generate_organic_foley_bed`, `dna_create_creative_brief`, `dna_scaffold_live_project`, `dna_get_reference_profiles`, `get_vocal_chain_guide`.\n
---

## 5. Índice Completo de la Suite de Pruebas (956 Tests — 100% Verde)

La suite oficial cuenta con **956 pruebas automatizadas** que garantizan cero regresiones acústicas, determinismo total y estabilidad de red:

### 5.1 Resumen Consolidado por Dominios
| Dominio Funcional | Cantidad de Archivos | Tests Totales | Tasa de Aprobación |
| :--- | :---: | :---: | :---: |
| **Copilot & Studio Doctor** | 5 | **51** | 100% PASS |
| **Gobernanza Causal, Transacciones & Snapshots** | 54 | **430** | 100% PASS |
| **Teoría Musical, Armonía & Composición** | 9 | **56** | 100% PASS |
| **Instrumentos, Navegador & Esculpido VST** | 13 | **76** | 100% PASS |
| **Arreglo, Transiciones & Estructura** | 15 | **87** | 100% PASS |
| **Digital Ear, Mezcla, Balance & Resonancias** | 16 | **83** | 100% PASS |
| **Masterización, Loudness & Gain Staging** | 7 | **53** | 100% PASS |
| **Audio Forense, STFT & Verificación** | 10 | **33** | 100% PASS |
| **Stems, Exportación & Pipeline E2E** | 6 | **33** | 100% PASS |
| **Voz, Procesamiento Vocal & Resiliencia** | 10 | **54** | 100% PASS |
| **TOTAL OFICIAL MAESTRO** | **145** | **956** | **100% PASS** |

### 5.2 Desglose Exhaustivo por Archivo de Prueba
| Módulo de Prueba | Pruebas | Estado |
| :--- | :---: | :---: |
| **--- COPILOT & STUDIO DOCTOR (51 Tests) ---** | | |
| [`tests/test_copilot_engine_upgrades.py`](file:///F:/Dev/AbletonEngine/tests/test_copilot_engine_upgrades.py) | 9 | 100% PASS |
| [`tests/test_copilot_stepper.py`](file:///F:/Dev/AbletonEngine/tests/test_copilot_stepper.py) | 17 | 100% PASS |
| [`tests/test_knowledge_base.py`](file:///F:/Dev/AbletonEngine/tests/test_knowledge_base.py) | 7 | 100% PASS |
| [`tests/test_session_doctor.py`](file:///F:/Dev/AbletonEngine/tests/test_session_doctor.py) | 15 | 100% PASS |
| [`tests/test_user_learning.py`](file:///F:/Dev/AbletonEngine/tests/test_user_learning.py) | 3 | 100% PASS |
| **--- GOBERNANZA CAUSAL, TRANSACCIONES & SNAPSHOTS (430 Tests) ---** | | |
| [`tests/test_ai_layers.py`](file:///F:/Dev/AbletonEngine/tests/test_ai_layers.py) | 6 | 100% PASS |
| [`tests/test_anti_cliche_guard.py`](file:///F:/Dev/AbletonEngine/tests/test_anti_cliche_guard.py) | 4 | 100% PASS |
| [`tests/test_automation_weaver.py`](file:///F:/Dev/AbletonEngine/tests/test_automation_weaver.py) | 3 | 100% PASS |
| [`tests/test_bass_glide.py`](file:///F:/Dev/AbletonEngine/tests/test_bass_glide.py) | 3 | 100% PASS |
| [`tests/test_clip_automation_suggester.py`](file:///F:/Dev/AbletonEngine/tests/test_clip_automation_suggester.py) | 6 | 100% PASS |
| [`tests/test_concurrency.py`](file:///F:/Dev/AbletonEngine/tests/test_concurrency.py) | 1 | 100% PASS |
| [`tests/test_creative_dna.py`](file:///F:/Dev/AbletonEngine/tests/test_creative_dna.py) | 8 | 100% PASS |
| [`tests/test_decision_memory.py`](file:///F:/Dev/AbletonEngine/tests/test_decision_memory.py) | 4 | 100% PASS |
| [`tests/test_ear_candy.py`](file:///F:/Dev/AbletonEngine/tests/test_ear_candy.py) | 3 | 100% PASS |
| [`tests/test_engine_governance.py`](file:///F:/Dev/AbletonEngine/tests/test_engine_governance.py) | 15 | 100% PASS |
| [`tests/test_extended_engine_suite.py`](file:///F:/Dev/AbletonEngine/tests/test_extended_engine_suite.py) | 14 | 100% PASS |
| [`tests/test_failure_diagnostics.py`](file:///F:/Dev/AbletonEngine/tests/test_failure_diagnostics.py) | 3 | 100% PASS |
| [`tests/test_failure_injection.py`](file:///F:/Dev/AbletonEngine/tests/test_failure_injection.py) | 22 | 100% PASS |
| [`tests/test_flow_enhancements_five_pillars.py`](file:///F:/Dev/AbletonEngine/tests/test_flow_enhancements_five_pillars.py) | 5 | 100% PASS |
| [`tests/test_forensics_failure_injection.py`](file:///F:/Dev/AbletonEngine/tests/test_forensics_failure_injection.py) | 6 | 100% PASS |
| [`tests/test_full_production_0_to_100.py`](file:///F:/Dev/AbletonEngine/tests/test_full_production_0_to_100.py) | 1 | 100% PASS |
| [`tests/test_fx_audio_track_and_routing.py`](file:///F:/Dev/AbletonEngine/tests/test_fx_audio_track_and_routing.py) | 4 | 100% PASS |
| [`tests/test_guided_session.py`](file:///F:/Dev/AbletonEngine/tests/test_guided_session.py) | 30 | 100% PASS |
| [`tests/test_guided_session_automation_surgical.py`](file:///F:/Dev/AbletonEngine/tests/test_guided_session_automation_surgical.py) | 6 | 100% PASS |
| [`tests/test_guided_session_improvements_integration.py`](file:///F:/Dev/AbletonEngine/tests/test_guided_session_improvements_integration.py) | 1 | 100% PASS |
| [`tests/test_interpretation_phase4.py`](file:///F:/Dev/AbletonEngine/tests/test_interpretation_phase4.py) | 13 | 100% PASS |
| [`tests/test_library_crawler.py`](file:///F:/Dev/AbletonEngine/tests/test_library_crawler.py) | 1 | 100% PASS |
| [`tests/test_live_automation.py`](file:///F:/Dev/AbletonEngine/tests/test_live_automation.py) | 3 | 100% PASS |
| [`tests/test_live_listener.py`](file:///F:/Dev/AbletonEngine/tests/test_live_listener.py) | 5 | 100% PASS |
| [`tests/test_live_master_chain.py`](file:///F:/Dev/AbletonEngine/tests/test_live_master_chain.py) | 3 | 100% PASS |
| [`tests/test_multitrack_drums.py`](file:///F:/Dev/AbletonEngine/tests/test_multitrack_drums.py) | 4 | 100% PASS |
| [`tests/test_parquet_indexer.py`](file:///F:/Dev/AbletonEngine/tests/test_parquet_indexer.py) | 2 | 100% PASS |
| [`tests/test_physical_snapshots.py`](file:///F:/Dev/AbletonEngine/tests/test_physical_snapshots.py) | 5 | 100% PASS |
| [`tests/test_production_completeness.py`](file:///F:/Dev/AbletonEngine/tests/test_production_completeness.py) | 6 | 100% PASS |
| [`tests/test_production_context.py`](file:///F:/Dev/AbletonEngine/tests/test_production_context.py) | 6 | 100% PASS |
| [`tests/test_production_executor.py`](file:///F:/Dev/AbletonEngine/tests/test_production_executor.py) | 14 | 100% PASS |
| [`tests/test_production_graph.py`](file:///F:/Dev/AbletonEngine/tests/test_production_graph.py) | 8 | 100% PASS |
| [`tests/test_production_integration.py`](file:///F:/Dev/AbletonEngine/tests/test_production_integration.py) | 21 | 100% PASS |
| [`tests/test_production_mcp.py`](file:///F:/Dev/AbletonEngine/tests/test_production_mcp.py) | 20 | 100% PASS |
| [`tests/test_production_models.py`](file:///F:/Dev/AbletonEngine/tests/test_production_models.py) | 23 | 100% PASS |
| [`tests/test_production_planner.py`](file:///F:/Dev/AbletonEngine/tests/test_production_planner.py) | 4 | 100% PASS |
| [`tests/test_production_policy.py`](file:///F:/Dev/AbletonEngine/tests/test_production_policy.py) | 20 | 100% PASS |
| [`tests/test_production_rollback.py`](file:///F:/Dev/AbletonEngine/tests/test_production_rollback.py) | 23 | 100% PASS |
| [`tests/test_production_storage.py`](file:///F:/Dev/AbletonEngine/tests/test_production_storage.py) | 1 | 100% PASS |
| [`tests/test_production_verification.py`](file:///F:/Dev/AbletonEngine/tests/test_production_verification.py) | 21 | 100% PASS |
| [`tests/test_reconciliation.py`](file:///F:/Dev/AbletonEngine/tests/test_reconciliation.py) | 3 | 100% PASS |
| [`tests/test_reference_deconstructor.py`](file:///F:/Dev/AbletonEngine/tests/test_reference_deconstructor.py) | 4 | 100% PASS |
| [`tests/test_resolver.py`](file:///F:/Dev/AbletonEngine/tests/test_resolver.py) | 3 | 100% PASS |
| [`tests/test_role_orchestrator.py`](file:///F:/Dev/AbletonEngine/tests/test_role_orchestrator.py) | 9 | 100% PASS |
| [`tests/test_session_fingerprint.py`](file:///F:/Dev/AbletonEngine/tests/test_session_fingerprint.py) | 5 | 100% PASS |
| [`tests/test_session_graph.py`](file:///F:/Dev/AbletonEngine/tests/test_session_graph.py) | 2 | 100% PASS |
| [`tests/test_snapshots.py`](file:///F:/Dev/AbletonEngine/tests/test_snapshots.py) | 2 | 100% PASS |
| [`tests/test_sound_engine.py`](file:///F:/Dev/AbletonEngine/tests/test_sound_engine.py) | 12 | 100% PASS |
| [`tests/test_spectral_chop_harmonizer.py`](file:///F:/Dev/AbletonEngine/tests/test_spectral_chop_harmonizer.py) | 5 | 100% PASS |
| [`tests/test_state_flexibility_and_micro_surgery.py`](file:///F:/Dev/AbletonEngine/tests/test_state_flexibility_and_micro_surgery.py) | 6 | 100% PASS |
| [`tests/test_suite_pillars.py`](file:///F:/Dev/AbletonEngine/tests/test_suite_pillars.py) | 20 | 100% PASS |
| [`tests/test_supervisor_gatekeeper.py`](file:///F:/Dev/AbletonEngine/tests/test_supervisor_gatekeeper.py) | 6 | 100% PASS |
| [`tests/test_transaction_guard.py`](file:///F:/Dev/AbletonEngine/tests/test_transaction_guard.py) | 2 | 100% PASS |
| [`tests/test_transactions.py`](file:///F:/Dev/AbletonEngine/tests/test_transactions.py) | 3 | 100% PASS |
| **--- TEORÍA MUSICAL, ARMONÍA & COMPOSICIÓN (56 Tests) ---** | | |
| [`tests/test_beat_switch_reharmonization.py`](file:///F:/Dev/AbletonEngine/tests/test_beat_switch_reharmonization.py) | 3 | 100% PASS |
| [`tests/test_composition_phase2.py`](file:///F:/Dev/AbletonEngine/tests/test_composition_phase2.py) | 11 | 100% PASS |
| [`tests/test_counter_melody_arp.py`](file:///F:/Dev/AbletonEngine/tests/test_counter_melody_arp.py) | 4 | 100% PASS |
| [`tests/test_groove_pocket.py`](file:///F:/Dev/AbletonEngine/tests/test_groove_pocket.py) | 5 | 100% PASS |
| [`tests/test_groove_pool.py`](file:///F:/Dev/AbletonEngine/tests/test_groove_pool.py) | 4 | 100% PASS |
| [`tests/test_music_engine.py`](file:///F:/Dev/AbletonEngine/tests/test_music_engine.py) | 17 | 100% PASS |
| [`tests/test_musical_os_and_prosody.py`](file:///F:/Dev/AbletonEngine/tests/test_musical_os_and_prosody.py) | 5 | 100% PASS |
| [`tests/test_phrase_evolver.py`](file:///F:/Dev/AbletonEngine/tests/test_phrase_evolver.py) | 4 | 100% PASS |
| [`tests/test_scale_tuning_and_automation_optimization.py`](file:///F:/Dev/AbletonEngine/tests/test_scale_tuning_and_automation_optimization.py) | 3 | 100% PASS |
| **--- INSTRUMENTOS, NAVEGADOR & ESCULPIDO VST (76 Tests) ---** | | |
| [`tests/test_analog_lab_ui_automator.py`](file:///F:/Dev/AbletonEngine/tests/test_analog_lab_ui_automator.py) | 2 | 100% PASS |
| [`tests/test_browser_catalog.py`](file:///F:/Dev/AbletonEngine/tests/test_browser_catalog.py) | 2 | 100% PASS |
| [`tests/test_drum_rack_guard.py`](file:///F:/Dev/AbletonEngine/tests/test_drum_rack_guard.py) | 5 | 100% PASS |
| [`tests/test_instrument_engine.py`](file:///F:/Dev/AbletonEngine/tests/test_instrument_engine.py) | 7 | 100% PASS |
| [`tests/test_instrumentation_phase3.py`](file:///F:/Dev/AbletonEngine/tests/test_instrumentation_phase3.py) | 15 | 100% PASS |
| [`tests/test_patch_decision.py`](file:///F:/Dev/AbletonEngine/tests/test_patch_decision.py) | 3 | 100% PASS |
| [`tests/test_preset_catalog.py`](file:///F:/Dev/AbletonEngine/tests/test_preset_catalog.py) | 10 | 100% PASS |
| [`tests/test_preset_selection_auto_load.py`](file:///F:/Dev/AbletonEngine/tests/test_preset_selection_auto_load.py) | 3 | 100% PASS |
| [`tests/test_vital_patch_builder.py`](file:///F:/Dev/AbletonEngine/tests/test_vital_patch_builder.py) | 6 | 100% PASS |
| [`tests/test_vst_guard.py`](file:///F:/Dev/AbletonEngine/tests/test_vst_guard.py) | 3 | 100% PASS |
| [`tests/test_vst_normalizer.py`](file:///F:/Dev/AbletonEngine/tests/test_vst_normalizer.py) | 8 | 100% PASS |
| [`tests/test_vst_preset_search.py`](file:///F:/Dev/AbletonEngine/tests/test_vst_preset_search.py) | 9 | 100% PASS |
| [`tests/test_vst_vocal_chain_detection.py`](file:///F:/Dev/AbletonEngine/tests/test_vst_vocal_chain_detection.py) | 3 | 100% PASS |
| **--- ARREGLO, TRANSICIONES & ESTRUCTURA (87 Tests) ---** | | |
| [`tests/test_arrangement_automation_injection.py`](file:///F:/Dev/AbletonEngine/tests/test_arrangement_automation_injection.py) | 2 | 100% PASS |
| [`tests/test_arrangement_automation_recorder.py`](file:///F:/Dev/AbletonEngine/tests/test_arrangement_automation_recorder.py) | 3 | 100% PASS |
| [`tests/test_arrangement_composer.py`](file:///F:/Dev/AbletonEngine/tests/test_arrangement_composer.py) | 4 | 100% PASS |
| [`tests/test_arrangement_engine.py`](file:///F:/Dev/AbletonEngine/tests/test_arrangement_engine.py) | 10 | 100% PASS |
| [`tests/test_audio_tracks_and_cue_points.py`](file:///F:/Dev/AbletonEngine/tests/test_audio_tracks_and_cue_points.py) | 3 | 100% PASS |
| [`tests/test_drum_evolver.py`](file:///F:/Dev/AbletonEngine/tests/test_drum_evolver.py) | 4 | 100% PASS |
| [`tests/test_foley_texture.py`](file:///F:/Dev/AbletonEngine/tests/test_foley_texture.py) | 5 | 100% PASS |
| [`tests/test_full_song_arranger.py`](file:///F:/Dev/AbletonEngine/tests/test_full_song_arranger.py) | 6 | 100% PASS |
| [`tests/test_genre_drums.py`](file:///F:/Dev/AbletonEngine/tests/test_genre_drums.py) | 13 | 100% PASS |
| [`tests/test_impacts_downlifters.py`](file:///F:/Dev/AbletonEngine/tests/test_impacts_downlifters.py) | 4 | 100% PASS |
| [`tests/test_live_arrangement_automation.py`](file:///F:/Dev/AbletonEngine/tests/test_live_arrangement_automation.py) | 3 | 100% PASS |
| [`tests/test_transient_chopper.py`](file:///F:/Dev/AbletonEngine/tests/test_transient_chopper.py) | 5 | 100% PASS |
| [`tests/test_transition_risers.py`](file:///F:/Dev/AbletonEngine/tests/test_transition_risers.py) | 4 | 100% PASS |
| [`tests/test_transitions_engine.py`](file:///F:/Dev/AbletonEngine/tests/test_transitions_engine.py) | 6 | 100% PASS |
| [`tests/test_transitions_phase5.py`](file:///F:/Dev/AbletonEngine/tests/test_transitions_phase5.py) | 15 | 100% PASS |
| **--- DIGITAL EAR, MEZCLA, BALANCE & RESONANCIAS (83 Tests) ---** | | |
| [`tests/test_acoustic_probe.py`](file:///F:/Dev/AbletonEngine/tests/test_acoustic_probe.py) | 3 | 100% PASS |
| [`tests/test_auto_curate.py`](file:///F:/Dev/AbletonEngine/tests/test_auto_curate.py) | 3 | 100% PASS |
| [`tests/test_auto_sidechain.py`](file:///F:/Dev/AbletonEngine/tests/test_auto_sidechain.py) | 3 | 100% PASS |
| [`tests/test_channel_strip.py`](file:///F:/Dev/AbletonEngine/tests/test_channel_strip.py) | 7 | 100% PASS |
| [`tests/test_depth_staging.py`](file:///F:/Dev/AbletonEngine/tests/test_depth_staging.py) | 2 | 100% PASS |
| [`tests/test_device_parameter_supervisor.py`](file:///F:/Dev/AbletonEngine/tests/test_device_parameter_supervisor.py) | 6 | 100% PASS |
| [`tests/test_dynamic_eq.py`](file:///F:/Dev/AbletonEngine/tests/test_dynamic_eq.py) | 4 | 100% PASS |
| [`tests/test_forensics_masking.py`](file:///F:/Dev/AbletonEngine/tests/test_forensics_masking.py) | 3 | 100% PASS |
| [`tests/test_frequency_balance_audit.py`](file:///F:/Dev/AbletonEngine/tests/test_frequency_balance_audit.py) | 5 | 100% PASS |
| [`tests/test_mix_engine.py`](file:///F:/Dev/AbletonEngine/tests/test_mix_engine.py) | 10 | 100% PASS |
| [`tests/test_mix_phase6.py`](file:///F:/Dev/AbletonEngine/tests/test_mix_phase6.py) | 15 | 100% PASS |
| [`tests/test_physical_sidechain.py`](file:///F:/Dev/AbletonEngine/tests/test_physical_sidechain.py) | 3 | 100% PASS |
| [`tests/test_physical_sidechain_and_mastering.py`](file:///F:/Dev/AbletonEngine/tests/test_physical_sidechain_and_mastering.py) | 3 | 100% PASS |
| [`tests/test_resonance_hunter.py`](file:///F:/Dev/AbletonEngine/tests/test_resonance_hunter.py) | 3 | 100% PASS |
| [`tests/test_static_mix_auditor.py`](file:///F:/Dev/AbletonEngine/tests/test_static_mix_auditor.py) | 2 | 100% PASS |
| [`tests/test_track_fx_rack.py`](file:///F:/Dev/AbletonEngine/tests/test_track_fx_rack.py) | 11 | 100% PASS |
| **--- MASTERIZACIÓN, LOUDNESS & GAIN STAGING (53 Tests) ---** | | |
| [`tests/test_bs1770_5_loudness.py`](file:///F:/Dev/AbletonEngine/tests/test_bs1770_5_loudness.py) | 17 | 100% PASS |
| [`tests/test_gain_staging.py`](file:///F:/Dev/AbletonEngine/tests/test_gain_staging.py) | 3 | 100% PASS |
| [`tests/test_guided_mastering.py`](file:///F:/Dev/AbletonEngine/tests/test_guided_mastering.py) | 3 | 100% PASS |
| [`tests/test_lufs_validation_gate.py`](file:///F:/Dev/AbletonEngine/tests/test_lufs_validation_gate.py) | 7 | 100% PASS |
| [`tests/test_mastering_and_delivery_features.py`](file:///F:/Dev/AbletonEngine/tests/test_mastering_and_delivery_features.py) | 5 | 100% PASS |
| [`tests/test_mastering_engine.py`](file:///F:/Dev/AbletonEngine/tests/test_mastering_engine.py) | 10 | 100% PASS |
| [`tests/test_mastering_phase7.py`](file:///F:/Dev/AbletonEngine/tests/test_mastering_phase7.py) | 8 | 100% PASS |
| **--- AUDIO FORENSE, STFT & VERIFICACIÓN (33 Tests) ---** | | |
| [`tests/test_forensics_anomalies.py`](file:///F:/Dev/AbletonEngine/tests/test_forensics_anomalies.py) | 5 | 100% PASS |
| [`tests/test_forensics_baseline.py`](file:///F:/Dev/AbletonEngine/tests/test_forensics_baseline.py) | 2 | 100% PASS |
| [`tests/test_forensics_causality.py`](file:///F:/Dev/AbletonEngine/tests/test_forensics_causality.py) | 2 | 100% PASS |
| [`tests/test_forensics_clipping.py`](file:///F:/Dev/AbletonEngine/tests/test_forensics_clipping.py) | 3 | 100% PASS |
| [`tests/test_forensics_correlation.py`](file:///F:/Dev/AbletonEngine/tests/test_forensics_correlation.py) | 3 | 100% PASS |
| [`tests/test_forensics_integration.py`](file:///F:/Dev/AbletonEngine/tests/test_forensics_integration.py) | 3 | 100% PASS |
| [`tests/test_forensics_models.py`](file:///F:/Dev/AbletonEngine/tests/test_forensics_models.py) | 5 | 100% PASS |
| [`tests/test_forensics_spectral.py`](file:///F:/Dev/AbletonEngine/tests/test_forensics_spectral.py) | 5 | 100% PASS |
| [`tests/test_forensics_stft.py`](file:///F:/Dev/AbletonEngine/tests/test_forensics_stft.py) | 3 | 100% PASS |
| [`tests/test_forensics_temporal.py`](file:///F:/Dev/AbletonEngine/tests/test_forensics_temporal.py) | 2 | 100% PASS |
| **--- STEMS, EXPORTACIÓN & PIPELINE E2E (33 Tests) ---** | | |
| [`tests/test_macro_finalizer_and_stem_pipeline.py`](file:///F:/Dev/AbletonEngine/tests/test_macro_finalizer_and_stem_pipeline.py) | 6 | 100% PASS |
| [`tests/test_macro_recipes.py`](file:///F:/Dev/AbletonEngine/tests/test_macro_recipes.py) | 5 | 100% PASS |
| [`tests/test_recipe_engine.py`](file:///F:/Dev/AbletonEngine/tests/test_recipe_engine.py) | 13 | 100% PASS |
| [`tests/test_release_package.py`](file:///F:/Dev/AbletonEngine/tests/test_release_package.py) | 4 | 100% PASS |
| [`tests/test_stem_bouncer.py`](file:///F:/Dev/AbletonEngine/tests/test_stem_bouncer.py) | 1 | 100% PASS |
| [`tests/test_stem_phase_audit.py`](file:///F:/Dev/AbletonEngine/tests/test_stem_phase_audit.py) | 4 | 100% PASS |
| **--- VOZ, PROCESAMIENTO VOCAL & RESILIENCIA (54 Tests) ---** | | |
| [`tests/test_pre_vocal_panning.py`](file:///F:/Dev/AbletonEngine/tests/test_pre_vocal_panning.py) | 5 | 100% PASS |
| [`tests/test_user_vocal_preservation_and_chop_guard.py`](file:///F:/Dev/AbletonEngine/tests/test_user_vocal_preservation_and_chop_guard.py) | 2 | 100% PASS |
| [`tests/test_vocal_and_mutation_suite.py`](file:///F:/Dev/AbletonEngine/tests/test_vocal_and_mutation_suite.py) | 9 | 100% PASS |
| [`tests/test_vocal_auto_orchestration.py`](file:///F:/Dev/AbletonEngine/tests/test_vocal_auto_orchestration.py) | 7 | 100% PASS |
| [`tests/test_vocal_chopper.py`](file:///F:/Dev/AbletonEngine/tests/test_vocal_chopper.py) | 5 | 100% PASS |
| [`tests/test_vocal_level_auditor.py`](file:///F:/Dev/AbletonEngine/tests/test_vocal_level_auditor.py) | 4 | 100% PASS |
| [`tests/test_vocal_pipeline.py`](file:///F:/Dev/AbletonEngine/tests/test_vocal_pipeline.py) | 4 | 100% PASS |
| [`tests/test_vocal_slicer_and_acoustics.py`](file:///F:/Dev/AbletonEngine/tests/test_vocal_slicer_and_acoustics.py) | 5 | 100% PASS |
| [`tests/test_vocal_staging.py`](file:///F:/Dev/AbletonEngine/tests/test_vocal_staging.py) | 4 | 100% PASS |
| [`tests/test_whisper_and_auto_anti_echo.py`](file:///F:/Dev/AbletonEngine/tests/test_whisper_and_auto_anti_echo.py) | 9 | 100% PASS |
| **TOTAL CONSOLIDADO** | **956** | **100% PASS** |

---

## 6. Taxonomía de Nodos y Aristas del Grafo Causal (`ProductionGraph`)

### 6.1 Tipos de Nodo (`NodeType`)
1. `INTENT`: Intención musical o técnica de alto nivel del usuario o LLM.
2. `OBSERVATION`: Medición acústica objetiva previa a la intervención.
3. `ANALYSIS`: Diagnóstico de headroom, balance espectral y detección de problemas.
4. `HYPOTHESIS`: Hipótesis causal que justifica por qué una acción logrará el objetivo.
5. `CANDIDATE`: Estrategia de producción candidata en competencia.
6. `POLICY_CHECK`: Evaluación de guardrails inviolables del `ProductionPolicyEngine`.
7. `PLAN`: Plan inmutable, versionado y asociado al fingerprint SHA-256 de la sesión.
8. `VALIDATION`: Comprobación previa de frescura (`STALE`) y ausencia de bloqueos.
9. `SIMULATION`: Dry-run acústico predictivo sin efectos secundarios en Live.
10. `TRANSACTION`: Unidad atómica de trabajo con snapshot de seguridad previo.
11. `ACTION`: Operación física en dispositivo o parámetro de Ableton Live.
12. `MEASUREMENT`: Medición acústica posterior a la ejecución.
13. `VERIFICATION`: Evaluación de la `VerificationMatrix` (delta real vs esperado y no regresión).
14. `RESULT`: Resultado final exitoso (`COMMITTED`).
15. `ROLLBACK`: Reversión atómica de la acción; conserva evidencia y causalidad.
16. `REJECTION`: Registro inmutable de un candidato descartado por violación de políticas.
17. `NO_OP`: Decisión formal de no intervenir bajo el Principio de Mínima Intervención.

### 6.2 Políticas Inviolables (`ProductionPolicyEngine`)
1. `MAX_LIMITER_GAIN_REDUCTION`: Máximo 2.5 dB de reducción de ganancia en limitador en master.
2. `TRUE_PEAK_CEILING`: El True Peak del Master nunca debe superar -0.3 dBTP (-1.0 dBTP en streaming).
3. `MASTER_EQ_MAX_BANDS`: El ecualizador del master no puede tener más de 2 bandas activas.
4. `MONO_SUB_BASS`: Frecuencias inferiores a 120 Hz deben mantenerse estrictamente en mono.
5. `MIN_HEADROOM_PREMASTER`: Headroom mínimo de 3.0 dB en premaster antes de la limitación final.
6. `MANDATORY_SYNTHESIS_SCULPTING`: En la fase de sonido, ningún sintetizador puede conservar parámetros por defecto ($\\Delta \\ge 1$).
7. `TOP_TAIL_ACOUSTIC_GUARD`: Pre-roll a 0.0s debe medir < -70 dBFS; compás final debe descender a $-\\infty$ dB.

---

## 7. Especificaciones Acústicas de Entrega y Formatos Comerciales

### 7.1 Perfiles de Sonoridad (ITU-R BS.1770-5 & EBU R 128)
| Perfil | Tipo de Autoridad | Target LUFS | Tolerancia | Techo True Peak | Max Limiter GR | Dinámica (LRA) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`EBU_R128`** | `STANDARD` | $-23.0\\text{ LUFS}$ | $\\pm 0.5\\text{ LU}$ | $-1.00\\text{ dBTP}$ | $2.0\\text{ dB}$ | $\\le 14.0\\text{ LU}$ |
| **`STREAMING`** | `RECOMMENDATION` | $-14.0\\text{ LUFS}$ | $\\pm 1.0\\text{ LU}$ | $-1.00\\text{ dBTP}$ | $2.5\\text{ dB}$ | $\\ge 4.0\\text{ LU}$ |
| **`CLUB`** | `PIE_POLICY` | $-7.5\\text{ LUFS}$ | $\\pm 1.0\\text{ LU}$ | $-0.30\\text{ dBTP}$ | $3.0\\text{ dB}$ | $\\ge 3.0\\text{ LU}$ |
| **`DIGITAL_DOWNLOAD`** | `RECOMMENDATION` | $-9.0\\text{ LUFS}$ | $\\pm 1.0\\text{ LU}$ | $-0.50\\text{ dBTP}$ | $2.5\\text{ dB}$ | $\\ge 4.0\\text{ LU}$ |
| **`PREMASTER`** | `PIE_POLICY` | $-18.0\\text{ LUFS}$ | $\\pm 2.0\\text{ LU}$ | $-3.00\\text{ dBTP}$ | $0.0\\text{ dB}$ | N/A |

### 7.2 Paquete de Stems Comerciales Certificado
- **Formato:** Broadcast WAV, 24-bit / 44.1 kHz sin compresión.
- **Grupos de Entrega (5 + Master):**
  1. `DRUMS.wav`: Kick, Snare, Hi-Hats y Percusiones.
  2. `BASS.wav`: 808s, Sub-graves y bajos sintéticos/eléctricos.
  3. `KEYS_BRASS.wav`: Pianos, Rhodes, Sintetizadores, Arpegios y Metales.
  4. `VOCALS.wav`: Voces principales, coros y vocal chops.
  5. `FX.wav`: Foley orgánico, risers, impactos y sweeps.
  6. `MASTER.wav`: Render comercial completo con cadena de mastering final.
- **Manifiesto Forense (`stems_manifest.json`):**
  - Hash SHA-256 de cada archivo individual.
  - Mediciones individuales de LUFS integrado, True Peak y LRA.
  - Correlación cruzada de fase multi-stem certificada ($\\rho \\ge 0.35$).
