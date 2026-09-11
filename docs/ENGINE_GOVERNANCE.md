# Especificación de Gobernanza del Motor AbletonEngine
## Código de Gobernanza Estricto de Producción para Agentes IA (DAW Governance Contract)

Este documento formaliza el contrato estricto de producción musical que rige a cualquier agente o módulo de IA al interactuar con **Ableton Live 12** a través de **AbletonMCP** y **AbletonEngine**.

La IA no puede operar de manera caótica, complaciente o superficial; el motor actúa como supervisor y guardián de calidad (*Gatekeeper*), bloqueando activamente cualquier operación que viole las mejores prácticas de la industria y la disciplina de producción comercial.

---

### 🚨 REGLA 1: Cero LUFS Sintéticos / Estimados (Auditoría de Audio Real ITU-R BS.1770-5)
* **Prohibición Absoluta**: Queda terminantemente prohibido generar reportes de sonoridad, integrados o de pico utilizando aproximaciones matemáticas artificiales o simuladas (ej. fórmulas analíticas con senoides `np.sin`).
* **Protocolo de Validación**:
  1. Solo se admiten muestras de audio físico real:
     * Archivo `.wav` físico renderizado en el disco local dentro del proyecto, o
     * Buffer de audio PCM estéreo capturado en vivo vía socket UDP en el puerto `9878` mientras la sesión de Live reproduce.
  2. Si no hay audio real disponible, los valores de Integrated LUFS y True Peak deben ser evaluados como `None`.
  3. No se toleran estimaciones de conveniencia: sin audio real, el estado es inamoviblemente `BLOCKED_AWAITING_AUDIO`.

---

### ⛔ REGLA 2: Compuerta de Masterización Bloqueante Incondicional (Gatekeeper Físico)
* **Principio**: La compuerta acústica de la Fase 8 (Masterización y LUFS) es una barrera física de calidad. **Bajo ninguna circunstancia se permite avanzar a la fase de finalización si los requerimientos no se cumplen**.
* **Protocolo de Bloqueo**:
  1. Si `real_audio is None`: Retorna `status: "BLOCKED_AWAITING_AUDIO"`, `retry_required: True`, y la sesión permanece congelada en la Fase 8.
  2. Si el audio real incumple la tolerancia comercial:
     * **CLUB**: $-8.5 \text{ LUFS} \pm 1.0$, $\text{Max True Peak } -0.5 \text{ dBTP}$.
     * **STREAMING**: $-14.0 \text{ LUFS} \pm 1.0$, $\text{Max True Peak } -1.0 \text{ dBTP}$.
     * El motor retorna `status: "NON_COMPLIANT_LUFS"`, reporta el `required_trim_db` y bloquea el avance exigiendo ajuste de faders/limitador y re-auditoría.
  3. **Certificación Única**: Únicamente cuando `audit_res.passed == True` con audio físico validado, se emite el certificado oficial de cumplimiento y se permite avanzar a `PHASE_9_COMPLETED`.

---

### 🛡️ REGLA 3: Cero Silenciamiento de Errores (Zero Silent Swallow)
* **Principio**: Queda prohibido el uso de bloques `try/except: pass` complacientes que enmascaren fallos en la interacción con Ableton Live o en la carga de plugins.
* **Protocolo**:
  1. Si un plugin VST3 (*Vital*, *Serum 2*, *Analog Lab V*) o un Drum Rack falla al cargarse o excede el tiempo límite de espera del LOM:
     * El motor detiene el progreso inmediatamente.
     * Retorna `status: "LOAD_FAILED"`, `retry_required: True`.
     * El cursor permanece en la pista afectada hasta que se resuelva o el usuario instruya explícitamente una alternativa.
  2. Queda prohibido avanzar dejando pistas con dispositivos o sonidos predeterminados por omisión (*Init*).

---

### 🥁 REGLA 4: Verificación Física de Drum Racks y VSTs
* **Principio**: La presencia de un dispositivo en la pista no garantiza sonido; debe auditarse la integridad del rack.
* **Protocolo**:
  1. En pistas de batería (`DRUMS`), el motor debe consultar la API (`get_drum_rack_pads` / `get_drum_pad_devices`) y verificar que al menos los pads críticos (Kick C1/36, Snare D1/38, Clap D#1/39, Hats F#1/42) contengan samples reales asignados.
  2. En instrumentos virtuales, debe comprobarse la conectividad LOM y la presencia de parámetros manipulables ($\Delta \ge 1$).

---

### 🎛️ REGLA 5: Esculpido Obligatorio de los 4 Cuadrantes de Síntesis y Gain Staging Inicial
* **Principio**: Ningún sintetizador puede participar en el arreglo con su timbre en estado *Init* de fábrica.
* **Protocolo**:
  1. Para cada generador sonoro, la IA está obligada a parametrizar quirúrgicamente los 4 cuadrantes tímbricos:
     * **Osciladores / Wavetable**: Tipo de forma de onda, unísono y sub-oscilador.
     * **Filtro**: Frecuencia de corte (*Cutoff*), resonancia y saturación de filtro (*Drive*).
     * **Envolventes ADSR**: Formado de ataque, decay, sustain y release.
     * **Espacio / Modulación**: Brillo y macros.
  2. Inmediatamente después, el motor calcula y aplica la ganancia inicial de pista en dBFS para garantizar un headroom de -18 a -12 dBFS antes de ingresar a la mezcla.

---

### 🔌 REGLA 6: Afinación de Efectos Dispositivo a Dispositivo y Parámetro a Parámetro
* **Principio**: Queda prohibido cargar cadenas de efectos de inserción (*Drum Buss*, *Glue Compressor*, *Saturator*, *EQ Eight*, *Valhalla*, *OTT*) y dejarlas con sus valores de fábrica.
* **Protocolo**:
  1. El motor itera sobre cada procesador de inserción individualmente (`device_index`).
  2. Se ajustan los parámetros cruciales (Threshold, Ratio, Drive, Transients, Cutoff, Attack/Release, Mix Dry/Wet).
  3. Cada inserción recalculada actualiza el margen de ganancia pre-bus.

---

### 🎼 REGLA 7: Composición Modular en 7 Ranuras con Silencios Estructurales Dinámicos
* **Principio**: Queda prohibido generar un clip único continuo que abarque toda la canción de forma monótona, o repetir bucles de 4 compases en todas las pistas simultáneamente.
* **Protocolo**:
  1. La composición musical se divide obligatoriamente en **7 ranuras de clips dedicadas (`0..6`)**:
     * Slot 0: Intro (8 compases).
     * Slot 1: Verso (16 compases).
     * Slot 2: Buildup / Redoble (8 compases).
     * Slot 3: Drop 1 / Estribillo (16 compases).
     * Slot 4: Puente / Calma (8 compases).
     * Slot 5: Drop 2 / Clímax (16 compases).
     * Slot 6: Outro (8 compases).
  2. **Silencios Estructurales Obligatorios**:
     * **Puente (c. 49-56)**: Silencio total en batería (0 notas) y silencio en bajo (0 notas). Solo textura armónica (Keys/Pads).
     * **Buildup (c. 25-32)**: Redoble acelerado progresivo de caja ($1/4 \to 1/8 \to 1/16 \to 1/32$) con **bajo silenciado al 100%** para acumular tensión.
     * **Drops (c. 33-48 y 57-72)**: Despliegue de energía máxima con pegada completa (velocidad 127 en bombos y 808 saturado).
  3. Los clips se copian y distribuyen de forma independiente en la línea temporal del Arrangement View.

---

### 📈 REGLA 8: Automatizaciones Vectoriales Tangibles en el Arrangement View
* **Principio**: La energía y dinamismo de la producción se logran mediante curvas de automatización físicas en la línea de tiempo, no con ajustes estáticos.
* **Protocolo**:
  1. Se utiliza el motor de recetas `ProductionRecipeEngine` y el tejedor de automatizaciones `ArrangementAutomationWeaver`.
  2. Al seleccionarse la **Opción A (Botón A)**, se inyectan en Live:
     * Barridos y risers de filtro en builds y pre-drops.
     * Washouts de reverb y delay antes del impacto con snap a cero en el compás del drop.
     * Cortes de silencio de vacío (*Pre-Drop Vacuums*) de 2 beats antes del impacto.
     * Desvanecimientos graduales en el outro.
  3. Se provee la **Opción B (Botón B)** para omitir (Bypass) de forma controlada cuando el productor lo solicite.

---

### 🧠 REGLA 10: Cero Valores Sugeridos en Configuraciones (Exposición de Rangos y Pensamiento Crítico)
* **Principio Fundamental**: Queda terminantemente prohibido que el motor imponga o proponga valores sugeridos pre-cocinados en las etapas de configuración. El motor no debe pensar por la IA ni por el productor; debe obligar a la IA a reflexionar sobre la física acústica y la identidad tímbrica.
* **Única Excepción**: Selección de plugins e instrumentos instalados (Fase 3), donde el motor consulta la librería física de VSTs y Drum Racks de Live 12.
* **Protocolo de Ejecución**:
  1. En las fases de diseño (Pistas, Estructura, Síntesis de 4 Cuadrantes, Parámetros de Efectos, Tonalidad/BPM y Masterización), el motor **únicamente expone los rangos numéricos técnicos y el comportamiento psicoacústico** de cada variable.
  2. Cada consulta debe plantear una **Decisión Técnica Requerida**, invitando a la IA a evaluar el balance espectral, la densidad y la dinámica.
  3. El motor debe aceptar y procesar cualquier especificación paramétrica legítima enviada por la IA/productor.

---

### ⚡ REGLA 9: Prohibición de Stop-Hooks Invasivos
* **Principio**: La experiencia de producción con el copiloto debe ser ágil y técnica, sin ser interrumpida por ventanas modales artificiales o bloqueos de confirmación innecesarios (`RequestFeedback: true`).
* **Protocolo**: Las acciones instruidas se ejecutan de manera directa, manteniendo la sesión en progreso constante y validando las compuertas a través de la lógica interna del motor.
