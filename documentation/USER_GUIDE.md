# Ableton Production Intelligence Engine (PIE) — Guía Completa de Usuario y Operación

## 1. Introducción al Sistema

El **Production Intelligence Engine (PIE)** es un middleware de producción musical autónomo, determinista y gobernado para **Ableton Live 12 Suite** (compatible con Live 11).

A diferencia de los asistentes basados exclusivamente en modelos de lenguaje que envían comandos arbitrarios a una DAW, PIE opera bajo un **marco estricto de gobernanza causal y transaccional**:
$$\text{El LLM decide la intención musical} \longrightarrow \text{PIE planifica, valida y verifica acústicamente} \longrightarrow \text{Ableton Live ejecuta}$$

### Capacidades Globales:
- **174 herramientas FastMCP** expuestas a clientes de IA (Claude Desktop, Antigravity, agentes autónomos).
- **331 pruebas automatizadas** de integración, aceptación, modelos DSP e inyección de fallos (100% de éxito).
- **Medición de sonoridad ITU-R BS.1770-5 / EBU R 128** con sobremuestreo sinc FIR $4\times$ para detección de True Peak inter-sample.
- **Transacciones ACID con Write-Ahead Logging (WAL)** y auto-rollback garantizado ante regresiones acústicas o caídas de red.
- **Grafo Causal Aclíclico (`ProductionGraph`)** que registra el linaje completo de *por qué* se tomó cada decisión.
- **Memoria de Decisiones (`DecisionMemory`)** contextual e indexada con el invariante *Candidate-Only* (la memoria proporciona evidencia, jamás se auto-ejecuta de forma autónoma).
- **Motor Forense de Audio (Fase 7)** con diagnóstico localizado en tiempo y frecuencia vía STFT.

---

## 2. Requisitos e Instalación

### 2.1 Requisitos del Sistema
- **Sistema Operativo:** Windows 10/11 (64-bit) o macOS (Apple Silicon / Intel).
- **Intérprete Python:** Python 3.11, 3.12 o 3.13 (64-bit).
- **Digital Audio Workstation:** Ableton Live 11 o 12 Suite (se requiere Live Suite para soporte completo de Max for Live y dispositivos nativos avanzados).
- **Librerías Python Principales:** `numpy`, `soundfile`, `networkx`, `mcp`, `pydantic`, `opentelemetry-api`, `pytest`.

### 2.2 Instalación de Dependencias
```bash
pip install numpy soundfile networkx mcp pydantic opentelemetry-api pytest
```

### 2.3 Configuración del MIDI Remote Script en Ableton Live
1. Localiza el directorio de scripts de control de Ableton Live:
   - **Windows:** `%USERPROFILE%\Documents\Ableton\User Library\Remote Scripts\`
   - **macOS:** `~/Music/Ableton/User Library/Remote Scripts/`
2. Copia la carpeta del script `AbletonMCP` dentro de `Remote Scripts`.
3. Abre Ableton Live, navega a **Preferences > Link / Tempo / MIDI**.
4. En la sección **Control Surface**, selecciona `AbletonMCP`.
5. El script abrirá automáticamente un servidor de sockets TCP en `localhost:9877`.

---

## 3. Puesta en Marcha

### 3.1 Servidor FastMCP (`server.py`)
El punto de entrada principal para interactuar con clientes de IA es `server.py`:
```bash
# Iniciar servidor MCP en modo standard I/O (para clientes MCP)
python server.py
```

### 3.2 Configuración en Claude Desktop / Antigravity
Agrega la configuración del servidor en tu archivo `claude_desktop_config.json` o configuración de MCP:
```json
{
  "mcpServers": {
    "ableton-pie": {
      "command": "python",
      "args": [
        "D:/Proyectos/TEST/AbletonEngine/server.py"
      ],
      "env": {
        "ABLETON_HOST": "localhost",
        "ABLETON_PORT": "9877"
      }
    }
  }
}
```

### 3.3 Verificación de la Suite de Pruebas
Puedes ejecutar la suite completa de pruebas de manera offline (no requiere tener Ableton abierto, gracias al `MockAbletonAdapter`):
```bash
python tests/run_all_tests.py
```
Resultado esperado: **331 passed in ~45s (0 failures, 0 regressions)**.

---

## 4. Guía Operativa por Dominios Funcionales

### 4.1 Dominio 1: Núcleo de Sesión y Control Directo (Fase 1)
Permite inspeccionar, navegar y manipular pistas, clips, dispositivos y parámetros de Live.

**Herramientas Clave:**
- `get_session_info`: Información global de tempo, signatura de compás, estado de reproducción y pistas.
- `get_track_info(track_id)`: Inspección detallada de volumen, panorama, mute, solo y cadena de dispositivos.
- `create_midi_track(name, index)` / `create_audio_track(name, index)`: Creación controlada de canales.
- `set_track_volume(track_id, volume)` / `set_track_pan(track_id, pan)`: Ajuste de faders y paneo.
- `lock_object(object_id, reason)`: Protege una pista o clip contra cualquier modificación automática.
- `tx_begin()` / `tx_commit()` / `tx_rollback()`: Transacciones manuales para agrupar múltiples cambios atómicamente.

---

### 4.2 Dominio 2: Teoría Musical, Armonía y Ritmo (Fase 2)
Genera contenido musical fundamentado en teoría de la armonía tonal, funciones tonales y conducción de voces.

**Herramientas Clave:**
- `music_generate_progression(key, scale, style, length)`: Diseña progresiones de acordes basadas en números romanos (ej. `I - vi - IV - V`), resolviendo tensiones armónicas.
- `music_apply_voice_leading(notes, root)`: Aplica conducción estricta de voces para minimizar saltos interválicos y evitar quintas/octavas paralelas.
- `music_apply_groove(clip_id, groove_template, amount)`: Inyecta micro-tiempos, acentuaciones y swing (16th swing, MPC feel, triplet shuffle).
- `music_humanize(clip_id, timing_range_ms, velocity_range)`: Aplica variaciones sutiles de timing y velocidad dentro de tolerancias musicales.

---

### 4.3 Dominio 3: Instrumentos y Sound Racks (Fase 2.5 y 3)
Resuelve y construye racks de instrumentos nativos de Ableton Live.

**Herramientas Clave:**
- `load_drum_kit(genre, kit_type)`: Carga kits de percusión balanceados según el estilo.
- `rack_build_drum_kit(target_track, samples)`: Ensambla un Drum Rack asignando pads canónicos (C1: Kick, D1: Snare, F#1: Closed Hat, etc.).
- `rack_map_macro(track_id, device_index, macro_index, param_name)`: Mapea parámetros profundos a las perillas Macro del rack para control macro-estructural.

---

### 4.4 Dominio 4: Arreglo y Macro-Estructura (Fase 4)
Orquesta la progresión de energía y la narrativa musical del track.

**Herramientas Clave:**
- `arrangement_generate(genre, bpm, energy_profile)`: Construye la línea temporal de secciones (Intro, Build, Drop, Breakdown, Drop 2, Outro).
- `arrangement_curve(section_name, target_energy)`: Modula densidad rítmica y capas tímbricas según la curva de energía deseada.
- `drop_design(drop_number, intensity)`: Aplica técnicas de contraste de frecuencia (corte de sub-graves previo al impacto, ensanchamiento estéreo en el drop).
- `arrangement_lint()`: Analiza el arreglo detectando secciones monótonas o transiciones abruptas sin preparación.

---

### 4.5 Dominio 5: Digital Ear & Motor de Mezcla (Fase 5)
Proporciona análisis acústico y resolución de conflictos de frecuencia.

**Herramientas Clave:**
- `mix_analyze(target_tracks)`: Extrae mediciones de RMS, pico, balance espectral en 8 bandas y correlación de fase estéreo.
- `mix_diagnose(context)`: Detecta enmascaramiento kick/bass, exceso de subgraves o desbalance lateral.
- `mix_conflict_graph()`: Construye el grafo de colisión entre pistas concurrentes.
- `mix_suggest_correction(conflict_id)`: Sugiere correcciones mínimas (sidechain, EQ dinámico, ducking espectral).
- `mix_apply_correction(correction_id)`: Aplica la corrección dentro de una transacción reversible.

---

### 4.6 Dominio 6: Masterización y Compliance Acústico (Fase 6 & BS.1770-5)
Prepara el master final cumpliendo normativas internacionales y perfiles de streaming.

**Herramientas Clave:**
- `master_readiness()`: Audita la mezcla previa (headroom disponible $\ge 3\text{ dB}$, ausencia de clipping, balance de graves).
- `master_create_chain(style, delivery_target)`: Configura la cadena de 5 procesadores de masterización:
  1. EQ Correctivo (High-pass sub-sónico a 30 Hz).
  2. Compresor de Bus (Glue, ratio 2:1 o 4:1, ataque lento, release automático).
  3. EQ Tonal / Tonal Balance (Coloración analógica suave).
  4. Procesador Estéreo (Mono maker sub-120 Hz, ensanchador de altas).
  5. Limitador True Peak (Techo a $-1.0\text{ dBTP}$ o $-0.3\text{ dBTP}$).
- `master_evaluate(profile_name)`: Evalúa el audio renderizado contra `EBU_R128`, `STREAMING` o `CLUB`.
- `master_translation_test()`: Simula la reproducción en 6 sistemas (Club PA, Smartphones, Auriculares, Coche, Monitores de estudio, Bluetooth speaker).

---

### 4.7 Dominio 7: Audio Forensics Engine (Fase 7)
Diagnóstico de alta precisión localizado en tiempo y frecuencia.

**Herramientas Clave:**
- `forensics_analyze_track(track_id)`: Análisis STFT multi-resolución.
- `forensics_detect_anomalies()`: Localiza clics, pops, cortes de señal (dropouts), offsets de corriente continua (DC Offset) e inversiones de fase.
- `forensics_spectral_percentiles()`: Calcula percentiles $p_{10}$, $p_{50}$ y $p_{90}$ de energía espectral por banda.
- `forensics_export_report()`: Genera un reporte forense inmutable con firma criptográfica SHA-256.

---

### 4.8 Dominio 8: Production Governance Layer (Hito 1)
La capa de supervisión que asegura que ninguna acción se ejecute sin justificación, políticas y verificación.

**Herramientas Clave:**
1. `production_status`: Retorna el estado global, versión del grafo y total de decisiones registradas.
2. `production_plan(intent, target, domain)`: Genera un plan formal evaluando candidatos bajo el Principio de Mínima Intervención. **No muta la sesión**.
3. `production_validate(plan_id)`: Verifica frescura del fingerprint (`STALE`), ausencia de locks y cumplimiento de políticas.
4. `production_execute(plan_id)`: Ejecuta atómicamente, captura mediciones posteriores, evalúa la matriz de verificación y confirma (`COMMIT`) o revierte (`ROLLBACK`).
5. `production_explain(decision_id)`: Genera el informe causal de auditoría (FACT, MEASUREMENT, INFERENCE, DECISION, ACTION, RESULT).
6. `production_history(limit)`: Lista cronológica de decisiones previas.
7. `production_graph(scope)`: Inspección del DAG causal.
8. `production_rollback(decision_id_or_tx)`: Reversión atómica de primera clase sin pérdida de historial.
9. `production_memory_search(query, context)`: Recuperación de precedentes técnicos (siempre como evidencia, jamás como auto-ejecución).

---

## 5. Ejemplo de Flujo de Trabajo Completo (Golden E2E)

### Caso: "Quiero que el master tenga más volumen para Spotify"

1. **Paso 1: Generar el Plan**
   ```json
   // Tool: production_plan
   {
     "intent": "Quiero que el master tenga más volumen para Spotify",
     "target": "Master",
     "domain": "mastering"
   }
   ```
   *Respuesta de PIE:*
   - Analiza medición base (-14.8 LUFS, True Peak -1.0 dBTP).
   - Target para streaming: -14.0 LUFS (delta requerido: +0.8 LUFS).
   - Genera candidatos (Limitador +0.8 dB, Limitador +3.5 dB, Master EQ +1.5 dB).
   - Aplica `ProductionPolicyEngine`: descarta Limitador +3.5 dB (exceso de GR) y EQ (exceso de ganancia).
   - Selecciona Limitador +0.8 dB y genera `plan_id = "plan_1234abcd"`.

2. **Paso 2: Validar el Plan**
   ```json
   // Tool: production_validate
   {
     "plan_id": "plan_1234abcd"
   }
   ```
   *Respuesta:* `{"status": "VALID", "valid": true}`.

3. **Paso 3: Ejecutar con Verificación Acústica**
   ```json
   // Tool: production_execute
   {
     "plan_id": "plan_1234abcd"
   }
   ```
   *Comportamiento interno:*
   - Abre transacción atómica con snapshot previo.
   - Aplica ajuste de limitador en Ableton Live.
   - Captura medición posterior: -14.0 LUFS, -0.4 dBTP.
   - Evalúa `VerificationMatrix`: Objetivo cumplido (+0.8 LUFS), sin regresión de True Peak.
   - Ejecuta `commit()`, actualiza el `ProductionGraph` con nodo `RESULT` e indexa en `DecisionMemory`.
   *Respuesta:* `{"success": true, "status": "COMMITTED", "actual_delta": {"integrated_lufs": 0.8}}`.

4. **Paso 4: Auditoría Causal**
   ```json
   // Tool: production_explain
   {
     "decision_id": "dec_5678ef01"
   }
   ```
   *Respuesta:* Informe estructurado con la evidencia acústica, reglas aplicadas y alternativas rechazadas.
