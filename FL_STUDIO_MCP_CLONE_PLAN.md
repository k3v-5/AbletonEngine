# Informe Detallado: Arquitectura y Funcionalidades de Ableton PIE (Production Intelligence Engine)
Este documento detalla la arquitectura, las fases funcionales, el sistema de gobernanza y las herramientas (tools) provistas por el proyecto Ableton PIE. El objetivo de este documento es servir como un plano (blueprint) integral para poder clonar esta funcionalidad en un MCP similar dirigido a FL Studio.

## 1. Filosofía Central
El sistema se basa en un marco estricto donde la IA (modelo de lenguaje) decide la "intención musical", pero el motor (PIE) se encarga de:
- Planificar y validar la viabilidad acústica.
- Asegurar reglas estrictas (Gobernanza y Políticas).
- Ejecutar transacciones atómicas con verificación de estado.
- Ableton Live actúa meramente como el ejecutor físico y proveedor del estado base a través de su Remote Script (puerto 9877).

Para FL Studio, el enfoque debe ser análogo, usando posiblemente la API de scripts MIDI de FL Studio (Python) o un puente de control (como IL Remote o un plugin VST puente) para exponer la misma superficie de control al servidor MCP.

---

## 2. Arquitectura General
El proyecto cuenta con un servidor principal (`server.py`) construido sobre `FastMCP`. Se comunica con Ableton a través de un socket TCP (`localhost:9877`).

### Flujo Causal
1. **Intención:** Recibe un prompt.
2. **PIE Graph & Memory:** Verifica el historial y planes (Shadow Graph).
3. **Policy Engine:** Valida guardrails inviolables.
4. **Execution:** Transacciones atómicas (ACID) y ejecución.
5. **Verification:** Confirmación acústica con DSP real, con *rollback automático* en caso de regresión.

---

## 3. Fases del Motor (Engine Phases)

### 3.1 Fase 1: Foundation (Fundación)
Se encarga de mantener un "Shadow Graph" (estado de la sesión) sincronizado con el estado real del DAW, y proporciona un sistema transaccional robusto (Write-Ahead Log y Snapshots).
**Herramientas Clave (Tools):**
- `session_inspect`, `session_refresh`, `session_diff`, `session_resolve`
- `transaction_begin`, `transaction_commit`, `transaction_rollback`, `transaction_preview`
- `snapshot_create`, `snapshot_restore`
- Herramientas de control directo: `create_midi_track`, `set_track_volume`, `create_clip`, `set_tempo`, `start_playback`

### 3.2 Fase 2 & 2.5: Music Engine & Instruments
Encargado de la teoría musical, rítmica y armonía. Genera progresiones, líneas de bajo, baterías y melodías. Mapea intenciones a instrumentos.
**Herramientas Clave (Tools):**
- `music_generate_part`, `music_generate_harmony`, `music_generate_bass`, `music_generate_drums`, `music_generate_melody`
- `music_humanize`, `music_apply_groove` (Swing, micro-tiempos)
- `instrument_inspect`, `load_instrument_or_effect`, `drum_rack_populate`, `drum_rack_add_pad`

### 3.3 Fase 3: Arrangement (Arreglo)
Orquesta la macro-estructura (Intro, Verso, Build, Drop) y curvas de energía musical, inyectando automatizaciones de LOM.
**Herramientas Clave (Tools):**
- `arrangement_generate`, `arrangement_add_energy_curve`
- `apply_transition_automation_weaver` (Risers, sweeps de filtro, washouts)
- `evolve_arrangement_phrase` (Rompe la monotonía con micro-fills y staccatos)
- `build_song` (Comando maestro que orquesta un proyecto entero)

### 3.4 Fase 4: Sound Design
Se encarga del diseño tímbrico y modulación (Macros). Modifica y aplica presets a cadenas de efectos e instrumentos.
**Herramientas Clave (Tools):**
- `sound_create`, `sound_update`, `sound_apply_profile`
- `sound_set_macro` (Brightness, warmth, punch, space, etc.)
- `sound_lint`, `sound_rebuild`

### 3.5 Fase 5: Digital Ear & Mix Intelligence
Realiza análisis acústico profundo usando DSP puro (sin requerir bounce externo si es posible) o analizando stems. Identifica choques de frecuencia, enmascaramiento kick/bass y balance mono.
**Herramientas Clave (Tools):**
- `audio_listen_live`, `audio_capture`
- `mix_analyze`, `mix_lint`, `mix_diagnose`
- `mix_suggest_correction`, `mix_apply_correction`
- `mix_get_conflicts`, `mix_check_mono`, `mix_check_headroom`

### 3.6 Fase 6: Mastering & Quality Control
Crea la cadena maestra y aplica normativas de Loudness internacionales (ITU-R BS.1770-5, EBU R128). Diferencia claramente los problemas de mezcla (que requieren arreglar pistas) frente al mastering.
**Herramientas Clave (Tools):**
- `master_analyze`, `master_readiness`
- `master_create_chain`, `master_apply`, `master_preview`
- `master_evaluate`, `master_quality_control`, `master_translation_test`
- `master_export`

### 3.7 Fase 7: Audio Forensics Engine
Diagnóstico preciso de problemas de audio a nivel de muestreo (clipping inter-sample, DC offset, fase).
**Herramientas Clave (Tools):**
- `forensics_analyze`, `forensics_report`, `forensics_events`, `forensics_explain`

---

## 4. Hito 1: Governance, Causal Memory & Production Planning
Es el "cerebro" central que supervisa las acciones, manteniendo un rastro de todo lo que sucede.
- **Production Graph:** Grafo Causal Aclíclico que modela las relaciones entre hechos, mediciones, planes y resultados.
- **Decision Memory:** Contextual, guarda memoria de qué funcionó en base a hashes, pero nunca auto-ejecuta.
- **Policy Engine:** Guardarraíles acústicos (ej. Limiter no mayor a 2.5 dB GR).

**Herramientas Clave (Tools):**
- `production_status`, `production_plan`, `production_validate`, `production_execute`
- `production_explain` (Justifica la trazabilidad causal)
- `production_rollback` (Revierte una decisión causal)

---

## 5. Implementación en FL Studio (Ideas para el Clon)

Para portar esto a **FL Studio**, se necesitará lo siguiente:
1. **Remote Script (Python):** FL Studio 20+ soporta MIDI scripting en Python. Se deberá crear un script que escuche un puerto TCP/UDP y exponga funciones como `channels.setVolume()`, `mixer.setTrackVolume()`, `patterns.addNote()`, etc.
2. **Server (FastMCP):** Un servidor local `server.py` que se conecte a este puerto de FL Studio, igual que lo hace con Ableton.
3. **DSP/Audio Analyzer:** Dependerá de Python (librerías como `numpy`, `librosa`, `soundfile`) analizando stems exportados, o mediante un plugin VST espía (como el `live_listener`) puesto en el Master de FL.
4. **Fases Engine:** Toda la lógica de "Music Theory", "Arrangement logic" y "Mix logic" puede reusarse en un 80% ya que es independiente del DAW. Solo cambiarían las implementaciones del Adaptador (`Adapter`) de Ableton al de FL Studio.
5. **VST3 Control:** Usar wrappers o controladores en FL (Control Surface) para manejar "Semantic Macros" similares a los Racks de Ableton.

### Resumen de Trabajo
El esfuerzo real radica en construir el `FLStudioAdapter` y el script en Python de FL Studio que exponga los 174 endpoints equivalentes a los usados en Ableton (crear tracks, añadir notas MIDI, establecer paneos, rutear el sidechain, etc.). La capa lógica del **Production Intelligence Engine (PIE)** (validaciones, planes, transacciones, music theory) es completamente modular.