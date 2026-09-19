# Ableton Production Intelligence Engine (PIE) — Guía Completa de Usuario y Operación

## 1. Introducción al Sistema

El **Production Intelligence Engine (PIE)** es un middleware de producción musical autónomo, determinista y gobernado para **Ableton Live 12 Suite** (compatible con Live 11).

A diferencia de los asistentes basados exclusivamente en modelos de lenguaje que envían comandos arbitrarios a una DAW, PIE opera bajo un **marco estricto de gobernanza causal y transaccional**:
$$\text{El LLM decide la intención musical} \longrightarrow \text{PIE planifica, valida y verifica acústicamente} \longrightarrow \text{Ableton Live ejecuta}$$

### Capacidades Globales:
- **301 herramientas FastMCP** expuestas a clientes de IA (Claude Desktop, Antigravity, agentes autónomos).
- **956 pruebas automatizadas** de integración, aceptación, modelos DSP, producción musical e inyección de fallos (100% de éxito).
- **El Doctor de Sesión (`copilot_session_doctor`)**: Motor de auditoría clínica en 8 dominios y reparación quirúrgica no destructiva con rollback instantáneo.
- **Producción Guiada de 10 Fases (`copilot_guided_session`)**: Flujo completo de 0 a 100 con 13 roles acústicos dinámicos, compás 63-64 fadeout, malla anti-barro a 441.4 Hz y exportación de stems comerciales.
- **Medición de sonoridad ITU-R BS.1770-5 / EBU R 128** con sobremuestreo sinc FIR $4\times$ para detección de True Peak inter-sample.
- **Transacciones ACID con Write-Ahead Logging (WAL)** y auto-rollback garantizado ante regresiones acústicas o caídas de red.
- **Grafo Causal Acíclico (`ProductionGraph`)** que registra el linaje completo de *por qué* se tomó cada decisión.
- **Memoria de Decisiones (`DecisionMemory`)** contextual e indexada con el invariante *Candidate-Only*.

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
Agrega la configuración del servidor en tu archivo de configuración de MCP:
```json
{
  "mcpServers": {
    "AbletonMCP": {
      "command": "python",
      "args": [
        "F:/Dev/AbletonEngine/server.py"
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
python -m pytest
```
Resultado esperado: **956 passed (100% Verde, 0 failures, 0 regressions)**.

---

## 4. ¿Cuándo usar cada Copiloto? (Guía de Decisión Rápida)

PIE ofrece dos grandes motores inteligentes que resuelven dos problemas completamente distintos:

```
                  ¿QUÉ NECESITAS HACER EN ABLETON LIVE?
                                    │
           ┌────────────────────────┴────────────────────────┐
           ▼                                                 ▼
¿Auditar, limpiar o arreglar                    ¿Crear una canción completa
una sesión/mezcla existente?                    desde cero (0 a 100)?
           │                                                 │
           ▼                                                 ▼
[ copilot_session_doctor ]                      [ copilot_guided_session ]
• Clínico, no destructivo.                      • Creativo, 10 fases.
• Jamás borra canales ni notas.                 • Compone ritmos, bajos, acordes.
• Faders, colisiones, efectos duplicados.       • Diseña sonido, transiciones, stems.
• Snapshots de reversión ("Deshacer").          • Master Gain Boost y 13 roles.
```

---

## 5. El Doctor de Sesión (`copilot_session_doctor`)

El **Doctor de Sesión** ([`session_doctor.py`](file:///F:/Dev/AbletonEngine/engine/production/doctor/session_doctor.py)) es el médico especialista de Ableton Live. Está diseñado para auditar y reparar mezclas saturadas, proyectos desordenados o sesiones importadas.

### 5.1 Principios Clínicos Inviolables
1. **Aislamiento de Estado:** Guarda su estado en `state/production/doctor_session.json`. Jamás toca ni resetea `guided_session.json`.
2. **Cirugía No Destructiva:** Nunca elimina pistas del usuario, nunca ejecuta wipes preflight y no agrega notas MIDI.
3. **Snapshot Previo:** Antes de cualquier cambio, guarda un snapshot físico completo en `state/production/snapshots/`.
4. **Deshacer Inmediato:** El usuario puede revertir todo con `"Deshacer"` o `"Rollback"`.

### 5.2 Los 8 Dominios Clínicos Auditados
1. **Faders & Headroom:** Detecta faders > 0.85 (0 dBFS digital). Aplica re-trimming proporcional conservando el balance relativo hacia niveles nominales controlados (-14 a -12 dBFS).
2. **Clips Vacíos & Zombies:** Localiza clips con longitud cero o sin notas MIDI que saturan el arreglo o consumen recursos.
3. **Pistas Huérfanas / Muertas:** Detecta pistas vacías sin clips, sin ruteo y sin dispositivos para sugerir su limpieza.
4. **Pistas Silenciadas con Contenido Activo:** Identifica pistas con clips sonoros activos que están muteadas accidentalmente.
5. **Efectos Duplicados / Redundantes:** Alerta sobre inserciones duplicadas idénticas (ej. doble EQ Eight consecutivo) que causan corrimiento de fase y sobrecarga.
6. **Campo Estéreo & Mono Compatibility:** Audita que las frecuencias sub-graves (< 120 Hz) estén en mono estricto y previene la saturación del centro estéreo.
7. **Colisión Psicoacústica Low-End (Kick vs 808/Bass):** Evalúa la acumulación de energía en 40-90 Hz y comprueba la presencia de sidechain físico o tallado espectral.
8. **Master Bus Headroom & True Peak:** Mide el margen de picos inter-sample en el Master para evitar distorsión inter-sample antes de la distribución.

### 5.3 Flujo de Uso del Doctor
1. **Lanzar Diagnóstico Pasivo:**
   - Comando: `"Diagnóstico Completo"`
   - El Doctor analiza los 8 dominios y emite un informe clasificando problemas en `CRITICAL`, `WARNING` e `INFO`.
2. **Aplicar Reparación Quirúrgica:**
   - Comando: `"Reparación Quirúrgica No Destructiva"`
   - El Doctor genera un snapshot, ajusta faders a ganancia nominal, elimina clips zombie, limpia efectos duplicados y optimiza el low-end.
3. **Reversión (si es necesaria):**
   - Comando: `"Deshacer"` o `"Rollback"`
   - Restaura el set exactamente a como estaba antes de la intervención.

---

## 6. Producción Guiada de 0 a 100 (`copilot_guided_session`)

El pipeline interactivo de 10 fases ([`guided_session.py`](file:///F:/Dev/AbletonEngine/engine/copilot/guided_session.py)) crea una canción comercial completa con gobernanza de calidad:

### 6.1 Las 10 Fases Explicadas
- **Fase 1: Inicialización & ADN Creativo:** Selección de género (Trap, House, Lo-Fi, Afrobeat, etc.), BPM, tonalidad y modo vocal (`Live Mic Mode` con cero clips en arreglo o importación de audio).
- **Fase 2: Armonía & Progresión:** Progresión de acordes tonales/modales con conducción de voces estricta (máximo salto de 5ta justa).
- **Fase 3: Scaffolding de Pistas & Instrumentos:** Creación dinámica de pistas según los **13 Roles Acústicos** (Kick, Drums, Bass/808, Keys, Brass, Pad, Arp, Lead, Guitars, Organ, Pluck, Vocal Chops, FX Audio). **Cero plantillas fijas.**
- **Fase 4: Composición Musical:** Generación de patrones rítmicos, líneas de bajo/808 con slides, acordes y contramelodías, humanizados en velocidad (15-25%) y microtiming.
- **Fase 5: Síntesis & Sound Design:** Asignación de VSTs (Analog Lab, Vital, Serum, etc.) o nativos con **Esculpido Obligatorio de Síntesis ($\Delta \ge 1$)** en filtros, envolventes o distorsión. Prohibido preset por defecto.
- **Fase 6: Arreglo Macro:** 64 compases con al menos 5 secciones identificadas con Cue Points canónicos (Intro, Verse, Chorus, Drop, Outro).
- **Fase 7: Transiciones & Automatizaciones:** Risers, sweeps, pre-drop vacuums y al menos 16 curvas de automatización continuas.
- **Fase 8: Mezcla, Sidechain & Anti-Mud:** Gain staging, sidechain físico Kick->808 y **Notch Quirúrgico a 441.4 Hz** ($Q=12.0$, -3.5 dB) en armónicos y Master EQ Eight Band 3 para eliminar el barro post-vocal.
- **Fase 9: Top & Tail & Pre-Master Gate:** **Top & Tail Acoustic Guards** (silencio pre-roll < -70 dBFS a 0.0s y fadeout en compases 63-64 a $-\infty$) y compuerta de validación LUFS pre-mastering.
- **Fase 10: Masterización & Stems:** Cadena de master de 5 procesadores con **Master Gain Boost** (+3.0 dB nominal / norm 0.635 con True Peak Mode = 1.0 -> -1.0 a -1.5 dBTP, -13.5 a -14.0 LUFS) y exportación de 6 stems Broadcast WAV 24-bit/44.1 kHz con `stems_manifest.json` y correlación certificada $ho \ge 0.35$.

### 6.2 Hot-Swap de Instrumentos en Fase 10
Al finalizar el proyecto, el usuario puede pedir en cualquier momento:
- `"Cambiar instrumento en pista 4 a Wurlitzer"`
- `"Probar otro sintetizador de lead en pista 7"`
El motor ejecuta un cambio tímbrico no destructivo preservando todas las notas, automatizaciones y cadenas de efectos.

---

## 7. Gobernanza Causal y Grafo Transaccional

Cada acción de PIE está respaldada por el grafo causal inmutable:
1. **Intención:** Definida por el usuario o LLM.
2. **Observación DSP:** Medición acústica objetiva previa.
3. **Plan de Mínima Intervención:** Generación de candidatos y descarte por políticas inviolables.
4. **Transacción con Snapshot:** Operación atómica en Live.
5. **Verificación Acústica:** Medición post-acción y evaluación contra la `VerificationMatrix`.
6. **Commit o Auto-Rollback:** Si la acción causa regresión de True Peak, distorsión o colisión de frecuencias, el motor revierte automáticamente en milisegundos.

---

## 8. Especificaciones de Entrega Comercial

### 8.1 Perfiles de Sonoridad
- **Streaming:** $-14.0	ext{ LUFS} \pm 1.0	ext{ LU}$, Techo $-1.00	ext{ dBTP}$, Max Limiter GR $2.5	ext{ dB}$.
- **Club:** $-7.5	ext{ LUFS} \pm 1.0	ext{ LU}$, Techo $-0.30	ext{ dBTP}$, Max Limiter GR $3.0	ext{ dB}$.
- **EBU R 128:** $-23.0	ext{ LUFS} \pm 0.5	ext{ LU}$, Techo $-1.00	ext{ dBTP}$, Max Limiter GR $2.0	ext{ dB}$.

### 8.2 Stems de Entrega (en `exports/stems/`)
1. `DRUMS.wav`
2. `BASS.wav`
3. `KEYS_BRASS.wav`
4. `VOCALS.wav`
5. `FX.wav`
6. `MASTER.wav`
7. `stems_manifest.json` (Hashes criptográficos SHA-256, mediciones LUFS/True Peak y correlación de fase $ho \ge 0.35$).
