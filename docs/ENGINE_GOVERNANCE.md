# Especificación de Gobernanza del Motor AbletonEngine
## Reglas Obligatorias de Producción para Agentes IA (DAW Governance Contract)

Este documento formaliza el contrato estricto de producción musical que rige a la IA al interactuar con **Ableton Live 12** a través de **AbletonMCP**. La IA no puede operar de manera arbitraria o caótica; el motor actúa como supervisor y guardián de calidad (*Gatekeeper*), bloqueando operaciones que violen las mejores prácticas de la industria y la disciplina de producción.

---

### 1. Regla de Obligatoriedad de Presets (Preset Enforcement)
- **Ámbito**: Instrumentos que dependen de bibliotecas de timbres o emulaciones complejas:
  - **Analog Lab V**: Selección obligatoria desde el catálogo indexado de 14,105 patches de Arturia vía `preset_search` y `preset_select_for_track` (MIDI Program Change).
  - **Omnisphere, ZENOLOGY, Fraction**: Selección obligatoria de preset `.adv` / `.adg` desde la User Library (`D:\Documentos\Ableton\User Library\Presets\Instruments\...`) o banco MIDI.
- **Prohibición**: Queda terminantemente prohibido dejar un sintetizador en sonido "Init" o predeterminado sin identidad tímbrica.
- **Consecuencia de Incumplimiento**: El motor emite `PresetSelectionRequiredError` y bloquea la generación de secuencias y clips en dicha pista hasta que el preset esté asignado.

---

### 2. Regla de Esculpido Inmediato de Parámetros (Mandatory Parameter Sculpting)
- **Ámbito**: Todos los instrumentos (nativos y VST3: *Vital*, *Serum 2*, *Massive X*, *Massive Classic*, *Pigments*, *Analog Lab V*).
- **Flujo Obligatorio**:
  1. Asignar preset o inicializar rol del instrumento.
  2. Inmediatamente después, la IA **debe inspeccionar los controles funcionales** (`plugin_inspect_parameters`) y **esculpir activamente los parámetros clave** (`plugin_set_semantic_parameter`):
     - Filtro / Cutoff (`CUTOFF`)
     - Envolventes (`AMP_ATTACK`, `AMP_RELEASE`)
     - Brillo y Timbre (`BRIGHTNESS`, `TIMBRE`)
     - Macros de hardware (`MACRO_1` .. `MACRO_8`)
     - Sub-osciladores o saturación (`SUB_OSC`, `DRIVE`)
- **Consecuencia de Incumplimiento**: Si una pista se detecta con parámetros en valores 0.0 o por defecto de fábrica, el Gatekeeper marca la pista como `UNCONFIGURED_VST` bloqueando el avance a la fase de mezcla.

---

### 3. Regla de Disciplina en Efectos (No Blind Stacking)
- **Ámbito**: Cadena de inserción de efectos de audio (*Pro-Q 4*, *Decapitator*, *EchoBoy*, *LittleAlterBoy*, *ShaperBox 3*, *Thermal*, *The God Particle*, *OTT*, *Efx REFRACT*, *Efx MOTIONS*, *Efx FRAGMENTS*, *Pro-L 2*).
- **Flujo Obligatorio**:
  - Al añadir un efecto a una pista (`request_add_effect`), la pista queda en estado **`AWAITING_EFFECT_SCULPTING`**.
  - **Bloqueo Activo**: La IA **no puede añadir otro efecto** en esa misma pista hasta haber modificado conscientemente los parámetros del efecto recién insertado.
- **Consecuencia de Incumplimiento**: Intentar apilar otro efecto sin configurar el actual dispara `UnconfiguredEffectStackingError`.

---

### 4. Regla de Reemplazo y Expansión Controlada de Efectos
- **Reemplazo Limpio**:
  - Si un procesador no encaja tímbricamente con el arreglo, el motor permite la sustitución directa (`replace_device`).
  - El nuevo efecto asume el slot pero reinicia su estado de esculpido, requiriendo parametrización inmediata.
- **Expansión Permisiva**:
  - La IA tiene total libertad para encadenar múltiples efectos (ej. Saturador $\rightarrow$ EQ quirúrgico $\rightarrow$ Delay analógico $\rightarrow$ Reverb de shimmer), **siempre y cuando cada efecto individual sea configurado antes de insertar el siguiente**.

---

### 5. Regla de Auditoría de Canal (Signal & Plugin Integrity Audit)
- Antes de dar por concluida cualquier sección o arreglo, el motor somete cada canal a una verificación exhaustiva:
  1. **Presencia de Dispositivos**: Cada pista debe contar con su instrumento o procesador de bus correspondiente.
  2. **Contenido Musical**: Las pistas melódicas, armónicas y rítmicas deben contener clips con eventos MIDI o audio reales.
  3. **Verificación de Señal Viva**: Durante la reproducción (`start_playback`), el motor sondea los medidores de señal de Ableton (`output_meter_level > 0.0`). Las pistas mudas o muertas son marcadas como `AcousticSilenceError`.

---

### 6. Regla de Cumplimiento Estricto de LUFS y Techo True Peak
- **Objetivo Comercial**:
  - **Integrated Loudness**: $-14.0 \text{ LUFS} \pm 0.5 \text{ LUFS}$ (estándar para streaming y difusión sin penalización por normalización).
  - **True Peak**: Techo infranqueable $\le -1.0 \text{ dBTP}$ para eliminar distorsión inter-sample en conversión analógica.
- **Ajuste Automatizado**:
  - El motor evalúa el nivel integrado al final de la canción.
  - Si difiere del objetivo, recalibra la ganancia del limitador maestro (*Pro-L 2*, *The God Particle* o limitador nativo) aplicando la compensación exacta (`limiter_remediation_gain_db = -lufs_delta`).
