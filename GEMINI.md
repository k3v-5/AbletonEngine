# Reglas del Sistema y Estándar de Almacenamiento de Canciones (AbletonEngine)

## 📁 1. Estructura Obligatoria de Almacenamiento de Canciones

Toda canción, producción, beat o proyecto generado mediante `copilot_guided_session`, `ProjectLifecycleManager`, `LiveGuiProjectSaver` o cualquier proceso de producción autónoma (incluyendo sesiones nocturnas) **DEBE** guardarse obligatoriamente bajo la siguiente jerarquía física en el disco `F:\Canciones`:

```text
F:\Canciones\
└── <Género>\
    └── <Nombre_Cancion>\
        ├── <Nombre_Cancion> Project\
        │   ├── <Nombre_Cancion>.als
        │   └── Ableton Project Info\
        ├── <Nombre_Cancion>.als
        ├── Presets\
        │   ├── *.vital (Presets de Vital diseñados para la canción)
        │   └── presets_manifest.json (Mapeo pista -> preset -> parámetros)
        └── GuidedSession_Info\
            ├── guided_session_state.json (Estado completo del motor)
            ├── project_manifest.json (Metadatos: BPM, tonalidad, pistas, roles)
            ├── scores\
            │   └── *_score.json (Partituras de eventos MIDI y tiempos)
            └── guided_session_report.md (Informe legible de producción)
```

---

## 🏷️ 2. Mapeo Canónico de Carpetas por Género

La carpeta de género (`<Género>`) se normaliza automáticamente según la siguiente taxonomía:
- **`Reggaeton`**: Reggaetón Clásico, Neo-Reggaetón, Dembow, Neoperreo, Perreo, estilo Tainy / Luny Tunes.
- **`Trap_HipHop`**: Dark Trap, Hip Hop, Drill, Boom Bap, Trap Latino.
- **`Electronic`**: House, Tech House, Techno, EDM, Afro House, Hard Techno.
- **`Synthwave`**: Retrowave, Cyberpunk, Synthpop, Darksynth.
- **`Rock`**: Rock, Metal, Punk, Indie Rock.
- **`Pop_RnB`**: Pop, R&B, Soul, Indie Pop.

---

## 🎛️ 3. Reglas de Presets y Diseño Sonoro
1. **Preservación de Presets Físicos:** Todo preset generado o afinado en **Vital Audio** para cada pista (`BASS_808`, `LEAD`, `KEYS`, `PAD`, etc.) debe exportarse físicamente a `<Nombre_Cancion>\Presets\`.
2. **Manifiesto de Presets (`presets_manifest.json`):** Debe documentar con precisión el índice de la pista, su nombre, su rol canónico en Copilot y el archivo de preset correspondiente.
3. **Invariante de la Pista de Batería (Pista 0):** Ningún plugin ni bajo 808 puede sobreescribir la Pista 0 cuando contenga un Drum Rack (`808 Core Kit` u otro kit de batería). Las etiquetas `[DRUMS]` están blindadas contra secuestros.

---

## 📑 4. Registro de Sesión Guiada (`GuidedSession_Info`)
Cada proyecto debe conservar dentro de `GuidedSession_Info\`:
1. El estado JSON de la sesión guiada (`guided_session_state.json`).
2. Las partituras MIDI generadas (`scores/*.json`).
3. El manifiesto del proyecto con los parámetros de mezcla y masterización (`project_manifest.json`).
4. El informe Markdown estructurado (`guided_session_report.md`).
5. El veredicto técnico de integridad (`session_audit_verdict.json`).

---

## 👁️ 5. Regla Mandatoria de Inspección Visual de la IA (`visual_audit.png`)

Al finalizar cada producción de canción (sea individual o en bucle nocturno), la IA **TIENE LA OBLIGACIÓN ESTRICTA** de:
1. **Ver la imagen físicamente:** La IA debe invocar la herramienta `view_file` sobre el archivo de imagen:
   `F:\Canciones\<Género>\<Nombre_Cancion>\visual_audit.png`
2. **Inspeccionar visualmente los 4 criterios de integridad:**
   - **Criterio A (Título):** Confirmar en la barra superior de Ableton que el proyecto tiene el nombre real de la canción (ej: `DATA_Horizon - Ableton Live 12 Suite`).
   - **Criterio B (Línea de Tiempo / Arrangement):** Confirmar que la vista Arrangement muestra los bloques de clips MIDI verdes distribuidos a lo largo del tiempo (intro, coro, versos) y que la canción no es un lienzo vacío.
   - **Criterio C (Batería en Pista 0):** Confirmar que la Pista 0 (`[DRUMS]`) contiene el Drum Rack y su cadena de inserción de efectos en la vista inferior, y que no fue secuestrada ni reemplazada por un sintetizador o bajo.
   - **Criterio D (Ausencia de Modales de Error):** Confirmar que la interfaz de Ableton está limpia y sin ventanas emergentes de error ("Audio Engine Off", "Missing Files", "Crash Dialog") bloqueando la pantalla.

---

## 🛡️ 6. Veredicto de Integridad Física Obligatorio (`audit_session_physical_integrity`)

El sistema ejecutará automáticamente la compuerta de verificación `LiveVisualAuditor.audit_session_physical_integrity()`:
- Comprueba que el `.als` exista y pese > 300 KB.
- Comprueba que la carpeta `Presets/` contenga los presets `.vital` y el `presets_manifest.json`.
- Comprueba que la Pista 0 contenga el kit de batería (`has_drum_kit: True`) y no esté secuestrada (`track_0_hijacked: False`).
- Comprueba que la imagen `visual_audit.png` sea válida (no sea un fotograma negro o congelado).
- **Si el veredicto no es `VERIFIED_SUCCESS`, la producción NO se da por finalizada** y el sistema debe aplicar reparación inmediata o alertar al usuario.
